# tests/test_tileset_residencias.py
"""
Modulo: test_tileset_residencias
Sistema: tests
Descripcion: Tileset de produccion - dimensiones, paleta cerrada y atlas nombrado.
"""
from __future__ import annotations

import hashlib
import importlib
from pathlib import Path

from PIL import Image

MOD = "src.stages.boss_venado.tools.gen_tileset_residencias"
ART_LIB = "src.stages.boss_venado.tools.art_lib"

# Contrato de nombres congelado: sha256 de ",".join(sorted(NAME_TO_INDEX)).
# Cambiar este hash DELIBERADAMENTE (y solo) cuando se agreguen/renombren/quiten
# tiles a proposito.
# Actualizado en la ronda 6 "vista real": se agregaron 18 tiles de cielo
# superior (bloque de luna 3x3, star_cluster_a/b, cloud_high_l/m/r,
# ridge_far_a/b, ridge_haze, campus_far).
# Actualizado en la ronda 7 (fix de legibilidad pedido por el usuario --
# plano jugable vs cesped de fondo): se agregaron 5 tiles -- grass_walk_a/b/c
# + grass_walk_bald (cesped caminable iluminado y calido con un borde superior)
# y meadow_base (fila de cesped de fondo con sombra de contacto).
# Actualizado en la ronda 10 (usuario dijo "hay que construir su parte
# faltante"): se agregaron 3 tiles -- plaza_slab + plaza_step_l/r, la
# terraza/pedestal de piedra calida sobre la que se asienta el gazebo (llena
# la huella despejada en la fila base; el cielo respira arriba).
# Actualizado en la ronda 11 (usuario dijo "hacer el lugar donde estaban los
# carros"): se agrego el set de CARPORT + VEHICULOS -- un bloque carroof
# 10x2 (20), carport_post(+_base), gravel(+_curb), tire, y los bloques de
# vehiculo sedan/pickup(4x2) + tractor(3x2).
EXPECTED_NAMES_SHA = "e5831bd3c5a0e25357edbf1c4a20743870275a66cf45095f427ffdf3ff2b2c68"


def test_atlas_names_are_dense_and_unique() -> None:
    g = importlib.import_module(MOD)
    idx = g.NAME_TO_INDEX
    assert len(idx) >= 100
    assert len(set(idx.values())) == len(idx)
    assert sorted(idx.values()) == list(range(len(idx)))


def test_png_generated_conforms(tmp_path: Path) -> None:
    # Regenerado en un directorio de descarte -- esto valida el codigo ACTUAL
    # del generador (NAME_TO_INDEX/art_lib), nunca el PNG sellado del arbol
    # del juego, asi que la prueba jamas necesita acceso de escritura a
    # assets/tilesets/.
    g = importlib.import_module(MOD)
    out = tmp_path / "atlas.png"
    g.main(out_png=out, contact_png=tmp_path / "contact.png")
    img = Image.open(out).convert("RGB")
    assert img.width == 12 * 16
    assert img.height % 16 == 0
    colors = img.getcolors(maxcolors=4096)
    assert colors is not None and len(colors) <= 36 + 1


def test_palette_is_closed(tmp_path: Path) -> None:
    g = importlib.import_module(MOD)
    art_lib = importlib.import_module(ART_LIB)
    out = tmp_path / "atlas.png"
    g.main(out_png=out, contact_png=tmp_path / "contact.png")
    img = Image.open(out).convert("RGB")
    # AU-20260826-02: `Image.getdata` está deprecado (se elimina en Pillow 14,
    # 2027-10) — migrado a `getcolors`, que no está deprecado, existe en TODAS
    # las versiones de Pillow y ya es el idioma de este archivo (ver
    # `test_png_generated_conforms` arriba). Se descartó `get_flattened_data`
    # (el reemplazo que sugiere el propio warning): es drop-in en Pillow 12.3
    # pero no existe en Pillow < 11.3 — riesgo de portabilidad innecesario
    # para la misma semántica.
    colores = {color for _, color in img.getcolors(maxcolors=img.width * img.height)}
    assert colores <= set(art_lib.PALETTE.values()) | {(0, 0, 0)}


def test_output_is_byte_idempotent(tmp_path: Path) -> None:
    # Dos regeneraciones independientes en archivos de descarte: demuestra que
    # el propio generador es determinista a nivel de bytes, sin depender de
    # (ni escribir en) el PNG sellado del arbol del juego.
    g = importlib.import_module(MOD)
    out_a = tmp_path / "atlas_a.png"
    out_b = tmp_path / "atlas_b.png"
    g.main(out_png=out_a, contact_png=tmp_path / "contact_a.png")
    g.main(out_png=out_b, contact_png=tmp_path / "contact_b.png")
    first = hashlib.sha256(out_a.read_bytes()).hexdigest()
    second = hashlib.sha256(out_b.read_bytes()).hexdigest()
    assert first == second


def test_name_contract_is_frozen() -> None:
    g = importlib.import_module(MOD)
    names_sha = hashlib.sha256(",".join(sorted(g.NAME_TO_INDEX)).encode()).hexdigest()
    assert names_sha == EXPECTED_NAMES_SHA
