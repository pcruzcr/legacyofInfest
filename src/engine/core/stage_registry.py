"""
Module: stage_registry
System: engine.core
Academic Unit: N/A
Description: Dynamic stage discovery and ordering. Scans src/stages/
in the defined STAGE_ORDER and imports existing stage modules,
returning their BaseScene subclasses in order.
"""
from __future__ import annotations

import importlib
import logging
from typing import TYPE_CHECKING

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from src.engine.core.game_context import GameContext
    from src.engine.scene.base_scene import BaseScene

# The canonical stage order (progression sequence for `main.py` and the title menu).
# Solo stage0 va en el juego; el resto son ejemplos (ver docs/86 y stage_mecanicas/cenital).
# stage_mecanicas y stage_cenital son laboratorios de ejemplo, no progresión.
# stage4_1 conecta con stage4_2 para mapa completo (NextTrigger 4_1 → 4_2).
STAGE_ORDER: list[str] = [
    "stage0",
    "stage1_1", "stage1_2", "stage1_3", "stage1_4_boss_venado",
    "stage2_1", "stage2_2", "stage2_3", "stage2_4_boss_rey",
    "stage3_1", "stage3_2", "stage3_3", "stage3_4_boss_gavilan",
    "stage4_1", "stage4_2_boss_paburu",
]

# Custom module import paths for stages that don't follow the {id}.{id} convention.
# Key: stage_id from STAGE_ORDER. Value: dotted module path.
_STAGE_MODULE_MAP: dict[str, str] = {
    "stage1_4_boss_venado": "src.stages.boss_venado.boss_venado_scene",
    # AUD-106 — las entregas de la Evaluación Práctica I.
    #
    # `STAGE_ORDER` usa los identificadores canónicos del documento de alcance
    # (`stage1_2`, `stage2_1`…). Los estudiantes nombraron sus carpetas con el
    # nombre del sitio —«la soda», «las aulas», «oficinas»—, que es más legible
    # y es lo que la guía les invita a hacer. Sin este mapa, `discover_stages`
    # encontraba **4 de 13** y los otros nueve no aparecían en el juego pese a
    # estar instalados y validados.
    #
    # Los nombres se dejan como los entregó cada estudiante: renombrarles la
    # carpeta para que encaje en una convención interna es trabajo del motor,
    # no suyo.
    "stage1_2": "src.stages.stage1_2_la_soda.stage1_2_la_soda",
    "stage1_3": "src.stages.stage1_3_las_aulas.stage1_3_las_aulas",
    "stage2_1": "src.stages.stage2_1_oficinas.stage2_1_oficinas",
    "stage2_3": "src.stages.lobby_datacenter.lobby_datacenter",
    "stage2_4_boss_rey": "src.stages.boss_rey.boss_rey_scene",
    "stage3_1": "src.stages.stage3_1_la_entrada_de_piedra.stage3_1_la_entrada_de_piedra",
    # `hall` estuvo mapeado a `stage2_2` por error mío al integrar. Su propio
    # código lo desmentía desde el principio: `ZONE = 3` y
    # `STAGE_NAME = "3-2  EL HALL"`. Ocupaba la ranura de otro compañero y se
    # jugaba en la zona equivocada. Va donde él dijo que iba.
    "stage3_2": "src.stages.hall.hall",
    "stage3_3": "src.stages.stage3_3_el_patio.stage3_3_el_patio",
    "stage4_2_boss_paburu": "src.stages.boss_paburu.boss_paburu_scene",
}

# AUD-518 — slots que no resuelven a una clase fija sino a una función
# fábrica: la función decide qué escena de verdad construir. `stage4_1` es
# el primer caso (sorteo entre variantes del nivel, persistido en el save,
# ver `src/stages/stage4_1/selector.py::crear_stage4_1`). Clave: stage_id.
# Valor: ruta punteada `módulo.función`, no `módulo.Clase` como
# `_STAGE_MODULE_MAP` — por eso es un diccionario aparte y no una entrada
# más del de arriba, que siempre busca una subclase de `BaseScene` dentro
# del módulo.
#
# `SceneManager._enter_next_stage` llama `next_stage_class(self._context)`
# igual para una clase que para una función; no hace falta tocarlo.
_STAGE_FACTORY_MAP: dict[str, str] = {
    "stage4_1": "src.stages.stage4_1.selector.crear_stage4_1",
}


