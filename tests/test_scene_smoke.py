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
    ("src.engine.scenes.stage_error_scene", "StageErrorScene"),
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
    ("src.engine.scenes.unit_theory_scene", "UnitTheoryScene"),
    ("src.engine.scenes.student_login_scene", "StudentLoginScene"),
]

#: Escenas cuyo constructor pide algo más que el contexto.
#:
#: Antes esto era un `except TypeError: scene_cls(context, 1)` que servía
#: para `StoryScene`, que toma un número de capítulo. Con `UnitTheoryScene`
#: —que toma el identificador de una unidad— aquel `1` habría construido la
#: escena de una unidad inexistente: no habría reventado, porque la escena lo
#: contempla, pero la prueba habría ejercitado la rama de error en vez de la
#: real. Una prueba que pasa recorriendo el camino equivocado es peor que una
#: que falla (AUD-098).
ARGUMENTO_EXTRA: dict[str, object] = {
    "StoryScene": 1,
    "UnitTheoryScene": "vectores",
}


def _construir(scene_cls: type, context: object) -> object:
    """Instancia una escena, con su argumento extra si lo necesita."""
    extra = ARGUMENTO_EXTRA.get(scene_cls.__name__)
    if extra is not None:
        return scene_cls(context, extra)
    return scene_cls(context)


#: Ficheros de `engine/scenes/` que no son escenas y por eso no están arriba.
#: Se listan a mano para que añadir un fichero nuevo obligue a decidir.
NO_SON_ESCENAS = {
    "__init__.py", "code_panel.py", "debug_overlay.py", "demo_common.py",
    "demo_layout.py", "demo_utils.py", "param_panel.py", "quiz_system.py",
    "scene_registry.py", "transition_manager.py", "tutorial_overlay.py",
}


def test_toda_escena_nueva_entra_en_el_arnes() -> None:
    """Ninguna escena puede quedarse fuera de este arnés en silencio.

    AUD-098. `UnitTheoryScene` se añadió en AUD-095 y no llegó a esta lista.
    No falló nada: simplemente dejó de comprobarse que arranca, dibuja y
    aguanta la entrada, que es justo lo que este fichero existe para
    garantizar. La lista explícita protege contra renombrados y borrados,
    pero no contra olvidos; esto sí.
    """
    from pathlib import Path

    directorio = Path(__file__).resolve().parent.parent / "src" / "engine" / "scenes"
    ficheros = {p.name for p in directorio.glob("*.py")}
    en_el_arnes = {
        f"{modulo.rsplit('.', 1)[-1]}.py" for modulo, _ in SCENE_PATHS
    }
    sin_cubrir = ficheros - en_el_arnes - NO_SON_ESCENAS
    assert not sin_cubrir, (
        f"escena(s) {sorted(sin_cubrir)} no están en SCENE_PATHS ni declaradas "
        f"como «no son escenas». Añádelas a una de las dos listas."
    )


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

    scene = _construir(scene_cls, context)

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
    scene = _construir(scene_cls, context)

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


def test_the_tile_map_specifically_is_drawn(context, display) -> None:
    """The tilemap must contribute pixels — not just the parallax backdrops.

    Found by mutation testing (AUD-048). Replacing ``map_layer.draw(surface)``
    with ``pass`` left ``test_stage_actually_renders_something`` green, because
    the background layers alone already produce hundreds of colours. The suite
    was asserting "something rendered", which is not the same claim as "the
    world rendered" — and the world not rendering is precisely the bug that
    shipped (AUD-039).

    This compares a frame against one drawn with the map layer suppressed, so
    it fails if the tilemap stops contributing regardless of what else paints.
    """
    from src.framework.stage.drawing_system import DrawContext
    from src.stages.stage0.stage0 import Stage0

    scene = Stage0(context)
    scene.awake()
    scene.start()
    scene.on_enter()
    try:
        for _ in range(5):
            scene.update(DT)

        def frame(*, with_map: bool) -> set[tuple[int, int, int]]:
            surface = pygame.Surface(INTERNAL_SIZE)
            surface.fill((0, 0, 0))
            stage = scene._stage_data
            saved = stage.map_layer
            if not with_map:
                stage.map_layer = None
            try:
                scene._drawing.draw(DrawContext(
                    surface=surface, stage=stage, player=scene._player,
                    camera=scene._camera,
                ))
            finally:
                stage.map_layer = saved
            return {surface.get_at((x, y))[:3]
                    for x in range(0, INTERNAL_SIZE[0], 7)
                    for y in range(0, INTERNAL_SIZE[1], 5)}

        with_map = frame(with_map=True)
        without_map = frame(with_map=False)
    finally:
        scene.on_exit()
        scene.destroy()

    only_from_map = with_map - without_map
    assert only_from_map, (
        "suppressing stage.map_layer changed nothing on screen, so the tile "
        "map is not being drawn — the world is rendering empty underneath the "
        "parallax backdrops"
    )
