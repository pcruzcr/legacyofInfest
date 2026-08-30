"""
LightPoolShimmer genérico — extraído de Monestel hall, nativo.

Antes solo hall tenía LightPoolShimmer con hsl_to_rgb breathing.
Ahora es del motor para cualquier stage con agua/luz.
"""

from __future__ import annotations

import math

from src.framework.processing.color_tools import ColorTools


class LightPoolShimmer:
    def __init__(self, base_color: tuple[int, int, int] = (80, 120, 180)) -> None:
        self.base = base_color
        self.t = 0.0

    def update(self, dt: float) -> tuple[int, int, int]:
        self.t += dt * 0.8
        k = 0.5 + 0.5 * math.sin(self.t)
        h, s, _l = ColorTools.rgb_to_hsl(*self.base)
        # Breathing: l 0.4-0.6
        l2 = 0.4 + 0.2 * k
        return ColorTools.hsl_to_rgb(h, s, l2)
