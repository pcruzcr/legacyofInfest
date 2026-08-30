"""
Modulo: test_art_lib
Sistema: tests
Descripcion: pruebas de la paleta maestra de art_lib y sus funciones
auxiliares de textura (bayer_dither, mottle, quantize_to_palette, despeckle)
extraidas de la referencia de vineta aprobada como estandar visual congelado
del mapa del boss.
"""
from __future__ import annotations
import importlib

import numpy as np


def test_palette_master_size_and_uniqueness() -> None:
    art_lib = importlib.import_module("src.stages.boss_venado.tools.art_lib")
    pal = art_lib.PALETTE  # dict nombre -> (r,g,b)
    assert 30 <= len(pal) <= 36
    assert len(set(pal.values())) == len(pal)

def test_helpers_exist() -> None:
    art_lib = importlib.import_module("src.stages.boss_venado.tools.art_lib")
    for fn in ("bayer_dither", "mottle", "quantize_to_palette", "despeckle"):
        assert callable(getattr(art_lib, fn))


def test_despeckle_replaces_isolated_orphan_with_neighbor_majority() -> None:
    art_lib = importlib.import_module("src.stages.boss_venado.tools.art_lib")
    canvas = np.zeros((5, 5, 3), dtype=np.uint8)
    canvas[:, :] = art_lib.PALETTE["O2"]
    canvas[2, 2] = art_lib.PALETTE["K0"]  # los 8 vecinos son identicos (O2), el centro difiere
    art_lib.despeckle(canvas, art_lib.PALETTE)
    assert tuple(canvas[2, 2]) == art_lib.PALETTE["O2"]


def test_despeckle_leaves_pixel_with_matching_neighbor_untouched() -> None:
    art_lib = importlib.import_module("src.stages.boss_venado.tools.art_lib")
    canvas = np.zeros((5, 5, 3), dtype=np.uint8)
    canvas[:, :] = art_lib.PALETTE["O2"]
    canvas[2, 2] = art_lib.PALETTE["K0"]
    canvas[2, 3] = art_lib.PALETTE["K0"]  # coincide con un vecino -> no esta aislado
    art_lib.despeckle(canvas, art_lib.PALETTE)
    assert tuple(canvas[2, 2]) == art_lib.PALETTE["K0"]


def test_despeckle_never_touches_protected_colors() -> None:
    art_lib = importlib.import_module("src.stages.boss_venado.tools.art_lib")
    canvas = np.zeros((5, 5, 3), dtype=np.uint8)
    canvas[:, :] = art_lib.PALETTE["O2"]
    canvas[2, 2] = art_lib.PALETTE["K0"]  # aislado, pero protegido explicitamente abajo
    art_lib.despeckle(canvas, art_lib.PALETTE, protect_keys=("K0",))
    assert tuple(canvas[2, 2]) == art_lib.PALETTE["K0"]


def test_quantize_to_palette_exact_color_roundtrips() -> None:
    art_lib = importlib.import_module("src.stages.boss_venado.tools.art_lib")
    for rgb in art_lib.PALETTE.values():
        assert tuple(art_lib.quantize_to_palette(rgb, art_lib.PALETTE)) == rgb


def test_quantize_to_palette_preserves_array_shape() -> None:
    art_lib = importlib.import_module("src.stages.boss_venado.tools.art_lib")
    img = np.zeros((4, 6, 3), dtype=np.uint8)
    out = art_lib.quantize_to_palette(img, art_lib.PALETTE)
    assert out.shape == img.shape
