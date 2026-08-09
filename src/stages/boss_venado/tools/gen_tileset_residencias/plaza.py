"""Pintores de tiles: lo habitable del suelo (plaza, farolas, bancos, vallas,
tendederos, hojas, arbor, carport y vehiculos).

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
    hash01,
)

from .core import (
    BLACK,
    TILE,
    _put,
    _rect,
    register_block,
    tile,
)

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


