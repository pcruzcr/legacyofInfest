from pathlib import Path
from src.engine.core import settings
from src.framework.scenes.stage_scene import StageScene
class Stage_Dimetrica(StageScene):
    STAGE_ID="dimetrica"
    STAGE_NAME="DIMETRICA DEMO"
    TMX_PATH=settings.ASSETS_DIR / "maps/stage_dimetrica/stage_dimetrica.tmx"
