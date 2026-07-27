"""
Module: settings
System: engine.core
Academic Unit: N/A
Description: All global constants for the Legacy of InFest engine.
"""
import os
from pathlib import Path
from typing import Final

INTERNAL_WIDTH: int = 800
INTERNAL_HEIGHT: int = 600
TARGET_FPS: int = 60
# Window upscale factor. Applied by SDL via pygame.SCALED, not by blitting a
# pre-scaled surface — see App._draw and AUD-013 for why doing it manually
# clipped three quarters of the screen.
_raw_scale = os.environ.get("LOI_DISPLAY_SCALE", "1")
DISPLAY_SCALE: int = max(1, int(_raw_scale) if _raw_scale.isdigit() else 1)

# AUD-021: the reference-resolution auto-scale branch that used to live here was
# unreachable — it required INTERNAL_WIDTH == 320, and INTERNAL_WIDTH is 800.
# The constants are retained because asset tooling references them as the
# design resolution for legacy sprite work.
REFERENCE_WIDTH: int = 320
REFERENCE_HEIGHT: int = 224

TILE_SIZE: int = 16

_PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent.parent.parent
PROJECT_ROOT: Path = _PROJECT_ROOT
ASSETS_DIR: Path = _PROJECT_ROOT / "assets"
STAGES_DIR: Path = _PROJECT_ROOT / "src/stages"
STUDENT_TEMPLATES_DIR: Path = _PROJECT_ROOT / "student_templates"

PLAYER_MAX_HEALTH: float = 5.0
GRAVITY: float = 800.0
PLAYER_WALK_SPEED: float = 90.0
PLAYER_JUMP_FORCE: float = -380.0
PLAYER_MAX_FALL_SPEED: float = 500.0
PLAYER_COYOTE_FRAMES: int = 6
PLAYER_DASH_SPEED: float = 200.0
PLAYER_AIR_DASH_LIMIT: int = 1
PLAYER_AIR_JUMPS: int = 1
PLAYER_SHORT_ATTACK_DURATION: float = 0.15
PLAYER_LONG_ATTACK_DURATION: float = 0.4
PLAYER_COOLDOWN_SHORT: float = 0.0
PLAYER_COOLDOWN_LONG: float = 0.067
BG_COLOR: tuple[int, int, int] = (15, 15, 40)

COMBO_WINDOW: float = 0.5
# AUD-021: a tuple, not a list. As a mutable list this balance table could be
# reordered or appended to from anywhere in the process — including by a test
# that forgot to restore it — silently rebalancing combat. Indexing is
# unchanged, so no call site needed updating.
COMBO_DAMAGE_MULT: Final[tuple[float, ...]] = (1.0, 1.5, 2.0)
COMBO_MAX: int = 3

# ── Accessibility and other player preferences ─────────────────
#
# AUD-021 / AUD-036: COLORBLIND_MODE and SUBTITLES_ENABLED used to live here as
# bare mutable globals. Nothing ever wrote to them, so the colourblind filter
# read a permanently-"off" value while the options screen persisted the player's
# real choice to a config file that nothing loaded — the setting could never
# take effect. Player preferences are now owned, validated and persisted by
# src.engine.core.user_settings; read them with:
#
#     from src.engine.core import user_settings
#     mode = user_settings.get().colorblind_mode
#
# This module is for engine constants that must never change at runtime.
