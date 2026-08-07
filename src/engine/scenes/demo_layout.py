"""
Module: demo_layout
Description: Resolution-responsive layout constants and drawing helpers
shared by all academic demonstration scenes.

All constants are computed from settings.INTERNAL_WIDTH and
settings.INTERNAL_HEIGHT so the UI adapts to any resolution.
Minimum tested: 800x600.
"""
from __future__ import annotations

import pygame

from src.engine.core import settings
from src.engine.ui.theme import Theme
from src.engine.utils.asset_loader import AssetLoader

# ── Computed Layout Constants ──────────────────────────────────────
# These scale with INTERNAL_WIDTH and INTERNAL_HEIGHT.
#
# AUD-312: aquí había un `_env_int()` y un comentario que prometía «override
# via env vars: LOI_TOP_BAR_H=40 LOI_PANEL_W=300». Ni la función tenía un solo
# llamante ni ninguna de las constantes de abajo consultaba el entorno: se
# calculan de `settings` y ya está. `75_BIBLIA_TECNICA.md` documentaba esas dos
# variables como si funcionaran, así que la promesa había llegado a un
# documento — que es como una función muerta acaba costando el tiempo de
# alguien que intenta usarla.
#
# Retirados los dos. Si algún día hace falta ajustar el kit de demos desde
# fuera, se escribe entonces y con su llamante.

