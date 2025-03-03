# 2D MMO Game

A simple 2D multiplayer online game with combat, user authentication, and a shared world.

## Features

- User registration and login system
- Real-time multiplayer gameplay
- Combat system with health and damage
- Attack animations and sound effects
- Damage number indicators
- Natural landscape with trees

## Requirements

- Python 3.6+
- Pygame
- Socket library (included in Python standard library)

## Installation

1. Clone the repository:
```
git clone https://github.com/jbdanura/game
cd 2d-mmo-game
```

2. Install the required packages:
```
pip install pygame
```

## Running the Game

1. Start the server:
```
python server.py
```

2. In a separate terminal, start the client:
```
python client.py
```

3. Register an account and log in to play.

## How to Play

- Use WASD or arrow keys to move your character
- Left-click to attack nearby players
- Attack has a 1-second cooldown
- Players respawn with full health when killed

## Project Structure

- `server.py`: Game server handling authentication, player positions, and combat
- `client.py`: Game client with UI, rendering, and player controls
- `data/`: Directory for game data (database and sound files)

## Notes

- The game uses SQLite to store user credentials
- Sound effects are generated programmatically if not found
- All players see the same map layout (synchronized via seed)

## License

This project is open source and available under the [MIT License](LICENSE). 