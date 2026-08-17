"""AUD-513 — los dos últimos puntos de GAP-059 (Fase 1) sin bloqueo de diseño.

* Punto 2 — *«tumbas con reacciones distintas: una con sonido al
  acercarse, una que cambia si el jugador vuelve»*: antes la única
  variación de la Fase 1 era el easter egg (Teresa/Hugo).
* Punto 10 — *«el jugador piensa: estoy seguro de que antes estaba
  diferente»*: nada dependía de que el jugador regresara a una zona ya
  visitada.

El choque de estructura (hub vs. pasillo, mismo GAP) sigue sin resolverse
a propósito: es una decisión del dueño, no algo que se pueda cerrar desde
aquí (ver AUD-467 y la nota de GAP-065 §14).
"""
from __future__ import annotations

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

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


class TestLaTumbaSusurra:
    def test_suena_al_acercarse(self, escena, monkeypatch) -> None:
        from src.stages.stage4_1 import trazado

        llamadas = []
        monkeypatch.setattr(
            escena, "_play_sfx_spatial",
            lambda *a, **kw: llamadas.append(a),
        )
        _posicionar_sin_fisica(escena, trazado.COLUMNA_TUMBA_SUSURRO)
        escena._actualizar_tumba_susurrante()
        assert llamadas, "la tumba no sonó al acercarse"

    def test_no_suena_dos_veces_seguidas_sin_alejarse(self, escena, monkeypatch) -> None:
        from src.stages.stage4_1 import trazado

        llamadas = []
        monkeypatch.setattr(
            escena, "_play_sfx_spatial",
            lambda *a, **kw: llamadas.append(a),
        )
        _posicionar_sin_fisica(escena, trazado.COLUMNA_TUMBA_SUSURRO)
        escena._actualizar_tumba_susurrante()
        escena._actualizar_tumba_susurrante()
        escena._actualizar_tumba_susurrante()
        assert len(llamadas) == 1, (
            f"sonó {len(llamadas)} veces seguidas sin que el jugador se alejara"
        )

    def test_vuelve_a_armarse_al_alejarse(self, escena, monkeypatch) -> None:
        from src.stages.stage4_1 import trazado

        llamadas = []
        monkeypatch.setattr(
            escena, "_play_sfx_spatial",
            lambda *a, **kw: llamadas.append(a),
        )
        _posicionar_sin_fisica(escena, trazado.COLUMNA_TUMBA_SUSURRO)
        escena._actualizar_tumba_susurrante()
        assert len(llamadas) == 1

        columna_lejos = trazado.COLUMNA_TUMBA_SUSURRO + int(
            escena.DISTANCIA_REARME_SUSURRO / 16) + 5
        _posicionar_sin_fisica(escena, columna_lejos)
        escena._actualizar_tumba_susurrante()

        _posicionar_sin_fisica(escena, trazado.COLUMNA_TUMBA_SUSURRO)
        escena._actualizar_tumba_susurrante()
        assert len(llamadas) == 2, "no volvió a sonar tras alejarse y volver"

    def test_no_suena_fuera_de_la_fase_1(self, escena, monkeypatch) -> None:
        from src.stages.stage4_1.fases import FASES

        llamadas = []
        monkeypatch.setattr(
            escena, "_play_sfx_spatial",
            lambda *a, **kw: llamadas.append(a),
        )
        _posicionar_sin_fisica(escena, FASES[1].desde_columna + 1)
        escena._actualizar_tumba_susurrante()
        assert not llamadas


class TestLaMemoriaEspacial:
    def test_no_hay_regreso_si_nunca_se_avanzo(self, escena) -> None:
        from src.stages.stage4_1 import trazado

        _posicionar_sin_fisica(escena, trazado.COLUMNA_LAPIDA_TERESA)
        escena._actualizar_memoria_espacial()
        assert escena._regreso_a_la_tumba is False

    def test_regresar_tras_avanzar_mucho_se_detecta(self, escena) -> None:
        from src.stages.stage4_1 import trazado

        _posicionar_sin_fisica(escena, 120)
        escena._actualizar_memoria_espacial()
        assert escena._regreso_a_la_tumba is False, (
            "sanity: avanzar solo no debe marcar un regreso"
        )

        _posicionar_sin_fisica(escena, trazado.COLUMNA_LAPIDA_TERESA)
        escena._actualizar_memoria_espacial()
        assert escena._regreso_a_la_tumba is True, (
            "volver desde la columna 120 hasta la lápida no se detectó como regreso"
        )

    def test_un_pequeno_vaiven_no_cuenta_como_regreso(self, escena) -> None:
        _posicionar_sin_fisica(escena, 50)
        escena._actualizar_memoria_espacial()
        _posicionar_sin_fisica(escena, 45)
        escena._actualizar_memoria_espacial()
        assert escena._regreso_a_la_tumba is False

    def test_el_fantasma_se_ve_mas_presente_al_regresar(self, escena) -> None:
        """El único efecto visible del regreso: el piso del vaivén de alfa
        sube. No cambia de forma ni de color."""
        import unittest.mock as mock

        import pygame

        from src.stages.stage4_1 import trazado

        _posicionar_sin_fisica(escena, trazado.COLUMNA_LAPIDA_TERESA)
        offset = pygame.Vector2(trazado.COLUMNA_LAPIDA_TERESA * 16 - 400, 0)

        def _alfa_pintado() -> int:
            with mock.patch(
                "src.stages.stage4_1.siluetas.dibujar_contorno",
            ) as espia:
                escena._dibujar_fantasma_personal(
                    pygame.Surface((800, 600)), offset)
            assert espia.called
            return espia.call_args.args[7]

        escena._tiempo = 0.0
        escena._regreso_a_la_tumba = False
        alfa_normal = _alfa_pintado()

        escena._regreso_a_la_tumba = True
        alfa_regreso = _alfa_pintado()

        assert alfa_regreso > alfa_normal
