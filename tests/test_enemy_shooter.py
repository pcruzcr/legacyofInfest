"""Tests for EnemyShooter projectile system."""

import pytest

import pygame

from src.framework.entities.enemy_shooter import EnemyShooter, Projectile
from src.framework.entities.enemy_base import EnemyState


@pytest.fixture
def shooter():
    return EnemyShooter(
        pygame.Vector2(100.0, 100.0),
        fire_rate=0.5,
        projectile_speed=120.0,
        projectile_damage=0.5,
    )


def test_initial_state(shooter):
    assert shooter.state == EnemyState.PATROL


def test_projectiles_empty_initially(shooter):
    assert len(shooter.projectiles) == 0


def test_fire_creates_projectile(shooter):
    shooter.set_target(pygame.Vector2(200.0, 100.0))
    shooter._fire()
    assert len(shooter.projectiles) == 1


def test_fire_max_three_projectiles(shooter):
    shooter.set_target(pygame.Vector2(200.0, 100.0))
    for _ in range(5):
        shooter._fire()
    assert len(shooter.projectiles) <= 3


def test_projectile_moves(shooter):
    shooter.set_target(pygame.Vector2(200.0, 100.0))
    shooter._fire()
    proj = shooter.projectiles[0]
    x0 = proj.position.x
    proj.update(0.1)
    assert proj.position.x != x0


def test_projectile_expires(shooter):
    proj = Projectile(
        spawn_position=pygame.Vector2(100.0, 100.0),
        velocity=pygame.Vector2(120.0, 0.0),
        damage=0.5,
        lifetime=0.1,
    )
    proj.update(0.2)
    assert not proj.is_active


def test_hurtbox_matches_spec(shooter):
    hurtbox = shooter._build_hurtbox()
    assert hurtbox.width == 24
    assert hurtbox.height == 30


def test_apply_hit(shooter):
    shooter.apply_hit(0.5, (0.0, 100.0))
    assert shooter.state == EnemyState.HURT


def test_apply_hit_kills(shooter):
    shooter.apply_hit(4.0, (0.0, 100.0))
    assert shooter.state == EnemyState.DYING


def test_die_expires_projectiles(shooter):
    shooter.set_target(pygame.Vector2(200.0, 100.0))
    shooter._fire()
    assert len(shooter.projectiles) == 1
    shooter._die()
    assert len(shooter.projectiles) == 0
