"""
Module: inventory_scene
System: engine.scenes
Academic Unit: N/A

Inventario en rejilla de los objetos recogidos.

Migrada al kit compartido (AUD-069)
-----------------------------------
Aquí **no** se usa `MenuList`: el kit modela listas verticales y esto es una
rejilla de cuatro columnas donde izquierda y derecha significan algo distinto
que arriba y abajo. Forzar el widget habría roto la navegación para ganar una
casilla en una tabla de migración, que es trabajo con forma de progreso y sin
efecto.

Lo que sí se unifica es lo que compartía con el resto: la paleta —tenía cinco
colores propios y un fondo `(20,20,30)` que no coincide con el del juego—, la
escala tipográfica y los atajos de teclado, que esta pantalla no mostraba.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from src.engine.core import settings
from src.engine.core.inventory import Inventory
from src.engine.input.action_map import Action
from src.engine.scene.base_scene import BaseScene
from src.engine.scenes.demo_common import BOTTOM_BAR_Y
from src.engine.ui.theme import Theme, font
from src.engine.ui.widgets import draw_key_hints, draw_screen

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext


class InventoryScene(BaseScene):
    """Inventory screen — displays collected items in a grid."""

    def __init__(self, context: GameContext) -> None:
        super().__init__(context)
        self._inventory: Inventory = context.inventory if hasattr(context, "inventory") else Inventory()
        self._selected_slot: int = 0
        # Fuentes de la escala del tema y a través de su caché, en vez de tres
        # objetos nuevos con tamaños inventados.
        self._font_item = font(Theme.FONT_SMALL)
        self._font_desc = font(Theme.FONT_TINY)

    def on_enter(self) -> None:
        self.context.scene_manager.transition.start_fade_in(0.5)

    def on_exit(self) -> None:
        pass

    def update(self, dt: float) -> None:
        im = self.input
        if im is None:
            return
        if im.is_action_just_pressed(Action.CANCEL) or im.is_action_just_pressed(Action.CONFIRM):
            from src.engine.scenes.title_scene import TitleScene
            self.context.scene_manager.replace(TitleScene(self.context))
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

    def draw(self, surface: pygame.Surface) -> None:
        top = draw_screen(surface, "INVENTARIO", "Objetos recogidos")
        item_ids = list(self._inventory.items.keys())
        if not item_ids:
            empty = self._font_item.render(
                "Todavía no has recogido nada.", True, Theme.TEXT_DIM,
            )
            surface.blit(
                empty,
                ((settings.INTERNAL_WIDTH - empty.get_width()) // 2, top + 40),
            )
        else:
            cols = 4
            slot_size = 48
            start_x = (settings.INTERNAL_WIDTH - cols * slot_size) // 2
            start_y = top + Theme.SPACE_M
            for idx, item_id in enumerate(item_ids):
                col = idx % cols
                row = idx // cols
                sx = start_x + col * slot_size
                sy = start_y + row * slot_size
                rect = pygame.Rect(sx + 4, sy + 4, slot_size - 8, slot_size - 8)
                focused = idx == self._selected_slot
                pygame.draw.rect(
                    surface,
                    Theme.SURFACE_RAISED if focused else Theme.SURFACE,
                    rect, border_radius=Theme.RADIUS,
                )
                if focused:
                    # Borde de acento: en una rejilla el fondo elevado solo no
                    # se distingue bien de la casilla contigua.
                    pygame.draw.rect(
                        surface, Theme.ACCENT, rect, 1,
                        border_radius=Theme.RADIUS,
                    )
                defn = self._inventory.get_def(item_id)
                name = defn.name if defn else item_id
                label = self._font_item.render(
                    name[:10], True, Theme.ACCENT if focused else Theme.TEXT,
                )
                surface.blit(label, (sx + 4, sy + slot_size - 14))
                if defn and defn.description and focused:
                    desc_surf = self._font_desc.render(
                        defn.description, True, Theme.TEXT_MUTED,
                    )
                    dx = (settings.INTERNAL_WIDTH - desc_surf.get_width()) // 2
                    surface.blit(desc_surf, (dx, BOTTOM_BAR_Y - 36))

        draw_key_hints(surface, [
            ("←→↑↓", "Navegar"),
            ("Esc", "Volver"),
        ])

