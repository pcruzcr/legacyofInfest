"""
Module: event_bus
System: engine.core
Academic Unit: N/A
Description: Pub/sub event dispatch system. Queue-based:
emit() queues the event, dispatch() drains the queue at the start of each frame.

DI NOTE (Fase 1): Now instance-based. Module-level convenience functions
subscribe() / unsubscribe() / emit() / etc. delegate to a default instance
for backward compatibility with existing callers.
"""
from __future__ import annotations
import logging
from typing import Callable, Any


class EventBus:
    """
    Instance-based publish/subscribe event bus.
    Each instance has independent subscriber lists and event queues.
    """

    def __init__(self) -> None:
        self._subscribers: dict[str, list[Callable[..., None]]] = {}
        self._queue: list[tuple[str, dict[str, Any]]] = []

    def subscribe(self, event_name: str, callback: Callable[..., None]) -> None:
        """Subscribe a callback to an event name. Logs warning on duplicate."""
        if event_name not in self._subscribers:
            self._subscribers[event_name] = []
        if callback not in self._subscribers[event_name]:
            self._subscribers[event_name].append(callback)
        else:
            logging.warning(
                f"EventBus: duplicate subscribe for '{event_name}' — "
                f"callback {callback.__name__} already registered"
            )

    def unsubscribe(self, event_name: str, callback: Callable[..., None]) -> None:
        """Unsubscribe a callback from an event name."""
        if event_name in self._subscribers:
            if callback in self._subscribers[event_name]:
                self._subscribers[event_name].remove(callback)
            if not self._subscribers[event_name]:
                del self._subscribers[event_name]

    def unsubscribe_all(self, events: list[str], callback: Callable[..., None]) -> None:
        """Unsubscribe a callback from multiple events at once."""
        for event_name in events:
            self.unsubscribe(event_name, callback)

    def subscriber_count(self) -> int:
        """Return total number of registered callbacks across all events."""
        return sum(len(cbs) for cbs in self._subscribers.values())

    def emit(self, event_name: str, **data: Any) -> None:
        """Queues the event; dispatched at the start of the next frame."""
        self._queue.append((event_name, data))

    def dispatch(self) -> None:
        """Called once per frame by App, before scene update. Drains the queue."""
        queue = self._queue[:]
        self._queue.clear()
        for event_name, data in queue:
            if event_name in self._subscribers:
                for callback in self._subscribers[event_name]:
                    callback(**data)

    def clear(self) -> None:
        """Clear all subscribers and pending events. Useful for testing."""
        self._subscribers.clear()
        self._queue.clear()


# ── Module-level default instance for backward compatibility ────────────

_default_bus: EventBus | None = None


def set_default_bus(bus: EventBus) -> None:
    """Set the module-level default EventBus instance (called by App)."""
    global _default_bus
    _default_bus = bus


def _get_bus() -> EventBus:
    """Lazy-init and return the default EventBus instance."""
    global _default_bus
    if _default_bus is None:
        _default_bus = EventBus()
    return _default_bus


# ── Backward-compatible convenience functions ──────────────────────────
# These replace old EventBus.subscribe(...) calls with subscribe(...).
# Both import paths are supported for migration:
#   from src.engine.core.event_bus import EventBus  →  EventBus().subscribe()
#   from src.engine.core.event_bus import subscribe  →  subscribe()

def subscribe(event_name: str, callback: Callable[..., None]) -> None:
    """Subscribe via the default EventBus instance."""
    _get_bus().subscribe(event_name, callback)


def unsubscribe(event_name: str, callback: Callable[..., None]) -> None:
    """Unsubscribe via the default EventBus instance."""
    _get_bus().unsubscribe(event_name, callback)


def unsubscribe_all(events: list[str], callback: Callable[..., None]) -> None:
    """Unsubscribe from multiple events via the default EventBus instance."""
    _get_bus().unsubscribe_all(events, callback)


def subscriber_count() -> int:
    """Return total subscriber count on the default EventBus instance."""
    return _get_bus().subscriber_count()


def emit(event_name: str, **data: Any) -> None:
    """Emit an event via the default EventBus instance."""
    _get_bus().emit(event_name, **data)


def dispatch() -> None:
    """Dispatch queued events on the default EventBus instance."""
    _get_bus().dispatch()


def clear() -> None:
    """Clear subscribers and queue on the default EventBus instance."""
    _get_bus().clear()
