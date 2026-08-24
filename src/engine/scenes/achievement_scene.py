"""
Module: achievement_scene
System: engine.scenes
Academic Unit: N/A

Lista de logros, desbloqueados y pendientes.

Migrada al kit compartido (AUD-069)
-----------------------------------
Tenía **seis** colores propios sólo para las filas —oro, crema, dos grises para
lo bloqueado, amarillo para el cursor y lila para la descripción— y navegación
que se fijaba en los extremos mientras otras pantallas del mismo juego dan la
vuelta.

Un detalle de legibilidad que sí era un defecto y no una preferencia: un logro
bloqueado y **enfocado** se dibujaba en `(100,100,100)` sobre un fondo oscuro.
Ese gris sobre ese fondo queda por debajo del mínimo de contraste AA, de modo
que la fila seleccionada era la más difícil de leer de la pantalla. Ahora el
foco usa el ámbar de acento en los dos casos y lo que distingue al bloqueado es
el icono y el contador de progreso, no un color ilegible.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pygame

from src.engine.core import settings
from src.engine.core.achievements import AchievementSystem, esta_oculta
from src.engine.scene.base_scene import BaseScene
from src.engine.ui.theme import Theme, font
from src.engine.ui.widgets import (
    MenuItem,
    MenuList,
    draw_key_hints,
    draw_screen,
    handle_menu_navigation,
)

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext

def y_de_la_descripcion() -> int:
    """Dónde va la descripción del logro enfocado: bajo su nombre."""
    return font(Theme.FONT_SMALL).get_linesize()


def alto_de_fila() -> int:
    """AUD-187 — el alto sale de la fuente, no de un número escrito a mano.

    Antes era `ROW_HEIGHT = 22`, y la fuente de la fila mide exactamente 22 px
    de interlineado: las filas se tocaban, sin un píxel de aire, y con el texto
    ampliado por accesibilidad (AUD-126) pasaban a pisarse. Una lista sin aire
    entre filas se lee como un bloque y el ojo no encuentra dónde empieza cada
    una.

    Reserva **dos** líneas porque el logro enfocado despliega su descripción
    debajo, que es lo que el comentario original ya pedía —«la separación tiene
    que dar cabida a dos líneas sin solaparse»— y los 22 px no daban.
    """
    return (y_de_la_descripcion()
            + font(Theme.FONT_TINY).get_linesize()
            + Theme.SPACE_S)


class AchievementScene(BaseScene):
    """Pantalla de logros con progreso por cada uno."""

    def __init__(self, context: GameContext) -> None:
        super().__init__(context)
        self._menu = MenuList(items=[])
        self._scroll_offset: int = 0

    def on_enter(self) -> None:
        self._refresh()
        self._scroll_offset = 0
        self.context.scene_manager.transition.start_fade_in(0.5)

    def on_exit(self) -> None:
        pass

    def _refresh(self) -> None:
        """Reconstruye las filas desde el sistema de logros.

        Antes se pedía la lista completa dos veces por fotograma —una en
        `update` y otra en `draw`—. Los logros sólo cambian cuando se
        desbloquea uno, así que basta con leerlos al entrar.
        """
        achievements = AchievementSystem.get_instance().get_all_achievements()
        # AUD-198 — las medallas secretas se quedan fuera de la lista mientras
        # estén bloqueadas: un logro oculto no debe delatar su existencia
        # (ni su descripción) antes de desbloquearse.
        self._menu.items = [
            MenuItem(definition.name, value=(definition, progress),
                     hint=definition.description)
            for definition, progress in achievements
            if not esta_oculta(definition, progress)
        ]
        self._menu.ensure_valid()

    def update(self, dt: float) -> None:
        self._menu.update(dt)
        handle_menu_navigation(
            self._menu, self.input, on_cancel=self._back_to_title,
        )

        visible = max(1, (settings.INTERNAL_HEIGHT - 100) // alto_de_fila())
        if self._menu.index < self._scroll_offset:
            self._scroll_offset = self._menu.index
        elif self._menu.index >= self._scroll_offset + visible:
            self._scroll_offset = self._menu.index - visible + 1

    def _back_to_title(self) -> None:
        from src.engine.scenes.title_scene import TitleScene

        self.context.scene_manager.transition.start_fade_out(0.4)
        self.context.scene_manager.replace(TitleScene(self.context))

    def draw(self, surface: pygame.Surface) -> None:
        unlocked = sum(
            1 for item in self._menu.items if item.value[1].unlocked
        )
        top = draw_screen(
            surface, "LOGROS",
            f"{unlocked} de {len(self._menu.items)} desbloqueados",
        )

        row_font = font(Theme.FONT_SMALL)
        for i, item in enumerate(self._menu.items):
            if i < self._scroll_offset:
                continue
            y = top + (i - self._scroll_offset) * alto_de_fila()
            if y > settings.INTERNAL_HEIGHT - 60:
                break
            self._draw_row(surface, row_font, item, i, y)

        draw_key_hints(surface, [
            ("↑↓", "Navegar"),
            ("Esc", "Volver"),
        ])
        self.context.scene_manager.transition.draw(surface)

    def _draw_row(
        self, surface: pygame.Surface, row_font: pygame.font.Font,
        item: MenuItem, index: int, y: int,
    ) -> None:
        definition, progress = item.value
        focused = index == self._menu.index

        if focused:
            # Ámbar tanto si está desbloqueado como si no: el estado se lee en
            # el icono y el progreso, no en un gris que no se ve.
            colour = Theme.ACCENT
        elif progress.unlocked:
            colour = Theme.TEXT
        else:
            colour = Theme.TEXT_DIM

        if focused:
            cursor = row_font.render("›", True, Theme.ACCENT)
            surface.blit(cursor, (Theme.MARGIN - Theme.SPACE_S, y))

        icon = "★" if progress.unlocked else "☆"
        suffix = (
            "" if progress.unlocked
            else f"  [{progress.current}/{definition.target}]"
        )
        label = row_font.render(
            f"{icon}  {definition.name}{suffix}", True, colour,
        )
        surface.blit(label, (Theme.MARGIN, y))

        if focused and definition.description:
            description = font(Theme.FONT_TINY).render(
                definition.description, True, Theme.TEXT_MUTED,
            )
            surface.blit(description,
                         (Theme.MARGIN + Theme.SPACE_M,
                          y + y_de_la_descripcion()))
