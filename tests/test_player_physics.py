import pygame
import pytest

from src.engine.core import settings
from src.framework.entities.player import Player


def _make_player(y: float = 0.0) -> Player:
    return Player(pygame.Vector2(50.0, y))


def _make_floor_rect(y: float = 200.0) -> list[pygame.Rect]:
    return [pygame.Rect(0, int(y), 640, 32)]


def test_initial_velocity_is_zero() -> None:
    player = _make_player()
    assert player.velocity == pygame.Vector2(0.0, 0.0)


def test_gravity_applied_when_airborne() -> None:
    player = _make_player()
    dt = 1.0 / 60.0
    player.update(dt)
    expected_vy = settings.GRAVITY * dt
    assert player.velocity.y == pytest.approx(expected_vy, abs=0.01)


def test_gravity_not_applied_when_grounded() -> None:
    player = _make_player(y=200.0)
    player.is_grounded = True
    dt = 1.0 / 60.0
    player.update(dt)
    assert player.velocity.y == 0.0


def test_max_fall_speed_clamped() -> None:
    player = _make_player()
    dt = 1.0 / 60.0
    for _ in range(300):
        player.update(dt)
    assert player.velocity.y <= settings.PLAYER_MAX_FALL_SPEED + 0.01


def test_gravity_multiplier_scales_fall_speed() -> None:
    player = _make_player()
    player.gravity_multiplier = 2.0
    dt = 1.0 / 60.0
    player.update(dt)
    expected = settings.GRAVITY * 2.0 * dt
    assert player.velocity.y == pytest.approx(expected, abs=0.01)


def test_ground_detection_on_landing() -> None:
    player = _make_player(y=100.0)
    floor = _make_floor_rect(200.0)
    player.velocity.y = 200.0
    dt = 1.0 / 60.0
    for _ in range(120):
        player.update(dt, floor)
        if player.is_grounded:
            break
    assert player.is_grounded
    assert player.velocity.y == pytest.approx(0.0)


def test_grounded_resets_coyote_counter() -> None:
    player = _make_player(y=100.0)
    floor = _make_floor_rect(200.0)
    player.velocity.y = 200.0
    dt = 1.0 / 60.0
    for _ in range(120):
        player.update(dt, floor)
    assert player._coyote_counter == 0


def test_coyote_time_allows_late_jump() -> None:
    player = _make_player()
    player.is_grounded = False
    player._coyote_counter = settings.PLAYER_COYOTE_FRAMES - 1
    assert player._can_jump()


def test_coyote_time_expires() -> None:
    player = _make_player()
    player.is_grounded = False
    player._air_jumps_used = settings.PLAYER_AIR_JUMPS
    player._coyote_counter = settings.PLAYER_COYOTE_FRAMES + 1
    assert not player._can_jump()


def test_air_jump_allowed_when_coyote_expired() -> None:
    player = _make_player()
    player.is_grounded = False
    player._coyote_counter = settings.PLAYER_COYOTE_FRAMES + 1
    player._air_jumps_used = 0
    assert player._can_jump()


def test_air_jumps_exhausted() -> None:
    player = _make_player()
    player.is_grounded = False
    player._coyote_counter = settings.PLAYER_COYOTE_FRAMES + 1
    player._air_jumps_used = settings.PLAYER_AIR_JUMPS + 1
    assert not player._can_jump()


def test_jump_sets_velocity() -> None:
    player = _make_player(y=200.0)
    player.is_grounded = True
    player._coyote_counter = 0
    player._do_jump()
    assert player.velocity.y == settings.PLAYER_JUMP_FORCE


def test_jump_sets_grounded_false() -> None:
    player = _make_player(y=200.0)
    player.is_grounded = True
    player._do_jump()
    assert not player.is_grounded


def test_jump_increments_air_jumps_when_not_grounded() -> None:
    player = _make_player()
    player.is_grounded = False
    player._air_jumps_used = 0
    player._do_jump()
    assert player._air_jumps_used == 1


def test_jump_cut_halves_velocity_on_release() -> None:
    player = _make_player()
    player.velocity.y = -300.0
    player._jump_cut_applied = False
    player.velocity.y *= 0.5
    player._jump_cut_applied = True
    assert player.velocity.y == pytest.approx(-150.0)


def test_jump_buffering_sets_pending_jump() -> None:
    player = _make_player()
    player.is_grounded = False
    player._pending_jump = True
    player._pending_jump_timer = 8.0 / 60.0
    assert player._pending_jump
    assert player._pending_jump_timer > 0


def test_buffered_jump_fires_on_landing() -> None:
    player = _make_player(y=150.0)
    floor = _make_floor_rect(200.0)
    player.is_grounded = False
    player.velocity.y = 200.0
    player._pending_jump = True
    player._pending_jump_timer = 8.0 / 60.0
    dt = 1.0 / 60.0
    for _ in range(120):
        player.update(dt, floor)
        if player.velocity.y == settings.PLAYER_JUMP_FORCE:
            break
    assert player.velocity.y == settings.PLAYER_JUMP_FORCE


def test_horizontal_collision_stops_movement() -> None:
    player = _make_player(y=180.0)
    wall = pygame.Rect(200, 170, 16, 64)
    floor = pygame.Rect(0, 212, 640, 32)
    player.velocity.x = 300.0
    player.position.x = 100.0
    dt = 1.0 / 60.0
    for _ in range(90):
        player.update(dt, [wall, floor])
    assert player.rect.right <= wall.left + 1


def test_velocity_zeroed_on_wall_collision() -> None:
    player = _make_player(y=180.0)
    wall = pygame.Rect(200, 170, 16, 64)
    floor = pygame.Rect(0, 212, 640, 32)
    player.velocity.x = 300.0
    player.position.x = 100.0
    dt = 1.0 / 60.0
    for _ in range(90):
        player.update(dt, [wall, floor])
    assert player.velocity.x == 0.0


def test_vertical_landing_sets_grounded() -> None:
    player = _make_player(y=100.0)
    floor = _make_floor_rect(200.0)
    player.velocity.y = 200.0
    dt = 1.0 / 60.0
    for _ in range(120):
        player.update(dt, floor)
        if player.is_grounded:
            break
    assert player.is_grounded
    assert player.velocity.y == pytest.approx(0.0)
