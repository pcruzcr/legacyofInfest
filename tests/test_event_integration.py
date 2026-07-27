"""Integration tests for EventBus events — verifies event contracts end-to-end."""
from __future__ import annotations

from typing import Any

import pytest

from src.engine.core.event_bus import EventBus
from src.engine.core.events import Events


def test_all_events_have_constant_in_events_class() -> None:
    """Every event string used in emit/subscribe should be defined as a constant."""
    events_attr = {v for k, v in vars(Events).items() if isinstance(v, str) and not k.startswith("_")}
    assert "PLAYER_DAMAGED" in events_attr
    assert "PLAYER_DIED" in events_attr
    assert "STAGE_COMPLETE" in events_attr
    assert "ENEMY_DIED" in events_attr
    assert len(events_attr) >= 35  # at least 35 events defined


class TestCriticalEventFlow:
    """Integration tests for critical gameplay events.
    
    These tests verify that the event contract (emitter → subscriber → payload)
    is respected for events that directly affect gameplay.
    """

    @pytest.fixture
    def bus(self) -> EventBus:
        return EventBus()

    def test_player_damaged_flow(self, bus: EventBus) -> None:
        """PLAYER_DAMAGED carries amount and source position."""
        received: dict[str, Any] = {}

        def handler(**data: Any) -> None:
            nonlocal received
            received = data

        bus.subscribe(Events.PLAYER_DAMAGED, handler)
        bus.emit(Events.PLAYER_DAMAGED, amount=15.0, source=(100.0, 200.0))
        bus.dispatch()

        assert "amount" in received
        assert "source" in received
        assert received["amount"] == 15.0
        assert received["source"] == (100.0, 200.0)

    def test_player_died_flow(self, bus: EventBus) -> None:
        """PLAYER_DIED carries position payload from StageScene."""
        received: dict[str, Any] = {}

        def handler(**data: Any) -> None:
            nonlocal received
            received = data

        bus.subscribe(Events.PLAYER_DIED, handler)
        bus.emit(Events.PLAYER_DIED, pos=(320.0, 240.0))
        bus.dispatch()

        assert "pos" in received
        assert received["pos"] == (320.0, 240.0)

    def test_enemy_died_flow(self, bus: EventBus) -> None:
        """ENEMY_DIED carries entity_id and position."""
        received: dict[str, Any] = {}

        def handler(**data: Any) -> None:
            nonlocal received
            received = data

        bus.subscribe(Events.ENEMY_DIED, handler)
        bus.emit(Events.ENEMY_DIED, entity_id=7, position=(400.0, 300.0))
        bus.dispatch()

        assert received.get("entity_id") == 7
        assert received.get("position") == (400.0, 300.0)

    def test_stage_complete_flow(self, bus: EventBus) -> None:
        """STAGE_COMPLETE carries stage_id."""
        received: dict[str, Any] = {}

        def handler(**data: Any) -> None:
            nonlocal received
            received = data

        bus.subscribe(Events.STAGE_COMPLETE, handler)
        bus.emit(Events.STAGE_COMPLETE, stage_id="stage0")
        bus.dispatch()

        assert "stage_id" in received
        assert received["stage_id"] == "stage0"

    def test_checkpoint_reached_flow(self, bus: EventBus) -> None:
        """CHECKPOINT_REACHED carries checkpoint_id."""
        received: dict[str, Any] = {}

        def handler(**data: Any) -> None:
            nonlocal received
            received = data

        bus.subscribe(Events.CHECKPOINT_REACHED, handler)
        bus.emit(Events.CHECKPOINT_REACHED, checkpoint_id=3)
        bus.dispatch()

        assert received.get("checkpoint_id") == 3

    def test_boss_phase_changed_flow(self, bus: EventBus) -> None:
        """BOSS_PHASE_CHANGED carries boss_name, phase, phase_name."""
        received: dict[str, Any] = {}

        def handler(**data: Any) -> None:
            nonlocal received
            received = data

        bus.subscribe(Events.BOSS_PHASE_CHANGED, handler)
        bus.emit(Events.BOSS_PHASE_CHANGED, boss_name="Venado", phase=2, phase_name="Phase 2")
        bus.dispatch()

        assert received.get("boss_name") == "Venado"
        assert received.get("phase") == 2
        assert received.get("phase_name") == "Phase 2"

    def test_vfx_parry_flow(self, bus: EventBus) -> None:
        """VFX_PARRY carries position."""
        received: dict[str, Any] = {}

        def handler(**data: Any) -> None:
            nonlocal received
            received = data

        bus.subscribe(Events.VFX_PARRY, handler)
        bus.emit(Events.VFX_PARRY, pos=(500.0, 150.0))
        bus.dispatch()

        assert "pos" in received
        assert received["pos"] == (500.0, 150.0)

    def test_sfx_events_are_emitted_without_payload(self, bus: EventBus) -> None:
        """SFX events should not crash when emitted (payload is optional)."""
        sfx_events = [
            Events.SFX_PLAYER_JUMP,
            Events.SFX_PLAYER_LAND,
            Events.SFX_HIT_CONNECT,
            Events.SFX_ENEMY_HIT,
            Events.SFX_MENU_HOVER,
            Events.SFX_MENU_CONFIRM,
            Events.SFX_CHECKPOINT,
        ]
        called: list[str] = []

        def handler(**data: Any) -> None:
            called.append("x")

        for evt in sfx_events:
            bus.subscribe(evt, handler)

        for evt in sfx_events:
            bus.emit(evt)

        bus.dispatch()
        assert len(called) == len(sfx_events)

    def test_multiple_subscribers_all_receive_event(self, bus: EventBus) -> None:
        """Critical events can have multiple subscribers."""
        results: list[int] = []

        def cb1(**data: Any) -> None:
            results.append(1)

        def cb2(**data: Any) -> None:
            results.append(2)

        bus.subscribe(Events.STAGE_COMPLETE, cb1)
        bus.subscribe(Events.STAGE_COMPLETE, cb2)
        bus.emit(Events.STAGE_COMPLETE, stage_id="boss_venado")
        bus.dispatch()

        assert results == [1, 2]

    def test_save_requested_flow(self, bus: EventBus) -> None:
        """SAVE_REQUESTED carries full save data payload."""
        received: dict[str, Any] = {}

        def handler(**data: Any) -> None:
            nonlocal received
            received = data

        bus.subscribe(Events.SAVE_REQUESTED, handler)
        bus.emit(
            Events.SAVE_REQUESTED,
            stage_id="stage0",
            stage_index=0,
            checkpoint_x=320.0,
            checkpoint_y=240.0,
            health=80,
            max_health=100,
        )
        bus.dispatch()

        assert received.get("stage_id") == "stage0"
        assert received.get("checkpoint_x") == 320.0
        assert received.get("health") == 80

    def test_achievement_unlocked_flow(self, bus: EventBus) -> None:
        """ACHIEVEMENT_UNLOCKED carries achievement_id and name."""
        received: dict[str, Any] = {}

        def handler(**data: Any) -> None:
            nonlocal received
            received = data

        bus.subscribe(Events.ACHIEVEMENT_UNLOCKED, handler)
        bus.emit(Events.ACHIEVEMENT_UNLOCKED, achievement_id="kill_10_enemies", name="Slayer")
        bus.dispatch()

        assert received.get("achievement_id") == "kill_10_enemies"
        assert received.get("name") == "Slayer"

    def test_show_message_flow(self, bus: EventBus) -> None:
        """SHOW_MESSAGE carries text and duration."""
        received: dict[str, Any] = {}

        def handler(**data: Any) -> None:
            nonlocal received
            received = data

        bus.subscribe(Events.SHOW_MESSAGE, handler)
        bus.emit(Events.SHOW_MESSAGE, text="Hello!", duration=5.0)
        bus.dispatch()

        assert received.get("text") == "Hello!"
        assert received.get("duration") == 5.0


