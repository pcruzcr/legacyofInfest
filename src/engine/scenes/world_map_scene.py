from __future__ import annotations
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pygame
from src.engine.core import settings
from src.engine.core.events import Events
from src.engine.input.action_map import Action
from src.engine.scene.base_scene import BaseScene
from src.engine.scenes.demo_common import BOTTOM_BAR_Y

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext
    from src.engine.core.save_data import SaveData


STAGE_NODES: list[dict[str, Any]] = [
    {"id": "stage0", "name": "Stage 0", "x": 80, "y": 60, "unlocks": ["stage1"]},
    {"id": "stage1", "name": "Zone 1-1", "x": 200, "y": 50, "unlocks": ["stage2"]},
    {"id": "stage2", "name": "Zone 1-2", "x": 280, "y": 80, "unlocks": ["stage3"]},
    {"id": "stage3", "name": "Zone 1-3", "x": 200, "y": 130, "unlocks": ["stage4"]},
    {"id": "stage4", "name": "Boss Venado", "x": 80, "y": 160, "unlocks": []},
]

_node_index = {nd["id"]: i for i, nd in enumerate(STAGE_NODES)}
CONNECTIONS: list[tuple[int, int]] = [
    (i, _node_index[uid])
    for i, nd in enumerate(STAGE_NODES)
    for uid in nd.get("unlocks", [])
]


class WorldMapScene(BaseScene):
    def __init__(self, context: GameContext) -> None:
        super().__init__(context)
        self._selected: int = 0
        self._font_title = pygame.font.Font(None, 28)
        self._font_name = pygame.font.Font(None, 18)
        self._font_hint = pygame.font.Font(None, 14)
        self._save_data: SaveData | None = None
        self._nodes: list[dict[str, Any]] = []

    def _load_save_data(self) -> None:
        sm = self.context.save_manager
        if sm is not None:
            slot = sm.newest_slot()
            if slot is not None:
                self._save_data = sm.load(slot)

    def _build_nodes(self) -> None:
        completed: list[str] = []
        if self._save_data is not None:
            completed = list(self._save_data.completed_stages)

        self._nodes = []
        for nd in STAGE_NODES:
            node = dict(nd)
            node["unlocked"] = (
                node["id"] == "stage0"
                or any(prev_id in completed for prev_id in STAGE_NODES
                       if node["id"] in nd.get("unlocks", []))
                or node["id"] in completed
            )
            node["completed"] = node["id"] in completed
            self._nodes.append(node)

    def on_enter(self) -> None:
        self._load_save_data()
        self._build_nodes()
        self.context.scene_manager.transition.start_fade_in(0.5)

    def on_exit(self) -> None:
        pass

    def update(self, dt: float) -> None:
        im = self.input
        if im is None:
            return
        prev = self._selected
        if im.is_action_just_pressed(Action.MOVE_RIGHT):
            self._selected = (self._selected + 1) % len(self._nodes)
        if im.is_action_just_pressed(Action.MOVE_LEFT):
            self._selected = (self._selected - 1) % len(self._nodes)
        if im.is_action_just_pressed(Action.MOVE_DOWN):
            self._selected = (self._selected + 2) % len(self._nodes)
        if im.is_action_just_pressed(Action.MOVE_UP):
            self._selected = (self._selected - 2) % len(self._nodes)
        if self._selected != prev:
            self.context.event_bus.emit(Events.SFX_MENU_HOVER)
        if im.is_action_just_pressed(Action.CONFIRM):
            node = self._nodes[self._selected]
            if node.get("unlocked"):
                self.context.event_bus.emit(Events.SFX_MENU_CONFIRM)
                node_id = node["id"]
                tmx_path = Path(settings.ASSETS_DIR / "maps" / node_id / f"{node_id}.tmx")
                if tmx_path.exists():
                    from src.framework.scenes.stage_scene import StageScene
                    self.context.scene_manager.replace(StageScene(self.context, tmx_path))
        if im.is_action_just_pressed(Action.CANCEL):
            from src.engine.scenes.title_scene import TitleScene
            self.context.scene_manager.replace(TitleScene(self.context))

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((15, 15, 25))
        title = self._font_title.render("WORLD MAP", True, (255, 255, 240))
        surface.blit(title, ((settings.INTERNAL_WIDTH - title.get_width()) // 2, 16))
        for a, b in CONNECTIONS:
            na = self._nodes[a]
            nb = self._nodes[b]
            color = (100, 160, 100) if na.get("completed") else (60, 60, 80)
            pygame.draw.line(surface, color, (na["x"], na["y"]), (nb["x"], nb["y"]), 2)
        for idx, node in enumerate(self._nodes):
            if idx == self._selected:
                color = (200, 200, 100)
            elif node.get("completed"):
                color = (100, 220, 100)
            elif node.get("unlocked"):
                color = (80, 160, 80)
            else:
                color = (80, 80, 80)
            pygame.draw.circle(surface, color, (node["x"], node["y"]), 10)
            label = self._font_name.render(
                node["name"], True,
                (220, 220, 220) if node.get("unlocked") else (120, 120, 120))
            surface.blit(label, (node["x"] + 16, node["y"] - 8))
        hint = self._font_hint.render("[ESC] Back  [ARROWS] Navigate  [ENTER] Select", True, (120, 120, 130))
        surface.blit(hint, ((settings.INTERNAL_WIDTH - hint.get_width()) // 2, BOTTOM_BAR_Y - 14))

