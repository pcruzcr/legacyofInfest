from pathlib import Path
from src.engine.core import settings
from src.framework.scenes.stage_scene import StageScene
class Stage_Dissolve(StageScene):
    STAGE_ID="dissolve"
    STAGE_NAME="DISSOLVE DEMO"
    TMX_PATH=settings.ASSETS_DIR / "maps/stage_dissolve/stage_dissolve.tmx"
