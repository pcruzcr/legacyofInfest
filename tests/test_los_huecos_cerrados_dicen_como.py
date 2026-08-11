"""AUD-421 — un hueco tachado sin resolución escrita no está cerrado.

El defecto
==========
La invariante 4 de `CLAUDE.md` dice:

    `KNOWN_GAPS.md` no se borra nunca. Una entrada resuelta se marca
    `~~[GAP-NNN] ...~~ *(Resuelto)*` y se le añade `**Resolution:**`.
    Formato en `docs/23_DATA_SCHEMAS.md` §8.

Dos cosas fallaban:

1. **No había nada comprobándolo.** `GAP-034` llegó a estar meses tachado sin
   resolución escrita, y sólo se descubrió a mano (AUD-412). Hoy le pasa lo
   mismo a `GAP-024`, que sí tiene la decisión razonada pero bajo el
   encabezado «Decisión del profesor» en vez de la etiqueta que la invariante
   pide, así que ningún `grep` lo encuentra.
2. **La sección a la que remite no lo documenta.** `docs/23_DATA_SCHEMAS.md`
   §8 define el formato de **alta** —`File`, `Phase`, `Reason`,
   `Resolution plan`— y no dice nada del cierre. La invariante mandaba a un
   sitio que no contenía lo prometido.

Por qué importa más de lo que parece
====================================
`KNOWN_GAPS.md` es la respuesta a «¿qué falta?», y se consulta con `grep`. Un
hueco tachado sin resolución legible cuenta como cerrado en el recuento y no
dice **por qué**, así que la siguiente persona que lo mire tiene que reabrir la
investigación entera para averiguar si se arregló, se midió y se descartó, o se
decidió no hacerlo. Es la diferencia entre cerrar y archivar.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

_RAIZ = Path(__file__).resolve().parent.parent
GAPS = _RAIZ / "KNOWN_GAPS.md"

#: Las formas que valen como resolución escrita.
#:
#: `Resolution` es la canónica de la invariante. `Decisión` se acepta porque un
#: hueco puede cerrarse **por decisión del dueño** sin que se toque una línea
#: de código —`GAP-024` y `GAP-041` son de ese tipo— y forzar la palabra
#: «Resolution» ahí sería pedir que se llame arreglo a lo que fue un criterio.
#: Lo que no vale es no decir nada.
_MARCAS = ("**Resolution", "**Resolución", "**Decisión", "**Decision")


def _bloques() -> list[tuple[str, str]]:
    """Cada entrada de `KNOWN_GAPS.md` como `(encabezado, cuerpo)`."""
    texto = GAPS.read_text(encoding="utf-8")
    partes = re.split(r"^## ", texto, flags=re.M)[1:]
    return [(p.splitlines()[0], p) for p in partes]


def _cerrados() -> list[tuple[str, str]]:
    return [(cab, cuerpo) for cab, cuerpo in _bloques() if cab.startswith("~~[GAP-")]


def test_hay_huecos_que_comprobar() -> None:
    """Si el fichero cambia de formato, el resto de pruebas pasarían vacías."""
    assert len(_cerrados()) >= 40, (
        f"sólo se reconocieron {len(_cerrados())} huecos cerrados; el formato "
        "de KNOWN_GAPS.md ha cambiado y estas pruebas ya no miran nada"
    )


@pytest.mark.parametrize("cabecera,cuerpo", _cerrados(),
                         ids=lambda v: v[:22] if isinstance(v, str) else "")
def test_todo_hueco_cerrado_dice_como_se_cerro(cabecera: str, cuerpo: str) -> None:
    """La invariante 4, comprobada.

    `GAP-034` estuvo meses tachado sin resolución y hubo que encontrarlo a
    mano. Esto lo pone en rojo el mismo día.
    """
    assert any(m in cuerpo for m in _MARCAS), (
        f"{cabecera[:70]} está tachado como resuelto y no dice cómo. "
        f"La invariante 4 de CLAUDE.md pide `**Resolution:**` (o `**Decisión`, "
        f"si se cerró por criterio del dueño). Un hueco tachado sin explicación "
        f"obliga a rehacer la investigación entera para saber si se arregló, se "
        f"midió y se descartó, o se decidió no hacerlo"
    )


def test_los_abiertos_declaran_su_plan() -> None:
    """El otro lado del contrato: un hueco abierto dice cómo se resolvería.

    Es el campo `Resolution plan` que `docs/23_DATA_SCHEMAS.md` §8 exige desde
    siempre para el alta.
    """
    sin_plan = [
        cab[:60] for cab, cuerpo in _bloques()
        if not cab.startswith("~~[GAP-") and cab.startswith("[GAP-")
        and "**Resolution plan:**" not in cuerpo
    ]
    assert not sin_plan, f"huecos abiertos sin plan de resolución: {sin_plan}"


def test_la_invariante_remite_a_un_sitio_que_lo_documenta() -> None:
    """`CLAUDE.md` manda a `docs/23` §8 para el formato; §8 tiene que tenerlo.

    Remitir a una sección que no contiene lo prometido es la misma clase de
    defecto que persigue toda esta fase: una referencia que se lee como
    autoridad y no dice nada.
    """
    esquemas = (_RAIZ / "docs" / "23_DATA_SCHEMAS.md").read_text(encoding="utf-8")
    i = esquemas.find("`KNOWN_GAPS.md` Entry Schema")
    assert i > 0, "no se encontró §8 en 23_DATA_SCHEMAS.md"
    seccion = esquemas[i:i + 4000]
    assert "Resolution:" in seccion, (
        "23_DATA_SCHEMAS.md §8 documenta el alta de un hueco pero no su "
        "cierre, y la invariante 4 de CLAUDE.md remite ahí para el formato "
        "de cierre"
    )
