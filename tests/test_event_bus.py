"""
Module: test_event_bus
System: tests
Academic Unit: N/A
Description: Tests for EventBus instance-based pub/sub dispatch system.
Covers: subscribe, emit (queued), dispatch, unsubscribe, multiple
subscribers, wildcard literal, clear(), and recursion guard.
"""
from __future__ import annotations

import pytest
from src.engine.core.event_bus import EventBus


@pytest.fixture
def bus() -> EventBus:
    return EventBus()


def test_subscribe_emit_dispatch_calls_callback(bus: EventBus) -> None:
    received: dict = {}

    def callback(**data: object) -> None:
        nonlocal received
        received = data

    bus.subscribe("TEST_EVENT", callback)
    bus.emit("TEST_EVENT", value=42, name="foo")
    bus.dispatch()
    assert received == {"value": 42, "name": "foo"}


def test_unsubscribe_stops_delivery(bus: EventBus) -> None:
    invoked = False

    def callback(**data: object) -> None:
        nonlocal invoked
        invoked = True

    bus.subscribe("TEST_EVENT", callback)
    bus.unsubscribe("TEST_EVENT", callback)
    bus.emit("TEST_EVENT")
    bus.dispatch()
    assert not invoked


def test_multiple_subscribers_all_called(bus: EventBus) -> None:
    results: list[int] = []

    def cb1(**data: object) -> None:
        results.append(1)

    def cb2(**data: object) -> None:
        results.append(2)

    bus.subscribe("TEST_EVENT", cb1)
    bus.subscribe("TEST_EVENT", cb2)
    bus.emit("TEST_EVENT")
    bus.dispatch()
    assert results == [1, 2]


def test_wildcard_as_literal_event_name(bus: EventBus) -> None:
    wildcard_called = False
    other_called = False

    def wildcard_cb(**data: object) -> None:
        nonlocal wildcard_called
        wildcard_called = True

    def other_cb(**data: object) -> None:
        nonlocal other_called
        other_called = True

    bus.subscribe("*", wildcard_cb)
    bus.subscribe("SPECIFIC", other_cb)

    bus.emit("SPECIFIC")
    bus.dispatch()
    assert other_called
    assert not wildcard_called


def test_clear_removes_all_subscribers_and_queue(bus: EventBus) -> None:
    invoked = False

    def callback(**data: object) -> None:
        nonlocal invoked
        invoked = True

    bus.subscribe("TEST", callback)
    bus.emit("TEST")
    bus.clear()
    bus.dispatch()
    assert not invoked
    assert bus.subscriber_count() == 0
    assert bus.queue_snapshot == []


def test_recursion_guard_via_queue_snapshot(bus: EventBus) -> None:
    inner_invoked = False

    def inner_cb(**data: object) -> None:
        nonlocal inner_invoked
        inner_invoked = True

    def outer_cb(**data: object) -> None:
        bus.emit("INNER")

    bus.subscribe("OUTER", outer_cb)
    bus.subscribe("INNER", inner_cb)

    bus.emit("OUTER")
    bus.dispatch()

    assert not inner_invoked, "Inner event should NOT be dispatched in same cycle"

    bus.dispatch()
    assert inner_invoked, "Inner event should be dispatched in next cycle"


def test_unsubscribe_nonexistent_does_not_raise(bus: EventBus) -> None:
    def callback(**data: object) -> None:
        pass

    bus.unsubscribe("NONEXISTENT", callback)


def test_duplicate_subscribe_logs_warning(bus: EventBus, caplog: pytest.LogCaptureFixture) -> None:
    def callback(**data: object) -> None:
        pass

    bus.subscribe("EVENT", callback)
    bus.subscribe("EVENT", callback)

    assert "duplicate" in caplog.text.lower()


def test_subscribers_snapshot_returns_names(bus: EventBus) -> None:
    def my_cb(**data: object) -> None:
        pass

    bus.subscribe("EVT", my_cb)
    snap = bus.subscribers_snapshot
    assert "EVT" in snap
    assert "my_cb" in snap["EVT"]
