"""
Module: stage_error_scene
System: engine.scenes
Academic Unit: N/A

Pantalla que muestra por qué un escenario no pudo cargarse.

Por qué existe (AUD-055)
------------------------
Cuando `StageLoader` lanzaba `FrameworkUsageError`, `App.run` lo registraba en
el log y llamaba a `_fallback_to_title()`. Desde el asiento del estudiante eso
se ve así: ejecuta el juego, aparece un instante de negro y vuelve al menú
principal. Sin mensaje, sin pista, sin nada que leer.

El diagnóstico existía —estaba en el log, un archivo que nadie mira mientras
diseña un nivel— pero no llegaba a la persona que podía actuar sobre él. Un
error que no se ve equivale a un error que no se explicó.

Esta escena pone el informe en pantalla, que es donde el estudiante ya está
mirando. `R` recarga sin reiniciar el juego: se corrige el mapa en Tiled, se
guarda y se pulsa `R`. Ese ciclo —ver el error, arreglarlo, verificar— es la
diferencia entre una herramienta que enseña y una que castiga.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

import pygame

from src.engine.core import settings
from src.engine.scene.base_scene import BaseScene
from src.engine.ui.theme import Theme, font
from src.engine.ui.widgets import draw_key_hints, draw_screen

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext


#: Cuántas líneas caben antes de tener que desplazar. Se calcula al dibujar,
#: pero el mínimo evita divisiones raras en resoluciones muy pequeñas.
_MIN_VISIBLE_LINES = 4


class StageErrorScene(BaseScene):
    """Muestra un error de carga de escenario y permite reintentar.

    Recibe un `retry` opcional en lugar de la escena a recrear: la escena que
    falló puede necesitar argumentos que esta pantalla no conoce, y pedírselos
    la acoplaría a cada escenario del juego. Quien la construye sabe cómo
    reconstruir lo que falló; aquí sólo se sabe cuándo hacerlo.
    """

    def __init__(
        self,
        context: GameContext,
        message: str,
        *,
        title: str = "NO SE PUDO CARGAR EL ESCENARIO",
        retry: Callable[[], None] | None = None,
    ) -> None:
        super().__init__(context)
        # Se acepta cualquier cosa y se convierte: quien llama suele tener una
        # excepción en la mano, y obligarle a recordar el `str()` sólo sirve
        # para que un `AttributeError` sustituya al mensaje que se quería leer.
        message = str(message)
        self._message = message
        self._title = title
        self._retry = retry
        self._lines: list[str] = message.splitlines() or ["(sin detalles)"]
        self._scroll = 0
        self._visible_lines = _MIN_VISIBLE_LINES

    # ── Ciclo de vida ──────────────────────────────────────────

    def on_enter(self) -> None:
        self._scroll = 0

    def on_exit(self) -> None:
        pass

    def update(self, dt: float) -> None:
        pass

    # ── Entrada ────────────────────────────────────────────────

    def process_events(self, events: list[pygame.event.Event]) -> None:
        for event in events:
            if event.type != pygame.KEYDOWN:
                continue
            if event.key in (pygame.K_DOWN, pygame.K_s):
                self._scroll_by(1)
            elif event.key in (pygame.K_UP, pygame.K_w):
                self._scroll_by(-1)
            elif event.key == pygame.K_PAGEDOWN:
                self._scroll_by(self._visible_lines)
            elif event.key == pygame.K_PAGEUP:
                self._scroll_by(-self._visible_lines)
            elif event.key == pygame.K_r and self._retry is not None:
                self._retry()
            elif event.key == pygame.K_ESCAPE:
                self._go_to_title()

    def _scroll_by(self, amount: int) -> None:
        largest = max(0, len(self._lines) - self._visible_lines)
        self._scroll = max(0, min(largest, self._scroll + amount))

    def _go_to_title(self) -> None:
        from src.engine.scenes.title_scene import TitleScene

        self.context.scene_manager.replace(TitleScene(self.context))

    # ── Dibujo ─────────────────────────────────────────────────

    def draw(self, surface: pygame.Surface) -> None:
        top = draw_screen(surface, self._title, "Revisa el mapa en Tiled")

        body = font(Theme.FONT_SMALL)
        line_height = body.get_height() + 2
        footer_room = Theme.SPACE_XL + Theme.SPACE_M
        available = settings.INTERNAL_HEIGHT - top - footer_room
        self._visible_lines = max(_MIN_VISIBLE_LINES, available // line_height)

        # Barra de acento a la izquierda: marca el bloque entero como el
        # mensaje del error, en vez de dejar el texto suelto sobre el fondo.
        block_height = min(len(self._lines), self._visible_lines) * line_height
        pygame.draw.rect(
            surface, Theme.DANGER,
            (Theme.MARGIN - Theme.SPACE_S, top, 2, block_height),
        )

        y = top
        end = self._scroll + self._visible_lines
        for raw in self._lines[self._scroll:end]:
            colour = Theme.TEXT_MUTED if raw.startswith("  ") else Theme.TEXT
            if "¿quisiste decir" in raw:
                # La sugerencia es lo accionable de todo el informe.
                colour = Theme.ACCENT
            surface.blit(body.render(raw[:96], True, colour), (Theme.MARGIN, y))
            y += line_height

        if len(self._lines) > self._visible_lines:
            shown = min(end, len(self._lines))
            marker = font(Theme.FONT_TINY).render(
                f"{shown}/{len(self._lines)} líneas", True, Theme.TEXT_DIM,
            )
            surface.blit(
                marker,
                (settings.INTERNAL_WIDTH - Theme.MARGIN - marker.get_width(), y),
            )

        hints = [("↑↓", "Desplazar"), ("Esc", "Menú")]
        if self._retry is not None:
            hints.insert(0, ("R", "Reintentar"))
        draw_key_hints(surface, hints)
