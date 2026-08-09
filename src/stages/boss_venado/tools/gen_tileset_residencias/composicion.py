"""Composicion: rutas de salida, atlas, contact sheet y ``main``.

AUD-345 — extraido de ``gen_tileset_residencias.py``. ``_compose_atlas`` itera
``TILES`` en orden de registro y despecklea celda a celda (el relleno por
vecindario de atlas desacoplaria cada tile del orden de registro); la razon de
la pasada esta en su docstring original, preservado abajo.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from src.stages.boss_venado.tools.art_lib import PALETTE, despeckle

from .core import COLS, TILE, TILES

# Bright, deliberately-isolated accents that despeckle must never clear.
_PROTECT = (
    "W0", "W1", "W2", "S4", "S5", "RC", "RM",
    "P0", "P1", "O3", "PL", "V3", "G3",
)


def _raiz_del_juego() -> Path:
    """La raiz del repo, hallada por marca y no por profundidad de ``__file__``.

    AUD-345 — el original usaba ``parents[4]`` de un archivo plano; en un
    paquete la profundidad cambia y el numero magico se rompe. Subir hasta
    encontrar el directorio que contiene ``src/stages`` es estable a cualquier
    profundidad.
    """
    p = Path(__file__).resolve()
    for padre in p.parents:
        if (padre / "src" / "stages").is_dir():
            return padre
    raise RuntimeError("no se encontro la raiz del juego subiendo desde " + str(p))


GAME_ROOT = _raiz_del_juego()                # .../game
LAB_ROOT = GAME_ROOT.parent                  # .../Centro de pruebas CPG I
OUT_PNG = GAME_ROOT / "assets" / "tilesets" / "tileset_residencias_crepusculo.png"
CONTACT_DIR = LAB_ROOT / "reports" / "map_residencias"
CONTACT_PNG = CONTACT_DIR / "tileset_contact_sheet.png"

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
