"""La tubería de GPU avisa cuando no corre en la tarjeta NVIDIA.

La regla del repositorio (CLAUDE.md §2): las mediciones de GPU se toman
siempre en la Quadro M2200, porque en Windows la tarjeta la elige una
preferencia por aplicación y no SDL ni ModernGL. Lo único que dice la verdad
en caliente es el string del renderer, y este test fija qué strings valen.
"""
from __future__ import annotations

from src.engine.render.gl_pipeline import _es_tarjeta_nvidia


class TestDetectarLaTarjetaNvidia:
    def test_la_quadro_de_este_equipo(self) -> None:
        assert _es_tarjeta_nvidia("Quadro M2200/PCIe/SSE2")

    def test_geforce_de_escritorio(self) -> None:
        assert _es_tarjeta_nvidia("NVIDIA GeForce RTX 3060")

    def test_en_minusculas_tambien(self) -> None:
        assert _es_tarjeta_nvidia("nvidia geforce gtx 1650")

    def test_la_integrada_de_intel_no_vale(self) -> None:
        assert not _es_tarjeta_nvidia("Intel(R) HD Graphics 530")

    def test_amd_tampoco(self) -> None:
        assert not _es_tarjeta_nvidia("AMD Radeon RX 6600")

    def test_sin_renderer_no_vale(self) -> None:
        assert not _es_tarjeta_nvidia("?")
        assert not _es_tarjeta_nvidia("")
