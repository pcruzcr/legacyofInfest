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
from src.engine.core.i18n import _
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

    def _item_ids(self) -> list[str]:
        """Lo que se ve en la rejilla, en orden.

        AUD-220 — las monedas quedan fuera. `coin` es un objeto del inventario
        como cualquier otro (así es como se guarda el saldo), pero enseñarlo
        como una casilla más invita a seleccionarlo y a esperar que haga algo.
        El saldo va en la cabecera, que es donde se lee una cifra.
        """
        return [iid for iid in self._inventory.items if iid != "coin"]

    def _equipar_seleccionado(self) -> None:
        """Pone o quita la prenda bajo el cursor.

        AUD-220 — GAP-029, conexión 3 de 4. `Inventory.equip()` no tenía un
        solo llamante en la interfaz. Desde AUD-207 la bonificación de la ropa
        **sólo cuenta puesta**, así que sin esta acción comprar ropa dejaba al
        jugador peor que antes: pagaba y no recibía nada.
        """
        ids = self._item_ids()
        if not ids:
            return
        item_id = ids[min(self._selected_slot, len(ids) - 1)]
        defn = self._inventory.get_def(item_id)
        # Sin hueco no hay nada que equipar: las mejoras permanentes cuentan
        # por tenerlas, y las habilidades de jefe no se ponen ni se quitan.
        if defn is None or defn.slot is None or defn.slot == "skill":
            return
        if self._inventory.get_equipped().get(defn.slot) == item_id:
            self._inventory.unequip(defn.slot)
        else:
            self._inventory.equip(item_id)

    def update(self, dt: float) -> None:
        im = self.input
        if im is None:
            return
        # AUD-220: `CONFIRM` ya no sale. Salía **además** de `CANCEL`, un atajo
        # redundante que ocupaba la única tecla natural para «ponerse esto».
        if im.is_action_just_pressed(Action.CANCEL):
            # AUD-533 — antes siempre reemplazaba por `TitleScene`, así que
            # sólo se podía llegar aquí desde el título (que la abría con
            # `replace`, el mismo error simétrico). Eso hacía imposible
            # abrir el inventario a mitad de partida: cancelar te mandaba
            # al título en vez de devolverte al juego pausado. `pop()`
            # vuelve a quien haya empujado esta pantalla — el título o una
            # partida en pausa — sea cual sea.
            self.context.scene_manager.pop()
            return
        if im.is_action_just_pressed(Action.CONFIRM):
            self._equipar_seleccionado()
            return
        total = len(self._item_ids())
        if not total:
            return
        # El cursor se recorta antes de moverlo: vender desde la tienda puede
        # haber dejado menos casillas de las que había al entrar.
        self._selected_slot = min(self._selected_slot, total - 1)
        if im.is_action_just_pressed(Action.MOVE_RIGHT):
            self._selected_slot = (self._selected_slot + 1) % total
        if im.is_action_just_pressed(Action.MOVE_LEFT):
            self._selected_slot = (self._selected_slot - 1) % total
        if im.is_action_just_pressed(Action.MOVE_DOWN):
            self._selected_slot = min(self._selected_slot + 4, total - 1)
        if im.is_action_just_pressed(Action.MOVE_UP):
            self._selected_slot = max(self._selected_slot - 4, 0)

    def draw(self, surface: pygame.Surface) -> None:
        top = draw_screen(surface, "INVENTARIO", "Objetos recogidos")
        # AUD-220: el saldo se dibuja aparte y **no** como subtítulo. La
        # traducción la hace `draw_screen` sobre la cadena entera, así que un
        # f-string con el número dentro no coincidiría con ninguna entrada del
        # catálogo y esta pantalla se quedaría sin traducir en inglés.
        # El literal va suelto y no dentro del f-string: `check_translations`
        # busca las cadenas envueltas en `_()` y no las ve anidadas.
        etiqueta = _("Monedas")
        saldo = self._font_item.render(
            f"{etiqueta}: {self._inventory.coins}", True, (255, 215, 0),
        )
        surface.blit(saldo, (settings.INTERNAL_WIDTH - saldo.get_width() - 16, top))
        item_ids = self._item_ids()
        equipado = self._inventory.get_equipped()
        if item_ids:
            self._selected_slot = min(self._selected_slot, len(item_ids) - 1)
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
                # AUD-220: lo puesto se marca. Sin la marca, el hueco es
                # invisible y el jugador no sabe si ya lleva la capucha o si
                # pulsó y no pasó nada.
                if defn is not None and equipado.get(defn.slot or "") == item_id:
                    pygame.draw.rect(
                        surface, Theme.SUCCESS, rect, 2,
                        border_radius=Theme.RADIUS,
                    )
                    puesto = self._font_desc.render(_("PUESTO"), True, Theme.SUCCESS)
                    surface.blit(puesto, (sx + 4, sy + 2))
                if defn and defn.description and focused:
                    desc_surf = self._font_desc.render(
                        defn.description, True, Theme.TEXT_MUTED,
                    )
                    dx = (settings.INTERNAL_WIDTH - desc_surf.get_width()) // 2
                    surface.blit(desc_surf, (dx, BOTTOM_BAR_Y - 36))

        draw_key_hints(surface, [
            ("←→↑↓", "Navegar"),
            ("Enter", "Poner / quitar"),
            ("Esc", "Volver"),
        ])

