"""Tests for EnemyFlying sine flight mode."""

import pytest

import pygame

from src.framework.entities.enemy_flying import EnemyFlying
from src.framework.entities.enemy_base import EnemyState


@pytest.fixture
def flyer():
    return EnemyFlying(
        pygame.Vector2(100.0, 100.0),
        flight_mode="sine",
        flight_speed=60.0,
        sine_amplitude=28.0,
        sine_frequency=1.5,
    )


def test_initial_state(flyer):
    assert flyer.state == EnemyState.PATROL


def test_sine_patrol_moves(flyer):
    x0 = flyer.position.x
    flyer._patrol_behavior(0.1)
    assert flyer.position.x != x0


def test_sine_vertical_oscillation(flyer):
    y0 = flyer.position.y
    flyer._patrol_behavior(0.5)
    assert flyer.position.y != y0


def test_alert_increases_speed(flyer):
    flyer._patrol_behavior(0.1)
    x_after_patrol = flyer.position.x
    flyer2 = EnemyFlying(
        pygame.Vector2(100.0, 100.0),
        flight_mode="sine",
        flight_speed=60.0,
    )
    flyer2._alert_behavior(0.1)
    x_after_alert = flyer2.position.x
    assert abs(x_after_alert - 100.0) > abs(x_after_patrol - 100.0)


def test_hurtbox_matches_spec(flyer):
    hurtbox = flyer._build_hurtbox()
    assert hurtbox.width == 20
    assert hurtbox.height == 20


def test_apply_hit(flyer):
    flyer.apply_hit(0.5, (0.0, 100.0))
    assert flyer.state == EnemyState.HURT


def test_apply_hit_kills(flyer):
    flyer.apply_hit(2.0, (0.0, 100.0))
    assert flyer.state == EnemyState.DYING


def test_bezier_fallback_to_sine():
    flyer = EnemyFlying(
        pygame.Vector2(100.0, 100.0),
        flight_mode="bezier",
    )
    flyer._patrol_behavior(0.1)
    assert flyer.position.x != 100.0


def test_patrol_fallback_to_sine():
    flyer = EnemyFlying(
        pygame.Vector2(100.0, 100.0),
        flight_mode="patrol",
    )
    flyer._patrol_behavior(0.1)
    assert flyer.position.x != 100.0
