from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from src.framework.scenes.stage_scene import StageScene
from src.framework.stage.stage_loader import StageLoader
from src.stages.stage3_4_boss_gavilan.boss_gavilan import BossGavilan

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext

# AUD-106 — línea añadida al integrar la entrega.
#
# `boss_gavilan.py` define `BossGavilan` correctamente y el TMX lo coloca con
# `type="BossGavilan"`, pero **nadie lo registraba**. Sin esta línea el
# cargador no sabe construirlo: el jefe no aparecería en su propia arena.
#
# Es lo que hacen sus compañeros —`stage1_3_las_aulas` registra así sus dos
# enemigos, `boss_paburu` y `boss_rey` lo hacen desde su escena— y lo que
# describe la guía del estudiante.
StageLoader.register_entity("BossGavilan", BossGavilan)


class Stage3_4BossGavilanScene(StageScene):
    STAGE_ID: str = "stage3_4_boss_gavilan"
    STAGE_NAME: str = "EL GAVILAN"
    ZONE: int = 3

    def __init__(self, context: GameContext) -> None:
        super().__init__(
            context,
            Path("assets/maps/stage3_4_boss_gavilan/stage3_4_boss_gavilan.tmx"),
        )

