from __future__ import annotations

import os
import types
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PGGAME_DISABLE_SOUND", "1")

import pygame
import pytest

from src.engine.core import settings


def _has_pydub() -> bool:
    try:
        import pydub  # noqa: F401
        return True
    except ImportError:
        return False


def _has_lupa() -> bool:
    try:
        import lupa  # noqa: F401
        return True
    except ImportError:
        return False


# AUD-235: aquí vivía `_has_pymunk()`, que nadie llamaba. Era el último rastro
# de la simulación de cuerpos rígidos que `collision_system.py` retiró, y la
# dependencia se ha ido con él.


def _make_test_wav(tmp_path: Path) -> Path:
    import struct
    import wave
    path = tmp_path / "test.wav"
    sample_rate = 44100
    duration = 0.1
    num_samples = int(sample_rate * duration)
    with wave.open(str(path), "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        for _ in range(num_samples):
            wf.writeframes(struct.pack("<h", 0))
    return path


# ── Audio Pipeline (pydub) ──────────────────────────────────────────────


@pytest.mark.skipif(not _has_pydub(), reason="pydub not installed")
class TestAudioPipeline:
    def test_load_as_wav_returns_bytes(self, tmp_path: Path) -> None:
        from src.engine.audio.audio_pipeline import AudioPipeline
        pipeline = AudioPipeline(cache_dir=tmp_path / "cache")
        # Create a minimal valid WAV file for testing
        wav = _make_test_wav(tmp_path)
        result = pipeline.load_as_wav(wav)
        assert isinstance(result, bytes)
        assert len(result) > 44  # WAV header

    def test_load_as_pcm_returns_array(self, tmp_path: Path) -> None:
        from src.engine.audio.audio_pipeline import AudioPipeline
        pipeline = AudioPipeline()
        wav = _make_test_wav(tmp_path)
        arr = pipeline.load_as_pcm(wav)
        import numpy as np
        assert isinstance(arr, np.ndarray)
        assert arr.ndim == 1
        assert arr.dtype == np.float32

    def test_cache_hits(self, tmp_path: Path) -> None:
        from src.engine.audio.audio_pipeline import AudioPipeline
        cache_dir = tmp_path / "cache"
        pipeline = AudioPipeline(cache_dir=cache_dir)
        wav = _make_test_wav(tmp_path)
        first = pipeline.load_as_wav(wav)
        # Second call should hit cache (same output)
        second = pipeline.load_as_wav(wav)
        assert first == second


# ── Lua Scripting (lupa) ────────────────────────────────────────────────


@pytest.mark.skipif(not _has_lupa(), reason="lupa not installed")
class TestLuaScriptEnemy:
    def test_patrol_returns_dx_dy(self) -> None:
        from src.framework.ai.lua_script import LuaScriptEnemy
        src = """
        function patrol(ctx)
            return 60 * ctx.dt, 0
        end
        """
        script = LuaScriptEnemy(src, name="test")
        assert script._script_source == src
        assert script._name == "test"
        # We can't easily test without real enemy/player objects,
        # but we can verify the Lua runtime compiled successfully

    def test_no_functions_does_not_error(self) -> None:
        from src.framework.ai.lua_script import LuaScriptEnemy
        script = LuaScriptEnemy("-- empty script", name="empty")
        result = script.call_patrol(None, None, 0.016)  # type: ignore[arg-type]
        assert result == (0.0, 0.0)

    def test_alert_defaults_to_approach(self) -> None:
        from src.framework.ai.lua_script import LuaScriptEnemy
        script = LuaScriptEnemy("-- only patrol defined", name="no_alert")
        result = script.call_alert(None, None, 0.016)  # type: ignore[arg-type]
        assert result == "approach"

    def test_on_hit_and_death_are_noops(self) -> None:
        from src.framework.ai.lua_script import LuaScriptEnemy
        script = LuaScriptEnemy("", name="no_callbacks")
        script.call_on_hit(None, None, 0.016)  # type: ignore[arg-type]
        script.call_on_death(None, None, 0.016)  # type: ignore[arg-type]


# ── Collision System ─────────────────────────────────────────────────────
#
# REWRITTEN (AUD-004). The previous tests in this block asserted on the
# internals of a pymunk Space — `cs._space.bodies`, `cs.add_player()` returning
# a body at a particular position — and passed. But nothing in the game ever
# called those methods, so the Space was empty on every real frame and the
# tests were measuring a façade rather than behaviour. Coverage went up; the
# knockback that the class advertised silently did nothing on every hit.
#
# These replacements assert only on observable outcomes: does a hit deal the
# damage the design specifies, does it land exactly once, does hit-stop expire.


class TestCollisionSystem:
    @staticmethod
    def _scene_double(entities):
        """Minimal stand-in for StageData — only `entity_list` is read."""
        return types.SimpleNamespace(entity_list=list(entities))

    def test_hitstop_expires_and_restores_time_scale(self) -> None:
        """Regression for AUD-001: the freeze must end on its own.

        Hit-stop sets clock.time_scale to 0. If the countdown is driven by the
        *scaled* delta, that same zero feeds back into the countdown and it can
        never drain — the game locks up permanently on the first landed hit.
        """
        from src.engine.core.clock import DeltaClock
        from src.framework.stage.collision_system import CollisionSystem

        cs = CollisionSystem(None)
        clock = DeltaClock()

        cs.trigger_hitstop(0.05)
        assert cs.is_hitstopped

        # Drive it the way StageScene does: always with the UNSCALED delta.
        for _ in range(10):
            clock.tick()
            cs.update_hitstop(clock.unscaled_dt, clock)

        assert not cs.is_hitstopped, "hit-stop never expired — game would be frozen"
        assert clock.time_scale == 1.0, "time_scale was not restored after hit-stop"

    def test_hitstop_freezes_then_releases_the_clock(self) -> None:
        from src.engine.core.clock import DeltaClock
        from src.framework.stage.collision_system import CollisionSystem

        cs = CollisionSystem(None)
        clock = DeltaClock()
        clock.tick()

        cs.trigger_hitstop(0.05)
        cs.update_hitstop(0.01, clock)
        assert clock.time_scale == 0.0, "hit-stop should freeze the simulation"

        cs.update_hitstop(0.10, clock)
        assert clock.time_scale == 1.0, "clock must resume once the freeze expires"

    def test_trigger_hitstop_extends_but_never_shortens(self) -> None:
        from src.framework.stage.collision_system import CollisionSystem

        cs = CollisionSystem(None)
        cs.trigger_hitstop(0.20)
        cs.trigger_hitstop(0.05)  # a weaker second hit lands mid-freeze
        assert cs._hitstop_timer == pytest.approx(0.20)

    def test_attack_applies_the_damage_the_design_specifies(self) -> None:
        """Regression for AUD-002.

        `_calculate_damage` read a private attribute `_current_attack_damage`
        that has never existed on Player, so getattr always returned its 1.0
        fallback: light and heavy attacks were indistinguishable and the combo
        multiplier was inert. Damage must come from the public property.
        """
        from src.engine.core.event_bus import EventBus
        from src.framework.entities.player import Player
        from src.framework.entities.states import ShortAttackState
        from src.framework.stage.collision_system import CollisionSystem

        pygame.display.set_mode((320, 240))
        cs = CollisionSystem(None)
        player = Player(pygame.Vector2(0, 0), event_bus=EventBus())
        player._change_state_instance(ShortAttackState())
        player._active_hitbox = pygame.Rect(0, 0, 20, 20)

        assert cs._calculate_damage(player, None) == pytest.approx(
            player.current_attack_damage,
        ), "collision damage diverged from the player's own damage model"

    def test_a_single_swing_damages_an_enemy_only_once(self) -> None:
        """Regression for AUD-003.

        An attack hitbox stays active for several frames (a 0.15 s short attack
        is ~9 frames at 60 fps). Without per-swing bookkeeping, process_attack
        re-damaged the same enemy on every one of those frames.
        """
        from src.engine.core.event_bus import EventBus
        from src.framework.entities.enemy_walker import EnemyWalker
        from src.framework.entities.player import Player
        from src.framework.entities.states import ShortAttackState
        from src.framework.stage.collision_system import CollisionSystem

        pygame.display.set_mode((320, 240))
        cs = CollisionSystem(None)
        player = Player(pygame.Vector2(100, 100), event_bus=EventBus())
        player._change_state_instance(ShortAttackState())

        enemy = EnemyWalker(pygame.Vector2(100, 100))
        enemy._invincibility_duration = 0.0  # isolate the swing logic
        # hurtbox is normally populated by EnemyBase.update(); pin it here so
        # the overlap is deterministic and the test measures only hit dedup.
        enemy.hurtbox = pygame.Rect(100, 100, 24, 28)
        player._active_hitbox = pygame.Rect(100, 100, 24, 28)

        stage = self._scene_double([enemy])
        start_hp = enemy.current_health
        # Sample before the swing: consuming the hitbox drops the property to 0.
        expected = player.current_attack_damage
        assert expected > 0, "test setup did not produce a damaging attack state"

        for _ in range(9):  # every frame the hitbox would be live
            cs.process_attack(1 / 60, player, stage, None, None)

        damage_dealt = start_hp - enemy.current_health
        assert damage_dealt > 0, "the attack never connected at all"
        assert damage_dealt == pytest.approx(expected), (
            f"one swing dealt {damage_dealt} damage over 9 frames — it should "
            f"deal exactly {expected} (multi-hit regression, AUD-003)"
        )

    def test_knockback_actually_moves_the_target(self) -> None:
        """Regression for AUD-004: apply_knockback used to be a silent no-op."""
        from src.framework.entities.enemy_walker import EnemyWalker
        from src.framework.stage.collision_system import CollisionSystem

        cs = CollisionSystem(None)
        enemy = EnemyWalker(pygame.Vector2(100, 100))
        before = float(enemy._knockback_velocity.x)

        cs.apply_knockback(enemy, 250.0, -100.0)

        assert enemy._knockback_velocity.x != before, (
            "knockback impulse was discarded — hits have no physical response"
        )

    def test_dead_enemies_are_not_damaged(self) -> None:
        from src.engine.core.event_bus import EventBus
        from src.framework.entities.enemy_walker import EnemyWalker
        from src.framework.entities.player import Player
        from src.framework.entities.states import ShortAttackState
        from src.framework.stage.collision_system import CollisionSystem

        pygame.display.set_mode((320, 240))
        cs = CollisionSystem(None)
        player = Player(pygame.Vector2(100, 100), event_bus=EventBus())
        player._change_state_instance(ShortAttackState())

        enemy = EnemyWalker(pygame.Vector2(100, 100))
        enemy.current_health = 0.0
        enemy.hurtbox = pygame.Rect(100, 100, 24, 28)
        player._active_hitbox = pygame.Rect(100, 100, 24, 28)

        cs.process_attack(1 / 60, player, self._scene_double([enemy]), None, None)
        assert enemy.current_health <= 0.0, "a corpse took further damage"

    def test_reset_clears_per_swing_state(self) -> None:
        from src.framework.stage.collision_system import CollisionSystem

        cs = CollisionSystem(None)
        cs.trigger_hitstop(0.2)
        cs._hit_this_swing.add(1234)

        cs.reset()

        assert not cs.is_hitstopped, "a stage reload during hit-stop stayed frozen"
        assert not cs._hit_this_swing


# ── Particle System (numba + numpy) ──────────────────────────────────────


class TestParticleEmitterExtended:
    """AUD-275 — estas pruebas leen ahora `[:em.count]`, no el arreglo entero.

    Los arreglos tienen capacidad reservada desde AUD-275: las partículas vivas
    van empaquetadas al principio y el resto son ranuras a cero. Recorrer el
    arreglo completo comprueba el relleno, no las partículas — que es lo que
    hacía fallar a las tres de aquí abajo aunque el comportamiento fuera
    correcto.
    """

    def test_emit_respects_gravity(self) -> None:
        from src.framework.vfx.particle_system import BurstConfig, ParticleEmitter
        em = ParticleEmitter()
        config = BurstConfig(count=10, speed=0, lifetime=1.0, size=(4, 4),
                             color=(255, 255, 255), spread=0, gravity=200, friction=1.0)
        em.emit(0, 0, config)
        assert em.count == 10
        assert all(g == 200.0 for g in em.gravity[:em.count])
        assert all(f == 1.0 for f in em.friction[:em.count])

    def test_emit_directed_stores_gravity_friction(self) -> None:
        from src.framework.vfx.particle_system import ParticleEmitter
        em = ParticleEmitter()
        em.emit_directed(100, 100, 90, 50, 5, 2.0, (3, 5),
                         (255, 0, 0), gravity=500, friction=0.5)
        assert em.count == 5
        assert all(g == 500.0 for g in em.gravity[:em.count])
        assert all(f == 0.5 for f in em.friction[:em.count])

    def test_update_applies_gravity(self) -> None:
        from src.framework.vfx.particle_system import BurstConfig, ParticleEmitter
        em = ParticleEmitter()
        config = BurstConfig(count=5, speed=0, lifetime=5.0, size=(2, 2),
                             color=(255, 255, 255), spread=0, gravity=100, friction=1.0)
        em.emit(0, 0, config)
        vivas = em.count
        initial_y = em.y[:vivas].copy()
        em.update(0.1)
        assert all(em.y[:vivas] > initial_y), "Particles should fall with gravity"

    def test_clear_resets_all_arrays(self) -> None:
        """AUD-275 — `clear()` vacía el emisor **sin soltar los arreglos**.

        Esta prueba miraba `len(em.gravity) == 0`, que era cierto cuando los
        arreglos crecían y encogían con las partículas. Ahora tienen capacidad
        reservada: `len()` da la capacidad y las vivas las da `count`.

        Y no soltar la memoria es deliberado — el sistema llama a `clear()` al
        cambiar de escena, y volver a la capacidad inicial obligaría a crecer
        otra vez desde cero en el primer combate, que es justo el trabajo que
        AUD-275 quitó.
        """
        from src.framework.vfx.particle_system import BurstConfig, ParticleEmitter
        em = ParticleEmitter()
        config = BurstConfig(count=5, speed=0, lifetime=1.0, size=(2, 2),
                             color=(255, 255, 255), spread=0)
        em.emit(0, 0, config)
        em.clear()
        assert em.count == 0
        assert em.capacidad > 0, "clear() no puede soltar los arreglos"

    def test_burst_config_init(self) -> None:
        from src.framework.vfx.particle_system import BurstConfig
        bc = BurstConfig(count=20, speed=100, lifetime=2.0, size=(3, 8),
                         color=(100, 200, 50), spread=180, gravity=50, friction=0.8)
        assert bc.count == 20
        assert bc.speed == 100
        assert bc.size_min == 3
        assert bc.size_max == 8
        assert bc.color == (100, 200, 50)
        assert bc.spread == 180
        assert bc.gravity == 50
        assert bc.friction == 0.8


# ── GL Pipeline (software fallback) ─────────────────────────────────────


class TestGLRendererFallback:
    def test_render_without_init_uses_software_fallback(self) -> None:
        from src.engine.render.gl_pipeline import GLRenderer
        renderer = GLRenderer()
        assert not renderer._initialized
        w, h = settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT
        pygame.display.set_mode((w, h))
        surf = pygame.Surface((w, h))
        renderer.render(surf)

    def test_destroy_idempotent(self) -> None:
        from src.engine.render.gl_pipeline import GLRenderer
        renderer = GLRenderer()
        renderer.destroy()
        assert not renderer._initialized

    def test_config_defaults(self) -> None:
        from src.engine.render.gl_pipeline import GLRenderConfig
        cfg = GLRenderConfig()
        assert cfg.bloom_enabled
        assert cfg.bloom_threshold == 0.8
        # AUD-222 — aquí ponía `assert cfg.vignette_enabled`, y venir en `True`
        # era justamente el defecto: la viñeta se dibujaba dos veces, la de CPU
        # sobre la superficie y ésta sobre la textura. De las dos, la que se
        # apaga es la del sombreador, porque la de CPU crece cuando al jugador
        # le queda poca vida (`set_damage_vignette`) y esta configuración es
        # estática. El razonamiento completo está en `GLRenderConfig` y las
        # pruebas del reparto en `tests/test_postprocesado_no_se_duplica.py`.
        assert not cfg.vignette_enabled
        assert cfg.lighting_enabled
        assert cfg.colorblind_mode == 0


# ── SaveManager orjson/pydantic integration ─────────────────────────────


class TestSaveDataIntegration:
    def test_to_json_roundtrip(self) -> None:
        from src.engine.core.save_data import SaveData
        data = SaveData(slot_id=1, stage_id="stage0", checkpoint_x=10.0, checkpoint_y=20.0)
        raw = data.to_json()
        assert isinstance(raw, bytes)
        restored = SaveData.from_json(raw)
        assert restored.slot_id == 1
        assert restored.stage_id == "stage0"
        assert restored.checkpoint_x == 10.0
        assert restored.checkpoint_y == 20.0

    def test_from_json_string(self) -> None:
        from src.engine.core.save_data import SaveData
        data = SaveData(slot_id=2, stage_id="boss", health=3.0, max_health=5.0)
        raw_str = data.to_json().decode("utf-8")
        restored = SaveData.from_json(raw_str)
        assert restored.slot_id == 2
        assert restored.stage_id == "boss"

    def test_migrate_static_preserved(self) -> None:
        """AUD-292 subió el esquema a la versión 3. Se compara con la constante
        y no con un número escrito a mano: es lo que hace que la próxima
        versión no vuelva a poner esta prueba en rojo por nada."""
        from src.engine.core.save_data import SAVE_VERSION, SaveData
        old = {"version": 0, "stage_id": "stage0"}
        result = SaveData.migrate(old)
        assert result["version"] == SAVE_VERSION

    def test_from_dict_validates_health(self) -> None:
        from src.engine.core.save_data import SaveData
        data = SaveData(health=4.567, max_health=5.0)
        d = data.to_dict()
        assert d["health"] == 4.6  # rounded to 1 decimal


# ── Difficulty pydantic integration ──────────────────────────────────────


class TestDifficultyConfig:
    def test_difficulty_config_defaults(self) -> None:
        from src.engine.core.difficulty import DifficultyConfig
        cfg = DifficultyConfig(label="test")
        assert cfg.label == "test"
        assert cfg.outgoing_damage_mult == 1.0
        assert cfg.incoming_damage_mult == 1.0
        assert cfg.enemy_health_mult == 1.0

    def test_difficulty_config_validation(self) -> None:
        """A negative damage multiplier must be rejected.

        AUD-032: this asserted ``pytest.raises(Exception)``, which passes if the
        constructor raises *anything at all* — including a TypeError from a
        renamed parameter or an ImportError from a broken module. That is a test
        that cannot fail for the right reason. Pin the actual validation error.
        """
        from pydantic import ValidationError

        from src.engine.core.difficulty import DifficultyConfig

        with pytest.raises(ValidationError):
            DifficultyConfig(label="test", incoming_damage_mult=-1.0)

    def test_difficulty_enum_values(self) -> None:
        from src.engine.core.difficulty import Difficulty
        assert Difficulty.EASY.value == "easy"
        assert Difficulty.NORMAL.value == "normal"
        assert Difficulty.HARD.value == "hard"


# ── Math Utils numba ────────────────────────────────────────────────────


class TestMathUtilsJIT:
    def test_clamp(self) -> None:
        from src.engine.utils.math_utils import clamp
        assert clamp(5, 0, 10) == 5
        assert clamp(-1, 0, 10) == 0
        assert clamp(15, 0, 10) == 10

    def test_lerp(self) -> None:
        from src.engine.utils.math_utils import lerp
        assert lerp(0, 100, 0.5) == 50
        assert lerp(0, 100, 0) == 0
        assert lerp(0, 100, 1) == 100

    def test_easing_functions_compile(self) -> None:
        from src.engine.utils.math_utils import (
            ease_in_cubic,
            ease_in_out_quad,
            ease_in_quad,
            ease_in_sine,
            ease_out_cubic,
            ease_out_quad,
            ease_out_sine,
        )
        assert ease_in_quad(0.5) == pytest.approx(0.25)
        assert ease_out_quad(0.5) == pytest.approx(0.75)
        assert 0 <= ease_in_out_quad(0.5) <= 1
        assert 0 <= ease_in_cubic(0.5) <= 1
        assert 0 <= ease_out_cubic(0.5) <= 1
        assert 0 <= ease_in_sine(0.5) <= 1
        assert 0 <= ease_out_sine(0.5) <= 1


# ── Weather System gravity per climate (BUG-082) ────────────────────────


class TestWeatherClimateGravity:
    def test_rain_climate_params(self) -> None:
        from src.framework.vfx.weather_system import WeatherSystem
        ws = WeatherSystem(climate="rain")
        assert ws._climate == "rain"
        assert ws.CLIMATE_PARAMS["rain"]["particles"] == 60

    def test_snow_climate_params(self) -> None:
        from src.framework.vfx.weather_system import WeatherSystem
        ws = WeatherSystem(climate="snow")
        assert ws._climate == "snow"
        assert ws.CLIMATE_PARAMS["snow"]["particles"] == 40

    def test_storm_climate_params(self) -> None:
        from src.framework.vfx.weather_system import WeatherSystem
        ws = WeatherSystem(climate="storm")
        assert ws._climate == "storm"
        assert ws.CLIMATE_PARAMS["storm"]["particles"] == 100

    def test_clear_climate_params(self) -> None:
        from src.framework.vfx.weather_system import WeatherSystem
        ws = WeatherSystem(climate="clear")
        assert ws._climate == "clear"
        assert ws.CLIMATE_PARAMS["clear"]["particles"] == 0

    def test_spawn_particle_rain_uses_high_gravity(self) -> None:
        from src.framework.vfx.weather_system import WeatherSystem
        ws = WeatherSystem(climate="rain")
        ws._emitter.clear()
        ws._spawn_particle(pygame.Vector2(0, 0))
        assert ws._emitter.count >= 1


# ── BossBase filter_frame reset (BUG-086) ───────────────────────────────


class TestBossFilterReset:
    def test_phase_transition_resets_filter_frame(self) -> None:
        import pygame

        from src.framework.entities.boss_base import BossBase, BossPhase
        class _MinionBoss(BossBase):
            def _patrol_behavior(self, dt: float) -> None: pass
            def _alert_behavior(self, dt: float) -> None: pass
            def _build_hitbox(self) -> pygame.Rect: return pygame.Rect(0, 0, 24, 24)
            def _build_hurtbox(self) -> pygame.Rect: return pygame.Rect(2, 2, 20, 20)
        boss = _MinionBoss(pygame.Vector2(100, 100), max_health=20.0)
        boss.set_phases([
            BossPhase(phase_index=0, health_threshold=20.0),
            BossPhase(phase_index=1, health_threshold=10.0),
        ])
        boss._filter_frame = 99
        boss._finish_phase_transition()
        assert boss._filter_frame == 0


# ── Bestiary orjson roundtrip (BUG-088) ────────────────────────────────


class TestBestiaryOrjson:
    def test_save_load_roundtrip(self, tmp_path) -> None:
        from src.framework.entities.bestiary import Bestiary
        save_path = tmp_path / "bestiary.json"
        b1 = Bestiary()
        b1.record_kill("walker")
        b1.save(str(save_path))
        assert save_path.exists()
        with open(str(save_path), "rb") as f:
            raw = f.read()
        assert b"walker" in raw
        assert b"kills" in raw
        b2 = Bestiary()
        b2.load(str(save_path))
        entry = b2.get_entry("walker")
        assert entry is not None
        assert entry.kills >= 1

    def test_load_missing_file_is_noop(self, tmp_path) -> None:
        from src.framework.entities.bestiary import Bestiary
        b = Bestiary()
        b.load(str(tmp_path / "nonexistent.json"))


# ── DrawingSystem DrawContext (ARC-001) ─────────────────────────────────


class TestDrawContext:
    def test_draw_context_constructs(self) -> None:
        import pygame

        from src.framework.stage.drawing_system import DrawContext
        surf = pygame.Surface((320, 224))
        ctx = DrawContext(surface=surf)
        assert ctx.surface is surf
        assert ctx.stage is None
        assert ctx.paused is False

    def test_draw_context_with_all_fields(self) -> None:
        import pygame

        from src.framework.stage.drawing_system import DrawContext
        surf = pygame.Surface((320, 224))
        ctx = DrawContext(
            surface=surf, paused=True, pause_selected=1,
            pause_options=["Resume", "Quit"], debug=True,
        )
        assert ctx.paused
        assert ctx.pause_selected == 1
        assert ctx.debug


# ── StageLoader safe converters ─────────────────────────────────────────


class TestStageLoaderSafeConverters:
    def test_safe_int_valid(self) -> None:
        from src.framework.stage.stage_loader import StageLoader
        assert StageLoader._safe_int("42", "test") == 42

    def test_safe_int_invalid_defaults_zero(self) -> None:
        from src.framework.stage.stage_loader import StageLoader
        assert StageLoader._safe_int("not_a_number", "test") == 0

    def test_safe_float_valid(self) -> None:
        from src.framework.stage.stage_loader import StageLoader
        assert StageLoader._safe_float("3.14", "test") == 3.14

    def test_safe_float_invalid_defaults_zero(self) -> None:
        from src.framework.stage.stage_loader import StageLoader
        assert StageLoader._safe_float("nan_value", "test") == 0.0

