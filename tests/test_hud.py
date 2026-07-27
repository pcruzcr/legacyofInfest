"""
Module: test_hud
System: tests
Description: Tests for HUD: heart slot states, timer display,
event-driven health updates.
"""
from __future__ import annotations

import pygame
import pytest

from src.engine.core import settings
from src.engine.core.event_bus import EventBus
from src.engine.ui.hud import HUD, _heart_slot_state


@pytest.fixture(autouse=True)
def _init_pygame() -> None:
    if not pygame.get_init():
        pygame.init()


class TestHeartSlotState:
    """Pure function tests for _heart_slot_state."""

    def test_slot_full(self) -> None:
        assert _heart_slot_state(5.0, 0) == "full"
        assert _heart_slot_state(5.0, 1) == "full"

    def test_slot_empty(self) -> None:
        assert _heart_slot_state(0.0, 0) == "empty"
        assert _heart_slot_state(0.0, 1) == "empty"

    def test_slot_half(self) -> None:
        assert _heart_slot_state(0.5, 0) == "half"

    def test_slot_three_quarter(self) -> None:
        assert _heart_slot_state(0.75, 0) == "three_quarter"

    def test_slot_quarter(self) -> None:
        assert _heart_slot_state(0.25, 0) == "quarter"

    def test_slot_negative_health(self) -> None:
        assert _heart_slot_state(-1.0, 0) == "empty"

    def test_slot_beyond_max(self) -> None:
        assert _heart_slot_state(10.0, 0) == "full"

    def test_slot_second_slot_empty(self) -> None:
        assert _heart_slot_state(1.0, 1) == "empty"

    def test_slot_second_slot_half(self) -> None:
        assert _heart_slot_state(1.5, 1) == "half"


class TestHUD:
    def test_initial_health(self, event_bus: EventBus) -> None:
        hud = HUD(event_bus)
        assert hud._health == settings.PLAYER_MAX_HEALTH

    def test_damage_event(self, event_bus: EventBus) -> None:
        hud = HUD(event_bus)
        event_bus.emit("PLAYER_DAMAGED", amount=1.0, source=(0, 0))
        event_bus.dispatch()
        assert hud._health == settings.PLAYER_MAX_HEALTH - 1.0

    def test_heal_event(self, event_bus: EventBus) -> None:
        hud = HUD(event_bus)
        event_bus.emit("PLAYER_DAMAGED", amount=3.0, source=(0, 0))
        event_bus.dispatch()
        event_bus.emit("PLAYER_HEALED", amount=1.0)
        event_bus.dispatch()
        assert hud._health == settings.PLAYER_MAX_HEALTH - 2.0

    def test_damage_below_zero(self, event_bus: EventBus) -> None:
        hud = HUD(event_bus)
        event_bus.emit("PLAYER_DAMAGED", amount=100.0, source=(0, 0))
        event_bus.dispatch()
        assert hud._health == 0.0

    def test_heal_above_max(self, event_bus: EventBus) -> None:
        hud = HUD(event_bus)
        event_bus.emit("PLAYER_HEALED", amount=100.0)
        event_bus.dispatch()
        assert hud._health == settings.PLAYER_MAX_HEALTH

    def test_timer_starts_at_zero(self, event_bus: EventBus) -> None:
        hud = HUD(event_bus)
        hud.start_timer()
        assert hud.current_time == 0.0

    def test_timer_increases(self, event_bus: EventBus) -> None:
        hud = HUD(event_bus)
        hud.start_timer()
        hud.update(1.0)
        assert hud.current_time == pytest.approx(1.0)

    def test_draw_does_not_crash(self, event_bus: EventBus) -> None:
        hud = HUD(event_bus)
        surface = pygame.Surface((320, 224))
        hud.draw(surface)
        assert surface.get_at((3, 3))[:3] != (0, 0, 0)


class TestHUDDestroy:
    def test_destroy_removes_subscriptions(self, event_bus: EventBus) -> None:
        hud = HUD(event_bus)
        before = event_bus.subscriber_count()
        hud.destroy()
        after = event_bus.subscriber_count()
        assert after == before - 6

    def test_destroy_is_idempotent(self, event_bus: EventBus) -> None:
        hud = HUD(event_bus)
        hud.destroy()
        count_after_first = event_bus.subscriber_count()
        hud.destroy()
        count_after_second = event_bus.subscriber_count()
        assert count_after_second == count_after_first

    def test_destroyed_hud_ignores_events(self, event_bus: EventBus) -> None:
        hud = HUD(event_bus)
        initial_health = hud._health
        hud.destroy()
        event_bus.emit("PLAYER_DAMAGED", amount=1.0, source=(0, 0))
        event_bus.dispatch()
        assert hud._health == initial_health
