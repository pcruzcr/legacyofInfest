"""
Module: spritesheet
System: engine
Academic Unit: N/A
Description: SpriteSheet slices a larger pygame.Surface into
equal-sized frame rectangles. The sheet is treated as a grid of
frame_w x frame_h cells; frames are numbered left-to-right,
top-to-bottom starting at zero.
"""

from __future__ import annotations

import pygame


class SpriteSheet:
    """Thin wrapper over a spritesheet pygame.Surface.

    The sheet is sliced into equal-sized frames of frame_w x
    frame_h pixels.
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
        """Total number of frames in the sheet (columns x rows)."""
        cols = self._surface.get_width() // self._frame_w
        rows = self._surface.get_height() // self._frame_h
        return cols * rows

    def get_frame(self, index: int) -> pygame.Surface:
        """Return a single frame surface by zero-based index."""
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
        """Return frames [start, end) as a list of surfaces."""
        return [self.get_frame(i) for i in range(start, end)]