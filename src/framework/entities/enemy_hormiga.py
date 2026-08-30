"""Walker_HormigaZompopa — deja ZonaDeFriccion inercia=0.7."""
from __future__ import annotations

import pygame

from src.framework.entities.enemy_walker import EnemyWalker


class EnemyHormiga(EnemyWalker):
    """Hormiga zompopa que corta camino dejando rastro resbaladizo."""

    def __init__(self, spawn_position: pygame.Vector2, **kw) -> None:
        super().__init__(spawn_position, patrol_length=120, patrol_speed=55, **kw)
        self.rect.width = 22
        self.rect.height = 20
        self._trail_timer = 0.0

    def _post_update(self, dt: float) -> None:
        super()._post_update(dt)
        # Deja fricción cada 0.4s
        self._trail_timer += dt
        if self._trail_timer >= 0.4:
            self._trail_timer = 0.0
            # La escena recoge componentes via mundo ECS; aquí solo marcamos
            # que la hormiga quiere dejar rastro — el sistema lo materializa
            if hasattr(self, "_mundo"):
                try:
                    from src.framework.ecs.components import ZonaDeFriccion
                    comp = ZonaDeFriccion(
                        rect=pygame.Rect(int(self.position.x - 10), int(self.position.y + 16), 20, 8),
                        multiplicador=1.0,
                        inercia=0.7,
                    )
                    self._mundo.poner(self.entidad, comp)
                except Exception:
                    pass

    def _build_hurtbox(self) -> pygame.Rect:
        return self.caja_ajustada(margen_x=2, margen_y=2)
