"""
Module: event_bus
System: engine.core
Academic Unit: N/A
Description: Singleton-style pub/sub event dispatch system. Queue-based:
emit() queues the event, dispatch() drains the queue at the start of each frame.
"""
from __future__ import annotations
import logging
from typing import Callable, Any


class EventBus:
    """Singleton-style static class. All methods are classmethods."""

    _subscribers: dict[str, list[Callable[..., None]]] = {}
    _queue: list[tuple[str, dict[str, Any]]] = []

    @classmethod
    def subscribe(cls, event_name: str, callback: Callable[..., None]) -> None:
        """Subscribe a callback to an event name. Logs warning on duplicate."""
        if event_name not in cls._subscribers:
            cls._subscribers[event_name] = []
        if callback not in cls._subscribers[event_name]:
            cls._subscribers[event_name].append(callback)
        else:
            logging.warning(
                f"EventBus: duplicate subscribe for '{event_name}' — "
                f"callback {callback.__name__} already registered"
            )

    @classmethod
    def unsubscribe(cls, event_name: str, callback: Callable[..., None]) -> None:
        """Unsubscribe a callback from an event name."""
        if event_name in cls._subscribers:
            if callback in cls._subscribers[event_name]:
                cls._subscribers[event_name].remove(callback)
            if not cls._subscribers[event_name]:
                del cls._subscribers[event_name]

    @classmethod
    def unsubscribe_all(cls, events: list[str], callback: Callable[..., None]) -> None:
        """Unsubscribe a callback from multiple events at once. Useful for scene cleanup."""
        for event_name in events:
            cls.unsubscribe(event_name, callback)

    @classmethod
    def subscriber_count(cls) -> int:
        """Return total number of registered callbacks across all events."""
        return sum(len(cbs) for cbs in cls._subscribers.values())

    @classmethod
    def emit(cls, event_name: str, **data: Any) -> None:
        """Queues the event; dispatched at the start of the next frame."""
        cls._queue.append((event_name, data))

    @classmethod
    def dispatch(cls) -> None:
        """Called once per frame by App, before scene update. Drains the queue."""
        queue = cls._queue[:]
        cls._queue.clear()
        for event_name, data in queue:
            if event_name in cls._subscribers:
                for callback in cls._subscribers[event_name]:
                    callback(**data)

    @classmethod
    def clear(cls) -> None:
        """Clear all subscribers and pending events. Useful for testing."""
        cls._subscribers.clear()
        cls._queue.clear()
