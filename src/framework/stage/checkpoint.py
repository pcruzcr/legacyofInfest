"""
Module: checkpoint
System: framework/stage
Academic Unit: Stage system
Description: Checkpoint entity that activates once when the player
overlaps its trigger rect. On activation it emits CHECKPOINT_REACHED
via the EventBus and marks itself as consumed.
Implements the contract from 22_API_CONTRACTS.md §11.2 and
06_TMX_SPEC.md §7.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from src.engine.core.event_bus import EventBus
from src.framework.entities.base_entity import BaseEntity

if TYPE_CHECKING:
    pass


class Checkpoint(BaseEntity):
    """A checkpoint that activates once on player overlap.

    Usage::

        cp = Checkpoint(
            position=pygame.Vector2(1080, 160),
            rect=pygame.Rect(1080, 160, 24, 32),
            checkpoint_id=0,
        )
        # Each frame while the stage is active:
        cp.update(dt)
        cp.draw(surface, camera_offset)
    """

    def __init__(
        self,
        position: pygame.Vector2,
        rect: pygame.Rect,
        checkpoint_id: int,
    ) -> None:
        """Create a checkpoint.

        Args:
            position: World-space centre-bottom of the checkpoint.
            rect: Trigger rect in world-space.
            checkpoint_id: Unique integer id (0-based, ascending).
        """
        # Set BaseEntity attributes directly (bypass super().__init__
        # to avoid BaseEntity setting self.is_active, which conflicts
        # with the read-only Checkpoint.is_active property below).
        self.position: pygame.Vector2 = position
        self.is_visible: bool = True
        self.layer: int = 4
        self._trigger_rect: pygame.Rect = rect
        self._checkpoint_id: int = checkpoint_id
        self._activated: bool = False
        self._sprite_glow: bool = False

    # ── Public API ────────────────────────────────────────────────

    def update(self, dt: float) -> None:
        """Check player overlap and activate once.

        If the checkpoint has not yet been activated and the player's
        rect overlaps the trigger rect, emits ``CHECKPOINT_REACHED``
        and marks the checkpoint as consumed.

        Args:
            dt: Delta time in seconds (unused, but part of the
                entity contract).
        """
        if self._activated:
            return

        # We need a player reference to check overlap.
        # The stage code must call _try_activate(player) instead, or
        # we receive the player via the stage's update loop.
        # For now we defer the overlap check to the stage code that
        # has access to both the player and checkpoint list.
        # This is intentional: Checkpoint does NOT hold a player
        # reference to respect entity isolation (02_CODEX_CONTEXT.md §7.3).
        pass

    def try_activate(self, player_rect: pygame.Rect) -> bool:
        """Check if *player_rect* overlaps and activate if not already.

        This is the intended call-point from stage code::

            for cp in stage_data.checkpoints:
                cp.try_activate(player.rect)

        Args:
            player_rect: The player's current world-space rect.

        Returns:
            ``True`` if the checkpoint was activated this call,
            ``False`` if already activated or no overlap.
        """
        if self._activated:
            return False

        if not self._trigger_rect.colliderect(player_rect):
            return False

        # Activate
        self._activated = True
        self._sprite_glow = True
        EventBus.emit("CHECKPOINT_REACHED", checkpoint_id=self._checkpoint_id)
        return True

    def draw(
        self, surface: pygame.Surface, camera_offset: pygame.Vector2
    ) -> None:
        """Render the checkpoint marker.

        When inactive, draws a simple grey post silhouette.  When
        active, draws a brighter animated marker.

        Args:
            surface: The internal 320×224 render target.
            camera_offset: Current camera world-space offset.
        """
        if not self.is_visible:
            return

        # Screen-space position of the trigger rect
        screen_rect: pygame.Rect = self._trigger_rect.move(
            -camera_offset.x,
            -camera_offset.y,
        )

        if self._activated:
            # Active: bright green glow
            alpha = 128 + int(127 * (pygame.time.get_ticks() % 800) / 800)
            color = (0, 255, min(alpha, 255))
            pygame.draw.rect(surface, color, screen_rect, width=2)
            # Extra glow triangle on top
            cx = screen_rect.centerx
            top_y = screen_rect.top - 4
            pygame.draw.polygon(
                surface,
                (255, 255, 200),
                [(cx, top_y), (cx - 4, top_y + 6), (cx + 4, top_y + 6)],
            )
        else:
            # Inactive: dim grey outline
            pygame.draw.rect(surface, (80, 80, 80), screen_rect, width=1)

    # ── Properties ────────────────────────────────────────────────

    @property
    def is_active(self) -> bool:
        """``True`` if this checkpoint has been activated."""
        return self._activated

    @property
    def checkpoint_id(self) -> int:
        """Unique identifier for this checkpoint."""
        return self._checkpoint_id

    @property
    def trigger_rect(self) -> pygame.Rect:
        """World-space trigger rect (read-only)."""
        return self._trigger_rect.copy()
