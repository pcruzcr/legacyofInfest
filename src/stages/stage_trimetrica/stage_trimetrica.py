from pathlib import Path
from src.engine.core import settings
from src.framework.scenes.stage_scene import StageScene
class Stage_Trimetrica(StageScene):
    STAGE_ID="trimetrica"
    STAGE_NAME="TRIMETRICA DEMO"
    TMX_PATH=settings.ASSETS_DIR / "maps/stage_trimetrica/stage_trimetrica.tmx"
