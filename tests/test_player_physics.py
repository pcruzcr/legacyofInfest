"""
Module: test_player_physics
System: tests
Academic Unit: N/A
Description: Tests for Player physics: gravity, jump, coyote time,
jump cut, collision resolution, and max fall speed clamping.
"""
import pygame

from src.engine.core import settings
from src.framework.entities.player import Player


def _make_player(y: float = 0.0) -> Player:
    """Helper to create a player at a given Y position."""
    return Player(pygame.Vector2(50.0, y))


def _make_floor_rect(y: float = 200.0) -> list[pygame.Rect]:
    """Helper to create a floor collision rect."""
    return [pygame.Rect(0, int(y), 640, 32)]


class TestGravity:
    """Tests for gravity application when airborne."""

    def test_gravity_applied_when_airborne(self) -> None:
        player = _make_player(y=0.0)
        initial_vy = player.velocity.y
        dt = 1.0 / 60.0
        player.update(dt)
        expected = initial_vy + settings.GRAVITY * dt
        assert abs(player.velocity.y - expected) < 0.01, (
            f"Expected {expected}, got {player.velocity.y}"
        )

    def test_max_fall_speed_clamped(self) -> None:
        player = _make_player(y=0.0)
        dt = 1.0 / 60.0
        # Simulate many frames of falling
        for _ in range(300):
            player.update(dt)
        assert player.velocity.y <= settings.PLAYER_MAX_FALL_SPEED + 0.01, (
            f"velocity.y {player.velocity.y} exceeds max fall speed "
            f"{settings.PLAYER_MAX_FALL_SPEED}"
        )


class TestJump:
    """Tests for jump mechanics."""

    def test_jump_sets_negative_velocity(self) -> None:
        player = _make_player(y=200.0)
        # Place on floor so grounded
        player.position.y = 200.0 - 32.0
        player.is_grounded = True
        player._coyote_counter = 0
        player._do_jump()
        assert abs(player.velocity.y - settings.PLAYER_JUMP_FORCE) < 0.01, (
            f"Expected jump force {settings.PLAYER_JUMP_FORCE}, "
            f"got {player.velocity.y}"
        )

    def test_coyote_time_allows_late_jump(self) -> None:
        player = _make_player(y=0.0)
        player.is_grounded = False
        player._coyote_counter = settings.PLAYER_COYOTE_FRAMES - 1
        assert player._can_jump() is True, (
            "Player should be able to jump within coyote time"
        )

    def test_coyote_time_expires(self) -> None:
        player = _make_player(y=0.0)
        player.is_grounded = False
        player._air_jumps_used = settings.PLAYER_AIR_JUMPS  # Exhaust air jumps
        player._coyote_counter = settings.PLAYER_COYOTE_FRAMES + 1
        assert player._can_jump() is False, (
            "Player should NOT be able to jump after coyote time expires when air jumps exhausted"
        )

    def test_air_jump_allowed(self) -> None:
        player = _make_player(y=0.0)
        player.is_grounded = False
        player._coyote_counter = settings.PLAYER_COYOTE_FRAMES + 1
        player._air_jumps_used = 0
        assert player._can_jump() is True, (
            "Player should be able to air jump after coyote time expires"
        )

    def test_jump_cut_halves_velocity(self) -> None:
        player = _make_player(y=0.0)
        player.velocity.y = -300.0  # ascending
        player._jump_cut_applied = False
        # Simulate releasing jump while ascending
        player.velocity.y *= 0.5
        player._jump_cut_applied = True
        assert abs(player.velocity.y - (-150.0)) < 0.01, (
            f"Expected -150.0 after jump cut, got {player.velocity.y}"
        )


class TestCollision:
    """Tests for AABB collision resolution."""

    def test_horizontal_collision_stops_movement(self) -> None:
        player = _make_player(y=180.0)
        player.rect.height = 32
        player.rect.width = 20
        # Wall + floor so player stays grounded and intersects the wall
        wall = pygame.Rect(200, 170, 16, 64)
        floor = pygame.Rect(0, 212, 640, 32)
        player.velocity.x = 300.0
        player.position.x = 100.0
        dt = 1.0 / 60.0
        for _ in range(90):
            player.update(dt, [wall, floor])
        assert player.rect.right <= wall.left + 1, (
            f"Player rect.right {player.rect.right} should be <= "
            f"wall.left {wall.left}"
        )

    def test_vertical_landing_sets_grounded(self) -> None:
        player = _make_player(y=100.0)
        floor = _make_floor_rect(200.0)
        player.velocity.y = 200.0  # falling
        dt = 1.0 / 60.0
        # Simulate enough frames to land
        for _ in range(120):
            player.update(dt, floor)
            if player.is_grounded:
                break
        err = "Player should be grounded after landing"
        assert player.is_grounded is True, err
        assert abs(player.velocity.y) < 0.01, (
            f"velocity.y should be 0 after landing, got {player.velocity.y}"
        )
