"""
Module: gen_tileset_residencias
System: tools (map art)
Description: Production tileset generator for the "Residencias al Crepusculo"
    boss arena. Emits a named 16x16 atlas (12 columns) plus a labelled contact
    sheet. Every pixel is a palette colour set directly into a numpy array (no
    anti-alias), sharing the frozen 34-colour master palette approved in the
    twilight vignette proof (2026-07-23). Filler tiles (sky/grass/forest/hedge/
    stucco) sample noise on GLOBAL atlas coordinates so sibling variants flow
    seamlessly; multi-tile structures (hastial, gazebo, tree, bungalow) are
    painted as a single large composition and then sliced into cells so they
    tile back together with no seams.

Origin
------
Techniques (ordered dither, per-pixel hash mottle, corrugated sheet grooves,
crepuscular sky ramp, stucco weathering, despeckle cleanup) are lifted from
``tools/vignette_reference.py`` and its extracted helpers in ``tools/art_lib``.
No colour value is re-derived: the atlas draws only names from
``art_lib.PALETTE`` (plus pure black ``(0, 0, 0)`` reserved as visual empty).

Outputs (idempotent; ``main()`` may be called repeatedly)
--------------------------------------------------------
- ``<game>/assets/tilesets/tileset_residencias_crepusculo.png`` (the atlas)
- ``<lab>/reports/map_residencias/tileset_contact_sheet.png`` (x3 NEAREST,
  every cell labelled ``idx name`` for visual review)
"""
from __future__ import annotations

import math
import os
from pathlib import Path
from typing import Callable

import numpy as np
from PIL import Image, ImageDraw

from src.stages.boss_venado.tools.art_lib import (
    BAYER_4X4,
    PALETTE,
    bayer_dither,
    despeckle,
    hash01,
    mottle,
)

# ---------------------------------------------------------------------------
# Paths (derived from __file__ so cwd never matters)
# ---------------------------------------------------------------------------
_HERE = Path(__file__).resolve()
GAME_ROOT = _HERE.parents[4]                 # .../game
LAB_ROOT = _HERE.parents[5]                  # .../Centro de pruebas CPG I
OUT_PNG = GAME_ROOT / "assets" / "tilesets" / "tileset_residencias_crepusculo.png"
CONTACT_DIR = LAB_ROOT / "reports" / "map_residencias"
CONTACT_PNG = CONTACT_DIR / "tileset_contact_sheet.png"

TILE = 16
COLS = 12
BLACK = (0, 0, 0)                            # tile 0 / visual empty

# Bright, deliberately-isolated accents that despeckle must never clear.
_PROTECT = (
    "W0", "W1", "W2", "S4", "S5", "RC", "RM",
    "P0", "P1", "O3", "PL", "V3", "G3",
)

# ---------------------------------------------------------------------------
# Registry: @tile decorator + block slicer, both feed TILES / NAME_TO_INDEX.
# A draw fn has signature (cell, gx, gy) -> None, where `cell` is the 16x16x3
# view of the atlas and (gx, gy) is that cell's top-left in GLOBAL atlas pixels
# (used by fillers so adjacent variants share one continuous noise field).
# ---------------------------------------------------------------------------
DrawFn = Callable[[np.ndarray, int, int], None]
TILES: list[tuple[str, DrawFn]] = []
NAME_TO_INDEX: dict[str, int] = {}


def _register(name: str, fn: DrawFn) -> None:
    if name in NAME_TO_INDEX:
        raise ValueError(f"duplicate tile name: {name}")
    NAME_TO_INDEX[name] = len(TILES)
    TILES.append((name, fn))


def tile(name: str) -> Callable[[DrawFn], DrawFn]:
    """Register a single 16x16 tile drawn by the decorated function."""
    def deco(fn: DrawFn) -> DrawFn:
        _register(name, fn)
        return fn
    return deco


_BLOCK_BUILDERS: dict[str, Callable[[], np.ndarray]] = {}
_BLOCK_CACHE: dict[str, np.ndarray] = {}


def _get_block(key: str) -> np.ndarray:
    if key not in _BLOCK_CACHE:
        _BLOCK_CACHE[key] = _BLOCK_BUILDERS[key]()
    return _BLOCK_CACHE[key]


def register_block(
    prefix: str,
    cols: int,
    rows: int,
    builder: Callable[[], np.ndarray],
    sep: str = "_",
) -> None:
    """Register a (cols x rows) tile block built as one composition.

    ``builder`` returns a ``(rows*16, cols*16, 3)`` uint8 buffer; it is painted
    once (memoised) and cut into cells named ``{prefix}{sep}{col}{row}``
    (column digit first, matching the inventory: a 7x6 gazebo's bottom-right is
    ``gaz_65``). E.g. ``hast_00``..``hast_55``, or ``tree_c00`` with ``sep=""``.
    """
    _BLOCK_BUILDERS[prefix] = builder

    def _cell(kk: str, rr: int, cc: int) -> DrawFn:
        def fn(cell: np.ndarray, gx: int, gy: int) -> None:
            blk = _get_block(kk)
            cell[:] = blk[rr * TILE:rr * TILE + TILE, cc * TILE:cc * TILE + TILE]
        return fn

    for r in range(rows):
        for c in range(cols):
            _register(f"{prefix}{sep}{c}{r}", _cell(prefix, r, c))


# ---------------------------------------------------------------------------
# Low-level pixel helpers (operate on any HxWx3 array)
# ---------------------------------------------------------------------------
def _put(A: np.ndarray, x: int, y: int, name: str) -> None:
    h, w = A.shape[:2]
    if 0 <= x < w and 0 <= y < h:
        A[y, x] = PALETTE[name]


def _rect(A: np.ndarray, x0: int, y0: int, x1: int, y1: int, name: str) -> None:
    h, w = A.shape[:2]
    x0 = max(0, x0); y0 = max(0, y0); x1 = min(w, x1); y1 = min(h, y1)
    if x1 > x0 and y1 > y0:
        A[y0:y1, x0:x1] = PALETTE[name]


# ===========================================================================
# TILE 0 - visual empty
# ===========================================================================
@tile("black")
def _black(A: np.ndarray, gx: int, gy: int) -> None:
    A[:] = BLACK


# ===========================================================================
# SKY  (crepuscular ramp, flat bands with fine mottle so each tiles cleanly)
# ===========================================================================
def _sky_fill(A, gx, gy, base, alt, alt_prob, salt):
    for y in range(TILE):
        for x in range(TILE):
            r = hash01(gx + x, gy + y, salt)
            A[y, x] = PALETTE[alt] if r < alt_prob else PALETTE[base]


@tile("sky_top")
def _sky_top(A, gx, gy):
    _sky_fill(A, gx, gy, "S0", "S1", 0.06, 1)


@tile("sky_high")
def _sky_high(A, gx, gy):
    _sky_fill(A, gx, gy, "S1", "S2", 0.10, 2)


@tile("sky_mid")
def _sky_mid(A, gx, gy):
    _sky_fill(A, gx, gy, "S2", "S3", 0.12, 3)


@tile("sky_low")
def _sky_low(A, gx, gy):
    _sky_fill(A, gx, gy, "S3", "S2", 0.12, 4)


@tile("sky_horizon")
def _sky_horizon(A, gx, gy):
    # Concentrated sunset CORE: a single soft vertical ramp rose(S3) -> peak
    # orange(S5) -> back to warm(S4), ordered-dithered so it reads as ONE smooth
    # gradient instead of the old hard "neon triple" sub-bands. A few W0 glints
    # flick along the brightest middle. Placed as a thin 2-row band at the
    # treeline; the forest crown breaks its lower edge so there is no hard line.
    for y in range(TILE):
        t = y / (TILE - 1)
        for x in range(TILE):
            if t < 0.30:
                base = bayer_dither(gx + x, gy + y, "S3", "S4", t / 0.30)
            elif t < 0.62:
                base = bayer_dither(gx + x, gy + y, "S4", "S5", (t - 0.30) / 0.32)
            else:
                base = bayer_dither(gx + x, gy + y, "S5", "S4", (t - 0.62) / 0.38)
            if 0.34 < t < 0.60 and hash01(gx + x, gy + y, 5) < 0.05:
                base = "W0"                    # faint blazing glint on the crest
            A[y, x] = PALETTE[base]


def _sky_trans(A, gx, gy, top, bot, salt):
    """A soft dithered band that ramps from ``top`` (its top edge) to ``bot``
    (its bottom edge) via ordered Bayer dither, so adjacent flat sky bands melt
    into each other with no hard horizontal seam. A little hash noise scuffs the
    dither so it never looks like a mechanical screen."""
    for y in range(TILE):
        t = y / (TILE - 1)
        for x in range(TILE):
            name = bayer_dither(gx + x, gy + y, top, bot, t)
            if hash01(gx + x, gy + y, salt) < 0.05:
                name = bot if name == top else top
            A[y, x] = PALETTE[name]


@tile("sky_tr_01")
def _sky_tr_01(A, gx, gy):
    _sky_trans(A, gx, gy, "S0", "S1", 21)      # deep violet -> indigo


@tile("sky_tr_12")
def _sky_tr_12(A, gx, gy):
    _sky_trans(A, gx, gy, "S1", "S2", 22)      # indigo -> purple


@tile("sky_tr_23")
def _sky_tr_23(A, gx, gy):
    _sky_trans(A, gx, gy, "S2", "S3", 23)      # purple -> rose dusk


@tile("sky_glow")
def _sky_glow(A, gx, gy):
    # Diffuse warm bloom that sits ABOVE the concentrated horizon core: rose(S3)
    # melting UP into the first warm(S4). Placed as a SINGLE row so its ramp
    # appears once (stacking the same ramp tile is what caused the old streaks).
    _sky_trans(A, gx, gy, "S3", "S4", 24)


@tile("sky_glow_dn")
def _sky_glow_dn(A, gx, gy):
    # The falling side of the sunset: warm(S4) melting back DOWN to rose(S3),
    # placed one row below the bright core so the orange fades symmetrically into
    # the dusk behind the buildings. Continues the core's S4 edge with no step.
    _sky_trans(A, gx, gy, "S4", "S3", 25)


@tile("sky_star_a")
def _sky_star_a(A, gx, gy):
    _sky_fill(A, gx, gy, "S0", "S1", 0.05, 1)
    _put(A, 5, 4, "W2"); _put(A, 11, 9, "RC"); _put(A, 8, 12, "RM")


@tile("sky_star_b")
def _sky_star_b(A, gx, gy):
    _sky_fill(A, gx, gy, "S1", "S0", 0.05, 2)
    _put(A, 10, 3, "RC"); _put(A, 4, 10, "W2"); _put(A, 7, 7, "W1")


_BAT = [(-3, 1), (-2, 0), (-1, 1), (0, 2), (1, 1), (2, 0), (3, 1)]


@tile("bat_a")
def _bat_a(A, gx, gy):
    _sky_fill(A, gx, gy, "S1", "S2", 0.06, 1)
    for dx, dy in _BAT:
        _put(A, 8 + dx, 7 + dy, "K1")


@tile("bat_b")
def _bat_b(A, gx, gy):
    _sky_fill(A, gx, gy, "S1", "S0", 0.06, 2)
    for dx, dy in _BAT:
        _put(A, 9 + dx, 10 + dy, "K1")
    for dx, dy in _BAT:                       # a second, further glider
        _put(A, 4 + dx, 4 + dy, "K0")


def _cloud_strip(warm_rim: bool) -> np.ndarray:
    """A 48x16 wispy cloud (3 tiles wide) sliced into l/m/r so they reconnect."""
    B = np.zeros((TILE, 48, 3), np.uint8)
    base_sky = "S2" if warm_rim else "S1"
    for y in range(TILE):
        for x in range(48):
            B[y, x] = PALETTE["S1" if hash01(x, y, 6) < 0.12 else base_sky]
    cx, cy, rx, thick = 24, 8, 22, 3
    for y in range(cy - thick, cy + thick + 1):
        for x in range(cx - rx, cx + rx + 1):
            if not (0 <= x < 48 and 0 <= y < TILE):
                continue
            fx = (x - cx) / rx
            prof = max(0.0, 1 - fx * fx) ** 0.6
            half = prof * thick
            dy = y - cy
            if abs(dy) > half + 0.5:
                continue
            if hash01(x, y, 5) > 0.45 + 0.4 * prof:
                continue
            if dy >= half - 1.2:
                base = ("S5" if warm_rim else "S4") if prof > 0.5 else "S4"
            elif dy <= -half + 1.0:
                base = "S2"
            else:
                base = "S3"
            B[y, x] = PALETTE[base]
    for x in range(cx - rx, cx + rx + 1):
        prof = max(0.0, 1 - ((x - cx) / rx) ** 2) ** 0.6
        yy = cy + int(prof * thick)
        if 0 <= x < 48 and 0 <= yy < TILE and prof > 0.4 and hash01(x, yy, 9) > 0.55:
            B[yy, x] = PALETTE["W0" if warm_rim else "W1"]
    if warm_rim:                              # blazing orange rim on the lit crest
        for x in range(cx - rx, cx + rx + 1):
            prof = max(0.0, 1 - ((x - cx) / rx) ** 2) ** 0.6
            yy = cy - int(prof * thick)
            if 0 <= x < 48 and 0 <= yy < TILE and prof > 0.25 and hash01(x, yy, 10) > 0.4:
                B[yy, x] = PALETTE["S5"]
    return B


