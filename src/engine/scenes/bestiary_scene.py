"""
Module: bestiary_scene
System: engine.scenes
Academic Unit: N/A

Catálogo de enemigos encontrados.

Migrada al kit compartido (AUD-069)
-----------------------------------
Antes tenía su propia paleta —oro `(255,215,0)` para el título y el foco, gris
`(100,100,110)` para las pistas, fondos `(30,30,45)` y `(18,18,32)` para las
filas— y su propia navegación, que **se fijaba** en los extremos mientras
`inventory_scene` y `world_map_scene` daban la vuelta. Dos pantallas contiguas
del mismo juego respondían distinto a la misma tecla.

También cargaba sus cuatro fuentes con `font(…)`, saltándose
la escala tipográfica del tema y la caché de fuentes: cuatro objetos nuevos por
escena que nadie reutilizaba.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from src.engine.core import settings
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

from src.engine.scene.base_scene import BaseScene

#: AUD-187 — el alto de la ficha sale de la fuente, no de un número escrito a
#: mano.
#:
#: Antes esto era `ENTRY_HEIGHT = 48` y la descripción se dibujaba en `y + 22`.
#: Ese 22 daba por hecho el alto del nombre; medido, el nombre ocupa 22 px
#: desde `y + 4`, así que terminaba en 26 y la descripción arrancaba en 22:
#: cuatro píxeles de solape de partida. Con el texto ampliado por accesibilidad
#: (AUD-126) el solape crece y la ficha se vuelve ilegible, que es lo contrario
#: de lo que esa opción busca.


def y_de_la_descripcion() -> int:
    """Dónde empieza la descripción, justo debajo del nombre."""
    return Theme.SPACE_XS + font(Theme.FONT_SMALL).get_linesize()


def alto_de_ficha() -> int:
    """Nombre + descripción + el aire de abajo, con la fuente de ahora."""
    return (y_de_la_descripcion()
            + font(Theme.FONT_TINY).get_linesize()
            + Theme.SPACE_S)


class BestiaryScene(BaseScene):
    """Lista de enemigos encontrados, con sus estadísticas."""

    def __init__(self, context: GameContext) -> None:
        super().__init__(context)
        self._menu = MenuList(items=[])
        self._scroll_offset: int = 0

    def on_enter(self) -> None:
        self._refresh_entries()
        self._scroll_offset = 0
        self.context.scene_manager.transition.start_fade_in(0.5)

    def on_exit(self) -> None:
        pass

    def _get_entries(self) -> list:
        from src.framework.entities.bestiary import Bestiary

        bestiary = Bestiary.get_instance()
        return [e for e in bestiary.get_all_entries() if e.encountered]

    def _refresh_entries(self) -> None:
        """Reconstruye las filas a partir del bestiario.

        Se hace al entrar y no en cada fotograma: recorrer el bestiario entero
        sesenta veces por segundo para una lista que sólo cambia al matar algo
        es trabajo tirado, y la versión anterior lo hacía dos veces por
        fotograma —una en `update` y otra en `draw`—.
        """
        self._menu.items = [
            MenuItem(entry.name, value=entry) for entry in self._get_entries()
        ]
        self._menu.ensure_valid()

    def _volver(self) -> None:
        """Vuelve al título, que es de donde se llega aquí.

        AUD-092 — Esc dejaba al jugador en la pantalla equivocada
        ---------------------------------------------------------
        Esto llamaba a `scene_manager.pop`. Pero `TitleScene` abre el bestiario
        con `replace`, que **sustituye** la cima de la pila en vez de apilar
        encima, así que al hacer `pop` no aparecía el título: aparecía lo que
        hubiera debajo, que según el camino recorrido era el menú de demos o
        directamente la pantalla de inicio.

        Medido: título -> demos -> Esc -> título -> bestiario -> Esc dejaba la
        pila en `['SplashScene']`.

        Sus dos hermanas —logros e inventario— ya usaban `replace(TitleScene)`,
        que es el patrón correcto cuando se ha entrado con `replace`. Ésta se
        quedó atrás.
        """
        from src.engine.scenes.title_scene import TitleScene

        self.context.scene_manager.replace(TitleScene(self.context))

    def update(self, dt: float) -> None:
        self._menu.update(dt)
        handle_menu_navigation(
            self._menu, self.input,
            on_cancel=self._volver,
        )
        # La ventana visible sigue al foco: la lista puede ser más larga que la
        # pantalla y el kit no sabe cuántas fichas caben aquí.
        visible = max(1, (settings.INTERNAL_HEIGHT - 60) // alto_de_ficha())
        if self._menu.index < self._scroll_offset:
            self._scroll_offset = self._menu.index
        elif self._menu.index >= self._scroll_offset + visible:
            self._scroll_offset = self._menu.index - visible + 1

    def draw(self, surface: pygame.Surface) -> None:
        top = draw_screen(surface, "BESTIARIO", "Enemigos que has encontrado")

        entry_font = font(Theme.FONT_SMALL)
        stat_font = font(Theme.FONT_TINY)

        if not self._menu.items:
            empty = entry_font.render(
                "Todavía no te has cruzado con ningún enemigo.",
                True, Theme.TEXT_DIM,
            )
            surface.blit(
                empty,
                ((settings.INTERNAL_WIDTH - empty.get_width()) // 2, top + 40),
            )
        else:
            self._draw_entries(surface, top, entry_font, stat_font)

        draw_key_hints(surface, [
            ("↑↓", "Navegar"),
            ("Esc", "Volver"),
        ])

    def _draw_entries(
        self, surface: pygame.Surface, top: int,
        entry_font: pygame.font.Font, stat_font: pygame.font.Font,
    ) -> None:
        for idx, item in enumerate(self._menu.items):
            if idx < self._scroll_offset:
                continue
            y = top + (idx - self._scroll_offset) * alto_de_ficha()
            if y > settings.INTERNAL_HEIGHT - 40:
                break

            entry = item.value
            focused = idx == self._menu.index
            row = pygame.Rect(
                Theme.MARGIN, y,
                settings.INTERNAL_WIDTH - Theme.MARGIN * 2,
                alto_de_ficha() - Theme.SPACE_XS,
            )
            pygame.draw.rect(
                surface,
                Theme.SURFACE_RAISED if focused else Theme.SURFACE,
                row, border_radius=Theme.RADIUS,
            )
            if focused:
                # El mismo cursor lateral que el resto de los menús: el foco no
                # se señala sólo con color, que es inservible con los filtros de
                # daltonismo activos.
                pygame.draw.rect(
                    surface, Theme.ACCENT,
                    pygame.Rect(row.x, row.y, 3, row.height), border_radius=1,
                )

            name = entry_font.render(
                entry.name, True, Theme.ACCENT if focused else Theme.TEXT,
            )
            surface.blit(name, (row.x + Theme.SPACE_M, row.y + Theme.SPACE_XS))

            desc = stat_font.render(entry.description, True, Theme.TEXT_MUTED)
            surface.blit(desc, (row.x + Theme.SPACE_M, row.y + y_de_la_descripcion()))

            kills = stat_font.render(f"Bajas: {entry.kills}", True, Theme.ACCENT_DIM)
            surface.blit(
                kills,
                (row.right - kills.get_width() - Theme.SPACE_M,
                 row.y + Theme.SPACE_XS),
            )

            health = stat_font.render(f"Vida: {entry.hp}", True, Theme.DANGER)
            surface.blit(
                health,
                (row.right - health.get_width() - Theme.SPACE_M,
                 row.y + y_de_la_descripcion()),
            )
