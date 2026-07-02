"""
Module: test_event_bus
System: tests
Academic Unit: N/A
Description: Tests for EventBus singleton-style pub/sub dispatch system.
Covers: subscribe, emit (queued), unsubscribe, multiple subscribers,
and unrelated event isolation.
"""
from __future__ import annotations
import pytest
from src.engine.core.event_bus import subscribe, unsubscribe, emit, dispatch, clear


@pytest.fixture(autouse=True)
def reset_event_bus():
    """Clear EventBus state before each test."""
    clear()
    yield


def test_subscribe_and_emit():
    """A subscribed callback receives the exact **data kwargs passed to emit()."""
    received = {}

    def callback(**data):
        nonlocal received
        received = data

    subscribe("TEST_EVENT", callback)
    emit("TEST_EVENT", value=42, name="foo")
    dispatch()
    assert received == {"value": 42, "name": "foo"}


def test_emit_queues_not_immediate():
    """Calling emit() does not invoke the callback until dispatch() is called."""
    invoked = False

    def callback(**data):
        nonlocal invoked
        invoked = True

    subscribe("TEST_EVENT", callback)
    emit("TEST_EVENT")
    assert not invoked, "Callback was invoked before dispatch()"
    dispatch()
    assert invoked, "Callback was not invoked after dispatch()"


def test_unsubscribe_stops_delivery():
    """After unsubscribe(), a subsequent emit() + dispatch() does not invoke the callback."""
    invoked = False

    def callback(**data):
        nonlocal invoked
        invoked = True

    subscribe("TEST_EVENT", callback)
    unsubscribe("TEST_EVENT", callback)
    emit("TEST_EVENT")
    dispatch()
    assert not invoked


def test_multiple_subscribers():
    """Two callbacks subscribed to the same event both receive it."""
    results = []

    def cb1(**data):
        results.append("cb1")

    def cb2(**data):
        results.append("cb2")

    subscribe("TEST_EVENT", cb1)
    subscribe("TEST_EVENT", cb2)
    emit("TEST_EVENT")
    dispatch()
    assert results == ["cb1", "cb2"]


def test_unrelated_event_not_delivered():
    """A callback subscribed to 'FOO' does not fire when 'BAR' is emitted."""
    invoked = False

    def callback(**data):
        nonlocal invoked
        invoked = True

    subscribe("FOO", callback)
    emit("BAR")
    dispatch()
    assert not invoked
