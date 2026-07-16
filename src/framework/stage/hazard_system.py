from __future__ import annotations

from typing import TYPE_CHECKING

from src.engine.core.events import Events
from src.engine.scenes.game_over_scene import GameOverScene

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext
    from src.framework.entities.player import Player
    from src.framework.stage.stage_loader import StageData


class HazardSystem:
    def __init__(self, context: GameContext) -> None:
        self._context = context
        self._death_timer: float = 0.0
        self._pending_death: bool = False

    def update(
        self, dt: float, player: Player, stage: StageData,
    ) -> None:
        if self._pending_death:
            self._death_timer -= dt
            if self._death_timer <= 0:
                self._context.event_bus.emit(Events.PLAYER_DIED)
                self._context.scene_manager.push(
                    GameOverScene(self._context, self._context.scene_manager.current)
                )
                self._pending_death = False
            return

        trigger_rect = player.rect.inflate(0, 2)

        for mt in stage.message_triggers:
            if not mt.triggered and trigger_rect.colliderect(mt.rect):
                mt.triggered = True
                self._context.event_bus.emit(
                    Events.SHOW_MESSAGE, text=mt.text, duration=8.0
                )

        for hz in stage.hazard_zones:
            if trigger_rect.colliderect(hz.rect):
                hz.timer -= dt
                if hz.timer <= 0 and player.rect is not None:
                    player.apply_damage(hz.damage, player.rect.center)
                    hz.timer = hz.cooldown
                    self._context.event_bus.emit(Events.SFX_HAZARD_ZONE)

        for dp in stage.death_pits:
            if trigger_rect.colliderect(dp.rect):
                self._kill_player()

    def _kill_player(self) -> None:
        self._pending_death = True
        self._death_timer = 0.3

    def reset(self) -> None:
        self._pending_death = False
        self._death_timer = 0.0
