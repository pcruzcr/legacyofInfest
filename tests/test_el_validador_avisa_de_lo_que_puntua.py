"""AUD-416 — el validador aprobaba lo que el calificador penaliza.

El defecto
==========
Un estudiante tiene dos herramientas y le dicen cosas distintas del mismo
fichero:

* `scripts/validate_tmx.py` — la que corre mientras construye el nivel.
* `scripts/grade_stage.py` — la que le pone la nota.

Y no estaban de acuerdo sobre qué propiedades hacen falta::

    validate_tmx.REQUIRED_MAP_PROPS  = ["stage_id", "stage_name", "bgm_track"]
    grade_stage.REQUIRED_GRADE_PROPS = ["author", "stage_id", "stage_name"]

`author` **puntúa en la rúbrica** y el validador no la pedía. Resultado medido
sobre la plantilla que copia todo el mundo: `validate_tmx` la da por `[OK]`, sin
un solo aviso, y `grade_stage` le quita 3 de los 10 puntos de metadata. El
estudiante comprueba su mapa, lo ve verde, lo entrega y pierde puntos por una
propiedad que ninguna herramienta le nombró.

Es AUD-058 otra vez, girado: aquella vez el validador aprobaba lo que **el
motor** rechazaba —«un validador que aprueba lo que el motor rechaza es peor
que no tener validador: enseña a no fiarse de él»—. Aquí aprueba lo que
**la rúbrica** penaliza, que para quien está siendo calificado es lo mismo.

Por qué avisa y no suspende
===========================
`author` no impide cargar el mapa: el motor no la lee, es metadato. Convertirla
en error rechazaría mapas que se juegan perfectamente y repetiría AUD-106 —el
validador reprobando a quien usa bien el framework—. Lo que hacía falta no era
prohibir, era **decírselo**.
"""
from __future__ import annotations

import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

_RAIZ = Path(__file__).resolve().parent.parent
STAGE0 = _RAIZ / "assets" / "maps" / "stage0" / "stage0.tmx"


def _mapa_sin(tmp_path: Path, propiedad: str) -> Path:
    destino = tmp_path / "mapa.tmx"
    shutil.copy(STAGE0, destino)
    arbol = ET.parse(destino)
    props = arbol.getroot().find("properties")
    assert props is not None
    for p in list(props.findall("property")):
        if p.get("name") == propiedad:
            props.remove(p)
    arbol.write(destino, encoding="utf-8", xml_declaration=True)
    return destino


def _validar(ruta: Path) -> tuple[list[str], list[str]]:
    from scripts import validate_tmx as v

    v.validate_tmx(ruta)
    return list(v._errors), list(v._warnings)


class TestLasDosHerramientasCoinciden:
    def test_lo_que_puntua_la_rubrica_lo_avisa_el_validador(
        self, tmp_path: Path
    ) -> None:
        """El defecto: `author` puntuaba y el validador callaba."""
        _errores, avisos = _validar(_mapa_sin(tmp_path, "author"))
        assert [a for a in avisos if "author" in a], (
            "un mapa sin 'author' pasa el validador en silencio y luego pierde "
            "3 de 10 puntos de metadata en grade_stage.py"
        )

    def test_el_aviso_explica_que_es_de_la_rubrica(self, tmp_path: Path) -> None:
        """Sin decir de dónde sale, el estudiante no sabe si puede ignorarlo."""
        _errores, avisos = _validar(_mapa_sin(tmp_path, "author"))
        propios = [a for a in avisos if "author" in a]
        assert any("nota" in a or "rúbrica" in a or "grade_stage" in a
                   for a in propios), f"el aviso no dice de dónde sale: {propios}"

    def test_no_suspende(self, tmp_path: Path) -> None:
        """`author` no impide cargar el mapa: el motor ni la lee."""
        errores, _avisos = _validar(_mapa_sin(tmp_path, "author"))
        assert not [e for e in errores if "author" in e]

    @pytest.mark.parametrize("propiedad", ["stage_id", "stage_name"])
    def test_las_compartidas_siguen_siendo_error(
        self, tmp_path: Path, propiedad: str
    ) -> None:
        """Las que ya eran obligatorias no se ablandan de paso.

        Están en las dos listas, y para el cargador son imprescindibles: sin
        `stage_id` el escenario no se puede identificar.
        """
        errores, _avisos = _validar(_mapa_sin(tmp_path, propiedad))
        assert [e for e in errores if propiedad in e]


def test_el_validador_lee_la_lista_de_la_rubrica_y_no_una_copia() -> None:
    """El trinquete: una segunda lista a mano se desincroniza igual que la
    primera.

    Es la misma lección de AUD-392, donde `KNOWN_TMX_PROPERTIES` llevaba
    declarada y sin usar el tiempo suficiente para quedarse en 7 propiedades
    mientras el cargador leía 40. Si mañana la rúbrica añade una propiedad
    puntuable, el validador tiene que enterarse solo.
    """
    from scripts.grade_stage import REQUIRED_GRADE_PROPS
    from scripts.validate_tmx import _propiedades_que_puntuan

    assert set(_propiedades_que_puntuan()) == set(REQUIRED_GRADE_PROPS)


def test_un_mapa_completo_no_produce_aviso_de_metadatos(tmp_path: Path) -> None:
    """El otro lado: `stage0` las declara todas y no debe avisar de nada.

    Sin esto, «avisa siempre» pasaría las pruebas de arriba.
    """
    destino = tmp_path / "intacto.tmx"
    shutil.copy(STAGE0, destino)
    _errores, avisos = _validar(destino)
    assert not [a for a in avisos if "la nota" in a]
