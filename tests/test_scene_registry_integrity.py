"""Every scene the demo menu can launch must actually launch.

``SceneRegistry.build()`` catches ``ImportError``, ``RuntimeError`` and
``TypeError``, logs a warning, and returns ``None``. That is reasonable
defensive behaviour at runtime — one broken lab should not take the menu down —
but it also means a registry entry pointing at a class that *cannot be
constructed* fails completely silently: the player selects the item, nothing
happens, and no test notices.

That is not hypothetical. ``scene_registry`` registered ``"achievement"``
against ``achievement_screen.AchievementScene``, a duplicate of the real
``achievement_scene.AchievementScene`` that was missing ``on_exit`` and was
therefore still abstract. Selecting Achievements from the demo menu did nothing
at all (AUD-043).

These tests build every registered scene and assert the result is real.
"""
from __future__ import annotations

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame
import pytest

INTERNAL_SIZE = (800, 600)


@pytest.fixture(scope="module")
def display():
    pygame.init()
    pygame.font.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode(INTERNAL_SIZE)
    yield pygame.display.get_surface()


@pytest.fixture
def context(display):
    from src.engine.audio.audio_manager import AudioManager
    from src.engine.core.event_bus import EventBus
    from src.engine.core.game_context import GameContext
    from src.engine.core.save_manager import SaveManager
    from src.engine.input.input_manager import InputManager
    from src.engine.scene.scene_manager import SceneManager
    from src.framework.entities import entity_factory

    entity_factory.ensure_registered()
    ctx = GameContext(
        input_manager=InputManager(),
        audio_manager=AudioManager(),
        scene_manager=None,
        event_bus=EventBus(),
        clock=None,
        save_manager=SaveManager(),
    )
    ctx.scene_manager = SceneManager(ctx)
    return ctx


@pytest.fixture(scope="module")
def registry_keys():
    from src.engine.scenes.scene_registry import get_registry, register_demo_scenes

    register_demo_scenes()
    return sorted(get_registry().keys)


def _scene_classes_in(module):
    """Scene subclasses *defined* in this module (not imported into it)."""
    from src.engine.scene.base_scene import BaseScene

    found = []
    for attr, obj in vars(module).items():
        if not isinstance(obj, type):
            continue
        try:
            if not issubclass(obj, BaseScene) or obj is BaseScene:
                continue
        except TypeError:
            # Generic aliases and similar satisfy isinstance(obj, type) but
            # are not valid issubclass arguments.
            continue
        if getattr(obj, "__module__", None) == module.__name__:
            found.append((attr, obj))
    return found


def test_registry_is_not_empty(registry_keys) -> None:
    assert registry_keys, "no demo scenes are registered at all"


def test_every_registered_scene_builds(registry_keys, context, display) -> None:
    """The core guard: a registry key that yields None is a dead menu entry."""
    from src.engine.scenes.scene_registry import get_registry

    registry = get_registry()
    broken: list[str] = []
    for key in registry_keys:
        if registry.build(key, context) is None:
            broken.append(key)

    assert not broken, (
        "these registry entries build to None, so selecting them in the demo "
        f"menu silently does nothing: {broken}"
    )


def test_every_registered_scene_runs_frames(registry_keys, context, display) -> None:
    """Building is not enough — the scene must survive real frames."""
    from src.engine.scenes.scene_registry import get_registry

    registry = get_registry()
    surface = pygame.Surface(INTERNAL_SIZE)
    failures: list[str] = []

    for key in registry_keys:
        scene = registry.build(key, context)
        if scene is None:
            continue  # covered by the test above
        try:
            scene.awake()
            scene.start()
            scene.on_enter()
            for _ in range(3):
                scene.update(1 / 60)
                scene.draw(surface)
            scene.on_exit()
            scene.destroy()
        except Exception as exc:
            failures.append(f"{key}: {type(exc).__name__}: {exc}")

    assert not failures, "registered scenes crashed while running:\n" + "\n".join(failures)


def test_no_duplicate_scene_class_names() -> None:
    """Two modules exporting the same scene class name is how AUD-043 happened.

    ``achievement_scene.AchievementScene`` and
    ``achievement_screen.AchievementScene`` coexisted; one was complete and
    wired to the title menu, the other was abstract and wired to the registry.
    Nothing flagged the collision, and the broken one won wherever it was used.
    """
    import importlib
    import pkgutil
    from collections import defaultdict

    import src.engine.scenes as scenes_pkg

    by_name: dict[str, list[str]] = defaultdict(list)
    for info in pkgutil.iter_modules(scenes_pkg.__path__):
        try:
            module = importlib.import_module(f"src.engine.scenes.{info.name}")
        except Exception:
            continue
        for attr, _obj in _scene_classes_in(module):
            by_name[attr].append(info.name)

    collisions = {name: mods for name, mods in by_name.items() if len(mods) > 1}
    assert not collisions, (
        f"the same scene class name is defined in several modules: {collisions}. "
        "Whichever one a caller imports is then a coin flip."
    )


def test_no_scene_class_is_abstract() -> None:
    """An abstract scene cannot be instantiated, so it is a guaranteed dead end."""
    import importlib
    import inspect
    import pkgutil

    import src.engine.scenes as scenes_pkg

    abstract: list[str] = []
    for info in pkgutil.iter_modules(scenes_pkg.__path__):
        try:
            module = importlib.import_module(f"src.engine.scenes.{info.name}")
        except Exception:
            continue
        for attr, obj in _scene_classes_in(module):
            if inspect.isabstract(obj):
                missing = sorted(getattr(obj, "__abstractmethods__", ()))
                abstract.append(f"{info.name}.{attr} (missing: {', '.join(missing)})")

    assert not abstract, (
        "these scenes are abstract and can never be instantiated:\n  "
        + "\n  ".join(abstract)
    )
