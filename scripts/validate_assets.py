"""
Script: validate_assets.py
Description: Validate all game assets (fonts, images, models, maps, sounds).
Exits with code 0 if all required files exist and load correctly, else 1.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Add project root to sys.path so that 'src' is importable
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import pygame

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"

REQUIRED_FONTS = ["fonts/game.ttf"]
REQUIRED_IMAGES = [
    # Title screen
    "title/logo.png",
    "title/bck1.png",
    # Splash screen
    "splash/logo.png",
    "splash/bck1.png",
    # Story backgrounds
    "story/h01.png",
    "story/h02.png",
    "story/h03.png",
    # Stage0 tileset / backgrounds
    "tilesets/tileset_stage0.png",
    "backgrounds/stage0/bg_stage0_far.png",
    "backgrounds/stage0/bg_stage0_mid.png",
    "backgrounds/stage0/bg_stage0_near.png",
    # Zone backgrounds
    "backgrounds/zone1/bg_zone1_far.png",
    "backgrounds/zone2/bg_zone2_far.png",
    "backgrounds/zone3/bg_zone3_far.png",
    # Player sprites
    "sprites/player/player_idle.png",
    "sprites/player/player_walk.png",
    "sprites/player/player_jump.png",
    "sprites/player/player_fall.png",
    "sprites/player/player_hurt.png",
    "sprites/player/player_die.png",
    "sprites/player/player_crouch.png",
    "sprites/player/player_short_attack.png",
    "sprites/player/player_long_attack.png",
    # UI
    "ui/hud_frame.png",
    "ui/heart_full.png",
    "ui/heart_empty.png",
    "ui/heart_half.png",
    "ui/heart_quarter.png",
    "ui/heart_three_quarter.png",
    "ui/heart_sparkle.png",
    "ui/menu_arrow.png",
    "ui/message_arrow.png",
    "ui/portrait_normal.png",
    "ui/portrait_hurt.png",
    "ui/portrait_critical.png",
    "ui/portrait_dead.png",
    "ui/banner_top.png",
    "ui/banner_bottom.png",
]
REQUIRED_MODELS = ["models/professor_sample.pkl"]
REQUIRED_SOUNDS = [
    # Music
    "music/bgm_title.wav",
    "music/bgm_story.wav",
    "music/bgm_splash.wav",
    "music/bgm_stage0.wav",
    "music/bgm_zone1_traverse.wav",
    "music/bgm_zone1_boss.wav",
    "music/bgm_zone2_traverse.wav",
    "music/bgm_zone2_boss.wav",
    "music/bgm_zone3_traverse.wav",
    "music/bgm_zone3_boss.wav",
    "music/bgm_paburu.wav",
    "music/bgm_final_approach.wav",
    # UI SFX
    "sfx/ui/sfx_ui_menu_move.wav",
    "sfx/ui/sfx_ui_menu_confirm.wav",
    "sfx/ui/sfx_ui_menu_cancel.wav",
    "sfx/ui/sfx_ui_stage_complete.wav",
    "sfx/ui/sfx_ui_stage_banner.wav",
    "sfx/ui/sfx_ui_game_over.wav",
    "sfx/ui/sfx_ui_checkpoint.wav",
    "sfx/ui/sfx_ui_heart_restore.wav",
    # Player SFX
    "sfx/player/sfx_player_jump.wav",
    "sfx/player/sfx_player_land.wav",
    "sfx/player/sfx_player_hurt.wav",
    "sfx/player/sfx_player_die.wav",
    "sfx/player/sfx_player_crouch.wav",
    "sfx/player/sfx_player_short_attack.wav",
    "sfx/player/sfx_player_long_attack.wav",
    "sfx/player/sfx_player_hit_connect.wav",
    # Enemies SFX
    "sfx/enemies/sfx_enemies_hit.wav",
    "sfx/enemies/sfx_enemies_die_small.wav",
    "sfx/enemies/sfx_enemies_projectile_fire.wav",
    "sfx/enemies/sfx_enemies_projectile_hit_wall.wav",
    # Boss SFX
    "sfx/bosses/sfx_bosses_venado_charge.wav",
    "sfx/bosses/sfx_bosses_venado_stomp.wav",
    "sfx/bosses/sfx_bosses_venado_vine.wav",
    "sfx/bosses/sfx_bosses_gavilan_dive.wav",
    "sfx/bosses/sfx_bosses_gavilan_mask_beam.wav",
    "sfx/bosses/sfx_bosses_paburu_eye_beam.wav",
    "sfx/bosses/sfx_bosses_paburu_wave.wav",
    "sfx/bosses/sfx_bosses_phase_change.wav",
    "sfx/bosses/sfx_bosses_relic_appear.wav",
    "sfx/bosses/sfx_bosses_rey_spit.wav",
    "sfx/bosses/sfx_bosses_rey_split.wav",
]
REQUIRED_MAPS = [
    "maps/stage0/stage0.tmx",
    "maps/boss_venado/boss_venado.tmx",
]

WARNINGS: list[str] = []
ERRORS: list[str] = []


def check_file(path: Path, category: str) -> None:
    if not path.exists():
        ERRORS.append(f"[MISSING] {category}: {path}")
    elif not path.is_file():
        ERRORS.append(f"[NOT FILE] {category}: {path}")
    elif path.stat().st_size == 0:
        WARNINGS.append(f"[EMPTY] {category}: {path}")


def check_font(path: Path) -> None:
    try:
        font = pygame.font.Font(str(path), 8)
        font.render("Test", True, (255, 255, 255))
    except Exception as e:
        ERRORS.append(f"[FONT LOAD FAILED] {path}: {e}")


def check_model(path: Path) -> None:
    try:
        from src.framework.processing.pattern_recognition_tools import (
            PatternRecognitionTools,
        )
        PatternRecognitionTools.load_model(str(path))
    except Exception as e:
        ERRORS.append(f"[MODEL LOAD FAILED] {path}: {e}")


def check_sound(path: Path) -> None:
    try:
        pygame.mixer.Sound(str(path))
    except Exception as e:
        WARNINGS.append(f"[SOUND LOAD FAILED] {path}: {e}")


def check_map(path: Path) -> None:
    if not path.exists():
        ERRORS.append(f"[MISSING MAP] {path}")


def main() -> int:
    pygame.init()
    pygame.mixer.init()

    print(f"Validating assets in: {ASSETS_DIR}")
    print()

    # Fonts
    for rel in REQUIRED_FONTS:
        p = ASSETS_DIR / rel
        check_file(p, "Font")
        if p.exists():
            check_font(p)

    # Images
    for rel in REQUIRED_IMAGES:
        p = ASSETS_DIR / rel
        check_file(p, "Image")

    # Models
    for rel in REQUIRED_MODELS:
        p = ASSETS_DIR / rel
        check_file(p, "Model")
        if p.exists():
            check_model(p)

    # Sounds
    for rel in REQUIRED_SOUNDS:
        p = ASSETS_DIR / rel
        check_file(p, "Sound")
        if p.exists():
            check_sound(p)

    # Maps
    for rel in REQUIRED_MAPS:
        p = ASSETS_DIR / rel
        check_map(p)

    # Report
    if WARNINGS:
        for w in WARNINGS:
            print(f"  WARNING: {w}")

    if ERRORS:
        for e in ERRORS:
            print(f"  ERROR: {e}")
        print()
        print(f"  {len(ERRORS)} error(s), {len(WARNINGS)} warning(s)")
        pygame.quit()
        return 1

    print("  All assets validated successfully.")
    print(f"  0 errors, {len(WARNINGS)} warning(s)")
    pygame.quit()
    return 0


if __name__ == "__main__":
    sys.exit(main())
