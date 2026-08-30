"""
Modulo: gen_tileset_residencias
Sistema: tools (arte de mapa)
Descripcion: Generador de tileset de produccion para la arena de boss
    "Residencias al Crepusculo". Emite un atlas 16x16 con nombres (12 columnas)
    mas una hoja de contacto etiquetada. Cada pixel es un color de paleta
    puesto directamente en un arreglo numpy (sin anti-alias), compartiendo la
    paleta maestra congelada de 34 colores aprobada en la prueba de la vineta
    crepuscular (2026-07-23). Los tiles de relleno (cielo/pasto/bosque/seto/
    estuco) muestrean ruido sobre coordenadas GLOBALES del atlas para que las
    variantes hermanas fluyan sin costuras; las estructuras multi-tile
    (hastial, gazebo, arbol, bungalow) se pintan como una sola composicion
    grande y luego se cortan en celdas para que encajen entre si sin costuras.

Origen
------
Las tecnicas (dither ordenado, moteado por hash por pixel, ranuras de lamina
corrugada, rampa de cielo crepuscular, desgaste de estuco, limpieza despeckle)
se toman de ``tools/vignette_reference.py`` y sus helpers extraidos en
``tools/art_lib``. Ningun valor de color se re-deriva: el atlas solo dibuja
nombres de ``art_lib.PALETTE`` (mas el negro puro ``(0, 0, 0)`` reservado como
vacio visual).

Salidas (idempotente; ``main()`` puede llamarse repetidamente)
--------------------------------------------------------
- ``<game>/assets/tilesets/tileset_residencias_crepusculo.png`` (el atlas)
- ``<lab>/reports/map_residencias/tileset_contact_sheet.png`` (x3 NEAREST,
  cada celda etiquetada ``idx nombre`` para revision visual)
"""
from __future__ import annotations

import math
import os
from pathlib import Path
from typing import Callable

import numpy as np
from PIL import Image, ImageDraw

from src.stages.boss_venado.tools.art_lib import (
    BAYER_4X4,
    PALETTE,
    bayer_dither,
    despeckle,
    hash01,
    mottle,
)

# ---------------------------------------------------------------------------
# Rutas (derivadas de __file__ para que el cwd nunca importe)
# ---------------------------------------------------------------------------
_HERE = Path(__file__).resolve()
GAME_ROOT = _HERE.parents[4]                 # .../game
LAB_ROOT = _HERE.parents[5]                  # .../Centro de pruebas CPG I
OUT_PNG = GAME_ROOT / "assets" / "tilesets" / "tileset_residencias_crepusculo.png"
CONTACT_DIR = LAB_ROOT / "reports" / "map_residencias"
CONTACT_PNG = CONTACT_DIR / "tileset_contact_sheet.png"

TILE = 16
COLS = 12
BLACK = (0, 0, 0)                            # tile 0 / vacio visual

# Acentos brillantes, deliberadamente aislados, que el despeckle jamas debe limpiar.
_PROTECT = (
    "W0", "W1", "W2", "S4", "S5", "RC", "RM",
    "P0", "P1", "O3", "PL", "V3", "G3",
)

# ---------------------------------------------------------------------------
# Registro: el decorador @tile + el cortador de bloques, ambos alimentan
# TILES / NAME_TO_INDEX. Una funcion de dibujo tiene firma (cell, gx, gy) ->
# None, donde `cell` es la vista 16x16x3 del atlas y (gx, gy) es la esquina
# superior-izquierda de esa celda en pixeles GLOBALES del atlas (usado por los
# rellenos para que las variantes adyacentes compartan un campo de ruido continuo).
# ---------------------------------------------------------------------------
DrawFn = Callable[[np.ndarray, int, int], None]
TILES: list[tuple[str, DrawFn]] = []
NAME_TO_INDEX: dict[str, int] = {}


def _register(name: str, fn: DrawFn) -> None:
    if name in NAME_TO_INDEX:
        raise ValueError(f"duplicate tile name: {name}")
    NAME_TO_INDEX[name] = len(TILES)
    TILES.append((name, fn))


def tile(name: str) -> Callable[[DrawFn], DrawFn]:
    """Registra un solo tile 16x16 dibujado por la funcion decorada."""
    def deco(fn: DrawFn) -> DrawFn:
        _register(name, fn)
        return fn
    return deco


_BLOCK_BUILDERS: dict[str, Callable[[], np.ndarray]] = {}
_BLOCK_CACHE: dict[str, np.ndarray] = {}


def _get_block(key: str) -> np.ndarray:
    if key not in _BLOCK_CACHE:
        _BLOCK_CACHE[key] = _BLOCK_BUILDERS[key]()
    return _BLOCK_CACHE[key]


def register_block(
    prefix: str,
    cols: int,
    rows: int,
    builder: Callable[[], np.ndarray],
    sep: str = "_",
) -> None:
    """Registra un bloque de tiles (cols x rows) construido como una composicion.

    ``builder`` devuelve un buffer uint8 ``(rows*16, cols*16, 3)``; se pinta
    una sola vez (memoizado) y se corta en celdas nombradas
    ``{prefix}{sep}{col}{row}`` (digito de columna primero, coincidiendo con
    el inventario: la esquina inferior-derecha de un gazebo 7x6 es ``gaz_65``).
    P. ej. ``hast_00``..``hast_55``, o ``tree_c00`` con ``sep=""``.
    """
    _BLOCK_BUILDERS[prefix] = builder

    def _cell(kk: str, rr: int, cc: int) -> DrawFn:
        def fn(cell: np.ndarray, gx: int, gy: int) -> None:
            blk = _get_block(kk)
            cell[:] = blk[rr * TILE:rr * TILE + TILE, cc * TILE:cc * TILE + TILE]
        return fn

    for r in range(rows):
        for c in range(cols):
            _register(f"{prefix}{sep}{c}{r}", _cell(prefix, r, c))


# ---------------------------------------------------------------------------
# Helpers de pixel de bajo nivel (operan sobre cualquier arreglo HxWx3)
# ---------------------------------------------------------------------------
def _put(A: np.ndarray, x: int, y: int, name: str) -> None:
    h, w = A.shape[:2]
    if 0 <= x < w and 0 <= y < h:
        A[y, x] = PALETTE[name]


def _rect(A: np.ndarray, x0: int, y0: int, x1: int, y1: int, name: str) -> None:
    h, w = A.shape[:2]
    x0 = max(0, x0); y0 = max(0, y0); x1 = min(w, x1); y1 = min(h, y1)
    if x1 > x0 and y1 > y0:
        A[y0:y1, x0:x1] = PALETTE[name]


# ===========================================================================
# TILE 0 - vacio visual
# ===========================================================================
@tile("black")
def _black(A: np.ndarray, gx: int, gy: int) -> None:
    A[:] = BLACK


# ===========================================================================
# CIELO  (rampa crepuscular, bandas planas con moteado fino para que cada una
# encaje limpiamente)
# ===========================================================================
def _sky_fill(A, gx, gy, base, alt, alt_prob, salt):
    for y in range(TILE):
        for x in range(TILE):
            r = hash01(gx + x, gy + y, salt)
            A[y, x] = PALETTE[alt] if r < alt_prob else PALETTE[base]


@tile("sky_top")
def _sky_top(A, gx, gy):
    _sky_fill(A, gx, gy, "S0", "S1", 0.06, 1)


@tile("sky_high")
def _sky_high(A, gx, gy):
    _sky_fill(A, gx, gy, "S1", "S2", 0.10, 2)


@tile("sky_mid")
def _sky_mid(A, gx, gy):
    _sky_fill(A, gx, gy, "S2", "S3", 0.12, 3)


@tile("sky_low")
def _sky_low(A, gx, gy):
    _sky_fill(A, gx, gy, "S3", "S2", 0.12, 4)


@tile("sky_horizon")
def _sky_horizon(A, gx, gy):
    # NUCLEO concentrado del atardecer: una sola rampa vertical suave rosa(S3)
    # -> pico naranja(S5) -> de vuelta a calido(S4), con dither ordenado para
    # que se lea como UN solo degradado suave en vez de las viejas sub-bandas
    # duras "triple neon". Unos pocos destellos W0 titilan a lo largo del
    # centro mas brillante. Colocada como una banda delgada de 2 filas en la
    # linea de arboles; la copa del bosque rompe su borde inferior para que no
    # haya una linea dura.
    for y in range(TILE):
        t = y / (TILE - 1)
        for x in range(TILE):
            if t < 0.30:
                base = bayer_dither(gx + x, gy + y, "S3", "S4", t / 0.30)
            elif t < 0.62:
                base = bayer_dither(gx + x, gy + y, "S4", "S5", (t - 0.30) / 0.32)
            else:
                base = bayer_dither(gx + x, gy + y, "S5", "S4", (t - 0.62) / 0.38)
            if 0.34 < t < 0.60 and hash01(gx + x, gy + y, 5) < 0.05:
                base = "W0"                    # tenue destello ardiente en la cresta
            A[y, x] = PALETTE[base]


def _sky_trans(A, gx, gy, top, bot, salt):
    """Una banda suave con dither que rampea de ``top`` (su borde superior) a
    ``bot`` (su borde inferior) via dither Bayer ordenado, para que las bandas
    de cielo planas adyacentes se fundan entre si sin costura horizontal dura.
    Un poco de ruido hash rasguna el dither para que nunca se vea como una
    trama mecanica."""
    for y in range(TILE):
        t = y / (TILE - 1)
        for x in range(TILE):
            name = bayer_dither(gx + x, gy + y, top, bot, t)
            if hash01(gx + x, gy + y, salt) < 0.05:
                name = bot if name == top else top
            A[y, x] = PALETTE[name]


@tile("sky_tr_01")
def _sky_tr_01(A, gx, gy):
    _sky_trans(A, gx, gy, "S0", "S1", 21)      # violeta profundo -> indigo


@tile("sky_tr_12")
def _sky_tr_12(A, gx, gy):
    _sky_trans(A, gx, gy, "S1", "S2", 22)      # indigo -> purpura


@tile("sky_tr_23")
def _sky_tr_23(A, gx, gy):
    _sky_trans(A, gx, gy, "S2", "S3", 23)      # purpura -> crepusculo rosado


@tile("sky_glow")
def _sky_glow(A, gx, gy):
    # Resplandor calido difuso que se ubica POR ENCIMA del nucleo concentrado
    # del horizonte: rosa(S3) fundiendose HACIA ARRIBA en el primer calido(S4).
    # Colocado como una UNICA fila para que su rampa aparezca una sola vez
    # (apilar el mismo tile de rampa fue lo que causo las viejas franjas).
    _sky_trans(A, gx, gy, "S3", "S4", 24)


@tile("sky_glow_dn")
def _sky_glow_dn(A, gx, gy):
    # El lado descendente del atardecer: calido(S4) fundiendose de vuelta HACIA
    # ABAJO a rosa(S3), colocado una fila debajo del nucleo brillante para que
    # el naranja se desvanezca simetricamente en el crepusculo detras de los
    # edificios. Continua el borde S4 del nucleo sin escalon.
    _sky_trans(A, gx, gy, "S4", "S3", 25)


@tile("sky_star_a")
def _sky_star_a(A, gx, gy):
    _sky_fill(A, gx, gy, "S0", "S1", 0.05, 1)
    _put(A, 5, 4, "W2"); _put(A, 11, 9, "RC"); _put(A, 8, 12, "RM")


@tile("sky_star_b")
def _sky_star_b(A, gx, gy):
    _sky_fill(A, gx, gy, "S1", "S0", 0.05, 2)
    _put(A, 10, 3, "RC"); _put(A, 4, 10, "W2"); _put(A, 7, 7, "W1")


_BAT = [(-3, 1), (-2, 0), (-1, 1), (0, 2), (1, 1), (2, 0), (3, 1)]


@tile("bat_a")
def _bat_a(A, gx, gy):
    _sky_fill(A, gx, gy, "S1", "S2", 0.06, 1)
    for dx, dy in _BAT:
        _put(A, 8 + dx, 7 + dy, "K1")


@tile("bat_b")
def _bat_b(A, gx, gy):
    _sky_fill(A, gx, gy, "S1", "S0", 0.06, 2)
    for dx, dy in _BAT:
        _put(A, 9 + dx, 10 + dy, "K1")
    for dx, dy in _BAT:                       # un segundo planeador, mas lejano
        _put(A, 4 + dx, 4 + dy, "K0")


def _cloud_strip(warm_rim: bool) -> np.ndarray:
    """Una nube vaporosa 48x16 (3 tiles de ancho) cortada en l/m/r para que se reconecten."""
    B = np.zeros((TILE, 48, 3), np.uint8)
    base_sky = "S2" if warm_rim else "S1"
    for y in range(TILE):
        for x in range(48):
            B[y, x] = PALETTE["S1" if hash01(x, y, 6) < 0.12 else base_sky]
    cx, cy, rx, thick = 24, 8, 22, 3
    for y in range(cy - thick, cy + thick + 1):
        for x in range(cx - rx, cx + rx + 1):
            if not (0 <= x < 48 and 0 <= y < TILE):
                continue
            fx = (x - cx) / rx
            prof = max(0.0, 1 - fx * fx) ** 0.6
            half = prof * thick
            dy = y - cy
            if abs(dy) > half + 0.5:
                continue
            if hash01(x, y, 5) > 0.45 + 0.4 * prof:
                continue
            if dy >= half - 1.2:
                base = ("S5" if warm_rim else "S4") if prof > 0.5 else "S4"
            elif dy <= -half + 1.0:
                base = "S2"
            else:
                base = "S3"
            B[y, x] = PALETTE[base]
    for x in range(cx - rx, cx + rx + 1):
        prof = max(0.0, 1 - ((x - cx) / rx) ** 2) ** 0.6
        yy = cy + int(prof * thick)
        if 0 <= x < 48 and 0 <= yy < TILE and prof > 0.4 and hash01(x, yy, 9) > 0.55:
            B[yy, x] = PALETTE["W0" if warm_rim else "W1"]
    if warm_rim:                              # borde naranja ardiente en la cresta iluminada
        for x in range(cx - rx, cx + rx + 1):
            prof = max(0.0, 1 - ((x - cx) / rx) ** 2) ** 0.6
            yy = cy - int(prof * thick)
            if 0 <= x < 48 and 0 <= yy < TILE and prof > 0.25 and hash01(x, yy, 10) > 0.4:
                B[yy, x] = PALETTE["S5"]
    return B


