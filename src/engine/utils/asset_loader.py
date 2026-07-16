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
    """
    Centralized asset manager with instance-based caching.

    Instance-based design (ARC-005): Internal ``_``-prefixed methods use
    instance state for proper test isolation. Classmethod wrappers with the
    public names (``load_image``, ``load_font``, etc.) delegate to a default
    singleton instance so existing code continues to work unchanged.

    Usage (existing code, via default instance):
        img = AssetLoader.load_image('path')

    Usage (new code, explicit instance injection):
        loader = AssetLoader()
        img = loader._load_image('path')
    """

    _default_instance: AssetLoader | None = None

    def __init__(self) -> None:
        self._images: dict[str, pygame.Surface] = {}
        self._fonts: dict[str, pygame.font.Font] = {}
        self._sounds: dict[str, pygame.mixer.Sound] = {}
        self._missing: set[str] = set()

    # ── Internal instance methods ──────────────────────────────

    def _clear_cache(self) -> None:
        """Release all cached images/fonts/sounds to free memory."""
        self._images.clear()
        self._fonts.clear()
        self._sounds.clear()
        self._missing.clear()

    def _resolve(self, path: str | Path) -> Path:
        path = Path(path)
        if path.is_absolute():
            return path
        custom = (PROJECT_ROOT / "custom_assets" / path).resolve()
        if custom.exists():
            return custom
        return (PROJECT_ROOT / path).resolve()

    def _load_image(
        self,
        path: str | Path,
        *,
        scale: float | None = None,
        size: tuple[int, int] | None = None,
        alpha: bool = True,
        smooth: bool = False,
    ) -> pygame.Surface:
        real_path = self._resolve(path)
        key = f"{real_path}|{scale}|{size}|{alpha}|{smooth}"
        if key in self._images:
            return self._images[key]
        try:
            image = pygame.image.load(real_path)
            image = image.convert_alpha() if alpha else image.convert()
        except (pygame.error, FileNotFoundError, PermissionError):
            category = real_path.parent.name
            placeholder_size = PLACEHOLDER_SIZES.get(category, (32, 32))
            color = PLACEHOLDER_COLORS.get(category, (120, 120, 120))
            image = pygame.Surface(placeholder_size, pygame.SRCALPHA)
            image.fill(color)
            pygame.draw.rect(image, (255, 255, 255), image.get_rect(), 1)
            if str(real_path) not in self._missing:
                logging.warning("Missing asset: %s", real_path)
                self._missing.add(str(real_path))
        if size:
            transform_fn = pygame.transform.smoothscale if smooth else pygame.transform.scale
            image = transform_fn(image, size)
        elif scale:
            transform_fn = pygame.transform.smoothscale if smooth else pygame.transform.scale
            image = transform_fn(image, (int(image.get_width() * scale), int(image.get_height() * scale)))
        self._images[key] = image
        return image

    def _load_font(self, path: str | Path | None, size: int) -> pygame.font.Font:
        key = f"{path}:{size}"
        if key in self._fonts:
            return self._fonts[key]
        try:
            if path is None:
                font = pygame.font.Font(None, size)
            else:
                font = pygame.font.Font(self._resolve(path), size)
        except (pygame.error, FileNotFoundError, PermissionError):
            font = pygame.font.Font(None, size)
        self._fonts[key] = font
        return font

    def _load_sound(self, path: str | Path) -> pygame.mixer.Sound | None:
        real = str(self._resolve(path))
        if real in self._sounds:
            return self._sounds[real]
        try:
            sound = pygame.mixer.Sound(real)
        except (pygame.error, FileNotFoundError, PermissionError):
            sound = None
        self._sounds[real] = sound
        return sound

    def _load_sprite_sheet(
        self,
        path: str | Path,
        frame_width: int,
        frame_height: int,
    ) -> list[pygame.Surface]:
        sheet = self._load_image(path)
        frames = []
        cols = sheet.get_width() // frame_width
        rows = sheet.get_height() // frame_height
        for y in range(rows):
            for x in range(cols):
                rect = pygame.Rect(x * frame_width, y * frame_height, frame_width, frame_height)
                frames.append(sheet.subsurface(rect))
        return frames

    # ── Classmethod wrappers (backward compatible) ─────────────

    @classmethod
    def _get_instance(cls) -> AssetLoader:
        if cls._default_instance is None:
            cls._default_instance = AssetLoader()
        return cls._default_instance

    @classmethod
    def clear_cache(cls) -> None:
        cls._get_instance()._clear_cache()

    @classmethod
    def load_image(
        cls,
        path: str | Path,
        *,
        scale: float | None = None,
        size: tuple[int, int] | None = None,
        alpha: bool = True,
        smooth: bool = False,
    ) -> pygame.Surface:
        return cls._get_instance()._load_image(path, scale=scale, size=size, alpha=alpha, smooth=smooth)

    @classmethod
    def load_font(cls, path: str | Path | None, size: int) -> pygame.font.Font:
        return cls._get_instance()._load_font(path, size)

    @classmethod
    def load_sound(cls, path: str | Path) -> pygame.mixer.Sound | None:
        return cls._get_instance()._load_sound(path)

    @classmethod
    def load_sprite_sheet(
        cls, path: str | Path, frame_width: int, frame_height: int,
    ) -> list[pygame.Surface]:
        return cls._get_instance()._load_sprite_sheet(path, frame_width, frame_height)
