"""
Module: asset_loader
System: engine
Academic Unit: N/A
Description: Centralised asset cache for pygame Surfaces, Sounds, and
SpriteSheets. All loaders are classmethods backed by a single
class-level cache keyed by the string form of path, so loading the
same path twice returns the identical Python object (is check passes).
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Union

import pygame

from src.engine.utils.spritesheet import SpriteSheet
from src.engine.core.settings import ASSETS_DIR

# Configure logger for asset loading warnings
_logger = logging.getLogger(__name__)


class AssetLoader:
    """All methods are classmethods; internal cache is a class-level dict keyed by str(path)."""

    _cache: dict[str, object] = {}

    @classmethod
    def _cache_key(cls, path: Union[str, Path]) -> str:
        """Return the string form of path to use as the cache key.

        Per 22_API_CONTRACTS.md §5.2 the cache is keyed by the
        literal string form of the supplied path — no path rewriting.
        """
        return str(path)

    @classmethod
    def load_image(cls, path: Union[str, Path]) -> pygame.Surface:
        """Load and cache an image surface.

        Returns the cached surface if the same path has been loaded
        before. Raises FileNotFoundError if the file does not exist.
        """
        key = cls._cache_key(path)
        if key not in cls._cache:
            try:
                surface = pygame.image.load(key).convert_alpha()
            except FileNotFoundError:
                _logger.warning("Asset not found: %s", key)
                raise
            cls._cache[key] = surface
        return cls._cache[key]

    @classmethod
    def load_sound(cls, path: Union[str, Path]) -> pygame.mixer.Sound:
        """Load and cache a sound object.

        Raises FileNotFoundError if the file does not exist.
        """
        key = cls._cache_key(path)
        if key not in cls._cache:
            try:
                sound = pygame.mixer.Sound(key)
            except FileNotFoundError:
                _logger.warning("Sound not found: %s", key)
                raise
            cls._cache[key] = sound
        return cls._cache[key]

    @classmethod
    def load_spritesheet(
        cls, path: Union[str, Path], frame_w: int, frame_h: int
    ) -> SpriteSheet:
        """Load an image and wrap it in a SpriteSheet.

        The cache key includes the frame dimensions so that the same
        image sliced differently produces distinct entries.
        """
        base_key = cls._cache_key(path)
        key = f"{base_key}:{frame_w}x{frame_h}"
        if key not in cls._cache:
            surface = cls.load_image(path)
            cls._cache[key] = SpriteSheet(surface, frame_w, frame_h)
        return cls._cache[key]