"""Tests for SceneManager — push/pop/replace lifecycle.

See 24_TEST_PLAN.md §5.1 for test specifications.
"""

import pytest

from src.engine.scene.base_scene import BaseScene
from src.engine.scene.scene_manager import SceneManager


class CallTrackingScene(BaseScene):
    """A minimal BaseScene subclass that records which callbacks fire."""

    def __init__(self, name: str = "") -> None:
        super().__init__()
        self.name: str = name
        self.calls: list[str] = []

    def on_enter(self) -> None:
        self.calls.append(f"{self.name}:on_enter")

    def on_exit(self) -> None:
        self.calls.append(f"{self.name}:on_exit")

    def update(self, dt: float) -> None:
        self.calls.append(f"{self.name}:update")

    def draw(self, surface: object) -> None:
        self.calls.append(f"{self.name}:draw")

    def on_pause(self) -> None:
        self.calls.append(f"{self.name}:on_pause")

    def on_resume(self) -> None:
        self.calls.append(f"{self.name}:on_resume")


@pytest.fixture
def mgr():
    """Provide a fresh SceneManager for each test."""
    return SceneManager()


def test_push_calls_on_enter(mgr):
    """Pushing a scene calls its on_enter() exactly once."""
    s = CallTrackingScene("A")
    mgr.push(s)
    assert s.calls == ["A:on_enter"]


def test_push_calls_previous_on_pause(mgr):
    """Pushing scene B while A is current calls A.on_pause()."""
    a = CallTrackingScene("A")
    b = CallTrackingScene("B")
    mgr.push(a)
    mgr.push(b)
    assert "A:on_pause" in a.calls
    assert b.calls == ["B:on_enter"]


def test_pop_calls_on_exit_and_resume(mgr):
    """Popping B (with A below) calls B.on_exit() then A.on_resume()."""
    a = CallTrackingScene("A")
    b = CallTrackingScene("B")
    mgr.push(a)
    mgr.push(b)
    a.calls.clear()
    b.calls.clear()

    mgr.pop()
    assert b.calls == ["B:on_exit"]
    assert a.calls == ["A:on_resume"]


def test_replace_does_not_call_pause_resume(mgr):
    """replace() calls on_exit()/on_enter() only — never pause/resume."""
    a = CallTrackingScene("A")
    c = CallTrackingScene("C")
    mgr.push(a)
    a.calls.clear()

    mgr.replace(c)
    assert a.calls == ["A:on_exit"]
    assert c.calls == ["C:on_enter"]


def test_current_property_reflects_top(mgr):
    """current always returns the most recently pushed scene."""
    a = CallTrackingScene("A")
    b = CallTrackingScene("B")
    assert mgr.current is None

    mgr.push(a)
    assert mgr.current is a

    mgr.push(b)
    assert mgr.current is b

    mgr.pop()
    assert mgr.current is a


def test_pop_empty_stack_does_not_crash(mgr):
    """Calling pop() on an empty stack no-ops safely."""
    mgr.pop()  # should not raise
    assert mgr.current is None
