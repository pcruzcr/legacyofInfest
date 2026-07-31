"""
Module: gen_level_residencias
System: tools (map composition)
Description: Composes the full "Residencias al Crepusculo" boss level TMX
    (205x38 tiles, 3280x608 px, side-scroller, 16x16 tiles). This is the level
    COMPOSITOR: it arranges the named tiles produced by ``gen_tileset_residencias``
    into eight ordered layers plus two object groups, following the approved
    twilight vignette (``art_proof.png`` / ``concept_master.png``, 2026-07-23) and
    the TMX contract of ``docs/06_TMX_SPEC.md``.

Design rules (hard constraints from the spec)
--------------------------------------------
- Everything is anchored to the ground: the walkable surface is row 35 (y=560),
  the visual ground body spans rows 35-37, and every structure rests its bottom
  tile on row 34 (its feet at y=560). Nothing structural floats.
- Four zones by tile column (round-11 widening + the new carport, user feedback
  "extender aun mas el mapa, cada zona un poco mas extensa, y hacer el lugar
  donde estaban los carros"): PRADERA [0,65) (a longer winding dirt path, two
  big trees, distant bungalows with lit/boarded windows, fallen fence,
  clothesline); CARPORT [65,95) (a dark corrugated carport on black metal posts
  over a gravel bay, a silver sedan + white pickup parked under it and an orange
  loader-tractor beside it, all dusk-silhouetted); ARCOS [95,155) (two passable
  hastial arches spaced wider so the telescope of a distant arch between them
  breathes, a continuous seto/patio treeline between them, near stone reveals in
  FG_Overlay so the player walks THROUGH each doorway, a leaning lamp and a
  broken bench); ARENA [155,205) (the lawn esplanade with the 7x6 gazebo, its
  stone plaza, hedges, fireflies and drifting leaves, where the boss is fought).
- The tileset is referenced with ``trans="000000"`` so the pure-black "visual
  empty" pixels of overlay/structure tiles read as transparent; this is what
  lets props, hedges, fireflies, the gazebo interior and the arch faces composite
  over the sky/ground instead of stamping black boxes.

Output (idempotent; ``main()`` may be called repeatedly, byte-stable)
--------------------------------------------------------------------
- ``<game>/assets/maps/boss_venado/boss_venado.tmx``
"""
from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from src.stages.boss_venado.tools.gen_tileset_residencias import NAME_TO_INDEX

# ---------------------------------------------------------------------------
# Paths / map constants (derived from __file__ so cwd never matters)
# ---------------------------------------------------------------------------
_HERE = Path(__file__).resolve()
GAME_ROOT = _HERE.parents[4]                     # .../game
OUT_TMX = GAME_ROOT / "assets" / "maps" / "boss_venado" / "boss_venado.tmx"