_CLOUD = _cloud_strip(False)
_CLOUD_RIM = _cloud_strip(True)


def _cloud_slice(strip, c0):
    def fn(cell, gx, gy):
        cell[:] = strip[:, c0:c0 + TILE]
    return fn


_register("cloud_l", _cloud_slice(_CLOUD, 0))
_register("cloud_m", _cloud_slice(_CLOUD, 16))
_register("cloud_r", _cloud_slice(_CLOUD, 32))
_register("cloud_rim_l", _cloud_slice(_CLOUD_RIM, 0))
_register("cloud_rim_m", _cloud_slice(_CLOUD_RIM, 16))
_register("cloud_rim_r", _cloud_slice(_CLOUD_RIM, 32))


def _cloud_soft_strip() -> np.ndarray:
    """Una nube crepuscular 48x16 iluminada por el atardecer sobre fondo
    TRANSPARENTE (negro).

    A diferencia de las nubes de BG_Far de arriba (que llevan su propia base
    de cielo y por eso solo pueden colocarse sobre una banda cuyo tono
    coincida), esta esta pensada para BG_Mid: sus pixeles vacios se quedan
    negro puro -> transparente -> compone sobre CUALQUIER banda de cielo
    dentro de la ventana de camara sin costura rectangular de tono base.
    Copa fria en sombra (S2), cuerpo rosado (S3), parte inferior calida
    iluminada por el atardecer (S4/S5)."""
    B = np.zeros((TILE, 48, 3), np.uint8)      # black == transparent
    cx, cy, rx, thick = 24, 9, 21, 3
    for y in range(TILE):
        for x in range(48):
            fx = (x - cx) / rx
            prof = max(0.0, 1 - fx * fx) ** 0.6
            half = prof * thick
            dy = y - cy
            if abs(dy) > half + 0.4:
                continue
            if hash01(x, y, 6) > 0.52 + 0.42 * prof:
                continue                       # borde irregular y suave (sigue transparente)
            if dy <= -half + 1.0:
                base = "S2"                    # copa fria en sombra
            elif dy >= half - 1.3:
                base = "S5" if prof > 0.55 else "S4"   # vientre calido iluminado por el atardecer
            else:
                base = "S3"                    # cuerpo rosado
            B[y, x] = PALETTE[base]
    for x in range(cx - rx, cx + rx + 1):      # un hilo de cresta iluminado captando la ultima luz
        prof = max(0.0, 1 - ((x - cx) / rx) ** 2) ** 0.6
        yy = cy - int(prof * thick)
        if 0 <= x < 48 and 0 <= yy < TILE and prof > 0.35 and hash01(x, yy, 10) > 0.5:
            B[yy, x] = PALETTE["W0"]
    return B


_CLOUD_SOFT = _cloud_soft_strip()
_register("cloud_soft_l", _cloud_slice(_CLOUD_SOFT, 0))
_register("cloud_soft_m", _cloud_slice(_CLOUD_SOFT, 16))
_register("cloud_soft_r", _cloud_slice(_CLOUD_SOFT, 32))


@tile("bat_soft")
def _bat_soft(A, gx, gy):
    # Par de murcielagos con fondo transparente (BG_Mid) para que se deslicen
    # sobre el cielo crepuscular dentro de la ventana sin un parche de tono
    # base. Dos siluetas oscuras a distintas profundidades.
    A[:] = BLACK
    for dx, dy in _BAT:
        _put(A, 9 + dx, 6 + dy, "K1")
    for dx, dy in _BAT:
        _put(A, 4 + dx, 11 + dy, "K0")


# ===========================================================================
# CELESTIAL + SILUETA DISTANTE  (ronda-6 "vista real": llenar el 65% superior
# del cuadro 800x600 -- TODA la altura del mapa esta en pantalla, no una
# ventana 320x224. Todos estos son overlays de fondo TRANSPARENTE para BG_Mid,
# para que compongan sobre la rampa de cielo de BG_Far sin parche de tono
# base, exactamente como cloud_soft / bat_soft.)
# ===========================================================================
def _build_moon() -> np.ndarray:
    """Una gran luna crepuscular baja (3x3 = 48x48): disco palido y frio, un
    terminador gibante suave (iluminado arriba-izquierda, en sombra
    abajo-derecha), un par de crateres tenues y un halo frio con dither --
    todo sobre fondo transparente (negro) para que cuelgue en el cielo indigo
    superior. La protagonista de la vista superior."""
    B = np.zeros((48, 48, 3), np.uint8)          # black == transparent
    cx, cy, rad = 23, 23, 19
    for y in range(48):
        for x in range(48):
            dx, dy = x - cx, y - cy
            d2 = dx * dx + dy * dy
            if d2 <= rad * rad:
                # luz desde arriba-izquierda; mares moteados y suaves por toda la cara
                lum = 0.60 - 0.42 * (dx / rad) - 0.42 * (dy / rad)
                lum += (hash01(x, y, 400) - 0.5) * 0.14
                if lum > 0.92:
                    t = "W2"                      # corona iluminada brillante
                elif lum > 0.60:
                    t = "W1"
                elif lum > 0.34:
                    t = "C0"                      # cuerpo crema
                else:
                    t = "RM"                      # limbo frio en sombra (terminador)
                B[y, x] = PALETTE[t]
            else:
                d = math.sqrt(d2)                 # halo frio con dither, adelgazandose
                if d < rad + 7:
                    falloff = 1.0 - (d - rad) / 7.0
                    if hash01(x, y, 401) < 0.30 * falloff:
                        B[y, x] = PALETTE["RC"]   # resplandor azul frio (protegido de despeckle)
    # crateres tenues: manchas tostado-frio de >=2px para que despeckle las conserve
    for mx, my, mr in [(18, 21, 3), (30, 27, 2), (26, 15, 2), (15, 14, 2)]:
        for yy in range(my - mr, my + mr):
            for xx in range(mx - mr, mx + mr):
                if (xx - mx) ** 2 + (yy - my) ** 2 <= mr * mr and \
                        (xx - cx) ** 2 + (yy - cy) ** 2 <= (rad - 2) ** 2:
                    B[yy, xx] = PALETTE["C1"]
    return B


register_block("moon", 3, 3, _build_moon)


@tile("star_cluster_a")
def _star_cluster_a(A, gx, gy):
    # Cumulo de estrellas transparente (BG_Mid): unos pocos puntos tenues en
    # colores de acento protegidos (sobreviven al despeckle) para que el cielo
    # alto no sea una banda vacia.
    A[:] = BLACK
    _put(A, 4, 3, "W2"); _put(A, 11, 6, "W1"); _put(A, 7, 12, "RC")


@tile("star_cluster_b")
def _star_cluster_b(A, gx, gy):
    A[:] = BLACK
    _put(A, 3, 9, "W1"); _put(A, 9, 4, "W2")
    _put(A, 13, 12, "RM"); _put(A, 6, 7, "RC")


def _cloud_high_strip() -> np.ndarray:
    """Una nube alta FRIA de 48x16 sobre fondo transparente (BG_Mid): borde frio
    iluminado por la luna arriba (RC), cuerpo purpura (S2), parte inferior fria
    oscura (S1). Distinta de las nubes calidas del horizonte -- estas flotan
    alto en el cielo indigo, a distintas altitudes."""
    B = np.zeros((TILE, 48, 3), np.uint8)
    cx, cy, rx, thick = 24, 8, 21, 3
    for y in range(TILE):
        for x in range(48):
            fx = (x - cx) / rx
            prof = max(0.0, 1 - fx * fx) ** 0.6
            half = prof * thick
            dy = y - cy
            if abs(dy) > half + 0.4:
                continue
            if hash01(x, y, 6) > 0.52 + 0.40 * prof:
                continue                          # borde irregular y suave (sigue transparente)
            if dy <= -half + 1.0:
                base = "RC"                       # corona fria iluminada por la luna
            elif dy >= half - 1.2:
                base = "S1"                       # parte inferior fria oscura
            else:
                base = "S2"                       # cuerpo purpura
            B[y, x] = PALETTE[base]
    for x in range(cx - rx, cx + rx + 1):         # un hilo de borde frio en la cresta
        prof = max(0.0, 1 - ((x - cx) / rx) ** 2) ** 0.6
        yy = cy - int(prof * thick)
        if 0 <= x < 48 and 0 <= yy < TILE and prof > 0.35 and hash01(x, yy, 11) > 0.5:
            B[yy, x] = PALETTE["RM"]
    return B


_CLOUD_HIGH = _cloud_high_strip()
_register("cloud_high_l", _cloud_slice(_CLOUD_HIGH, 0))
_register("cloud_high_m", _cloud_slice(_CLOUD_HIGH, 16))
_register("cloud_high_r", _cloud_slice(_CLOUD_HIGH, 32))


def _ridge_far(A, gx, gy, salt, phase):
    # Una linea de cresta/bosquecillo lejano para el SEGUNDO plano de
    # profundidad (el mas distante). Se ubica alto en el cielo, bien encima
    # del bosque cercano, para que con el hueco de cielo entre ambos la
    # composicion se lea con 3 planos. Deliberadamente de BAJO CONTRASTE: un
    # violeta apenas un poco mas claro que el cielo S2 (perspectiva
    # atmosferica) -- un dither ordenado S2->S3 con un borde frio RM,
    # transparente por encima de la cresta.
    A[:] = BLACK
    for x in range(TILE):
        gxx = gx + x
        crest = 5 + int(3 * hash01(gxx, 0, salt)) + int(2 + 2 * math.sin(gxx * 0.35 + phase))
        crest = max(2, min(13, crest))
        for y in range(crest, TILE):
            t = (y - crest) / max(1, TILE - crest)     # mas claro en la cresta, se funde hacia abajo
            A[y, x] = PALETTE[bayer_dither(gxx, gy + y, "S3", "S2", 0.35 + 0.5 * t)]
        if hash01(gxx, 0, salt + 9) > 0.45:            # borde frio captando el cielo
            A[crest, x] = PALETTE["RM"]


@tile("ridge_far_a")
def _ridge_far_a(A, gx, gy):
    _ridge_far(A, gx, gy, 51, 0.0)


@tile("ridge_far_b")
def _ridge_far_b(A, gx, gy):
    _ridge_far(A, gx, gy, 57, 2.6)


@tile("ridge_haze")
def _ridge_haze(A, gx, gy):
    # La fila de cuerpo DEBAJO de la cresta de la cordillera: un desvanecido
    # ordenado desde el tono de la cresta (S3) arriba de vuelta al cielo S2
    # abajo, para que la cordillera distante se disuelva en el crepusculo en
    # vez de terminar en una linea dura.
    for y in range(TILE):
        t = y / (TILE - 1)
        for x in range(TILE):
            A[y, x] = PALETTE[bayer_dither(gx + x, gy + y, "S3", "S2", 0.15 + 0.85 * t)]


@tile("campus_far")
def _campus_far(A, gx, gy):
    # Una silueta de campus distante asomando sobre la cordillera lejana: un
    # esbelto campanario con una capucha a dos aguas y un par de ranuras de
    # ventana iluminadas, mas una franja de techo colindante. El mismo violeta
    # desaturado que la cordillera (apenas mas claro que el cielo) para que
    # retroceda; borde RM, ventanitas calidas.
    A[:] = BLACK
    # techo colindante bajo (lado derecho), un toque mas claro que el cielo
    for x in range(9, TILE):
        for y in range(11, TILE):
            A[y, x] = PALETTE["S3" if hash01(gx + x, gy + y, 60) > 0.4 else "S2"]
    for x in range(9, TILE):                       # cumbrera del techo
        A[10, x] = PALETTE["RM"] if hash01(gx + x, 0, 61) > 0.5 else PALETTE["S3"]
    # campanario (cols 3..7), elevandose desde la fila 3 hasta abajo
    for y in range(4, TILE):
        for x in range(3, 8):
            A[y, x] = PALETTE["S3" if (x in (3, 7) or hash01(gx + x, gy + y, 62) > 0.5) else "S2"]
    for x in range(2, 9):                           # capucha a dos aguas
        A[3, x] = PALETTE["RM"]
    A[2, 5] = PALETTE["RM"]; A[1, 5] = PALETTE["RC"]   # remate
    _put(A, 5, 8, "W0"); _put(A, 5, 12, "W0")          # ranuras de ventana calidas y tenues
    _put(A, 4, 8, "F0"); _put(A, 6, 8, "F0")           # jambas de ventana (mas oscuras)
    return


# ===========================================================================
# BOSQUE LEJANO  (silueta violeta, borde frio brumoso en las copas)
# ===========================================================================
def _forest_top(A, gx, gy, salt, phase):
    # Todo por encima de la copa irregular se queda TRANSPARENTE (negro) para
    # que la banda calida del horizonte detras de la linea de arboles se vea
    # a traves de los huecos entre las copas -- el atardecer siluetea el
    # bosque en vez del viejo parche purpura-frio (que competia con el cielo
    # calido que ahora esta justo detras).
    A[:] = BLACK
    for x in range(TILE):
        gxx = gx + x
        crown = 3 + int(4 * hash01(gxx, 0, salt)) + int(2 + 2 * math.sin(gxx * 0.5 + phase))
        crown = max(1, min(13, crown))
        for y in range(crown, TILE):
            A[y, x] = PALETTE["K1" if hash01(gxx, gy + y, 7) < 0.16 else "F0"]
    # luz de borde fria en el pixel F0 mas alto de cada columna (borde frio
    # contra el cielo calido -> la luz de borde crepuscular que pide el checklist)
    f0 = PALETTE["F0"]
    for x in range(TILE):
        for y in range(TILE):
            if tuple(A[y, x]) == f0:
                if hash01(gx + x, y, 302) > 0.5:
                    A[y, x] = PALETTE["RC" if hash01(gx + x, y, 303) > 0.5 else "V3"]
                break


@tile("forest_top_a")
def _ft_a(A, gx, gy):
    _forest_top(A, gx, gy, 31, 0.0)


@tile("forest_top_b")
def _ft_b(A, gx, gy):
    _forest_top(A, gx, gy, 37, 2.1)


@tile("forest_top_c")
def _ft_c(A, gx, gy):
    _forest_top(A, gx, gy, 41, 4.2)


