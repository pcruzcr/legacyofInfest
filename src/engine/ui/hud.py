"""
Module: hud
System: engine.ui
Description: Heads-Up Display showing hearts (health), timer, and stage info.
Uses sprite-based hearts from assets/ui/ with font fallback.
"""
from __future__ import annotations

import logging
import math
from typing import cast

import pygame

from src.engine.core import settings
from src.engine.core.event_bus import EventBus
from src.engine.core.events import Events
from src.engine.ui.theme import ANCHO_DE_DISENO as theme_ancho_de_diseno
from src.engine.ui.theme import ESCALA_DE_INTERFAZ, escalar, font
from src.engine.utils.asset_loader import AssetLoader

logger = logging.getLogger(__name__)

#: AUD-453 — la escala vive en `theme`, que es el módulo de los tokens de
#: diseño. Estaba aquí desde AUD-451, y eso obligaba al cuadro de mensajes, a
#: la franja del escenario y a los subtítulos a importar del HUD para
#: colocarse: una dependencia que no significa nada. Se reexporta con el
#: nombre de antes porque hay pruebas que lo nombran.
ANCHO_DE_DISENO = theme_ancho_de_diseno
ESCALA_DEL_HUD: float = ESCALA_DE_INTERFAZ

_e = escalar


def _rect_escalado(x: int, y: int, w: int, h: int) -> pygame.Rect:
    """Una región de la maqueta original, a escala."""
    return pygame.Rect(_e(x), _e(y), _e(w), _e(h))


# AUD-527 — decisión del dueño (2026-08-17, AUD-524): modernizar el HUD de
# verdad, rompiendo la convención de `docs/09_HUD_SPEC.md` §1 ("sin
# antialiasing, sin degradados, sin sombras mezcladas por alfa"). Las barras
# (especial, estamina, tiempo bala, vida de jefe) eran las últimas piezas que
# seguían siendo `pygame.draw.rect` a un color plano con un borde de 1 px —
# el propio lenguaje visual que la spec mandaba. `_relleno_redondeado` y
# `_dibujar_barra_moderna` son el reemplazo común a las cuatro: relleno con
# degradado, esquinas redondeadas, y un halo suave cuando la barra llega al
# tope. Vive aquí y no en `theme.py` porque hoy sólo lo usa el HUD; si otra
# pantalla necesita el mismo lenguaje, es cuando se mueve.
#
# AUD-527 (medido) — la primera versión reconstruía el degradado pixel a
# pixel (`pygame.draw.line` por columna) **cada fotograma y por cada
# barra**: `test_stage4_1.py::TestCabeEnElPresupuestoDeFotograma` lo cazó en
# 30 ms contra un presupuesto de 15. El ancho, el alto y los dos colores de
# cada barra son casi siempre los mismos fotograma a fotograma —sólo cambia
# `pct`—, así que el degradado a ancho completo se calcula una sola vez por
# combinación y se recorta con `subsurface` (una vista, no una copia) para
# el ancho de relleno de ese fotograma. La caché no tiene límite de tamaño
# a propósito: las claves posibles son un puñado de tamaños de barra fijos
# por un puñado de pares de color fijos, nunca crece sin cota.
_CACHE_RELLENOS: dict[
    tuple[int, int, int, tuple[int, int, int], tuple[int, int, int]], pygame.Surface,
] = {}


