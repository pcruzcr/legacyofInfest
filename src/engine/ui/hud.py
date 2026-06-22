"""
Module: hud
System: engine
Academic Unit: Framework scaffold
Description: Heads-Up Display for the player.  The HUD is drawn in
screen space on top of all stage content.  Heart-rendering logic is
implemented as a pure function (``heart_slot_state``) so that it can
be unit-tested without a ``pygame.Surface``.

Heart threshold algorithm per 09_HUD_SPEC.md §4.3.
"""

from __future__ import annotations

from typing import Any

from src.engine.core import settings
from src.engine.core.event_bus import EventBus


def heart_slot_state(
    current_health: float, slot_index: int
) -> str:
    """Determine the heart sprite name for a single slot.

    Each slot represents one heart (1.0 health).  The slot at *index*
    0 is the leftmost (first full heart).  Returns one of:
    ``"full"``, ``"three_quarter"``, ``"half"``, ``"quarter"``,
    ``"empty"``.

    Args:
        current_health: The player's current health (0.0 to
            ``PLAYER_MAX_HEALTH``).
        slot_index: Zero-based heart slot index (0–4).

    Returns:
        The heart state string for this slot.
    """
    heart_value: float = max(
        0.0, min(1.0, current_health - slot_index)
    )

    if heart_value >= 1.0:
        return "full"
    if heart_value >= 0.75:
        return "three_quarter"
    if heart_value >= 0.50:
        return "half"
    if heart_value >= 0.25:
        return "quarter"
    return "empty"


class HUD:
    """Heads-Up Display.

    Subscribes to ``PLAYER_DAMAGED``, ``PLAYER_HEALED``, and
    ``PLAYER_DIED`` via ``EventBus``.
    """

    def __init__(self) -> None:
        """Subscribe to player-state events."""
        self._health: float = settings.PLAYER_MAX_HEALTH
        self._portrait_state: str = "NORMAL"
        self._hurt_timer: float = 0.0

        EventBus.subscribe(
            "PLAYER_DAMAGED", self._on_player_damaged
        )
        EventBus.subscribe(
            "PLAYER_HEALED", self._on_player_healed
        )
        EventBus.subscribe(
            "PLAYER_DIED", self._on_player_died
        )

    def _on_player_damaged(self, **data: Any) -> None:
        """Handle ``PLAYER_DAMAGED`` event."""
        amount: float = data.get("amount", 0.0)
        self._health = max(0.0, self._health - amount)
        self._hurt_timer = 0.8

    def _on_player_healed(self, **data: Any) -> None:
        """Handle ``PLAYER_HEALED`` event."""
        amount: float = data.get("amount", 0.0)
        self._health = min(
            settings.PLAYER_MAX_HEALTH, self._health + amount
        )

    def _on_player_died(self, **data: Any) -> None:
        """Handle ``PLAYER_DIED`` event."""
        self._health = 0.0

    def update(self, dt: float) -> None:
        """Update per-frame state (e.g. hurt timer decay)."""
        if self._hurt_timer > 0:
            self._hurt_timer -= dt

        if self._health <= 0.0:
            self._portrait_state = "DEAD"
        elif self._health <= 1.0:
            self._portrait_state = "CRITICAL"
        elif self._hurt_timer > 0:
            self._portrait_state = "HURT"
        else:
            self._portrait_state = "NORMAL"

    def draw(self, surface: object) -> None:
        """Render HUD elements onto *surface* (placeholder)."""

    def start_timer(self, seconds: int) -> None:
        """Start the HUD timer (placeholder)."""

    def pause_timer(self) -> None:
        """Pause the HUD timer (placeholder)."""

    def resume_timer(self) -> None:
        """Resume the HUD timer (placeholder)."""

    def bind_player(self, player: object) -> None:
        """Store a reference to the player for portrait state (placeholder)."""
