"""
Module: test_enemy_flying
System: tests
Academic Unit: N/A
Description: Tests for EnemyFlying sine movement, alert acceleration,
and path modes (Bézier / waypoint patrol).
"""
import math

import pygame

from src.framework.entities.enemy_flying import EnemyFlying


class TestFlyingSineMovement:
    """Tests for sine-wave patrol."""

    def test_sine_oscillates_vertically(self) -> None:
        e = EnemyFlying(
            pygame.Vector2(100.0, 100.0),
            sine_amplitude=40.0,
            sine_frequency=1.0,
        )
        # directly test the math: sine should produce oscillating y
        e._t = 0.25  # quarter period
        e._sine_patrol(0.0)  # no dt increment, just apply current t
        # sin(2*pi*1.0*0.25) = sin(pi/2) = 1.0
        expected_y = 100.0 + 40.0 * 1.0
        assert abs(e.position.y - expected_y) < 0.1, (
            f"Expected y≈{expected_y}, got {e.position.y}"
        )

    def test_sine_reverses_at_boundary(self) -> None:
        e = EnemyFlying(pygame.Vector2(100.0, 100.0))
        e.facing_direction = 1
        e.update(1.0 / 60.0)
        # Simulate reaching boundary
        e.position.x = e._origin.x + 100.0
        e.update(1.0 / 60.0)
        assert e.facing_direction == -1, "Should reverse at boundary"

    def test_alert_increases_speed(self) -> None:
        e = EnemyFlying(
            pygame.Vector2(100.0, 100.0),
            flight_speed=60.0,
            sine_amplitude=10.0,
            sine_frequency=0.5,
        )
        e.state = type(e.state).ALERT  # force ALERT
        dt = 1.0 / 60.0
        x_before = e.position.x
        e._alert_behavior(dt)
        x_after = e.position.x
        # Should have moved
        assert abs(x_after - x_before) > 0.0


class TestFlyingBezierMode:
    """Tests for Bézier spline path mode."""

    def test_bezier_moves_along_path(self) -> None:
        waypoints = [(0.0, 0.0), (64.0, -48.0), (128.0, 0.0)]
        e = EnemyFlying(
            pygame.Vector2(0.0, 0.0),
            flight_mode="bezier",
            waypoints=waypoints,
        )
        x_before = e.position.x
        # Advance along the path
        for _ in range(60):
            e._patrol_behavior(1.0 / 60.0)
        # Should have moved, and progress should have advanced
        assert e.position.x != x_before, (
            f"Expected x to change, got {e.position.x}"
        )
        assert e._path_progress > 0.0

    def test_bezier_loops_at_end(self) -> None:
        waypoints = [(0.0, 0.0), (32.0, -24.0), (64.0, 0.0)]
        e = EnemyFlying(
            pygame.Vector2(0.0, 0.0),
            flight_mode="bezier",
            waypoints=waypoints,
        )
        # Run many frames to wrap around
        for _ in range(300):
            e._patrol_behavior(1.0 / 60.0)
        # Should still be in valid range
        assert 0.0 <= e._path_progress <= 1.0
        assert not math.isnan(e.position.x)
        assert not math.isnan(e.position.y)

    def test_bezier_default_waypoints(self) -> None:
        """Without explicit waypoints, bezier mode uses a diamond path."""
        e = EnemyFlying(
            pygame.Vector2(100.0, 100.0),
            flight_mode="bezier",
        )
        e._patrol_behavior(1.0 / 60.0)
        assert not math.isnan(e.position.x)
        assert not math.isnan(e.position.y)


class TestFlyingPatrolMode:
    """Tests for linear waypoint patrol mode."""

    def test_patrol_moves_toward_first_waypoint(self) -> None:
        """Spawn at origin, target at (100,0) — moves right."""
        waypoints = [(100.0, 0.0), (200.0, 0.0)]
        e = EnemyFlying(
            pygame.Vector2(0.0, 0.0),
            flight_mode="patrol",
            waypoints=waypoints,
        )
        e._patrol_behavior(1.0 / 60.0)
        assert e.position.x > 0.0
        assert e.facing_direction == 1

    def test_patrol_loops_through_waypoints(self) -> None:
        waypoints = [(0.0, 0.0), (100.0, 0.0), (100.0, 100.0)]
        e = EnemyFlying(
            pygame.Vector2(0.0, 0.0),
            flight_mode="patrol",
            waypoints=waypoints,
            flight_speed=200.0,
        )
        # Run enough frames to reach all waypoints and loop
        for _ in range(200):
            e._patrol_behavior(1.0 / 60.0)
        # Should have wrapped waypoint_index back to 0
        assert e._waypoint_index == 0 or e._waypoint_index == 1

    def test_patrol_faces_target_direction(self) -> None:
        waypoints = [(100.0, 0.0), (0.0, 0.0)]
        e = EnemyFlying(
            pygame.Vector2(100.0, 0.0),
            flight_mode="patrol",
            waypoints=waypoints,
        )
        e._patrol_behavior(1.0 / 60.0)
        # Should move left toward (0, 0)
        assert e.facing_direction == -1
