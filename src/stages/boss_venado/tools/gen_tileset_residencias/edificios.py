"""Pintores de tiles: estructuras habitadas (hastial, arco con hiedra, bungalow y gazebo).

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
    BAYER_4X4,
    PALETTE,
    hash01,
    mottle,
)

from .core import (
    BLACK,
    TILE,
    _put,
    _rect,
    _register,
    register_block,
    tile,
)


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


