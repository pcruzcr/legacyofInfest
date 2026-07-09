from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pygame

from src.engine.core import settings
from src.engine.input.action_map import Action
from src.engine.core.events import Events
from src.engine.scene.base_scene import BaseScene
from src.engine.ui.hud import HUD
from src.engine.utils.asset_loader import AssetLoader
from src.engine.ui.message_box import MessageBox
from src.engine.ui.screen_banner import ScreenBanner
from src.framework.entities.boss_base import BossBase
from src.framework.entities.enemy_base import EnemyBase
from src.framework.entities.player import Player
from src.framework.stage.camera import Camera
from src.framework.stage.stage_loader import StageLoader
from src.framework.stage.collision_system import CollisionSystem
from src.framework.stage.hazard_system import HazardSystem
from src.framework.stage.progression_system import ProgressionSystem
from src.framework.stage.drawing_system import DrawingSystem

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext


class StageScene(BaseScene):
    def __init__(self, context: GameContext, tmx_path: Path) -> None:
        super().__init__(context)
        self._tmx_path = tmx_path
        self._stage_data = None
        self._player: Player | None = None
        self._camera: Camera = Camera()
        self._hud: HUD | None = None
        self._msg_box: MessageBox | None = None
        self._banner: ScreenBanner | None = None
        self._checkpoints: list = []
        self._checkpoint_reached: int | None = None
        self._checkpoint_position: pygame.Vector2 | None = None
        self._stage_complete: bool = False
        self._game_over: bool = False
        self._paused: bool = False
        self._pause_selected: int = 0
        self._pause_options: list[str] = ["Resume", "Save & Quit", "Quit to Title"]
        self._debug: bool = False
        self._was_grounded: bool = False
        self._pending_game_over: bool = False

        self._collision = CollisionSystem(context)
        self._hazards = HazardSystem(context)
        self._progression = ProgressionSystem(context)
        self._drawing = DrawingSystem()

    def on_stage_start(self) -> None: ...
    def on_player_landed(self) -> None: ...
    def on_enemy_died(self, enemy: EnemyBase) -> None: ...
    def on_next_trigger_entered(self) -> None: ...
    def on_debug_toggle(self, enabled: bool) -> None: ...

    def on_enter(self) -> None:
        self._stage_data = StageLoader.load(self._tmx_path)
        spawn = self._stage_data.spawn_point
        self._player = Player(spawn)

        pending = self.context.pending_load
        if pending is not None and pending.stage_id == self._stage_data.stage_id:
            self._player.set_spawn(pygame.Vector2(pending.checkpoint_x, pending.checkpoint_y))
            self._player._health = min(pending.health, pending.max_health)
            self._checkpoint_position = pygame.Vector2(pending.checkpoint_x, pending.checkpoint_y)
            self.context.pending_load = None

        self._camera = Camera()
        self._camera.follow(self._player)
        self._camera.set_map_size(*self._stage_data.map_pixel_size)

        for enemy in self._stage_data.entity_list:
            if hasattr(enemy, "set_player_ref"):
                enemy.set_player_ref(self._player.rect)
            if hasattr(enemy, "set_collision_rects"):
                enemy.set_collision_rects(
                    self._stage_data.collision_rects,
                    one_way=self._stage_data.one_way_rects,
                )

        self._checkpoints = list(self._stage_data.checkpoints)
        self._checkpoint_position = None
        self._stage_complete = False
        self._game_over = False
        self._pending_game_over = False
        self._was_grounded = False
        self._collision.reset()
        self._hazards.reset()
        self._progression.reset()

        if self._stage_data.bgm_track:
            audio = self.audio
            if audio is not None:
                bgm_path = Path("assets/music") / f"{self._stage_data.bgm_track}.wav"
                audio.play_music(bgm_path)

        self._msg_box = MessageBox(self.context.event_bus)
        self._banner = ScreenBanner()
        if self._stage_data.stage_name:
            self._banner.play(self._stage_data.stage_id, self._stage_data.stage_name)
            self.context.event_bus.emit(Events.SFX_STAGE_BANNER)

        self._hud = HUD(self.context.event_bus)
        if self._stage_data.time_limit > 0:
            self._hud.start_timer(self._stage_data.time_limit)
        else:
            self._hud.start_timer()

        self.on_stage_start()

        self._sfx_handlers: dict[str, object] = {}
        sfx_map = {
            Events.SFX_PLAYER_JUMP: "sfx_player_jump",
            Events.SFX_PLAYER_LAND: "sfx_player_land",
            Events.SFX_PLAYER_SHORT_ATTACK: "sfx_player_short_attack",
            Events.SFX_PLAYER_LONG_ATTACK: "sfx_player_long_attack",
            Events.SFX_PLAYER_HURT: "sfx_player_hurt",
            Events.SFX_PLAYER_DIE: "sfx_player_die",
            Events.SFX_HIT_CONNECT: "sfx_player_hit_connect",
            Events.SFX_ENEMY_HIT: "sfx_enemies_hit",
            Events.SFX_ENEMY_DIE_SMALL: "sfx_enemies_die_small",
            Events.SFX_ENEMY_DIE_LARGE: "sfx_enemies_die_large",
            Events.SFX_PROJECTILE_FIRE: "sfx_enemies_projectile_fire",
            Events.SFX_CHECKPOINT: "sfx_ui_checkpoint",
            Events.SFX_STAGE_BANNER: "sfx_ui_stage_banner",
            Events.SFX_STAGE_COMPLETE: "sfx_ui_stage_complete",
            Events.SFX_HAZARD_ZONE: "sfx_environment_hazard_zone",
        }
        self._sfx_names = sfx_map
        for evt, sname in sfx_map.items():
            def _make_handler(n):
                def handler(**d):
                    self._play_sfx_named(n)
                return handler
            handler = _make_handler(sname)
            self.context.event_bus.subscribe(evt, handler)
            self._sfx_handlers[evt] = handler

    def _play_sfx_named(self, name: str) -> None:
        audio = self.audio
        if audio is not None:
            audio.play_sfx(name)

    def on_exit(self) -> None:
        if self.context.clock is not None:
            self.context.clock.time_scale = 1.0
        for evt, handler in self._sfx_handlers.items():
            self.context.event_bus.unsubscribe(evt, handler)
        self._sfx_handlers.clear()
        if self._hud is not None:
            self._hud.destroy()
            self._hud = None
        if self._msg_box is not None:
            self._msg_box.destroy()
            self._msg_box = None
        audio = self.audio
        if audio is not None:
            audio.stop_music()
        AssetLoader.clear_cache()
        self._stage_data = None
        self._player = None

    def respawn(self) -> None:
        if self.context.clock is not None:
            self.context.clock.time_scale = 1.0
        self._game_over = False
        saved_time = self._hud.current_time if self._hud is not None else 0.0
        saved_time_limit = self._hud.time_limit if self._hud is not None else 0
        cp = self._checkpoint_position
        if self._hud is not None:
            self._hud.destroy()
            self._hud = None
        if self._msg_box is not None:
            self._msg_box.destroy()
            self._msg_box = None
        self.on_enter()
        self._hud.current_time = saved_time
        self._hud.is_countdown = saved_time_limit > 0
        if cp is not None:
            self._player.position = pygame.Vector2(cp)
            self._player.rect.center = (int(cp.x), int(cp.y))
        self._player._invincibility_timer = 2.0

    def update(self, dt: float) -> None:
        if self._stage_data is None or self._player is None:
            return
        if self._game_over:
            return

        player = self._player
        stage = self._stage_data
        im = self.input

        if im:
            if im.is_action_just_pressed(Action.PAUSE):
                self._paused = not self._paused
                self._pause_selected = 0
            if hasattr(pygame.key, 'get_just_pressed') and pygame.key.get_just_pressed()[pygame.K_F1]:
                self._debug = not self._debug
                self.on_debug_toggle(self._debug)

        if self._paused:
            if im:
                if im.is_action_just_pressed(Action.MOVE_DOWN):
                    self._pause_selected = (self._pause_selected + 1) % len(self._pause_options)
                if im.is_action_just_pressed(Action.MOVE_UP):
                    self._pause_selected = (self._pause_selected - 1) % len(self._pause_options)
                if im.is_action_just_pressed(Action.CANCEL):
                    self._paused = False
                if im.is_action_pressed(Action.CONFIRM):
                    choice = self._pause_options[self._pause_selected]
                    if choice == "Resume":
                        self._paused = False
                    elif choice == "Save & Quit":
                        self._save_and_quit()
                    elif choice == "Quit to Title":
                        self._quit_to_title()
            return

        original_time_scale = 1.0
        if self.context.clock is not None:
            original_time_scale = self.context.clock.time_scale
        try:
            player.update(dt, stage.collision_rects, im, one_way_rects=stage.one_way_rects)

            if player.is_grounded and not self._was_grounded:
                self.on_player_landed()
            self._was_grounded = player.is_grounded

            for entity in stage.entity_list:
                if isinstance(entity, EnemyBase) and not entity.is_alive:
                    if getattr(entity, "_was_alive", True):
                        entity._was_alive = False
                        self.on_enemy_died(entity)

            self._collision.update_enemies(dt, player, stage)
            self._collision.process_attack(dt, player, stage, self._camera, self.context.clock)
        finally:
            self._collision.update_hitstop(dt, self.context.clock)
            if self._collision._hitstop_timer <= 0 and self.context.clock is not None:
                self.context.clock.time_scale = original_time_scale

        self._camera.update(dt)

        center_x = self._camera.offset.x + settings.INTERNAL_WIDTH / 2
        center_y = self._camera.offset.y + settings.INTERNAL_HEIGHT / 2
        stage.map_layer.center((center_x, center_y))

        self._camera.set_camera_locks(stage.camera_locks)

        cp_pos = self._progression.process_checkpoints(player, stage, self._checkpoints, self._hud)
        if cp_pos is not None:
            self._checkpoint_position = cp_pos

        if self._progression.check_next_trigger(player, stage):
            self.on_next_trigger_entered()
            self._banner.play("STAGE_COMPLETE", "STAGE COMPLETE")
            self.context.event_bus.emit(Events.SFX_STAGE_COMPLETE)

        if self._progression.check_boss_defeat(stage):
            self._banner.play("STAGE_COMPLETE", "STAGE COMPLETE")
            self.context.event_bus.emit(Events.SFX_STAGE_COMPLETE)

        if self._progression.update_complete_timer(dt):
            self.context.event_bus.emit(Events.STAGE_COMPLETE, stage_id=stage.stage_id)
            return

        if self._progression.stage_complete:
            if self._msg_box:
                self._msg_box.update(dt)
            if self._banner:
                self._banner.update(dt)
            return

        if self._hud:
            boss_found = False
            for entity in stage.entity_list:
                if isinstance(entity, BossBase) and entity.is_alive:
                    self._hud.set_boss_hud(
                        entity._boss_name,
                        entity.current_health,
                        entity._phase_max_health,
                        getattr(entity, "current_phase", 0) + 1,
                        getattr(entity, "phase_count", 1),
                    )
                    boss_found = True
                    break
            if not boss_found:
                self._hud.clear_boss_hud()

        if self._msg_box:
            self._msg_box.update(dt)
            if self._msg_box.is_dismiss_on_confirm and im.is_action_just_pressed(Action.CONFIRM):
                self._msg_box.hide()
        if self._banner:
            self._banner.update(dt)
        if self._hud:
            self._hud.set_combo_count(player.combo_count)
            self._hud.update(dt)

        self._hazards.update(dt, player, stage)

        if player.current_health <= 0 and not self._game_over:
            self._kill_player()
            return

        if self._hud and self._hud.current_time <= 0 and self._hud.is_countdown and not self._game_over:
            self._kill_player()
            return

    def _save_and_quit(self) -> None:
        sm = self.context.save_manager
        if sm is not None and self._stage_data is not None and self._player is not None:
            sm.auto_save(
                stage_id=self._stage_data.stage_id,
                stage_index=self.context.scene_manager.stage_index,
                checkpoint_x=self._player.rect.centerx,
                checkpoint_y=self._player.rect.centery,
                health=self._player.current_health,
                max_health=settings.PLAYER_MAX_HEALTH,
            )
        self._quit_to_title()

    def _quit_to_title(self) -> None:
        from src.engine.scenes.title_scene import TitleScene
        self.context.scene_manager.replace(TitleScene(self.context))

    def _kill_player(self) -> None:
        self._game_over = True
        self.context.event_bus.emit(Events.PLAYER_DIED)
        from src.engine.scenes.game_over_scene import GameOverScene
        self.context.scene_manager.push(GameOverScene(self.context, self))

    def draw(self, surface: pygame.Surface) -> None:
        self._drawing.draw(
            surface, self._stage_data, self._player, self._checkpoints,
            self._camera, self._hud, self._msg_box, self._banner,
            self._paused, self._debug, self._pause_selected, self._pause_options,
        )
