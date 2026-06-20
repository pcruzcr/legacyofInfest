"""
Module: event_bus
System: engine
Academic Unit: Framework scaffold
Description: Singleton-style event bus with queued dispatch. Events are
emitted immediately into a queue and dispatched synchronously at the
start of each frame via dispatch(). This decouples event producers
(entities, systems) from consumers (HUD, AudioManager, SceneManager).
"""

from typing import Any, Callable


class EventBus:
    """Singleton-style static class. All methods are classmethods.

    Usage:
        EventBus.subscribe("PLAYER_DAMAGED", my_callback)
        EventBus.emit("PLAYER_DAMAGED", amount=1.0, source=(0.0, 0.0))
        EventBus.dispatch()  # called once per frame by App
    """

    _subscribers: dict[str, list[Callable[..., None]]] = {}
    _queue: list[tuple[str, dict[str, Any]]] = []

    @classmethod
    def subscribe(cls, event_name: str, callback: Callable[..., None]) -> None:
        """Register *callback* for *event_name*.

        The callback receives the ``**data`` kwargs passed to ``emit()``.
        """
        if event_name not in cls._subscribers:
            cls._subscribers[event_name] = []
        cls._subscribers[event_name].append(callback)

    @classmethod
    def unsubscribe(
        cls, event_name: str, callback: Callable[..., None]
    ) -> None:
        """Remove a previously registered *callback* for *event_name*.

        If the callback was not registered, this is a no-op.
        """
        if event_name in cls._subscribers:
            try:
                cls._subscribers[event_name].remove(callback)
            except ValueError:
                pass

    @classmethod
    def emit(cls, event_name: str, **data: Any) -> None:
        """Queue an event for delivery at the next ``dispatch()`` call.

        Events are *not* delivered immediately — they are queued and
        flushed synchronously when ``dispatch()`` is called.
        """
        cls._queue.append((event_name, data))

    @classmethod
    def dispatch(cls) -> None:
        """Deliver all queued events. Called once per frame by App.

        Each queued event is delivered to every subscriber registered
        for that event name. The queue is cleared after delivery.
        """
        queue = cls._queue
        cls._queue = []
        for event_name, data in queue:
            callbacks = cls._subscribers.get(event_name, [])
            for callback in callbacks:
                callback(**data)

    @classmethod
    def _reset(cls) -> None:
        """Clear all subscribers and the pending queue.

        Intended for test teardown only — not part of the public API.
        """
        cls._subscribers.clear()
        cls._queue.clear()