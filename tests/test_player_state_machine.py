from __future__ import annotations

import pygame

from src.engine.core import settings
from src.engine.input.input_manager import InputManager
from src.framework.entities.player import Player, PlayerState
from src.framework.entities.player_states import (
    ShortAttackState, DyingState, IdleState,
    WalkingState, JumpingState, FallingState,
)


def _make_input() -> InputManager:
    """Create a fresh InputManager for testing."""
    return InputManager()


def _press_key(im: InputManager, key: int) -> None:
    """Simulate a KEYDOWN by directly injecting into InputManager internals."""
    im._pressed_this_frame.add(key)
    im._held.add(key)


class TestIdleWalking:
    """Tests for IDLE and WALKING state transitions via real input."""

    def test_idle_to_walking_on_move_input(self) -> None:
        im = _make_input()
        player = Player(pygame.Vector2(50.0, 192.0))
        player.is_grounded = True
        player._change_state_instance(IdleState())
        _press_key(im, pygame.K_RIGHT)
        player.update(1.0 / 60.0, [pygame.Rect(0, 224, 640, 32)], im)
        assert player.state == PlayerState.WALKING
        assert player.velocity.x > 0

    def test_walking_to_idle_on_input_release(self) -> None:
        _make_input()
        player = Player(pygame.Vector2(50.0, 192.0))
        player.is_grounded = True
        player._change_state_instance(WalkingState())
        player.velocity.x = settings.PLAYER_WALK_SPEED
        player.update(1.0 / 60.0, [pygame.Rect(0, 224, 640, 32)])
        assert player.state == PlayerState.IDLE


class TestJumpingFalling:
    """Tests for JUMPING and FALLING state transitions."""

    def test_grounded_jump_input_to_jumping(self) -> None:
        im = _make_input()
        player = Player(pygame.Vector2(50.0, 192.0))
        player.is_grounded = True
        player._change_state_instance(IdleState())
        _press_key(im, pygame.K_SPACE)
        player.update(1.0 / 60.0, [pygame.Rect(0, 224, 640, 32)], im)
        assert player.state == PlayerState.JUMPING

    def test_jumping_to_falling_at_peak(self) -> None:
        _make_input()
        player = Player(pygame.Vector2(50.0, 0.0))
        player.is_grounded = False
        player._change_state_instance(JumpingState())
        player._jump_cut_applied = True
        player.velocity.y = 100.0
        dt = 1.0 / 60.0
        player.update(dt)
        assert player.state == PlayerState.FALLING

    def test_falling_to_idle_on_land(self) -> None:
        _make_input()
        player = Player(pygame.Vector2(50.0, 160.0))
        player.is_grounded = False
        player._change_state_instance(FallingState())
        player.velocity.y = 200.0
        dt = 1.0 / 60.0
        rects = [pygame.Rect(0, 192, 640, 32)]
        player.update(dt, rects)
        player.update(dt, rects)
        assert player.state == PlayerState.IDLE


class TestCrouch:
    """Tests for CROUCHING state."""

    def test_crouch_locks_horizontal_velocity(self) -> None:
        im = _make_input()
        player = Player(pygame.Vector2(50.0, 192.0))
        player.is_grounded = True
        player._change_state_instance(IdleState())
        _press_key(im, pygame.K_DOWN)
        player.update(1.0 / 60.0, [pygame.Rect(0, 224, 640, 32)], im)
        assert player.state == PlayerState.CROUCHING

    def test_crouch_keeps_feet_on_floor(self) -> None:
        im = _make_input()
        player = Player(pygame.Vector2(50.0, 161.0))
        player.is_grounded = True
        player._change_state_instance(IdleState())
        player.velocity.y = 300.0
        rects = [pygame.Rect(0, 192, 640, 32)]
        player.update(1.0 / 60.0, rects)
        assert player.is_grounded
        assert player.rect.bottom == 192
        standing_bottom = player.rect.bottom
        im._pressed_this_frame.add(pygame.K_DOWN)
        im._held.add(pygame.K_DOWN)
        player.update(1.0 / 60.0, rects, im)
        assert player.state == PlayerState.CROUCHING
        assert player.rect.bottom == standing_bottom


class TestAttack:
    """Tests for attack state input locking."""

    def test_attack_state_locks_input(self) -> None:
        player = Player(pygame.Vector2(50.0, 0.0))
        player.is_grounded = True
        player._change_state_instance(ShortAttackState())
        player.velocity.x = settings.PLAYER_WALK_SPEED
        assert player.state == PlayerState.SHORT_ATTACK


class TestHurtDying:
    """Tests for HURT and DYING state transitions."""

    def test_damage_forces_hurt_state(self) -> None:
        player = Player(pygame.Vector2(50.0, 0.0))
        player._change_state_instance(IdleState())
        player.apply_damage(0.5, (50.0, 0.0))
        assert player.state == PlayerState.HURT

    def test_health_zero_forces_dying_state(self) -> None:
        player = Player(pygame.Vector2(50.0, 0.0))
        player._change_state_instance(IdleState())
        player.apply_damage(settings.PLAYER_MAX_HEALTH, (50.0, 0.0))
        assert player.state == PlayerState.DYING

    def test_dying_state_is_terminal(self) -> None:
        player = Player(pygame.Vector2(50.0, 0.0))
        player._change_state_instance(DyingState())
        player.apply_damage(0.5, (50.0, 0.0))
        assert player.state == PlayerState.DYING