@tile("forest_fill")
def _forest_fill(A, gx, gy):
    # La fila de TRANSICION CON DITHER entre la linea de arboles oscura y el
    # prado verde debajo: un desvanecido ordenado (Bayer) desde la masa
    # arborea violeta (F0) arriba hasta el VERDE crepuscular (V1) abajo -- para
    # que el bosque se funda HACIA ABAJO en el cesped (y no en una banda de
    # bruma azul, que se leia como una franja apilada). Un poco de textura de
    # follaje + alguna mota de bruma lo mantiene organico.
    for y in range(TILE):
        t = y / (TILE - 1)
        for x in range(TILE):
            base = bayer_dither(gx + x, gy + y, "F0", "V1", 0.20 + 0.6 * t)
            r = hash01(gx + x, gy + y, 7)
            if r < 0.12:
                base = "V0"                       # mata de follaje oscuro
            elif r > 0.95:
                base = "S1"                        # mota de bruma dispersa (atmosfera)
            A[y, x] = PALETTE[base]


@tile("forest_canopy")
def _forest_canopy(A, gx, gy):
    # La fila superior del cuerpo del bosque, justo debajo de la copa: capta un
    # poco del atardecer filtrandose sobre las copas de los arboles (motas
    # calidas O1 en lo alto) y lleva follaje extra iluminado para que el
    # limite horizonte-bosque tenga profundidad, no un borde duro.
    for y in range(TILE):
        for x in range(TILE):
            r = hash01(gx + x, gy + y, 7)
            if y < 3 and hash01(gx + x, gy + y, 310) > 0.86:
                A[y, x] = PALETTE["O1"]           # atardecer calido captado en las copas
            elif r < 0.14:
                A[y, x] = PALETTE["K1"]
            elif r < 0.55:
                A[y, x] = PALETTE["F0"]
            elif r < 0.78:
                A[y, x] = PALETTE["V0"]
            else:
                A[y, x] = PALETTE["V1"]


@tile("meadow_far")
def _meadow_far(A, gx, gy):
    # El cesped de FONDO distante al PIE del bosque, conectando la linea de
    # arboles con el suelo cercano -- bosque -> cesped -> primer plano, como
    # en la vineta. RONDA-7 (arreglo de legibilidad pedido por el usuario):
    # deliberadamente OSCURO + FRIO (violeta-desaturado) para que RETROCEDA y
    # nunca compita con el cesped transitable iluminado que tiene delante.
    # Sesgado hacia el FONDO de la rampa vegetal (V0/V1) con recesion violeta
    # fria (F0) y un susurro de bruma (S1) a lo largo de la parte superior --
    # SIN hojas brillantes V3 (esas ahora pertenecen exclusivamente al piso
    # transitable, para que el ojo lea "fondo" aqui y "piso" alla).
    for y in range(TILE):
        for x in range(TILE):
            r = hash01(gx + x, gy + y, 330)
            if y < 2 and r > 0.55:
                base = "S1"                       # bruma fria fundiendose hacia la linea de arboles
            elif r < 0.40:
                base = "V1"                       # pasto crepuscular (medio-oscuro)
            elif r < 0.66:
                base = "V0"                       # mata en sombra
            elif r < 0.84:
                base = "F0"                        # mota violeta de recesion fria
            else:
                base = "V2"                        # el ocasional destello tenue de luz
            A[y, x] = PALETTE[base]


@tile("meadow_base")
def _meadow_base(A, gx, gy):
    # La fila de cesped distante que TOCA el plano de suelo transitable
    # (colocada en la fila 34, justo encima del piso). Misma recesion oscura
    # y fria que meadow_far, pero sus 2px inferiores se profundizan hasta una
    # SOMBRA DE CONTACTO (V0 -> K1): el pliegue oscuro sutil donde el fondo
    # que retrocede se encuentra con el plano del piso, reforzando la
    # separacion del borde de cesped iluminado justo debajo (directiva de
    # sombra de contacto de la ronda-7). Los 14px superiores son identicos a
    # meadow_far para que las filas 33/34 se apilen sin costura.
    _meadow_far(A, gx, gy)
    for x in range(TILE):
        A[TILE - 2, x] = PALETTE["V0" if hash01(gx + x, TILE - 2, 331) > 0.4 else "K1"]
        A[TILE - 1, x] = PALETTE["K1"]


@tile("forest_gap")
def _forest_gap(A, gx, gy):
    for y in range(TILE):
        gapw = 2 + int(1.6 * (1 + math.sin(y * 0.4)))
        for x in range(TILE):
            if abs(x - 8) < gapw and y < 12:
                A[y, x] = PALETTE["S3" if hash01(gx + x, gy + y, 8) < 0.6 else "S2"]
            else:
                A[y, x] = PALETTE["K1" if hash01(gx + x, gy + y, 7) < 0.18 else "F0"]
    for x in range(TILE):                     # maleza captando la ultima luz
        if hash01(gx + x, 0, 57) > 0.55:
            _put(A, x, 15, "V1")
            if hash01(gx + x, 1, 57) > 0.7:
                _put(A, x, 14, "V2")


# ===========================================================================
# VEGETACION MEDIA  (setos + arbol grande)
# ===========================================================================
@tile("hedge_fill")
def _hedge_fill(A, gx, gy):
    for y in range(TILE):
        for x in range(TILE):
            r = hash01(gx + x, gy + y, 103)
            if r > 0.82:
                t = "V2"
            elif r < 0.12:
                t = "V0"
            else:
                t = "V1"
            A[y, x] = PALETTE[t]


def _hedge_top(A, gx, gy, salt):
    for x in range(TILE):
        gxx = gx + x
        top = 2 + int(2.5 * (1 + math.sin(gxx * 0.5 + salt)))
        for y in range(TILE):
            if y < top:
                A[y, x] = PALETTE["V0"]
            elif y <= top + 1:
                if hash01(gxx, y, 106 + salt) > 0.82:
                    A[y, x] = PALETTE["RC"]           # reflejo frio crepuscular en la cresta
                else:
                    A[y, x] = PALETTE["V3" if hash01(gxx, y, 107) > 0.5 else "V2"]
            else:
                r = hash01(gxx, gy + y, 103 + salt)
                A[y, x] = PALETTE["V2" if r > 0.78 else ("V0" if r < 0.12 else "V1")]


@tile("hedge_top_a")
def _hedge_top_a(A, gx, gy):
    _hedge_top(A, gx, gy, 0)


@tile("hedge_top_b")
def _hedge_top_b(A, gx, gy):
    _hedge_top(A, gx, gy, 2)


@tile("hedge_flower")
def _hedge_flower(A, gx, gy):
    _hedge_fill(A, gx, gy)
    for dx, dy in [(0, 0), (1, 0), (0, 1), (-1, 0)]:
        _put(A, 8 + dx, 7 + dy, "P0")
    _put(A, 9, 6, "P1"); _put(A, 7, 8, "V2")
    _put(A, 4, 11, "P0"); _put(A, 5, 11, "P1")


@tile("bush")
def _bush(A, gx, gy):
    # Un solo arbusto crepuscular redondeado, enraizado en la parte inferior
    # del tile (esquinas transparentes -> compone sobre el cesped/suelo). Se
    # usa como un acento PUNTUAL de pradera en vez de una banda continua de
    # seto, y con un volumen redondeado nunca se lee como un cubo verde
    # flotante. Iluminado por el crepusculo arriba-derecha, oscuro por debajo.
    A[:] = BLACK
    cx, cy, rx, ry = 8, 11, 7, 6
    for y in range(TILE):
        for x in range(TILE):
            nx = (x - cx) / rx
            ny = (y - cy) / ry
            edge = 1.0 + 0.22 * (hash01(x, y, 340) - 0.5) * 2
            if nx * nx + ny * ny <= edge and y <= 15:
                r = hash01(gx + x, gy + y, 341)
                lum = 0.5 - 0.32 * ny - 0.16 * nx + (r - 0.5) * 0.4
                # RONDA-7: el arbusto pegado al suelo mantiene su saturacion
                # pero su luminosidad esta LIMITADA POR DEBAJO del cesped
                # transitable iluminado -- el tono iluminado tope en V2 (solo
                # una punta V3 rara y dispersa), con violeta frio F0 en la
                # sombra profunda del nucleo para la recesion crepuscular.
                # Nunca debe leerse tan brillante como el piso donde para el
                # jugador.
                if lum > 0.80 and hash01(x, y, 344) > 0.6:
                    t = "V3"                      # punta calida rara (dispersa)
                elif lum > 0.50:
                    t = "V2"
                elif lum > 0.28:
                    t = "V1"
                elif lum > 0.12:
                    t = "V0"
                else:
                    t = "F0"                      # sombra violeta fria del nucleo
                A[y, x] = PALETTE[t]
    if hash01(gx, 0, 342) > 0.5:                  # un par de bayas/flores crepusculares
        _put(A, 6, 9, "P0"); _put(A, 10, 8, "P1")


