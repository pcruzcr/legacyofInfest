"""
Module: shop_scene
System: engine.scenes
Academic Unit: N/A

La tienda: comprar y vender ropa con las monedas.

Por qué existe (AUD-221, GAP-029)
---------------------------------
`Inventory.buy()` y `Inventory.sell()` estaban escritos y probados por unidad
desde AUD-207, y **sin un solo llamante**. Las monedas que AUD-218 hizo caer de
los enemigos terminaban en una cifra del HUD que no compraba nada.

Es una entrada de menú y no un mercader en el mapa: un interactuable nuevo
obligaría a tocar el cargador de TMX, la rúbrica del calificador y las 26
entregas existentes.

AUD-550 — deja de ser sólo del título. Las monedas se ganan **jugando**
(AUD-218), así que sólo se podían gastar volviendo al título a mitad de
una partida en curso — el mismo defecto de alcance que ya tuvieron
`InventoryScene`/`SkillTreeScene` antes de AUD-533. La tienda se suma al
menú de pausa (`StageScene._abrir_tienda`, `push()`) y `_volver()` sale
con `pop()` en vez de `replace(TitleScene(...))`, para volver a quien la
abrió — el título o la partida pausada — en vez de mandar siempre al
título.

La lista **sale del catálogo** (`_ITEM_DEFS`), no de una copia escrita a mano:
un artículo nuevo con `price > 0` aparece aquí solo. Escribirla a mano es como
`60_GUIA_COMPLETA_DEL_MOTOR.md` acabó publicando seis objetos cuando ya había
dieciséis.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from src.engine.core import settings
from src.engine.core.i18n import _
from src.engine.core.inventory import Inventory, get_inventory
from src.engine.input.action_map import Action
from src.engine.scene.base_scene import BaseScene
from src.engine.scenes.demo_common import BOTTOM_BAR_Y
from src.engine.ui.theme import Theme, font
from src.engine.ui.widgets import (
    MenuItem,
    MenuList,
    draw_key_hints,
    draw_screen,
    handle_menu_navigation,
)

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext


class ShopScene(BaseScene):
    """Pantalla de compraventa de ropa."""

    def __init__(self, context: GameContext) -> None:
        super().__init__(context)
        self._inventory: Inventory = get_inventory()
        #: `"comprar"` o `"vender"`. Izquierda y derecha alternan: arriba y
        #: abajo ya recorren la lista y `CONFIRM` actúa en el modo activo, así
        #: que no hace falta una tecla nueva que rebindear y documentar.
        self.modo: str = "comprar"
        self._aviso: str = ""
        self._aviso_timer: float = 0.0
        self._font_row = font(Theme.FONT_SMALL)
        self._font_desc = font(Theme.FONT_TINY)
        self._menu = MenuList(items=self._construir_filas())

    # ── datos ──────────────────────────────────────────────────────
    def _articulos(self) -> list[str]:
        """Lo que tiene precio, en el orden del catálogo.

        Fuera quedan las mejoras permanentes (se recogen en el nivel), las
        habilidades (las sueltan los jefes) y `coin`, que es el saldo. Ninguna
        se compra, y enseñarlas prometería algo que no se puede hacer.
        """
        from src.engine.core.inventory import _ITEM_DEFS

        return [iid for iid, d in _ITEM_DEFS.items() if d.price > 0]

    def _construir_filas(self) -> list[MenuItem]:
        filas: list[MenuItem] = []
        for item_id in self._articulos():
            defn = self._inventory.get_def(item_id)
            if defn is None:
                continue
            filas.append(MenuItem(
                label=defn.name, value=item_id, hint=defn.description,
            ))
        return filas

    def _precio(self, item_id: str) -> int:
        """Lo que cuesta la operación del modo activo.

        Vender da la mitad, redondeando hacia abajo — el mismo cálculo que
        hace `Inventory.sell()`. Se repite aquí sólo para *mostrarlo*; quien
        mueve el saldo sigue siendo el inventario, que es donde vive la regla.
        """
        defn = self._inventory.get_def(item_id)
        if defn is None:
            return 0
        return defn.price if self.modo == "comprar" else defn.price // 2

    # ── ciclo ──────────────────────────────────────────────────────
    def on_enter(self) -> None:
        self.context.scene_manager.transition.start_fade_in(0.5)

    def on_exit(self) -> None:
        pass

    def _avisar(self, texto: str) -> None:
        self._aviso = texto
        self._aviso_timer = 1.6

    def _operar(self, item: MenuItem) -> None:
        item_id = str(item.value)
        if self.modo == "comprar":
            # `buy()` comprueba el saldo y no deja deber: si devuelve `False`
            # no se ha movido nada. Esa es la comprobación que evita el saldo
            # negativo, y vive en el inventario, no aquí.
            if self._inventory.buy(item_id):
                self._avisar(_("Comprado"))
            else:
                self._avisar(_("No te alcanza"))
        elif self._inventory.sell(item_id):
            self._avisar(_("Vendido"))
        else:
            self._avisar(_("No tienes ninguno"))

    def _volver(self) -> None:
        # AUD-550 — mismo defecto simétrico que `InventoryScene` antes de
        # AUD-533: salía siempre a `TitleScene`, sin importar quién la
        # hubiera abierto. Las monedas se ganan jugando y sólo se
        # gastaban volviendo al título — la tienda se suma al menú de
        # pausa (`StageScene._abrir_tienda`) y necesita `pop()` para
        # devolver a la partida pausada, no `replace()` para saltarse la
        # pila entera.
        self.context.scene_manager.pop()

    def update(self, dt: float) -> None:
        if self._aviso_timer > 0.0:
            self._aviso_timer -= dt
            if self._aviso_timer <= 0.0:
                self._aviso = ""
        im = self.input
        if im is None:
            return
        # El cambio de modo va antes: `handle_menu_navigation` no mira
        # izquierda ni derecha, así que devolvería `False` y las perdería.
        if im.is_action_just_pressed(Action.MOVE_RIGHT):
            self.modo = "vender"
            return
        if im.is_action_just_pressed(Action.MOVE_LEFT):
            self.modo = "comprar"
            return
        handle_menu_navigation(
            self._menu, im, on_confirm=self._operar, on_cancel=self._volver,
        )

    # ── dibujo ─────────────────────────────────────────────────────
    def draw(self, surface: pygame.Surface) -> None:
        top = draw_screen(surface, "TIENDA", "Ropa y equipo")

        etiqueta = _("Monedas")
        saldo = self._font_row.render(
            f"{etiqueta}: {self._inventory.coins}", True, (255, 215, 0),
        )
        surface.blit(saldo, (settings.INTERNAL_WIDTH - saldo.get_width() - 16, top))

        modo_txt = _("Comprar") if self.modo == "comprar" else _("Vender")
        modo_surf = self._font_row.render(f"< {modo_txt} >", True, Theme.ACCENT)
        surface.blit(modo_surf, (16, top))

        y = top + Theme.SPACE_M + modo_surf.get_height()
        fila_h = self._font_row.get_height() + Theme.SPACE_S
        for idx, item in enumerate(self._menu.items):
            item_id = str(item.value)
            foco = idx == self._menu.index
            fila = pygame.Rect(16, y, settings.INTERNAL_WIDTH - 32, fila_h)
            if foco:
                pygame.draw.rect(
                    surface, Theme.SURFACE_RAISED, fila,
                    border_radius=Theme.RADIUS,
                )
            color = Theme.ACCENT if foco else Theme.TEXT
            surface.blit(self._font_row.render(item.label, True, color),
                         (fila.x + 8, fila.y + 2))

            # A la derecha, el precio de la operación y cuántos se tienen: son
            # las dos cifras que deciden la compra, y buscarlas en otra
            # pantalla es lo que hace tediosa una tienda.
            tengo = self._inventory.count(item_id)
            precio = self._font_row.render(
                f"{self._precio(item_id)}", True, (255, 215, 0),
            )
            surface.blit(precio, (fila.right - precio.get_width() - 8, fila.y + 2))
            if tengo:
                marca = self._font_desc.render(f"x{tengo}", True, Theme.TEXT_MUTED)
                surface.blit(
                    marca,
                    (fila.right - precio.get_width() - marca.get_width() - 16,
                     fila.y + 4),
                )
            y += fila_h

        actual = self._menu.current
        if actual is not None and actual.hint:
            desc = self._font_desc.render(actual.hint, True, Theme.TEXT_MUTED)
            surface.blit(
                desc,
                ((settings.INTERNAL_WIDTH - desc.get_width()) // 2,
                 BOTTOM_BAR_Y - 36),
            )
        if self._aviso:
            aviso = self._font_row.render(self._aviso, True, Theme.SUCCESS)
            surface.blit(
                aviso,
                ((settings.INTERNAL_WIDTH - aviso.get_width()) // 2,
                 BOTTOM_BAR_Y - 56),
            )

        draw_key_hints(surface, [
            ("↑↓", "Navegar"),
            ("←→", "Comprar / vender"),
            ("Enter", "Confirmar"),
            ("Esc", "Volver"),
        ])
