"""AUD-493 — una sola pista de música para las seis fases del 4-1.

Tres GAP distintos señalan el mismo defecto desde tres sitios:

* GAP-059 (Fase 1), punto 5: *«`BGM_TRACK = "bgm_final_approach"` es una
  sola pista para las seis fases — no hay mecanismo para que la Fase 1 suene
  distinta de la aproximación final a Paburu, lo que compite con el punto 5
  del dueño ("guardar el sonido como recurso")»*.
* GAP-064 (Fase 6), puntos 13-14: el tema debería *«nacer del mundo»*.
* GAP-065 §12 y su plan de resolución, punto (3): lo clasifica como uno de
  los tres huecos de infraestructura que *«resolverlos una vez sirve a las
  seis fases a la vez»*.

El efecto medible del defecto: el tema de la aproximación final a Paburu —la
carta emocional más fuerte del nivel— sonaba desde el primer paso del
cementerio, y las cuatro ambientaciones que AUD-465 generó por código
competían contra una cama de música constante.
"""
from __future__ import annotations

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pytest

from tests.ayudantes_stage4_1 import construir_escena, preparar_video
from tests.test_stage4_1 import (
    _dentro_de_la_fase,
    _posicionar_sin_fisica,
)


@pytest.fixture(scope="module")
def _video():
    preparar_video()


@pytest.fixture
def escena(_video):
    sc = construir_escena()
    yield sc
    sc.on_exit()



class _AudioEspia:
    """Anota qué se le pidió a la música, sin tocar el mezclador."""

    def __init__(self) -> None:
        self.puestas: list[str] = []
        self.paradas: int = 0
        self.ambientes: list[str] = []

    def play_music(self, path, loops=-1, fundido_ms=0) -> None:
        self.puestas.append(str(path))

    def stop_music(self) -> None:
        self.paradas += 1

    # El ambiente por fase (AUD-465) va por otro canal y no es lo que se
    # mide aquí; se acepta y se ignora, pero no se omite: si faltaran,
    # `_actualizar_sonido_de_fase` reventaría y la prueba estaría midiendo
    # una excepción en vez de la música.
    def play_ambient(self, path, volume=1.0) -> None:
        self.ambientes.append(str(path))

    def crossfade_ambient(self, path, duration=1.0, volume=1.0) -> None:
        self.ambientes.append(str(path))

    def stop_ambient(self) -> None:
        pass


def _espiar(escena, monkeypatch) -> _AudioEspia:
    espia = _AudioEspia()
    monkeypatch.setattr(
        type(escena), "audio", property(lambda _self: espia), raising=False,
    )
    return espia


class TestLaTablaDeFasesMandaSobreLaMusica:
    def test_solo_la_ultima_fase_tiene_musica(self) -> None:
        from src.stages.stage4_1.fases import FASES, MUSICA_DEL_DESPERTAR

        con_musica = [f.numero for f in FASES if f.musica is not None]
        assert con_musica == [6], (
            f"fases con música: {con_musica}. El punto 5 del dueño es "
            f"«guardar el sonido como recurso»: las cinco primeras se "
            f"sostienen con su ambiente"
        )
        assert FASES[5].musica == MUSICA_DEL_DESPERTAR

    def test_el_mapa_sigue_declarando_su_pista(self) -> None:
        """`bgm_track` es propiedad obligatoria del TMX
        (`scripts/validate_tmx.py`), así que no se quita: el mapa dice
        **cuál** es la pista del nivel y la tabla de fases decide
        **cuándo** suena."""
        from pathlib import Path

        tmx = Path("assets/maps/stage4_1/stage4_1.tmx").read_text(encoding="utf-8")
        assert 'name="bgm_track"' in tmx


class TestElCementerioEmpiezaEnSilencio:
    def test_la_fase_1_para_la_musica_del_mapa(self, escena, monkeypatch) -> None:
        espia = _espiar(escena, monkeypatch)
        # Lo que `StageScene.on_stage_start` dejó puesto, que es de donde
        # parte el defecto.
        escena._musica_sonando = "bgm_final_approach"
        escena._fase_actual = -1
        _posicionar_sin_fisica(escena, _dentro_de_la_fase(1))
        assert espia.paradas == 1, (
            "la aproximación final a Paburu sigue sonando desde el primer "
            "paso del cementerio"
        )
        assert espia.puestas == []

    def test_las_fases_2_a_5_siguen_en_silencio(self, escena, monkeypatch) -> None:
        espia = _espiar(escena, monkeypatch)
        escena._musica_sonando = None
        for numero in (2, 3, 4, 5):
            escena._fase_actual = numero - 2
            _posicionar_sin_fisica(escena, _dentro_de_la_fase(numero))
        assert espia.puestas == [], (
            f"alguna fase intermedia puso música: {espia.puestas}"
        )


class TestLaMusicaNaceEnLaFase6:
    def test_entrar_en_la_fase_6_pone_la_pista(self, escena, monkeypatch) -> None:
        espia = _espiar(escena, monkeypatch)
        escena._musica_sonando = None
        escena._fase_actual = 4
        _posicionar_sin_fisica(escena, _dentro_de_la_fase(6))
        assert len(espia.puestas) == 1, (
            "la música no entró al llegar al camino hacia Paburu"
        )
        assert "bgm_final_approach" in espia.puestas[0]

    def test_entra_con_fundido_no_de_golpe(self, escena, monkeypatch) -> None:
        """Tras cinco fases de silencio, un corte seco se oye como un
        fallo de reproducción, no como que algo despierta."""
        fundidos: list[int] = []
        espia = _AudioEspia()

        def _play(path, loops=-1, fundido_ms=0):
            fundidos.append(fundido_ms)
            espia.puestas.append(str(path))

        espia.play_music = _play  # type: ignore[method-assign]
        monkeypatch.setattr(
            type(escena), "audio", property(lambda _self: espia), raising=False,
        )
        escena._musica_sonando = None
        escena._fase_actual = 4
        _posicionar_sin_fisica(escena, _dentro_de_la_fase(6))
        assert fundidos and fundidos[0] >= 1000, (
            f"la música entró con un fundido de {fundidos}: se oirá como un "
            f"corte, no como un despertar"
        )


class TestNoSeReiniciaSola:
    def test_moverse_dentro_de_la_fase_6_no_repone_la_pista(
        self, escena, monkeypatch,
    ) -> None:
        """El mismo cuidado que `_actualizar_fase` ya tiene con el clima:
        reponer la pista en cada frontera la reiniciaría desde el principio."""
        espia = _espiar(escena, monkeypatch)
        escena._musica_sonando = None
        escena._fase_actual = 4
        _posicionar_sin_fisica(escena, _dentro_de_la_fase(6))
        assert len(espia.puestas) == 1
        for _ in range(30):
            escena._actualizar_musica_de_fase(escena.fase)
        assert len(espia.puestas) == 1, (
            "la pista se repuso sola: sonaría reiniciándose desde el principio"
        )
