"""
Module: asset_loader
System: engine.utils

Centralized asset manager for Legacy of InFest.

Responsibilities
----------------
- Cached image loading
- Cached sound loading
- Cached font loading
- Music playback
- Placeholder generation
- Sprite sheet loading
- Automatic scaling
"""

from __future__ import annotations

import logging
from pathlib import Path

import pygame


PROJECT_ROOT = Path(__file__).resolve().parents[3]


PLACEHOLDER_SIZES = {
    "player": (20, 32),
    "enemies": (24, 24),
    "bosses": (64, 64),
    "ui": (32, 32),
    "tilesets": (16, 16),
    "backgrounds": (320, 224),
    "splash": (320, 224),
}


PLACEHOLDER_COLORS = {
    "player": (40, 140, 255),
    "enemies": (220, 60, 60),
    "bosses": (180, 40, 40),
    "tilesets": (90, 90, 90),
    "ui": (220, 220, 220),
    "backgrounds": (35, 35, 35),
    "splash": (20, 20, 40),
}


class AssetLoader:

    _images: dict[str, pygame.Surface] = {}
    _fonts: dict[str, pygame.font.Font] = {}
    _sounds: dict[str, pygame.mixer.Sound] = {}

    _missing: set[str] = set()

    # -------------------------------------------------------

    @classmethod
    def _resolve(cls, path: str | Path) -> Path:

        path = Path(path)

        if path.is_absolute():
            return path

        return (PROJECT_ROOT / path).resolve()

    # -------------------------------------------------------

    @classmethod
    def load_image(
        cls,
        path: str | Path,
        *,
        scale: float | None = None,
        size: tuple[int, int] | None = None,
        alpha: bool = True,
    ) -> pygame.Surface:

        real_path = cls._resolve(path)

        key = f"{real_path}|{scale}|{size}|{alpha}"

        if key in cls._images:
            return cls._images[key]

        try:

            image = pygame.image.load(real_path)

            image = (
                image.convert_alpha()
                if alpha
                else image.convert()
            )

        except Exception:

            category = real_path.parent.name

            placeholder_size = PLACEHOLDER_SIZES.get(
                category,
                (32, 32),
            )

            color = PLACEHOLDER_COLORS.get(
                category,
                (120, 120, 120),
            )

            image = pygame.Surface(
                placeholder_size,
                pygame.SRCALPHA,
            )

            image.fill(color)

            pygame.draw.rect(
                image,
                (255, 255, 255),
                image.get_rect(),
                1,
            )

            if str(real_path) not in cls._missing:

                logging.warning(
                    "Missing asset: %s",
                    real_path,
                )

                cls._missing.add(str(real_path))

        if size:

            image = pygame.transform.smoothscale(
                image,
                size,
            )

        elif scale:

            image = pygame.transform.smoothscale(
                image,
                (
                    int(image.get_width() * scale),
                    int(image.get_height() * scale),
                ),
            )

        cls._images[key] = image

        return image

    # -------------------------------------------------------

    @classmethod
    def load_font(
        cls,
        path: str | Path | None,
        size: int,
    ) -> pygame.font.Font:

        key = f"{path}:{size}"

        if key in cls._fonts:
            return cls._fonts[key]

        try:

            if path is None:

                font = pygame.font.Font(
                    None,
                    size,
                )

            else:

                font = pygame.font.Font(
                    cls._resolve(path),
                    size,
                )

        except Exception:

            font = pygame.font.Font(
                None,
                size,
            )

        cls._fonts[key] = font

        return font

    # -------------------------------------------------------

    @classmethod
    def load_sound(
        cls,
        path: str | Path,
    ):

        real = str(cls._resolve(path))

        if real in cls._sounds:
            return cls._sounds[real]

        try:

            sound = pygame.mixer.Sound(real)

        except Exception:

            sound = None

        cls._sounds[real] = sound

        return sound

    # -------------------------------------------------------

    @classmethod
    def load_sprite_sheet(
        cls,
        path: str | Path,
        frame_width: int,
        frame_height: int,
    ) -> list[pygame.Surface]:

        sheet = cls.load_image(path)

        frames = []

        cols = sheet.get_width() // frame_width
        rows = sheet.get_height() // frame_height

        for y in range(rows):

            for x in range(cols):

                rect = pygame.Rect(
                    x * frame_width,
                    y * frame_height,
                    frame_width,
                    frame_height,
                )

                frame = pygame.Surface(
                    rect.size,
                    pygame.SRCALPHA,
                )

                frame.blit(
                    sheet,
                    (0, 0),
                    rect,
                )

                frames.append(frame)

        return frames

    # -------------------------------------------------------

    @classmethod
    def clear_cache(cls):

        cls._images.clear()
        cls._fonts.clear()
        cls._sounds.clear()
