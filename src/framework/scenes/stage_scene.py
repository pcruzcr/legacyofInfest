from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pygame

from src.engine.core import settings
from src.engine.core.event_bus import emit
from src.engine.input.action_map import Action
from src.engine.core.events import Events
from src.engine.scene.base_scene import BaseScene
from src.engine.ui.hud import HUD
from src.engine.ui.message_box import MessageBox
from src.engine.ui.screen_banner import ScreenBanner
from src.framework.entities.enemy_base import EnemyBase
from src.framework.entities.player import Player
from src.framework.stage.camera import Camera
from src.framework.stage.stage_loader import (
    StageLoader,
)

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext


class StageScene(BaseScene):
    """Gameplay scene — loads a TMX stage and runs the full game loop."""

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
        self._stage_complete: bool = False
        self._game_over: bool = False
        self._paused: bool = False

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
        self._checkpoint_position: pygame.Vector2 | None = None
        self._stage_complete = False
        self._game_over = False
        self._hitstop_timer: float = 0.0

        # Play BGM if specified in TMX
        if self._stage_data.bgm_track:
            audio = self.audio
            if audio is not None:
                from pathlib import Path
                bgm_path = Path("assets/music") / f"{self._stage_data.bgm_track}.wav"
                audio.play_music(bgm_path)

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
        #
        # Cleanup: destruir HUD y MessageBox antes de descartarlos
        # para evitar acumulación de suscripciones al EventBus.
        #
        if self._hud is not None:
            self._hud.destroy()
            self._hud = None
        if self._msg_box is not None:
            self._msg_box.destroy()
            self._msg_box = None
        audio = self.audio
        if audio is not None:
            audio.stop_music()
        self._stage_data = None
        self._player = None

    def respawn(self) -> None:
        """Reload the stage and place player at last checkpoint (or spawn point)."""
        self._game_over = False
        # Preserve timer and checkpoint across respawn
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
        # Restore timer from before death
        self._hud.current_time = saved_time
        self._hud.is_countdown = saved_time_limit > 0
        if cp is not None:
            self._player.position = pygame.Vector2(cp)
            self._player.rect.center = (int(cp.x), int(cp.y))

        # 2 seconds of invincibility after respawn
        self._player._invincibility_timer = 2.0

    def update(self, dt: float) -> None:
        if self._stage_data is None or self._player is None:
            return
        if self._game_over:
            return

        player = self._player
        stage = self._stage_data
        im = self.input

        if im and im.is_action_just_pressed(Action.PAUSE):
            self._paused = not getattr(self, '_paused', False)
        if getattr(self, '_paused', False):
            return

        player.update(dt, stage.collision_rects, im, one_way_rects=stage.one_way_rects)

        for entity in stage.entity_list:
            if isinstance(entity, EnemyBase):
                if hasattr(entity, "set_player_ref"):
                    entity.set_player_ref(player.rect)
                if entity.is_alive:
                    entity.check_player_contact(player)
            entity.update(dt)

        # Player attack hitbox → enemy hurtbox collision
        hitbox = player.active_hitbox
        if hitbox is not None:
            for entity in stage.entity_list:
                if isinstance(entity, EnemyBase) and entity.is_alive:
                    if hitbox.colliderect(entity.hurtbox):
                        entity.apply_hit(player.current_attack_damage, player.rect.center)
                        player.consume_hitbox()
                        # Hitstop: 2 frames for short attack (0.5), 4 frames for long attack (1.0)
                        hitstop_frames = 4.0 if player.current_attack_damage >= 1.0 else 2.0
                        if hasattr(self.context, "clock") and self.context.clock is not None:
                            self.context.clock.time_scale = 0.15
                            self._hitstop_timer = hitstop_frames / 60.0
                        break

        # Hitstop timer — restore time_scale when expired
        if self._hitstop_timer > 0:
            self._hitstop_timer -= dt
            if self._hitstop_timer <= 0:
                if self.context.clock is not None:
                    self.context.clock.time_scale = 1.0

        self._camera.update(dt)

        center_x = self._camera.offset.x + settings.INTERNAL_WIDTH / 2
        center_y = self._camera.offset.y + settings.INTERNAL_HEIGHT / 2
        stage.map_layer.center((center_x, center_y))

        # Check message triggers
        for mt in stage.message_triggers:
            if not mt.triggered and player.rect.colliderect(mt.rect):
                mt.triggered = True
                emit(Events.SHOW_MESSAGE, text=mt.text, duration=4.0)

        # Check hazard zones
        for hz in stage.hazard_zones:
            hz.timer -= dt
            if hz.timer <= 0 and player.rect.colliderect(hz.rect):
                player.apply_damage(hz.damage, player.rect.center)
                hz.timer = hz.cooldown

        # Check death pits
        for dp in stage.death_pits:
            if player.rect.colliderect(dp.rect):
                self._kill_player()
                return

        # Camera locks — enforce lock zones
        self._camera.set_camera_locks(stage.camera_locks)

        # Checkpoints — restore health and track latest activated position
        for cp in self._checkpoints:
            if cp.check_collision(player.rect):
                self._checkpoint_position = pygame.Vector2(cp.rect.center)
                if player.current_health < settings.PLAYER_MAX_HEALTH:
                    heal_amount = settings.PLAYER_MAX_HEALTH - player.current_health
                    player.heal(heal_amount)
                    emit(Events.PLAYER_HEALED, amount=heal_amount)

        # Next trigger
        if not self._stage_complete and stage.next_trigger and player.rect.colliderect(stage.next_trigger):
            self._stage_complete = True
            self._stage_complete_timer = 2.0
            self._banner.play("STAGE_COMPLETE", "STAGE COMPLETE")

        # Delayed stage complete emission (gives banner time to display)
        if self._stage_complete and hasattr(self, "_stage_complete_timer"):
            self._stage_complete_timer -= dt
            if self._msg_box:
                self._msg_box.update(dt)
            if self._banner:
                self._banner.update(dt)
            if self._stage_complete_timer <= 0:
                emit(Events.STAGE_COMPLETE, stage_id=stage.stage_id)
                return
            return

        # Update boss HUD
        if self._hud:
            boss_found = False
            for entity in stage.entity_list:
                if hasattr(entity, "_boss_name") and entity.is_alive:
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
            self._hud.update(dt)

        # Player death (health-based)
        if player.current_health <= 0 and not self._game_over:
            self._kill_player()
            return

        # Timer expiry death (HUD emits PLAYER_DIED for portrait update)
        if self._hud and self._hud.current_time <= 0 and self._hud.is_countdown and not self._game_over:
            self._kill_player()
            return

    def _kill_player(self) -> None:
        self._game_over = True
        emit(Events.PLAYER_DIED)
        from src.engine.scenes.game_over_scene import GameOverScene
        self.context.scene_manager.push(GameOverScene(self.context, self))

    def draw(self, surface: pygame.Surface) -> None:
        if self._stage_data is None or self._player is None:
            return
        if self._game_over:
            return

        surface.fill(settings.BG_COLOR)
        stage = self._stage_data
        # Draw parallax background layers (loaded from assets/backgrounds/)
        bg_layers = stage.background_layers
        bg_names = ("BG_Far", "BG_Mid", "BG_Near")
        for i, bg_surf in enumerate(bg_layers):
            layer_name = bg_names[i] if i < len(bg_names) else "BG_Far"
            off = self._camera.layer_offset(layer_name)
            bg_w = bg_surf.get_width()
            bg_h = bg_surf.get_height()
            # Tile the background to fill the screen
            for bx in range(0, settings.INTERNAL_WIDTH, bg_w):
                for by in range(0, settings.INTERNAL_HEIGHT, bg_h):
                    surface.blit(bg_surf, (bx - int(off.x * 0.15 * (i + 1)),
                                           by - int(off.y * 0.15 * (i + 1))))
        stage.map_layer.draw(surface)
        cam_offset = self._camera.offset

        # Y-sort all world-space entities (player + enemies + checkpoints)
        drawables = [(self._player, self._player.rect.centery)]
        for entity in stage.entity_list:
            if not isinstance(entity, EnemyBase) or entity.is_alive:
                drawables.append((entity, entity.rect.centery))
        for cp in self._checkpoints:
            drawables.append((cp, cp.rect.centery))
        drawables.sort(key=lambda x: x[1])
        for obj, _ in drawables:
            obj.draw(surface, cam_offset)

        if self._msg_box:
            self._msg_box.draw(surface)
        if self._banner:
            self._banner.draw(surface)
        if self._hud:
            self._hud.draw(surface)

        if getattr(self, '_paused', False):
            s = pygame.Surface((settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT))
            s.set_alpha(160)
            s.fill((0, 0, 0))
            surface.blit(s, (0, 0))
            pause_font = pygame.font.Font(None, 20)
            pause_text = pause_font.render("PAUSED", True, (255, 255, 255))
            pt_x = (settings.INTERNAL_WIDTH - pause_text.get_width()) // 2
            pt_y = (settings.INTERNAL_HEIGHT - pause_text.get_height()) // 2
            surface.blit(pause_text, (pt_x, pt_y))
