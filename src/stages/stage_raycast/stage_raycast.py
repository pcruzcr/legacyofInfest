from pathlib import Path
from src.engine.core import settings
from src.framework.scenes.stage_scene import StageScene
class Stage_Raycast(StageScene):
    STAGE_ID="raycast"
    STAGE_NAME="RAYCAST DEMO"
    TMX_PATH=settings.ASSETS_DIR / "maps/stage_raycast/stage_raycast.tmx"
