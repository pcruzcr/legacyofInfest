from __future__ import annotations

from typing import TYPE_CHECKING

from src.engine.core.events import Events
if TYPE_CHECKING:
    from src.engine.core.clock import DeltaClock
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
        is_slam = getattr(player, "_state_instance", None) is not None and \
            type(player._state_instance).__name__ == "AerialSlamState"

        for entity in stage.entity_list:
            from src.framework.entities.enemy_base import EnemyBase
            if isinstance(entity, EnemyBase) and entity.is_alive:
                if hitbox.colliderect(entity.hurtbox):
                    if is_slam:
                        entity._knockback_velocity.y = 400.0
                        entity._knockback_velocity.x = 0.0
                        entity._hurt_timer = 0.4
                    entity.apply_hit(player.current_attack_damage, player.rect.center)
                    hit_any = True
                    hit_pos = list(entity.rect.center)
                    self._context.event_bus.emit(
                        Events.SFX_ENEMY_HIT,
                        pos=hit_pos, damage=player.current_attack_damage,
                    )
                    # Air combo bounce
                    if not player.is_grounded and not is_slam:
                        player.velocity.y = -250.0
                    # Special meter gain
                    player.special_meter = min(
                        player.special_meter_max,
                        player.special_meter + player.current_attack_damage * 8.0,
                    )

        if not hit_any:
            return

        player.consume_hitbox()
        self._context.event_bus.emit(
            Events.SFX_HIT_CONNECT,
            pos=list(player.rect.center),
            damage=player.current_attack_damage,
        )
        hitstop_frames = 6.0 if is_slam else (4.0 if player.current_attack_damage >= 1.0 else 2.0)
        if clock is not None:
            clock.time_scale = 0.15
            self._hitstop_timer = hitstop_frames / 60.0
        amp = min(4.0 if is_slam else 2.0, 0.5 * getattr(player, "combo_count", 1))
        camera.apply_shake(amplitude=amp, duration=0.1 if not is_slam else 0.2)

    def update_hitstop(self, dt: float, clock: DeltaClock | None) -> None:
        if self._hitstop_timer > 0:
            self._hitstop_timer -= dt
            if self._hitstop_timer <= 0 and clock is not None:
                clock.time_scale = 1.0

    def reset(self) -> None:
        self._hitstop_timer = 0.0
