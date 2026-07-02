"""
Module: settings
System: engine.core
Academic Unit: N/A
Description: All global constants for the Legacy of InFest engine.
"""
import os
from pathlib import Path

INTERNAL_WIDTH: int = 320
INTERNAL_HEIGHT: int = 224
TARGET_FPS: int = 60
DISPLAY_SCALE: int = int(os.environ.get("LOI_DISPLAY_SCALE", "3"))
TILE_SIZE: int = 16

ASSETS_DIR: Path = Path("assets")
STAGES_DIR: Path = Path("src/stages")
STUDENT_TEMPLATES_DIR: Path = Path("student_templates")

PLAYER_MAX_HEALTH: float = 5.0
GRAVITY: float = 800.0
PLAYER_WALK_SPEED: float = 90.0
PLAYER_JUMP_FORCE: float = -380.0
PLAYER_MAX_FALL_SPEED: float = 500.0
PLAYER_COYOTE_FRAMES: int = 6
PLAYER_INVINCIBILITY_DURATION: float = 1.5
PLAYER_DASH_SPEED: float = 200.0
PLAYER_AIR_DASH_LIMIT: int = 1
PLAYER_SHORT_ATTACK_DURATION: float = 0.15
PLAYER_LONG_ATTACK_DURATION: float = 0.4
PLAYER_COOLDOWN_SHORT: float = 0.0
PLAYER_COOLDOWN_LONG: float = 0.067
BG_COLOR: tuple[int, int, int] = (15, 15, 40)
