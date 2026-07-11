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
_raw_scale = os.environ.get("LOI_DISPLAY_SCALE", "3")
DISPLAY_SCALE: int = max(1, int(_raw_scale) if _raw_scale.isdigit() else 3)
TILE_SIZE: int = 16

_PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent.parent.parent
ASSETS_DIR: Path = _PROJECT_ROOT / "assets"
STAGES_DIR: Path = _PROJECT_ROOT / "src/stages"
STUDENT_TEMPLATES_DIR: Path = _PROJECT_ROOT / "student_templates"

PLAYER_MAX_HEALTH: float = 5.0
GRAVITY: float = 800.0
PLAYER_WALK_SPEED: float = 90.0
PLAYER_JUMP_FORCE: float = -380.0
PLAYER_MAX_FALL_SPEED: float = 500.0
PLAYER_COYOTE_FRAMES: int = 6
PLAYER_INVINCIBILITY_DURATION: float = 1.5
PLAYER_DASH_SPEED: float = 200.0
PLAYER_AIR_DASH_LIMIT: int = 1
PLAYER_AIR_JUMPS: int = 1
PLAYER_SHORT_ATTACK_DURATION: float = 0.15
PLAYER_LONG_ATTACK_DURATION: float = 0.4
PLAYER_COOLDOWN_SHORT: float = 0.0
PLAYER_COOLDOWN_LONG: float = 0.067
BG_COLOR: tuple[int, int, int] = (15, 15, 40)

COMBO_WINDOW: float = 0.5
COMBO_DAMAGE_MULT: list[float] = [1.0, 1.5, 2.0]
COMBO_MAX: int = 3

# Accessibility
COLORBLIND_MODE: str = "off"  # off, protanopia, deuteranopia, tritanopia
SUBTITLES_ENABLED: bool = False
