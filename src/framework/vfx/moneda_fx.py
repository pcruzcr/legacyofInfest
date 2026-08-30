"""
MonedaFx genérico — extraído de Rebeca 3-3, nativo.

Antes solo stage3_3 tenía MonedaFxController con ease destello.
Ahora cualquier stage puede usarlo para feedback de pickup.
"""

from __future__ import annotations

from src.engine.utils.math_utils import ease_out_quad


class MonedaFx:
    def __init__(self) -> None:
        self.t = 0.0
        self.activa = False

    def disparar(self) -> None:
        self.activa = True
        self.t = 0.0

    def update(self, dt: float) -> float:
        if not self.activa:
            return 0.0
        self.t = min(1.0, self.t + dt * 3.0)
        k = ease_out_quad(self.t)
        if self.t >= 1.0:
            self.activa = False
        return k
