"""
Module: settings
System: engine
Academic Unit: N/A
Description: All global constants for the Legacy of InFest engine.
Every module in the engine and framework imports these constants
rather than hardcoding values. No logic — declarations only.
"""

from pathlib import Path

# Display
INTERNAL_WIDTH: int = 320
INTERNAL_HEIGHT: int = 224
TARGET_FPS: int = 60
DISPLAY_SCALE: int = 3
TILE_SIZE: int = 16
BACKGROUND_COLOR: tuple[int, int, int] = (15, 15, 40)  # dark navy per Rule 10

# Paths
ASSETS_DIR: Path = Path("assets")
STAGES_DIR: Path = Path("src/stages")
STUDENT_TEMPLATES_DIR: Path = Path("student_templates")

# Player
PLAYER_MAX_HEALTH: float = 5.0
GRAVITY: float = 800.0
PLAYER_WALK_SPEED: float = 90.0
PLAYER_JUMP_FORCE: float = -380.0
PLAYER_MAX_FALL_SPEED: float = 500.0
PLAYER_COYOTE_FRAMES: int = 6
PLAYER_INVINCIBILITY_DURATION: float = 1.5