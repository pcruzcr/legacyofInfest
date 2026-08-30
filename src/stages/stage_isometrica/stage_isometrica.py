from pathlib import Path
from src.engine.core import settings
from src.framework.scenes.stage_scene import StageScene
class Stage_Isometrica(StageScene):
    STAGE_ID="isometrica"
    STAGE_NAME="ISOMETRICA DEMO"
    TMX_PATH=settings.ASSETS_DIR / "maps/stage_isometrica/stage_isometrica.tmx"
