#!/usr/bin/env python3
"""Tubería HD 2D/2.5D estilo PS4 — re-render real de los tilesets a 2× y 4×.

Roadmap 97 (`docs/97_ROADMAP_PS4_HD_2D_2_5D.md`) declaraba dos piezas por hacer:
`tileset_hd 2048` y los normal maps generalizados. Esta herramienta cierra ambas
para los tilesets procedurales y deja el resto en escalado NEAREST fiel:

- `<nombre>_hd.png`   — 512², baldosas de 32 px. Los 15 temas de `TILESET_THEMES`
  se RE-DIBUJAN con `_dibujar_tile_hd`: la misma gramática de 16 variantes de
  `_dibujar_tile_procedural` con TODA la geometría proporcional a `k = ts/16`
  (bisel 3→6 px, surcos cada 5→10 px, AO 3→6, outline 1→2). Detalle nuevo real,
  no un reescalado.
- `<nombre>_hd4.png`  — 1024², ×2 NEAREST de la anterior (crisp por construcción).
- `<nombre>_hd_2048.png` — 2048², ×4 NEAREST (la pieza que nombra el roadmap,
  para zoom de Tiled sin costuras).
- `<nombre>_hd_n.png` — normal map 8-bit vía `_gen_normal_map_para_tileset`
  (el mismo generador PSX que ya usan los `*_n.png` del 4-1).
- `manifiesto.json`   — origen, tamaños y mapeo autotile %16 de cada hoja.

Los tilesets de autor o con pintor propio (gothic/stage0, stage4_1b, caverna,
liquidos) no tienen pintor paramétrico: se entregan como `_hd.png` por NEAREST
2× (sin colores nuevos, paleta intacta) + normal map, y el manifiesto lo declara.

Uso:  python tools/generar_hd.py            (todo)
      python tools/generar_hd.py --solo-temas tileset_planicie tileset_aulas
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

# AUD-839 — consolas Windows cp1252: el manifiesto y los avisos llevan acentos.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
_RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_RAIZ))

try:
    from tools.generate_all_assets import (  # type: ignore
        BAYER_4X4,
        TILESET_THEMES,
        _gen_gothic_tileset,
        _gen_normal_map_para_tileset,
        _gen_procedural_tileset,
    )
except ImportError:  # ejecutado desde tools/ sin paquete
    from generate_all_assets import (  # type: ignore
        BAYER_4X4,
        TILESET_THEMES,
        _gen_gothic_tileset,
        _gen_normal_map_para_tileset,
        _gen_procedural_tileset,
    )

from PIL import Image, ImageDraw  # noqa: E402 — va tras el sys.path del paquete

# AUD-839 — consolas Windows cp1252: los avisos llevan acentos.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SALIDA = _RAIZ / "assets" / "tilesets_hd"
TS_HD = 32          # baldosa HD real (2× de 16)
GRID = 16           # la grilla 16×16 de siempre (mapeo %16 intacto)

#: Sin pintor HD propio: se entregan por NEAREST 2× (paleta intacta).
POR_ESCALADO = {"tileset_stage0", "tileset_stage4_1b", "tileset_stage4_1b_caverna"}

#: AUD-839 (cobertura total) — tilesets de AUTOR que usan los mapas y no
#: tienen pintor paramétrico: se entregan por NEAREST 2× + normal map, igual
#: que POR_ESCALADO. La fuente se resuelve en assets/tilesets y, si no está,
#: en student_assets/tilesets (entregas de estudiantes).
POR_ESCALADO_AUTOR = {
    "tileset_aulas_yariel", "tileset_gavilan_ciudad",
    "tileset_invenio_gothic_v5", "tileset_paburu", "tileset_parqueo",
    "tileset_residencias_crepusculo", "tileset_residencias_crepusculo_bgfar_bruma",
    "tileset_stage41_f1", "tileset_stage41_f2", "tileset_stage41_f3",
    "tileset_stage41_f4", "tileset_stage41_f5", "tileset_stage41_f6",
}


def _fuente_autor(nombre: str) -> Path | None:
    for raiz in (_RAIZ / "assets" / "tilesets",
                 _RAIZ / "student_assets" / "tilesets"):
        candidato = raiz / f"{nombre}.png"
        if candidato.exists():
            return candidato
    return None


# ══════════════════════════════════════════════════════════════
# El pintor HD — la misma gramática, geometría proporcional a k
# ══════════════════════════════════════════════════════════════

def _dibujar_tile_hd(draw: ImageDraw.ImageDraw, ox: int, oy: int, ts: int,
                     ttype: int, theme: dict) -> None:
    """Variante HD de `_dibujar_tile_procedural`: offsets ×k en vez de fijos.

    k = ts // 16. Con k=2 todo lo que el original hacía a 1 px pasa a 2 px y
    cada margen fijo (3, 4, 5…) se dobla: misma lectura a distancia de juego,
    micro-detalle nuevo al acercarse (vetas dobles, AO de 6 px, bisel de 2).
    """
    k = max(1, ts // 16)
    floor = theme["floor"]
    wall = theme["wall"]
    deco = theme["deco"]
    floor_claro = tuple(min(255, c + 30) for c in floor)
    floor_medio = tuple(min(255, c + 14) for c in floor)
    floor_oscuro = tuple(max(0, c - 30) for c in floor)
    floor_sombra = tuple(max(0, c - 48) for c in floor)
    wall_claro = tuple(min(255, c + 28) for c in wall)
    wall_oscuro = tuple(max(0, c - 28) for c in wall)
    wall_sombra = tuple(max(0, c - 45) for c in wall)
    deco_claro = tuple(min(255, c + 24) for c in deco)
    deco_oscuro = tuple(max(0, c - 24) for c in deco)
    metal_brillo = tuple(min(255, c + 55) for c in wall)
    madera_veta = tuple(max(0, c - 18) for c in deco)
    madera_base = deco

    def _dither_rect(x0, y0, x1, y1, col_a, col_b, umbral=8):
        for yy in range(y0, y1 + 1):
            for xx in range(x0, x1 + 1):
                b = BAYER_4X4[yy % 4][xx % 4]
                draw.point((xx, yy), fill=col_a if b < umbral else col_b)

    def _ao_esquina(x0, y0, size):
        for dy in range(size):
            for dx in range(size):
                dist = dx + dy
                col = floor_sombra if dist < 2 * k - 1 else (
                    floor_oscuro if dist < 4 * k - 1 else floor)
                b = BAYER_4X4[(y0 + dy) % 4][(x0 + dx) % 4]
                use_sombra = b < (10 - dist // k * 2)
                c = col if use_sombra else floor_oscuro if dist < 3 * k else floor
                if ox <= x0 + dx < ox + ts and oy <= y0 + dy < oy + ts:
                    draw.point((x0 + dx, y0 + dy), fill=c)

    def _bloque(x0, y0, x1, y1, col):
        draw.rectangle((x0, y0, x1, y1), fill=col)

    if ttype == 0:  # SUELO PIEDRA
        _bloque(ox, oy, ox + ts - 1, oy + ts - 1, floor)
        _bloque(ox + 3 * k, oy + 3 * k, ox + ts - 1 - 3 * k, oy + ts - 1 - 3 * k, floor_medio)
        _bloque(ox + 4 * k, oy + 4 * k, ox + ts - 1 - 4 * k, oy + ts - 1 - 4 * k, floor)
        for (cx, cy) in ((ox, oy), (ox + ts - 3 * k, oy),
                         (ox, oy + ts - 3 * k), (ox + ts - 3 * k, oy + ts - 3 * k)):
            _ao_esquina(cx, cy, 3 * k)
        _dither_rect(ox + 4 * k, oy + 4 * k, ox + ts - 1 - 4 * k, oy + 5 * k,
                     floor_oscuro, floor, 6)
        draw.rectangle((ox + 5 * k, oy + 5 * k,
                        ox + 5 * k + k - 1, oy + 5 * k + k - 1), fill=floor_claro)
        draw.rectangle((ox + ts - 6 * k, oy + ts - 6 * k,
                        ox + ts - 6 * k + k - 1, oy + ts - 6 * k + k - 1), fill=floor_oscuro)
    elif ttype == 1:  # MURO PIEDRA — surcos verticales
        _bloque(ox, oy, ox + ts - 1, oy + ts - 1, wall)
        for i in range(3):
            x = ox + 3 * k + i * 5 * k
            draw.line((x, oy + 2 * k, x, oy + ts - 1 - 2 * k), fill=wall_claro)
            _dither_rect(x + k, oy + 2 * k, x + k, oy + ts - 1 - 2 * k,
                         wall_oscuro, wall, 9)
        draw.line((ox, oy, ox + ts - 1, oy), fill=metal_brillo)
        draw.rectangle((ox + k, oy + k, ox + k, oy + k), fill=deco_claro)
        _dither_rect(ox, oy + k, ox + k, oy + ts - 1 - k, wall_sombra, wall, 7)
    elif ttype == 2:  # SUELO DECO — inset con bisel
        _bloque(ox, oy, ox + ts - 1, oy + ts - 1, floor)
        _bloque(ox + 2 * k, oy + 2 * k, ox + ts - 1 - 2 * k, oy + ts - 1 - 2 * k, deco)
        draw.line((ox + 2 * k, oy + 2 * k, ox + ts - 1 - 2 * k, oy + 2 * k), fill=deco_claro)
        draw.line((ox + 2 * k, oy + 2 * k, ox + 2 * k, oy + ts - 1 - 2 * k), fill=deco_claro)
        _dither_rect(ox + 2 * k, oy + ts - 1 - 2 * k, ox + ts - 1 - 2 * k,
                     oy + ts - 1 - 2 * k, deco_oscuro, deco, 8)
        _dither_rect(ox + ts - 1 - 2 * k, oy + 2 * k, ox + ts - 1 - 2 * k,
                     oy + ts - 1 - 2 * k, deco_oscuro, deco, 8)
        _bloque(ox + 5 * k, oy + 5 * k, ox + ts - 1 - 5 * k, oy + ts - 1 - 5 * k, floor_medio)
        _dither_rect(ox + 5 * k, oy + 5 * k, ox + ts - 1 - 5 * k, oy + 6 * k,
                     floor_oscuro, floor_medio, 6)
    elif ttype == 3:  # TECHO PLATAFORMA
        _bloque(ox, oy, ox + ts - 1, oy + ts - 1, wall)
        draw.line((ox, oy, ox + ts - 1, oy), fill=metal_brillo)
        draw.line((ox, oy + k, ox + ts - 1, oy + k), fill=wall_claro)
        draw.line((ox, oy + 2 * k, ox + ts - 1, oy + 2 * k), fill=deco)
        _dither_rect(ox, oy + 3 * k, ox + ts - 1, oy + 4 * k, wall_oscuro, wall, 10)
    elif ttype == 4:  # AGUA — ondas dithered
        _bloque(ox, oy, ox + ts - 1, oy + ts - 1, (28, 58, 128))
        for i in range(3):
            y = oy + 5 * k + i * 4 * k
            _dither_rect(ox + 2 * k + i * k, y, ox + 6 * k + i * 2 * k, y,
                         (50, 100, 180), (30, 58, 128), 7)
            draw.line((ox + 2 * k, y + k, ox + ts - 1 - 2 * k, y + k), fill=(70, 130, 210))
        draw.line((ox + 2 * k, oy + 2 * k, ox + ts - 1 - 2 * k, oy + 2 * k), fill=(90, 150, 230))
        for x in range(ox + 2 * k, ox + ts - 2 * k, 2 * k):
            b = BAYER_4X4[(oy + 3 * k) % 4][x % 4]
            if b < 8:
                draw.rectangle((x, oy + 3 * k, x + k - 1, oy + 3 * k + k - 1),
                               fill=(140, 200, 255))
    elif ttype == 5:  # MADERA — tablones y vetas diagonales
        _bloque(ox, oy, ox + ts - 1, oy + ts - 1, madera_base)
        for i in range(4):
            y = oy + 2 * k + i * 4 * k
            draw.line((ox + 2 * k, y, ox + ts - 1 - 2 * k, y), fill=madera_veta)
            for x in range(ox + 3 * k, ox + ts - 1 - 2 * k, 4 * k):
                b = BAYER_4X4[y % 4][x % 4]
                if b < 5:
                    draw.rectangle((x, y + k, x + k - 1, y + k), fill=madera_veta)
                if b < 9:
                    draw.rectangle((x + k, y + 2 * k, x + k, y + 2 * k),
                                   fill=tuple(max(0, c - 10) for c in madera_veta))
            if i % 2 == 0:
                draw.rectangle((ox + (4 + i) * k, y + k,
                                ox + (4 + i) * k + k - 1, y + k), fill=deco_claro)
        draw.line((ox + 2 * k, oy + 2 * k, ox + 2 * k, oy + ts - 1 - 2 * k),
                  fill=tuple(min(255, c + 20) for c in madera_base))
        _dither_rect(ox + 2 * k, oy + ts - 1 - 2 * k, ox + ts - 1 - 2 * k,
                     oy + ts - 1 - k, madera_veta, madera_base, 9)
    elif ttype == 6:  # PINCHOS/METAL
        _bloque(ox, oy, ox + ts - 1, oy + ts - 1, (135, 38, 38))
        for i in range(4):
            bx = ox + 2 * k + i * 4 * k
            draw.polygon([(bx, oy + ts - 2 * k),
                          (bx + 2 * k, oy + 2 * k),
                          (bx + 4 * k, oy + ts - 2 * k)], fill=(175, 58, 58))
            draw.line((bx + 2 * k, oy + 4 * k, bx + 2 * k, oy + 8 * k), fill=(220, 120, 120))
            _dither_rect(bx, oy + ts - 4 * k, bx + 4 * k, oy + ts - 2 * k,
                         (90, 28, 28), (135, 38, 38), 7)
        _bloque(ox + k, oy + k, ox + ts - 1 - k, oy + 3 * k, (155, 48, 48))
        draw.line((ox + k, oy + k, ox + ts - 1 - k, oy + k), fill=(210, 90, 90))
    elif ttype == 7:  # VACÍO — transparencia binaria
        pass
    elif ttype == 8:  # BORDE IZQ
        _bloque(ox, oy, ox + ts - 1, oy + ts - 1, floor)
        _bloque(ox, oy, ox + 2 * k, oy + ts - 1, wall)
        draw.line((ox + 2 * k, oy, ox + 2 * k, oy + ts - 1), fill=wall_claro)
        _dither_rect(ox + 3 * k, oy, ox + 4 * k, oy + ts - 1, wall_oscuro, floor, 7)
        draw.line((ox, oy, ox, oy + ts - 1), fill=metal_brillo)
        _ao_esquina(ox, oy, 2 * k)
    elif ttype == 9:  # BORDE DER
        _bloque(ox, oy, ox + ts - 1, oy + ts - 1, floor)
        _bloque(ox + ts - 1 - 2 * k, oy, ox + ts - 1, oy + ts - 1, wall)
        draw.line((ox + ts - 1 - 2 * k, oy, ox + ts - 1 - 2 * k, oy + ts - 1), fill=wall_claro)
        _dither_rect(ox + ts - 1 - 4 * k, oy, ox + ts - 1 - 3 * k, oy + ts - 1,
                     wall_oscuro, floor, 7)
        draw.line((ox + ts - 1, oy, ox + ts - 1, oy + ts - 1), fill=metal_brillo)
    elif ttype == 10:  # BORDE SUP
        _bloque(ox, oy, ox + ts - 1, oy + ts - 1, floor)
        _bloque(ox, oy, ox + ts - 1, oy + 2 * k, wall)
        draw.line((ox, oy, ox + ts - 1, oy), fill=metal_brillo)
        draw.line((ox, oy + 2 * k, ox + ts - 1, oy + 2 * k), fill=wall_claro)
        _dither_rect(ox, oy + 3 * k, ox + ts - 1, oy + 4 * k, wall_oscuro, floor, 8)
    elif ttype == 11:  # BORDE INF
        _bloque(ox, oy, ox + ts - 1, oy + ts - 1, floor)
        _bloque(ox, oy + ts - 1 - 2 * k, ox + ts - 1, oy + ts - 1, wall)
        draw.line((ox, oy + ts - 1 - 2 * k, ox + ts - 1, oy + ts - 1 - 2 * k), fill=wall_claro)
        _dither_rect(ox, oy + ts - 1 - 4 * k, ox + ts - 1, oy + ts - 1 - 3 * k,
                     wall_sombra, floor, 6)
        draw.line((ox, oy + ts - 1, ox + ts - 1, oy + ts - 1), fill=wall_oscuro)
    elif ttype == 12:  # ESQUINA SUP-IZQ
        _bloque(ox, oy, ox + ts - 1, oy + ts - 1, floor)
        _bloque(ox, oy, ox + 3 * k, oy + 3 * k, wall)
        _bloque(ox, oy, ox + 2 * k, oy + ts - 1, wall)
        _bloque(ox, oy, ox + ts - 1, oy + 2 * k, wall)
        draw.line((ox, oy, ox + 2 * k, oy), fill=metal_brillo)
        draw.line((ox, oy, ox, oy + 2 * k), fill=metal_brillo)
        _dither_rect(ox + 3 * k, oy + 3 * k, ox + 4 * k, oy + 4 * k, wall_oscuro, floor, 8)
        _ao_esquina(ox + 3 * k, oy + 3 * k, 2 * k)
    elif ttype == 13:  # ESQUINA SUP-DER
        _bloque(ox, oy, ox + ts - 1, oy + ts - 1, floor)
        _bloque(ox + ts - 1 - 3 * k, oy, ox + ts - 1, oy + 3 * k, wall)
        _bloque(ox + ts - 1 - 2 * k, oy, ox + ts - 1, oy + ts - 1, wall)
        _bloque(ox, oy, ox + ts - 1, oy + 2 * k, wall)
        draw.line((ox + ts - 1 - 2 * k, oy, ox + ts - 1, oy), fill=metal_brillo)
        _dither_rect(ox + ts - 1 - 4 * k, oy + 3 * k, ox + ts - 1 - 3 * k, oy + 4 * k,
                     wall_oscuro, floor, 8)
    elif ttype == 14:  # ESQUINA INF-IZQ
        _bloque(ox, oy, ox + ts - 1, oy + ts - 1, floor)
        _bloque(ox, oy + ts - 1 - 3 * k, ox + 3 * k, oy + ts - 1, wall)
        _bloque(ox, oy, ox + 2 * k, oy + ts - 1, wall)
        _bloque(ox, oy + ts - 1 - 2 * k, ox + ts - 1, oy + ts - 1, wall)
        draw.line((ox, oy + ts - 1, ox + 2 * k, oy + ts - 1), fill=wall_oscuro)
        _dither_rect(ox + 3 * k, oy + ts - 1 - 4 * k, ox + 4 * k, oy + ts - 1 - 3 * k,
                     wall_sombra, floor, 7)
    elif ttype == 15:  # ESQUINA INF-DER
        _bloque(ox, oy, ox + ts - 1, oy + ts - 1, floor)
        _bloque(ox + ts - 1 - 3 * k, oy + ts - 1 - 3 * k, ox + ts - 1, oy + ts - 1, wall)
        _bloque(ox + ts - 1 - 2 * k, oy, ox + ts - 1, oy + ts - 1, wall)
        _bloque(ox, oy + ts - 1 - 2 * k, ox + ts - 1, oy + ts - 1, wall)
        draw.line((ox + ts - 1, oy + ts - 1 - 2 * k, ox + ts - 1, oy + ts - 1), fill=wall_oscuro)
        _dither_rect(ox + ts - 1 - 4 * k, oy + ts - 1 - 4 * k,
                     ox + ts - 1 - 3 * k, oy + ts - 1 - 3 * k, wall_oscuro, floor, 7)
    else:
        _bloque(ox, oy, ox + ts - 1, oy + ts - 1, floor)
    # Outline 2px PSX con reflejo en la esquina sup-izq
    outline_color = tuple(max(0, c - 22) for c in wall)
    draw.rectangle((ox, oy, ox + ts - 1, oy + ts - 1), outline=outline_color, width=k)
    draw.rectangle((ox, oy, ox + k - 1, oy + k - 1), fill=metal_brillo)


def _gen_tileset_hd(path: Path, theme: dict) -> Path:
    """Hoja HD 512²: 16×16 baldosas de 32 px re-dibujadas (no reescaladas)."""
    _ensure_hd(path)
    img = Image.new("RGBA", (TS_HD * GRID, TS_HD * GRID), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    for gy in range(GRID):
        for gx in range(GRID):
            if gx < 8 and gy < 8:
                ttype = (gy * 8 + gx) % 8
            else:
                ttype = (gy * GRID + gx) % 16
            _dibujar_tile_hd(draw, gx * TS_HD, gy * TS_HD, TS_HD, ttype, theme)
    # Ruido de material ×4 (misma densidad relativa que el original: 160 ptos
    # en 256² → 640 en 512²), con la misma semilla determinista por nombre.
    import random
    rng = random.Random(hash(path.stem) % (2**31))
    for _ in range(640):
        x = rng.randint(0, TS_HD * GRID - 1)
        y = rng.randint(0, TS_HD * GRID - 1)
        px = img.getpixel((x, y))
        if px[3] == 0:
            continue
        d = rng.choice((-12, -8, -6, 6, 8, 12))
        ruido = tuple(max(0, min(255, c + d)) for c in px[:3])
        img.putpixel((x, y), (*ruido, px[3]))
    img.save(path)
    return path


def _escalado_nearest(origen: Path, destino: Path, factor: int) -> Path:
    im = Image.open(origen).convert("RGBA")
    im.resize((im.width * factor, im.height * factor), Image.NEAREST).save(destino)
    return destino


def _ensure_hd(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def generar_todo_hd(solo_temas: list[str] | None = None) -> dict:
    """Punto de entrada: llena `assets/tilesets_hd/` y devuelve el manifiesto."""
    SALIDA.mkdir(parents=True, exist_ok=True)
    manifiesto: dict[str, dict] = {}
    temas = {n: t for n, t in TILESET_THEMES.items()
             if not solo_temas or n in solo_temas}
    # AUD-839 — cobertura total de los mapas: los tilesets de autor entran
    # por la ruta NEAREST aunque no sean temas paramétricos.
    for nombre in POR_ESCALADO_AUTOR:
        if not solo_temas or nombre in solo_temas:
            temas.setdefault(nombre, None)
    for nombre, tema in sorted(temas.items()):
        hd = SALIDA / f"{nombre}_hd.png"
        if nombre in POR_ESCALADO or nombre in POR_ESCALADO_AUTOR:
            origen = (_RAIZ / "assets" / "tilesets" / f"{nombre}.png")
            if not origen.exists():
                origen = _fuente_autor(nombre)
            if origen is None:
                print(f"  AVISO: sin fuente para {nombre}; se omite")
                continue
            _escalado_nearest(origen, hd, 2)
            tecnica = "nearest_2x (pintor propio no paramétrico; paleta intacta)"
        elif tema == "gothic":
            _gen_gothic_tileset(hd, ts=TS_HD)
            tecnica = "pintor gótico paramétrico ts=32"
        elif nombre.startswith("tileset_stage4_1_fase"):
            _gen_procedural_tileset(hd, tema, ts=TS_HD)
            tecnica = "pintor procedural paramétrico ts=32"
        else:
            _gen_tileset_hd(hd, tema)
            tecnica = "re-render HD (geometría ×k)"
        hd4 = _escalado_nearest(hd, SALIDA / f"{nombre}_hd4.png", 2)
        hd2048 = _escalado_nearest(hd4, SALIDA / f"{nombre}_hd_2048.png", 2)
        normal = _gen_normal_map_para_tileset(hd, ts=TS_HD)
        manifiesto[nombre] = {
            "tecnica": tecnica,
            "hd": {"ruta": hd.name, "tam": "512x512", "tile": 32},
            "hd4": {"ruta": hd4.name, "tam": "1024x1024", "tile": 64},
            "hd_2048": {"ruta": hd2048.name, "tam": "2048x2048", "tile": 128},
            "normal": Path(normal).name if normal else None,
            "autotile": "bloque 8×8 sup-izq = %8 (mapeo TMX viejo); "
                        "resto = 16 variantes de borde/esquina (%16)",
            "determinismo": "semilla = hash(nombre); NEAREST para escalados",
        }
        print(f"  HD {nombre}: {tecnica}")
    ruta = SALIDA / "manifiesto.json"
    ruta.write_text(json.dumps(
        {"version": 1, "barra": "PS4 HD 2D/2.5D (roadmap 97)",
         "hojas": manifiesto}, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"HD completo: {len(manifiesto)} temas → {SALIDA} (manifiesto.json)")
    return manifiesto


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--solo-temas", nargs="*", default=None)
    args = parser.parse_args()
    generar_todo_hd(args.solo_temas)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
