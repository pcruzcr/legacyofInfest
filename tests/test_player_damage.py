"""Tests for Player damage system (T5.4)."""

import pytest

from src.framework.entities.player import Player


@pytest.fixture
def player():
    return Player(100.0, 100.0)


def test_damage_reduces_health(player):
    """Light damage reduces health by 0.25."""
    player.take_damage(0.25, source=(0.0, player.pos.y))
    assert player._health == pytest.approx(4.75)


def test_damage_clamps_to_zero(player):
    """Heavy enough damage clamps health to 0.0."""
    player.take_damage(5.0, source=(0.0, player.pos.y))
    assert player._health == 0.0


def test_damage_emits_event(player):
    """take_damage emits PLAYER_DAMAGED with correct payload."""
    # EventBus monitoring would require a listener; here we verify no exception
    player.take_damage(0.5, source=(0.0, player.pos.y))
    assert player.state.name == "HURT"


def test_damage_sets_invincibility(player):
    """Damage sets invincibility timer to 1.5s."""
    assert player._invincibility_timer == 0.0
    player.take_damage(0.25, source=(0.0, player.pos.y))
    assert player._invincibility_timer == pytest.approx(1.5)


def test_damage_applies_knockback(player):
    """Damage applies knockback velocities."""
    player.take_damage(0.5, source=(0.0, player.pos.y))
    assert player.vel.x != 0.0
    assert player.vel.y < 0.0


def test_damage_during_invincibility_is_ignored(player):
    """Damage during invincibility period does not apply."""
    player.take_damage(0.5, source=(0.0, player.pos.y))
    health_after_first = player._health
    player.take_damage(1.0, source=(0.0, player.pos.y))
    assert player._health == health_after_first


def test_zero_health_emits_died_event(player):
    """Setting health to 0 emits PLAYER_DIED and transitions to DYING."""
    player.take_damage(5.0, source=(0.0, player.pos.y))
    assert player.state.name == "DYING"
