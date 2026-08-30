"""Módulo: gen_tileset_bgfar_blur
Sistema: tools (generación de assets)
Descripción: Unidad VII (b) -- profundidad de campo barata: pre-difumina las
    tiles que compose_sky() usa en BG_Far (gen_level_residencias.py:255-325)
    y las empaqueta en un tileset NUEVO (nunca se sobrescribe el original --
    zona de creación permitida, CLAUDE.md "ZONAS EDITABLES" punto 3).

    Historia del atlas que BG_Far termina referenciando en el TMX:
    - TAREA 13 (2026-08-24, campaña "La Peregrinación al Venado") creó el
      atlas SOLO-blur (``generar_tileset_borroso`` -> ``TILESET_BLUR``):
      cada tile pasado por ``FilterTools.gaussian_blur`` con SIGMA=1.6.
    - TAREA (2026-08-27, cierre de brechas del Entregable 2, decisión del
      usuario, dictamen doc-guardian AMARILLO) lo reemplaza por un segundo
      atlas, "bruma" (``generar_tileset_bruma`` -> ``TILESET_BRUMA``): el
      MISMO blur (SIGMA=1.6, sin cambios) más una reducción de contraste
      local (``FilterTools.adjust_contrast``, ``CONTRASTE_BRUMA`` < 1.0) --
      perspectiva atmosférica real: los planos lejanos, además de perder
      nitidez, pierden contraste. El PNG solo-blur NUNCA se sobrescribe
      (zona de creación permitida, punto 3 de arriba) y queda huérfano en
      disco -- ``main()`` ya no lo vuelve a generar, ver su docstring.

    Por qué en tiempo de generación y no en on_enter(): BG_Far/BG_Mid/BG_Near
    se renderizan TODAS juntas por un único pyscroll.BufferedRenderer -- no
    hay forma de blurear selectivamente una capa sin tocar el motor. Además
    pytmx cachea el mapa parseado a nivel de PROCESO
    (stage_loader.py::StageLoader._tmx_cache) -- mutar sus imágenes en
    on_enter() contaminaría otras escenas. Pre-blurear en la generación del
    mapa es MÁS barato aún que "una vez en on_enter": coste CERO en runtime,
    ni siquiera una vez por partida.

    El kernel documentado (evidencia académica de Unidad VII): ver el
    comentario de SIGMA más abajo -- no es una matriz NxN explícita como la
    de ``apply_kernel`` (identity/sharpen/box_blur/sobel...), sino un filtro
    Gaussiano SEPARABLE cuyo tamaño efectivo se DERIVA del sigma."""
from __future__ import annotations

from pathlib import Path

import pygame

from src.framework.processing.filter_tools import FilterTools
from src.stages.boss_venado.tools.gen_level_residencias import (
    COLUMNS,
    TILE,
    _blank,
    compose_sky,
)
from src.stages.boss_venado.tools.gen_tileset_residencias import NAME_TO_INDEX

_HERE = Path(__file__).resolve()
GAME_ROOT = _HERE.parents[4]
TILESET_ORIGINAL = GAME_ROOT / "assets" / "tilesets" / "tileset_residencias_crepusculo.png"
TILESET_BLUR = GAME_ROOT / "assets" / "tilesets" / "tileset_residencias_crepusculo_bgfar_blur.png"
#: TAREA (2026-08-27): atlas "bruma" (blur + reduccion de contraste) -- el
#: que el TMX termina referenciando en BG_Far desde esta tarea (ver
#: gen_level_residencias.py, TILESET_BRUMA_NAME/TILESET_BRUMA_IMG). Mismo
#: patron de ruta que TILESET_BLUR, nombre de archivo nuevo -- se CREA, no
#: se sobrescribe nada existente (CLAUDE.md "ZONAS EDITABLES" punto 3).
TILESET_BRUMA = GAME_ROOT / "assets" / "tilesets" / "tileset_residencias_crepusculo_bgfar_bruma.png"

