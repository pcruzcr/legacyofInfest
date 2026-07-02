"""
Module: test_hud
System: tests
Academic Unit: N/A
Description: Tests for HUD: heart slot states, timer display,
event-driven health updates.
"""
from __future__ import annotations
import pygame
import pytest
from src.engine.ui.hud import HUD, _heart_slot_state
from src.engine.core.event_bus import emit, dispatch, clear, subscriber_count
from src.engine.core import settings


@pytest.fixture(autouse=True)
def reset_bus():
    clear()
    yield


class TestHeartSlotState:
    """Pure function tests for _heart_slot_state."""

    def test_slot_full(self):
        assert _heart_slot_state(5.0, 0) == "full"
        assert _heart_slot_state(5.0, 1) == "full"

    def test_slot_empty(self):
        assert _heart_slot_state(0.0, 0) == "empty"
        assert _heart_slot_state(0.0, 1) == "empty"

    def test_slot_half(self):
        assert _heart_slot_state(0.5, 0) == "half"

    def test_slot_three_quarter(self):
        assert _heart_slot_state(0.75, 0) == "three_quarter"

    def test_slot_quarter(self):
        assert _heart_slot_state(0.25, 0) == "quarter"

    def test_slot_negative_health(self):
        assert _heart_slot_state(-1.0, 0) == "empty"

    def test_slot_beyond_max(self):
        assert _heart_slot_state(10.0, 0) == "full"

    def test_slot_second_slot_empty(self):
        # health=1.0, slot=1 => v = max(0, min(1, 1.0-1)) = 0 => empty
        assert _heart_slot_state(1.0, 1) == "empty"

    def test_slot_second_slot_half(self):
        # health=1.5, slot=1 => v = max(0, min(1, 1.5-1)) = 0.5 => half
        assert _heart_slot_state(1.5, 1) == "half"


class TestHUD:
    def test_initial_health(self):
        hud = HUD()
        assert hud._health == settings.PLAYER_MAX_HEALTH

    def test_damage_event(self):
        hud = HUD()
        emit("PLAYER_DAMAGED", amount=1.0, source=(0, 0))
        dispatch()
        assert hud._health == settings.PLAYER_MAX_HEALTH - 1.0

    def test_heal_event(self):
        hud = HUD()
        emit("PLAYER_DAMAGED", amount=3.0, source=(0, 0))
        dispatch()
        emit("PLAYER_HEALED", amount=1.0)
        dispatch()
        assert hud._health == settings.PLAYER_MAX_HEALTH - 2.0

    def test_damage_below_zero(self):
        hud = HUD()
        emit("PLAYER_DAMAGED", amount=100.0, source=(0, 0))
        dispatch()
        assert hud._health == 0.0

    def test_heal_above_max(self):
        hud = HUD()
        emit("PLAYER_HEALED", amount=100.0)
        dispatch()
        assert hud._health == settings.PLAYER_MAX_HEALTH

    def test_timer_starts_at_zero(self):
        hud = HUD()
        hud.start_timer()
        assert hud.current_time == 0.0

    def test_timer_increases(self):
        hud = HUD()
        hud.start_timer()
        hud.update(1.0)
        assert hud.current_time == pytest.approx(1.0)

    def test_draw_does_not_crash(self):
        """HUD.draw() renders content on the surface."""
        hud = HUD()
        surface = pygame.Surface((320, 224))
        hud.draw(surface)
        # Content should be drawn (not all-black)
        assert surface.get_at((3, 3))[:3] != (0, 0, 0), "Portrait area should be drawn"


class TestHUDDestroy:
    """Destroy must unsubscribe all events to prevent callback accumulation."""

    def test_destroy_removes_subscriptions(self):
        hud = HUD()
        before = subscriber_count()
        hud.destroy()
        after = subscriber_count()
        assert after == before - 4, (
            f"Expected 4 fewer subscribers, got {before} -> {after}"
        )

    def test_destroy_is_idempotent(self):
        hud = HUD()
        hud.destroy()
        count_after_first = subscriber_count()
        hud.destroy()
        count_after_second = subscriber_count()
        assert count_after_second == count_after_first, (
            "Second destroy() should not change subscriber count"
        )

    def test_destroyed_hud_ignores_events(self):
        hud = HUD()
        initial_health = hud._health
        hud.destroy()
        emit("PLAYER_DAMAGED", amount=1.0, source=(0, 0))
        dispatch()
        assert hud._health == initial_health, (
            "Destroyed HUD should not process events"
        )
