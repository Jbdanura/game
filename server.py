import socket
import threading
import json
import time
import sqlite3
import hashlib
import os
import random
import math
from datetime import datetime

# Ensure database directory exists
os.makedirs('data', exist_ok=True)

# Set up database
def setup_database():
    conn = sqlite3.connect('data/game_users.db')
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        created_at TEXT NOT NULL,
        last_login TEXT
    )
    ''')
    conn.commit()
    conn.close()

# Initialize database
setup_database()

# Map constants
MAP_WIDTH = 50
MAP_HEIGHT = 50
TILE_SIZE = 40

class GameServer:
    def __init__(self, host='localhost', port=5555):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.clients = {}
        self.players = {}
        self.active_users = {}  # Track active user sessions by username
        self.player_count = 0
        self.running = False
        self.lock = threading.Lock()
        
        # Define spawn area (center of map)
        self.spawn_x = (MAP_WIDTH * TILE_SIZE) // 2
        self.spawn_y = (MAP_HEIGHT * TILE_SIZE) // 2
        self.spawn_range = 150  # Range around spawn point
        
        # Combat constants
        self.MAX_HEALTH = 100
        self.ATTACK_DAMAGE = 10
        self.ATTACK_COOLDOWN = 1.0  # Seconds
        self.ATTACK_RANGE = 60      # Pixels
        
        # Map seed for fixed map generation
        self.map_seed = 12345
        
        # Generate server-side map representation for spawn validation
        self.map_tiles = self.generate_simple_map()
        
    def generate_simple_map(self):
        """Generate a simple map representation to validate spawn points"""
        # Set the random seed for consistent generation
        random.seed(self.map_seed)
        
        # Initialize with grass
        tiles = [["grass" for _ in range(MAP_WIDTH)] for _ in range(MAP_HEIGHT)]
        
        # Add fewer trees in a more structured pattern
        for y in range(MAP_HEIGHT):
            for x in range(MAP_WIDTH):
                # Keep the center completely clear to ensure safe spawning
                distance_to_center = ((x - MAP_WIDTH//2)**2 + (y - MAP_HEIGHT//2)**2)**0.5
                
                # Create fewer trees in the outer areas
                if distance_to_center > 20 and random.random() < 0.2:
                    tiles[y][x] = "tree"
                
                # Create very scattered trees in the mid-range
                elif 10 < distance_to_center <= 20 and random.random() < 0.08:
                    tiles[y][x] = "tree"
                    
                # Create a few decorative tree clusters
                elif self.is_in_tree_cluster(x, y):
                    tiles[y][x] = "tree"
                    
        return tiles
    
    def is_in_tree_cluster(self, x, y):
        """Check if position is in a tree cluster"""
        # Define smaller tree cluster centers (decorative)
        clusters = [
            (MAP_WIDTH//5, MAP_HEIGHT//5),
            (4*MAP_WIDTH//5, MAP_HEIGHT//5),
            (MAP_WIDTH//5, 4*MAP_HEIGHT//5),
            (4*MAP_WIDTH//5, 4*MAP_HEIGHT//5)
        ]
        
        # Check if within any cluster radius - smaller clusters
        for cx, cy in clusters:
            dist = ((x - cx)**2 + (y - cy)**2)**0.5
            if dist < 2 and random.random() < 0.7:  # Smaller clusters
                return True
        return False
    
    def is_valid_spawn_position(self, x, y):
        """Check if a position is valid for spawning (not on a tree)"""
        # Convert to tile coordinates
        tile_x = int(x // TILE_SIZE)
        tile_y = int(y // TILE_SIZE)
        
        # Check bounds
        if (tile_x < 0 or tile_y < 0 or 
            tile_x >= MAP_WIDTH or tile_y >= MAP_HEIGHT):
            return False
            
        # Check if not a tree
        return self.map_tiles[tile_y][tile_x] != "tree"
    
    def get_valid_spawn_position(self):
        """Get a valid spawn position that's not on a tree"""
        # Try up to 20 times to find a valid spawn position
        for _ in range(20):
            spawn_x = self.spawn_x + random.randint(-self.spawn_range, self.spawn_range)
            spawn_y = self.spawn_y + random.randint(-self.spawn_range, self.spawn_range)
            
            if self.is_valid_spawn_position(spawn_x, spawn_y):
                return spawn_x, spawn_y
                
        # If all attempts fail, use the exact center (which should be clear)
        return self.spawn_x, self.spawn_y
        
    def start(self):
        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            self.running = True
            print(f"Server started on {self.host}:{self.port}")
            
            # Start broadcasting game state
            broadcast_thread = threading.Thread(target=self.broadcast_game_state)
            broadcast_thread.daemon = True
            broadcast_thread.start()
            
            while self.running:
                client_socket, addr = self.server_socket.accept()
                print(f"Connection from {addr}")
                
                # Handle authentication before assigning player_id
                auth_thread = threading.Thread(target=self.handle_authentication, args=(client_socket, addr))
                auth_thread.daemon = True
                auth_thread.start()
                
        except Exception as e:
            print(f"Server error: {e}")
        finally:
            self.server_socket.close()
    
    def handle_authentication(self, client_socket, addr):
        try:
            # Wait for auth message
            while True:
                auth_data = self.receive_data(client_socket)
                if not auth_data:
                    break
                
                auth_type = auth_data.get("type")
                
                if auth_type == "register":
                    # Handle registration
                    result = self.register_user(auth_data.get("username"), auth_data.get("password"))
                    self.send_data(client_socket, {"type": "register_result", "success": result[0], "message": result[1]})
                    if not result[0]:
                        continue  # If registration failed, wait for another auth attempt
                
                elif auth_type == "login":
                    # Handle login
                    result = self.login_user(auth_data.get("username"), auth_data.get("password"))
                    self.send_data(client_socket, {"type": "login_result", "success": result[0], "message": result[1]})
                    if not result[0]:
                        continue  # If login failed, wait for another auth attempt
                    
                    # If login successful, create player and start game handling
                    username = auth_data.get("username")
                    with self.lock:
                        self.player_count += 1
                        player_id = self.player_count
                        self.clients[player_id] = client_socket
                        
                        # Generate valid spawn position (not on trees)
                        spawn_x, spawn_y = self.get_valid_spawn_position()
                        
                        # Initial player data
                        self.players[player_id] = {
                            "id": player_id,
                            "username": username,
                            "x": spawn_x,
                            "y": spawn_y,
                            "health": self.MAX_HEALTH,
                            "max_health": self.MAX_HEALTH,
                            "last_attack_time": 0,
                            "color": (0, 0, 255)  # Default blue
                        }
                        
                        # Send map seed so all clients generate the same map
                        map_data = {
                            "type": "map_data",
                            "seed": self.map_seed
                        }
                        self.send_data(client_socket, map_data)
                    
                    # Send player ID and spawn position to client
                    self.send_data(client_socket, {
                        "type": "player_id", 
                        "id": player_id,
                        "x": spawn_x,
                        "y": spawn_y
                    })
                    
                    # Handle client communication in a separate thread
                    client_thread = threading.Thread(target=self.handle_client, args=(player_id,))
                    client_thread.daemon = True
                    client_thread.start()
                    
                    # No need to continue the auth loop
                    break
        except Exception as e:
            print(f"Authentication error: {e}")
            client_socket.close()
    
    def register_user(self, username, password):
        if not username or not password:
            return (False, "Username and password are required")
        
        if len(username) < 3:
            return (False, "Username must be at least 3 characters")
            
        if len(password) < 4:
            return (False, "Password must be at least 4 characters")
        
        try:
            # Hash the password
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            # Store in database
            conn = sqlite3.connect('data/game_users.db')
            cursor = conn.cursor()
            
            # Check if user already exists
            cursor.execute("SELECT username FROM users WHERE username = ?", (username,))
            if cursor.fetchone():
                conn.close()
                return (False, "Username already exists")
            
            # Insert new user
            created_at = datetime.now().isoformat()
            cursor.execute(
                "INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)",
                (username, password_hash, created_at)
            )
            conn.commit()
            conn.close()
            return (True, "Registration successful")
        except Exception as e:
            print(f"Registration error: {e}")
            return (False, "Server error during registration")
    
    def login_user(self, username, password):
        if not username or not password:
            return (False, "Username and password are required")
        
        try:
            # Check if user is already logged in
            with self.lock:
                if username in self.active_users:
                    return (False, "User already logged in")
                
            # Hash the password
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            # Check credentials
            conn = sqlite3.connect('data/game_users.db')
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id FROM users WHERE username = ? AND password_hash = ?", 
                (username, password_hash)
            )
            user = cursor.fetchone()
            
            if not user:
                conn.close()
                return (False, "Invalid username or password")
            
            # Update last login time
            last_login = datetime.now().isoformat()
            cursor.execute(
                "UPDATE users SET last_login = ? WHERE username = ?",
                (last_login, username)
            )
            conn.commit()
            conn.close()
            
            # Mark user as active
            with self.lock:
                self.active_users[username] = True
                
            return (True, "Login successful")
        except Exception as e:
            print(f"Login error: {e}")
            return (False, "Server error during login")
    
    def handle_client(self, player_id):
        client_socket = self.clients.get(player_id)
        if not client_socket:
            return
            
        try:
            while self.running:
                data = self.receive_data(client_socket)
                if not data:
                    break
                
                # Handle movement updates
                if "x" in data and "y" in data:
                    with self.lock:
                        if player_id in self.players:
                            self.players[player_id]["x"] = data["x"]
                            self.players[player_id]["y"] = data["y"]
                
                # Handle attack requests
                if data.get("type") == "attack":
                    self.handle_attack(player_id)
                
        except Exception as e:
            print(f"Error handling client {player_id}: {e}")
        finally:
            print(f"Client {player_id} disconnected")
            self.disconnect_player(player_id)
    
    def handle_attack(self, attacker_id):
        with self.lock:
            # Check if attacker exists and attack cooldown has passed
            if attacker_id not in self.players:
                return
                
            attacker = self.players[attacker_id]
            current_time = time.time()
            
            if current_time - attacker.get("last_attack_time", 0) < self.ATTACK_COOLDOWN:
                return  # Attack on cooldown
                
            # Update last attack time
            attacker["last_attack_time"] = current_time
            
            # Get attacker position
            attacker_x = attacker["x"]
            attacker_y = attacker["y"]
            
            # Check for targets in range
            attacked_players = []
            for target_id, target in self.players.items():
                if target_id == attacker_id:
                    continue  # Skip self
                    
                # Calculate distance
                target_x = target["x"]
                target_y = target["y"]
                distance = ((attacker_x - target_x) ** 2 + (attacker_y - target_y) ** 2) ** 0.5
                
                if distance <= self.ATTACK_RANGE:
                    # Apply damage
                    target["health"] = max(0, target["health"] - self.ATTACK_DAMAGE)
                    attacked_players.append(target_id)
                    
                    # Send attack notification to all clients
                    attack_data = {
                        "type": "attack_event",
                        "attacker_id": attacker_id,
                        "target_id": target_id,
                        "damage": self.ATTACK_DAMAGE,
                        "remaining_health": target["health"]
                    }
                    
                    # If player died, handle respawn
                    if target["health"] <= 0:
                        # Get a valid respawn position
                        respawn_x, respawn_y = self.get_valid_spawn_position()
                        
                        # Respawn with full health at spawn point
                        target["health"] = self.MAX_HEALTH
                        target["x"] = respawn_x
                        target["y"] = respawn_y
                        
                        # Add death info to the attack event
                        attack_data["killed"] = True
                        attack_data["respawn_x"] = respawn_x
                        attack_data["respawn_y"] = respawn_y
                    
                    # Broadcast the attack event
                    for _, client_socket in self.clients.items():
                        try:
                            self.send_data(client_socket, attack_data)
                        except:
                            pass  # Handle in the client thread
                    
            return len(attacked_players) > 0  # Return true if attack hit someone
    
    def disconnect_player(self, player_id):
        with self.lock:
            if player_id in self.clients:
                self.clients[player_id].close()
                del self.clients[player_id]
            if player_id in self.players:
                # Remove username from active users
                username = self.players[player_id].get("username")
                if username and username in self.active_users:
                    del self.active_users[username]
                # Remove player
                del self.players[player_id]
    
    def send_data(self, client_socket, data):
        try:
            message = json.dumps(data).encode('utf-8')
            message_length = len(message).to_bytes(4, byteorder='big')
            client_socket.send(message_length + message)
        except Exception as e:
            print(f"Error sending data: {e}")
    
    def receive_data(self, client_socket):
        try:
            # Receive message length (4 bytes)
            message_length_bytes = client_socket.recv(4)
            if not message_length_bytes:
                return None
                
            message_length = int.from_bytes(message_length_bytes, byteorder='big')
            
            # Receive the actual message
            message = b""
            bytes_received = 0
            
            while bytes_received < message_length:
                chunk = client_socket.recv(min(message_length - bytes_received, 4096))
                if not chunk:
                    return None
                message += chunk
                bytes_received += len(chunk)
                
            return json.loads(message.decode('utf-8'))
        except Exception as e:
            print(f"Error receiving data: {e}")
            return None
    
    def broadcast_game_state(self):
        while self.running:
            with self.lock:
                if self.players:
                    game_state = {"type": "game_state", "players": self.players}
                    for player_id, client_socket in self.clients.items():
                        try:
                            self.send_data(client_socket, game_state)
                        except:
                            pass  # Handle in the client thread
            time.sleep(0.033)  # ~30 updates per second

if __name__ == "__main__":
    server = GameServer()
    server.start() 