class TestEventConsistency:
    """Ensure event names are consistent across the codebase."""

    def test_events_class_has_all_expected_constants(self) -> None:
        """Verify known event names exist as constants."""
        required = [
            "PLAYER_DAMAGED", "PLAYER_DIED", "PLAYER_HEALED",
            "ENEMY_DIED", "BOSS_PHASE_CHANGED", "BOSS_ATTACK",
            "SHOW_MESSAGE", "HIDE_MESSAGE",
            "CHECKPOINT_REACHED", "STAGE_COMPLETE",
            "SAVE_REQUESTED",
            "ACHIEVEMENT_UNLOCKED", "ACHIEVEMENT_PROGRESS",
            "VFX_PARRY", "VFX_CHARGE", "VFX_SLAM", "VFX_ULTIMATE",
            "ITEM_COLLECTED", "FLAG_SET",
        ]
        for name in required:
            assert hasattr(Events, name), f"Missing event constant: {name}"

    def test_event_strings_match_constant_names(self) -> None:
        """Each event string should equal its constant name for debuggability."""
        for attr_name in dir(Events):
            if attr_name.startswith("_"):
                continue
            val = getattr(Events, attr_name)
            if isinstance(val, str):
                assert val == attr_name, (
                    f"Events.{attr_name} = '{val}' but expected '{attr_name}'"
                )

    def test_orphan_events_exist_but_are_defined(self) -> None:
        """Events defined for future use should at least be valid strings."""
        orphan = [
            Events.SFX_BOSSES_GAVILAN_DIVE,
            Events.SFX_BOSSES_GAVILAN_MASK_BEAM,
            Events.SFX_BOSSES_PABURU_EYE_BEAM,
            Events.SFX_BOSSES_PABURU_WAVE,
            Events.SFX_BOSSES_RELIC_APPEAR,
            Events.SFX_BOSSES_REY_SPIT,
            Events.SFX_BOSSES_REY_SPLIT,
        ]
        for evt in orphan:
            assert isinstance(evt, str)
            assert len(evt) > 0


class TestEventBusIntegration:
    """Tests that verify EventBus integration patterns used across the codebase."""

    def test_emit_without_subscribers_does_not_crash(self, event_bus: EventBus) -> None:
        """Emitted events with no subscribers should be no-ops."""
        event_bus.emit(Events.SFX_PLAYER_JUMP)
        event_bus.dispatch()

    def test_subscribe_then_unsubscribe_leaves_no_trace(self, event_bus: EventBus) -> None:
        """After unsubscribe, an event should not be deliverable."""
        called = False

        def handler(**data: Any) -> None:
            nonlocal called
            called = True

        event_bus.subscribe(Events.STAGE_COMPLETE, handler)
        event_bus.unsubscribe(Events.STAGE_COMPLETE, handler)
        event_bus.emit(Events.STAGE_COMPLETE, stage_id="test")
        event_bus.dispatch()
        assert not called

    def test_subscriber_snapshot_matches_subscribed_count(self, event_bus: EventBus) -> None:
        """subscribers_snapshot should reflect current subscriptions."""
        def h1(**d: Any) -> None: pass
        def h2(**d: Any) -> None: pass

        event_bus.subscribe("A", h1)
        event_bus.subscribe("A", h2)
        event_bus.subscribe("B", h1)

        snap = event_bus.subscribers_snapshot
        assert len(snap["A"]) == 2
        assert len(snap["B"]) == 1
