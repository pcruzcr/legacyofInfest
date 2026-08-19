"""AUD-546 — reemplaza el supuesto de AUD-493: cada fase tiene su propia
pista, no sólo la última.

Este archivo probaba el diseño anterior (`AUD-493`): una sola pista de
música existía para las seis fases (`bgm_final_approach`), así que la
tabla de fases la reservaba para la Fase 6 y dejaba las cinco primeras en
silencio, apoyadas sólo en su `sonido_ambiente`. Ese razonamiento seguía
siendo correcto para el problema que resolvía — no había más que una
pista, y sonar desde el minuto cero la desgastaba.

AUD-546 cambia la premisa, no revierte el razonamiento: llegó material de
autor, una pista por fase (`assets/music/bgm_stage4_1_fase1..6.mp3`), y
el pedido fue explícito — *"usa los mp3 para cada fase correspondiente
como música de fondo que cambie de acuerdo a cada fase"*. Con seis pistas
propias, el problema de AUD-493 (una sola pista, sonando de más) no
existe: cada fase tiene la suya, y el nombre del archivo sigue siendo lo
que distingue al clímax, no el ser la única con sonido.

El nombre del archivo se conserva porque `tests/test_los_huecos_cerrados_
dicen_como.py` sigue viendo el título "la música del 4-1 entra tarde" en
`KNOWN_GAPS.md` §GAP-059/064/065: ese hueco histórico está resuelto de
verdad (había un defecto real, cero variación musical) aunque la forma en
que se resolvió cambió de nuevo con material de autor.
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


class TestLaTablaDeFasesLeDaUnaPistaACadaUna:
    def test_las_seis_fases_tienen_musica(self) -> None:
        from src.stages.stage4_1.fases import FASES, MUSICA_POR_FASE

        con_musica = [f.numero for f in FASES if f.musica is not None]
        assert con_musica == [1, 2, 3, 4, 5, 6], (
            f"fases con música: {con_musica}. AUD-546: llegó una pista de "
            f"autor por fase, ya no hay motivo para dejar ninguna en "
            f"silencio total de música"
        )
        assert tuple(f.musica for f in FASES) == MUSICA_POR_FASE

    def test_cada_fase_tiene_una_pista_distinta(self) -> None:
        """Seis pistas de verdad, no la misma repetida seis veces."""
        from src.stages.stage4_1.fases import FASES

        pistas = [f.musica for f in FASES]
        assert len(set(pistas)) == 6, (
            f"las fases repiten pista entre sí: {pistas}"
        )

    def test_la_fase_6_sigue_siendo_la_del_clímax_por_nombre_no_por_ser_la_unica(
        self,
    ) -> None:
        from src.stages.stage4_1.fases import FASES

        assert FASES[5].musica == "bgm_stage4_1_fase6"

    def test_el_mapa_sigue_declarando_su_pista(self) -> None:
        """`bgm_track` es propiedad obligatoria del TMX
        (`scripts/validate_tmx.py`), así que no se quita: el mapa dice
        **cuál** es la pista que arranca `StageScene` en el primer
        fotograma, y la tabla de fases decide qué suena a partir de ahí
        (incluida la Fase 1, ahora)."""
        from pathlib import Path

        tmx = Path("assets/maps/stage4_1/stage4_1.tmx").read_text(encoding="utf-8")
        assert 'name="bgm_track"' in tmx
        assert 'value="bgm_stage4_1_fase1"' in tmx, (
            "el mapa sigue declarando la pista del clímax como arranque; "
            "debería ser la de la Fase 1 (AUD-546) para no sonar de más "
            "ni un fotograma"
        )


class TestCadaFronteraDeFaseCambiaLaPista:
    def test_la_fase_1_pone_su_propia_pista(self, escena, monkeypatch) -> None:
        """AUD-546 invierte el comportamiento que probaba esta clase antes
        de AUD-493: la Fase 1 ya no calla la música del mapa, la
        reemplaza por la suya."""
        espia = _espiar(escena, monkeypatch)
        # Lo que `StageScene.on_stage_start` dejó puesto — la propia
        # pista de la Fase 1, ver `test_el_mapa_sigue_declarando_su_pista`.
        escena._musica_sonando = "bgm_stage4_1_fase1"
        escena._fase_actual = -1
        _posicionar_sin_fisica(escena, _dentro_de_la_fase(1))
        # La pista ya sonando coincide con la que pide la Fase 1: no hace
        # falta pararla ni reponerla.
        assert espia.paradas == 0
        assert espia.puestas == []

    def test_las_fases_2_a_6_cada_una_pone_la_suya(self, escena, monkeypatch) -> None:
        espia = _espiar(escena, monkeypatch)
        escena._musica_sonando = "bgm_stage4_1_fase1"
        for numero in (2, 3, 4, 5, 6):
            escena._fase_actual = numero - 2
            _posicionar_sin_fisica(escena, _dentro_de_la_fase(numero))
        assert len(espia.puestas) == 5, (
            f"se esperaban 5 cambios de pista (fases 2 a 6), hubo "
            f"{len(espia.puestas)}: {espia.puestas}"
        )
        for numero, puesta in zip((2, 3, 4, 5, 6), espia.puestas, strict=True):
            assert f"bgm_stage4_1_fase{numero}" in puesta, (
                f"la fase {numero} debía poner su propia pista, puso "
                f"{puesta!r}"
            )


class TestLaEntradaDeMusicaEsConFundido:
    def test_toda_entrada_de_pista_lleva_fundido(self, escena, monkeypatch) -> None:
        """Ya no es sólo la Fase 6 la que «despierta» tras el silencio —
        cada cambio de fase cruza a una pista nueva, y un corte seco entre
        pistas se oye como un fallo de reproducción."""
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
            f"la música entró con un fundido de {fundidos}: se oirá como "
            f"un corte entre pistas, no como una transición"
        )


class TestNoSeReiniciaSola:
    def test_moverse_dentro_de_una_fase_no_repone_la_pista(
        self, escena, monkeypatch,
    ) -> None:
        """El mismo cuidado que `_actualizar_fase` ya tiene con el clima:
        reponer la pista en cada frontera la reiniciaría desde el
        principio."""
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
