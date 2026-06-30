from __future__ import annotations

from pathlib import Path

import pygame

from src.engine.core import settings
from src.engine.core.event_bus import EventBus
from src.engine.scene.base_scene import BaseScene
from src.engine.ui.hud import HUD
from src.framework.entities.enemy_base import EnemyBase
from src.framework.entities.player import Player
from src.framework.stage.camera import Camera
from src.framework.stage.stage_loader import StageLoader
from src.framework.stage.checkpoint import Checkpoint


class StageScene(BaseScene):
    """Gameplay scene — loads a TMX stage via StageLoader and runs the game loop."""

    def __init__(self, tmx_path: Path) -> None:
        self._tmx_path = tmx_path
        self._stage_data = None
        self._player: Player | None = None
        self._camera: Camera = Camera()
        self._hud: HUD = HUD()
        self._checkpoints: list[Checkpoint] = []
        self._checkpoint_reached: int | None = None
        self._stage_complete: bool = False

    def on_enter(self) -> None:
        self._stage_data = StageLoader.load(self._tmx_path)

        spawn = self._stage_data.spawn_point
        self._player = Player(spawn)

        self._camera = Camera()
        self._camera.follow(self._player)
        self._camera.set_map_size(*self._stage_data.map_pixel_size)

        for enemy in self._stage_data.entity_list:
            if hasattr(enemy, "set_player_ref"):
                enemy.set_player_ref(self._player.rect)
            if hasattr(enemy, "set_collision_rects"):
                enemy.set_collision_rects(self._stage_data.collision_rects)

        self._checkpoints = list(self._stage_data.checkpoints)
        self._checkpoint_reached = None
        self._stage_complete = False

        self._hud = HUD()
        if self._stage_data.time_limit > 0:
            self._hud.start_timer(self._stage_data.time_limit)
        else:
            self._hud.start_timer()

    def on_exit(self) -> None:
        self._stage_data = None
        self._player = None

    def _respawn(self) -> None:
        self.on_enter()

    def update(self, dt: float) -> None:
        if self._stage_data is None or self._player is None:
            return

        if self._stage_complete:
            return

        player = self._player
        stage = self._stage_data

        player.update(dt, stage.collision_rects)

        for entity in stage.entity_list:
            if isinstance(entity, EnemyBase):
                if hasattr(entity, "_player_ref"):
                    entity._player_ref = player.rect
                if entity.is_alive:
                    entity._check_player_contact(player)
            entity.update(dt)

        self._camera.update(dt)

        center_x = self._camera.offset.x + settings.INTERNAL_WIDTH / 2
        center_y = self._camera.offset.y + settings.INTERNAL_HEIGHT / 2
        stage.map_layer.center((center_x, center_y))

        for cp in self._checkpoints:
            if not cp.is_activated and cp.rect.colliderect(player.rect):
                cp.activate()
                self._checkpoint_reached = cp.checkpoint_id
                EventBus.emit("CHECKPOINT_REACHED", checkpoint_id=cp.checkpoint_id)

        if stage.next_trigger and player.rect.colliderect(stage.next_trigger):
            self._stage_complete = True
            EventBus.emit("STAGE_COMPLETE", stage_id=stage.stage_id)

        if self._player.current_health <= 0:
            self._respawn()
            return

        self._hud.update(dt)

    def draw(self, surface: pygame.Surface) -> None:
        if self._stage_data is None or self._player is None:
            return

        surface.fill(settings.BG_COLOR)

        stage = self._stage_data
        stage.map_layer.draw(surface)

        cam_offset = self._camera.offset

        self._player.draw(surface, cam_offset)

        for entity in stage.entity_list:
            if isinstance(entity, EnemyBase) and entity.is_alive:
                entity.draw(surface, cam_offset)
            else:
                entity.draw(surface, cam_offset)

        for cp in self._checkpoints:
            cp.draw(surface, cam_offset)

        self._hud.draw(surface)
