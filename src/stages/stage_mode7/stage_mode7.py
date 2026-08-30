from pathlib import Path
from src.engine.core import settings
from src.framework.scenes.stage_scene import StageScene
class Stage_Mode7(StageScene):
    STAGE_ID="mode7"
    STAGE_NAME="MODE7 DEMO"
    TMX_PATH=settings.ASSETS_DIR / "maps/stage_mode7/stage_mode7.tmx"
