"""Nucleo del generador: registro de tiles y helpers de bajo nivel.

AUD-345 — extraido de ``gen_tileset_residencias.py``. El registro es global de
modulo a proposito: los decoradores ``@tile`` y las llamadas ``register_block``
corren al importar, y el orden de importacion de los modulos de tema (ver
``__init__.py``) es el orden de ``TILES``, que es el contrato del layout del
atlas: ``_compose_atlas`` pinta la celda i-esima del atlas con el tile i-esimo,
y ``NAME_TO_INDEX`` lo consume ``gen_level_residencias`` para nombrar los tiles
del TMX.
"""
from __future__ import annotations

from collections.abc import Callable

import numpy as np

from src.stages.boss_venado.tools.art_lib import PALETTE

TILE = 16
COLS = 12
BLACK = (0, 0, 0)                            # tile 0 / visual empty

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
