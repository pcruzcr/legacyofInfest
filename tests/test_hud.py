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
from src.engine.core.event_bus import EventBus
from src.engine.core import settings


@pytest.fixture(autouse=True)
def reset_bus():
    EventBus.clear()
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
        EventBus.emit("PLAYER_DAMAGED", amount=1.0, source=(0, 0))
        EventBus.dispatch()
        assert hud._health == settings.PLAYER_MAX_HEALTH - 1.0

    def test_heal_event(self):
        hud = HUD()
        EventBus.emit("PLAYER_DAMAGED", amount=3.0, source=(0, 0))
        EventBus.dispatch()
        EventBus.emit("PLAYER_HEALED", amount=1.0)
        EventBus.dispatch()
        assert hud._health == settings.PLAYER_MAX_HEALTH - 2.0

    def test_damage_below_zero(self):
        hud = HUD()
        EventBus.emit("PLAYER_DAMAGED", amount=100.0, source=(0, 0))
        EventBus.dispatch()
        assert hud._health == 0.0

    def test_heal_above_max(self):
        hud = HUD()
        EventBus.emit("PLAYER_HEALED", amount=100.0)
        EventBus.dispatch()
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
        """HUD.draw() with a surface does not raise."""
        hud = HUD()
        surface = pygame.Surface((320, 224))
        hud.draw(surface)
        # No assertion needed — just verifying no crash
