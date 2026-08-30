"""Flying_Oropel — CatmullRom entre Waypoints, vulnerable a luz."""
from __future__ import annotations

import pygame

from src.framework.entities.enemy_flying import EnemyFlying


class EnemyOropel(EnemyFlying):
    """Oropel que sigue curva y se vuelve vulnerable si está iluminado."""

    def __init__(self, spawn_position: pygame.Vector2, **kw) -> None:
        super().__init__(spawn_position, **kw)
        self._light_vulnerable = False

    def update(self, dt: float) -> None:
        # Si hay luz ambiental alta, quita invulnerabilidad
        try:
            # La escena expone LightSystem; aquí solo simulamos
            # Si el jefe tiene luz, el oropel es vulnerable
            self._light_vulnerable = True
        except Exception:
            pass
        super().update(dt)

    def apply_hit(self, damage: float, source_position: tuple[float, float], canal: str | None = None) -> None:
        # Solo vulnerable si está iluminado o si no tiene invulnerabilidad por fase
        if not self._light_vulnerable and getattr(self, "invulnerable", False):
            return
        super().apply_hit(damage, source_position, canal=canal)
