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


def test_duplicate_subscribe_is_idempotent(bus: EventBus) -> None:
    """Subscribing the same callback twice must not double-deliver.

    Rewritten (AUD-019): this test used to assert that a warning containing the
    word "duplicate" reached the log. That pinned the logging implementation
    rather than the contract, and the contract is what callers depend on —
    scenes re-arm their handlers after a respawn and must not end up receiving
    every event twice. Duplicate subscription is now a DEBUG-level detail, so
    the behaviour is asserted directly instead.
    """
    calls: list[int] = []

    def callback(**data: object) -> None:
        calls.append(1)

    bus.subscribe("EVENT", callback)
    bus.subscribe("EVENT", callback)
    assert bus.subscriber_count() == 1

    bus.emit("EVENT")
    bus.dispatch()
    assert calls == [1], f"handler fired {len(calls)} times for one event"


def test_collected_subscriber_is_dropped(bus: EventBus) -> None:
    """A subscriber whose owner is collected stops firing and is pruned.

    AUD-028: the bus previously held strong references, so a popped scene was
    kept alive forever and its handlers kept firing on a destroyed object.
    """
    import gc

    class Listener:
        def __init__(self) -> None:
            self.hits = 0

        def on_event(self, **data: object) -> None:
            self.hits += 1

    listener = Listener()
    bus.subscribe("EVENT", listener.on_event)

    bus.emit("EVENT")
    bus.dispatch()
    assert listener.hits == 1

    del listener
    gc.collect()

    bus.emit("EVENT")
    bus.dispatch()  # must not raise, and must prune the dead subscription
    assert bus.subscriber_count() == 0


def test_partial_callback_failure_does_not_mask_the_error(
    bus: EventBus, caplog: pytest.LogCaptureFixture,
) -> None:
    """AUD-029: the error handler used to raise on callbacks without __name__.

    ``functools.partial`` has no ``__name__``, so ``callback.__name__`` inside
    the ``except`` block raised ``AttributeError``, discarding the real
    exception and replacing a useful diagnostic with a misleading one.
    """
    import functools

    def handler(flag: object, **data: object) -> None:
        raise ValueError("boom")

    bound = functools.partial(handler, flag=True)
    bus.subscribe("EVENT", bound)
    bus.emit("EVENT")

    bus.dispatch()  # must not propagate AttributeError

    assert "boom" in caplog.text or "ValueError" in caplog.text


def test_subscribers_snapshot_returns_names(bus: EventBus) -> None:
    def my_cb(**data: object) -> None:
        pass

    bus.subscribe("EVT", my_cb)
    snap = bus.subscribers_snapshot
    assert "EVT" in snap
    assert "my_cb" in snap["EVT"]
