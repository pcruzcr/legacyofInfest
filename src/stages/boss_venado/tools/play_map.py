"""
Module: play_map
System: stages.boss_venado.tools
Description: PLAYABLE (real window, real input) in-engine viewer for the
"Residencias al Crepusculo" boss arena map -- the human-playable counterpart
to ``capture_map.py`` in this same directory. Where ``capture_map.py`` boots
the real App headlessly and teleports the player to fixed x positions for
screenshots, this tool boots the SAME real App/scene pipeline but opens an
actual OS window, runs a REAL 60 FPS game loop (``DeltaClock``/``pygame.time.
Clock`` real-time pacing, not manually-stepped dt), and lets the user walk
the map with the engine's own controls (arrows/A-D to move, SPACE/UP/W to
jump -- ``src/engine/input/action_map.py`` DEFAULT_KEY_BINDINGS, unmodified).
Movement/physics/collision are handled entirely by the real code path
main.py uses (``InputManager.pump`` -> ``EventBus.dispatch`` ->
``SceneManager.update`` -> ``StageScene.update`` -> ``Player.update(dt,
collision_rects, input_manager)``) -- this tool never reads or writes the
player's position/velocity itself; see ``_frame`` below.

PREVIEW DE FASE 2 -- this tool carries forward the exact same two per-frame,
capture-tool-only compensations that ``capture_map.py`` documents at length
(read that module's docstring for the full technical rationale, links to
``reports\\map_residencias\\CAMERALOCK.md`` and ``reports\\FINDINGS.md`` H-10,
and the architect approval). Summary, reproduced here because a human at the
keyboard needs BOTH to actually see themselves move through the arena instead
of a frozen/stale view:

  PREVIEW COMPENSATION A -- CameraLock global switch: the TMX's
  CameraLock_01 (see ``ArenaZone_01``/``CameraLock_01`` at x=1600 in
  boss_venado.tmx) freezes BOTH camera axes for the ENTIRE stage from frame 0
  (``Camera.set_camera_locks()`` does not gate on the lock's rect, a known
  engine bug). Compensation: empty ``scene._stage_data.camera_locks`` right
  after the scene is pushed, once, at startup.

  PREVIEW COMPENSATION B -- H-10: ``StageScene`` never calls pyscroll's real
  ``BufferedRenderer.center()``, so the tile BACKGROUND art stays glued to the
  spawn corner forever while entities (drawn separately) move correctly with
  ``camera.offset``. Compensation: every frame, between
  ``scene_manager.update()`` (camera offset final for the frame) and
  ``app._draw()`` (pyscroll blits from it), call the real
  ``stage.map_layer.center((camera.offset.x + W/2, camera.offset.y + H/2))``.

  PREVIEW COMPENSATION C -- boss AI arena-clamp bug (capture_map's
  COMPENSATION 3): the professor's original ``BossVenado`` movement AI uses a
  320-scale arena constant (``ARENA_W = 320``) against WORLD coordinates, so
  on its very first ``update()`` it flings itself from its TMX spawn (see
  ``BossVenado_01`` in boss_venado.tmx) out to world x~44, out of the arena.
  Out of scope for a MAP viewer (logged in FINDINGS.md). This tool snapshots
  the boss's actual spawn position (``boss.position``) right after the scene
  loads -- BEFORE any ``update()`` has a chance to move it -- and re-pins the
  boss to THAT snapshot every frame, same pattern as capture_map.py's
  ``_pin_boss``/``boss_home``, so it stays visible wherever the TMX places it
  (previously this was a stale hardcoded (2000, 240) coordinate, wrong since
  the map's round-11/round-12 widening moved the real spawn -- see FINDINGS).

None of these three touch src/engine, src/framework, or the TMX -- all three
mutate already-constructed runtime objects (StageData, PyscrollGroup, the
boss entity) from outside, through their existing public API/fields, exactly
like capture_map.py does. They are documented as "preview of phase 2" because
the real fix (making Camera/StageScene/the boss AI correct) is out of scope
for a map-viewing tool and belongs to later boss-AI/engine-bridge work.

REAL WINDOW, NOT DUMMY: unlike capture_map.py, this tool wants an actual OS
window, so it force-sets SDL_VIDEODRIVER to "windows" -- NOT ``setdefault``
-- but ONLY when launched as the script itself (``if __name__ ==
"__main__"``). This matters because ``tests/conftest.py`` hard-sets
``os.environ["SDL_VIDEODRIVER"] = "dummy"`` for the whole pytest session, and
PowerShell env vars persist across commands typed into the SAME shell
session (unlike a fresh subprocess env) -- so a shell that recently ran
pytest could otherwise silently leak "dummy" into this tool and produce a
window-less run even though a real window was requested. Guarding the force
behind ``__name__ == "__main__"`` means: run directly -> always get a real
window regardless of what leaked in; imported as a module (this project's own
smoke test does exactly that, setting SDL_VIDEODRIVER=dummy itself BEFORE
importing this module) -> the import is a no-op on the env var, so the smoke
test stays headless. SDL_AUDIODRIVER is left untouched either way -- a real
play session should get real audio like main.py does; the smoke test doesn't
call App() long enough to hit anything but pygame.mixer.init() (harmless
under whatever driver is already active in that process).

Usage (from the LAB's ``game`` directory, real window/audio):

    path\\to\\python.exe src\\stages\\boss_venado\\tools\\play_map.py

Controls: arrows or A/D to move, SPACE/UP/W to jump (engine defaults, see
``src/engine/input/action_map.py``). ESC or closing the window exits
cleanly. (Note: ESC is ALSO bound to Action.PAUSE/CANCEL, which
StageScene.update() uses to open its own in-game pause menu -- that still
happens, in parallel, since the same real events are fed to InputManager;
this tool additionally watches the raw ESC keydown itself, independent of
the scene, to guarantee the viewer window always closes on ESC per this
tool's own spec, rather than only surfacing a pause menu the tester would
then have to navigate out of.)

VERIFICATION: because this tool wants a real window, it can't be exercised
end-to-end by an automated smoke test without one. What CAN be, and is
covered by this project's own headless smoke check (SDL dummy, run from the
LAB, not committed -- see ``reports\\FINDINGS.md`` / session notes for the
exact command), is that the frame-stepping function below (``_frame``),
which is the one and only thing that runs every frame and is unique to this
tool (everything else is either identical to capture_map.py or is the
standard App/SceneManager real-loop wiring), correctly lets synthetic
KEYDOWN input reach the real Player through the real InputManager/EventBus/
SceneManager pipeline and that the two camera compensations keep
``camera.offset`` following the player -- i.e. that this file's own logic,
not pygame's window/event system, is correct.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Force a REAL SDL video driver, but only when this file is executed as the
# script itself -- see "REAL WINDOW, NOT DUMMY" in the module docstring for
# why this must NOT be a blanket process-wide setting and NOT `setdefault`.
if __name__ == "__main__":
    os.environ["SDL_VIDEODRIVER"] = "windows"

# tools/ -> boss_venado/ -> stages/ -> src/ -> game/ (LAB game root, the
# equivalent of legacyofInfest/ in the real project). Same layout constant
# as capture_map.py.
_GAME_ROOT = Path(__file__).resolve().parents[4]
os.chdir(_GAME_ROOT)  # StageLoader.load() resolves the TMX path relative to cwd.
sys.path.insert(0, str(_GAME_ROOT))

import pygame  # noqa: E402

from src.engine.core import settings  # noqa: E402
from src.engine.core.app import App  # noqa: E402
from src.framework.entities.boss_base import BossBase  # noqa: E402
from src.stages.boss_venado.boss_venado_scene import BossVenadoScene  # noqa: E402


def _sync_map_render(scene: BossVenadoScene) -> None:
    """PREVIEW COMPENSATION B (H-10, see module docstring): call pyscroll's
    real ``center()`` API so the tile background actually follows
    ``camera.offset`` instead of staying glued to the initial buffer window.
    Verbatim logic to capture_map.py's ``_sync_map_render``."""
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
    """PREVIEW COMPENSATION C (boss AI arena-clamp bug, see module
    docstring): hold the boss at its TMX spawn every frame, after the scene's
    own update() has (mis)moved it and before draw(). Verbatim logic to
    capture_map.py's ``_pin_boss`` -- ``home`` is a snapshot of the boss's
    REAL spawn position taken dynamically in ``setup()``, not a hardcoded
    coordinate, so it always matches wherever the current TMX places it."""
    if boss is None or home is None:
        return
    boss.position.update(home)
    boss.rect.x = int(home.x)
    boss.rect.y = int(home.y)
    if hasattr(boss, "velocity"):
        boss.velocity.update(0.0, 0.0)


