"""
Module: event_bus
System: engine.core
Academic Unit: N/A

Queue-based publish/subscribe dispatch. ``emit()`` queues an event;
``dispatch()`` drains the queue once per frame, before scene update.

Design notes
------------
**Weak subscriber references (AUD-028).** The bus holds *weak* references to
subscriber callbacks. A scene that is popped without unsubscribing is therefore
garbage-collectable, and its now-dead callbacks are dropped on the next
dispatch instead of firing forever on a destroyed object. Strong-reference
buses are a classic source of both leaks and use-after-destroy bugs in scene
stacks, and this codebase had no automatic cleanup despite ``SceneManager``'s
docstring claiming otherwise.

Callers may still unsubscribe explicitly — and should, when the lifetime is
known — but forgetting is no longer a leak.

**No module-level singleton (AUD-019).** An earlier revision exposed
``_get_bus()`` returning a lazily created global, used by ``achievements``,
``checkpoint``, ``base_entity`` and ``debug_overlay``, while scenes used the
injected ``context.event_bus``. In production ``App`` called
``set_default_bus()`` so the two coincided; under test they did not, so an
entity could emit into one bus while the scene under test listened to another.
Every consumer now receives its bus explicitly.
"""
from __future__ import annotations

import logging
import weakref
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)


def _describe(callback: Callable[..., None]) -> str:
    """Human-readable name for a callback, for log messages.

    AUD-029: the previous code used ``callback.__name__`` directly inside an
    ``except`` block. ``functools.partial`` objects and callable class
    instances have no ``__name__``, so the error handler itself raised
    ``AttributeError`` — losing the original exception and replacing a useful
    diagnostic with a confusing one.
    """
    name = getattr(callback, "__name__", None)
    if name:
        return name
    return type(callback).__name__


class _Subscription:
    """A weak reference to a callback, comparable by referent identity.

    Bound methods are recreated on every attribute access, so a plain
    ``weakref.ref`` to one dies immediately. ``weakref.WeakMethod`` handles
    that case; plain functions and callables use ``weakref.ref``. Objects that
    cannot be weak-referenced at all (some C types) are held strongly, which
    is the safe fallback.
    """

    __slots__ = ("__weakref__", "_name", "_ref", "_strong")

    def __init__(self, callback: Callable[..., None]) -> None:
        self._name = _describe(callback)
        self._strong: Callable[..., None] | None = None
        self._ref: Any = None
        try:
            if hasattr(callback, "__self__") and hasattr(callback, "__func__"):
                self._ref = weakref.WeakMethod(callback)
            else:
                self._ref = weakref.ref(callback)
        except TypeError:
            # Not weak-referenceable (e.g. a functools.partial or a builtin).
            self._strong = callback

    @property
    def name(self) -> str:
        return self._name

    def resolve(self) -> Callable[..., None] | None:
        """The callback, or None if its owner has been collected."""
        if self._strong is not None:
            return self._strong
        return self._ref()

    def is_alive(self) -> bool:
        return self.resolve() is not None

    def matches(self, callback: Callable[..., None]) -> bool:
        return self.resolve() == callback


