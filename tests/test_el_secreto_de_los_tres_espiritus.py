"""AUD-584 — GAP-064 punto 32, el secreto opcional de los tres espíritus.

El diseño pide *«un secreto opcional»* para quien liberó a los tres
espíritus de verdad (AUD-474) y además se detiene a mirar. Las dos piezas
ya existían por separado —la quietud que revela (`atencion.Atencion`,
AUD-492) y el registro de quién fue liberado—; éste es el cruce de las
dos: junto al mirador de la Fase 6, detenerse unos segundos con los tres
liberados los reúne una vez, juntos, antes del final.

Es opcional por construcción: no hay disparador ni cartel — si nunca te
detienes, o no liberaste a los tres, no existe.
"""
from __future__ import annotations

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame
import pytest

from src.engine.core import settings
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


def _liberar_a_los_tres(escena) -> None:
    from src.stages.stage4_1 import trazado
    from src.stages.stage4_1.fases import FASES

    for fase in FASES:
        if fase.espiritu is None:
            continue
        evento = trazado.evento_de_liberacion(fase.numero)
        for d in escena._stage_data.disparadores:
            if d.evento == evento:
                d.disparado = True


def _pararse_en_el_secreto(escena) -> None:
    from src.stages.stage4_1 import trazado

    _posicionar_sin_fisica(
        escena, trazado.COLUMNA_DEL_SECRETO)
    escena._atencion.quietud = 99.0


class TestElSecretoDeLosTresEspiritus:
    def test_sin_liberar_a_los_tres_no_existe(self, escena) -> None:
        from src.stages.stage4_1 import trazado
        from src.stages.stage4_1.fases import FASES

        _posicionar_sin_fisica(escena, 40)
        for fase in FASES:
            if fase.espiritu is None or fase.espiritu == 2:
                continue
            evento = trazado.evento_de_liberacion(fase.numero)
            for d in escena._stage_data.disparadores:
                if d.evento == evento:
                    d.disparado = True
        _pararse_en_el_secreto(escena)
        escena._actualizar_secreto_de_los_espiritus(1 / 60)
        assert not escena._secreto_visto

    def test_lejos_del_mirador_no_existe(self, escena) -> None:
        _liberar_a_los_tres(escena)
        _posicionar_sin_fisica(escena, 820)
        escena._atencion.quietud = 99.0
        escena._actualizar_secreto_de_los_espiritus(1 / 60)
        assert not escena._secreto_visto

    def test_en_movimiento_no_existe(self, escena) -> None:
        _liberar_a_los_tres(escena)
        _pararse_en_el_secreto(escena)
        escena._atencion.quietud = 0.0
        escena._actualizar_secreto_de_los_espiritus(1 / 60)
        assert not escena._secreto_visto

    def test_detenerse_con_los_tres_los_reune(self, escena) -> None:
        _liberar_a_los_tres(escena)
        _pararse_en_el_secreto(escena)
        escena._actualizar_secreto_de_los_espiritus(1 / 60)
        assert escena._secreto_visto, (
            "quieto junto al mirador con los tres liberados: el secreto "
            "tenía que ocurrir")
        assert escena._secreto_fundido > 0.0

    def test_solo_ocurre_una_vez(self, escena) -> None:
        _liberar_a_los_tres(escena)
        _pararse_en_el_secreto(escena)
        escena._actualizar_secreto_de_los_espiritus(1 / 60)
        escena._secreto_fundido = 0.0
        escena._actualizar_secreto_de_los_espiritus(1 / 60)
        assert escena._secreto_fundido == 0.0, (
            "el secreto se volvió a encender: es una sola vez")

    def test_se_dibuja_y_se_apaga(self, escena) -> None:
        _liberar_a_los_tres(escena)
        _pararse_en_el_secreto(escena)
        escena._actualizar_secreto_de_los_espiritus(1 / 60)
        lienzo = pygame.Surface(
            (settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT))
        escena._dibujar_secreto_de_los_espiritus(
            lienzo, pygame.Vector2(0.0, 0.0))
        assert _hay_tinta(lienzo)
        for _ in range(int(escena.DURACION_DEL_SECRETO * 60) + 5):
            escena._actualizar_secreto_de_los_espiritus(1 / 60)
        assert escena._secreto_fundido <= 0.0
        lienzo = pygame.Surface(
            (settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT))
        escena._dibujar_secreto_de_los_espiritus(
            lienzo, pygame.Vector2(0.0, 0.0))
        assert not _hay_tinta(lienzo)


def _hay_tinta(lienzo: pygame.Surface) -> bool:
    ancho, alto = lienzo.get_size()
    for y in range(60, alto // 2, 6):
        for x in range(0, ancho, 8):
            if lienzo.get_at((x, y))[:3] != (0, 0, 0):
                return True
    return False