def _find_boss(scene: BossVenadoScene) -> BossBase | None:
    stage = scene._stage_data
    if stage is None:
        return None
    for entity in stage.entity_list:
        if isinstance(entity, BossBase):
            return entity
    return None


def _poll_events() -> tuple[list[pygame.event.Event], bool]:
    """Poll the real event queue for this frame. Returns (events,
    quit_requested); quit_requested is True on window-close (QUIT) or a raw
    ESC keydown -- this tool's own clean-exit hotkey (see module docstring
    re: ESC also being Action.PAUSE/CANCEL, handled separately/normally by
    the scene once these events are fed to InputManager in ``_frame``)."""
    events = pygame.event.get()
    quit_requested = any(
        e.type == pygame.QUIT
        or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE)
        for e in events
    )
    return events, quit_requested


def _frame(
    app: App,
    scene: BossVenadoScene,
    boss: BossBase | None,
    boss_home: pygame.Vector2 | None,
    events: list[pygame.event.Event],
    dt: float,
) -> None:
    """One iteration of the real game loop body -- the same pipeline
    App.run() drives (input -> dispatch -> update -> draw), reproduced here
    (instead of calling app.run() directly) only because the two per-frame
    compensations must run BETWEEN scene_manager.update() [camera offset
    final for the frame] and app._draw() [pyscroll blits from it], a point
    app.run() has no hook for. Movement/physics/collision are entirely the
    engine's own: this function feeds real events through InputManager same
    as App._process_events(), then lets SceneManager/StageScene/Player do
    everything they normally do -- it does not read or write player state."""
    app.input_manager.pump(events)
    app.event_bus.dispatch()
    app.scene_manager.update(dt)
    _pin_boss(boss, boss_home)
    app.scene_manager.transition.update(dt)
    _sync_map_render(scene)
    app._draw()