#: sigma del gaussian_blur -- FilterTools.gaussian_blur exige (0.0, 10.0]
#: (filter_tools.py:138); 1.6 suaviza el detalle de estrellas/nubes/murciélagos
#: sin volverlos manchas irreconocibles en un tile de solo 16x16.
#:
#: EL KERNEL, DOCUMENTADO (evidencia de Unidad VII -- convolución/filtrado):
#: ``FilterTools.gaussian_blur`` (filter_tools.py:134-148) NO recibe una
#: matriz NxN a mano como ``apply_kernel``; delega en
#: ``scipy.ndimage.gaussian_filter(canal, sigma=sigma, mode="reflect")``,
#: aplicado por separado a cada canal R/G/B (`for c in range(3)`). El filtro
#: Gaussiano 2D es SEPARABLE: en vez de convolucionar con una matriz densa
#: (kernel_size x kernel_size), scipy hace dos pasadas 1D (una por eje X,
#: otra por eje Y), cada una con el kernel discreto
#:
#:     G[k] = exp(-k^2 / (2*sigma^2)) / (sigma * sqrt(2*pi)),   k = -r..r
#:
#: normalizado para sumar 1.0. El radio ``r`` (cuántas celdas a cada lado del
#: centro entran en el kernel) NO es un parámetro libre: scipy lo deriva de
#: ``sigma`` con su ``truncate`` por defecto (4.0, no expuesto por
#: ``FilterTools.gaussian_blur`` -- toma el default de la librería) como
#: ``r = int(truncate * sigma + 0.5)``. Con SIGMA=1.6:
#:
#:     r = int(4.0 * 1.6 + 0.5) = int(6.9) = 6
#:     kernel 1D efectivo: 2*r + 1 = 13 muestras
#:     "huella" 2D efectiva (producto de las dos pasadas 1D): 13x13 px
#:
#: es decir, cada píxel de salida promedia (con pesos gaussianos, no un
#: promedio plano) un área de 13x13 alrededor suyo -- casi el tile ENTERO de
#: 16x16, que es exactamente el punto: un tile de fondo lejano se vuelve una
#: mancha de luz suave en vez de conservar su silueta (estrella/nube/
#: murciélago), sin necesitar generar una matriz 13x13 en memoria (la
#: separabilidad la evita: 2*13 multiplicaciones por píxel en vez de 13*13).
#: ``mode="reflect"`` fija el borde del tile reflejando los píxeles vecinos en
#: vez de asumir negro fuera de rango, para que las esquinas del tile no se
#: oscurezcan artificialmente por "fuga" hacia un borde inexistente.
SIGMA = 1.6

#: factor de ``FilterTools.adjust_contrast`` para el atlas "bruma" (TAREA
#: 2026-08-27, decisión del usuario, dictamen doc-guardian AMARILLO):
#: perspectiva atmosférica -- los planos lejanos, además de desenfocarse,
#: pierden CONTRASTE LOCAL (es una segunda señal de profundidad, no un
#: sustituto del blur -- se aplica DESPUÉS del gaussian_blur, nunca en su
#: lugar). ``FilterTools.adjust_contrast`` valida su factor en [0.0, 4.0]
#: (filter_tools.py:87-88) y con un factor < 1.0 comprime cada canal hacia
#: 128 (``(valor - 128) * factor + 128``): 0.85 es una reducción sutil,
#: perceptible tile a tile pero que no aplana el detalle que el blur ya
#: dejó (un factor cercano a 0.0 volvería la bruma un gris casi plano).
CONTRASTE_BRUMA = 0.85


def _nombres_de_bg_far() -> frozenset[str]:
    """Corre compose_sky() sobre capas en blanco y recoge los nombres únicos
    que escribe en bg_far -- se DERIVA del generador real en vez de
    mantenerse a mano, así que nunca se desincroniza si compose_sky cambia."""
    bg_far, bg_mid = _blank(), _blank()
    compose_sky(bg_far=bg_far, bg_mid=bg_mid)
    return frozenset(nombre for fila in bg_far for nombre in fila if nombre is not None)


NOMBRES_BG_FAR: frozenset[str] = _nombres_de_bg_far()


