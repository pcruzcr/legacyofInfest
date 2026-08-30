from pathlib import Path
from src.engine.core import settings
from src.framework.scenes.stage_scene import StageScene
class Stage_Stencil(StageScene):
    STAGE_ID="stencil"
    STAGE_NAME="STENCIL DEMO"
    TMX_PATH=settings.ASSETS_DIR / "maps/stage_stencil/stage_stencil.tmx"
