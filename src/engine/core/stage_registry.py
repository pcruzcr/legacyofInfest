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
    from src.engine.scene.base_scene import BaseScene

# The canonical stage order matching the sequence defined in 33_SCOPE_ADJUSTMENT.md §2.1
STAGE_ORDER: list[str] = [
    "stage0",
    # F5.13 — el laboratorio de mecánicas va justo después del prólogo.
    #
    # Ahí y no al final por un motivo: es material didáctico, y el material
    # didáctico que hay que desbloquear no lo ve nadie. Un estudiante que abre
    # el juego para ver cómo funciona el viento no debería tener que jugarse
    # trece niveles antes.
    "stage_mecanicas",
    "stage1_1", "stage1_2", "stage1_3", "stage1_4_boss_venado",
    "stage2_1", "stage2_2", "stage2_3", "stage2_4_boss_rey",
    "stage3_1", "stage3_2", "stage3_3", "stage3_4_boss_gavilan",
    "stage4_1", "stage4_2_boss_paburu",
]

# Custom module import paths for stages that don't follow the {id}.{id} convention.
# Key: stage_id from STAGE_ORDER. Value: dotted module path.
# Configurable in a JSON config file for extensibility (see ARC-004 in 33_SCOPE_ADJUSTMENT.md).
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


def discover_stages() -> list[type[BaseScene]]:
    """Scans src/stages/ in STAGE_ORDER. Imports each module that exists
    and finds the BaseScene subclass. Returns ordered list. Skips missing stages."""
    from src.engine.scene.base_scene import BaseScene

    stages: list[type[BaseScene]] = []
    for stage_id in STAGE_ORDER:
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
