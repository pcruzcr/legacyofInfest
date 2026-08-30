"""Renderiza un .tmx a PNG para poder MIRARLO.

Existe porque el mapa se generaba con un script y nadie veia el resultado:
cielos mal, texturas mal, tiles mal colocados. Un generador sin bucle de
verificacion visual es escribir a ciegas.

Uso:
    python render_mapa.py <ruta.tmx> <salida.png> [--desde COL] [--hasta COL]
    python render_mapa.py <ruta.tmx> <salida.png> --capa BG_Far
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame  # noqa: E402
from pytmx.util_pygame import load_pygame  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("tmx"); ap.add_argument("salida")
    ap.add_argument("--desde", type=int, default=0, help="columna inicial (tiles)")
    ap.add_argument("--hasta", type=int, default=None, help="columna final (tiles)")
    ap.add_argument("--fila-desde", type=int, default=0, dest="fila_desde")
    ap.add_argument("--fila-hasta", type=int, default=None, dest="fila_hasta")
    ap.add_argument("--capa", default=None, help="renderizar SOLO esta capa")
    ap.add_argument("--escala", type=float, default=1.0)
    a = ap.parse_args()

    pygame.init()
    pygame.display.set_mode((64, 64))
    tmx = load_pygame(a.tmx)

    c0 = max(0, a.desde)
    c1 = min(tmx.width, a.hasta if a.hasta is not None else tmx.width)
    tw, th = tmx.tilewidth, tmx.tileheight
    f0 = max(0, a.fila_desde)
    f1 = min(tmx.height, a.fila_hasta if a.fila_hasta is not None else tmx.height)
    ancho, alto = (c1 - c0) * tw, (f1 - f0) * th

    # Fondo magenta: cualquier magenta que sobreviva es un hueco sin pintar.
    lienzo = pygame.Surface((ancho, alto)); lienzo.fill((255, 0, 255))

    pintadas = []
    for capa in tmx.visible_layers:
        if not hasattr(capa, "tiles"):
            continue
        if a.capa and capa.name != a.capa:
            continue
        pintadas.append(capa.name)
        for x, y, img in capa.tiles():
            if c0 <= x < c1 and f0 <= y < f1 and img is not None:
                lienzo.blit(img, ((x - c0) * tw, (y - f0) * th))

    if a.escala != 1.0:
        lienzo = pygame.transform.scale_by(lienzo, a.escala)

    Path(a.salida).parent.mkdir(parents=True, exist_ok=True)
    pygame.image.save(lienzo, a.salida)
    print(f"{a.salida}  {lienzo.get_width()}x{lienzo.get_height()}px")
    print(f"columnas {c0}..{c1}  filas {f0}..{f1}  capas: {', '.join(pintadas)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
