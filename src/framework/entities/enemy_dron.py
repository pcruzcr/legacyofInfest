"""Dron04 genérico — extraído de Saúl 2-1, nativo.

Usa vec2_distance/dot/normalize + cono frontal, y lazo 6 puntos CurveTools.
Ahora es un enemigo del motor, no solo de un stage.
"""

from __future__ import annotations

import pygame

from src.engine.utils.math_utils import vec2_distance, vec2_dot, vec2_normalize
from src.framework.entities.enemy_flying import EnemyFlying


class EnemyDron(EnemyFlying):
    def __init__(self, spawn_position: pygame.Vector2, **kw) -> None:
        super().__init__(spawn_position, **kw)
        self.detection_range_x = 140
        self.detection_range_y = 80

    def _alert_behavior(self, dt: float) -> None:
        if self._player_ref is None:
            return
        my_pos = pygame.Vector2(self.rect.center)
        player_pos = pygame.Vector2(self._player_ref.center)
        dist = vec2_distance(my_pos, player_pos)
        if dist < 96:
            # Cono frontal 120°
            aim = vec2_normalize(player_pos - my_pos)
            fwd = pygame.Vector2(1, 0) if self.facing_direction > 0 else pygame.Vector2(-1, 0)
            if vec2_dot(aim, fwd) > 0.5:  # cos 60°
                # Persigue
                self.position += aim * 85 * dt
