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

from src.engine.core import settings

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
    # Sombra de paneles (RGBA): se blit desplazada 3-4 px bajo el cuerpo.
    SHADOW: Final[tuple[int, int, int, int]] = (0, 0, 0, 110)

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
    # AUD-187: subida un escalón. La escala anterior —34/24/18/15/13— venía de
    # cuando la superficie interna era de 320x240; a los 800x600 actuales el
    # cuerpo de texto se quedaba pequeño y jugando cuesta leer los menús. Los
    # altos de fila del bestiario y de los logros salen ahora de la métrica de
    # la fuente, así que la escala puede moverse sin que nada se solape.
    FONT_TITLE: Final[int] = 38
    FONT_HEADING: Final[int] = 27
    FONT_BODY: Final[int] = 20
    FONT_SMALL: Final[int] = 17
    FONT_TINY: Final[int] = 15

    # ── Motion ──────────────────────────────────────────────────
    # Short enough to feel instant, long enough to be legible. Anything above
    # ~250 ms on a menu starts to feel unresponsive.
    FADE_FAST: Final[float] = 0.12
    FADE: Final[float] = 0.22
    CURSOR_PULSE_HZ: Final[float] = 1.6

    # ── Radii ───────────────────────────────────────────────────
    RADIUS: Final[int] = 4
    RADIUS_L: Final[int] = 8


#: Ancho para el que se dibujó la maqueta original de la interfaz — AUD-453.
#:
#: El juego se diseñó sobre una pantalla de 320×224 y pasó a 800×600 sin que
#: la interfaz se recolocara. AUD-451 lo encontró en el HUD; la misma huella
#: estaba en el cuadro de mensajes, en la franja del título de escenario y en
#: los subtítulos. Todos dibujaban números de la pantalla vieja **sin
#: escalar**, así que salían a menos de la mitad de su tamaño.
#:
#: Vive aquí y no en `hud` porque es un token de diseño, igual que los colores
#: y los espaciados: la relación entre la maqueta y la pantalla es de todos, y
#: tenerla en el HUD obligaba a los demás a importar del HUD para colocarse.
ANCHO_DE_DISENO: Final[int] = 320

#: La escala vigente. Se resuelve al importar porque la resolución interna es
#: una constante del motor, no una preferencia que cambie en caliente.
ESCALA_DE_INTERFAZ: Final[float] = settings.INTERNAL_WIDTH / ANCHO_DE_DISENO


def escalar(valor: int | float) -> int:
    """Un número de la maqueta original, llevado a la pantalla actual.

    Se calcula en vez de escribirse por lo que enseñó AUD-187 con el menú de
    título: una maqueta escrita en píxeles de una resolución concreta se queda
    obsoleta en silencio el día que la resolución cambia. Aquí pasaron
    800/320 = 2,5 veces sin que saltara nada.
    """
    return round(valor * ESCALA_DE_INTERFAZ)


def escalar_pixel_art(valor: int | float) -> int:
    """Escala para arte pixelado: entero, nearest, nunca smooth.

    Para tiles de 16x16 el escalado fraccional (2.5x) debe resolverse con
    ``pygame.transform.scale`` (vecino mas cercano), nunca ``smoothscale``
    que difumina el pixel art. Esta funcion devuelve el tamano escalado
    redondeado a entero para usar con ``scale``: el caller decide la
    superficie y el metodo, pero el valor viene de aqui para no repetir
    ``round(valor*ESCALA)`` a mano. Mantiene el estilo pixel a 800x600
    sin agregar biomas nuevos, solo mas detalle en los 4 zonas."""
    return round(valor * ESCALA_DE_INTERFAZ)


def escalar_suave(valor: int | float) -> int:
    """Escala para UI no-pixel (fuentes, barras degradadas): puede usar smooth.

    Separar ``escalar_pixel_art`` de ``escalar_suave`` evita que un futuro
    cambio en HUD use ``smoothscale`` por error sobre baldosas."""
    return round(valor * ESCALA_DE_INTERFAZ)


_font_cache: dict[tuple[str | None, int], pygame.font.Font] = {}

#: Centinela: `None` es una respuesta válida de `_tipografia_del_juego()` —
#: significa «no está el fichero, usa la de pygame»— así que no sirve para
#: marcar «aún no lo he mirado».
# AUD-371 — antes esto era un centinela `object()` con la caché anotada
# `object | str | None`. Funcionaba, y hacía que la función mintiera: su
# firma promete `str | None` y devolvía un tipo que incluye `object`, así
# que quien la llamara con el comprobador puesto veía un error donde no lo
# había. Una bandera separada dice lo mismo sin ensuciar el tipo de la
# caché, que es el valor que de verdad viaja.
_RUTA_JUEGO_CACHE: str | None = None
_RUTA_JUEGO_RESUELTA: bool = False

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


def _tipografia_del_juego() -> str | None:
    """La ruta de `game.ttf`, o `None` si no está y hay que caer a la de pygame.

    AUD-203 — por qué el kit no puede seguir con la tipografía por defecto
    ---------------------------------------------------------------------
    `pygame.font.Font(None, N)` no dibuja N píxeles de letra: entrega bastante
    menos tinta por punto pedido que un TTF normal. Medido a escala 1.0x con la
    palabra «Salud», alto real de la tinta:

    * `FONT_BODY` = 20 px  ->   9 px por defecto,  12 px con `game.ttf`
    * `FONT_TITLE` = 38 px ->  19 px por defecto,  21 px con `game.ttf`

    Esos 9 px del cuerpo convivían en el mismo juego con los **12 px** que
    `pygame_gui` dibuja en la pantalla de Opciones pidiendo 14 px. Un jugador
    que pasaba de Opciones a cualquier otra pantalla veía la letra encogerse un
    tercio sin haber tocado nada, y la queja fue literalmente que el texto del
    juego «ni se nota» al lado del de Opciones.

    `game.ttf` es la tipografía propia del proyecto y la pantalla de título ya
    la usaba directamente por su cuenta: el kit era el que iba por libre. Cierra
    el hueco con Opciones y **ocupa menos ancho** —un 16 % menos en «CONTINUAR
    PARTIDA»—, así que ninguna maqueta se desborda por el cambio.

    Si el fichero no está se devuelve `None` y se cae a la de pygame: el juego
    tiene que poder dibujar texto aunque falte un asset.
    """
    global _RUTA_JUEGO_CACHE, _RUTA_JUEGO_RESUELTA
    if not _RUTA_JUEGO_RESUELTA:
        from src.engine.core import settings

        ruta = settings.ASSETS_DIR / "fonts" / "game.ttf"
        _RUTA_JUEGO_CACHE = str(ruta) if ruta.is_file() else None
        _RUTA_JUEGO_RESUELTA = True
    return _RUTA_JUEGO_CACHE


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
    if path is None:
        path = _tipografia_del_juego()
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
