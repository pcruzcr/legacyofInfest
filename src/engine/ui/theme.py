"""
Module: theme
System: engine.ui
Academic Unit: N/A

Design tokens — the single source of truth for colour, spacing and type.

Why this exists (AUD-044)
-------------------------
Before this module, every scene invented its own visual language. A survey of
``src/engine/scenes/*.py`` found **six different background colours** all
meaning "dark backdrop"::

    (10, 10, 20)   (20, 20, 30)   (20, 20, 35)
    (15, 15, 40)   (15, 15, 25)   (10,  5, 20)

…and selection highlights, title sizes, margins and footer hints were
open-coded per file. The result is that moving between the title screen, the
options screen and a lab feels like moving between three different games, and a
change to the look requires editing thirty-four files.

Tokens, not literals. A scene asks for ``Theme.BG``, ``Theme.ACCENT`` or
``Theme.SPACE_M`` and inherits the game's identity for free.

The palette is derived from the HUD, which is the screen the player looks at
most and therefore the de-facto identity of the game: deep desaturated blues for
surfaces, warm amber for focus and highlights, red reserved exclusively for
damage and danger.
"""
from __future__ import annotations

from typing import Final

import pygame

RGB = tuple[int, int, int]
RGBA = tuple[int, int, int, int]


class Theme:
    """Design tokens. All values are constants; nothing here mutates."""

    # ── Surfaces ────────────────────────────────────────────────
    # A three-step depth ramp. Anything that sits "on top" uses the next step
    # up, which is what gives panels their sense of layering without borders.
    BG: Final[RGB] = (14, 15, 28)            # window background
    SURFACE: Final[RGB] = (24, 26, 44)       # panels, cards, list rows
    SURFACE_RAISED: Final[RGB] = (36, 39, 62)  # focused row, active tab
    OVERLAY: Final[RGBA] = (8, 9, 18, 200)   # modal scrim (pause, dialogs)

    # ── Lines ───────────────────────────────────────────────────
    BORDER: Final[RGB] = (60, 64, 96)
    BORDER_STRONG: Final[RGB] = (100, 106, 150)

    # ── Text ────────────────────────────────────────────────────
    # Three levels only. More than three and hierarchy stops reading.
    TEXT: Final[RGB] = (236, 238, 248)       # primary
    TEXT_MUTED: Final[RGB] = (154, 160, 190)  # secondary / help
    TEXT_DIM: Final[RGB] = (96, 102, 132)    # disabled / placeholder

    # ── Accent and state ────────────────────────────────────────
    # Amber carries focus and progress. It is the only colour used for "this is
    # where you are", so focus is never ambiguous.
    ACCENT: Final[RGB] = (255, 200, 90)
    ACCENT_DIM: Final[RGB] = (168, 130, 56)
    SUCCESS: Final[RGB] = (120, 220, 140)
    WARNING: Final[RGB] = (255, 176, 72)
    # Red is reserved for damage and danger. Never use it for focus or for a
    # merely-destructive menu item, or players learn to ignore it.
    DANGER: Final[RGB] = (238, 84, 76)

    # ── Spacing ─────────────────────────────────────────────────
    # A 4px base scale. Every margin and gap in the game is one of these, which
    # is what makes unrelated screens feel like the same product.
    SPACE_XS: Final[int] = 4
    SPACE_S: Final[int] = 8
    SPACE_M: Final[int] = 16
    SPACE_L: Final[int] = 24
    SPACE_XL: Final[int] = 40

    # Distance from the screen edge to any content. Generous on purpose: the
    # game renders at 800x600 and is upscaled, so edge crowding reads as sloppy.
    MARGIN: Final[int] = 32

    # ── Type scale ──────────────────────────────────────────────
    FONT_TITLE: Final[int] = 34
    FONT_HEADING: Final[int] = 24
    FONT_BODY: Final[int] = 18
    FONT_SMALL: Final[int] = 15
    FONT_TINY: Final[int] = 13

    # ── Motion ──────────────────────────────────────────────────
    # Short enough to feel instant, long enough to be legible. Anything above
    # ~250 ms on a menu starts to feel unresponsive.
    FADE_FAST: Final[float] = 0.12
    FADE: Final[float] = 0.22
    CURSOR_PULSE_HZ: Final[float] = 1.6

    # ── Radii ───────────────────────────────────────────────────
    RADIUS: Final[int] = 4
    RADIUS_L: Final[int] = 8


