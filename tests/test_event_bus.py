"""
Tests for EventBus — singleton-style event dispatch system.

See 24_TEST_PLAN.md §3.1 for test specifications.
"""

import pytest

from src.engine.core.event_bus import EventBus


@pytest.fixture(autouse=True)
def reset_event_bus():
    """Reset EventBus state before and after each test."""
    EventBus._reset()
    yield
    EventBus._reset()


def test_subscribe_and_emit():
    """A subscribed callback receives the exact **data kwargs from emit()."""
    received = {}

    def callback(**data):
        received.update(data)

    EventBus.subscribe("PLAYER_DAMAGED", callback)
    EventBus.emit("PLAYER_DAMAGED", amount=1.0, source=(0.0, 0.0))
    EventBus.dispatch()

    assert received == {"amount": 1.0, "source": (0.0, 0.0)}


def test_emit_queues_not_immediate():
    """emit() queues the event; callback runs only after dispatch()."""
    invoked = False

    def callback(**data):
        nonlocal invoked
        invoked = True

    EventBus.subscribe("TEST", callback)
    EventBus.emit("TEST", value=42)

    # Should NOT have been invoked yet
    assert not invoked, "Callback was invoked before dispatch()"

    EventBus.dispatch()
    assert invoked, "Callback was not invoked after dispatch()"


def test_unsubscribe_stops_delivery():
    """After unsubscribe(), a subsequent emit() + dispatch() does not
    invoke the callback."""
    call_count = 0

    def callback(**data):
        nonlocal call_count
        call_count += 1

    EventBus.subscribe("TEST", callback)
    EventBus.emit("TEST")
    EventBus.dispatch()
    assert call_count == 1

    EventBus.unsubscribe("TEST", callback)
    EventBus.emit("TEST")
    EventBus.dispatch()
    assert call_count == 1, "Callback was invoked after unsubscribe()"


def test_multiple_subscribers():
    """Two callbacks subscribed to the same event both receive it."""
    results_1 = []
    results_2 = []

    def cb1(**data):
        results_1.append(data.get("msg"))

    def cb2(**data):
        results_2.append(data.get("msg"))

    EventBus.subscribe("EVENT", cb1)
    EventBus.subscribe("EVENT", cb2)
    EventBus.emit("EVENT", msg="hello")
    EventBus.dispatch()

    assert results_1 == ["hello"]
    assert results_2 == ["hello"]


def test_unrelated_event_not_delivered():
    """A callback subscribed to 'FOO' does not fire when 'BAR' is emitted."""
    received_foo = []
    received_bar = []

    def foo_cb(**data):
        received_foo.append(data)

    def bar_cb(**data):
        received_bar.append(data)

    EventBus.subscribe("FOO", foo_cb)
    EventBus.subscribe("BAR", bar_cb)

    EventBus.emit("FOO", x=1)
    EventBus.dispatch()

    assert len(received_foo) == 1
    assert len(received_bar) == 0

    EventBus.emit("BAR", y=2)
    EventBus.dispatch()

    assert len(received_foo) == 1
    assert len(received_bar) == 1
