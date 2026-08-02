from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from src.engine.core import settings
from src.engine.core.events import Events
from src.framework.entities.boss_base import BossBase

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext
    from src.engine.ui.hud import HUD
    from src.framework.entities.player import Player
    from src.framework.stage.checkpoint import Checkpoint
    from src.framework.stage.stage_loader import StageData


class ProgressionSystem:
    def __init__(self, context: GameContext) -> None:
        self._context = context
        self._stage_complete: bool = False
        self._complete_timer: float = 0.0

    def process_checkpoints(
        self, player: Player, stage: StageData,
        checkpoints: list[Checkpoint], hud: HUD | None,
        stage_key: str = "",
    ) -> pygame.Vector2 | None:
        """AUD-156 — `stage_key` es la identidad única del escenario.

        Se pasa desde la escena porque aquí sólo hay `StageData`, y el
        `stage_id` del TMX no siempre coincide con el que el resto del juego
        usa: `lobby_datacenter` guarda `stage_template` en su mapa. Guardar con
        un identificador y buscarlo con otro es lo que dejaba al jugador al
        principio del nivel al cargar. Por defecto cae al del mapa para no
        romper a quien llame a este método con la firma vieja.
        """
        if stage is None or player is None:
            return None
        clave = stage_key or stage.stage_id
        checkpoint_position: pygame.Vector2 | None = None
        for cp in checkpoints:
            if not cp.is_activated and cp.check_collision(player.rect):
                checkpoint_position = pygame.Vector2(cp.rect.center)
                self._context.event_bus.emit(Events.SFX_CHECKPOINT)
                if player.current_health < settings.PLAYER_MAX_HEALTH:
                    heal_amount = settings.PLAYER_MAX_HEALTH - player.current_health
                    player.heal(heal_amount)
                    self._context.event_bus.emit(
                        Events.PLAYER_HEALED, amount=heal_amount
                    )
                self._context.event_bus.emit(
                    Events.SAVE_REQUESTED,
                    stage_id=clave,
                    stage_index=self._context.scene_manager.stage_index,
                    checkpoint_x=player.rect.centerx,
                    checkpoint_y=player.rect.centery,
                    health=player.current_health,
                    max_health=settings.PLAYER_MAX_HEALTH,
                )
                if hud is not None:
                    hud.trigger_save_notification()
        return checkpoint_position

    def check_next_trigger(self, player: Player, stage: StageData) -> bool:
        if not self._stage_complete and stage.next_trigger is not None:
            if player.rect.colliderect(stage.next_trigger):
                self._stage_complete = True
                self._complete_timer = 2.9
                return True
        return False

    def check_boss_defeat(self, stage: StageData) -> bool:
        if self._stage_complete:
            return False
        for entity in stage.entity_list:
            if (
                isinstance(entity, BossBase)
                and not entity.is_alive
                and entity.death_timer <= 0
                and not entity.completion_fired
            ):
                entity.completion_fired = True
                self._stage_complete = True
                self._complete_timer = 2.9
                return True
        return False

    def update_complete_timer(self, dt: float) -> bool:
        if not self._stage_complete:
            return False
        self._complete_timer -= dt
        return self._complete_timer <= 0

    @property
    def stage_complete(self) -> bool:
        return self._stage_complete

    @stage_complete.setter
    def stage_complete(self, value: bool) -> None:
        self._stage_complete = value

    @property
    def complete_timer(self) -> float:
        return self._complete_timer

    def reset(self) -> None:
        self._stage_complete = False
        self._complete_timer = 0.0
