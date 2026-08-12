"""AUD-430 — ocho propiedades del motor que ningún documento mencionaba.

El defecto
==========
Al traducir `06_TMX_SPEC.md` se contaron sus propiedades de mapa contra las que
`StageLoader` lee de verdad: el documento citaba **23** y el motor lee **39**.
Buscando esas dieciséis en los otros dos documentos de referencia aparecieron
**ocho que no estaban en ninguno**:

    cielo · god_rays · habilidades_libres
    water_speed · water_amplitude · water_frequency · water_alpha · water_tint

Ocho características construidas, probadas y **imposibles de descubrir**. Los
cinco mandos del agua existen desde AUD-240 con sus rangos medidos; `cielo` se
había añadido ese mismo día (AUD-426) y su autor —yo— no la documentó.

Es el modo de fallo de este repositorio aplicado a la documentación. `AUD-378`
lo cerró para la **cobertura** —«una característica que el motor lee del TMX y
ningún mapa declara es una característica que no existe»— y faltaba la otra
mitad: una que ningún documento nombra tampoco existe, porque el estudiante no
la encuentra abriendo un mapa en Tiled si no sabe que puede escribirla.

Por qué tres documentos y no uno
================================
No se exige que cada propiedad esté en **todos**, sino en **alguno**. Los tres
tienen público distinto —`60` es el manual del diseñador, `06` el contrato del
formato, `STAGE_CREATION` la guía de primeros pasos— y obligar a las tres
listas a coincidir crearía justo el problema que `AUD-392` desmontó: tres copias
de un inventario que se desincronizan.
"""
from __future__ import annotations

import pathlib

import pytest

RAIZ = pathlib.Path(__file__).resolve().parent.parent

#: Los documentos donde un estudiante busca «qué puedo poner en el mapa».
REFERENCIAS: tuple[str, ...] = (
    "60_GUIA_COMPLETA_DEL_MOTOR.md",
    "06_TMX_SPEC.md",
    "STAGE_CREATION.md",
)

#: Propiedades que el motor lee y que **no** hace falta documentar, con su
#: motivo. Está vacío, y conviene que siga estándolo: llenarlo es la forma
#: elegante de dejar de documentar.
#:
#: El primer intento metió aquí `camera` y `view` —las grafías inglesas de
#: `camara` y `vista`—, y `test_las_exenciones_siguen_siendo_ciertas` lo cazó
#: en la primera ejecución: **no están** en `PROPIEDADES_DEL_MOTOR`. AUD-378 ya
#: las había separado en `ALIAS_DE_PROPIEDAD` justo para que no se contaran
#: como características aparte, así que la exención sobraba.
NO_SE_DOCUMENTAN: dict[str, str] = {}


def _texto_de_referencias() -> dict[str, str]:
    return {n: (RAIZ / "docs" / n).read_text(encoding="utf-8") for n in REFERENCIAS}


def _propiedades_del_motor() -> list[str]:
    from scripts.check_tmx_coverage import PROPIEDADES_DEL_MOTOR

    return sorted(PROPIEDADES_DEL_MOTOR)


def test_las_referencias_existen() -> None:
    """Si alguna se renombra, el resto de pruebas pasarían mirando al vacío."""
    for nombre in REFERENCIAS:
        assert (RAIZ / "docs" / nombre).is_file(), f"no existe docs/{nombre}"


@pytest.mark.parametrize("propiedad", _propiedades_del_motor())
def test_toda_propiedad_del_motor_esta_documentada(propiedad: str) -> None:
    """Cada propiedad que `StageLoader` lee aparece en algún documento.

    Se busca con comillas invertidas —`` `bloom` ``— y no suelta: «zone» y
    «season» son palabras que aparecen en prosa por casualidad, y buscarlas sin
    marcar daría por documentado lo que sólo está mencionado de pasada.
    """
    if propiedad in NO_SE_DOCUMENTAN:
        pytest.skip(NO_SE_DOCUMENTAN[propiedad])

    textos = _texto_de_referencias()
    donde = [n for n, t in textos.items() if f"`{propiedad}`" in t]
    assert donde, (
        f"el motor lee la propiedad de mapa `{propiedad}` y no la menciona "
        f"ninguno de {list(REFERENCIAS)}. Una característica que ningún "
        "documento nombra no la puede descubrir un estudiante: documéntala "
        "donde corresponda a su público, o quítala del cargador"
    )


def test_las_exenciones_siguen_siendo_ciertas() -> None:
    """Una exención sobre algo que el motor ya no lee es una excusa vieja."""
    del_motor = set(_propiedades_del_motor())
    muertas = sorted(set(NO_SE_DOCUMENTAN) - del_motor)
    assert not muertas, (
        f"estas exenciones ya no corresponden a nada que el motor lea: "
        f"{muertas}. Retíralas de NO_SE_DOCUMENTAN"
    )
