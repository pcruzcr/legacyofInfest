"""
Module: events
System: engine.core
Academic Unit: N/A
Description: Centralized declaration of all EventBus event names.
Using string constants instead of raw literals prevents typos and makes
it easy to discover all events in the system.

OBSERVER PATTERN (Fase 5): EventBus is the sole notification mechanism.
These constants are the contract between emitters and subscribers.
"""
from __future__ import annotations


class Events:
    """Canonical event names used across the codebase.
    Every event is defined here — never use raw strings for emit/subscribe."""

    # ── Player lifecycle ──────────────────────────────────────────
    PLAYER_DAMAGED: str = "PLAYER_DAMAGED"
    """Emitted by Player.apply_damage(). Payload: amount, source."""
    PLAYER_HEALED: str = "PLAYER_HEALED"
    """Reserved — not yet emitted. Payload: amount."""
    PLAYER_DIED: str = "PLAYER_DIED"
    """Emitted by Player.apply_damage() or StageScene._kill_player()."""

    # ── Enemy lifecycle ───────────────────────────────────────────
    ENEMY_DIED: str = "ENEMY_DIED"
    """Emitted by EnemyBase._die(). Payload: entity_id, position."""
    BOSS_PHASE_CHANGED: str = "BOSS_PHASE_CHANGED"
    """Emitted by BossBase._finish_phase_transition(). Payload: boss_name, phase, ..."""
    BOSS_ATTACK: str = "BOSS_ATTACK"
    """Emitted by BossVenado._do_stomp(). Payload: pattern, rect."""

    # ── UI / messaging ────────────────────────────────────────────
    SHOW_MESSAGE: str = "SHOW_MESSAGE"
    """Emitted by StageScene on trigger overlap. Payload: text, duration."""
    HIDE_MESSAGE: str = "HIDE_MESSAGE"
    """Emitted by MessageBox.hide(). Payload: none."""

    # ── Stage / progression ───────────────────────────────────────
    CHECKPOINT_REACHED: str = "CHECKPOINT_REACHED"
    """Emitted by Checkpoint.activate(). Payload: checkpoint_id."""
    STAGE_COMPLETE: str = "STAGE_COMPLETE"
    """Emitted by StageScene (next trigger) or BossVenado.on_defeated(). Payload: stage_id."""
