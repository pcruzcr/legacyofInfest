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
REQUIRED_IMAGES = []
REQUIRED_MODELS = ["models/professor_sample.pkl"]
REQUIRED_SOUNDS = []
REQUIRED_MAPS = []

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
