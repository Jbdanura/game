import pygame
import sys
import socket
import json
import threading
import random
import math
import time
import os

# Initialize pygame
pygame.init()
pygame.mixer.init()  # Initialize the sound mixer

# Game constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
PLAYER_SPEED = 5
TILE_SIZE = 40  # Size of map tiles
MAP_WIDTH = 50  # Width in tiles
MAP_HEIGHT = 50  # Height in tiles

# Combat constants
ATTACK_RANGE = 60
ATTACK_COOLDOWN = 1.0  # seconds
ATTACK_DAMAGE = 10
MAX_HEALTH = 100

# UI Constants
INPUT_BOX_WIDTH = 280
INPUT_BOX_HEIGHT = 36
BUTTON_WIDTH = 140
BUTTON_HEIGHT = 40
PADDING = 15

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
GRAY = (200, 200, 200)
LIGHT_BLUE = (173, 216, 230)
DARK_GRAY = (80, 80, 80)

# Modern UI Color Scheme
BACKGROUND_COLOR = (240, 242, 245)
PRIMARY_COLOR = (66, 103, 178)  # Facebook blue
SECONDARY_COLOR = (24, 119, 242)  # Lighter blue
ACCENT_COLOR = (53, 120, 229)
ERROR_COLOR = (235, 87, 87)
SUCCESS_COLOR = (75, 181, 67)
BORDER_COLOR = (218, 220, 224)
TEXT_COLOR = (28, 30, 33)
PLACEHOLDER_COLOR = (142, 142, 142)
BOX_BACKGROUND = (255, 255, 255)
BUTTON_TEXT_COLOR = (255, 255, 255)

# Nature-themed Colors
GRASS_GREEN = (126, 200, 80)
TREE_GREEN = (53, 125, 34)
WATER_BLUE = (64, 164, 223)
SAND_COLOR = (237, 201, 175)
PATH_BROWN = (160, 126, 84)
FLOWER_COLORS = [
    (255, 0, 0),      # Red
    (255, 201, 14),   # Yellow
    (156, 39, 176),   # Purple
    (255, 87, 34)     # Orange
]

# Health bar colors
HEALTH_BAR_BG = (60, 60, 60)
HEALTH_BAR_BORDER = BLACK
HEALTH_COLOR = (0, 200, 0)
LOW_HEALTH_COLOR = (200, 50, 0)

# Create the game window
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("2D MMO Game - Client")
clock = pygame.time.Clock()

# Setup fonts
font = pygame.font.SysFont(None, 28)
small_font = pygame.font.SysFont(None, 22)
title_font = pygame.font.SysFont(None, 44)
tiny_font = pygame.font.SysFont(None, 18)

