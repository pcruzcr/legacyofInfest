"""
La versión del producto es una sola y dice la verdad.

AUD-105
=======
`pyproject.toml` declaraba **2.0.0** mientras el producto entregable era de la
línea **1.x**. La 2.0.0 es la versión *futura*, la que describe
`docs/50_IMPROVEMENT_ROADMAP.md`.

Lo más probable es que alguien copiara la versión de un documento: cada
documento del proyecto lleva su propia cabecera `Version:` y son
independientes de la del producto —el roadmap va por la `4.0.0`, la auditoría
de implementación por la `2.0.0`—. Es una confusión fácil y con consecuencias
concretas: un estudiante que abre una incidencia diciendo «me pasa en la
2.0.0» está describiendo una versión que no existe, y nadie puede
reproducirla.

Qué se vigila
-------------
Que **haya un solo número** y que las tres fuentes que lo publican coincidan:
`pyproject.toml`, lo que expone el paquete, y la entrada más reciente del
CHANGELOG. Nada más: no se comprueba que exista una etiqueta de git, porque
etiquetar es un acto deliberado del profesor y no algo que deba bloquear la
suite.
"""
from __future__ import annotations

import pathlib
import re

import pytest

RAIZ = pathlib.Path(__file__).resolve().parent.parent
PYPROJECT = RAIZ / "pyproject.toml"
CHANGELOG = RAIZ / "CHANGELOG.md"

#: Versión mayor de la línea que se está entregando. La 2.x es futura y está
#: descrita en el roadmap; que este número suba solo debe ser una decisión
#: consciente, no el resultado de copiar la cabecera de un documento.
LINEA_ACTUAL = 1


def _version_de_pyproject() -> str:
    texto = PYPROJECT.read_text(encoding="utf-8")
    seccion = texto.split("[project]", 1)[-1].split("\n[", 1)[0]
    encontrado = re.search(r'^version\s*=\s*"([^"]+)"', seccion, re.M)
    assert encontrado, "pyproject.toml no declara ninguna versión en [project]"
    return encontrado.group(1)


def _versiones_del_changelog() -> list[str]:
    """Las versiones del CHANGELOG, de la más reciente a la más antigua."""
    return re.findall(r"^## \[([0-9]+\.[0-9]+\.[0-9]+)\]", CHANGELOG.read_text(encoding="utf-8"), re.M)


def test_pyproject_declara_una_version_semantica() -> None:
    assert re.fullmatch(r"\d+\.\d+\.\d+", _version_de_pyproject()), (
        f"versión no semántica: {_version_de_pyproject()!r}"
    )


def test_el_paquete_expone_la_misma_version_que_pyproject() -> None:
    """`src.__version__` la lee; no la repite.

    Si alguien la escribiera a mano, habría dos números y acabarían diciendo
    cosas distintas, que es exactamente lo que originó AUD-105.
    """
    import src

    assert src.__version__ == _version_de_pyproject()
    assert src.version() == src.__version__


def test_el_changelog_tiene_una_entrada_para_la_version_actual() -> None:
    """Entregar una versión sin entrada deja al profesor sin saber qué cambió."""
    actual = _version_de_pyproject()
    versiones = _versiones_del_changelog()
    assert versiones, "el CHANGELOG no tiene ninguna entrada de versión"
    assert versiones[0] == actual, (
        f"pyproject declara {actual} y la entrada más reciente del CHANGELOG "
        f"es {versiones[0]}. Añade la entrada antes de publicar."
    )


def test_seguimos_en_la_linea_1_x() -> None:
    """La 2.0.0 es la versión futura del roadmap, no la que se entrega.

    Si algún día se sube de verdad a la 2.x, hay que cambiar `LINEA_ACTUAL`
    **a mano**: es una decisión, y tiene que costar un cambio deliberado.
    """
    mayor = int(_version_de_pyproject().split(".", 1)[0])
    assert mayor == LINEA_ACTUAL, (
        f"la versión declarada es {mayor}.x y este proyecto entrega la "
        f"{LINEA_ACTUAL}.x. Si el salto es intencionado, actualiza "
        f"LINEA_ACTUAL en esta prueba y explica el porqué en el CHANGELOG."
    )


def test_las_versiones_del_changelog_van_de_mayor_a_menor() -> None:
    """Un CHANGELOG desordenado hace dudar de cuál es la última."""
    versiones = [tuple(int(p) for p in v.split(".")) for v in _versiones_del_changelog()]
    assert versiones == sorted(versiones, reverse=True), (
        f"el CHANGELOG no está en orden descendente: {_versiones_del_changelog()}"
    )


@pytest.mark.parametrize("documento", ["50_IMPROVEMENT_ROADMAP.md", "51_IMPLEMENTATION_AUDIT.md"])
def test_la_version_de_un_documento_no_es_la_del_producto(documento: str) -> None:
    """La distinción que se perdió, dejada por escrito.

    Estos documentos llevan su propia cabecera `Version:` y **deben** poder
    diferir de la del producto. La prueba no exige que difieran; exige que el
    fichero siga teniendo su propia cabecera, para que quien lo lea entienda
    que ese número es del documento y no del motor.
    """
    ruta = RAIZ / "docs" / documento
    if not ruta.is_file():
        pytest.skip(f"{documento} ya no existe")
    texto = ruta.read_text(encoding="utf-8")
    assert re.search(r"\*\*Version:\*\*\s*[0-9]+\.[0-9]+\.[0-9]+", texto), (
        f"{documento} ha perdido su cabecera de versión de documento; sin ella "
        f"se confunde con la versión del producto, que es como se declaró un "
        f"2.0.0 que no existía"
    )