class EventBus:
    """Instance-based publish/subscribe event bus.

    Each instance has independent subscriber lists and event queues.
    """

    def __init__(self) -> None:
        self._subscribers: dict[str, list[_Subscription]] = {}
        self._queue: list[tuple[str, dict[str, Any]]] = []
        self._dispatching: bool = False

    # ── subscription ───────────────────────────────────────────

    def subscribe(self, event_name: str, callback: Callable[..., None]) -> None:
        """Subscribe ``callback`` to ``event_name``. Subscribing twice is a no-op.

        .. important::
           The bus holds a **weak** reference. The caller must keep the
           callback alive for as long as it should fire — which happens
           naturally for bound methods (the owning object holds them) and for
           closures stored on the subscriber, as ``StageScene`` does with
           ``self._sfx_handlers``. Subscribing a throwaway lambda that nothing
           else references will not raise, but the subscription is collected
           and dropped at the next dispatch, with a warning logged so the
           "my handler stopped firing" symptom is diagnosable rather than
           mysterious.
        """
        subs = self._subscribers.setdefault(event_name, [])
        for existing in subs:
            if existing.matches(callback):
                # Idempotent by contract: re-subscribing the same callback is
                # how scenes defensively re-arm handlers after a respawn.
                logger.debug(
                    "EventBus: '%s' already has %s registered; ignoring duplicate",
                    event_name, _describe(callback),
                )
                return
        subs.append(_Subscription(callback))

    def unsubscribe(self, event_name: str, callback: Callable[..., None]) -> None:
        """Unsubscribe ``callback`` from ``event_name``.

        Unsubscribing something that is not subscribed is a no-op, not a
        warning. Scenes defensively unsubscribe in ``on_exit`` whether or not
        they ever subscribed; the previous implementation logged a warning for
        each such call, burying real problems under routine noise.
        """
        subs = self._subscribers.get(event_name)
        if not subs:
            return
        self._subscribers[event_name] = [
            s for s in subs if s.is_alive() and not s.matches(callback)
        ]
        if not self._subscribers[event_name]:
            del self._subscribers[event_name]

    def unsubscribe_all(self, events: list[str], callback: Callable[..., None]) -> None:
        """Unsubscribe ``callback`` from several events at once."""
        for event_name in events:
            self.unsubscribe(event_name, callback)

    def subscriber_count(self) -> int:
        """Total live callbacks across all events."""
        return sum(
            sum(1 for s in subs if s.is_alive())
            for subs in self._subscribers.values()
        )

    # ── dispatch ───────────────────────────────────────────────

    def emit(self, event_name: str, **data: Any) -> None:
        """Queue an event for the next ``dispatch()``."""
        self._queue.append((event_name, data))

    def dispatch(self) -> None:
        """Drain the queue, invoking subscribers.

        Re-entrancy guard: events emitted *by* a subscriber are queued for the
        next frame rather than dispatched recursively, which keeps frame
        ordering predictable and makes infinite emit-loops impossible.
        """
        if self._dispatching:
            return
        self._dispatching = True
        try:
            queue = self._queue[:]
            self._queue.clear()
            for event_name, data in queue:
                subs = self._subscribers.get(event_name)
                if not subs:
                    continue
                dead = False
                for subscription in list(subs):
                    callback = subscription.resolve()
                    if callback is None:
                        # The subscriber was garbage-collected while still
                        # registered. Usually correct (a popped scene that did
                        # not unsubscribe), but it is also the signature of a
                        # throwaway lambda the caller failed to retain, so say
                        # so once rather than silently going quiet.
                        logger.warning(
                            "EventBus: dropping collected subscriber %s for '%s' "
                            "— if this handler was expected to fire, the caller "
                            "must keep a reference to it",
                            subscription.name, event_name,
                        )
                        dead = True
                        continue
                    try:
                        callback(**data)
                    except Exception:
                        logger.exception(
                            "EventBus: callback %s failed for '%s'",
                            subscription.name, event_name,
                        )
                if dead:
                    self._prune(event_name)
        finally:
            self._dispatching = False

    def _prune(self, event_name: str) -> None:
        """Drop subscriptions whose owner has been garbage-collected."""
        subs = self._subscribers.get(event_name)
        if subs is None:
            return
        alive = [s for s in subs if s.is_alive()]
        if alive:
            self._subscribers[event_name] = alive
        else:
            del self._subscribers[event_name]

    def clear(self) -> None:
        """Drop all subscribers and pending events."""
        self._subscribers.clear()
        self._queue.clear()

    # ── introspection (debug overlay / tests) ──────────────────

    @property
    def queue_snapshot(self) -> list[tuple[str, dict[str, object]]]:
        """Read-only snapshot of the pending event queue."""
        return list(self._queue)

    @property
    def subscribers_snapshot(self) -> dict[str, list[str]]:
        """Read-only snapshot mapping event name -> live callback names."""
        return {
            evt: [s.name for s in subs if s.is_alive()]
            for evt, subs in self._subscribers.items()
            if any(s.is_alive() for s in subs)
        }
