"""
Module: spritesheet
System: engine.utils
Academic Unit: N/A
Description: SpriteSheet utility for slicing frames from a sprite sheet image.
"""
from __future__ import annotations

import pygame


class SpriteSheet:
    """Slice frames from a sprite sheet image."""

    def __init__(self, sheet: pygame.Surface) -> None:
        self.sheet: pygame.Surface = sheet

    def get_frame(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        colorkey: tuple[int, int, int] | None = None,
    ) -> pygame.Surface:
        """Extract a single frame from the sheet at (x, y) with given dimensions."""
        frame = pygame.Surface((width, height), pygame.SRCALPHA)
        frame.blit(self.sheet, (0, 0), (x, y, width, height))
        if colorkey is not None:
            frame.set_colorkey(colorkey)
        return frame

    def get_frames(
        self,
        rects: list[tuple[int, int, int, int]],
        colorkey: tuple[int, int, int] | None = None,
    ) -> list[pygame.Surface]:
        """Extract multiple frames from a list of (x, y, w, h) rects."""
        return [self.get_frame(x, y, w, h, colorkey) for (x, y, w, h) in rects]

    def get_grid(
        self,
        columns: int,
        rows: int,
        frame_width: int,
        frame_height: int,
        colorkey: tuple[int, int, int] | None = None,
    ) -> list[list[pygame.Surface]]:
        """Extract a grid of frames arranged in columns x rows."""
        grid: list[list[pygame.Surface]] = []
        for row in range(rows):
            row_frames: list[pygame.Surface] = []
            for col in range(columns):
                x = col * frame_width
                y = row * frame_height
                frame = self.get_frame(x, y, frame_width, frame_height, colorkey)
                row_frames.append(frame)
            grid.append(row_frames)
        return grid
