"""
BarreraKiosco genérica — extraída de César 2-2, nativa.

Antes solo stage2_2 tenía kiosco con easing y EVENTO_ABIERTA.
Ahora cualquier stage declara Barrera(rect) y el sistema la anima.
"""

from __future__ import annotations

import pygame

from src.engine.utils.math_utils import ease_out_quad


class BarreraKiosco:
    def __init__(self, rect: pygame.Rect) -> None:
        self.rect = rect
        self._inicio_x = int(rect.x)
        self.abierta = False
        self.t = 0.0
        self._desplazamiento = 64  # px que se abre la barrera (antes 2*60 frames ≈ 120 pero sin referencia)

    def abrir(self) -> None:
        self.abierta = True

    def update(self, dt: float) -> None:
        if not self.abierta:
            return
        self.t = min(1.0, self.t + dt * 2.0)
        k = ease_out_quad(self.t)
        # Lerp desde inicio, no incremento acumulativo (evita drift)
        self.rect.x = int(self._inicio_x + k * self._desplazamiento)
