"""Brute_Ceibo — Shield frontal + WeakPoint detrás."""
from __future__ import annotations

import pygame

from src.framework.ecs.components import ShieldComponent
from src.framework.entities.boss_kit import WeakPoint
from src.framework.entities.enemy_brute import EnemyBrute


class EnemyCeibo(EnemyBrute):
    """Ceibo con escudo frontal 3 HP, vulnerable por detrás 2.5x."""

    def __init__(self, spawn_position: pygame.Vector2, **kw) -> None:
        super().__init__(spawn_position, **kw)
        self._shield = ShieldComponent(shield_health=3.0, shield_max_health=3.0)
        self.weak_points = [WeakPoint(offset=(6, 8), size=(10, 12), multiplier=2.5, label="corteza")]

    def apply_hit(self, damage: float, source_position: tuple[float, float], canal: str | None = None) -> None:
        # Si el golpe viene de frente y el escudo está activo, bloquea
        dx = source_position[0] - self.position.x
        facing = self.facing_direction
        # Frente: dx y facing mismo signo (jugador delante)
        is_front = (dx * facing) > 0
        if is_front and self._shield.shield_health > 0:
            self._shield.shield_health -= damage
            if self._shield.shield_health <= 0:
                self._shield._broken = True
                try:
                    self._event_bus.emit("SFX_PLAYER_PARRY", pos=(self.position.x, self.position.y))
                except Exception:
                    pass
            return
        super().apply_hit(damage, source_position, canal=canal)
