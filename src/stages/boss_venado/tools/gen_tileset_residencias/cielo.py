"""Pintores de tiles: cielo, atmosfera y horizonte (sol, luna, estrellas,
nubes, murcielagos, crestas y el campus lejano).

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
    _register,
    register_block,
    tile,
)


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


