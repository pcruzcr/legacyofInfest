from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pygame

from src.engine.core.events import Events
if TYPE_CHECKING:
    from src.engine.core.clock import DeltaClock
    from src.engine.core.game_context import GameContext
    from src.framework.entities.player import Player
    from src.framework.stage.camera import Camera
    from src.framework.stage.stage_loader import StageData


class SpatialGrid:
    """Simple spatial hash grid for broad-phase entity lookups.
    Cell size of ~64px. Entities register their position each frame."""

    def __init__(self, cell_size: int = 64) -> None:
        self.cell_size = cell_size
        self.cells: dict[tuple[int, int], list[Any]] = {}

    def clear(self) -> None:
        self.cells.clear()

    def _cell_key(self, x: float, y: float) -> tuple[int, int]:
        return (int(x // self.cell_size), int(y // self.cell_size))

    def insert(self, entity: Any, rect: pygame.Rect) -> None:
        tl = self._cell_key(rect.left, rect.top)
        br = self._cell_key(rect.right, rect.bottom)
        for cx in range(tl[0], br[0] + 1):
            for cy in range(tl[1], br[1] + 1):
                key = (cx, cy)
                if key not in self.cells:
                    self.cells[key] = []
                self.cells[key].append(entity)

    def get_nearby(self, rect: pygame.Rect) -> list[Any]:
        tl = self._cell_key(rect.left, rect.top)
        br = self._cell_key(rect.right, rect.bottom)
        seen: set[int] = set()
        result: list[Any] = []
        for cx in range(tl[0], br[0] + 1):
            for cy in range(tl[1], br[1] + 1):
                for entity in self.cells.get((cx, cy), []):
                    eid = id(entity)
                    if eid not in seen:
                        seen.add(eid)
                        result.append(entity)
        return result


class CollisionSystem:
    def __init__(self, context: GameContext) -> None:
        self._context = context
        self._hitstop_timer: float = 0.0
        self._spatial_grid: SpatialGrid = SpatialGrid(cell_size=64)

    def build_spatial_grid(self, stage: StageData) -> None:
        self._spatial_grid.clear()
        from src.framework.entities.enemy_base import EnemyBase
        for entity in stage.entity_list:
            if isinstance(entity, EnemyBase) and entity.is_alive:
                self._spatial_grid.insert(entity, entity.hurtbox)

    def update_enemies(self, dt: float, player: Player, stage: StageData) -> None:
        self.build_spatial_grid(stage)
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
        state_instance = getattr(player, "_state_instance", None)
        is_slam = False
        if state_instance is not None:
            from src.framework.entities.player_states import AerialSlamState
            is_slam = isinstance(state_instance, AerialSlamState)

        from src.framework.entities.enemy_base import EnemyBase
        nearby = self._spatial_grid.get_nearby(hitbox)
        for entity in nearby:
            if isinstance(entity, EnemyBase) and entity.is_alive:
                if hitbox.colliderect(entity.hurtbox):
                    entity.apply_hit(player.current_attack_damage, player.rect.center)
                    if is_slam and entity.is_alive:
                        entity._knockback_velocity.y = 400.0
                        entity._knockback_velocity.x = 0.0
                        entity._hurt_timer = 0.4
                    hit_any = True
                    hit_pos = list(entity.rect.center)
                    self._context.event_bus.emit(
                        Events.SFX_ENEMY_HIT,
                        pos=hit_pos, damage=player.current_attack_damage,
                    )
                    if not player.is_grounded and not is_slam:
                        player.velocity.y = min(player.velocity.y, -250.0)
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
            if self._hitstop_timer <= 0:
                clock.time_scale = 0.15
            self._hitstop_timer = hitstop_frames / 60.0
        amp = min(4.0 if is_slam else 2.0, 0.5 * max(1, getattr(player, "combo_count", 0)))
        camera.apply_shake(amplitude=amp, duration=0.1 if not is_slam else 0.2)

    def update_hitstop(self, dt: float, clock: DeltaClock | None) -> None:
        if self._hitstop_timer > 0:
            self._hitstop_timer -= dt
            if self._hitstop_timer <= 0 and clock is not None:
                clock.time_scale = 1.0

    def reset(self) -> None:
        self._hitstop_timer = 0.0
        self._spatial_grid.clear()