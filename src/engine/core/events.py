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

    # ── SFX events (emitted by entities, played by StageScene) ────
    SFX_PLAYER_JUMP: str = "SFX_PLAYER_JUMP"
    SFX_PLAYER_LAND: str = "SFX_PLAYER_LAND"
    SFX_PLAYER_FOOTSTEP: str = "SFX_PLAYER_FOOTSTEP"
    SFX_MENU_HOVER: str = "SFX_MENU_HOVER"
    SFX_MENU_CONFIRM: str = "SFX_MENU_CONFIRM"
    SFX_MENU_CANCEL: str = "SFX_MENU_CANCEL"
    MUSIC_STINGER: str = "MUSIC_STINGER"

    # ── VFX events (emitted by entities, consumed by StageScene) ─
    VFX_PARRY: str = "VFX_PARRY"
    """Emitted by ParryState. Payload: pos."""
    VFX_CHARGE: str = "VFX_CHARGE"
    """Emitted by ChargingState. Payload: pos, level."""
    VFX_SLAM: str = "VFX_SLAM"
    """Emitted on slam attack. Payload: pos."""
    VFX_ULTIMATE: str = "VFX_ULTIMATE"
    """Emitted on ultimate attack. Payload: pos."""
    SFX_PLAYER_SHORT_ATTACK: str = "SFX_PLAYER_SHORT_ATTACK"
    SFX_PLAYER_LONG_ATTACK: str = "SFX_PLAYER_LONG_ATTACK"
    SFX_PLAYER_HURT: str = "SFX_PLAYER_HURT"
    SFX_PLAYER_DIE: str = "SFX_PLAYER_DIE"
    SFX_HIT_CONNECT: str = "SFX_HIT_CONNECT"
    SFX_ENEMY_HIT: str = "SFX_ENEMY_HIT"
    SFX_ENEMY_DIE_SMALL: str = "SFX_ENEMY_DIE_SMALL"
    SFX_ENEMY_DIE_LARGE: str = "SFX_ENEMY_DIE_LARGE"
    SFX_PROJECTILE_FIRE: str = "SFX_PROJECTILE_FIRE"
    SFX_CHECKPOINT: str = "SFX_CHECKPOINT"
    SFX_STAGE_BANNER: str = "SFX_STAGE_BANNER"
    SFX_STAGE_COMPLETE: str = "SFX_STAGE_COMPLETE"
    SFX_HAZARD_ZONE: str = "SFX_HAZARD_ZONE"

    # ── Achievement events ─────────────────────────────────────────
    ACHIEVEMENT_UNLOCKED: str = "ACHIEVEMENT_UNLOCKED"
    """Emitted when an achievement is unlocked. Payload: achievement_id, name."""
    ACHIEVEMENT_PROGRESS: str = "ACHIEVEMENT_PROGRESS"
    """Emitted on progress toward achievement. Payload: achievement_id, progress, target."""
