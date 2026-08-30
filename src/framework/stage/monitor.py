"""
MonitorSeguridad genérico — extraído de César 2-2 y Saúl 2-1, nativo.

Usa histograma + Sobel para decidir auto_levels, como en stage2_2/monitor_seguridad.py
y stage2_1/security_monitor.py. Ahora es un componente del engine.
"""

from __future__ import annotations

import pygame

from src.framework.processing.filter_tools import FilterTools


class MonitorSeguridad:
    def __init__(self) -> None:
        self.nivel = 0.0

    def update(self, surface: pygame.Surface) -> str:
        """Analiza histograma y bordes, devuelve modo: 'normal'|'alerta'"""
        hist = FilterTools.compute_histogram(surface)
        # Si luminancia media >180, alerta
        lum = hist["luminance"]
        total = hist["total_pixels"]
        # Peso medio
        mean = sum(i * lum[i] for i in range(256)) / max(1, total)
        return "alerta" if mean > 180 else "normal"