def setup() -> tuple[App, BossVenadoScene, BossBase | None, pygame.Vector2 | None]:
    """Boot the real App, push BossVenadoScene (identical to capture_map.py's
    startup sequence), apply PREVIEW COMPENSATION A once, locate the boss and
    snapshot its spawn. Split out from main() so a headless smoke test can
    drive frames directly without opening a real window."""
    app = App()
    scene = BossVenadoScene(app.context)
    app.scene_manager.push(scene)  # awake() -> start() -> on_enter(), same as main.py

    assert scene._player is not None, "on_enter() did not spawn a player"
    assert scene._stage_data is not None, "on_enter() did not load stage data"

    # PREVIEW COMPENSATION A (CameraLock global switch, see module
    # docstring): empty the parsed CameraLock list on the already-loaded
    # StageData so Camera.set_camera_locks() -- re-read every frame from
    # StageScene.update() -- never sees a lock_x/lock_y=True entry.
    n_locks = len(scene._stage_data.camera_locks)
    scene._stage_data.camera_locks = []
    print(f"[play_map] cleared {n_locks} CameraLock(s) from stage_data for this session")

    boss = _find_boss(scene)
    # Snapshot the boss's spawn BEFORE any update() runs (its AI would relocate
    # it on frame 0 -- see PREVIEW COMPENSATION C / _pin_boss): this is where
    # the CURRENT TMX puts it, read dynamically instead of a hardcoded
    # coordinate that would go stale the next time the map is edited.
    boss_home = pygame.Vector2(boss.position) if boss is not None else None
    print(
        f"[play_map] player spawn={tuple(scene._player.position)} "
        f"boss={'found' if boss else 'MISSING'}"
        f"{' spawn=' + str(tuple(boss_home)) if boss is not None else ''}"
    )
    return app, scene, boss, boss_home


def main() -> None:
    app, scene, boss, boss_home = setup()
    print("[play_map] window open -- move: arrows/A-D, jump: SPACE/UP/W, exit: ESC or close window")

    running = True
    while running and app.context.running:
        dt = app.clock.tick()  # real-time pacing at settings.TARGET_FPS (60)
        events, quit_requested = _poll_events()
        if quit_requested:
            running = False
            break
        _frame(app, scene, boss, boss_home, events, dt)
        pygame.display.flip()

    app._shutdown()
    print("[play_map] closed.")


if __name__ == "__main__":
    main()
