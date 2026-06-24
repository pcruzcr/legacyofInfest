"""
Tests for Checkpoint (T7.2).
"""

from __future__ import annotations

import pygame

from src.framework.stage.checkpoint import Checkpoint


# ── Helpers ──────────────────────────────────────────────────────────────


class _StubPlayerRect:
    """Stand-in for a player collision rect."""

    def __init__(self, x: int, y: int, w: int = 16, h: int = 32) -> None:
        self._rect = pygame.Rect(x, y, w, h)

    def colliderect(self, other: pygame.Rect) -> bool:
        return self._rect.colliderect(other)


# ── Tests ────────────────────────────────────────────────────────────────


class TestCheckpoint:
    """Checkpoint smoke tests per 24_TEST_PLAN.md §9.3."""

    def test_activates_once_on_player_overlap(self) -> None:
        """First overlap activates; is_active becomes True."""
        cp = Checkpoint(
            position=pygame.Vector2(100, 50),
            rect=pygame.Rect(100, 50, 24, 32),
            checkpoint_id=0,
        )
        player_rect = pygame.Rect(110, 50, 16, 32)

        assert cp.is_active is False
        result = cp.try_activate(player_rect)

        assert result is True
        assert cp.is_active is True

    def test_does_not_reactivate_on_repeat_overlap(self) -> None:
        """Repeat overlap emits nothing; is_active stays True."""
        cp = Checkpoint(
            position=pygame.Vector2(100, 50),
            rect=pygame.Rect(100, 50, 24, 32),
            checkpoint_id=0,
        )
        player_rect = pygame.Rect(110, 50, 16, 32)

        cp.try_activate(player_rect)
        result = cp.try_activate(player_rect)

        assert result is False
        assert cp.is_active is True

    def test_no_activate_without_overlap(self) -> None:
        """Player rect that does not overlap does not activate."""
        cp = Checkpoint(
            position=pygame.Vector2(100, 50),
            rect=pygame.Rect(100, 50, 24, 32),
            checkpoint_id=0,
        )
        player_rect = pygame.Rect(500, 50, 16, 32)
        result = cp.try_activate(player_rect)
        assert result is False
        assert cp.is_active is False
