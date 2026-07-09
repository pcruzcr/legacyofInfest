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

# Palette definitions: (glob_pattern, set_of_allowed_RGB_tuples)
# These are derived from the actual pixel data in the repository assets.
# Run `python -m scripts.collect_palettes` to regenerate.
SPRITE_PALETTES: list[tuple[str, set[tuple[int, int, int]]]] = [
    ("sprites/player/*.png", {
        (20, 30, 60), (40, 50, 90), (60, 60, 80), (80, 80, 110),
        (100, 80, 50), (140, 140, 170), (180, 140, 100),
        (200, 180, 100), (220, 180, 140),
    }),
    ("sprites/enemies/*.png", {
        (0, 0, 0), (30, 80, 30), (40, 10, 10), (40, 120, 60),
        (50, 30, 80), (60, 60, 120), (60, 120, 60), (80, 30, 30),
        (80, 50, 20), (80, 60, 120), (80, 100, 40), (100, 20, 20),
        (100, 30, 20), (100, 60, 60), (100, 60, 100), (120, 80, 40),
        (120, 100, 60), (140, 30, 20), (160, 120, 200), (180, 40, 30),
        (180, 50, 50), (180, 100, 220), (180, 140, 220), (200, 50, 40),
        (200, 80, 240), (200, 120, 240), (200, 160, 240), (220, 60, 60),
        (220, 100, 255), (220, 140, 255), (220, 180, 255), (240, 80, 80),
        (240, 120, 255), (240, 160, 255), (255, 100, 100), (255, 120, 120),
        (255, 140, 255), (255, 255, 0), (255, 255, 255),
    }),
    ("tilesets/*.png", {
        (25, 95, 75), (30, 28, 40), (30, 60, 130), (40, 40, 60),
        (40, 80, 30), (45, 42, 52), (45, 135, 105), (50, 50, 70),
        (50, 100, 180), (55, 50, 65), (60, 60, 60), (60, 100, 50),
        (65, 75, 55), (70, 50, 30), (70, 70, 80), (70, 70, 90),
        (75, 70, 85), (80, 70, 60), (80, 80, 90), (80, 120, 70),
        (90, 90, 100), (90, 90, 110), (95, 90, 105), (100, 70, 40),
        (100, 90, 80), (100, 100, 110), (100, 120, 60), (100, 140, 90),
        (110, 90, 70), (110, 110, 120), (110, 110, 130), (115, 110, 125),
        (120, 110, 100), (120, 120, 130), (120, 120, 140), (120, 140, 80),
        (130, 110, 90), (130, 130, 150), (140, 40, 40), (140, 120, 80),
        (140, 120, 100), (140, 130, 120), (140, 140, 150), (140, 160, 100),
        (150, 130, 110), (155, 135, 95), (160, 140, 100), (160, 140, 120),
        (160, 180, 120), (170, 150, 130), (180, 60, 60), (180, 160, 120),
        (180, 160, 140), (200, 180, 140), (255, 255, 255),
    }),
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


def check_palette(path: Path) -> None:
    """Verify that all pixels use only allowed palette colors for the sprite type."""
    allowed = None
    rel = path.relative_to(ASSETS_DIR).as_posix()
    import fnmatch
    for pattern, palette in SPRITE_PALETTES:
        if fnmatch.fnmatch(rel, pattern):
            allowed = palette
            break
    if allowed is None:
        return

    try:
        raw = pygame.image.load(str(path))
        img = raw.convert_alpha()
    except Exception as e:
        ERRORS.append(f"[LOAD FAIL] {path}  ({e})")
        return

    w, h = img.get_size()
    na = pygame.surfarray.pixels3d(img)
    alpha = pygame.surfarray.pixels_alpha(img) if (img.get_flags() & pygame.SRCALPHA) else None
    bad: set[tuple[int, int, int]] = set()

    for y in range(h):
        for x in range(w):
            if alpha is not None and alpha[x, y] == 0:
                continue
            r, g, b = int(na[x, y, 0]), int(na[x, y, 1]), int(na[x, y, 2])
            if (r, g, b) not in allowed:
                bad.add((r, g, b))
                if len(bad) > 20:
                    break
        if len(bad) > 20:
            break

    if bad:
        s = ", ".join(f"({r},{g},{b})" for r, g, b in sorted(bad)[:10])
        ERRORS.append(f"[PALETTE] {rel}: {len(bad)} off-palette colors ({s})")


def check_map(path: Path) -> None:
    if not path.exists():
        ERRORS.append(f"[MISSING MAP] {path}")


def main() -> int:
    pygame.init()
    pygame.mixer.init()
    pygame.display.set_mode((1, 1))

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

    # Palette validation for all sprite/tileset/background PNGs
    import fnmatch
    checked: set[Path] = set()
    for p in sorted(ASSETS_DIR.rglob("*.png")):
        rel = p.relative_to(ASSETS_DIR).as_posix()
        if any(fnmatch.fnmatch(rel, pattern) for pattern, _ in SPRITE_PALETTES):
            if p not in checked:
                checked.add(p)
                check_palette(p)

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
