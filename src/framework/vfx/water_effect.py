"""
Module: water_effect
System: framework.vfx
Academic Unit: N/A
Description: Water effect overlay with animated waves and distortion.
"""
from __future__ import annotations
import pygame
import math
from typing import TYPE_CHECKING
from src.engine.core import settings

if TYPE_CHECKING:
    from pygame import Surface


class WaterEffect:
    """Animated water overlay using sine waves and alpha blending."""

    def __init__(self, width: int = settings.INTERNAL_WIDTH, height: int = settings.INTERNAL_HEIGHT) -> None:
        self._width = width
        self._height = height
        self._time: float = 0.0
        self._speed: float = 1.5
        self._amplitude: int = 4
        self._frequency: float = 0.04
        self._alpha: int = 100
        self._tint: tuple[int, int, int] = (40, 80, 160)
        self._overlay = pygame.Surface((width, height), pygame.SRCALPHA)

    def set_params(self, speed: float = 1.5, amplitude: int = 4,
                   frequency: float = 0.04, alpha: int = 100,
                   tint: tuple[int, int, int] = (40, 80, 160)) -> None:
        self._speed = speed
        self._amplitude = amplitude
        self._frequency = frequency
        self._alpha = alpha
        self._tint = tint

    def update(self, dt: float) -> None:
        self._time += dt * self._speed

    def draw(self, surface: Surface, offset: pygame.Vector2) -> None:
        self._overlay.fill((0, 0, 0, 0))
        ox = int(offset.x) % self._width
        for y in range(0, self._height, 2):
            wave = math.sin(y * self._frequency + self._time) * self._amplitude
            x = (ox + int(wave)) % self._width
            pygame.draw.line(self._overlay, (*self._tint, self._alpha), (x, y), (x + 4, y), 2)
        surface.blit(self._overlay, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
