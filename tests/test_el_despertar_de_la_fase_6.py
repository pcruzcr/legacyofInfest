"""AUD-513 — dos puntos de GAP-064 (Fase 6) que quedaban pendientes.

* Punto 6 — las grietas encendían siempre a la misma distancia y se
  apagaban siempre al mismo ritmo, en toda la Fase 6: *«empiezan pocas y
  aumentan... el entorno completo parece estar conectado por ellas»*.
* Punto 25 — el final era un corte seco: *«vibración del suelo, shake
  pequeño... la música se detiene, silencio, un sonido profundo»* antes de
  cruzar a `stage4_2_boss_paburu`.
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


class TestLasGrietasEscalan:
    def test_se_encienden_mas_lejos_al_final_del_tramo(self, escena) -> None:
        from src.stages.stage4_1.fases import FASES

        fase6 = FASES[5]
        _posicionar_sin_fisica(escena, fase6.desde_columna + 1)
        distancia_inicial = escena.DISTANCIA_DE_GRIETA + escena._avance_en_fase(
            escena.fase) * (escena.DISTANCIA_DE_GRIETA_FINAL - escena.DISTANCIA_DE_GRIETA)

        _posicionar_sin_fisica(escena, fase6.desde_columna + 149)
        distancia_final = escena.DISTANCIA_DE_GRIETA + escena._avance_en_fase(
            escena.fase) * (escena.DISTANCIA_DE_GRIETA_FINAL - escena.DISTANCIA_DE_GRIETA)

        assert distancia_final > distancia_inicial
        assert distancia_final == pytest.approx(escena.DISTANCIA_DE_GRIETA_FINAL, abs=1.0)

    def test_tardan_mas_en_apagarse_al_final(self, escena) -> None:
        """El «entorno completo conectado»: más grietas encendidas a la
        vez cerca del final, porque tardan más en apagarse detrás del
        jugador."""
        from src.stages.stage4_1.fases import FASES

        fase6 = FASES[5]
        _posicionar_sin_fisica(escena, fase6.desde_columna + 149)
        assert escena.BAJADA_DE_GRIETA_FINAL > escena.BAJADA_DE_GRIETA


class TestLaSecuenciaDeDespertar:
    def _tras_el_despertar(self, escena, avance: float):
        from src.stages.stage4_1 import trazado
        from src.stages.stage4_1.fases import FASES

        fase6 = FASES[5]
        columna = fase6.desde_columna + int(avance * trazado.ANCHO_SECCION)
        _posicionar_sin_fisica(escena, columna)
        return fase6

    def test_no_dispara_antes_del_umbral(self, escena) -> None:
        self._tras_el_despertar(escena, escena.AVANCE_DEL_DESPERTAR - 0.05)
        escena._actualizar_secuencia_de_despertar()
        assert escena._despertar_disparado is False

    def test_dispara_una_vez_pasado_el_umbral(self, escena, monkeypatch) -> None:
        sonidos = []
        monkeypatch.setattr(
            escena, "_play_sfx_named",
            lambda *a, **kw: sonidos.append(a),
        )
        self._tras_el_despertar(escena, escena.AVANCE_DEL_DESPERTAR + 0.02)
        escena._actualizar_secuencia_de_despertar()
        assert escena._despertar_disparado is True
        assert sonidos, "la secuencia de despertar no reprodujo ningún sonido"

    def test_usa_el_sonido_profundo_propio_no_un_cue_de_jefe(self, escena, monkeypatch) -> None:
        """AUD-515 — antes tomaba prestado `sfx_bosses_phase_change`, un cue
        de combate sin relación con «el mundo despierta»."""
        sonidos = []
        monkeypatch.setattr(
            escena, "_play_sfx_named",
            lambda *a, **kw: sonidos.append(a[0] if a else None),
        )
        self._tras_el_despertar(escena, escena.AVANCE_DEL_DESPERTAR + 0.02)
        escena._actualizar_secuencia_de_despertar()
        assert sonidos == ["sfx_environment_despertar_profundo"]

    def test_no_se_repite_en_la_misma_visita(self, escena, monkeypatch) -> None:
        llamadas = []
        monkeypatch.setattr(
            escena, "_play_sfx_named",
            lambda *a, **kw: llamadas.append(a),
        )
        self._tras_el_despertar(escena, escena.AVANCE_DEL_DESPERTAR + 0.02)
        escena._actualizar_secuencia_de_despertar()
        escena._actualizar_secuencia_de_despertar()
        escena._actualizar_secuencia_de_despertar()
        assert len(llamadas) == 1, (
            f"la secuencia disparó {len(llamadas)} veces en la misma visita"
        )

    def test_se_reinicia_al_reentrar_a_la_fase_6(self, escena) -> None:
        from src.stages.stage4_1.fases import FASES

        self._tras_el_despertar(escena, escena.AVANCE_DEL_DESPERTAR + 0.02)
        escena._actualizar_secuencia_de_despertar()
        assert escena._despertar_disparado is True

        # Salir de la Fase 6 y volver a entrar: `_actualizar_fase` debe
        # reiniciar la bandera, igual que ya hace con `_shake_disparado`
        # de la Fase 4.
        _posicionar_sin_fisica(escena, FASES[4].desde_columna + 1)
        _posicionar_sin_fisica(escena, FASES[5].desde_columna + 1)
        assert escena._despertar_disparado is False
