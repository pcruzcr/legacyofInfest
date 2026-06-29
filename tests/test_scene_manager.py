"""
Module: test_scene_manager
System: tests
Academic Unit: N/A
Description: Tests for SceneManager push/pop/replace semantics,
stage queue advancement, and event-driven scene transitions.
"""
from __future__ import annotations
import pygame
import pytest
from src.engine.scene.scene_manager import SceneManager
from src.engine.scene.base_scene import BaseScene
from src.engine.core.event_bus import EventBus


class _TestSceneA(BaseScene):
    def __init__(self) -> None:
        self.entered = False
        self.exited = False
        self.paused = False
        self.resumed = False

    def on_enter(self) -> None:
        self.entered = True

    def on_exit(self) -> None:
        self.exited = True

    def on_pause(self) -> None:
        self.paused = True

    def on_resume(self) -> None:
        self.resumed = True

    def update(self, dt: float) -> None:
        pass

    def draw(self, surface: pygame.Surface) -> None:
        pass


class _TestSceneB(BaseScene):
    def __init__(self) -> None:
        self.entered = False
        self.exited = False

    def on_enter(self) -> None:
        self.entered = True

    def on_exit(self) -> None:
        self.exited = True

    def update(self, dt: float) -> None:
        pass

    def draw(self, surface: pygame.Surface) -> None:
        pass


@pytest.fixture(autouse=True)
def reset_bus():
    EventBus.clear()
    yield


@pytest.fixture
def manager():
    return SceneManager()


class TestSceneManager:
    def test_push_adds_scene(self, manager):
        scene = _TestSceneA()
        manager.push(scene)
        assert manager.stack_size == 1
        assert manager.current is scene

    def test_push_calls_on_enter(self, manager):
        scene = _TestSceneA()
        manager.push(scene)
        assert scene.entered

    def test_push_pauses_previous(self, manager):
        a = _TestSceneA()
        b = _TestSceneB()
        manager.push(a)
        manager.push(b)
        assert a.paused

    def test_pop_removes_scene(self, manager):
        a = _TestSceneA()
        manager.push(a)
        manager.pop()
        assert manager.stack_size == 0

    def test_pop_calls_on_exit(self, manager):
        a = _TestSceneA()
        manager.push(a)
        manager.pop()
        assert a.exited

    def test_pop_resumes_previous(self, manager):
        a = _TestSceneA()
        b = _TestSceneB()
        manager.push(a)
        manager.push(b)
        manager.pop()
        assert a.resumed

    def test_replace_switches_scene(self, manager):
        a = _TestSceneA()
        b = _TestSceneB()
        manager.push(a)
        manager.replace(b)
        assert manager.stack_size == 1
        assert manager.current is b
        assert a.exited
        assert b.entered

    def test_set_stage_queue(self, manager):
        manager.set_stage_queue([_TestSceneA, _TestSceneB])
        assert manager._stage_index == 0
        assert len(manager._stage_queue) == 2

    def test_stage_complete_advances_queue(self, manager):
        manager.set_stage_queue([_TestSceneA, _TestSceneB])
        a = _TestSceneA()
        manager.push(a)
        EventBus.emit("STAGE_COMPLETE")
        EventBus.dispatch()
        # Should have advanced to next stage
        assert manager._stage_index == 1
        assert isinstance(manager.current, _TestSceneB)

    def test_empty_stack_raises(self, manager):
        with pytest.raises(RuntimeError):
            _ = manager.current
