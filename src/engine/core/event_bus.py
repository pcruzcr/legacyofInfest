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
        self._dispatching: bool = False

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
            else:
                logging.warning(
                    f"EventBus: callback not found for '{event_name}' — "
                    f"callback {callback.__name__} not registered"
                )
            if not self._subscribers[event_name]:
                del self._subscribers[event_name]
        else:
            logging.warning(
                f"EventBus: no subscribers for '{event_name}'"
            )

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
        """
        Called once per frame by App, before scene update. Drains the queue.
        BUG-048: Recursion guard prevents re-entrant dispatch.
        """
        if self._dispatching:
            return
        self._dispatching = True
        try:
            queue = self._queue[:]
            self._queue.clear()
            for event_name, data in queue:
                if event_name in self._subscribers:
                    for callback in list(self._subscribers[event_name]):
                        try:
                            callback(**data)
                        except Exception:
                            logging.error(
                                f"EventBus: callback {callback.__name__} failed for '{event_name}'",
                                exc_info=True,
                            )
        finally:
            self._dispatching = False

    def clear(self) -> None:
        """Clear all subscribers and pending events. Useful for testing."""
        self._subscribers.clear()
        self._queue.clear()

    @property
    def queue_snapshot(self) -> list[tuple[str, dict[str, object]]]:
        """Read-only snapshot of the pending event queue."""
        return list(self._queue)

    @property
    def subscribers_snapshot(self) -> dict[str, list[str]]:
        """Read-only snapshot of subscribers, mapping event_name -> callback names."""
        return {evt: [cb.__name__ for cb in cbs]
                for evt, cbs in self._subscribers.items()}


# ── Module-level default instance for infrastructure ──────────────────

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