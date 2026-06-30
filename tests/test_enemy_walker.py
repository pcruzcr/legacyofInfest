"""
Module: test_enemy_walker
System: tests
Academic Unit: N/A
Description: Tests for EnemyWalker patrol reversal and ledge detection.
"""
import pygame

from src.framework.entities.enemy_walker import EnemyWalker


class TestWalkerPatrolReversal:
    """Tests for patrol limit reversal."""

    def test_reverses_after_patrol_half_length(self) -> None:
        w = EnemyWalker(pygame.Vector2(100.0, 0.0), patrol_length=96.0)
        w.facing_direction = 1
        # Simulate update at origin (distance 0)
        w.update(1.0 / 60.0)
        initial_dir = w.facing_direction
        # Move to patrol_length / 2
        w.position.x = w._patrol_origin.x + 48.0
        w.update(1.0 / 60.0)
        assert w.facing_direction == -initial_dir, (
            "Should reverse direction at patrol limit"
        )

    def test_starts_right_facing(self) -> None:
        w = EnemyWalker(
            pygame.Vector2(0.0, 0.0), facing="right"
        )
        assert w.facing_direction == 1

    def test_starts_left_facing(self) -> None:
        w = EnemyWalker(
            pygame.Vector2(0.0, 0.0), facing="left"
        )
        assert w.facing_direction == -1


class TestWalkerLedgeDetection:
    """Tests for ledge behavior."""

    def test_no_collision_rects_no_fall(self) -> None:
        w = EnemyWalker(pygame.Vector2(100.0, 0.0))
        w._collision_rects = []
        # Should not crash with no collision rects
        w.update(1.0 / 60.0)

    def test_reverses_on_ledge(self) -> None:
        w = EnemyWalker(
            pygame.Vector2(100.0, 100.0), facing="right"
        )
        # Capture initial direction before any update
        initial_dir = w.facing_direction
        # Floor rect that does NOT extend to the probe point
        w._collision_rects = [pygame.Rect(0, 200, 50, 32)]
        w.update(1.0 / 60.0)
        # Probe at (114, 132) misses the rect → reverses
        assert w.facing_direction == -initial_dir
