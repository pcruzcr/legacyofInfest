"""
Module: test_message_box
System: tests
Description: Tests for MessageBox: show/hide events, typewriter effect,
and destroy cleanup.
"""
from __future__ import annotations
import pygame
import pytest
from src.engine.ui.message_box import MessageBox
from src.engine.core.event_bus import EventBus


@pytest.fixture(autouse=True)
def _init_pygame() -> None:
    if not pygame.get_init():
        pygame.init()


class TestMessageBox:
    def test_initial_state(self, event_bus: EventBus) -> None:
        mb = MessageBox(event_bus)
        assert not mb.is_visible
        assert mb._text == ""

    def test_show_message_event(self, event_bus: EventBus) -> None:
        mb = MessageBox(event_bus)
        event_bus.emit("SHOW_MESSAGE", text="Hello", duration=3.0)
        event_bus.dispatch()
        assert mb.is_visible
        assert mb._full_text == "Hello"

    def test_hide_message_event(self, event_bus: EventBus) -> None:
        mb = MessageBox(event_bus)
        event_bus.emit("SHOW_MESSAGE", text="Hello", duration=3.0)
        event_bus.dispatch()
        assert mb.is_visible
        event_bus.emit("HIDE_MESSAGE")
        event_bus.dispatch()
        assert not mb.is_visible
        assert mb._text == ""

    def test_typewriter_reveals_text_over_time(self, event_bus: EventBus) -> None:
        mb = MessageBox(event_bus)
        mb._full_text = "Hello"
        mb._visible = True
        mb._chars_per_second = 10.0
        mb.update(0.1)
        assert len(mb._text) == 1
        mb.update(0.3)
        assert len(mb._text) == 4
        mb.update(1.0)
        assert mb._text == "Hello"

    def test_auto_dismiss_after_duration(self, event_bus: EventBus) -> None:
        mb = MessageBox(event_bus)
        mb._chars_per_second = 1000.0
        event_bus.emit("SHOW_MESSAGE", text="Hi", duration=0.5)
        event_bus.dispatch()
        assert mb.is_visible
        mb.update(0.01)
        assert mb.is_visible
        mb.update(0.6)
        assert not mb.is_visible

    def test_draw_does_not_crash_when_visible(self, event_bus: EventBus) -> None:
        mb = MessageBox(event_bus)
        surface = pygame.Surface((320, 224))
        mb.draw(surface)
        event_bus.emit("SHOW_MESSAGE", text="Test", duration=3.0)
        event_bus.dispatch()
        mb.update(1.0)
        mb.draw(surface)

    def test_destroy_removes_subscriptions(self, event_bus: EventBus) -> None:
        mb = MessageBox(event_bus)
        before = event_bus.subscriber_count()
        mb.destroy()
        after = event_bus.subscriber_count()
        assert after == before - 2

    def test_destroy_is_idempotent(self, event_bus: EventBus) -> None:
        mb = MessageBox(event_bus)
        mb.destroy()
        count_after_first = event_bus.subscriber_count()
        mb.destroy()
        count_after_second = event_bus.subscriber_count()
        assert count_after_second == count_after_first

    def test_destroyed_message_box_ignores_events(self, event_bus: EventBus) -> None:
        mb = MessageBox(event_bus)
        mb.destroy()
        event_bus.emit("SHOW_MESSAGE", text="Should not appear", duration=3.0)
        event_bus.dispatch()
        assert not mb.is_visible

    def test_queue_maintains_order_after_dismiss(self, event_bus: EventBus) -> None:
        mb = MessageBox(event_bus)
        mb._chars_per_second = 1000.0
        event_bus.emit("SHOW_MESSAGE", text="First", duration=0.0)
        event_bus.dispatch()
        assert mb._full_text == "First"
        event_bus.emit("SHOW_MESSAGE", text="Second", duration=0.0)
        event_bus.dispatch()
        event_bus.emit("SHOW_MESSAGE", text="Third", duration=0.0)
        event_bus.dispatch()
        assert len(mb._queue) == 2
        event_bus.emit("HIDE_MESSAGE")
        event_bus.dispatch()
        assert len(mb._queue) == 2
        mb.update(0.0)
        assert mb._full_text == "Second"
        event_bus.emit("HIDE_MESSAGE")
        event_bus.dispatch()
        mb.update(0.0)
        assert mb._full_text == "Third"

    def test_chars_to_add_never_exceeds_full_text(self, event_bus: EventBus) -> None:
        mb = MessageBox(event_bus)
        mb._full_text = "Hi"
        mb._visible = True
        mb._char_timer = 100.0
        mb._chars_per_second = 30.0
        mb.update(0.0)
        assert mb._text == "Hi"
