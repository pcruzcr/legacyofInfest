"""
Module: inventory_scene
System: engine.scenes
Academic Unit: N/A
Description: Inventory screen showing collected items with grid layout.
"""
from __future__ import annotations
import pygame
from typing import TYPE_CHECKING
from src.engine.core import settings
from src.engine.input.action_map import Action
from src.engine.scene.base_scene import BaseScene
from src.engine.core.inventory import Inventory
from src.engine.scenes.demo_common import BOTTOM_BAR_Y

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext


class InventoryScene(BaseScene):
    """Inventory screen — displays collected items in a grid."""

    def __init__(self, context: GameContext) -> None:
        super().__init__(context)
        self._inventory: Inventory = context.inventory if hasattr(context, "inventory") else Inventory()
        self._selected_slot: int = 0
        self._font_title = pygame.font.Font(None, 28)
        self._font_item = pygame.font.Font(None, 18)
        self._font_desc = pygame.font.Font(None, 14)

    def on_enter(self) -> None:
        pass

    def on_exit(self) -> None:
        pass

    def update(self, dt: float) -> None:
        im = self.input
        if im is None:
            return
        items = self._inventory.items
        if not items:
            return
        if im.is_action_just_pressed(Action.MOVE_RIGHT):
            self._selected_slot = (self._selected_slot + 1) % len(items)
        if im.is_action_just_pressed(Action.MOVE_LEFT):
            self._selected_slot = (self._selected_slot - 1) % len(items)
        if im.is_action_just_pressed(Action.MOVE_DOWN):
            self._selected_slot = min(self._selected_slot + 4, len(items) - 1)
        if im.is_action_just_pressed(Action.MOVE_UP):
            self._selected_slot = max(self._selected_slot - 4, 0)
        if im.is_action_just_pressed(Action.CANCEL) or im.is_action_just_pressed(Action.CONFIRM):
            from src.engine.scenes.title_scene import TitleScene
            self.context.scene_manager.replace(TitleScene(self.context))

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((20, 20, 30))
        title = self._font_title.render("INVENTORY", True, (255, 255, 240))
        surface.blit(title, ((settings.INTERNAL_WIDTH - title.get_width()) // 2, 20))
        item_ids = list(self._inventory.items.keys())
        if not item_ids:
            empty = self._font_item.render("No items collected yet.", True, (160, 160, 160))
            surface.blit(empty, ((settings.INTERNAL_WIDTH - empty.get_width()) // 2, 96))
        else:
            cols = 4
            slot_size = 48
            start_x = (settings.INTERNAL_WIDTH - cols * slot_size) // 2
            start_y = 70
            for idx, item_id in enumerate(item_ids):
                col = idx % cols
                row = idx // cols
                sx = start_x + col * slot_size
                sy = start_y + row * slot_size
                rect = pygame.Rect(sx + 4, sy + 4, slot_size - 8, slot_size - 8)
                color_bg = (60, 60, 90) if idx == self._selected_slot else (40, 40, 60)
                pygame.draw.rect(surface, color_bg, rect, border_radius=4)
                defn = self._inventory.get_def(item_id)
                name = defn.name if defn else item_id
                label = self._font_item.render(name[:10], True, (220, 220, 220))
                surface.blit(label, (sx + 4, sy + slot_size - 14))
                if defn and defn.description and idx == self._selected_slot:
                    desc_surf = self._font_desc.render(defn.description, True, (180, 180, 180))
                    dx = (settings.INTERNAL_WIDTH - desc_surf.get_width()) // 2
                    surface.blit(desc_surf, (dx, BOTTOM_BAR_Y - 36))