def _relleno_redondeado(
    w: int, h: int, radio: int, color_inicio: tuple[int, int, int],
    color_fin: tuple[int, int, int],
) -> pygame.Surface:
    """Degradado horizontal a ancho completo, con las cuatro esquinas ya
    redondeadas — cacheado, ver nota de arriba.

    Una barra parcial recorta una vista (`subsurface`) del lado izquierdo de
    este relleno: la esquina izquierda sale redondeada porque ya lo está en
    la imagen completa, y el borde derecho del recorte queda recto — que es
    exactamente cómo se lee el frente de una barra de progreso llenándose,
    no hace falta redondearlo también.
    """
    w, h = max(1, w), max(1, h)
    clave = (w, h, radio, color_inicio, color_fin)
    cacheado = _CACHE_RELLENOS.get(clave)
    if cacheado is not None:
        return cacheado
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    for x in range(w):
        t = x / max(1, w - 1)
        col = tuple(
            int(color_inicio[i] + (color_fin[i] - color_inicio[i]) * t)
            for i in range(3)
        )
        pygame.draw.line(surf, (*col, 255), (x, 0), (x, h - 1))
    mascara = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(mascara, (255, 255, 255, 255), mascara.get_rect(), border_radius=radio)
    surf.blit(mascara, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    _CACHE_RELLENOS[clave] = surf
    return surf


#: Fondo translúcido redondeado de una barra — mismo argumento de caché que
#: el relleno: tamaño y radio se repiten fotograma a fotograma.
_CACHE_PANELES: dict[tuple[int, int, int], pygame.Surface] = {}


def _panel_redondeado(w: int, h: int, radio: int) -> pygame.Surface:
    clave = (w, h, radio)
    cacheado = _CACHE_PANELES.get(clave)
    if cacheado is not None:
        return cacheado
    panel = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(panel, (18, 18, 30, 210), panel.get_rect(), border_radius=radio)
    _CACHE_PANELES[clave] = panel
    return panel


def _dibujar_barra_moderna(
    surface: pygame.Surface, rect: pygame.Rect, pct: float,
    color_inicio: tuple[int, int, int], color_fin: tuple[int, int, int],
    *, halo_al_llenar: bool = True,
) -> None:
    """Fondo translúcido redondeado + relleno con degradado + halo opcional.

    `pct` ya viene acotado a [0, 1] por quien llama — esta función sólo
    dibuja, no valida el dato del jugador.
    """
    radio = max(2, min(rect.height // 2, _e(4)))
    surface.blit(_panel_redondeado(rect.width, rect.height, radio), rect.topleft)

    if pct > 0.0:
        ancho_relleno = max(1, int(rect.width * pct))
        relleno_completo = _relleno_redondeado(
            rect.width, rect.height, radio, color_inicio, color_fin)
        surface.blit(relleno_completo.subsurface((0, 0, ancho_relleno, rect.height)),
                     rect.topleft)

        if halo_al_llenar and pct >= 1.0:
            m = _e(3)
            halo = pygame.Surface((rect.width + m * 2, rect.height + m * 2), pygame.SRCALPHA)
            pygame.draw.rect(halo, (*color_fin, 70), halo.get_rect(),
                             border_radius=radio + m)
            surface.blit(halo, (rect.x - m, rect.y - m), special_flags=pygame.BLEND_RGBA_ADD)

    pygame.draw.rect(surface, (*color_fin, 190), rect, width=1, border_radius=radio)


def _recortar_circular(surf: pygame.Surface) -> pygame.Surface:
    """AUD-535 — recorta `surf` a un círculo inscrito en su rectángulo.

    Se llama una sola vez por retrato al cargar (`__init__`), no en cada
    `draw()`: una máscara nueva por fotograma sería exactamente el error
    de rendimiento que AUD-527 ya cazó con el degradado de las barras.
    """
    w, h = surf.get_size()
    mascara = pygame.Surface((w, h), pygame.SRCALPHA)
    radio = min(w, h) // 2
    pygame.draw.circle(mascara, (255, 255, 255, 255), (w // 2, h // 2), radio)
    recortado = surf.copy()
    recortado.blit(mascara, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    return recortado


#: Anillo del retrato — un círculo, no el marco 9-slice rectangular de
#: antes. Cacheado por (radio, grosor, color): el retrato sólo cambia de
#: color con el estado del jugador (normal/hurt/critical/dead), un
#: puñado de combinaciones fijas.
_CACHE_ANILLOS: dict[tuple[int, int, tuple[int, int, int]], pygame.Surface] = {}


def _anillo_del_retrato(diametro: int, grosor: int, color: tuple[int, int, int]) -> pygame.Surface:
    clave = (diametro, grosor, color)
    cacheado = _CACHE_ANILLOS.get(clave)
    if cacheado is not None:
        return cacheado
    anillo = pygame.Surface((diametro, diametro), pygame.SRCALPHA)
    radio = diametro // 2
    pygame.draw.circle(anillo, (*color, 220), (radio, radio), radio, width=grosor)
    # Halo suave hacia afuera — el mismo lenguaje que ya usan las barras
    # al llenarse (AUD-527): un borde duro sobre un fondo oscuro se lee
    # como pixel art aunque el trazo esté antialiasado.
    halo = pygame.Surface((diametro, diametro), pygame.SRCALPHA)
    pygame.draw.circle(halo, (*color, 60), (radio, radio), radio, width=grosor + 2)
    anillo.blit(halo, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
    _CACHE_ANILLOS[clave] = anillo
    return anillo


#: Ícono del reloj — cacheado por (diámetro, color): sólo cambia entre
#: el color normal y el de alerta (AUD-535, "un ícono de reloj
#: estilizado" en vez del texto "TIME").
_CACHE_ICONOS_RELOJ: dict[tuple[int, tuple[int, int, int]], pygame.Surface] = {}


def _icono_de_reloj(diametro: int, color: tuple[int, int, int]) -> pygame.Surface:
    clave = (diametro, color)
    cacheado = _CACHE_ICONOS_RELOJ.get(clave)
    if cacheado is not None:
        return cacheado
    icono = pygame.Surface((diametro, diametro), pygame.SRCALPHA)
    radio = diametro // 2
    centro = (radio, radio)
    pygame.draw.circle(icono, color, centro, radio, width=max(1, diametro // 8))
    # Manecillas: la larga (minutero) hacia arriba, la corta (hora) hacia
    # la derecha — una pose fija y legible, no una hora real.
    grosor = max(1, diametro // 8)
    pygame.draw.line(icono, color, centro, (radio, max(1, radio - int(radio * 0.7))), grosor)
    pygame.draw.line(icono, color, centro, (radio + int(radio * 0.5), radio), grosor)
    _CACHE_ICONOS_RELOJ[clave] = icono
    return icono


#: Ícono de moneda del marcador — cacheado por (diámetro, color): un
#: disco con un brillo, no el glifo "¤" que la fuente no tiene (AUD-535).
_CACHE_ICONOS_MONEDA: dict[tuple[int, tuple[int, int, int]], pygame.Surface] = {}


def _icono_de_moneda(diametro: int, color: tuple[int, int, int]) -> pygame.Surface:
    clave = (diametro, color)
    cacheado = _CACHE_ICONOS_MONEDA.get(clave)
    if cacheado is not None:
        return cacheado
    icono = pygame.Surface((diametro, diametro), pygame.SRCALPHA)
    radio = diametro // 2
    pygame.draw.circle(icono, color, (radio, radio), radio)
    borde = (max(0, color[0] - 60), max(0, color[1] - 60), max(0, color[2] - 60))
    pygame.draw.circle(icono, borde, (radio, radio), radio, width=max(1, diametro // 8))
    if radio >= 3:
        pygame.draw.circle(icono, (255, 255, 255, 180),
                           (radio - radio // 3, radio - radio // 3), max(1, radio // 3))
    _CACHE_ICONOS_MONEDA[clave] = icono
    return icono


#: El hueco del minimapa, en coordenadas de la maqueta de 320 (AUD-499).
#:
#: Vive aquí y no en `minimap.py` porque el HUD es quien conoce la franja
#: entera: el minimapa solo no puede saber que el cronómetro ocupa el borde
#: derecho, que es exactamente lo que no sabía cuando se colocaba encima.
# AUD-547 — "circular de verdad", no un rectángulo de esquinas muy
# redondeadas: un círculo inscrito en un rectángulo no cuadrado recorta
# contenido de los lados largos y deja aire de los cortos, así que deja
# de leerse como un círculo — es exactamente el mismo razonamiento que
# ya se aplicó al retrato (círculo inscrito en un marco cuadrado). El
# minimapa pasa de 62×44 a 44×44 —el lado menor de antes— para que
# `minimap.py` pueda recortarlo con `pygame.draw.circle`, no con
# `border_radius`. El margen respecto al borde derecho de la pantalla
# usa la misma constante `MARGEN_DE_PANTALLA` que el resto del HUD
# (antes eran 4 px sueltos, un caso especial que nadie más seguía).
RECUADRO_MINIMAPA_DISENO: tuple[int, int, int, int] = (270, 26, 44, 44)


def minimap_rect_por_defecto() -> pygame.Rect:
    """`RECUADRO_MINIMAPA_DISENO` a la escala de la pantalla real."""
    return _rect_escalado(*RECUADRO_MINIMAPA_DISENO)


_PORTRAIT_STATES = ("normal", "hurt", "critical", "dead")


class HUD:
    """Heads-up display: vida, estamina, carga, reloj, retrato."""

    #: AUD-535 — pedido explícito: "cuando resten exactamente 10
    #: segundos, el contador cambiará de color". Antes eran 30.
    UMBRAL_DE_ALERTA_S: int = 10

    def __init__(self, event_bus: EventBus) -> None:
        self._event_bus = event_bus
        self._health: float = settings.PLAYER_MAX_HEALTH
        self._max_health: float = settings.PLAYER_MAX_HEALTH
        self._timer: float = 0.0
        self._timer_running: bool = False
        self._time_limit: int = 0
        self._is_countdown: bool = False
        self._timer_paused: bool = False
        self._hurt_portrait_timer: float = 0.0
        self._destroyed: bool = False
        self._save_notify_timer: float = 0.0
        #: AUD-281 — lo que queda del rebote del contador de monedas.
        self._pulso_timer: float = 0.0

        # Portrait frame (34x34 with 1px border, inner sprite at 3,3)
        # AUD-499 — el retrato bajó de 34 a 24 de lado (85 px a 60 en
        # pantalla). A ×2,5 la maqueta heredada daba una cara de 85×85: el
        # elemento más grande de toda la franja, más ancho que la hilera de
        # corazones es alta, y el dueño lo describió como «muy grande». La
        # proporción respecto al diseño de 320 era la correcta; lo que no
        # aguanta el salto de escala es que un retrato ocupe el 10 % del
        # ancho de la pantalla.
        # AUD-547 — pedido explícito tras jugarlo: "nada quede pegado a la
        # izquierda o a la derecha o arriba y abajo". El retrato vivía en
        # (2,2) de maqueta —5 px reales del borde—, casi tocando el marco
        # de la ventana. `MARGEN_DE_PANTALLA` es el margen mínimo que
        # respeta cualquier elemento que viva junto a un borde real de la
        # pantalla (no junto a otro elemento del HUD, eso es un gap
        # aparte); el resto de esta franja deriva sus posiciones del
        # retrato, así que un solo número mueve todo el bloque de
        # identidad a la vez.
        MARGEN_DE_PANTALLA = 6
        self._portrait_frame_rect = _rect_escalado(
            MARGEN_DE_PANTALLA, MARGEN_DE_PANTALLA, 24, 24)
        self._portrait_sprite_rect = _rect_escalado(
            MARGEN_DE_PANTALLA + 1, MARGEN_DE_PANTALLA + 1, 22, 22)
        self._timer_fill = None
        self._timer_edges: dict[str, pygame.Surface] = {}
        # Load 9-slice frame from hud_frame.png, pre-scale all variants once
        try:
            raw_frame = AssetLoader.load_image(settings.ASSETS_DIR / "ui" / "hud_frame.png")
            fw, fh = raw_frame.get_size()
            if fw >= 6 and fh >= 6:
                c = 2  # corner size, en la maqueta
                esquinas = {
                    "tl": raw_frame.subsurface((0, 0, c, c)),
                    "tr": raw_frame.subsurface((fw - c, 0, c, c)),
                    "bl": raw_frame.subsurface((0, fh - c, c, c)),
                    "br": raw_frame.subsurface((fw - c, fh - c, c, c)),
                }
                src_edges = {
                    "top": raw_frame.subsurface((c, 0, fw - 2 * c, c)),
                    "bottom": raw_frame.subsurface((c, fh - c, fw - 2 * c, c)),
                    "left": raw_frame.subsurface((0, c, c, fh - 2 * c)),
                    "right": raw_frame.subsurface((fw - c, c, c, fh - 2 * c)),
                }
                # AUD-459 — las esquinas y el grosor del borde iban a 2 px
                # dentro de marcos de 80 px: el 9-slice escalaba el relleno y
                # no la orla. Se escalan al mismo factor que la maqueta y los
                # bordes se pre-escalan contra ese grosor (`ce`), no contra 2.
                ce = _e(c)
                self._frame_corners = {
                    k: pygame.transform.scale(v, (ce, ce))
                    for k, v in esquinas.items()
                }
                self._frame_edges = src_edges
                src_fill = raw_frame.subsurface((c, c, fw - 2 * c, fh - 2 * c))
                self._frame_fill = src_fill
                # AUD-535 — el retrato ya no usa este marco 9-slice
                # rectangular (era el "borde en línea recta" que el pedido
                # quería quitar); sólo lo sigue usando el fondo del reloj,
                # que conserva su panel rectangular.
                # Timer background pre-scaling deferred until _timer_bg_rect is set
            else:
                self._frame_corners = {}
                self._frame_edges = {}
                self._frame_fill = None
        except (pygame.error, FileNotFoundError, PermissionError):
            logger.warning("hud: failed to load hud_frame.png")
            self._frame_corners = {}
            self._frame_edges = {}
            self._frame_fill = None

        # AUD-535 — rediseño espacial pedido tras jugarlo: retrato + tres
        # barras apiladas (vida/estamina/carga) del mismo ancho que el
        # retrato, en vez de una fila de corazones separada. Las barras
        # viven justo debajo del marco del retrato (que termina en
        # y=2+24=26), con 2 px de aire y 1 px de separación entre ellas.
        ancho_bloque = self._portrait_frame_rect.width
        x_bloque = self._portrait_frame_rect.x
        y_barras = self._portrait_frame_rect.bottom + _e(2)
        alto_barra = _e(5)
        paso_barra = alto_barra + _e(1)
        # AUD-565 — guardadas para que `_reflow_bloque_de_identidad` pueda
        # recalcular sólo la `y` de la barra de carga más adelante, sin
        # repetir la aritmética del bloque.
        self._y_barras_bloque = y_barras
        self._paso_barra_bloque = paso_barra
        self._vida_bar_rect = pygame.Rect(x_bloque, y_barras, ancho_bloque, alto_barra)
        self._estamina_bar_rect = pygame.Rect(
            x_bloque, y_barras + paso_barra, ancho_bloque, alto_barra)
        self._carga_bar_rect = pygame.Rect(
            x_bloque, y_barras + paso_barra * 2, ancho_bloque, alto_barra)

        # AUD-219/AUD-535 — marcador de puntos y monedas, reubicado junto
        # al bloque de identidad (retrato + barras) ahora que los
        # corazones ya no ocupan la fila horizontal donde vivía antes.
        # AUD-547 — su x deriva del borde derecho del retrato con el
        # mismo hueco de 6 px que tenía antes (26+6=32); con el retrato
        # movido a MARGEN_DE_PANTALLA=6, ese borde ahora cae en 30, así
        # que el marcador se corre a 36 para conservar el mismo hueco. Su
        # y usa el mismo margen de pantalla que el retrato — sin esto
        # quedaría más cerca del borde superior que su propio vecino.
        self._score_region = _rect_escalado(
            MARGEN_DE_PANTALLA + 30, MARGEN_DE_PANTALLA, 92, 24)
        self._score: int = 0
        self._coins: int = 0
        # AUD-535 — el reloj se centra arriba (antes pegado al borde
        # derecho) y pierde la etiqueta "TIME": un ícono la reemplaza,
        # dibujado en `_draw_timer`, no un sprite nuevo que mantener.
        # AUD-547 — y usa el margen de pantalla; x no lo necesita (está
        # centrado horizontalmente, lejos de ambos bordes laterales).
        self._timer_bg_rect = _rect_escalado(134, MARGEN_DE_PANTALLA, 52, 16)
        # Pre-scale timer background once (deferred from frame load block)
        self._timer_fill = (
            pygame.transform.scale(
                self._frame_fill,
                (self._timer_bg_rect.width, self._timer_bg_rect.height),
            )
            if isinstance(self._frame_fill, pygame.Surface)
            else None
        )
        if self._frame_edges:
            tr = self._timer_bg_rect
            # AUD-459 — grosor del borde a escala, igual que en el retrato.
            ce = _e(2)
            self._timer_edges = {
                "top": pygame.transform.scale(self._frame_edges["top"], (tr.width - 2 * ce, ce)),
                "bottom": pygame.transform.scale(self._frame_edges["bottom"], (tr.width - 2 * ce, ce)),
                "left": pygame.transform.scale(self._frame_edges["left"], (ce, tr.height - 2 * ce)),
                "right": pygame.transform.scale(self._frame_edges["right"], (ce, tr.height - 2 * ce)),
            }
        # AUD-535 — el ícono ocupa el borde izquierdo del marco del reloj;
        # las cifras, el resto. `_timer_label_rect` (el texto "TIME") ya
        # no existe — el ícono es la etiqueta.
        self._timer_icon_rect = _rect_escalado(137, MARGEN_DE_PANTALLA + 1, 12, 12)
        self._timer_rect = _rect_escalado(151, MARGEN_DE_PANTALLA, 34, 14)
        self._timer_flash_timer: float = 0.0
        self._timer_flash_on: bool = False
        # Load timer font (TTF preferred for readability)
        # AUD-455 — iba por fuera de `theme.font()`, así que el 12 nunca se
        # escalaba ni se le aplicaba la preferencia de accesibilidad: a 800×600
        # el reloj se veía a 12 px reales, un tercio del que debía (AUD-451
        # escaló el marcador y el marco del reloj, no la cifra que va dentro).
        self._timer_digit_font: pygame.font.Font = font(_e(12))

        # AUD-535 — antes rastreaban qué ranura de corazón parpadeaba;
        # con una barra continua no hay ranuras, sólo un destello de color
        # sobre la barra entera: rojo al recibir daño, verde al curarse.
        self._vida_flash_timer: float = 0.0
        self._vida_heal_timer: float = 0.0

        # AUD-535 — pedido explícito: "se eliminan los corazones clásicos
        # para darle un aspecto más actual". La vida es ahora
        # `_vida_bar_rect`, una barra continua dibujada con
        # `_dibujar_barra_moderna` — no queda sprite de corazón que cargar
        # (`heart_*.png`/`heart_sparkle.png` se retiran del árbol, ver
        # `tools/generate_all_assets.py`).

        # Load portrait sprites
        self._portraits: dict[str, pygame.Surface] = {}
        for state in _PORTRAIT_STATES:
            path = settings.ASSETS_DIR / "ui" / f"portrait_{state}.png"
            try:
                # AUD-459 — el retrato se subía a 32×32 a pelo; el marco
                # media 80×80. Misma lección que los corazones.
                # AUD-499 — el tamaño sale del rectángulo de la maqueta, no
                # de un 32 escrito aquí. Con el número suelto, mover el marco
                # dejaba el sprite del tamaño anterior: exactamente lo que
                # pasó al reducir el retrato, que se salía de su propio marco.
                destino = self._portrait_sprite_rect.size
                surf = AssetLoader.load_image(path, size=destino)
                # AUD-535 — "diseño circular o de bordes redondeados
                # suaves". Se recorta una sola vez al cargar, no cada
                # fotograma: multiplicar por una máscara circular en
                # `draw()` costaría lo mismo que reconstruir el degradado
                # de las barras cada fotograma (AUD-527, ya cazado una vez).
                self._portraits[state] = _recortar_circular(surf)
            except (pygame.error, FileNotFoundError, PermissionError):
                logger.warning("hud: failed to load portrait %s", state)
        self._current_portrait_state: str = "normal"

        # Boss HUD state
        self._boss_name: str = ""
        self._boss_health: float = 0.0
        self._boss_max_health: float = 0.0
        #: AUD-512 — la fase ACTUAL, 1-indexada. Existía `_boss_phase_count`
        #: (el total) y nada guardaba la actual: `set_boss_hud` recibía
        #: `phase` y lo tiraba, así que el HUD mostraba «PHASE {total}»
        #: fijo durante toda la pelea en vez de avanzar con el jefe.
        self._boss_phase: int = 0
        self._boss_phase_count: int = 0
        self._boss_active: bool = False

        # Combo state
        self._combo_count: int = 0
        self._special_current: float = 0.0
        #: AUD-141 — estamina. En 0 la barra no se dibuja.
        self._estamina_actual: float = 0.0
        self._estamina_max: float = 0.0
        #: AUD-260 — tiempo bala. Negativo = el escenario no lo pide.
        self._bala_fraccion: float = -1.0
        self._bala_activo: bool = False
        #: AUD-274 — franja del Boss Rush. Progreso vacío = modo apagado, que
        #: es el caso de la partida normal.
        self._rush_progreso: str = ""
        self._rush_jefe: str = ""
        self._rush_puntos: int = 0
        self._rush_golpes: int = 0
        self._special_max: float = 100.0

        # AUD-451 — por `theme.font()` y a la escala de la maqueta.
        #
        # Era `pygame.font.Font(None, 12)`: 6 px de tinta medidos, la
        # tipografía por defecto de pygame en vez de la del juego, y sin pasar
        # por `escalar_texto`, así que subir el texto en Opciones no le
        # llegaba. El 12 se escala como el resto de la maqueta porque es un
        # número de la misma maqueta: dejarlo fijo habría agrandado el marco y
        # no lo que va dentro.
        self._font = font(_e(12))

        self._event_bus.subscribe(Events.PLAYER_DAMAGED, self._on_player_damaged)
        self._event_bus.subscribe(Events.PLAYER_HEALED, self._on_player_healed)
        self._event_bus.subscribe(Events.PLAYER_DIED, self._on_player_died)
        self._event_bus.subscribe(Events.BOSS_PHASE_CHANGED, self._on_boss_phase_changed)
        self._event_bus.subscribe(Events.CHECKPOINT_REACHED, self._on_checkpoint_reached)
        self._event_bus.subscribe(Events.STAGE_COMPLETE, self._on_stage_complete)

        # AUD-565 — con la estamina apagada de fábrica (el caso normal:
        # sólo un escenario de los 26 la declara, AUD-141), el bloque
        # arranca ya colapsado a dos barras, no a tres con un hueco en
        # blanco a la espera de un `set_estamina` que puede no llegar en
        # el primer fotograma.
        self._reflow_bloque_de_identidad()

    #
    # destroy(): MUST be called before discarding this HUD instance.
    # Removes EventBus subscriptions to prevent orphan callbacks
    # from accumulating across respawns / scene transitions.
    # Idempotent — safe to call multiple times.
    #
    def destroy(self) -> None:
        """Desuscribe todos los eventos del EventBus.
        Obligatorio llamar antes de descartar el HUD.
        Idempotente: llama varias veces sin efecto secundario.
        """
        if self._destroyed:
            return
        self._destroyed = True
        self._event_bus.unsubscribe(Events.PLAYER_DAMAGED, self._on_player_damaged)
        self._event_bus.unsubscribe(Events.PLAYER_HEALED, self._on_player_healed)
        self._event_bus.unsubscribe(Events.PLAYER_DIED, self._on_player_died)
        self._event_bus.unsubscribe(Events.BOSS_PHASE_CHANGED, self._on_boss_phase_changed)
        self._event_bus.unsubscribe(Events.CHECKPOINT_REACHED, self._on_checkpoint_reached)
        self._event_bus.unsubscribe(Events.STAGE_COMPLETE, self._on_stage_complete)

    def _on_player_damaged(self, **data: object) -> None:
        if self._destroyed:
            return
        amount = cast(float, data.get("amount", 1.0))
        self._health = max(0.0, self._health - amount)
        self._hurt_portrait_timer = 0.8
        # AUD-535 — antes rastreaba qué ranura de corazón cambió de
        # estado; una barra continua no tiene ranuras, sólo un destello
        # sobre la barra entera (`_draw_barra_de_vida`).
        if amount > 0.0:
            self._vida_flash_timer = 0.6

    def _on_player_healed(self, **data: object) -> None:
        if self._destroyed:
            return
        amount = cast(float, data.get("amount", 1.0))
        self._health = min(self._max_health, self._health + amount)
        if amount > 0.0:
            self._vida_heal_timer = 0.6

    def _on_player_died(self, **data: object) -> None:
        if self._destroyed:
            return
        self._health = 0.0
        self._timer_running = False
        self._timer_paused = False

    def minimap_rect(self) -> pygame.Rect:
        """Dónde cabe el minimapa sin pisar a nadie — AUD-499.

        Lo decide el HUD y no el minimapa porque el HUD es quien conoce la
        franja entera. El defecto que esto arregla: el minimapa se colocaba
        solo en `INTERNAL_WIDTH - 84, 4`, en píxeles de pantalla y sin pasar
        por la escala, mientras el cronómetro ocupaba el borde derecho de la
        maqueta (258..320 de 320). Los dos reclamaban la misma esquina y se
        solapaban en 80×38 px.

        Va **debajo** del cronómetro y con su mismo ancho: la franja
        superior está llena, y alinearlo con el reloj hace que se lea como
        una columna y no como una caja suelta.
        """
        return minimap_rect_por_defecto()

    def timer_rect(self) -> pygame.Rect:
        """El marco del cronómetro. Lo consulta la prueba de maqueta."""
        return pygame.Rect(self._timer_bg_rect)

    def vida_bar_rect(self) -> pygame.Rect:
        """Lo que ocupa la barra de vida, a la escala actual.

        AUD-535 — reemplaza a `heart_row_rect()`: la vida ya no es una
        fila de corazones, es una barra continua del ancho del retrato.
        """
        return pygame.Rect(self._vida_bar_rect)

    def estamina_bar_rect(self) -> pygame.Rect:
        """Lo que ocupa la barra de estamina, a la escala actual.

        AUD-541 — la prueba de la barra de estamina sondaba píxeles fijos
        de la maqueta vieja (corazones a la izquierda); el rediseño de
        AUD-535 apiló las barras bajo el retrato y los píxeles dejaron de
        tocar la barra. El acceso público evita que una prueba dependa de
        coordenadas de maqueta.
        """
        return pygame.Rect(self._estamina_bar_rect)

    def regiones(self) -> dict[str, pygame.Rect]:
        """Las zonas de la franja superior — AUD-451.

        Existe para que una prueba pueda comprobar de una vez que ninguna se
        sale de la pantalla ni pisa a otra. Escalar una maqueta sin comprobar
        eso sólo cambia un defecto por otro: lo que antes era ilegible por
        pequeño pasaría a ser ilegible por solaparse.
        """
        return {
            "retrato": pygame.Rect(self._portrait_frame_rect),
            "vida": self.vida_bar_rect(),
            "marcador": pygame.Rect(self._score_region),
            "cronometro": self.timer_rect(),
            # AUD-499 — el minimapa faltaba aquí, y por eso la prueba de «no
            # se pisan» no cazó que llevaba tiempo encima del reloj. Una
            # región que no se declara no la vigila nadie.
            "minimapa": self.minimap_rect(),
        }

    @property
    def ranuras_de_corazon(self) -> int:
        """Cuántas unidades enteras de vida representa la barra ahora
        mismo — AUD-439. El nombre («ranuras de corazón») es historia:
        AUD-535 quitó los corazones, pero el número —vida máxima
        redondeada a entero— sigue siendo lo que muchas pruebas y la
        lógica de mejoras permanentes necesitan comprobar."""
        return max(1, int(self._max_health))

    def set_salud_maxima(self, maxima: float) -> None:
        """La vida máxima **real** del jugador, reliquias y árbol incluidos.

        AUD-439 — `_max_health` se fijaba una vez en `__init__` desde
        `settings.PLAYER_MAX_HEALTH` y no había forma de cambiarlo, así que el
        marcador dibujaba cinco corazones aunque el jugador tuviera diez.
        Comprar el casco de la tienda no producía ningún cambio en pantalla.

        Lo empuja el escenario cada fotograma, igual que la puntuación o la
        estamina, y por lo mismo: es un valor del jugador, no del marcador, y
        el que manda es el jugador. No se hace por eventos porque el máximo no
        cambia con un suceso puntual sino con lo que llevas encima.

        Se acota por abajo a un corazón: `max_health` sale de sumar
        bonificaciones y una partida editada a mano puede traer un cero o un
        negativo. Un marcador sin ranuras no dice nada y además rompería el
        recorrido de dibujo.
        """
        self._max_health = max(1.0, float(maxima))
        # Si el tope baja —se quita una reliquia— la vida no puede quedarse por
        # encima: se verían corazones fuera del marcador.
        self._health = min(self._health, self._max_health)

    def set_boss_hud(self, name: str, health: float, max_health: float, phase: int, phase_count: int) -> None:
        self._boss_name = name
        self._boss_health = health
        self._boss_max_health = max_health
        self._boss_phase = phase
        self._boss_phase_count = phase_count
        self._boss_active = True

    def clear_boss_hud(self) -> None:
        self._boss_active = False
        self._boss_name = ""

    def set_combo_count(self, count: int) -> None:
        self._combo_count = max(0, count)

    def _on_boss_phase_changed(self, **data: object) -> None:
        if self._destroyed:
            return
        self._boss_name = str(data.get("boss_name", ""))
        # AUD-512 — `BossBase.change_phase` emite `phase=self.current_phase`
        # (0-indexado: el primer valor tras nacer es 0), y `set_boss_hud`
        # recibe la fase ya 1-indexada desde `actualizaciones.py`
        # (`current_phase + 1`). El +1 aquí iguala las dos rutas para que no
        # importe si el HUD se entera por la llamada directa o por el evento.
        self._boss_phase = cast(int, data.get("phase", 0)) + 1
        self._boss_phase_count = cast(int, data.get("phase_count", 1))

    def _on_checkpoint_reached(self, **data: object) -> None:
        if self._destroyed:
            return
        # Timer keeps running through checkpoints — no op

    def _on_stage_complete(self, **data: object) -> None:
        if self._destroyed:
            return
        self.stop_timer()

    def trigger_save_notification(self) -> None:
        if self._destroyed:
            return
        self._save_notify_timer = 2.0

    def start_timer(self, time_limit: int = 0) -> None:
        self._time_limit = time_limit
        self._is_countdown = time_limit > 0
        self._timer = float(time_limit) if self._is_countdown else 0.0
        self._timer_running = True

    def stop_timer(self) -> None:
        self._timer_running = False

    def pause_timer(self) -> None:
        self._timer_running = False
        self._timer_paused = True

    def resume_timer(self) -> None:
        self._timer_running = True
        self._timer_paused = False

    def update(self, dt: float) -> None:
        if self._timer_running:
            if self._is_countdown:
                self._timer -= dt
                if self._timer <= 0.0:
                    self._timer = 0.0
                    self._event_bus.emit(Events.PLAYER_DIED)
                    self._timer_running = False
            else:
                self._timer += dt
        self._hurt_portrait_timer = max(0.0, self._hurt_portrait_timer - dt)
        self._save_notify_timer = max(0.0, self._save_notify_timer - dt)
        self._pulso_timer = max(0.0, self._pulso_timer - dt)
        self._vida_flash_timer = max(0.0, self._vida_flash_timer - dt)
        self._vida_heal_timer = max(0.0, self._vida_heal_timer - dt)
        # AUD-535 — pedido explícito: "cuando resten exactamente 10
        # segundos, el contador cambiará de color". Antes eran 30.
        if self._timer_running or self._timer_paused:
            total_seconds = int(self._timer)
            if self._is_countdown and total_seconds <= self.UMBRAL_DE_ALERTA_S:
                self._timer_flash_timer += dt
                # AUD-553 — "la música acelerará su tempo": `pygame.mixer.
                # music` no tiene control de tempo (ver la nota junto a
                # `Events.SFX_TIMER_ALERT_PULSE`), así que lo que sí se
                # acelera de verdad es el intervalo del pulso — de 0,25s a
                # los 10s restantes hasta un piso de 0,08s cerca de 0s. El
                # ritmo lo decide este bucle, no el audio, así que "acelerar"
                # es simplemente reducir el intervalo, sin DSP de por medio.
                progreso = 1.0 - max(0.0, min(1.0, self._timer / self.UMBRAL_DE_ALERTA_S))
                intervalo = 0.25 - (0.25 - 0.08) * progreso
                if self._timer_flash_timer >= intervalo:
                    self._timer_flash_on = not self._timer_flash_on
                    self._timer_flash_timer = 0.0
                    if self._timer_flash_on and self._timer_running:
                        self._event_bus.emit(Events.SFX_TIMER_ALERT_PULSE)
            else:
                self._timer_flash_on = False
                self._timer_flash_timer = 0.0

    def _get_portrait_state(self) -> str:
        if self._health <= 0:
            return "dead"
        if self._health <= 1.0:
            return "critical"
        if self._hurt_portrait_timer > 0:
            return "hurt"
        return "normal"

    def draw(self, surface: pygame.Surface) -> None:
        self._draw_portrait(surface)
        self._draw_barra_de_vida(surface)
        self._draw_special_meter(surface)
        self._draw_estamina(surface)
        self._draw_tiempo_bala(surface)
        self._draw_boss_rush(surface)
        self._draw_score(surface)
        self._draw_timer(surface)
        if self._boss_active:
            self._draw_boss_hud(surface)
        if self._combo_count > 1:
            self._draw_combo_indicator(surface)
        self._draw_save_notification(surface)

    def set_score(self, puntos: int, monedas: int = 0) -> None:
        """Puntos de la partida y saldo de monedas (AUD-219).

        Van juntos porque se leen juntos: los puntos dicen cómo va la partida y
        las monedas, si ya alcanza para comprar algo. Enseñar sólo lo primero
        deja al jugador yendo a la tienda a ver si le llega.
        """
        self._score = max(0, int(puntos))
        self._coins = max(0, int(monedas))

    #: AUD-535 — el glifo "¤" (moneda genérica, U+00A4) no existe en la
    #: fuente del tema: `theme.font().render("¤56", ...)` medía 22 px de
    #: ancho para tres caracteres —la mitad de lo real— y el trazo salía
    #: superpuesto, ilegible. El pedido original ya quería "iconos
    #: sutiles" para el marcador; un ícono dibujado en vez de un glifo
    #: que la fuente no tiene resuelve las dos cosas a la vez.
    _ANCHO_ICONO_MONEDA_MAQUETA = 8

    def _score_text(self) -> str:
        return f"{self._score}  {self._coins}"

    def score_rect(self) -> pygame.Rect:
        """Lo que ocupa de verdad el marcador dibujado, no la región reservada.

        La usa la prueba que comprueba que cabe donde `09_HUD_SPEC.md` dice, y
        que no pisa ni la barra de vida ni el cronómetro.
        """
        w, h = self._font.size(self._score_text())
        w += _e(self._ANCHO_ICONO_MONEDA_MAQUETA) + _e(2)
        r = self._score_region
        return pygame.Rect(r.right - w, r.y, w, min(h, r.height))

    def set_boss_rush(self, progreso: str, jefe: str,
                      puntos: int, golpes: int) -> None:
        """Los datos del Boss Rush. Con `progreso` vacío la franja no se dibuja.

        AUD-274 — AUD-261 conectó el modo entero y el jugador no veía nada: la
        puntuación se calculaba, los golpes se contaban, la vida se arrastraba,
        y todo ello era invisible. Un marcador que no se ve es, para quien
        juega, un marcador que no existe.
        """
        self._rush_progreso = progreso
        self._rush_jefe = jefe
        self._rush_puntos = puntos
        self._rush_golpes = golpes

    def _draw_boss_rush(self, surface: pygame.Surface) -> None:
        """Una línea arriba: en qué combate va, contra quién y cuántos golpes.

        Una línea y no un panel: el Boss Rush es un modo de concentración, y
        una interfaz que tape la arena trabaja en contra del propio modo.
        """
        if not self._rush_progreso:
            return
        izquierda = self._font.render(
            f"RUSH {self._rush_progreso}  {self._rush_jefe}", True, (255, 210, 120))
        derecha = self._font.render(
            f"{self._rush_puntos} pts   {self._rush_golpes} golpes",
            True, (235, 235, 210))
        y = 20
        surface.blit(izquierda, (settings.INTERNAL_WIDTH // 2
                                 - izquierda.get_width() // 2, y))
        surface.blit(derecha, (settings.INTERNAL_WIDTH
                               - derecha.get_width() - 8, y))

    #: AUD-281 — cuánto dura el rebote del contador al recoger algo.
    #:
    #: 0,18 s. Más corto no se ve; más largo y dos monedas seguidas dejan el
    #: número temblando, que es lo que hace que un jugador acabe mirando la
    #: esquina en vez del escenario.
    _PULSO_DE_RECOGIDA: float = 0.18

    #: Cuánto crece en el pico, en veces. 1,25 se nota de reojo sin empujar el
    #: número contra el marco del cronómetro.
    _PULSO_ESCALA: float = 1.25

    def pulso_de_recogida(self) -> None:
        """Rebota el contador de monedas. Lo llama la escena al recoger algo.

        Respeta «movimiento reducido» dejándolo en nada: es adorno, y la opción
        existe justamente para quitar el adorno que se mueve. Aquí sí se puede
        anular del todo —al contrario que la estela del dash, que era la única
        señal de que el dash ocurrió—, porque el número ya dice lo que pasó.
        """
        from src.engine.core import user_settings

        if user_settings.preferencia("reduced_motion", False):
            return
        self._pulso_timer = self._PULSO_DE_RECOGIDA

    def _draw_score(self, surface: pygame.Surface) -> None:
        """Alineado a la derecha, pegado al cronómetro.

        Alineado a la derecha y no a la izquierda porque el número crece: con
        el origen fijo a la izquierda, pasar de 9999 a 10000 lo empujaría
        contra el marco del cronómetro a mitad de partida.
        """
        r = self.score_rect()
        puntos = self._font.render(str(self._score), True, (235, 235, 210))
        monedas = self._font.render(str(self._coins), True, (255, 215, 0))
        surface.blit(puntos, (r.x, r.y))

        # AUD-281 — el rebote. Crece y vuelve, anclado a su borde derecho para
        # que el número no se desplace mientras late: escalar desde la esquina
        # superior izquierda lo empujaría contra el cronómetro en cada moneda.
        if self._pulso_timer > 0.0:
            fase = self._pulso_timer / self._PULSO_DE_RECOGIDA
            # Media onda de seno: sube y baja una vez, sin tirón al terminar.
            escala = 1.0 + (self._PULSO_ESCALA - 1.0) * math.sin(fase * math.pi)
            ancho = max(1, int(monedas.get_width() * escala))
            alto = max(1, int(monedas.get_height() * escala))
            monedas = pygame.transform.smoothscale(monedas, (ancho, alto))

        surface.blit(monedas, (r.right - monedas.get_width(), r.y))
        icono = _icono_de_moneda(_e(self._ANCHO_ICONO_MONEDA_MAQUETA), (255, 215, 0))
        ix = r.right - monedas.get_width() - icono.get_width() - _e(2)
        iy = r.y + (monedas.get_height() - icono.get_height()) // 2
        surface.blit(icono, (ix, iy))

    def set_special_meter(self, current: float, max_val: float) -> None:
        self._special_current = current
        self._special_max = max_val

    def set_estamina(self, current: float, max_val: float) -> None:
        """AUD-141. Con `max_val = 0` la barra no se dibuja.

        Un medidor vacío en pantalla en los quince escenarios que no usan
        estamina sería una promesa falsa: el jugador buscaría qué lo llena.

        AUD-565 — «no se dibuja» ya no basta por sí solo: sin esto, el
        bloque de identidad (AUD-535/547) apilaba las tres barras a
        posiciones fijas, así que un escenario sin estamina dejaba un
        hueco en blanco del tamaño de una barra entera entre la de vida y
        la de carga. `_reflow_bloque_de_identidad` recoloca la barra de
        carga cada vez que cambia el estado activo/inactivo.
        """
        self._estamina_actual = current
        self._estamina_max = max_val
        self._reflow_bloque_de_identidad()

    def _reflow_bloque_de_identidad(self) -> None:
        """AUD-565 — con la estamina apagada, la barra de carga sube a
        ocupar el sitio que dejaría vacío la de estamina, en vez de que el
        bloque de identidad se quede con un tercio en blanco.

        `_estamina_bar_rect` no cambia de tamaño ni desaparece: sigue
        existiendo con su ancho de siempre (lo consultan pruebas y
        `estamina_bar_rect()`) — sólo deja de pintarse (`_draw_estamina`
        ya lo hacía por su cuenta) y de reservarle sitio a la barra de
        abajo.
        """
        if self._estamina_max > 0.0:
            self._carga_bar_rect.y = self._y_barras_bloque + self._paso_barra_bloque * 2
        else:
            self._carga_bar_rect.y = self._y_barras_bloque + self._paso_barra_bloque

    def set_tiempo_bala(self, fraccion: float, activo: bool) -> None:
        """AUD-260. Con `fraccion` negativa la barra no se dibuja.

        Mismo trato que la estamina (AUD-141): un medidor en pantalla en los
        dieciséis escenarios que no declaran `tiempo_bala` sería una promesa
        falsa. La escena manda `-1.0` cuando la mecánica está apagada.
        """
        self._bala_fraccion = fraccion
        self._bala_activo = activo

    #: AUD-535 — el tiempo bala no es una de las tres barras del bloque
    #: de identidad (vida/estamina/carga, pedidas explícitamente) — sigue
    #: siendo la excepción rara (16 de 26 escenarios no la declaran,
    #: AUD-260), así que se dibuja debajo del bloque, no dentro, con la
    #: misma anchura para que se lea como parte de la misma columna.
    def _draw_tiempo_bala(self, surface: pygame.Surface) -> None:
        if self._bala_fraccion < 0.0:
            return
        rect = pygame.Rect(
            self._carga_bar_rect.x, self._carga_bar_rect.bottom + _e(3),
            self._carga_bar_rect.width, self._carga_bar_rect.height)
        pct = max(0.0, min(1.0, self._bala_fraccion))
        # AUD-527 — azul mientras está guardada, blanco mientras se gasta: el
        # jugador tiene que ver **que la está usando** sin apartar la vista
        # del combate, que es cuando la usa. El degradado va del tono
        # guardado al tono en uso para que el cambio de estado se lea en la
        # propia barra, no sólo en un color plano que cambia de golpe.
        color_fin = (255, 255, 255) if self._bala_activo else (110, 160, 255)
        _dibujar_barra_moderna(surface, rect, pct, (60, 60, 110), color_fin,
                                halo_al_llenar=False)

    def _draw_estamina(self, surface: pygame.Surface) -> None:
        if self._estamina_max <= 0.0:
            return
        pct = max(0.0, min(1.0, self._estamina_actual / self._estamina_max))
        # AUD-547 — pedido explícito: amarillo para la estamina, sin
        # excepción de color al quedar poca (antes viraba de verde a
        # ámbar). El propio degradado —oscuro a amarillo pleno— ya
        # comunica cuánto queda; no hace falta un segundo color en el
        # camino para leerlo.
        color_fin = (240, 210, 60)
        _dibujar_barra_moderna(surface, self._estamina_bar_rect, pct,
                               (70, 60, 15), color_fin, halo_al_llenar=False)

    def _draw_special_meter(self, surface: pygame.Surface) -> None:
        pct = min(1.0, self._special_current / max(self._special_max, 1.0))
        # AUD-547 — pedido explícito: azul para la carga del ultimate,
        # constante — antes viraba a dorado al llenarse. El halo de
        # `_dibujar_barra_moderna` ya marca "lista" al tope; un segundo
        # color encima era redundante con esa señal.
        color_fin = (90, 140, 255)
        _dibujar_barra_moderna(surface, self._carga_bar_rect, pct, (20, 30, 70), color_fin)
        if pct >= 1.0:
            flash = (int(pygame.time.get_ticks() / 200) % 2 == 0)
            if flash:
                label = self._font.render("CARGA LISTA", True, (255, 220, 50))
                surface.blit(label, (self._carga_bar_rect.x,
                                     self._carga_bar_rect.y - _e(12)))

    def _draw_save_notification(self, surface: pygame.Surface) -> None:
        if self._save_notify_timer <= 0:
            return
        alpha = int(255 * min(1.0, self._save_notify_timer / 0.5))
        txt = self._font.render("SAVED", True, (100, 255, 100))
        txt.set_alpha(alpha)
        tx = (settings.INTERNAL_WIDTH - txt.get_width()) // 2
        ty = settings.INTERNAL_HEIGHT - 20
        surface.blit(txt, (tx, ty))

    def _draw_combo_indicator(self, surface: pygame.Surface) -> None:
        import src.engine.core.settings as settings
        idx = min(self._combo_count - 1, len(settings.COMBO_DAMAGE_MULT) - 1)
        mult = settings.COMBO_DAMAGE_MULT[idx]
        txt = self._font.render(f"COMBO x{self._combo_count}! {mult}x", True, (255, 220, 100))
        tx = (settings.INTERNAL_WIDTH - txt.get_width()) // 2
        ty = settings.INTERNAL_HEIGHT - 32
        surface.blit(txt, (tx, ty))

    def _draw_portrait(self, surface: pygame.Surface) -> None:
        """AUD-535 — "diseño circular o de bordes redondeados suaves":
        el marco 9-slice rectangular se reemplaza por un disco de fondo,
        el retrato recortado en círculo (`_recortar_circular`, una vez al
        cargar) y un anillo — no una caja."""
        state = self._get_portrait_state()
        portrait = self._portraits.get(state)
        r = self._portrait_frame_rect
        centro = r.center
        radio = r.width // 2

        color_map = {"normal": (60, 60, 80), "hurt": (180, 60, 60),
                     "critical": (200, 40, 40), "dead": (40, 40, 40)}
        color_anillo = color_map.get(state, (60, 60, 80))

        pygame.draw.circle(surface, (14, 14, 22), centro, radio)
        if portrait:
            surface.blit(portrait, self._portrait_sprite_rect)
        else:
            pygame.draw.circle(surface, color_anillo, centro,
                               self._portrait_sprite_rect.width // 2)

        anillo = _anillo_del_retrato(r.width, max(2, _e(1)), color_anillo)
        surface.blit(anillo, r.topleft)

    def _draw_barra_de_vida(self, surface: pygame.Surface) -> None:
        """AUD-535 — reemplaza la fila de corazones: "se eliminan los
        corazones clásicos para darle un aspecto más actual". Misma
        barra redondeada con degradado que ya usan estamina/carga/tiempo
        bala (AUD-527), del mismo ancho que el retrato."""
        pct = max(0.0, min(1.0, self._health / self._max_health))
        # AUD-547 — pedido explícito: rojo para la vida, sin excepción de
        # color a poca vida (antes viraba a naranja). La urgencia de
        # "vida crítica" la sigue marcando el retrato (su anillo pasa a
        # rojo intenso/oscuro en `_get_portrait_state`) y el destello de
        # daño de aquí abajo — no hacía falta un segundo canal de color
        # en la propia barra.
        color_fin = (230, 60, 60)
        _dibujar_barra_moderna(surface, self._vida_bar_rect, pct,
                               (70, 15, 15), color_fin, halo_al_llenar=False)

        # Destello de color sobre la barra entera — rojo al recibir daño,
        # verde al curarse. Reemplaza el parpadeo por ranura (no hay
        # ranuras) y la animación de chispas secuencial (no hay "de
        # derecha a izquierda" en una barra continua).
        if self._vida_flash_timer > 0.0 and int(self._vida_flash_timer * 10) % 2 == 0:
            destello = pygame.Surface(self._vida_bar_rect.size, pygame.SRCALPHA)
            radio = max(2, min(self._vida_bar_rect.height // 2, _e(4)))
            pygame.draw.rect(destello, (255, 255, 255, 120), destello.get_rect(),
                             border_radius=radio)
            surface.blit(destello, self._vida_bar_rect.topleft)
        elif self._vida_heal_timer > 0.0:
            alpha = int(140 * min(1.0, self._vida_heal_timer / 0.6))
            destello = pygame.Surface(self._vida_bar_rect.size, pygame.SRCALPHA)
            radio = max(2, min(self._vida_bar_rect.height // 2, _e(4)))
            pygame.draw.rect(destello, (120, 255, 140, alpha), destello.get_rect(),
                             border_radius=radio)
            surface.blit(destello, self._vida_bar_rect.topleft, special_flags=pygame.BLEND_RGBA_ADD)

    def _draw_boss_hud(self, surface: pygame.Surface) -> None:
        """Draw boss health bar and name at top of screen."""
        # AUD-459 — la barra era la última maqueta sin escalar: 200×12 a pelo
        # sobre 800×600. Se escala como el resto del HUD.
        bar_width = _e(200)
        bar_height = _e(12)
        bar_x = (settings.INTERNAL_WIDTH - bar_width) // 2
        bar_y = _e(4)
        # Boss name
        # AUD-512 — antes leía `_boss_phase_count` (el total, fijo durante
        # toda la pelea) donde debía leer la fase actual.
        phase_text = f"PHASE {self._boss_phase}" if self._boss_phase_count > 0 else ""
        label = f"{self._boss_name}  {phase_text}" if phase_text else self._boss_name
        name_surf = self._font.render(label, True, (200, 180, 120))
        nx = bar_x + (bar_width - name_surf.get_width()) // 2
        surface.blit(name_surf, (nx, bar_y - _e(2)))
        # AUD-527 — degradado en vez de relleno plano: ámbar mientras el
        # jefe tiene margen, rojo cuando queda poco. El halo se apaga aquí
        # a propósito — un jefe a tope de vida no necesita un brillo de
        # "listo", el que sí lo pide es el medidor especial del jugador.
        ratio = (max(0.0, self._boss_health / self._boss_max_health)
                 if self._boss_max_health > 0 else 0.0)
        color_fin = (210, 70, 50) if ratio < 0.3 else (215, 190, 70)
        rect = pygame.Rect(bar_x, bar_y + _e(10), bar_width, bar_height)
        _dibujar_barra_moderna(surface, rect, ratio, (60, 20, 15), color_fin,
                                halo_al_llenar=False)

    def _draw_timer_background(self, surface: pygame.Surface) -> None:
        r = self._timer_bg_rect
        c = _e(2)
        if self._frame_corners:
            surface.blit(self._frame_corners["tl"], (r.x, r.y))
            surface.blit(self._frame_corners["tr"], (r.right - c, r.y))
            surface.blit(self._frame_corners["bl"], (r.x, r.bottom - c))
            surface.blit(self._frame_corners["br"], (r.right - c, r.bottom - c))
            surface.blit(self._timer_edges["top"], (r.x + c, r.y))
            surface.blit(self._timer_edges["bottom"], (r.x + c, r.bottom - c))
            surface.blit(self._timer_edges["left"], (r.x, r.y + c))
            surface.blit(self._timer_edges["right"], (r.right - c, r.y + c))
            if self._timer_fill:
                surface.blit(self._timer_fill, r, special_flags=pygame.BLEND_ALPHA_SDL2)
        else:
            pygame.draw.rect(surface, (10, 10, 30), r)
            pygame.draw.rect(surface, (100, 100, 140), r, 1)

    def _draw_timer(self, surface: pygame.Surface) -> None:
        if not self._timer_running and not self._timer_paused:
            return
        self._draw_timer_background(surface)
        total_seconds = int(self._timer)
        # AUD-535 — "se elimina la etiqueta de texto Timer; en su lugar,
        # un ícono de reloj". `_en_alerta` decide el color del ícono y de
        # las cifras a la vez: los dos cuentan la misma historia.
        en_alerta = self._is_countdown and total_seconds <= self.UMBRAL_DE_ALERTA_S
        color_icono = (255, 90, 90) if en_alerta else (215, 215, 225)
        icono = _icono_de_reloj(self._timer_icon_rect.width, color_icono)
        surface.blit(icono, self._timer_icon_rect.topleft)

        minutes = total_seconds // 60
        seconds = total_seconds % 60
        time_str = f"{minutes:02d}:{seconds:02d}"
        # 2Hz flash: hide text when flashing
        flash = en_alerta
        if flash and not self._timer_flash_on:
            return
        color = (255, 110, 110) if en_alerta else (255, 255, 255)
        if self._timer_digit_font:
            time_surf = self._timer_digit_font.render(time_str, True, color)
            if time_surf.get_width() > 0:
                tx = self._timer_rect.x + max(0, (self._timer_rect.width - time_surf.get_width()) // 2)
                ty = self._timer_rect.y + (self._timer_rect.height - time_surf.get_height()) // 2
                surface.blit(time_surf, (tx, ty))
        else:
            text = self._font.render(time_str, True, color)
            tx = self._timer_rect.x + max(0, (self._timer_rect.width - text.get_width()) // 2)
            ty = self._timer_rect.y + (self._timer_rect.height - text.get_height()) // 2
            surface.blit(text, (tx, ty))

    @property
    def current_time(self) -> float:
        return self._timer

    @current_time.setter
    def current_time(self, value: float) -> None:
        self._timer = value

    @property
    def time_limit(self) -> int:
        return self._time_limit

    @property
    def is_countdown(self) -> bool:
        return self._is_countdown

    @is_countdown.setter
    def is_countdown(self, value: bool) -> None:
        self._is_countdown = value
