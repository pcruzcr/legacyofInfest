"""Every scene must boot, update and DRAW without raising.

Why this file exists
--------------------
The 2026-07 audit shipped a suite of 722 passing tests, a clean lint run and
seven green CI stages — and the game still crashed on launch with three
separate ``AttributeError``s in the render path::

    AttributeError: 'Camera' object has no attribute 'get_offset'
    AttributeError: 'StageData' object has no attribute 'background_objects'
    TypeError: Iterating over key states is not supported

Every one of those is a one-line typo against an API that does not exist, and
every one would have been caught by *calling the method once*. They survived
because the suite tested subsystems in isolation and never drove a real frame:
``stage_scene.py`` sat at 20% coverage and ``stage0.py`` at 0%.

Coverage percentages did not communicate that. "Zero percent on the only
shipping stage" and "the game does not start" are the same fact, and the suite
reported only the first one.

This module closes that gap in the bluntest way available: instantiate every
scene the game can reach, run real frames through ``update()`` and ``draw()``,
and fail loudly on any exception. It is deliberately not clever. Its whole value
is that it exercises the code path a player actually hits on frame one.
"""
from __future__ import annotations

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame
import pytest

INTERNAL_SIZE = (800, 600)
FRAMES = 5
DT = 1.0 / 60.0


# ── fixtures ─────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def display():
    pygame.init()
    pygame.font.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode(INTERNAL_SIZE)
    yield pygame.display.get_surface()


@pytest.fixture
def context(display):
    """A GameContext wired closely enough to production to be meaningful."""
    from src.engine.audio.audio_manager import AudioManager
    from src.engine.core.event_bus import EventBus
    from src.engine.core.game_context import GameContext
    from src.engine.core.save_manager import SaveManager
    from src.engine.input.input_manager import InputManager
    from src.engine.scene.scene_manager import SceneManager
    from src.framework.entities import entity_factory

    entity_factory.ensure_registered()

    bus = EventBus()
    ctx = GameContext(
        input_manager=InputManager(),
        audio_manager=AudioManager(),
        scene_manager=None,
        event_bus=bus,
        clock=None,
        save_manager=SaveManager(),
    )
    ctx.scene_manager = SceneManager(ctx)
    return ctx


def _run_frames(scene, surface, frames: int = FRAMES) -> None:
    """Drive a scene the way App.run does: enter, update+draw, exit."""
    scene.awake()
    scene.start()
    scene.on_enter()
    try:
        for _ in range(frames):
            scene.process_events([])
            scene.update(DT)
            scene.draw(surface)
    finally:
        scene.on_exit()
        scene.destroy()


# ── every registered menu / lab / demo scene ─────────────────────

# Scenes reachable from the title menu or the demo menu. Listed explicitly
# rather than auto-discovered so that a scene which is deleted or renamed makes
# this file fail — silence would defeat the purpose.
SCENE_PATHS: list[tuple[str, str]] = [
    ("src.engine.scenes.title_scene", "TitleScene"),
    ("src.engine.scenes.splash_scene", "SplashScene"),
    ("src.engine.scenes.options_scene", "OptionsScene"),
    ("src.engine.scenes.keybinding_scene", "KeybindingScene"),
    ("src.engine.scenes.load_game_scene", "LoadGameScene"),
    ("src.engine.scenes.tutorial_scene", "TutorialScene"),
    ("src.engine.scenes.game_over_scene", "GameOverScene"),
    ("src.engine.scenes.end_credits_scene", "EndCreditsScene"),
    ("src.engine.scenes.world_map_scene", "WorldMapScene"),
    ("src.engine.scenes.inventory_scene", "InventoryScene"),
    ("src.engine.scenes.bestiary_scene", "BestiaryScene"),
    ("src.engine.scenes.achievement_scene", "AchievementScene"),
    ("src.engine.scenes.leaderboard_scene", "LeaderboardScene"),
    ("src.engine.scenes.progress_scene", "ProgressScene"),
    ("src.engine.scenes.demo_menu_scene", "DemoMenuScene"),
    ("src.engine.scenes.loading_scene", "LoadingScene"),
    # Academic labs and demos
    ("src.engine.scenes.vector_lab_scene", "VectorLabScene"),
    ("src.engine.scenes.transform_lab_scene", "TransformLabScene"),
    ("src.engine.scenes.collision_lab_scene", "CollisionLabScene"),
    ("src.engine.scenes.interpolation_lab_scene", "InterpolationLabScene"),
    ("src.engine.scenes.noise_lab_scene", "NoiseLabScene"),
    ("src.engine.scenes.curve_editor_scene", "CurveEditorScene"),
    ("src.engine.scenes.color_theory_scene", "ColorTheoryScene"),
    ("src.engine.scenes.filter_demo_scene", "FilterDemoScene"),
    ("src.engine.scenes.vision_demo_scene", "VisionDemoScene"),
    ("src.engine.scenes.pattern_demo_scene", "PatternDemoScene"),
    ("src.engine.scenes.pipeline_builder_scene", "PipelineBuilderScene"),
    ("src.engine.scenes.combo_demo_scene", "ComboDemoScene"),
    ("src.engine.scenes.sandbox_scene", "SandboxScene"),
    ("src.engine.scenes.stage_wizard_scene", "StageWizardScene"),
    ("src.engine.scenes.story_scene", "StoryScene"),
]


def _load(module_path: str, class_name: str):
    import importlib

    module = importlib.import_module(module_path)
    return getattr(module, class_name)


