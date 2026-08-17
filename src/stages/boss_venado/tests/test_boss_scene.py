"""Boss scene tests: zone-based camera policy + engine/harness contracts."""
import types

import pygame

from src.engine.core import settings
from src.framework.stage.camera import Camera
from src.stages.boss_venado.boss_venado_scene import (
    ARENA_SETTLE_DURATION,
    ARENA_X0,
    PLAYER_HALO_PEAK,
    PLAYER_HALO_RADIUS,
    BossVenadoScene,
)

MAP_W, MAP_H = 3280, 608   # boss_venado.tmx (mapa Residencias promovido 2026-07-24)




def test_locks_pure_logic():
    sentinel = [object()]
    assert BossVenadoScene._locks_for_player_x(100.0, sentinel) == []
    assert BossVenadoScene._locks_for_player_x(ARENA_X0 - 1, sentinel) == []
    assert BossVenadoScene._locks_for_player_x(ARENA_X0, sentinel) == sentinel
    assert BossVenadoScene._locks_for_player_x(3200.0, sentinel) == sentinel


def _bare_scene_with_camera(camera_offset: tuple[float, float]) -> BossVenadoScene:
    """H-17 candado (see boss_venado_scene.py's H-17 docstring +
    reports/FINDINGS.md H-17): a real (but display-less -- Camera() only
    touches pygame.Vector2/settings, no display boot needed) Camera wired
    just enough for _pin_camera_to_arena()/_arena_target_offset() to run in
    isolation, same avoid-the-expensive-App-boot pattern the rest of this
    file already uses."""
    scene = BossVenadoScene.__new__(BossVenadoScene)
    scene._camera = Camera()
    scene._camera.offset = pygame.Vector2(camera_offset)
    scene._camera.set_map_size(MAP_W, MAP_H)
    scene._stage_data = types.SimpleNamespace(map_pixel_size=(MAP_W, MAP_H))
    scene._in_arena_prev = False
    scene._arena_ease_elapsed = ARENA_SETTLE_DURATION
    scene._arena_ease_start = pygame.Vector2(0.0, 0.0)
    return scene


def test_pin_camera_to_arena_settles_on_the_true_right_edge():
    """H-17 regression lock -- human playtest bug (2026-07-30): entering the
    arena on foot used to freeze the camera with the right edge stuck around
    x=2900 (mid-gazebo) instead of the map's true edge (3280). Simulates the
    exact freeze offset the headless repro measured (offset.x=2105.2 the
    frame the lock engaged) and confirms _pin_camera_to_arena eases it all
    the way to ARENA_X0 (== MAP_W - INTERNAL_WIDTH == 2480) within
    ARENA_SETTLE_DURATION, and holds it there afterwards."""
    scene = _bare_scene_with_camera((2105.2, 8.0))
    dt = 1.0 / 60.0
    frames = int(ARENA_SETTLE_DURATION / dt) + 5   # settle window + margin
    for _ in range(frames):
        scene._pin_camera_to_arena(dt, True)
    assert scene._camera.offset.x == ARENA_X0
    assert scene._camera.offset.x + settings.INTERNAL_WIDTH == MAP_W, (
        "borde derecho visible debe ser exactamente el borde real del mapa")
    assert scene._camera.offset.y == 8.0   # MAP_H - INTERNAL_HEIGHT clamp

    # Holds steady on later frames too (not just the instant the ease ends).
    for _ in range(120):
        scene._pin_camera_to_arena(dt, True)
    assert scene._camera.offset.x == ARENA_X0


def test_pin_camera_to_arena_eases_instead_of_snapping():
    """Guards the "border-jump" fix documented in boss_venado_scene.py's
    H-17 section (and backups/pre-reset-2026-07-21/src/boss_venado_scene.py,
    where a hard snap was tried first and rejected): the very first frame
    after crossing into the arena must still be mid-transition, not already
    sitting on the target -- a silent regression back to a hard snap would
    reproduce the ~400px single-frame screen_x hard cut."""
    scene = _bare_scene_with_camera((2105.2, 8.0))
    scene._pin_camera_to_arena(1.0 / 60.0, True)
    assert 2105.2 < scene._camera.offset.x < ARENA_X0, (
        "el primer frame enganchado debe seguir en pleno ease, no ya en el target")


def test_pin_camera_to_arena_is_noop_outside_the_arena():
    """Outside the arena, _pin_camera_to_arena must leave camera.offset
    completely untouched -- the inherited StageScene follow-lerp (already
    run by super().update() earlier in the frame) is what's supposed to be
    in control there."""
    scene = _bare_scene_with_camera((600.0, 8.0))
    scene._pin_camera_to_arena(1.0 / 60.0, False)
    assert (scene._camera.offset.x, scene._camera.offset.y) == (600.0, 8.0)


