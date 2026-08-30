"""
SolPoniente genérico — extraído de Fabrizio 1-1, nativo.

Evento EVENTO_SOL_EN_EL_HORIZONTE + ease, ya estaba en stage1_1/sol_poniente.py
Ahora es del motor para cualquier stage cenital.
"""

from __future__ import annotations

from src.engine.utils.math_utils import ease_out_quad


class SolPoniente:
    def __init__(self) -> None:
        self.progreso = 0.0

    def update(self, dt: float, player_y: float, horizonte_y: float) -> float:
        # Progreso 0-1 según altura del sol
        self.progreso = max(0.0, min(1.0, (horizonte_y - player_y) / 200.0))
        k = ease_out_quad(self.progreso)
        return k
