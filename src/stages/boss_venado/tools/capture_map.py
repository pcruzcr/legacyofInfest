"""
Module: capture_map
System: stages.boss_venado.tools
Description: Headless in-engine screenshot harness for the "Residencias al
Crepusculo" boss arena map (Task 6, in-game verification). Boots the real
App (same pipeline main.py's ``--boss boss_venado`` uses) under SDL dummy
video/audio drivers, pushes BossVenadoScene (still the professor's original
stub -- STAGE_ID/STAGE_NAME/ZONE plus the TMX path, nothing else -- so this
exercises StageScene straight from the framework), teleports the player to
three x positions along the corridor/arena, and dumps the engine's actual
internal render surface (settings.INTERNAL_WIDTH x INTERNAL_HEIGHT, cleared
every frame with settings.BG_COLOR) to PNG. Adapted from the proven base
``backups\\pre-reset-2026-07-21\\src\\tools\\capture_frames.py`` (read-only
reference, not modified) -- same App-boot / manual-dt-step pipeline, extended
from 2 fixed captures to 3 parametrized ones and with two CAPTURE-ONLY
compensations documented below.

Captures five frames (round-11: the map widened to 205 cols with a new CARPORT
zone; round-12: the boss moved to the arena's far right and a 5th "final"
capture added), all with the player's FEET at world y=560 (TMX floor top, see
the ``Floor`` collision object at y=560 in boss_venado.tmx):
  1. spawn   -- x=48   (TMX's own PlayerSpawn_01 position).
  2. carport -- x=1280 (the new parking bay, CARPORT zone cols 65-95).
  3. arcos   -- x=2000 (corridor, before the arena boundary at x=2480).
  4. arena   -- x=2880 (inside ArenaZone_01/CameraLock_01, framing the
     gazebo set-piece; BossVenado_01 no longer spawns here as of round-12).
  5. final   -- x=3150 (round-12, user feedback "pon el boss al final del
     mapa": near BossVenado_01's new spawn at x=3168, past the gazebo and
     close to RightWall_Arena at x=3264, to verify the boss lands there).

This tool only *drives* the scene through the public update()/draw() loop
and pokes at the already-instantiated Player's public position/velocity/rect
fields to teleport, plus two narrowly-scoped, capture-only compensations for
known engine issues (both documented in full in
``reports\\map_residencias\\CAMERALOCK.md`` and ``reports\\FINDINGS.md``
H-10) -- it does NOT modify src/engine, src/framework, or the TMX.

CAPTURE-ONLY COMPENSATION 1 -- CameraLock global switch (approved by the
architect for this capture tool only): the TMX declares CameraLock_01
(lock_x=lock_y=true) covering the arena. ``Camera.set_camera_locks()``
(src/framework/stage/camera.py:63-67) does **not** gate on the lock's rect
at all -- it does ``self._is_locked_x = any(l.lock_x for l in locks)`` over
the FULL list, unconditionally, every frame (called from
``StageScene.update()`` line ~612). So the presence of any CameraLock object
in the TMX freezes the camera on BOTH axes for the entire stage, from frame
0, including the corridor -- there is no "only once the player enters the
rect" gating anywhere in the engine (verified against
``tests/test_camera.py::TestCameraLockZones``, which only asserts the
boolean, never the rect). Left as-is, every capture below would show the
spawn frame frozen in place. Compensation: immediately after the scene is
pushed, this script empties ``scene._stage_data.camera_locks = []``. Because
``StageScene.update()`` re-reads ``stage.camera_locks`` (not a cached copy)
every single frame, an empty list keeps both axes unlocked for the rest of
this process's lifetime. This is a data mutation on the already-loaded
StageData instance done from the harness, not an edit to the TMX or the
engine file that reads it.

CAPTURE-ONLY COMPENSATION 2 -- H-10 (known engine bug, see
``reports\\FINDINGS.md`` search "H-10"): ``StageScene`` never calls the one
pyscroll method that actually repositions the tilemap buffer
(``BufferedRenderer.center()`` / ``PyscrollGroup.center()``,
.venv-boss/Lib/site-packages/pyscroll/{orthographic,group}.py). Instead it
only overwrites ``stage.map_layer._map_layer.view_rect`` directly (a plain
pygame.Rect field that pyscroll's real blit path,
``BufferedRenderer._render_map()``, never reads -- it reads
``_x_offset``/``_y_offset``/``_tile_view``/``_buffer``, which are only ever
touched inside ``center()``). Net effect: ``camera.offset`` (the Camera
class, framework) advances correctly frame to frame, entities (drawn
separately via each entity's own ``draw(surface, camera_offset)``) move
correctly relative to it, but the pyscroll tile *background* stays glued to
whatever ``_initialize_buffers()`` left it at when the map was first loaded
-- i.e. the corner around the spawn -- no matter how far the player/camera
travel. Confirmed independently for ``stage0`` too (same StageScene base),
so this is a shared-engine bug, not something introduced by this tool or by
BossVenadoScene (the stub does not touch pyscroll/map_layer at all).
Compensation: this script's own per-frame step helper (``_step``, below)
calls the REAL pyscroll API, ``stage.map_layer.center((camera.offset.x +
INTERNAL_WIDTH / 2, camera.offset.y + INTERNAL_HEIGHT / 2))`` (``center()``
wants the viewport's CENTER, not its top-left corner, hence the ``+ w/2,
+ h/2`` over the top-left-style ``camera.offset`` that entity ``draw()``
calls already subtract directly) -- right after ``scene_manager.update()``
computes the frame's final camera offset and right before ``app._draw()``
consumes it, every single frame. This mirrors the previously-verified fix
pattern (``reports\\FINDINGS.md`` H-10, "Corrección aplicada") of an earlier,
now-reset iteration of ``BossVenadoScene`` (a ``_sync_map_render()`` method
called from the scene itself) -- reproduced here at the harness level
instead, since this task only creates a capture tool and does not touch
``boss_venado_scene.py``. No src/engine or src/framework file is edited by
either compensation; both act on already-constructed runtime objects
(StageData, PyscrollGroup) from outside, through their existing public API.

HISTORICAL NOTE (former WORKAROUND 3, now removed) -- BossVenado_01
constructor/TMX mismatch: earlier this tool discovered that
``gen_level_residencias.py`` emitted ``arena_origin_x``/``arena_origin_y``
(typed float) properties on ``BossVenado_01``, copied from a superseded
generator paired with an OLDER boss ctor that accepted those kwargs. The
CURRENT (professor's original, reset) ``boss_venado.py`` has a bare
``__init__(self, spawn_position)``, and ``StageLoader.load()`` passes every
TMX object property as a keyword arg to the entity class, so those props made
it raise ``TypeError`` and abort the whole stage load -- crashing the real
``python main.py --boss boss_venado`` too. This is now FIXED at the source:
``gen_level_residencias.py`` emits BossVenado_01 as a bare point object with
no properties, so the boss instantiates normally and appears in the arena
capture -- no registry workaround is needed here anymore. A regression test,
``tests/test_map_residencias.py::test_entities_instantiate_from_tmx``, loads
the TMX with "BossVenado" registered and asserts the boss instantiates.

Usage (from the LAB's ``game`` directory, dummy drivers so no real window/
audio device is required -- also force-set below so the script is robust
even if the caller forgets the env vars):

    SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy \
        path/to/python.exe src/stages/boss_venado/tools/capture_map.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Must be set before pygame is imported anywhere (App.__init__ calls
# pygame.init()/pygame.mixer.init()) so no real display/audio device is
# touched in this headless environment.
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

# tools/ -> boss_venado/ -> stages/ -> src/ -> game/ (LAB game root, the
# equivalent of legacyofInfest/ in the real project).
_GAME_ROOT = Path(__file__).resolve().parents[4]
os.chdir(_GAME_ROOT)  # StageLoader.load() resolves the TMX path relative to cwd.
sys.path.insert(0, str(_GAME_ROOT))

import pygame  # noqa: E402

from src.engine.core import settings  # noqa: E402
from src.engine.core.app import App  # noqa: E402
from src.framework.entities.boss_base import BossBase  # noqa: E402
from src.stages.boss_venado.boss_venado_scene import BossVenadoScene  # noqa: E402

# LAB root (one level above game/) -- reports/ lives alongside game/, not
# nested inside the engine tree.
OUT_DIR = _GAME_ROOT.parent / "reports" / "map_residencias"
DT: float = 1.0 / 60.0
SETTLE_FRAMES: int = 400  # settle long enough (>6s) that the transient intro HUD
#                           (stage banner ~2.9s + "move" tutorial TIP 6s) expires,
#                           so the captures show the STEADY-STATE real view -- the
#                           map art, not intro overlays covering the sky/ground.

# (name, world x, feet-y) -- feet y is always 560 (TMX Floor collision top).
# ROUND-11: four positions, one per ~800px camera window of the widened 205-col
# map (spawn 0-50, carport 50-100, arcos 100-150, arena 150-205).
# ROUND-12 (user feedback: "pon el boss al final del mapa"): a 5th "final"
# position added near the boss's new spawn (x=3168) so its placeholder is
# visible in the captures, past the gazebo and close to RightWall_Arena.
CAPTURES: list[tuple[str, float, float]] = [
    ("spawn", 48.0, 560.0),     # TMX PlayerSpawn_01
    ("carport", 1280.0, 560.0),  # CARPORT zone (cols 65-95), the parking bay
    ("arcos", 2000.0, 560.0),   # corridor, before the arena boundary at x=2480
    ("arena", 2880.0, 560.0),   # inside ArenaZone_01/CameraLock_01, frames the gazebo
    ("final", 3150.0, 560.0),   # near BossVenado_01's new spawn (x=3168), map's far end
]


def _sync_map_render(scene: BossVenadoScene) -> None:
    """CAPTURE-ONLY COMPENSATION 2 (H-10, see module docstring): call
    pyscroll's real ``center()`` API so the tile background actually follows
    ``camera.offset`` instead of staying glued to the initial buffer window.
    Defensively no-ops if stage/map_layer aren't ready yet (e.g. very first
    tick before on_enter() has run, or a stage without a tilemap)."""
    stage = scene._stage_data
    if stage is None:
        return
    map_layer = getattr(stage, "map_layer", None)
    if map_layer is None:
        return
    offset = scene._camera.offset
    map_layer.center((
        offset.x + settings.INTERNAL_WIDTH / 2,
        offset.y + settings.INTERNAL_HEIGHT / 2,
    ))


def _pin_boss(boss: BossBase | None, home: pygame.Vector2 | None) -> None:
    """CAPTURE-ONLY COMPENSATION 3 -- hold the boss at its TMX spawn.

    The professor's original ``BossVenado`` movement AI uses arena constants at
    a 320x224 scale (``ARENA_W = 320``) but operates on WORLD coordinates, so on
    its very first ``update()`` the sine-drift clamp (``if position.x > ARENA_W
    - 32``) yanks the boss from its world spawn (x=3168, inside the arena) to
    world x~44 -- flinging it out of the arena and into the PRADERA sky, where it
    then floats through the spawn/arcos art frames and vanishes from the arena
    frame. That 320-scale arena-clamp bug is the professor's boss AI, out of
    scope for this MAP capture tool (logged as a FINDINGS entry). To capture the
    MAP with the boss where the TMX actually places it, we re-pin the boss to its
    spawn every frame AFTER the scene update (which moved it) and BEFORE the draw
    -- a runtime mutation on the already-constructed entity, exactly like the two
    compensations above; no engine/TMX/boss file is edited."""
    if boss is None or home is None:
        return
    boss.position.update(home)
    boss.rect.x = int(home.x)
    boss.rect.y = int(home.y)
    if hasattr(boss, "velocity"):
        boss.velocity.update(0.0, 0.0)


def _step(app: App, scene: BossVenadoScene, boss: BossBase | None = None,
          boss_home: pygame.Vector2 | None = None, dt: float = DT) -> None:
    """One iteration of exactly what App.run()'s loop body does per frame,
    minus real-time pacing (app.clock.tick()) and input polling -- we drive
    dt manually so captures don't cost wall-clock seconds for nothing, and
    there is no real input device under SDL dummy anyway. The H-10 sync runs
    between update() and draw(), i.e. after the camera offset is final for
    this frame but before pyscroll's buffer is blitted from it. The boss pin
    (COMPENSATION 3) also sits between update() and draw()."""
    app.scene_manager.update(dt)
    _pin_boss(boss, boss_home)
    app.scene_manager.transition.update(dt)
    _sync_map_render(scene)
    app._draw()
    pygame.event.pump()


def _find_boss(scene: BossVenadoScene) -> BossBase | None:
    stage = scene._stage_data
    if stage is None:
        return None
    for entity in stage.entity_list:
        if isinstance(entity, BossBase):
            return entity
    return None


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    app = App()

    # (Former WORKAROUND 3 removed.) The BossVenado_01 constructor/TMX mismatch
    # was fixed at the source: gen_level_residencias.py no longer emits the stray
    # arena_origin_x/y properties, so App()'s ensure_registered() can keep
    # "BossVenado" registered and StageLoader.load() instantiates the boss
    # normally -- it now appears in the arena capture. Regression-guarded by
    # tests/test_map_residencias.py::test_entities_instantiate_from_tmx.
    scene = BossVenadoScene(app.context)
    app.scene_manager.push(scene)  # awake() -> start() -> on_enter(), same as SceneManager.push in main.py

    assert scene._player is not None, "on_enter() did not spawn a player"
    assert scene._stage_data is not None, "on_enter() did not load stage data"

    # CAPTURE-ONLY COMPENSATION 1 (CameraLock global switch, see module
    # docstring): empty the parsed CameraLock list on the already-loaded
    # StageData so Camera.set_camera_locks() -- re-read every frame from
    # StageScene.update() -- never sees a lock_x/lock_y=True entry.
    n_locks = len(scene._stage_data.camera_locks)
    scene._stage_data.camera_locks = []
    print(f"[capture] cleared {n_locks} CameraLock(s) from stage_data for this capture session")

    boss = _find_boss(scene)
    # snapshot the boss's spawn BEFORE any update() runs (its AI would relocate
    # it on frame 0 -- see _pin_boss / COMPENSATION 3); this is where the TMX puts
    # it and where the arena capture should show it.
    boss_home = pygame.Vector2(boss.position) if boss is not None else None
    print(f"[capture] scene loaded. player spawn={tuple(scene._player.position)} "
          f"boss={'found' if boss else 'MISSING'}"
          f"{' spawn=' + str(tuple(boss_home)) if boss else ''}")

    player = scene._player
    feet_offset = player.rect.height  # TMX Y is feet position; rect.y is top-left (see stage_loader.py)

    for name, world_x, feet_y in CAPTURES:
        player.position = pygame.Vector2(world_x, feet_y - feet_offset)
        player.velocity = pygame.Vector2(0.0, 0.0)
        player.rect.x = int(player.position.x)
        player.rect.y = int(player.position.y)

        for _ in range(SETTLE_FRAMES):
            _step(app, scene, boss, boss_home)

        out_path = OUT_DIR / f"ingame_{name}.png"
        pygame.image.save(app.internal_surface, str(out_path))

        boss = _find_boss(scene)  # re-fetch in case entity_list identity changed
        boss_info = "N/A"
        if boss is not None:
            boss_info = (
                f"state={boss.state.name} phase={boss.current_phase} "
                f"hp={boss.current_health}/{boss.phase_max_health} "
                f"pos={tuple(boss.position)}"
            )
        camera_locked = (scene._camera._is_locked_x, scene._camera._is_locked_y)
        print(
            f"[capture] {name} saved -> {out_path} size={app.internal_surface.get_size()} "
            f"player_pos={tuple(player.position)} player_feet_y={player.position.y + feet_offset} "
            f"camera_offset={tuple(scene._camera.offset)} camera_locked={camera_locked} "
            f"boss=[{boss_info}]"
        )


if __name__ == "__main__":
    main()