W, H = 205, 38                                    # map size in tiles (round-11 widening)
TILE = 16
FIRSTGID = 1
TILECOUNT = len(NAME_TO_INDEX)                    # single source of truth (imported atlas)
COLUMNS = 12
TILESET_NAME = "tileset_residencias_crepusculo"
TILESET_IMG = "../../tilesets/tileset_residencias_crepusculo.png"
# ROUND-10 FIX (root cause of "kiosco cortado"): DERIVE the declared image height
# from the actual tile count so it always matches the atlas the tileset generator
# emits. It had been hardcoded at 240 (15 rows) since early rounds while the atlas
# grew to 19 rows (304 px). pytmx slices a tileset by its DECLARED <image height>,
# so EVERY tile in atlas row >= 15 (gid index >= 180) -- the gazebo's bottom two
# rows (stone bases, pad, table silhouette, the r8 light pool) AND the new plaza --
# was silently DROPPED at render time, leaving sky-void under the kiosk. Deriving
# the height (rounding the tile count up to whole rows) fixes rendering for good.
TILESET_W = COLUMNS * TILE                        # 192 (12 cols x 16 px)
TILESET_H = ((TILECOUNT + COLUMNS - 1) // COLUMNS) * TILE   # whole rows to fit every tile

GROUND_ROW = 35                                   # walkable surface row (y=560)
SUB_ROWS = (36, 37)                               # underground fill rows
BASE_ROW = 34                                     # structures' bottom tile row

# Zone boundaries in tile columns. These are the ONE source of truth for where a
# zone starts/ends: the ground surface thresholds and every structure's ``col0``
# are derived from them (e.g. ARCOS.start + 4), so shifting a zone is one edit.
# NOTE: a handful of fine-tuned DECORATIVE positions that were nudged for balance
# stay absolute within their zone (the arena firefly swarm coordinates, and the
# fence/clothesline pixel spans) - they cannot be "reasonably derived" from a
# boundary and are marked at their use sites.
PRADERA = range(0, 65)
CARPORT = range(65, 95)                           # round-11: "el lugar donde estaban los carros"
ARCOS = range(95, 155)
ARENA = range(155, 205)

# ROUND-8 (user feedback: the gazebo -- the arena set-piece -- is "poco visible",
# its lit body fusing with the dark woods behind). A cleared GLADE is opened
# around the gazebo so its roof+lit-body silhouette reads against the OPEN dusk
# sky/meadow instead of a crowding treeline. The gazebo block is 7 wide at
# ARENA.start+22 (cols 177-183 after the round-11 shift); the glade opens ~4 cols
# each flank, with a 2-col low-mound SHOULDER softening each edge so it reads as a
# clearing in the woods (not a hard rectangular hole) and the round-5/6
# clump-and-gap rhythm resumes beyond it. Only consulted inside ARENA (>= 171).
_GAZEBO_C0 = ARENA.start + 22                                       # 177 (gazebo left col)
_GAZEBO_C1 = _GAZEBO_C0 + 6                                         # 183 (gazebo right col)
_ARENA_GAZEBO_GLADE = range(_GAZEBO_C0 - 4, _GAZEBO_C1 + 5)         # 173..187: no tall clumps
_ARENA_GLADE_SHOULDER = (set(range(_GAZEBO_C0 - 6, _GAZEBO_C0 - 4))  # 171-172 low-mound shoulders
                         | set(range(_GAZEBO_C1 + 5, _GAZEBO_C1 + 7)))  # 188-189 low-mound shoulders

# ROUND-9 (user: "el retoque está bien, le falta que no lo tapen los arbustos del
# fondo"). The continuous ground-line green strip (the meadow band at rows 33-34)
# plus the FG grass tufts were burying the gazebo's stone bases, post feet and
# doorway. Its FOOTPRINT -- the 7 gazebo cols + 2 of margin each side -- is kept
# CLEAR of the meadow band AND of the FG grass tufts, so the set-piece stands on
# clean floor (its own cream stone bases + the r7 lit turf at row 35 below) with
# open dusk sky at its immediate flanks: nothing sprouts in front of the doorway.
# The rest of the arena keeps its meadow/tufts (rhythm). Only ever ARENA (>=120).
_GAZEBO_FOOTPRINT = range(_GAZEBO_C0 - 2, _GAZEBO_C1 + 3)          # 175..185

# ROUND-11 (user: "hacer el lugar donde estaban los carros"). The carport is a
# 10-col dark corrugated roof on black metal posts over a dark gravel bay, with a
# silver sedan + white pickup parked under it and an orange loader-tractor beside
# it. Like the gazebo, a cleared GLADE is opened around it so its dark silhouette
# reads against the OPEN dusk sky/horizon instead of a crowding treeline, and the
# gravel bay replaces the meadow band along its footprint. All positions derive
# from CARPORT.start so the whole assembly moves with its zone.
_CARPORT_C0 = CARPORT.start + 6                                    # 71 (roof left col)
_CARPORT_ROOF_W = 10
_CARPORT_C1 = _CARPORT_C0 + _CARPORT_ROOF_W - 1                    # 80 (roof right col)
_CARPORT_POSTS = (_CARPORT_C0, _CARPORT_C0 + 5, _CARPORT_C1)       # 71, 76, 80
_CARPORT_GRAVEL = range(_CARPORT_C0 - 1, _CARPORT_C1 + 4)          # 70..83 (bay + tractor apron)
_CARPORT_GLADE = range(_CARPORT_C0 - 2, _CARPORT_C1 + 6)           # 69..85 open sky behind it

Layer = list[list[str | None]]


# ---------------------------------------------------------------------------
# Low-level grid helpers
# ---------------------------------------------------------------------------
def _blank() -> Layer:
    """A fresh HxW grid of empty cells (None -> gid 0)."""
    return [[None for _ in range(W)] for _ in range(H)]


def _gid(name: str) -> int:
    """GID of a named tile: atlas index + firstgid (0 stays reserved as empty)."""
    try:
        return NAME_TO_INDEX[name] + FIRSTGID
    except KeyError:
        raise KeyError(f"unknown tile name '{name}'") from None


def put(layer: Layer, x: int, y: int, name: str) -> None:
    """Set a single cell, silently clipping to the map bounds."""
    if 0 <= x < W and 0 <= y < H:
        layer[y][x] = name


def hband(layer: Layer, y0: int, y1: int, name: str, x0: int = 0, x1: int = W) -> None:
    """Fill rows [y0, y1) across columns [x0, x1) with a single tile."""
    for y in range(y0, y1):
        for x in range(x0, x1):
            put(layer, x, y, name)


def pick(options: list[str], x: int, y: int) -> str:
    """Deterministic variant chooser (pure function of position -> idempotent)."""
    return options[(x * 7 + y * 13) % len(options)]


def place_block(
    layer: Layer,
    prefix: str,
    cols: int,
    rows: int,
    col0: int,
    row0: int,
    sep: str = "_",
    skip: set[tuple[int, int]] | None = None,
) -> None:
    """Stamp a (cols x rows) named tile block with its top-left at (col0, row0).

    Cells are named ``{prefix}{sep}{c}{r}`` (column digit first), matching the
    inventory produced by ``register_block`` (e.g. a 7x6 gazebo's bottom-right
    is ``gaz_65``; a tree uses ``sep=""`` -> ``tree_c33``). ``skip`` omits block
    cells given as ``(c, r)`` pairs (used to punch the passable arch openings).

    A block must fit entirely on the map: unlike ``put`` (which silently clips
    loose tiles), a block that runs off the edge is a composition error and
    raises, so a mis-placed multi-tile structure fails loudly instead of tiling
    back a sliced sprite.
    """
    if col0 < 0 or row0 < 0 or col0 + cols > W or row0 + rows > H:
        raise ValueError(
            f"block '{prefix}' at ({col0},{row0}) size {cols}x{rows} exceeds map {W}x{H}"
        )
    skip = skip or set()
    for c in range(cols):
        for r in range(rows):
            if (c, r) in skip:
                continue
            put(layer, col0 + c, row0 + r, f"{prefix}{sep}{c}{r}")


def place_hedge_column(layer: Layer, x0: int, x1: int, r_top: int) -> None:
    """A jardinera/hedge mass from crown row ``r_top`` down to the ground (BASE_ROW).

    Used as coherent, ground-anchored visual support beneath one-way platforms.
    """
    for x in range(x0, x1):
        put(layer, x, r_top, pick(["hedge_top_a", "hedge_top_b"], x, r_top))
        for y in range(r_top + 1, BASE_ROW + 1):
            name = "hedge_flower" if (x + y) % 7 == 0 else "hedge_fill"
            put(layer, x, y, name)


def place_bench(layer: Layer, x: int) -> None:
    """A two-tile broken bench prop resting on the ground at columns x..x+1."""
    put(layer, x, BASE_ROW, "bench_broken_l")
    put(layer, x + 1, BASE_ROW, "bench_broken_r")


def scatter_leaves(layer: Layer, xs: Iterable[int]) -> None:
    """Drop drifting-leaf tiles on the ground at each column in ``xs``."""
    for x in xs:
        put(layer, x, BASE_ROW, pick(["leaves_drift_a", "leaves_drift_b"], x, BASE_ROW))


def scatter_fg_grass(layer: Layer, xs: Iterable[int]) -> None:
    """Foreground grass tufts along the ground at each column in ``xs`` (depth)."""
    for x in xs:
        put(layer, x, BASE_ROW, pick(["fg_grass_a", "fg_grass_b", "fg_grass_c"], x, BASE_ROW))


# ===========================================================================
# GLOBAL COMPOSITION: sky + distant forest
# ===========================================================================
def compose_sky(*, bg_far: Layer, bg_mid: Layer) -> None:
    """Crepuscular sky gradient (BG_Far) + the in-window sky life (BG_Mid).

    METHODOLOGY NOTE (round 6): the engine's REAL internal resolution is 800x600
    (settings.py; the 320x224 branch is dead code), and the map is 2400x608, so
    the player sees essentially the WHOLE map height at once -- rows 0..37 are all
    on screen, NOT just a bottom 320x224 window as rounds 1-5 assumed. The band
    layout below is unchanged (it still lands the warm horizon at the treeline),
    but the once-"extended, postcard-only" upper sky (rows 0..23) is fully
    visible in game and is now composed by ``compose_celestial`` (moon, clouds,
    stars, far ridge) instead of being left as empty gradient bands.

    The gradient runs deep-violet (top) down through purple/rose and is joined
    by DITHERED transition bands (no hard horizontal seams). The concentrated
    warm sunset ``sky_horizon`` core + its diffuse ``sky_glow`` bloom are pulled
    down to rows ~27-30, right at the treeline/rooftops, so in-game the buildings
    are silhouetted against the sunset instead of a flat mauve wall. BG_Far is
    still fully filled so no transparent structure pixel ever reveals black.

    Stars/high clouds/bats stay in the deep upper sky on bands whose base tone
    matches theirs (invisible seams). The *in-window* clouds/bats instead go in
    BG_Mid on a transparent background, so they composite over the warm bands
    with no rectangular patch.
    """
    # --- BG_Far gradient (top -> bottom) --------------------------------------
    # Flat mottled bands do the bulk (they tile seamlessly because they're
    # uniform); a dithered RAMP tile bridges each pair, placed on EXACTLY ONE
    # row so its gradient appears once. (Stacking a ramp over several rows is
    # what repeated the gradient into the old "neon" streaks.) The warm sunset
    # is a continuous S3->S4->S5->S4->S3 run: glow / bright core / glow_dn.
    hband(bg_far, 0, 4, "sky_top")                # deep violet   (extended)
    hband(bg_far, 4, 5, "sky_tr_01")              # 1-row ramp
    hband(bg_far, 5, 10, "sky_high")              # indigo        (extended)
    hband(bg_far, 10, 11, "sky_tr_12")            # 1-row ramp
    hband(bg_far, 11, 24, "sky_mid")              # purple; reaches row 23
    hband(bg_far, 24, 25, "sky_tr_23")            # 1-row ramp -> rose (row 24, window top)
    hband(bg_far, 25, 27, "sky_low")              # rose dusk      (rows 25-26)
    hband(bg_far, 27, 28, "sky_glow")             # warm bloom rise (row 27)
    hband(bg_far, 28, 29, "sky_horizon")          # bright sunset core (row 28, over apexes)
    hband(bg_far, 29, 30, "sky_glow_dn")          # warm fall       (row 29)
    hband(bg_far, 30, H, "sky_low")               # cool dusk behind treeline/buildings/ground

    # stars scattered through the deep upper sky (base tone matches sky_top/high).
    # ROUND-11: spread across the full 205-col width so no 800px window is bare.
    stars = [(5, 1), (14, 3), (23, 2), (34, 4), (47, 1), (61, 3),
             (76, 2), (89, 4), (102, 1), (116, 3), (129, 2), (141, 4),
             (9, 6), (52, 8), (95, 7), (138, 9),
             (156, 2), (168, 4), (181, 1), (193, 3), (201, 2),
             (160, 7), (176, 9), (188, 6)]
    for i, (x, y) in enumerate(stars):
        put(bg_far, x, y, "sky_star_a" if i % 2 == 0 else "sky_star_b")

    # high bats + wispy postcard clouds (base tone matches their band), spread wide
    for x, y in [(30, 5), (58, 8), (118, 6), (150, 5), (186, 7)]:
        put(bg_far, x, y, pick(["bat_a", "bat_b"], x, y))
    clouds = [(8, 5, True), (40, 8, False), (70, 4, False),
              (96, 7, True), (120, 5, False), (134, 9, True),
              (158, 6, False), (176, 4, True), (196, 8, False)]
    for x, y, rim in clouds:
        l, m, r = ("cloud_rim_l", "cloud_rim_m", "cloud_rim_r") if rim else ("cloud_l", "cloud_m", "cloud_r")
        put(bg_far, x, y, l)
        put(bg_far, x + 1, y, m)
        put(bg_far, x + 2, y, r)

    # --- in-window sky life (BG_Mid, transparent bg -> no base-tone seam) -----
    # ROUND-11: spread so EACH ~800px camera window (spawn 0-50, carport 50-100,
    # arcos 100-150, arena 150-205) frames a drifting cloud, all at rows 25-26 ->
    # fully INSIDE the frame. Kept sparse (checklist: moderation).
    for x, y in [(3, 25), (28, 26), (60, 25), (82, 26), (116, 26), (140, 25),
                 (160, 26), (184, 25), (198, 26)]:
        put(bg_mid, x, y, "cloud_soft_l")
        put(bg_mid, x + 1, y, "cloud_soft_m")
        put(bg_mid, x + 2, y, "cloud_soft_r")
    for x, y in [(12, 26), (66, 27), (124, 26), (172, 27)]:
        put(bg_mid, x, y, "bat_soft")


def compose_celestial(*, bg_mid: Layer) -> None:
    """Round-6 "real view": populate the upper ~65% of the 800x600 frame.

    The engine renders at 800x600 (settings.py) and the map is 2400x608, so the
    player sees the WHOLE map height at once -- the sky above the treeline is NOT
    off-camera (as rounds 1-5 assumed a 320x224 window) but fully on screen. This
    fills it with a composed twilight vista, all as TRANSPARENT overlays on
    BG_Mid (composite over the BG_Far ramp, no base-tone patch):

      * ONE big low moon, asymmetric (cols 33-35, rows 6-8), in the spawn window;
      * denser star clusters across the high sky of all three windows;
      * cool high cloud banks at two altitudes (rows ~4-6 and ~14-16), some
        6 tiles long, spread so EACH 800px window frames cloud interest;
      * a far ridge/campus silhouette line (rows 18-20) -- the most DISTANT of
        three depth planes (this ridge -> the near forest -> the near scene).

    The three camera windows are exactly cols [0,50] (spawn), [50,100] (arcos),
    [100,150] (arena) at this resolution, so placements below are chosen to give
    every window a moon OR clouds, stars, and the ridge.
    """
    # --- hero moon (3x3 block), high-left in the spawn window --------------
    place_block(bg_mid, "moon", 3, 3, col0=33, row0=6)

    # --- star clusters, spread across the high sky of ALL FOUR windows (r11) ---
    stars = [(4, 2), (14, 8), (23, 3), (44, 5), (9, 12), (47, 11),          # spawn
             (55, 3), (66, 9), (78, 2), (90, 6), (95, 12), (60, 14),        # carport
             (104, 4), (116, 8), (128, 3), (140, 6), (110, 13), (146, 11),  # arcos
             (158, 4), (170, 9), (182, 3), (196, 6), (164, 13), (200, 11)]   # arena
    for i, (x, y) in enumerate(stars):
        put(bg_mid, x, y, "star_cluster_a" if i % 2 == 0 else "star_cluster_b")

    # --- cool high cloud banks at two altitudes (l/m/r 3-tile strips; a couple
    # doubled to 6 tiles). Each ~800px window gets a high (rows 4-6) and a mid
    # (14-16) bank so no slice of sky is empty (round-11: extended to arena).
    cloud_banks = [(6, 5), (44, 4), (20, 15),               # spawn
                   (58, 5), (61, 5), (82, 15), (88, 16),    # carport (58/61 = 6-tile)
                   (120, 6), (104, 16), (128, 14), (131, 14),  # arcos (128/131 = 6-tile)
                   (158, 5), (196, 4), (172, 15), (175, 15)]  # arena (172/175 = 6-tile)
    for x, y in cloud_banks:
        put(bg_mid, x, y, "cloud_high_l")
        put(bg_mid, x + 1, y, "cloud_high_m")
        put(bg_mid, x + 2, y, "cloud_high_r")

    # --- far ridge line (most distant plane): crest row 18, haze rows 19-20.
    # Placed in the S2-purple sky band so its S2->S3 tone reads as "barely lighter
    # than the sky" (atmospheric perspective), well above the near forest.
    for x in range(W):
        put(bg_mid, x, 18, pick(["ridge_far_a", "ridge_far_b"], x, 18))
        put(bg_mid, x, 19, "ridge_haze")
        put(bg_mid, x, 20, "ridge_haze")
    # distant campus silhouettes poking above the ridge, spread across the width
    for cx in (12, 40, 70, 106, 138, 168, 198):
        put(bg_mid, cx, 18, "campus_far")


def compose_forest(*, bg_mid: Layer) -> None:
    """Distant forest silhouette on the horizon (BG_Mid), behind the buildings.

    Pulled DOWN to the camera window as a THIN 3-row treeline (crown 31, lit
    canopy 32, hazy base 33) so it reads as a distant band on the horizon, not a
    heavy wall: below it (row 34) the rose dusk shows down to the near ground at
    row 35, exactly like the vignette where the lawn rises IN FRONT of the woods.
    Tall structures (hastial gable, gazebo cupola: apex row 29) rise above the
    treeline into the sunset. The crown tiles are transparent above their
    silhouette, so the warm horizon shows through the gaps between crowns, and
    the hazy base dissolves the woods into the dusk (atmospheric perspective).
    """
    tops = ["forest_top_a", "forest_top_b", "forest_top_c"]
    for x in range(W):
        if x in ARCOS:
            # ARCOS keeps a CONTINUOUS treeline/hedge between the houses -- it
            # reads as the enclosed courtyard/patio the director wants to keep.
            put(bg_mid, x, 31, pick(tops, x, 31))
            put(bg_mid, x, 32, "forest_canopy")
            put(bg_mid, x, 33, "forest_fill")             # green transition
            put(bg_mid, x, BASE_ROW, "meadow_base")       # meadow at row 34 (contact shadow)
        else:
            # PRADERA / ARENA: the mid vegetation is SEPARATED, rounded tree clumps
            # (1-3 rows) with SKY GAPS between them, sitting on a CONTINUOUS OPEN
            # GREEN MEADOW band (rows 33-34). The sunset breathes through the gaps
            # and the dirt path reads against the green -- no solid midground wall.
            # (Director round-5 fixes #1 + #2.)
            # ROUND-8: inside ARENA, the tall clumps around the gazebo are CLEARED
            # (a glade) with soft low-mound shoulders at its edges, so the lit
            # set-piece silhouette reads against the open dusk sky (user feedback).
            cyc = x % 13                                  # 5-col clump, then an 8-col gap
            if x in _ARENA_GLADE_SHOULDER:
                # a single low mound row: a soft shoulder easing the glade into the
                # surrounding treeline (no hard rectangular hole).
                put(bg_mid, x, 32, pick(tops, x, 32))
            elif x not in _ARENA_GAZEBO_GLADE and x not in _CARPORT_GLADE and cyc < 5:
                # rounded mound; centre column reaches row 29 -> a 4-row clump that
                # pokes into the warm horizon (round-6 point 5: near forest to 3-4
                # rows "donde convenga"), while the 8-col GAPS stay empty so the
                # sunset still breathes between clumps -- no solid wall (round 4-5).
                crown = [32, 31, 29, 31, 32][cyc]         # rounded mound (tallest at centre)
                put(bg_mid, x, crown, pick(tops, x, crown))
                for y in range(crown + 1, 33):            # canopy/fill down to row 32
                    put(bg_mid, x, y, "forest_canopy" if y == crown + 1 else "forest_fill")
            if x not in _GAZEBO_FOOTPRINT and x not in _CARPORT_GRAVEL:
                # ROUND-9 gazebo footprint + ROUND-11 carport gravel bay are kept
                # CLEAR of the meadow band (the gravel/plaza is the ground there).
                put(bg_mid, x, 33, "meadow_far")          # open dusk meadow band (recedes)...
                put(bg_mid, x, BASE_ROW, "meadow_base")   # ...row 34 carries the contact shadow
            # ...stays CLEAR of the meadow band so its bases/doorway are not buried;
            # BG_Far dusk sky shows at the flanks, the r7 turf (row 35) is its floor.


# ===========================================================================
# GROUND SURFACE (Terrain rows 35-37)
# ===========================================================================
def compose_ground(*, terrain: Layer) -> None:
    """Walkable surface (row 35) per zone + underground soil (rows 36-37).

    The zone thresholds are wired to the PRADERA/ARCOS/ARENA boundaries so the
    surface follows a zone when it moves.
    """
    walk = ["grass_walk_a", "grass_walk_b", "grass_walk_c"]
    for x in range(W):
        if x < PRADERA.start + 3:                          # a sliver of open lawn at the spawn
            surf = pick(walk, x, GROUND_ROW)
        elif x == PRADERA.start + 3:                       # lawn -> the dirt path begins
            surf = "path_edge_l"
        elif x < CARPORT.start - 4:                         # THE CAMINO (walkable dirt), now longer
            surf = pick(["dirt_path_a", "dirt_path_b"], x, GROUND_ROW)
        elif x == CARPORT.start - 4:                       # dirt -> lawn (path ends into the carport)
            surf = "path_edge_r"
        elif x < ARCOS.start - 2:                           # CARPORT lawn (walkable grass; gravel is bg)
            surf = "grass_walk_bald" if x % 13 == 0 else pick(walk, x, GROUND_ROW)
        elif x < ARCOS.start:                              # lawn -> sidewalk approach
            surf = pick(["sidewalk_slab_a", "sidewalk_slab_b"], x, GROUND_ROW)
        elif x < ARENA.start:                              # arcos sidewalk
            surf = _sidewalk_variant(x)
        elif x < ARENA.start + 5:                          # sidewalk -> lawn
            surf = "sidewalk_moss" if x % 2 else "sidewalk_slab_c"
        else:                                              # arena esplanade lawn
            surf = "grass_walk_bald" if x % 11 == 0 else pick(walk, x, GROUND_ROW)
        put(terrain, x, GROUND_ROW, surf)
        # underground soil: darkens downward, stones + roots (row 36 then 37)
        put(terrain, x, SUB_ROWS[0], "subsoil_top")
        put(terrain, x, SUB_ROWS[1], "subsoil_deep")

    # THE CAMINO, made LEGIBLE (director round-5 fix #1): the pradera dirt path is
    # 2 tiles tall where it "swells" toward the viewer and drops to 1 tile (green
    # meadow shows above it) where it bends away, so it reads as a dirt path
    # WINDING through the meadow -- born at the spawn (col 3) and snaking right.
    # The axis shifts on an 11-col cycle; grass/dirt seams use path_edge tiles.
    px0, px1 = PRADERA.start + 4, CARPORT.start - 4
    for x in range(px0, px1):
        seg = (x - px0) % 11
        if seg < 5:                                        # swell: dirt rises to row 34
            if seg == 0:
                put(terrain, x, BASE_ROW, "path_edge_l")   # meadow(left) -> path(right)
            elif seg == 4:
                put(terrain, x, BASE_ROW, "path_edge_r")   # path(left) -> meadow(right)
            else:
                put(terrain, x, BASE_ROW, pick(["dirt_path_a", "dirt_path_b"], x, BASE_ROW))
        # else seg 5-10: the path bends away -> row 34 stays background meadow (meadow_base)


def _sidewalk_variant(x: int) -> str:
    """Weathered paving mix for the arcos sidewalk."""
    m = x % 9
    if m == 0:
        return "sidewalk_crack"
    if m == 3:
        return "sidewalk_moss"
    if m == 6:
        return "sidewalk_broken_corner"
    return pick(["sidewalk_slab_a", "sidewalk_slab_b", "sidewalk_slab_c"], x, GROUND_ROW)


# ===========================================================================
# ZONE: PRADERA [0, 50)
# ===========================================================================
def compose_pradera(*, bg_near: Layer, terrain_detail: Layer, fg: Layer) -> None:
    """Meadow: big tree, distant bungalows, fallen fence, clothesline, tufts."""
    # big tree (BG_Near, behind the player), rooted on the ground. Its own block
    # already carries the trunk + roots, so no extra trunk tile is stamped (that
    # read as a detached box under the canopy).
    place_block(bg_near, "tree_c", 4, 4, col0=PRADERA.start + 6, row0=BASE_ROW - 3, sep="")
    # ROUND-11: a SECOND big tree out in the widened meadow so the longer pradera
    # keeps interest to the right (user: "cada zona un poco mas extensa").
    place_block(bg_near, "tree_c", 4, 4, col0=PRADERA.start + 52, row0=BASE_ROW - 3, sep="")

    # a near, lit bungalow INSIDE the spawn window (cols 11-13, BG_Near) so the
    # opening frame has scale + a warm sign of life, not just a lone tree
    bung_spawn = PRADERA.start + 11
    place_block(bg_near, "bung", 3, 3, col0=bung_spawn, row0=BASE_ROW - 2)
    put(bg_near, bung_spawn + 1, BASE_ROW - 1, "bung_win_lit")

    # two more distant bungalows with lit / boarded windows (BG_Near)
    bung_a = PRADERA.start + 26
    place_block(bg_near, "bung", 3, 3, col0=bung_a, row0=BASE_ROW - 2)
    put(bg_near, bung_a + 1, BASE_ROW - 1, "bung_win_lit")             # overwrite a body cell -> window
    bung_b = PRADERA.start + 34
    place_block(bg_near, "bung", 3, 3, col0=bung_b, row0=BASE_ROW - 2)
    put(bg_near, bung_b + 1, BASE_ROW - 1, "bung_win_board")

    # fence with fallen sections (Terrain_Detail, on the ground); starts at col 15
    # so it clears the spawn bungalow. Fallen columns kept absolute (see zone note)
    for x in range(PRADERA.start + 15, PRADERA.start + 25):
        name = "fence_fallen" if x in (18, 19) else pick(["fence_a", "fence_b", "fence_c"], x, BASE_ROW)
        put(terrain_detail, x, BASE_ROW, name)

    # clothesline strung between two leaning posts (low, near the ground)
    cl0 = PRADERA.start + 40
    put(terrain_detail, cl0, BASE_ROW - 1, "clothesline_l")
    put(terrain_detail, cl0 + 1, BASE_ROW - 1, "clothesline_m")
    put(terrain_detail, cl0 + 2, BASE_ROW - 1, "clothesline_r")

    # corridor density (director FIX 3): abandonment props + PUNCTUAL rounded
    # bushes dotted on the lawn (not a continuous hedge band, no floating cubes).
    put(terrain_detail, PRADERA.start + 2, BASE_ROW, "branch_fallen")   # spawn-window prop
    put(terrain_detail, PRADERA.start + 9, BASE_ROW, "branch_fallen")
    put(terrain_detail, PRADERA.start + 57, BASE_ROW, "branch_fallen")  # r11: fill the widened meadow
    for bx in (PRADERA.start + 20, PRADERA.start + 32, PRADERA.start + 43,
               PRADERA.start + 50, PRADERA.start + 60):                 # r11: more shrubs to the right
        put(terrain_detail, bx, BASE_ROW, "bush")                       # single shrubs, ground-rooted
    place_bench(terrain_detail, PRADERA.start + 46)                     # broken bench in the meadow
    scatter_leaves(terrain_detail, (PRADERA.start + 7, PRADERA.start + 15, PRADERA.start + 37,
                                    PRADERA.start + 55, PRADERA.start + 62))

    # foreground grass tufts (FG_Overlay), now SPARSE (every 6th col) so they read
    # as verges beside the dirt path instead of a green fringe burying it -- the
    # camino must stay legible (director round-5 fix #1).
    scatter_fg_grass(fg, range(PRADERA.start + 1, PRADERA.stop, 6))


# ===========================================================================
# ZONE: CARPORT [65, 95)  (round-11: "el lugar donde estaban los carros")
# ===========================================================================
def compose_carport(*, bg_near: Layer, terrain_detail: Layer, fg: Layer) -> None:
    """The parking bay: dark corrugated carport on black posts over a gravel bay,
    a silver sedan + white pickup parked under it, an orange tractor beside it.

    The carport structure + gravel go in BG_Near (behind the player); the vehicles
    and ground props go in Terrain_Detail (in front of the posts/gravel); the ivy,
    roof-leaves and fringe tufts go in FG_Overlay. The walkable surface (Terrain
    row 35) stays lawn -- the gravel is purely the visual backdrop of the bay
    (task: "la gravilla es el fondo visual del aparcadero ... no cambia la
    colision"), and compose_forest already cleared a glade so the dark carport
    silhouettes against the open dusk sky.
    """
    # dark gravel bay (BG_Near, behind the vehicles) with a lit concrete curb
    for x in _CARPORT_GRAVEL:
        put(bg_near, x, BASE_ROW - 1, "gravel")            # row 33
        put(bg_near, x, BASE_ROW, "gravel_curb")           # row 34 (front concrete edge)

    # carport roof (10x2) + BLACK metal posts down to cracked concrete bases
    place_block(bg_near, "carroof", _CARPORT_ROOF_W, 2, col0=_CARPORT_C0, row0=BASE_ROW - 5)
    for pc in _CARPORT_POSTS:
        for r in range(BASE_ROW - 4, BASE_ROW):            # rows 30..33 (post shaft)
            put(bg_near, pc, r, "carport_post")
        put(bg_near, pc, BASE_ROW, "carport_post_base")    # row 34 (post + basa)

    # parked vehicles (Terrain_Detail, drawn over the posts/gravel), feet on row 34
    place_block(terrain_detail, "sedan", 4, 2, col0=_CARPORT_C0 + 1, row0=BASE_ROW - 1)   # 72-75
    place_block(terrain_detail, "pickup", 4, 2, col0=_CARPORT_C0 + 5, row0=BASE_ROW - 1)  # 76-79
    place_block(terrain_detail, "tractor", 3, 2, col0=_CARPORT_C1 + 3, row0=BASE_ROW - 1)  # 83-85

    # abandonment beats: a worn tyre propped on the last post, an unlit lamp by the
    # driveway, drifting leaves + a couple of shrubs framing the bay.
    put(terrain_detail, _CARPORT_C1 + 1, BASE_ROW, "tire")             # col 81 (against post 80)
    put(terrain_detail, CARPORT.start + 3, BASE_ROW - 1, "lamp_top")   # col 68 (leaning lamp)
    put(terrain_detail, CARPORT.start + 3, BASE_ROW, "lamp_base")
    put(terrain_detail, CARPORT.start + 1, BASE_ROW, "bush")           # col 66 (approach shrub)
    put(terrain_detail, ARCOS.start - 3, BASE_ROW, "bush")             # col 92 (exit shrub)
    scatter_leaves(terrain_detail, (CARPORT.start + 6, ARCOS.start - 5))

    # ivy climbing the tractor (FG_Overlay) + leaves accumulated on the car roofs
    put(fg, _CARPORT_C1 + 5, BASE_ROW - 2, "ivy_b")                    # col 85, vine up the rear
    put(fg, _CARPORT_C1 + 5, BASE_ROW - 1, "ivy_a")
    put(fg, _CARPORT_C0 + 2, BASE_ROW - 1, pick(["leaves_drift_a", "leaves_drift_b"], _CARPORT_C0, 0))  # sedan roof
    put(fg, _CARPORT_C0 + 6, BASE_ROW - 1, pick(["leaves_drift_a", "leaves_drift_b"], _CARPORT_C1, 0))  # pickup cab roof

    # sparse foreground grass tufts framing the bay (skip the gravel/vehicle span)
    reserved = set(_CARPORT_GRAVEL) | set(range(_CARPORT_C1 + 3, _CARPORT_C1 + 6))
    scatter_fg_grass(fg, [x for x in range(CARPORT.start + 2, CARPORT.stop, 6) if x not in reserved])


# ===========================================================================
# ZONE: ARCOS [95, 155)
# ===========================================================================
# Passable hastial arches. Each 6x6 hastial rests on BASE_ROW; its arch opening
# occupies block cells (col 2..3, row 4..5). We punch those cells out of Terrain
# (leaving them transparent) so a warm far-doorway glow placed in BG_Near shows
# THROUGH, then draw the near stone reveal in FG_Overlay so the player passes
# inside the doorway. A distant hastial in the alley between the two gives the
# telescope (arch-within-arch) depth.
_ARCH_SKIP = {(2, 4), (3, 4), (2, 5), (3, 5)}


def _passable_arch(bg_near: Layer, terrain: Layer, fg: Layer, col0: int) -> None:
    row0 = BASE_ROW - 5                                   # 6 tall -> rows 29..34
    place_block(terrain, "hast", 6, 6, col0=col0, row0=row0, skip=_ARCH_SKIP)
    ocx, orow = col0 + 2, BASE_ROW - 1                    # opening: cols ocx..ocx+1, rows orow..BASE_ROW
    # warm far-doorway glow revealed through the punched opening (BG_Near)
    for dx in (0, 1):
        put(bg_near, ocx + dx, orow, "arch_glow_top")
        put(bg_near, ocx + dx, BASE_ROW, "arch_glow_bottom")
    # near stone reveal drawn IN FRONT of the player (FG_Overlay), 3 wide x 2 tall
    faces_top = ("arch_front_l_top", "arch_front_m_top", "arch_front_r_top")
    faces_bot = ("arch_front_l_bot", "arch_front_m_bot", "arch_front_r_bot")
    for i in range(3):
        put(fg, col0 + 1 + i, orow, faces_top[i])
        put(fg, col0 + 1 + i, BASE_ROW, faces_bot[i])


def compose_arcos(*, bg_near: Layer, terrain: Layer, terrain_detail: Layer, fg: Layer) -> None:
    """Two passable arches with a telescope of a distant arch, lamp and bench."""
    # ROUND-11: the two front arches are spaced WIDER (was +4/+23 in a 50-col zone;
    # now +5/+38 in a 60-col zone) so the distant telescope arch between them has
    # room to breathe, with the continuous seto/patio treeline running between.
    _passable_arch(bg_near, terrain, fg, col0=ARCOS.start + 5)         # front hastial #1 (100)
    _passable_arch(bg_near, terrain, fg, col0=ARCOS.start + 38)        # front hastial #2 (133)

    # distant hastial in the alley between them (BG_Near) -> telescope depth
    place_block(bg_near, "hast", 6, 6, col0=ARCOS.start + 22, row0=BASE_ROW - 5)   # 117

    # leaning lamp (unlit) rooted on the sidewalk
    put(terrain_detail, ARCOS.start + 2, BASE_ROW - 1, "lamp_top")
    put(terrain_detail, ARCOS.start + 2, BASE_ROW, "lamp_base")

    # broken bench on the ground in the alley/patio between the arches
    place_bench(terrain_detail, ARCOS.start + 28)

    # drifting leaves on the paving, spread across the wider corridor
    scatter_leaves(terrain_detail, (ARCOS.start + 13, ARCOS.start + 46, ARCOS.start + 54))


# ===========================================================================
# ZONE: ARENA [155, 205)
# ===========================================================================
def compose_arena(*, bg_mid: Layer, bg_near: Layer, terrain_detail: Layer, fg: Layer) -> None:
    """Lawn esplanade with the centered gazebo, its stone plaza, fireflies, leaves."""
    # gazebo centerpiece (BG_Near), 7x6 centered ~cols 122-128, rooted on ground
    place_block(bg_near, "gaz", 7, 6, col0=ARENA.start + 22, row0=BASE_ROW - 5)

    # ROUND-10 (user: "hay que construir su parte faltante" / no dejar el kiosco
    # cortado): seat the gazebo on a warm stone PLAZA/PLINTH filling the cleared
    # footprint at the base row (BG_Mid, BEHIND the gazebo so it draws over it and
    # the plaza only shows at the kiosk's transparent base sliver + its flanks).
    # This closes the pink sky-void at ground level (its LOW terrace = the 1-row
    # ground-hugging closure directive #3 asks for) while the dusk sky keeps
    # breathing ABOVE the terrace and through the kiosk interior. Step tiles cap
    # the ends. The gaz_* stone bases sit on the lit lip -> the kiosk reads seated.
    put(bg_mid, _GAZEBO_FOOTPRINT.start, BASE_ROW, "plaza_step_l")          # col 120 (left end)
    for x in range(_GAZEBO_FOOTPRINT.start + 1, _GAZEBO_FOOTPRINT.stop - 1):  # 121..129
        put(bg_mid, x, BASE_ROW, "plaza_slab")
    put(bg_mid, _GAZEBO_FOOTPRINT.stop - 1, BASE_ROW, "plaza_step_r")       # col 130 (right end)

    # PLAZOLETA ambience (directive #2): two low flank ornaments -- unlit leaning
    # lamps just OUTSIDE the kiosk (cols 121/129) so nothing covers the doorway --
    # plus a couple of fallen-leaf drifts off to the side. Low, to the flanks.
    for lc in (_GAZEBO_C0 - 1, _GAZEBO_C1 + 1):                             # cols 121, 129
        put(terrain_detail, lc, BASE_ROW - 1, "lamp_top")
        put(terrain_detail, lc, BASE_ROW, "lamp_base")
    scatter_leaves(terrain_detail, (_GAZEBO_C1 + 2, _GAZEBO_C1 + 3))        # plazoleta leaf drift (130-131)

    # esplanade framed by PUNCTUAL rounded shrubs on the lawn (not a hedge band)
    for bx in (ARENA.start + 2, ARENA.start + 6, ARENA.stop - 3, ARENA.stop - 7):
        put(terrain_detail, bx, BASE_ROW, "bush")

    # standalone broken bench prop
    place_bench(terrain_detail, ARENA.start + 12)

    # fireflies drifting over the arena (FG_Overlay); the swarm coordinates are a
    # fine-tuned decorative scatter kept absolute within the zone (see zone note).
    # ROUND-8: the swarm is BIASED toward the gazebo (cols 118-133) to reinforce
    # the focus on the lit set-piece, thinning out toward the arena edges; each
    # firefly already carries a 1px warm halo. Kept to 9 total (moderation).
    fireflies = [(159, 31), (167, 28), (173, 33), (176, 31), (181, 27),
                 (184, 32), (188, 30), (179, 29), (195, 29)]
    for x, y in fireflies:
        put(fg, x, y, "firefly")

    # drifting leaves + foreground grass tufts. ROUND-9: the FG grass tufts SKIP
    # the gazebo footprint so nothing sprouts in front of its bases/doorway (the
    # user's remaining complaint); the tufts keep peppering the rest of the arena.
    scatter_fg_grass(fg, [x for x in range(ARENA.start + 1, ARENA.stop, 3)
                          if x not in _GAZEBO_FOOTPRINT])
    scatter_leaves(terrain_detail, (ARENA.start + 6, ARENA.start + 20, ARENA.start + 36, ARENA.start + 48))


# ===========================================================================
# PLATFORMS (one-way ledges) with coherent ground-anchored decoration.
# Each entry: (x, y, w) in pixels + the tile-column span of its supporting hedge.
# ===========================================================================
# ROUND-11: the 5 platforms (2 corridor + 3 arena) keep their HEIGHTS but are
# re-distributed into the widened/shifted zones (corridor ledges in the longer
# pradera + arcos corridor; the 3 arena ledges shifted +55 cols / +880px with the
# arena, keeping their layout around the gazebo). The test contract fixes only
# that 2 corridor + 3 arena platforms EXIST, not their x positions.
_PLATFORMS: list[tuple[int, int, int]] = [
    (768, 488, 48),      # corridor C1  (cols 48-50, pradera meadow)
    (1776, 472, 48),     # corridor C2  (cols 111-113, arcos alley, clear of the arches)
    (2576, 488, 64),     # arena P1     (cols 161-164)
    (2768, 472, 48),     # arena P2     (cols 173-175, left of the gazebo)
    (2992, 488, 48),     # arena P3     (cols 187-189, right of the gazebo)
]


def place_arbor(layer: Layer, x0: int, x1: int, r_top: int) -> None:
    """A garden arbor/pergola supporting a one-way ledge from r_top to the ground.

    A walkable leafy crossbeam (r_top) on two end posts, with an OPEN vine
    lattice between them so the sunset/forest show through (never a solid tower),
    rooted in a low stone jardinera at BASE_ROW. Composited over the sky in
    Terrain_Detail; carries no collision itself (the ledge is the map's Platform
    object), so the player passes through the airy body.
    """
    for x in range(x0, x1):
        put(layer, x, r_top, "arbor_beam")
        for y in range(r_top + 1, BASE_ROW):
            put(layer, x, y, "arbor_post" if x in (x0, x1 - 1) else "arbor_lattice")
        put(layer, x, BASE_ROW, "arbor_base")


def compose_platform_decor(*, terrain_detail: Layer) -> None:
    """Draw a garden arbor under every platform so no ledge floats."""
    for x, y, w in _PLATFORMS:
        c0 = x // TILE
        c1 = (x + w) // TILE
        r_top = y // TILE                                 # beam just under the ledge
        place_arbor(terrain_detail, c0, c1, r_top)


# ===========================================================================
# LIGHTS (feature B, spec 2026-07-29 "adopcion V2: sfx/luces/weakpoints" sec.
# 2). Five ``type="Light"`` objects: four warm lamps anchored to the exact
# tile compose_carport()/compose_arcos()/compose_arena() already stamp with a
# ``lamp_top``/``lamp_base`` pair (decorative "unlit lamp" set dressing --
# lighting it is a literal reading of a prop already drawn, not new art), plus
# one cold accent on the distant ARCOS hastial's oculo (the "telescope" gable
# depth cue). No pixel is invented: every ``col``/``row`` below is a formula
# over the SAME zone constants ``compose_*()`` used to place its lamp (cited
# per entry), so a future zone shift (e.g. CARPORT widening again) carries the
# light with it. ``StageLoader._handle_light`` reads a Tiled rect's CENTRE, and
# a TILE x TILE (16x16) box rooted at ``(col*TILE, row*TILE)`` centres exactly
# on that tile -- so no separate pixel math needs to stay in sync either.
# ===========================================================================
_LAMP_ROW = BASE_ROW - 1   # 33: the row every lamp_top/lamp_base pair sits on

_LIGHTS: list[dict] = [
    dict(
        obj_id=5, name="Light_CarportLamp_01", anchor="lamp",
        col=CARPORT.start + 3, row=_LAMP_ROW,       # compose_carport() lamp_top
        radius="90", color="warm", intensity="0.75",
        flicker=True, flicker_speed="4.0", flicker_amount="0.20",
    ),
    dict(
        obj_id=6, name="Light_ArcosLamp_01", anchor="lamp",
        col=ARCOS.start + 2, row=_LAMP_ROW,         # compose_arcos() lamp_top
        radius="80", color="warm", intensity="0.65",
        flicker=True, flicker_speed="4.0", flicker_amount="0.20",
    ),
    dict(
        obj_id=7, name="Light_ArenaLampWest_01", anchor="lamp",
        col=_GAZEBO_C0 - 1, row=_LAMP_ROW,          # compose_arena() lamp_top (west flank)
        radius="100", color="warm", intensity="0.85",
        flicker=True, flicker_speed="4.5", flicker_amount="0.22",
    ),
    dict(
        obj_id=8, name="Light_ArenaLampEast_01", anchor="lamp",
        col=_GAZEBO_C1 + 1, row=_LAMP_ROW,          # compose_arena() lamp_top (east flank)
        radius="100", color="warm", intensity="0.85",
        flicker=True, flicker_speed="4.5", flicker_amount="0.22",
    ),
    dict(
        obj_id=9, name="Light_ArcosOculo_01", anchor="oculo",
        col=ARCOS.start + 22, row=31,               # compose_arcos() distant hastial block (telescope)
        radius="140", color="cold", intensity="0.5",
        flicker=False, flicker_speed=None, flicker_amount=None,
    ),
]


def _light_object_xml(spec: dict) -> str:
    """One ``type="Light"`` object from a ``_LIGHTS`` entry (format copied
    from the professor's reference TMX, ``reference/v2_boss_profesor/maps/
    boss_venado.tmx`` -- a TILE-sized rect with radius/color/intensity/
    flicker* as typed ``<properties>``)."""
    x, y = spec["col"] * TILE, spec["row"] * TILE
    props = (
        _prop("radius", spec["radius"], "float", "    ")
        + _prop("color", spec["color"], "string", "    ")
        + _prop("intensity", spec["intensity"], "float", "    ")
    )
    if spec["flicker"]:
        props += (
            _prop("flicker", "true", "bool", "    ")
            + _prop("flicker_speed", spec["flicker_speed"], "float", "    ")
            + _prop("flicker_amount", spec["flicker_amount"], "float", "    ")
        )
    return (
        f'  <object id="{spec["obj_id"]}" name="{spec["name"]}" type="Light" '
        f'x="{x}" y="{y}" width="{TILE}" height="{TILE}">\n'
        '   <properties>\n'
        + props +
        '   </properties>\n'
        '  </object>\n'
    )


# ===========================================================================
# XML SERIALISATION
# ===========================================================================
def _prop(name: str, value: str, ptype: str | None = None, indent: str = "  ") -> str:
    """One typed ``<property/>`` line (``type`` attribute omitted when None)."""
    type_attr = f' type="{ptype}"' if ptype else ""
    return f'{indent}<property name="{name}"{type_attr} value="{value}"/>\n'


def _csv_layer(layer: Layer, layer_name: str) -> str:
    """Row-major GID CSV: values comma-joined, a newline after each row's comma.

    Rows are joined with ``",\\n"`` so stripping newlines yields one clean
    comma-separated stream (no merged values, no trailing comma). An unknown
    tile name is re-raised with its layer and (x, y) cell for a pinpoint fix.
    """
    rows: list[str] = []
    for y, row in enumerate(layer):
        cells: list[str] = []
        for x, name in enumerate(row):
            if name is None:
                cells.append("0")
                continue
            try:
                cells.append(str(_gid(name)))
            except KeyError as exc:
                raise KeyError(f"layer '{layer_name}' cell ({x},{y}): {exc}") from exc
        rows.append(",".join(cells))
    return ",\n".join(rows)


def _tile_layer_xml(lid: int, name: str, layer: Layer) -> str:
    return (
        f' <layer id="{lid}" name="{name}" width="{W}" height="{H}">\n'
        f'  <data encoding="csv">\n{_csv_layer(layer, name)}\n</data>\n'
        f' </layer>\n'
    )


def _objects_xml() -> str:
    return (
        ' <objectgroup id="6" name="Objects">\n'
        '  <object id="1" name="PlayerSpawn_01" type="PlayerSpawn" x="48" y="560">\n'
        '   <point/>\n'
        '  </object>\n'
        # BossVenado_01 is a bare POINT object: name/type/x/y only, NO custom
        # properties. StageLoader.load() passes EVERY TMX object property to the
        # entity as a keyword argument (stage_loader.py ~L239:
        # ``entity_class(Vector2(obj.x, obj.y), **cleaned)``), and the professor's
        # original boss is ``BossVenado.__init__(self, spawn_position)`` -- a bare
        # ctor with no kwargs. So ANY property here (the old arena_origin_x/y,
        # copied from a superseded generator) raises ``TypeError: __init__() got
        # an unexpected keyword argument`` and aborts the whole stage load --
        # crashing ``python main.py --boss boss_venado`` too, not just the harness.
        # The arena rect the boss fights inside is already carried by
        # CameraLock_01 (x=2480 = ARENA.start*16, w=800 = 50 cols) below; a
        # future phase-2 boss that needs an arena origin will re-introduce it
        # AS A CTOR KWARG first. ROUND-11: boss + arena shifted with the arena
        # zone (ARENA now [155,205); arena x=2480).
        # ROUND-12 (user feedback: "pon el boss al final del mapa"): the boss
        # point moves from the arena's centre (col 180 -> x=2880) to its FAR
        # RIGHT, past the gazebo (cols 177-183) and close to RightWall_Arena
        # (col 204 -> x=3264): col 198 -> x=3168. The arena zone itself
        # (CameraLock_01, x=2480 w=800) is unchanged -- only the boss spawn
        # point moves within it.
        # ENGINE V2: the ArenaZone_01 marker object (type="ArenaZone", purely
        # descriptive, never read by any code -- the arena bounds live in the
        # ARENA_X0/X1 constants in boss_venado.py/boss_venado_scene.py) used to
        # sit here too. StageLoader V2's object validator (tmx_diagnostics.
        # BUILTIN_OBJECT_TYPES) now aborts the whole stage load on any object
        # type it doesn't recognize, and there is no generic inert marker type
        # in that list -- so a type invented just to leave a visual note in
        # Tiled is no longer free. Dropped rather than re-typed as one of the
        # real builtins (CameraLock already covers the same rect, see above).
        '  <object id="2" name="BossVenado_01" type="BossVenado" x="3168" y="240">\n'
        '   <point/>\n'
        '  </object>\n'
        '  <object id="4" name="CameraLock_01" type="CameraLock" x="2480" y="0" width="800" height="608">\n'
        '   <properties>\n'
        + _prop("lock_x", "true", "bool", "    ")
        + _prop("lock_y", "true", "bool", "    ")
        + '   </properties>\n'
        '  </object>\n'
        + "".join(_light_object_xml(spec) for spec in _LIGHTS)
        + ' </objectgroup>\n'
    )


def _collision_xml() -> str:
    lines = [
        ' <objectgroup id="7" name="Collision">',
        # ROUND-11: Floor spans the full widened map (W*16 = 3280) and the right
        # wall sits at the last column ((W-1)*16 = 3264).
        '  <object id="10" name="Floor" x="0" y="560" width="3280" height="48"/>',
        '  <object id="11" name="LeftWall_World" x="0" y="0" width="16" height="608"/>',
        '  <object id="12" name="RightWall_Arena" x="3264" y="0" width="16" height="608"/>',
    ]
    for i, (x, y, w) in enumerate(_PLATFORMS):
        lines.append(
            f'  <object id="{20 + i}" name="Platform" type="Platform" '
            f'x="{x}" y="{y}" width="{w}" height="16"/>'
        )
    lines.append(' </objectgroup>\n')
    return "\n".join(lines)


def build_tmx() -> str:
    """Compose every layer and return the complete TMX document as text."""
    bg_far, bg_mid, bg_near = _blank(), _blank(), _blank()
    terrain, terrain_detail, fg = _blank(), _blank(), _blank()

    compose_sky(bg_far=bg_far, bg_mid=bg_mid)
    compose_celestial(bg_mid=bg_mid)
    compose_forest(bg_mid=bg_mid)
    compose_ground(terrain=terrain)
    compose_pradera(bg_near=bg_near, terrain_detail=terrain_detail, fg=fg)
    compose_carport(bg_near=bg_near, terrain_detail=terrain_detail, fg=fg)
    compose_arcos(bg_near=bg_near, terrain=terrain, terrain_detail=terrain_detail, fg=fg)
    compose_arena(bg_mid=bg_mid, bg_near=bg_near, terrain_detail=terrain_detail, fg=fg)
    compose_platform_decor(terrain_detail=terrain_detail)

    header = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<map version="1.10" tiledversion="1.12.2" orientation="orthogonal" '
        f'renderorder="right-down" width="{W}" height="{H}" '
        f'tilewidth="{TILE}" tileheight="{TILE}" infinite="0" '
        f'nextlayerid="20" nextobjectid="99">\n'
        ' <properties>\n'
        + _prop("stage_id", "boss_venado")
        + _prop("stage_name", "VENADO")
        + _prop("time_limit", "0", "int")
        + _prop("bgm_track", "bgm_zone1_boss")
        + _prop("background_zone", "zone1")
        # Feature B (spec 2026-07-29 sec. 2.1): lighting/atmosphere props,
        # adopted from the professor's reference TMX but pulled toward the
        # ambient already approved in map rounds 7-12 (zone 1's implicit
        # 0.62/0.18/0.30 ambient/bloom/vignette, "leaves" ambient_fx),
        # NOT the reference's darker "storm" numbers. ``climate`` and
        # ``day_length`` are deliberately omitted -- see
        # test_tmx_omits_climate_day_length_start_hour_and_season.
        #
        # RECALIBRATION (user decision, visual critique round 2): the first
        # pass also declared start_hour="dusk" + season="autumn", expecting
        # the engine's day/night cycle to LAND the composed ambient near
        # 0.60. Measured in runtime instead of assumed: it does not.
        # ``StageScene._aplicar_hora`` (stage_scene.py:518-526) computes
        #     ambient = max(MIN_AMBIENTE, ambient_light * luz.factor_ambiente
        #                                  * estacion.factor_luz)
        # (``MIN_AMBIENTE = 0.45``, stage_scene.py:516). "dusk" resolves to
        # hour 19.0 (``RelojDeMundo.MOMENTOS["dusk"]``, day_night.py:150),
        # which interpolates between the 18h/20h stops (factor_ambiente
        # 0.80/0.66, day_night.py:61-62) to 0.73; "autumn" contributes
        # ``factor_luz = 0.94`` (seasons.py:66). 0.60 * 0.73 * 0.94 = 0.412,
        # BELOW the 0.45 floor -- so the composed ambient always clamped to
        # the floor the user just rejected, no matter how ``ambient_light``
        # was tuned up to ~0.60 in isolation.
        #
        # The tileset's own palette is already painted for dusk (round-6/7
        # crepuscular vignette), so the engine's time-of-day/season TINTING
        # is redundant on top of it -- option (a) from the recalibration
        # brief: drop ``start_hour``/``season`` entirely rather than fight
        # the multiplier. Omitted, the engine does NOT fall back to a
        # neutral (x1) multiplier for either factor on its own:
        #   - no start_hour -> ``StageData.start_hour is None`` ->
        #     ``StageScene.HORA_POR_DEFECTO = 12.0`` (noon, stage_scene.py:
        #     505) -> the 10h-14h stops are BOTH 1.00 (day_night.py:59-60),
        #     so factor_ambiente is exactly 1.0 (genuinely neutral).
        #   - no season -> ``StageData.season == ""`` -> ``seasons.estacion("")``
        #     falls to ``POR_DEFECTO = "summer"`` (seasons.py:79,90), whose
        #     ``factor_luz = 1.08`` (seasons.py:60) -- NOT neutral.
        # So the true composed multiplier with both omitted is 1.0 * 1.08 =
        # 1.08, not 1.0. ``ambient_light`` is solved against that measured
        # multiplier, not assumed: 0.55 * 1.08 = 0.594, inside the requested
        # ~0.58-0.60 band and nowhere near MIN_AMBIENTE. Regression-locked by
        # test_effective_ambient_stays_above_playable_floor, which calls the
        # SAME production formula/constants instead of re-deriving them.
        #
        # Bonus finding: with ``climate`` undeclared, the engine's effective
        # weather (``StageScene._clima_efectivo``, stage_scene.py:456-469)
        # falls back to ``estacion.clima`` -- "rain" for autumn, "clear" for
        # the summer default. Dropping ``season`` therefore also retires an
        # unintended rain-weather VFX that "autumn" had silently switched on
        # (the map's approved crepuscular critique never asked for rain).
        #
        # bloom/vignette (step 2 of the recalibration): ``_aplicar_hora``
        # also adds ``luz.bloom_extra`` on top of the declared ``bloom``
        # (stage_scene.py:527-528). At the dusk/autumn hour that extra was
        # ~0.085 (18h/20h stops 0.06/0.11 interpolated, day_night.py:61-62),
        # pushing the applied bloom to ~0.305 -- already the "disproportionate"
        # case step 2 warns about. At the neutral noon default, bloom_extra
        # is exactly 0.00 (day_night.py:59-60), so the declared 0.22 now
        # applies UNMODIFIED -- already subtle, no further change needed.
        # ``vignette`` is never touched by day/night or season (grepped: only
        # ``_setup_post_processing`` reads it), so 0.32 is unaffected either
        # way and is left as-is.
        + _prop("zone", "1", "int")
        + _prop("ambient_light", "0.55", "float")
        + _prop("bloom", "0.22", "float")
        + _prop("vignette", "0.32", "float")
        + _prop("ambient_fx", "leaves", "string")
        + _prop("ambient_fx_rate", "10", "float")
        + ' </properties>\n'
        f' <tileset firstgid="{FIRSTGID}" name="{TILESET_NAME}" '
        f'tilewidth="{TILE}" tileheight="{TILE}" tilecount="{TILECOUNT}" columns="{COLUMNS}">\n'
        f'  <image source="{TILESET_IMG}" width="{TILESET_W}" height="{TILESET_H}" trans="000000"/>\n'
        ' </tileset>\n'
    )

    body = (
        _tile_layer_xml(1, "BG_Far", bg_far)
        + _tile_layer_xml(2, "BG_Mid", bg_mid)
        + _tile_layer_xml(3, "BG_Near", bg_near)
        + _tile_layer_xml(4, "Terrain", terrain)
        + _tile_layer_xml(5, "Terrain_Detail", terrain_detail)
        + _objects_xml()
        + _collision_xml()
        + _tile_layer_xml(8, "FG_Overlay", fg)
    )

    return header + body + "</map>\n"


def main() -> None:
    """Write the TMX (idempotent; byte-stable across repeated calls)."""
    OUT_TMX.parent.mkdir(parents=True, exist_ok=True)
    OUT_TMX.write_text(build_tmx(), encoding="utf-8")
    print(f"tmx -> {OUT_TMX} ({W}x{H} tiles, {len(_PLATFORMS)} platforms)")


if __name__ == "__main__":
    main()