_CLOUD = _cloud_strip(False)
_CLOUD_RIM = _cloud_strip(True)


def _cloud_slice(strip, c0):
    def fn(cell, gx, gy):
        cell[:] = strip[:, c0:c0 + TILE]
    return fn


_register("cloud_l", _cloud_slice(_CLOUD, 0))
_register("cloud_m", _cloud_slice(_CLOUD, 16))
_register("cloud_r", _cloud_slice(_CLOUD, 32))
_register("cloud_rim_l", _cloud_slice(_CLOUD_RIM, 0))
_register("cloud_rim_m", _cloud_slice(_CLOUD_RIM, 16))
_register("cloud_rim_r", _cloud_slice(_CLOUD_RIM, 32))


def _cloud_soft_strip() -> np.ndarray:
    """A 48x16 sunset-lit dusk cloud on a TRANSPARENT (black) background.

    Unlike the BG_Far clouds above (which carry their own sky base and so must
    be dropped only on a band whose tone matches), this one is meant for BG_Mid:
    its empty pixels stay pure black -> transparent -> it composites over ANY
    sky band inside the camera window with no rectangular base-tone seam. Cool
    shadowed crown (S2), rose body (S3), warm sunset-lit underside (S4/S5)."""
    B = np.zeros((TILE, 48, 3), np.uint8)      # black == transparent
    cx, cy, rx, thick = 24, 9, 21, 3
    for y in range(TILE):
        for x in range(48):
            fx = (x - cx) / rx
            prof = max(0.0, 1 - fx * fx) ** 0.6
            half = prof * thick
            dy = y - cy
            if abs(dy) > half + 0.4:
                continue
            if hash01(x, y, 6) > 0.52 + 0.42 * prof:
                continue                       # ragged, soft (still-transparent) edge
            if dy <= -half + 1.0:
                base = "S2"                    # cool shadowed top
            elif dy >= half - 1.3:
                base = "S5" if prof > 0.55 else "S4"   # warm sunset-lit belly
            else:
                base = "S3"                    # rose body
            B[y, x] = PALETTE[base]
    for x in range(cx - rx, cx + rx + 1):      # a lit crest thread catching last light
        prof = max(0.0, 1 - ((x - cx) / rx) ** 2) ** 0.6
        yy = cy - int(prof * thick)
        if 0 <= x < 48 and 0 <= yy < TILE and prof > 0.35 and hash01(x, yy, 10) > 0.5:
            B[yy, x] = PALETTE["W0"]
    return B


_CLOUD_SOFT = _cloud_soft_strip()
_register("cloud_soft_l", _cloud_slice(_CLOUD_SOFT, 0))
_register("cloud_soft_m", _cloud_slice(_CLOUD_SOFT, 16))
_register("cloud_soft_r", _cloud_slice(_CLOUD_SOFT, 32))


@tile("bat_soft")
def _bat_soft(A, gx, gy):
    # Transparent-bg bat pair (BG_Mid) so it glides over the dusk sky inside the
    # window without a base-tone patch. Two dark silhouettes at different depths.
    A[:] = BLACK
    for dx, dy in _BAT:
        _put(A, 9 + dx, 6 + dy, "K1")
    for dx, dy in _BAT:
        _put(A, 4 + dx, 11 + dy, "K0")


# ===========================================================================
# CELESTIAL + DISTANT SILHOUETTE  (round-6 "real view": fill the upper 65% of
# the 800x600 frame -- the WHOLE map height is on screen, not a 320x224 window.
# All of these are TRANSPARENT-bg overlays for BG_Mid so they composite over the
# BG_Far sky ramp with no base-tone patch, exactly like cloud_soft / bat_soft.)
# ===========================================================================
def _build_moon() -> np.ndarray:
    """A big low crepuscular moon (3x3 = 48x48): pale cool disc, a soft gibbous
    terminator (lit upper-left, shaded lower-right), a couple of faint craters
    and a dithered cool halo -- all on a transparent (black) background so it
    hangs in the indigo upper sky. The hero of the upper vista."""
    B = np.zeros((48, 48, 3), np.uint8)          # black == transparent
    cx, cy, rad = 23, 23, 19
    for y in range(48):
        for x in range(48):
            dx, dy = x - cx, y - cy
            d2 = dx * dx + dy * dy
            if d2 <= rad * rad:
                # light from the upper-left; soft mottled maria across the face
                lum = 0.60 - 0.42 * (dx / rad) - 0.42 * (dy / rad)
                lum += (hash01(x, y, 400) - 0.5) * 0.14
                if lum > 0.92:
                    t = "W2"                      # brilliant lit crown
                elif lum > 0.60:
                    t = "W1"
                elif lum > 0.34:
                    t = "C0"                      # cream body
                else:
                    t = "RM"                      # cool shaded limb (terminator)
                B[y, x] = PALETTE[t]
            else:
                d = math.sqrt(d2)                 # dithered cool halo, thinning out
                if d < rad + 7:
                    falloff = 1.0 - (d - rad) / 7.0
                    if hash01(x, y, 401) < 0.30 * falloff:
                        B[y, x] = PALETTE["RC"]   # cold blue glow (despeckle-protected)
    # faint craters: >=2px cool-tan blobs so despeckle keeps them
    for mx, my, mr in [(18, 21, 3), (30, 27, 2), (26, 15, 2), (15, 14, 2)]:
        for yy in range(my - mr, my + mr):
            for xx in range(mx - mr, mx + mr):
                if (xx - mx) ** 2 + (yy - my) ** 2 <= mr * mr and \
                        (xx - cx) ** 2 + (yy - cy) ** 2 <= (rad - 2) ** 2:
                    B[yy, xx] = PALETTE["C1"]
    return B


register_block("moon", 3, 3, _build_moon)


@tile("star_cluster_a")
def _star_cluster_a(A, gx, gy):
    # Transparent star cluster (BG_Mid): a few faint pin-pricks in protected
    # accent colours (survive despeckle) so the high sky isn't an empty band.
    A[:] = BLACK
    _put(A, 4, 3, "W2"); _put(A, 11, 6, "W1"); _put(A, 7, 12, "RC")


@tile("star_cluster_b")
def _star_cluster_b(A, gx, gy):
    A[:] = BLACK
    _put(A, 3, 9, "W1"); _put(A, 9, 4, "W2")
    _put(A, 13, 12, "RM"); _put(A, 6, 7, "RC")


def _cloud_high_strip() -> np.ndarray:
    """A 48x16 COOL high cloud on a transparent bg (BG_Mid): moonlit cool rim on
    top (RC), purple body (S2), dark cool underside (S1). Distinct from the warm
    horizon clouds -- these ride high in the indigo sky at different altitudes."""
    B = np.zeros((TILE, 48, 3), np.uint8)
    cx, cy, rx, thick = 24, 8, 21, 3
    for y in range(TILE):
        for x in range(48):
            fx = (x - cx) / rx
            prof = max(0.0, 1 - fx * fx) ** 0.6
            half = prof * thick
            dy = y - cy
            if abs(dy) > half + 0.4:
                continue
            if hash01(x, y, 6) > 0.52 + 0.40 * prof:
                continue                          # ragged soft edge (stays transparent)
            if dy <= -half + 1.0:
                base = "RC"                       # cool moonlit crown
            elif dy >= half - 1.2:
                base = "S1"                       # dark cool underside
            else:
                base = "S2"                       # purple body
            B[y, x] = PALETTE[base]
    for x in range(cx - rx, cx + rx + 1):         # a cool rim thread on the crest
        prof = max(0.0, 1 - ((x - cx) / rx) ** 2) ** 0.6
        yy = cy - int(prof * thick)
        if 0 <= x < 48 and 0 <= yy < TILE and prof > 0.35 and hash01(x, yy, 11) > 0.5:
            B[yy, x] = PALETTE["RM"]
    return B


_CLOUD_HIGH = _cloud_high_strip()
_register("cloud_high_l", _cloud_slice(_CLOUD_HIGH, 0))
_register("cloud_high_m", _cloud_slice(_CLOUD_HIGH, 16))
_register("cloud_high_r", _cloud_slice(_CLOUD_HIGH, 32))


def _ridge_far(A, gx, gy, salt, phase):
    # A far ridge/tree-copse line for the SECOND (most distant) depth plane. Sits
    # high in the sky, well above the near forest, so with the sky gap between
    # them the composition reads with 3 planes. Deliberately LOW CONTRAST: a
    # violet only a touch lighter than the S2 sky (atmospheric perspective) --
    # an ordered S2->S3 dither with a cool RM rim, transparent above the crest.
    A[:] = BLACK
    for x in range(TILE):
        gxx = gx + x
        crest = 5 + int(3 * hash01(gxx, 0, salt)) + int(2 + 2 * math.sin(gxx * 0.35 + phase))
        crest = max(2, min(13, crest))
        for y in range(crest, TILE):
            t = (y - crest) / max(1, TILE - crest)     # lighter at the crest, melts down
            A[y, x] = PALETTE[bayer_dither(gxx, gy + y, "S3", "S2", 0.35 + 0.5 * t)]
        if hash01(gxx, 0, salt + 9) > 0.45:            # cool rim catching the sky
            A[crest, x] = PALETTE["RM"]


@tile("ridge_far_a")
def _ridge_far_a(A, gx, gy):
    _ridge_far(A, gx, gy, 51, 0.0)


@tile("ridge_far_b")
def _ridge_far_b(A, gx, gy):
    _ridge_far(A, gx, gy, 57, 2.6)


@tile("ridge_haze")
def _ridge_haze(A, gx, gy):
    # The body row UNDER the ridge crest: an ordered fade from the ridge tone
    # (S3) at the top back to the S2 sky at the bottom, so the distant ridge
    # dissolves into the dusk instead of ending on a hard line.
    for y in range(TILE):
        t = y / (TILE - 1)
        for x in range(TILE):
            A[y, x] = PALETTE[bayer_dither(gx + x, gy + y, "S3", "S2", 0.15 + 0.85 * t)]


@tile("campus_far")
def _campus_far(A, gx, gy):
    # A distant campus silhouette poking above the far ridge: a slender bell
    # tower (campanario) with a pitched cap and a couple of lit window slits,
    # plus a sliver of adjoining roofline. Same desaturated violet as the ridge
    # (barely lighter than the sky) so it recedes; RM rim, tiny warm windows.
    A[:] = BLACK
    # adjoining low roofline (right side), a touch lighter than sky
    for x in range(9, TILE):
        for y in range(11, TILE):
            A[y, x] = PALETTE["S3" if hash01(gx + x, gy + y, 60) > 0.4 else "S2"]
    for x in range(9, TILE):                       # roof ridge cap
        A[10, x] = PALETTE["RM"] if hash01(gx + x, 0, 61) > 0.5 else PALETTE["S3"]
    # bell tower (cols 3..7), rising from row 3 to the bottom
    for y in range(4, TILE):
        for x in range(3, 8):
            A[y, x] = PALETTE["S3" if (x in (3, 7) or hash01(gx + x, gy + y, 62) > 0.5) else "S2"]
    for x in range(2, 9):                           # pitched cap
        A[3, x] = PALETTE["RM"]
    A[2, 5] = PALETTE["RM"]; A[1, 5] = PALETTE["RC"]   # finial
    _put(A, 5, 8, "W0"); _put(A, 5, 12, "W0")          # faint warm window slits
    _put(A, 4, 8, "F0"); _put(A, 6, 8, "F0")           # window jambs (darker)
    return


# ===========================================================================
# FAR FOREST  (violet silhouette, hazy cool rim on crowns)
# ===========================================================================
def _forest_top(A, gx, gy, salt, phase):
    # Everything above the ragged crown stays TRANSPARENT (black) so the warm
    # horizon band behind the treeline shows through the gaps between the crowns
    # -- the sunset silhouettes the woods instead of the old cool-purple patch
    # (which fought the warm sky now sitting right behind it).
    A[:] = BLACK
    for x in range(TILE):
        gxx = gx + x
        crown = 3 + int(4 * hash01(gxx, 0, salt)) + int(2 + 2 * math.sin(gxx * 0.5 + phase))
        crown = max(1, min(13, crown))
        for y in range(crown, TILE):
            A[y, x] = PALETTE["K1" if hash01(gxx, gy + y, 7) < 0.16 else "F0"]
    # cool rim-light on the topmost F0 pixel of each column (cold edge against
    # the warm sky -> the crepuscular rim-light the checklist calls for)
    f0 = PALETTE["F0"]
    for x in range(TILE):
        for y in range(TILE):
            if tuple(A[y, x]) == f0:
                if hash01(gx + x, y, 302) > 0.5:
                    A[y, x] = PALETTE["RC" if hash01(gx + x, y, 303) > 0.5 else "V3"]
                break


@tile("forest_top_a")
def _ft_a(A, gx, gy):
    _forest_top(A, gx, gy, 31, 0.0)


@tile("forest_top_b")
def _ft_b(A, gx, gy):
    _forest_top(A, gx, gy, 37, 2.1)


@tile("forest_top_c")
def _ft_c(A, gx, gy):
    _forest_top(A, gx, gy, 41, 4.2)


