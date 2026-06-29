"""
Module: asset_loader
System: engine.utils
Academic Unit: N/A
Description: Class-level cached asset loading with graceful fallback
for missing images, sounds, and fonts.
"""
from __future__ import annotations
import logging
from pathlib import Path
import pygame

# Placeholder dimensions per ASSET BIBLE categories
PLACEHOLDER_SIZES: dict[str, tuple[int, int]] = {
    "player": (20, 32),
    "walker": (24, 28),
    "flying": (20, 14),
    "shooter": (16, 24),
    "checkpoint": (16, 32),
    "tile": (16, 16),
    "boss": (48, 48),
}
PLACEHOLDER_COLORS: dict[str, tuple[int, int, int]] = {
    "player": (0, 120, 255),
    "walker": (200, 0, 0),
    "flying": (255, 150, 0),
    "shooter": (150, 0, 200),
    "checkpoint_off": (100, 100, 100),
    "checkpoint_on": (255, 215, 0),
    "tile_solid": (60, 60, 60),
    "tile_platform": (80, 80, 80),
    "boss": (180, 0, 0),
}


class AssetLoader:
    """Class-level cached asset loading. All methods are classmethods."""

    _image_cache: dict[str, pygame.Surface] = {}
    _sound_cache: dict[str, pygame.mixer.Sound] = {}
    _font_cache: dict[str, pygame.font.Font] = {}

    @classmethod
    def load_image(cls, path: str | Path) -> pygame.Surface:
        """Load an image with fallback placeholder if file not found."""
        path_str = str(path)
        if path_str in cls._image_cache:
            return cls._image_cache[path_str]

        try:
            surface = pygame.image.load(path_str).convert_alpha()
            cls._image_cache[path_str] = surface
            return surface
        except FileNotFoundError:
            # Determine fallback size and color
            size = PLACEHOLDER_SIZES.get(path_str, (32, 32))
            color = PLACEHOLDER_COLORS.get(path_str, (128, 128, 128))
            surface = pygame.Surface(size, pygame.SRCALPHA)
            surface.fill(color)
            pygame.draw.rect(surface, (255, 255, 255), surface.get_rect(), 1)
            logging.warning(f"Asset no encontrado: {path_str} — usando placeholder {size}")
            cls._image_cache[path_str] = surface
            return surface
        except pygame.error as e:
            logging.warning(f"Error cargando asset {path_str}: {e} — usando placeholder")
            size = (32, 32)
            surface = pygame.Surface(size, pygame.SRCALPHA)
            surface.fill((128, 128, 128))
            pygame.draw.rect(surface, (255, 255, 255), surface.get_rect(), 1)
            cls._image_cache[path_str] = surface
            return surface

    @classmethod
    def load_sound(cls, path: str | Path) -> pygame.mixer.Sound | None:
        """Load a sound file. Returns None if missing (silent fallback)."""
        path_str = str(path)
        if path_str in cls._sound_cache:
            return cls._sound_cache[path_str]

        try:
            sound = pygame.mixer.Sound(path_str)
            cls._sound_cache[path_str] = sound
            return sound
        except FileNotFoundError:
            logging.warning(f"Sonido no encontrado: {path_str} — silencio")
            cls._sound_cache[path_str] = None
            return None
        except pygame.error as e:
            logging.warning(f"Error cargando sonido {path_str}: {e} — silencio")
            cls._sound_cache[path_str] = None
            return None

    @classmethod
    def load_font(cls, path: str | Path | None, size: int) -> pygame.font.Font:
        """Load a font. Falls back to default pygame font if missing."""
        key = f"{path}:{size}"
        if key in cls._font_cache:
            return cls._font_cache[key]

        try:
            if path is None:
                font = pygame.font.Font(None, size)
            else:
                font = pygame.font.Font(str(path), size)
            cls._font_cache[key] = font
            return font
        except FileNotFoundError:
            logging.warning(f"Font no encontrado: {path} — usando default")
            font = pygame.font.Font(None, size)
            cls._font_cache[key] = font
            return font

    @classmethod
    def clear_cache(cls) -> None:
        """Clear all caches. Useful between scenes or for testing."""
        cls._image_cache.clear()
        cls._sound_cache.clear()
        cls._font_cache.clear()
