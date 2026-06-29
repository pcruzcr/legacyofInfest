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

if TYPE_CHECKING:
    from src.engine.scene.base_scene import BaseScene

# The canonical stage order matching the sequence defined in 33_SCOPE_ADJUSTMENT.md §2.1
STAGE_ORDER: list[str] = [
    "stage0",
    "stage1_1", "stage1_2", "stage1_3", "stage1_4_boss_venado",
    "stage2_1", "stage2_2", "stage2_3", "stage2_4_boss_rey",
    "stage3_1", "stage3_2", "stage3_3", "stage3_4_boss_gavilan",
    "stage4_1", "stage4_2_boss_paburu",
]


def discover_stages() -> list[type["BaseScene"]]:
    """Scans src/stages/ in STAGE_ORDER. Imports each module that exists
    and finds the BaseScene subclass. Returns ordered list. Skips missing stages."""
    from src.engine.scene.base_scene import BaseScene

    stages: list[type[BaseScene]] = []
    for stage_id in STAGE_ORDER:
        try:
            module = importlib.import_module(f"src.stages.{stage_id}.{stage_id}")
            found = False
            for name in dir(module):
                obj = getattr(module, name)
                if (isinstance(obj, type)
                        and issubclass(obj, BaseScene)
                        and obj is not BaseScene):
                    stages.append(obj)
                    found = True
                    logging.info(f"StageRegistry: discovered {stage_id} -> {name}")
                    break
            if not found:
                logging.warning(
                    f"StageRegistry: {stage_id} imported but no BaseScene subclass found"
                )
        except ModuleNotFoundError:
            logging.info(f"StageRegistry: {stage_id} not found — skipping")
        except Exception as e:
            logging.error(f"StageRegistry: error loading {stage_id}: {e}")

    return stages
