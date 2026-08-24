"""AUD-391 — el validador de TMX imprimía «FAILED» y devolvía 0 en CI.

El defecto
==========
`scripts/validate_tmx.py --ci` es uno de los siete validadores que CI ejecuta
(`CLAUDE.md` §2). Terminaba así::

    if args.ci:
        return 1 if _errors else 0

`_errors` es una lista de módulo, y `validate_tmx()` la **vacía al entrar a cada
fichero**. Al acabar el bucle no contiene los errores de la ejecución: contiene
los del *último mapa validado*. Con los mapas recorridos en orden alfabético,
un fallo en `boss_paburu` y un `stage_mecanicas` limpio daban esto::

      1/2 FAILED
    === CODIGO DE SALIDA CON --ci: 0 ===

El guion diagnosticaba bien, lo imprimía bien, y le decía a CI que todo estaba
en orden. Un gate que no puede ponerse rojo no es un gate — es el mismo patrón
que AUD-378, donde el detector de cosas no-leídas era él mismo cosa no-leída.

Por qué se mira el recuento de ficheros y no la lista global
============================================================
`failed` ya cuenta bien, porque `validate_tmx()` sólo devuelve `False` cuando
hubo errores —los avisos nunca suspenden a nadie—. Esa equivalencia es real
pero sutil, y apoyarse en ella es lo que produjo el defecto. El arreglo lleva
su propio contador acumulado para que la condición de CI no dependa de leer
tres funciones y deducir que coinciden.
"""
from __future__ import annotations

import shutil
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

_RAIZ = Path(__file__).resolve().parent.parent


@pytest.fixture
def par_de_mapas(tmp_path: Path) -> Path:
    """Un mapa roto que ordena **antes** que uno sano.

    El orden importa y es la esencia del defecto: `main()` recorre
    `sorted(tmx_files)`, así que el sano se valida el último y deja la lista
    global limpia. Invertir los nombres haría pasar la prueba con el código
    defectuoso.
    """
    origen = _RAIZ / "assets" / "maps" / "stage0" / "stage0.tmx"
    shutil.copy(origen, tmp_path / "z_sano.tmx")

    arbol = ET.parse(origen)
    props = arbol.getroot().find("properties")
    assert props is not None
    for p in list(props.findall("property")):
        if p.get("name") == "stage_id":
            props.remove(p)
    arbol.write(tmp_path / "a_roto.tmx", encoding="utf-8", xml_declaration=True)
    return tmp_path


def _correr(monkeypatch: pytest.MonkeyPatch, *argumentos: str) -> int:
    from scripts.validate_tmx import main

    monkeypatch.setattr(sys, "argv", ["validate_tmx.py", *argumentos])
    return main()


def test_ci_falla_cuando_el_mapa_roto_no_es_el_ultimo(
    monkeypatch: pytest.MonkeyPatch, par_de_mapas: Path
) -> None:
    """El defecto exacto: error en el primero, sano el último, CI en verde."""
    codigo = _correr(
        monkeypatch, "--ci",
        str(par_de_mapas / "a_roto.tmx"),
        str(par_de_mapas / "z_sano.tmx"),
    )
    assert codigo == 1, (
        "validate_tmx.py --ci devolvió 0 con un mapa que le falta 'stage_id'. "
        "El gate de TMX de CI sólo estaba mirando el último fichero validado."
    )


def test_ci_sigue_pasando_cuando_todos_los_mapas_estan_sanos(
    monkeypatch: pytest.MonkeyPatch, par_de_mapas: Path
) -> None:
    """El otro lado: el arreglo no puede volver el gate rojo permanente.

    Sin esto, cambiar el `return` por un `1` fijo pasaría la prueba de arriba.
    """
    codigo = _correr(monkeypatch, "--ci", str(par_de_mapas / "z_sano.tmx"))
    assert codigo == 0


def test_los_avisos_por_si_solos_no_suspenden_en_ci(
    monkeypatch: pytest.MonkeyPatch, par_de_mapas: Path
) -> None:
    """`--ci` significa «sólo errores», y eso tiene que seguir siendo cierto.

    El mapa copiado a un directorio temporal deja de encontrar la imagen de su
    tileset —ruta relativa— y por eso avisa siempre. Sirve de comprobación de
    que el acumulador nuevo cuenta errores y no avisos.
    """
    from scripts import validate_tmx as v

    codigo = _correr(monkeypatch, "--ci", str(par_de_mapas / "z_sano.tmx"))
    assert v._warnings, "se esperaba al menos un aviso del tileset no hallado"
    assert codigo == 0