# Top bar: 5% of height, min 28px, max 48px
TOP_BAR_H: int = max(28, min(48, int(settings.INTERNAL_HEIGHT * 0.055)))
# Bottom bar: 4% of height, min 20px, max 32px
BOTTOM_BAR_H: int = max(20, min(32, int(settings.INTERNAL_HEIGHT * 0.04)))
# Panel width (AUD-094): los dos paneles se reparten el ancho dejando una
# canaleta entre ellos.
#
# Antes esto era `INTERNAL_WIDTH * 0.32`, un 32 % heredado de cuando había
# tres columnas. Con dos paneles sobre 800 px daba 256 de panel y **288 de
# hueco central**: el vacío era más ancho que cada panel. Medido con una
# rejilla de 3x3 sobre el área útil, cuatro demos —filtros, visión, patrones
# y el constructor de tuberías— daban el patrón `#.#/#.#/#.#`: contenido en
# los bordes, columna central muerta. Es la mitad de la queja «la imagen no
# está centrada»: no es que estuviera descentrada, es que estaban las dos
# empujadas contra los bordes.
#
# La canaleta se fija en píxeles y no en porcentaje porque separa dos
# imágenes que se comparan una junto a otra: lo que hace falta es un borde
# visible, no una proporción.
PANEL_GUTTER: int = 24
PANEL_W: int = max(200, (settings.INTERNAL_WIDTH - PANEL_GUTTER) // 2)
LEFT_PANEL_W: int = PANEL_W
RIGHT_PANEL_W: int = PANEL_W
# Panel height: fill space between top bar and bottom bar minus reserves
_RESERVE_Y: int = max(60, int(settings.INTERNAL_HEIGHT * 0.10))
PANEL_H: int = max(180, settings.INTERNAL_HEIGHT - TOP_BAR_H - BOTTOM_BAR_H - _RESERVE_Y)

TOP_BAR_Y: int = 0
LEFT_PANEL_X: int = 0
LEFT_PANEL_Y: int = TOP_BAR_H
RIGHT_PANEL_X: int = settings.INTERNAL_WIDTH - RIGHT_PANEL_W
RIGHT_PANEL_Y: int = TOP_BAR_H
BOTTOM_BAR_Y: int = settings.INTERNAL_HEIGHT - BOTTOM_BAR_H

PANEL_SIZE: tuple[int, int] = (PANEL_W, PANEL_H)

# Center area (between panels) for controls/info
CENTER_X: int = LEFT_PANEL_W + 8
CENTER_W: int = max(100, RIGHT_PANEL_X - LEFT_PANEL_W - 16)

# ── Área útil y lienzo de autoría (AUD-094) ────────────────────────
#
# El problema medido
# ------------------
# Las demos académicas se escribieron cuando la resolución interna era
# 320x224 y nunca se migraron a 800x600. Sus coordenadas están puestas a
# mano: `center = (160, 100)` en el laboratorio de transformaciones,
# `x = 20; y = 40` en el de combos, un tarjetón de color de 312 px de ancho
# en el de teoría del color. Medido sobre la pantalla real:
#
#   TransformLabScene   contenido en x[4,247] y[33,199]   centroide desviado (-312,-196)
#   ComboDemoScene      contenido en x[20,273] y[43,238]  centroide desviado (-308,-187)
#   VectorLabScene      contenido en x[8,379] y[40,159]   centroide desviado (-286,-212)
#
# Es decir: el elemento que el estudiante manipula vive en el cuadrante
# superior izquierdo y las tres cuartas partes de la pantalla están vacías.
# Es el mismo defecto que AUD-093 en el mapa del mundo, en otras trece
# pantallas.
#
# La solución
# -----------
# No reescribir a mano los cientos de números de las trece escenas: eso es
# donde se introducen los errores. En su lugar, un lienzo que traduce las
# coordenadas de autoría (320x224) al área útil real, escalando de forma
# uniforme y centrando el sobrante. La escena sigue razonando en el sistema
# en el que fue escrita —que además es el que aparece en la pizarra cuando
# se explica una transformación afín— y el lienzo se ocupa del resto.
#
# El texto no se escala: las fuentes ya se calculan desde INTERNAL_WIDTH y
# están a su tamaño correcto. Lo que se escala es la geometría, que es lo
# que estaba encogido.

#: Área entre la barra superior y la inferior. Todo lo que dibuja una demo
#: cabe aquí; fuera queda tapado por las barras.
CONTENT_X: int = 0
CONTENT_Y: int = TOP_BAR_H
CONTENT_W: int = settings.INTERNAL_WIDTH
CONTENT_H: int = max(1, BOTTOM_BAR_Y - TOP_BAR_H)

#: Tamaño para el que se escribieron las demos originalmente.
AUTHORED_W: int = 320
AUTHORED_H: int = 224


def area_de_contenido() -> pygame.Rect:
    """El rectángulo utilizable, sin las barras."""
    return pygame.Rect(CONTENT_X, CONTENT_Y, CONTENT_W, CONTENT_H)


def centrar_bloque(ancho: int, alto: int) -> tuple[int, int]:
    """Esquina superior izquierda para que un bloque quede centrado."""
    area = area_de_contenido()
    return (area.x + (area.w - ancho) // 2, area.y + (area.h - alto) // 2)


#: Cuánto puede desviarse del centro el elemento principal de una demo, en
#: fracción del ancho útil. No es cero porque varias escenas ponen a un lado
#: una columna de lecturas numéricas —la matriz, las componentes del
#: vector— y el elemento se corre para dejarle sitio. Sí es lo bastante
#: estrecho para que un elemento pegado a la esquina no pase: antes de
#: AUD-094 las desviaciones iban del 22 % al 34 %.
TOLERANCIA_CENTRADO: float = 0.20
#: Fracción mínima del área útil que debe ocupar el elemento principal.
OCUPACION_MINIMA: float = 0.30


def esta_centrado(rect: pygame.Rect, tolerancia: float = TOLERANCIA_CENTRADO) -> bool:
    """¿Está este rectángulo lo bastante centrado en el área útil?

    Se comprueba sólo el eje horizontal a propósito: en vertical casi todas
    las demos reservan una banda arriba para el rótulo y otra abajo para las
    lecturas, y exigir simetría vertical obligaría a rellenar con vacío.
    """
    area = area_de_contenido()
    return abs(rect.centerx - area.centerx) <= area.w * tolerancia


def area_con_columna(ancho_columna: int) -> tuple[pygame.Rect, pygame.Rect]:
    """Parte el área útil en una columna de texto y un escenario.

    Devuelve ``(columna, escenario)``. Varias demos escriben lecturas
    numéricas —matrices, componentes de un vector, pasos de una conversión de
    color— junto a la figura que el estudiante manipula. Antes se apilaban
    ambas en la esquina; así el texto tiene su sitio y la figura el suyo.
    """
    area = area_de_contenido()
    ancho_columna = max(0, min(ancho_columna, area.w - 120))
    columna = pygame.Rect(area.x, area.y, ancho_columna, area.h)
    escenario = pygame.Rect(
        area.x + ancho_columna, area.y, area.w - ancho_columna, area.h,
    )
    return (columna, escenario)


class Lienzo:
    """Traduce coordenadas de autoría al área útil, escaladas y centradas.

    ``Lienzo(320, 224)`` sobre una pantalla de 800x600 da escala 2.42 y
    márgenes de 12 px a los lados: lo que antes ocupaba una esquina pasa a
    llenar la pantalla.

    Se escala de forma **uniforme** —el mismo factor en las dos dimensiones—
    porque estas escenas enseñan geometría: un círculo tiene que seguir
    siendo un círculo y una rotación tiene que conservar los ángulos. Un
    escalado no uniforme convertiría la lección en una mentira.
    """

    __slots__ = ("alto", "ancho", "escala", "x0", "y0")

    def __init__(
        self, ancho: int = AUTHORED_W, alto: int = AUTHORED_H,
        margen: int = 8, escala_maxima: float = 4.0,
        area: pygame.Rect | None = None,
    ) -> None:
        self.ancho = max(1, ancho)
        self.alto = max(1, alto)
        area = area_de_contenido() if area is None else area
        disponible_w = max(1, area.w - margen * 2)
        disponible_h = max(1, area.h - margen * 2)
        self.escala = min(
            disponible_w / self.ancho, disponible_h / self.alto, escala_maxima,
        )
        usado_w = self.ancho * self.escala
        usado_h = self.alto * self.escala
        self.x0 = area.x + (area.w - usado_w) / 2.0
        self.y0 = area.y + (area.h - usado_h) / 2.0

    # -- traducción ------------------------------------------------
    def x(self, valor: float) -> int:
        return int(self.x0 + valor * self.escala)

    def y(self, valor: float) -> int:
        return int(self.y0 + valor * self.escala)

    def p(self, x: float, y: float) -> tuple[int, int]:
        """Un punto de autoría en coordenadas de pantalla."""
        return (self.x(x), self.y(y))

    def l(self, valor: float) -> int:  # noqa: E743 - 'l' de longitud, se usa mucho
        """Una longitud (radio, grosor, ancho) escalada, mínimo 1."""
        return max(1, round(valor * self.escala))

    def r(self, x: float, y: float, w: float, h: float) -> pygame.Rect:
        """Un rectángulo de autoría en coordenadas de pantalla."""
        return pygame.Rect(self.x(x), self.y(y), self.l(w), self.l(h))

    def rect(self) -> pygame.Rect:
        """El lienzo entero, ya en pantalla."""
        return pygame.Rect(
            int(self.x0), int(self.y0),
            int(self.ancho * self.escala), int(self.alto * self.escala),
        )

    def inverso(self, sx: float, sy: float) -> tuple[float, float]:
        """De pantalla a autoría. Para el ratón."""
        if self.escala <= 0:
            return (sx, sy)
        return ((sx - self.x0) / self.escala, (sy - self.y0) / self.escala)

# ── Colours ────────────────────────────────────────────────────
#
# AUD-044: these were hand-picked literals that happened to be *close to* the
# menu palette without matching it — the labs used (10, 10, 30) for their
# background while menus used five other near-blacks, so moving from the title
# screen into a lab produced a visible, unexplained shift in tone.
#
# The names are kept so the eighteen lab scenes need no edits; the values now
# come from engine.ui.theme, which is the single source of truth. Change the
# theme and every lab follows.
COLOR_BG = Theme.BG
COLOR_TOP_BAR_BG = Theme.SURFACE
COLOR_BOTTOM_BAR_BG = Theme.SURFACE
COLOR_DIVIDER = Theme.BORDER
COLOR_TEXT = Theme.TEXT
COLOR_HIGHLIGHT = Theme.ACCENT
COLOR_ACCENT = (108, 172, 255)   # informational blue: labs only, never focus
COLOR_ERROR = Theme.DANGER
COLOR_GOLD = Theme.ACCENT

# Font sizes — scale with resolution, floored at the theme's type scale so a
# small window never renders text below the legibility threshold.
FONT_SMALL: int = max(Theme.FONT_TINY, settings.INTERNAL_WIDTH // 55)
FONT_MEDIUM: int = max(Theme.FONT_SMALL, settings.INTERNAL_WIDTH // 42)
FONT_LARGE: int = max(Theme.FONT_BODY, settings.INTERNAL_WIDTH // 35)

# Shared font cache
_FONT_CACHE: dict[int, pygame.font.Font] = {}

# ── Public: re-export everything that demo_common exposes ──────────
__all__ = [
    "AUTHORED_H",
    "AUTHORED_W",
    "BOTTOM_BAR_H",
    "BOTTOM_BAR_Y",
    "CENTER_W",
    "CENTER_X",
    "COLOR_ACCENT",
    "COLOR_BG",
    "COLOR_BOTTOM_BAR_BG",
    "COLOR_DIVIDER",
    "COLOR_ERROR",
    "COLOR_GOLD",
    "COLOR_HIGHLIGHT",
    "COLOR_TEXT",
    "COLOR_TOP_BAR_BG",
    "CONTENT_H",
    "CONTENT_W",
    "CONTENT_X",
    "CONTENT_Y",
    "FONT_LARGE",
    "FONT_MEDIUM",
    "FONT_SMALL",
    "LEFT_PANEL_W",
    "LEFT_PANEL_X",
    "LEFT_PANEL_Y",
    "PANEL_H",
    "PANEL_SIZE",
    "PANEL_W",
    "RIGHT_PANEL_W",
    "RIGHT_PANEL_X",
    "RIGHT_PANEL_Y",
    "TOP_BAR_H",
    "TOP_BAR_Y",
    "Lienzo",
    "draw_bottom_bar",
    "draw_bottom_bar_error",
    "draw_divider",
    "draw_histogram_bars",
    "draw_panel_border",
    "draw_save_notification",
    "draw_top_bar",
]


def clear_demo_font_cache() -> None:
    _FONT_CACHE.clear()


def _get_demo_font(size: int) -> pygame.font.Font:
    key = size
    if key not in _FONT_CACHE:
        _FONT_CACHE[key] = AssetLoader.load_font(
            settings.ASSETS_DIR / "fonts" / "game.ttf", size)
    return _FONT_CACHE[key]


def draw_top_bar(surface: pygame.Surface, title: str, unit: str) -> None:
    pygame.draw.rect(surface, COLOR_TOP_BAR_BG,
                     (0, TOP_BAR_Y, settings.INTERNAL_WIDTH, TOP_BAR_H))
    fnt = _get_demo_font(FONT_MEDIUM)
    ts = fnt.render(f"  {title}", True, COLOR_HIGHLIGHT)
    surface.blit(ts, (8, TOP_BAR_Y + (TOP_BAR_H - ts.get_height()) // 2))
    ts2 = fnt.render(f"{unit}  ", True, COLOR_ACCENT)
    tw = ts2.get_width()
    surface.blit(ts2, (settings.INTERNAL_WIDTH - tw - 8, TOP_BAR_Y + (TOP_BAR_H - ts2.get_height()) // 2))


def draw_bottom_bar(surface: pygame.Surface, text: str) -> None:
    pygame.draw.rect(surface, COLOR_BOTTOM_BAR_BG,
                     (0, BOTTOM_BAR_Y, settings.INTERNAL_WIDTH, BOTTOM_BAR_H))
    fnt = _get_demo_font(FONT_SMALL)
    ts = fnt.render(text, True, COLOR_TEXT)
    surface.blit(ts, (8, BOTTOM_BAR_Y + (BOTTOM_BAR_H - ts.get_height()) // 2))


def draw_bottom_bar_error(surface: pygame.Surface, error: str) -> None:
    pygame.draw.rect(surface, (40, 10, 10),
                     (0, BOTTOM_BAR_Y, settings.INTERNAL_WIDTH, BOTTOM_BAR_H))
    fnt = _get_demo_font(FONT_SMALL)
    ts = fnt.render(error, True, COLOR_ERROR)
    surface.blit(ts, (8, BOTTOM_BAR_Y + (BOTTOM_BAR_H - ts.get_height()) // 2))


def draw_panel_border(surface: pygame.Surface, panel_rect: pygame.Rect) -> None:
    pygame.draw.rect(surface, COLOR_DIVIDER, panel_rect, 1)


def draw_divider(surface: pygame.Surface) -> None:
    pygame.draw.line(surface, COLOR_DIVIDER, (LEFT_PANEL_W, TOP_BAR_Y), (LEFT_PANEL_W, TOP_BAR_Y + PANEL_H), 1)
    pygame.draw.line(surface, COLOR_DIVIDER,
                     (RIGHT_PANEL_X, TOP_BAR_Y), (RIGHT_PANEL_X, TOP_BAR_Y + PANEL_H), 1)


def draw_save_notification(surface: pygame.Surface, saved_path: str, font: pygame.font.Font) -> None:
    ts = font.render(f"Saved: {saved_path}", True, COLOR_GOLD)
    surface.blit(ts, (8, BOTTOM_BAR_Y + 2))


def draw_histogram_bars(
    surface: pygame.Surface,
    rect: pygame.Rect,
    hist_r: list[int],
    hist_g: list[int],
    hist_b: list[int],
    bar_w: int = 2,
    max_h: int = 40,
) -> None:
    bar_area = pygame.Rect(rect.x, rect.y + rect.h - max_h - 2, rect.w, max_h + 2)
    pygame.draw.rect(surface, (5, 5, 15), bar_area)
    n = min(len(hist_r), bar_area.w // bar_w)
    if n == 0 or not hist_g or not hist_b:
        return
    step = len(hist_r) // n
    max_val = max(max(hist_r), max(hist_g), max(hist_b)) + 1
    for i in range(n):
        idx = i * step
        for channel, hist, color in [(0, hist_r, (255, 60, 60)),
                                     (1, hist_g, (60, 200, 60)),
                                     (2, hist_b, (60, 60, 255))]:
            h_val = int((hist[idx] / max_val) * max_h)
            if h_val > 0:
                bx = bar_area.x + i * bar_w + 1
                by = bar_area.bottom - 2 - channel * (max_h // 3 + 2) - h_val
                bw = max(bar_w - 2, 1)
                pygame.draw.rect(surface, color, (bx, by, bw, h_val))
