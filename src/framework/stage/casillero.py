"""
Casillero bounce — extraído de Yariel 1-3, nativo.

Antes solo stage1_3 tenía puerta 32x48 con ease_out_bounce.
Ahora cualquier stage declara Casillero(rect) y el sistema lo anima.
"""

from __future__ import annotations

import pygame

from src.engine.utils.math_utils import ease_out_bounce


class Casillero:
    def __init__(self, rect: pygame.Rect) -> None:
        self.rect = rect
        self.abierto = False
        self.t = 0.0

    def abrir(self) -> None:
        self.abierto = True

    def update(self, dt: float) -> None:
        if not self.abierto:
            return
        self.t = min(1.0, self.t + dt * 2.0)
        k = ease_out_bounce(self.t)
        # Encoge altura con bounce
        self.rect.height = int(48 * (1.0 - k))