@tile("forest_fill")
def _forest_fill(A, gx, gy):
    # The DITHERED TRANSITION row between the dark treeline and the green meadow
    # below it: an ordered (Bayer) fade from violet tree mass (F0) at the top to
    # dusk GREEN (V1) at the bottom -- so the woods melt DOWN into the lawn (not
    # into a blue haze band, which read as a stacked stripe). A little foliage
    # texture + the odd haze fleck keeps it organic.
    for y in range(TILE):
        t = y / (TILE - 1)
        for x in range(TILE):
            base = bayer_dither(gx + x, gy + y, "F0", "V1", 0.20 + 0.6 * t)
            r = hash01(gx + x, gy + y, 7)
            if r < 0.12:
                base = "V0"                       # dark foliage clump
            elif r > 0.95:
                base = "S1"                        # sparse haze fleck (atmosphere)
            A[y, x] = PALETTE[base]


@tile("forest_canopy")
def _forest_canopy(A, gx, gy):
    # The top row of the forest body, just under the crown: catches a little of
    # the sunset filtering over the treetops (warm O1 flecks up high) and carries
    # extra lit-foliage so the horizon-forest boundary has depth, not a hard edge.
    for y in range(TILE):
        for x in range(TILE):
            r = hash01(gx + x, gy + y, 7)
            if y < 3 and hash01(gx + x, gy + y, 310) > 0.86:
                A[y, x] = PALETTE["O1"]           # warm sunset caught on treetops
            elif r < 0.14:
                A[y, x] = PALETTE["K1"]
            elif r < 0.55:
                A[y, x] = PALETTE["F0"]
            elif r < 0.78:
                A[y, x] = PALETTE["V0"]
            else:
                A[y, x] = PALETTE["V1"]


@tile("meadow_far")
def _meadow_far(A, gx, gy):
    # The distant BACKGROUND lawn at the FOOT of the woods, bridging the treeline
    # to the near ground -- woods -> lawn -> foreground, like the vignette.
    # ROUND-7 (user legibility fix): deliberately DARK + COOL (violet-desaturated)
    # so it RECEDES and never competes with the lit walkable turf in front of it.
    # Biased to the BOTTOM of the veg ramp (V0/V1) with cool violet recession
    # (F0) and a whisper of haze (S1) along the top -- NO bright V3 blades (those
    # now belong exclusively to the walkable floor, so the eye reads "background"
    # here and "floor" there).
    for y in range(TILE):
        for x in range(TILE):
            r = hash01(gx + x, gy + y, 330)
            if y < 2 and r > 0.55:
                base = "S1"                       # cool haze melting up into the treeline
            elif r < 0.40:
                base = "V1"                       # dusk grass (mid-dark)
            elif r < 0.66:
                base = "V0"                       # shadow tuft
            elif r < 0.84:
                base = "F0"                        # cool violet recession fleck
            else:
                base = "V2"                        # the occasional dim catch of light
            A[y, x] = PALETTE[base]


@tile("meadow_base")
def _meadow_base(A, gx, gy):
    # The row of distant lawn that TOUCHES the walkable ground plane (placed at
    # row 34, directly above the floor). Same dark, cool recession as meadow_far,
    # but its bottom 2px deepen to a CONTACT SHADOW (V0 -> K1): the subtle dark
    # crease where the receding background meets the floor plane, reinforcing the
    # separation from the lit turf rim right below it (round-7 contact-shadow
    # directive). The top 14px are identical to meadow_far so rows 33/34 stack
    # with no seam.
    _meadow_far(A, gx, gy)
    for x in range(TILE):
        A[TILE - 2, x] = PALETTE["V0" if hash01(gx + x, TILE - 2, 331) > 0.4 else "K1"]
        A[TILE - 1, x] = PALETTE["K1"]


@tile("forest_gap")
def _forest_gap(A, gx, gy):
    for y in range(TILE):
        gapw = 2 + int(1.6 * (1 + math.sin(y * 0.4)))
        for x in range(TILE):
            if abs(x - 8) < gapw and y < 12:
                A[y, x] = PALETTE["S3" if hash01(gx + x, gy + y, 8) < 0.6 else "S2"]
            else:
                A[y, x] = PALETTE["K1" if hash01(gx + x, gy + y, 7) < 0.18 else "F0"]
    for x in range(TILE):                     # undergrowth catching last light
        if hash01(gx + x, 0, 57) > 0.55:
            _put(A, x, 15, "V1")
            if hash01(gx + x, 1, 57) > 0.7:
                _put(A, x, 14, "V2")


# ===========================================================================
# MID VEGETATION  (hedges + big tree)
# ===========================================================================
@tile("hedge_fill")
def _hedge_fill(A, gx, gy):
    for y in range(TILE):
        for x in range(TILE):
            r = hash01(gx + x, gy + y, 103)
            if r > 0.82:
                t = "V2"
            elif r < 0.12:
                t = "V0"
            else:
                t = "V1"
            A[y, x] = PALETTE[t]


def _hedge_top(A, gx, gy, salt):
    for x in range(TILE):
        gxx = gx + x
        top = 2 + int(2.5 * (1 + math.sin(gxx * 0.5 + salt)))
        for y in range(TILE):
            if y < top:
                A[y, x] = PALETTE["V0"]
            elif y <= top + 1:
                if hash01(gxx, y, 106 + salt) > 0.82:
                    A[y, x] = PALETTE["RC"]           # cool dusk highlight on crest
                else:
                    A[y, x] = PALETTE["V3" if hash01(gxx, y, 107) > 0.5 else "V2"]
            else:
                r = hash01(gxx, gy + y, 103 + salt)
                A[y, x] = PALETTE["V2" if r > 0.78 else ("V0" if r < 0.12 else "V1")]


@tile("hedge_top_a")
def _hedge_top_a(A, gx, gy):
    _hedge_top(A, gx, gy, 0)


@tile("hedge_top_b")
def _hedge_top_b(A, gx, gy):
    _hedge_top(A, gx, gy, 2)


@tile("hedge_flower")
def _hedge_flower(A, gx, gy):
    _hedge_fill(A, gx, gy)
    for dx, dy in [(0, 0), (1, 0), (0, 1), (-1, 0)]:
        _put(A, 8 + dx, 7 + dy, "P0")
    _put(A, 9, 6, "P1"); _put(A, 7, 8, "V2")
    _put(A, 4, 11, "P0"); _put(A, 5, 11, "P1")


@tile("bush")
def _bush(A, gx, gy):
    # A single rounded dusk shrub, rooted at the tile bottom (transparent corners
    # -> composites over the lawn/ground). Used as a PUNCTUAL meadow accent rather
    # than a continuous hedge band, and with a rounded volume it never reads as a
    # floating green cube. Dusk-lit top-right, dark undersides.
    A[:] = BLACK
    cx, cy, rx, ry = 8, 11, 7, 6
    for y in range(TILE):
        for x in range(TILE):
            nx = (x - cx) / rx
            ny = (y - cy) / ry
            edge = 1.0 + 0.22 * (hash01(x, y, 340) - 0.5) * 2
            if nx * nx + ny * ny <= edge and y <= 15:
                r = hash01(gx + x, gy + y, 341)
                lum = 0.5 - 0.32 * ny - 0.16 * nx + (r - 0.5) * 0.4
                # ROUND-7: ground-hugging shrub keeps its saturation but its
                # luminosity is CAPPED BELOW the lit walkable turf -- the lit tone
                # tops out at V2 (only a rare, sparse V3 tip), with cool violet F0
                # in the deep core shade for dusk recession. It must never read as
                # bright as the floor the player stands on.
                if lum > 0.80 and hash01(x, y, 344) > 0.6:
                    t = "V3"                      # rare warm tip (sparse)
                elif lum > 0.50:
                    t = "V2"
                elif lum > 0.28:
                    t = "V1"
                elif lum > 0.12:
                    t = "V0"
                else:
                    t = "F0"                      # cool violet core shadow
                A[y, x] = PALETTE[t]
    if hash01(gx, 0, 342) > 0.5:                  # a couple of dusk berries/flowers
        _put(A, 6, 9, "P0"); _put(A, 10, 8, "P1")


