"""
Module: widgets
System: engine.ui
Academic Unit: N/A

Shared UI building blocks: screen frame, menu list, panels, key hints.

Why this exists (AUD-045)
-------------------------
Every menu scene re-implemented the same four things by hand:

* a background fill and a title (in six different colours — see ``theme``),
* selection movement, always as ``(index ± 1) % len(options)``,
* a highlight for the focused row, each with its own colour and offset,
* a footer telling the player which keys do what — present on some screens,
  missing on others, worded differently on each.

Duplicated navigation is not just repetition; it is where inconsistency comes
from. ``(index + 1) % len`` wraps, ``min(index + 1, len - 1)`` clamps, and the
codebase had both — so moving down past the last item wrapped on one screen and
stopped on another. Players notice that even when they cannot name it.

These widgets own that behaviour once. A scene declares *what* its options are;
the widget decides how focus looks and moves.

Accessibility notes
-------------------
* Focus is never conveyed by colour alone. The focused row gets a raised
  background, a left cursor glyph **and** brighter text, so the screen stays
  usable with the colourblind filters enabled and at low contrast settings.
* Disabled rows are dimmed *and* skipped by navigation, so a player holding a
  direction never lands somewhere that does nothing.
* Every screen shows its key hints. Discoverability should not depend on the
  player guessing that Escape goes back.
"""
from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from typing import ClassVar

import pygame

from src.engine.core import settings
from src.engine.core.i18n import _
from src.engine.ui.theme import Theme, font, pulse, with_alpha


@dataclass
class MenuItem:
    """One row in a :class:`MenuList`.

    ``value`` lets a caller carry arbitrary payload (a scene key, an enum) so
    the scene does not need a parallel list to map index -> meaning, which is
    another place the old hand-rolled menus drifted out of sync.

    AUD-630 — accesibilidad: ``accessible_name`` es lo que un lector de
    pantalla anuncia cuando el foco llega a esta fila. Por defecto es la
    etiqueta + el hint (si existe), pero se puede sobreescribir para dar
    más contexto.
    """

    label: str
    value: object = None
    enabled: bool = True
    hint: str = ""
    # Rendered right-aligned on the row: the current value of a setting, a
    # completion percentage, a key binding.
    trailing: str = ""

    @property
    def accessible_name(self) -> str:
        """Lo que un lector de pantalla anuncia al enfocar esta fila."""
        if self.hint:
            return f"{self.label}. {self.hint}"
        return self.label