def _generar_atlas(origen: Path, destino: Path, transformar_tile) -> dict[str, int]:
    """Ayudante privado (TAREA 2026-08-27): el pipeline de recorte + orden
    alfabético + empaquetado en grilla + guardado es idéntico para el atlas
    blur y el atlas bruma -- lo único que cambia entre uno y otro es QUÉ
    transformación se le aplica a cada tile recortado. Extraído del cuerpo
    que antes vivía directo dentro de ``generar_tileset_borroso`` para que
    ``generar_tileset_bruma`` lo reuse sin duplicar esa lógica (dos copias
    del mismo bucle de recorte/empaquetado se habrían desincronizado tarde o
    temprano -- p. ej. si el orden de la grilla cambiara para uno y no para
    el otro).

    Extrae cada tile de NOMBRES_BG_FAR del atlas ``origen``, le aplica
    ``transformar_tile`` (una función tile -> tile transformado) y empaqueta
    el resultado en un atlas nuevo del mismo ancho de columnas. Devuelve
    {nombre: índice_en_el_atlas_nuevo}.

    Deliberadamente SIN `.convert_alpha()`: ese método exige un modo de
    video ya establecido (`pygame.display.set_mode`), y este generador (a
    diferencia de la escena real) puede correr en un proceso que solo hizo
    `pygame.init()` -- el tileset usa colorkey (`trans="000000"` en el TMX),
    no un canal alfa nativo, así que `.convert_alpha()` no aportaba nada
    aquí y solo añadía una dependencia frágil."""
    atlas = pygame.image.load(str(origen))
    nombres_ordenados = sorted(NOMBRES_BG_FAR)
    n = len(nombres_ordenados)
    filas = (n + COLUMNS - 1) // COLUMNS
    salida = pygame.Surface((COLUMNS * TILE, filas * TILE), pygame.SRCALPHA)
    mapping: dict[str, int] = {}
    for nuevo_idx, nombre in enumerate(nombres_ordenados):
        idx_original = NAME_TO_INDEX[nombre]
        col, row = idx_original % COLUMNS, idx_original // COLUMNS
        tile = atlas.subsurface((col * TILE, row * TILE, TILE, TILE)).copy()
        transformado = transformar_tile(tile)
        col_n, row_n = nuevo_idx % COLUMNS, nuevo_idx // COLUMNS
        salida.blit(transformado, (col_n * TILE, row_n * TILE))
        mapping[nombre] = nuevo_idx
    destino.parent.mkdir(parents=True, exist_ok=True)
    pygame.image.save(salida, str(destino))
    return mapping


def generar_tileset_borroso(origen: Path = TILESET_ORIGINAL,
                            destino: Path = TILESET_BLUR) -> dict[str, int]:
    """Extrae cada tile de NOMBRES_BG_FAR del atlas `origen`, le aplica
    gaussian_blur y empaqueta el resultado en un atlas nuevo del mismo ancho
    de columnas. Devuelve {nombre: índice_en_el_atlas_nuevo}.

    Contrato público sin cambios (TAREA 2026-08-27 solo reubicó el cuerpo a
    ``_generar_atlas``, ver su docstring): sigue siendo el atlas SOLO-blur,
    huérfano desde que ``main()`` dejó de regenerarlo -- se conserva por si
    una tarea futura lo necesita de nuevo (p. ej. tests existentes lo siguen
    ejercitando directamente)."""
    return _generar_atlas(origen, destino, lambda tile: FilterTools.gaussian_blur(tile, SIGMA))


def generar_tileset_bruma(origen: Path = TILESET_ORIGINAL,
                           destino: Path = TILESET_BRUMA) -> dict[str, int]:
    """Igual que ``generar_tileset_borroso``, pero cada tile pasa ADEMÁS por
    ``FilterTools.adjust_contrast(_, CONTRASTE_BRUMA)`` tras el blur (nunca
    en su lugar -- ver el docstring de ``CONTRASTE_BRUMA``): perspectiva
    atmosférica real, blur + pérdida de contraste local. Este es el atlas
    que ``gen_level_residencias.py`` referencia para BG_Far desde la TAREA
    2026-08-27 (ver TILESET_BRUMA_NAME/TILESET_BRUMA_IMG ahí)."""
    def _tile_con_bruma(tile: pygame.Surface) -> pygame.Surface:
        borroso = FilterTools.gaussian_blur(tile, SIGMA)
        return FilterTools.adjust_contrast(borroso, CONTRASTE_BRUMA)
    return _generar_atlas(origen, destino, _tile_con_bruma)


def main() -> None:
    """Genera SOLO el atlas bruma (el que el TMX referencia hoy).

    El atlas solo-blur (``TILESET_BLUR``) NUNCA se vuelve a escribir aquí:
    es zona de creación permitida (CLAUDE.md "ZONAS EDITABLES" punto 3,
    "solo CREAR archivos nuevos, jamás sobrescribir existentes"), y desde
    que ``gen_level_residencias.py`` dejó de referenciarlo (TAREA
    2026-08-27) regenerarlo aquí no serviría de nada -- quedaría un PNG
    huérfano en disco, sin ningún GID del TMX apuntándole (la limpieza de
    ese huérfano es una decisión de borrado pendiente del usuario, no de
    este script)."""
    if not pygame.get_init():
        pygame.init()
    mapping = generar_tileset_bruma()
    print(f"tileset bruma -> {TILESET_BRUMA} ({len(mapping)} tiles)")


if __name__ == "__main__":
    main()
