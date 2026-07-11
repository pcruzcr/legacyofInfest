"""
Module: world_map_scene
System: engine.scenes
Academic Unit: N/A
Description: World map scene with nodes connected by paths.
"""
from __future__ import annotations
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pygame
from src.engine.core import settings
from src.engine.input.action_map import Action
from src.engine.scene.base_scene import BaseScene

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext


class WorldMapScene(BaseScene):
    """World map — nodes connected by paths, hover to see name."""

    def __init__(self, context: GameContext) -> None:
        super().__init__(context)
        self._nodes: list[dict[str, Any]] = [
            {"id": "stage0", "name": "Forest", "x": 80, "y": 100, "unlocked": True},
            {"id": "stage1", "name": "Caves", "x": 200, "y": 80, "unlocked": True},
            {"id": "stage2", "name": "Ruins", "x": 320, "y": 120, "unlocked": False},
            {"id": "stage3", "name": "Citadel", "x": 240, "y": 160, "unlocked": False},
            {"id": "stage4", "name": "Boss", "x": 160, "y": 160, "unlocked": False},
        ]
        self._connections: list[tuple[int, int]] = [(0, 1), (1, 2), (2, 3), (3, 4), (1, 4)]
        self._selected: int = 0
        self._font_title = pygame.font.Font(None, 28)
        self._font_name = pygame.font.Font(None, 18)
        self._font_hint = pygame.font.Font(None, 14)

    def on_enter(self) -> None:
        pass

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
            from src.engine.core.event_bus import emit
            from src.engine.core.events import Events
            emit(Events.SFX_MENU_HOVER)
        if im.is_action_just_pressed(Action.CONFIRM):
            node = self._nodes[self._selected]
            if node.get("unlocked"):
                from src.engine.core.event_bus import emit
                from src.engine.core.events import Events
                emit(Events.SFX_MENU_CONFIRM)
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
        for a, b in self._connections:
            na = self._nodes[a]
            nb = self._nodes[b]
            pygame.draw.line(surface, (60, 60, 80), (na["x"], na["y"]), (nb["x"], nb["y"]), 2)
        for idx, node in enumerate(self._nodes):
            color = (200, 200, 100) if idx == self._selected \
                else ((80, 160, 80) if node.get("unlocked") else (80, 80, 80))
            pygame.draw.circle(surface, color, (node["x"], node["y"]), 10)
            label = self._font_name.render(
                node["name"], True,
                (220, 220, 220) if node.get("unlocked") else (120, 120, 120))
            surface.blit(label, (node["x"] + 16, node["y"] - 8))
        hint = self._font_hint.render("[ESC] Back  [ARROWS] Navigate  [ENTER] Select", True, (120, 120, 130))
        surface.blit(hint, ((settings.INTERNAL_WIDTH - hint.get_width()) // 2, settings.INTERNAL_HEIGHT - 18))
