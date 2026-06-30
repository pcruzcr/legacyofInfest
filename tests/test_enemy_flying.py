"""
Module: test_enemy_flying
System: tests
Academic Unit: N/A
Description: Tests for EnemyFlying sine movement, alert acceleration,
and deferred modes (Bézier/patrol).
"""
import pytest

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


class TestFlyingDeferredModes:
    """Tests for modes deferred to Phase 8."""

    def test_bezier_raises_not_implemented(self) -> None:
        e = EnemyFlying(
            pygame.Vector2(0.0, 0.0), flight_mode="bezier"
        )
        with pytest.raises(NotImplementedError):
            e._patrol_behavior(1.0 / 60.0)

    def test_patrol_raises_not_implemented(self) -> None:
        e = EnemyFlying(
            pygame.Vector2(0.0, 0.0), flight_mode="patrol"
        )
        with pytest.raises(NotImplementedError):
            e._patrol_behavior(1.0 / 60.0)