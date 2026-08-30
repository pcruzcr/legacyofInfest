"""
Losa genérica — extraída de Avril 3-1, nativa en motor.

Antes solo Avril tenía 5 losas con ease_out_cubic/elastic y EventBus STAGE31_LOSAS_COMPLETAS.
Ahora cualquier stage declara Losa(rect, ease="cubic") y el sistema la anima.
"""

from __future__ import annotations

import pygame

from src.engine.utils.math_utils import ease_out_cubic, ease_out_elastic

EASING = {
    "cubic": ease_out_cubic,
    "elastic": ease_out_elastic,
}


class Losa:
    def __init__(self, rect: pygame.Rect, ease: str = "cubic", duration: float = 0.6) -> None:
        self.rect = rect
        self._inicio_y = int(rect.y)
        self.ease_name = ease
        self.duration = duration
        self.t = 0.0
        self.activa = False
        self._elevacion = 8  # px que sube la losa

    def activar(self) -> None:
        self.activa = True
        self.t = 0.0

    def update(self, dt: float) -> bool:
        """Avanza animación, devuelve True si completó."""
        if not self.activa:
            return False
        self.t = min(1.0, self.t + dt / self.duration)
        fn = EASING.get(self.ease_name, ease_out_cubic)
        k = fn(self.t)
        # Lerp desde inicio, no drift acumulativo
        self.rect.y = int(self._inicio_y - k * self._elevacion)
        return self.t >= 1.0
