"""AUD-579 — GAP-060 punto 16, «el bosque observa» en la Fase 2.

El dueño pidió señales de que el bosque mira: *«ramas sin viento, ojos
entre árboles, huellas, una figura, hojas desplazándose»*. Las huellas
existen desde AUD-513 y el Venado asoma a destellos desde AUD-479; lo que
faltaba son los **ojos** — pares de puntos que se abren en la línea de
árboles y **se cierran si el jugador se acerca** (mirar de vuelta los
cierra, que es lo que hace inquietante a la señal) — y las **hojas
muertas** que el viento arrastra cruzando la pantalla.

Sólo corren en la Fase 2: es su sección, y fuera de ella serían ruido.
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
from tests.test_stage4_1 import _dentro_de_la_fase, _posicionar_sin_fisica


@pytest.fixture(scope="module")
def _video():
    preparar_video()


@pytest.fixture
def escena(_video):
    sc = construir_escena()
    yield sc
    sc.on_exit()


class TestLosOjosDelBosque:
    def test_se_abren_cuando_su_temporizador_vence(
        self, escena,
    ) -> None:
        _posicionar_sin_fisica(escena, _dentro_de_la_fase(2))
        escena._ojos_visibles = 0.0
        escena._proxima_aparicion_ojos = 0.0

        escena._actualizar_bosque_que_observa(0.016)

        assert escena._ojos_visibles > 0.0, (
            "el temporizador venció y los ojos no se abrieron"
        )

    def test_se_cierran_si_el_jugador_se_acercan(
        self, escena,
    ) -> None:
        columna = _dentro_de_la_fase(2)
        _posicionar_sin_fisica(escena, columna)
        escena._ojos_visibles = 3.0
        escena._ojos_columna = float(columna)

        # El jugador cae justo debajo del par: mirar de vuelta los cierra.
        escena._actualizar_bosque_que_observa(0.016)

        assert escena._ojos_visibles == 0.0, (
            "los ojos siguieron abiertos con el jugador encima"
        )

    def test_no_abren_fuera_de_la_fase_2(self, escena) -> None:
        _posicionar_sin_fisica(escena, _dentro_de_la_fase(1))
        escena._ojos_visibles = 0.0
        escena._proxima_aparicion_ojos = 0.0

        escena._actualizar_bosque_que_observa(0.016)

        assert escena._ojos_visibles == 0.0

    def test_dibujarlos_no_explota(self, escena) -> None:
        _posicionar_sin_fisica(escena, _dentro_de_la_fase(2))
        escena._ojos_visibles = 1.0
        escena._ojos_columna = float(_dentro_de_la_fase(2))
        lienzo = pygame.Surface(
            (settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT))
        escena._dibujar_bosque_que_observa(lienzo, pygame.Vector2(0.0, 0.0))


class TestLasHojasConViento:
    def test_el_viento_suelta_hojas_en_la_fase_2(self, escena) -> None:
        _posicionar_sin_fisica(escena, _dentro_de_la_fase(2))
        for _ in range(30):
            escena._actualizar_bosque_que_observa(0.05)

        assert len(escena._hojas) > 0, (
            "medio segundo de Fase 2 y el viento no soltó ninguna hoja"
        )

    def test_las_hojas_avanzan_contra_el_jugador(self, escena) -> None:
        _posicionar_sin_fisica(escena, _dentro_de_la_fase(2))
        escena._hojas.clear()
        escena._hojas.append({"x": 5000.0, "y": 200.0, "vaiven": 0.0})
        antes = escena._hojas[0]["x"]

        escena._actualizar_bosque_que_observa(0.1)

        assert escena._hojas[0]["x"] < antes, (
            "la hoja no se movió contra el viento (el viento del nivel sopla "
            "hacia la izquierda, fuerza_x negativa)"
        )

    def test_ninguna_hoja_fuera_de_la_fase_2(self, escena) -> None:
        _posicionar_sin_fisica(escena, _dentro_de_la_fase(1))
        for _ in range(30):
            escena._actualizar_bosque_que_observa(0.05)

        assert len(escena._hojas) == 0

    def test_dibujarlas_no_explota(self, escena) -> None:
        _posicionar_sin_fisica(escena, _dentro_de_la_fase(2))
        escena._hojas.append({"x": 100.0, "y": 200.0, "vaiven": 0.0})
        lienzo = pygame.Surface(
            (settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT))
        escena._dibujar_bosque_que_observa(lienzo, pygame.Vector2(0.0, 0.0))