_font_cache: dict[tuple[str | None, int], pygame.font.Font] = {}

#: Tamaño mínimo en píxeles. Por debajo de esto la fuente por defecto de
#: pygame deja de tener trazos distinguibles y el texto es una mancha.
_TAMANO_MINIMO: int = 8


def escalar_texto(size: int) -> int:
    """El tamaño pedido, multiplicado por la preferencia de accesibilidad.

    AUD-126 — por qué aquí y no en cada escena
    -------------------------------------------
    `font()` es el **único** sitio del proyecto por el que pasan todas las
    fuentes de la interfaz. Aplicar la escala aquí la aplica a las 34 escenas
    sin tocar ninguna, que es exactamente lo que consiguió alinear las 18
    demos cuando `demo_layout` pasó a derivar su paleta del tema.

    La alternativa —un parámetro `escala` en cada llamada— habría dependido de
    que 34 escenas se acordaran de pasarlo, y bastaría que una se olvidara para
    que el jugador que necesita el texto grande se encontrara una pantalla
    ilegible sin saber por qué.

    Si la preferencia no se puede leer se devuelve el tamaño original: el juego
    tiene que dibujar texto aunque la configuración esté rota.
    """
    from src.engine.core import user_settings

    escala = user_settings.preferencia("text_scale", 1.0)
    return max(_TAMANO_MINIMO, round(size * escala))


def font(size: int, path: str | None = None) -> pygame.font.Font:
    """Cached font lookup.

    Scenes previously constructed ``pygame.font.Font(None, N)`` in their own
    ``__init__``, rebuilding identical font objects on every scene
    construction. Caching by (path, size) means a menu transition reuses them.

    AUD-077 — la caché puede llenarse de cadáveres
    ----------------------------------------------
    Un ``pygame.font.Font`` deja de servir en cuanto alguien llama a
    ``pygame.quit()`` o ``pygame.font.quit()``. No se recupera: volver a
    inicializar el módulo devuelve ``get_init() is True`` pero el objeto viejo
    sigue lanzando ``pygame.error: Invalid font (font module quit since font
    created)`` para siempre. Y la comprobación anterior —``if not
    pygame.font.get_init()``— sólo se ejecutaba cuando la caché *fallaba*, así
    que jamás veía el problema: la caché acertaba, devolvía el cadáver, y la
    pantalla reventaba al primer ``render()``.

    Esto se descubrió midiendo, no leyendo: ``tests/test_student_template.py``
    apaga pygame después de cada prueba, y a partir de ahí toda pantalla que
    usara el kit de interfaz fallaba en la misma sesión de pytest. Lo mismo le
    pasaría al juego tras un cambio de modo de vídeo que reinicie el módulo.

    La validación cuesta 0,08 µs —menos que la propia búsqueda en el
    diccionario, 0,095 µs—, así que se hace en cada acierto de caché.
    """
    size = escalar_texto(size)
    key = (path, size)
    cached = _font_cache.get(key)
    if cached is not None:
        try:
            cached.get_height()
        except pygame.error:
            # El módulo de fuentes se apagó bajo nuestros pies: todo lo que
            # hay en la caché es basura, no sólo esta entrada.
            _font_cache.clear()
            cached = None
    if cached is None:
        if not pygame.font.get_init():
            pygame.font.init()
        cached = pygame.font.Font(path, size)
        _font_cache[key] = cached
    return cached


def clear_font_cache() -> None:
    """Drop cached fonts (test teardown, or after a display mode change)."""
    _font_cache.clear()


def pulse(elapsed: float, low: float = 0.55, high: float = 1.0) -> float:
    """A smooth 0-1 oscillation for focus indicators.

    Used so the selection cursor breathes rather than blinking. A hard blink
    draws the eye repeatedly and becomes tiring on a screen the player may sit
    on for a while; a slow sine is noticeable without being insistent.
    """
    import math

    phase = (math.sin(elapsed * Theme.CURSOR_PULSE_HZ * math.tau) + 1.0) * 0.5
    return low + (high - low) * phase


def with_alpha(color: RGB, alpha: int) -> RGBA:
    """Attach an alpha channel to an RGB token."""
    return (color[0], color[1], color[2], max(0, min(255, alpha)))
