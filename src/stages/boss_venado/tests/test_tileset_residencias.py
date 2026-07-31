# tests/test_tileset_residencias.py
"""
Module: test_tileset_residencias
System: tests
Description: Tileset de produccion - dimensiones, paleta cerrada y atlas nombrado.
"""
from __future__ import annotations

import hashlib
import importlib
from pathlib import Path

from PIL import Image

MOD = "src.stages.boss_venado.tools.gen_tileset_residencias"
ART_LIB = "src.stages.boss_venado.tools.art_lib"

# Frozen name contract: sha256 of ",".join(sorted(NAME_TO_INDEX)). Bump this
# DELIBERATELY (and only) when tiles are intentionally added/renamed/removed.
# Bumped for round-6 "real view": added 18 upper-sky tiles (moon 3x3 block,
# star_cluster_a/b, cloud_high_l/m/r, ridge_far_a/b, ridge_haze, campus_far).
# Bumped for round-7 (user legibility fix -- playable plane vs background lawn):
# added 5 tiles -- grass_walk_a/b/c + grass_walk_bald (lit, warm walkable turf
# with a top rim) and meadow_base (background lawn row with a contact shadow).
# Bumped for round-10 (user "hay que construir su parte faltante"): added 3 tiles
# -- plaza_slab + plaza_step_l/r, the warm stone terrace/plinth the gazebo is
# seated on (fills the cleared footprint at the base row; sky breathes above it).
# Bumped for round-11 (user "hacer el lugar donde estaban los carros"): added the
# CARPORT + VEHICLES set -- a carroof 10x2 block (20), carport_post(+_base),
# gravel(+_curb), tire, and the sedan/pickup(4x2) + tractor(3x2) vehicle blocks.
EXPECTED_NAMES_SHA = "e5831bd3c5a0e25357edbf1c4a20743870275a66cf45095f427ffdf3ff2b2c68"


def test_atlas_names_are_dense_and_unique() -> None:
    g = importlib.import_module(MOD)
    idx = g.NAME_TO_INDEX
    assert len(idx) >= 100
    assert len(set(idx.values())) == len(idx)
    assert sorted(idx.values()) == list(range(len(idx)))


def test_png_generated_conforms(tmp_path: Path) -> None:
    # Regenerated into a scratch dir -- this validates the CURRENT generator
    # code (NAME_TO_INDEX/art_lib), never the sealed game-tree PNG, so the
    # test never needs write access to assets/tilesets/.
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
    assert set(img.getdata()) <= set(art_lib.PALETTE.values()) | {(0, 0, 0)}


def test_output_is_byte_idempotent(tmp_path: Path) -> None:
    # Two independent regenerations into scratch files: proves the generator
    # itself is byte-deterministic, with no dependency on (or write to) the
    # sealed game-tree PNG.
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