def discover_stages() -> list[Callable[[GameContext], BaseScene]]:
    """Scans src/stages/ in STAGE_ORDER. Imports each module that exists
    and finds the BaseScene subclass. Returns ordered list. Skips missing stages.

    A stage_id in `_STAGE_FACTORY_MAP` skips the class search entirely: its
    factory function decides what to build, possibly differently each call.
    """
    from src.engine.scene.base_scene import BaseScene

    stages: list[Callable[[GameContext], BaseScene]] = []
    for stage_id in STAGE_ORDER:
        fabrica_path = _STAGE_FACTORY_MAP.get(stage_id)
        if fabrica_path is not None:
            modulo_path, _, nombre_funcion = fabrica_path.rpartition(".")
            try:
                modulo_fabrica = importlib.import_module(modulo_path)
                stages.append(getattr(modulo_fabrica, nombre_funcion))
                logger.info(
                    "StageRegistry: discovered %s -> %s (fábrica)", stage_id, fabrica_path
                )
            except (ModuleNotFoundError, AttributeError) as e:
                logger.error(
                    "StageRegistry: error loading factory for %s: %s", stage_id, e
                )
            continue

        module_path = _STAGE_MODULE_MAP.get(
            stage_id, f"src.stages.{stage_id}.{stage_id}"
        )
        try:
            module = importlib.import_module(module_path)
            found = False
            for name in dir(module):
                obj = getattr(module, name)
                if (isinstance(obj, type)
                        and issubclass(obj, BaseScene)
                        and obj is not BaseScene):
                    stages.append(obj)
                    found = True
                    logger.info("StageRegistry: discovered %s -> %s", stage_id, name)
                    break
            if not found:
                logger.warning(
                    "StageRegistry: %s imported but no BaseScene subclass found", stage_id
                )
        except ModuleNotFoundError:
            logger.info("StageRegistry: %s not found — skipping", stage_id)
        except (ImportError, AttributeError) as e:
            logger.error("StageRegistry: error loading %s: %s", stage_id, e)

    return stages


def carpeta_del_mapa(stage_id: str) -> str:
    """A qué carpeta de `assets/maps/` corresponde este `stage_id`.

    AUD-548 — los créditos necesitaban saber dónde vive el `.tmx` de cada
    escenario para leer su `author`, y no existía nada que lo resolviera
    fuera de `discover_stages()` (que además importa el módulo entero,
    caro para algo que sólo quiere leer metadatos de un XML). La carpeta
    de mapas sigue la misma convención que la de `src/stages/`: el
    penúltimo segmento de la ruta punteada (`_STAGE_MODULE_MAP` o
    `_STAGE_FACTORY_MAP` si están declarados; si no, `stage_id` tal
    cual, la convención por defecto `src.stages.{id}.{id}`).
    """
    ruta = (_STAGE_FACTORY_MAP.get(stage_id) or _STAGE_MODULE_MAP.get(stage_id)
            or f"src.stages.{stage_id}.{stage_id}")
    partes = ruta.split(".")
    # ["src", "stages", "<carpeta>", ...resto]
    return partes[2] if len(partes) > 2 else stage_id


def ruta_del_mapa(stage_id: str) -> Path | None:
    """El `.tmx` principal de este `stage_id`, o `None` si no se encuentra.

    "Principal": si la carpeta trae más de un `.tmx` (como `stage4_1c`,
    con tres plantillas), se queda con el que comparte nombre con la
    carpeta — la convención que sigue cada escenario de verdad — y si
    ninguno calza, el primero en orden alfabético; cualquiera de los dos
    sirve para leer metadatos que hoy son iguales en las tres plantillas.
    """
    from src.engine.core import settings

    carpeta = settings.ASSETS_DIR / "maps" / carpeta_del_mapa(stage_id)
    if not carpeta.is_dir():
        return None
    candidato = carpeta / f"{carpeta.name}.tmx"
    if candidato.exists():
        return candidato
    tmxs = sorted(carpeta.glob("*.tmx"))
    return tmxs[0] if tmxs else None
