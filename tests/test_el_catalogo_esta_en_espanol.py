"""AUD-440 — el catálogo de objetos estaba entero en inglés.

Qué fallaba
-----------
La tienda, el inventario y las notificaciones de recogida están en español y
pasan por `_()`. Los **nombres y descripciones de los 17 objetos** no: vivían
escritos a mano en `inventory.py` como "Heart Vessel", "Swift Boots" o
"Boss drop: deflect attacks". El resultado es una tienda con los rótulos en
español y la mercancía en inglés.

Rompe la invariante 5 de `CLAUDE.md` —«todo en español, sin excepciones»— y
`scripts/check_translations.py` pasaba en verde porque no mira aquí: comprueba
los ficheros de `locale/`, y este catálogo no está en ninguno.

Qué comprueba esto y qué no
---------------------------
Detectar «esto es inglés» de forma general no tiene solución barata ni fiable.
Lo que sí se puede afirmar sin ambigüedad es que ciertas palabras **no
aparecen en español**: `damage`, `speed`, `max HP`, `Boss drop`. Un guardián
por lista negra no demuestra que el texto esté bien escrito, pero sí detecta
el caso que de verdad ocurre — alguien añade un objeto copiando el estilo del
de al lado— que es para lo que sirve.

Los `id` quedan fuera a propósito: son la clave con la que las partidas
guardadas referencian cada objeto, y traducirlos rompería todos los guardados
existentes.
"""
from __future__ import annotations

import re

import pytest

from src.engine.core.inventory import _ITEM_DEFS

#: Palabras que sólo aparecen si el texto se quedó en inglés. Minúsculas; se
#: comparan como palabra suelta para no cazar «impulso» dentro de otra cosa.
_DELATORES = (
    "damage", "speed", "max hp", "boss drop", "cloak", "hood", "boots",
    "jump", "dash", "parry", "coin", "currency", "faster", "resists",
    "clearer", "the shop", "mid-air", "forward", "deflect", "attacks",
    "light", "warm", "venom", "jungle",
)


def _delatores_en(texto: str) -> list[str]:
    bajo = texto.lower()
    return [p for p in _DELATORES if re.search(rf"\b{re.escape(p)}\b", bajo)]


@pytest.mark.parametrize("item_id", sorted(_ITEM_DEFS))
def test_el_nombre_del_objeto_esta_en_espanol(item_id: str) -> None:
    definicion = _ITEM_DEFS[item_id]
    encontrados = _delatores_en(definicion.name)
    assert not encontrados, (
        f"el objeto {item_id!r} se llama {definicion.name!r}, en inglés "
        f"({', '.join(encontrados)}). Lo lee el jugador en la tienda y en el "
        f"inventario."
    )


@pytest.mark.parametrize("item_id", sorted(_ITEM_DEFS))
def test_la_descripcion_del_objeto_esta_en_espanol(item_id: str) -> None:
    definicion = _ITEM_DEFS[item_id]
    encontrados = _delatores_en(definicion.description)
    assert not encontrados, (
        f"la descripción de {item_id!r} está en inglés ({', '.join(encontrados)}): "
        f"{definicion.description!r}"
    )


def test_los_identificadores_no_se_traducen() -> None:
    """El control que impide arreglar esto rompiendo las partidas guardadas.

    Los `id` son la clave con la que un guardado referencia lo que llevas
    encima. Traducirlos dejaría el inventario de todo el mundo vacío en la
    siguiente carga, porque `restaurar()` descarta los que no reconoce.
    """
    for item_id, definicion in _ITEM_DEFS.items():
        assert definicion.id == item_id
        assert re.fullmatch(r"[a-z0-9_]+", item_id), (
            f"{item_id!r} dejó de ser un identificador estable"
        )


def test_el_catalogo_no_se_ha_quedado_vacio() -> None:
    """Sin esto, borrar el catálogo haría pasar todo lo de arriba.

    Dieciséis: seis mejoras permanentes, la moneda, seis prendas equipables y
    tres habilidades que sueltan los jefes.
    """
    assert len(_ITEM_DEFS) >= 16