def test_pin_camera_to_arena_settles_across_repeated_oscillation():
    """H-17 candado de vaivén (2026-07-30): las corridas largas oficiales
    (final_cam_dodger/final_cam_competent, 7200/14400f seed 1) muestran al
    bot cruzando ARENA_X0 hacia adelante y atrás varias veces cerca del
    umbral (keep-away del dodger, proximity-gate del competent) antes de
    quedarse en combate. Cada entrada debe volver a asentar EXACTO en
    ARENA_X0, sin importar cuántas veces se repita el vaivén -- guarda
    contra que el pin se vuelva frágil bajo oscilación repetida (una de las
    hipótesis descartadas al investigar el falso rojo del gate)."""
    scene = _bare_scene_with_camera((2105.2, 8.0))
    dt = 1.0 / 60.0
    ease_frames = int(ARENA_SETTLE_DURATION / dt) + 5

    for cycle in range(4):
        for _ in range(ease_frames):
            scene._pin_camera_to_arena(dt, True)
        assert scene._camera.offset.x == ARENA_X0, (
            f"ciclo {cycle}: no asentó en {ARENA_X0} (offset={scene._camera.offset.x})")
        # el player sale de la arena unos frames (follow-lerp normal, simulado
        # moviendo el offset directamente) antes de la siguiente entrada.
        scene._pin_camera_to_arena(dt, False)
        scene._camera.offset.x = 1950.0 + cycle * 10.0   # posición "de salida" distinta cada vez


def test_pin_camera_to_arena_re_eases_on_re_entry():
    """Leaving the arena (in_arena=False) resets the transient ease latch,
    so walking back out and back in re-eases cleanly from the new
    follow-camera position instead of silently staying "settled" at a stale
    target (or, worse, snapping)."""
    scene = _bare_scene_with_camera((2105.2, 8.0))
    dt = 1.0 / 60.0
    for _ in range(int(ARENA_SETTLE_DURATION / dt) + 5):
        scene._pin_camera_to_arena(dt, True)
    assert scene._camera.offset.x == ARENA_X0

    # Player walks back out -- follow-lerp (simulated here by just moving
    # the offset directly) takes the camera elsewhere.
    scene._pin_camera_to_arena(dt, False)
    scene._camera.offset.x = 1900.0

    # Re-entering must ease again, not instantly re-snap to ARENA_X0.
    scene._pin_camera_to_arena(dt, True)
    assert 1900.0 < scene._camera.offset.x < ARENA_X0


def test_scene_declares_engine_contract():
    assert BossVenadoScene.STAGE_ID == "boss_venado"
    assert hasattr(BossVenadoScene, "_get_boss")        # playtest Recorder contract


def test_player_halo_is_a_bright_center_dark_edge_gradient():
    """Playtest finding (2026-07-28): the hooded player sprite camouflages
    against the dusk foliage. _build_player_halo() is the pure/cacheable
    builder for the additive moonlight fix -- no scene needed to test it."""
    halo = BossVenadoScene._build_player_halo()
    assert isinstance(halo, pygame.Surface)
    assert halo.get_size() == (PLAYER_HALO_RADIUS * 2, PLAYER_HALO_RADIUS * 2)
    center_px = halo.get_at((PLAYER_HALO_RADIUS, PLAYER_HALO_RADIUS))
    edge_px = halo.get_at((0, 0))
    assert sum(center_px[:3]) > sum(edge_px[:3]), (
        "halo center should be brighter than its edge (radial gradient)")


def test_scene_overrides_draw_for_player_halo():
    """Constructing the real scene (App/TMX/pygame display) is expensive --
    this only asserts the override exists on BossVenadoScene itself (not
    just inherited from StageScene), which is what actually blits the halo."""
    assert hasattr(BossVenadoScene, "draw")
    assert "draw" in BossVenadoScene.__dict__


def test_player_halo_never_silently_disabled():
    """Regression lock: nothing should be able to quietly neuter the halo
    fix (e.g. someone drops PLAYER_HALO_PEAK toward 0, or shrinks the
    radius until it's a no-op) without a test going red.

    Floor agreed after the 2026-07-28 playtest -- the hooded sprite is
    RGB~=(15, 20, 35) on a dusk palette; below this the hero camouflages
    again."""
    assert PLAYER_HALO_PEAK >= 30
    assert PLAYER_HALO_RADIUS >= 32

    halo = BossVenadoScene._build_player_halo()
    center_px = halo.get_at((PLAYER_HALO_RADIUS, PLAYER_HALO_RADIUS))
    assert sum(center_px[:3]) >= 3 * 25, (
        "halo center is too dim to read against the dusk palette -- "
        "the fix was silently weakened")


def test_scene_no_longer_carries_the_hud_phase_compensation():
    """H-02, FIXED upstream (AUD-512): `HUD.set_boss_hud` used to ignore its
    own ``phase`` argument and render `phase_count` (the TOTAL, constant for
    the whole fight) instead of the current phase. This scene used to carry
    a `_compensate_boss_hud_phase` workaround, re-calling `set_boss_hud`
    after `super().update(dt)` with the current phase jammed into the
    `phase_count` slot -- the one the old, buggy renderer read.

    Now that `hud.py` tracks `_boss_phase` for real (see
    `tests/test_el_hud_esta_a_la_escala_de_la_pantalla.py`), that workaround
    would do actual harm if it came back: it would overwrite the real,
    correct `phase_count` the engine's own call already set. This just
    guards against it silently returning."""
    assert not hasattr(BossVenadoScene, "_compensate_boss_hud_phase")
