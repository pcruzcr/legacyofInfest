"""
Module: test_scene_manager
System: tests
Academic Unit: N/A
Description: Tests for SceneManager push/pop/replace lifecycle,
current scene property, queue management, and cleanup.
"""
from __future__ import annotations
import pygame
import pytest
from unittest.mock import MagicMock

from src.engine.core.game_context import GameContext
from src.engine.core.event_bus import EventBus
from src.engine.scene.scene_manager import SceneManager
from src.engine.scene.base_scene import BaseScene


class _TestSceneA(BaseScene):
    def __init__(self, context: GameContext) -> None:
        super().__init__(context)
        self.awaken = False
        self.started = False
        self.entered = False
        self.exited = False
        self.paused = False
        self.resumed = False
        self.destroyed = False

    def awake(self) -> None:
        self.awaken = True

    def start(self) -> None:
        self.started = True

    def on_enter(self) -> None:
        self.entered = True

    def on_exit(self) -> None:
        self.exited = True

    def on_pause(self) -> None:
        self.paused = True

    def on_resume(self) -> None:
        self.resumed = True

    def destroy(self) -> None:
        self.destroyed = True

    def update(self, dt: float) -> None:
        pass

    def draw(self, surface: pygame.Surface) -> None:
        pass


class _TestSceneB(BaseScene):
    def __init__(self, context: GameContext) -> None:
        super().__init__(context)
        self.awaken = False
        self.started = False
        self.entered = False
        self.exited = False
        self.destroyed = False

    def awake(self) -> None:
        self.awaken = True

    def start(self) -> None:
        self.started = True

    def on_enter(self) -> None:
        self.entered = True

    def on_exit(self) -> None:
        self.exited = True

    def destroy(self) -> None:
        self.destroyed = True

    def update(self, dt: float) -> None:
        pass

    def draw(self, surface: pygame.Surface) -> None:
        pass


@pytest.fixture
def context() -> GameContext:
    bus = EventBus()
    ctx = GameContext(
        input_manager=MagicMock(),
        audio_manager=MagicMock(),
        scene_manager=None,
        event_bus=bus,
    )
    return ctx


@pytest.fixture
def manager(context: GameContext) -> SceneManager:
    sm = SceneManager(context)
    context.scene_manager = sm
    return sm


class TestSceneManager:
    def test_push_calls_lifecycle_methods(self, manager: SceneManager, context: GameContext) -> None:
        scene = _TestSceneA(context)
        manager.push(scene)
        assert scene.awaken
        assert scene.started
        assert scene.entered
        assert manager.stack_size == 1
        assert manager.current is scene

    def test_push_pauses_previous(self, manager: SceneManager, context: GameContext) -> None:
        a = _TestSceneA(context)
        b = _TestSceneB(context)
        manager.push(a)
        manager.push(b)
        assert a.paused
        assert b.entered

    def test_pop_calls_lifecycle_methods(self, manager: SceneManager, context: GameContext) -> None:
        scene = _TestSceneA(context)
        manager.push(scene)
        manager.pop()
        assert scene.exited
        assert scene.destroyed
        assert manager.stack_size == 0

    def test_pop_resumes_previous(self, manager: SceneManager, context: GameContext) -> None:
        a = _TestSceneA(context)
        b = _TestSceneB(context)
        manager.push(a)
        manager.push(b)
        manager.pop()
        assert a.resumed

    def test_pop_empty_stack_does_nothing(self, manager: SceneManager) -> None:
        manager.pop()
        assert manager.stack_size == 0

    def test_replace_calls_lifecycle_methods(self, manager: SceneManager, context: GameContext) -> None:
        a = _TestSceneA(context)
        b = _TestSceneB(context)
        manager.push(a)
        manager.replace(b)
        assert a.exited
        assert a.destroyed
        assert b.awaken
        assert b.started
        assert b.entered
        assert manager.stack_size == 1
        assert manager.current is b

    def test_replace_on_empty_stack(self, manager: SceneManager, context: GameContext) -> None:
        scene = _TestSceneA(context)
        manager.replace(scene)
        assert scene.awaken
        assert scene.started
        assert scene.entered
        assert manager.current is scene

    def test_current_property(self, manager: SceneManager, context: GameContext) -> None:
        scene = _TestSceneA(context)
        manager.push(scene)
        assert manager.current is scene

    def test_current_on_empty_stack_raises(self, manager: SceneManager) -> None:
        with pytest.raises(RuntimeError):
            _ = manager.current

    def test_current_is_top_of_stack(self, manager: SceneManager, context: GameContext) -> None:
        a = _TestSceneA(context)
        b = _TestSceneB(context)
        manager.push(a)
        manager.push(b)
        assert manager.current is b

    def test_stack_size(self, manager: SceneManager, context: GameContext) -> None:
        assert manager.stack_size == 0
        manager.push(_TestSceneA(context))
        assert manager.stack_size == 1
        manager.push(_TestSceneB(context))
        assert manager.stack_size == 2
        manager.pop()
        assert manager.stack_size == 1

    def test_set_stage_queue(self, manager: SceneManager) -> None:
        manager.set_stage_queue([_TestSceneA, _TestSceneB])
        assert manager.stage_index == 0

    def test_set_stage_index(self, manager: SceneManager) -> None:
        manager.set_stage_queue([_TestSceneA, _TestSceneB])
        manager.set_stage_index(1)
        assert manager.stage_index == 1

    def test_transition_property(self, manager: SceneManager) -> None:
        assert manager.transition is not None

    def test_cleanup_unsubscribes_from_event_bus(self, context: GameContext) -> None:
        sm = SceneManager(context)
        assert context.event_bus.subscriber_count() == 2
        sm.cleanup()
        assert context.event_bus.subscriber_count() == 0
