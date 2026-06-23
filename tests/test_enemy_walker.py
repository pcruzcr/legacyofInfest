"""Tests for EnemyWalker patrol and ledge detection."""

import pytest

import pygame

from src.framework.entities.enemy_walker import EnemyWalker
from src.framework.entities.enemy_base import EnemyState


@pytest.fixture
def walker():
    return EnemyWalker(
        pygame.Vector2(100.0, 200.0),
        patrol_length=96.0,
        facing="right",
    )


def test_initial_state(walker):
    assert walker.state == EnemyState.PATROL


def test_patrol_movement(walker):
    x0 = walker.position.x
    walker._patrol_behavior(0.1)
    assert walker.position.x > x0


def test_patrol_reverses_at_limit(walker):
    walker.position.x = 148.0  # near patrol limit
    walker._patrol_behavior(1.0)
    assert walker.facing_direction == -1


def test_alert_behavior(walker):
    walker.set_target_x(0.0)
    walker._alert_behavior(0.1)
    assert walker.facing_direction == -1


def test_hurtbox_matches_spec(walker):
    hurtbox = walker._build_hurtbox()
    assert hurtbox.width == 24
    assert hurtbox.height == 28
    assert hurtbox.x == 4
    assert hurtbox.y == 2


def test_apply_hit(walker):
    walker.apply_hit(0.5, (0.0, 100.0))
    assert walker.state == EnemyState.HURT


def test_apply_hit_kills(walker):
    walker.apply_hit(2.0, (0.0, 100.0))
    assert walker.state == EnemyState.DYING