def _build_tree() -> np.ndarray:
    B = np.zeros((64, 64, 3), np.uint8)       # zeros == black == empty corners
    cx, cy, rx, ry = 32, 25, 27, 23
    for y in range(64):
        for x in range(64):
            nx = (x - cx) / rx
            ny = (y - cy) / ry
            d = nx * nx + ny * ny
            edge = (1.0 + 0.30 * (hash01(x // 2, y // 2, 80) - 0.5) * 2
                    + 0.12 * math.sin(x * 0.6) + 0.12 * math.sin(y * 0.7))
            if d <= edge:
                r = hash01(x, y, 81)
                lum = 0.52 - 0.34 * ny - 0.20 * nx + (r - 0.5) * 0.42
                if d > edge - 0.16 and lum > 0.60 and hash01(x, y, 82) > 0.5:
                    t = "V3"                  # puntas de borde iluminadas por el crepusculo (arriba-derecha)
                elif lum > 0.60:
                    t = "V2"
                elif lum > 0.40:
                    t = "V1"
                else:
                    t = "V0"
                B[y, x] = PALETTE[t]
    # tronco + un par de raices
    for y in range(43, 64):
        for x in range(29, 35):
            r = hash01(x, y, 83)
            B[y, x] = PALETTE["O0" if (x < 31 or r < 0.32) else ("O1" if r < 0.8 else "O2")]
    for (sx, sy, dx) in [(29, 60, -1), (34, 60, 1)]:
        x, y = sx, sy
        for _ in range(4):
            _put(B, x, y, "O0"); x += dx; y += 1
    return B


register_block("tree_c", 4, 4, _build_tree, sep="")


def _trunk(A, gx, gy, knot):
    A[:] = BLACK
    for y in range(TILE):
        for x in range(4, 12):
            r = hash01(gx + x, gy + y, 83)
            A[y, x] = PALETTE["O0" if (x < 7 or r < 0.30) else ("O1" if r < 0.78 else "O2")]
    for y in range(0, TILE, 3):               # ranuras de corteza
        _put(A, 5, y, "O0"); _put(A, 9, y, "O0")
    if knot:
        _put(A, 8, 8, "O0"); _put(A, 8, 7, "K1"); _put(A, 9, 8, "O0")


@tile("tree_trunk_a")
def _trunk_a(A, gx, gy):
    _trunk(A, gx, gy, False)


@tile("tree_trunk_b")
def _trunk_b(A, gx, gy):
    _trunk(A, gx, gy, True)


# ===========================================================================
# SUELO JUGABLE  (pasto / sendero de tierra / acera / guijarros)
# ===========================================================================
def _grass(A, gx, gy, salt):
    for y in range(TILE):
        for x in range(TILE):
            r = hash01(gx + x, gy + y, 11 + salt)
            if r > 0.90:
                t = "V3"
            elif r > 0.60:
                t = "V2"
            elif r > 0.22:
                t = "V1"
            else:
                t = "V0"
            A[y, x] = PALETTE[t]


@tile("grass_a")
def _grass_a(A, gx, gy):
    _grass(A, gx, gy, 0)


@tile("grass_b")
def _grass_b(A, gx, gy):
    _grass(A, gx, gy, 1)


@tile("grass_c")
def _grass_c(A, gx, gy):
    _grass(A, gx, gy, 2)


@tile("grass_bald")
def _grass_bald(A, gx, gy):
    _grass(A, gx, gy, 0)
    for y in range(TILE):
        for x in range(TILE):
            if ((x - 8) / 7.0) ** 2 + ((y - 9) / 5.0) ** 2 < 1.0 and hash01(gx + x, gy + y, 104) > 0.28:
                A[y, x] = PALETTE["O1" if hash01(gx + x, gy + y, 105) > 0.5 else "G1"]


# ---------------------------------------------------------------------------
# Cesped TRANSITABLE (fila de piso Terrain). Arreglo de legibilidad de la
# ronda-7 pedido por el usuario: el plano donde para el jugador era
# indistinguible del cesped de fondo (misma rampa vegetal). Estos tiles son
# deliberadamente la vegetacion MAS CLARA + MAS CALIDA de la escena y llevan
# un BORDE SUPERIOR ILUMINADO de 2px (el clasico borde de plataforma), para
# que la linea del piso se lea AL INSTANTE separada del fondo mas oscuro y
# frio (meadow_far / meadow_base / forest). Los viejos ``grass_*`` de arriba
# se quedan en el atlas como reserva de pasto de fondo; solo estos
# ``grass_walk_*`` van en la fila transitable.
# ---------------------------------------------------------------------------
def _grass_walk(A, gx, gy, salt):
    # Cesped transitable soleado: cuerpo sesgado hacia la CIMA de la rampa
    # vegetal (V2/V3 dominante) con un destello ocre calido disperso para dar
    # calidez (con moderacion).
    for y in range(TILE):
        for x in range(TILE):
            r = hash01(gx + x, gy + y, 11 + salt)
            if r > 0.72:
                t = "V3"                          # hojas iluminadas (dominante)
            elif r > 0.34:
                t = "V2"                          # verde medio
            elif r > 0.10:
                t = "V1"                          # sombra dispersa
            else:
                t = "V0"                          # sombra profunda rara
            if hash01(gx + x, gy + y, 260 + salt) > 0.93:
                t = "O2"                          # mota calida soleada (calidez, dispersa)
            A[y, x] = PALETTE[t]
    # BORDE SUPERIOR ILUMINADO (rim): fila 0 = el verde mas calido con
    # destellos crema dispersos (el labio delantero captando el sol bajo);
    # fila 1 = verde mas claro fragmentado para que el borde tenga cuerpo sin
    # una linea mecanica solida. V3/C0/W1 son acentos protegidos de
    # despeckle, para que el borde sobreviva la limpieza por-tile como un
    # resalte continuo.
    for x in range(TILE):
        A[0, x] = PALETTE["C0" if hash01(gx + x, 0, 261 + salt) > 0.82 else "V3"]
        if hash01(gx + x, 1, 262 + salt) > 0.42:
            A[1, x] = PALETTE["V3"]
        if hash01(gx + x, 1, 263 + salt) > 0.93:
            A[1, x] = PALETTE["W1"]               # chispa calida ocasional en la cresta


@tile("grass_walk_a")
def _grass_walk_a(A, gx, gy):
    _grass_walk(A, gx, gy, 0)


@tile("grass_walk_b")
def _grass_walk_b(A, gx, gy):
    _grass_walk(A, gx, gy, 1)


@tile("grass_walk_c")
def _grass_walk_c(A, gx, gy):
    _grass_walk(A, gx, gy, 2)


@tile("grass_walk_bald")
def _grass_walk_bald(A, gx, gy):
    # Parche de tierra desgastado sobre el cesped transitable (conserva el
    # borde iluminado: la elipse esta en el interior del tile, filas 4-14,
    # para que las filas del borde superior queden intactas).
    _grass_walk(A, gx, gy, 0)
    for y in range(TILE):
        for x in range(TILE):
            if ((x - 8) / 7.0) ** 2 + ((y - 9) / 5.0) ** 2 < 1.0 and hash01(gx + x, gy + y, 104) > 0.28:
                A[y, x] = PALETTE["O1" if hash01(gx + x, gy + y, 105) > 0.5 else "G1"]


def _dirt(A, gx, gy, salt):
    for y in range(TILE):
        for x in range(TILE):
            r = hash01(gx + x, gy + y, 110 + salt)
            if r > 0.90:
                t = "G1"
            elif r > 0.55:
                t = "O1"
            elif r > 0.22:
                t = "O0"
            else:
                t = "K1"
            A[y, x] = PALETTE[t]
    for k in range(3):                        # guijarros dispersos
        px = int(15 * hash01(gx + k * 3, salt, 111))
        py = int(15 * hash01(gy + k * 5, salt, 112))
        _put(A, px, py, "G2")


@tile("dirt_path_a")
def _dirt_a(A, gx, gy):
    _dirt(A, gx, gy, 0)


@tile("dirt_path_b")
def _dirt_b(A, gx, gy):
    _dirt(A, gx, gy, 1)


def _path_border(gy: int, y: int) -> int:
    """Columna de limite irregular pasto/tierra compartida por ambos tiles de borde de sendero."""
    return 8 + int(2.5 * math.sin((gy + y) * 0.7)) + int((hash01(gy + y, 0, 120) - 0.5) * 4)


@tile("path_edge_l")
def _path_edge_l(A, gx, gy):
    # pasto a la IZQUIERDA, tierra a la DERECHA (limite irregular)
    for y in range(TILE):
        border = _path_border(gy, y)
        for x in range(TILE):
            if x < border:
                A[y, x] = PALETTE["V2" if hash01(gx + x, gy + y, 11) > 0.55 else "V1"]
            else:
                A[y, x] = PALETTE["O1" if hash01(gx + x, gy + y, 110) > 0.5 else "O0"]


@tile("path_edge_r")
def _path_edge_r(A, gx, gy):
    # tierra a la IZQUIERDA, pasto a la DERECHA
    for y in range(TILE):
        border = _path_border(gy, y)
        for x in range(TILE):
            if x < border:
                A[y, x] = PALETTE["O1" if hash01(gx + x, gy + y, 110) > 0.5 else "O0"]
            else:
                A[y, x] = PALETTE["V2" if hash01(gx + x, gy + y, 11) > 0.55 else "V1"]


def _slab(A, gx, gy, salt):
    for y in range(TILE):
        for x in range(TILE):
            b = 0.5 + 0.5 * hash01((gx + x) // 13, (gy + y) // 9, 111 + salt)
            b += (hash01(gx + x, gy + y, 112) - 0.5) * 0.22
            if b < 0.30:
                t = "G0"
            elif b < 0.55:
                t = "G1"
            elif b < 0.82:
                t = "G2"
            else:
                t = "G3"
            A[y, x] = PALETTE[t]
    for y in range(TILE):                     # juntas arriba+izquierda -> cuadricula de pavimento
        A[y, 0] = PALETTE["G0"]
    for x in range(TILE):
        A[0, x] = PALETTE["G0"]


@tile("sidewalk_slab_a")
def _slab_a(A, gx, gy):
    _slab(A, gx, gy, 0)


@tile("sidewalk_slab_b")
def _slab_b(A, gx, gy):
    _slab(A, gx, gy, 3)


@tile("sidewalk_slab_c")
def _slab_c(A, gx, gy):
    _slab(A, gx, gy, 6)


@tile("sidewalk_crack")
def _sidewalk_crack(A, gx, gy):
    _slab(A, gx, gy, 0)
    x, y = 5, 2
    for _ in range(12):
        _put(A, x, y, "G0")
        y += 1
        x += 1 if hash01(x, y, 203) > 0.5 else 0
        if y >= TILE:
            break
    _put(A, 9, 13, "V2"); _put(A, 9, 12, "V3")   # maleza brotando de la grieta


@tile("sidewalk_moss")
def _sidewalk_moss(A, gx, gy):
    _slab(A, gx, gy, 3)
    for y in range(TILE):                     # musgo trepando por la junta izquierda
        if hash01(gx, gy + y, 143) > 0.5:
            _put(A, 1, y, "V1" if hash01(gx, gy + y, 145) > 0.5 else "V2")
    for x in range(TILE):                     # y la junta superior
        if hash01(gx + x, gy, 146) > 0.55:
            _put(A, x, 1, "V2")


@tile("sidewalk_broken_corner")
def _sidewalk_broken_corner(A, gx, gy):
    _slab(A, gx, gy, 6)
    for dx, dy in [(0, 0), (1, 0), (0, 1), (2, 0), (1, 1), (0, 2), (2, 1)]:
        _put(A, dx, dy, "G0")                 # mordisco oscuro astillado
    _put(A, 3, 0, "G3"); _put(A, 0, 3, "G3")  # borde claro expuesto


@tile("pebbles")
def _pebbles(A, gx, gy):
    for y in range(TILE):
        for x in range(TILE):
            A[y, x] = PALETTE["G1" if hash01(gx + x, gy + y, 130) > 0.4 else "G0"]
    for k in range(6):
        px = int(15 * hash01(gx + k * 7, 0, 131))
        py = int(15 * hash01(gy + k * 5, 0, 132))
        _put(A, px, py, "G3" if hash01(px, py, 133) > 0.5 else "G0")
        _put(A, px, py + 1, "G0")


def _subsoil(A, gx, gy, deep: bool):
    # Suelo subterraneo bajo el piso transitable. Se oscurece hacia abajo (un
    # desvanecido Bayer), con piedras dispersas e hilos de raiz -> se lee como
    # tierra apisonada/lecho rocoso, no el "corcho" marron plano de antes.
    # `deep` = la fila mas baja (mas oscura, mas pedregosa).
    top, bot = ("O0", "K1") if not deep else ("K1", "K0")
    for y in range(TILE):
        t = y / (TILE - 1)
        for x in range(TILE):
            A[y, x] = PALETTE[bayer_dither(gx + x, gy + y, top, bot, 0.25 + 0.55 * t)]
    if not deep:                                  # hilos de raiz que llegan hacia abajo (suelo superior)
        for sx in (3, 11):
            x, y = sx, 0
            for _ in range(TILE):
                _put(A, x, y, "O0")
                y += 1
                x += 1 if hash01(gx + x, gy + y, 353) > 0.6 else 0
                if y >= TILE:
                    break
    for k in range(5 if not deep else 3):         # piedras incrustadas
        px = int(15 * hash01(gx + k * 4, 0, 351))
        py = int(15 * hash01(gy + k * 6, 0, 352))
        _put(A, px, py, "G1" if not deep else "G0")
        _put(A, min(15, px + 1), py, "G0")
        _put(A, px, min(15, py + 1), "G0")


@tile("subsoil_top")
def _subsoil_top(A, gx, gy):
    _subsoil(A, gx, gy, deep=False)


@tile("subsoil_deep")
def _subsoil_deep(A, gx, gy):
    # La fila MAS PROFUNDA en la base misma del cuadro: un desvanecido suave a
    # casi negro sin piedras/raices y sin patron de dither estampado -> se lee
    # como el suelo retrocediendo hacia la oscuridad (una continuacion del
    # subsuelo), no una banda de vacio con patron. Solo un susurro de K1
    # arriba mezclandose con K0 solido.
    for y in range(TILE):
        for x in range(TILE):
            if y < 2:
                c = "K1"
            elif y < 4:
                c = bayer_dither(gx + x, gy + y, "K1", "K0", (y - 2) / 2.0)
            else:
                c = "K0"
            A[y, x] = PALETTE[c]


# ===========================================================================
# HASTIAL  (6x6 = 96x96): casa de fronton ocre, techo de lamina, oculo, arco
# ===========================================================================
def _build_hastial() -> np.ndarray:
    W = H = 96
    B = np.zeros((H, W, 3), np.uint8)
    HX0, HX1 = 12, 84
    PEAK_X, PEAK_Y = 48, 6
    WALL_TOP = 46
    GROUND = 90

    def wall_tone(x, y):
        tx = (x - HX0) / (HX1 - HX0)
        ty = (y - WALL_TOP) / (GROUND - WALL_TOP)
        lum = 0.56 + 0.16 * tx - 0.12 * ty
        # sombra del alero (voladizo del techo): una banda que abraza solo la
        # parte superior del CUERPO DE LA PARED. El triangulo del fronton
        # esta por encima de WALL_TOP y capta cielo abierto, asi que NO debe
        # oscurecerse (o se leeria marron en vez de mostaza).
        es_span = 10 + 3 * hash01(x, 0, 44)
        if y < WALL_TOP:
            es = 0.0
        else:
            es = max(0.0, min(1.0, (WALL_TOP + es_span - y) / es_span))
        lum -= 0.20 * es * es
        # moteado de estuco: el mismo campo de racimos de 3 octavas del que se
        # extrajo art_lib.mottle (sales 45/46/47) -- se reutiliza en vez de re-inlinearlo.
        lum += mottle(x, y, salt=45)
        base_prox = max(0.0, (ty - 0.42) / 0.58)
        corner = max(0.0, 1.0 - min(tx, 1.0 - tx) / 0.20)
        if hash01(x // 5, y // 4, 48) > 0.60:
            lum -= (0.10 + 0.16 * corner) * base_prox
        if hash01(x // 6, y // 3, 49) > 0.90:
            lum -= 0.10 * base_prox
        if lum < 0.34:
            return "O0"
        if lum < 0.54:
            return "O1"
        if lum < 0.78:
            return "O2"
        return "O3"

    # triangulo del fronton
    for y in range(PEAK_Y, WALL_TOP):
        frac = (y - PEAK_Y) / (WALL_TOP - PEAK_Y)
        halfw = frac * ((HX1 - HX0) / 2)
        for x in range(int(PEAK_X - halfw), int(PEAK_X + halfw)):
            B[y, x] = PALETTE[wall_tone(x, y)]
    # cuerpo de la pared
    for y in range(WALL_TOP, GROUND):
        for x in range(HX0, HX1):
            B[y, x] = PALETTE[wall_tone(x, y)]

    # remate del techo (lamina de terracota) + cenefa crema siguiendo ambas aguas
    ROOF_SHEET_H = 4                          # espesor de la banda de lamina de terracota
    FASCIA_H = 2                              # espesor de la tabla de la cenefa crema

    def roof_line(x):
        if x <= PEAK_X:
            t = (x - (HX0 - 6)) / (PEAK_X - (HX0 - 6))
        else:
            t = (x - (HX1 + 6)) / (PEAK_X - (HX1 + 6))
        t = max(0.0, min(1.0, t))
        return int(PEAK_Y + (WALL_TOP - PEAK_Y) * (1 - t))

    for x in range(HX0 - 6, HX1 + 6):
        ry = roof_line(x)
        for yy in range(ry, ry + ROOF_SHEET_H):
            if not (0 <= x < W):
                continue
            tone = "R2" if yy == ry else ("R1" if yy < ry + 2 else "R0")
            if (x % 4 == 0) and yy > ry:
                tone = "R0"                   # ranura de corrugado
            rp = hash01(x // 4, yy, 201)
            if rp > 0.93 and yy >= ry + 1:
                tone = "O1"                   # mancha de oxido
            elif rp < 0.05 and yy >= ry + 2:
                tone = "V1"                   # musgo en la lamina
            B[yy, x] = PALETTE[tone]
        for yy in range(ry + ROOF_SHEET_H, ry + ROOF_SHEET_H + FASCIA_H):  # cenefa crema
            if 0 <= x < W:
                B[yy, x] = PALETTE["C0" if yy < ry + ROOF_SHEET_H + 1 else "C1"]

    # OCULO: anillo de piedra + cielo crepuscular visto a traves
    ocx, ocy, orad = PEAK_X, 28, 8
    for y in range(ocy - orad - 1, ocy + orad + 2):
        for x in range(ocx - orad - 1, ocx + orad + 2):
            d = (x - ocx) ** 2 + (y - ocy) ** 2
            if d <= (orad - 2) ** 2:
                rel = (y - (ocy - orad)) / (2 * orad)
                B[y, x] = PALETTE["S1" if rel < 0.36 else ("S2" if rel < 0.62 else "S3")]
            elif d <= orad ** 2:
                B[y, x] = PALETTE["C0" if (x - ocx + y - ocy) > 0 else "C1"]
    for x in range(ocx - 5, ocx + 5):         # hojas asomando por arriba
        yy = ocy - orad + 2 + int(2 * hash01(x, 0, 51))
        if (x - ocx) ** 2 + (yy - ocy) ** 2 <= (orad - 3) ** 2:
            B[yy, x] = PALETTE["V1"]

    # Portal en ARCO: apertura apuntada, pasaje oscuro, puerta lejana calida
    acx, ahw = PEAK_X, 14
    spring_y, apex_y = 66, 48
    base_y = GROUND

    def arch_top(x):
        frac = abs(x - acx) / ahw
        if frac > 1:
            return None
        return int(spring_y - (spring_y - apex_y) * (1 - frac ** 1.7))

    far_cx, far_cy = acx, 78
    far_hw, far_hh = 4, 8
    for x in range(acx - ahw - 1, acx + ahw + 2):
        yt = arch_top(x)
        if yt is None:
            continue
        for y in range(yt, base_y):
            if abs(x - acx) >= ahw - 1 or y <= yt + 1:
                B[y, x] = PALETTE["O1" if hash01(x, y, 65) > 0.4 else "O0"]   # jamba
                continue
            dx = x - far_cx
            dy = y - far_cy
            if abs(dx) <= far_hw and abs(dy) <= far_hh and abs(dx) / far_hw + max(0, -dy) / far_hh < 1.05:
                # puerta lejana calida
                core = abs(dx) < far_hw - 1 and dy > -far_hh + 2
                B[y, x] = PALETTE["W1" if core else "W0"]
            else:
                # tunel oscuro con un hilo de piso calido convergente
                thread = abs(dx) <= 1 and y > far_cy
                if thread and hash01(x, y, 62) < 0.6:
                    B[y, x] = PALETTE["S5" if y > far_cy + 4 else "W0"]
                elif y < far_cy and hash01(x, y, 66) > 0.85:
                    B[y, x] = PALETTE["R0"]   # pared profunda calida tenue
                else:
                    B[y, x] = PALETTE["K0" if hash01(x, y, 61) > 0.3 else "K1"]
    # marco de piedra alrededor de la puerta lejana
    for y in range(far_cy - far_hh, far_cy + far_hh + 1):
        for x in range(far_cx - far_hw - 1, far_cx + far_hw + 2):
            dx = x - far_cx
            if abs(dx) == far_hw + 1 and -far_hh < (y - far_cy) <= far_hh:
                if arch_top(x) is not None and y >= arch_top(x):
                    B[y, x] = PALETTE["C1"]

    # hiedra en la esquina izquierda
    for y in range(WALL_TOP - 2, GROUND):
        for x in range(HX0 - 1, HX0 + 5 + int(2 * math.sin(y * 0.4))):
            if x >= HX0 - 1 and hash01(x, y, 71) > 0.52:
                B[y, x] = PALETTE["V1" if hash01(x, y, 72) > 0.5 else "V2"]

    # unas pocas grietas capilares (evitando la boca del arco)
    rng = np.random.default_rng(11)

    def clear(x, y):
        return not (acx - ahw < x < acx + ahw and y > apex_y)

    for _ in range(6):
        x = int(rng.integers(HX0 + 6, HX1 - 6))
        y = int(rng.integers(WALL_TOP + 4, GROUND - 16))
        for _ in range(int(rng.integers(8, 18))):
            if HX0 < x < HX1 and WALL_TOP < y < GROUND and clear(x, y):
                B[y, x] = PALETTE["O0" if hash01(x, y, 202) > 0.35 else "K1"]
            if hash01(x, y, 203) > 0.22:
                y += 1
            x += int(rng.integers(-1, 2))

    # 2 desconchados (revoque astillado -> yeso palido)
    for (sx, sy, rw, rh) in [(HX1 - 10, GROUND - 26, 3, 2), (HX0 + 8, 60, 2, 2)]:
        for dy in range(-rh, rh + 1):
            for dx in range(-rw, rw + 1):
                if (dx / rw) ** 2 + (dy / rh) ** 2 > 1.0:
                    continue
                x, y = sx + dx, sy + dy
                if not (HX0 < x < HX1 and WALL_TOP < y < GROUND and clear(x, y)):
                    continue
                if dy >= rh - 1:
                    B[y, x] = PALETTE["O0"]
                elif (dx / rw) ** 2 + (dy / rh) ** 2 > 0.58:
                    B[y, x] = PALETTE["O1"]
                else:
                    B[y, x] = PALETTE["PL" if hash01(x, y, 204) > 0.25 else "O2"]

    # musgo + maleza reconquistando la base
    for x in range(HX0, HX1):
        if acx - ahw < x < acx + ahw:
            continue
        r = hash01(x, 0, 205)
        if r > 0.42:
            mh = 2 + int(2 * hash01(x, 1, 206))
            for i in range(mh):
                _put(B, x, GROUND - 1 - i, "V1" if i < mh - 1 else "V2")
        if r > 0.80:
            hh = 3 + int(2 * hash01(x, 2, 82))
            for i in range(hh):
                _put(B, x, GROUND - 1 - i, "V2" if i < hh - 1 else "V3")

    return B


register_block("hast", 6, 6, _build_hastial)


@tile("arch_glow_top")
def _arch_glow_top(A, gx, gy):
    # mitad superior de la puerta lejana calida: arco apuntado + silueta de follaje
    A[:] = BLACK
    cx = 8
    for y in range(TILE):
        hw = 3 + int(4 * (y / TILE))
        for x in range(TILE):
            dx = x - cx
            if abs(dx) <= hw:
                if abs(dx) >= hw - 1 or y < 2:
                    A[y, x] = PALETTE["C1"]           # derrame de piedra / parte superior
                else:
                    A[y, x] = PALETTE["W1" if abs(dx) < hw - 3 else "W0"]
    for x in range(cx - 4, cx + 5):           # hojas siluetadas arriba
        if hash01(gx + x, 0, 51) > 0.5:
            _put(A, x, 2, "V0")


@tile("arch_glow_bottom")
def _arch_glow_bottom(A, gx, gy):
    # mitad inferior: nucleo calido desvaneciendose a una base de piedra oscura
    A[:] = BLACK
    cx, hw = 8, 7
    for y in range(TILE):
        for x in range(TILE):
            dx = x - cx
            if abs(dx) <= hw:
                if y >= TILE - 2:
                    A[y, x] = PALETTE["O0"]           # sombra del umbral
                elif abs(dx) >= hw - 1:
                    A[y, x] = PALETTE["C1"]
                else:
                    core = abs(dx) < hw - 3 and y < 10
                    A[y, x] = PALETTE["W1" if core else ("W0" if y < 12 else "S5")]


def _ivy(A, gx, gy, salt):
    A[:] = BLACK
    for y in range(TILE):
        cx = 8 + int(3 * math.sin(y * 0.5 + salt))
        for x in range(cx - 2, cx + 3):
            if hash01(gx + x, gy + y, 71 + salt) > 0.45:
                A[y, x] = PALETTE["V1" if hash01(gx + x, gy + y, 72) > 0.5 else "V2"]
        if y % 4 == 0:
            _put(A, cx + 2, y, "V3")          # una hoja iluminada por el crepusculo
        if y % 5 == 0:
            _put(A, cx - 2, y, "V0")


@tile("ivy_a")
def _ivy_a(A, gx, gy):
    _ivy(A, gx, gy, 0)


@tile("ivy_b")
def _ivy_b(A, gx, gy):
    _ivy(A, gx, gy, 3)


# ---------------------------------------------------------------------------
# CARA FRONTAL DEL ARCO  (FG_Overlay): el derrame de piedra del arco apuntado
# cercano que se dibuja POR DELANTE del jugador, 3 cols x 2 filas. Vacio
# (negro) dentro de la apertura y fuera de la silueta exterior para que solo
# las jambas de piedra/corona ocluyan.
# ---------------------------------------------------------------------------
def _build_arch_front() -> np.ndarray:
    W, H = 48, 32
    B = np.zeros((H, W, 3), np.uint8)
    cx = 24
    J_OUT, O_HW = 23.0, 15.0
    sp_o, sp_i, apex_i = 12, 15, 4

    def outer_hw(y):
        return J_OUT if y >= sp_o else J_OUT * (y / sp_o) ** 0.6

    def inner_hw(y):
        if y >= sp_i:
            return O_HW
        if y <= apex_i:
            return -1.0
        return O_HW * ((y - apex_i) / (sp_i - apex_i)) ** 0.6

    for y in range(H):
        oh, ih = outer_hw(y), inner_hw(y)
        for x in range(W):
            dx = abs(x - cx)
            if dx > oh or dx < ih:
                continue                      # vacio (negro)
            if dx >= oh - 1:
                c = "C1"                      # borde exterior iluminado por el cielo
            elif ih >= 0 and dx <= ih + 1:
                c = "O0"                      # derrame interior en sombra
            elif hash01(x, y, 204) > 0.9:
                c = "PL"                      # un desconchado astillado
            elif hash01(x, y, 45) > 0.7:
                c = "O2"                      # moteado de estuco
            else:
                c = "O1"
            B[y, x] = PALETTE[c]
    _rect(B, cx - 2, 0, cx + 2, 4, "O2")      # dovela clave en la corona
    _put(B, cx - 2, 0, "C1"); _put(B, cx + 1, 0, "C1")
    return B


_ARCH_FRONT = _build_arch_front()


def _archfront_slice(r0, c0):
    def fn(cell, gx, gy):
        cell[:] = _ARCH_FRONT[r0:r0 + TILE, c0:c0 + TILE]
    return fn


for _cc, _cn in ((0, "l"), (16, "m"), (32, "r")):
    _register(f"arch_front_{_cn}_top", _archfront_slice(0, _cc))
for _cc, _cn in ((0, "l"), (16, "m"), (32, "r")):
    _register(f"arch_front_{_cn}_bot", _archfront_slice(16, _cc))


# ===========================================================================
# BUNGALOW  (3x3 = 48x48): casa baja distante
# ===========================================================================
def _build_bungalow() -> np.ndarray:
    W = H = 48
    B = np.zeros((H, W, 3), np.uint8)
    bx0, bx1 = 4, 44
    roof_y, base_y = 14, 46
    for y in range(roof_y, base_y):           # cuerpo
        for x in range(bx0, bx1):
            B[y, x] = PALETTE["O1" if hash01(x, y, 31) > 0.4 else "O0"]
    for x in range(bx0 - 3, bx1 + 3):         # techo de lamina de poca pendiente
        ry = roof_y - int((x - (bx0 - 3)) * 0.06)
        for y in range(ry - 4, ry):
            if not (0 <= x < W):
                continue
            tone = "R1"
            if x % 3 == 0:
                tone = "R0"
            elif hash01(x // 4, y, 32) > 0.92:
                tone = "O1"
            B[y, x] = PALETTE[tone]
        if 0 <= x < W:
            B[ry, x] = PALETTE["C1"]          # linea de cenefa
    # puerta (oscura, ligeramente entreabierta)
    dx0 = 22
    _rect(B, dx0, base_y - 14, dx0 + 7, base_y, "K1")
    _rect(B, dx0 + 1, base_y - 13, dx0 + 5, base_y, "K0")
    _put(B, dx0 + 4, base_y - 7, "O3")        # destello de la manija
    return B


register_block("bung", 3, 3, _build_bungalow)


@tile("bung_win_lit")
def _bung_win_lit(A, gx, gy):
    A[:] = PALETTE["O1"]
    _rect(A, 2, 3, 14, 13, "K1")
    _rect(A, 3, 4, 13, 12, "W0")
    for y in range(4, 12):                    # travesano de ventana
        _put(A, 8, y, "K1")
    _put(A, 4, 8, "K1"); _put(A, 12, 8, "K1")
    _put(A, 3, 4, "W1")                       # destello calido


@tile("bung_win_board")
def _bung_win_board(A, gx, gy):
    A[:] = PALETTE["O1"]
    _rect(A, 2, 3, 14, 13, "K1")
    for i, yy in enumerate(range(4, 12, 2)):  # tablas
        _rect(A, 3, yy, 13, yy + 1, "O0")
    _put(A, 4, 3, "O0"); _put(A, 12, 12, "O0")


# ===========================================================================
# GAZEBO  (7x6 = 112x96): pabellon octagonal, techo conico rojo, postes, mesa
# ===========================================================================
def _build_gazebo() -> np.ndarray:
    W, H = 112, 96
    B = np.zeros((H, W, 3), np.uint8)
    cx = 56
    apex_y = 6
    eave_y = 50
    pad_y = 90
    post_top = 52
    half = 52                                 # media envergadura del techo en el alero
    lx, ly = cx, 60                           # farol colgante = la FUENTE DE LUZ interior

    # RONDA-8 (retroalimentacion del usuario: "el cuerpo del gazebo es una
    # masa oscura que se funde con el bosque oscuro detras"): el interior
    # ahora esta ILUMINADO DESDE ADENTRO por un farol colgante en vez de una
    # sombra plana. Un resplandor radial calido -- la MISMA rampa calida
    # W0/W1/W2 que usan las puertas en arco -- llena el pabellon, mas
    # brillante junto al farol y encharcandose HACIA ABAJO sobre el piso
    # (una caida elipse, sesgada hacia abajo), desvaneciendose hacia las
    # esquinas residuales en sombra (nunca negro puro, para que se mantenga
    # opaco, no transparente). El cuerpo se lee como una pieza escenica
    # resplandeciente; la mesa/banca de enfrente se leen como SILUETAS.
    for y in range(post_top, pad_y):
        for x in range(cx - 46, cx + 46):
            dx, dy = x - lx, y - ly
            ry = 15.0 if dy < 0 else 33.0     # la luz llega mas lejos HACIA ABAJO (se derrama al piso)
            g = 1.0 - math.sqrt((dx / 30.0) ** 2 + (dy / ry) ** 2)
            g += (float(BAYER_4X4[y & 3, x & 3]) - 0.5) * 0.14   # dither ordenado ("como los arcos")
            g += (hash01(x, y, 93) - 0.5) * 0.10                 # rasguno organico
            if g > 0.80:
                t = "W2"                      # nucleo calido ardiente cerca del farol
            elif g > 0.60:
                t = "W1"
            elif g > 0.42:
                t = "W0"
            elif g > 0.28:
                t = "S5"                      # halo naranja-atardecer calido
            elif g > 0.16:
                t = "S4"
            elif g > 0.06:
                t = "O1"                      # caida calida tenue
            else:
                t = "V0" if hash01(x, y, 93) > 0.5 else "K1"     # sombra residual (opaca, no negra)
            B[y, x] = PALETTE[t]

    # mesa de picnic + banca, CONTRALUZ -> SILUETAS oscuras contra el
    # resplandor, con un borde calido tenue donde la luz del farol envuelve
    # sus bordes superiores.
    _rect(B, cx - 16, 71, cx + 16, 77, "K1")          # tablero de la mesa (silueta oscura)
    _rect(B, cx - 16, 76, cx + 16, 77, "K0")          # sombra inferior
    for x in range(cx - 16, cx + 16):                 # borde calido a contraluz en el borde superior
        if hash01(x, 0, 96) > 0.45:
            _put(B, x, 70, "W0" if hash01(x, 1, 96) > 0.5 else "S5")
    for lx2 in (cx - 13, cx + 12):                    # patas de la mesa
        _rect(B, lx2, 77, lx2 + 1, 85, "K0")
    _rect(B, cx - 16, 84, cx + 15, 86, "K0")          # travesano inferior
    _rect(B, cx - 24, 80, cx - 8, 82, "K1")           # una banca baja al frente (silueta)
    for x in range(cx - 24, cx - 8):
        if hash01(x, 0, 97) > 0.55:
            _put(B, x, 79, "S5")                      # borde calido tenue en la banca
    _rect(B, cx - 22, 82, cx - 21, 86, "K0"); _rect(B, cx - 11, 82, cx - 10, 86, "K0")  # patas de la banca

    # viga de amarre bajo el alero
    for x in range(cx - 46, cx + 46):
        _put(B, x, post_top, "K1"); _put(B, x, post_top + 1, "K0")

    # farol colgante -- la FUENTE de luz interior (dibujado sobre el resplandor que proyecta)
    for y in range(post_top + 2, 56):                 # cuerda desde la viga de amarre
        _put(B, lx, y, "K1")
    _rect(B, lx - 3, 56, lx + 4, 65, "K0")            # carcasa de hierro
    _rect(B, lx - 2, 57, lx + 3, 64, "W0")            # vidrio calido
    _rect(B, lx - 2, 58, lx + 2, 63, "W1")
    _rect(B, lx - 1, 59, lx + 1, 62, "W2")            # nucleo ardiente
    _put(B, lx, 55, "R1"); _put(B, lx, 65, "R0")      # tapa superior + remate inferior
    _put(B, lx - 3, 60, "R1"); _put(B, lx + 3, 60, "R1")   # destellos calidos de metal en el marco

    # postes con bases de piedra. RONDA-8: el borde que da al interior capta
    # un reflejo calido de 1px del farol; el borde exterior capta un reflejo
    # frio crepuscular mas disperso; las bases de piedra se ACLARAN a crema
    # (C0/C1) para que los cimientos se lean iluminados.
    for px in (cx - 44, cx - 20, cx + 19, cx + 43):
        left_is_interior = px > cx                    # los postes a la derecha del centro se iluminan por su IZQUIERDA
        for y in range(post_top - 2, pad_y - 3):
            _put(B, px, y, "K0"); _put(B, px + 1, y, "K0"); _put(B, px + 2, y, "K1")
            wx = px if left_is_interior else px + 2   # borde que da al interior -> reflejo calido del farol
            if hash01(wx, y, 94) > 0.30:
                _put(B, wx, y, "O2" if hash01(wx, y, 98) > 0.45 else "W0")
            cxo = px + 2 if left_is_interior else px   # borde exterior -> reflejo frio crepuscular (disperso)
            if hash01(cxo, y, 99) > 0.82:
                _put(B, cxo, y, "RC")
        _rect(B, px - 2, pad_y - 3, px + 4, pad_y, "C1")
        _rect(B, px - 2, pad_y - 3, px + 4, pad_y - 2, "C0")
        _put(B, px - 2, pad_y - 1, "G0"); _put(B, px + 3, pad_y - 1, "G0")

    # techo conico/octagonal rojo que se eleva hasta una cupula
    for x in range(cx - half, cx + half):
        t = abs(x - cx) / half                # 0 centro .. 1 punta del alero
        top_y = int(apex_y + (eave_y - 8 - apex_y) * (t ** 0.85))
        edge_y = int(eave_y - 2 + t * 2)
        for y in range(top_y, edge_y):
            ridge = y < top_y + 2
            eave = y > edge_y - 3
            if ridge:
                shade = "R0"
            elif eave:
                shade = "R1"
            elif hash01(x, 0, 91) > 0.74:
                shade = "R1"                  # ranura de corrugado
            else:
                shade = "R2" if abs(x - cx) < half * 0.55 else "R1"
            B[y, x] = PALETTE[shade]
        _put(B, x, edge_y, "C1")              # goterón crema
    # lineas de limahoya desde el apice
    for k in (-1, 1):
        for i in range(half):
            x = cx + k * i
            y = int(apex_y + (eave_y - 8 - apex_y) * ((i / half) ** 0.85))
            _put(B, x, y, "R0")

    # cupula / remate del farol. RONDA-8: +1px de borde en la cumbrera para
    # que la corona se lea contra el cielo -- un borde frio crepuscular en
    # sus aristas ascendentes + una chispa calida.
    _rect(B, cx - 6, apex_y - 4, cx + 6, apex_y + 3, "R1")
    _rect(B, cx - 4, apex_y - 3, cx + 4, apex_y + 1, "K1")
    _put(B, cx - 2, apex_y - 3, "K0"); _put(B, cx + 1, apex_y - 3, "K0")
    for i in range(4):
        _rect(B, cx - 5 + i, apex_y - 4 - i, cx + 6 - i, apex_y - 3 - i, "R2" if i < 2 else "R0")
        _put(B, cx - 5 + i, apex_y - 4 - i, "RC")     # borde frio del cielo, arista ascendente izquierda
        _put(B, cx + 5 - i, apex_y - 4 - i, "RC")     # y la arista ascendente derecha
    _put(B, cx, apex_y - 9, "R0"); _put(B, cx, apex_y - 10, "W1")
    _put(B, cx, apex_y - 4, "W1")                     # chispa calida de cresta en la cupula

    # base de concreto + CHARCO de luz calida derramandose sobre el piso bajo
    # el farol (con dither, "como los arcos"), desvaneciendose a concreto
    # simplemente iluminado en el borde.
    for x in range(cx - 46, cx + 46):
        dxp = x - cx
        pool = 1.0 - abs(dxp) / 24.0 + (float(BAYER_4X4[pad_y & 3, x & 3]) - 0.5) * 0.28
        if pool > 0.74:
            top = "W0"
        elif pool > 0.52:
            top = "S5"
        elif pool > 0.30:
            top = "S4"
        else:
            top = "G2"                                # concreto simplemente iluminado mas alla del charco
        _put(B, x, pad_y, top)
        _put(B, x, pad_y + 1, "S4" if abs(dxp) < 16 else "G1")
        _put(B, x, pad_y + 2, "G0")
    # hiedra en un poste cercano
    for y in range(pad_y - 12, pad_y):
        if hash01(y, 0, 95) > 0.4:
            _put(B, cx - 45, y, "V2"); _put(B, cx - 46, y, "V1")

    return B


register_block("gaz", 7, 6, _build_gazebo)


# ===========================================================================
# PLAZA / PLINTO DEL GAZEBO  (ronda-10: pedido del usuario "hay que construir
# su parte faltante"). Una terraza de piedra calida sobre la que se ASIENTA
# el kiosco, llenando la huella despejada en la fila base (34) para que el
# gazebo se lea COMPLETO y anclado al suelo -- no cortado/flotando sobre el
# vacio de cielo rosado que dejo la ronda 9. Deliberadamente BAJA: solo los
# ~9px inferiores del tile son piedra (un labio crema iluminado en la parte
# superior de la terraza, alineado con las bases de piedra de gaz_*), la
# parte superior es transparente para que el cielo crepuscular siga
# respirando POR ENCIMA de la terraza y a traves del interior del kiosco.
# Pavimento frio (rampa G) con motas calidas O2 para que el charco de luz del
# farol caiga sobre pavimento, no sobre el vacio.
# ===========================================================================
_PLAZA_LIP = 7                                 # fila del borde superior de la terraza (alinea con las bases de gaz)


def _plaza_body(A: np.ndarray, gx: int, gy: int) -> None:
    for y in range(_PLAZA_LIP + 1, TILE):
        for x in range(TILE):
            b = 0.5 + 0.5 * hash01((gx + x) // 6, (gy + y) // 4, 472)
            b += (hash01(gx + x, gy + y, 473) - 0.5) * 0.20
            t = "G1" if b < 0.34 else ("G2" if b < 0.66 else "G3")
            if hash01(gx + x, gy + y, 474) > 0.90:
                t = "O2"                       # mota de pavimento calida (conecta con el resplandor del farol)
            A[y, x] = PALETTE[t]
    for x in range(0, TILE, 6):                # juntas verticales
        for y in range(_PLAZA_LIP + 1, TILE):
            A[y, x] = PALETTE["G1"]
    for x in range(TILE):                      # una junta horizontal a media altura del cuerpo
        if hash01(gx + x, 0, 475) > 0.35:
            A[_PLAZA_LIP + 4, x] = PALETTE["G1"]


def _plaza_lip(A: np.ndarray, gx: int, gy: int, x0: int = 0, x1: int = TILE) -> None:
    for x in range(x0, x1):
        A[_PLAZA_LIP, x] = PALETTE["C0" if hash01(gx + x, 0, 470) > 0.72 else "G3"]
        if hash01(gx + x, 1, 471) > 0.90:
            A[_PLAZA_LIP, x] = PALETTE["W1"]   # destello calido raro captando la ultima luz


@tile("plaza_slab")
def _plaza_slab(A, gx, gy):
    A[:] = BLACK                               # transparente por encima del labio -> el cielo respira
    _plaza_body(A, gx, gy)
    _plaza_lip(A, gx, gy)


@tile("plaza_step_l")
def _plaza_step_l(A, gx, gy):
    # extremo IZQUIERDO de la terraza: una cara lateral de piedra en sombra baja un escalon a la izquierda.
    A[:] = BLACK
    _plaza_body(A, gx, gy)
    _plaza_lip(A, gx, gy, x0=3)                # el labio empieza unos px mas adentro (esquina redondeada)
    for y in range(_PLAZA_LIP, TILE):          # cara lateral vertical oscura
        for x in range(0, 3):
            A[y, x] = PALETTE["G0"]
    A[_PLAZA_LIP, 3] = PALETTE["G1"]


@tile("plaza_step_r")
def _plaza_step_r(A, gx, gy):
    A[:] = BLACK
    _plaza_body(A, gx, gy)
    _plaza_lip(A, gx, gy, x1=TILE - 3)
    for y in range(_PLAZA_LIP, TILE):
        for x in range(TILE - 3, TILE):
            A[y, x] = PALETTE["G0"]
    A[_PLAZA_LIP, TILE - 4] = PALETTE["G1"]


# ===========================================================================
# PROPS  (narrativa de abandono)
# ===========================================================================
@tile("lamp_top")
def _lamp_top(A, gx, gy):
    A[:] = BLACK
    _rect(A, 6, 6, 12, 14, "K1")              # carcasa del farol (apagado)
    _rect(A, 7, 7, 11, 13, "K0")              # vidrio oscuro
    _put(A, 8, 3, "K1"); _put(A, 8, 4, "K0"); _put(A, 8, 5, "K1")  # remate
    _put(A, 6, 6, "RC")                       # destello frio del cielo en la tapa
    for y in range(14, TILE):                 # parte superior del poste inclinado
        _put(A, 8, y, "K0"); _put(A, 9, y, "K1")


@tile("lamp_base")
def _lamp_base(A, gx, gy):
    A[:] = BLACK
    for y in range(0, 11):                    # poste inclinado
        x = 8 + int((10 - y) * 0.2)
        _put(A, x, y, "K0"); _put(A, x + 1, y, "K1")
    _rect(A, 5, 11, 12, 16, "G1")             # base de piedra agrietada
    _rect(A, 5, 11, 12, 13, "G2")
    _put(A, 8, 13, "G0"); _put(A, 9, 14, "G0")


@tile("bench_broken_l")
def _bench_broken_l(A, gx, gy):
    A[:] = BLACK
    for i in range(TILE):                     # el asiento se inclina hacia abajo-derecha
        y = 7 + int(i * 0.22)
        _put(A, i, y, "O2"); _put(A, i, y + 1, "O1")
    for i in range(TILE):                     # tablilla del respaldo
        _put(A, 2 + i, 4 - int(i * 0.1), "O1")
    _rect(A, 3, 9, 4, 15, "O0")               # pata en pie


@tile("bench_broken_r")
def _bench_broken_r(A, gx, gy):
    A[:] = BLACK
    for i in range(TILE):
        y = 10 + int(i * 0.22)
        _put(A, i, y, "O2"); _put(A, i, y + 1, "O1")
    _put(A, 12, 14, "O0"); _put(A, 12, 15, "O0")   # muñon de pata rota corto


def _fence(A, gx, gy, salt):
    A[:] = BLACK
    _rect(A, 1, 6, 3, TILE, "O1")             # postes
    _rect(A, 13, 6, 15, TILE, "O1")
    _put(A, 1, 6, "O2"); _put(A, 13, 6, "O2")
    _rect(A, 0, 8, TILE, 9, "O0")             # rieles que atraviesan de borde a borde (tileable)
    _rect(A, 0, 12, TILE, 13, "O0")
    if hash01(gx, 0, 100 + salt) > 0.6:       # una estaca desgastada/rota
        _rect(A, 7, 6, 8, TILE, "O0")


@tile("fence_a")
def _fence_a(A, gx, gy):
    _fence(A, gx, gy, 0)


@tile("fence_b")
def _fence_b(A, gx, gy):
    _fence(A, gx, gy, 1)


@tile("fence_c")
def _fence_c(A, gx, gy):
    _fence(A, gx, gy, 2)


@tile("fence_fallen")
def _fence_fallen(A, gx, gy):
    A[:] = BLACK
    for i in range(TILE):                     # tablones tirados en el suelo
        y = 11 + int(i * 0.1)
        _put(A, i, y, "O2"); _put(A, i, y + 1, "O1"); _put(A, i, y + 2, "O0")
    _rect(A, 3, 9, 4, 14, "O1")               # un poste derribado
    _rect(A, 10, 10, 11, 15, "O0")


def _clothesline(A, gx, gy, cloth):
    A[:] = BLACK
    for x in range(TILE):                     # alambre colgado (catenaria)
        t = (gx + x) % 48 / 48.0
        y = 3 + int(4 * (1 - (2 * t - 1) ** 2))
        _put(A, x, y, "K1")
    if cloth:
        _rect(A, 6, 5, 11, 13, "C1")          # un trapo colgando
        _rect(A, 6, 5, 11, 7, "C0")
        _put(A, 6, 12, "C0"); _put(A, 10, 13, "G1")


@tile("clothesline_l")
def _clothesline_l(A, gx, gy):
    _clothesline(A, gx, gy, False)
    _rect(A, 1, 1, 2, TILE, "K0")             # poste inclinado


@tile("clothesline_m")
def _clothesline_m(A, gx, gy):
    _clothesline(A, gx, gy, True)


@tile("clothesline_r")
def _clothesline_r(A, gx, gy):
    _clothesline(A, gx, gy, False)
    _rect(A, 14, 1, 15, TILE, "K0")


def _leaves(A, gx, gy, salt):
    A[:] = BLACK
    cols = ["O1", "O2", "R1", "V2"]
    for k in range(7):
        x = int(15 * hash01(gx + k * 3, salt, 170))
        y = int(15 * hash01(gy + k * 5, salt, 171))
        col = cols[int(4 * hash01(x, y, 172)) % 4]
        _put(A, x, y, col)
        if hash01(x, y, 173) > 0.5:
            _put(A, x + 1, y, col)
        if hash01(x, y, 174) > 0.6:
            _put(A, x, y + 1, "O0")


@tile("leaves_drift_a")
def _leaves_a(A, gx, gy):
    _leaves(A, gx, gy, 0)


@tile("leaves_drift_b")
def _leaves_b(A, gx, gy):
    _leaves(A, gx, gy, 1)


@tile("branch_fallen")
def _branch_fallen(A, gx, gy):
    A[:] = BLACK
    for x in range(TILE):                     # rama principal a lo largo del tile
        y = 8 + int(2 * math.sin((gx + x) * 0.25))
        _put(A, x, y, "K0"); _put(A, x, y + 1, "O0")
    for (sx, sy, dx, dy, n) in [(4, 8, 1, -1, 5), (11, 9, 1, -1, 4)]:  # ramitas
        x, y = sx, sy
        for _ in range(n):
            _put(A, x, y, "K0"); x += dx; y += dy


def _fg_grass(A, gx, gy, salt):
    # Franja de pasto iluminado por el crepusculo (FG_Overlay). Las hojas son
    # VERDE crepuscular, deliberadamente mantenidas MAS OSCURAS que el cesped
    # transitable (RONDA-7: puntas limitadas a V2, sin punta V3 brillante)
    # para que estos penachos decorativos de primer plano enmarquen el piso
    # dando profundidad, en vez de igualar -- y devorar -- su borde de
    # superficie iluminado.
    A[:] = BLACK
    for x in range(TILE):
        hh = 4 + int(9 * hash01(gx + x, salt, 181))
        lean = (hash01(gx + x, salt, 182) - 0.5) * 4
        for i in range(hh):
            y = TILE - 1 - i
            xx = x + int(lean * (i / max(1, hh)))
            frac = i / max(1, hh)
            col = "V0" if frac < 0.4 else ("V1" if frac < 0.8 else "V2")
            _put(A, xx, y, col)


@tile("fg_grass_a")
def _fg_grass_a(A, gx, gy):
    _fg_grass(A, gx, gy, 0)


@tile("fg_grass_b")
def _fg_grass_b(A, gx, gy):
    _fg_grass(A, gx, gy, 1)


@tile("fg_grass_c")
def _fg_grass_c(A, gx, gy):
    _fg_grass(A, gx, gy, 2)


@tile("firefly")
def _firefly(A, gx, gy):
    A[:] = BLACK
    cx, cy = 8, 8
    _put(A, cx, cy, "W2")                     # nucleo brillante
    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        _put(A, cx + dx, cy + dy, "W0")       # halo calido
    _put(A, cx - 1, cy - 1, "W1")


# ===========================================================================
# ARCO DE JARDIN / PERGOLA  (soporte de plataforma de un solo sentido).
# Reemplaza la vieja "torre de seto" plana. Un arco de madera aireado: una
# viga transversal frondosa y transitable sobre dos postes, un enrejado de
# vid ABIERTO entre ellos (mayormente transparente, para que el
# atardecer/bosque se vean A TRAVES -> se lee como mobiliario de jardin de
# campus, nunca como una torre solida), enraizado en una jardinera baja de
# piedra. Compuesto en Terrain_Detail sobre el cielo.
# ===========================================================================
@tile("arbor_beam")
def _arbor_beam(A, gx, gy):
    A[:] = BLACK
    for x in range(TILE):                     # vid frondosa cayendo sobre la parte superior
        if hash01(gx + x, 0, 210) > 0.60:
            _put(A, x, 0, "V3"); _put(A, x, 1, "V2")
    for y in range(2, 7):                     # la viga transversal de tablones (parte superior transitable)
        for x in range(TILE):
            r = hash01(gx + x, gy + y, 211)
            if y == 2:
                A[y, x] = PALETTE["O3" if r > 0.55 else "O2"]   # borde superior soleado
            elif y == 6:
                A[y, x] = PALETTE["O0"]                          # sombra inferior
            else:
                A[y, x] = PALETTE["O1" if r > 0.32 else "O0"]    # veta
    for x in range(0, TILE, 5):               # sombras de juntas de tablones
        for y in range(2, 7):
            _put(A, x, y, "O0")
    if hash01(gx, 0, 212) > 0.45:             # un zarcillo colgante ocasional
        _put(A, 4, 7, "V1"); _put(A, 4, 8, "V2"); _put(A, 11, 7, "V2")


@tile("arbor_post")
def _arbor_post(A, gx, gy):
    A[:] = BLACK
    for y in range(TILE):                     # un poste de madera centrado (lados abiertos)
        for x in range(6, 10):
            r = hash01(gx + x, gy + y, 213)
            A[y, x] = PALETTE["O1" if (x < 8 or r < 0.7) else "O2"]
        _put(A, 6, y, "O0"); _put(A, 9, y, "O0")   # bordes en sombra -> poste redondo
    for y in range(TILE):                     # vid trepadora que espirala el poste
        vx = 5 + int(3 * (1 + math.sin((gy + y) * 0.5)))
        if hash01(gx + vx, gy + y, 214) > 0.4:
            _put(A, vx, y, "V2" if hash01(gx + vx, gy + y, 215) > 0.5 else "V1")
        if (gy + y) % 4 == 0:
            _put(A, vx, y, "V3")              # una hoja iluminada por el crepusculo


@tile("arbor_lattice")
def _arbor_lattice(A, gx, gy):
    A[:] = BLACK                              # aireado, pero un enrejado FRONDOSO (no una red)
    for y in range(TILE):                     # listones diagonales entrecruzados y apretados
        for x in range(TILE):
            if (x + y) % 4 == 0 or (x - y) % 4 == 0:
                A[y, x] = PALETTE["O1" if hash01(gx + x, gy + y, 216) > 0.5 else "O0"]
    for x in range(TILE):                     # una vigueta horizontal de pergola a media altura del tile
        if hash01(gx + x, 0, 227) > 0.35:
            A[8, x] = PALETTE["O0" if hash01(gx + x, 1, 227) > 0.5 else "O1"]
    for k in range(10):                       # vid trepadora pesada drapeada sobre los listones
        lx = int(15 * hash01(gx + k * 3, gy, 217))
        ly = int(15 * hash01(gy + k * 5, gx, 218))
        _put(A, lx, ly, "V2")
        _put(A, lx, min(TILE - 1, ly + 1), "V1")
        if hash01(lx, ly, 219) > 0.4:
            _put(A, min(TILE - 1, lx + 1), ly, "V2")
        if hash01(lx, ly, 220) > 0.62:
            _put(A, lx, ly, "V3")             # hoja iluminada por el crepusculo
    for fx, fy, salt in [(7, 6, 221), (11, 11, 226), (4, 12, 228)]:   # flores en la vid
        if hash01(gx, gy, salt) > 0.45:
            _put(A, fx, fy, "P0"); _put(A, fx + 1, fy, "P1")


@tile("arbor_base")
def _arbor_base(A, gx, gy):
    A[:] = BLACK                              # jardinera de piedra baja anclando el arco
    for x in range(TILE):                     # penacho de seto/flor derramandose sobre el borde
        if hash01(gx + x, 0, 224) > 0.5:
            _put(A, x, 2, "V3"); _put(A, x, 3, "V2")
    if hash01(gx, 0, 225) > 0.45:
        _put(A, 5, 2, "P0"); _put(A, 10, 3, "P1")
    for y in range(4, TILE):                  # la caja de la jardinera
        for x in range(TILE):
            if y <= 5:
                A[y, x] = PALETTE["O0"]                          # superficie de tierra oscura
            elif y == 6:
                A[y, x] = PALETTE["G3" if hash01(gx + x, gy + y, 222) > 0.4 else "G2"]  # borde de piedra iluminado
            else:
                b = 0.5 + 0.5 * hash01((gx + x) // 7, (gy + y) // 5, 223)
                A[y, x] = PALETTE["G1" if b > 0.5 else "G0"]     # cuerpo de piedra
    for x in range(0, TILE, 6):               # lineas de junta de piedra
        for y in range(7, TILE):
            _put(A, x, y, "G0")


# ===========================================================================
# CARPORT + VEHICULOS  (ronda-11: el usuario pidio "hacer el lugar donde
# estaban los carros"). Fiel a las fotos de referencia (imagenes para el
# mapa/3,8,9,12): un techo corrugado oscuro a una sola agua sobre postes de
# metal NEGRO por encima de una bahia de GRAVA OSCURA, un sedan plateado + una
# pickup blanca estacionados debajo y un tractor cargador naranja al lado.
# Todo construido con tonos apagados de crepusculo para que siluetean contra
# el cielo crepuscular como cualquier otra estructura -- la paleta se mantiene
# CERRADA: la carroceria plateada es C0/C1 + vidrio frio RC + sombra K*, la
# pickup blanca es C0/W* + K*, y el tractor es la rampa terracota R* (el
# "naranja" del crepusculo) + llantas K* + metal G*.
# ===========================================================================
def _build_carport_roof() -> np.ndarray:
    """Un techo de carport oscuro corrugado a una sola agua de 10x2 (cortado en carroof_cr).

    La lamina baja suavemente hacia el frente (derecha); su borde superior
    capta un hilo de la ultima luz calida (borde S5/W0) para que la silueta
    oscura se lea contra el atardecer, con una tabla de cenefa crema y una
    sombra inferior de 2px para que el voladizo tenga profundidad. Todo por
    debajo de la lamina se mantiene transparente (la bahia abierta) -- los
    postes (un tile aparte) llevan la estructura hasta el suelo.
    """
    cols = 10
    Wp, Hp = cols * TILE, 2 * TILE
    B = np.zeros((Hp, Wp, 3), np.uint8)
    for x in range(Wp):
        ry = 3 + int(6 * x / (Wp - 1))            # una sola agua suave, mas alto atras
        _put(B, x, ry, "S5" if hash01(x, 0, 480) > 0.4 else "W0")   # borde calido del atardecer
        for i in range(1, 5):                     # cuerpo corrugado de terracota oscura de 4px
            tone = "R1"                           # lamina de terracota oscura limpia
            if x % 4 == 0:
                tone = "R0"                       # ranura de corrugado cada 4px
            if i == 4:
                tone = "R0"                       # mas oscuro hacia el alero
            _put(B, x, ry + i, tone)
        _put(B, x, ry + 5, "C1")                  # tabla de cenefa crema
        _put(B, x, ry + 6, "K1")                  # sombra inferior (profundidad del voladizo)
        _put(B, x, ry + 7, "K0")
    return B


register_block("carroof", 10, 2, _build_carport_roof)


@tile("carport_post")
def _carport_post(A, gx, gy):
    # Un poste de metal NEGRO esbelto (nucleo de 2px) que encaja verticalmente.
    # Un borde calido del atardecer lame su borde izquierdo (de cara al sol) y
    # un borde frio disperso del cielo su borde derecho, para que el poste
    # negro siga leyendose como metal redondo contra el crepusculo, no como
    # una barra plana.
    A[:] = BLACK
    for y in range(TILE):
        _put(A, 7, y, "K1"); _put(A, 8, y, "K0"); _put(A, 9, y, "K0")
        if hash01(gx + 7, gy + y, 490) > 0.45:
            _put(A, 7, y, "O2" if hash01(gx, y, 491) > 0.5 else "W0")   # borde calido de sol
        if hash01(gx + 10, gy + y, 492) > 0.80:
            _put(A, 10, y, "RC")                  # borde frio disperso del cielo


@tile("carport_post_base")
def _carport_post_base(A, gx, gy):
    # El pie del poste: el fuste baja hasta una basa de CONCRETO agrietada (tarea: "2px con basa").
    A[:] = BLACK
    for y in range(0, 11):
        _put(A, 7, y, "K1"); _put(A, 8, y, "K0"); _put(A, 9, y, "K0")
        if hash01(gx + 7, gy + y, 490) > 0.45:
            _put(A, 7, y, "O2" if hash01(gx, y, 491) > 0.5 else "W0")
    _rect(A, 5, 11, 12, TILE, "G1")               # basa de concreto
    _rect(A, 5, 11, 12, 12, "G2")                 # parte superior iluminada de la basa
    _put(A, 6, 13, "G0"); _put(A, 10, 14, "G0")   # astillas/grietas


@tile("gravel")
def _gravel(A, gx, gy):
    # Grava de estacionamiento OSCURA (tarea: "gravilla oscura"), deliberadamente
    # mas oscura/fria que `pebbles` de la acera (G0/G1) para que la superficie
    # del aparcadero retroceda: un campo K1/G0 con algunas astillas G1
    # iluminadas captando el crepusculo.
    for y in range(TILE):
        for x in range(TILE):
            r = hash01(gx + x, gy + y, 495)
            A[y, x] = PALETTE["K1" if r < 0.45 else ("G0" if r < 0.86 else "G1")]


@tile("gravel_curb")
def _gravel_curb(A, gx, gy):
    # La fila del borde FRONTAL de la bahia de grava: grava oscura arriba, luego
    # un labio de bordillo de CONCRETO iluminado (tarea: "borde de concreto")
    # donde el aparcadero se encuentra con el cesped.
    for y in range(TILE):
        for x in range(TILE):
            if y < 8:
                r = hash01(gx + x, gy + y, 495)
                A[y, x] = PALETTE["K1" if r < 0.45 else ("G0" if r < 0.86 else "G1")]
            elif y < 11:
                A[y, x] = PALETTE["G3" if hash01(gx + x, gy + y, 493) > 0.55 else "G2"]  # bordillo iluminado
            else:
                A[y, x] = PALETTE["G1" if hash01(gx + x, gy + y, 494) > 0.5 else "G0"]
    for x in range(TILE):                          # linea de resalte superior del bordillo
        if hash01(gx + x, 0, 499) > 0.5:
            A[8, x] = PALETTE["G3"]


@tile("tire")
def _tire(A, gx, gy):
    # Una llanta desgastada apoyada contra un poste (detalle de abandono): una
    # ROSCA de caucho oscura -- un anillo claramente ABIERTO (el cielo se ve a
    # traves del cubo) para que nunca se lea como una bola/cabeza solida,
    # sentada baja en el suelo con un susurro de borde frio del cielo.
    A[:] = BLACK
    cx, cy = 8, 10                                          # baja en el tile -> en el suelo
    rox, roy, rix, riy = 6.0, 5.0, 3.8, 3.0                # caucho grueso, agujero ABIERTO ancho
    for y in range(TILE):
        for x in range(TILE):
            ox = ((x - cx) / rox) ** 2 + ((y - cy) / roy) ** 2
            ix = ((x - cx) / rix) ** 2 + ((y - cy) / riy) ** 2
            if ox <= 1.0 and ix >= 1.0:                     # entre la elipse exterior + interior
                A[y, x] = PALETTE["K0" if hash01(gx + x, gy + y, 486) > 0.4 else "K1"]
    _put(A, cx - 3, cy - 3, "RC")                          # borde frio del cielo arriba-izquierda


def _wheel(B: np.ndarray, wx: int, wy: int, rr: int, flat: bool = False) -> None:
    """Una rueda de caucho oscuro (opcionalmente PONCHADA/desinflada) con un cubo gris."""
    Hh, Wp = B.shape[:2]
    for y in range(Hh):
        for x in range(Wp):
            dy = y - wy
            if flat and dy > 0:
                dy = int(dy * 1.7)                # aplasta la zona de contacto -> desinflada
            d = (x - wx) ** 2 + dy * dy
            if d <= rr * rr:
                B[y, x] = PALETTE["G1" if d <= (rr - 3) ** 2 else
                                  ("K1" if hash01(x, y, 487) > 0.5 else "K0")]


def _build_sedan() -> np.ndarray:
    """Un sedan plateado bajo (4x2 = 64x32), vidrio polarizado oscuro, una llanta delantera PONCHADA.

    Carroceria plateada de la paleta cerrada: masa C1, resalte C0 en
    hombro/techo, habitaculo polarizado frio RC, sombra/llantas K*, con un
    destello calido de sol en la cola.
    """
    Wp, Hp = 64, 32
    B = np.zeros((Hp, Wp, 3), np.uint8)
    ground = 29
    bxl, bxr = 6, 58
    belt = 17                                     # marco de ventana / parte superior de la caja de carroceria
    roof = 9                                      # linea del techo
    # CAJA de carroceria inferior (cofre / puertas / baul): un 2-box plateado
    # limpio, parte superior plana en la linea de cintura, esquinas
    # inferiores delantera/trasera suavemente redondeadas, umbral en sombra.
    for y in range(belt, ground - 1):
        for x in range(bxl, bxr):
            if (x < bxl + 2 or x > bxr - 3) and y > ground - 3:
                continue                          # recoge hacia adentro las esquinas inferiores
            if y == belt:
                t = "C0"                          # brillo luminoso en la linea de cintura
            elif y >= ground - 2:
                t = "K1"                          # sombra bajo los umbrales
            else:
                t = "C1"                          # flanco plateado limpio
            B[y, x] = PALETTE[t]
    # habitaculo / cabina: un trapezoide inclinado (techo iluminado angosto ->
    # mas ancho en la cintura) con vidrio polarizado OSCURO (tarea) y solo
    # reflejos frios dispersos del cielo.
    for y in range(roof, belt):
        frac = (y - roof) / (belt - roof)
        x0 = int(24 - 6 * frac)                   # inclinacion del pilar A (parabrisas)
        x1 = int(41 + 6 * frac)                   # inclinacion del pilar C (luneta trasera)
        for x in range(x0, x1):
            if y <= roof + 1:
                t = "C0"                          # techo iluminado
            elif y >= belt - 1:
                t = "C1"                          # marco de ventana
            else:
                t = "RC" if hash01(x, y, 501) > 0.82 else "K1"   # vidrio oscuro + destello del cielo
            B[y, x] = PALETTE[t]
        _put(B, x0, y, "C1"); _put(B, x1 - 1, y, "C1")   # los pilares A/C captan la luz
    _put(B, 32, roof + 1, "C1")                   # pilar B
    for wx in (16, 46):                           # sombras del arco de rueda anclando la carroceria
        for dx in range(-5, 6):
            _put(B, wx + dx, ground - 3, "K1" if abs(dx) < 4 else "C1")
    # ruedas: la trasera normal, la DELANTERA desinflada (tarea: "una desinflada")
    _wheel(B, 46, ground - 2, 5, flat=False)
    _wheel(B, 16, ground - 2, 5, flat=True)
    _put(B, bxr - 3, belt + 3, "S5"); _put(B, bxr - 2, belt + 3, "W0")  # destello de la luz trasera
    _put(B, bxl + 1, belt + 3, "W0")              # captura del faro delantero
    return B


register_block("sedan", 4, 2, _build_sedan)


def _build_pickup() -> np.ndarray:
    """Una pickup blanca (4x2 = 64x32): cabina alta (izquierda) + platon de carga abierto (derecha).

    Carroceria blanca = C0 con una captura calida W1 del atardecer en el
    techo y un lado en sombra C1; vidrio de cabina oscuro + interior del
    platon; llantas K*. La paleta se mantiene cerrada.
    """
    Wp, Hp = 64, 32
    B = np.zeros((Hp, Wp, 3), np.uint8)
    ground = 29
    # losa de carroceria inferior (blanca) que abarca cabina + platon
    for y in range(16, ground - 1):
        for x in range(5, 59):
            r = hash01(x, y, 510)
            if y >= ground - 4:
                t = "C1" if r > 0.4 else "K1"     # zocalo en sombra
            else:
                t = "C0" if r > 0.3 else "C1"
            B[y, x] = PALETTE[t]
    # cabina (izquierda, mas alta) con techo iluminado calidamente + vidrio oscuro
    for y in range(9, 16):
        for x in range(8, 34):
            B[y, x] = PALETTE["W1" if (y < 11 and hash01(x, 0, 511) > 0.5) else "C0"]
    _rect(B, 11, 11, 31, 16, "K1")                # banda del parabrisas
    for y in range(11, 16):
        for x in range(11, 31):
            if hash01(x, y, 512) > 0.6:
                B[y, x] = PALETTE["RC"]            # destello frio de vidrio
    _put(B, 21, 11, "K0")                         # pilar de puerta
    # platon (derecha): riel superior + interior en sombra
    _rect(B, 34, 17, 57, 19, "C1")                # riel lateral del platon
    _rect(B, 34, 16, 35, 19, "C0")               # mamparo frontal iluminado
    _rect(B, 36, 19, 56, ground - 2, "K1")        # sombra del interior del platon
    for x in range(36, 56):
        if hash01(x, 0, 513) > 0.7:
            _put(B, x, 19, "O0")                  # escombros/hojas dispersas en el platon
    # ruedas (ambas normales)
    _wheel(B, 16, ground - 2, 5)
    _wheel(B, 46, ground - 2, 5)
    _put(B, 7, 17, "W0")                          # captura del faro delantero
    return B


register_block("pickup", 4, 2, _build_pickup)


def _build_tractor() -> np.ndarray:
    """Un tractor cargador naranja (3x2 = 48x32): rueda trasera grande, brazo cargador delantero.

    El "naranja" viene de la rampa terracota R* (apagada por el crepusculo)
    para que se mantenga en la paleta cerrada; llantas K*, metal G* en el
    brazo/pila del cargador, un borde calido en el cofre. Un tile de hiedra
    se drapea sobre el por separado en el compositor.
    """
    Wp, Hp = 48, 32
    B = np.zeros((Hp, Wp, 3), np.uint8)
    ground = 29
    # rueda trasera grande (derecha) + rueda delantera pequena (izquierda)
    _wheel(B, 34, ground - 5, 8)
    _wheel(B, 11, ground - 3, 4)
    # cofre del motor / cuerpo (rampa naranja terracota)
    for y in range(13, ground - 3):
        for x in range(9, 39):
            r = hash01(x, y, 520)
            if y <= 14:
                t = "R2"                          # parte superior del cofre iluminada
            elif r > 0.85:
                t = "O2"                          # rasguno ocre calido del panel
            else:
                t = "R1" if r > 0.4 else "R0"     # naranja medio / en sombra
            B[y, x] = PALETTE[t]
    for x in range(9, 39):                        # borde calido del atardecer en la cresta del cofre
        if hash01(x, 0, 521) > 0.5:
            _put(B, x, 13, "S5" if hash01(x, 1, 521) > 0.5 else "W0")
    # arco antivuelco / jaula del conductor + asiento (silueta oscura) sobre el eje trasero
    _rect(B, 27, 6, 29, 15, "K0")                 # poste trasero del arco
    _rect(B, 33, 8, 35, 15, "K0")                 # poste delantero del arco
    _rect(B, 27, 6, 35, 7, "K1")                  # barra superior
    _rect(B, 29, 12, 33, 15, "K1")               # asiento
    _rect(B, 24, 8, 26, 14, "G0")                 # tubo de escape
    # brazo cargador delantero que alcanza hacia abajo-izquierda un balde
    for i in range(10):
        x = 18 - i
        y = 16 + int(i * 0.9)
        _put(B, x, y, "O3"); _put(B, x, y + 1, "O2")
    _rect(B, 3, 24, 10, 28, "G1")                 # balde del cargador
    _rect(B, 3, 24, 10, 25, "G2")                 # labio iluminado del balde
    _put(B, 3, 27, "G0"); _put(B, 9, 27, "G0")
    return B


register_block("tractor", 3, 2, _build_tractor)


# ===========================================================================
# COMPOSICION
# ===========================================================================
def _compose_atlas() -> np.ndarray:
    n = len(TILES)
    rows = (n + COLS - 1) // COLS
    atlas = np.zeros((rows * TILE, COLS * TILE, 3), np.uint8)   # sobrante = negro
    for i, (_name, fn) in enumerate(TILES):
        ox = (i % COLS) * TILE
        oy = (i // COLS) * TILE
        fn(atlas[oy:oy + TILE, ox:ox + TILE], ox, oy)
    # Aplicar despeckle a cada celda de forma INDEPENDIENTE. Correr despeckle
    # sobre todo el atlas sangra color entre los limites de los tiles (un
    # pixel del borde de una celda se "limpia" usando su vecino del atlas,
    # acoplando el resultado al orden de registro). Rellenamos cada celda
    # 16x16 con un anillo de 1px replicado en el borde para que los pixeles
    # de frontera obtengan un contexto completo de 8 vecinos sin tomar
    # prestado de ningun otro tile, y luego copiamos de vuelta el interior
    # limpio.
    for i in range(len(TILES)):
        ox = (i % COLS) * TILE
        oy = (i // COLS) * TILE
        padded = np.pad(atlas[oy:oy + TILE, ox:ox + TILE],
                        ((1, 1), (1, 1), (0, 0)), mode="edge")
        despeckle(padded, PALETTE, protect_keys=_PROTECT)
        atlas[oy:oy + TILE, ox:ox + TILE] = padded[1:-1, 1:-1]
    return atlas


def _build_contact_sheet(atlas: np.ndarray) -> Image.Image:
    scale = 3
    cw, ch = TILE * scale, TILE * scale
    label_h = 12
    pad = 3
    cell_w = cw + pad * 2
    cell_h = ch + label_h + pad
    n = len(TILES)
    rows = (n + COLS - 1) // COLS
    sheet = Image.new("RGB", (COLS * cell_w, rows * cell_h), (24, 20, 30))
    draw = ImageDraw.Draw(sheet)
    for i, (name, _fn) in enumerate(TILES):
        c = i % COLS
        r = i // COLS
        ox = (i % COLS) * TILE
        oy = (i // COLS) * TILE
        cell = atlas[oy:oy + TILE, ox:ox + TILE]
        img = Image.fromarray(cell, "RGB").resize((cw, ch), Image.NEAREST)
        px = c * cell_w + pad
        py = r * cell_h + pad
        sheet.paste(img, (px, py))
        draw.rectangle([px - 1, py - 1, px + cw, py + ch], outline=(70, 62, 78))
        label = f"{i} {name}"
        draw.text((px, py + ch + 1), label[:12], fill=(200, 190, 205))
    return sheet


def main(out_png: Path | None = None, contact_png: Path | None = None) -> None:
    """Genera el PNG del atlas y la hoja de contacto etiquetada (idempotente).

    ``out_png``/``contact_png`` por defecto usan las ubicaciones canonicas del
    arbol del juego (``OUT_PNG``/``CONTACT_PNG``) -- la ruta a la que siempre
    ha escrito el flujo de autoria ``python -m ...``. Los tests pasan un
    ``tmp_path`` aqui en su lugar para que pytest nunca escriba (ni necesite
    acceso de escritura) dentro del arbol de assets sellado; ver
    ``tests/test_tileset_residencias.py``.
    """
    out_png = OUT_PNG if out_png is None else out_png
    contact_png = CONTACT_PNG if contact_png is None else contact_png

    atlas = _compose_atlas()
    out_png.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(atlas, "RGB").save(out_png)

    contact_png.parent.mkdir(parents=True, exist_ok=True)
    _build_contact_sheet(atlas).save(contact_png)

    used = np.unique(atlas.reshape(-1, 3), axis=0)
    print(f"tiles={len(TILES)} atlas={atlas.shape[1]}x{atlas.shape[0]} "
          f"unique_colors={len(used)}")
    print(f"atlas -> {out_png}")
    print(f"contact -> {contact_png}")


if __name__ == "__main__":
    main()