@pytest.mark.parametrize(("module_path", "class_name"), SCENE_PATHS,
                         ids=[c for _, c in SCENE_PATHS])
def test_scene_boots_updates_and_draws(module_path, class_name, context, display) -> None:
    """The scene must survive five real frames without raising."""
    scene_cls = _load(module_path, class_name)
    surface = pygame.Surface(INTERNAL_SIZE)

    try:
        scene = scene_cls(context)
    except TypeError:
        # A few scenes take an extra argument (StoryScene takes a chapter).
        scene = scene_cls(context, 1)

    _run_frames(scene, surface)


@pytest.mark.parametrize(("module_path", "class_name"), SCENE_PATHS,
                         ids=[c for _, c in SCENE_PATHS])
def test_scene_survives_input(module_path, class_name, context, display) -> None:
    """Pressing every bound action must not crash any scene.

    Menu scenes read input directly, and a scene that indexes into an options
    list without bounds-checking crashes the moment a player holds a direction.
    """
    from src.engine.input.action_map import DEFAULT_KEY_BINDINGS

    scene_cls = _load(module_path, class_name)
    surface = pygame.Surface(INTERNAL_SIZE)
    try:
        scene = scene_cls(context)
    except TypeError:
        scene = scene_cls(context, 1)

    scene.awake()
    scene.start()
    scene.on_enter()
    try:
        input_manager = context.input_manager
        for keys in DEFAULT_KEY_BINDINGS.values():
            for key in keys:
                event = pygame.event.Event(pygame.KEYDOWN, key=key, mod=0, unicode="")
                input_manager.pump([event])
                scene.process_events([event])
                scene.update(DT)
                scene.draw(surface)
                up = pygame.event.Event(pygame.KEYUP, key=key, mod=0)
                input_manager.pump([up])
                scene.process_events([up])
    finally:
        scene.on_exit()
        scene.destroy()


# ── stages and bosses ────────────────────────────────────────────


STAGE_PATHS: list[tuple[str, str]] = [
    ("src.stages.stage0.stage0", "Stage0"),
    ("src.stages.boss_venado.boss_venado_scene", "BossVenadoScene"),
]


@pytest.mark.parametrize(("module_path", "class_name"), STAGE_PATHS,
                         ids=[c for _, c in STAGE_PATHS])
def test_stage_boots_updates_and_draws(module_path, class_name, context, display) -> None:
    """The full gameplay render path — the one that crashed on launch."""
    import importlib

    module = importlib.import_module(module_path)
    stage_cls = getattr(module, class_name, None)
    if stage_cls is None:
        # Fall back to the first StageScene subclass in the module.
        from src.framework.scenes.stage_scene import StageScene

        stage_cls = next(
            (obj for obj in vars(module).values()
             if isinstance(obj, type) and issubclass(obj, StageScene)
             and obj is not StageScene),
            None,
        )
    if stage_cls is None:
        pytest.skip(f"no StageScene subclass in {module_path}")

    surface = pygame.Surface(INTERNAL_SIZE)
    scene = stage_cls(context)
    _run_frames(scene, surface, frames=10)


def test_stage_survives_a_paused_frame(context, display) -> None:
    """Pausing must not crash the draw path — it takes a different branch."""
    from src.stages.stage0.stage0 import Stage0

    surface = pygame.Surface(INTERNAL_SIZE)
    scene = Stage0(context)
    scene.awake()
    scene.start()
    scene.on_enter()
    try:
        scene.update(DT)
        scene._paused = True
        for _ in range(3):
            scene.update(DT)
            scene.draw(surface)
    finally:
        scene.on_exit()
        scene.destroy()


def test_stage_survives_debug_overlay(context, display) -> None:
    """F1 debug rendering is a separate branch and is never otherwise run."""
    from src.stages.stage0.stage0 import Stage0

    surface = pygame.Surface(INTERNAL_SIZE)
    scene = Stage0(context)
    scene.awake()
    scene.start()
    scene.on_enter()
    try:
        scene._debug = True
        for _ in range(3):
            scene.update(DT)
            scene.draw(surface)
    finally:
        scene.on_exit()
        scene.destroy()


def test_stage_actually_renders_something(context, display) -> None:
    """A stage frame must not be a flat fill.

    The three launch crashes all lived in DrawingSystem, whose helpers reached
    for StageData attributes that do not exist (`background_objects`,
    `tile_layer`, `top_layer`). Once those raise no longer, the next failure
    mode is silent: the draw completes and paints nothing. Assert that the
    frame contains more than the background colour.
    """
    from src.engine.core import settings
    from src.stages.stage0.stage0 import Stage0

    surface = pygame.Surface(INTERNAL_SIZE)
    scene = Stage0(context)
    scene.awake()
    scene.start()
    scene.on_enter()
    try:
        for _ in range(5):
            scene.update(DT)
        surface.fill((0, 0, 0))
        scene.draw(surface)
    finally:
        scene.on_exit()
        scene.destroy()

    colors = {surface.get_at((x, y))[:3]
              for x in range(0, INTERNAL_SIZE[0], 17)
              for y in range(0, INTERNAL_SIZE[1], 13)}
    colors.discard((0, 0, 0))
    colors.discard(tuple(settings.BG_COLOR))

    assert colors, (
        "the stage rendered nothing but background — DrawingSystem completed "
        "without painting the map, entities or HUD"
    )