# Load or create game assets
def create_simple_image(color, size, shape="rect"):
    surf = pygame.Surface(size, pygame.SRCALPHA)
    if shape == "rect":
        pygame.draw.rect(surf, color, (0, 0, size[0], size[1]))
    elif shape == "circle":
        pygame.draw.circle(surf, color, (size[0]//2, size[1]//2), min(size[0], size[1])//2)
    return surf

# Create game assets
def create_game_assets():
    assets = {}
    
    # Tile assets
    assets["grass"] = create_tile_grass()
    assets["tree"] = create_tile_tree()
    
    # Character assets
    assets["player_base"] = create_player_sprite()
    
    # Combat assets
    assets["attack_effect"] = create_attack_effect()
    
    # Load sounds
    assets["sound_attack"] = pygame.mixer.Sound("data/attack.wav")
    assets["sound_hit"] = pygame.mixer.Sound("data/hit.wav")
    
    # Set sound volumes
    assets["sound_attack"].set_volume(0.3)
    assets["sound_hit"].set_volume(0.4)
    
    return assets

def create_tile_grass():
    surf = pygame.Surface((TILE_SIZE, TILE_SIZE))
    surf.fill(GRASS_GREEN)
    # Add some grass detail
    for _ in range(5):
        x = random.randint(5, TILE_SIZE-5)
        y = random.randint(5, TILE_SIZE-5)
        height = random.randint(3, 7)
        width = random.randint(1, 2)
        color = (min(GRASS_GREEN[0] + 30, 255), min(GRASS_GREEN[1] + 30, 255), min(GRASS_GREEN[2] + 30, 255))
        pygame.draw.line(surf, color, (x, y), (x, y-height), width)
    return surf

def create_tile_tree():
    surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
    # Tree trunk
    trunk_color = PATH_BROWN
    pygame.draw.rect(surf, trunk_color, (TILE_SIZE//2 - 4, TILE_SIZE//2, 8, TILE_SIZE//2))
    # Tree leaves
    leaf_color = TREE_GREEN
    pygame.draw.circle(surf, leaf_color, (TILE_SIZE//2, TILE_SIZE//3), TILE_SIZE//3)
    return surf

def create_player_sprite():
    surf = pygame.Surface((30, 40), pygame.SRCALPHA)
    
    # Body
    pygame.draw.rect(surf, (180, 140, 120), (10, 15, 10, 15))  # torso
    
    # Head
    pygame.draw.circle(surf, (225, 198, 153), (15, 10), 8)  # head
    
    # Arms
    pygame.draw.rect(surf, (180, 140, 120), (5, 15, 5, 12))  # left arm
    pygame.draw.rect(surf, (180, 140, 120), (20, 15, 5, 12))  # right arm
    
    # Legs
    pygame.draw.rect(surf, (70, 70, 180), (10, 30, 4, 10))  # left leg
    pygame.draw.rect(surf, (70, 70, 180), (16, 30, 4, 10))  # right leg
    
    return surf

def create_attack_effect():
    # Create a more dynamic attack effect animation
    surf = pygame.Surface((80, 80), pygame.SRCALPHA)
    
    # Draw a slash effect
    pygame.draw.arc(surf, (255, 255, 255, 200), (5, 5, 70, 70), 0, math.pi, 6)
    pygame.draw.arc(surf, (255, 200, 0, 200), (10, 10, 60, 60), 0, math.pi, 4)
    pygame.draw.arc(surf, (255, 100, 0, 180), (15, 15, 50, 50), 0, math.pi, 3)
    
    return surf

class DamageNumber:
    def __init__(self, x, y, amount, color=(255, 50, 50)):
        self.x = x
        self.y = y
        self.amount = amount
        self.color = color
        self.start_time = time.time()
        self.duration = 1.0  # Show for 1 second
        self.speed = 1.5     # Float up speed
        
    def is_expired(self):
        return time.time() - self.start_time > self.duration
        
    def draw(self, surface, camera_x, camera_y):
        # Calculate elapsed time and animation progress
        elapsed = time.time() - self.start_time
        progress = elapsed / self.duration  # 0.0 to 1.0
        
        # Calculate position with upward movement
        screen_x = self.x - camera_x
        screen_y = self.y - camera_y - (progress * 40)  # Float upward
        
        # Calculate alpha for fade-out
        alpha = int(255 * (1.0 - progress))
        
        # Render text with size pulsing
        scale = 1.0 + 0.5 * math.sin(progress * math.pi)  # Pulse size
        font_size = int(24 * scale)
        damage_font = pygame.font.SysFont(None, font_size)
        
        # Render the damage number
        text = damage_font.render(f"-{self.amount}", True, self.color)
        text.set_alpha(alpha)
        
        # Draw with slight glow effect
        glow = damage_font.render(f"-{self.amount}", True, (255, 255, 200))
        glow.set_alpha(int(alpha * 0.5))
        
        surface.blit(glow, (screen_x+2, screen_y+2))
        surface.blit(text, (screen_x, screen_y))

class AnimationManager:
    def __init__(self):
        self.animations = []
        self.damage_numbers = []
    
    def add_attack_animation(self, x, y, duration=0.3):
        self.animations.append({
            "type": "attack",
            "x": x,
            "y": y,
            "start_time": time.time(),
            "duration": duration
        })
    
    def add_damage_number(self, x, y, amount):
        self.damage_numbers.append(DamageNumber(x, y, amount))
    
    def update(self):
        # Remove expired animations
        current_time = time.time()
        self.animations = [anim for anim in self.animations if current_time - anim["start_time"] < anim["duration"]]
        
        # Remove expired damage numbers
        self.damage_numbers = [dmg for dmg in self.damage_numbers if not dmg.is_expired()]
    
    def draw(self, surface, camera_x, camera_y, assets):
        # Draw attack animations
        for anim in self.animations:
            if anim["type"] == "attack":
                # Draw attack animation
                screen_x = anim["x"] - camera_x
                screen_y = anim["y"] - camera_y
                
                # Calculate animation progress (0.0 to 1.0)
                progress = (time.time() - anim["start_time"]) / anim["duration"]
                
                # Scale and fade based on progress
                scale = 1.0 + progress * 0.5  # Grows to 1.5x size
                alpha = int(255 * (1.0 - progress))  # Fades out
                
                # Get and scale the attack effect
                attack_effect = assets["attack_effect"]
                scaled_effect = pygame.transform.scale(
                    attack_effect, 
                    (int(attack_effect.get_width() * scale), int(attack_effect.get_height() * scale))
                )
                
                # Set alpha
                scaled_effect.set_alpha(alpha)
                
                # Apply rotation animation
                angle = progress * 80  # Rotate up to 80 degrees
                rotated_effect = pygame.transform.rotate(scaled_effect, angle)
                
                # Draw the effect centered on attack point
                effect_rect = rotated_effect.get_rect(center=(screen_x, screen_y))
                surface.blit(rotated_effect, effect_rect)
        
        # Draw damage numbers
        for damage_number in self.damage_numbers:
            damage_number.draw(surface, camera_x, camera_y)

# Generate a fixed map based on a seed
class GameMap:
    def __init__(self, width=MAP_WIDTH, height=MAP_HEIGHT, seed=12345):
        self.width = width
        self.height = height
        self.tile_size = TILE_SIZE
        self.tiles = []
        self.seed = seed
        self.generate_map()
        
    def generate_map(self):
        # Set the random seed for consistent generation
        random.seed(self.seed)
        
        # Initialize with grass
        self.tiles = [["grass" for _ in range(self.width)] for _ in range(self.height)]
        
        # Add fewer trees in a more structured pattern
        # Create a central clearing with trees around the edges
        
        # Forest edges - much fewer trees
        for y in range(self.height):
            for x in range(self.width):
                # Keep the center completely clear to ensure safe spawning
                distance_to_center = ((x - self.width//2)**2 + (y - self.height//2)**2)**0.5
                
                # Create fewer trees in the outer areas
                if distance_to_center > 20 and random.random() < 0.2:  # Reduced from 0.6 to 0.2
                    self.tiles[y][x] = "tree"
                
                # Create very scattered trees in the mid-range
                elif 10 < distance_to_center <= 20 and random.random() < 0.08:  # Reduced from 0.05
                    self.tiles[y][x] = "tree"
                    
                # Create a few decorative tree clusters
                elif self.is_in_tree_cluster(x, y):
                    self.tiles[y][x] = "tree"
    
    def is_in_tree_cluster(self, x, y):
        # Define smaller tree cluster centers (decorative)
        clusters = [
            (self.width//5, self.height//5),
            (4*self.width//5, self.height//5),
            (self.width//5, 4*self.height//5),
            (4*self.width//5, 4*self.height//5)
        ]
        
        # Check if within any cluster radius - smaller clusters
        for cx, cy in clusters:
            dist = ((x - cx)**2 + (y - cy)**2)**0.5
            if dist < 2 and random.random() < 0.7:  # Smaller clusters
                return True
        return False
        
    def set_seed(self, seed):
        self.seed = seed
        self.generate_map()
    
    def draw(self, surface, camera_x, camera_y, assets):
        # Calculate visible area
        start_x = max(0, camera_x // TILE_SIZE)
        end_x = min(self.width, (camera_x + SCREEN_WIDTH) // TILE_SIZE + 1)
        start_y = max(0, camera_y // TILE_SIZE)
        end_y = min(self.height, (camera_y + SCREEN_HEIGHT) // TILE_SIZE + 1)
        
        # Draw visible tiles
        for y in range(start_y, end_y):
            for x in range(start_x, end_x):
                tile_type = self.tiles[y][x]
                tile_asset = assets[tile_type]
                screen_x = x * TILE_SIZE - camera_x
                screen_y = y * TILE_SIZE - camera_y
                surface.blit(tile_asset, (screen_x, screen_y))
                
    def is_valid_position(self, x, y):
        # Check map boundaries
        if x < 0 or y < 0 or x >= self.width * TILE_SIZE or y >= self.height * TILE_SIZE:
            return False
            
        # Get tile coordinates
        tile_x = int(x // TILE_SIZE)
        tile_y = int(y // TILE_SIZE)
        
        # Check if tile is traversable (not a tree)
        if tile_x >= self.width or tile_y >= self.height:
            return False
            
        tile_type = self.tiles[tile_y][tile_x]
        return tile_type != "tree"

class Camera:
    def __init__(self):
        self.x = 0
        self.y = 0
        
    def update(self, target_x, target_y):
        # Center camera on target
        self.x = target_x - SCREEN_WIDTH // 2
        self.y = target_y - SCREEN_HEIGHT // 2
        
        # Keep camera within map bounds
        self.x = max(0, min(self.x, TILE_SIZE * MAP_WIDTH - SCREEN_WIDTH))
        self.y = max(0, min(self.y, TILE_SIZE * MAP_HEIGHT - SCREEN_HEIGHT))

class Button:
    def __init__(self, x, y, width, height, text, color=PRIMARY_COLOR, hover_color=SECONDARY_COLOR):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.is_hovered = False
        
    def draw(self, surface):
        color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(surface, color, self.rect, border_radius=8)
        
        text_surf = font.render(self.text, True, BUTTON_TEXT_COLOR)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)
        
    def update(self, mouse_pos):
        self.is_hovered = self.rect.collidepoint(mouse_pos)
        
    def is_clicked(self, mouse_pos, mouse_click):
        return self.rect.collidepoint(mouse_pos) and mouse_click

class InputBox:
    def __init__(self, x, y, width, height, text='', placeholder='', is_password=False):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.placeholder = placeholder
        self.is_password = is_password
        self.active = False
        self.color = BORDER_COLOR
        self.active_color = PRIMARY_COLOR
        self.bg_color = BOX_BACKGROUND
        self.error = False
        
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Toggle active state
            self.active = self.rect.collidepoint(event.pos)
            self.error = False  # Clear error state when clicking
            
        if event.type == pygame.KEYDOWN:
            if self.active:
                if event.key == pygame.K_RETURN:
                    return True
                elif event.key == pygame.K_BACKSPACE:
                    self.text = self.text[:-1]
                    self.error = False  # Clear error state when editing
                else:
                    # Only accept alphanumeric characters
                    if event.unicode.isalnum() or event.unicode == '_':
                        self.text += event.unicode
                        self.error = False  # Clear error state when editing
        return False
                
    def draw(self, surface):
        # Draw the input box with a shadow effect
        shadow_rect = pygame.Rect(self.rect.x, self.rect.y + 2, self.rect.width, self.rect.height)
        pygame.draw.rect(surface, (0, 0, 0, 30), shadow_rect, border_radius=8)
        
        # Draw the input box background
        pygame.draw.rect(surface, self.bg_color, self.rect, border_radius=8)
        
        # Draw border - red if error, active color if active, else normal color
        if self.error:
            border_color = ERROR_COLOR
        else:
            border_color = self.active_color if self.active else self.color
        
        pygame.draw.rect(surface, border_color, self.rect, 2, border_radius=8)
        
        # Render text or placeholder
        if self.text:
            if self.is_password:
                # Show asterisks for password
                display_text = '•' * len(self.text)
            else:
                display_text = self.text
            text_surf = font.render(display_text, True, TEXT_COLOR)
        else:
            text_surf = font.render(self.placeholder, True, PLACEHOLDER_COLOR)
            
        # Position text
        text_rect = text_surf.get_rect(midleft=(self.rect.left + 10, self.rect.centery))
        
        # Blit to screen
        surface.blit(text_surf, text_rect)
        
    def set_error(self, has_error=True):
        self.error = has_error

class NetworkClient:
    def __init__(self, host='localhost', port=5555):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.player_id = None
        self.other_players = {}
        self.connected = False
        self.receive_thread = None
        
        # Initialize spawn position
        self.spawn_x = 500
        self.spawn_y = 500
        
        # Map data
        self.map_seed = 12345
        
    def connect(self):
        try:
            self.socket.connect((self.host, self.port))
            self.connected = True
            # Start receiving thread
            self.receive_thread = threading.Thread(target=self.receive_data_thread)
            self.receive_thread.daemon = True
            self.receive_thread.start()
            return True
        except Exception as e:
            print(f"Connection error: {e}")
            return False
        
    def register(self, username, password):
        if not self.connected:
            return (False, "Not connected to server")
        
        data = {
            "type": "register",
            "username": username,
            "password": password
        }
        self.send_data(data)
        
        # The response will be handled in the receive_data_thread
    
    def login(self, username, password):
        if not self.connected:
            return (False, "Not connected to server")
            
        data = {
            "type": "login",
            "username": username,
            "password": password
        }
        self.send_data(data)
        
        # The response will be handled in the receive_data_thread
    
    def send_attack(self):
        if self.connected and self.player_id is not None:
            self.send_data({
                "type": "attack"
            })
    
    def send_data(self, data):
        try:
            # Convert data to JSON string
            message = json.dumps(data).encode('utf-8')
            # Send message length first (4 bytes)
            message_length = len(message).to_bytes(4, byteorder='big')
            self.socket.send(message_length + message)
        except Exception as e:
            print(f"Error sending data: {e}")
            self.connected = False
    
    def receive_data(self):
        try:
            # Receive message length (4 bytes)
            message_length_bytes = self.socket.recv(4)
            if not message_length_bytes:
                return None
                
            message_length = int.from_bytes(message_length_bytes, byteorder='big')
            
            # Receive the actual message
            message = b""
            bytes_received = 0
            
            while bytes_received < message_length:
                chunk = self.socket.recv(min(message_length - bytes_received, 4096))
                if not chunk:
                    return None
                message += chunk
                bytes_received += len(chunk)
                
            return json.loads(message.decode('utf-8'))
        except Exception as e:
            print(f"Error receiving data: {e}")
            self.connected = False
            return None
    
    def receive_data_thread(self):
        while self.connected:
            data = self.receive_data()
            if not data:
                self.connected = False
                break
                
            # Handle different types of messages
            if data.get("type") == "player_id":
                self.player_id = data.get("id")
                
                # Get spawn position from server
                self.spawn_x = data.get("x", self.spawn_x)
                self.spawn_y = data.get("y", self.spawn_y)
                
                print(f"Assigned player ID: {self.player_id} at position ({self.spawn_x}, {self.spawn_y})")
                
            elif data.get("type") == "game_state":
                self.other_players = data.get("players", {})
                
            elif data.get("type") == "register_result":
                print(f"Registration result: {data.get('message')}")
                # Store the result for the UI to use
                self.last_register_result = data
                
            elif data.get("type") == "login_result":
                print(f"Login result: {data.get('message')}")
                # Store the result for the UI to use
                self.last_login_result = data
                
            elif data.get("type") == "map_data":
                # Update map seed
                self.map_seed = data.get("seed", 12345)
                print(f"Received map seed: {self.map_seed}")
                
            elif data.get("type") == "attack_event":
                # Store attack event for rendering
                self.last_attack_event = data
                
                # Get damage amount
                damage = data.get("damage", 0)
                
                # Process respawn if needed
                if data.get("target_id") == self.player_id and data.get("killed", False):
                    self.spawn_x = data.get("respawn_x", self.spawn_x)
                    self.spawn_y = data.get("respawn_y", self.spawn_y)
                
                # Play sound effect
                if hasattr(self, "play_sound") and callable(self.play_sound):
                    if data.get("attacker_id") == self.player_id:
                        self.play_sound("sound_attack")
                    elif data.get("target_id") == self.player_id:
                        self.play_sound("sound_hit")
                
                # Add to animation queue and damage display
                if hasattr(self, "animation_callback") and callable(self.animation_callback):
                    attacker_id = data.get("attacker_id")
                    target_id = data.get("target_id")
                    
                    # Show attack animation from attacker
                    if str(attacker_id) in self.other_players:
                        attacker = self.other_players[str(attacker_id)]
                        attack_x = attacker.get("x", 0) + 15  # Center of player
                        attack_y = attacker.get("y", 0) + 20
                        self.animation_callback("attack", attack_x, attack_y)
                    
                    # Show damage number at target
                    if str(target_id) in self.other_players:
                        target = self.other_players[str(target_id)]
                        damage_x = target.get("x", 0) + 15  # Center of player
                        damage_y = target.get("y", 0) - 10   # Above the player
                        self.animation_callback("damage", damage_x, damage_y, damage)
    
    def disconnect(self):
        self.connected = False
        self.socket.close()
        
    def register_animation_callback(self, callback):
        self.animation_callback = callback
        
    def register_sound_callback(self, callback):
        self.play_sound = callback

class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 30
        self.height = 40
        self.color = RED
        self.speed = PLAYER_SPEED
        self.direction = 1  # 1: right, -1: left
        self.last_movement_time = 0
        self.health = MAX_HEALTH
        self.max_health = MAX_HEALTH
        self.last_attack_time = 0
        
    def update(self, game_map):
        prev_x, prev_y = self.x, self.y
        
        # Handle movement input
        moved = self.handle_input()
        
        # Ensure we're not stuck in obstacles
        if not game_map.is_valid_position(self.x + self.width // 2, self.y + self.height // 2):
            # Try to find a valid position nearby
            for dx, dy in [(0, 0), (-5, 0), (5, 0), (0, -5), (0, 5)]:
                test_x = prev_x + dx
                test_y = prev_y + dy
                if game_map.is_valid_position(test_x + self.width // 2, test_y + self.height // 2):
                    self.x, self.y = test_x, test_y
                    break
            else:
                # If no valid position found, go back to previous position
                self.x, self.y = prev_x, prev_y
        
    def draw(self, surface, camera_x, camera_y, assets):
        screen_x = self.x - camera_x
        screen_y = self.y - camera_y
        
        # Flip sprite based on direction
        sprite = assets["player_base"]
        if self.direction < 0:
            sprite = pygame.transform.flip(sprite, True, False)
            
        surface.blit(sprite, (screen_x, screen_y))
        
        # Draw health bar
        self.draw_health_bar(surface, screen_x, screen_y)
        
    def draw_health_bar(self, surface, screen_x, screen_y):
        # Health bar position above player
        bar_width = 30
        bar_height = 5
        bar_x = screen_x
        bar_y = screen_y - 10
        
        # Draw background
        pygame.draw.rect(surface, HEALTH_BAR_BG, (bar_x, bar_y, bar_width, bar_height))
        
        # Calculate health percentage
        health_percent = self.health / self.max_health
        health_width = int(bar_width * health_percent)
        
        # Determine color based on health
        if health_percent > 0.6:
            health_color = HEALTH_COLOR
        elif health_percent > 0.3:
            health_color = (220, 220, 0)  # Yellow
        else:
            health_color = LOW_HEALTH_COLOR
            
        # Draw health bar
        if health_width > 0:
            pygame.draw.rect(surface, health_color, (bar_x, bar_y, health_width, bar_height))
            
        # Draw border
        pygame.draw.rect(surface, HEALTH_BAR_BORDER, (bar_x, bar_y, bar_width, bar_height), 1)
        
    def handle_input(self):
        # Throttle movement updates slightly to avoid network spam
        current_time = pygame.time.get_ticks()
        if current_time - self.last_movement_time < 16:  # ~60 FPS
            return False
            
        keys = pygame.key.get_pressed()
        moved = False
        
        # Store original position
        original_x, original_y = self.x, self.y
        
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.x -= self.speed
            self.direction = -1
            moved = True
            
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.x += self.speed
            self.direction = 1
            moved = True
            
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.y -= self.speed
            moved = True
            
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.y += self.speed
            moved = True
            
        # Keep player within map bounds
        self.x = max(0, min(self.x, MAP_WIDTH * TILE_SIZE - self.width))
        self.y = max(0, min(self.y, MAP_HEIGHT * TILE_SIZE - self.height))
        
        # Update movement time if we moved
        if moved:
            self.last_movement_time = current_time
            
        return moved
    
    def can_attack(self):
        current_time = time.time()
        return current_time - self.last_attack_time >= ATTACK_COOLDOWN
        
    def attack(self):
        if self.can_attack():
            self.last_attack_time = time.time()
            return True
        return False
        
class GameState:
    LOGIN = 0
    REGISTER = 1
    PLAYING = 2
    
class LoginUI:
    def __init__(self, network_client):
        self.network_client = network_client
        self.state = GameState.LOGIN
        self.message = ""
        self.message_color = TEXT_COLOR
        
        # Center coordinates for UI elements
        self.center_x = SCREEN_WIDTH // 2
        self.start_y = SCREEN_HEIGHT // 3
        
        # Login UI elements
        self.username_box = InputBox(self.center_x - INPUT_BOX_WIDTH//2, self.start_y, 
                                    INPUT_BOX_WIDTH, INPUT_BOX_HEIGHT, 
                                    placeholder="Username")
        
        self.password_box = InputBox(self.center_x - INPUT_BOX_WIDTH//2, self.start_y + INPUT_BOX_HEIGHT + PADDING, 
                                    INPUT_BOX_WIDTH, INPUT_BOX_HEIGHT, 
                                    placeholder="Password", is_password=True)
        
        # Increase spacing between buttons
        button_y = self.start_y + 2 * (INPUT_BOX_HEIGHT + PADDING) + 10
        self.login_button = Button(self.center_x - BUTTON_WIDTH - PADDING, button_y,
                                  BUTTON_WIDTH, BUTTON_HEIGHT, "Login")
        
        self.register_button = Button(self.center_x + PADDING, button_y,
                                     BUTTON_WIDTH, BUTTON_HEIGHT, "Register", 
                                     color=SECONDARY_COLOR, hover_color=ACCENT_COLOR)
        
        # Register UI elements
        self.reg_username_box = InputBox(self.center_x - INPUT_BOX_WIDTH//2, self.start_y, 
                                       INPUT_BOX_WIDTH, INPUT_BOX_HEIGHT, 
                                       placeholder="Username")
        
        self.reg_password_box = InputBox(self.center_x - INPUT_BOX_WIDTH//2, self.start_y + INPUT_BOX_HEIGHT + PADDING, 
                                       INPUT_BOX_WIDTH, INPUT_BOX_HEIGHT, 
                                       placeholder="Password", is_password=True)
        
        self.confirm_password_box = InputBox(self.center_x - INPUT_BOX_WIDTH//2, self.start_y + 2 * (INPUT_BOX_HEIGHT + PADDING), 
                                           INPUT_BOX_WIDTH, INPUT_BOX_HEIGHT, 
                                           placeholder="Confirm Password", is_password=True)
        
        button_y = self.start_y + 3 * (INPUT_BOX_HEIGHT + PADDING) + 10
        self.create_account_button = Button(self.center_x - BUTTON_WIDTH - PADDING//2, button_y,
                                          BUTTON_WIDTH, BUTTON_HEIGHT, "Create Account")
        
        self.back_button = Button(self.center_x + PADDING//2, button_y,
                                BUTTON_WIDTH, BUTTON_HEIGHT, "Back",
                                color=DARK_GRAY, hover_color=(120, 120, 120))
    
    def handle_events(self, events):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                
                if self.state == GameState.LOGIN:
                    if self.login_button.is_clicked(mouse_pos, True):
                        self.attempt_login()
                    elif self.register_button.is_clicked(mouse_pos, True):
                        self.state = GameState.REGISTER
                        self.message = ""
                
                elif self.state == GameState.REGISTER:
                    if self.create_account_button.is_clicked(mouse_pos, True):
                        self.attempt_register()
                    elif self.back_button.is_clicked(mouse_pos, True):
                        self.state = GameState.LOGIN
                        self.message = ""
            
            # Handle input box events
            if self.state == GameState.LOGIN:
                self.username_box.handle_event(event)
                enter_pressed = self.password_box.handle_event(event)
                if enter_pressed:
                    self.attempt_login()
            
            elif self.state == GameState.REGISTER:
                self.reg_username_box.handle_event(event)
                self.reg_password_box.handle_event(event)
                enter_pressed = self.confirm_password_box.handle_event(event)
                if enter_pressed:
                    self.attempt_register()
    
    def attempt_login(self):
        username = self.username_box.text.strip()
        password = self.password_box.text
        
        if not username:
            self.username_box.set_error(True)
            self.message = "Please enter your username"
            self.message_color = ERROR_COLOR
            return
            
        if not password:
            self.password_box.set_error(True)
            self.message = "Please enter your password"
            self.message_color = ERROR_COLOR
            return
            
        if not username.isalnum() and '_' not in username:
            self.username_box.set_error(True)
            self.message = "Username must be alphanumeric"
            self.message_color = ERROR_COLOR
            return
        
        # Send login request to server
        self.network_client.login(username, password)
        self.message = "Logging in..."
        self.message_color = ACCENT_COLOR
    
    def attempt_register(self):
        username = self.reg_username_box.text.strip()
        password = self.reg_password_box.text
        confirm = self.confirm_password_box.text
        
        validation_passed = True
        
        if not username:
            self.reg_username_box.set_error(True)
            self.message = "Please enter a username"
            self.message_color = ERROR_COLOR
            validation_passed = False
            
        elif len(username) < 3:
            self.reg_username_box.set_error(True)
            self.message = "Username must be at least 3 characters"
            self.message_color = ERROR_COLOR
            validation_passed = False
            
        elif not username.isalnum() and '_' not in username:
            self.reg_username_box.set_error(True)
            self.message = "Username must be alphanumeric (letters, numbers, _)"
            self.message_color = ERROR_COLOR
            validation_passed = False
            
        if not password:
            self.reg_password_box.set_error(True)
            self.message = "Please enter a password"
            self.message_color = ERROR_COLOR
            validation_passed = False
            
        elif len(password) < 4:
            self.reg_password_box.set_error(True)
            self.message = "Password must be at least 4 characters"
            self.message_color = ERROR_COLOR
            validation_passed = False
            
        elif not all(c.isalnum() or c == '_' for c in password):
            self.reg_password_box.set_error(True)
            self.message = "Password must be alphanumeric (letters, numbers, _)"
            self.message_color = ERROR_COLOR
            validation_passed = False
            
        if password != confirm:
            self.confirm_password_box.set_error(True)
            self.message = "Passwords do not match"
            self.message_color = ERROR_COLOR
            validation_passed = False
            
        if not validation_passed:
            return
        
        # Send registration request to server
        self.network_client.register(username, password)
        self.message = "Creating account..."
        self.message_color = ACCENT_COLOR
    
    def update(self, mouse_pos):
        # Update button hover states
        if self.state == GameState.LOGIN:
            self.login_button.update(mouse_pos)
            self.register_button.update(mouse_pos)
        elif self.state == GameState.REGISTER:
            self.create_account_button.update(mouse_pos)
            self.back_button.update(mouse_pos)
        
        # Check for server responses
        if hasattr(self.network_client, 'last_login_result'):
            result = self.network_client.last_login_result
            
            if result.get('success'):
                self.state = GameState.PLAYING
            else:
                self.message = result.get('message', 'Login failed')
                self.message_color = ERROR_COLOR
            
            # Clear the result so we don't process it again
            delattr(self.network_client, 'last_login_result')
        
        if hasattr(self.network_client, 'last_register_result'):
            result = self.network_client.last_register_result
            
            if result.get('success'):
                self.message = "Registration successful! You can now log in."
                self.message_color = SUCCESS_COLOR
                self.state = GameState.LOGIN
                # Clear registration fields
                self.reg_username_box.text = ""
                self.reg_password_box.text = ""
                self.confirm_password_box.text = ""
            else:
                self.message = result.get('message', 'Registration failed')
                self.message_color = ERROR_COLOR
            
            # Clear the result so we don't process it again
            delattr(self.network_client, 'last_register_result')
    
    def draw(self, surface):
        # Draw background with gradient effect
        surface.fill(BACKGROUND_COLOR)
        
        # Draw title with shadow effect
        title_shadow = title_font.render("2D MMO Game", True, (0, 0, 0, 128))
        title_shadow_rect = title_shadow.get_rect(center=(SCREEN_WIDTH//2 + 2, SCREEN_HEIGHT//6 + 2))
        surface.blit(title_shadow, title_shadow_rect)
        
        title_text = title_font.render("2D MMO Game", True, PRIMARY_COLOR)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//6))
        surface.blit(title_text, title_rect)
        
        # Draw message
        if self.message:
            msg_text = small_font.render(self.message, True, self.message_color)
            msg_rect = msg_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT - 80))
            surface.blit(msg_text, msg_rect)
        
        if self.state == GameState.LOGIN:
            # Draw form container with shadow
            form_rect = pygame.Rect(self.center_x - (INPUT_BOX_WIDTH + 40)//2, self.start_y - 30, INPUT_BOX_WIDTH + 40, 3 * INPUT_BOX_HEIGHT + 2 * PADDING + BUTTON_HEIGHT + 60)
            shadow_rect = pygame.Rect(form_rect.x + 5, form_rect.y + 5, form_rect.width, form_rect.height)
            pygame.draw.rect(surface, (0, 0, 0, 20), shadow_rect, border_radius=12)
            pygame.draw.rect(surface, BOX_BACKGROUND, form_rect, border_radius=12)
            pygame.draw.rect(surface, BORDER_COLOR, form_rect, 1, border_radius=12)
            
            # Draw form title
            form_title = font.render("Login to Your Account", True, TEXT_COLOR)
            form_title_rect = form_title.get_rect(center=(SCREEN_WIDTH//2, self.start_y - 10))
            surface.blit(form_title, form_title_rect)
            
            # Draw form elements
            self.username_box.draw(surface)
            self.password_box.draw(surface)
            self.login_button.draw(surface)
            self.register_button.draw(surface)
            
            # Draw helper text below the buttons instead of between them
            helper_text = tiny_font.render("Need an account? Register here →", True, PLACEHOLDER_COLOR)
            helper_rect = helper_text.get_rect(right=self.register_button.rect.right, top=self.register_button.rect.bottom + 10)
            surface.blit(helper_text, helper_rect)
            
        elif self.state == GameState.REGISTER:
            # Draw form container with shadow
            form_rect = pygame.Rect(self.center_x - (INPUT_BOX_WIDTH + 40)//2, self.start_y - 30, INPUT_BOX_WIDTH + 40, 4 * INPUT_BOX_HEIGHT + 3 * PADDING + BUTTON_HEIGHT + 60)
            shadow_rect = pygame.Rect(form_rect.x + 5, form_rect.y + 5, form_rect.width, form_rect.height)
            pygame.draw.rect(surface, (0, 0, 0, 20), shadow_rect, border_radius=12)
            pygame.draw.rect(surface, BOX_BACKGROUND, form_rect, border_radius=12)
            pygame.draw.rect(surface, BORDER_COLOR, form_rect, 1, border_radius=12)
            
            # Draw form title
            form_title = font.render("Create New Account", True, TEXT_COLOR)
            form_title_rect = form_title.get_rect(center=(SCREEN_WIDTH//2, self.start_y - 10))
            surface.blit(form_title, form_title_rect)
            
            # Draw form elements
            self.reg_username_box.draw(surface)
            self.reg_password_box.draw(surface)
            self.confirm_password_box.draw(surface)
            self.create_account_button.draw(surface)
            self.back_button.draw(surface)
            
            # Draw requirements text
            req_text = tiny_font.render("Usernames and passwords must be alphanumeric", True, PLACEHOLDER_COLOR)
            req_rect = req_text.get_rect(center=(SCREEN_WIDTH//2, self.back_button.rect.bottom + 15))
            surface.blit(req_text, req_rect)

def draw_other_players(surface, other_players, my_id, camera_x, camera_y, assets):
    for player_id, player_data in other_players.items():
        # Convert player_id to integer for comparison
        try:
            player_id = int(player_id)
            if player_id != my_id:
                # Extract player position
                player_x = player_data["x"]
                player_y = player_data["y"]
                
                # Draw player sprite
                screen_x = player_x - camera_x
                screen_y = player_y - camera_y
                
                # Only draw if player is on screen
                if -30 <= screen_x <= SCREEN_WIDTH and -40 <= screen_y <= SCREEN_HEIGHT:
                    # Use the player base sprite for all players
                    sprite = assets["player_base"]
                    
                    # Add custom color for player
                    colored_sprite = sprite.copy()
                    
                    # Get player color or use default blue
                    color = player_data.get("color", BLUE)
                    if isinstance(color, list):
                        color = tuple(color)
                        
                    # Apply color to the clothes part of the sprite
                    # This is a simple approach - in a real game, you'd use separate layers
                    pixels = pygame.PixelArray(colored_sprite)
                    for x in range(colored_sprite.get_width()):
                        for y in range(colored_sprite.get_height()):
                            # Check if pixel is blue (the default clothing color)
                            if colored_sprite.get_at((x, y))[0:3] == (70, 70, 180):
                                pixels[x, y] = color
                    del pixels
                    
                    surface.blit(colored_sprite, (screen_x, screen_y))
                    
                    # Draw username if available
                    if "username" in player_data:
                        name_text = small_font.render(player_data["username"], True, BLACK)
                        name_rect = name_text.get_rect(centerx=screen_x + 15, bottom=screen_y - 5)
                        # Draw with shadow for better visibility
                        shadow_text = small_font.render(player_data["username"], True, (0, 0, 0))
                        surface.blit(shadow_text, (name_rect.x + 1, name_rect.y + 1))
                        surface.blit(name_text, name_rect)
                    
                    # Draw health bar
                    # Health bar position above player
                    health = player_data.get("health", MAX_HEALTH)
                    max_health = player_data.get("max_health", MAX_HEALTH)
                    
                    bar_width = 30
                    bar_height = 5
                    bar_x = screen_x
                    bar_y = screen_y - 10
                    
                    # Draw background
                    pygame.draw.rect(surface, HEALTH_BAR_BG, (bar_x, bar_y, bar_width, bar_height))
                    
                    # Calculate health percentage
                    health_percent = health / max_health
                    health_width = int(bar_width * health_percent)
                    
                    # Determine color based on health
                    if health_percent > 0.6:
                        health_color = HEALTH_COLOR
                    elif health_percent > 0.3:
                        health_color = (220, 220, 0)  # Yellow
                    else:
                        health_color = LOW_HEALTH_COLOR
                        
                    # Draw health bar
                    if health_width > 0:
                        pygame.draw.rect(surface, health_color, (bar_x, bar_y, health_width, bar_height))
                    
                    # Draw border
                    pygame.draw.rect(surface, HEALTH_BAR_BORDER, (bar_x, bar_y, bar_width, bar_height), 1)
        except:
            pass  # Skip invalid player data

def draw_attack_range(surface, player, camera_x, camera_y, color=(255, 200, 200, 80)):
    # Draw a circle showing attack range
    center_x = player.x + player.width//2 - camera_x
    center_y = player.y + player.height//2 - camera_y
    
    # Create a surface for the attack range circle
    circle_surf = pygame.Surface((ATTACK_RANGE*2, ATTACK_RANGE*2), pygame.SRCALPHA)
    pygame.draw.circle(circle_surf, color, (ATTACK_RANGE, ATTACK_RANGE), ATTACK_RANGE)
    
    # Draw the attack indicator
    surface.blit(circle_surf, (center_x - ATTACK_RANGE, center_y - ATTACK_RANGE))

def draw_hud(surface, player):
    # Draw attack cooldown indicator
    cooldown_remaining = max(0, ATTACK_COOLDOWN - (time.time() - player.last_attack_time))
    cooldown_percent = min(1.0, cooldown_remaining / ATTACK_COOLDOWN)
    
    # Draw cooldown bar
    if cooldown_percent > 0:
        bar_width = 150
        bar_height = 15
        bar_x = 10
        bar_y = SCREEN_HEIGHT - 30
        
        # Draw background
        pygame.draw.rect(surface, DARK_GRAY, (bar_x, bar_y, bar_width, bar_height))
        
        # Draw remaining cooldown
        remaining_width = int(bar_width * cooldown_percent)
        if remaining_width > 0:
            pygame.draw.rect(surface, (200, 50, 50), (bar_x, bar_y, remaining_width, bar_height))
        
        # Draw border
        pygame.draw.rect(surface, BLACK, (bar_x, bar_y, bar_width, bar_height), 1)
        
        # Draw text
        text = small_font.render("Attack Cooldown", True, WHITE)
        surface.blit(text, (bar_x + 5, bar_y - 20))
    else:
        # Draw "Ready" text
        text = small_font.render("Attack Ready! (Left Click to Attack)", True, GREEN)
        surface.blit(text, (10, SCREEN_HEIGHT - 30))

def main():
    # Make sure data directory exists for sounds
    os.makedirs("data", exist_ok=True)
    
    # Create placeholder sound files if they don't exist
    create_placeholder_sounds()
    
    # Create game assets
    assets = create_game_assets()
    
    # Create animation manager
    animation_manager = AnimationManager()
    
    # Create game map
    game_map = GameMap()
    
    # Create camera
    camera = Camera()
    
    # Create network client
    network_client = NetworkClient()
    if not network_client.connect():
        print("Could not connect to server")
        return
        
    # Register animation callback
    def animation_handler(anim_type, x, y, amount=None):
        if anim_type == "attack":
            animation_manager.add_attack_animation(x, y)
        elif anim_type == "damage":
            animation_manager.add_damage_number(x, y, amount)
    
    network_client.register_animation_callback(animation_handler)
    
    # Register sound callback
    def sound_handler(sound_name):
        if sound_name in assets:
            assets[sound_name].play()
    
    network_client.register_sound_callback(sound_handler)
    
    # Create login UI
    login_ui = LoginUI(network_client)
    
    # Create player (when logged in)
    player = None
    
    # Main game loop
    running = True
    while running:
        # Handle events
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and login_ui.state == GameState.PLAYING:
                if event.button == 1:  # Left mouse button
                    # Try to attack
                    if player and player.can_attack():
                        if network_client.send_attack():
                            # Attack animation will be triggered by server response
                            player.attack()
                
        # Get mouse position for UI updates
        mouse_pos = pygame.mouse.get_pos()
        
        # Update game state
        if login_ui.state == GameState.PLAYING:
            # Update map seed if received from server
            if game_map.seed != network_client.map_seed:
                game_map.set_seed(network_client.map_seed)
            
            # If we've just entered the playing state, create the player
            if player is None:
                # Use spawn position from server
                player = Player(network_client.spawn_x, network_client.spawn_y)
                
            # Update player
            player.update(game_map)
            
            # Update animations
            animation_manager.update()
            
            # Update player health from server data
            if network_client.player_id and str(network_client.player_id) in network_client.other_players:
                player_data = network_client.other_players[str(network_client.player_id)]
                player.health = player_data.get("health", player.health)
                
                # Check if we've been killed and need to respawn
                if hasattr(network_client, 'last_attack_event'):
                    event = network_client.last_attack_event
                    if (event.get('target_id') == network_client.player_id and 
                        event.get('killed', False)):
                        player.x = network_client.spawn_x
                        player.y = network_client.spawn_y
                        player.health = MAX_HEALTH
                        # Clear the event so we don't respawn again
                        delattr(network_client, 'last_attack_event')
            
            # Update camera
            camera.update(player.x, player.y)
            
            # Send player position to server
            if network_client.connected and network_client.player_id is not None:
                network_client.send_data({
                    "x": player.x,
                    "y": player.y
                })
                
            # Draw game
            screen.fill(WHITE)
            
            # Draw map
            game_map.draw(screen, camera.x, camera.y, assets)
            
            # Draw attack range when ready
            if player.can_attack():
                draw_attack_range(screen, player, camera.x, camera.y)
            
            # Draw other players
            if network_client.player_id:
                draw_other_players(screen, network_client.other_players, network_client.player_id, camera.x, camera.y, assets)
                
            # Draw animations
            animation_manager.draw(screen, camera.x, camera.y, assets)
                
            # Draw player
            player.draw(screen, camera.x, camera.y, assets)
            
            # Draw HUD
            draw_hud(screen, player)
            
        else:
            # Handle login/register UI
            login_ui.handle_events(events)
            login_ui.update(mouse_pos)
            login_ui.draw(screen)
        
        # Update display
        pygame.display.flip()
        clock.tick(60)
    
    # Clean up
    if network_client.connected:
        network_client.disconnect()
    pygame.quit()
    sys.exit()

def create_placeholder_sounds():
    """Create basic placeholder sound files if they don't exist"""
    if not os.path.exists("data/attack.wav"):
        create_basic_sound("data/attack.wav", "attack")
    if not os.path.exists("data/hit.wav"):
        create_basic_sound("data/hit.wav", "hit")

def create_basic_sound(filename, sound_type):
    """Create a basic sound file for testing"""
    try:
        import numpy as np
        from scipy.io import wavfile
        
        # Sample rate
        sample_rate = 22050
        
        # Generate different sounds based on type
        if sound_type == "attack":
            # Create a quick swoosh sound
            t = np.linspace(0, 0.2, int(0.2 * sample_rate), False)
            frequency = np.linspace(800, 300, len(t))
            tone = 0.5 * np.sin(2 * np.pi * frequency * t)
            
            # Apply envelope
            envelope = np.exp(-5 * t)
            waveform = (tone * envelope * 32767).astype(np.int16)
            
        elif sound_type == "hit":
            # Create a hit/impact sound
            t = np.linspace(0, 0.3, int(0.3 * sample_rate), False)
            tone1 = np.sin(2 * np.pi * 200 * t) * 0.7
            tone2 = np.sin(2 * np.pi * 600 * t) * 0.3
            noise = np.random.uniform(-0.2, 0.2, len(t))
            
            # Combine tones and apply envelope
            combined = tone1 + tone2 + noise
            envelope = np.exp(-10 * t)
            waveform = (combined * envelope * 32767).astype(np.int16)
        else:
            # Default simple beep
            t = np.linspace(0, 0.2, int(0.2 * sample_rate), False)
            waveform = (0.5 * np.sin(2 * np.pi * 440 * t) * 32767).astype(np.int16)
        
        # Save as WAV file
        wavfile.write(filename, sample_rate, waveform)
        print(f"Created sound file: {filename}")
    except ImportError:
        print("Warning: Could not create sound files (numpy or scipy not installed)")
        # Create empty files as placeholders
        with open(filename, 'wb') as f:
            # Minimal valid WAV header
            f.write(b'RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x44\xac\x00\x00\x88\x58\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00')

if __name__ == "__main__":
    # Set a consistent random seed for testing
    random.seed(42)
    main() 