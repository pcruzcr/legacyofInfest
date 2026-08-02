"""
El cronómetro de speedrun y el fantasma, ante un fichero corrupto.

AUD-171 — el hallazgo
=====================
`AUD-100` fijó una política para los datos del jugador en disco: un fichero
corrupto **no tumba el juego, pero tampoco desaparece en silencio**. Se aplicó
al bestiario, a los logros y al inventario, y `test_corrupt_saves_are_loud.py`
la vigila desde entonces.

`speedrun_mode.py` se quedó fuera, con exactamente la forma que aquella
auditoría había condenado, y en dos sitios::

    except (FileNotFoundError, orjson.JSONDecodeError):
        pass

Que el mismo proyecto trate la misma situación de dos maneras opuestas es lo
que convierte esto en un defecto y no en una preferencia — la frase es de
AUD-100 y sigue valiendo.

El segundo defecto, que era peor
--------------------------------
El `except` sólo nombraba `JSONDecodeError`, así que cubría «esto no es JSON».
No cubría «esto es JSON perfectamente válido, de otra forma»:

* `SpeedrunTimer.load` hacía `data.get("global_time", 0.0)`. Con un fichero
  que contuviera `[]` —JSON válido—, `orjson` devuelve una lista, `.get` no
  existe en una lista y salía un `AttributeError` **sin capturar**, por encima
  de `load()`, hasta donde llegara.
* `GhostData.load` asignaba el resultado a `self._frames` sin mirarlo. Con un
  fichero que contuviera `{"a": 1}`, el fantasma se quedaba con un diccionario
  donde el resto del módulo espera una lista: `frame_count` seguía
  respondiendo, y `get_frame(0)` reventaba con `KeyError` mucho más tarde y
  muy lejos del fichero que lo causó.

Un fichero de datos del jugador no es una fuente de confianza. Puede venir de
una versión anterior, de un disco que se llenó a mitad de la escritura o de
alguien que lo editó a mano — y las tres cosas producen JSON válido con la
forma equivocada mucho más a menudo que basura sin parsear.
"""
from __future__ import annotations

import logging

import pytest

from src.framework.stage.speedrun_mode import GhostData, SpeedrunTimer

#: Basura que no es JSON por ninguna vía.
BASURA = b"{esto no es json, ni pretende serlo"

#: JSON **válido** cuya forma no es la que el cargador espera. Es el caso que
#: el `except` anterior no cubría.
FORMAS_EQUIVOCADAS = [
    pytest.param(b"[]", id="lista-vacia"),
    pytest.param(b"[1, 2, 3]", id="lista-de-numeros"),
    pytest.param(b'"una cadena"', id="cadena"),
    pytest.param(b"42", id="numero"),
    pytest.param(b"null", id="null"),
]


class TestElCronometro:
    def test_un_fichero_corrupto_avisa_y_no_lanza(self, tmp_path, caplog) -> None:
        roto = tmp_path / "speedrun.json"
        roto.write_bytes(BASURA)
        crono = SpeedrunTimer()

        with caplog.at_level(logging.WARNING):
            crono.load(roto)

        assert any("ilegible" in r.getMessage() for r in caplog.records), (
            "el cronómetro se comió un fichero corrupto sin decir nada"
        )

    def test_el_aviso_nombra_la_ruta_que_fallo(self, tmp_path, caplog) -> None:
        roto = tmp_path / "otro_sitio.json"
        roto.write_bytes(BASURA)

        with caplog.at_level(logging.WARNING):
            SpeedrunTimer().load(roto)

        assert any("otro_sitio.json" in r.getMessage() for r in caplog.records), (
            "el aviso no dice cuál de los ficheros falló"
        )

    def test_sin_fichero_no_hay_aviso(self, tmp_path, caplog) -> None:
        """Que no exista todavía es lo normal la primera vez que se juega."""
        with caplog.at_level(logging.WARNING):
            SpeedrunTimer().load(tmp_path / "no_existe.json")

        assert not [r for r in caplog.records if r.levelno >= logging.WARNING], (
            "un arranque limpio no puede parecer un error"
        )

    @pytest.mark.parametrize("contenido", FORMAS_EQUIVOCADAS)
    def test_json_valido_con_forma_equivocada_no_lanza(
        self, tmp_path, caplog, contenido: bytes
    ) -> None:
        raro = tmp_path / "speedrun.json"
        raro.write_bytes(contenido)
        crono = SpeedrunTimer()

        with caplog.at_level(logging.WARNING):
            crono.load(raro)   # antes: AttributeError sin capturar

        assert crono.global_time == 0.0
        assert crono.get_splits() == []
        assert any("ilegible" in r.getMessage() for r in caplog.records)

    def test_un_fichero_correcto_sigue_cargando(self, tmp_path) -> None:
        """La red de seguridad no puede tragarse el caso bueno."""
        crono = SpeedrunTimer()
        crono._global_time = 12.5
        crono._splits = [{"stage": "stage0", "time": 12.5}]
        destino = tmp_path / "speedrun.json"
        crono.save(destino)

        leido = SpeedrunTimer()
        leido.load(destino)

        assert leido.global_time == 12.5
        assert leido.get_splits() == [{"stage": "stage0", "time": 12.5}]


class TestElFantasma:
    def test_un_fichero_corrupto_avisa_y_no_lanza(self, tmp_path, caplog) -> None:
        roto = tmp_path / "ghost.json"
        roto.write_bytes(BASURA)
        fantasma = GhostData()

        with caplog.at_level(logging.WARNING):
            fantasma.load(roto)

        assert fantasma.frame_count == 0
        assert any("ilegible" in r.getMessage() for r in caplog.records)

    @pytest.mark.parametrize("contenido", [
        pytest.param(b'{"a": 1}', id="diccionario"),
        pytest.param(b'"cadena"', id="cadena"),
        pytest.param(b"7", id="numero"),
    ])
    def test_json_valido_con_forma_equivocada_deja_el_fantasma_vacio(
        self, tmp_path, caplog, contenido: bytes
    ) -> None:
        """Antes se guardaba tal cual y reventaba mucho después, en `get_frame`."""
        raro = tmp_path / "ghost.json"
        raro.write_bytes(contenido)
        fantasma = GhostData()

        with caplog.at_level(logging.WARNING):
            fantasma.load(raro)

        assert fantasma.frame_count == 0
        assert fantasma.get_frame(0) is None
        assert any("ilegible" in r.getMessage() for r in caplog.records)

    def test_sin_fichero_no_hay_aviso(self, tmp_path, caplog) -> None:
        with caplog.at_level(logging.WARNING):
            GhostData().load(tmp_path / "no_existe.json")

        assert not [r for r in caplog.records if r.levelno >= logging.WARNING]

    def test_una_grabacion_correcta_sigue_cargando(self, tmp_path) -> None:
        fantasma = GhostData()
        fantasma._frames = [{"x": 1.0, "y": 2.0}, {"x": 3.0, "y": 4.0}]
        destino = tmp_path / "ghost.json"
        fantasma.save(destino)

        leido = GhostData()
        leido.load(destino)

        assert leido.frame_count == 2
        assert leido.get_frame(1) == {"x": 3.0, "y": 4.0}
