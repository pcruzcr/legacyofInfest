"""Regression tests for the defects found in the 2026-07-26 audit.

Each test here corresponds to a numbered finding in docs/AUDIT_2026-07.md and
fails against the pre-audit code. They are grouped by finding, not by module,
so that a future regression points straight at the original analysis.

These are deliberately behavioural: they assert on outcomes a player or a
packager would notice, not on internal structure. Several of the bugs they
cover were *already* "covered" by tests that passed — because those tests
asserted on a façade rather than on behaviour (see AUD-004).
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame
import pytest

ROOT = Path(__file__).resolve().parent.parent


# ── AUD-001: hit-stop deadlock ───────────────────────────────────────────


class TestHitstopDeadlock:
    """The game froze permanently the first time the player landed a hit.

    Chain: process_attack -> trigger_hitstop -> update_hitstop sets
    clock.time_scale = 0 -> DeltaClock.tick() returns dt = raw * 0 = 0 ->
    update_hitstop decrements the countdown by 0 -> the countdown never
    reaches 0 -> time_scale stays 0 forever. Every dt-driven system (player,
    enemies, camera, animation, VFX, HUD timer) stops. Rendering continues, so
    the symptom is a live window showing a frozen image.
    """

    def test_scaled_delta_collapses_to_zero_when_time_scale_is_zero(self) -> None:
        """The mechanism itself — documents why unscaled_dt has to exist."""
        from src.engine.core.clock import DeltaClock

        clock = DeltaClock()
        clock.tick()
        clock.time_scale = 0.0

        assert clock.tick() == 0.0
        assert clock.unscaled_dt > 0.0, (
            "unscaled_dt must keep advancing while the simulation is frozen, "
            "otherwise nothing can ever un-freeze it"
        )

    def test_hitstop_drains_and_the_game_resumes(self) -> None:
        from src.engine.core.clock import DeltaClock
        from src.framework.stage.collision_system import CollisionSystem

        clock = DeltaClock()
        collision = CollisionSystem(None)
        collision.trigger_hitstop(0.05)

        for _ in range(30):  # half a second of real time
            clock.tick()
            collision.update_hitstop(clock.unscaled_dt, clock)
            if not collision.is_hitstopped:
                break

        assert not collision.is_hitstopped
        assert clock.time_scale == 1.0

    def test_driving_hitstop_with_the_scaled_delta_still_deadlocks(self) -> None:
        """Guards the fix itself.

        If someone later "simplifies" StageScene by passing `dt` instead of
        `unscaled_dt`, this test documents exactly what breaks. It asserts the
        deadlock is reproducible with the wrong input, so the distinction
        cannot be quietly erased.
        """
        from src.engine.core.clock import DeltaClock
        from src.framework.stage.collision_system import CollisionSystem

        clock = DeltaClock()
        collision = CollisionSystem(None)
        collision.trigger_hitstop(0.05)

        for _ in range(30):
            scaled_dt = clock.tick()
            collision.update_hitstop(scaled_dt, clock)  # the original bug

        assert collision.is_hitstopped, (
            "expected the scaled delta to deadlock the countdown; if this now "
            "passes, DeltaClock.tick() no longer multiplies by time_scale and "
            "this test needs revisiting"
        )


# ── AUD-002: the damage model was unreachable ────────────────────────────


class TestAttackDamageModel:
    """`_calculate_damage` read `player._current_attack_damage`, which does not
    exist, so `getattr(..., 1.0)` returned its fallback on every single hit.
    Light attacks (0.5), heavy attacks (1.0), the 1.0/1.5/2.0 combo ladder and
    the difficulty multiplier were all inert — every hit dealt a flat 1.0.
    """

    @staticmethod
    def _player_in(state_cls):
        from src.engine.core.event_bus import EventBus
        from src.framework.entities.player import Player

        pygame.display.set_mode((320, 240))
        player = Player(pygame.Vector2(0, 0), event_bus=EventBus())
        player._change_state_instance(state_cls())
        player._active_hitbox = pygame.Rect(0, 0, 20, 20)
        return player

    def test_player_has_no_private_damage_attribute(self) -> None:
        """The attribute the old code reached for never existed."""
        from src.framework.entities.states import ShortAttackState

        player = self._player_in(ShortAttackState)
        assert not hasattr(player, "_current_attack_damage")

    def test_light_and_heavy_attacks_deal_different_damage(self) -> None:
        from src.framework.entities.states import LongAttackState, ShortAttackState
        from src.framework.stage.collision_system import CollisionSystem

        collision = CollisionSystem(None)
        light = collision._calculate_damage(self._player_in(ShortAttackState), None)
        heavy = collision._calculate_damage(self._player_in(LongAttackState), None)

        assert light < heavy, (
            f"light attack deals {light}, heavy deals {heavy} — the attack "
            "weight design is not reaching the damage calculation"
        )

    def test_collision_damage_matches_the_player_damage_model(self) -> None:
        from src.framework.entities.states import LongAttackState, ShortAttackState
        from src.framework.stage.collision_system import CollisionSystem

        collision = CollisionSystem(None)
        for state_cls in (ShortAttackState, LongAttackState):
            player = self._player_in(state_cls)
            assert collision._calculate_damage(player, None) == pytest.approx(
                player.current_attack_damage,
            ), f"{state_cls.__name__}: collision and player disagree on damage"


class TestSwingDeduplicationIsLoadBearing:
    """El conjunto por-golpe debe protegernos por sí solo.

    Encontrado por mutation testing (AUD-048). Al eliminar
    ``self._hit_this_swing.add(id(entity))`` la suite seguía en verde: el test
    de AUD-003 dispara nueve fotogramas, pero ``process_attack`` llama a
    ``consume_hitbox()`` en cuanto conecta, lo que vacía ``active_hitbox`` y hace
    que el segundo fotograma salga por la rama temprana. El conjunto nunca
    llegaba a consultarse.

    Es decir: dos mecanismos solapados y sólo uno probado. El test no era falso,
    era *insuficiente* — pasaba por la razón equivocada. Estos casos ejercitan
    cada mecanismo por separado, de modo que romper cualquiera de los dos falla.
    """

    @staticmethod
    def _scene(entities):
        import types

        return types.SimpleNamespace(entity_list=list(entities))

    def _setup(self):
        from src.engine.core.event_bus import EventBus
        from src.framework.entities.enemy_walker import EnemyWalker
        from src.framework.entities.player import Player
        from src.framework.entities.states import ShortAttackState
        from src.framework.stage.collision_system import CollisionSystem

        pygame.display.set_mode((320, 240))
        collision = CollisionSystem(None)
        player = Player(pygame.Vector2(100, 100), event_bus=EventBus())
        player._change_state_instance(ShortAttackState())

        enemy = EnemyWalker(pygame.Vector2(100, 100))
        enemy._invincibility_duration = 0.0
        enemy.hurtbox = pygame.Rect(100, 100, 24, 28)
        player._active_hitbox = pygame.Rect(100, 100, 24, 28)
        return collision, player, enemy

    def test_dedup_holds_even_if_the_hitbox_stays_active(self) -> None:
        """Aísla el conjunto: se reactiva la hitbox en cada fotograma.

        Simula que ``consume_hitbox`` no llegara a limpiar la hitbox —
        exactamente la condición bajo la que el conjunto es el único guardián.
        """
        collision, player, enemy = self._setup()
        stage = self._scene([enemy])
        live_hitbox = pygame.Rect(100, 100, 24, 28)
        start_hp = enemy.current_health
        expected = player.current_attack_damage

        for _ in range(9):
            # Reponer la hitbox: neutraliza el efecto de consume_hitbox.
            player._active_hitbox = pygame.Rect(live_hitbox)
            player._hitbox_consumed = False
            collision.process_attack(1 / 60, player, stage, None, None)

        dealt = start_hp - enemy.current_health
        assert dealt == pytest.approx(expected), (
            f"con la hitbox permanentemente activa el golpe infligió {dealt} en "
            f"lugar de {expected}: el conjunto _hit_this_swing no está "
            f"deduplicando y sólo consume_hitbox nos protegía"
        )

    def test_one_swing_can_still_hit_several_enemies(self) -> None:
        """La deduplicación es *por enemigo*, no por golpe.

        Un barrido que alcanza a dos enemigos debe dañar a los dos. Si el
        conjunto se aplicara al golpe entero, el arma dejaría de tener área y
        nadie lo notaría salvo jugando.
        """
        from src.framework.entities.enemy_walker import EnemyWalker

        collision, player, first = self._setup()
        second = EnemyWalker(pygame.Vector2(110, 100))
        second._invincibility_duration = 0.0
        second.hurtbox = pygame.Rect(105, 100, 24, 28)

        stage = self._scene([first, second])
        hp1, hp2 = first.current_health, second.current_health

        collision.process_attack(1 / 60, player, stage, None, None)

        assert first.current_health < hp1, "el primer enemigo no recibió daño"
        assert second.current_health < hp2, (
            "el segundo enemigo dentro del área no recibió daño: la "
            "deduplicación se está aplicando al golpe en vez de por enemigo"
        )


# ── AUD-005: autosave destroyed campaign progress ────────────────────────


class TestAutosavePreservesProgress:
    """`auto_save` built a fresh SaveData from six arguments and wrote it over
    the newest slot, resetting every field those arguments did not cover.
    `SceneManager._on_stage_complete` appends to `completed_stages`, saves, and
    then calls `auto_save` on that same slot — so a stage completion was erased
    microseconds after being recorded. Players could never bank progress.
    """

    @pytest.fixture
    def manager(self, tmp_path, monkeypatch):
        from src.engine.core.save_manager import SaveManager

        monkeypatch.setattr(SaveManager, "SAVES_DIR", tmp_path)
        return SaveManager()

    def test_autosave_keeps_completed_stages(self, manager) -> None:
        from src.engine.core.save_data import SaveData

        manager.save(1, SaveData(
            slot_id=1,
            timestamp="2026-01-01T00:00:00+00:00",
            stage_id="stage0",
            completed_stages=["stage0", "stage1"],
        ))

        manager.auto_save(
            stage_id="stage2", stage_index=2,
            checkpoint_x=10.0, checkpoint_y=20.0,
            health=3.0, max_health=5.0,
        )

        reloaded = manager.load(1)
        assert reloaded is not None
        assert reloaded.completed_stages == ["stage0", "stage1"], (
            "autosave wiped the player's completed-stage history"
        )
        assert reloaded.stage_id == "stage2"
        assert reloaded.checkpoint_x == pytest.approx(10.0)

    def test_autosave_keeps_zone_flags(self, manager) -> None:
        from src.engine.core.save_data import SaveData

        manager.save(1, SaveData(
            slot_id=1,
            timestamp="2026-01-01T00:00:00+00:00",
            zone_flags={"secret_grove": True},
        ))
        manager.auto_save(
            stage_id="stage1", stage_index=1,
            checkpoint_x=0.0, checkpoint_y=0.0,
            health=5.0, max_health=5.0,
        )

        reloaded = manager.load(1)
        assert reloaded is not None
        assert reloaded.zone_flags == {"secret_grove": True}

    def test_stage_complete_then_autosave_keeps_both_writes(self, manager) -> None:
        """The exact production sequence from SceneManager._on_stage_complete."""
        from src.engine.core.save_data import SaveData

        manager.save(1, SaveData(slot_id=1, timestamp="2026-01-01T00:00:00+00:00"))

        data = manager.load(1)
        data.completed_stages.append("stage0")
        manager.save(1, data)
        manager.auto_save(
            stage_id="stage1", stage_index=1,
            checkpoint_x=0.0, checkpoint_y=0.0,
            health=5.0, max_health=5.0,
        )

        final = manager.load(1)
        assert final.completed_stages == ["stage0"]
        assert final.stage_id == "stage1"

    def test_autosave_timestamp_is_timezone_aware(self, manager) -> None:
        """newest_slot() orders slots by comparing timestamp *strings*.

        Naive local timestamps sort incorrectly across a DST rollback, which
        would make the game load an older save than the newest one.
        """
        from datetime import datetime

        manager.auto_save(
            stage_id="s", stage_index=0,
            checkpoint_x=0.0, checkpoint_y=0.0,
            health=5.0, max_health=5.0,
        )
        stamp = manager.load(1).timestamp
        assert datetime.fromisoformat(stamp).tzinfo is not None


# ── AUD-009: CANCEL in the tutorial force-started the campaign ───────────


class TestTutorialCancelReturnsToTitle:
    """One `_exit_requested` flag served both "finished the tutorial" and
    "pressed Escape", and both routed to StoryScene. A player who opened the
    tutorial from the title menu to check the controls could not get back —
    Escape dropped them into a cutscene and then into gameplay.
    """

    @staticmethod
    def _tutorial_with_input(pressed_action):
        """A TutorialScene past its fade-in, wired to a stub input manager."""
        from src.engine.core.event_bus import EventBus
        from src.engine.core.game_context import GameContext
        from src.engine.scenes.tutorial_scene import TutorialScene

        pygame.init()
        pygame.font.init()
        pygame.display.set_mode((320, 240))

        class _StubInput:
            def is_action_just_pressed(self, action):
                return action == pressed_action

            def __getattr__(self, _name):
                return lambda *a, **k: False

        class _StubTransition:
            def start_fade_in(self, *a, **k):
                return None

        class _StubSceneManager:
            def __init__(self):
                self.replaced_with = None
                self.transition = _StubTransition()

            def replace(self, scene):
                self.replaced_with = scene

        context = GameContext(
            input_manager=_StubInput(),
            audio_manager=None,
            scene_manager=_StubSceneManager(),
            event_bus=EventBus(),
            clock=None,
            save_manager=None,
        )
        scene = TutorialScene(context)
        scene.on_enter()
        scene._ready = True          # skip the fade-in
        scene._fade_alpha = 0
        return scene, context.scene_manager

    def test_cancel_returns_to_the_title_screen(self) -> None:
        from src.engine.input.action_map import Action
        from src.engine.scenes.title_scene import TitleScene

        scene, manager = self._tutorial_with_input(Action.CANCEL)

        scene.update(1 / 60)                    # CANCEL registers
        for _ in range(60):                     # let the fade-out finish
            scene.update(1 / 60)
            if manager.replaced_with is not None:
                break

        assert manager.replaced_with is not None, "CANCEL did not leave the tutorial"
        assert isinstance(manager.replaced_with, TitleScene), (
            f"CANCEL landed on {type(manager.replaced_with).__name__}; pressing "
            "Escape in the tutorial must return to the title, not force-start "
            "the campaign"
        )

    def test_confirming_through_the_end_still_starts_the_story(self) -> None:
        from src.engine.input.action_map import Action
        from src.engine.scenes.story_scene import StoryScene
        from src.engine.scenes.tutorial_scene import _TUTORIAL_STEPS

        scene, manager = self._tutorial_with_input(Action.CONFIRM)

        for _ in range(len(_TUTORIAL_STEPS) + 90):
            scene.update(1 / 60)
            if manager.replaced_with is not None:
                break

        assert isinstance(manager.replaced_with, StoryScene), (
            "completing the tutorial should still lead into the story"
        )


# ── AUD-006: numba made the math helpers slower, and broke installs ──────


class TestMathUtilsHasNoHardJitDependency:
    def test_module_imports_without_numba(self) -> None:
        """math_utils must not require numba.

        numba was absent from requirements.txt but imported unguarded here, so
        the README's documented install produced a game that crashed on start.
        Benchmarks also showed the JIT wrappers were 1.0-2.1x *slower* than
        plain Python for these scalar bodies.
        """
        source = (ROOT / "src" / "engine" / "utils" / "math_utils.py").read_text(
            encoding="utf-8",
        )
        code_lines = [
            line for line in source.splitlines()
            if not line.lstrip().startswith("#")
        ]
        code = "\n".join(code_lines)
        assert "import numba" not in code, "numba is a hard import again"

    @pytest.mark.parametrize("name", [
        "ease_in_quad", "ease_out_quad", "ease_in_out_quad",
        "ease_in_cubic", "ease_out_cubic", "ease_out_bounce",
        "ease_out_elastic", "ease_in_sine", "ease_out_sine",
    ])
    def test_easing_curves_are_normalised(self, name: str) -> None:
        """Behaviour preserved across the de-JIT: f(0)=0, f(1)=1, in-range."""
        from src.engine.utils import math_utils

        fn = getattr(math_utils, name)
        assert fn(0.0) == pytest.approx(0.0, abs=1e-6)
        assert fn(1.0) == pytest.approx(1.0, abs=1e-6)
        for i in range(11):
            value = fn(i / 10)
            assert -0.5 <= value <= 1.5, f"{name}({i / 10}) = {value} out of range"

    def test_vector_helpers_match_pygame(self) -> None:
        from src.engine.utils import math_utils

        a = pygame.Vector2(3.0, 4.0)
        b = pygame.Vector2(-1.0, 2.0)

        assert math_utils.vec2_length(a) == pytest.approx(5.0)
        assert math_utils.vec2_dot(a, b) == pytest.approx(a.dot(b))
        assert math_utils.vec2_distance(a, b) == pytest.approx(a.distance_to(b))
        assert math_utils.vec2_length(math_utils.vec2_normalize(a)) == pytest.approx(1.0)

    def test_normalize_of_zero_vector_does_not_divide_by_zero(self) -> None:
        from src.engine.utils import math_utils

        result = math_utils.vec2_normalize(pygame.Vector2(0.0, 0.0))
        assert result == pygame.Vector2(0.0, 0.0)


# ── AUD-007 / AUD-008: dependency manifests disagreed ────────────────────


class TestDependencyManifests:
    def test_manifests_are_in_sync(self) -> None:
        """requirements.txt used to omit five packages that src/ imports."""
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "check_dependency_sync.py")],
            capture_output=True, text=True,
        )
        assert result.returncode == 0, result.stdout + result.stderr

    def test_build_backend_is_one_setuptools_actually_publishes(self) -> None:
        """`setuptools.backends._legacy:_Backend` is not a real module — any
        `pip install .` failed with ModuleNotFoundError before the fix.

        AUD-175: this used to `importlib.import_module` the backend, which
        conflated two different claims — "the name is spelled right" and
        "setuptools happens to be installed in whatever interpreter runs the
        tests". Only the first is the project's business: PEP 517 builds the
        wheel in an isolated environment created from `build-system.requires`,
        and since Python 3.12 `ensurepip` no longer ships setuptools, so a
        fresh venv does not have it. The test failed on a correct tree.

        Checking the name against the backends setuptools documents still
        fails on the AUD-007 string, and no longer depends on the environment.
        """
        import importlib
        import importlib.util
        import re

        valid = {
            "setuptools.build_meta",
            "setuptools.build_meta:__legacy__",
        }

        text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        match = re.search(r'^build-backend\s*=\s*"([^"]+)"', text, re.MULTILINE)
        assert match, "pyproject.toml declares no build-backend"
        backend = match.group(1)

        requires = re.search(r"^requires\s*=\s*\[(.*?)\]", text, re.MULTILINE | re.DOTALL)
        assert requires and "setuptools" in requires.group(1), (
            f"build-backend is {backend!r} but build-system.requires does not "
            f"ask for setuptools, so the backend would never be installed"
        )
        assert backend in valid, (
            f"{backend!r} is not a backend setuptools publishes; expected one "
            f"of {sorted(valid)}. `pip install .` would fail with "
            f"ModuleNotFoundError before building anything"
        )

        # Where setuptools *is* present, hold it to the stronger claim too.
        if importlib.util.find_spec("setuptools") is not None:
            importlib.import_module(backend.split(":")[0])

    def test_no_unused_heavy_dependencies_declared(self) -> None:
        """PyYAML and pytweening were required but imported nowhere."""
        text = (ROOT / "requirements.txt").read_text(encoding="utf-8").lower()
        for package in ("pyyaml", "pytweening"):
            assert package not in text, (
                f"{package} is declared but nothing in the repository imports it"
            )


# ── AUD-010: CI never ran ────────────────────────────────────────────────


class TestCIActuallyTriggers:
    def test_workflow_targets_branches_that_exist(self) -> None:
        """CI triggered on main/develop; the repo's branches are prod/pprod/dev.

        Every push and PR went unmatched, so the workflow had never executed —
        which is how a failing test and an unsatisfiable lock file survived in
        the tree with an apparently clean CI history.
        """
        workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(
            encoding="utf-8",
        )
        assert "main" not in workflow.split("jobs:")[0] or "prod" in workflow
        assert "prod" in workflow, "CI still does not target the prod branch"


# ── AUD-012: no audio device must not prevent launch ─────────────────────


class TestAudioIsOptional:
    def test_mixer_init_failure_is_survivable(self, monkeypatch) -> None:
        """`pygame.mixer.init()` was unguarded in App._init_pygame, so any
        machine without a working audio device aborted at startup."""
        import src.engine.core.app as app_module

        calls = {"init": 0}

        def _boom(*args, **kwargs):
            calls["init"] += 1
            raise pygame.error("No available audio device")

        monkeypatch.setattr(pygame.mixer, "init", _boom)

        source = Path(app_module.__file__).read_text(encoding="utf-8")
        assert "pygame.mixer.init" in source
        init_block = source.split("pygame.mixer.init")[0]
        assert init_block.rstrip().endswith("try:") or "try:" in init_block[-200:], (
            "pygame.mixer.init() is not wrapped in a try block — a machine "
            "with no sound card cannot launch the game"
        )
