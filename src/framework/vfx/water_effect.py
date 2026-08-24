"""
Module: water_effect
System: framework.vfx
Academic Unit: N/A
Description: Water effect overlay with animated waves and distortion.

AUD-111 — enchufado
===================
Mismo caso que `fog_of_war`: escrito, documentado (`docs/47_WATER_EFFECT.md`),
probado en aislamiento, y sin una sola instanciación en el motor. Lo enciende
`StageScene` cuando el TMX declara `water_effect`.

Es el compañero visual de `ZonaDeAgua`: aquélla es la física —nado, oxígeno,
corriente— y esto es lo que se ve. Van por separado a propósito, porque un
escenario puede querer el aspecto de agua sin el ahogamiento, o al revés.
"""
from __future__ import annotations

import math
from typing import TYPE_CHECKING

import pygame

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
        self._wave_offsets: list[int] = [0] * (height // 2)

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
        for i in range(len(self._wave_offsets)):
            y = i * 2
            self._wave_offsets[i] = int(math.sin(y * self._frequency + self._time) * self._amplitude)

    def draw(self, surface: Surface, offset: pygame.Vector2) -> None:
        self._overlay.fill((0, 0, 0, 0))
        ox = int(offset.x) % self._width
        for i, wave in enumerate(self._wave_offsets):
            y = i * 2
            x = (ox + wave) % self._width
            pygame.draw.line(self._overlay, (*self._tint, self._alpha), (x, y), (x + 4, y), 2)
        surface.blit(self._overlay, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
