"""Tests for HUD heart-fraction logic and event subscriptions.

See 24_TEST_PLAN.md §6.1 for test specifications.
"""

from src.engine.core.event_bus import EventBus
from src.engine.ui.hud import HUD, heart_slot_state


# ---------------------------------------------------------------------------
# Heart slot state (pure function) tests
# ---------------------------------------------------------------------------


def test_heart_full_state():
    """current_health = 5.0 → all 5 heart slots render as 'full'."""
    for i in range(5):
        assert heart_slot_state(5.0, i) == "full"


def test_heart_fraction_states():
    """health 2.6 → slots 0,1 full; slot 2 half; 3,4 empty."""
    assert heart_slot_state(2.6, 0) == "full"
    assert heart_slot_state(2.6, 1) == "full"
    assert heart_slot_state(2.6, 2) == "half"
    assert heart_slot_state(2.6, 3) == "empty"
    assert heart_slot_state(2.6, 4) == "empty"


def test_heart_zero_health():
    """current_health = 0.0 → all 5 slots are 'empty'."""
    for i in range(5):
        assert heart_slot_state(0.0, i) == "empty"


def test_heart_slot_state_full():
    """health exactly at integer boundary → full."""
    assert heart_slot_state(2.0, 1) == "full"


def test_heart_slot_state_half():
    """health exactly at 0.5 → half."""
    assert heart_slot_state(2.5, 2) == "half"


def test_heart_slot_state_three_quarter():
    """health 2.8 → slot 2 is three_quarter."""
    assert heart_slot_state(2.8, 2) == "three_quarter"


def test_heart_slot_state_quarter():
    """health exactly at 0.25 → quarter."""
    assert heart_slot_state(2.25, 2) == "quarter"


# ---------------------------------------------------------------------------
# HUD instance tests
# ---------------------------------------------------------------------------


def test_hud_does_not_crash_without_player():
    """HUD constructed and .update(dt)/.draw(surface) called with no
    PLAYER_DAMAGED ever emitted — no exception."""
    hud = HUD()
    hud.update(0.016)
    hud.draw(None)


def test_player_damaged_updates_health_display():
    """Emitting PLAYER_DAMAGED followed by EventBus.dispatch() changes
    the HUD's internal health-tracking value."""
    hud = HUD()
    EventBus._reset()
    EventBus.subscribe("PLAYER_DAMAGED", hud._on_player_damaged)
    EventBus.emit("PLAYER_DAMAGED", amount=1.0, source=(0.0, 0.0))
    EventBus.dispatch()
    assert hud._health == 5.0 - 1.0  # PLAYER_MAX_HEALTH = 5.0
