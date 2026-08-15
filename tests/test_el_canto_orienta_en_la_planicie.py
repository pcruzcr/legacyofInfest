"""AUD-488 — en la Planicie de los Muertos, el sonido no orientaba a nadie.

GAP-063 hace dos observaciones sobre la Fase 5 que resultan ser la misma:

* *«El sonido no es navegación, es un solo bucle ambiental.
  `sonido_ambiente = canto_ancestral.wav` es un único canal en volumen
  constante — no depende de si la luna está arriba, no tiene dirección
  (mismo hueco que GAP-062 documentó para el grito del Gavilán:
  `_play_sfx_spatial` existe y sigue sin usarse aquí), y no hay ninguna voz
  o campana que el jugador pueda seguir para orientarse (puntos 12-14).»*
* *«Nada depende de si la luna está arriba o abajo.»*

Las dos se cierran con el mismo mecanismo: un canto que suena desde un punto
fijo del mundo —así el paneo estéreo dice hacia dónde— y que sube de volumen
cuando la luna se esconde, que es cuando el oído tiene que sustituir a la
vista.

Y completa el punto 14, la *«mezcla de información confiable e información
ambigua»*: el canto es la mitad fiable; el grito del Gavilán, que desde
AUD-492 rehúye la mirada del jugador, es la ambigua.
"""
from __future__ import annotations

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

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


def _cantos(escena, monkeypatch) -> list[tuple[str, float, float]]:
    """Anota cada llamada espacial en vez de reproducirla."""
    registro: list[tuple[str, float, float]] = []
    monkeypatch.setattr(
        escena, "_play_sfx_spatial",
        lambda nombre, world_x, volume=1.0: registro.append((nombre, world_x, volume)),
    )
    return registro


def _en_la_planicie(escena) -> None:
    _posicionar_sin_fisica(escena, _dentro_de_la_fase(5))
    assert escena.fase.numero == 5


class TestElCantoVieneDeUnSitio:
    def test_suena_por_el_canal_espacial(self, escena, monkeypatch) -> None:
        registro = _cantos(escena, monkeypatch)
        _en_la_planicie(escena)
        escena._proximo_canto = 0.0
        escena._actualizar_canto_ancestral(1 / 60)
        assert len(registro) == 1
        assert registro[0][0] == "sfx_environment_canto_ancestral"

    def test_siempre_desde_la_misma_columna(self, escena, monkeypatch) -> None:
        """Un punto fijo es lo que lo vuelve una brújula. Si se moviera —o
        si sonara al azar como el grito del Gavilán— no se podría seguir."""
        from src.stages.stage4_1 import trazado

        registro = _cantos(escena, monkeypatch)
        _en_la_planicie(escena)
        for _ in range(12):
            escena._proximo_canto = 0.0
            escena._actualizar_canto_ancestral(1 / 60)
        posiciones = {x for _n, x, _v in registro}
        assert len(posiciones) == 1, (
            f"el canto sonó desde {len(posiciones)} sitios distintos: no "
            f"sirve para orientarse"
        )
        assert posiciones.pop() == pytest.approx(
            trazado.COLUMNA_DEL_CANTO * settings.TILE_SIZE,
        )

    def test_esta_hacia_la_salida_no_hacia_atras(self) -> None:
        """Seguir el canto tiene que llevar hacia adelante: si estuviera al
        principio de la sección, orientarse por el oído haría retroceder."""
        from src.stages.stage4_1 import trazado
        from src.stages.stage4_1.fases import FASES

        fase5, fase6 = FASES[4], FASES[5]
        assert fase5.desde_columna < trazado.COLUMNA_DEL_CANTO <= fase6.desde_columna
        mitad = fase5.desde_columna + (fase6.desde_columna - fase5.desde_columna) / 2
        assert trazado.COLUMNA_DEL_CANTO > mitad

    def test_fuera_de_la_planicie_no_canta(self, escena, monkeypatch) -> None:
        registro = _cantos(escena, monkeypatch)
        for numero in (1, 2, 3, 4, 6):
            _posicionar_sin_fisica(escena, _dentro_de_la_fase(numero))
            escena._proximo_canto = 0.0
            escena._actualizar_canto_ancestral(1 / 60)
        assert registro == []


class TestLaLunaMandaSobreElVolumen:
    """El punto que GAP-063 pone primero: *«nada depende de si la luna está
    arriba o abajo»*. Ahora depende esto."""

    def _volumen_con_ambiente(self, escena, monkeypatch, ambiente: float) -> float:
        registro = _cantos(escena, monkeypatch)
        _en_la_planicie(escena)
        escena._ambiente_base = ambiente
        escena._proximo_canto = 0.0
        escena._actualizar_canto_ancestral(1 / 60)
        return registro[-1][2]

    def test_llama_mas_fuerte_a_oscuras(self, escena, monkeypatch) -> None:
        con_luna = self._volumen_con_ambiente(
            escena, monkeypatch, escena.AMBIENTE_MAX_LUNA,
        )
        sin_luna = self._volumen_con_ambiente(
            escena, monkeypatch, escena.AMBIENTE_MIN_LUNA,
        )
        assert sin_luna > con_luna, (
            f"con luna {con_luna:.2f}, sin luna {sin_luna:.2f}: el oído no "
            f"sustituye a la vista"
        )

    def test_el_volumen_se_queda_en_su_rango(self, escena, monkeypatch) -> None:
        flojo, fuerte = escena.VOLUMEN_DEL_CANTO
        for ambiente in (0.0, 0.1, 0.2, 0.35, 0.48, 0.9):
            v = self._volumen_con_ambiente(escena, monkeypatch, ambiente)
            assert flojo <= v <= fuerte, f"ambiente {ambiente} dio volumen {v}"

    def test_luna_oculta_es_cero_fuera_de_la_fase_5(self, escena) -> None:
        _posicionar_sin_fisica(escena, _dentro_de_la_fase(2))
        assert escena.luna_oculta == 0.0


class TestElRitmoEsFiableNoInquietante:
    def test_el_intervalo_es_estrecho(self, escena) -> None:
        """Al revés que `ESPERA_ENTRE_GRITOS` (4-10 s), que es ancho a
        propósito para que el Gavilán no se vuelva previsible: una brújula
        que llama a intervalos impredecibles no es una brújula."""
        minimo, maximo = escena.ESPERA_ENTRE_CANTOS
        assert maximo - minimo <= 3.0
        gritos = escena.ESPERA_ENTRE_GRITOS
        assert (maximo - minimo) < (gritos[1] - gritos[0])

    def test_no_canta_en_cada_fotograma(self, escena, monkeypatch) -> None:
        registro = _cantos(escena, monkeypatch)
        _en_la_planicie(escena)
        escena._proximo_canto = escena.ESPERA_ENTRE_CANTOS[0]
        for _ in range(60 * 30):  # 30 s
            escena._actualizar_canto_ancestral(1 / 60)
        esperados = 30 / escena.ESPERA_ENTRE_CANTOS[0]
        assert len(registro) <= esperados + 1, (
            f"{len(registro)} cantos en 30 s: se convirtió en un bucle"
        )
        assert len(registro) >= 3, "el canto apenas llamó en medio minuto"
