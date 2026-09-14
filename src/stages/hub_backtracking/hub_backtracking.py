from pathlib import Path
from src.engine.core import settings
from src.framework.scenes.stage_scene import StageScene
class HubBacktracking(StageScene):
    STAGE_ID = "hub_backtracking"
    STAGE_NAME = "HUB — NEXO DE VISTAS (100%)"
    TMX_PATH = settings.ASSETS_DIR / "maps/hub_backtracking/hub_backtracking.tmx"
    ZONE = 0
    def __init__(self, context):
        super().__init__(context, self.TMX_PATH)
