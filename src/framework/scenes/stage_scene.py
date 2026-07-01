from __future__ import annotations

from pathlib import Path

import pygame

from src.engine.core import settings
from src.engine.core.event_bus import EventBus
from src.engine.scene.base_scene import BaseScene
from src.engine.ui.hud import HUD
from src.engine.ui.message_box import MessageBox
from src.engine.ui.screen_banner import ScreenBanner
from src.framework.entities.enemy_base import EnemyBase
from src.framework.entities.player import Player, PlayerState
from src.framework.stage.camera import Camera
from src.framework.stage.stage_loader import (
    StageLoader,
)


class StageScene(BaseScene):
    """Gameplay scene — loads a TMX stage and runs the full game loop."""

    def __init__(self, tmx_path: Path) -> None:
        self._tmx_path = tmx_path
        self._stage_data = None
        self._player: Player | None = None
        self._camera: Camera = Camera()
        self._hud: HUD = HUD()
        self._msg_box: MessageBox = MessageBox()
        self._banner: ScreenBanner = ScreenBanner()
        self._checkpoints: list = []
        self._checkpoint_reached: int | None = None
        self._stage_complete: bool = False
        self._game_over: bool = False

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
        self._game_over = False

        self._msg_box = MessageBox()
        self._banner = ScreenBanner()
        if self._stage_data.stage_name:
            self._banner.play(self._stage_data.stage_id, self._stage_data.stage_name)

        self._hud = HUD()
        if self._stage_data.time_limit > 0:
            self._hud.start_timer(self._stage_data.time_limit)
        else:
            self._hud.start_timer()

    def on_exit(self) -> None:
        self._stage_data = None
        self._player = None

    def _respawn(self) -> None:
        self._game_over = False
        self.on_enter()

    def _get_input_manager(self):
        from src.engine.core.app import App
        return App._input_manager if App._instance is not None else None

    def update(self, dt: float) -> None:
        if self._stage_data is None or self._player is None:
            return
        if self._stage_complete or self._game_over:
            return

        player = self._player
        stage = self._stage_data
        im = self._get_input_manager()

        player.update(dt, stage.collision_rects, im)

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

        # Check message triggers
        for mt in stage.message_triggers:
            if not mt.triggered and player.rect.colliderect(mt.rect):
                mt.triggered = True
                EventBus.emit("SHOW_MESSAGE", text=mt.text, duration=4.0)

        # Check hazard zones
        for hz in stage.hazard_zones:
            hz._timer -= dt
            if hz._timer <= 0 and player.rect.colliderect(hz.rect):
                player.apply_damage(hz.damage, player.rect.center)
                hz._timer = hz.cooldown

        # Check death pits
        for dp in stage.death_pits:
            if player.rect.colliderect(dp.rect):
                self._kill_player()
                return

        # Checkpoints
        for cp in self._checkpoints:
            cp.check_collision(player.rect)

        # Next trigger
        if stage.next_trigger and player.rect.colliderect(stage.next_trigger):
            self._stage_complete = True
            EventBus.emit("STAGE_COMPLETE", stage_id=stage.stage_id)

        # Player death
        if player.current_health <= 0 and player.state != PlayerState.DYING:
            self._kill_player()
            return

        self._msg_box.update(dt)
        self._banner.update(dt)
        self._hud.update(dt)

    def _kill_player(self) -> None:
        self._game_over = True
        EventBus.emit("PLAYER_DIED")
        from src.engine.core.app import App
        if App._instance is not None:
            from src.engine.scenes.game_over_scene import GameOverScene
            App._instance.scene_manager.push(GameOverScene(self))

    def draw(self, surface: pygame.Surface) -> None:
        if self._stage_data is None or self._player is None:
            return
        if self._game_over:
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

        self._msg_box.draw(surface)
        self._banner.draw(surface)
        self._hud.draw(surface)
