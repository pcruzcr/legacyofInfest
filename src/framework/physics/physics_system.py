"""
PhysicsSystem — fachada unificada para resolver_eje_x / resolver_eje_y.

P0 para motor genérico: antes Player y Enemy duplicaban la llamada a
resolver_eje_x/y con matices. Este sistema es el único sitio que lo hace.
"""

from __future__ import annotations

from typing import Any

import pygame

from src.framework.physics.resolucion import EstadoDeMovimiento, resolver_eje_x, resolver_eje_y


class PhysicsSystem:
    """Sistema puro: no guarda estado, solo resuelve."""

    @staticmethod
    def step(
        estado: EstadoDeMovimiento,
        dt: float,
        solidos: list[pygame.Rect],
        pendientes: list[Any] | None = None,
    ) -> tuple[Any, Any]:
        """Resuelve X luego Y y devuelve (eje_x, eje_y) con hechos."""
        # X
        ex = resolver_eje_x(estado, dt, solidos)
        # Y se resuelve contra los mismos sólidos; pendientes las maneja
        # el llamador (Player) via resolver_cuestas separado para no mezclar.
        ey = resolver_eje_y(estado, dt, solidos)
        return ex, ey

    @staticmethod
    def from_player(player: Any, dt: float) -> EstadoDeMovimiento:
        """Construye EstadoDeMovimiento desde Player (atajo para StageScene)."""
        # Usa el helper ya existente en Player para no duplicar lógica
        try:
            return player._estado_de_movimiento_para_resolver()  # type: ignore[attr-defined]
        except Exception:
            # Fallback genérico
            return EstadoDeMovimiento(
                posicion=player.position,
                velocidad=player.velocity,
                ancho=player.rect.width,
                alto=player.rect.height,
                en_el_suelo=getattr(player, "is_grounded", False),
                prev_foot_y=getattr(player, "_prev_foot_y", player.position.y + player.rect.height),
            )
