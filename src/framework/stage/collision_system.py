from __future__ import annotations

from typing import TYPE_CHECKING

from src.engine.core.events import Events
from src.framework.entities.enemy_base import EnemyBase

if TYPE_CHECKING:
    from src.engine.core.clock import DeltaClock
    from src.engine.core.event_bus import EventBus
    from src.engine.core.game_context import GameContext
    from src.framework.entities.player import Player
    from src.framework.stage.camera import Camera
    from src.framework.stage.stage_loader import StageData


class CollisionSystem:
    def __init__(self, context: GameContext) -> None:
        self._context = context
        self._hitstop_timer: float = 0.0

    def update_enemies(self, dt: float, player: Player, stage: StageData) -> None:
        for entity in stage.entity_list:
            from src.framework.entities.enemy_base import EnemyBase
            if isinstance(entity, EnemyBase):
                if hasattr(entity, "set_player_ref"):
                    entity.set_player_ref(player.rect)
                if entity.is_alive:
                    entity._check_player_contact(player)
            entity.update(dt)

    def process_attack(
        self, dt: float, player: Player, stage: StageData,
        camera: Camera, clock: DeltaClock | None,
    ) -> None:
        hitbox = player.active_hitbox
        if hitbox is None:
            return

        hit_any = False
        for entity in stage.entity_list:
            from src.framework.entities.enemy_base import EnemyBase
            if isinstance(entity, EnemyBase) and entity.is_alive:
                if hitbox.colliderect(entity.hurtbox):
                    entity.apply_hit(player.current_attack_damage, player.rect.center)
                    hit_any = True
                    self._context.event_bus.emit(Events.SFX_ENEMY_HIT)

        if not hit_any:
            return

        player.consume_hitbox()
        self._context.event_bus.emit(Events.SFX_HIT_CONNECT)
        hitstop_frames = 4.0 if player.current_attack_damage >= 1.0 else 2.0
        if clock is not None:
            clock.time_scale = 0.15
            self._hitstop_timer = hitstop_frames / 60.0
        if getattr(player, "combo_count", 0) > 1:
            amp = min(2.0, 0.5 * player.combo_count)
            camera.apply_shake(amplitude=amp, duration=0.1)

    def update_hitstop(self, dt: float, clock: DeltaClock | None) -> None:
        if self._hitstop_timer > 0:
            self._hitstop_timer -= dt
            if self._hitstop_timer <= 0 and clock is not None:
                clock.time_scale = 1.0

    def reset(self) -> None:
        self._hitstop_timer = 0.0
