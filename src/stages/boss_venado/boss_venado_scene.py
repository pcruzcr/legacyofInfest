"""Module: boss_venado_scene
System: stages.boss_venado — student scene for the Venado arena (Práctica I)
Academic Unit: IV — scene representation and camera policy
Description: The engine's CameraLock is a GLOBAL switch (camera.py:63-67 uses
    any() over the whole lock list and ignores each lock's rect). This scene
    compensates from the editable zone only: outside the arena the lock list
    is emptied so the camera follows the player; inside (x >= 2480) the TMX
    locks are restored so the camera stays fixed on the gazebo fight.

    H-10 compensation: StageScene.update() (stage_scene.py:605-610) writes
    the frame's camera offset straight into
    ``stage.map_layer._map_layer.view_rect`` — a plain pygame.Rect field that
    pyscroll's real blit path, ``BufferedRenderer._render_map()``, never
    reads (it reads ``_x_offset``/``_y_offset``/``_tile_view``/``_buffer``,
    which only ever change inside ``center()``). So camera.offset advances
    correctly and every entity (each draws itself via
    ``draw(surface, camera_offset)``) moves correctly relative to it, but the
    pyscroll tile BACKGROUND stays glued to wherever ``_initialize_buffers()``
    left it at load time. ``_sync_map_render()`` below calls the real public
    pyscroll API, ``stage.map_layer.center(...)`` (PyscrollGroup — see
    stage_loader.py:138 — forwards to the underlying BufferedRenderer), every
    frame after ``super().update(dt)`` has finalized the camera offset for
    this frame. Same fix pattern already proven in this same editable zone by
    tools/capture_map.py and tools/play_map.py (see their module docstrings,
    "COMPENSATION 2" / "PREVIEW COMPENSATION B") — reproduced here at the
    scene level so it applies to every entry point (main.py --boss
    boss_venado, the playtest harness), not just the two standalone viewers.

    Player halo: user playtest finding (2026-07-28) -- the hooded player
    sprite (near-black, RGB~15,20,35) camouflages against the dark foliage
    of the dusk palette, so the hero was hard to see on-screen. Fix: a
    screen-space additive moonlight halo drawn around the player every
    frame (thematic -- moon light, not a generic outline) via
    pygame.BLEND_RGB_ADD. Additive blending only ever brightens pixels
    underneath it, it never occludes, so it does not break the painter's
    draw order established elsewhere in this codebase (boss_venado.py's
    explicit painter's-order docstring) -- it's a lighting pass, not
    another sprite in the stack.

    H-02 engine bug compensation (hud.py ignores the phase param -- it only
    stores/renders phase_count, see HUD.set_boss_hud/_draw_boss_hud): remove
    if fixed. StageScene._update_hud_ui (stage_scene.py ~L1052-1057) calls
    ``set_boss_hud(name, health, max_health, phase, phase_count)`` every
    frame with ``phase_count = boss.phase_count`` (the TOTAL phase count,
    constant 2 for this boss), while ``HUD._draw_boss_hud`` renders
    ``f"PHASE {self._boss_phase_count}"`` -- i.e. it reads the phase_count
    slot as if it were the CURRENT phase, and the phase slot is stored
    nowhere and never read. Net effect: the label reads "PHASE 2" for the
    entire duration of phase 0. ``_compensate_boss_hud_phase`` below re-calls
    the HUD's own public ``set_boss_hud`` API AFTER ``super().update(dt)``
    (so it runs after the engine's own call for this frame and wins),
    passing the CURRENT 1-indexed phase in the ``phase_count`` slot -- the
    one the renderer actually reads. See reports/FINDINGS.md H-02 for the
    full forensic trail (this same pattern was proven pre-reset).

    H-17 arena camera pin (human playtest bug, 2026-07-30): ``Camera``
    (camera.py, unchanged between motor V1 and V2 -- verified byte-for-byte
    identical logic, only two cosmetic renames) never reads a lock's
    ``.rect`` -- ``set_camera_locks()`` only flips ``_is_locked_x/y`` and
    ``update()`` then simply stops writing ``offset`` on a locked axis,
    freezing it wherever it already was (see camera.py `update()`/
    `set_camera_locks()`). ``_locks_for_player_x`` above restores the TMX
    locks the instant ``player.centerx >= ARENA_X0``, but the follow-camera
    is still mid-lerp at that exact instant -- headless repro (walking, not
    teleporting, from ``PLAYER_SPAWN``) measured the freeze landing at
    ``offset.x == 2102.87`` the frame the lock engages (f1377,
    player.x=2482), i.e. the right edge froze at ``2902.87`` instead of the
    map's true edge at ``3280`` (``offset.x`` needs to be exactly
    ``ARENA_X0`` == ``map_w - INTERNAL_WIDTH`` == 2480 for the arena to
    fill the viewport) -- this is the "camera doesn't reach the end of the
    gazebo" bug. This exact problem (and this exact fix shape) was already
    solved once, pre-reset -- see
    ``backups/pre-reset-2026-07-21/src/boss_venado_scene.py``'s
    ``ARENA_RECT``/``_arena_engaged`` latch and its docstring, which documents
    trying a hard snap first and rejecting it: it produced a ~400px
    "border-jump" hard cut in screen_x for one frame. `_pin_camera_to_arena`
    below reproduces that proven shape adapted to this scene's current
    toggle-based lock policy (no permanent latch, no entrance-sealing wall
    -- both were pre-reset-only design choices this rewrite intentionally
    doesn't have, see the no_damage_outside_arena regression gate in
    playtest/invariants.py, which depends on the player being able to walk
    back out of the arena mid-fight): the instant ``player.centerx`` crosses
    ``ARENA_X0``, it eases ``camera.offset`` from wherever the follow-camera
    currently sits to the arena's exact target view over
    ``ARENA_SETTLE_DURATION`` seconds (ease-in-out), then pins it there
    explicitly EVERY frame for as long as the player stays inside -- so the
    final offset is always exactly right regardless of walk speed,
    entry/exit toggling, or engine lock quirks, and leaving the arena simply
    stops the override and lets the inherited follow-lerp resume untouched.
"""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pygame

