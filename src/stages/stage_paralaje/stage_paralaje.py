from pathlib import Path
from src.engine.core import settings
from src.framework.scenes.stage_scene import StageScene
class Stage_Paralaje(StageScene):
    STAGE_ID="paralaje"
    STAGE_NAME="PARALAJE DEMO"
    TMX_PATH=settings.ASSETS_DIR / "maps/stage_paralaje/stage_paralaje.tmx"
