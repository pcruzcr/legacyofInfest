from __future__ import annotations

import random
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable

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
from src.framework.vfx.particle_system import ParticleSystem
from src.framework.vfx.damage_numbers import DamageNumberManager
from src.framework.vfx.hit_effects import HitEffects
from src.framework.vfx.post_processing import PostProcessing
from src.framework.vfx.lighting import LightSystem, LightSource
from src.framework.vfx.ambient_particles import AmbientParticleSystem
from src.framework.vfx.weather_system import WeatherSystem
from src.framework.vfx.trail_system import TrailSystem
from src.framework.audio.dynamic_music import DynamicMusicSystem
from src.framework.ui.tutorial_overlay import TutorialOverlay
from src.framework.ui.learning_overlay import LearningOverlay
from src.framework.ui.dialogue_system import DialogueSystem
from src.framework.entities.bestiary import Bestiary
from src.framework.stage.speedrun_mode import SpeedrunTimer
from src.engine.ui.minimap import Minimap
from src.engine.core.achievements import AchievementSystem
from src.engine.core.inventory import get_inventory

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext
    from src.framework.stage.checkpoint import Checkpoint
    from src.framework.stage.stage_loader import StageData


class StageScene(BaseScene):
    def __init__(self, context: GameContext, tmx_path: Path) -> None:
        self._tutorial_shown: set[str] = set()
        super().__init__(context)
        self._tmx_path = tmx_path
        self._stage_data: StageData | None = None
        self._player: Player | None = None
        self._camera: Camera = Camera()
        self._hud: HUD | None = None
        self._msg_box: MessageBox | None = None
        self._banner: ScreenBanner | None = None
        self._checkpoints: list[Checkpoint] = []
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
        self._particle_system = ParticleSystem()
        self._damage_numbers = DamageNumberManager()
        self._post_processing = PostProcessing()
        self._ambient_particles = AmbientParticleSystem()
        self._weather = WeatherSystem()
        self._trail_system = TrailSystem()
        self._lighting = LightSystem(ambient_brightness=0.7)
        self._player_light: LightSource | None = None
        self._stage_lights: list[LightSource] = []
        audio_mgr = self.context.audio_manager if hasattr(self.context, 'audio_manager') else None
        self._dynamic_music = DynamicMusicSystem(audio_mgr) if audio_mgr is not None else None
        self._tutorial = TutorialOverlay()
        self._learning = LearningOverlay()
        self._minimap = Minimap()
        self._achievements = AchievementSystem.get_instance()
        self._achievements.load()
        self._bestiary = Bestiary.get_instance()
        self._speedrun = SpeedrunTimer()
        self._dialogue = DialogueSystem(self.context)
        self._player_spawned: bool = False
        self._damage_taken_this_stage: float = 0.0
        self._stage_start_time: float = 0.0

    def on_stage_start(self) -> None:
        if "move" not in self._tutorial_shown:
            self._tutorial.show("move", duration=6.0)
            self._tutorial_shown.add("move")

    def on_player_landed(self) -> None:
        if "landed" not in self._tutorial_shown and hasattr(self, '_player') and self._player is not None:
            if abs(self._player.velocity.x) > 0:
                self._tutorial.show("attack", duration=5.0)
                self._tutorial_shown.add("landed")

    def on_enemy_died(self, enemy: EnemyBase) -> None:
        if hasattr(enemy, "enemy_id"):
            self._bestiary.record_kill(enemy.enemy_id)
        if "enemy_kill" not in self._tutorial_shown:
            self._tutorial.show("advanced", duration=5.0)
            self._tutorial_shown.add("enemy_kill")

    def on_next_trigger_entered(self) -> None:
        if "checkpoint" not in self._tutorial_shown:
            self._tutorial.show("checkpoint", duration=3.0)
            self._tutorial_shown.add("checkpoint")

    def on_debug_toggle(self, enabled: bool) -> None:
        ...

    def on_enter(self) -> None:
        self._stage_data = StageLoader.load(self._tmx_path)
        spawn = self._stage_data.spawn_point
        self._player = Player(spawn)
        if hasattr(self._stage_data, "gravity_multiplier"):
            self._player.gravity_multiplier = self._stage_data.gravity_multiplier

        pending = self.context.pending_load
        if pending is not None and pending.stage_id == self._stage_data.stage_id:
            self._player.set_spawn(pygame.Vector2(pending.checkpoint_x, pending.checkpoint_y))
            self._player.set_health(pending.health)
            self._checkpoint_position = pygame.Vector2(pending.checkpoint_x, pending.checkpoint_y)
            self.context.pending_load = None

        self._achievements.mark_explorer(self._stage_data.stage_id)

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
            if hasattr(enemy, "enemy_id"):
                self._bestiary.record_encounter(enemy.enemy_id)

        self._checkpoints = list(self._stage_data.checkpoints)
        for cp in self._checkpoints:
            cp._event_bus = self.context.event_bus
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
                if not bgm_path.exists():
                    bgm_path = Path("assets/music") / f"{self._stage_data.bgm_track}.ogg"
                audio.play_music(bgm_path)
            if self._dynamic_music is not None:
                zone = getattr(self._stage_data, "zone", 0)
                self._dynamic_music.set_zone(zone, self._stage_data.bgm_track)

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

        # Init minimap with stage size
        if self._stage_data is not None:
            self._minimap.set_map_size(*self._stage_data.map_pixel_size)

        # Speedrun timer
        self._speedrun.start()
        self._speedrun.start_stage(self._stage_data.stage_id)

        # Track stage start for achievement timing
        self._player_spawned = True
        self._damage_taken_this_stage = 0.0
        self._stage_start_time = 0.0

        # Subscribe achievement system
        self._achievements.subscribe_events()

        self._particle_system.clear()
        self._damage_numbers.clear()
        self._tutorial.show("move", duration=6.0)
        self._ambient_particles.clear()
        self._trail_system.clear()
        self._weather.clear()
        climate = getattr(self._stage_data, "climate", "")
        self._weather.set_climate(climate)
        if climate:
            audio_key = self._weather.get_ambient_audio_key()
            if audio_key and self.context.audio is not None:
                ambient_path = settings.ASSETS_DIR / "sfx" / "ambient" / f"{audio_key}.wav"
                if ambient_path.exists():
                    self.context.audio.play_ambient(ambient_path, volume=0.3)

        # Set up stage lighting
        self._lighting.clear()
        self._player_light = None
        zone = int(getattr(self._stage_data, "zone", 0))
        if zone == 0:
            self._lighting.ambient_brightness = 0.8
            self._stage_lights = [
                LightSource(pygame.Vector2(80, 80), radius=70, color=(255, 220, 180), intensity=0.7),
                LightSource(pygame.Vector2(240, 80), radius=70, color=(255, 220, 180), intensity=0.7),
            ]
        elif zone == 1:
            self._lighting.ambient_brightness = 0.6
            self._stage_lights = [
                LightSource(pygame.Vector2(100, 60), radius=60, color=(200, 255, 180), intensity=0.6, flicker=True),
            ]
        elif zone == 2:
            self._lighting.ambient_brightness = 0.3
            self._stage_lights = [
                LightSource(pygame.Vector2(100, 80), radius=80, color=(255, 100, 50), intensity=0.8, flicker=True),
                LightSource(pygame.Vector2(200, 60), radius=50, color=(255, 150, 80), intensity=0.7, flicker=True),
            ]
        elif zone >= 3:
            self._lighting.ambient_brightness = 0.2
            self._stage_lights = [
                LightSource(pygame.Vector2(80, 70), radius=90, color=(255, 80, 30), intensity=0.9, flicker=True),
                LightSource(pygame.Vector2(180, 50), radius=70, color=(255, 120, 50), intensity=0.8, flicker=True),
                LightSource(pygame.Vector2(280, 90), radius=60, color=(255, 60, 20), intensity=0.7, flicker=True),
            ]
        else:
            self._lighting.ambient_brightness = 0.7
            self._stage_lights = []
        for sl in self._stage_lights:
            self._lighting.add_light(sl)

        self._vfx_handlers: dict[str, Callable[..., None]] = {}

        def _on_enemy_died(**data: Any) -> None:
            pos = data.get("position", (0, 0))
            self._particle_system.get_emitter("death").emit(
                float(pos[0]), float(pos[1]), HitEffects.DEATH,
            )

        def _on_hit_connect(**data: Any) -> None:
            pos = data.get("pos", [0, 0])
            dmg = data.get("damage", 1.0)
            self._particle_system.get_emitter("hits").emit(
                pos[0], pos[1], HitEffects.get_for_damage(dmg),
            )
            self._damage_numbers.add(pos[0], pos[1], str(int(dmg)))

        def _on_enemy_hit(**data: Any) -> None:
            pos = data.get("pos", [0, 0])
            dmg = data.get("damage", 1.0)
            self._particle_system.get_emitter("blood").emit(
                pos[0], pos[1], HitEffects.get_blood_for_damage(dmg),
            )
            self._camera.apply_shake(amplitude=1.5, duration=0.06)

        def _on_player_damaged(**data: Any) -> None:
            src = data.get("source", (0, 0))
            self._particle_system.get_emitter("blood").emit(
                float(src[0]), float(src[1]), HitEffects.BLOOD_BIG,
            )
            self._camera.apply_shake(amplitude=2.0, duration=0.1)
            self._post_processing.flash((255, 50, 50), alpha=180, duration=0.15)
            health_pct = self._player.current_health / max(settings.PLAYER_MAX_HEALTH, 1)
            self._post_processing.set_damage_vignette(max(0, 0.5 - health_pct * 0.5))

        def _on_vfx_parry(**data: Any) -> None:
            pos = data.get("pos", (0, 0))
            self._particle_system.get_emitter("parry").emit(
                float(pos[0]), float(pos[1]), HitEffects.PARRY,
            )
            self._camera.apply_shake(amplitude=3.0, duration=0.15)
            self._post_processing.flash((100, 200, 255), alpha=120, duration=0.1)
            self._post_processing.set_bloom(0.3, duration=0.15)

        def _on_vfx_charge(**data: Any) -> None:
            pos = data.get("pos", (0, 0))
            self._particle_system.get_emitter("charge").emit(
                float(pos[0]), float(pos[1]), HitEffects.CHARGE_GLOW,
            )

        def _on_vfx_slam(**data: Any) -> None:
            pos = data.get("pos", (0, 0))
            self._particle_system.get_emitter("slam").emit(
                float(pos[0]), float(pos[1]), HitEffects.SPARK_BIG,
            )
            self._camera.apply_shake(amplitude=4.0, duration=0.2)

        def _on_vfx_ultimate(**data: Any) -> None:
            pos = data.get("pos", (0, 0))
            self._particle_system.get_emitter("parry").emit(
                float(pos[0]), float(pos[1]), HitEffects.SPARK_BIG,
            )
            self._post_processing.set_bloom(0.8, duration=0.6)
            self._post_processing.flash((255, 255, 255), alpha=255, duration=0.15)
            self._camera.apply_shake(amplitude=5.0, duration=0.4)

        self.context.event_bus.subscribe(Events.SFX_HIT_CONNECT, _on_hit_connect)
        self.context.event_bus.subscribe(Events.SFX_ENEMY_HIT, _on_enemy_hit)
        self.context.event_bus.subscribe(Events.ENEMY_DIED, _on_enemy_died)

        def _on_player_died(**data: Any) -> None:
            pos = data.get("pos", [0, 0])
            self._particle_system.get_emitter("death").emit(
                float(pos[0]), float(pos[1]), HitEffects.get_blood_for_damage(10),
            )
            for _ in range(3):
                self._particle_system.get_emitter("death").emit(
                    float(pos[0]) + random.uniform(-8, 8),
                    float(pos[1]) + random.uniform(-8, 8),
                    HitEffects.get_blood_for_damage(5),
                )
            self._camera.apply_shake(amplitude=8.0, duration=0.5)
            self._post_processing.flash((255, 0, 0), alpha=180, duration=0.3)

        self.context.event_bus.subscribe(Events.PLAYER_DAMAGED, _on_player_damaged)
        self.context.event_bus.subscribe(Events.PLAYER_DIED, _on_player_died)
        self.context.event_bus.subscribe(Events.VFX_PARRY, _on_vfx_parry)
        self.context.event_bus.subscribe(Events.VFX_CHARGE, _on_vfx_charge)
        self.context.event_bus.subscribe(Events.VFX_SLAM, _on_vfx_slam)
        self.context.event_bus.subscribe(Events.VFX_ULTIMATE, _on_vfx_ultimate)

        def _on_music_stinger(**data: Any) -> None:
            name = data.get("name", "stinger_boss_phase")
            vol = data.get("volume", 0.8)
            self.context.audio.play_stinger(name, volume=vol)
        self.context.event_bus.subscribe(Events.MUSIC_STINGER, _on_music_stinger)
        self._vfx_handlers[Events.SFX_HIT_CONNECT] = _on_hit_connect
        self._vfx_handlers[Events.SFX_ENEMY_HIT] = _on_enemy_hit
        self._vfx_handlers[Events.ENEMY_DIED] = _on_enemy_died
        self._vfx_handlers[Events.PLAYER_DAMAGED] = _on_player_damaged
        self._vfx_handlers[Events.PLAYER_DIED] = _on_player_died
        self._vfx_handlers[Events.MUSIC_STINGER] = _on_music_stinger
        self._vfx_handlers[Events.VFX_PARRY] = _on_vfx_parry
        self._vfx_handlers[Events.VFX_CHARGE] = _on_vfx_charge
        self._vfx_handlers[Events.VFX_SLAM] = _on_vfx_slam
        self._vfx_handlers[Events.VFX_ULTIMATE] = _on_vfx_ultimate

        self._sfx_handlers: dict[str, Callable[..., None]] = {}
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
            Events.SFX_PLAYER_FOOTSTEP: "sfx_player_footstep",
            Events.SFX_MENU_HOVER: "sfx_ui_hover",
            Events.SFX_MENU_CONFIRM: "sfx_ui_confirm",
            Events.SFX_MENU_CANCEL: "sfx_ui_cancel",
        }
        self._sfx_names = sfx_map
        for evt, sname in sfx_map.items():
            def _make_handler(n: str) -> Any:
                def handler(**d: Any) -> None:
                    vol = 1.0
                    if "damage" in d:
                        vol = 0.8 + random.random() * 0.4
                    pos = d.get("pos")
                    if pos is not None:
                        self._play_sfx_spatial(n, pos[0], volume=vol)
                    else:
                        self._play_sfx_named(n, volume=vol)
                return handler
            handler = _make_handler(sname)
            self.context.event_bus.subscribe(evt, handler)
            self._sfx_handlers[evt] = handler

    def _play_sfx_named(self, name: str, volume: float = 1.0) -> None:
        audio = self.audio
        if audio is not None:
            audio.play_sfx(name, volume=volume)

    def _play_sfx_spatial(self, name: str, world_x: float, volume: float = 1.0) -> None:
        audio = self.audio
        if audio is not None:
            screen_center_x = self._camera.offset.x + settings.INTERNAL_WIDTH / 2
            audio.play_sfx_at(name, world_x, screen_center_x, volume=volume)

    def _play_sfx_varied(self, names: list[str], volume: float = 1.0) -> None:
        """Pick a random sound from a list for variation."""
        self._play_sfx_named(random.choice(names), volume=volume)

    def on_exit(self) -> None:
        if self.context.clock is not None:
            self.context.clock.time_scale = 1.0
        for evt, handler in self._sfx_handlers.items():
            self.context.event_bus.unsubscribe(evt, handler)
        self._sfx_handlers.clear()
        for evt, handler in self._vfx_handlers.items():
            self.context.event_bus.unsubscribe(evt, handler)
        self._vfx_handlers.clear()
        if self._hud is not None:
            self._hud.destroy()
            self._hud = None
        if self._msg_box is not None:
            self._msg_box.destroy()
            self._msg_box = None
        self._dialogue.end_dialogue()
        audio = self.audio
        if audio is not None:
            audio.stop_music()
        self._achievements.save()
        self._achievements.unsubscribe_events()
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
        for evt, handler in self._sfx_handlers.items():
            self.context.event_bus.unsubscribe(evt, handler)
        self._sfx_handlers.clear()
        for evt, handler in self._vfx_handlers.items():
            self.context.event_bus.unsubscribe(evt, handler)
        self._vfx_handlers.clear()
        self.on_enter()
        assert self._hud is not None
        self._hud.current_time = saved_time
        self._hud.is_countdown = saved_time_limit > 0
        if cp is not None:
            self._player.position = pygame.Vector2(cp)
            self._player.rect.center = (int(cp.x), int(cp.y))
        self._player._invincibility_timer = 2.0
        self._post_processing.flash((255, 255, 255), alpha=255, duration=0.3)
        self.context.scene_manager.transition.start_fade_in(0.5)

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
            if im and im.is_raw_key_pressed(pygame.K_F1):
                self._debug = not self._debug
                self.on_debug_toggle(self._debug)
            for fkey in (pygame.K_F2, pygame.K_F3, pygame.K_F4, pygame.K_F5,
                         pygame.K_F6, pygame.K_F7, pygame.K_F8, pygame.K_F9,
                         pygame.K_F10):
                if im and im.is_raw_key_pressed(fkey):
                    self._learning.toggle(fkey)
                    break

        if self._paused:
            if im:
                if im.is_action_just_pressed(Action.MOVE_DOWN):
                    self._pause_selected = (self._pause_selected + 1) % len(self._pause_options)
                if im.is_action_just_pressed(Action.MOVE_UP):
                    self._pause_selected = (self._pause_selected - 1) % len(self._pause_options)
                if im.is_action_just_pressed(Action.CANCEL):
                    self._paused = False
                if im.is_action_just_pressed(Action.CONFIRM):
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

            if player.combo_active and player.combo_count > 0:
                self._achievements.mark_air_assault(player._combo_air_hits)
                self._achievements.mark_combo_king(player.combo_count)

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
            if self._damage_taken_this_stage == 0:
                self._achievements.mark_untouchable()
            if self._stage_start_time < 60.0:
                self._achievements.mark_speed_demon()
            self._speedrun.split(self._stage_data.stage_id)
            self._speedrun.stop()
            self.context.event_bus.emit(Events.STAGE_COMPLETE, stage_id=stage.stage_id)
            return

        if self._progression.stage_complete:
            if self._hud:
                self._hud.clear_boss_hud()
            if self._msg_box:
                self._msg_box.update(dt)
            if self._banner:
                self._banner.update(dt)
            return

        # Dynamic music intensity
        if self._dynamic_music is not None:
            has_boss = any(isinstance(e, BossBase) and e.is_alive for e in stage.entity_list)
            has_enemies = any(isinstance(e, EnemyBase) and e.is_alive for e in stage.entity_list)
            intensity = self._dynamic_music.detect_intensity_from_state(has_boss, has_enemies)
            self._dynamic_music.set_intensity(intensity)

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
            self._hud.set_special_meter(player.special_meter, player.special_meter_max)
            self._hud.update(dt)

        self._speedrun.update(dt)
        self._hazards.update(dt, player, stage)
        self._tutorial.update(dt, im)
        self._particle_system.update(dt)
        self._damage_numbers.update(dt)
        self._post_processing.update(dt)
        self._ambient_particles.update(dt, self._camera.offset)
        self._weather.update(dt, self._camera.offset)
        self._dialogue.update(dt)

        # Update lighting
        if self._player is not None:
            combat = len([e for e in stage.entity_list if isinstance(e, EnemyBase) and e.is_alive]) > 0
            if self._player_light is None:
                self._player_light = self._lighting.get_player_light(self._player.position, combat)
                self._lighting.add_light(self._player_light)
            else:
                self._player_light.position = self._player.position
                self._player_light.intensity = 0.9 if combat else 0.6
                self._player_light.radius = 100 if combat else 60
        self._lighting.update(dt, self._camera.offset)

        # Update achievements & inventory notifications
        self._achievements.update_notifications(dt)
        get_inventory().update_notifications(dt)
        if self._player_spawned:
            self._stage_start_time += dt
            # Track damage for untouchable achievement
            if self._player is not None:
                old_health = getattr(self, '_last_player_health', self._player.current_health)
                if old_health > self._player.current_health:
                    self._damage_taken_this_stage += old_health - self._player.current_health
                self._last_player_health = self._player.current_health
                # survivor: survive with 0.5 health or less
                if self._player.current_health <= 0.5 and self._player.current_health > 0:
                    self._achievements.mark_survived_low_health()

        # Update minimap
        if self._player is not None and self._stage_data is not None:
            enemy_positions = [
                (e.position.x, e.position.y)
                for e in self._stage_data.entity_list
                if isinstance(e, EnemyBase) and e.is_alive
            ]
            boss_positions = [
                (e.position.x, e.position.y)
                for e in self._stage_data.entity_list
                if isinstance(e, BossBase) and e.is_alive
            ]
            cp_positions = [
                (cp.rect.centerx, cp.rect.centery)
                for cp in self._checkpoints
            ]
            activated = {i for i, cp in enumerate(self._checkpoints) if cp.is_activated}
            self._minimap.update(
                player_pos=(player.position.x, player.position.y),
                player_dir=player.facing_direction,
                enemy_positions=enemy_positions,
                boss_positions=boss_positions,
                checkpoint_positions=cp_positions,
                activated_checkpoints=activated,
            )
            # Explore area around player
            explore_rect = pygame.Rect(
                player.rect.centerx - 80, player.rect.centery - 60,
                160, 120,
            )
            self._minimap.explore_rect(explore_rect)

        # Capture trail during dash
        if self._player is not None:
            is_dashing = getattr(self._player, "_dash_timer", 0) > 0
            is_moving = abs(getattr(self._player, "velocity", pygame.Vector2()).x) > 50
            if is_dashing or (is_moving and not self._player.is_grounded):
                self._trail_system.capture(self._player)
        self._trail_system.update(dt)

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
            particle_system=self._particle_system,
            damage_numbers=self._damage_numbers,
            ambient_particles=self._ambient_particles,
            weather_system=self._weather,
            trail_system=self._trail_system,
            tutorial_overlay=self._tutorial,
            learning_overlay=self._learning,
            dialogue_system=self._dialogue,
        )
        self._lighting.render(surface, self._camera.offset)
        self._post_processing.apply(surface)
        self._minimap.draw(surface)
        self._achievements.draw_notifications(surface)
        get_inventory().draw_notifications(surface)
