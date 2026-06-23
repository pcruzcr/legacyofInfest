"""Tests for Player movement and physics (T5.2).

Per 24_TEST_PLAN.md §7.
"""

import pytest

from src.framework.entities.player import Player


@pytest.fixture
def player():
    return Player(100.0, 100.0)


def test_gravity_applied(player):
    """Gravity accelerates velocity.y downward."""
    player._coyote_timer = 0.0
    player.is_grounded = False
    player.vel.y = 0.0
    player.update(0.1)
    assert player.vel.y > 0


def test_crouch_locks_horizontal_movement():
    """When crouching, velocity.x remains 0 regardless of direction."""
    p = Player(100.0, 100.0)
    p.is_grounded = True
    p.set_crouch(True)
    p.update(0.1)
    assert p.vel.x == 0.0


def test_jump_requires_grounded():
    """start_jump() does nothing when not grounded and no coyote time."""
    p = Player(100.0, 100.0)
    p.is_grounded = False
    p._coyote_timer = 0.0
    p.vel.y = 0.0
    p.start_jump()
    assert p.vel.y == 0.0


def test_jump_sets_upward_vel():
    """start_jump() sets vel.y to JUMP_VELOCITY when grounded."""
    p = Player(100.0, 100.0)
    p.is_grounded = True
    p.start_jump()
    assert p.vel.y == pytest.approx(p.JUMP_VELOCITY)


def test_jump_cut_halves_ascending_vel():
    """release_jump() halves vel.y while ascending."""
    p = Player(100.0, 100.0)
    p.vel.y = -200.0
    p.release_jump()
    assert p.vel.y == pytest.approx(-100.0)


def test_take_damage_applies_knockback():
    """take_damage with a source applies knockback velocities."""
    p = Player(100.0, 100.0)
    p._invincibility_timer = 0.0
    p.take_damage(0.5, source=(0.0, p.position.y))
    assert abs(p.vel.x) == pytest.approx(150.0)
    assert p.vel.y == pytest.approx(-200.0)


def test_coyote_time_allows_jump_after_leaving_edge():
    """Player can jump within COYOTE_FRAMES/60 seconds after leaving ground."""
    p = Player(100.0, 100.0)
    p.is_grounded = False
    p._coyote_timer = p.COYOTE_FRAMES / 60.0
    p.start_jump()
    assert p.vel.y == pytest.approx(p.JUMP_VELOCITY)
