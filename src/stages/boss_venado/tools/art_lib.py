"""art_lib: shared master palette + reusable pixel-art texture helpers.

Origin
------
Extracted from `tools/vignette_reference.py` (the 480x224 twilight vignette
proof approved by the user on 2026-07-23) — the frozen visual standard for
this boss's map art. Everything below is either a byte-identical copy of the
original's data/logic, or a straightforward generalisation of it (hardcoded
globals like ``canvas``/``W``/``H``/``PAL`` replaced with parameters so the
same technique can run against any array/palette). No colour value was
"improved" or re-derived — the palette here must stay byte-identical to the
approved vignette so downstream generators (tileset, TMX) share one visual
truth.

What this module exposes
-------------------------
- ``PALETTE``: the 34-colour master palette, name -> (r, g, b). A read-only
  ``types.MappingProxyType`` view (quality-review hardening: still supports
  ``len()``/indexing/``.values()``/``.items()`` like a plain dict, but can't
  be accidentally mutated).
- ``hash01(x, y, salt=0)``: deterministic per-pixel pseudo-random noise in
  [0, 1). Faithful copy; underlies both ``mottle`` and the vignette's own
  per-pixel breakup everywhere (clouds, grass, cracks, ...).
- ``BAYER_4X4``: the 4x4 ordered-dither matrix, normalised to [0, 1).
  Read-only (``setflags(write=False)``: quality-review hardening).
- ``bayer_dither(x, y, a, b, t)``: ordered (Bayer) dither pick between two
  values. Faithful copy of the original's ``dither2``.
- ``mottle(x, y, salt=0)``: multi-octave (coarse/medium/fine) clustered noise
  offset, extracted from ``wall_tone()``'s stucco mottling formula (the
  hastial wall in the vignette). With ``salt=45`` it reproduces that wall's
  mottling exactly (the original chained salts 45/46/47 for its three
  octaves; here a single ``salt`` seeds all three as salt/salt+1/salt+2).
- ``despeckle(canvas, palette, protect_keys=(), min_majority=6)``:
  generalised version of the original's ``despeckle_key()`` — clears isolated
  single-pixel colour orphans by replacing them with their neighbourhood's
  majority colour, skipping any colour listed in ``protect_keys``. Does not
  touch the canvas's outer 1px border (see its own docstring).
- ``quantize_to_palette(rgb, palette)``: NOT present in the original (which
  hand-paints every pixel with a named palette colour directly and never
  needs to snap an arbitrary colour). Added here as a foundational technique
  for later generators that may synthesise colour procedurally and need to
  snap it back onto the frozen palette. Standard nearest-colour (Euclidean,
  RGB-space) quantisation; only ever returns values already in ``palette``.

Name map (original -> here)
----------------------------
- ``PAL`` -> ``PALETTE`` (same 34 key names: S0-S5, W0-W2, F0, O0-O3, R0-R2,
  C0-C1, V0-V3, G0-G3, K0-K1, P0-P1, RM, RC, PL — untouched).
- ``BAYER`` -> ``BAYER_4X4``.
- ``dither2`` -> ``bayer_dither`` (same signature/body).
- the inline ``mott = ...`` expression inside ``wall_tone()`` -> ``mottle()``.
- ``despeckle_key()`` -> ``despeckle()`` (globals promoted to parameters).
- ``hx()`` -> ``_hx()``: kept private. It's a one-shot literal helper used
  only to build ``PALETTE`` below, not a reusable texture technique, so it
  isn't part of this module's public surface.

Composition functions from the original (``build_sky``, ``build_hastial``,
``draw_crack``, the corrugated-roof inline patterns, etc.) are scene-specific
— they paint directly onto that vignette's fixed geometry/canvas — and are
intentionally NOT extracted here. Same for anything requiring a standalone
function to exist in the original that doesn't (e.g. "corrugated sheet" and
"grass" are inline one-liners scattered per building/patch, not reusable
helpers).

This module has no side effects on import: no file I/O, no plotting, no
canvas allocation. Any demo/proof code belongs under a caller's own
``if __name__ == "__main__":``, not here.
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping
from types import MappingProxyType
from typing import TypeVar

import numpy as np

T = TypeVar("T")


def _hx(h: str) -> tuple[int, int, int]:
    """Hex string ('#RRGGBB' or 'RRGGBB') -> (r, g, b) int tuple. Faithful copy.

    Private: a one-shot literal helper used only to build ``PALETTE`` below;
    not a reusable texture technique, so it isn't exported.
    """
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


# ---------------------------------------------------------------------------
# MASTER PALETTE — byte-identical to vignette_reference.PAL (34 colours).
# Wrapped in MappingProxyType: read-only, but still supports len(), .values(),
# .keys(), .items() and palette[name] indexing exactly like a plain dict.
# ---------------------------------------------------------------------------
PALETTE: Mapping[str, tuple[int, int, int]] = MappingProxyType({
    # sky (top -> horizon), 6
    "S0": _hx("#2A2150"), "S1": _hx("#463A6E"), "S2": _hx("#6E4E7E"),
    "S3": _hx("#9C5E76"), "S4": _hx("#C86C4E"), "S5": _hx("#E8853C"),
    # warm / glow, 3
    "W0": _hx("#F2C878"), "W1": _hx("#F5E1A0"), "W2": _hx("#FFF6D0"),
    # far silhouette, 1
    "F0": _hx("#2E2448"),
    # ochre stucco wall, 4  (dusk-muted mustard, base ~#C99046)
    "O0": _hx("#47301F"), "O1": _hx("#6E4A2A"), "O2": _hx("#A2743A"), "O3": _hx("#C6934C"),
    # roof terracotta, 3  (dusk-muted ~#C74A32)
    "R0": _hx("#2A1418"), "R1": _hx("#6E2E22"), "R2": _hx("#A04A32"),
    # cenefa (cream-white fascia), 2
    "C0": _hx("#E6DCC6"), "C1": _hx("#9A8266"),
    # vegetation, 4
    "V0": _hx("#10160E"), "V1": _hx("#1E2C18"), "V2": _hx("#33482A"), "V3": _hx("#547038"),
    # stone sidewalk, 4
    "G0": _hx("#332C2A"), "G1": _hx("#574B44"), "G2": _hx("#7C6C5C"), "G3": _hx("#A08A72"),
    # ink, 2
    "K0": _hx("#0C0A0C"), "K1": _hx("#1E1620"),
    # flowers, 2
    "P0": _hx("#A83A34"), "P1": _hx("#D06048"),
    # cool rim, 1
    "RM": _hx("#B49AB0"),
    # jewelry pass: cool AA rim-light + exposed light plaster (spalls), 2
    "RC": _hx("#9AA8CE"),   # cold violet-blue rim on top silhouette edges / stars
    "PL": _hx("#C9B48A"),   # pale plaster revealed by spalled stucco
})


def hash01(x: int, y: int, salt: int = 0) -> float:
    """Deterministic pseudo-random noise in [0, 1) for pixel (x, y). Faithful copy."""
    v = (x * 374761393 + y * 668265263 + salt * 2246822519) & 0xFFFFFFFF
    v = (v ^ (v >> 13)) * 1274126177 & 0xFFFFFFFF
    return ((v ^ (v >> 16)) & 0xFFFF) / 65535.0


# Ordered dithering (Bayer 4x4), normalised to [0, 1). Faithful copy of BAYER.
# Read-only (setflags(write=False)): shared constant, never meant to be mutated.
BAYER_4X4: np.ndarray = np.array([
    [0, 8, 2, 10],
    [12, 4, 14, 6],
    [3, 11, 1, 9],
    [15, 7, 13, 5],
], dtype=np.float32) / 16.0
BAYER_4X4.setflags(write=False)


def bayer_dither(x: int, y: int, a: T, b: T, t: float) -> T:
    """Ordered (Bayer 4x4) dither pick between two values.

    Returns ``b`` if ``t`` (fraction toward ``b``, 0..1) clears the dither
    threshold at (x, y), else ``a``. Faithful copy of the original's
    ``dither2``; ``a``/``b`` are typically palette names but can be anything.
    """
    return b if t > BAYER_4X4[y & 3, x & 3] else a


def mottle(x: int, y: int, salt: int = 0) -> float:
    """Multi-octave (coarse+medium+fine) clustered mottling noise.

    Extracted from ``wall_tone()``'s stucco mottling formula in the vignette
    (soft cluster field, no directional grain): three ``hash01`` octaves at
    cluster sizes 5px/3px/1px with decreasing amplitude, summed. Returns a
    signed float offset (~-0.14..0.14) meant to be added to a base
    luminance/threshold before mapping to a palette ramp.

    ``salt`` seeds all three octaves (as salt, salt+1, salt+2); the original
    hastial wall used salts 45/46/47, i.e. ``mottle(x, y, salt=45)``
    reproduces it exactly.
    """
    return (
        (hash01(x // 5, y // 5, salt) - 0.5) * 0.15
        + (hash01(x // 3, y // 3, salt + 1) - 0.5) * 0.09
        + (hash01(x, y, salt + 2) - 0.5) * 0.04
    )


def quantize_to_palette(
    rgb: Iterable[int] | np.ndarray,
    palette: dict[str, tuple[int, int, int]],
) -> np.ndarray:
    """Snap an RGB colour (or array of colours) to the nearest colour in `palette`.

    Not present in vignette_reference.py — added as a foundational technique
    for generators that synthesise colour procedurally (e.g. from noise or
    reference photos) and need to snap it back onto the frozen palette.
    Nearest-colour by squared Euclidean distance in RGB space.

    ``rgb`` may be a single (r, g, b) tuple/sequence or a numpy array of shape
    (..., 3). Returns the matching palette value(s) as uint8, in the same
    shape as the input (never a colour absent from `palette`).
    """
    names = list(palette.keys())
    values = np.array([palette[n] for n in names], dtype=np.float32)  # (K, 3)
    arr = np.asarray(rgb, dtype=np.float32)
    single = arr.ndim == 1
    if single:
        arr = arr[None, :]
    orig_shape = arr.shape
    flat = arr.reshape(-1, 3)
    d = ((flat[:, None, :] - values[None, :, :]) ** 2).sum(axis=2)
    idx = d.argmin(axis=1)
    out = values[idx].astype(np.uint8).reshape(orig_shape)
    return out[0] if single else out


def despeckle(
    canvas: np.ndarray,
    palette: dict[str, tuple[int, int, int]],
    protect_keys: Iterable[str] = (),
    min_majority: int = 6,
) -> np.ndarray:
    """Clear isolated single-pixel colour orphans on `canvas`.

    Generalised from the original's ``despeckle_key()`` (which hardcoded the
    global ``canvas``/``H``/``W``/``PAL`` and a fixed protect list): for every
    pixel whose colour matches none of its 8 neighbours and isn't in
    `protect_keys` (palette names to leave alone, e.g. sparse bright accents
    that are meant to be isolated), replace it with the majority neighbour
    colour if at least `min_majority` of the 8 neighbours agree on one.

    `canvas` is an (H, W, 3) uint8 array, mutated in place. `palette` is the
    name -> (r, g, b) dict used to resolve `protect_keys`. Returns `canvas`.

    Caveat (faithful to the original): the outer 1px border of the canvas is
    never processed — the original iterates ``range(1, H-1)`` / ``range(1,
    W-1)``, so every pixel it actually inspects has a full 8-neighbour ring;
    border pixels are left exactly as they were, orphan or not.
    """
    H, W = canvas.shape[:2]
    packed = (
        (canvas[:, :, 0].astype(np.int32) << 16)
        | (canvas[:, :, 1].astype(np.int32) << 8)
        | canvas[:, :, 2]
    )
    protect = set()
    for k in protect_keys:
        r, g, b = palette[k]
        protect.add((r << 16) | (g << 8) | b)
    src = packed.copy()
    for y in range(1, H - 1):
        rowm1 = src[y - 1]; row = src[y]; rowp1 = src[y + 1]
        for x in range(1, W - 1):
            cpx = row[x]
            if cpx in protect:
                continue
            n = (rowm1[x - 1], rowm1[x], rowm1[x + 1], row[x - 1], row[x + 1],
                 rowp1[x - 1], rowp1[x], rowp1[x + 1])
            if cpx in n:
                continue                                    # not isolated
            best = None; bc = 0
            for v in n:
                cc = n.count(v)
                if cc > bc:
                    bc = cc; best = v
            if bc >= min_majority:                           # strong majority -> stray edge px
                canvas[y, x] = (best >> 16 & 255, best >> 8 & 255, best & 255)
    return canvas
