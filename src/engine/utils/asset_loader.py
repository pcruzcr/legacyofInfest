"""
Module: asset_loader
System: engine
Academic Unit: Framework scaffold
Description: Centralised asset cache for pygame Surfaces, Sounds, and
SpriteSheets.  All loaders are classmethods backed by a single
class-level cache keyed by the string form of *path*, so loading the
same path twice returns the identical Python object (``is`` check
passes).
"""

from __future__ import annotations

from pathlib import Path
from typing import Union

import pygame


class SpriteSheet:
    """Thin wrapper over a spritesheet ``pygame.Surface``.

    The sheet is sliced into equal-sized frames of ``frame_w`` ×
    ``frame_h`` pixels.
    """

    def __init__(
        self, surface: pygame.Surface, frame_w: int, frame_h: int
    ) -> None:
        """Store the sheet surface and frame dimensions."""
        self._surface: pygame.Surface = surface
        self._frame_w: int = frame_w
        self._frame_h: int = frame_h

    @property
    def frame_count(self) -> int:
        """Total number of frames in the sheet (columns × rows)."""
        cols = self._surface.get_width() // self._frame_w
        rows = self._surface.get_height() // self._frame_h
        return cols * rows

    def get_frame(self, index: int) -> pygame.Surface:
        """Return a single frame surface by zero-based *index*."""
        if index < 0 or index >= self.frame_count:
            raise IndexError(
                f"SpriteSheet index {index} out of range "
                f"(frame_count={self.frame_count})"
            )
        cols = self._surface.get_width() // self._frame_w
        col = index % cols
        row = index // cols
        rect = pygame.Rect(
            col * self._frame_w,
            row * self._frame_h,
            self._frame_w,
            self._frame_h,
        )
        return self._surface.subsurface(rect).copy()

    def get_frames(self, start: int, end: int) -> list[pygame.Surface]:
        """Return frames ``[start, end)`` as a list of surfaces."""
        return [self.get_frame(i) for i in range(start, end)]


class AssetLoader:
    """All methods are classmethods; internal cache is a class-level dict."""

    _cache: dict[str, object] = {}

    @classmethod
    def _cache_key(cls, path: Union[str, Path]) -> str:
        """Return the string form of *path* to use as the cache key.

        Per ``22_API_CONTRACTS.md`` §5.2 the cache is keyed by the
        literal string form of the supplied path — no path rewriting.
        """
        return str(path)

    @classmethod
    def load_image(cls, path: Union[str, Path]) -> pygame.Surface:
        """Load and cache an image surface.

        Returns the cached surface if the same *path* has been loaded
        before.  Raises ``FileNotFoundError`` if the file does not exist.
        """
        key = cls._cache_key(path)
        if key not in cls._cache:
            # ``pygame.display`` may not be initialised during early
            # unit tests — defer format conversion to the caller or to
            # ``App`` initialisation (Phase 1+).
            cls._cache[key] = pygame.image.load(key)
        return cls._cache[key]

    @classmethod
    def load_sound(cls, path: Union[str, Path]) -> pygame.mixer.Sound:
        """Load and cache a sound object.

        Raises ``FileNotFoundError`` if the file does not exist.
        """
        key = cls._cache_key(path)
        if key not in cls._cache:
            cls._cache[key] = pygame.mixer.Sound(key)
        return cls._cache[key]

    @classmethod
    def load_spritesheet(
        cls, path: Union[str, Path], frame_w: int, frame_h: int
    ) -> SpriteSheet:
        """Load an image and wrap it in a :class:`SpriteSheet`.

        The cache key includes the frame dimensions so that the same
        image sliced differently produces distinct entries.
        """
        base_key = cls._cache_key(path)
        key = f"{base_key}:{frame_w}x{frame_h}"
        if key not in cls._cache:
            surface = cls.load_image(path)
            cls._cache[key] = SpriteSheet(surface, frame_w, frame_h)
        return cls._cache[key]