@dataclass
class MenuList:
    """A vertical list with focus, wrapping navigation and disabled rows."""

    items: list[MenuItem] = field(default_factory=list)
    index: int = 0
    _elapsed: float = 0.0
    #: AUD-446 — cuántas filas se ven a la vez. `None` las enseña todas, que
    #: es lo que quieren las listas cortas: los logros, el inventario o la
    #: tienda caben enteros y hacerlas desplazarse sólo escondería filas que
    #: hoy se ven. Se pone un número donde la lista es larga —el título tiene
    #: catorce opciones, 420 px de los 600 que hay— y entonces la lista se
    #: desliza para mantener la seleccionada dentro.
    visible_rows: int | None = None
    #: Desplazamiento actual, en filas. Es `float` porque se interpola.
    _desplazamiento: float = 0.0

    #: Cuánto del camino que falta se recorre por segundo. 12 da una respuesta
    #: que se siente inmediata sin que el ojo pierda de vista dónde estaba:
    #: llega en unos 250 ms.
    VELOCIDAD_DE_DESPLAZAMIENTO: ClassVar[float] = 12.0

    # ── navigation ──────────────────────────────────────────────

    def _step(self, direction: int) -> None:
        """Move focus, skipping disabled rows, wrapping at the ends.

        Wrapping (not clamping) is the deliberate choice: these lists are short,
        and wrapping means a player can reach the last item from the top with
        one press. The important part is that *every* list in the game now does
        the same thing.
        """
        if not self.items:
            return
        selectable = [i for i, item in enumerate(self.items) if item.enabled]
        if not selectable:
            return
        if self.index in selectable:
            position = selectable.index(self.index)
            self.index = selectable[(position + direction) % len(selectable)]
        else:
            self.index = selectable[0]

    def move_down(self) -> None:
        self._step(1)

    def move_up(self) -> None:
        self._step(-1)

    @property
    def current(self) -> MenuItem | None:
        if 0 <= self.index < len(self.items):
            return self.items[self.index]
        return None

    def ensure_valid(self) -> None:
        """Clamp focus into range after the item list changes.

        A save-slot list that shrinks while the player is on the last row would
        otherwise leave ``index`` past the end — an IndexError the moment they
        press Confirm.
        """
        if not self.items:
            self.index = 0
            return
        self.index = max(0, min(self.index, len(self.items) - 1))
        if not self.items[self.index].enabled:
            self._step(1)

    # ── la ventana de filas visibles (AUD-446) ──────────────────

    @property
    def desplazamiento(self) -> float:
        """Cuántas filas se han deslizado hacia arriba, ahora mismo."""
        return self._desplazamiento

    def _desplazamiento_deseado(self) -> float:
        """Dónde debería estar la ventana para que el foco se vea.

        Se centra el foco en la ventana y luego se acota a los extremos. Lo
        segundo importa tanto como lo primero: sin ello, al llegar al final de
        la lista la ventana seguiría bajando y dejaría filas vacías debajo.
        """
        if self.visible_rows is None:
            return 0.0
        maximo = max(0, len(self.items) - self.visible_rows)
        centrado = self.index - (self.visible_rows - 1) // 2
        return float(max(0, min(centrado, maximo)))

    def filas_visibles(self) -> list[int]:
        """Índices de las filas que se dibujan ahora mismo.

        Redondea el desplazamiento en curso: a mitad de la animación la
        ventana está entre dos filas, y lo que se pregunta aquí es qué se ve.
        """
        if self.visible_rows is None:
            return list(range(len(self.items)))
        primera = round(self._desplazamiento)
        primera = max(0, min(primera, max(0, len(self.items) - self.visible_rows)))
        return list(range(primera, min(primera + self.visible_rows, len(self.items))))

    def update(self, dt: float) -> None:
        self._elapsed += dt
        if self.visible_rows is None:
            return
        # AUD-446 — interpolación exponencial hacia el destino. Saltar de golpe
        # cuando el foco cruza el borde hace perder de vista dónde estabas: el
        # ojo no sigue un salto instantáneo de tres filas.
        objetivo = self._desplazamiento_deseado()
        avance = min(1.0, self.VELOCIDAD_DE_DESPLAZAMIENTO * max(0.0, dt))
        self._desplazamiento += (objetivo - self._desplazamiento) * avance
        # Sin esto la interpolación nunca termina del todo y la lista queda
        # temblando a una milésima de fila de su sitio.
        if abs(objetivo - self._desplazamiento) < 0.01:
            self._desplazamiento = objetivo

    # ── rendering ───────────────────────────────────────────────

    ROW_HEIGHT = 30

    def draw(
        self, surface: pygame.Surface, x: int, y: int, width: int,
        *, row_height: int | None = None,
    ) -> int:
        """Draw the list; returns the y coordinate just past the last row."""
        height = row_height or self.ROW_HEIGHT
        label_font = font(Theme.FONT_BODY)
        trail_font = font(Theme.FONT_SMALL)

        # AUD-446 — con ventana se recorta a lo que se ve y se desplaza el
        # origen. El recorte es lo que impide que la fila que está entrando
        # asome por encima del logo mientras se desliza.
        recorte_previo = surface.get_clip()
        desplazamiento_px = 0
        if self.visible_rows is not None:
            visibles = min(self.visible_rows, len(self.items))
            surface.set_clip(pygame.Rect(x, y, width, visibles * height))
            desplazamiento_px = round(self._desplazamiento * height)

        for i, item in enumerate(self.items):
            row = pygame.Rect(x, y + i * height - desplazamiento_px, width,
                              height - Theme.SPACE_XS)
            if self.visible_rows is not None and (
                row.bottom < y or row.top > y + self.visible_rows * height
            ):
                # Fuera de la ventana: ni se dibuja ni se paga su tipografía.
                continue
            focused = (i == self.index)

            if focused:
                # Raised surface + cursor + brighter text: three redundant
                # focus cues so none of them has to carry it alone.
                pygame.draw.rect(surface, Theme.SURFACE_RAISED, row,
                                 border_radius=Theme.RADIUS)
                accent = pygame.Rect(row.x, row.y, 3, row.height)
                intensity = pulse(self._elapsed)
                pygame.draw.rect(
                    surface,
                    tuple(int(c * intensity) for c in Theme.ACCENT),
                    accent, border_radius=1,
                )

            if not item.enabled:
                color = Theme.TEXT_DIM
            elif focused:
                color = Theme.ACCENT
            else:
                color = Theme.TEXT

            # AUD-321: el rótulo va por el catálogo, como el resto del kit.
            # El `value` se queda intacto: es la clave de ruteo, no texto.
            label = label_font.render(_(item.label), True, color)
            surface.blit(label, (row.x + Theme.SPACE_M, row.centery - label.get_height() // 2))

            if item.trailing:
                trailing = trail_font.render(
                    item.trailing, True,
                    Theme.TEXT_MUTED if not focused else Theme.TEXT,
                )
                surface.blit(
                    trailing,
                    (row.right - trailing.get_width() - Theme.SPACE_M,
                     row.centery - trailing.get_height() // 2),
                )

        # AUD-446 — se devuelve el recorte anterior pase lo que pase: dejarlo
        # puesto cortaría todo lo que se dibuje después —los avisos de abajo,
        # el logo— por una región que no es suya, y eso se ve como «desapareció
        # media pantalla».
        surface.set_clip(recorte_previo)
        if self.visible_rows is not None:
            return y + min(self.visible_rows, len(self.items)) * height
        return y + len(self.items) * height

    def draw_hint(self, surface: pygame.Surface, y: int) -> None:
        """Render the focused item's explanatory hint, if it has one."""
        item = self.current
        if item is None or not item.hint:
            return
        text = font(Theme.FONT_SMALL).render(_(item.hint), True, Theme.TEXT_MUTED)
        surface.blit(text, ((settings.INTERNAL_WIDTH - text.get_width()) // 2, y))


# ── screen furniture ─────────────────────────────────────────────


def draw_screen(surface: pygame.Surface, title: str, subtitle: str = "") -> int:
    """Paint the standard screen background and header.

    Returns the y coordinate where content should begin, so callers never
    hard-code a magic starting offset — which is how the old screens ended up
    with titles at y=14, y=20, y=40 and y=60.
    """
    surface.fill(Theme.BG)

    # F3.1: la traducción se hace **aquí**, en el kit, y no en cada escena.
    # Las treinta pantallas del juego pasan por `draw_screen`, así que
    # traducir en este punto las cubre todas sin tocar treinta archivos —y sin
    # que un estudiante que escriba una escena nueva tenga que acordarse de
    # envolver sus cadenas.
    title = _(title)
    subtitle = _(subtitle) if subtitle else subtitle

    y = Theme.MARGIN
    if title:
        label = font(Theme.FONT_TITLE).render(title, True, Theme.TEXT)
        surface.blit(label, ((settings.INTERNAL_WIDTH - label.get_width()) // 2, y))
        y += label.get_height() + Theme.SPACE_XS

    if subtitle:
        sub = font(Theme.FONT_SMALL).render(subtitle, True, Theme.TEXT_MUTED)
        surface.blit(sub, ((settings.INTERNAL_WIDTH - sub.get_width()) // 2, y))
        y += sub.get_height()

    # A hairline under the header anchors the title to the screen instead of
    # leaving it floating in space.
    y += Theme.SPACE_S
    pygame.draw.line(
        surface, Theme.BORDER,
        (Theme.MARGIN, y), (settings.INTERNAL_WIDTH - Theme.MARGIN, y),
    )
    return y + Theme.SPACE_L


def draw_panel(
    surface: pygame.Surface, rect: pygame.Rect, *,
    title: str = "", raised: bool = False,
) -> pygame.Rect:
    """Draw a titled panel; returns the rect available for its content."""
    fill = Theme.SURFACE_RAISED if raised else Theme.SURFACE
    pygame.draw.rect(surface, fill, rect, border_radius=Theme.RADIUS_L)
    pygame.draw.rect(surface, Theme.BORDER, rect, 1, border_radius=Theme.RADIUS_L)

    inner = rect.inflate(-Theme.SPACE_M * 2, -Theme.SPACE_M * 2)
    if title:
        label = font(Theme.FONT_SMALL).render(title.upper(), True, Theme.TEXT_MUTED)
        surface.blit(label, (inner.x, inner.y))
        inner.y += label.get_height() + Theme.SPACE_S
        inner.height -= label.get_height() + Theme.SPACE_S
    return inner


def draw_key_hints(surface: pygame.Surface, hints: Sequence[tuple[str, str]]) -> None:
    """Footer showing which keys do what, e.g. ``[("Enter", "Select")]``.

    Every screen gets one. Discoverability should not rest on the player
    guessing that Escape goes back — and several screens previously offered no
    hint at all, including the tutorial, which was the one place a new player is
    most likely to be lost.
    """
    if not hints:
        return
    key_font = font(Theme.FONT_TINY)
    gap = Theme.SPACE_M

    parts: list[tuple[pygame.Surface, pygame.Surface]] = []
    total = 0
    for key, action in hints:
        # La tecla no se traduce —«Esc» es «Esc» en los dos idiomas—; la
        # acción sí.
        action = _(action)
        k = key_font.render(f" {key} ", True, Theme.BG)
        a = key_font.render(action, True, Theme.TEXT_MUTED)
        parts.append((k, a))
        total += k.get_width() + Theme.SPACE_XS + a.get_width() + gap
    total -= gap

    x = (settings.INTERNAL_WIDTH - total) // 2
    y = settings.INTERNAL_HEIGHT - Theme.MARGIN

    for k, a in parts:
        cap = pygame.Rect(x, y - 2, k.get_width(), k.get_height() + 4)
        pygame.draw.rect(surface, Theme.TEXT_MUTED, cap, border_radius=Theme.RADIUS)
        surface.blit(k, (x, y))
        x += k.get_width() + Theme.SPACE_XS
        surface.blit(a, (x, y))
        x += a.get_width() + gap


def draw_modal_scrim(surface: pygame.Surface) -> None:
    """Dim everything behind a modal so the modal is unambiguously on top."""
    scrim = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    scrim.fill(Theme.OVERLAY)
    surface.blit(scrim, (0, 0))


def draw_progress_bar(
    surface: pygame.Surface, rect: pygame.Rect, fraction: float,
    *, color: tuple[int, int, int] | None = None, label: str = "",
) -> None:
    """A labelled progress/meter bar used by loading, XP and boss health."""
    fraction = max(0.0, min(1.0, fraction))
    pygame.draw.rect(surface, Theme.SURFACE, rect, border_radius=Theme.RADIUS)
    if fraction > 0:
        filled = pygame.Rect(rect.x, rect.y, int(rect.width * fraction), rect.height)
        pygame.draw.rect(surface, color or Theme.ACCENT, filled,
                         border_radius=Theme.RADIUS)
    pygame.draw.rect(surface, Theme.BORDER, rect, 1, border_radius=Theme.RADIUS)

    if label:
        text = font(Theme.FONT_TINY).render(label, True, Theme.TEXT)
        surface.blit(text, (rect.centerx - text.get_width() // 2,
                            rect.centery - text.get_height() // 2))


def draw_toast(
    surface: pygame.Surface, message: str, y: int,
    *, color: tuple[int, int, int] | None = None, alpha: int = 255,
) -> None:
    """A transient centred notification (item picked up, setting applied)."""
    text = font(Theme.FONT_SMALL).render(message, True, color or Theme.TEXT)
    box = pygame.Rect(0, 0, text.get_width() + Theme.SPACE_L,
                      text.get_height() + Theme.SPACE_S)
    box.centerx = settings.INTERNAL_WIDTH // 2
    box.y = y

    panel = pygame.Surface(box.size, pygame.SRCALPHA)
    panel.fill(with_alpha(Theme.SURFACE, min(alpha, 230)))
    surface.blit(panel, box.topleft)
    pygame.draw.rect(surface, Theme.BORDER, box, 1, border_radius=Theme.RADIUS)

    text.set_alpha(alpha)
    surface.blit(text, (box.centerx - text.get_width() // 2,
                        box.centery - text.get_height() // 2))


# ── standard navigation handling ─────────────────────────────────


def handle_menu_navigation(
    menu: MenuList, input_manager, *,
    on_confirm: Callable[[MenuItem], None] | None = None,
    on_cancel: Callable[[], None] | None = None,
) -> bool:
    """Apply the game-wide menu control scheme to ``menu``.

    One implementation means Up/Down/Confirm/Cancel behave identically on every
    screen, and a rebind in the options menu takes effect everywhere at once.
    Returns True if the input was consumed.
    """
    from src.engine.input.action_map import Action

    if input_manager is None:
        return False

    if input_manager.is_action_just_pressed(Action.MOVE_DOWN):
        menu.move_down()
        return True
    if input_manager.is_action_just_pressed(Action.MOVE_UP):
        menu.move_up()
        return True
    if input_manager.is_action_just_pressed(Action.CONFIRM):
        item = menu.current
        if item is not None and item.enabled and on_confirm is not None:
            on_confirm(item)
        return True
    if input_manager.is_action_just_pressed(Action.CANCEL):
        if on_cancel is not None:
            on_cancel()
        return True
    return False
