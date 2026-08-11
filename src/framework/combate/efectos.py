"""
Module: efectos
System: framework.combate
Academic Unit: N/A

AUD-388 — efectos temporales. Cierra GAP-044.

El hueco
========
Los efectos temporales existían sueltos, cada uno con su temporizador a mano
dentro de `PlayerStateData`: `damage_mult`, `invincibility_timer`,
`flash_timer`. Nada los agrupaba, así que no se podía envenenar a un enemigo,
ni ralentizar a nadie, ni escribir un potenciador sin añadir **otro** campo y
**otro** temporizador al jugador.

Cuatro cosas modificables, y por qué esas
=========================================
`dano_infligido`, `dano_recibido`, `velocidad` y `por_segundo`. Las eligió el
dueño, y cubren lo que un plataformas necesita sin la maquinaria de un RPG:
pegar más, aguantar más, moverse distinto y perder vida con el tiempo.

Los factores **multiplican** y no suman, por el mismo motivo que las
resistencias de AUD-387: dos penalizaciones multiplicadas nunca dan un valor
negativo, y dos restadas sí. `0.65 × 0.8` es lento; `-0.35 - 0.2` acabaría
haciendo andar al jugador hacia atrás.

Reaplicar refresca, no acumula
------------------------------
Dos charcas de veneno no envenenan el doble: renuevan el reloj. Acumular sin
tope es como se acaba con un jugador que cruza una sala y sale con veinte capas
de veneno. Es la regla más simple que se comporta bien, y es el modelo que el
dueño eligió.

Lo que este módulo NO hace
--------------------------
No conoce entidades ni el ECS: recibe un componente `Efectos` y devuelve
números. El que aplica el daño por segundo y descuenta las duraciones es
`sistema_efectos`, en `ecs/systems.py`, que es donde vive lo que corre por
fotograma.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_FICHERO = Path(__file__).resolve().parents[3] / "data" / "effects.json"

#: Las cuatro estadísticas que un efecto puede tocar. Es un conjunto cerrado a
#: propósito: un efecto que declare otra cosa es una errata del catálogo, y
#: dejarla pasar produciría un efecto que no hace nada y que nadie encuentra.
MODIFICABLES: frozenset[str] = frozenset({
    "dano_infligido", "dano_recibido", "velocidad", "por_segundo",
})


def _cargar() -> dict[str, dict[str, Any]]:
    """Lee el catálogo. Si falla, el motor se queda sin efectos y sigue.

    Un catálogo ilegible no puede impedir arrancar: sin efectos, el juego es el
    de antes de AUD-388. Misma decisión que en `dano.py` y que en el cargador
    de mapas.
    """
    try:
        datos = json.loads(_FICHERO.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        logger.exception("effects.json ilegible; el motor se queda sin efectos")
        return {}

    salida: dict[str, dict[str, Any]] = {}
    for ficha in datos.get("efectos", []):
        if not isinstance(ficha, dict) or not ficha.get("id"):
            continue
        if ficha.get("modifica") not in MODIFICABLES:
            logger.error(
                "effects.json: «%s» modifica %r, que no es una estadística "
                "válida (%s); se ignora",
                ficha.get("id"), ficha.get("modifica"), ", ".join(sorted(MODIFICABLES)),
            )
            continue
        salida[str(ficha["id"])] = ficha
    return salida


#: El catálogo, por id. Se lee una vez al importar.
CATALOGO: dict[str, dict[str, Any]] = _cargar()


@dataclass(slots=True)
class EfectoActivo:
    """Un efecto puesto sobre alguien, con lo que le queda."""

    id: str
    restante: float


def existe(nombre: object) -> bool:
    return isinstance(nombre, str) and nombre in CATALOGO


def aplicar(componente: Any, nombre: str, duracion: float | None = None) -> None:
    """Pone un efecto, o refresca el que ya estuviera.

    `duracion` en segundos; sin ella se usa la del catálogo, que es lo que
    quiere quien aplica un efecto sin tener una opinión.

    Un efecto desconocido se ignora con un aviso: viene de un dato —de Tiled o
    de un JSON— y un nombre mal escrito no puede tumbar la partida.
    """
    if not existe(nombre):
        logger.warning(
            "efecto «%s» desconocido; se ignora. Válidos: %s",
            nombre, ", ".join(sorted(CATALOGO)),
        )
        return
    segundos = float(
        duracion if duracion is not None
        else CATALOGO[nombre].get("duracion", 1.0)
    )
    for activo in componente.activos:
        if activo.id == nombre:
            # Refrescar y no acumular: ver el docstring del módulo.
            activo.restante = max(activo.restante, segundos)
            return
    componente.activos.append(EfectoActivo(id=str(nombre), restante=segundos))


def modificador(componente: Any, que: str) -> float:
    """El multiplicador acumulado para esa estadística. 1,0 si no hay nada.

    Se multiplican entre sí los factores de todos los efectos activos que
    tocan `que`. Devolver 1,0 cuando no hay efectos es lo que permite que el
    llamante multiplique siempre, sin una rama `if hay_efectos`.
    """
    total = 1.0
    for activo in getattr(componente, "activos", ()):
        ficha = CATALOGO.get(activo.id)
        if ficha is None or ficha.get("modifica") != que:
            continue
        total *= float(ficha.get("factor", 1.0))
    return total


def dano_por_segundo(componente: Any) -> float:
    """Vida que se pierde por segundo por todos los efectos continuos."""
    total = 0.0
    for activo in getattr(componente, "activos", ()):
        ficha = CATALOGO.get(activo.id)
        if ficha is None or ficha.get("modifica") != "por_segundo":
            continue
        total += float(ficha.get("por_segundo", 0.0))
    return total
