from pathlib import Path
from src.engine.core import settings
from src.framework.scenes.stage_scene import StageScene
class Stage_Oblicua(StageScene):
    STAGE_ID="oblicua"
    STAGE_NAME="OBLICUA DEMO"
    TMX_PATH=settings.ASSETS_DIR / "maps/stage_oblicua/stage_oblicua.tmx"
