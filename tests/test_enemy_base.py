"""Tests for EnemyBase abstract class and EnemyState."""

import pytest

import pygame

from src.framework.entities.enemy_base import EnemyBase, EnemyState


class ConcreteEnemy(EnemyBase):
    """Minimal implementation for testing EnemyBase."""

    def __init__(self, position):
        super().__init__(position, max_health=2.0)
        self.patrol_called = False
        self.alert_called = False

    def _patrol_behavior(self, dt: float) -> None:
        self.patrol_called = True

    def _alert_behavior(self, dt: float) -> None:
        self.alert_called = True

    def _get_animation_state(self) -> str:
        return "idle"

    def _build_hitbox(self) -> pygame.Rect:
        return pygame.Rect(0, 0, 16, 16)

    def _build_hurtbox(self) -> pygame.Rect:
        return pygame.Rect(0, 0, 16, 16)


@pytest.fixture
def enemy():
    return ConcreteEnemy(pygame.Vector2(100.0, 100.0))


def test_initial_state_is_patrol(enemy):
    assert enemy.state == EnemyState.PATROL


def test_apply_hit_sets_hurt(enemy):
    enemy.apply_hit(0.5, (0.0, 100.0))
    assert enemy.state == EnemyState.HURT
    assert enemy.current_health == 1.5


def test_apply_hit_ignores_during_invincibility(enemy):
    enemy.apply_hit(0.5, (0.0, 100.0))
    first_health = enemy.current_health
    enemy.apply_hit(0.5, (0.0, 100.0))
    assert enemy.current_health == first_health


def test_apply_hit_kills(enemy):
    enemy.apply_hit(2.0, (0.0, 100.0))
    assert enemy.state == EnemyState.DYING
    assert enemy.current_health == 0.0
    assert enemy.is_alive is True
    # After death timer expires, _die() sets is_alive=False
    enemy._death_timer = 0.01
    enemy.update(0.016)
    assert enemy.is_alive is False


def test_patrol_behavior_called(enemy):
    enemy.update(0.016)
    assert enemy.patrol_called is True


def test_hurt_transitions_back_to_patrol(enemy):
    enemy.apply_hit(0.5, (0.0, 100.0))
    assert enemy.state == EnemyState.HURT
    # Simulate time passing
    enemy._hurt_timer = 0.01
    enemy.update(0.016)
    assert enemy.state == EnemyState.PATROL


def test_contact_cooldown_prevents_repeated_damage(enemy):
    enemy._contact_cooldown = 0.3
    enemy.patrol_called = False
    enemy.update(0.016)
    # Should not call patrol again because cooldown active
    assert enemy.state == EnemyState.PATROL
