"""AUD-513 — dos puntos de GAP-063 que quedaban pendientes tras AUD-482/488.

* Punto 7 — *«cuando la luna está oculta pueden ocurrir cosas: una figura
  aparece, una tumba se abre, una sombra cruza»*: nada en la Fase 5 leía
  `luna_oculta` salvo el canto ancestral (AUD-488).
* Punto 21 — *«árbol muerto, torre, capilla, roca, grupo de tumbas»*:
  landmarks distintos entre sí, no la misma cruz cada 30 columnas.
"""
from __future__ import annotations

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame
import pytest

from tests.ayudantes_stage4_1 import construir_escena, preparar_video
from tests.test_stage4_1 import _posicionar_sin_fisica


@pytest.fixture(scope="module")
def _video():
    preparar_video()


@pytest.fixture
def escena(_video):
    sc = construir_escena()
    yield sc
    sc.on_exit()


def _en_la_planicie(escena):
    from src.stages.stage4_1.fases import FASES

    fase5 = FASES[4]
    _posicionar_sin_fisica(escena, fase5.desde_columna + 1)
    assert escena.fase.numero == 5
    return fase5


class TestLaFiguraSoloConLaLunaOculta:
    def test_no_aparece_con_la_luna_alta(self, escena) -> None:
        import unittest.mock as mock

        _en_la_planicie(escena)
        escena._ambiente_base = escena.AMBIENTE_MAX_LUNA
        assert escena.luna_oculta < escena.UMBRAL_LUNA_OCULTA
        with mock.patch(
            "src.stages.stage4_1.siluetas.dibujar_contorno",
        ) as espia:
            escena._dibujar_figura_de_la_luna(pygame.Surface((800, 600)), pygame.Vector2(0, 0))
        assert not espia.called

    def test_aparece_con_la_luna_oculta(self, escena) -> None:
        import unittest.mock as mock

        from src.stages.stage4_1 import trazado

        _en_la_planicie(escena)
        escena._ambiente_base = escena.AMBIENTE_MIN_LUNA
        assert escena.luna_oculta == pytest.approx(1.0)
        col_centro = trazado.TUMBAS_FASE5[len(trazado.TUMBAS_FASE5) // 2] + 3
        offset = pygame.Vector2(col_centro * 16 - 400, 0)
        with mock.patch(
            "src.stages.stage4_1.siluetas.dibujar_contorno",
        ) as espia:
            escena._dibujar_figura_de_la_luna(pygame.Surface((800, 600)), offset)
        assert espia.called

    def test_no_aparece_fuera_de_la_fase_5(self, escena) -> None:
        import unittest.mock as mock

        from src.stages.stage4_1.fases import FASES

        _posicionar_sin_fisica(escena, FASES[3].desde_columna + 1)
        escena._ambiente_base = 0.0
        with mock.patch(
            "src.stages.stage4_1.siluetas.dibujar_contorno",
        ) as espia:
            escena._dibujar_figura_de_la_luna(pygame.Surface((800, 600)), pygame.Vector2(0, 0))
        assert not espia.called


class TestLosLandmarksVarian:
    def test_las_tumbas_no_son_todas_la_misma_silueta(self, escena) -> None:
        import unittest.mock as mock

        from src.stages.stage4_1 import siluetas, trazado

        _en_la_planicie(escena)
        formas_vistas = set()
        for columna in trazado.TUMBAS_FASE5:
            offset = pygame.Vector2((columna * 16 - 400) / 0.85, 0)
            with mock.patch(
                "src.stages.stage4_1.siluetas.dibujar_contorno",
            ) as espia:
                escena._dibujar_decoracion(pygame.Surface((800, 600)), offset)
            assert espia.called
            formas_vistas.add(espia.call_args.args[1])
        assert len(formas_vistas) == len(siluetas.LANDMARKS_DE_LA_PLANICIE), (
            f"sólo se vieron {len(formas_vistas)} siluetas distintas de "
            f"{len(siluetas.LANDMARKS_DE_LA_PLANICIE)}: las tumbas siguen "
            "leyéndose como la misma cruz repetida"
        )
