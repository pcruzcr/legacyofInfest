from pathlib import Path
from src.engine.core import settings
from src.framework.scenes.stage_scene import StageScene
class StageYSorting(StageScene):  # AUD-XXX: identificador Python no puede contener guion; clase renombrada desde Stage_Y-sorting
    STAGE_ID = "y-sorting"
    STAGE_NAME = "Y-SORTING DEMO"
    TMX_PATH = settings.ASSETS_DIR / "maps/stage_y-sorting/stage_y-sorting.tmx"
