"""
Module: fog_of_war
System: framework.vfx
Academic Unit: N/A
Description: Fog of war overlay — hides unexplored areas with
editable holes revealed by player/enemy positions.
"""
from __future__ import annotations
import pygame

from src.engine.core import settings


class FogOfWar:
    """Black overlay with alpha holes around revealed positions."""

    def __init__(self, width: int = settings.INTERNAL_WIDTH, height: int = settings.INTERNAL_HEIGHT,
                 radius: int = 80, hardness: float = 0.6) -> None:
        self._width = width
        self._height = height
        self._radius = radius
        self._hardness = hardness
        self._overlay = pygame.Surface((width, height), pygame.SRCALPHA)
        self._overlay.fill((0, 0, 0, 220))
        self._mask = pygame.Surface((width, height), pygame.SRCALPHA)
        self._mask.fill((0, 0, 0, 0))
        self._revealed: list[tuple[float, float]] = []

    def clear(self) -> None:
        self._revealed.clear()

    def reveal(self, x: float, y: float) -> None:
        self._revealed.append((float(x), float(y)))

    def reveal_all(self, points: list[tuple[float, float]]) -> None:
        self._revealed.extend((float(x), float(y)) for x, y in points)

    def update(self, dt: float) -> None:
        """No-op placeholder for future fading."""

    def draw(self, surface: pygame.Surface, offset: pygame.Vector2) -> None:
        self._mask.fill((0, 0, 0, 0))
        for x, y in self._revealed:
            sx = int(x - offset.x)
            sy = int(y - offset.y)
            pygame.draw.circle(self._mask, (0, 0, 0, 255), (sx, sy), self._radius)
        self._overlay.fill((0, 0, 0, 220))
        self._overlay.blit(self._mask, (0, 0), special_flags=pygame.BLEND_RGBA_SUB)
        surface.blit(self._overlay, (0, 0))
