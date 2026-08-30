from pathlib import Path
from src.engine.core import settings
from src.framework.scenes.stage_scene import StageScene
class Stage_Frontal(StageScene):
    STAGE_ID="frontal"
    STAGE_NAME="FRONTAL DEMO"
    TMX_PATH=settings.ASSETS_DIR / "maps/stage_frontal/stage_frontal.tmx"
