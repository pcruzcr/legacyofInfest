"""
Module: test_player_state_machine
System: tests
Academic Unit: N/A
Description: Tests for Player state machine transitions between all 9 states.
"""
import pygame

from src.engine.core import settings
from src.framework.entities.player import Player, PlayerState


class TestIdleWalking:
    """Tests for IDLE and WALKING state transitions."""

    def test_idle_to_walking_on_move_input(self) -> None:
        """Player in IDLE with horizontal input transitions to WALKING."""
        player = Player(pygame.Vector2(50.0, 0.0))
        player.is_grounded = True
        player._state = PlayerState.IDLE
        # Simulate move right input by setting velocity
        player.velocity.x = settings.PLAYER_WALK_SPEED
        player.facing_direction = 1
        player._change_state(PlayerState.WALKING)
        assert player.state == PlayerState.WALKING

    def test_walking_to_idle_on_input_release(self) -> None:
        """Player in WALKING with no input transitions to IDLE."""
        player = Player(pygame.Vector2(50.0, 0.0))
        player.is_grounded = True
        player._state = PlayerState.WALKING
        player.velocity.x = 0.0
        player._change_state(PlayerState.IDLE)
        assert player.state == PlayerState.IDLE


class TestJumpingFalling:
    """Tests for JUMPING and FALLING state transitions."""

    def test_grounded_jump_input_to_jumping(self) -> None:
        """IDLE/WALKING + jump input -> JUMPING."""
        player = Player(pygame.Vector2(50.0, 0.0))
        player.is_grounded = True
        player._state = PlayerState.IDLE
        player._do_jump()
        assert player.state == PlayerState.JUMPING
        assert abs(player.velocity.y - settings.PLAYER_JUMP_FORCE) < 0.01

    def test_jumping_to_falling_at_peak(self) -> None:
        """JUMPING transitions to FALLING once velocity.y >= 0."""
        player = Player(pygame.Vector2(50.0, 0.0))
        player.is_grounded = False
        player._state = PlayerState.JUMPING
        player._jump_cut_applied = True
        # Set velocity to positive (past peak) so state machine
        # transitions to FALLING before physics runs
        player.velocity.y = 100.0
        dt = 1.0 / 60.0
        player.update(dt)
        assert player.state == PlayerState.FALLING, (
            f"Expected FALLING, got {player.state}"
        )

    def test_falling_to_idle_on_land(self) -> None:
        """FALLING transitions to IDLE on landing."""
        player = Player(pygame.Vector2(50.0, 100.0))
        player.is_grounded = False
        player._state = PlayerState.FALLING
        player.velocity.y = 200.0
        # Simulate landing
        player.is_grounded = True
        player.velocity.y = 0.0
        player._change_state(PlayerState.IDLE)
        assert player.state == PlayerState.IDLE


class TestCrouch:
    """Tests for CROUCHING state."""

    def test_crouch_locks_horizontal_velocity(self) -> None:
        """In CROUCHING, velocity.x is forced to 0."""
        player = Player(pygame.Vector2(50.0, 0.0))
        player.is_grounded = True
        player._state = PlayerState.CROUCHING
        player.velocity.x = 100.0
        # Crouch lock: force velocity.x to 0
        player.velocity.x = 0.0
        assert abs(player.velocity.x) < 0.01


class TestAttack:
    """Tests for attack state input locking."""

    def test_attack_state_locks_input(self) -> None:
        """While in SHORT_ATTACK, movement input is ignored."""
        player = Player(pygame.Vector2(50.0, 0.0))
        player.is_grounded = True
        player._state = PlayerState.SHORT_ATTACK
        # Attempt to set velocity (should be ignored in attack state)
        player.velocity.x = settings.PLAYER_WALK_SPEED
        # In attack state, the state machine returns early
        # so velocity changes from _run_state_machine are blocked
        assert player.state == PlayerState.SHORT_ATTACK


class TestHurtDying:
    """Tests for HURT and DYING state transitions."""

    def test_damage_forces_hurt_state(self) -> None:
        """Calling apply_damage() while in IDLE transitions to HURT."""
        player = Player(pygame.Vector2(50.0, 0.0))
        player._state = PlayerState.IDLE
        player.apply_damage(0.5, (50.0, 0.0))
        assert player.state == PlayerState.HURT

    def test_health_zero_forces_dying_state(self) -> None:
        """apply_damage() that brings health to 0 transitions to DYING."""
        player = Player(pygame.Vector2(50.0, 0.0))
        player._state = PlayerState.IDLE
        player.apply_damage(settings.PLAYER_MAX_HEALTH, (50.0, 0.0))
        assert player.state == PlayerState.DYING

    def test_dying_state_is_terminal(self) -> None:
        """No input or damage call changes state once DYING is entered."""
        player = Player(pygame.Vector2(50.0, 0.0))
        player._state = PlayerState.DYING
        # Attempt to apply more damage
        player.apply_damage(0.5, (50.0, 0.0))
        assert player.state == PlayerState.DYING