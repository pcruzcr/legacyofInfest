"""Shooter_Cerbatana — PredictiveAim con arco visible."""
from __future__ import annotations

import pygame

from src.framework.ecs.components import PredictiveAimComponent
from src.framework.entities.enemy_shooter import EnemyShooter


class EnemyCerbatana(EnemyShooter):
    """Cerbatana que usa PredictiveAimComponent con gravedad 120 y telegrafía."""

    def __init__(self, spawn_position: pygame.Vector2, **kw) -> None:
        super().__init__(spawn_position, **kw)
        self._aim = PredictiveAimComponent(predict_factor=0.35, projectile_speed=110.0, gravity=120.0)
        self._telegraph_timer = 0.0

    def _alert_behavior(self, dt: float) -> None:
        # Telegrafía 0.5s antes de disparar
        if self._telegraph_timer > 0:
            self._telegraph_timer -= dt
            if self._telegraph_timer <= 0:
                super()._alert_behavior(dt)
            return
        # Si el jugador está en rango, inicia telegrafía
        if self._player_ref is not None and self._check_detection_range():
            self._telegraph_timer = 0.5
            # VFX: emitir evento de carga
            try:
                from src.engine.core.events import Events

                self._event_bus.emit(Events.VFX_CHARGE, pos=(self.position.x, self.position.y))
            except Exception:
                pass
            return
        super()._alert_behavior(dt)
