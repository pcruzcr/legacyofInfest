"""
Module: test_enemy_flying
System: tests
Description: Tests for EnemyFlying sine movement, alert acceleration,
and path modes (Bézier / waypoint patrol).
"""
from __future__ import annotations
import math
import pygame
from src.framework.entities.enemy_flying import EnemyFlying
from src.framework.entities.enemy_base import EnemyState


class TestFlyingSineMovement:
    def test_sine_oscillates_vertically(self) -> None:
        e = EnemyFlying(
            pygame.Vector2(100.0, 100.0),
            sine_amplitude=40.0,
            sine_frequency=1.0,
        )
        e._t = 0.25
        e._patrol_behavior(0.0)
        expected_y = 100.0 + 40.0 * 1.0
        assert abs(e.position.y - expected_y) < 0.1

    def test_sine_reverses_at_boundary(self) -> None:
        e = EnemyFlying(pygame.Vector2(100.0, 100.0))
        e.facing_direction = 1
        e.update(1.0 / 60.0)
        e.position.x = e._origin.x + 100.0
        e.update(1.0 / 60.0)
        assert e.facing_direction == -1

    def test_alert_increases_speed(self) -> None:
        e = EnemyFlying(
            pygame.Vector2(100.0, 100.0),
            flight_speed=60.0,
            sine_amplitude=10.0,
            sine_frequency=0.5,
        )
        e.state = EnemyState.ALERT
        dt = 1.0 / 60.0
        x_before = e.position.x
        e._patrol_behavior(dt)
        patrol_dx = abs(e.position.x - x_before)
        e.position.x = 100.0
        x_before = e.position.x
        e._alert_behavior(dt)
        alert_dx = abs(e.position.x - x_before)
        assert alert_dx > patrol_dx


class TestFlyingBezierMode:
    def test_bezier_moves_along_path(self) -> None:
        waypoints = [(0.0, 0.0), (64.0, -48.0), (128.0, 0.0)]
        e = EnemyFlying(
            pygame.Vector2(0.0, 0.0),
            flight_mode="bezier",
            waypoints=waypoints,
        )
        x_before = e.position.x
        for _ in range(60):
            e._patrol_behavior(1.0 / 60.0)
        assert e.position.x != x_before
        assert e._path_progress > 0.0

    def test_bezier_loops_at_end(self) -> None:
        waypoints = [(0.0, 0.0), (32.0, -24.0), (64.0, 0.0)]
        e = EnemyFlying(
            pygame.Vector2(0.0, 0.0),
            flight_mode="bezier",
            waypoints=waypoints,
        )
        for _ in range(300):
            e._patrol_behavior(1.0 / 60.0)
        assert 0.0 <= e._path_progress <= 1.0
        assert not math.isnan(e.position.x)
        assert not math.isnan(e.position.y)

    def test_bezier_default_waypoints(self) -> None:
        e = EnemyFlying(
            pygame.Vector2(100.0, 100.0),
            flight_mode="bezier",
        )
        e._patrol_behavior(1.0 / 60.0)
        assert not math.isnan(e.position.x)
        assert not math.isnan(e.position.y)


class TestFlyingPatrolMode:
    def test_patrol_moves_toward_first_waypoint(self) -> None:
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
        for _ in range(200):
            e._patrol_behavior(1.0 / 60.0)
        assert e._waypoint_index == 0 or e._waypoint_index == 1

    def test_patrol_faces_target_direction(self) -> None:
        waypoints = [(100.0, 0.0), (0.0, 0.0)]
        e = EnemyFlying(
            pygame.Vector2(100.0, 0.0),
            flight_mode="patrol",
            waypoints=waypoints,
        )
        e._patrol_behavior(1.0 / 60.0)
        assert e.facing_direction == -1


class TestFlyingDamage:
    def test_apply_hit_reduces_health(self) -> None:
        e = EnemyFlying(pygame.Vector2(0.0, 0.0), max_health=1.5)
        e.apply_hit(1.0, (0.0, 0.0))
        assert abs(e.current_health - 0.5) < 0.01

    def test_death_on_zero_health(self) -> None:
        e = EnemyFlying(pygame.Vector2(0.0, 0.0), max_health=1.0)
        e.apply_hit(1.0, (0.0, 0.0))
        assert e.state == EnemyState.DYING
        assert e.is_alive is True  # alive during death animation
        # After death timer expires, is_alive becomes False
        e._tick_cooldowns(0.6)
        assert e.is_alive is False
