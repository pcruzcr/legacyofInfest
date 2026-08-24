"""Pintores de tiles: suelo y vegetacion (bosque, pradera, setos, arboles, hierba, tierra, caminos, aceras y subsuelo).

Extraidos verbatim de ``gen_tileset_residencias.py`` en AUD-345 (particion del
archivo dios de 2364 lineas en un paquete por tema). El cuerpo de cada pintor
no cambio ni un caracter: los registros corren al importar el modulo, y el
orden de importacion en ``__init__`` reproduce el orden de registro original,
que es el contrato del layout del atlas (el indice de cada tile lo consume
``gen_level_residencias`` via ``NAME_TO_INDEX``).
"""
from __future__ import annotations

import math

import numpy as np

from src.stages.boss_venado.tools.art_lib import (
    PALETTE,
    bayer_dither,
    hash01,
)

from .core import (
    BLACK,
    TILE,
    _put,
    register_block,
    tile,
)


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