def _build_tree() -> np.ndarray:
    B = np.zeros((64, 64, 3), np.uint8)       # zeros == black == empty corners
    cx, cy, rx, ry = 32, 25, 27, 23
    for y in range(64):
        for x in range(64):
            nx = (x - cx) / rx
            ny = (y - cy) / ry
            d = nx * nx + ny * ny
            edge = (1.0 + 0.30 * (hash01(x // 2, y // 2, 80) - 0.5) * 2
                    + 0.12 * math.sin(x * 0.6) + 0.12 * math.sin(y * 0.7))
            if d <= edge:
                r = hash01(x, y, 81)
                lum = 0.52 - 0.34 * ny - 0.20 * nx + (r - 0.5) * 0.42
                if d > edge - 0.16 and lum > 0.60 and hash01(x, y, 82) > 0.5:
                    t = "V3"                  # dusk-lit rim tips (upper-right)
                elif lum > 0.60:
                    t = "V2"
                elif lum > 0.40:
                    t = "V1"
                else:
                    t = "V0"
                B[y, x] = PALETTE[t]
    # trunk + a couple of roots
    for y in range(43, 64):
        for x in range(29, 35):
            r = hash01(x, y, 83)
            B[y, x] = PALETTE["O0" if (x < 31 or r < 0.32) else ("O1" if r < 0.8 else "O2")]
    for (sx, sy, dx) in [(29, 60, -1), (34, 60, 1)]:
        x, y = sx, sy
        for _ in range(4):
            _put(B, x, y, "O0"); x += dx; y += 1
    return B


register_block("tree_c", 4, 4, _build_tree, sep="")


def _trunk(A, gx, gy, knot):
    A[:] = BLACK
    for y in range(TILE):
        for x in range(4, 12):
            r = hash01(gx + x, gy + y, 83)
            A[y, x] = PALETTE["O0" if (x < 7 or r < 0.30) else ("O1" if r < 0.78 else "O2")]
    for y in range(0, TILE, 3):               # bark grooves
        _put(A, 5, y, "O0"); _put(A, 9, y, "O0")
    if knot:
        _put(A, 8, 8, "O0"); _put(A, 8, 7, "K1"); _put(A, 9, 8, "O0")


@tile("tree_trunk_a")
def _trunk_a(A, gx, gy):
    _trunk(A, gx, gy, False)


@tile("tree_trunk_b")
def _trunk_b(A, gx, gy):
    _trunk(A, gx, gy, True)


# ===========================================================================
# PLAYABLE GROUND  (grass / dirt path / sidewalk / pebbles)
# ===========================================================================
def _grass(A, gx, gy, salt):
    for y in range(TILE):
        for x in range(TILE):
            r = hash01(gx + x, gy + y, 11 + salt)
            if r > 0.90:
                t = "V3"
            elif r > 0.60:
                t = "V2"
            elif r > 0.22:
                t = "V1"
            else:
                t = "V0"
            A[y, x] = PALETTE[t]


@tile("grass_a")
def _grass_a(A, gx, gy):
    _grass(A, gx, gy, 0)


@tile("grass_b")
def _grass_b(A, gx, gy):
    _grass(A, gx, gy, 1)


@tile("grass_c")
def _grass_c(A, gx, gy):
    _grass(A, gx, gy, 2)


@tile("grass_bald")
def _grass_bald(A, gx, gy):
    _grass(A, gx, gy, 0)
    for y in range(TILE):
        for x in range(TILE):
            if ((x - 8) / 7.0) ** 2 + ((y - 9) / 5.0) ** 2 < 1.0 and hash01(gx + x, gy + y, 104) > 0.28:
                A[y, x] = PALETTE["O1" if hash01(gx + x, gy + y, 105) > 0.5 else "G1"]


# ---------------------------------------------------------------------------
# WALKABLE turf (Terrain floor row). ROUND-7 user legibility fix: the plane the
# player stands on was indistinguishable from the background lawn (same veg
# ramp). These tiles are deliberately the LIGHTEST + WARMEST vegetation in the
# scene and carry a 2px LIT TOP EDGE (the classic platform rim), so the floor
# line reads INSTANTLY apart from the darker, cooler background (meadow_far /
# meadow_base / forest). The old ``grass_*`` above stay in the atlas as a
# background-grass reserve; only these ``grass_walk_*`` go on the walkable row.
# ---------------------------------------------------------------------------
def _grass_walk(A, gx, gy, salt):
    # Sunlit walkable turf: body biased to the TOP of the veg ramp (V2/V3
    # dominant) with a sparse warm ochre glint for warmth (moderation).
    for y in range(TILE):
        for x in range(TILE):
            r = hash01(gx + x, gy + y, 11 + salt)
            if r > 0.72:
                t = "V3"                          # lit blades (dominant)
            elif r > 0.34:
                t = "V2"                          # mid green
            elif r > 0.10:
                t = "V1"                          # sparse shadow
            else:
                t = "V0"                          # rare deep shadow
            if hash01(gx + x, gy + y, 260 + salt) > 0.93:
                t = "O2"                          # warm sunlit fleck (warmth, sparse)
            A[y, x] = PALETTE[t]
    # LIT TOP EDGE (rim): row 0 = warmest green with sparse cream glints (the
    # front lip catching the low sun); row 1 = broken lighter green so the rim
    # has body without a solid mechanical line. V3/C0/W1 are despeckle-protected
    # accents, so the rim survives the per-tile cleanup as a continuous highlight.
    for x in range(TILE):
        A[0, x] = PALETTE["C0" if hash01(gx + x, 0, 261 + salt) > 0.82 else "V3"]
        if hash01(gx + x, 1, 262 + salt) > 0.42:
            A[1, x] = PALETTE["V3"]
        if hash01(gx + x, 1, 263 + salt) > 0.93:
            A[1, x] = PALETTE["W1"]               # occasional warm crest spark


@tile("grass_walk_a")
def _grass_walk_a(A, gx, gy):
    _grass_walk(A, gx, gy, 0)


@tile("grass_walk_b")
def _grass_walk_b(A, gx, gy):
    _grass_walk(A, gx, gy, 1)


@tile("grass_walk_c")
def _grass_walk_c(A, gx, gy):
    _grass_walk(A, gx, gy, 2)


@tile("grass_walk_bald")
def _grass_walk_bald(A, gx, gy):
    # Worn dirt patch on the walkable turf (keeps the lit rim: the ellipse sits
    # in the tile interior, rows 4-14, so the top rim rows are untouched).
    _grass_walk(A, gx, gy, 0)
    for y in range(TILE):
        for x in range(TILE):
            if ((x - 8) / 7.0) ** 2 + ((y - 9) / 5.0) ** 2 < 1.0 and hash01(gx + x, gy + y, 104) > 0.28:
                A[y, x] = PALETTE["O1" if hash01(gx + x, gy + y, 105) > 0.5 else "G1"]


def _dirt(A, gx, gy, salt):
    for y in range(TILE):
        for x in range(TILE):
            r = hash01(gx + x, gy + y, 110 + salt)
            if r > 0.90:
                t = "G1"
            elif r > 0.55:
                t = "O1"
            elif r > 0.22:
                t = "O0"
            else:
                t = "K1"
            A[y, x] = PALETTE[t]
    for k in range(3):                        # scattered pebbles
        px = int(15 * hash01(gx + k * 3, salt, 111))
        py = int(15 * hash01(gy + k * 5, salt, 112))
        _put(A, px, py, "G2")


@tile("dirt_path_a")
def _dirt_a(A, gx, gy):
    _dirt(A, gx, gy, 0)


@tile("dirt_path_b")
def _dirt_b(A, gx, gy):
    _dirt(A, gx, gy, 1)


def _path_border(gy: int, y: int) -> int:
    """Ragged grass/dirt boundary column shared by both path-edge tiles."""
    return 8 + int(2.5 * math.sin((gy + y) * 0.7)) + int((hash01(gy + y, 0, 120) - 0.5) * 4)


@tile("path_edge_l")
def _path_edge_l(A, gx, gy):
    # grass on the LEFT, dirt on the RIGHT (ragged boundary)
    for y in range(TILE):
        border = _path_border(gy, y)
        for x in range(TILE):
            if x < border:
                A[y, x] = PALETTE["V2" if hash01(gx + x, gy + y, 11) > 0.55 else "V1"]
            else:
                A[y, x] = PALETTE["O1" if hash01(gx + x, gy + y, 110) > 0.5 else "O0"]


@tile("path_edge_r")
def _path_edge_r(A, gx, gy):
    # dirt on the LEFT, grass on the RIGHT
    for y in range(TILE):
        border = _path_border(gy, y)
        for x in range(TILE):
            if x < border:
                A[y, x] = PALETTE["O1" if hash01(gx + x, gy + y, 110) > 0.5 else "O0"]
            else:
                A[y, x] = PALETTE["V2" if hash01(gx + x, gy + y, 11) > 0.55 else "V1"]


def _slab(A, gx, gy, salt):
    for y in range(TILE):
        for x in range(TILE):
            b = 0.5 + 0.5 * hash01((gx + x) // 13, (gy + y) // 9, 111 + salt)
            b += (hash01(gx + x, gy + y, 112) - 0.5) * 0.22
            if b < 0.30:
                t = "G0"
            elif b < 0.55:
                t = "G1"
            elif b < 0.82:
                t = "G2"
            else:
                t = "G3"
            A[y, x] = PALETTE[t]
    for y in range(TILE):                     # joints on top+left -> paving grid
        A[y, 0] = PALETTE["G0"]
    for x in range(TILE):
        A[0, x] = PALETTE["G0"]


@tile("sidewalk_slab_a")
def _slab_a(A, gx, gy):
    _slab(A, gx, gy, 0)


@tile("sidewalk_slab_b")
def _slab_b(A, gx, gy):
    _slab(A, gx, gy, 3)


@tile("sidewalk_slab_c")
def _slab_c(A, gx, gy):
    _slab(A, gx, gy, 6)


@tile("sidewalk_crack")
def _sidewalk_crack(A, gx, gy):
    _slab(A, gx, gy, 0)
    x, y = 5, 2
    for _ in range(12):
        _put(A, x, y, "G0")
        y += 1
        x += 1 if hash01(x, y, 203) > 0.5 else 0
        if y >= TILE:
            break
    _put(A, 9, 13, "V2"); _put(A, 9, 12, "V3")   # weed from the crack


@tile("sidewalk_moss")
def _sidewalk_moss(A, gx, gy):
    _slab(A, gx, gy, 3)
    for y in range(TILE):                     # moss creeping the left joint
        if hash01(gx, gy + y, 143) > 0.5:
            _put(A, 1, y, "V1" if hash01(gx, gy + y, 145) > 0.5 else "V2")
    for x in range(TILE):                     # and the top joint
        if hash01(gx + x, gy, 146) > 0.55:
            _put(A, x, 1, "V2")


@tile("sidewalk_broken_corner")
def _sidewalk_broken_corner(A, gx, gy):
    _slab(A, gx, gy, 6)
    for dx, dy in [(0, 0), (1, 0), (0, 1), (2, 0), (1, 1), (0, 2), (2, 1)]:
        _put(A, dx, dy, "G0")                 # chipped dark bite
    _put(A, 3, 0, "G3"); _put(A, 0, 3, "G3")  # exposed light edge


@tile("pebbles")
def _pebbles(A, gx, gy):
    for y in range(TILE):
        for x in range(TILE):
            A[y, x] = PALETTE["G1" if hash01(gx + x, gy + y, 130) > 0.4 else "G0"]
    for k in range(6):
        px = int(15 * hash01(gx + k * 7, 0, 131))
        py = int(15 * hash01(gy + k * 5, 0, 132))
        _put(A, px, py, "G3" if hash01(px, py, 133) > 0.5 else "G0")
        _put(A, px, py + 1, "G0")


def _subsoil(A, gx, gy, deep: bool):
    # Underground soil under the walkable floor. Darkens toward the bottom (a
    # Bayer fade), with scattered stones and root threads -> reads as packed
    # earth/bedrock, not the flat brown "cork" of before. `deep` = the lowest
    # row (darker, stonier).
    top, bot = ("O0", "K1") if not deep else ("K1", "K0")
    for y in range(TILE):
        t = y / (TILE - 1)
        for x in range(TILE):
            A[y, x] = PALETTE[bayer_dither(gx + x, gy + y, top, bot, 0.25 + 0.55 * t)]
    if not deep:                                  # root threads reaching down (upper soil)
        for sx in (3, 11):
            x, y = sx, 0
            for _ in range(TILE):
                _put(A, x, y, "O0")
                y += 1
                x += 1 if hash01(gx + x, gy + y, 353) > 0.6 else 0
                if y >= TILE:
                    break
    for k in range(5 if not deep else 3):         # embedded stones
        px = int(15 * hash01(gx + k * 4, 0, 351))
        py = int(15 * hash01(gy + k * 6, 0, 352))
        _put(A, px, py, "G1" if not deep else "G0")
        _put(A, min(15, px + 1), py, "G0")
        _put(A, px, min(15, py + 1), "G0")


@tile("subsoil_top")
def _subsoil_top(A, gx, gy):
    _subsoil(A, gx, gy, deep=False)


@tile("subsoil_deep")
def _subsoil_deep(A, gx, gy):
    # The DEEPEST row at the very bottom of the frame: a smooth fade to near-black
    # with NO stones/roots and no stamped dither pattern -> it reads as the ground
    # receding into darkness (a continuation of the subsoil), not a patterned void
    # band. Just a whisper of K1 up top blending into solid K0.
    for y in range(TILE):
        for x in range(TILE):
            if y < 2:
                c = "K1"
            elif y < 4:
                c = bayer_dither(gx + x, gy + y, "K1", "K0", (y - 2) / 2.0)
            else:
                c = "K0"
            A[y, x] = PALETTE[c]


# ===========================================================================
# HASTIAL  (6x6 = 96x96): ochre gable house, sheet roof, oculus, arch
# ===========================================================================
def _build_hastial() -> np.ndarray:
    W = H = 96
    B = np.zeros((H, W, 3), np.uint8)
    HX0, HX1 = 12, 84
    PEAK_X, PEAK_Y = 48, 6
    WALL_TOP = 46
    GROUND = 90

    def wall_tone(x, y):
        tx = (x - HX0) / (HX1 - HX0)
        ty = (y - WALL_TOP) / (GROUND - WALL_TOP)
        lum = 0.56 + 0.16 * tx - 0.12 * ty
        # eave (roof-overhang) shadow: a band hugging the top of the WALL BODY
        # only. The gable triangle sits above WALL_TOP and catches open sky, so
        # it must NOT be darkened (else it reads brown instead of mustard).
        es_span = 10 + 3 * hash01(x, 0, 44)
        if y < WALL_TOP:
            es = 0.0
        else:
            es = max(0.0, min(1.0, (WALL_TOP + es_span - y) / es_span))
        lum -= 0.20 * es * es
        # stucco mottling: the exact 3-octave cluster field art_lib.mottle was
        # extracted from (salts 45/46/47) -- reuse it instead of re-inlining.
        lum += mottle(x, y, salt=45)
        base_prox = max(0.0, (ty - 0.42) / 0.58)
        corner = max(0.0, 1.0 - min(tx, 1.0 - tx) / 0.20)
        if hash01(x // 5, y // 4, 48) > 0.60:
            lum -= (0.10 + 0.16 * corner) * base_prox
        if hash01(x // 6, y // 3, 49) > 0.90:
            lum -= 0.10 * base_prox
        if lum < 0.34:
            return "O0"
        if lum < 0.54:
            return "O1"
        if lum < 0.78:
            return "O2"
        return "O3"

    # gable triangle
    for y in range(PEAK_Y, WALL_TOP):
        frac = (y - PEAK_Y) / (WALL_TOP - PEAK_Y)
        halfw = frac * ((HX1 - HX0) / 2)
        for x in range(int(PEAK_X - halfw), int(PEAK_X + halfw)):
            B[y, x] = PALETTE[wall_tone(x, y)]
    # wall body
    for y in range(WALL_TOP, GROUND):
        for x in range(HX0, HX1):
            B[y, x] = PALETTE[wall_tone(x, y)]

    # roof trim (terracotta sheet) + cream fascia following both slopes
    ROOF_SHEET_H = 4                          # terracotta sheet band thickness
    FASCIA_H = 2                              # cream cenefa (fascia) board thickness

    def roof_line(x):
        if x <= PEAK_X:
            t = (x - (HX0 - 6)) / (PEAK_X - (HX0 - 6))
        else:
            t = (x - (HX1 + 6)) / (PEAK_X - (HX1 + 6))
        t = max(0.0, min(1.0, t))
        return int(PEAK_Y + (WALL_TOP - PEAK_Y) * (1 - t))

    for x in range(HX0 - 6, HX1 + 6):
        ry = roof_line(x)
        for yy in range(ry, ry + ROOF_SHEET_H):
            if not (0 <= x < W):
                continue
            tone = "R2" if yy == ry else ("R1" if yy < ry + 2 else "R0")
            if (x % 4 == 0) and yy > ry:
                tone = "R0"                   # corrugation groove
            rp = hash01(x // 4, yy, 201)
            if rp > 0.93 and yy >= ry + 1:
                tone = "O1"                   # rust bloom
            elif rp < 0.05 and yy >= ry + 2:
                tone = "V1"                   # moss on the sheet
            B[yy, x] = PALETTE[tone]
        for yy in range(ry + ROOF_SHEET_H, ry + ROOF_SHEET_H + FASCIA_H):  # cream fascia
            if 0 <= x < W:
                B[yy, x] = PALETTE["C0" if yy < ry + ROOF_SHEET_H + 1 else "C1"]

    # OCULUS: stone ring + dusk sky seen through
    ocx, ocy, orad = PEAK_X, 28, 8
    for y in range(ocy - orad - 1, ocy + orad + 2):
        for x in range(ocx - orad - 1, ocx + orad + 2):
            d = (x - ocx) ** 2 + (y - ocy) ** 2
            if d <= (orad - 2) ** 2:
                rel = (y - (ocy - orad)) / (2 * orad)
                B[y, x] = PALETTE["S1" if rel < 0.36 else ("S2" if rel < 0.62 else "S3")]
            elif d <= orad ** 2:
                B[y, x] = PALETTE["C0" if (x - ocx + y - ocy) > 0 else "C1"]
    for x in range(ocx - 5, ocx + 5):         # leaves peeking in top
        yy = ocy - orad + 2 + int(2 * hash01(x, 0, 51))
        if (x - ocx) ** 2 + (yy - ocy) ** 2 <= (orad - 3) ** 2:
            B[yy, x] = PALETTE["V1"]

    # ARCH doorway: pointed opening, dark passage, warm far doorway
    acx, ahw = PEAK_X, 14
    spring_y, apex_y = 66, 48
    base_y = GROUND

    def arch_top(x):
        frac = abs(x - acx) / ahw
        if frac > 1:
            return None
        return int(spring_y - (spring_y - apex_y) * (1 - frac ** 1.7))

    far_cx, far_cy = acx, 78
    far_hw, far_hh = 4, 8
    for x in range(acx - ahw - 1, acx + ahw + 2):
        yt = arch_top(x)
        if yt is None:
            continue
        for y in range(yt, base_y):
            if abs(x - acx) >= ahw - 1 or y <= yt + 1:
                B[y, x] = PALETTE["O1" if hash01(x, y, 65) > 0.4 else "O0"]   # jamb
                continue
            dx = x - far_cx
            dy = y - far_cy
            if abs(dx) <= far_hw and abs(dy) <= far_hh and abs(dx) / far_hw + max(0, -dy) / far_hh < 1.05:
                # warm far doorway
                core = abs(dx) < far_hw - 1 and dy > -far_hh + 2
                B[y, x] = PALETTE["W1" if core else "W0"]
            else:
                # dark tunnel with a converging warm floor thread
                thread = abs(dx) <= 1 and y > far_cy
                if thread and hash01(x, y, 62) < 0.6:
                    B[y, x] = PALETTE["S5" if y > far_cy + 4 else "W0"]
                elif y < far_cy and hash01(x, y, 66) > 0.85:
                    B[y, x] = PALETTE["R0"]   # faint warm deep wall
                else:
                    B[y, x] = PALETTE["K0" if hash01(x, y, 61) > 0.3 else "K1"]
    # stone frame around the far doorway
    for y in range(far_cy - far_hh, far_cy + far_hh + 1):
        for x in range(far_cx - far_hw - 1, far_cx + far_hw + 2):
            dx = x - far_cx
            if abs(dx) == far_hw + 1 and -far_hh < (y - far_cy) <= far_hh:
                if arch_top(x) is not None and y >= arch_top(x):
                    B[y, x] = PALETTE["C1"]

    # ivy on the left corner
    for y in range(WALL_TOP - 2, GROUND):
        for x in range(HX0 - 1, HX0 + 5 + int(2 * math.sin(y * 0.4))):
            if x >= HX0 - 1 and hash01(x, y, 71) > 0.52:
                B[y, x] = PALETTE["V1" if hash01(x, y, 72) > 0.5 else "V2"]

    # a few hairline cracks (avoid the arch mouth)
    rng = np.random.default_rng(11)

    def clear(x, y):
        return not (acx - ahw < x < acx + ahw and y > apex_y)

    for _ in range(6):
        x = int(rng.integers(HX0 + 6, HX1 - 6))
        y = int(rng.integers(WALL_TOP + 4, GROUND - 16))
        for _ in range(int(rng.integers(8, 18))):
            if HX0 < x < HX1 and WALL_TOP < y < GROUND and clear(x, y):
                B[y, x] = PALETTE["O0" if hash01(x, y, 202) > 0.35 else "K1"]
            if hash01(x, y, 203) > 0.22:
                y += 1
            x += int(rng.integers(-1, 2))

    # 2 spalls (chipped render -> pale plaster)
    for (sx, sy, rw, rh) in [(HX1 - 10, GROUND - 26, 3, 2), (HX0 + 8, 60, 2, 2)]:
        for dy in range(-rh, rh + 1):
            for dx in range(-rw, rw + 1):
                if (dx / rw) ** 2 + (dy / rh) ** 2 > 1.0:
                    continue
                x, y = sx + dx, sy + dy
                if not (HX0 < x < HX1 and WALL_TOP < y < GROUND and clear(x, y)):
                    continue
                if dy >= rh - 1:
                    B[y, x] = PALETTE["O0"]
                elif (dx / rw) ** 2 + (dy / rh) ** 2 > 0.58:
                    B[y, x] = PALETTE["O1"]
                else:
                    B[y, x] = PALETTE["PL" if hash01(x, y, 204) > 0.25 else "O2"]

    # moss + weeds reclaiming the base
    for x in range(HX0, HX1):
        if acx - ahw < x < acx + ahw:
            continue
        r = hash01(x, 0, 205)
        if r > 0.42:
            mh = 2 + int(2 * hash01(x, 1, 206))
            for i in range(mh):
                _put(B, x, GROUND - 1 - i, "V1" if i < mh - 1 else "V2")
        if r > 0.80:
            hh = 3 + int(2 * hash01(x, 2, 82))
            for i in range(hh):
                _put(B, x, GROUND - 1 - i, "V2" if i < hh - 1 else "V3")

    return B


register_block("hast", 6, 6, _build_hastial)


@tile("arch_glow_top")
def _arch_glow_top(A, gx, gy):
    # top half of the warm far doorway: pointed arch + foliage silhouette
    A[:] = BLACK
    cx = 8
    for y in range(TILE):
        hw = 3 + int(4 * (y / TILE))
        for x in range(TILE):
            dx = x - cx
            if abs(dx) <= hw:
                if abs(dx) >= hw - 1 or y < 2:
                    A[y, x] = PALETTE["C1"]           # stone reveal / top
                else:
                    A[y, x] = PALETTE["W1" if abs(dx) < hw - 3 else "W0"]
    for x in range(cx - 4, cx + 5):           # leaves silhouetted at the top
        if hash01(gx + x, 0, 51) > 0.5:
            _put(A, x, 2, "V0")


@tile("arch_glow_bottom")
def _arch_glow_bottom(A, gx, gy):
    # bottom half: warm core fading to a dark stone base
    A[:] = BLACK
    cx, hw = 8, 7
    for y in range(TILE):
        for x in range(TILE):
            dx = x - cx
            if abs(dx) <= hw:
                if y >= TILE - 2:
                    A[y, x] = PALETTE["O0"]           # threshold shadow
                elif abs(dx) >= hw - 1:
                    A[y, x] = PALETTE["C1"]
                else:
                    core = abs(dx) < hw - 3 and y < 10
                    A[y, x] = PALETTE["W1" if core else ("W0" if y < 12 else "S5")]


def _ivy(A, gx, gy, salt):
    A[:] = BLACK
    for y in range(TILE):
        cx = 8 + int(3 * math.sin(y * 0.5 + salt))
        for x in range(cx - 2, cx + 3):
            if hash01(gx + x, gy + y, 71 + salt) > 0.45:
                A[y, x] = PALETTE["V1" if hash01(gx + x, gy + y, 72) > 0.5 else "V2"]
        if y % 4 == 0:
            _put(A, cx + 2, y, "V3")          # a dusk-lit leaf
        if y % 5 == 0:
            _put(A, cx - 2, y, "V0")


@tile("ivy_a")
def _ivy_a(A, gx, gy):
    _ivy(A, gx, gy, 0)


@tile("ivy_b")
def _ivy_b(A, gx, gy):
    _ivy(A, gx, gy, 3)


# ---------------------------------------------------------------------------
# ARCH FRONT FACE  (FG_Overlay): the near pointed-arch stone reveal that draws
# IN FRONT of the player, 3 cols x 2 rows. Void (black) inside the opening and
# outside the outer silhouette so only the stone jambs/crown occlude.
# ---------------------------------------------------------------------------
def _build_arch_front() -> np.ndarray:
    W, H = 48, 32
    B = np.zeros((H, W, 3), np.uint8)
    cx = 24
    J_OUT, O_HW = 23.0, 15.0
    sp_o, sp_i, apex_i = 12, 15, 4

    def outer_hw(y):
        return J_OUT if y >= sp_o else J_OUT * (y / sp_o) ** 0.6

    def inner_hw(y):
        if y >= sp_i:
            return O_HW
        if y <= apex_i:
            return -1.0
        return O_HW * ((y - apex_i) / (sp_i - apex_i)) ** 0.6

    for y in range(H):
        oh, ih = outer_hw(y), inner_hw(y)
        for x in range(W):
            dx = abs(x - cx)
            if dx > oh or dx < ih:
                continue                      # void (black)
            if dx >= oh - 1:
                c = "C1"                      # outer sky-lit edge
            elif ih >= 0 and dx <= ih + 1:
                c = "O0"                      # inner shadowed reveal
            elif hash01(x, y, 204) > 0.9:
                c = "PL"                      # a chipped spall
            elif hash01(x, y, 45) > 0.7:
                c = "O2"                      # stucco mottle
            else:
                c = "O1"
            B[y, x] = PALETTE[c]
    _rect(B, cx - 2, 0, cx + 2, 4, "O2")      # keystone at the crown
    _put(B, cx - 2, 0, "C1"); _put(B, cx + 1, 0, "C1")
    return B


_ARCH_FRONT = _build_arch_front()


def _archfront_slice(r0, c0):
    def fn(cell, gx, gy):
        cell[:] = _ARCH_FRONT[r0:r0 + TILE, c0:c0 + TILE]
    return fn


for _cc, _cn in ((0, "l"), (16, "m"), (32, "r")):
    _register(f"arch_front_{_cn}_top", _archfront_slice(0, _cc))
for _cc, _cn in ((0, "l"), (16, "m"), (32, "r")):
    _register(f"arch_front_{_cn}_bot", _archfront_slice(16, _cc))


# ===========================================================================
# BUNGALOW  (3x3 = 48x48): distant low house
# ===========================================================================
def _build_bungalow() -> np.ndarray:
    W = H = 48
    B = np.zeros((H, W, 3), np.uint8)
    bx0, bx1 = 4, 44
    roof_y, base_y = 14, 46
    for y in range(roof_y, base_y):           # body
        for x in range(bx0, bx1):
            B[y, x] = PALETTE["O1" if hash01(x, y, 31) > 0.4 else "O0"]
    for x in range(bx0 - 3, bx1 + 3):         # low sloped sheet roof
        ry = roof_y - int((x - (bx0 - 3)) * 0.06)
        for y in range(ry - 4, ry):
            if not (0 <= x < W):
                continue
            tone = "R1"
            if x % 3 == 0:
                tone = "R0"
            elif hash01(x // 4, y, 32) > 0.92:
                tone = "O1"
            B[y, x] = PALETTE[tone]
        if 0 <= x < W:
            B[ry, x] = PALETTE["C1"]          # fascia line
    # door (dark, slightly ajar)
    dx0 = 22
    _rect(B, dx0, base_y - 14, dx0 + 7, base_y, "K1")
    _rect(B, dx0 + 1, base_y - 13, dx0 + 5, base_y, "K0")
    _put(B, dx0 + 4, base_y - 7, "O3")        # handle glint
    return B


register_block("bung", 3, 3, _build_bungalow)


@tile("bung_win_lit")
def _bung_win_lit(A, gx, gy):
    A[:] = PALETTE["O1"]
    _rect(A, 2, 3, 14, 13, "K1")
    _rect(A, 3, 4, 13, 12, "W0")
    for y in range(4, 12):                    # muntin
        _put(A, 8, y, "K1")
    _put(A, 4, 8, "K1"); _put(A, 12, 8, "K1")
    _put(A, 3, 4, "W1")                       # warm glint


@tile("bung_win_board")
def _bung_win_board(A, gx, gy):
    A[:] = PALETTE["O1"]
    _rect(A, 2, 3, 14, 13, "K1")
    for i, yy in enumerate(range(4, 12, 2)):  # boards
        _rect(A, 3, yy, 13, yy + 1, "O0")
    _put(A, 4, 3, "O0"); _put(A, 12, 12, "O0")


# ===========================================================================
# GAZEBO  (7x6 = 112x96): octagonal pavilion, conical red roof, posts, table
# ===========================================================================
def _build_gazebo() -> np.ndarray:
    W, H = 112, 96
    B = np.zeros((H, W, 3), np.uint8)
    cx = 56
    apex_y = 6
    eave_y = 50
    pad_y = 90
    post_top = 52
    half = 52                                 # roof half-span at the eave
    lx, ly = cx, 60                           # hung lantern = the interior LIGHT SOURCE

    # ROUND-8 (user feedback: "the gazebo body is a dark mass fusing with the dark
    # woods behind"): the interior is now LIT FROM WITHIN by a hung lantern instead
    # of a flat shadow. A warm radial glow -- the SAME W0/W1/W2 warm ramp the arch
    # doorways use -- fills the pavilion, brightest at the lantern and pooling DOWN
    # onto the floor (an elliptical, downward-biased falloff), fading to the residual
    # shadowed corners (never pure black, so it stays opaque, not see-through). The
    # body reads as a glowing set-piece; the table/bench in front read as SILHOUETTES.
    for y in range(post_top, pad_y):
        for x in range(cx - 46, cx + 46):
            dx, dy = x - lx, y - ly
            ry = 15.0 if dy < 0 else 33.0     # light throws farther DOWN (spills to the floor)
            g = 1.0 - math.sqrt((dx / 30.0) ** 2 + (dy / ry) ** 2)
            g += (float(BAYER_4X4[y & 3, x & 3]) - 0.5) * 0.14   # ordered dither ("como los arcos")
            g += (hash01(x, y, 93) - 0.5) * 0.10                 # organic scuff
            if g > 0.80:
                t = "W2"                      # blazing warm core near the lantern
            elif g > 0.60:
                t = "W1"
            elif g > 0.42:
                t = "W0"
            elif g > 0.28:
                t = "S5"                      # warm sunset-orange halo
            elif g > 0.16:
                t = "S4"
            elif g > 0.06:
                t = "O1"                      # dim warm falloff
            else:
                t = "V0" if hash01(x, y, 93) > 0.5 else "K1"     # residual shadow (opaque, not black)
            B[y, x] = PALETTE[t]

    # picnic table + bench, BACKLIT -> dark SILHOUETTES against the glow, with a
    # faint warm rim where the lantern light wraps their top edges.
    _rect(B, cx - 16, 71, cx + 16, 77, "K1")          # tabletop slab (dark silhouette)
    _rect(B, cx - 16, 76, cx + 16, 77, "K0")          # shadow underside
    for x in range(cx - 16, cx + 16):                 # warm backlit rim on the top edge
        if hash01(x, 0, 96) > 0.45:
            _put(B, x, 70, "W0" if hash01(x, 1, 96) > 0.5 else "S5")
    for lx2 in (cx - 13, cx + 12):                    # table legs
        _rect(B, lx2, 77, lx2 + 1, 85, "K0")
    _rect(B, cx - 16, 84, cx + 15, 86, "K0")          # foot cross-brace
    _rect(B, cx - 24, 80, cx - 8, 82, "K1")           # a low bench in front (silhouette)
    for x in range(cx - 24, cx - 8):
        if hash01(x, 0, 97) > 0.55:
            _put(B, x, 79, "S5")                      # faint warm rim on the bench
    _rect(B, cx - 22, 82, cx - 21, 86, "K0"); _rect(B, cx - 11, 82, cx - 10, 86, "K0")  # bench legs

    # tie-beam under the eave
    for x in range(cx - 46, cx + 46):
        _put(B, x, post_top, "K1"); _put(B, x, post_top + 1, "K0")

    # hung lantern -- the interior light SOURCE (drawn over the glow it casts)
    for y in range(post_top + 2, 56):                 # cord from the tie-beam
        _put(B, lx, y, "K1")
    _rect(B, lx - 3, 56, lx + 4, 65, "K0")            # iron housing
    _rect(B, lx - 2, 57, lx + 3, 64, "W0")            # warm glass
    _rect(B, lx - 2, 58, lx + 2, 63, "W1")
    _rect(B, lx - 1, 59, lx + 1, 62, "W2")            # blazing core
    _put(B, lx, 55, "R1"); _put(B, lx, 65, "R0")      # top cap + bottom finial
    _put(B, lx - 3, 60, "R1"); _put(B, lx + 3, 60, "R1")   # warm metal glints on the frame

    # posts with stone bases. ROUND-8: the interior-facing edge catches a 1px warm
    # rim from the lantern; the outer edge catches a sparser cool dusk-sky rim; the
    # stone bases are LIGHTENED to cream (C0/C1) so the footings read as lit.
    for px in (cx - 44, cx - 20, cx + 19, cx + 43):
        left_is_interior = px > cx                    # posts right of centre are lit on their LEFT
        for y in range(post_top - 2, pad_y - 3):
            _put(B, px, y, "K0"); _put(B, px + 1, y, "K0"); _put(B, px + 2, y, "K1")
            wx = px if left_is_interior else px + 2   # interior-facing edge -> warm lantern rim
            if hash01(wx, y, 94) > 0.30:
                _put(B, wx, y, "O2" if hash01(wx, y, 98) > 0.45 else "W0")
            cxo = px + 2 if left_is_interior else px   # outer edge -> cool dusk-sky rim (sparser)
            if hash01(cxo, y, 99) > 0.82:
                _put(B, cxo, y, "RC")
        _rect(B, px - 2, pad_y - 3, px + 4, pad_y, "C1")
        _rect(B, px - 2, pad_y - 3, px + 4, pad_y - 2, "C0")
        _put(B, px - 2, pad_y - 1, "G0"); _put(B, px + 3, pad_y - 1, "G0")

    # conical/octagonal red roof rising to a cupola
    for x in range(cx - half, cx + half):
        t = abs(x - cx) / half                # 0 centre .. 1 eave tip
        top_y = int(apex_y + (eave_y - 8 - apex_y) * (t ** 0.85))
        edge_y = int(eave_y - 2 + t * 2)
        for y in range(top_y, edge_y):
            ridge = y < top_y + 2
            eave = y > edge_y - 3
            if ridge:
                shade = "R0"
            elif eave:
                shade = "R1"
            elif hash01(x, 0, 91) > 0.74:
                shade = "R1"                  # corrugation groove
            else:
                shade = "R2" if abs(x - cx) < half * 0.55 else "R1"
            B[y, x] = PALETTE[shade]
        _put(B, x, edge_y, "C1")              # cream drip-edge
    # facet hip lines from the apex
    for k in (-1, 1):
        for i in range(half):
            x = cx + k * i
            y = int(apex_y + (eave_y - 8 - apex_y) * ((i / half) ** 0.85))
            _put(B, x, y, "R0")

    # cupola / lantern-top. ROUND-8: +1px rim on the cumbrera so the crown reads
    # against the sky -- a cool dusk-sky rim on its ascending edges + a warm spark.
    _rect(B, cx - 6, apex_y - 4, cx + 6, apex_y + 3, "R1")
    _rect(B, cx - 4, apex_y - 3, cx + 4, apex_y + 1, "K1")
    _put(B, cx - 2, apex_y - 3, "K0"); _put(B, cx + 1, apex_y - 3, "K0")
    for i in range(4):
        _rect(B, cx - 5 + i, apex_y - 4 - i, cx + 6 - i, apex_y - 3 - i, "R2" if i < 2 else "R0")
        _put(B, cx - 5 + i, apex_y - 4 - i, "RC")     # cool sky rim, left ascending edge
        _put(B, cx + 5 - i, apex_y - 4 - i, "RC")     # and the right ascending edge
    _put(B, cx, apex_y - 9, "R0"); _put(B, cx, apex_y - 10, "W1")
    _put(B, cx, apex_y - 4, "W1")                     # warm crest spark on the cupola

    # concrete pad + warm light POOL spilling onto the floor under the lantern
    # (dithered, "como los arcos"), fading to plain lit concrete at the rim.
    for x in range(cx - 46, cx + 46):
        dxp = x - cx
        pool = 1.0 - abs(dxp) / 24.0 + (float(BAYER_4X4[pad_y & 3, x & 3]) - 0.5) * 0.28
        if pool > 0.74:
            top = "W0"
        elif pool > 0.52:
            top = "S5"
        elif pool > 0.30:
            top = "S4"
        else:
            top = "G2"                                # plain lit concrete beyond the pool
        _put(B, x, pad_y, top)
        _put(B, x, pad_y + 1, "S4" if abs(dxp) < 16 else "G1")
        _put(B, x, pad_y + 2, "G0")
    # ivy on a near post
    for y in range(pad_y - 12, pad_y):
        if hash01(y, 0, 95) > 0.4:
            _put(B, cx - 45, y, "V2"); _put(B, cx - 46, y, "V1")

    return B


register_block("gaz", 7, 6, _build_gazebo)


# ===========================================================================
# GAZEBO PLAZA / PLINTH  (round-10: user "hay que construir su parte faltante").
# A warm stone terrace the kiosk is SEATED on, filling the cleared footprint at
# the base row (34) so the gazebo reads COMPLETE and grounded -- not cut/floating
# over the pink sky-void round 9 left. Deliberately LOW: only the bottom ~9px of
# the tile are stone (a lit cream lip at the terrace top aligning with the gaz_*
# stone bases), the top is transparent so the dusk sky keeps breathing ABOVE the
# terrace and through the kiosk interior. Cool paving (G-ramp) with warm O2 flecks
# so the lantern's light pool falls on pavement, not on void.
# ===========================================================================
_PLAZA_LIP = 7                                 # terrace top-edge row (aligns with gaz bases)


def _plaza_body(A: np.ndarray, gx: int, gy: int) -> None:
    for y in range(_PLAZA_LIP + 1, TILE):
        for x in range(TILE):
            b = 0.5 + 0.5 * hash01((gx + x) // 6, (gy + y) // 4, 472)
            b += (hash01(gx + x, gy + y, 473) - 0.5) * 0.20
            t = "G1" if b < 0.34 else ("G2" if b < 0.66 else "G3")
            if hash01(gx + x, gy + y, 474) > 0.90:
                t = "O2"                       # warm paving fleck (ties to the lantern glow)
            A[y, x] = PALETTE[t]
    for x in range(0, TILE, 6):                # vertical joints
        for y in range(_PLAZA_LIP + 1, TILE):
            A[y, x] = PALETTE["G1"]
    for x in range(TILE):                      # a horizontal joint mid-body
        if hash01(gx + x, 0, 475) > 0.35:
            A[_PLAZA_LIP + 4, x] = PALETTE["G1"]


def _plaza_lip(A: np.ndarray, gx: int, gy: int, x0: int = 0, x1: int = TILE) -> None:
    for x in range(x0, x1):
        A[_PLAZA_LIP, x] = PALETTE["C0" if hash01(gx + x, 0, 470) > 0.72 else "G3"]
        if hash01(gx + x, 1, 471) > 0.90:
            A[_PLAZA_LIP, x] = PALETTE["W1"]   # rare warm sparkle catching the last light


@tile("plaza_slab")
def _plaza_slab(A, gx, gy):
    A[:] = BLACK                               # transparent above the lip -> sky breathes
    _plaza_body(A, gx, gy)
    _plaza_lip(A, gx, gy)


@tile("plaza_step_l")
def _plaza_step_l(A, gx, gy):
    # left END of the terrace: a shadowed stone side-face steps down on the left.
    A[:] = BLACK
    _plaza_body(A, gx, gy)
    _plaza_lip(A, gx, gy, x0=3)                # lip starts a few px in (rounded corner)
    for y in range(_PLAZA_LIP, TILE):          # dark vertical side face
        for x in range(0, 3):
            A[y, x] = PALETTE["G0"]
    A[_PLAZA_LIP, 3] = PALETTE["G1"]


@tile("plaza_step_r")
def _plaza_step_r(A, gx, gy):
    A[:] = BLACK
    _plaza_body(A, gx, gy)
    _plaza_lip(A, gx, gy, x1=TILE - 3)
    for y in range(_PLAZA_LIP, TILE):
        for x in range(TILE - 3, TILE):
            A[y, x] = PALETTE["G0"]
    A[_PLAZA_LIP, TILE - 4] = PALETTE["G1"]


# ===========================================================================
# PROPS  (abandonment narrative)
# ===========================================================================
@tile("lamp_top")
def _lamp_top(A, gx, gy):
    A[:] = BLACK
    _rect(A, 6, 6, 12, 14, "K1")              # lantern housing (unlit)
    _rect(A, 7, 7, 11, 13, "K0")              # dark glass
    _put(A, 8, 3, "K1"); _put(A, 8, 4, "K0"); _put(A, 8, 5, "K1")  # finial
    _put(A, 6, 6, "RC")                       # cool sky glint on the cap
    for y in range(14, TILE):                 # top of the leaning pole
        _put(A, 8, y, "K0"); _put(A, 9, y, "K1")


@tile("lamp_base")
def _lamp_base(A, gx, gy):
    A[:] = BLACK
    for y in range(0, 11):                    # leaning pole
        x = 8 + int((10 - y) * 0.2)
        _put(A, x, y, "K0"); _put(A, x + 1, y, "K1")
    _rect(A, 5, 11, 12, 16, "G1")             # cracked stone base
    _rect(A, 5, 11, 12, 13, "G2")
    _put(A, 8, 13, "G0"); _put(A, 9, 14, "G0")


@tile("bench_broken_l")
def _bench_broken_l(A, gx, gy):
    A[:] = BLACK
    for i in range(TILE):                     # seat tilts down-right
        y = 7 + int(i * 0.22)
        _put(A, i, y, "O2"); _put(A, i, y + 1, "O1")
    for i in range(TILE):                     # backrest slat
        _put(A, 2 + i, 4 - int(i * 0.1), "O1")
    _rect(A, 3, 9, 4, 15, "O0")               # standing leg


@tile("bench_broken_r")
def _bench_broken_r(A, gx, gy):
    A[:] = BLACK
    for i in range(TILE):
        y = 10 + int(i * 0.22)
        _put(A, i, y, "O2"); _put(A, i, y + 1, "O1")
    _put(A, 12, 14, "O0"); _put(A, 12, 15, "O0")   # broken short leg stub


def _fence(A, gx, gy, salt):
    A[:] = BLACK
    _rect(A, 1, 6, 3, TILE, "O1")             # posts
    _rect(A, 13, 6, 15, TILE, "O1")
    _put(A, 1, 6, "O2"); _put(A, 13, 6, "O2")
    _rect(A, 0, 8, TILE, 9, "O0")             # rails span edge-to-edge (tileable)
    _rect(A, 0, 12, TILE, 13, "O0")
    if hash01(gx, 0, 100 + salt) > 0.6:       # a weathered/broken picket
        _rect(A, 7, 6, 8, TILE, "O0")


@tile("fence_a")
def _fence_a(A, gx, gy):
    _fence(A, gx, gy, 0)


@tile("fence_b")
def _fence_b(A, gx, gy):
    _fence(A, gx, gy, 1)


@tile("fence_c")
def _fence_c(A, gx, gy):
    _fence(A, gx, gy, 2)


@tile("fence_fallen")
def _fence_fallen(A, gx, gy):
    A[:] = BLACK
    for i in range(TILE):                     # planks lying on the ground
        y = 11 + int(i * 0.1)
        _put(A, i, y, "O2"); _put(A, i, y + 1, "O1"); _put(A, i, y + 2, "O0")
    _rect(A, 3, 9, 4, 14, "O1")               # a toppled post
    _rect(A, 10, 10, 11, 15, "O0")


def _clothesline(A, gx, gy, cloth):
    A[:] = BLACK
    for x in range(TILE):                     # sagging wire (catenary)
        t = (gx + x) % 48 / 48.0
        y = 3 + int(4 * (1 - (2 * t - 1) ** 2))
        _put(A, x, y, "K1")
    if cloth:
        _rect(A, 6, 5, 11, 13, "C1")          # a hanging rag
        _rect(A, 6, 5, 11, 7, "C0")
        _put(A, 6, 12, "C0"); _put(A, 10, 13, "G1")


@tile("clothesline_l")
def _clothesline_l(A, gx, gy):
    _clothesline(A, gx, gy, False)
    _rect(A, 1, 1, 2, TILE, "K0")             # leaning post


@tile("clothesline_m")
def _clothesline_m(A, gx, gy):
    _clothesline(A, gx, gy, True)


@tile("clothesline_r")
def _clothesline_r(A, gx, gy):
    _clothesline(A, gx, gy, False)
    _rect(A, 14, 1, 15, TILE, "K0")


def _leaves(A, gx, gy, salt):
    A[:] = BLACK
    cols = ["O1", "O2", "R1", "V2"]
    for k in range(7):
        x = int(15 * hash01(gx + k * 3, salt, 170))
        y = int(15 * hash01(gy + k * 5, salt, 171))
        col = cols[int(4 * hash01(x, y, 172)) % 4]
        _put(A, x, y, col)
        if hash01(x, y, 173) > 0.5:
            _put(A, x + 1, y, col)
        if hash01(x, y, 174) > 0.6:
            _put(A, x, y + 1, "O0")


@tile("leaves_drift_a")
def _leaves_a(A, gx, gy):
    _leaves(A, gx, gy, 0)


@tile("leaves_drift_b")
def _leaves_b(A, gx, gy):
    _leaves(A, gx, gy, 1)


@tile("branch_fallen")
def _branch_fallen(A, gx, gy):
    A[:] = BLACK
    for x in range(TILE):                     # main limb across the tile
        y = 8 + int(2 * math.sin((gx + x) * 0.25))
        _put(A, x, y, "K0"); _put(A, x, y + 1, "O0")
    for (sx, sy, dx, dy, n) in [(4, 8, 1, -1, 5), (11, 9, 1, -1, 4)]:  # twigs
        x, y = sx, sy
        for _ in range(n):
            _put(A, x, y, "K0"); x += dx; y += dy


def _fg_grass(A, gx, gy, salt):
    # Dusk-lit grass fringe (FG_Overlay). Blades are dusk GREEN, deliberately
    # kept DARKER than the walkable turf (ROUND-7: tips capped at V2, no bright
    # V3 tip) so these decorative foreground tufts frame the floor for depth
    # instead of matching -- and swallowing -- its lit surface rim.
    A[:] = BLACK
    for x in range(TILE):
        hh = 4 + int(9 * hash01(gx + x, salt, 181))
        lean = (hash01(gx + x, salt, 182) - 0.5) * 4
        for i in range(hh):
            y = TILE - 1 - i
            xx = x + int(lean * (i / max(1, hh)))
            frac = i / max(1, hh)
            col = "V0" if frac < 0.4 else ("V1" if frac < 0.8 else "V2")
            _put(A, xx, y, col)


@tile("fg_grass_a")
def _fg_grass_a(A, gx, gy):
    _fg_grass(A, gx, gy, 0)


@tile("fg_grass_b")
def _fg_grass_b(A, gx, gy):
    _fg_grass(A, gx, gy, 1)


@tile("fg_grass_c")
def _fg_grass_c(A, gx, gy):
    _fg_grass(A, gx, gy, 2)


@tile("firefly")
def _firefly(A, gx, gy):
    A[:] = BLACK
    cx, cy = 8, 8
    _put(A, cx, cy, "W2")                     # bright core
    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        _put(A, cx + dx, cy + dy, "W0")       # warm halo
    _put(A, cx - 1, cy - 1, "W1")


# ===========================================================================
# GARDEN ARBOR / PERGOLA  (one-way platform support). Replaces the old flat
# "hedge tower". An airy wooden arbor: a walkable leafy crossbeam on two posts,
# an OPEN vine lattice between them (mostly transparent, so the sunset/forest
# show THROUGH -> it reads as campus garden furniture, never a solid tower),
# rooted in a low stone jardinera. Composited in Terrain_Detail over the sky.
# ===========================================================================
@tile("arbor_beam")
def _arbor_beam(A, gx, gy):
    A[:] = BLACK
    for x in range(TILE):                     # leafy vine draping over the top
        if hash01(gx + x, 0, 210) > 0.60:
            _put(A, x, 0, "V3"); _put(A, x, 1, "V2")
    for y in range(2, 7):                     # the plank crossbeam (walkable top)
        for x in range(TILE):
            r = hash01(gx + x, gy + y, 211)
            if y == 2:
                A[y, x] = PALETTE["O3" if r > 0.55 else "O2"]   # sunlit top edge
            elif y == 6:
                A[y, x] = PALETTE["O0"]                          # shadow underside
            else:
                A[y, x] = PALETTE["O1" if r > 0.32 else "O0"]    # grain
    for x in range(0, TILE, 5):               # plank joint shadows
        for y in range(2, 7):
            _put(A, x, y, "O0")
    if hash01(gx, 0, 212) > 0.45:             # an occasional hanging tendril
        _put(A, 4, 7, "V1"); _put(A, 4, 8, "V2"); _put(A, 11, 7, "V2")


@tile("arbor_post")
def _arbor_post(A, gx, gy):
    A[:] = BLACK
    for y in range(TILE):                     # a centred wooden post (sides open)
        for x in range(6, 10):
            r = hash01(gx + x, gy + y, 213)
            A[y, x] = PALETTE["O1" if (x < 8 or r < 0.7) else "O2"]
        _put(A, 6, y, "O0"); _put(A, 9, y, "O0")   # shaded edges -> round post
    for y in range(TILE):                     # climbing vine spiralling the post
        vx = 5 + int(3 * (1 + math.sin((gy + y) * 0.5)))
        if hash01(gx + vx, gy + y, 214) > 0.4:
            _put(A, vx, y, "V2" if hash01(gx + vx, gy + y, 215) > 0.5 else "V1")
        if (gy + y) % 4 == 0:
            _put(A, vx, y, "V3")              # a dusk-lit leaf


@tile("arbor_lattice")
def _arbor_lattice(A, gx, gy):
    A[:] = BLACK                              # airy, but a LUSH trellis (not a net)
    for y in range(TILE):                     # tight diagonal criss-cross laths
        for x in range(TILE):
            if (x + y) % 4 == 0 or (x - y) % 4 == 0:
                A[y, x] = PALETTE["O1" if hash01(gx + x, gy + y, 216) > 0.5 else "O0"]
    for x in range(TILE):                     # a horizontal pergola rafter mid-tile
        if hash01(gx + x, 0, 227) > 0.35:
            A[8, x] = PALETTE["O0" if hash01(gx + x, 1, 227) > 0.5 else "O1"]
    for k in range(10):                       # heavy climbing vine draped on the laths
        lx = int(15 * hash01(gx + k * 3, gy, 217))
        ly = int(15 * hash01(gy + k * 5, gx, 218))
        _put(A, lx, ly, "V2")
        _put(A, lx, min(TILE - 1, ly + 1), "V1")
        if hash01(lx, ly, 219) > 0.4:
            _put(A, min(TILE - 1, lx + 1), ly, "V2")
        if hash01(lx, ly, 220) > 0.62:
            _put(A, lx, ly, "V3")             # dusk-lit leaf
    for fx, fy, salt in [(7, 6, 221), (11, 11, 226), (4, 12, 228)]:   # flowers on the vine
        if hash01(gx, gy, salt) > 0.45:
            _put(A, fx, fy, "P0"); _put(A, fx + 1, fy, "P1")


@tile("arbor_base")
def _arbor_base(A, gx, gy):
    A[:] = BLACK                              # low stone jardinera anchoring the arbor
    for x in range(TILE):                     # hedge/flower tuft spilling over the rim
        if hash01(gx + x, 0, 224) > 0.5:
            _put(A, x, 2, "V3"); _put(A, x, 3, "V2")
    if hash01(gx, 0, 225) > 0.45:
        _put(A, 5, 2, "P0"); _put(A, 10, 3, "P1")
    for y in range(4, TILE):                  # the planter box
        for x in range(TILE):
            if y <= 5:
                A[y, x] = PALETTE["O0"]                          # dark soil surface
            elif y == 6:
                A[y, x] = PALETTE["G3" if hash01(gx + x, gy + y, 222) > 0.4 else "G2"]  # lit stone rim
            else:
                b = 0.5 + 0.5 * hash01((gx + x) // 7, (gy + y) // 5, 223)
                A[y, x] = PALETTE["G1" if b > 0.5 else "G0"]     # stone body
    for x in range(0, TILE, 6):               # stone joint lines
        for y in range(7, TILE):
            _put(A, x, y, "G0")


# ===========================================================================
# CARPORT + VEHICLES  (round-11: user asked to "hacer el lugar donde estaban los
# carros"). Faithful to the reference photos (imagenes para el mapa/3,8,9,12):
# a dark corrugated mono-pitch roof on BLACK metal posts over a DARK GRAVEL bay,
# a silver sedan + a white pickup parked under it and an orange loader-tractor
# beside it. All built dusk-muted so they silhouette against the crepuscular sky
# like every other structure -- palette stays CLOSED: the silver bodywork is
# C0/C1 + cool RC glass + K* shadow, the white pickup is C0/W* + K*, and the
# tractor is the terracotta R* ramp (dusk "orange") + K* tyres + G* metal.
# ===========================================================================
def _build_carport_roof() -> np.ndarray:
    """A 10x2 dark corrugated mono-pitch carport roof (sliced into carroof_cr).

    The sheet slopes gently down toward the front (right); its top edge catches
    a thread of the last warm light (S5/W0 rim) so the dark silhouette reads
    against the sunset, with a cream fascia board and a 2px underside shadow so
    the overhang has depth. Everything below the sheet stays transparent (the
    open bay) -- the posts (a separate tile) carry the structure to the ground.
    """
    cols = 10
    Wp, Hp = cols * TILE, 2 * TILE
    B = np.zeros((Hp, Wp, 3), np.uint8)
    for x in range(Wp):
        ry = 3 + int(6 * x / (Wp - 1))            # gentle mono-pitch, higher at the back
        _put(B, x, ry, "S5" if hash01(x, 0, 480) > 0.4 else "W0")   # warm sunset rim
        for i in range(1, 5):                     # 4px dark corrugated terracotta body
            tone = "R1"                           # clean dark terracotta sheet
            if x % 4 == 0:
                tone = "R0"                       # corrugation groove every 4px
            if i == 4:
                tone = "R0"                       # darker toward the eave
            _put(B, x, ry + i, tone)
        _put(B, x, ry + 5, "C1")                  # cream fascia board
        _put(B, x, ry + 6, "K1")                  # underside shadow (overhang depth)
        _put(B, x, ry + 7, "K0")
    return B


register_block("carroof", 10, 2, _build_carport_roof)


@tile("carport_post")
def _carport_post(A, gx, gy):
    # A slender BLACK metal post (2px core) that tiles vertically. A warm sunset
    # rim licks its left (sun-facing) edge and a sparse cool sky-rim its right, so
    # the black post still reads as round metal against the dusk, not a flat bar.
    A[:] = BLACK
    for y in range(TILE):
        _put(A, 7, y, "K1"); _put(A, 8, y, "K0"); _put(A, 9, y, "K0")
        if hash01(gx + 7, gy + y, 490) > 0.45:
            _put(A, 7, y, "O2" if hash01(gx, y, 491) > 0.5 else "W0")   # warm sun rim
        if hash01(gx + 10, gy + y, 492) > 0.80:
            _put(A, 10, y, "RC")                  # sparse cool sky rim


@tile("carport_post_base")
def _carport_post_base(A, gx, gy):
    # The post's foot: shaft down to a cracked CONCRETE basa (task: "2px con basa").
    A[:] = BLACK
    for y in range(0, 11):
        _put(A, 7, y, "K1"); _put(A, 8, y, "K0"); _put(A, 9, y, "K0")
        if hash01(gx + 7, gy + y, 490) > 0.45:
            _put(A, 7, y, "O2" if hash01(gx, y, 491) > 0.5 else "W0")
    _rect(A, 5, 11, 12, TILE, "G1")               # concrete basa
    _rect(A, 5, 11, 12, 12, "G2")                 # lit top of the basa
    _put(A, 6, 13, "G0"); _put(A, 10, 14, "G0")   # chips/cracks


@tile("gravel")
def _gravel(A, gx, gy):
    # DARK parking gravel (task: "gravilla oscura"), deliberately darker/cooler
    # than the sidewalk `pebbles` (G0/G1) so the aparcadero surface recedes: a
    # K1/G0 field with a few lit G1 chips catching the dusk.
    for y in range(TILE):
        for x in range(TILE):
            r = hash01(gx + x, gy + y, 495)
            A[y, x] = PALETTE["K1" if r < 0.45 else ("G0" if r < 0.86 else "G1")]


@tile("gravel_curb")
def _gravel_curb(A, gx, gy):
    # The FRONT edge row of the gravel bay: dark gravel up top, then a lit CONCRETE
    # curb lip (task: "borde de concreto") where the aparcadero meets the lawn.
    for y in range(TILE):
        for x in range(TILE):
            if y < 8:
                r = hash01(gx + x, gy + y, 495)
                A[y, x] = PALETTE["K1" if r < 0.45 else ("G0" if r < 0.86 else "G1")]
            elif y < 11:
                A[y, x] = PALETTE["G3" if hash01(gx + x, gy + y, 493) > 0.55 else "G2"]  # lit curb
            else:
                A[y, x] = PALETTE["G1" if hash01(gx + x, gy + y, 494) > 0.5 else "G0"]
    for x in range(TILE):                          # curb top highlight line
        if hash01(gx + x, 0, 499) > 0.5:
            A[8, x] = PALETTE["G3"]


@tile("tire")
def _tire(A, gx, gy):
    # A worn tyre propped against a post (abandonment beat): a dark rubber DONUT
    # -- a clearly OPEN ring (the sky shows through the hub) so it never reads as a
    # solid ball/head, sitting low on the ground with a whisper of cool sky rim.
    A[:] = BLACK
    cx, cy = 8, 10                                          # low in the tile -> on the ground
    rox, roy, rix, riy = 6.0, 5.0, 3.8, 3.0                # thick rubber, wide OPEN hole
    for y in range(TILE):
        for x in range(TILE):
            ox = ((x - cx) / rox) ** 2 + ((y - cy) / roy) ** 2
            ix = ((x - cx) / rix) ** 2 + ((y - cy) / riy) ** 2
            if ox <= 1.0 and ix >= 1.0:                     # between outer + inner ellipse
                A[y, x] = PALETTE["K0" if hash01(gx + x, gy + y, 486) > 0.4 else "K1"]
    _put(A, cx - 3, cy - 3, "RC")                          # cool sky rim on the upper-left


def _wheel(B: np.ndarray, wx: int, wy: int, rr: int, flat: bool = False) -> None:
    """A dark rubber wheel (optionally a FLAT/deflated one) with a grey hub."""
    Hh, Wp = B.shape[:2]
    for y in range(Hh):
        for x in range(Wp):
            dy = y - wy
            if flat and dy > 0:
                dy = int(dy * 1.7)                # squash the contact patch -> deflated
            d = (x - wx) ** 2 + dy * dy
            if d <= rr * rr:
                B[y, x] = PALETTE["G1" if d <= (rr - 3) ** 2 else
                                  ("K1" if hash01(x, y, 487) > 0.5 else "K0")]


def _build_sedan() -> np.ndarray:
    """A low silver sedan (4x2 = 64x32), dark tinted glass, one FLAT front tyre.

    Silver bodywork from the closed palette: C1 mass, C0 shoulder/roof highlight,
    RC cool tinted greenhouse, K* shadow/tyres, with a warm sun-glint on the tail.
    """
    Wp, Hp = 64, 32
    B = np.zeros((Hp, Wp, 3), np.uint8)
    ground = 29
    bxl, bxr = 6, 58
    belt = 17                                     # window-sill / top of the body box
    roof = 9                                      # roofline
    # lower body BOX (hood / doors / boot): a clean silver 2-box, flat top at the
    # beltline, softly rounded front/rear bottom corners, shadowed sill.
    for y in range(belt, ground - 1):
        for x in range(bxl, bxr):
            if (x < bxl + 2 or x > bxr - 3) and y > ground - 3:
                continue                          # tuck the bottom corners in
            if y == belt:
                t = "C0"                          # bright beltline sheen
            elif y >= ground - 2:
                t = "K1"                          # shadow under the sills
            else:
                t = "C1"                          # clean silver flank
            B[y, x] = PALETTE[t]
    # greenhouse / cabin: a raked trapezoid (narrow lit roof -> wider at the belt)
    # with DARK tinted glass (task) and only sparse cool sky reflections.
    for y in range(roof, belt):
        frac = (y - roof) / (belt - roof)
        x0 = int(24 - 6 * frac)                   # A-pillar rake (windshield)
        x1 = int(41 + 6 * frac)                   # C-pillar rake (backlight)
        for x in range(x0, x1):
            if y <= roof + 1:
                t = "C0"                          # lit roof
            elif y >= belt - 1:
                t = "C1"                          # window sill
            else:
                t = "RC" if hash01(x, y, 501) > 0.82 else "K1"   # dark glass + sky glint
            B[y, x] = PALETTE[t]
        _put(B, x0, y, "C1"); _put(B, x1 - 1, y, "C1")   # A/C pillars catch the light
    _put(B, 32, roof + 1, "C1")                   # B-pillar
    for wx in (16, 46):                           # wheel-arch shadows anchoring the body
        for dx in range(-5, 6):
            _put(B, wx + dx, ground - 3, "K1" if abs(dx) < 4 else "C1")
    # wheels: rear normal, FRONT deflated (task: "una desinflada")
    _wheel(B, 46, ground - 2, 5, flat=False)
    _wheel(B, 16, ground - 2, 5, flat=True)
    _put(B, bxr - 3, belt + 3, "S5"); _put(B, bxr - 2, belt + 3, "W0")  # tail-light glint
    _put(B, bxl + 1, belt + 3, "W0")              # headlight catch
    return B


register_block("sedan", 4, 2, _build_sedan)


def _build_pickup() -> np.ndarray:
    """A white pickup (4x2 = 64x32): tall cab (left) + open cargo bed (right).

    White bodywork = C0 with a warm W1 sunset catch on the roof and a C1 shadow
    side; dark cab glass + bed interior; K* tyres. Palette stays closed.
    """
    Wp, Hp = 64, 32
    B = np.zeros((Hp, Wp, 3), np.uint8)
    ground = 29
    # lower body slab (white) spanning cab + bed
    for y in range(16, ground - 1):
        for x in range(5, 59):
            r = hash01(x, y, 510)
            if y >= ground - 4:
                t = "C1" if r > 0.4 else "K1"     # shadowed rocker
            else:
                t = "C0" if r > 0.3 else "C1"
            B[y, x] = PALETTE[t]
    # cab (left, taller) with a warm-lit roof + dark glass
    for y in range(9, 16):
        for x in range(8, 34):
            B[y, x] = PALETTE["W1" if (y < 11 and hash01(x, 0, 511) > 0.5) else "C0"]
    _rect(B, 11, 11, 31, 16, "K1")                # windscreen band
    for y in range(11, 16):
        for x in range(11, 31):
            if hash01(x, y, 512) > 0.6:
                B[y, x] = PALETTE["RC"]            # cool glass glint
    _put(B, 21, 11, "K0")                         # door pillar
    # bed (right): top rail + shadowed interior
    _rect(B, 34, 17, 57, 19, "C1")                # bed side rail
    _rect(B, 34, 16, 35, 19, "C0")               # front bulkhead lit
    _rect(B, 36, 19, 56, ground - 2, "K1")        # bed interior shadow
    for x in range(36, 56):
        if hash01(x, 0, 513) > 0.7:
            _put(B, x, 19, "O0")                  # scattered debris/leaves in the bed
    # wheels (both normal)
    _wheel(B, 16, ground - 2, 5)
    _wheel(B, 46, ground - 2, 5)
    _put(B, 7, 17, "W0")                          # headlight catch
    return B


register_block("pickup", 4, 2, _build_pickup)


def _build_tractor() -> np.ndarray:
    """An orange loader-tractor (3x2 = 48x32): big rear wheel, front loader arm.

    "Orange" comes from the terracotta R* ramp (dusk-muted) so it stays on the
    closed palette; K* tyres, G* metal on the loader arm/stack, a warm rim on the
    hood. An ivy tile is draped over it separately by the compositor.
    """
    Wp, Hp = 48, 32
    B = np.zeros((Hp, Wp, 3), np.uint8)
    ground = 29
    # big rear wheel (right) + small front wheel (left)
    _wheel(B, 34, ground - 5, 8)
    _wheel(B, 11, ground - 3, 4)
    # engine hood / body (orange terracotta ramp)
    for y in range(13, ground - 3):
        for x in range(9, 39):
            r = hash01(x, y, 520)
            if y <= 14:
                t = "R2"                          # lit hood top
            elif r > 0.85:
                t = "O2"                          # warm ochre panel scuff
            else:
                t = "R1" if r > 0.4 else "R0"     # mid / shadowed orange
            B[y, x] = PALETTE[t]
    for x in range(9, 39):                        # warm sunset rim on the hood crest
        if hash01(x, 0, 521) > 0.5:
            _put(B, x, 13, "S5" if hash01(x, 1, 521) > 0.5 else "W0")
    # roll-bar / driver cage + seat (dark silhouette) over the rear axle
    _rect(B, 27, 6, 29, 15, "K0")                 # rear roll post
    _rect(B, 33, 8, 35, 15, "K0")                 # front roll post
    _rect(B, 27, 6, 35, 7, "K1")                  # top bar
    _rect(B, 29, 12, 33, 15, "K1")               # seat
    _rect(B, 24, 8, 26, 14, "G0")                 # exhaust stack
    # front loader arm reaching down-left to a bucket
    for i in range(10):
        x = 18 - i
        y = 16 + int(i * 0.9)
        _put(B, x, y, "O3"); _put(B, x, y + 1, "O2")
    _rect(B, 3, 24, 10, 28, "G1")                 # loader bucket
    _rect(B, 3, 24, 10, 25, "G2")                 # lit bucket lip
    _put(B, 3, 27, "G0"); _put(B, 9, 27, "G0")
    return B


register_block("tractor", 3, 2, _build_tractor)


# ===========================================================================
# COMPOSITION
# ===========================================================================
def _compose_atlas() -> np.ndarray:
    n = len(TILES)
    rows = (n + COLS - 1) // COLS
    atlas = np.zeros((rows * TILE, COLS * TILE, 3), np.uint8)   # trailing = black
    for i, (_name, fn) in enumerate(TILES):
        ox = (i % COLS) * TILE
        oy = (i // COLS) * TILE
        fn(atlas[oy:oy + TILE, ox:ox + TILE], ox, oy)
    # Despeckle every cell INDEPENDENTLY. Running despeckle on the whole atlas
    # bleeds colour across tile boundaries (a cell's edge pixel is "cleaned"
    # using its atlas neighbour, coupling the result to registration order). We
    # pad each 16x16 cell with a 1px edge-replicated ring so border pixels get a
    # full 8-neighbour context without borrowing from any other tile, then copy
    # the cleaned interior back.
    for i in range(len(TILES)):
        ox = (i % COLS) * TILE
        oy = (i // COLS) * TILE
        padded = np.pad(atlas[oy:oy + TILE, ox:ox + TILE],
                        ((1, 1), (1, 1), (0, 0)), mode="edge")
        despeckle(padded, PALETTE, protect_keys=_PROTECT)
        atlas[oy:oy + TILE, ox:ox + TILE] = padded[1:-1, 1:-1]
    return atlas


def _build_contact_sheet(atlas: np.ndarray) -> Image.Image:
    scale = 3
    cw, ch = TILE * scale, TILE * scale
    label_h = 12
    pad = 3
    cell_w = cw + pad * 2
    cell_h = ch + label_h + pad
    n = len(TILES)
    rows = (n + COLS - 1) // COLS
    sheet = Image.new("RGB", (COLS * cell_w, rows * cell_h), (24, 20, 30))
    draw = ImageDraw.Draw(sheet)
    for i, (name, _fn) in enumerate(TILES):
        c = i % COLS
        r = i // COLS
        ox = (i % COLS) * TILE
        oy = (i // COLS) * TILE
        cell = atlas[oy:oy + TILE, ox:ox + TILE]
        img = Image.fromarray(cell, "RGB").resize((cw, ch), Image.NEAREST)
        px = c * cell_w + pad
        py = r * cell_h + pad
        sheet.paste(img, (px, py))
        draw.rectangle([px - 1, py - 1, px + cw, py + ch], outline=(70, 62, 78))
        label = f"{i} {name}"
        draw.text((px, py + ch + 1), label[:12], fill=(200, 190, 205))
    return sheet


def main(out_png: Path | None = None, contact_png: Path | None = None) -> None:
    """Generate the atlas PNG and the labelled contact sheet (idempotent).

    ``out_png``/``contact_png`` default to the canonical game-tree locations
    (``OUT_PNG``/``CONTACT_PNG``) -- the path the ``python -m ...`` authoring
    workflow has always written to. Tests pass a ``tmp_path`` here instead so
    pytest never writes (or needs write access) into the sealed asset tree;
    see ``tests/test_tileset_residencias.py``.
    """
    out_png = OUT_PNG if out_png is None else out_png
    contact_png = CONTACT_PNG if contact_png is None else contact_png

    atlas = _compose_atlas()
    out_png.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(atlas, "RGB").save(out_png)

    contact_png.parent.mkdir(parents=True, exist_ok=True)
    _build_contact_sheet(atlas).save(contact_png)

    used = np.unique(atlas.reshape(-1, 3), axis=0)
    print(f"tiles={len(TILES)} atlas={atlas.shape[1]}x{atlas.shape[0]} "
          f"unique_colors={len(used)}")
    print(f"atlas -> {out_png}")
    print(f"contact -> {contact_png}")


if __name__ == "__main__":
    main()
