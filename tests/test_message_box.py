"""
Module: test_message_box
System: tests
Academic Unit: N/A
Description: Tests for MessageBox: show/hide events, typewriter effect,
and destroy cleanup.
"""
from __future__ import annotations
import pygame
import pytest
from src.engine.ui.message_box import MessageBox
from src.engine.core.event_bus import emit, dispatch, clear, subscriber_count


@pytest.fixture(autouse=True)
def reset_bus():
    clear()
    yield


class TestMessageBox:
    def test_initial_state(self):
        mb = MessageBox()
        assert not mb.is_visible
        assert mb._text == ""

    def test_show_message_event(self):
        mb = MessageBox()
        emit("SHOW_MESSAGE", text="Hello", duration=3.0)
        dispatch()
        assert mb.is_visible
        assert mb._full_text == "Hello"

    def test_hide_message_event(self):
        mb = MessageBox()
        emit("SHOW_MESSAGE", text="Hello", duration=3.0)
        dispatch()
        assert mb.is_visible
        emit("HIDE_MESSAGE")
        dispatch()
        assert not mb.is_visible
        assert mb._text == ""

    def test_typewriter_reveals_text_over_time(self):
        mb = MessageBox()
        mb._full_text = "Hello"
        mb._visible = True
        mb._chars_per_second = 10.0
        mb.update(0.1)  # 0.1s * 10 = 1 char
        assert len(mb._text) == 1
        mb.update(0.3)  # total 0.4s * 10 = 4 chars
        assert len(mb._text) == 4
        mb.update(1.0)  # total well beyond length
        assert mb._text == "Hello"

    def test_auto_dismiss_after_duration(self):
        mb = MessageBox()
        mb._chars_per_second = 1000.0  # instant typewriter
        emit("SHOW_MESSAGE", text="Hi", duration=0.5)
        dispatch()
        assert mb.is_visible
        mb.update(0.01)  # finish typewriter
        assert mb.is_visible  # still within display_duration
        mb.update(0.6)  # beyond display_duration
        assert not mb.is_visible

    def test_draw_does_not_crash_when_visible(self):
        mb = MessageBox()
        surface = pygame.Surface((320, 224))
        mb.draw(surface)  # not visible, should be no-op
        emit("SHOW_MESSAGE", text="Test", duration=3.0)
        dispatch()
        # Advance typewriter so text is revealed
        mb.update(1.0)
        mb.draw(surface)  # visible with text, should not crash

    def test_destroy_removes_subscriptions(self):
        mb = MessageBox()
        before = subscriber_count()
        mb.destroy()
        after = subscriber_count()
        assert after == before - 2, (
            f"Expected 2 fewer subscribers, got {before} -> {after}"
        )

    def test_destroy_is_idempotent(self):
        mb = MessageBox()
        mb.destroy()
        count_after_first = subscriber_count()
        mb.destroy()
        count_after_second = subscriber_count()
        assert count_after_second == count_after_first

    def test_destroyed_message_box_ignores_events(self):
        mb = MessageBox()
        mb.destroy()
        emit("SHOW_MESSAGE", text="Should not appear", duration=3.0)
        dispatch()
        assert not mb.is_visible

    def test_chars_to_add_never_exceeds_full_text(self):
        mb = MessageBox()
        mb._full_text = "Hi"
        mb._visible = True
        # Simulate a large dt so chars_to_add would exceed the string length
        mb._char_timer = 100.0
        mb._chars_per_second = 30.0
        mb.update(0.0)
        assert mb._text == "Hi", f"Expected 'Hi', got '{mb._text}'"
