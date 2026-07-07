"""
Module: boss_template
Academic Unit: Final Project — Boss Battle
Description: Template for custom boss battles. Students extend BossBase
and implement the placeholder methods below.
"""
from __future__ import annotations

import pygame

from src.framework.entities.boss_base import BossBase


class CustomBoss(BossBase):
    """A custom boss enemy with configurable behaviour.

    TODO:
    1. Define attack patterns in _build_attack_sequence().
    2. Override update() to implement phase transitions.
    3. Override draw() to add custom visual effects.
    4. Override on_defeated() for loot / cutscene triggers.
    """

    def __init__(self, pos: pygame.Vector2, **kwargs) -> None:
        super().__init__(pos, **kwargs)
        self._phase: int = 1
        self._attack_cooldown: float = 0.0

    def _build_attack_sequence(self) -> list[dict]:
        """Define the boss's attack pattern.

        Each entry: {"type": str, "damage": int, "cooldown": float, ...}
        """
        return [
            {"type": "projectile", "damage": 10, "cooldown": 2.0, "speed": 200},
            {"type": "melee", "damage": 15, "cooldown": 1.5, "range": 48},
        ]

    def update(self, dt: float) -> None:
        """Called every frame with the delta time in seconds."""
        super().update(dt)

    def draw(self, surface: pygame.Surface, offset: pygame.Vector2) -> None:
        """Render the boss and any custom effects."""
        super().draw(surface, offset)

    def on_defeated(self) -> None:
        """Called when the boss's health reaches zero."""

    # ── Exercise: EventBus queue_snapshot ─────────────────────────────────
    #
    # Goal: Monitor attack events via EventBus.queue_snapshot to react to
    # incoming projectiles before they are dispatched.
    #
    # Starter code — uncomment and implement:
    #
    # def _detect_incoming_attacks(self) -> list[dict]:
    #     from src.engine.core.event_bus import _get_bus
    #     bus = _get_bus()
    #     attacks = []
    #     for event_name, data in bus.queue_snapshot:
    #         if event_name == "boss_attack":
    #             attacks.append(data)
    #     return attacks
    #
    # Challenge: Use the detected attacks to trigger a dodge or shield
    # animation. Call _detect_incoming_attacks() at the start of update().