from src.engine.core import settings
from src.engine.utils.math_utils import ease_in_out_quad, lerp
from src.framework.entities.boss_base import BossBase
from src.framework.scenes.stage_scene import StageScene

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext

ARENA_X0 = 2480.0  # keep in sync with boss_venado.ARENA_X0 (CameraLock_01 left edge)

# H-17: how long (seconds) the camera takes to ease from wherever the
# follow-camera sits to the arena's pinned frame once the player crosses
# ARENA_X0 -- see _pin_camera_to_arena / the module docstring's H-17 section.
# Same value the pre-reset reference used (backups/pre-reset-2026-07-21).
ARENA_SETTLE_DURATION = 0.3

PLAYER_HALO_RADIUS = 44   # px; halo surface is (2*RADIUS, 2*RADIUS)
PLAYER_HALO_PEAK = 46     # max additive brightness at the halo's center
PLAYER_HALO_TINT = (46, 52, 66)   # cold moonlight tint at peak brightness (r channel == PLAYER_HALO_PEAK)


class BossVenadoScene(StageScene):
    STAGE_ID: str = "boss_venado"
    STAGE_NAME: str = "VENADO"
    ZONE: int = 1  # Zone 1 (Stage 1-4) per 17_BOSS_SPEC §3.1; attribute unused by the engine, kept coherent with README front-matter

    def __init__(self, context: GameContext) -> None:
        super().__init__(context, Path("assets/maps/boss_venado/boss_venado.tmx"))
        self._original_camera_locks: list = []
        self._player_halo: pygame.Surface | None = None   # lazy-cached, built on first draw()
        # H-17 arena camera pin (see module docstring): transient ease state,
        # NOT a permanent latch -- re-armed every time player_x crosses back
        # below ARENA_X0, so re-entering re-eases cleanly instead of hard-cutting.
        self._in_arena_prev: bool = False
        self._arena_ease_elapsed: float = ARENA_SETTLE_DURATION  # start "settled"
        self._arena_ease_start: pygame.Vector2 = pygame.Vector2(0.0, 0.0)

    def on_enter(self) -> None:
        super().on_enter()
        if self._stage_data is not None:
            self._original_camera_locks = list(self._stage_data.camera_locks)
        # H-06-style reset (see boss-venado FINDINGS H-06): on_enter() is
        # replayed verbatim by respawn(), which rebuilds a fresh Camera at
        # offset (0, 0) -- a stale True here would skip the ease and pin the
        # fresh camera to the arena on frame 1 even though the player just
        # respawned back at the level's PlayerSpawn, outside the arena.
        self._in_arena_prev = False
        self._arena_ease_elapsed = ARENA_SETTLE_DURATION
        self._arena_ease_start.update(0.0, 0.0)

    @staticmethod
    def _locks_for_player_x(player_x: float, original_locks: list) -> list:
        """Pure zone policy: empty outside the arena, original locks inside."""
        return original_locks if player_x >= ARENA_X0 else []

    def _get_boss(self) -> BossBase | None:
        """Playtest Recorder contract: expose the live boss entity."""
        if self._stage_data is None:
            return None
        for entity in self._stage_data.entity_list:
            if isinstance(entity, BossBase):
                return entity
        return None

    def _arena_target_offset(self) -> tuple[float, float]:
        """H-17 (see module docstring): the offset that frames the arena
        exactly -- x = ARENA_X0 (the arena is exactly one INTERNAL_WIDTH
        viewport wide, by map design: map_w - ARENA_X0 == 800 ==
        INTERNAL_WIDTH), y = the map's own bottom clamp (mirrors
        Camera.update()'s own ``max(0.0, min(offset.y, map_h - screen_h))``
        clamp, so this never fights that clamp on axes CameraLock_01 doesn't
        actually need pinned)."""
        stage = self._stage_data
        map_h = stage.map_pixel_size[1] if stage is not None else settings.INTERNAL_HEIGHT
        target_y = max(0.0, float(map_h) - settings.INTERNAL_HEIGHT)
        return ARENA_X0, target_y

    def _pin_camera_to_arena(self, dt: float, in_arena: bool) -> None:
        """H-17 (see module docstring): explicitly drive camera.offset to the
        arena's exact framing while the player is inside, instead of relying
        on Camera's lock-freezes-wherever-it-is semantics. Must run AFTER
        super().update(dt) (so it has the final say for this frame, same
        ordering constraint the H-02 HUD compensation already documents) and
        BEFORE _sync_map_render() (so pyscroll's background centers on the
        pinned offset, not the pre-pin one). Uses ``getattr`` (not a plain
        ``self._camera``) so it degrades to a no-op on the bare
        ``BossVenadoScene.__new__(...)`` test doubles this file's sibling
        unit-test module hand-wires without a real ``__init__`` (see
        test_boss_scene.py's ``_bare_scene_with_boss``), same defensive
        style ``_compensate_boss_hud_phase``'s ``self._hud is None`` guard
        already relies on."""
        if getattr(self, "_camera", None) is None:
            return
        if not in_arena:
            self._in_arena_prev = False
            return
        target_x, target_y = self._arena_target_offset()
        if not self._in_arena_prev:
            # Just crossed ARENA_X0 this frame (or re-entered after leaving):
            # start a fresh ease from wherever the follow-camera currently
            # sits -- snapping produces the ~400px "border-jump" hard cut
            # the pre-reset reference already fought and rejected (see
            # backups/pre-reset-2026-07-21/src/boss_venado_scene.py).
            self._arena_ease_elapsed = 0.0
            self._arena_ease_start.update(self._camera.offset)
            self._in_arena_prev = True
        if self._arena_ease_elapsed < ARENA_SETTLE_DURATION:
            self._arena_ease_elapsed += dt
            t = min(1.0, self._arena_ease_elapsed / ARENA_SETTLE_DURATION)
            eased_t = ease_in_out_quad(t)
            self._camera.offset.x = lerp(self._arena_ease_start.x, target_x, eased_t)
            self._camera.offset.y = lerp(self._arena_ease_start.y, target_y, eased_t)
            if t >= 1.0:
                # Land exactly on target (floating-point lerp at t==1.0
                # already does this, but pin explicitly so nothing downstream
                # ever sees an off-by-epsilon offset).
                self._camera.offset.x = target_x
                self._camera.offset.y = target_y
        # else: the ease already finished on an earlier frame -- deliberately
        # NOT re-writing offset here every frame. `stage.camera_locks` is
        # already the (non-empty) TMX locks while in_arena (see update()), so
        # Camera's own lock-freeze (camera.py update()/set_camera_locks(),
        # see the module docstring's H-17 section) now holds offset.x/y at
        # exactly target_x/target_y on its own -- nothing else writes to a
        # locked axis except apply_shake()'s screen-shake offset, which
        # Camera.update() adds AND removes symmetrically every frame
        # (`offset -= self._shake_offset` then recompute then
        # `offset += self._shake_offset`), so it nets to zero drift on its
        # own. Unconditionally overwriting offset here every frame (the
        # pre-reset reference's approach -- see the module docstring) would
        # silently cancel that shake for the entire rest of the fight, e.g.
        # every VFX_SLAM/VFX_ULTIMATE/player-hit screen shake StageScene
        # applies while the player is in the arena.

    @staticmethod
    def _build_player_halo() -> pygame.Surface:
        """Pure builder (no scene state) for the moonlight halo -- see module
        docstring. Concentric circles from the outer radius inward, each one
        drawn a little brighter than the last, produce a cheap radial
        gradient: PLAYER_HALO_TINT (scaled to PLAYER_HALO_PEAK) at the
        center, fading linearly to black (RGB_ADD no-op) at the rim. Callers
        should build this ONCE and cache the result (see draw() below) --
        this function itself does no caching."""
        size = PLAYER_HALO_RADIUS * 2
        halo = pygame.Surface((size, size))
        center = (PLAYER_HALO_RADIUS, PLAYER_HALO_RADIUS)
        for radius in range(PLAYER_HALO_RADIUS, 0, -1):
            # 0.0 at the rim (radius == PLAYER_HALO_RADIUS) -> ~1.0 near the center.
            brightness = 1.0 - (radius / PLAYER_HALO_RADIUS)
            color = tuple(int(channel * brightness) for channel in PLAYER_HALO_TINT)
            pygame.draw.circle(halo, color, center, radius)
        return halo

    def _sync_map_render(self) -> None:
        """H-10 compensation (see module docstring): call pyscroll's real
        center() so the tile background actually follows camera.offset
        instead of staying glued to the initial buffer window. Defensively
        no-ops if stage/map_layer aren't ready yet."""
        stage = self._stage_data
        if stage is None:
            return
        map_layer = getattr(stage, "map_layer", None)
        if map_layer is None:
            return
        offset = self._camera.offset
        map_layer.center((
            offset.x + settings.INTERNAL_WIDTH / 2,
            offset.y + settings.INTERNAL_HEIGHT / 2,
        ))

    def _compensate_boss_hud_phase(self) -> None:
        """H-02 engine bug compensation (hud.py ignores the phase param --
        it only stores/renders phase_count; see the module docstring's
        H-02 section for the full forensic trail): remove if fixed.

        No-ops if there is no HUD yet (before on_enter()/pre-boot) or no
        live boss (corridor before the fight, or after the death sequence
        finishes and StageScene's own ``clear_boss_hud()`` takes over)."""
        boss = self._get_boss()
        if boss is None or not boss.is_alive or self._hud is None:
            return
        current_phase_1indexed = boss.current_phase + 1
        self._hud.set_boss_hud(
            boss.boss_name, boss.current_health, boss.phase_max_health,
            current_phase_1indexed, current_phase_1indexed,
        )

    def update(self, dt: float) -> None:
        in_arena = False
        if self._stage_data is not None and self._player is not None:
            in_arena = float(self._player.rect.centerx) >= ARENA_X0
            self._stage_data.camera_locks = (
                self._original_camera_locks if in_arena else [])
        super().update(dt)
        self._compensate_boss_hud_phase()
        # H-17 (see module docstring): must run AFTER super().update(dt) (so
        # it has the final say over camera.offset for this frame) and BEFORE
        # _sync_map_render() (so pyscroll centers on the pinned offset).
        self._pin_camera_to_arena(dt, in_arena)
        self._sync_map_render()

    def draw(self, surface: pygame.Surface) -> None:
        """Player halo (see module docstring): drawn AFTER the engine's own
        draw() so it lands on top of the fully-composited frame, screen-space,
        additive -- it brightens the hero and the foliage right around them
        without occluding anything already painted, so it doesn't disturb the
        painter's order the rest of the stage/entities already establish."""
        super().draw(surface)
        if self._player is not None and self._camera is not None:
            if self._player_halo is None:
                self._player_halo = self._build_player_halo()
            offset = self._camera.offset
            top_left = (
                self._player.rect.centerx - offset.x - PLAYER_HALO_RADIUS,
                self._player.rect.centery - offset.y - PLAYER_HALO_RADIUS,
            )
            surface.blit(self._player_halo, top_left, special_flags=pygame.BLEND_RGB_ADD)
