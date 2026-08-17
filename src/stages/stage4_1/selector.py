"""
Module: selector
System: stages.stage4_1
Description: AUD-518 — elige cuál de las variantes de 4-1 (cementerio,
acuático, aéreo) juega esta partida, una sola vez, y no vuelve a preguntar.

Por qué un módulo aparte y no una rama dentro de Stage4_1
==========================================================
`STAGE_ORDER` (`stage_registry.py`) resolvía el slot "stage4_1" a **una**
clase fija de escena, igual que los otros 25. Para que el mismo slot se
convierta en uno de tres niveles distintos sin tocar `SceneManager` ni el
resto del registro, el slot pasa a resolver a `crear_stage4_1` en vez de a
una clase — ver `_STAGE_FACTORY_MAP` en `stage_registry.py`.
`SceneManager._enter_next_stage` la llama exactamente igual que llamaría
al constructor de una clase (`next_stage_class(self._context)`), así que
no necesita saber que hay un sorteo detrás.

Persistencia — una vez por partida, no por intento
====================================================
Se sortea la primera vez que la partida llega aquí y se guarda en
`SaveData.stage4_1_variante`. Morir y reaparecer en un checkpoint de la
misma variante **no** vuelve a sortear — decisión confirmada con el dueño
vía `AskUserQuestion` (2026-08-17): un sorteo por partida, para que los
checkpoints sigan significando algo. Si el sorteo se repitiera en cada
intento, morir a mitad del nivel acuático podría reaparecer en el aéreo.

Qué variantes existen hoy
===========================
`VARIANTES_DISPONIBLES` trae `Stage4_1` (el cementerio, AUD-518) y
`Stage4_1B` (la fosa abisal, AUD-519). Falta la aérea. El mecanismo
—elegir, persistir, no volver a preguntar— se probó primero contra un
catálogo de mentira (`tests/test_selector_de_stage4_1.py`) sin depender
de que ningún escenario real existiera todavía: añadir cada variante de
verdad fue una línea en el diccionario, no un cambio de arquitectura.
"""
from __future__ import annotations

import importlib
import logging
from typing import TYPE_CHECKING

from src.engine.core import azar

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext
    from src.engine.scene.base_scene import BaseScene

logger = logging.getLogger(__name__)

#: Variante -> ruta punteada de su clase de escena.
VARIANTES_DISPONIBLES: dict[str, str] = {
    "cementerio": "src.stages.stage4_1.stage4_1.Stage4_1",
    # AUD-519 — misma travesía horizontal, sumergida: el jugador nada en
    # vez de caminar, y un pez abismal aparece y persigue sin poder tocar
    # ni ser tocado. Ver `src/stages/stage4_1b/stage4_1b.py`.
    "acuatico": "src.stages.stage4_1b.stage4_1b.Stage4_1B",
}

#: A cuál caer si una partida trae guardada una variante que ya no existe
#: en el catálogo (por ejemplo, se retiró una variante entre versiones).
#: Tiene que ser una clave real de `VARIANTES_DISPONIBLES` — lo comprueba
#: `test_la_variante_por_defecto_esta_en_el_catalogo`.
VARIANTE_POR_DEFECTO = "cementerio"


def elegir_variante(disponibles: dict[str, str] | None = None) -> str:
    """Sortea una variante entre las disponibles.

    Usa `azar.generador()` — el generador aislado del proceso, no el
    global — para no competir por estado con partículas, clima o
    decisiones de enemigo, y para que una prueba pueda fijar la semilla
    sin tocar el azar de nadie más (mismo criterio que AUD-374/375).

    `disponibles` es un parámetro y no siempre `VARIANTES_DISPONIBLES`
    para que una prueba pueda forzar un catálogo de dos o tres variantes
    de mentira sin monkeypatchear el módulo.
    """
    catalogo = VARIANTES_DISPONIBLES if disponibles is None else disponibles
    if not catalogo:
        return VARIANTE_POR_DEFECTO
    # Orden estable: un `dict` conserva el de inserción, no uno sorteable
    # por sí mismo. Sin ordenar, la misma semilla podría elegir claves
    # distintas sólo porque el diccionario se construyó en otro orden.
    claves = sorted(catalogo)
    return azar.generador().choice(claves)


def _cargar_clase(ruta: str) -> type[BaseScene]:
    modulo, _, nombre = ruta.rpartition(".")
    mod = importlib.import_module(modulo)
    return getattr(mod, nombre)  # type: ignore[no-any-return]


def _variante_persistida(context: GameContext) -> str | None:
    """La variante que ya sorteó esta partida, o `None` si no hay ninguna
    todavía (primera vez, o no hay partida activa que consultar)."""
    gestor = context.save_manager
    slot = gestor.ranura_activa or gestor.newest_slot()
    if slot is None:
        return None
    data = gestor.load(slot)
    if data is None or not data.stage4_1_variante:
        return None
    return data.stage4_1_variante


def _persistir_variante(context: GameContext, variante: str) -> None:
    gestor = context.save_manager
    if gestor.ranura_activa is None and gestor.newest_slot() is None:
        # Sin partida a la que atar el sorteo — por ejemplo, arrancado con
        # `--stage stage4_1` para probar. Se juega la variante elegida sin
        # guardarla; la próxima vez se sortea de nuevo, que es correcto
        # porque no hay "próxima vez" que rastrear.
        return
    gestor.fijar_variante_de_stage4_1(variante)


def crear_stage4_1(context: GameContext) -> BaseScene:
    """La función que `STAGE_ORDER` llama en vez de una clase (ver
    `_STAGE_FACTORY_MAP` en `stage_registry.py`)."""
    variante = _variante_persistida(context)
    if variante is None or variante not in VARIANTES_DISPONIBLES:
        variante = elegir_variante()
        _persistir_variante(context, variante)
    ruta = VARIANTES_DISPONIBLES[variante]
    logger.info("stage4_1: variante '%s' (%s)", variante, ruta)
    clase = _cargar_clase(ruta)
    return clase(context)


# `world_map_scene.py::construir_nodos` lee `STAGE_ID`/`STAGE_NAME` por
# `getattr(cls, ...)` esperando una clase de escena; funciona igual con una
# función siempre que declare los mismos atributos — Python no distingue.
# El mapa del mundo se construye **antes** de que exista ninguna partida
# (a nivel de módulo, en la importación), así que no puede reflejar qué
# variante le tocará a ésta: muestra siempre la identidad del cementerio,
# que es la entrada canónica del slot. Sin esto, el nodo se leería
# "crear_stage4_1" (el `__name__` de la función, el mismo respaldo que
# usa `construir_nodos` cuando no encuentra el atributo).
crear_stage4_1.STAGE_ID = "stage4_1"  # type: ignore[attr-defined]
crear_stage4_1.STAGE_NAME = "4-1  EL CEMENTERIO SAGRADO"  # type: ignore[attr-defined]
