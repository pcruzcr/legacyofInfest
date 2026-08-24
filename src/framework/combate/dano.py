"""
Module: dano
System: framework.combate
Academic Unit: N/A

AUD-387 — los canales de daño. Cierra GAP-043.

El hueco
========
`CollisionSystem._calculate_damage` devolvía un escalar y `EnemyBase.apply_hit`
lo restaba de la vida. No había forma de que un enemigo fuera **débil a una
cosa y resistente a otra**, que es lo que separa un bestiario de una lista de
sacos de vida con distinta cantidad.

Cómo está montado, y por qué así
================================
El catálogo vive en `data/damage_types.json` y las resistencias se declaran en
Tiled (`resistencias="veneno:0.5, fuego:2"`). Es la misma forma que el resto
del motor —el bestiario, los logros, las mecánicas de la fase 5— y por el mismo
motivo: un estudiante añade un canal o hace resistente a su enemigo **sin
escribir Python**, que es la única manera en que una característica se adopta.

Los tres canales de salida salen del lore, no de una lista genérica: `veneno`
aparece ocho veces en `65_EL_LORE_EXTENSO.md` y `fuego` tres; hielo y
electricidad, ninguna. Un canal sin contenido detrás es una característica que
nadie usa, que es justo el problema que GAP-052 vino a cerrar.

Lo que este módulo NO decide
----------------------------
No aplica el daño ni conoce entidades: recibe una cantidad, un canal y un
diccionario de resistencias, y devuelve una cantidad. Se puede probar sin
pygame y sin un enemigo delante, que es lo que lo hace utilizable como
contrato.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_FICHERO = Path(__file__).resolve().parents[3] / "data" / "damage_types.json"


def _cargar() -> tuple[dict[str, dict[str, Any]], str]:
    """Lee el catálogo. Si falla, deja el motor con el canal físico.

    Un catálogo ilegible no puede impedir que el juego arranque: sin canales,
    todo el daño es físico y el juego es el de antes de AUD-387. Es la misma
    decisión que toma el cargador de mapas con una propiedad mal escrita.
    """
    minimo = ({"fisico": {"id": "fisico", "nombre": "Fisico"}}, "fisico")
    try:
        datos = json.loads(_FICHERO.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        logger.exception("damage_types.json ilegible; todo el daño será físico")
        return minimo

    canales = {
        c["id"]: c for c in datos.get("canales", [])
        if isinstance(c, dict) and c.get("id")
    }
    if not canales:
        logger.error("damage_types.json sin canales; todo el daño será físico")
        return minimo

    por_defecto = str(datos.get("por_defecto", "") or "")
    if por_defecto not in canales:
        # Elegir uno cualquiera sería peor: el canal por defecto es el que
        # reciben los 32 llamantes que no dicen nada, así que un catálogo que
        # no lo declara bien tiene que ser ruidoso.
        logger.error(
            "damage_types.json: «por_defecto» = %r no está en los canales %s; "
            "se usa el primero", por_defecto, sorted(canales),
        )
        por_defecto = next(iter(canales))
    return canales, por_defecto


#: El catálogo, por id. Se lee una vez al importar: es un fichero de datos que
#: no cambia en caliente, y releerlo por golpe sería absurdo.
CANALES: dict[str, dict[str, Any]]
#: El canal de quien no dice nada. Ver `apply_hit`: son 32 llamantes, 26 de
#: ellos en entregas de estudiantes.
CANAL_POR_DEFECTO: str
CANALES, CANAL_POR_DEFECTO = _cargar()


def canal_valido(nombre: object) -> bool:
    """¿Existe ese canal en el catálogo?"""
    return isinstance(nombre, str) and nombre in CANALES


def normalizar(nombre: object) -> str:
    """El canal pedido, o el por defecto si no existe.

    Un canal mal escrito en Tiled produce daño físico y un aviso, no un error
    de carga: el estudiante necesita ver su nivel para darse cuenta de que
    escribió `plasma` donde quería `veneno`.
    """
    if canal_valido(nombre):
        return str(nombre)
    if nombre not in (None, ""):
        logger.warning(
            "canal de daño %r desconocido; se aplica %s. Válidos: %s",
            nombre, CANAL_POR_DEFECTO, ", ".join(sorted(CANALES)),
        )
    return CANAL_POR_DEFECTO


def mitigar(cantidad: float, canal: object,
            resistencias: dict[str, float] | None) -> float:
    """El daño que entra de verdad, tras la resistencia del que lo recibe.

    El factor es un **multiplicador**, no un porcentaje restado, porque así el
    mismo número expresa las dos cosas que interesan: `0.5` es resistencia,
    `2.0` es debilidad y `0.0` es inmunidad. Un bestiario se vuelve interesante
    por las debilidades, no por las resistencias.

    Se recorta a cero por abajo: un factor negativo escrito en Tiled
    convertiría un golpe en una cura, y un dato hostil debe producir algo raro
    pero jugable, no una mecánica invertida.
    """
    if not resistencias:
        return float(cantidad)
    factor = resistencias.get(normalizar(canal))
    if factor is None:
        return float(cantidad)
    return max(0.0, float(cantidad) * max(0.0, float(factor)))
