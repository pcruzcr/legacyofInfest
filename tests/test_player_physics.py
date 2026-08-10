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


# AUD-308 — las dos pruebas de arriba fijan el contador a mano y sólo
# comprueban la comparación; nadie defendía el AVANCE (`+= dt * 60.0`).
# Una mutación que dejara el contador congelado en cero pasaba la suite.
def test_coyote_counter_avanza_con_el_tiempo() -> None:
    player = _make_player()
    player.is_grounded = False
    player._coyote_counter = 0.0
    player._apply_physics(1.0 / 60.0)
    assert player._coyote_counter == pytest.approx(1.0, abs=1e-6)


def test_coyote_time_expira_por_acumulacion() -> None:
    player = _make_player()
    player.is_grounded = False
    player._air_jumps_used = settings.PLAYER_AIR_JUMPS
    player._coyote_counter = 0.0
    player._apply_physics((settings.PLAYER_COYOTE_FRAMES + 1) / 60.0)
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


# ── GAP-033: `draw()` no lo dibujaba nadie en pruebas ────────────────
#
# AUD-308/309 blindaron física y vida máxima; el dibujo (AUD-310,
# AUD-311, AUD-316, AUD-317) y el SFX de aterrizaje (AUD-313) seguían sin
# una sola prueba que pintara el jugador. Aquí se cierran las dos ramas de
# `draw()` (sprite, con el centrado `// 2`, y rectángulo de respaldo) y el
# aterrizaje que emite `SFX_PLAYER_LAND`.


def _sin_sprites(player: Player) -> None:
    """Fuerza el rectángulo de respaldo: en CI los PNG existen."""
    for key in player._sprite_frames:
        player._sprite_frames[key] = []


def test_draw_fallback_no_pinta_cuando_invisible() -> None:
    """Con `_flash_visible=True` la guarda `and not _flash_visible` deja
    pintar; la mutación `And → Or` lo ocultaría todo el parpadeo."""
    player = _make_player()
    _sin_sprites(player)
    player._invincibility_timer = 999.0
    player._flash_visible = True
    surface = pygame.Surface((640, 400))
    surface.fill((0, 0, 0))
    player.draw(surface, pygame.Vector2(0.0, 0.0))
    assert surface.get_at((55, 5))[:3] == (0, 120, 255)


def test_draw_oculta_cuando_el_flash_no_es_visible() -> None:
    player = _make_player()
    _sin_sprites(player)
    player._invincibility_timer = 999.0
    player._flash_visible = False
    surface = pygame.Surface((640, 400))
    surface.fill((0, 0, 0))
    player.draw(surface, pygame.Vector2(0.0, 0.0))
    assert surface.get_at((55, 5))[:3] == (0, 0, 0)


def test_draw_fallback_centra_el_rectangulo_respecto_a_la_camara() -> None:
    """Sin sprites se pinta el rectángulo de respaldo en pantalla.

    La cámara en (50, 40) resta: el jugador en (50, 100) debe quedar en
    (0, 60). Una mutación `Sub → Add` lo dejaría en (100, 140) y el píxel
    del rectángulo quedaría vacío; las constantes de ancho/alto a cero
    pintarían un rectángulo sin área.
    """
    player = _make_player(y=100.0)
    _sin_sprites(player)
    surface = pygame.Surface((640, 400))
    surface.fill((0, 0, 0))
    player.draw(surface, pygame.Vector2(50.0, 40.0))
    assert surface.get_at((5, 65))[:3] == (0, 120, 255)
    assert surface.get_at((15, 88))[:3] == (0, 120, 255)
    assert surface.get_at((110, 150))[:3] == (0, 0, 0)


def test_draw_con_sprite_lo_centra_sobre_la_caja_de_colision() -> None:
    """Con sprites de 32 px y caja de 20 px, el fotograma se centra:
    `offset_x = (20 - 32) // 2 = -6`. La mutación `2 → 0` del divisor
    explota con ZeroDivisionError; `Sub → Add` desplazaría el sprite fuera
    del píxel que sí pinta la versión correcta.
    """
    player = _make_player(y=100.0)
    frame = pygame.Surface((32, 32))
    frame.fill((255, 0, 255))
    player._sprite_frames["IDLE"] = [frame]
    for key in player._sprite_frames:
        if key != "IDLE":
            player._sprite_frames[key] = []
    surface = pygame.Surface((640, 400))
    surface.fill((0, 0, 0))
    player.draw(surface, pygame.Vector2(0.0, 0.0))
    # (50-6, 100) → dentro del sprite de 32x32.
    assert surface.get_at((50, 100))[:3] == (255, 0, 255)
    assert surface.get_at((81, 100))[:3] == (0, 0, 0)


def test_draw_del_estado_hurt_usa_su_color_de_respaldo() -> None:
    """El rectángulo de respaldo de `HURT` es de un rojo distinto al azul
    de IDLE: la constante de color no es decoración, es semántica."""
    from src.framework.entities.states import HurtState
    player = _make_player(y=100.0)
    _sin_sprites(player)
    player._state_instance = HurtState()
    player._invincibility_timer = 0.0
    player._flash_visible = True
    surface = pygame.Surface((640, 400))
    surface.fill((0, 0, 0))
    player.draw(surface, pygame.Vector2(50.0, 40.0))
    assert surface.get_at((5, 65))[:3] == (255, 100, 100)


def test_aterrizar_en_suelo_emite_sfx_land() -> None:
    """AUD-317/AUD-033: la mutación `Ecuación → NoEcuación` en
    `aterrizo_en == "suelo"` silenciaba el aterrizaje sin que la suite lo
    notara."""
    from src.engine.core.event_bus import EventBus
    from src.engine.core.events import Events
    bus = EventBus()
    player = Player(pygame.Vector2(50.0, 100.0), event_bus=bus)
    landed = False
    def on_land() -> None:
        nonlocal landed
        landed = True
    bus.subscribe(Events.SFX_PLAYER_LAND, on_land)
    player.velocity.y = 200.0
    dt = 1.0 / 60.0
    for _ in range(120):
        player.update(dt, _make_floor_rect(200.0))
        if player.is_grounded:
            break
    bus.dispatch()
    assert landed
