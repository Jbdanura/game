import pygame
import sys

# Initialize pygame
pygame.init()

# Game constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
PLAYER_SPEED = 5

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
BROWN = (165, 42, 42)

# Create the game window
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("2D MMO Game")
clock = pygame.time.Clock()

# Map class
class Map:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.tile_size = 40
        self.tiles = self.generate_map()
        
    def generate_map(self):
        # Simple map generation
        tiles = []
        for y in range(self.height):
            row = []
            for x in range(self.width):
                # Border walls
                if (x == 0 or x == self.width - 1 or y == 0 or y == self.height - 1):
                    row.append(1)  # Wall
                # Random obstacles
                elif (x % 10 == 0 and y % 8 == 0):
                    row.append(1)  # Wall
                else:
                    row.append(0)  # Floor
            tiles.append(row)
        return tiles
    
    def draw(self, surface, camera_x, camera_y):
        # Only draw tiles that are visible on screen
        start_x = max(0, camera_x // self.tile_size)
        end_x = min(self.width, (camera_x + SCREEN_WIDTH) // self.tile_size + 1)
        start_y = max(0, camera_y // self.tile_size)
        end_y = min(self.height, (camera_y + SCREEN_HEIGHT) // self.tile_size + 1)
        
        for y in range(start_y, end_y):
            for x in range(start_x, end_x):
                # Convert map position to screen position
                rect_x = x * self.tile_size - camera_x
                rect_y = y * self.tile_size - camera_y
                
                # Draw different tiles based on type
                if self.tiles[y][x] == 0:  # Floor
                    pygame.draw.rect(surface, GREEN, (rect_x, rect_y, self.tile_size, self.tile_size))
                elif self.tiles[y][x] == 1:  # Wall
                    pygame.draw.rect(surface, BROWN, (rect_x, rect_y, self.tile_size, self.tile_size))

# Camera class
class Camera:
    def __init__(self, map_width, map_height):
        self.x = 0
        self.y = 0
        self.map_width = map_width
        self.map_height = map_height
    
    def update(self, target_x, target_y):
        # Center the camera on the target
        self.x = target_x - SCREEN_WIDTH // 2
        self.y = target_y - SCREEN_HEIGHT // 2
        
        # Keep camera within map bounds
        self.x = max(0, min(self.x, self.map_width - SCREEN_WIDTH))
        self.y = max(0, min(self.y, self.map_height - SCREEN_HEIGHT))

# Player class
class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 40
        self.height = 40
        self.color = RED
        self.velocity_x = 0
        self.velocity_y = 0
    
    def update(self, game_map):
        # Store previous position for collision resolution
        prev_x = self.x
        prev_y = self.y
        
        # Update position
        self.x += self.velocity_x
        self.y += self.velocity_y
        
        # Check for map boundaries
        if self.x < 0:
            self.x = 0
        if self.y < 0:
            self.y = 0
        if self.x > game_map.width * game_map.tile_size - self.width:
            self.x = game_map.width * game_map.tile_size - self.width
        if self.y > game_map.height * game_map.tile_size - self.height:
            self.y = game_map.height * game_map.tile_size - self.height
        
        # Check for collision with walls
        self.check_collision(game_map, prev_x, prev_y)
    
    def check_collision(self, game_map, prev_x, prev_y):
        # Get the tile positions the player is overlapping
        left_tile = int(self.x // game_map.tile_size)
        right_tile = int((self.x + self.width - 1) // game_map.tile_size)
        top_tile = int(self.y // game_map.tile_size)
        bottom_tile = int((self.y + self.height - 1) // game_map.tile_size)
        
        # Check if any of these tiles are walls
        for y in range(top_tile, bottom_tile + 1):
            for x in range(left_tile, right_tile + 1):
                if 0 <= x < game_map.width and 0 <= y < game_map.height:
                    if game_map.tiles[y][x] == 1:  # Wall
                        # Collision detected, reset position
                        self.x = prev_x
                        self.y = prev_y
                        return
    
    def draw(self, surface, camera_x, camera_y):
        # Draw player relative to camera position
        pygame.draw.rect(surface, self.color, 
                         (self.x - camera_x, self.y - camera_y, self.width, self.height))
    
    def handle_input(self):
        keys = pygame.key.get_pressed()
        
        # Reset velocity
        self.velocity_x = 0
        self.velocity_y = 0
        
        # Update velocity based on key presses
        if keys[pygame.K_LEFT]:
            self.velocity_x = -PLAYER_SPEED
        if keys[pygame.K_RIGHT]:
            self.velocity_x = PLAYER_SPEED
        if keys[pygame.K_UP]:
            self.velocity_y = -PLAYER_SPEED
        if keys[pygame.K_DOWN]:
            self.velocity_y = PLAYER_SPEED

# Create the player
player = Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)

# Create a larger map
MAP_WIDTH = 50
MAP_HEIGHT = 50
game_map = Map(MAP_WIDTH, MAP_HEIGHT)

# Create the camera
camera = Camera(MAP_WIDTH * game_map.tile_size, MAP_HEIGHT * game_map.tile_size)

# Game loop
running = True
while running:
    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    
    # Process input
    player.handle_input()
    
    # Update game state
    player.update(game_map)
    camera.update(player.x + player.width // 2, player.y + player.height // 2)
    
    # Draw everything
    screen.fill(BLACK)
    game_map.draw(screen, camera.x, camera.y)
    player.draw(screen, camera.x, camera.y)
    
    # Display player coordinates for debugging
    font = pygame.font.SysFont(None, 24)
    coords_text = font.render(f"Position: ({player.x}, {player.y})", True, WHITE)
    screen.blit(coords_text, (10, 10))
    
    pygame.display.flip()
    
    # Cap the frame rate
    clock.tick(60)

# Quit pygame
pygame.quit()
sys.exit() 