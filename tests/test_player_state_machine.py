"""Tests for Player state machine transitions (T5.3)."""

import pytest

from src.framework.entities.player import Player
from src.framework.entities.player_state import PlayerState


@pytest.fixture
def player():
    return Player(100.0, 100.0)


def test_initial_state_idle(player):
    """Player spawns in IDLE state."""
    assert player.state == PlayerState.IDLE


def test_idle_to_walk_when_direction_set(player):
    """Providing direction while grounded transitions to WALKING."""
    player._direction = 1
    player.is_grounded = True
    player.update(0.1)
    assert player.state == PlayerState.WALKING


def test_walk_to_idle_when_no_direction(player):
    """Clearing direction while grounded returns to IDLE."""
    player._direction = 1
    player.is_grounded = True
    player.state = PlayerState.WALKING
    player._direction = 0
    player.update(0.1)
    assert player.state == PlayerState.IDLE


def test_idle_to_jump_on_start_jump(player):
    """start_jump() from IDLE transitions to JUMPING immediately."""
    player.is_grounded = True
    player.start_jump()
    assert player.state == PlayerState.JUMPING


def test_jump_to_fall_when_peak_velocity(player):
    """JUMPING transitions to FALLING when velocity.y turns positive."""
    player.state = PlayerState.JUMPING
    player.vel.y = 1.0
    player.update(0.1)
    assert player.state == PlayerState.FALLING


def test_fall_to_idle_on_land(player):
    """FALLING transitions to IDLE when grounded."""
    player.state = PlayerState.FALLING
    player.is_grounded = True
    player.update(0.1)
    assert player.state == PlayerState.IDLE


def test_idle_to_crouch_on_crouch_input(player):
    """set_crouch(True) while grounded transitions to CROUCHING."""
    player.is_grounded = True
    player.set_crouch(True)
    player.update(0.1)
    assert player.state == PlayerState.CROUCHING


def test_crouch_to_short_attack(player):
    """Short attack input while CROUCHING transitions to SHORT_ATTACK."""
    player.state = PlayerState.CROUCHING
    player._crouching = True
    player._attack_input = "short"
    player.update(0.1)
    assert player.state == PlayerState.SHORT_ATTACK


def test_any_to_hurt_on_damage(player):
    """take_damage() transitions to HURT from any non-DYING state."""
    player.state = PlayerState.IDLE
    player._invincibility_timer = 0.0
    player.take_damage(0.5, source=(0.0, player.pos.y))
    assert player.state == PlayerState.HURT


def test_hurt_to_idle_after_knockback(player):
    """HURT returns to IDLE once invincibility expires."""
    player.state = PlayerState.HURT
    player._invincibility_timer = 0.1
    player.update(0.2)
    assert player.state == PlayerState.IDLE


def test_dying_when_health_zero(player):
    """Health reaching 0 transitions to DYING."""
    player.state = PlayerState.IDLE
    player._invincibility_timer = 0.0
    player._health = 0.5
    player.take_damage(0.5, source=(0.0, player.pos.y))
    assert player.state == PlayerState.DYING
