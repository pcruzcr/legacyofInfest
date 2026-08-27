#!/usr/bin/env python3
"""
Complete procedural asset generator for Legacy of InFest.
Generates ALL 250+ professor-owned assets per the Asset Bible (20_ASSET_BIBLE.md).
"""
from __future__ import annotations

import math
import random
import struct
import sys
import wave
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

# AUD-62 / test_salida_de_consola — la consola de Windows usa cp1252 por
# defecto y este generador imprime «→» y otros caracteres que no existen en
# esa codificación. Sin reconfigurar la salida, el proceso muere con
# UnicodeEncodeError a mitad del trabajo — el modo de fallo exacto que el
# resto de herramientas ya evitó (mismo patrón que check_orphan_systems.py).
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
A = PROJECT_ROOT / "assets"

W, H = 800, 600
SAMPLE_RATE = 22050
random.seed(42)

# PSX 2D Alta Calidad — matriz Bayer 4×4 para dithering ordenado de sombras (32-bit)
BAYER_4X4 = [
    [0, 8, 2, 10],
    [12, 4, 14, 6],
    [3, 11, 1, 9],
    [15, 7, 13, 5],
]

def _ensure(*paths):
    for p in paths:
        p.parent.mkdir(parents=True, exist_ok=True)

def _gradient(w, h, top, bot):
    img = Image.new("RGB", (w, h))
    for y in range(h):
        t = y / max(h - 1, 1)
        r = int(top[0] + (bot[0] - top[0]) * t)
        g = int(top[1] + (bot[1] - top[1]) * t)
        b = int(top[2] + (bot[2] - top[2]) * t)
        for x in range(w):
            img.putpixel((x, y), (r, g, b))
    return img

def _noise(w, h, scale=12):
    rng = random.Random(42)
    gw, gh = int(w / scale) + 2, int(h / scale) + 2
    g = [[rng.random() for _ in range(gw)] for _ in range(gh)]
    n = [[0.0]*w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            fx, fy = x / scale, y / scale
            ix, iy = int(fx), int(fy)
            dx, dy = fx - ix, fy - iy
            dx = dx*dx*(3-2*dx)
            dy = dy*dy*(3-2*dy)
            n00=g[iy][ix]
            n10=g[iy][ix+1]
            n01=g[iy+1][ix]
            n11=g[iy+1][ix+1]
            nx0 = n00 + (n10-n00)*dx
            nx1 = n01 + (n11-n01)*dx
            n[y][x] = nx0 + (nx1-nx0)*dy
    return n

def _apply_noise(img, noise, strength=40):
    w,h = img.size
    for y in range(h):
        for x in range(w):
            r,g,b = img.getpixel((x,y))
            nv = (noise[y][x]-0.5)*strength
            img.putpixel((x,y), (max(0,min(255,int(r+nv))),max(0,min(255,int(g+nv))),max(0,min(255,int(b+nv)))))

def _save_sheet(path, frames, fw, fh):
    """Save horizontal sprite sheet from list of PIL Images."""
    _ensure(path)
    total = len(frames)
    sheet = Image.new("RGBA", (fw * total, fh), (0,0,0,0))
    for i, f in enumerate(frames):
        sheet.paste(f, (i * fw, 0))
    sheet.save(path)


def _psx_outline_y_sombra(img: Image.Image) -> Image.Image:
    """Aplica outline 1px + sombra dithered Bayer PSX a sprite RGBA.

    PSX 32-bit: outline nítido 1px (no blur) y sombra dithered en base con
    Bayer 4×4 para evitar banding, manteniendo pixel 1:1 NEAREST. Aumenta
    riqueza de paleta sin perder legibilidad (32-64 colores por sprite).
    """
    w, h = img.size
    pix = img.load()
    outline = (14, 14, 20, 255)
    to_outline: list[tuple[int, int]] = []
    for y in range(h):
        for x in range(w):
            if pix[x, y][3] == 0:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < w and 0 <= ny < h and pix[nx, ny][3] != 0:
                        to_outline.append((x, y))
                        break
    for x, y in to_outline:
        pix[x, y] = outline
    # Sombra dithered en 2-3 filas inferiores de cada columna opaca
    for y in range(h):
        for x in range(w):
            r, g, b, a = pix[x, y]
            if a != 0 and y >= h - 4:
                bv = BAYER_4X4[y % 4][x % 4]
                if bv < 6:
                    pix[x, y] = (max(0, r - 26), max(0, g - 26), max(0, b - 26), a)
                elif bv < 10:
                    pix[x, y] = (max(0, r - 12), max(0, g - 12), max(0, b - 12), a)
    return img

# ════════════════════════════════════════
# SECTION 1: PLAYER SPRITES (32x32, PSX 32-bit HQ — 2 piernas, espada separada, capucha oscura)
# ════════════════════════════════════════

def _pixel_art(draw, x, y, data, palette):
    """Draw pixel art from string data: '.'=transparent, '0'-'9'=palette index."""
    lines = data.strip().split("\n")
    for row_idx, line in enumerate(lines):
        for col_idx, ch in enumerate(line):
            if ch != '.':
                color = palette.get(int(ch), (255,0,255))
                draw.point((x + col_idx, y + row_idx), fill=color)

# ── Paleta PSX 32-bit extendida — capucha oscura, 32-64 colores por sprite ──
_PLAYER_COL = {
    'hood_dark': (18, 22, 38, 255),
    'hood_mid': (34, 40, 68, 255),
    'hood_light': (54, 60, 92, 255),
    'hood_hi': (78, 86, 118, 255),
    'face_dark': (130, 90, 60, 255),
    'face_mid': (190, 135, 95, 255),
    'face_light': (235, 195, 150, 255),
    'tunic_dark': (38, 48, 86, 255),
    'tunic_mid': (58, 70, 118, 255),
    'tunic_light': (84, 96, 144, 255),
    'tunic_hi': (108, 120, 168, 255),
    'arm_dark': (48, 58, 98, 255),
    'arm_mid': (68, 78, 122, 255),
    'belt': (110, 82, 48, 255),
    'belt_dark': (78, 58, 32, 255),
    'belt_gold': (192, 162, 92, 255),
    'leg_dark': (42, 52, 92, 255),
    'leg_mid': (60, 72, 122, 255),
    'leg_light': (78, 90, 148, 255),
    'boot': (62, 42, 28, 255),
    'boot_dark': (42, 28, 18, 255),
    'sword_blade': (222, 224, 236, 255),
    'sword_mid': (188, 192, 210, 255),
    'sword_dark': (148, 158, 180, 255),
    'sword_hilt': (182, 162, 90, 255),
    'sword_hilt_dark': (132, 112, 60, 255),
    'eye': (245, 210, 90, 255),
    'eye_dark': (180, 140, 40, 255),
}

PLAYER_PAL = {
    0: (60, 60, 80, 255), 1: (80, 80, 110, 255), 2: (140, 140, 170, 255),
    3: (220, 180, 140, 255), 4: (180, 140, 100, 255), 5: (20, 30, 60, 255),
    6: (40, 50, 90, 255), 7: (100, 80, 50, 255), 8: (60, 50, 30, 255),
    9: (200, 180, 100, 255),
}
PLAYER_IDLE = ""; PLAYER_WALK_A = ""; PLAYER_WALK_B = ""; PLAYER_JUMP = ""
PLAYER_CROUCH = ""; PLAYER_SWIM_KICK = ""; PLAYER_ATTACK = ""


def _dibujar_jugador_psx(draw: ImageDraw.ImageDraw, pose: str, fi: int, total: int) -> None:
    """Dibuja silueta PSX 32-bit HQ encapuchada oscura, SIEMPRE 2 piernas, espada separada."""
    C = _PLAYER_COL
    cx = 16
    base_y = 27
    def bayer_lt(x, y, umbral=8):
        return BAYER_4X4[y % 4][x % 4] < umbral
    hood_y0 = 1
    if pose in ("crouch", "slide"):
        hood_y0 = 4
    elif pose == "jump":
        hood_y0 = 1
    elif pose == "fall":
        hood_y0 = 2
    elif pose == "climb":
        hood_y0 = 0
    elif pose == "hurt":
        hood_y0 = 2
    draw.ellipse((cx - 6, hood_y0, cx + 6, hood_y0 + 9), fill=C['hood_dark'])
    draw.ellipse((cx - 5, hood_y0 + 1, cx + 5, hood_y0 + 8), fill=C['hood_mid'])
    draw.ellipse((cx - 4, hood_y0 + 2, cx + 4, hood_y0 + 7), fill=C['hood_light'])
    draw.rectangle((cx - 3, hood_y0 + 3, cx + 3, hood_y0 + 8), fill=C['hood_dark'])
    draw.rectangle((cx - 3, hood_y0 + 4, cx + 3, hood_y0 + 7), fill=C['face_mid'])
    draw.rectangle((cx - 2, hood_y0 + 5, cx + 2, hood_y0 + 6), fill=C['face_light'])
    eye_y = hood_y0 + 5
    if pose not in ("die", "hurt"):
        draw.point((cx - 2, eye_y), fill=C['eye'])
        draw.point((cx + 1, eye_y), fill=C['eye'])
    else:
        draw.point((cx - 2, eye_y), fill=C['eye_dark'])
        draw.point((cx + 1, eye_y), fill=C['eye_dark'])
    draw.point((cx - 3, hood_y0 + 2), fill=C['hood_hi'])
    torso_y0 = hood_y0 + 9
    torso_y1 = torso_y0 + 9
    if pose in ("crouch", "slide"):
        torso_y1 = torso_y0 + 7
    elif pose == "swim":
        torso_y1 = torso_y0 + 8
    draw.rectangle((cx - 5, torso_y0, cx + 5, torso_y1), fill=C['tunic_mid'])
    draw.rectangle((cx - 4, torso_y0 + 1, cx + 4, torso_y1 - 1), fill=C['tunic_light'])
    for yy in range(torso_y1 - 2, torso_y1):
        for xx in range(cx - 4, cx + 5):
            if bayer_lt(xx, yy, 6):
                draw.point((xx, yy), fill=C['tunic_dark'])
    belt_y = torso_y0 + 5
    if pose not in ("climb", "zipline"):
        draw.rectangle((cx - 5, belt_y, cx + 5, belt_y + 2), fill=C['belt'])
        draw.rectangle((cx - 1, belt_y, cx + 1, belt_y + 2), fill=C['belt_gold'])
        draw.point((cx, belt_y), fill=(220, 190, 120, 255))
    draw.line((cx, torso_y0 + 2, cx, belt_y - 1), fill=C['tunic_dark'])
    def dibujar_brazo(ax0, ay0, ax1, ay1, col_mid, col_dark):
        draw.line((ax0, ay0, ax1, ay1), fill=col_mid, width=2)
        if ax0 < ax1:
            draw.point((ax1, ay1), fill=col_dark)
    def dibujar_espada(sx0, sy0, sx1, sy1, grosor=2):
        draw.line((sx0, sy0, sx1, sy1), fill=C['sword_blade'], width=grosor)
        draw.line((sx0, sy0, sx1, sy1), fill=C['sword_mid'], width=1)
        draw.line((sx0 - 1, sy0, sx0 + 1, sy0), fill=C['sword_hilt_dark'])
        draw.point((sx0, sy0), fill=C['sword_hilt'])
        mx, my = (sx0 + sx1) // 2, (sy0 + sy1) // 2
        draw.point((mx, my), fill=(255, 255, 255, 220))
    fase = (fi / max(1, total - 1)) if total > 1 else 0.0
    bob = 0
    if pose == "idle":
        bob = -1 if fi % 2 else 0
        torso_y0 += bob
        torso_y1 += bob
        dibujar_brazo(cx - 5, torso_y0 + 2, cx - 7, torso_y0 + 7, C['arm_mid'], C['arm_dark'])
        dibujar_brazo(cx + 5, torso_y0 + 2, cx + 7, torso_y0 + 6, C['arm_mid'], C['arm_dark'])
        dibujar_espada(cx + 8, torso_y0 + 5, cx + 8, torso_y0 + 11, grosor=2)
    elif pose == "walk":
        bob = [0, -1, 0, 0, 0, -1, 0, 0][fi % 8] if total >= 8 else 0
        torso_y0 += bob
        torso_y1 += bob
        if fi % 2 == 0:
            dibujar_brazo(cx - 5, torso_y0 + 2, cx - 8, torso_y0 + 6, C['arm_mid'], C['arm_dark'])
            dibujar_brazo(cx + 5, torso_y0 + 2, cx + 8, torso_y0 + 4, C['arm_mid'], C['arm_dark'])
        else:
            dibujar_brazo(cx - 5, torso_y0 + 2, cx - 7, torso_y0 + 4, C['arm_mid'], C['arm_dark'])
            dibujar_brazo(cx + 5, torso_y0 + 2, cx + 9, torso_y0 + 6, C['arm_mid'], C['arm_dark'])
        sx = cx + 9 + (1 if fi % 2 else 0)
        dibujar_espada(sx, torso_y0 + 4, sx, torso_y0 + 10, grosor=2)
    elif pose == "jump":
        jitter = -1 if fi == 1 else (1 if fi == 2 else 0)
        torso_y0 += jitter
        torso_y1 += jitter
        dibujar_brazo(cx - 5, torso_y0 + 2, cx - 6, torso_y0 - 1, C['arm_mid'], C['arm_dark'])
        dibujar_brazo(cx + 5, torso_y0 + 2, cx + 6, torso_y0 - 1, C['arm_mid'], C['arm_dark'])
        sx_off = 9 + (fi % 2)
        dibujar_espada(cx + 6, torso_y0 - 1, cx + sx_off, torso_y0 - 4, grosor=2)
    elif pose == "fall":
        cape_shift = 1 if fi % 2 else 0
        dibujar_brazo(cx - 5, torso_y0 + 2, cx - 8 - cape_shift, torso_y0 + 5, C['arm_mid'], C['arm_dark'])
        dibujar_brazo(cx + 5, torso_y0 + 2, cx + 8 + cape_shift, torso_y0 + 5, C['arm_mid'], C['arm_dark'])
        dibujar_espada(cx + 8 + cape_shift, torso_y0 + 5, cx + 10 + cape_shift, torso_y0 + 9, grosor=2)
        for x in range(cx - 4, cx + 4):
            if bayer_lt(x + fi, torso_y1, 7):
                draw.point((x, torso_y1), fill=C['hood_dark'])
    elif pose == "crouch":
        bob = -1 if fi % 2 else 0
        torso_y0 += bob
        torso_y1 += bob
        dibujar_brazo(cx - 5, torso_y0 + 2, cx - 6, torso_y0 + 5, C['arm_mid'], C['arm_dark'])
        dibujar_brazo(cx + 5, torso_y0 + 2, cx + 6, torso_y0 + 5, C['arm_mid'], C['arm_dark'])
        dibujar_espada(cx + 6, torso_y0 + 4, cx + 8, torso_y0 + 8, grosor=2)
    elif pose == "short_attack":
        dibujar_brazo(cx - 5, torso_y0 + 2, cx - 3, torso_y0 + 4, C['arm_mid'], C['arm_dark'])
        dibujar_brazo(cx + 5, torso_y0 + 2, cx + 10, torso_y0 + 4, C['arm_mid'], C['arm_dark'])
        sx0, sy0 = cx + 10, torso_y0 + 4
        sx1 = sx0 + 8 + int(fase * 4)
        draw.line((sx0, sy0, sx1, sy0), fill=C['sword_blade'], width=3)
        draw.line((sx0, sy0, sx1, sy0), fill=C['sword_mid'], width=1)
        draw.point(((sx0 + sx1)//2, sy0), fill=(255, 255, 255, 255))
        draw.rectangle((sx0 - 2, sy0 - 1, sx0, sy0 + 1), fill=C['sword_hilt'])
    elif pose == "long_attack":
        ang = -0.6 + fase * 1.4
        sx0, sy0 = cx + 5, torso_y0 + 2
        length = 10
        sx1 = int(sx0 + length * math.cos(ang))
        sy1 = int(sy0 + length * math.sin(ang))
        dibujar_brazo(cx - 5, torso_y0 + 2, cx - 4, torso_y0 + 5, C['arm_mid'], C['arm_dark'])
        dibujar_brazo(cx + 5, torso_y0 + 2, sx0, sy0, C['arm_mid'], C['arm_dark'])
        dibujar_espada(sx0, sy0, sx1, sy1, grosor=2)
        if fi > 0:
            draw.point((sx1 - 1, sy1), fill=(255, 255, 255, 90))
    elif pose == "hurt":
        draw.ellipse((cx - 6, hood_y0 + 1, cx + 6, hood_y0 + 9), fill=(160, 60, 60, 255))
        dibujar_brazo(cx - 5, torso_y0 + 2, cx - 8, torso_y0 + 3, C['arm_mid'], C['arm_dark'])
        dibujar_brazo(cx + 5, torso_y0 + 2, cx + 9, torso_y0 + 3, C['arm_mid'], C['arm_dark'])
        dibujar_espada(cx + 9, torso_y0 + 3, cx + 9, torso_y0 + 7, grosor=2)
        if fi % 2 == 0:
            draw.point((cx, torso_y0 + 4), fill=(255, 180, 180, 255))
    elif pose == "die":
        progreso = fi / max(1, total - 1)
        desplome = int(progreso * 6)
        draw.ellipse((cx - 6, hood_y0 + desplome, cx + 6, hood_y0 + 9 + desplome), fill=C['hood_dark'])
        draw.rectangle((cx - 5, torso_y0 + desplome, cx + 5, torso_y1 + desplome), fill=C['tunic_dark'])
        dibujar_espada(cx + 6, torso_y0 + desplome + 4, cx + 6, torso_y0 + desplome + 8, grosor=2)
    elif pose == "swim":
        if fi % 2 == 0:
            dibujar_brazo(cx - 5, torso_y0 + 2, cx - 9, torso_y0 + 3, C['arm_mid'], C['arm_dark'])
            dibujar_brazo(cx + 5, torso_y0 + 2, cx + 9, torso_y0 + 3, C['arm_mid'], C['arm_dark'])
        else:
            dibujar_brazo(cx - 5, torso_y0 + 2, cx - 3, torso_y0 + 5, C['arm_mid'], C['arm_dark'])
            dibujar_brazo(cx + 5, torso_y0 + 2, cx + 3, torso_y0 + 5, C['arm_mid'], C['arm_dark'])
        dibujar_espada(cx + 7, torso_y0 + 4, cx + 9, torso_y0 + 5, grosor=2)
        if fi % 2:
            draw.point((cx - 6, torso_y0 + 6), fill=(180, 220, 255, 180))
            draw.point((cx + 6, torso_y0 + 6), fill=(180, 220, 255, 180))
    elif pose == "climb":
        dibujar_brazo(cx - 5, torso_y0 + 2, cx - 4, torso_y0 - 3, C['arm_mid'], C['arm_dark'])
        dibujar_brazo(cx + 5, torso_y0 + 2, cx + 4, torso_y0 - 3, C['arm_mid'], C['arm_dark'])
        draw.point((cx - 4, torso_y0 - 3), fill=C['face_light'])
        draw.point((cx + 4, torso_y0 - 3), fill=C['face_light'])
        dibujar_espada(cx + 4, torso_y0 - 3, cx + 6, torso_y0 + 2, grosor=2)
    elif pose == "zipline":
        dibujar_brazo(cx - 5, torso_y0 + 2, cx - 2, torso_y0 - 4, C['arm_mid'], C['arm_dark'])
        dibujar_brazo(cx + 5, torso_y0 + 2, cx + 2, torso_y0 - 4, C['arm_mid'], C['arm_dark'])
        draw.line((cx - 6, torso_y0 - 5, cx + 6, torso_y0 - 5), fill=(90, 90, 100, 255))
        draw.point((cx, torso_y0 - 5), fill=(200, 200, 210, 255))
        dibujar_espada(cx + 2, torso_y0 - 4, cx + 4, torso_y0 + 1, grosor=2)
    elif pose == "parry":
        dibujar_brazo(cx - 5, torso_y0 + 2, cx - 2, torso_y0 + 4, C['arm_mid'], C['arm_dark'])
        dibujar_brazo(cx + 5, torso_y0 + 2, cx + 6, torso_y0 + 4, C['arm_mid'], C['arm_dark'])
        dibujar_espada(cx + 7, torso_y0 + 1, cx + 7, torso_y0 + 9, grosor=3)
        if fi % 2 == 0:
            draw.point((cx + 7, torso_y0 + 5), fill=(255, 255, 180, 255))
    elif pose == "slide":
        dibujar_brazo(cx - 5, torso_y0 + 2, cx - 7, torso_y0 + 5, C['arm_mid'], C['arm_dark'])
        dibujar_brazo(cx + 5, torso_y0 + 2, cx + 7, torso_y0 + 5, C['arm_mid'], C['arm_dark'])
        dibujar_espada(cx + 7, torso_y0 + 5, cx + 10, torso_y0 + 6, grosor=2)
    else:
        dibujar_brazo(cx - 5, torso_y0 + 2, cx - 7, torso_y0 + 6, C['arm_mid'], C['arm_dark'])
        dibujar_brazo(cx + 5, torso_y0 + 2, cx + 7, torso_y0 + 6, C['arm_mid'], C['arm_dark'])
        dibujar_espada(cx + 8, torso_y0 + 5, cx + 8, torso_y0 + 11, grosor=2)
    leg_h = 8
    if pose in ("crouch", "slide"):
        leg_h = 5
    elif pose == "jump":
        leg_h = 6
    elif pose == "swim":
        leg_h = 4
    elif pose in ("climb", "zipline"):
        leg_h = 7
    left_x = cx - 5
    right_x = cx + 2
    if pose == "walk":
        if fi % 2 == 0:
            left_x -= 2
            right_x += 1
        else:
            left_x += 1
            right_x -= 1
    elif pose == "jump":
        left_x = cx - 4
        right_x = cx + 1
        leg_h = 5
    elif pose == "fall":
        left_x = cx - 5
        right_x = cx + 2
        if fi % 2:
            left_x -= 1
            right_x += 1
    elif pose == "short_attack":
        right_x += 2 + int(fase * 2)
        left_x -= 1
    elif pose == "long_attack":
        right_x += 1 + int(fase * 3)
        left_x -= int(fase * 1)
    elif pose == "hurt":
        left_x -= 1
        right_x -= 1
    elif pose == "swim":
        if fi % 2 == 0:
            left_x -= 4
            right_x += 2
        else:
            left_x = cx - 4
            right_x = cx + 1
    elif pose in ("climb", "zipline"):
        off = 1 if fi % 2 else -1
        left_x += off
        right_x += off
    elif pose == "parry":
        left_x -= 1
        right_x += 1
    elif pose == "slide":
        right_x += 4
        left_x -= 2
    for lx in (left_x, right_x):
        draw.rectangle((lx, base_y - leg_h, lx + 3, base_y), fill=C['leg_mid'])
        draw.rectangle((lx, base_y - leg_h + 1, lx + 2, base_y - 1), fill=C['leg_light'])
        for yy in range(base_y - leg_h, base_y + 1):
            if bayer_lt(lx + 3, yy, 5):
                draw.point((lx + 3, yy), fill=C['leg_dark'])
        draw.rectangle((lx, base_y - 1, lx + 3, base_y), fill=C['boot'])
        draw.rectangle((lx, base_y, lx + 3, base_y), fill=C['boot_dark'])
        draw.point((lx + 1, base_y - leg_h + 1), fill=C['leg_light'])
    for x in range(cx - 1, cx + 2):
        if bayer_lt(x, base_y - leg_h + 2, 6):
            draw.point((x, base_y - leg_h + 2), fill=C['leg_dark'])
    draw.point((cx - 5, torso_y0 + 1), fill=C['tunic_hi'])
    draw.point((cx + 4, torso_y0 + 1), fill=C['tunic_hi'])


def _gen_player_sheet(pose: str, frames: int, fw: int = 32, fh: int = 32):
    """Genera hoja PSX 32-bit HQ para pose dada; cada frame distinto (no copia IDLE)."""
    result: list[Image.Image] = []
    for fi in range(frames):
        img = Image.new("RGBA", (fw, fh), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        _dibujar_jugador_psx(draw, pose, fi, frames)
        _psx_outline_y_sombra(img)
        result.append(img)
    return result

def _gen_player_sprite(frames, base_data, fw=32, fh=32):
    return _gen_player_sheet("idle", frames, fw, fh)

def _gen_player_walk(frames=8, fw=32, fh=32):
    return _gen_player_sheet("walk", frames, fw, fh)

def _gen_player_swim(frames=4, fw=32, fh=32):
    return _gen_player_sheet("swim", frames, fw, fh)

def _gen_player_slashing(sheet_name, frames, fw=32, fh=32):
    pose = "short_attack" if "short" in sheet_name else "long_attack"
    return _gen_player_sheet(pose, frames, fw, fh)

def _gen_player_die(frames=8, fw=32, fh=32):
    return _gen_player_sheet("die", frames, fw, fh)

def _gen_player_all():
    print("  Player sprites...")
    hojas = {
        "player_idle.png": ("idle", 4),
        "player_walk.png": ("walk", 8),
        "player_jump.png": ("jump", 3),
        "player_fall.png": ("fall", 2),
        "player_crouch.png": ("crouch", 2),
        "player_short_attack.png": ("short_attack", 6),
        "player_long_attack.png": ("long_attack", 10),
        "player_hurt.png": ("hurt", 4),
        "player_die.png": ("die", 8),
        "player_swim.png": ("swim", 4),
        "player_parry.png": ("parry", 4),
        "player_climb.png": ("climb", 4),
        "player_zipline.png": ("zipline", 2),
    }
    for fname, (pose, frames) in hojas.items():
        sheet = _gen_player_sheet(pose, frames, 32, 32)
        _save_sheet(A / "sprites" / "player" / fname, sheet, 32, 32)


# ════════════════════════════════════════
# SECTION 2: ENEMY SPRITES per zone
# ════════════════════════════════════════

def _gen_enemy_sheet(path, w, h, frames, color, detail_color):
    """Generate enemy spritesheet PSX 32-bit con outline 1px + sombra dithered y variación real por frame."""
    imgs = []
    for _f in range(frames):
        img = Image.new("RGBA", (w, h), (0,0,0,0))
        draw = ImageDraw.Draw(img)
        # Body ellipse con highlight 1px arriba para metal/piel PSX
        draw.ellipse((2, 2, w-3, h-3), fill=color, outline=detail_color)
        # Highlight 1px reflejo superior
        highlight = tuple(min(255, c + 35) for c in color)
        draw.arc((2, 2, w-3, h-3), 200, 340, fill=highlight)
        # Eyes
        draw.rectangle((w//4, h//4, w//4+2, h//4+2), fill=(255,255,255))
        draw.rectangle((w*3//4-2, h//4, w*3//4, h//4+2), fill=(255,255,255))
        draw.point((w//4+1, h//4+1), fill=(0,0,0))
        draw.point((w*3//4-1, h//4+1), fill=(0,0,0))
        # Legs con variación real por fotograma (alternancia)
        off = 1 if _f % 2 == 0 else -1
        draw.line((w//4, h-3, w//4-2+off, h-1), fill=detail_color, width=1)
        draw.line((w*3//4, h-3, w*3//4+2-off, h-1), fill=detail_color, width=1)
        # Segundo par interior para walkers con trazo extra
        if w >= 16:
            draw.line((w//3, h-3, w//3-1+off, h-1), fill=detail_color)
            draw.line((w*2//3, h-3, w*2//3+1-off, h-1), fill=detail_color)
        # Sombra oclusión inferior dithered Bayer
        for x in range(2, w-2):
            bv = BAYER_4X4[(h-3) % 4][x % 4]
            if bv < 8:
                draw.point((x, h-3), fill=tuple(max(0, c - 22) for c in color))
        _psx_outline_y_sombra(img)
        imgs.append(img)
    _save_sheet(path, imgs, w, h)


# ── Dibujado por especie (PSX 32-bit HQ, silueta legible, paleta extendida, outline+Bayer) ──
# Cada especie tiene silueta única que parece el animal/objeto: rata con cola, cucaracha con alas,
# cuaderno con ojos, serpiente reptante, etc. Mantiene tamaños 16×12/14×10/12×12 y estilo vintage moderno.

def _dibujar_especie(draw, sid, w, h, f, nframes, mode="walk"):
    """Dibuja la silueta de la especie sid en el frame f (0..nframes-1), modo walk/hurt/die."""
    # Colores base por especie (walk); hurt/die los atenua pero conserva forma para legibilidad
    # Paleta extendida PSX 32-bit: 32-64 colores por sprite (no SNES 16)
    is_hurt = (mode == "hurt")
    is_die = (mode == "die")
    # helper highlight / sombra
    def hi(col): return tuple(min(255, c+35) for c in col)
    def dk(col, v=22): return tuple(max(0, c-v) for c in col)
    # oscilación por frame para animación
    paso = f % 2
    wing = 1 if f % 2 == 0 else -1
    leg = 1 if f % 2 == 0 else -1
    # --- WalkerInsect: escarabajo selva caparazón marrón, 6 patas, antenas ---
    if sid == "WalkerInsect":
        body = (92,62,38) if not is_hurt else (190,60,50)
        if is_die: body=(60,34,24)
        detail=(68,42,22) if not is_hurt else (110,30,30)
        if is_die: detail=(38,20,14)
        shell_hi=hi(body)
        # caparazón oval
        draw.ellipse((2,2,w-3,h-3), fill=body, outline=detail)
        draw.arc((2,2,w-3,h-3), 210, 340, fill=shell_hi)
        # línea central del élitro
        draw.line((w//2,3,w//2,h-3), fill=detail)
        # ojos blancos
        draw.point((w//3, h//3), fill=(255,255,255)); draw.point((w*2//3, h//3), fill=(255,255,255))
        draw.point((w//3, h//3+1), fill=(20,20,20)); draw.point((w*2//3, h//3+1), fill=(20,20,20))
        # 6 patas (3 por lado) con alternancia
        for i, y in enumerate((h-5, h-4, h-3)):
            off = leg if i%2==0 else -leg
            draw.line((4, y, 1+off, y+1), fill=detail)
            draw.line((w-5, y, w-2-off, y+1), fill=detail)
        # antenas
        draw.line((w//2-2,3, w//2-4,1), fill=detail); draw.line((w//2+2,3, w//2+4,1), fill=detail)
        draw.point((w//2-4,1), fill=(40,30,20)); draw.point((w//2+4,1), fill=(40,30,20))
        # dither sombra inferior
        for x in range(3,w-3):
            if BAYER_4X4[(h-3)%4][x%4] < 7:
                draw.point((x,h-3), fill=dk(body))
    # --- WalkerRaton: rata gris ojos rojos, cola, orejas, hocico ---
    elif sid == "WalkerRaton":
        body=(120,120,130) if not is_hurt else (190,60,50)
        if is_die: body=(70,68,72)
        detail=(80,80,90) if not is_hurt else (100,30,30)
        if is_die: detail=(50,48,52)
        # cuerpo oval
        draw.ellipse((3,3,w-5,h-4), fill=body, outline=detail)
        draw.ellipse((3,3,w-5,h-4), fill=body)
        draw.arc((3,3,w-5,h-4), 200, 320, fill=hi(body))
        # orejas
        draw.ellipse((4,1,7,4), fill=(200,150,150), outline=detail)
        draw.ellipse((w-8,1,w-5,4), fill=(200,150,150), outline=detail)
        draw.point((5,2), fill=(160,110,110)); draw.point((w-7,2), fill=(160,110,110))
        # hocico puntiagudo a la derecha
        draw.polygon([(w-5,h//2-1),(w-2,h//2),(w-5,h//2+1)], fill=body, outline=detail)
        draw.point((w-3,h//2), fill=(40,30,30))
        # ojos rojos
        draw.rectangle((w//2-1, h//3, w//2+1, h//3+2), fill=(220,40,35))
        draw.rectangle((w//2+3, h//3, w//2+5, h//3+2), fill=(220,40,35))
        draw.point((w//2, h//3+1), fill=(255,220,200)); draw.point((w//2+4, h//3+1), fill=(255,220,200))
        # cola curva atrás
        tx0, ty0 = 2, h//2
        tx1, ty1 = 0, h//2 + (1 if paso else -1)
        draw.line((tx0, ty0, tx1, ty1), fill=(180,130,120), width=1)
        draw.line((tx1, ty1, tx1-1, ty1 + (1 if paso else -1)), fill=(160,110,100))
        # patas con variación
        draw.line((w//3, h-3, w//3-1+leg, h-1), fill=detail)
        draw.line((w*2//3, h-3, w*2//3+1-leg, h-1), fill=detail)
        for x in range(4,w-4):
            if BAYER_4X4[(h-3)%4][x%4] < 8: draw.point((x,h-3), fill=dk(body))
    # --- FlyingCucaracha: cucaracha voladora alas desplegadas, caparazón brillante, antenas ---
    elif sid == "FlyingCucaracha":
        body=(84,62,36) if not is_hurt else (190,60,50)
        if is_die: body=(60,42,28)
        detail=(58,42,22); wing_col=(148,118,74) if not is_hurt else (200,90,80)
        if is_die: wing_col=(90,72,52)
        # cuerpo central
        draw.ellipse((w//2-4, h//2-2, w//2+4, h//2+3), fill=body, outline=detail)
        draw.arc((w//2-4, h//2-2, w//2+4, h//2+3), 210, 330, fill=hi(body))
        # alas (2) con batido por frame
        off = 1 if paso else 0
        # ala izquierda
        draw.ellipse((1, 2+off, w//2-1, h-2-off), fill=wing_col, outline=detail)
        # ala derecha
        draw.ellipse((w//2+1, 2+off, w-2, h-2-off), fill=wing_col, outline=detail)
        # brillo 1px en alas
        draw.point((3, h//2), fill=hi(wing_col)); draw.point((w-4, h//2), fill=hi(wing_col))
        # antenas largas
        draw.line((w//2-2, h//2-2, 1, 1), fill=detail); draw.line((w//2+2, h//2-2, w-2, 1), fill=detail)
        # ojos blancos con pupila
        draw.point((w//2-2, h//2-1), fill=(255,255,255)); draw.point((w//2+2, h//2-1), fill=(255,255,255))
        draw.point((w//2-2, h//2), fill=(0,0,0)); draw.point((w//2+2, h//2), fill=(0,0,0))
        # patas plegadas abajo
        draw.line((w//2-2, h//2+3, w//2-4, h-1), fill=detail); draw.line((w//2+2, h//2+3, w//2+4, h-1), fill=detail)
        for x in range(2,w-2):
            if BAYER_4X4[(h-2)%4][x%4] < 7: draw.point((x,h-2), fill=dk(body,14))
    # --- FlyingBird: ave selva momoto verde azulado/naranja, pico, alas ---
    elif sid == "FlyingBird":
        body=(70,140,110) if not is_hurt else (190,60,50)
        if is_die: body=(58,90,78)
        detail=(45,95,75); wing=(60,110,180) if not is_hurt else (200,80,80)
        if is_die: wing=(48,78,120)
        chest=(230,150,70)  # naranja momoto
        # cuerpo pájaro
        draw.ellipse((w//2-3, h//2-2, w//2+3, h//2+3), fill=body, outline=detail)
        draw.ellipse((w//2-2, h//2-1, w//2+2, h//2+2), fill=chest)
        # alas desplegadas con aleteo
        wy = 1 if paso else 0
        draw.polygon([(1, h//2-1+wy),(w//2-2, h//2),(1, h//2+2-wy)], fill=wing, outline=detail)
        draw.polygon([(w-2, h//2-1+wy),(w//2+2, h//2),(w-2, h//2+2-wy)], fill=wing, outline=detail)
        draw.point((2, h//2), fill=hi(wing)); draw.point((w-3, h//2), fill=hi(wing))
        # cabeza y pico naranja
        draw.ellipse((w//2+2, h//2-3, w//2+5, h//2), fill=body, outline=detail)
        draw.polygon([(w//2+5, h//2-1),(w-1, h//2),(w//2+5, h//2+1)], fill=(240,180,60), outline=(150,110,30))
        # cola
        draw.polygon([(w//2-4, h//2+1),(0, h//2+2),(w//2-4, h//2+3)], fill=(40,80,60))
        # ojo
        draw.point((w//2+3, h//2-2), fill=(255,255,255)); draw.point((w//2+3, h//2-1), fill=(0,0,0))
        for x in range(2,w-2):
            if BAYER_4X4[(h-3)%4][x%4] < 7: draw.point((x,h-2), fill=dk(body,18))
    # --- ShooterFrog: rana dardo roja/azul Oophaga pumilio ---
    elif sid == "ShooterFrog":
        body=(190,42,48) if not is_hurt else (220,70,70)
        if is_die: body=(110,30,34)
        belly=(60,90,200) if not is_hurt else (200,70,70)
        if is_die: belly=(40,60,130)
        detail=(120,28,32)
        # cuerpo rana agachada
        draw.ellipse((2, h-8, w-3, h-2), fill=body, outline=detail)
        draw.ellipse((w//2-3, h-9, w//2+3, h-5), fill=body, outline=detail) # cabeza
        draw.ellipse((w//2-4, h-9, w//2-1, h-6), fill=belly) # mancha azul
        draw.ellipse((w//2+1, h-9, w//2+4, h-6), fill=belly)
        # ojos saltones
        draw.ellipse((w//2-4, 1, w//2-1, 4), fill=(255,255,255), outline=(0,0,0))
        draw.ellipse((w//2+1, 1, w//2+4, 4), fill=(255,255,255), outline=(0,0,0))
        draw.ellipse((w//2-3,2,w//2-2,3), fill=(0,0,0)); draw.ellipse((w//2+2,2,w//2+3,3), fill=(0,0,0))
        draw.point((w//2-3,2), fill=(80,140,255)); draw.point((w//2+2,2), fill=(80,140,255))
        # patas delanteras
        draw.line((4, h-5, 2, h-2), fill=detail); draw.line((w-5, h-5, w-3, h-2), fill=detail)
        # patas traseras anchas
        draw.line((3, h-4, 1, h-2), fill=detail); draw.line((w-4, h-4, w-2, h-2), fill=detail)
        # puntos azules en lomo (veneno)
        draw.point((w//2, h-6), fill=belly); draw.point((w//2-2, h-5), fill=belly); draw.point((w//2+2, h-5), fill=belly)
        for x in range(3,w-3):
            if BAYER_4X4[(h-3)%4][x%4] < 7: draw.point((x,h-3), fill=dk(body,16))
    # --- ShooterCocinero: cocinero uniforme manchado lanzando bandeja ---
    elif sid == "ShooterCocinero":
        body=(236,232,222) if not is_hurt else (220,90,90)
        if is_die: body=(150,148,142)
        detail=(90,85,78); skin=(232,192,148); hat=(250,250,250)
        # cuerpo uniforme
        draw.rectangle((w//2-3, 3, w//2+3, h-3), fill=body, outline=detail)
        draw.rectangle((w//2-3, h-4, w//2+3, h-3), fill=(120,120,130)) # cinturón
        # manchas
        draw.point((w//2-1,5), fill=(180,60,60)); draw.point((w//2+1,7), fill=(120,80,30))
        # gorro alto
        draw.rectangle((w//2-3,0,w//2+3,3), fill=hat, outline=detail)
        draw.rectangle((w//2-2,1,w//2+2,2), fill=hat)
        # cabeza
        draw.rectangle((w//2-2,2,w//2+2,4), fill=skin)
        # ojos
        draw.point((w//2-1,3), fill=(0,0,0)); draw.point((w//2+1,3), fill=(0,0,0))
        # brazo lanzando bandeja por frame
        off = 2 if paso else 0
        draw.line((w//2+3,5, w//2+5+off,4), fill=skin, width=1)
        # bandeja
        draw.ellipse((w//2+4+off,3,w//2+8+off,6), fill=(192,152,96), outline=(120,90,60))
        draw.point((w//2+6+off,4), fill=hi((192,152,96)))
        # piernas
        draw.line((w//2-2, h-3, w//2-2, h-1), fill=(60,60,70)); draw.line((w//2+2, h-3, w//2+2, h-1), fill=(60,60,70))
        for x in range(w//2-3,w//2+4):
            if BAYER_4X4[(h-2)%4][x%4] <7: draw.point((x,h-2), fill=dk(body,12))
    # --- WalkerEstudiante: estudiante mochila teléfono ---
    elif sid == "WalkerEstudiante":
        body=(66,82,128) if not is_hurt else (190,60,50)
        if is_die: body=(52,64,98)
        detail=(48,62,98); skin=(236,200,160); pant=(52,62,92)
        # torso
        draw.rectangle((w//2-3,2,w//2+3, h-4), fill=body, outline=detail)
        draw.line((w//2,3,w//2,h-4), fill=detail)
        # mochila atrás (bulto)
        draw.rectangle((w//2-4,4,w//2-1,8), fill=(120,80,45), outline=(80,52,28))
        draw.point((w//2-3,5), fill=hi((120,80,45)))
        # cabeza
        draw.ellipse((w//2-2,0,w//2+2,3), fill=skin, outline=(180,150,120))
        draw.point((w//2-1,1), fill=(0,0,0)); draw.point((w//2+1,1), fill=(0,0,0))
        # brazos, uno con teléfono brillante
        off = leg
        draw.line((w//2-3,5,w//2-5,7+off), fill=skin)
        draw.line((w//2+3,5,w//2+5+off,6), fill=skin)
        # teléfono
        draw.rectangle((w//2+4+off,5,w//2+6+off,8), fill=(40,200,240), outline=(20,140,180))
        draw.point((w//2+5+off,6), fill=(255,255,255))
        # piernas con marcha
        draw.line((w//2-2,h-4,w//2-3+leg,h-1), fill=pant)
        draw.line((w//2+2,h-4,w//2+3-leg,h-1), fill=pant)
        for x in range(w//2-3,w//2+4):
            if BAYER_4X4[(h-2)%4][x%4]<7: draw.point((x,h-2), fill=dk(body,12))
    # --- FlyingNotebook: hojas cuaderno animadas con ojos, líneas ---
    elif sid == "FlyingNotebook":
        paper=(244,244,236) if not is_hurt else (240,160,160)
        if is_die: paper=(180,180,172)
        line_bl=(120,150,220); margin_rd=(220,90,90); detail=(180,180,172)
        # hoja principal rect con espiral
        draw.rectangle((2,2,w-3,h-3), fill=paper, outline=detail)
        # líneas azules
        for y in range(4,h-4,2):
            draw.line((4,y,w-4,y), fill=line_bl)
        # margen rojo vertical
        draw.line((5,2,5,h-3), fill=margin_rd)
        # ojos en la hoja (posesos)
        draw.ellipse((w//3-1, h//3-1, w//3+1, h//3+1), fill=(255,255,255), outline=(0,0,0))
        draw.ellipse((w*2//3-1, h//3-1, w*2//3+1, h//3+1), fill=(255,255,255), outline=(0,0,0))
        draw.point((w//3, h//3), fill=(0,0,0)); draw.point((w*2//3, h//3), fill=(0,0,0))
        draw.point((w//3+1, h//3), fill=(80,140,255)); draw.point((w*2//3+1, h//3), fill=(80,140,255))
        # giro por frame: hoja secundaria detrás con offset
        off = 1 if paso else -1
        draw.rectangle((3+off,3+off,w-4+off,h-4+off), outline=(200,200,180))
        # brillo 1px
        draw.point((4,3), fill=(255,255,255))
        for x in range(3,w-3):
            if BAYER_4X4[(h-3)%4][x%4] <8: draw.point((x,h-3), fill=dk(paper,14))
    # --- ShooterTiza: borrador pizarra antropomorfo ---
    elif sid == "ShooterTiza":
        body=(120,92,68) if not is_hurt else (200,80,80)
        if is_die: body=(92,72,54)
        detail=(90,70,52); chalk=(244,244,240)
        # borrador rect felpa
        draw.rectangle((1,3,w-2,h-3), fill=body, outline=detail)
        draw.rectangle((2,4,w-3,h-4), fill=body)
        # fieltro textura dither
        for y in range(4,h-4):
            for x in range(2,w-2):
                if BAYER_4X4[y%4][x%4] <4:
                    draw.point((x,y), fill=dk(body,10))
        # ojos saltones en borrador
        draw.ellipse((w//3-1,1,w//3+1,3), fill=(255,255,255), outline=(0,0,0))
        draw.ellipse((w*2//3-1,1,w*2//3+1,3), fill=(255,255,255), outline=(0,0,0))
        draw.point((w//3,2), fill=(0,0,0)); draw.point((w*2//3,2), fill=(0,0,0))
        # tiza en mano por frame
        tx = w-3 + (1 if paso else 0)
        draw.rectangle((tx,5,tx+2,8), fill=chalk, outline=(200,200,190))
        draw.point((tx+1,6), fill=(255,255,255))
        # polvo tiza
        draw.point((w//2, h-2), fill=(220,220,210))
        for x in range(2,w-2):
            if BAYER_4X4[(h-2)%4][x%4] <6: draw.point((x,h-2), fill=dk(body,12))
    # --- WalkerSerpientePequena: terciopelo pequeña marrón/bronceada reptante ---
    elif sid == "WalkerSerpientePequena":
        body=(118,86,54) if not is_hurt else (200,80,70)
        if is_die: body=(84,62,40)
        detail=(84,58,34); belly=(200,185,150); tongue=(220,60,60)
        # serpiente horizontal con onda por frame: 3 segmentos
        y0 = h//2 -1 + (1 if paso else -1)
        y1 = h//2 + (1 if not paso else -1)
        pts=[(2,y0),(6,y1),(10,y0),(14,y1),(w-2,y0)]
        for i in range(len(pts)-1):
            draw.line((pts[i][0],pts[i][1],pts[i+1][0],pts[i+1][1]), fill=body, width=2)
            draw.line((pts[i][0],pts[i][1],pts[i+1][0],pts[i+1][1]), fill=detail, width=1)
        # cabeza triangular a la derecha
        draw.polygon([(w-5,h//2-2),(w-2,h//2),(w-5,h//2+2)], fill=body, outline=detail)
        draw.point((w-4,h//2-1), fill=(0,0,0)); draw.point((w-4,h//2), fill=(255,200,60))
        # lengua bífida
        draw.line((w-2,h//2, w, h//2-1), fill=tongue); draw.line((w-2,h//2, w, h//2+1), fill=tongue)
        # patrón manchas
        for x in (6,10,14):
            draw.point((x, y0 if x%4==2 else y1), fill=belly)
        for x in range(2,w-2):
            if BAYER_4X4[(h-2)%4][x%4] <7: draw.point((x,h-2), fill=dk(body,14))
    # --- FlyingBoa: boa arborícola grande ondulando ---
    elif sid == "FlyingBoa":
        body=(92,112,66) if not is_hurt else (200,80,80)
        if is_die: body=(70,86,52)
        detail=(64,84,44); belly=(210,200,170)
        y0 = h//2 + (1 if paso else -1)
        y1 = h//2 - (1 if paso else -1)
        pts=[(1,y0),(4,y1),(8,y0),(11,y1),(w-2,y0)]
        for i in range(len(pts)-1):
            draw.line((pts[i][0],pts[i][1],pts[i+1][0],pts[i+1][1]), fill=body, width=3)
        for i in range(len(pts)-1):
            draw.line((pts[i][0],pts[i][1],pts[i+1][0],pts[i+1][1]), fill=detail, width=1)
        # cabeza
        draw.ellipse((w-5,h//2-2,w-1,h//2+2), fill=body, outline=detail)
        draw.point((w-3,h//2-1), fill=(0,0,0)); draw.point((w-2,h//2-1), fill=(255,200,60))
        # patrón
        for x in (4,8,11):
            draw.point((x, y0 if x%2 else y1), fill=belly)
        for x in range(1,w-1):
            if BAYER_4X4[(h-2)%4][x%4]<7: draw.point((x,h-2), fill=dk(body,10))
    # --- ShooterSerpienteArbol: víbora árbol verde enroscada en rama ---
    elif sid == "ShooterSerpienteArbol":
        body=(58,148,78) if not is_hurt else (200,80,80)
        if is_die: body=(44,108,58)
        detail=(38,108,58); belly=(180,220,160)
        # rama horizontal
        draw.line((0,h-3,w-1,h-3), fill=(110,80,50))
        draw.line((0,h-2,w-1,h-2), fill=(140,110,80))
        # serpiente enroscada: espiral 2 vueltas
        cx, cy = w//2, h//2 -1
        draw.ellipse((cx-5,cy-3,cx+5,cy+3), outline=body, width=2)
        draw.ellipse((cx-3,cy-2,cx+3,cy+1), fill=body, outline=detail)
        # cabeza saliente arriba
        draw.ellipse((cx+3,1,cx+7,4), fill=body, outline=detail)
        draw.point((cx+5,2), fill=(255,220,60)); draw.point((cx+6,2), fill=(0,0,0))
        draw.point((cx+5,3), fill=(0,0,0))
        # lengua
        if paso: draw.line((cx+7,2,cx+9,1), fill=(220,60,60)); draw.line((cx+7,2,cx+9,3), fill=(220,60,60))
        # patrón verde oscuro manchas
        draw.point((cx-2,cy), fill=detail); draw.point((cx+2,cy), fill=belly)
        for x in range(1,w-1):
            if BAYER_4X4[(h-3)%4][x%4] <7: draw.point((x,h-3), fill=dk(detail,12))
    # --- WalkerTerciopelo: terciopelo grande adulta cuerpo grueso ---
    elif sid == "WalkerTerciopelo":
        body=(108,78,42) if not is_hurt else (210,80,70)
        if is_die: body=(78,56,32)
        detail=(78,54,28); pattern=(210,150,80); belly=(220,200,170)
        # cuerpo grueso ondulado 3 segmentos más alto
        y0 = h//2 + (1 if paso else 0)
        y1 = h//2 - (1 if paso else 0)
        pts=[(1,y0),(5,y1),(9,y0),(13,y1),(w-1,y0)]
        for i in range(len(pts)-1):
            draw.line((pts[i][0],pts[i][1],pts[i+1][0],pts[i+1][1]), fill=body, width=3)
            draw.line((pts[i][0],pts[i][1],pts[i+1][0],pts[i+1][1]), fill=detail, width=1)
        # cabeza más grande
        draw.polygon([(w-6,h//2-3),(w-1,h//2),(w-6,h//2+3)], fill=body, outline=detail)
        draw.point((w-4,h//2-1), fill=(0,0,0)); draw.point((w-3,h//2), fill=(255,210,60))
        draw.line((w-1,h//2, w+1, h//2-1), fill=(220,40,40)); draw.line((w-1,h//2, w+1, h//2+1), fill=(220,40,40))
        # patrón diamante
        for x in (5,9,13):
            draw.point((x, y0 if x%2 else y1), fill=pattern)
            draw.point((x, (y0+y1)//2), fill=belly)
        for x in range(1,w-1):
            if BAYER_4X4[(h-2)%4][x%4]<6: draw.point((x,h-2), fill=dk(body,14))
    # --- ShooterVenomoLargo: cobra escupidora elevada balanceándose ---
    elif sid == "ShooterVenomoLargo":
        body=(140,120,70) if not is_hurt else (220,90,90)
        if is_die: body=(100,86,52)
        detail=(100,86,52); hood=(90,76,42); belly=(210,200,170)
        # cuerpo vertical cobra (cuello)
        cx=w//2 + (1 if paso else -1)
        draw.rectangle((cx-2,4,cx+2,h-2), fill=body, outline=detail)
        # capucha expandida
        draw.ellipse((cx-4,1,cx+4,6), fill=hood, outline=detail)
        draw.ellipse((cx-3,2,cx+3,5), fill=body)
        # patrón capucha ocelo
        draw.point((cx-1,3), fill=detail); draw.point((cx+1,3), fill=detail)
        # cabeza
        draw.ellipse((cx-2,0,cx+2,3), fill=body, outline=detail)
        draw.point((cx-1,1), fill=(0,0,0)); draw.point((cx+1,1), fill=(0,0,0))
        draw.point((cx,2), fill=(220,40,40))
        # lengua
        draw.line((cx,3,cx,5), fill=(220,60,60))
        # brillo
        draw.point((cx-2,2), fill=hi(body))
        for x in range(cx-2,cx+3):
            if BAYER_4X4[(h-2)%4][x%4] <7: draw.point((x,h-2), fill=dk(body,14))
    # --- FlyingTerciovolador: serpiente alada mitológica 2 alas pequeñas ---
    elif sid == "FlyingTerciovolador":
        body=(110,130,70) if not is_hurt else (210,80,80)
        if is_die: body=(84,98,52)
        detail=(84,98,52); wing=(210,190,140)
        # serpiente
        y0 = h//2 + (1 if paso else -1)
        y1 = h//2 - (1 if paso else -1)
        pts=[(2,y0),(6,y1),(10,y0),(w-3,y1)]
        for i in range(len(pts)-1):
            draw.line((pts[i][0],pts[i][1],pts[i+1][0],pts[i+1][1]), fill=body, width=2)
            draw.line((pts[i][0],pts[i][1],pts[i+1][0],pts[i+1][1]), fill=detail, width=1)
        # cabeza
        draw.polygon([(w-5,h//2-1),(w-2,h//2),(w-5,h//2+1)], fill=body, outline=detail)
        draw.point((w-4,h//2), fill=(0,0,0))
        # alas pequeñas
        wy = 1 if paso else 0
        draw.polygon([(w//2-2, y0-1+wy),(w//2, y0-4+wy),(w//2+2, y0-1+wy)], fill=wing, outline=detail)
        draw.polygon([(w//2-2, y0+1-wy),(w//2, y0+4-wy),(w//2+2, y0+1-wy)], fill=wing, outline=detail)
        draw.point((w//2, y0-3+wy), fill=hi(wing)); draw.point((w//2, y0+3-wy), fill=hi(wing))
        for x in range(2,w-2):
            if BAYER_4X4[(h-2)%4][x%4] <7: draw.point((x,h-2), fill=dk(body,12))
    # --- WalkerGuardia: guardia seguridad uniforme linterna ojos brillo verde ---
    elif sid == "WalkerGuardia":
        body=(48,58,112) if not is_hurt else (210,70,70)
        if is_die: body=(38,46,88)
        detail=(36,44,86); skin=(236,200,164); pant=(36,44,86); vest=(88,88,108)
        # torso uniforme
        draw.rectangle((w//2-3,2,w//2+3,h-4), fill=body, outline=detail)
        # chaleco
        draw.rectangle((w//2-2,4,w//2+2,8), fill=vest, outline=(60,60,80))
        draw.point((w//2,5), fill=(200,200,220))
        # cabeza + gorra
        draw.rectangle((w//2-2,0,w//2+2,2), fill=(40,40,60), outline=detail) # gorra
        draw.rectangle((w//2-2,1,w//2+2,3), fill=skin)
        # ojos brillo verde (poseído)
        draw.point((w//2-1,2), fill=(80,255,120)); draw.point((w//2+1,2), fill=(80,255,120))
        draw.point((w//2-1,2), fill=(255,255,255))
        # linterna en mano derecha
        off = 1 if paso else 0
        draw.rectangle((w//2+3+off,5,w//2+5+off,6), fill=(60,60,70), outline=(40,40,50))
        draw.rectangle((w//2+5+off,5,w//2+7+off,6), fill=(255,240,120), outline=(200,180,60))
        draw.point((w//2+6+off,5), fill=(255,255,255))
        # piernas
        draw.line((w//2-2,h-4,w//2-3+leg,h-1), fill=pant)
        draw.line((w//2+2,h-4,w//2+3-leg,h-1), fill=pant)
        for x in range(w//2-3,w//2+4):
            if BAYER_4X4[(h-2)%4][x%4]<7: draw.point((x,h-2), fill=dk(body,12))
    # --- Shielded: guardia con escudo frontal metálico ---
    elif sid == "Shielded":
        body=(54,64,118) if not is_hurt else (210,70,70)
        if is_die: body=(44,52,94)
        detail=(40,48,92); shield=(168,172,188); shield_dk=(112,116,132)
        # cuerpo como guardia pero con escudo grande delante
        draw.rectangle((w//2-3,2,w//2+1,h-4), fill=body, outline=detail) # torso parcialmente oculto
        draw.rectangle((w//2-2,0,w//2,2), fill=(40,40,60)) # gorra
        draw.rectangle((w//2-2,1,w//2,3), fill=(236,200,164))
        draw.point((w//2-1,2), fill=(80,255,120))
        # escudo frontal metálico grande
        draw.rectangle((w//2+1,1,w-2,h-2), fill=shield, outline=shield_dk)
        # emblema escudo
        draw.rectangle((w//2+3,3,w-4,5), fill=shield_dk)
        draw.ellipse((w//2+4,6,w-4,8), fill=(200,40,40), outline=shield_dk)
        # brillo metal 1px
        draw.line((w//2+1,1,w//2+1,h-2), fill=hi(shield))
        draw.point((w//2+2,2), fill=(255,255,255))
        # piernas
        draw.line((w//2-2,h-4,w//2-2,h-1), fill=detail); draw.line((w//2,h-4,w//2+1,h-1), fill=detail)
    # --- Swimmer: nadador con aletas deriva ---
    elif sid == "Swimmer":
        body=(38,78,148) if not is_hurt else (210,80,80)
        if is_die: body=(30,62,118)
        detail=(28,58,118); skin=(236,200,164); fin=(68,148,188)
        # cuerpo horizontal nadando
        cx, cy = w//2, h//2
        off = 1 if paso else -1
        draw.ellipse((cx-5, cy-3+off, cx+5, cy+3+off), fill=body, outline=detail)
        draw.ellipse((cx-3, cy-2+off, cx+1, cy+2+off), fill=skin)
        # cabeza + snorkel
        draw.ellipse((cx+4, cy-2+off, cx+7, cy+1+off), fill=skin, outline=detail)
        draw.rectangle((cx+6, cy-3+off, cx+7, cy-1+off), fill=(40,200,255), outline=detail)
        # gafas
        draw.rectangle((cx+5, cy-1+off, cx+7, cy+0+off), fill=(0,0,0))
        # aletas pies
        draw.polygon([(cx-6, cy+1+off),(cx-9, cy+3+off),(cx-6, cy+3+off)], fill=fin, outline=detail)
        draw.polygon([(cx-6, cy-1+off),(cx-9, cy-3+off),(cx-6, cy-1+off)], fill=fin, outline=detail)
        # brazos brazada
        draw.line((cx-1, cy+off, cx-4+off, cy+1+off), fill=skin)
        # burbujas
        if paso: draw.point((cx+8, cy-2+off), fill=(180,230,255,200))
        for x in range(cx-5,cx+6):
            if BAYER_4X4[(cy+3)%4][x%4] <7: draw.point((x, cy+3+off), fill=dk(body,12))
    # --- FlyingBomber: dron bombardero ---
    elif sid == "FlyingBomber":
        body=(112,116,128) if not is_hurt else (210,70,70)
        if is_die: body=(88,92,102)
        detail=(84,88,100); prop=(64,68,78); bomb=(52,52,62)
        # cuerpo central dron
        draw.rectangle((w//2-4, h//2-2, w//2+4, h//2+2), fill=body, outline=detail)
        draw.rectangle((w//2-3, h//2-1, w//2+3, h//2+1), fill=hi(body))
        # hélices 4 (pequeñas barras girando por frame)
        rot = 1 if paso else -1
        draw.line((w//2-4, h//2-3, w//2-2-rot, h//2-3), fill=prop, width=1)
        draw.line((w//2+2+rot, h//2-3, w//2+4, h//2-3), fill=prop)
        draw.line((w//2-4, h//2+3, w//2-2-rot, h//2+3), fill=prop)
        draw.line((w//2+2+rot, h//2+3, w//2+4, h//2+3), fill=prop)
        # ojo sensor rojo
        draw.rectangle((w//2-1, h//2-1, w//2+1, h//2), fill=(220,50,50), outline=(0,0,0))
        draw.point((w//2, h//2-1), fill=(255,100,100))
        # bomba colgando
        draw.ellipse((w//2-2, h//2+2, w//2+2, h//2+5), fill=bomb, outline=detail)
        draw.point((w//2, h//2+3), fill=hi(bomb))
        for x in range(w//2-4,w//2+5):
            if BAYER_4X4[(h-2)%4][x%4] <7: draw.point((x,h-2), fill=dk(body,10))
    # --- BruteGolemHielo: gólem de hielo ground slam ---
    elif sid == "BruteGolemHielo":
        body=(158,216,244) if not is_hurt else (220,150,150)
        if is_die: body=(110,150,170)
        detail=(98,148,178); crack=(220,244,255)
        # cuerpo bloque hielo grande
        draw.rectangle((2,2,w-3,h-3), fill=body, outline=detail)
        draw.rectangle((4,4,w-5,h-5), fill=hi(body))
        # grietas hielo
        draw.line((w//2,4,w//2-1,h-5), fill=crack)
        draw.line((4,h//2,w-4,h//2), fill=crack)
        draw.line((w//3,3,w//2, h//2), fill=detail)
        # ojos brillantes azules
        draw.rectangle((w//3-1, h//3, w//3+1, h//3+2), fill=(0,80,200), outline=(0,0,0))
        draw.rectangle((w*2//3-1, h//3, w*2//3+1, h//3+2), fill=(0,80,200), outline=(0,0,0))
        draw.point((w//3, h//3+1), fill=(120,200,255)); draw.point((w*2//3, h//3+1), fill=(120,200,255))
        # brazos gruesos
        off = 1 if paso else 0
        draw.rectangle((1, h//2+off, 4, h-3), fill=body, outline=detail)
        draw.rectangle((w-5, h//2+off, w-2, h-3), fill=body, outline=detail)
        # sombra dither
        for x in range(3,w-3):
            if BAYER_4X4[(h-3)%4][x%4] <7: draw.point((x,h-3), fill=dk(body,18))
    # --- ChargerWolf: lobo de planicie carga ---
    elif sid == "ChargerWolf":
        body=(136,136,144) if not is_hurt else (220,90,90)
        if is_die: body=(100,100,108)
        detail=(88,88,96); belly=(210,210,220); snout=(180,180,190); nose=(20,20,24)
        # cuerpo lobo
        draw.ellipse((3, h-7, w-6, h-2), fill=body, outline=detail)
        draw.ellipse((3, h-7, w-6, h-2), fill=body)
        draw.arc((3, h-7, w-6, h-2), 200, 340, fill=hi(body))
        # cabeza
        draw.ellipse((w-7, h-8, w-1, h-3), fill=body, outline=detail)
        draw.ellipse((w-6, h-7, w-2, h-4), fill=snout)
        draw.point((w-2, h-6), fill=nose)
        # orejas triangulares
        draw.polygon([(w-6,h-8),(w-5,h-10),(w-4,h-8)], fill=body, outline=detail)
        draw.polygon([(w-4,h-8),(w-3,h-10),(w-2,h-8)], fill=body, outline=detail)
        # ojos amarillos
        draw.point((w-4,h-6), fill=(255,220,80)); draw.point((w-4,h-5), fill=(0,0,0))
        # cola
        draw.line((3, h-5, 0, h-4-leg), fill=body, width=1); draw.line((3, h-5, 0, h-4-leg), fill=detail)
        # patas con carrera por frame
        leg_off = 2 if paso else -1
        draw.line((6, h-2, 5+leg_off, h-1), fill=detail)
        draw.line((w-8, h-2, w-9-leg_off, h-1), fill=detail)
        # dientes
        draw.point((w-3, h-4), fill=(255,255,255))
        for x in range(3,w-6):
            if BAYER_4X4[(h-2)%4][x%4] <7: draw.point((x,h-2), fill=dk(body,12))
    # --- WalkerGarza: garza alta pasos lentos ---
    elif sid == "WalkerGarza":
        body=(228,228,236) if not is_hurt else (220,120,120)
        if is_die: body=(170,170,178)
        detail=(180,180,190); beak=(255,228,100); leg_col=(44,44,52)
        # cuerpo
        draw.ellipse((w//2-3, h-7, w//2+3, h-2), fill=body, outline=detail)
        draw.point((w//2, h-6), fill=hi(body))
        # cuello largo en S por frame
        nx = w//2+1 + (1 if paso else -1)
        draw.line((w//2, h-7, nx, 2), fill=body, width=1)
        draw.line((w//2, h-7, nx, 2), fill=detail)
        # cabeza y pico largo
        draw.ellipse((nx-2,0,nx+2,3), fill=body, outline=detail)
        draw.polygon([(nx+1,1),(nx+6,1),(nx+1,2)], fill=beak, outline=(180,160,60))
        draw.point((nx,1), fill=(0,0,0))
        # patas largas finas
        draw.line((w//2-1, h-2, w//2-2+leg, h-1), fill=leg_col)
        draw.line((w//2+1, h-2, w//2+2-leg, h-1), fill=leg_col)
        # ala plegada
        draw.ellipse((w//2-2, h-6, w//2+2, h-4), fill=hi(body), outline=detail)
        for x in range(w//2-3,w//2+4):
            if BAYER_4X4[(h-2)%4][x%4] <7: draw.point((x,h-2), fill=dk(body,12))
    # --- FlyingHalcon: gavilán caminero vuelo + picado ---
    elif sid == "FlyingHalcon":
        body=(128,88,48) if not is_hurt else (220,90,90)
        if is_die: body=(96,66,36)
        detail=(88,60,30); wing=(100,70,36); belly=(236,232,220)
        # cuerpo
        draw.ellipse((w//2-3, h//2-2, w//2+3, h//2+2), fill=body, outline=detail)
        draw.ellipse((w//2-2, h//2-1, w//2+2, h//2+1), fill=belly)
        # alas con batido
        wy = 2 if paso else -1
        draw.polygon([(1, h//2+wy),(w//2-2, h//2),(1, h//2+2+wy)], fill=wing, outline=detail)
        draw.polygon([(w-2, h//2+wy),(w//2+2, h//2),(w-2, h//2+2+wy)], fill=wing, outline=detail)
        draw.point((2, h//2+wy), fill=hi(wing)); draw.point((w-3, h//2+wy), fill=hi(wing))
        # cabeza pico ganchudo
        draw.ellipse((w//2+2, h//2-3, w//2+5, h//2-1), fill=body, outline=detail)
        draw.polygon([(w//2+5,h//2-2),(w-1,h//2-1),(w//2+5,h//2-1)], fill=(240,210,60), outline=(180,160,40))
        draw.point((w//2+3, h//2-3), fill=(255,255,255)); draw.point((w//2+3, h//2-2), fill=(0,0,0))
        # cola bandeada
        draw.rectangle((w//2-4, h//2+1, w//2-1, h//2+2), fill=belly)
        draw.line((w//2-4, h//2+1, w//2-1, h//2+1), fill=detail)
        for x in range(2,w-2):
            if BAYER_4X4[(h-2)%4][x%4] <7: draw.point((x,h-2), fill=dk(body,12))
    # --- ShooterQuetzal: quetzal francotirador posado, pluma larga ---
    elif sid == "ShooterQuetzal":
        body=(48,156,88) if not is_hurt else (220,90,90)
        if is_die: body=(36,116,66)
        detail=(32,116,66); chest=(190,48,48); beak=(255,228,60)
        # cuerpo erguido 12x12
        draw.ellipse((w//2-3,4,w//2+3,h-2), fill=body, outline=detail)
        draw.ellipse((w//2-3,5,w//2+3,7), fill=chest, outline=(140,36,36))
        draw.arc((w//2-3,4,w//2+3,h-2), 200, 330, fill=hi(body))
        # cabeza cresta
        draw.ellipse((w//2-2,1,w//2+2,4), fill=body, outline=detail)
        draw.polygon([(w//2,1),(w//2+1,0),(w//2+2,1)], fill=body, outline=detail) # cresta
        draw.point((w//2+1,2), fill=(0,0,0))
        # pico pequeño
        draw.polygon([(w//2+2,2),(w//2+4,2),(w//2+2,3)], fill=beak, outline=(180,160,40))
        # pluma cola larguísima (se sale por abajo pero recortada)
        draw.line((w//2, h-2, w//2+1, h-1), fill=(20,180,120), width=1)
        draw.line((w//2+1, h-2, w//2+2, h-1), fill=(40,200,140))
        # rama donde se posa
        draw.line((1,h-2,w-2,h-2), fill=(110,80,50))
        for x in range(w//2-3,w//2+4):
            if BAYER_4X4[(h-2)%4][x%4] <7: draw.point((x,h-2), fill=dk(body,14))
    # --- WalkerPalom: paloma domestica corrompida ---
    elif sid == "WalkerPalom":
        body=(138,138,148) if not is_hurt else (220,90,90)
        if is_die: body=(100,100,108)
        detail=(100,100,110); neck=(88,108,158); beak=(244,168,68); eye_col=(220,44,44)
        # cuerpo paloma gordita
        draw.ellipse((2,3,w-3,h-2), fill=body, outline=detail)
        draw.arc((2,3,w-3,h-2), 200, 340, fill=hi(body))
        # cuello iridiscente
        draw.ellipse((w-6,3,w-3,7), fill=neck, outline=detail)
        # cabeza
        draw.ellipse((w-6,2,w-2,5), fill=body, outline=detail)
        draw.polygon([(w-2,3),(w,3),(w-2,4)], fill=beak, outline=(180,120,40))
        # ojo rojo poseído
        draw.ellipse((w-5,3,w-4,4), fill=eye_col, outline=(0,0,0))
        draw.point((w-5,3), fill=(255,255,255))
        # patas rosa
        draw.line((w//3, h-2, w//3-1+leg, h-1), fill=(200,120,120))
        draw.line((w*2//3, h-2, w*2//3+1-leg, h-1), fill=(200,120,120))
        # ala plegada
        draw.ellipse((w//2-2,5,w//2+3,8), fill=detail, outline=body)
        for x in range(3,w-3):
            if BAYER_4X4[(h-2)%4][x%4] <7: draw.point((x,h-2), fill=dk(body,12))
    # --- ShooterBuitre: zopilote negro posado encorvado ---
    elif sid == "ShooterBuitre":
        body=(38,38,44) if not is_hurt else (200,70,70)
        if is_die: body=(28,28,32)
        detail=(28,28,34); head=(190,70,64); beak=(160,160,170)
        # cuerpo encorvado
        draw.ellipse((2,4,w-3,h-2), fill=body, outline=detail)
        draw.ellipse((2,4,w-3,h-2), fill=body)
        draw.arc((2,4,w-3,h-2), 200, 330, fill=hi(body))
        # cabeza calva encorvada adelante
        draw.ellipse((w//2-2,1,w//2+2,4), fill=head, outline=(140,50,46))
        # pico ganchudo gris
        draw.polygon([(w//2+1,2),(w//2+4,2),(w//2+1,3)], fill=beak, outline=(120,120,130))
        draw.point((w//2,2), fill=(0,0,0))
        # ala plegada grande
        draw.ellipse((w//2-1,5,w-4,8), fill=detail, outline=body)
        # patas cortas
        draw.line((w//3, h-2, w//3, h-1), fill=leg_col if (leg_col:=(60,60,70)) else (60,60,70))
        draw.line((w*2//3, h-2, w*2//3, h-1), fill=(60,60,70))
        # buche?
        draw.point((w//2,6), fill=hi(body))
        for x in range(3,w-3):
            if BAYER_4X4[(h-2)%4][x%4] <7: draw.point((x,h-2), fill=dk(body,10))
    # --- ArcherQuetzal: quetzal arquero tiro arco ---
    elif sid == "ArcherQuetzal":
        body=(52,162,94) if not is_hurt else (220,90,90)
        if is_die: body=(40,122,70)
        detail=(36,122,70); bow=(128,88,48)
        # cuerpo como quetzal pero con arco
        draw.ellipse((w//2-3,4,w//2+3,h-2), fill=body, outline=detail)
        draw.ellipse((w//2-2,5,w//2+2,7), fill=(190,48,48))
        draw.ellipse((w//2-2,1,w//2+2,4), fill=body, outline=detail)
        draw.point((w//2+1,2), fill=(0,0,0))
        draw.polygon([(w//2+2,2),(w//2+4,2),(w//2+2,3)], fill=(255,228,60))
        # arco
        cx=w//2+4
        draw.arc((cx-3,3,cx+3,9), 270, 90, fill=bow)
        draw.line((cx,3,cx,9), fill=(200,180,140))
        # flecha: pluma
        off = 1 if paso else 0
        draw.line((cx,6,cx+3+off,6), fill=(120,80,30))
        draw.polygon([(cx+3+off,6),(cx+5+off,5),(cx+5+off,7)], fill=bow)
        draw.line((1,h-2,w-2,h-2), fill=(110,80,50))
        for x in range(w//2-3,w//2+4):
            if BAYER_4X4[(h-2)%4][x%4] <7: draw.point((x,h-2), fill=dk(body,14))
    # --- CasterHealer: curandero con orbe perseguidor ---
    elif sid == "CasterHealer":
        body=(78,118,84) if not is_hurt else (220,90,90)
        if is_die: body=(60,90,64)
        detail=(58,88,64); skin=(236,200,164); orb=(80,220,255)
        # túnica
        draw.rectangle((w//2-3,3,w//2+3,h-2), fill=body, outline=detail)
        draw.line((w//2,4,w//2,h-2), fill=detail)
        draw.arc((w//2-3,3,w//2+3,h-2), 200, 340, fill=hi(body))
        # cabeza capucha
        draw.ellipse((w//2-2,0,w//2+2,3), fill=body, outline=detail)
        draw.rectangle((w//2-1,1,w//2+1,3), fill=skin)
        draw.point((w//2-1,2), fill=(0,0,0)); draw.point((w//2+1,2), fill=(0,0,0))
        # báculo
        draw.line((w//2-4,3,w//2-4,9), fill=(120,80,40), width=1)
        # orbe flotante por frame con pulso
        r = 2 + (1 if paso else 0)
        ox, oy = w//2+4, 2
        draw.ellipse((ox-r, oy-r, ox+r, oy+r), fill=orb, outline=(40,140,180))
        draw.point((ox, oy), fill=(255,255,255))
        draw.point((ox+1, oy-1), fill=hi(orb))
        for x in range(w//2-3,w//2+4):
            if BAYER_4X4[(h-2)%4][x%4] <7: draw.point((x,h-2), fill=dk(body,12))
    # --- TerrainShaper: modelador terreno crea bloques ---
    elif sid == "TerrainShaper":
        body=(108,86,62) if not is_hurt else (220,90,90)
        if is_die: body=(82,66,48)
        detail=(82,66,48); skin=(236,200,164); block=(136,130,118); haz=(220,80,60)
        # cuerpo robusto
        draw.rectangle((w//2-3,3,w//2+3,h-2), fill=body, outline=detail)
        draw.arc((w//2-3,3,w//2+3,h-2), 200, 330, fill=hi(body))
        draw.line((w//2,4,w//2, h-3), fill=detail)
        # cabeza casco
        draw.rectangle((w//2-2,0,w//2+2,3), fill=(140,140,150), outline=detail)
        draw.rectangle((w//2-1,1,w//2+1,2), fill=skin)
        # martillo
        draw.line((w//2+3,5,w//2+5,9), fill=(120,80,40))
        draw.rectangle((w//2+3,5,w//2+6,7), fill=block, outline=detail)
        # bloque/hazard que crea por frame
        bx = w//2-5 if paso else w//2-6
        draw.rectangle((bx, h-4, bx+3, h-2), fill=haz, outline=(160,40,30))
        draw.point((bx+1, h-3), fill=hi(haz))
        for x in range(w//2-3,w//2+4):
            if BAYER_4X4[(h-2)%4][x%4] <7: draw.point((x,h-2), fill=dk(body,12))
    # --- Summoner: invocador que genera esbirros ---
    elif sid == "Summoner":
        body=(96,64,132) if not is_hurt else (220,90,90)
        if is_die: body=(72,48,100)
        detail=(72,48,100); skin=(236,200,164); glow=(180,80,255)
        # túnica púrpura
        draw.rectangle((w//2-3,3,w//2+3,h-1), fill=body, outline=detail)
        draw.line((w//2,4,w//2,h-1), fill=detail)
        draw.arc((w//2-3,3,w//2+3,h-1), 200, 340, fill=hi(body))
        # cabeza
        draw.ellipse((w//2-2,0,w//2+2,3), fill=skin, outline=(180,150,120))
        draw.point((w//2-1,1), fill=(0,0,0)); draw.point((w//2+1,1), fill=(0,0,0))
        # capucha
        draw.arc((w//2-3,0,w//2+3,4), 200, 340, fill=detail)
        # círculo invocación por frame pulsante
        r = 2 if paso else 1
        draw.ellipse((w//2-r, h-2-r, w//2+r, h-2+r), outline=glow, width=1)
        draw.point((w//2, h-2), fill=glow)
        # manos levantadas
        draw.line((w//2-3,5,w//2-5,3), fill=skin); draw.line((w//2+3,5,w//2+5,3), fill=skin)
        for x in range(w//2-3,w//2+4):
            if BAYER_4X4[(h-2)%4][x%4] <7: draw.point((x,h-2), fill=dk(body,12))
    # --- Cangrejo: cangrejo mina (usa dibujo mejorado, mantiene 20×14) ---
    elif sid == "Cangrejo":
        body=(150,86,52) if not is_hurt else (210,80,80)
        if is_die: body=(112,64,40)
        detail=(104,58,36); pinza=(120,66,40); eye_c=(30,22,14)
        # caparazón oval ancho
        draw.ellipse((3,3,w-4,h-5), fill=body, outline=detail)
        draw.arc((3,3,w-4,h-5), 210, 340, fill=hi(body))
        abierta = 2 if paso==0 else 0
        draw.polygon([(2, h//2-1),(2-abierta, h//2-4),(1, h//2+2)], fill=pinza, outline=detail)
        draw.polygon([(w-3, h//2-1),(w-1+abierta, h//2-4),(w-2, h//2+2)], fill=pinza, outline=detail)
        for i in range(3):
            lx, rx = 4+i*2, w-6-i*2
            ly = h//2+1 + (1 if paso else 0)
            draw.line((lx, ly, lx-1, h-2), fill=detail); draw.line((rx, ly, rx+1, h-2), fill=detail)
        for ex in (7, w-8):
            draw.line((ex,4,ex,6), fill=detail); draw.ellipse((ex-1,3,ex+1,5), fill=eye_c, outline=(0,0,0))
        for x in range(4,w-4):
            if BAYER_4X4[(h-3)%4][x%4] <7: draw.point((x,h-3), fill=dk(body,14))
    # --- Medusa: medusa pozo translúcida ---
    elif sid == "Medusa":
        body=(96,140,148) if not is_hurt else (200,120,140)
        if is_die: body=(72,106,112)
        hi_c=(140,176,182)
        # campana
        draw.pieslice((2,1,w-2,h-2), 180, 360, fill=(*body,190) if not is_die else body)
        draw.arc((2,1,w-2,h-2), 180, 360, fill=hi_c)
        # tentáculos ondulantes
        for i in range(4):
            tx=4+i*3
            doblez=1 + (1 if paso else -1) if i%2 else 1 - (1 if paso else -1)
            draw.line((tx, h//2, tx+doblez, h-1), fill=(*hi_c,160) if isinstance(hi_c, tuple) and len(hi_c)==3 else hi_c)
            # si alpha error, usar hi_c sin alpha
            try:
                draw.line((tx, h//2, tx+doblez, h-1), fill=hi_c)
            except Exception:
                pass
        for x in range(3,w-3):
            if BAYER_4X4[(h-2)%4][x%4] <7: draw.point((x,h-2), fill=dk(body,10))
    # --- PezAbismal: pez oscuro con luz pulsante ---
    elif sid == "PezAbismal":
        body=(14,18,26) if not is_hurt else (180,60,60)
        if is_die: body=(10,14,20)
        borde=(6,8,14); luz=(120,220,210)
        ond=1 if paso else -1
        draw.ellipse((2, h//2-4+ond, w-8, h//2+4-ond), fill=body, outline=borde)
        draw.polygon([(w-8,h//2-2),(w-1,h//2+ond),(w-8,h//2+2)], fill=borde)
        pulso=2 + (1 if paso else 0)
        cx,cy=4,h//2
        draw.ellipse((cx-pulso, cy-pulso, cx+pulso, cy+pulso), fill=luz, outline=(180,255,245))
        draw.point((cx,cy), fill=(255,255,255))
        for x in range(3,w-8):
            if BAYER_4X4[(h-3)%4][x%4] <7: draw.point((x,h-3), fill=dk(body,10))
    # --- AssassinSombra: sombra sigilosa cementerio ---
    elif sid == "AssassinSombra":
        body=(44,44,58) if not is_hurt else (200,80,80)
        if is_die: body=(34,34,44)
        detail=(28,28,38); blade=(180,180,190); eye_col=(255,60,60)
        # silueta encapuchada oscura
        draw.ellipse((w//2-3,0,w//2+3,5), fill=body, outline=detail) # capucha
        draw.rectangle((w//2-2,3,w//2+2,h-3), fill=body, outline=detail)
        draw.arc((w//2-2,3,w//2+2,h-3), 210, 330, fill=hi(body))
        # ojos rojos brillantes
        draw.point((w//2-1,2), fill=eye_col); draw.point((w//2+1,2), fill=eye_col)
        draw.point((w//2-1,2), fill=(255,255,255))
        # daga por frame: a veces visible
        if paso:
            draw.line((w//2+3,5,w//2+5,7), fill=blade, width=1)
            draw.polygon([(w//2+5,7),(w//2+6,8),(w//2+4,8)], fill=blade, outline=detail)
            draw.point((w//2+5,6), fill=(255,255,255))
        else:
            draw.line((w//2-3,5,w//2-4,7), fill=blade)
        # sigilo: sombra abajo dither
        for x in range(w//2-3,w//2+4):
            if BAYER_4X4[(h-2)%4][x%4] <6: draw.point((x,h-2), fill=dk(body,14))
    # --- Climber: trepador lianas tirolesa ---
    elif sid == "Climber":
        body=(90,72,52) if not is_hurt else (210,90,90)
        if is_die: body=(68,54,40)
        detail=(68,54,40); skin=(236,200,164); rope=(200,180,140); metal=(180,180,190)
        # cuerpo cazadora
        draw.rectangle((w//2-3,3,w//2+3,h-4), fill=body, outline=detail)
        draw.rectangle((w//2-2,4,w//2+2,7), fill=hi(body))
        # cabeza + casco
        draw.ellipse((w//2-2,0,w//2+2,3), fill=skin, outline=detail)
        draw.rectangle((w//2-2,0,w//2+2,1), fill=(250,220,80), outline=detail)
        draw.point((w//2-1,1), fill=(0,0,0)); draw.point((w//2+1,1), fill=(0,0,0))
        # arnés
        draw.line((w//2-3,5,w//2+3,5), fill=detail); draw.line((w//2,5,w//2,8), fill=detail)
        # cuerda vertical
        draw.line((w//2,0,w//2,h-1), fill=rope)
        draw.point((w//2,2), fill=metal)
        # mosquetón por frame
        off = 1 if paso else -1
        draw.ellipse((w//2+2+off,6,w//2+4+off,8), outline=metal)
        # piernas
        draw.line((w//2-2,h-4,w//2-3+leg,h-1), fill=detail); draw.line((w//2+2,h-4,w//2+3-leg,h-1), fill=detail)
        for x in range(w//2-3,w//2+4):
            if BAYER_4X4[(h-2)%4][x%4] <7: draw.point((x,h-2), fill=dk(body,10))
    # --- Shielded ya tratado arriba ---
    # --- Swimmer ya tratado ---
    # --- FlyingBomber ya tratado ---
    # --- BruteGolemHielo ya tratado ---
    # --- ChargerWolf ya tratado ---
    else:
        # Fallback genérico pero con variación (nunca debe usarse si todas las 35 están cubiertas)
        body_col = (120,80,40) if not is_hurt else (190,60,50)
        if is_die: body_col=(70,40,30)
        detail_col=(80,50,20)
        draw.ellipse((2,2,w-3,h-3), fill=body_col, outline=detail_col)
        draw.arc((2,2,w-3,h-3), 200, 340, fill=hi(body_col))
        draw.rectangle((w//4, h//4, w//4+2, h//4+2), fill=(255,255,255))
        draw.rectangle((w*3//4-2, h//4, w*3//4, h//4+2), fill=(255,255,255))
        draw.point((w//4+1, h//4+1), fill=(0,0,0)); draw.point((w*3//4-1, h//4+1), fill=(0,0,0))
        off = 1 if f%2 else -1
        draw.line((w//4, h-3, w//4-2+off, h-1), fill=detail_col)
        draw.line((w*3//4, h-3, w*3//4+2-off, h-1), fill=detail_col)
        for x in range(2,w-2):
            if BAYER_4X4[(h-3)%4][x%4] <8:
                draw.point((x,h-3), fill=dk(body_col))

def _gen_enemy_sheet_especie(sid, path, w, h, frames, mode="walk"):
    """Genera hoja para especie sid con silueta única. Garantiza 6/4f variación real."""
    imgs=[]
    for f in range(frames):
        img=Image.new("RGBA", (w,h),(0,0,0,0))
        draw=ImageDraw.Draw(img)
        _dibujar_especie(draw, sid, w, h, f, frames, mode)
        # Variación real garantizada: respiración/bob 1px en frames impares para que ningún
        # walk de 4f quede idéntico si la especie es estática (shooter). Los walkers/flyers ya
        # tienen leg/wing swing, este bob se suma como respiración sutil sin romper anclaje:
        # se desplaza el contenido 1px arriba en frames impares antes del outline, manteniendo
        # pies anclados visualmente porque el outline y la sombra se recalculan después.
        if f % 2 == 1 and frames == 4:
            bob = Image.new("RGBA", (w,h),(0,0,0,0))
            bob.paste(img, (0, -1))
            img = bob
        # outline + sombra dithered Bayer PSX HQ
        _psx_outline_y_sombra(img)
        imgs.append(img)
    _save_sheet(path, imgs, w, h)

ZONE1_PAL = {"body": (120, 80, 40), "detail": (80, 50, 20), "fly": (60, 60, 120), "shoot": (40, 120, 60)}
ZONE2_PAL = {"body": (60, 120, 60), "detail": (30, 80, 30), "fly": (100, 60, 100), "shoot": (80, 100, 40)}
ZONE3_PAL = {"body": (80, 60, 120), "detail": (50, 30, 80), "fly": (120, 100, 60), "shoot": (100, 60, 60)}

ENEMY_ZONES = {
    "zone1": ZONE1_PAL,
    "zone2": ZONE2_PAL,
    "zone3": ZONE3_PAL,
}

ENEMY_TYPES = {
    "walker": {"w": 16, "h": 12, "frames": 6, "extras": ["hurt", "die"]},
    "flying": {"w": 16, "h": 12, "frames": 4, "extras": ["hurt", "die"]},
    "shooter": {"w": 12, "h": 12, "frames": 4, "extras": ["aim", "fire", "hurt", "die"]},
}

def _gen_all_enemies():
    for zname, zp in ENEMY_ZONES.items():
        base = A / "sprites" / "enemies" / zname
        print(f"  Enemies {zname}...")
        _gen_enemy_sheet(base / f"enemy_{zname}_walk.png", 16, 12, 6, zp["body"], zp["detail"])
        _gen_enemy_sheet(base / f"enemy_{zname}_hurt.png", 16, 12, 3, (180,50,50), (100,20,20))
        _gen_enemy_sheet(base / f"enemy_{zname}_die.png", 16, 12, 5, (80,30,30), (40,10,10))
        _gen_enemy_sheet(base / f"enemy_fly_{zname}.png", 14, 10, 4, zp["fly"], zp["detail"])
        _gen_enemy_sheet(base / f"enemy_shoot_{zname}.png", 12, 12, 4, zp["shoot"], zp["detail"])
    # ── Por especie: 35 siluetas únicas con variación real 6/4f ──
    # Asegurar que PROJECT_ROOT está en sys.path para importar bestiary (cuando se ejecuta como script)
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))
    try:
        from src.framework.entities.bestiary_registry import SPECIES
        print(f"    Cargadas {len(SPECIES)} especies del bestiario")
    except Exception as e:
        print(f"    WARN: no se pudo cargar bestiary_registry: {e}")
        SPECIES={}
    # Tamaños por clase base (mantener 16×12/14×10/12×12 y especiales sin nuevos biomas)
    base_size={
        "EnemyWalker": (16,12,6), "EnemyFlying": (14,10,4), "EnemyShooter": (12,12,4),
        "EnemyShielded": (16,14,4), "EnemySwimmer": (16,12,4), "EnemyCangrejo": (20,14,4),
        "EnemyMedusa": (16,14,4), "EnemyPezAbismal": (28,20,4), "EnemyClimber": (16,16,4),
        "EnemyFlyingBomber": (20,14,4), "EnemyTerrainShaper": (16,14,4), "EnemySummoner": (16,16,4),
        "EnemyArcher": (12,14,4), "EnemyBrute": (24,18,4), "EnemyCharger": (14,12,6),
        "EnemyCaster": (14,14,4), "EnemyAssassin": (12,12,4),
    }
    for sid, spec in SPECIES.items():
        w,h,frames = base_size.get(spec.base, (16,12,6))
        zone_dir = A / "sprites" / "enemies" / f"zone{spec.zone}"
        species_dir = A / "sprites" / "enemies" / "species"
        zone_dir.mkdir(parents=True, exist_ok=True)
        species_dir.mkdir(parents=True, exist_ok=True)
        # walk
        _gen_enemy_sheet_especie(sid, zone_dir / f"enemy_{sid.lower()}_walk.png", w, h, frames, "walk")
        _gen_enemy_sheet_especie(sid, species_dir / f"{sid}_walk.png", w, h, frames, "walk")
        # hurt/die (3/5 frames)
        _gen_enemy_sheet_especie(sid, zone_dir / f"enemy_{sid.lower()}_hurt.png", w, h, 3, "hurt")
        _gen_enemy_sheet_especie(sid, zone_dir / f"enemy_{sid.lower()}_die.png", w, h, 5, "die")
        # compatibilidad species hurt/die si algún cargador los busca
        _gen_enemy_sheet_especie(sid, species_dir / f"{sid}_hurt.png", w, h, 3, "hurt")
        _gen_enemy_sheet_especie(sid, species_dir / f"{sid}_die.png", w, h, 5, "die")
        print(f"    Especie {sid} zone{spec.zone} {spec.base} {w}x{h} {frames}f")




def _gen_pez_abismal_sheet(path, w=28, h=20, frames=4):
    """AUD-519 — el pez abismal de 4.1b: no un bicho con patas como
    `_gen_enemy_sheet` (esa silueta es de tierra firme, no de fosa), sino
    una forma alargada, casi sin rasgos, con un único punto que pulsa —el
    señuelo bioluminiscente— para que se lea como amenaza abisal y no
    como un pez de acuario. La regla de oro de 4-1 (cero enemigos, la
    atmósfera es el desafío) se traduce aquí en «una sola criatura, y que
    apenas se distinga»: el contorno importa menos que el punto de luz
    que se acerca en la oscuridad.

    AUD-529 — 28×20 por fotograma, el doble de lo que tenía (14×10).
    Pedido explícito tras jugarlo: «debe ser mucho más grande y
    amenazador». Ya no es el tamaño que `EnemyFlying._load_zone_sprites`
    pide para el resto de voladores — `EnemyPezAbismal._load_extra_sprites`
    lo sobreescribe a propósito, junto con `_sprite_fw/_sprite_fh` y el
    `rect` de colisión, así que el recorte de la hoja sigue cuadrando.
    """
    cuerpo = (14, 18, 26)
    borde = (6, 8, 14)
    luz = (120, 220, 210)
    imgs = []
    for f in range(frames):
        img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        # El cuerpo ondula de fotograma a fotograma — un vaivén sinusoidal
        # simple, no una animación de nado anatómicamente precisa.
        ondulacion = int(2 * math.sin(f / max(frames - 1, 1) * math.pi * 2))
        draw.ellipse((2, h // 2 - 6 + ondulacion, w - 8, h // 2 + 6 - ondulacion),
                     fill=cuerpo, outline=borde)
        # Cola, apenas un triángulo que se dobla con la ondulación.
        draw.polygon([
            (w - 8, h // 2 - 4),
            (w - 1, h // 2 + ondulacion * 2),
            (w - 8, h // 2 + 4),
        ], fill=borde)
        # El señuelo: pulsa de tamaño, no de posición — es lo primero que
        # se ve venir en la oscuridad, antes que el cuerpo.
        pulso = 2 + (f % 2) * 2
        cx, cy = 4, h // 2
        draw.ellipse((cx - pulso, cy - pulso, cx + pulso, cy + pulso), fill=luz)
        _psx_outline_y_sombra(img)
        imgs.append(img)
    _save_sheet(path, imgs, w, h)


def _gen_cangrejo_sheet(path, w=20, h=14, frames=4):
    """AUD-575 — el cangrejo de la mina inundada. La fauna del nivel es
    presencia, nunca combate (regla del 4-1b: nada daña), así que el
    sprite tiene que leerse como *habitante* de la mina: un caparazón
    café oxidado, pinzas que abren y cierran al andar, ojos en tallos.
    Vista frontal de cangrejo caminando de lado — como se ve al
    patrullar el andén del patio de carga (S3) de cara al jugador."""
    caparazon = (150, 86, 52)
    caparazon_oscuro = (104, 58, 36)
    pinza = (120, 66, 40)
    ojo = (30, 22, 14)
    imgs = []
    for f in range(frames):
        img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        paso = f % 2
        # Caparazón ovalado, más ancho que alto.
        draw.ellipse((3, 3, w - 3, h - 5), fill=caparazon, outline=caparazon_oscuro)
        # Pinzas: abren y cierran con el paso (el cangrejo de frente
        # amenaza con las dos a la vez).
        abierta = 2 if paso == 0 else 0
        draw.polygon([(2, h // 2 - 1), (2 - abierta, h // 2 - 4),
                      (1, h // 2 + 3)], fill=pinza)
        draw.polygon([(w - 3, h // 2 - 1), (w - 1 + abierta, h // 2 - 4),
                      (w - 2, h // 2 + 3)], fill=pinza)
        # Patas: cuatro por lado, alternan.
        for i in range(4):
            lx, rx = 2 + i * 1, w - 4 - i * 1
            ly = h // 2 + 2 + (1 if paso else 0)
            draw.line((lx, ly, lx - 1, h - 2), fill=caparazon_oscuro)
            draw.line((rx, ly, rx + 1, h - 2), fill=caparazon_oscuro)
        # Ojos en tallos: miran fijos al jugador.
        for ex in (7, w - 8):
            draw.line((ex, 4, ex, 6), fill=caparazon_oscuro)
            draw.ellipse((ex - 1, 3, ex + 1, 5), fill=ojo)
        _psx_outline_y_sombra(img)
        imgs.append(img)
    _save_sheet(path, imgs, w, h)


def _gen_medusa_sheet(path, w=16, h=14, frames=4):
    """AUD-575 — la medusa del pozo del drenaje (S4/S5). Presencia como
    todo el ecosistema: deriva en la columna, no persigue. Se distingue
    del pez abismal a propósito: el pez es una silueta oscura con un
    punto de luz que pulsa (amenaza), la medusa es una campana
    translúcida pálida sin ningún brillo propio (plancton). Los
    tentáculos ondulan de fotograma a fotograma."""
    campana = (96, 140, 148)
    campana_clara = (140, 176, 182)
    imgs = []
    for f in range(frames):
        img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        # Campana: medio óvalo, translúcida (alpha 190).
        fill = (*campana, 190)
        draw.pieslice((2, 1, w - 2, h - 2), 180, 360, fill=fill)
        draw.arc((2, 1, w - 2, h - 2), 180, 360, fill=campana_clara)
        # Tentáculos: cuatro, ondulan con el fotograma.
        for i in range(4):
            tx = 4 + i * 3
            doblez = 1 + (f % 2) * 2 if i % 2 else 1 - (f % 2) * 2
            draw.line((tx, h // 2, tx + doblez, h - 1),
                      fill=(*campana_clara, 160), width=1)
        _psx_outline_y_sombra(img)
        imgs.append(img)
    _save_sheet(path, imgs, w, h)

# ════════════════════════════════════════
# SECTION 3: BOSS SPRITES
# ════════════════════════════════════════

def _draw_venado_deer(draw, w, h, pal, sheet, frame, total):
    """Draw a 48x48 deer/venado facing right using PIL primitives."""
    ivory, dk_green, md_green, brown, tan, black, _red_brown = pal

    import math
    t = frame / max(total - 1, 1)

    # Pose parameters per sheet
    leg_cycle = 0.0
    head_lower = 0
    front_up = 0
    collapse = 0

    if sheet == "drift":
        leg_cycle = math.sin(t * math.pi * 2)
    elif sheet == "stomp":
        front_up = 1 if frame < total // 2 else 0
    elif sheet == "charge":
        head_lower = 3
    elif sheet == "frenzy_drift":
        leg_cycle = math.sin(t * math.pi * 4)
    elif sheet == "vine":
        leg_cycle = math.sin(t * math.pi * 3)
    elif sheet == "hurt":
        head_lower = 2
    elif sheet == "death":
        collapse = t * 16

    def _clamp(y): return max(0, min(h - 1, y))
    cy = int(collapse)

    # Tail
    draw.ellipse((4, _clamp(18 + cy), 8, _clamp(22 + cy)), fill=ivory)

    # Body
    body_y = 16 + cy
    draw.ellipse((10, _clamp(body_y), 38, _clamp(36 + cy)), fill=md_green, outline=dk_green)
    draw.ellipse((14, _clamp(24 + cy), 34, _clamp(34 + cy)), fill=tan)

    # Neck
    ny = 10 + cy + head_lower
    draw.polygon([(34, _clamp(18 + cy)), (38, _clamp(ny)), (42, _clamp(12 + cy)), (38, _clamp(22 + cy))], fill=md_green, outline=dk_green)

    # Head
    draw.ellipse((36, _clamp(6 + cy + head_lower), 46, _clamp(16 + cy + head_lower)), fill=md_green, outline=dk_green)
    draw.ellipse((42, _clamp(10 + cy + head_lower), 48, _clamp(14 + cy + head_lower)), fill=tan)
    draw.point((39, _clamp(10 + cy + head_lower)), fill=black)
    draw.point((40, _clamp(10 + cy + head_lower)), fill=black)
    draw.polygon([(36, _clamp(8 + cy + head_lower)), (34, _clamp(4 + cy + head_lower)), (38, _clamp(6 + cy + head_lower))], fill=md_green, outline=dk_green)

    # Antlers
    ay = cy + head_lower
    for (x1,y1,x2,y2) in [(40, 6 + ay, 38, 0), (38, 3 + ay, 42, 0), (38, 3 + ay, 34, 0),
                           (40, 4 + ay, 42, 2), (38, 5 + ay, 34, 3)]:
        draw.line((x1, _clamp(y1), x2, _clamp(y2)), fill=ivory)

    # Front legs
    fl_off = int(leg_cycle * 2)
    if front_up:
        draw.rectangle((14, _clamp(body_y - 4), 18, _clamp(body_y + 4)), fill=dk_green)
        draw.rectangle((20 + fl_off, _clamp(body_y - 2), 24 + fl_off, _clamp(body_y + 6)), fill=dk_green)
    else:
        draw.rectangle((12, _clamp(34 + cy), 16, _clamp(min(h, 46 + cy))), fill=dk_green)
        draw.rectangle((18 + fl_off, _clamp(34 + cy), 22 + fl_off, _clamp(min(h, 46 + cy))), fill=dk_green)

    # Back legs
    bl_off = int(-leg_cycle * 2)
    draw.rectangle((26 + bl_off, _clamp(34 + cy), 30 + bl_off, _clamp(min(h, 46 + cy))), fill=dk_green)
    draw.rectangle((32, _clamp(34 + cy), 36, _clamp(min(h, 46 + cy))), fill=dk_green)

    # Hooves
    if not front_up:
        draw.rectangle((12, _clamp(44 + cy), 16, h - 1), fill=brown)
        draw.rectangle((18 + fl_off, _clamp(44 + cy), 22 + fl_off, h - 1), fill=brown)
    draw.rectangle((26 + bl_off, _clamp(44 + cy), 30 + bl_off, h - 1), fill=brown)
    draw.rectangle((32, _clamp(44 + cy), 36, h - 1), fill=brown)


def _draw_boss_generic(draw, w, h, pal, bname, sheet, frame, total):
    """Fallback: draw a colored boss creature for non-venado bosses."""
    cols = pal
    c = cols[frame % len(cols)]
    draw.rectangle((2, 2, w - 3, h - 3), fill=c, outline=(255, 255, 255))
    draw.ellipse((w // 4, h // 4, w * 3 // 4, h * 3 // 4), fill=cols[(frame + 1) % len(cols)])


BOSS_DEFS = {
    "venado": {
        "fw": 48, "fh": 48,
        "sheets": {"drift": 6, "stomp": 8, "charge": 6, "frenzy_drift": 6, "vine": 10, "hurt": 4, "death": 12},
        "pal": [(200,200,180), (45,74,30), (74,120,50), (107,68,35), (200,184,150), (10,10,10), (140,110,60)]
    },
    "rey": {
        "fw": 40, "fh": 56,
        "sheets": {"walk": 8, "spit": 6, "split": 8, "merge": 6, "rampage": 8, "hurt": 4, "death": 14},
        "pal": [(200,162,100), (74,50,24), (140,100,50), (125,125,125), (60,60,60), (50,160,80), (80,200,120)]
    },
    "gavilan": {
        "fw": 56, "fh": 40,
        "sheets": {"glide": 8, "dive": 6, "hover": 4, "storm": 8, "masked": 6, "hurt": 4, "death": 16},
        "pal": [(140,90,40), (200,140,60), (200,200,180), (212,160,23), (140,104,0), (30,107,107), (212,90,0)]
    },
    "paburu": {
        "fw": 64, "fh": 64,
        "sheets": {"stone": 4, "stone_slam": 8, "mask": 6, "gold": 6, "black": 6, "spirit": 8, "hurt": 4, "transcend": 20},
        "pal": [(60,100,50), (90,140,80), (140,180,150), (80,200,120), (40,164,80), (10,100,40), (200,215,200)]
    }
}

def _gen_all_bosses():
    for bname, bd in BOSS_DEFS.items():
        bdir = A / "sprites" / "bosses"
        print(f"  Boss {bname}...")
        for sname, frames in bd["sheets"].items():
            imgs = []
            for f in range(frames):
                img = Image.new("RGBA", (bd["fw"], bd["fh"]), (0,0,0,0))
                draw = ImageDraw.Draw(img)
                if bname == "venado":
                    _draw_venado_deer(draw, bd["fw"], bd["fh"], bd["pal"], sname, f, frames)
                else:
                    _draw_boss_generic(draw, bd["fw"], bd["fh"], bd["pal"], bname, sname, f, frames)
                _psx_outline_y_sombra(img)
                imgs.append(img)
            fname = f"boss_{bname}_{sname}.png"
            _save_sheet(bdir / fname, imgs, bd["fw"], bd["fh"])

# ════════════════════════════════════════
# SECTION 4: TILESETS (all 10 zones)
# ════════════════════════════════════════

# ── Tileset pixel art palette for stage0 (gothic castle/cave) ──
TILESET_PAL = {
    0: (30, 28, 40), 1: (55, 50, 65), 2: (75, 70, 85), 3: (95, 90, 105),
    4: (45, 42, 52), 5: (65, 75, 55), 6: (115, 110, 125), 7: (25, 95, 75),
    8: (45, 135, 105), 9: (155, 135, 95),
}

# 16×16 gothic castle/cave tiles (8 types)
TILE_FLOOR = """
..1221..1221..
.233332.233332.
13333331333331
13333331333331
.233332.233332.
..1221..1221..
....22....22...
...233...233...
..13331.13331..
.1333331333331.
133333313333331
133333313333331
.1333331333331.
..13331.13331..
...1221.1221...
....22....22...
"""

TILE_WALL = """
1111111111111111
1000000000000001
1011101110111011
1000000000000001
1011101110111011
1000000000000001
1011101110111011
1000000000000001
1011101110111011
1000000000000001
1011101110111011
1000000000000001
1011101110111011
1000000000000001
1111111111111111
1111111111111111
"""

TILE_DECO_FLOOR = """
..1221..1221..
.233332.233332.
13333331333331
13333931333931
.233332.233332.
..1221..1221..
....22....22...
...233...233...
..13331.13331..
.1333331333331.
133333313333331
13333931333931
.1333331333331.
..13331.13331..
...1221.1221...
....22....22...
"""

TILE_PLATFORM = """
5555555555555555
5555555555555555
1111111111111111
1000000000000001
1011101110111011
1000000000000001
1011101110111011
1000000000000001
1011101110111011
1000000000000001
1011101110111011
1000000000000001
1011101110111011
1000000000000001
1111111111111111
1111111111111111
"""

TILE_WATER = """
7777777777777777
8787878787878787
7777777777777777
7878787878787878
7777777777777777
8787878787878787
7777777777777777
7878787878787878
7777777777777777
8787878787878787
7777777777777777
7878787878787878
7777777777777777
8787878787878787
7777777777777777
7878787878787878
"""

TILE_BRIDGE = """
..11..11..11..
.1111.1111.1111.
1111111111111111
.1221.1221.1221.
..11..11..11...
.1111.1111.1111.
1111111111111111
.1221.1221.1221.
..11..11..11...
.1111.1111.1111.
1111111111111111
.1221.1221.1221.
..11..11..11...
.1111.1111.1111.
1111111111111111
.1221.1221.1221.
"""

TILE_SPIKE = """
.......44.......
......4644......
.....466644.....
....46666644....
...4666666644...
..466666666644..
.46666666666644.
4666666666666644
4666666666666644
.46666666666644.
..466666666644..
...4666666644...
....46666644....
.....466644.....
......4644......
.......44.......
"""

TILE_EMPTY = """
................
................
................
................
................
................
................
................
................
................
................
................
................
................
................
................
"""

_GOTHIC_TILES = [TILE_FLOOR, TILE_WALL, TILE_DECO_FLOOR, TILE_PLATFORM, TILE_WATER, TILE_BRIDGE, TILE_SPIKE, TILE_EMPTY]

TILESET_THEMES = {
    "tileset_stage0": "gothic",
    "tileset_jungle_stone": {"floor": (60,100,50), "wall": (80,120,70), "deco": (40,80,30)},
    "tileset_cafeteria": {"floor": (140,120,100), "wall": (160,140,120), "deco": (180,160,140)},
    "tileset_aulas": {"floor": (160,140,100), "wall": (180,160,120), "deco": (140,120,80)},
    "tileset_planicie": {"floor": (120,140,80), "wall": (140,160,100), "deco": (100,120,60)},
    "tileset_datacenter_ext": {"floor": (100,100,110), "wall": (120,120,130), "deco": (80,80,90)},
    "tileset_datacenter": {"floor": (90,90,110), "wall": (110,110,130), "deco": (70,70,90)},
    "tileset_heredia_stone": {"floor": (100,90,80), "wall": (120,110,100), "deco": (80,70,60)},
    "tileset_heredia_interior": {"floor": (130,110,90), "wall": (150,130,110), "deco": (110,90,70)},
    "tileset_cemetery": {"floor": (50,50,70), "wall": (70,70,90), "deco": (40,40,60)},
    "tileset_stage4_1": {"floor": (90,80,70), "wall": (58,56,70), "deco": (70,60,50)},
    # AUD-531 — reemplaza la paleta abisal azul de AUD-519. Pedido tras
    # jugarlo: «el nivel no puede ser totalmente negro. El negro debe
    # representar únicamente la ausencia de luz; la paleta principal debe
    # basarse en tonos café para transmitir la sensación de estar dentro
    # de una cueva». Roca húmeda, no fosa azul — el negro sigue reservado
    # para lo que de verdad no recibe luz (`ambient_light=0.28` en el
    # TMX, sin cambios).
    "tileset_stage4_1b": {"floor": (58,42,28), "wall": (34,24,16), "deco": (78,56,36)},
    # AUD-520 — 4.1c, la variante aérea: nubes y niebla pálidas, sin
    # verde ni piedra — las plataformas sólidas tienen que leerse contra
    # un cielo, no contra tierra.
    "tileset_stage4_1c": {"floor": (150,150,170), "wall": (110,110,135), "deco": (190,190,205)},
}

def _paleta_32_para_tema(theme):
    """Expande un tema de 3 colores a 64-96 colores PSX 32-bit alta calidad con dithering Bayer.

    PSX 2D Tributo Vintage Moderno: paleta extendida real 64-128 por tileset, 1024 global
    (ver docs/20_ASSET_BIBLE.md §2.1). Cada base genera variaciones con deltas amplios
    (-60..+60, no sólo ±40) y mezclas Bayer para sombras sin banding. 32 acentos en vez
    de 17 permiten detalle material (veteado madera, piedra oclusión, metal reflejo).
    Mantiene identidad de zona (verde Universidad, azul Datacenter, ocre Heredia,
    dorado Cementerio) pero con riqueza cromática moderna 32-bit."""
    base = [theme["floor"], theme["wall"], theme["deco"]]
    pal: list[tuple[int, int, int]] = []
    # Deltas amplios PSX: -60 a +60 con pasos sutiles para 32-bit sin banding
    deltas = (-60, -45, -30, -18, -8, 0, 12, 24, 38, 52, 60)
    for c in base:
        for delta in deltas:
            pal.append(tuple(max(0, min(255, ch + delta)) for ch in c))
    # Mezclas Bayer entre bases: dithering ordenado para sombras intermedias
    # Peso Bayer 0..15 -> ratio para interpolación floor/wall/deco
    for w in (4, 8, 12):
        for a, b in [(base[0], base[1]), (base[1], base[2]), (base[0], base[2])]:
            ratio = w / 16.0
            mixed = tuple(int(a[i] * (1 - ratio) + b[i] * ratio) for i in range(3))
            pal.append(mixed)
            pal.append(tuple(max(0, ch - 22) for ch in mixed))  # AO variante oscura
            pal.append(tuple(min(255, ch + 18) for ch in mixed))  # highlight
    # 32 acentos PSX extendidos: madera, piedra, metal, vegetación, acentos cálidos/fríos
    acentos = [
        (255, 220, 120), (90, 180, 120), (70, 110, 160),
        (180, 80, 60), (200, 200, 210), (30, 30, 40),
        (120, 150, 100), (160, 120, 90), (100, 80, 120),
        (50, 70, 90), (200, 180, 140), (80, 100, 80),
        (140, 140, 160), (60, 50, 40), (220, 220, 220),
        (40, 60, 50), (180, 160, 110), (220, 180, 80),
        (60, 140, 180), (160, 60, 80), (100, 180, 100),
        (180, 100, 140), (120, 80, 60), (80, 120, 140),
        (140, 80, 80), (80, 140, 120), (120, 120, 180),
        (200, 140, 60), (60, 200, 140), (140, 200, 60),
        (80, 80, 100), (180, 180, 200),
    ]
    pal.extend(acentos)
    # Dedup preservando orden, cap 96 (rango 64-96 para PSX extendida)
    seen: set[tuple[int, int, int]] = set()
    out: list[tuple[int, int, int]] = []
    for c in pal:
        if c not in seen:
            seen.add(c)
            out.append(c)
    # Relleno determinista si faltan para llegar a 64 mínimo
    rng = random.Random(hash(str(sorted(theme.items()))) % (2**31))
    intentos = 0
    while len(out) < 64 and intentos < 200:
        c = rng.choice(base)
        delta = rng.randint(-58, 58)
        variant = tuple(max(0, min(255, ch + delta + rng.randint(-6, 6))) for ch in c)
        if variant not in seen:
            seen.add(variant)
            out.append(variant)
        intentos += 1
    return out[:96]


def _gen_gothic_tileset(path, ts=16, cols=16, rows=16):
    """Tileset gotico PSX 32-bit alta calidad 1024×1024 (64×64 baldosas).

    PSX Tributo Vintage Moderno: 64-128 colores, Bayer 4×4 para sombras,
    veteado y oclusión. Mantiene grilla 16×16 y NEAREST."""
    _ensure(path)
    if "stage0" in str(path) and cols == 16 and rows == 16:
        cols, rows = 64, 64
        img = Image.new("RGBA", (ts*cols, ts*rows), (0,0,0,0))
        draw = ImageDraw.Draw(img)
        for gy in range(rows):
            for gx in range(cols):
                ox, oy = gx * ts, gy * ts
                tile_idx = (gy * cols + gx) % len(_GOTHIC_TILES)
                tile_data = _GOTHIC_TILES[tile_idx]
                _pixel_art(draw, ox, oy, tile_data, TILESET_PAL)
        # Bayer dithered noise PSX: amplía a ±16 con patrón para 64-100 colores
        rng = random.Random(42)
        for _ in range(1200):
            x = rng.randint(0, ts*cols-1)
            y = rng.randint(0, ts*rows-1)
            v = rng.randint(-16, 16)
            if BAYER_4X4[y%4][x%4] < 6:
                v = int(v*0.5)
            r,g,b,a = img.getpixel((x,y))
            if a:
                img.putpixel((x,y), (max(0,min(255,r+v)), max(0,min(255,g+v)), max(0,min(255,b+v)), a))
        img.save(path)
        _gen_normal_map_para_tileset(path)
        return
    _ensure(path)
    img = Image.new("RGBA", (ts*cols, ts*rows), (0,0,0,0))
    for gy in range(rows):
        for gx in range(cols):
            ox, oy = gx * ts, gy * ts
            tile_idx = (gy * cols + gx) % len(_GOTHIC_TILES)
            tile_data = _GOTHIC_TILES[tile_idx]
            draw = ImageDraw.Draw(img)
            _pixel_art(draw, ox, oy, tile_data, TILESET_PAL)
            if (gx + gy) % 3 == 0:
                outline = tuple(min(255,c+18) for c in TILESET_PAL[1])
                draw.rectangle((ox, oy, ox+ts-1, oy+ts-1), outline=outline, width=1)
            # AO dithered sutil PSX
            if (gx+gy) % 7 == 0:
                b = BAYER_4X4[oy%4][ox%4]
                if b < 7:
                    draw.point((ox+1, oy+1), fill=tuple(max(0,c-14) for c in TILESET_PAL[0]))
    rng = random.Random(43)
    for _ in range(180):
        x = rng.randint(0, ts*cols-1)
        y = rng.randint(0, ts*rows-1)
        r,g,b,a = img.getpixel((x,y))
        if a and BAYER_4X4[y%4][x%4] < 10:
            v = rng.randint(-12,12)
            img.putpixel((x,y), (max(0,min(255,r+v)), max(0,min(255,g+v)), max(0,min(255,b+v)), a))
    img.save(path)
    _gen_normal_map_para_tileset(path)

def _dibujar_tile_procedural(draw, ox, oy, ts, ttype, theme):
    """Una baldosa del tileset procedural PSX 32-bit alta calidad — 16 variantes autotiling.

    PSX Tributo Vintage Moderno: paleta extendida 64-128 por tileset, 1024 global,
    dithering Bayer 4×4 para sombras sin banding, outline 1px, detalle material real:
    madera con vetas diagonales dithered, piedra con oclusión en esquinas (AO),
    metal con reflejo 1px. Mantiene grilla 16×16 y compatibilidad TMX 8×8
    (``if gx<8 and gy<8: %8 else %16`` en el caller) con ``NEAREST``.
    """
    floor = theme["floor"]
    wall = theme["wall"]
    deco = theme["deco"]
    # Variaciones extendidas 32-bit con deltas amplios
    floor_claro = tuple(min(255, c + 30) for c in floor)
    floor_medio = tuple(min(255, c + 14) for c in floor)
    floor_oscuro = tuple(max(0, c - 30) for c in floor)
    floor_sombra = tuple(max(0, c - 48) for c in floor)
    wall_claro = tuple(min(255, c + 28) for c in wall)
    wall_medio = tuple(min(255, c + 12) for c in wall)  # usado en highlight interior madera
    _ = wall_medio
    wall_oscuro = tuple(max(0, c - 28) for c in wall)
    wall_sombra = tuple(max(0, c - 45) for c in wall)
    deco_claro = tuple(min(255, c + 24) for c in deco)
    deco_oscuro = tuple(max(0, c - 24) for c in deco)
    metal_brillo = tuple(min(255, c + 55) for c in wall)
    madera_veta = tuple(max(0, c - 18) for c in deco)
    madera_base = deco  # madera toma tono deco cálido

    def _dither_rect(x0, y0, x1, y1, col_a, col_b, umbral=8):
        """Rellena rect con Bayer dithered entre col_a y col_b (PSX sombras)."""
        for yy in range(y0, y1 + 1):
            for xx in range(x0, x1 + 1):
                b = BAYER_4X4[yy % 4][xx % 4]
                draw.point((xx, yy), fill=col_a if b < umbral else col_b)

    def _ao_esquina(x0, y0, size=3):
        """Oclusión ambiental dithered en esquina 3×3 con Bayer."""
        for dy in range(size):
            for dx in range(size):
                dist = dx + dy
                col = floor_sombra if dist < 2 else floor_oscuro if dist < 4 else floor
                b = BAYER_4X4[(y0 + dy) % 4][(x0 + dx) % 4]
                # Dithering: mezcla según distancia y Bayer
                use_sombra = b < (10 - dist * 2)
                c = col if use_sombra else floor_oscuro if dist < 3 else floor
                # Evita sobreescribir fuera del tile
                if ox <= x0 + dx < ox + ts and oy <= y0 + dy < oy + ts:
                    draw.point((x0 + dx, y0 + dy), fill=c)

    if ttype == 0:  # SUELO PIEDRA — oclusión + dither
        draw.rectangle((ox, oy, ox+ts-1, oy+ts-1), fill=floor)
        # Centro elevado con borde biselado claro
        draw.rectangle((ox+3, oy+3, ox+ts-4, oy+ts-4), fill=floor_medio)
        draw.rectangle((ox+4, oy+4, ox+ts-5, oy+ts-5), fill=floor)
        # AO en esquinas con Bayer
        _ao_esquina(ox, oy, 3)
        _ao_esquina(ox+ts-3, oy, 3)
        _ao_esquina(ox, oy+ts-3, 3)
        _ao_esquina(ox+ts-3, oy+ts-3, 3)
        # Sombra dithered interior 2px
        _dither_rect(ox+4, oy+4, ox+ts-5, oy+5, floor_oscuro, floor, 6)
        draw.point((ox+5, oy+5), fill=floor_claro)
        draw.point((ox+ts-6, oy+ts-6), fill=floor_oscuro)
    elif ttype == 1:  # MURO PIEDRA — surcos verticales + reflejo metal
        draw.rectangle((ox, oy, ox+ts-1, oy+ts-1), fill=wall)
        for i in range(3):
            x = ox+3+i*5
            draw.line((x, oy+2, x, oy+ts-3), fill=wall_claro)
            # Sombra dithered al lado del surco para relieve
            _dither_rect(x+1, oy+2, x+1, oy+ts-3, wall_oscuro, wall, 9)
        # Reflejo metal 1px arriba (PSX)
        draw.line((ox, oy, ox+ts-1, oy), fill=metal_brillo)
        draw.point((ox+1, oy+1), fill=deco_claro)
        # AO lateral
        _dither_rect(ox, oy+1, ox+1, oy+ts-2, wall_sombra, wall, 7)
    elif ttype == 2:  # SUELO DECO — inset con bisel + sombra dithered
        draw.rectangle((ox, oy, ox+ts-1, oy+ts-1), fill=floor)
        draw.rectangle((ox+2, oy+2, ox+ts-3, oy+ts-3), fill=deco)
        # Bisel claro arriba/izq, oscuro abajo/der
        draw.line((ox+2, oy+2, ox+ts-3, oy+2), fill=deco_claro)
        draw.line((ox+2, oy+2, ox+2, oy+ts-3), fill=deco_claro)
        _dither_rect(ox+2, oy+ts-3, ox+ts-3, oy+ts-3, deco_oscuro, deco, 8)
        _dither_rect(ox+ts-3, oy+2, ox+ts-3, oy+ts-3, deco_oscuro, deco, 8)
        draw.rectangle((ox+5, oy+5, ox+ts-6, oy+ts-6), fill=floor_medio)
        _dither_rect(ox+5, oy+5, ox+ts-6, oy+6, floor_oscuro, floor_medio, 6)
    elif ttype == 3:  # TECHO PLATAFORMA — borde metal reflejo
        draw.rectangle((ox, oy, ox+ts-1, oy+ts-1), fill=wall)
        draw.line((ox, oy, ox+ts-1, oy), fill=metal_brillo)
        draw.line((ox, oy+1, ox+ts-1, oy+1), fill=wall_claro)
        draw.line((ox, oy+2, ox+ts-1, oy+2), fill=deco)
        _dither_rect(ox, oy+3, ox+ts-1, oy+4, wall_oscuro, wall, 10)
    elif ttype == 4:  # AGUA — ondas con dithering Bayer
        draw.rectangle((ox, oy, ox+ts-1, oy+ts-1), fill=(28, 58, 128))
        for i in range(3):
            y = oy+5+i*4
            _dither_rect(ox+2+i, y, ox+6+i*2, y, (50, 100, 180), (30, 58, 128), 7)
            draw.line((ox+2, y+1, ox+ts-3, y+1), fill=(70, 130, 210))
        draw.line((ox+2, oy+2, ox+ts-3, oy+2), fill=(90, 150, 230))
        # Brillo dithered en superficie
        for x in range(ox+2, ox+ts-2, 2):
            b = BAYER_4X4[(oy+3) % 4][x % 4]
            if b < 8:
                draw.point((x, oy+3), fill=(140, 200, 255))
    elif ttype == 5:  # MADERA — vetas diagonales dithered PSX + reflejo
        draw.rectangle((ox, oy, ox+ts-1, oy+ts-1), fill=madera_base)
        # Tablones horizontales con junta oscura
        for i in range(4):
            y = oy+2+i*4
            draw.line((ox+2, y, ox+ts-3, y), fill=madera_veta)
            # Vetas diagonales dithered cada tablón
            for x in range(ox+3, ox+ts-3, 4):
                b = BAYER_4X4[y % 4][x % 4]
                if b < 5:
                    draw.point((x, y+1), fill=madera_veta)
                if b < 9:
                    draw.point((x+1, y+2), fill=tuple(max(0, c-10) for c in madera_veta))
            # Highlight 1px diagonal sutil
            if i % 2 == 0:
                draw.point((ox+4+i, y+1), fill=deco_claro)
        # Reflejo 1px vertical izq (metal/madera barnizada)
        draw.line((ox+2, oy+2, ox+2, oy+ts-3), fill=tuple(min(255, c+20) for c in madera_base))
        # AO inferior dithered
        _dither_rect(ox+2, oy+ts-3, ox+ts-3, oy+ts-2, madera_veta, madera_base, 9)
    elif ttype == 6:  # PINCHOS/METAL — peligro con reflejo 1px
        draw.rectangle((ox, oy, ox+ts-1, oy+ts-1), fill=(135, 38, 38))
        for i in range(4):
            draw.polygon([(ox+2+i*4, oy+ts-2), (ox+4+i*4, oy+2), (ox+6+i*4, oy+ts-2)], fill=(175, 58, 58))
            # Reflejo 1px en cara iluminada del pincho
            draw.line((ox+4+i*4, oy+4, ox+4+i*4, oy+8), fill=(220, 120, 120))
            # Sombra dithered base del pincho
            _dither_rect(ox+2+i*4, oy+ts-4, ox+6+i*4, oy+ts-2, (90, 28, 28), (135, 38, 38), 7)
        draw.rectangle((ox+1, oy+1, ox+ts-2, oy+3), fill=(155, 48, 48))
        draw.line((ox+1, oy+1, ox+ts-2, oy+1), fill=(210, 90, 90))
    elif ttype == 7:  # VACÍO — transparente (PSX mantiene transparencia binaria)
        pass
    elif ttype == 8:  # BORDE IZQ — oclusión dithered
        draw.rectangle((ox, oy, ox+ts-1, oy+ts-1), fill=floor)
        draw.rectangle((ox, oy, ox+2, oy+ts-1), fill=wall)
        draw.line((ox+2, oy, ox+2, oy+ts-1), fill=wall_claro)
        _dither_rect(ox+3, oy, ox+4, oy+ts-1, wall_oscuro, floor, 7)
        draw.line((ox, oy, ox, oy+ts-1), fill=metal_brillo)
        _ao_esquina(ox, oy, 2)
    elif ttype == 9:  # BORDE DER
        draw.rectangle((ox, oy, ox+ts-1, oy+ts-1), fill=floor)
        draw.rectangle((ox+ts-3, oy, ox+ts-1, oy+ts-1), fill=wall)
        draw.line((ox+ts-3, oy, ox+ts-3, oy+ts-1), fill=wall_claro)
        _dither_rect(ox+ts-5, oy, ox+ts-4, oy+ts-1, wall_oscuro, floor, 7)
        draw.line((ox+ts-1, oy, ox+ts-1, oy+ts-1), fill=metal_brillo)
    elif ttype == 10:  # BORDE SUP — reflejo 1px
        draw.rectangle((ox, oy, ox+ts-1, oy+ts-1), fill=floor)
        draw.rectangle((ox, oy, ox+ts-1, oy+2), fill=wall)
        draw.line((ox, oy, ox+ts-1, oy), fill=metal_brillo)
        draw.line((ox, oy+2, ox+ts-1, oy+2), fill=wall_claro)
        _dither_rect(ox, oy+3, ox+ts-1, oy+4, wall_oscuro, floor, 8)
    elif ttype == 11:  # BORDE INF — AO dithered
        draw.rectangle((ox, oy, ox+ts-1, oy+ts-1), fill=floor)
        draw.rectangle((ox, oy+ts-3, ox+ts-1, oy+ts-1), fill=wall)
        draw.line((ox, oy+ts-3, ox+ts-1, oy+ts-3), fill=wall_claro)
        _dither_rect(ox, oy+ts-5, ox+ts-1, oy+ts-4, wall_sombra, floor, 6)
        draw.line((ox, oy+ts-1, ox+ts-1, oy+ts-1), fill=wall_oscuro)
    elif ttype == 12:  # ESQUINA SUP-IZQ
        draw.rectangle((ox, oy, ox+ts-1, oy+ts-1), fill=floor)
        draw.rectangle((ox, oy, ox+3, oy+3), fill=wall)
        draw.rectangle((ox, oy, ox+2, oy+ts-1), fill=wall)
        draw.rectangle((ox, oy, ox+ts-1, oy+2), fill=wall)
        draw.line((ox, oy, ox+2, oy), fill=metal_brillo)
        draw.line((ox, oy, ox, oy+2), fill=metal_brillo)
        _dither_rect(ox+3, oy+3, ox+4, oy+4, wall_oscuro, floor, 8)
        _ao_esquina(ox+3, oy+3, 2)
    elif ttype == 13:  # ESQUINA SUP-DER
        draw.rectangle((ox, oy, ox+ts-1, oy+ts-1), fill=floor)
        draw.rectangle((ox+ts-4, oy, ox+ts-1, oy+3), fill=wall)
        draw.rectangle((ox+ts-3, oy, ox+ts-1, oy+ts-1), fill=wall)
        draw.rectangle((ox, oy, ox+ts-1, oy+2), fill=wall)
        draw.line((ox+ts-3, oy, ox+ts-1, oy), fill=metal_brillo)
        _dither_rect(ox+ts-5, oy+3, ox+ts-4, oy+4, wall_oscuro, floor, 8)
    elif ttype == 14:  # ESQUINA INF-IZQ
        draw.rectangle((ox, oy, ox+ts-1, oy+ts-1), fill=floor)
        draw.rectangle((ox, oy+ts-4, ox+3, oy+ts-1), fill=wall)
        draw.rectangle((ox, oy, ox+2, oy+ts-1), fill=wall)
        draw.rectangle((ox, oy+ts-3, ox+ts-1, oy+ts-1), fill=wall)
        draw.line((ox, oy+ts-1, ox+2, oy+ts-1), fill=wall_oscuro)
        _dither_rect(ox+3, oy+ts-5, ox+4, oy+ts-4, wall_sombra, floor, 7)
    elif ttype == 15:  # ESQUINA INF-DER
        draw.rectangle((ox, oy, ox+ts-1, oy+ts-1), fill=floor)
        draw.rectangle((ox+ts-4, oy+ts-4, ox+ts-1, oy+ts-1), fill=wall)
        draw.rectangle((ox+ts-3, oy, ox+ts-1, oy+ts-1), fill=wall)
        draw.rectangle((ox, oy+ts-3, ox+ts-1, oy+ts-1), fill=wall)
        draw.line((ox+ts-1, oy+ts-3, ox+ts-1, oy+ts-1), fill=wall_oscuro)
        _dither_rect(ox+ts-5, oy+ts-5, ox+ts-4, oy+ts-4, wall_oscuro, floor, 7)
    else:
        draw.rectangle((ox, oy, ox+ts-1, oy+ts-1), fill=floor)
    # Outline 1px PSX con oclusión sutil (no plano)
    outline_color = tuple(max(0, c - 22) for c in wall)
    draw.rectangle((ox, oy, ox+ts-1, oy+ts-1), outline=outline_color, width=1)
    # Reflejo 1px en esquina sup-izq del outline para PSX
    draw.point((ox, oy), fill=metal_brillo)


def _gen_procedural_tileset(path, theme, ts=16, cols=16, rows=16):
    """Genera tileset procedural 256x256 (16x16 baldosas) PSX 32-bit alta calidad.

    PSX 2D Tributo: 64-128 colores por tileset, dithering Bayer 4×4 para sombras,
    detalle material (veteado, oclusión, reflejo). Compatibilidad: el bloque
    8×8 superior-izquierdo mantiene el mapeo antiguo (``%8``) para que los TMX
    existentes (GID 1..64) sigan viendo la misma baldosa. Las variantes nuevas
    (bordes autotiling ``%16``) viven en el resto de la hoja. 800×600 + NEAREST.
    """
    _ensure(path)
    img = Image.new("RGBA", (ts*cols, ts*rows), (0,0,0,0))
    draw = ImageDraw.Draw(img)
    for gy in range(rows):
        for gx in range(cols):
            ox, oy = gx * ts, gy * ts
            if gx < 8 and gy < 8:
                ttype = (gy * 8 + gx) % 8
            else:
                ttype = (gy * cols + gx) % 16
            _dibujar_tile_procedural(draw, ox, oy, ts, ttype, theme)
    # Ruido Bayer dithered PSX alta calidad: ±14 con patrón 4×4 para vetear sin banding
    # 160 puntos para riqueza 70-90 colores (antes 120 ±10 daba 59, 280 daba 120+)
    rng = random.Random(hash(str(path)) % (2**31))
    for _ in range(160):
        x = rng.randint(0, ts*cols-1)
        y = rng.randint(0, ts*rows-1)
        r, g, b, a = img.getpixel((x, y))
        if a:
            bayer = BAYER_4X4[y % 4][x % 4]
            delta = rng.randint(-16, 16)
            if bayer < 4:
                delta = int(delta * 0.5)
            elif bayer > 12:
                delta = int(delta * 1.2)
            img.putpixel((x, y), (max(0, min(255, r + delta)), max(0, min(255, g + delta)), max(0, min(255, b + delta)), a))
    # Sombra AO dithered sutil cada 8 baldosas para no saturar paleta
    for gy in range(rows):
        for gx in range(cols):
            if (gx + gy) % 8 == 0:
                ox, oy = gx * ts, gy * ts
                for dy in range(2):
                    for dx in range(2):
                        px, py = ox + ts - 2 + dx, oy + ts - 2 + dy
                        if 0 <= px < ts * cols and 0 <= py < ts * rows:
                            r, g, b, a = img.getpixel((px, py))
                            if a:
                                bayer = BAYER_4X4[py % 4][px % 4]
                                darken = 10 if bayer < 8 else 4
                                img.putpixel((px, py), (max(0, r - darken), max(0, g - darken), max(0, b - darken), a))
    img.save(path)
    _gen_normal_map_para_tileset(path)


def _gen_tileset_stage4_1b(path, ts=16, cols=8, rows=10):
    """AUD-575 — el tileset de la mina inundada: las ocho baldosas
    genéricas de la paleta café (roca húmeda, AUD-531) más dos filas de
    decoración propia de la mina:

      GID 65  estalactita grande      — cuelga del techo (BG_Near)
      GID 66  estalactita pequeña     — cuelga del techo (BG_Near)
      GID 67  alga                    — la maleza que agarra (Terrain_Detail)
      GID 68  alga alta               — la maleza que agarra (Terrain_Detail)
      GID 69  viga oxidada            — la madera del andén del patio
      GID 70  planta de agua          — coral/planta del lecho
      GID 71  roca con óxido          — mancha de hierro viejo en el lecho
      GID 72  soporte con riel        — la maquinaria abandonada
      GID 73  vagoneta oxidada        — storytelling: "aquí había gente"
      GID 74  cadena colgante         — la maquinaria abandonada (techo)
      GID 75  lámpara apagada         — la última, antes del abismo
      GID 76  pico de mina            — herramienta abandonada en el lecho

    La fila extra es por qué `tools/generate_stage4_1b.py` declara
    `TILESET_ROWS = 10`: el tilecount del TMX y el alto de la imagen
    tienen que cuadrar con lo que aquí se dibuja.
    """
    theme = TILESET_THEMES["tileset_stage4_1b"]
    _ensure(path)
    img = Image.new("RGBA", (ts*cols, ts*rows), (0,0,0,0))
    draw = ImageDraw.Draw(img)
    for gy in range(rows - 2):
        for gx in range(cols):
            ox, oy = gx * ts, gy * ts
            ttype = (gy * cols + gx) % 8
            _dibujar_tile_procedural(draw, ox, oy, ts, ttype, theme)

    # ── la fila de la mina ──────────────────────────────────────
    roca = theme["floor"]                      # (58,42,28)
    roca_clara = theme["deco"]                 # (78,56,36)
    roca_oscura = theme["wall"]                # (34,24,16)
    oxido = (140, 70, 40)
    oxido_oscuro = (110, 50, 30)
    musgo = (70, 82, 46)
    musgo_claro = (92, 106, 60)
    madera = (96, 68, 40)
    planta = (150, 92, 60)

    def tile(gx, dibuja):
        _dibujar_tile_procedural(draw, gx * ts, (rows - 1) * ts, ts, 7, theme)
        dibuja(gx * ts, (rows - 1) * ts)

    def estalactita(ox, oy, ancho, alto, con_punta_ligera=True):
        cx = ox + ts // 2
        draw.polygon([(cx - ancho // 2, oy), (cx + ancho // 2, oy),
                      (cx, oy + alto)], fill=roca_oscura, outline=roca)
        if con_punta_ligera:
            draw.line((cx, oy + alto - 3, cx, oy + alto), fill=roca)

    tile(0, lambda ox, oy: estalactita(ox, oy, 12, 16))
    tile(1, lambda ox, oy: estalactita(ox, oy, 8, 11))

    def alga(ox, oy, alta):
        for i in range(2 if alta else 1):
            ax = ox + 3 + i * 8
            pts = [(ax, oy + ts - 1), (ax - 1, oy + 4), (ax + 2, oy + 6),
                   (ax + 1, oy + ts - 1)]
            draw.polygon(pts, fill=musgo, outline=musgo_claro)

    tile(2, lambda ox, oy: alga(ox, oy, False))
    tile(3, lambda ox, oy: alga(ox, oy, True))

    def viga_oxidada(ox, oy):
        draw.rectangle((ox, oy + 3, ox + ts - 1, oy + 8), fill=madera)
        draw.line((ox, oy + 5, ox + ts - 1, oy + 5), fill=roca_oscura)
        draw.rectangle((ox, oy + 10, ox + ts - 1, oy + 12), fill=oxido)
        draw.ellipse((ox + 4, oy + 5, ox + 6, oy + 7), fill=oxido_oscuro)
        draw.ellipse((ox + 10, oy + 5, ox + 12, oy + 7), fill=oxido_oscuro)

    tile(4, viga_oxidada)

    def planta_de_agua(ox, oy):
        cx = ox + ts // 2
        draw.line((cx, oy + ts - 1, cx, oy + 6), fill=planta)
        draw.line((cx, oy + 10, cx - 5, oy + 3), fill=planta)
        draw.line((cx, oy + 8, cx + 5, oy + 2), fill=planta)
        draw.ellipse((cx - 6, oy + 1, cx - 2, oy + 5), fill=roca_clara)
        draw.ellipse((cx + 2, oy, cx + 6, oy + 4), fill=roca_clara)

    tile(5, planta_de_agua)

    def roca_con_oxido(ox, oy):
        _dibujar_tile_procedural(draw, ox, oy, ts, 0, theme)
        draw.ellipse((ox + 3, oy + 4, ox + 9, oy + 10), fill=oxido)
        draw.ellipse((ox + 8, oy + 8, ox + 13, oy + 13), fill=oxido_oscuro)
        draw.line((ox + 5, oy + 6, ox + 11, oy + 12), fill=roca)

    tile(6, roca_con_oxido)

    def soporte_con_riel(ox, oy):
        draw.rectangle((ox + 6, oy, ox + 9, oy + ts - 1), fill=madera)
        draw.line((ox + 3, oy + 4, ox + 12, oy + 4), fill=oxido_oscuro)
        draw.line((ox + 3, oy + 6, ox + 12, oy + 6), fill=oxido)
        draw.rectangle((ox, oy + 10, ox + ts - 1, oy + 13), fill=roca_oscura)

    tile(7, soporte_con_riel)

    # ── la segunda fila de la mina (AUD-576) ─────────────────────
    # La narrativa ambiental del blueprint 10/10: la mina se reconoce y
    # luego se deshace. Vagonetas y herramientas cuentan "aquí había
    # gente"; la lámpara apagada es el último farol, antes del abismo.
    def tile2(gx, dibuja):
        _dibujar_tile_procedural(draw, gx * ts, (rows - 2) * ts, ts, 7, theme)
        dibuja(gx * ts, (rows - 2) * ts)

    def vagoneta(ox, oy):
        # Cuerpo de metal oxidado sobre una rueda: la vagoneta de mina.
        draw.rounded_rectangle(
            (ox + 2, oy + 5, ox + 13, oy + 12), radius=2, fill=oxido_oscuro,
            outline=oxido)
        draw.line((ox + 4, oy + 6, ox + 11, oy + 6), fill=oxido)
        draw.ellipse((ox + 5, oy + 12, ox + 10, oy + 15), fill=roca_oscura,
                     outline=oxido)
        draw.line((ox + 8, oy + 13, ox + 8, oy + 15), fill=roca)
        draw.rectangle((ox + 6, oy + 8, ox + 9, oy + 11), fill=(40, 26, 16))

    tile2(0, vagoneta)

    def cadena(ox, oy):
        # Dos eslabones colgando del techo, oxidadas.
        for ex in (ox + 5, ox + 10):
            draw.ellipse((ex, oy + 1, ex + 2, oy + 5), outline=oxido_oscuro)
            draw.ellipse((ex, oy + 5, ex + 2, oy + 9), outline=oxido)
            draw.ellipse((ex, oy + 9, ex + 2, oy + 13), outline=oxido_oscuro)

    tile2(1, cadena)

    def lampara_apagada(ox, oy):
        # El farol que ya no alumbra: la caja sin luz, contra la roca.
        draw.rectangle((ox + 3, oy + 3, ox + 12, oy + 6), fill=madera)
        draw.rectangle((ox + 4, oy + 6, ox + 11, oy + 12), fill=(22, 16, 12),
                       outline=roca_oscura)
        draw.line((ox + 6, oy + 7, ox + 9, oy + 7), fill=roca_oscura)

    tile2(2, lampara_apagada)

    def pico(ox, oy):
        # Herramienta abandonada: mango de madera y cabeza de hierro.
        draw.line((ox + 3, oy + 14, ox + 11, oy + 4), fill=madera, width=2)
        draw.arc((ox + 7, oy + 1, ox + 14, oy + 8), 60, 240,
                 fill=oxido, width=2)
        draw.line((ox + 11, oy + 4, ox + 13, oy + 2), fill=oxido_oscuro)

    tile2(3, pico)

    img.save(path)
    _gen_normal_map_para_tileset(path)

# ── El tileset del cementerio (AUD-237) ──
#
# `tileset_cemetery.png` existía y no lo usaba **nadie**. Lo hacía
# `_gen_procedural_tileset`, que produce ocho baldosas genéricas —piedra lisa,
# azul oscuro, tablones, ladrillo rojo— repetidas ocho veces hacia abajo; el
# Asset Bible le pide «stone markers, ceremonial carvings». Por eso el 4-1
# pintaba su suelo con el tileset del prólogo: el del cementerio era peor.
#
# Aquí se dibujan las ocho baldosas que el nivel usa de verdad, y con una regla
# encima: **el musgo y el lodo son la misma losa con otra superficie**. Si fueran
# tres materiales que no se parecen, el jugador leería «tres suelos distintos»;
# siendo la misma piedra con algo encima, lee «esta losa está cubierta», que es
# lo que explica por qué resbala.
CEM_LOSA = (96, 96, 110)          # la piedra que se pisa
CEM_LOSA_LUZ = (128, 128, 144)
CEM_LOSA_SOMBRA = (62, 62, 74)
CEM_TIERRA_T = (46, 34, 28)       # bajo la losa
CEM_MURO = (58, 56, 70)
CEM_MUSGO_T = (58, 128, 62)
CEM_MUSGO_OSC = (36, 84, 44)
CEM_LODO_T = (104, 74, 44)
CEM_LODO_OSC = (68, 48, 28)

#: Qué hay en cada casilla de la hoja, por índice. El GID del TMX es índice + 1,
#: así que esta lista **es** el contrato con `generate_stage4_1.py`: cambiar el
#: orden aquí sin cambiarlo allí repinta el nivel entero con las baldosas
#: equivocadas, que es como `stage_mecanicas` acabó pintando basura (AUD-115).
CEM_ORDEN = (
    "vacio", "losa", "relleno", "muro",
    "musgo", "musgo_relleno", "lodo", "lodo_relleno",
    "lapida_alta", "lapida_baja", "cruz", "grieta",
)


def _cem_losa(draw, ox, oy, ts, base=CEM_LOSA, luz=CEM_LOSA_LUZ):
    """La piedra PSX 32-bit: canto iluminado, junta y AO dithered con Bayer."""
    draw.rectangle((ox, oy, ox + ts - 1, oy + ts - 1), fill=base)
    draw.line((ox, oy, ox + ts - 1, oy), fill=luz)
    draw.line((ox, oy + 1, ox + ts - 1, oy + 1),
              fill=tuple((oscuro + claro) // 2
                         for oscuro, claro in zip(base, luz, strict=True)))
    draw.line((ox, oy + ts - 1, ox + ts - 1, oy + ts - 1), fill=CEM_LOSA_SOMBRA)
    draw.line((ox + ts // 3, oy + 3, ox + ts // 3, oy + ts - 2),
              fill=CEM_LOSA_SOMBRA)
    # AO dithered en esquinas con Bayer 4×4 (PSX)
    for dy in range(2):
        for dx in range(2):
            b = BAYER_4X4[(oy+dy) % 4][(ox+dx) % 4]
            if b < 6:
                draw.point((ox+dx, oy+dy), fill=CEM_LOSA_SOMBRA)
            b2 = BAYER_4X4[(oy+ts-1-dy) % 4][(ox+ts-1-dx) % 4]
            if b2 < 10:
                draw.point((ox+ts-1-dx, oy+ts-1-dy), fill=tuple(max(0, c-12) for c in base))
    # Reflejo 1px metal en borde superior izq
    draw.point((ox, oy), fill=tuple(min(255, c+22) for c in luz))


def _gen_tileset_cementerio(path, ts=16, cols=16, rows=16):
    """Cementerio 256x256 (16x16) - mantiene GID contrato para primeros 12 y anade variantes.

    Compatibilidad AUD-115: los GID 1..12 (indices 0..11) quedan en las mismas
    celdas 8x8 originales (``%8``), el resto de la hoja 16x16 son variantes nuevas.
    """
    _ensure(path)
    img = Image.new("RGBA", (ts * cols, ts * rows), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    rng = random.Random(4341)

    for indice, clase in enumerate(CEM_ORDEN):
        ox, oy = (indice % 8) * ts, (indice // 8) * ts

        if clase == "vacio":
            continue

        if clase == "losa":
            _cem_losa(draw, ox, oy, ts)

        elif clase == "relleno":
            draw.rectangle((ox, oy, ox + ts - 1, oy + ts - 1), fill=CEM_TIERRA_T)
            for _ in range(14):     # guijarros, para que no sea un plano liso
                px, py = rng.randint(ox + 1, ox + ts - 2), rng.randint(oy + 1, oy + ts - 2)
                draw.point((px, py), fill=(62, 48, 40))

        elif clase == "muro":
            draw.rectangle((ox, oy, ox + ts - 1, oy + ts - 1), fill=CEM_MURO)
            for fy in (0, 8):       # sillares alternados
                dx = 0 if fy == 0 else ts // 2
                draw.line((ox + dx, oy + fy, ox + dx, oy + fy + 7),
                          fill=(44, 42, 54))
                draw.line((ox, oy + fy + 7, ox + ts - 1, oy + fy + 7),
                          fill=(44, 42, 54))

        elif clase in ("musgo", "lodo"):
            # La misma losa debajo: es lo que hace que se lea como suelo cubierto
            # y no como otro material.
            _cem_losa(draw, ox, oy, ts)
            claro, oscuro = ((CEM_MUSGO_T, CEM_MUSGO_OSC) if clase == "musgo"
                             else (CEM_LODO_T, CEM_LODO_OSC))
            draw.rectangle((ox, oy, ox + ts - 1, oy + 5), fill=claro)
            draw.line((ox, oy + 5, ox + ts - 1, oy + 5), fill=oscuro)
            if clase == "musgo":
                # Matas que asoman: la señal de lejos de que ahí se resbala.
                for mx in range(ox + 1, ox + ts - 1, 3):
                    alto = rng.randint(2, 4)
                    draw.line((mx, oy - alto + 6, mx, oy + 6), fill=claro)
                    draw.point((mx, oy - alto + 6), fill=(120, 200, 110))
            else:
                # Raíces: dos hilos que cruzan el barro.
                for _ in range(3):
                    ry = rng.randint(oy + 1, oy + 4)
                    draw.line((ox, ry, ox + ts - 1, ry + rng.randint(-1, 1)),
                              fill=oscuro)

        elif clase in ("musgo_relleno", "lodo_relleno"):
            fondo = CEM_MUSGO_OSC if clase == "musgo_relleno" else CEM_LODO_OSC
            draw.rectangle((ox, oy, ox + ts - 1, oy + ts - 1), fill=fondo)
            for _ in range(10):
                px, py = rng.randint(ox + 1, ox + ts - 2), rng.randint(oy + 1, oy + ts - 2)
                draw.point((px, py), fill=tuple(max(0, c - 14) for c in fondo))

        elif clase in ("lapida_alta", "lapida_baja"):
            # Dos mitades de una lápida de dos baldosas de alto: la de arriba
            # lleva la cabeza redondeada y la inscripción.
            draw.rectangle((ox + 3, oy, ox + ts - 4, oy + ts - 1), fill=CEM_LOSA)
            if clase == "lapida_alta":
                # La cúpula, **dentro** de su baldosa. Con un `oy - 4` se salía
                # por arriba y manchaba la casilla de al lado en la hoja: una
                # baldosa vacía que no está vacía es basura que aparece en el
                # mapa donde nadie la puso.
                draw.ellipse((ox + 3, oy, ox + ts - 4, oy + 9), fill=CEM_LOSA)
                draw.line((ox + 5, oy + 9, ox + ts - 6, oy + 9), fill=CEM_LOSA_SOMBRA)
                draw.line((ox + 5, oy + 12, ox + ts - 6, oy + 12), fill=CEM_LOSA_SOMBRA)
            else:
                draw.rectangle((ox + 1, oy + ts - 3, ox + ts - 2, oy + ts - 1),
                               fill=CEM_LOSA_SOMBRA)
            draw.line((ox + 3, oy, ox + 3, oy + ts - 1), fill=CEM_LOSA_LUZ)

        elif clase == "cruz":
            draw.rectangle((ox + 7, oy + 2, ox + 9, oy + ts - 1), fill=CEM_LOSA)
            draw.rectangle((ox + 3, oy + 5, ox + ts - 4, oy + 7), fill=CEM_LOSA)
            draw.line((ox + 7, oy + 2, ox + 7, oy + ts - 1), fill=CEM_LOSA_LUZ)

        elif clase == "grieta":
            # Una fisura verde para quien quiera pintarla en el mapa en vez de
            # dejársela a la escena.
            draw.rectangle((ox, oy, ox + ts - 1, oy + ts - 1), fill=CEM_TIERRA_T)
            x = ox + ts // 2
            for y in range(oy, oy + ts):
                x += rng.randint(-1, 1)
                x = max(ox + 1, min(ox + ts - 2, x))
                draw.point((x, y), fill=(90, 220, 120))
                draw.point((x + 1, y), fill=(40, 120, 60))

    # Rellena el resto de la hoja 16x16 (fuera del bloque 8x8 original) — PSX variantes con dithering
    for gy in range(rows):
        for gx in range(cols):
            if gy < 2 and gx < 8:
                indice = gy*8 + gx
                if indice < len(CEM_ORDEN):
                    continue
            ox, oy = gx*ts, gy*ts
            if img.getpixel((ox+2, oy+2))[3] == 0:
                _cem_losa(draw, ox, oy, ts)
                if (gx+gy) % 5 == 0:
                    draw.point((ox+2, oy+2), fill=(140,140,150))
                # Vetado piedra sutil con Bayer cada 6 baldosas
                if (gx+gy) % 6 == 0:
                    for yy in range(oy+4, oy+ts-4, 4):
                        for xx in range(ox+3, ox+ts-3, 6):
                            if BAYER_4X4[yy%4][xx%4] < 5:
                                draw.point((xx, yy), fill=tuple(max(0, c-10) for c in CEM_LOSA))
    # Ruido Bayer PSX para riqueza cromática 60-90 colores (cementerio era 19, muy bajo)
    rng2 = random.Random(hash(str(path)) % (2**31))
    for _ in range(180):
        x = rng2.randint(0, ts*cols-1)
        y = rng2.randint(0, ts*rows-1)
        r, g, b, a = img.getpixel((x, y))
        if a:
            dv = rng2.randint(-14, 14)
            if BAYER_4X4[y%4][x%4] < 6:
                dv = int(dv*0.5)
            img.putpixel((x, y), (max(0,min(255,r+dv)), max(0,min(255,g+dv)), max(0,min(255,b+dv)), a))
    img.save(path)
    _gen_normal_map_para_tileset(path)


#: AUD-469 — el 4-1 reconstruido (`docs/niveles/15_DISENO_4_1_EL_CEMENTERIO.md`)
#: tiene **seis secciones con terreno propio**, no una gradación de color
#: sobre el mismo suelo de siempre — eso fue justo lo que el dueño del
#: proyecto rechazó del primer intento (AUD-462…466). Cada familia de
#: baldosa es una sección: cripta, bosque, camino de huesos, tierra
#: quemada, tumbas, piedra sagrada. El musgo y el lodo de la Fase 2 siguen
#: la misma regla que ya vale para el cementerio: la misma losa con otra
#: superficie encima, no un material que no se parece a nada.
S4_CRIPTA = (96, 96, 110)
S4_CRIPTA_RELLENO = (46, 34, 28)
S4_BOSQUE = (58, 64, 40)
S4_BOSQUE_RELLENO = (32, 30, 20)
S4_HUESOS = (168, 158, 132)
S4_HUESOS_RELLENO = (90, 80, 64)
S4_QUEMADO = (48, 40, 36)
S4_QUEMADO_RELLENO = (26, 22, 20)
S4_TUMBAS = (72, 58, 44)
S4_TUMBAS_RELLENO = (40, 32, 24)
S4_SAGRADA = (66, 66, 86)
S4_SAGRADA_RELLENO = (36, 36, 50)
S4_VERDE_ESPECTRAL = (124, 255, 160)

#: El contrato con `generate_stage4_1.py` — igual que `CEM_ORDEN` para el
#: cementerio: cambiar el orden aquí sin cambiarlo allí repinta el nivel
#: entero con la baldosa equivocada (AUD-115).
STAGE4_1_ORDEN = (
    "vacio", "cripta", "cripta_relleno", "muro",
    "bosque", "bosque_relleno", "musgo", "musgo_relleno",
    "lodo", "lodo_relleno", "huesos", "huesos_relleno",
    "quemado", "quemado_relleno", "tumbas", "tumbas_relleno",
    "sagrada", "sagrada_relleno", "lapida_alta", "lapida_baja",
    "cruz", "calavera",
)


def _gen_tileset_stage4_1(path, ts=16, cols=8, rows=3):
    _ensure(path)
    img = Image.new("RGBA", (ts * cols, ts * rows), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    rng = random.Random(4691)

    def _relleno(ox, oy, color):
        draw.rectangle((ox, oy, ox + ts - 1, oy + ts - 1), fill=color)
        for _ in range(10):
            px = rng.randint(ox + 1, ox + ts - 2)
            py = rng.randint(oy + 1, oy + ts - 2)
            draw.point((px, py), fill=tuple(max(0, c - 14) for c in color))

    for indice, clase in enumerate(STAGE4_1_ORDEN):
        ox, oy = (indice % cols) * ts, (indice // cols) * ts

        if clase == "vacio":
            continue
        elif clase == "muro":
            draw.rectangle((ox, oy, ox + ts - 1, oy + ts - 1), fill=CEM_MURO)
            draw.line((ox, oy, ox + ts - 1, oy), fill=(78, 76, 90))
        elif clase == "cripta":
            _cem_losa(draw, ox, oy, ts, base=S4_CRIPTA, luz=CEM_LOSA_LUZ)
        elif clase == "cripta_relleno":
            _relleno(ox, oy, S4_CRIPTA_RELLENO)
        elif clase == "bosque":
            draw.rectangle((ox, oy, ox + ts - 1, oy + ts - 1), fill=S4_BOSQUE)
            draw.line((ox, oy, ox + ts - 1, oy), fill=(80, 90, 56))
            for _ in range(6):  # hierba
                bx = rng.randint(ox + 1, ox + ts - 2)
                draw.line((bx, oy, bx, oy - rng.randint(1, 3)), fill=(90, 110, 60))
        elif clase == "bosque_relleno":
            _relleno(ox, oy, S4_BOSQUE_RELLENO)
        elif clase in ("musgo", "lodo"):
            # La misma tierra de bosque debajo, con la superficie encima —
            # la regla del cementerio, aplicada aquí también.
            draw.rectangle((ox, oy, ox + ts - 1, oy + ts - 1), fill=S4_BOSQUE)
            claro, oscuro = ((CEM_MUSGO_T, CEM_MUSGO_OSC) if clase == "musgo"
                             else (CEM_LODO_T, CEM_LODO_OSC))
            draw.rectangle((ox, oy, ox + ts - 1, oy + 5), fill=claro)
            draw.line((ox, oy + 5, ox + ts - 1, oy + 5), fill=oscuro)
            if clase == "musgo":
                for mx in range(ox + 1, ox + ts - 1, 3):
                    alto = rng.randint(2, 4)
                    draw.line((mx, oy - alto + 6, mx, oy + 6), fill=claro)
            else:
                for _ in range(3):
                    ry = rng.randint(oy + 1, oy + 4)
                    draw.line((ox, ry, ox + ts - 1, ry + rng.randint(-1, 1)),
                              fill=oscuro)
        elif clase in ("musgo_relleno", "lodo_relleno"):
            fondo = CEM_MUSGO_OSC if clase == "musgo_relleno" else CEM_LODO_OSC
            _relleno(ox, oy, fondo)
        elif clase == "huesos":
            draw.rectangle((ox, oy, ox + ts - 1, oy + ts - 1), fill=S4_HUESOS)
            # Una costilla curva, apenas insinuada — el camino está hecho de
            # huesos, no sólo tiene huesos encima.
            draw.arc((ox + 1, oy + 4, ox + ts - 2, oy + ts + 4), 200, 340,
                     fill=(120, 112, 92))
        elif clase == "huesos_relleno":
            _relleno(ox, oy, S4_HUESOS_RELLENO)
        elif clase == "quemado":
            draw.rectangle((ox, oy, ox + ts - 1, oy + ts - 1), fill=S4_QUEMADO)
            for _ in range(4):  # brasas apagadas
                px = rng.randint(ox + 1, ox + ts - 2)
                py = rng.randint(oy + 1, oy + ts - 2)
                draw.point((px, py), fill=(90, 50, 30))
        elif clase == "quemado_relleno":
            _relleno(ox, oy, S4_QUEMADO_RELLENO)
        elif clase == "tumbas":
            draw.rectangle((ox, oy, ox + ts - 1, oy + ts - 1), fill=S4_TUMBAS)
            draw.line((ox, oy + 2, ox + ts - 1, oy + 1), fill=(56, 46, 34))
        elif clase == "tumbas_relleno":
            _relleno(ox, oy, S4_TUMBAS_RELLENO)
        elif clase == "sagrada":
            draw.rectangle((ox, oy, ox + ts - 1, oy + ts - 1), fill=S4_SAGRADA)
            # La veta verde que la Fase 6 enciende al paso (AUD-463): aquí
            # sólo se insinúa, tenue — el brillo real lo pone la luz de la
            # escena, no la baldosa.
            vx = ox + ts // 2
            for y in range(oy, oy + ts):
                draw.point((vx, y), fill=(*S4_VERDE_ESPECTRAL, 90))
        elif clase == "sagrada_relleno":
            _relleno(ox, oy, S4_SAGRADA_RELLENO)
        elif clase in ("lapida_alta", "lapida_baja"):
            draw.rectangle((ox + 3, oy, ox + ts - 4, oy + ts - 1), fill=CEM_LOSA)
            if clase == "lapida_alta":
                draw.ellipse((ox + 3, oy, ox + ts - 4, oy + 9), fill=CEM_LOSA)
                draw.line((ox + 5, oy + 9, ox + ts - 6, oy + 9), fill=CEM_LOSA_SOMBRA)
            else:
                draw.rectangle((ox + 1, oy + ts - 3, ox + ts - 2, oy + ts - 1),
                               fill=CEM_LOSA_SOMBRA)
            draw.line((ox + 3, oy, ox + 3, oy + ts - 1), fill=CEM_LOSA_LUZ)
        elif clase == "cruz":
            draw.rectangle((ox + 7, oy + 2, ox + 9, oy + ts - 1), fill=CEM_LOSA)
            draw.rectangle((ox + 3, oy + 5, ox + ts - 4, oy + 7), fill=CEM_LOSA)
        elif clase == "calavera":
            # Un cráneo pequeño, hueco de ojos oscuro — el acento del camino
            # de huesos, no el suelo entero.
            draw.rectangle((ox, oy, ox + ts - 1, oy + ts - 1), fill=S4_HUESOS)
            cx, cy = ox + ts // 2, oy + ts // 2
            draw.ellipse((cx - 5, cy - 5, cx + 5, cy + 3), fill=(228, 220, 200))
            draw.ellipse((cx - 3, cy - 2, cx - 1, cy), fill=(40, 36, 30))
            draw.ellipse((cx + 1, cy - 2, cx + 3, cy), fill=(40, 36, 30))

    img.save(path)
    _gen_normal_map_para_tileset(path)


def _gen_normal_map_para_tileset(tileset_path):
    """Genera *_n.png normal map 8-bit PSX alta calidad para un tileset (Light con sombras_proyectadas).

    8-bit por canal (RGB 32-bit con 12 normales): plano (128,128,255) + 8 direcciones
    cardinales/diagonales + 4 esquinas diagonales internas = 12 variaciones distintas.
    El LightSystem lee la normal via sprite_batch GPU (atlas + normales); para tiles se
    usa como bump que el sombreado direccional muestrea con NEAREST sin difuminar.
    PSX 32-bit: relieve sutil con oclusión, no blur."""
    try:
        src = Image.open(str(tileset_path)).convert("RGBA")
    except Exception:
        return
    w, h = src.size
    normal = Image.new("RGB", (w, h), (128, 128, 255))
    n_draw = ImageDraw.Draw(normal)
    ts = 16
    cols = w // ts
    rows = h // ts
    for gy in range(rows):
        for gx in range(cols):
            ox, oy = gx*ts, gy*ts
            vacia = True
            for yy in range(oy, oy+ts):
                for xx in range(ox, ox+ts):
                    if src.getpixel((xx, yy))[3] != 0:
                        vacia = False
                        break
                if not vacia:
                    break
            if vacia:
                continue
            # 8 direcciones cardinales + diagonales (PSX 32-bit)
            n_draw.line((ox, oy, ox, oy+ts-1), fill=(96, 128, 255))  # W
            n_draw.line((ox+ts-1, oy, ox+ts-1, oy+ts-1), fill=(160, 128, 255))  # E
            n_draw.line((ox, oy, ox+ts-1, oy), fill=(128, 96, 255))  # N
            n_draw.line((ox, oy+ts-1, ox+ts-1, oy+ts-1), fill=(128, 160, 255))  # S
            n_draw.point((ox, oy), fill=(96, 96, 255))  # NW
            n_draw.point((ox+ts-1, oy), fill=(160, 96, 255))  # NE
            n_draw.point((ox, oy+ts-1), fill=(96, 160, 255))  # SW
            n_draw.point((ox+ts-1, oy+ts-1), fill=(160, 160, 255))  # SE
            # 4 esquinas diagonales internas adicionales para 12 totales (8 dirs +4 esquinas)
            # Mids con Bayer sutil para variación PSX sin esquinas quemadas
            n_draw.line((ox+2, oy, ox+ts-3, oy), fill=(112, 96, 255))  # N mid
            n_draw.line((ox+2, oy+ts-1, ox+ts-3, oy+ts-1), fill=(112, 160, 255))  # S mid
            n_draw.line((ox, oy+2, ox, oy+ts-3), fill=(96, 112, 255))  # W mid
            n_draw.line((ox+ts-1, oy+2, ox+ts-1, oy+ts-3), fill=(160, 112, 255))  # E mid
    n_path = tileset_path.with_name(tileset_path.stem + "_n.png")
    normal.save(n_path)


def _gen_tileset_liquidos(path=None, ts=16):
    """Tileset liquidos animado 128x32 (4 frames de 32x32) para HazardZone/WaterZone.

    Cada frame es una variante de agua/peligro animada - se usa como tileset
    animado o como decoracion liquida sobre zonas de dano/agua ya existentes.
    Mantiene el estilo pixel (nearest) y la paleta de 32 colores de la zona."""
    if path is None:
        path = A / "tilesets" / "tileset_liquidos.png"
    _ensure(path)
    fw, fh = 32, 32
    frames = 4
    w, h = fw*frames, fh
    sheet = Image.new("RGBA", (w, h), (0,0,0,0))
    for f in range(frames):
        ox = f*fw
        img = Image.new("RGBA", (fw, fh), (0,0,0,0))
        d = ImageDraw.Draw(img)
        for y in range(fh):
            t = y / fh
            r = int(30 + t*20 + f*2)
            g = int(90 + t*40 + f*3)
            b = int(160 + t*50)
            d.line((0, y, fw-1, y), fill=(r,g,b,255))
        for x in range(0, fw, 4):
            wy = int(8 + 6*__import__('math').sin((x + f*8)/8.0) + (f % 2)*2)
            d.line((x, wy, x+2, wy), fill=(150, 220, 240, 200))
            d.point((x+1, wy+1), fill=(255,255,255,180))
        if f % 2 == 0:
            d.rectangle((2, 2, fw-3, 6), fill=(200, 230, 255, 160))
        if f >= 2:
            d.rectangle((0, fh-8, fw-1, fh-1), fill=(180, 60, 50, 120))
        sheet.paste(img, (ox, 0))
    sheet.save(path)
    _gen_normal_map_para_tileset(path)
    return path


def _gen_all_tilesets():
    print("  Tilesets...")
    for name, theme in TILESET_THEMES.items():
        if name == "tileset_cemetery":
            _gen_tileset_cementerio(A / "tilesets" / f"{name}.png")
        elif name == "tileset_stage4_1":
            _gen_tileset_stage4_1(A / "tilesets" / f"{name}.png")
        elif name == "tileset_stage4_1b":
            _gen_tileset_stage4_1b(A / "tilesets" / f"{name}.png")
        elif theme == "gothic":
            _gen_gothic_tileset(A / "tilesets" / f"{name}.png")
        else:
            _gen_procedural_tileset(A / "tilesets" / f"{name}.png", theme)
    _gen_tileset_liquidos()

# ════════════════════════════════════════
# SECTION 5: BACKGROUNDS (all zones, 3 layers each)
# ════════════════════════════════════════

# ── Stage 0 backgrounds: gothic cave/castle parallax layers ──

def _gen_bg_stage0_far(path, w=320, h=224):
    """Far layer: night sky with stars and crescent moon."""
    _ensure(path)
    img = Image.new("RGB", (w, h))
    draw = ImageDraw.Draw(img)
    for y in range(h):
        t = y / h
        r = int(8 + t * 20)
        g = int(12 + t * 30)
        b = int(28 + t * 48)
        draw.line((0, y, w - 1, y), fill=(r, g, b))
    rng = random.Random(42)
    for _ in range(80):
        sx = rng.randint(0, w - 1)
        sy = rng.randint(0, h // 2)
        br = rng.randint(120, 255)
        draw.point((sx, sy), fill=(br, br, br))
    draw.ellipse((230, 20, 280, 70), fill=(190, 190, 175))
    draw.ellipse((238, 22, 285, 72), fill=(8, 12, 28))
    img.save(path)


def _gen_bg_stage0_mid(path, w=640, h=224):
    """Mid layer: gothic castle silhouette."""
    _ensure(path)
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    castle = (22, 18, 38)
    tower = (18, 14, 32)
    spire = (14, 10, 26)

    def _draw_castle(cx, cy, cw, ch):
        draw.rectangle((cx, cy, cx + cw, cy + ch), fill=castle)
        for bx in range(cx, cx + cw, 8):
            draw.rectangle((bx, cy, bx + 5, cy + 8), fill=tower)
    def _draw_tower(tx, ty, tw, th, sp=20):
        draw.rectangle((tx, ty, tx + tw, ty + th), fill=tower)
        draw.polygon([(tx, ty), (tx + tw // 2, ty - sp), (tx + tw, ty)], fill=spire)

    _draw_castle(180, 75, 120, 149)
    _draw_tower(170, 55, 25, 169, 16)
    _draw_tower(285, 45, 25, 179, 20)
    _draw_tower(400, 80, 30, 144, 22)
    draw.rectangle((420, 90, 480, 224), fill=castle)
    _draw_tower(470, 60, 25, 164, 18)
    _draw_castle(40, 100, 80, 124)
    _draw_tower(30, 85, 22, 139, 14)
    img.save(path)


def _gen_bg_stage0_near(path, w=960, h=224):
    """Near layer: cave interior with stone pillars and torches."""
    _ensure(path)
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    rng = random.Random(99)
    pillar_color = (30, 28, 40)
    for px in range(0, w, 120):
        rw = rng.randint(14, 20)
        # Pillar
        draw.rectangle((px, 0, px + rw, h), fill=pillar_color)
        draw.rectangle((px - 2, 0, px + rw + 2, 10), fill=(35, 33, 45))
        # Torch glow
        tx = px + rw // 2
        torch_h = 100 + rng.randint(-20, 40)
        for rad, alpha in [(40, 20), (25, 40), (15, 80)]:
            glow = Image.new("RGBA", (rad * 2, rad * 2), (0, 0, 0, 0))
            ImageDraw.Draw(glow).ellipse((0, 0, rad * 2, rad * 2),
                                         fill=(255, 200, 50, alpha))
            img.paste(glow, (tx - rad, torch_h - rad), glow)
        draw.rectangle((tx - 2, torch_h, tx + 2, torch_h + 20), fill=(60, 40, 20))
        draw.ellipse((tx - 4, torch_h - 10, tx + 4, torch_h + 4),
                     fill=(255, 200, 50))
    # Floor silhouette
    draw.rectangle((0, h - 40, w, h), fill=(18, 16, 28))
    img.save(path)


# ── Zona Final: el cementerio (bg_final_*) ──
#
# AUD-209: estas tres capas las hacía `_gen_procedural_bg`, o sea un degradado
# con ruido y nada más — sin lápidas, sin árboles, sin horizonte. El 4-1, que es
# el único nivel de la zona, acabó por eso apuntando al fondo del prólogo
# (`background_zone = "stage0"`) y se jugaba dentro del castillo gótico del
# principio: el documento de diseño prometía un cementerio y en pantalla había
# otra cosa.
#
# La paleta no me la invento: es la que fija el Asset Bible
# (`docs/20_ASSET_BIBLE.md`, «Cemetery background palette»).
CEM_CIELO_ALTO = (10, 0, 20)      # morado casi negro
CEM_CIELO_BAJO = (34, 22, 50)
CEM_PIEDRA = (74, 74, 90)
CEM_VERDE = (40, 200, 80)         # el verde espectral del canon
CEM_LUNA = (200, 212, 200)
CEM_TIERRA = (30, 20, 16)

#: Dónde va la línea del suelo dentro de la imagen, en tanto por uno de su alto.
#:
#: No es una decisión estética, es aritmética. `StageLoader._try_append_bg`
#: **estira** cada capa a los 800×600 de la resolución interna, sea cual sea su
#: tamaño original, y el suelo del 4-1 está en la fila 30 de 38 — o sea a y=480
#: de los 608 px del mapa, que en pantalla cae sobre y≈476 de 600. Todo lo que
#: se dibuje por debajo de esa proporción queda **detrás de las baldosas del
#: terreno** y no lo ve nadie.
#:
#: Se deja un margen: 0,72 pone el horizonte del cementerio un poco por encima
#: del suelo que se pisa, que además es lo que hace que se lea como «el
#: cementerio sigue hacia el fondo» y no como una calcomanía a la misma altura.
CEM_HORIZONTE = 0.72


def _lapida(draw, x, base, ancho, alto, color):
    """Una lápida: el cuerpo y la cabeza redondeada."""
    draw.rectangle((x, base - alto, x + ancho, base), fill=color)
    draw.ellipse((x, base - alto - ancho // 2, x + ancho,
                  base - alto + ancho // 2), fill=color)


def _cruz(draw, x, base, alto, color):
    """Una cruz de las que se ven desde lejos: dos trazos y ya."""
    grosor = max(2, alto // 10)
    draw.rectangle((x, base - alto, x + grosor, base), fill=color)
    draw.rectangle((x - alto // 4, base - alto + grosor,
                    x + grosor + alto // 4, base - alto + grosor * 2),
                   fill=color)


# AUD-480 — pixel art de verdad, no vector plano escalado
# ============================================================
# Las tres capas de abajo (AUD-209) eran una silueta correcta pero
# dibujada directamente a la resolución final con las primitivas de PIL:
# eso da bordes lisos — vector plano, no pixel art, por mucho que el
# color sea sólido. El dueño lo señaló viendo el resultado (no se veía
# como las referencias que mandó: verja de hierro, arco con puerta,
# lápidas con "RIP" tallado, luna grande, árboles muertos).
#
# La técnica que sí se lee como pixel art: dibujar en un lienzo **chico**
# (`_ESCALA_PX` veces más pequeño que el final) y escalar hacia arriba
# con vecino más cercano (`Image.NEAREST`, nunca `BICUBIC`/`LANCZOS`) —
# así el bloque de píxel queda visible a propósito, que es lo que
# distingue el pixel art de un dibujo vectorial con colores planos.
_ESCALA_PX = 4

#: Fuente de bloque 3×5 para "RIP" tallado en las lápidas — un cuerpo de
#: letra por píxel del lienzo chico, nada de fuente TrueType: a esta
#: resolución una tipografía de verdad se volvería ilegible o pediría
#: anti-aliasing, que rompería el bloque de píxel del resto de la imagen.
_FUENTE_3X5 = {
    "R": ["111", "101", "111", "110", "101"],
    "I": ["111", "010", "010", "010", "111"],
    "P": ["111", "101", "111", "100", "100"],
}


def _texto_rip(draw, x, y, color):
    cursor = x
    for letra in "RIP":
        for fy, fila in enumerate(_FUENTE_3X5[letra]):
            for fx, bit in enumerate(fila):
                if bit == "1":
                    draw.point((cursor + fx, y + fy), fill=color)
        cursor += 4


def _luna_llena(draw, cx, cy, radio, rng):
    base, sombra = (232, 226, 190), (206, 198, 158)
    draw.ellipse((cx - radio, cy - radio, cx + radio, cy + radio), fill=base)
    for _ in range(6):
        ang = rng.uniform(0, math.tau)
        rad = rng.uniform(0, radio * 0.7)
        px, py = cx + math.cos(ang) * rad, cy + math.sin(ang) * rad
        cr = rng.uniform(1, max(2, radio * 0.14))
        draw.ellipse((px - cr, py - cr, px + cr, py + cr), fill=sombra)


def _nube_plana(draw, cx, cy, ancho, alto, color):
    draw.ellipse((cx - ancho, cy - alto, cx + ancho * 0.5, cy + alto), fill=color)
    draw.ellipse((cx - ancho * 0.3, cy - alto * 1.3, cx + ancho, cy + alto * 0.6),
                  fill=color)


def _arbol_muerto_px(draw, x, base, alto, color, semilla):
    """Árbol muerto ramificado — pura silueta, sin follaje: la Fase 1
    todavía no es el bosque cortado de la Fase 4."""
    r = random.Random(semilla)

    def rama(x, y, ang, largo):
        if largo < 3:
            return
        x2 = x + math.cos(ang) * largo
        y2 = y - math.sin(ang) * largo
        draw.line((x, y, x2, y2), fill=color, width=1)
        if largo > 5:
            rama(x2, y2, ang + r.uniform(0.4, 0.7), largo * 0.65)
            rama(x2, y2, ang - r.uniform(0.4, 0.7), largo * 0.65)

    rama(x, base, math.pi / 2 + r.uniform(-0.1, 0.1), alto)


def _verja_hierro(draw, x0, x1, base, alto, color, paso=5):
    """Verja de hierro forjado con punta de lanza — el elemento que más
    identifica las referencias del dueño, y el que más faltaba en la
    versión anterior (que sólo tenía barrotes verticales sin remate)."""
    draw.rectangle((x0, base - alto, x1, base - alto + 1), fill=color)
    draw.rectangle((x0, base - 2, x1, base - 1), fill=color)
    x = x0
    while x < x1:
        draw.line((x, base - alto, x, base), fill=color)
        draw.point((x, base - alto - 1), fill=color)
        x += paso


def _arco_con_puerta(draw, cx, base, ancho, alto, color, sombra, reja):
    """El arco de entrada, a juego con la verja: columnas con junta de
    mortero, medio círculo, y una puerta de barrotes en el hueco — no un
    arco vacío, que es lo que hacía el círculo de monolitos de la versión
    anterior (arte de un diseño de pozo que este pasillo ya no tiene)."""
    x0, x1 = cx - ancho // 2, cx + ancho // 2
    col_ancho = max(2, ancho // 7)
    for cxi, es_der in ((x0, False), (x1 - col_ancho, True)):
        draw.rectangle((cxi, base - alto, cxi + col_ancho, base), fill=color)
        if es_der:
            draw.rectangle((cxi + col_ancho - 1, base - alto, cxi + col_ancho, base),
                            fill=sombra)
    arco_r = ancho * 0.42
    cy = base - alto + arco_r
    draw.pieslice((cx - arco_r, cy - arco_r, cx + arco_r, cy + arco_r),
                  180, 360, fill=color)
    r_int = max(1, arco_r - col_ancho)
    draw.pieslice((cx - r_int, cy - r_int, cx + r_int, cy + r_int), 180, 360,
                  fill=CEM_CIELO_ALTO)
    x = int(cx - r_int + 1)
    while x < cx + r_int - 1:
        draw.line((x, cy, x, base), fill=reja)
        x += 2


def _lapida_con_texto(draw, x, base, ancho, alto, color, sombra, con_cruz=False):
    """Lápida con volumen (sombra plana a un lado, no degradado) y "RIP"
    o una cruz tallada — la pieza que más faltaba: la versión anterior
    dibujaba un rectángulo con la cabeza redonda y nada más."""
    top = base - alto
    redondeo = max(2, ancho // 3)
    draw.rectangle((x, top + redondeo, x + ancho, base), fill=color)
    draw.pieslice((x, top, x + ancho, top + redondeo * 2), 180, 360, fill=color)
    sw = max(1, ancho // 4)
    draw.rectangle((x + ancho - sw, top + redondeo, x + ancho, base), fill=sombra)
    if con_cruz:
        cx = x + ancho // 2
        draw.rectangle((cx, top + redondeo + 1, cx, base - 1), fill=(60, 56, 50))
        draw.rectangle((cx - 1, top + redondeo + 2, cx + 1, top + redondeo + 3),
                        fill=(60, 56, 50))
    else:
        _texto_rip(draw, x + max(1, (ancho - 12) // 2), top + redondeo + 2,
                   (60, 56, 50))


def _gen_bg_final_far(path, w=320, h=224):
    """Capa lejana: cielo, luna, nubes y colinas — pixel art de verdad
    (AUD-480): se dibuja a `_ESCALA_PX` veces menos resolución y se
    escala con vecino más cercano, así el bloque de píxel se ve.

    La luna **no se anima aquí**: la escena (`stage4_1.py`, ciclo de la
    Fase 5) la mueve por separado. Esta es la luna llena de fondo, visible
    en las fases donde no hay ciclo — coherente con las referencias, que
    la ponen grande y fija en el cielo.
    """
    _ensure(path)
    ew, eh = w // _ESCALA_PX, h // _ESCALA_PX
    img = Image.new("RGB", (ew, eh))
    draw = ImageDraw.Draw(img)
    rng = random.Random(410)
    horizonte = int(eh * CEM_HORIZONTE)

    for y in range(horizonte):
        t = y / max(horizonte - 1, 1)
        c = tuple(int(CEM_CIELO_ALTO[i] + (CEM_CIELO_BAJO[i] - CEM_CIELO_ALTO[i]) * t)
                   for i in range(3))
        draw.line((0, y, ew, y), fill=c)

    color_nube = (26, 20, 42)
    _nube_plana(draw, ew * 0.20, eh * 0.16, ew * 0.05, eh * 0.03, color_nube)
    _nube_plana(draw, ew * 0.68, eh * 0.10, ew * 0.06, eh * 0.04, color_nube)

    _luna_llena(draw, int(ew * 0.16), int(eh * 0.18), max(4, int(ew * 0.08)), rng)

    # Colinas: dos crestas, la de atrás más clara — profundidad sin capas
    # de más.
    for cresta, tinte in ((horizonte - eh * 0.09, (32, 25, 46)),
                          (horizonte, (20, 15, 32))):
        pts = [(0, eh)]
        for i in range(9):
            pts.append((i * ew // 8, cresta + rng.randint(-2, 2)))
        pts.append((ew, eh))
        draw.polygon(pts, fill=tinte)

    draw.rectangle((0, horizonte, ew, eh), fill=CEM_CIELO_BAJO)
    img.resize((w, h), Image.NEAREST).save(path)


def _gen_bg_final_mid(path, w=640, h=224):
    """Capa media: la verja de hierro y el arco de entrada — el elemento
    que más faltaba (AUD-480), calcado de las referencias del dueño."""
    _ensure(path)
    ew, eh = w // _ESCALA_PX, h // _ESCALA_PX
    img = Image.new("RGBA", (ew, eh), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    rng = random.Random(411)
    horizonte = int(eh * CEM_HORIZONTE)

    color_verja = (58, 84, 96)
    # Un arco por tramo de pantalla, para que se note recorriendo el
    # pasillo sin que la capa se lea vacía entre uno y otro.
    paso_arco = int(ew * 0.5)
    x = paso_arco // 2
    while x < ew:
        arco_x0, arco_x1 = x - 9, x + 9
        _verja_hierro(draw, max(0, x - paso_arco // 2 + 4), arco_x0,
                      horizonte + 6, 8, color_verja)
        _verja_hierro(draw, arco_x1, min(ew, x + paso_arco // 2 - 4),
                      horizonte + 6, 8, color_verja)
        _arco_con_puerta(draw, x, horizonte + 6, 19, 11,
                         (100, 108, 118), (70, 76, 86), color_verja)
        x += paso_arco

    # Lápidas pequeñas al fondo, entre los arcos.
    piedra = (78, 76, 90)
    piedra_sombra = (54, 52, 64)
    xi = 4
    while xi < ew:
        if rng.random() < 0.6:
            _lapida_con_texto(draw, xi, horizonte + 6, rng.randint(4, 6),
                              rng.randint(5, 8), piedra, piedra_sombra,
                              con_cruz=rng.random() < 0.4)
        xi += rng.randint(10, 16)

    draw.rectangle((0, horizonte + 6, ew, eh), fill=CEM_TIERRA)
    img.resize((w, h), Image.NEAREST).save(path)


def _gen_bg_final_near(path, w=960, h=224):
    """Capa cercana: lápidas con "RIP" tallado, árboles muertos y el
    suelo de pasto sobre tierra — pixel art de verdad (AUD-480)."""
    _ensure(path)
    ew, eh = w // _ESCALA_PX, h // _ESCALA_PX
    img = Image.new("RGBA", (ew, eh), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    rng = random.Random(412)
    horizonte = int(eh * CEM_HORIZONTE)

    color_arbol = (12, 10, 18)
    for x in range(20, ew, 90):
        _arbol_muerto_px(draw, x, horizonte + 2, rng.randint(14, 20),
                         color_arbol, x)

    piedra = (150, 148, 140)
    piedra_sombra = (108, 106, 100)
    x = 6
    while x < ew:
        ancho, alto = rng.randint(9, 13), rng.randint(9, 15)
        _lapida_con_texto(draw, x, horizonte + 4, ancho, alto, piedra,
                          piedra_sombra, con_cruz=rng.random() < 0.35)
        x += rng.randint(26, 42)

    pasto_alto = max(2, int(eh * 0.05))
    draw.rectangle((0, horizonte + 4, ew, horizonte + 4 + pasto_alto),
                    fill=(46, 92, 40))
    draw.rectangle((0, horizonte + 4, ew, horizonte + 5), fill=(58, 110, 50))
    draw.rectangle((0, horizonte + 4 + pasto_alto, ew, eh), fill=CEM_TIERRA)

    img.resize((w, h), Image.NEAREST).save(path)


# ── Splash/title/story backgrounds ──

def _gen_bg_splash(path, w=320, h=224):
    """Splash screen: dark atmospheric gradient."""
    _ensure(path)
    img = Image.new("RGB", (w, h))
    draw = ImageDraw.Draw(img)
    for y in range(h):
        t = y / h
        r = int(10 + t * 5)
        g = int(8 + t * 4)
        b = int(25 + t * 15)
        draw.line((0, y, w - 1, y), fill=(r, g, b))
    # Radial glow at center
    cx, cy = w // 2, h // 2
    for rad in range(100, 0, -5):
        alpha = max(0, 30 - (100 - rad))
        glow = Image.new("RGBA", (rad * 2, rad * 2), (0, 0, 0, 0))
        c = int(15 * (1 - rad / 100))
        ImageDraw.Draw(glow).ellipse((0, 0, rad * 2, rad * 2),
                                     fill=(40 + c, 30 + c, 60 + c, alpha))
        img.paste(glow, (cx - rad, cy - rad), glow)
    img.save(path)


def _gen_bg_title(path, w=320, h=224):
    """Title screen: dramatic gradient with light rays."""
    _ensure(path)
    img = Image.new("RGB", (w, h))
    draw = ImageDraw.Draw(img)
    rng = random.Random(7)
    for y in range(h):
        t = y / h
        r = int(15 + t * 30)
        g = int(10 + t * 20)
        b = int(35 + t * 45)
        draw.line((0, y, w - 1, y), fill=(r, g, b))
    # Light rays from top center
    for _i in range(6):
        angle = rng.uniform(-0.4, 0.4)
        x_off = int(math.tan(angle) * h * 0.6)
        cx = w // 2
        for y in range(0, h, 4):
            t = y / h
            x = int(cx + x_off * t)
            alpha = int(20 * (1 - t))
            for dx in range(-2, 3):
                px = x + dx
                if 0 <= px < w:
                    rp, gp, bp = img.getpixel((px, y))
                    img.putpixel((px, y), (min(255, rp + alpha),
                                           min(255, gp + alpha),
                                           min(255, bp + alpha)))
    img.save(path)


def _gen_bg_story(path, w=320, h=224):
    """Story screen: dark mysterious."""
    _ensure(path)
    img = Image.new("RGB", (w, h))
    draw = ImageDraw.Draw(img)
    for y in range(h):
        t = y / h
        r = int(5 + t * 12)
        g = int(4 + t * 8)
        b = int(18 + t * 25)
        draw.line((0, y, w - 1, y), fill=(r, g, b))
    # Subtle fog bands
    rng = random.Random(13)
    for _ in range(4):
        fy = rng.randint(40, 180)
        rng.randint(60, 120)
        for y in range(fy, min(fy + 20, h)):
            t = (y - fy) / 20
            alpha = int(15 * (1 - abs(t - 0.5) * 2))
            draw.line((0, y, w - 1, y), fill=(alpha + 5, alpha + 4, alpha + 18))
    img.save(path)


BG_ZONES = {
    "zone1": [(40,70,30), (20,40,15)],
    "zone2": [(70,50,40), (40,30,20)],
    "zone3": [(80,60,90), (40,30,50)],
    "final": [(15,10,30), (10,5,20)],
}

def _gen_procedural_bg(path, w, h, top, bot, has_mountains=True, has_trees=True):
    _ensure(path)
    img = _gradient(w, h, top, bot)
    draw = ImageDraw.Draw(img)
    n = _noise(w, h, scale=16)
    _apply_noise(img, n, strength=12)
    if has_mountains:
        pts = [(0, h)]
        for i in range(12):
            pts.append((i * w // 11, 100 + random.randint(-20, 20)))
        pts.append((w, h))
        draw.polygon(pts, fill=(max(0,top[0]-20), max(0,top[1]-20), max(0,top[2]-20)))
    if has_trees:
        for i in range(8):
            tx = i * 45 + random.randint(-10, 10)
            ty = h - 30 - random.randint(0, 10)
            draw.rectangle((tx-2, ty-10, tx+2, ty), fill=(40,30,10))
            for r in range(10, 3, -2):
                draw.ellipse((tx-r, ty-12-r, tx+r, ty-12+r), fill=(r*5, r*8+20, r*3))
    img.save(path)

BG_SIZES = {"far": (W, H), "mid": (W*2, H), "near": (W*3, H)}

def _gen_all_backgrounds():
    print("  Backgrounds...")
    # Stage 0 gothic parallax
    for layer, (bw, bh) in BG_SIZES.items():
        p = A / "backgrounds" / "stage0"
        _ensure(p)
        if layer == "far":
            _gen_bg_stage0_far(p / "bg_stage0_far.png", bw, bh)
        elif layer == "mid":
            _gen_bg_stage0_mid(p / "bg_stage0_mid.png", bw, bh)
        else:
            _gen_bg_stage0_near(p / "bg_stage0_near.png", bw, bh)

    # Zona Final: el cementerio, a mano como el stage0 (ver AUD-209).
    for layer, (bw, bh) in BG_SIZES.items():
        p = A / "backgrounds" / "final"
        _ensure(p)
        if layer == "far":
            _gen_bg_final_far(p / "bg_final_far.png", bw, bh)
        elif layer == "mid":
            _gen_bg_final_mid(p / "bg_final_mid.png", bw, bh)
        else:
            _gen_bg_final_near(p / "bg_final_near.png", bw, bh)

    # Other zones (procedural)
    for zone, (top, bot) in BG_ZONES.items():
        if zone == "final":
            continue
        for layer, (bw, bh) in BG_SIZES.items():
            p = A / "backgrounds" / zone
            _ensure(p)
            _gen_procedural_bg(p / f"bg_{zone}_{layer}.png", bw, bh, top, bot,
                    has_mountains=zone in ("stage0","zone1","zone3"),
                    has_trees=zone in ("stage0","zone1","zone2"))

    # Splash / title / story
    p = A / "backgrounds"
    _ensure(p)
    _gen_bg_splash(p / "bg_splash.png", W, H)
    _gen_bg_title(p / "bg_title.png", W, H)
    _gen_bg_story(p / "bg_story.png", W, H)

# ════════════════════════════════════════
# SECTION 6: UI SPRITES
# ════════════════════════════════════════

def _gen_ui_portraits():
    print("  UI portraits...")
    ui = A / "ui"
    states = {
        "portrait_normal.png": (220, 180, 140),
        "portrait_hurt.png": (200, 120, 100),
        "portrait_critical.png": (200, 80, 80),
        "portrait_dead.png": (100, 100, 100),
    }
    for fname, color in states.items():
        img = Image.new("RGBA", (32, 32), (0,0,0,0))
        draw = ImageDraw.Draw(img)
        draw.ellipse((4, 2, 28, 20), fill=color)
        draw.rectangle((8, 18, 24, 30), fill=(60, 60, 80))
        draw.ellipse((10, 8, 14, 12), fill=(255,255,255))
        draw.ellipse((18, 8, 22, 12), fill=(255,255,255))
        draw.ellipse((10, 8, 13, 11), fill=(0,0,0))
        draw.ellipse((18, 8, 21, 11), fill=(0,0,0))
        img.save(ui / fname)

def _gen_dialogue_portraits():
    print("  Dialogue portraits (animados)...")
    dest = A / "sprites" / "portraits"
    dest.mkdir(parents=True, exist_ok=True)
    # Paletas por personaje — 4 frames cada uno (idle/habla/media/boca abierta + blink)
    personajes = {
        "eco": (220, 180, 120),
        "jhon": (180, 200, 220),
        "jill": (220, 160, 180),
        "venado": (180, 220, 160),
        "rey_terciopelo": (140, 180, 220),
        "gavilan": (210, 190, 140),
        "paburu": (200, 160, 120),
        "narrador": (200, 200, 200),
    }
    for nombre, base in personajes.items():
        # 4 frames horizontales, cada uno 48x48 — PSX 32-bit con outline 1px + sombra dithered
        strip = Image.new("RGBA", (48 * 4, 48), (0, 0, 0, 0))
        for i in range(4):
            d = ImageDraw.Draw(strip)
            x0 = i * 48
            # Fondo cara con highlight 1px PSX
            d.ellipse((x0 + 4, 4, x0 + 44, 36), fill=base, outline=(40, 40, 60))
            highlight = tuple(min(255, c + 30) for c in base)
            d.arc((x0 + 4, 4, x0 + 44, 36), 200, 340, fill=highlight)
            # Ojos
            if i == 3:  # blink
                d.line((x0 + 12, 16, x0 + 20, 16), fill=(20, 20, 30), width=2)
                d.line((x0 + 28, 16, x0 + 36, 16), fill=(20, 20, 30), width=2)
            else:
                d.ellipse((x0 + 12, 14, x0 + 20, 20), fill=(255, 255, 255))
                d.ellipse((x0 + 28, 14, x0 + 36, 20), fill=(255, 255, 255))
                d.ellipse((x0 + 14, 15, x0 + 18, 19), fill=(20, 20, 30))
                d.ellipse((x0 + 30, 15, x0 + 34, 19), fill=(20, 20, 30))
                # Brillo
                d.ellipse((x0 + 16, 16, x0 + 18, 18), fill=(255, 255, 255))
                d.ellipse((x0 + 32, 16, x0 + 34, 18), fill=(255, 255, 255))
            # Boca según frame
            if i == 0:  # cerrado idle
                d.line((x0 + 18, 30, x0 + 30, 30), fill=(80, 40, 40), width=2)
            elif i == 1:  # medio
                d.ellipse((x0 + 18, 28, x0 + 30, 33), fill=(90, 50, 50), outline=(60, 30, 30))
            elif i == 2:  # abierto
                d.ellipse((x0 + 16, 27, x0 + 32, 34), fill=(120, 60, 60), outline=(60, 30, 30))
                d.rectangle((x0 + 20, 30, x0 + 28, 32), fill=(240, 220, 220))
            else:  # blink también boca cerrada
                d.line((x0 + 18, 30, x0 + 30, 30), fill=(80, 40, 40), width=2)
        # PSX outline 1px + sombra dithered por frame
        for i in range(4):
            sub = strip.crop((i * 48, 0, (i + 1) * 48, 48))
            _psx_outline_y_sombra(sub)
            strip.paste(sub, (i * 48, 0))
        strip.save(dest / f"{nombre}.png")
        # También guarda versión 1-frame estática para compatibilidad vieja
        # (el primer frame como archivo separado si alguien usa eco.png)
        # No necesario: el sistema soporta 1 frame del mismo archivo.
        # Para aliases comunes
        for alias in [f"{nombre}_normal", f"{nombre}_habla"]:
            strip.save(dest / f"{alias}.png")
    # Genérico fallback
    fallback = Image.new("RGBA", (48 * 4, 48), (0, 0, 0, 0))
    for i in range(4):
        d = ImageDraw.Draw(fallback)
        x0 = i * 48
        d.rectangle((x0 + 2, 2, x0 + 46, 46), fill=(180, 180, 180), outline=(80, 80, 90))
        d.text((x0 + 14, 18), "?", fill=(40, 40, 60))
    fallback.save(dest / "placeholder.png")
    fallback.save(dest / "default.png")

def _gen_ui_banners():
    # AUD-526 — cada mitad se dibujaba como un rectángulo cerrado en las
    # cuatro caras (`draw.rectangle(..., outline=...)`). `ScreenBanner.draw`
    # las pega una encima de otra sin hueco (`banner_bottom` empieza justo
    # donde termina `banner_top`), así que el borde inferior de la mitad de
    # arriba y el borde superior de la mitad de abajo caían en la misma
    # fila de píxeles: una línea doble exactamente donde se centra el
    # nombre del escenario — se leía como texto tachado. Cada mitad dibuja
    # ahora sólo sus tres lados exteriores (arriba+izq+der la de arriba,
    # abajo+izq+der la de abajo); la costura del medio queda sin trazo.
    print("  UI banners...")
    ui = A / "ui"
    color = (200, 180, 100, 200)
    top = Image.new("RGBA", (W, 24), (0, 0, 0, 180))
    d = ImageDraw.Draw(top)
    d.line([(0, 0), (W - 1, 0)], fill=color, width=1)
    d.line([(0, 0), (0, 23)], fill=color, width=1)
    d.line([(W - 1, 0), (W - 1, 23)], fill=color, width=1)
    top.save(ui / "banner_top.png")

    bottom = Image.new("RGBA", (W, 24), (0, 0, 0, 180))
    d = ImageDraw.Draw(bottom)
    d.line([(0, 23), (W - 1, 23)], fill=color, width=1)
    d.line([(0, 0), (0, 23)], fill=color, width=1)
    d.line([(W - 1, 0), (W - 1, 23)], fill=color, width=1)
    bottom.save(ui / "banner_bottom.png")

def _gen_ui_misc():
    print("  UI misc...")
    ui = A / "ui"

    # AUD-527 — `hud_frame.png` era un relleno plano con un borde de 1 px
    # blanco: exactamente lo que rompe la decisión del dueño de modernizar
    # el HUD. El panel ahora lleva un degradado vertical (más claro arriba,
    # como si lo iluminara una fuente por encima, no una plancha uniforme) y
    # un halo suave alrededor del borde — dibujado a 4x y reducido con
    # remuestreo para que el degradado y el halo salgan antialiased de
    # verdad, no en escalones de píxel. `hud.py` sigue troceándolo en
    # 9-slice con el mismo tamaño de esquina de siempre: sólo cambia lo que
    # hay dentro de cada trozo.
    fw, fh, ss = 36, 36, 4
    w, h = fw * ss, fh * ss
    claro, oscuro = (82, 84, 118), (32, 32, 52)
    fondo = Image.new("RGBA", (w, h))
    fd = ImageDraw.Draw(fondo)
    for y in range(h):
        t = y / max(1, h - 1)
        col = tuple(int(claro[i] + (oscuro[i] - claro[i]) * t) for i in range(3))
        fd.line([(0, y), (w, y)], fill=(*col, 235))
    halo_alfa = Image.new("L", (w, h), 0)
    ImageDraw.Draw(halo_alfa).rectangle(
        (0, 0, w - 1, h - 1), outline=255, width=ss * 2)
    halo_alfa = halo_alfa.filter(ImageFilter.GaussianBlur(ss))
    halo = Image.new("RGBA", (w, h), (150, 160, 220, 0))
    halo.putalpha(halo_alfa)
    panel = Image.alpha_composite(fondo, halo)
    panel = panel.resize((fw, fh), Image.LANCZOS)
    panel.save(ui / "hud_frame.png")

    items = {
        "message_arrow.png": (5, 7, (255, 215, 0)),
        "menu_arrow.png": (5, 8, (255, 215, 0)),
    }
    for fname, (fw, fh, color) in items.items():
        img = Image.new("RGBA", (fw, fh), (0,0,0,0))
        draw = ImageDraw.Draw(img)
        draw.rectangle((0, 0, fw-1, fh-1), fill=color, outline=(255,255,255))
        img.save(ui / fname)

    # Relic icons
    relics = {
        "relic_pepita.png": (8, 6, (255, 215, 0)),
        "relic_perla.png": (7, 7, (0, 0, 0)),
        "relic_fragment1.png": (12, 12, (200, 200, 150)),
        "relic_fragment2.png": (12, 12, (100, 180, 100)),
        "relic_fragment3.png": (12, 12, (200, 150, 100)),
    }
    for fname, (fw, fh, color) in relics.items():
        img = Image.new("RGBA", (fw, fh), (0,0,0,0))
        draw = ImageDraw.Draw(img)
        draw.rectangle((0, 0, fw-1, fh-1), fill=color, outline=(255,255,255))
        img.save(ui / fname)

def _gen_bitmap_font(path, label, cw, char_height, chars, color=(200, 200, 200)):
    _ensure(path)
    total = len(chars)
    img = Image.new("RGBA", (cw * total, char_height), (0,0,0,0))
    draw = ImageDraw.Draw(img)
    for i, ch in enumerate(chars):
        ox = i * cw
        draw.rectangle((ox+1, 1, ox+cw-2, char_height-2), fill=color, outline=(255,255,255,80))
        draw.text((ox+2, 1), ch, fill=(255,255,255), font=None)
    img.save(path)

def _gen_ui_fonts():
    print("  UI fonts...")
    fdir = A / "fonts"
    _ensure(fdir)
    _gen_bitmap_font(fdir / "hud_digits.png", "digits", 6, 8, "0123456789: ")
    _gen_bitmap_font(fdir / "message_font.png", "msg", 5, 7, "".join(chr(i) for i in range(32,127)))
    _gen_bitmap_font(fdir / "banner_large.png", "banner_large", 10, 14, "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 ")
    _gen_bitmap_font(fdir / "banner_medium.png", "banner_med", 6, 9, "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 .:-")
    _gen_bitmap_font(fdir / "gameover_font.png", "gameover", 12, 16, "ABCDEFGHIJKLMNOPQRSTUVWXYZ ")
    _gen_bitmap_font(fdir / "menu_font.png", "menu", 6, 9, "".join(chr(i) for i in range(32,127)))

# ════════════════════════════════════════
# SECTION 7: SHARED SPRITES
# ════════════════════════════════════════

def _gen_shared():
    print("  Shared sprites...")
    sd = A / "sprites" / "shared"
    _ensure(sd)
    # AUD-522 — `checkpoint.png` generaba el poste con farol que
    # `Checkpoint` ya no dibuja: el haz de luz (`LightSource`) reemplazó
    # el sprite en los 26 escenarios, no sólo en 4.1b/4.1c (AUD-517 lo
    # dejó opt-in; el dueño pidió el reemplazo completo). El archivo se
    # borró del repositorio junto con este bloque.

    # Torch (8x16, 4 frames) PSX con outline 1px + sombra dithered y brillo 1px
    imgs = []
    for f in range(4):
        img = Image.new("RGBA", (8, 16), (0,0,0,0))
        draw = ImageDraw.Draw(img)
        draw.rectangle((3, 10, 5, 16), fill=(60, 40, 20))
        flame = [(255, 200, 50), (255, 150, 30), (200, 100, 20), (150, 80, 10)][f]
        draw.ellipse((1, 2, 7, 12), fill=flame)
        # Brillo 1px arriba del flame
        draw.point((4, 3), fill=(255, 255, 200))
        # Sombra dithered base
        for x in range(1, 7):
            if BAYER_4X4[12 % 4][x % 4] < 8:
                draw.point((x, 12), fill=tuple(max(0, c - 18) for c in flame))
        _psx_outline_y_sombra(img)
        imgs.append(img)
    _save_sheet(sd / "torch_anim.png", imgs, 8, 16)

# ════════════════════════════════════════
# SECTION 8: MUSIC (12 tracks)
# ════════════════════════════════════════

def _square(freq, t, duty=0.5):
    return 1.0 if ((t * freq) % 1.0) < duty else -1.0

def _saw(freq, t):
    return 2.0 * ((t * freq) % 1.0) - 1.0

def _tri(freq, t):
    p = 2.0 * ((t * freq) % 1.0)
    return 2.0 * abs(p - 1.0) - 1.0

# AUD-546 — síntesis procedural para las tres "recetas" del dueño
# (`crujido_seco`, `rafaga_viento`, `impacto_tension`). El resto de este
# fichero ya sintetiza ruido filtrado a mano con un paso-bajo de un polo
# (`anterior = anterior*a + crudo*(1-a)`, repetido en línea en
# `rain_ambient`/`storm_ambient`/etc.); estas tres funciones factorizan
# ese mismo principio para poder pedirle un pasa-altos, un corte que
# cambia por muestra (el barrido del viento) y ruido rosa, que ninguna
# de las recetas anteriores necesitaba.


def _pasa_altos(muestras, corte_hz, rate=SAMPLE_RATE):
    """Pasa-altos de un polo — sólo dejar pasar por encima de `corte_hz`.

    AUD-546 — el pedido original dice *"aleatoriza el corte... cada vez
    que lo llamas por script"*, es decir, en tiempo de reproducción. Este
    motor no tiene DSP en tiempo real (`_aplicar_reverberacion` explica
    la misma limitación para la reverberación): el `.wav` se hornea una
    vez. `corte_hz` sí se aleatoriza en **tiempo de generación**
    (`crujido_seco` sortea el corte antes de llamar aquí), que es lo más
    cerca de "que ningún crujido suene igual" que permite hornear un
    fichero fijo.
    """
    if not muestras:
        return []
    rc = 1.0 / (2.0 * math.pi * max(1.0, corte_hz))
    dt = 1.0 / rate
    alfa = rc / (rc + dt)
    salida = [0.0] * len(muestras)
    salida[0] = muestras[0]
    for i in range(1, len(muestras)):
        salida[i] = alfa * (salida[i - 1] + muestras[i] - muestras[i - 1])
    return salida


def _paso_pasa_bajos(muestra, estado_anterior, corte_hz, rate=SAMPLE_RATE):
    """Un paso de pasa-bajos de un polo, con `corte_hz` que puede cambiar
    muestra a muestra — lo que necesita `rafaga_viento` para el barrido
    del filtro (300→1200→300Hz), y que el patrón habitual de este
    fichero (coeficiente fijo `anterior*a + crudo*(1-a)`) no permite sin
    recalcular `a` en cada llamada."""
    rc = 1.0 / (2.0 * math.pi * max(1.0, corte_hz))
    dt = 1.0 / rate
    alfa = dt / (rc + dt)
    return estado_anterior + alfa * (muestra - estado_anterior)


def _ruido_rosa(n, rng=random):
    """Ruido rosa — el filtro económico de tres polos de Paul Kellet, la
    aproximación estándar que no necesita FFT. Más natural que el ruido
    blanco puro (menos energía en los agudos estridentes), que es
    exactamente lo que pide la receta de la ráfaga de viento."""
    b0 = b1 = b2 = 0.0
    salida = []
    for _ in range(n):
        blanco = rng.uniform(-1.0, 1.0)
        b0 = 0.99765 * b0 + blanco * 0.0990460
        b1 = 0.96300 * b1 + blanco * 0.2965164
        b2 = 0.57000 * b2 + blanco * 1.0526913
        salida.append((b0 + b1 + b2 + blanco * 0.1848) * 0.2)
    return salida


def _recorte_suave(x):
    """Saturación suave (soft clipping) vía tangente hiperbólica — el
    "golpe percusivo" que pide `impacto_tension` para sus primeros
    100ms, sin el escalón duro de un recorte dígital (`max(-1, min(1,
    x))`)."""
    return math.tanh(x)


def _aplicar_reverberacion(samples, rate=SAMPLE_RATE, decaimiento=0.55,
                            retardo_ms=45.0, ecos=6, cola_extra_s=1.2):
    """Reverberación horneada en el propio clip (AUD-515, GAP-058).

    El mezclador de este motor (SDL mixer) no tiene DSP en tiempo real: no
    hay un nudo de «reverb de zona» al que conectar un sonido y que lo
    devuelva con eco. GAP-058 lo señala para el silencio súbito de la
    Fase 4 del 4-1 —*«el silencio se resuelve bajando el clima y las
    partículas a cero, no con una reverberación que se apaga»*— y hasta
    ahora se dejaba así, sin fecha, por asumir que hacía falta DSP de
    verdad.

    No hace falta. Todo el audio de este proyecto ya se genera por código
    (`_gen_sfx`), así que la reverberación se puede **hornear en el propio
    `.wav`**: varias copias del sonido, retrasadas y cada vez más flojas,
    sumadas por encima del original — el mismo principio que un comb
    filter, la base de cualquier reverberación algorítmica, sólo que
    calculado una vez al generar en vez de en tiempo real. El resultado es
    más largo que el original (`cola_extra_s` de silencio al final para que
    el último eco no se corte).
    """
    retardo_muestras = max(1, int(rate * retardo_ms / 1000.0))
    cola_muestras = int(rate * cola_extra_s)
    salida = list(samples) + [0.0] * cola_muestras
    ganancia = 1.0
    for eco in range(1, ecos + 1):
        ganancia *= decaimiento
        offset = retardo_muestras * eco
        for i, s in enumerate(samples):
            idx = i + offset
            if idx < len(salida):
                salida[idx] += s * ganancia
    return salida


def _write_wav(path, samples, rate=SAMPLE_RATE):
    _ensure(path)
    mx = max(abs(s) for s in samples) or 1.0
    norm = [int(s / mx * 16383) for s in samples]
    with wave.open(str(path), "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(rate)
        wf.writeframes(struct.pack(f"<{len(norm)}h", *norm))


def _write_wav_stereo(path, izquierda, derecha, rate=SAMPLE_RATE):
    """AUD-546 — el único `.wav` de dos canales de este proyecto: el
    paneo de `rafaga_viento` es el propio pedido (*"panea... para que se
    sienta que el viento atraviesa el mapa"*), y un paneo de verdad
    necesita dos canales — `_write_wav` sólo escribe mono. Normaliza los
    dos canales **juntos**, no cada uno por separado: normalizarlos
    aparte rompería el balance relativo entre izquierda y derecha que es
    lo que hace el paneo audible.
    """
    _ensure(path)
    mx = max(
        max((abs(s) for s in izquierda), default=0.0),
        max((abs(s) for s in derecha), default=0.0),
    ) or 1.0
    n = min(len(izquierda), len(derecha))
    entrelazado = []
    for i in range(n):
        entrelazado.append(int(izquierda[i] / mx * 16383))
        entrelazado.append(int(derecha[i] / mx * 16383))
    with wave.open(str(path), "w") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(rate)
        wf.writeframes(struct.pack(f"<{len(entrelazado)}h", *entrelazado))


def _mix(*tracks):
    n = max(len(t) for t in tracks) if tracks else 0
    r = [0.0] * n
    for t in tracks:
        for i in range(len(t)):
            r[i] += t[i]
    return r

MUSIC_DEFS = {
    "bgm_splash": {"bpm": 80, "dur": 8, "notes": [110, 130.81, 164.81, 220], "desc": "ambient"},
    "bgm_title": {"bpm": 130, "dur": 12, "notes": [440, 523.25, 587.33, 659.25], "desc": "heroic"},
    "bgm_story": {"bpm": 70, "dur": 10, "notes": [261.63, 329.63, 392, 523.25], "desc": "mysterious"},
    "bgm_stage0": {"bpm": 110, "dur": 10, "notes": [220, 261.63, 293.66, 349.23], "desc": "tense"},
    "bgm_zone1_traverse": {"bpm": 120, "dur": 12, "notes": [196, 246.94, 293.66, 369.99], "desc": "jungle"},
    "bgm_zone1_boss": {"bpm": 100, "dur": 12, "notes": [174.61, 220, 261.63, 329.63], "desc": "ancient"},
    "bgm_zone2_traverse": {"bpm": 130, "dur": 12, "notes": [130.81, 164.81, 196, 246.94], "desc": "industrial"},
    "bgm_zone2_boss": {"bpm": 90, "dur": 12, "notes": [110, 146.83, 185, 220], "desc": "ominous"},
    "bgm_zone3_traverse": {"bpm": 140, "dur": 12, "notes": [349.23, 440, 523.25, 659.25], "desc": "aerial"},
    "bgm_zone3_boss": {"bpm": 110, "dur": 12, "notes": [293.66, 369.99, 440, 554.37], "desc": "ceremonial"},
    # AUD-227: esta fila ya no se usa para generar el audio — `_gen_all_music`
    # desvía `bgm_final_approach` a `_gen_bgm_organo`, porque la ficha del 4-1 y
    # el Asset Bible piden un órgano y el generador genérico hace chiptune. Se
    # deja para que la tabla siga listando los doce temas y para no perder los
    # valores originales si alguien quiere comparar.
    "bgm_final_approach": {"bpm": 60, "dur": 10, "notes": [65.41, 82.41, 98, 130.81], "desc": "ritual (generado por _gen_bgm_organo)"},
    "bgm_paburu": {"bpm": 140, "dur": 16, "notes": [110, 146.83, 185, 220, 293.66, 369.99], "desc": "epic"},
}

def _gen_music_track(name, defn):
    rate = SAMPLE_RATE
    dur = defn["dur"]
    n = int(rate * dur)
    bpm = defn["bpm"]
    beat = 60.0 / bpm
    notes = defn["notes"]
    
    bass = [0.0] * n
    melody = [0.0] * n
    perc = [0.0] * n
    pad = [0.0] * n
    
    for i in range(n):
        t = i / rate
        note_idx = int(t / (beat * 2)) % len(notes)
        freq = notes[note_idx]
        bass[i] = _square(freq / 2, t, 0.5) * 0.15
        env = max(0, 1 - (t % (beat * 2)) / (beat * 2))
        melody[i] = _square(freq * 2, t, 0.3) * 0.08 * env
        pad[i] = _tri(freq, t) * 0.04
        
        bp = t % beat
        if bp < 0.02:
            perc[i] = random.uniform(-0.2, 0.2)
        elif bp > beat * 0.5 and bp < beat * 0.5 + 0.015:
            if int(t / beat) % 2 == 1:
                perc[i] = random.uniform(-0.1, 0.1)
    
    result = _mix(bass, melody, perc, pad)
    fade = int(rate * 0.3)
    for i in range(fade):
        f = i / fade
        result[i] *= f
        result[n - 1 - i] *= f
    return result

# ── El órgano del cementerio (AUD-227) ──
#
# `_gen_music_track` es un chiptune: onda cuadrada, saw, triangular y ruido
# blanco de percusión. Sirve para los diez temas que lo usan y no sirve para
# éste. La ficha del 4-1 y el Asset Bible piden un órgano —el nivel es una
# procesión por un cementerio— y lo que sonaba eran tambores de onda cuadrada.
#
# Un órgano de tubos no se imita con una envolvente: **es** síntesis aditiva. Un
# registro es un tubo que suena a un múltiplo entero de la fundamental, y tirar
# de varios a la vez es sumar senos. Por eso esto no es un truco para que «suene
# parecido»: es como funciona el instrumento.
#
# Los seis registros son los clásicos de un principal:
#   1×  Principal 8'      la nota
#   2×  Octava 4'         una octava arriba
#   3×  Quinta 2 2/3'     la duodécima — lo que da el color «de iglesia»
#   4×  Superoctava 2'
#   6×  Larigot 1 1/3'
#   8×  Flautín 1'
ORGANO_REGISTROS: tuple[tuple[int, float], ...] = (
    (1, 1.00), (2, 0.50), (3, 0.30), (4, 0.25), (6, 0.12), (8, 0.10),
)

#: La progresión, en re menor: i – VI – III – v. Es la cadencia de procesión de
#: toda la música fúnebre occidental, y re menor es la tonalidad del órgano por
#: antonomasia. Cada acorde son sus tres notas en hercios; el pedal va aparte.
ORGANO_ACORDES: tuple[tuple[float, ...], ...] = (
    (73.42, 87.31, 110.00),    # Dm  — D2  F2  A2
    (58.27, 73.42, 87.31),     # Bb  — Bb1 D2  F2
    (87.31, 110.00, 130.81),   # F   — F2  A2  C3
    (55.00, 65.41, 82.41),     # Am  — A1  C2  E2
)

#: El pedal: la fundamental una octava por debajo. Es el registro de 16' y es lo
#: que hace que un órgano se sienta en el pecho en vez de oírse en la oreja.
ORGANO_PEDAL: tuple[float, ...] = (36.71, 29.14, 43.65, 27.50)

#: Segundos por acorde. Cuatro, y no menos: un órgano no se apresura, y el
#: silencio entre cambios es la mitad del efecto.
ORGANO_COMPAS = 4.0


def _gen_bgm_organo(dur=16.0, rate=SAMPLE_RATE):
    """El tema del 4-1: órgano de tubos, sin percusión y sin prisa.

    Sin percusión a propósito. La ficha dice que en este nivel *«el silencio es
    el jefe»*, y una caja de ritmos debajo convierte una procesión en un nivel
    de acción. Lo único que se mueve es el trémolo, que en un órgano real es un
    registro más.
    """
    import numpy as np

    n = int(rate * dur)
    t = np.arange(n, dtype=np.float64) / rate
    salida = np.zeros(n, dtype=np.float64)

    # El trémolo: un 6 % de variación a 4,8 Hz. Más y suena a sirena; menos y no
    # se nota que el aire está vivo.
    tremulo = 1.0 + 0.06 * np.sin(2.0 * np.pi * 4.8 * t)

    for compas in range(int(dur / ORGANO_COMPAS)):
        acorde = ORGANO_ACORDES[compas % len(ORGANO_ACORDES)]
        pedal = ORGANO_PEDAL[compas % len(ORGANO_PEDAL)]
        i0 = int(compas * ORGANO_COMPAS * rate)
        i1 = min(n, int((compas + 1) * ORGANO_COMPAS * rate))
        if i1 <= i0:
            continue
        tramo = t[i0:i1]
        voz = np.zeros(i1 - i0, dtype=np.float64)
        for freq in (*acorde, pedal):
            peso = 0.9 if freq == pedal else 0.55
            for armonico, amplitud in ORGANO_REGISTROS:
                # El pedal sólo lleva los registros graves: con los agudos se
                # embarra la mezcla y deja de leerse como un bajo.
                if freq == pedal and armonico > 3:
                    continue
                voz += np.sin(2.0 * np.pi * freq * armonico * tramo) * amplitud * peso

        # El «habla» del tubo: 60 ms para llenarse de aire y 200 para vaciarse.
        # Sin esto el acorde entra con un chasquido, que es el ruido que delata
        # a un órgano sintetizado.
        ataque = min(len(voz), int(rate * 0.06))
        caida = min(len(voz) - ataque, int(rate * 0.20))
        if ataque > 0:
            voz[:ataque] *= np.linspace(0.0, 1.0, ataque)
        if caida > 0:
            voz[-caida:] *= np.linspace(1.0, 0.0, caida)
        salida[i0:i1] += voz * tremulo[i0:i1]

    # El soplo del fuelle, muy por debajo: un órgano nunca está en silencio del
    # todo mientras el motor está encendido.
    aire = np.random.default_rng(4127).normal(0.0, 1.0, n)
    for _ in range(6):          # suavizado: ruido blanco filtrado a marrón
        aire = np.convolve(aire, np.ones(64) / 64.0, mode="same")
    salida += aire / (np.max(np.abs(aire)) or 1.0) * 0.05

    fundido = int(rate * 0.4)
    salida[:fundido] *= np.linspace(0.0, 1.0, fundido)
    salida[-fundido:] *= np.linspace(1.0, 0.0, fundido)
    return salida.tolist()


def _gen_all_music():
    print("  Music...")
    mdir = A / "music"
    _ensure(mdir)
    for name, defn in MUSIC_DEFS.items():
        if name == "bgm_final_approach":
            samples = _gen_bgm_organo()
        else:
            samples = _gen_music_track(name, defn)
        _write_wav(mdir / f"{name}.wav", samples)

# ════════════════════════════════════════
# SECTION 9: SOUND EFFECTS
# ════════════════════════════════════════

SFX_CATEGORIES = {
    "player": ["jump", "land", "short_attack", "long_attack", "hit_connect", "hurt", "die", "crouch",
               # AUD-522 — el musgo resbala y hasta ahora no se oía.
               "footstep_musgo",
               # AUD-551 — GAP-070 punto 1: el lodo frenaba de verdad y
               # sonaba igual que tierra firme.
               "footstep_lodo",
               # AUD-554 — GAP-070 "Pasos sobre Tierra/Grava" (Fase 1) y
               # "Pasos Ahogados" (Fase 5): las dos piezas de pisadas que
               # quedaban del pedido original, ahora que las dos fases
               # tienen su propia `FrictionZone` nombrada (AUD-554,
               # `tools/generate_stage4_1.py`).
               "footstep_grava", "footstep_ahogado",
               # AUD-594 — GAP-070 punto 7: variantes `_con_eco` del bus de
               # reverberación de la Fase 6 (ver `_gen_sfx`): los sonidos
               # compartidos que suenan durante el recorrido hacia Paburu,
               # horneados con la misma reverberación que los cues propios
               # del nivel. `AudioManager.activar_eco(True)` las prefiere.
               "jump_con_eco", "land_con_eco", "crouch_con_eco",
               "short_attack_con_eco", "long_attack_con_eco",
               "hit_connect_con_eco", "hurt_con_eco"],
    "enemies": ["hit", "die_small", "die_large", "projectile_fire", "projectile_hit_wall",
                # AUD-529 — que se oiga antes de verse.
                "pez_abismal_acercarse"],
    "bosses": ["venado_stomp", "venado_charge", "venado_vine", "rey_spit", "rey_split",
               "gavilan_dive", "gavilan_mask_beam", "paburu_eye_beam", "paburu_wave",
               "phase_change", "relic_appear"],
    "ui": ["menu_move", "menu_confirm", "menu_cancel", "checkpoint", "stage_banner",
           "game_over", "heart_restore", "stage_complete",
           # AUD-553 — el pulso de la alerta de los últimos 10 segundos del
           # reloj (HUD.UMBRAL_DE_ALERTA_S): un solo fichero corto que suena
           # cada vez más seguido según el propio `HUD.update()` acorta el
           # intervalo — la aceleración la da el bucle del juego, no el
           # audio (ver la nota junto a `Events.SFX_TIMER_ALERT_PULSE`).
            "timer_alert_pulse",
            # AUD-594 — el checkpoint del 4-1 Fase 6, por el bus de eco
            # (ver la nota en "player").
            "checkpoint_con_eco"],
    "environment": ["jungle_ambient", "datacenter_hum", "wind_indoor", "cemetery_silence",
                    "screen_shake", "hazard_zone", "one_way_platform",
                    # AUD-271 — `rain` y `storm` eran los dos climas que
                    # `WeatherSystem.SIN_ASSET` declaraba sin fichero desde
                    # AUD-145. Declararlo en voz alta estuvo bien; generarlos
                    # por el mismo camino que los demás lo cierra.
                    "rain_ambient", "storm_ambient", "thunder",
                    # AUD-465 — los cuatro ambientes propios del 4-1
                    # rediseñado (`docs/niveles/15_DISENO_4_1_EL_CEMENTERIO.md`
                    # §5): uno por fase que lo pide. `canto_ancestral` es un
                    # coro sin palabras — el mismo principio que ya aplican
                    # las voces de `venado_fase1`: una vocalización de
                    # marcador de posición, no un intento de representar una
                    # lengua o una ceremonia real.
                    "viento_de_bosque", "grito_de_gavilan", "canto_ancestral",
                    "resonancia_solemne",
                    # AUD-515 — el sonido profundo de la secuencia de
                    # despertar de la Fase 6 (GAP-064 punto 25), con
                    # reverberación horneada — ver `_aplicar_reverberacion`.
                    "despertar_profundo",
                    # AUD-546 — las tres "recetas" de síntesis del dueño:
                    # ruido blanco pasa-altos (ramas/huesos, Fases 2-3),
                    # ruido rosa pasa-bajos barrido con paneo estéreo
                    # (ráfaga de viento, Fases 3-4), y un golpe de
                    # sub-graves con caída de tono (el impacto de la
                    # Fase 4 tras el silencio). Ver `_gen_sfx` para los
                    # parámetros exactos — cada uno cita el ADSR y el
                    # filtro del pedido original.
                    "crujido_seco", "rafaga_viento", "impacto_tension",
                    # AUD-592 — GAP-070 punto 4: la tormenta de la Fase 3
                    # con los dos LFO que pedía la receta del dueño horneados
                    # en un `.wav` estéreo propio (paneo -0.8↔0.8 y corte de
                    # filtro barriendo 400-2200Hz). Ver `_gen_sfx`.
                    "tormenta_paneada",
                    # AUD-593 — GAP-070 punto 5: la lluvia de la Fase 4
                    # pasada por un pasa-banda estrecho (~1500Hz), «a través
                    # de una radio vieja», sin tocar el bucle limpio que
                    # comparte el clima. Ver `_gen_sfx`.
                    "lluvia_de_radio",
                    # AUD-551 — GAP-070 punto 6: grillos de la Fase 5 (no
                    # existía ningún SFX de insecto, sólo el canto
                    # ancestral). Un solo fichero contiene la ráfaga
                    # entera de 3-4 "cri-cri" — el hueco entre ráfagas ya
                    # lo da el temporizador de `sonidos_aislados`.
                    "grillo",
                    # AUD-551 — GAP-070 "Pisadas de Energía Verde": tres
                    # variantes, una por nota de la tríada de Re menor
                    # (293.66/349.23/440.00Hz) — `Stage4_1` elige una al
                    # azar cada vez que una grieta termina de encenderse.
                    "paso_de_luz_re", "paso_de_luz_fa", "paso_de_luz_la",
                    # AUD-568 — propuesta "nivel cine" aprobada por el
                    # dueño: un acorde propio en el instante exacto en
                    # que un espíritu se libera de verdad (AUD-474), no
                    # reusado de ningún otro cue del nivel. Ver `_gen_sfx`.
                    "liberacion_espiritu"],
    # AUD-263 — las voces. GAP-031 decía «el motor sabe reproducir voz y no hay
    # ni un solo fichero», y se dejó así a propósito para no cablear mentiras.
    # Pero **todo** el audio de este juego está sintetizado aquí: los pasos, los
    # jefes, el menú. Una voz de marcador de posición generada por el mismo
    # camino no es una mentira, es la misma clase de recurso que el resto.
    #
    # Son las líneas del venado, el jefe de referencia, en sus dos cambios de
    # fase y en su muerte: lo justo para que `play_voz` tenga un demo real que
    # un estudiante pueda copiar para su propio jefe.
    # AUD-551 — GAP-070 "Diálogo de la Serpiente"/"Diálogo del Halcón":
    # el Venado ya tenía voz de marcador de posición (AUD-263); el Rey
    # Terciopelo y el Gavilán, no. Sintetizadas con las recetas
    # específicas del pedido (batimiento de dos senoidales para la
    # serpiente, FM de dos ondas para el halcón) — ver `_gen_sfx`.
    # AUD-554 — GAP-070 "La Voz del Bosque": el Venado del 4-1 seguía con
    # el timbre genérico de AUD-263 (`venado_fase1/2/muerte`) mientras el
    # Rey Terciopelo y el Gavilán ya tenían su receta propia desde
    # AUD-551 — `venado_ancestral` es la que usa `Stage4_1.
    # _VOZ_POR_ESPIRITU` al liberarlo. `venado_fase1/2/muerte` se dejan
    # tal cual: siguen sin ningún disparador propio (código muerto ya
    # documentado), pero no es a esta pieza a la que le toca resolverlo.
    "voz": ["venado_fase1", "venado_fase2", "venado_muerte",
            "rey_terciopelo", "gavilan", "venado_ancestral"],
}

#: AUD-592 — el pico del LFO de paneo de la tormenta de la Fase 3, tal como
#: lo pide la receta («oscilando -0.8↔0.8»).
PICO_DE_PANEO_TORMENTA = 0.8


def _bucle_sin_clic(muestras, rate=SAMPLE_RATE, fundido_ms=40.0):
    """Cierra un bucle perfecto: funde la cola con la cabeza (AUD-592).

    Que los LFO cierren ciclo dentro del bucle evita el clic de la
    **envolvente**, no el del **material**: el ruido crudo es distinto en la
    primera y en la última muestra, y el salto entre ambas es un chasquido
    audible cada vuelta (`loops=-1`). La técnica estándar de bucles lo
    quita así: se renderizan `fundido_ms` extra al final y la cabeza se
    sustituye por una mezcla a cruz entre esa cola y el arranque — la
    muestra que suena justo después del borde es continua con la que suena
    justo antes, porque literalmente empieza siendo la misma.

    Espera recibir `n + fundido` muestras y devuelve exactamente `n`.
    """
    fundido = int(rate * fundido_ms / 1000.0)
    if fundido <= 0 or len(muestras) <= fundido:
        return list(muestras)
    cuerpo = list(muestras[:len(muestras) - fundido])
    cola = list(muestras[len(muestras) - fundido:])
    salida = []
    for i in range(fundido):
        w = i / float(fundido)
        salida.append(cola[i] * (1.0 - w) + cuerpo[i] * w)
    return salida + cuerpo[fundido:]


def _gen_sfx(name, rate=SAMPLE_RATE):
    t_dur = {"jump": 0.2, "land": 0.1, "short_attack": 0.15, "long_attack": 0.25,
             "hit_connect": 0.1, "hurt": 0.3, "die": 0.5, "crouch": 0.1,
             "hit": 0.15, "die_small": 0.2, "die_large": 0.4, "projectile_fire": 0.15,
             "projectile_hit_wall": 0.1, "menu_move": 0.08, "menu_confirm": 0.15,
             "menu_cancel": 0.12, "checkpoint": 0.4, "stage_banner": 0.6, "game_over": 1.0,
             "heart_restore": 0.3, "stage_complete": 0.8, "phase_change": 0.5, "relic_appear": 0.4,
             "screen_shake": 0.3, "hazard_zone": 0.2, "one_way_platform": 0.1,
             "venado_stomp": 0.4, "venado_charge": 0.5, "venado_vine": 0.3,
             "rey_spit": 0.3, "rey_split": 0.6, "gavilan_dive": 0.4, "gavilan_mask_beam": 0.5,
             "paburu_eye_beam": 0.5, "paburu_wave": 0.6,
             "jungle_ambient": 2.0, "datacenter_hum": 2.0, "wind_indoor": 2.0, "cemetery_silence": 2.0,
             "venado_fase1": 0.9, "venado_fase2": 1.1, "venado_muerte": 1.4,
             "rain_ambient": 2.0, "storm_ambient": 2.0, "thunder": 1.6,
             "viento_de_bosque": 2.0, "grito_de_gavilan": 0.7,
             "canto_ancestral": 3.0, "resonancia_solemne": 4.0,
             "despertar_profundo": 1.6, "footstep_musgo": 0.12,
             "pez_abismal_acercarse": 2.2,
             # AUD-546 — duraciones del pedido original: el crujido es
             # ~150ms (ataque+decaimiento+relajación), la ráfaga de
             # viento ocupa el segundo completo del ADSR pedido, y el
             # impacto redondea la caída de tono (400ms) más su propio
             # decaimiento y relajación.
             "crujido_seco": 0.153, "rafaga_viento": 1.0,
             "impacto_tension": 0.955,
             # AUD-592 — GAP-070 punto 4: bucle de 2s como `storm_ambient`;
             # los dos LFO (paneo y corte) cierran ciclos enteros dentro de
             # él para que la vuelta no haga clic.
             "tormenta_paneada": 2.0,
             # AUD-593 — GAP-070 punto 5: mismo bucle de 2s de `rain_ambient`.
             "lluvia_de_radio": 2.0,
             # AUD-551 — GAP-070: lodo (ADSR hasta 12+80+0+100ms), la
             # ráfaga de grillo (tres "cri-cri" con hueco entre ellos),
             # las voces nuevas (misma duración que da el propio ADSR de
             # cada receta) y los tres pasos de luz (ADSR 15/200/-/1200ms).
             "footstep_lodo": 0.192, "grillo": 0.55,
             "rey_terciopelo": 1.7, "gavilan": 0.66,
             "paso_de_luz_re": 1.415, "paso_de_luz_fa": 1.415,
             "paso_de_luz_la": 1.415,
             # AUD-553 — corto a propósito: se repite cada vez más seguido
             # (hasta cada 80ms cerca de 0s), así que si durara más que su
             # propio intervalo se solaparía consigo mismo.
             "timer_alert_pulse": 0.12,
             # AUD-554 — GAP-070: grava (ADSR 2/45/-/15ms), ahogado (ADSR
             # 15/50/-/30ms), y la voz del Venado (ADSR 600/200/80%/2000ms
             # — la cola de reverberación se suma después, igual que
             # `paso_de_luz_*`).
             "footstep_grava": 0.062, "footstep_ahogado": 0.095,
             "venado_ancestral": 2.8,
             # AUD-568 — dry: 250ms ataque + 250ms sostenido + 1200ms
             # relajación = 1.7s; la reverberación añade su propia cola
             # aparte (ver `_aplicar_reverberacion`).
             "liberacion_espiritu": 1.7}
    
    dur = t_dur.get(name, 0.3)
    n = int(rate * dur)

    # AUD-594 — GAP-070 punto 7: las variantes `_con_eco` del bus de
    # reverberación de la Fase 6 no tienen receta propia: generan su base y
    # le hornean encima la misma `_aplicar_reverberacion` que ya llevan los
    # cues propios del nivel (despertar_profundo, cemetery_silence,
    # paso_de_luz_*). El sufijo lo lista explícitamente `SFX_CATEGORIES`.
    if name.endswith("_con_eco"):
        return _aplicar_reverberacion(_gen_sfx(name[:-len("_con_eco")], rate),
                                      rate)

    if name == "rain_ambient":
        # AUD-271 — lluvia: ruido blanco filtrado, sin envolvente. Es un bucle
        # de ambiente, así que **no** puede decaer: un ambiente que se apaga
        # delata el bucle en cuanto da la vuelta.
        anterior = 0.0
        samples = []
        for _ in range(n):
            crudo = random.uniform(-1.0, 1.0)
            anterior = anterior * 0.6 + crudo * 0.4     # paso bajo sencillo
            samples.append(anterior * 0.11)
    elif name == "storm_ambient":
        # Lo mismo, más grave y más fuerte: la tormenta es lluvia con cuerpo.
        anterior = 0.0
        samples = []
        for i in range(n):
            crudo = random.uniform(-1.0, 1.0)
            anterior = anterior * 0.82 + crudo * 0.18   # más filtrado = más grave
            # Un vaivén lento de intensidad, como ráfagas.
            rafaga = 0.75 + 0.25 * math.sin(2.0 * math.pi * (i / rate) / 3.0)
            samples.append(anterior * 0.17 * rafaga)
    elif name == "thunder":
        # El retumbar: ruido grave con ataque lento y cola larga. Lo que
        # distingue un trueno de un golpe es que **tarda** en llegar a su
        # máximo, y que se va apagando mucho después.
        anterior = 0.0
        samples = []
        for i in range(n):
            t_seg = i / rate
            avance = t_seg / dur
            crudo = random.uniform(-1.0, 1.0)
            anterior = anterior * 0.93 + crudo * 0.07
            env = min(1.0, avance * 6.0) * max(0.0, 1.0 - avance) ** 1.8
            samples.append((anterior + _tri(45.0, t_seg) * 0.25) * env * 0.5)
    elif name in ("jungle_ambient", "datacenter_hum", "wind_indoor"):
        # AUD-511 — mismo defecto que AUD-271 documentó para `rain_ambient`,
        # sin arreglar aquí: éstos SÍ decaían a cero (`* max(0, 1 - i/n)`).
        # `weather_system.AMBIENTES` reproduce `wind_indoor` con
        # `play_ambient(loops=-1)` para los climas «snow» y «fog» — un bucle
        # de verdad, de 2 s, que caía a silencio y volvía de golpe a volumen
        # lleno cada vuelta: un clic audible cada 2 segundos, indefinidamente,
        # mientras dure el clima. Sin envolvente, como `rain_ambient`.
        samples = [random.uniform(-0.05, 0.05) for _ in range(n)]
    elif name == "cemetery_silence":
        # A diferencia de los tres de arriba, este SÍ es un solo disparo: lo
        # usa `stage4_1._actualizar_silencio_y_shake` para «el clima calla de
        # golpe» a mitad de la Fase 4, una vez por visita. Decaer a silencio
        # es exactamente el efecto que pide — quitarle la envolvente sería
        # cambiarle el sentido, no arreglar nada.
        #
        # AUD-515, GAP-058 — le faltaba la reverberación que el propio hueco
        # pedía: *«el silencio se resuelve bajando el clima y las partículas
        # a cero, no con una reverberación que se apaga»*. `_aplicar_reverberacion`
        # la hornea encima del hush ya generado, en vez de quitarle la
        # envolvente que sí es correcta.
        samples = [random.uniform(-0.05, 0.05) * max(0, 1 - i/n) for i in range(n)]
        samples = _aplicar_reverberacion(samples, rate)
    elif name == "despertar_profundo":
        # AUD-515, GAP-064 punto 25 — el «sonido profundo» de la secuencia
        # de despertar antes del corte a `stage4_2_boss_paburu`. Antes
        # tomaba prestado `sfx_bosses_phase_change` (un cue de combate, no
        # de despertar del mundo); éste es un retumbar grave propio, con la
        # misma reverberación horneada que el silencio de la Fase 4 — las
        # dos son la misma idea, un espacio sagrado que resuena, así que
        # comparten el tratamiento.
        anterior = 0.0
        samples = []
        for i in range(n):
            t_seg = i / rate
            avance = t_seg / dur
            crudo = random.uniform(-1.0, 1.0)
            anterior = anterior * 0.95 + crudo * 0.05   # muy filtrado, muy grave
            env = min(1.0, avance * 3.0) * max(0.0, 1.0 - avance) ** 1.4
            samples.append((anterior + _tri(38.0, t_seg) * 0.3) * env * 0.55)
        samples = _aplicar_reverberacion(samples, rate, decaimiento=0.62, ecos=8,
                                          cola_extra_s=1.8)
    elif name == "jump":
        samples = [_square(200 + 1200 * (i/(n-1)) if n > 1 else 200, i/rate, 0.5) * (1 - i/n) * 0.3 for i in range(n)]
    elif name in ("short_attack", "long_attack", "hit_connect", "hit", "projectile_fire", "hazard_zone"):
        freq = {"short_attack": 300, "long_attack": 200, "hit_connect": 400, "hit": 200, "projectile_fire": 500, "hazard_zone": 100}
        samples = [_square(freq.get(name, 300), i/rate, 0.3) * (1 - i/n) * 0.25 + random.uniform(-0.1, 0.1) * (1 - i/n) for i in range(n)]
    elif name in ("hurt", "die", "die_small", "die_large", "game_over"):
        samples = [_square(80 - 40 * (i/n), i/rate, 0.5) * (1 - i/n) * 0.3 + random.uniform(-0.3, 0.3) * (1 - i/n) * 0.4 for i in range(n)]
    elif name in ("menu_move", "menu_confirm", "menu_cancel", "select"):
        freq = {"menu_move": 600, "menu_confirm": 800, "menu_cancel": 400, "select": 700}
        samples = [_square(freq.get(name, 600), i/rate, 0.5) * (1 - i/n) * 0.2 for i in range(n)]
    elif name in ("checkpoint", "heart_restore", "relic_appear", "stage_complete", "phase_change", "stage_banner"):
        samples = []
        for i in range(n):
            t = i / rate
            f = 400 + 800 * (t / dur)
            env = max(0, 1 - (t / dur))
            samples.append(_tri(f, t) * env * 0.2 + _square(f * 0.5, t, 0.5) * env * 0.1)
    elif name in ("venado_stomp", "venado_charge", "venado_vine", "rey_spit", "rey_split",
                  "gavilan_dive", "gavilan_mask_beam", "paburu_eye_beam", "paburu_wave"):
        samples = []
        for i in range(n):
            t = i / rate
            env = max(0, 1 - t / dur)
            samples.append(_square(100, t, 0.3) * 0.2 + _square(150, t, 0.3) * 0.15 + random.uniform(-0.2, 0.2) * env)
    elif name == "viento_de_bosque":
        # Fase 2 (El Venado): el mismo filtrado paso-bajo que `rain_ambient`,
        # pero con ráfagas más lentas (el viento entre árboles, no la lluvia)
        # y un roce agudo y débil por encima — hojas, no gotas.
        anterior = 0.0
        samples = []
        for i in range(n):
            t_seg = i / rate
            crudo = random.uniform(-1.0, 1.0)
            anterior = anterior * 0.70 + crudo * 0.30
            rafaga = 0.6 + 0.4 * math.sin(2.0 * math.pi * t_seg / 4.0)
            hoja = random.uniform(-1.0, 1.0) * 0.15
            samples.append((anterior * 0.14 + hoja * 0.05) * rafaga)
    elif name == "grito_de_gavilan":
        # Fase 4: un solo grito, aislado (lo dispara la escena, no un bucle).
        # Empieza agudo y cae — el perfil de un chillido de ave rapaz, no una
        # nota musical ni una palabra.
        samples = []
        for i in range(n):
            t = i / rate
            avance = t / dur
            f = 1400.0 - 900.0 * avance
            env = math.sin(min(1.0, avance) * math.pi) ** 0.6
            aspereza = random.uniform(-0.3, 0.3)
            samples.append((_tri(f, t) * 0.5 + aspereza * 0.3) * env)
    elif name == "canto_ancestral":
        # Fase 5 (La Planicie de los Muertos): un coro sin palabras. Tres
        # voces en unísono ligeramente desafinado —la disonancia mínima que
        # se lee como «varias voces» y no como un tono puro— con una
        # respiración lenta de volumen. Nada de esto finge una lengua: es la
        # misma vocalización de marcador de posición que ya usa el proyecto
        # para `venado_fase1`, aquí en registro humano y sostenida.
        voces = (98.0, 98.6, 147.3)  # sol grave, la misma nota un pelín
                                      # desafinada, y su quinta
        samples = []
        for i in range(n):
            t = i / rate
            respira = 0.7 + 0.3 * math.sin(2.0 * math.pi * t / 5.0)
            v = sum(_tri(f, t) for f in voces) / len(voces)
            samples.append(v * 0.22 * respira)
    elif name == "resonancia_solemne":
        # Fase 6 (El Camino hacia Paburu): el mismo principio aditivo que
        # `_gen_bgm_organo` —un armónico es un múltiplo entero de la
        # fundamental— pero sin acordes que cambien: un solo acorde
        # sostenido, la misma tónica de re menor del órgano de la pista
        # (`bgm_final_approach`), como si siguiera resonando después de
        # cruzar el umbral.
        fundamental = 73.42  # Re2
        armonicos = (1, 2, 3, 5)
        samples = []
        for i in range(n):
            t = i / rate
            tremolo = 1.0 + 0.05 * math.sin(2.0 * math.pi * t * 4.5)
            v = sum(_tri(fundamental * h, t) / h for h in armonicos)
            samples.append(v * 0.16 * tremolo)
    elif name == "footstep_musgo":
        # AUD-522 — el musgo resbala y hasta ahora no se oía ni se veía.
        # Un chapoteo corto y sordo: ruido muy filtrado —blando, sin
        # agudos, nada del crujido de `sfx_step`— con ataque casi
        # instantáneo y caída rápida, una pisada suelta, no un charco
        # entero.
        anterior = 0.0
        samples = []
        for i in range(n):
            t_seg = i / rate
            avance = t_seg / dur
            crudo = random.uniform(-1.0, 1.0)
            anterior = anterior * 0.9 + crudo * 0.1
            env = min(1.0, avance * 20.0) * max(0.0, 1.0 - avance) ** 2.0
            samples.append(anterior * env * 0.3)
    elif name == "pez_abismal_acercarse":
        # AUD-529 — «que el jugador lo sienta y lo escuche antes de poder
        # verlo». `Stage4_1B._invocar_pez` lo dispara al aparecer, fuera
        # de cámara a propósito (GAP-065 §4) — este sonido es el segundo
        # o dos de aviso antes de que la silueta entre nadando en cuadro.
        # Un gemido grave que se desliza —no un pitido fijo, una criatura
        # respirando/crujiendo bajo el agua— con textura de ruido muy
        # filtrado encima, no el aullido agudo de `grito_de_gavilan`
        # (ave rapaz, registro alto): esto es abisal, registro grave.
        fundamental_inicio = 42.0
        fundamental_fin = 58.0
        ruido_previo = 0.0
        samples = []
        for i in range(n):
            t = i / rate
            avance = t / dur
            # Ataque lento (se acerca), sostenido, caída hacia el final
            # (se aleja / se pierde en el agua) — no un golpe seco.
            env = min(1.0, avance * 2.2) * (1.0 - max(0.0, (avance - 0.6) / 0.4)) ** 1.3
            f = fundamental_inicio + (fundamental_fin - fundamental_inicio) * avance
            # Vibrato lento: una criatura, no una sirena.
            f *= 1.0 + 0.03 * math.sin(2.0 * math.pi * t * 2.2)
            tono = _tri(f, t) + 0.4 * _tri(f * 2.0, t)
            crudo = random.uniform(-1.0, 1.0)
            ruido_previo = ruido_previo * 0.93 + crudo * 0.07
            samples.append((tono * 0.5 + ruido_previo * 0.35) * env * 0.6)
    elif name in ("venado_fase1", "venado_fase2", "venado_muerte"):
        # AUD-263 — voz de marcador de posición: una vocalización grave con
        # formantes, no una palabra. Un gruñido con inflexión se lee como «una
        # criatura ha dicho algo» sin fingir un idioma, que es lo que hace falta
        # para probar la mezcla —el ducking de la música al 35 %— y para que el
        # estudiante oiga dónde encaja su propia grabación.
        # Nota: antes era `startswith("venado_")` y tragaba `venado_vine`/`venado_stomp`
        # causando KeyError en generación completa (fix para generación PSX 32-bit).
        base = {"venado_fase1": 110.0, "venado_fase2": 95.0, "venado_muerte": 80.0}[name]
        samples = []
        for i in range(n):
            t = i / rate
            avance = t / dur
            # La inflexión sube y vuelve a bajar: una frase, no un pitido.
            f = base * (1.0 + 0.25 * math.sin(math.pi * avance))
            # Envolvente con ataque corto y cola larga, como una exhalación.
            env = min(1.0, avance * 12.0) * max(0.0, 1.0 - avance) ** 0.7
            voz = (_tri(f, t) * 0.45 + _square(f * 2.0, t, 0.35) * 0.18
                   + _tri(f * 3.0, t) * 0.10)
            # Un poco de aire: sin él suena a sintetizador y no a garganta.
            samples.append((voz + random.uniform(-0.06, 0.06)) * env * 0.35)
    elif name == "crujido_seco":
        # AUD-546 — receta del dueño: ruido blanco, pasa-altos 2000-3500Hz
        # (aleatorizado por generación, ver la nota de `_pasa_altos` más
        # abajo sobre por qué no es por-reproducción), ADSR
        # ataque=1-5ms/decaimiento=100ms/sostenimiento=0/relajación=50ms.
        # Ramas rompiéndose (Fase 2) u osamentas chocando (Fase 3): el
        # mismo timbre agudo y seco sirve para los dos, es la fuente la
        # que cambia en la ficción, no el filtro.
        corte = random.uniform(2000.0, 3500.0)
        crudo = [random.uniform(-1.0, 1.0) for _ in range(n)]
        filtrado = _pasa_altos(crudo, corte, rate)
        ataque = max(1, int(rate * 0.003))       # 3ms, dentro de 1-5ms
        decaimiento = int(rate * 0.100)
        relajacion = int(rate * 0.050)
        samples = []
        for i, s in enumerate(filtrado):
            if i < ataque:
                env = i / ataque
            elif i < ataque + decaimiento:
                # Decae hasta un residuo bajo, no hasta cero: sin esto la
                # relajación no tendría nada que desvanecer (sostenimiento
                # 0 más decaimiento a 0 dejaría la relajación sonando
                # silencio).
                env = 1.0 - 0.85 * (i - ataque) / decaimiento
            else:
                j = i - ataque - decaimiento
                env = max(0.0, 0.15 * (1.0 - j / max(1, relajacion)))
            samples.append(s * env * 0.5)
    elif name == "rafaga_viento":
        # AUD-546 — receta del dueño: ruido rosa, ADSR
        # 300ms/200ms/50%/500ms (suma exacta: un segundo), pasa-bajos
        # barrido 300→1200→300Hz por un LFO, paneo de -1.0 a 1.0 durante
        # el segundo entero. Es el único SFX de este proyecto en estéreo
        # de verdad —`_gen_all_sfx` lo detecta por que esta rama devuelve
        # un par (izquierda, derecha), no una lista plana— porque el
        # paneo direccional es el propio pedido, no un adorno.
        rosa = _ruido_rosa(n)
        mono = []
        estado_filtro = 0.0
        for i in range(n):
            t = i / rate
            # Medio seno: sube de 300 a 1200Hz y vuelve a bajar a 300Hz a
            # lo largo del segundo — «barre... subiendo y baja de nuevo».
            frac = math.sin(math.pi * min(1.0, t / dur))
            corte = 300.0 + 900.0 * frac
            estado_filtro = _paso_pasa_bajos(rosa[i], estado_filtro, corte, rate)
            if t < 0.3:
                env = t / 0.3
            elif t < 0.5:
                env = 1.0 - 0.5 * (t - 0.3) / 0.2
            else:
                env = 0.5 * max(0.0, 1.0 - (t - 0.5) / 0.5)
            mono.append(estado_filtro * env * 0.6)
        izquierda, derecha = [], []
        for i, s in enumerate(mono):
            # Paneo lineal de -1.0 (izquierda) a 1.0 (derecha) a lo largo
            # del segundo — «atraviesa el mapa».
            pan = -1.0 + 2.0 * (i / max(1, n - 1))
            izquierda.append(s * (1.0 - pan) * 0.5)
            derecha.append(s * (1.0 + pan) * 0.5)
        samples = (izquierda, derecha)
    elif name == "tormenta_paneada":
        # AUD-592 — GAP-070 punto 4: la receta del dueño para la tormenta
        # de la Fase 3 pedía «un LFO de paneo oscilando -0.8↔0.8 más un
        # LFO de filtro barriendo 400-2200Hz» sobre el bucle ya en
        # reproducción. Este motor no tiene DSP en tiempo real, pero cada
        # `Fase` declara su propio `sonido_ambiente`, así que la respuesta
        # es hornear una variante estéreo propia — el mismo camino que
        # demostró `rafaga_viento`, del que ésta se diferencia en que los
        # dos LFO cierran ciclos **enteros** dentro del bucle de 2s: el
        # seno vale lo mismo en t=0 que en t=T, y la vuelta del bucle no
        # hace clic.
        #
        # Cuerpo: el mismo ruido blanco muy filtrado con ráfagas lentas de
        # `storm_ambient` («la tormenta es lluvia con cuerpo»), pasado por
        # el corte variable — 1300±900Hz, un ciclo por bucle — usando el
        # paso de `_paso_pasa_bajos` que `rafaga_viento` dejó listo para
        # cortes muestra a muestra. Se renderizan 40ms extra al final y
        # `_bucle_sin_clic` los funde con la cabeza: los LFO cierran ciclo,
        # pero el material crudo no, y sin ese pliegue la vuelta haría clic.
        mono = []
        estado_filtro = 0.0
        anterior = 0.0
        total = n + int(rate * 0.04)
        for i in range(total):
            t = i / rate
            crudo = random.uniform(-1.0, 1.0)
            anterior = anterior * 0.82 + crudo * 0.18
            corte = 1300.0 + 900.0 * math.sin(2.0 * math.pi * i / n)
            cuerpo_filtrado = _paso_pasa_bajos(anterior, estado_filtro, corte, rate)
            estado_filtro = cuerpo_filtrado
            rafaga = 0.75 + 0.25 * math.sin(2.0 * math.pi * t / 2.0)
            mono.append(cuerpo_filtrado * 0.17 * rafaga)
        mono = _bucle_sin_clic(mono, rate, fundido_ms=40.0)
        izquierda, derecha = [], []
        for i, s in enumerate(mono):
            pan = PICO_DE_PANEO_TORMENTA * math.sin(2.0 * math.pi * i / n)
            izquierda.append(s * (1.0 - pan) * 0.5)
            derecha.append(s * (1.0 + pan) * 0.5)
        samples = (izquierda, derecha)
    elif name == "lluvia_de_radio":
        # AUD-593 — GAP-070 punto 5: la receta pide que la lluvia de la
        # Fase 4 suene «a través de una radio vieja»: el mismo cuerpo de
        # `rain_ambient` pasado por un **pasa-banda estrecho alrededor de
        # 1500Hz** — sólo en esta fase, no en el bucle limpio del clima.
        # El pasa-banda es una cascada de lo que el fichero ya tiene, con
        # DOS polos por lado (los un polo son demasiado suaves: dejan un
        # rumor grave que domina la banda): `_pasa_altos` dos veces por
        # abajo y dos pasos de `_paso_pasa_bajos` por arriba. Como el
        # pasa-banda deja pasar mucha menos energía que el paso-bajo
        # ancho, da igual: los `.wav` se normalizan al escribirlos
        # (`_write_wav`). El pliegue de `_bucle_sin_clic` evita el clic de
        # la vuelta.
        total = n + int(rate * 0.04)
        base = []
        anterior = 0.0
        for _ in range(total):
            crudo = random.uniform(-1.0, 1.0)
            anterior = anterior * 0.6 + crudo * 0.4     # lluvia: paso bajo
            base.append(anterior)
        banda = _pasa_altos(base, corte_hz=1050.0, rate=rate)
        banda = _pasa_altos(banda, corte_hz=1050.0, rate=rate)
        filtrado = []
        estado_bajo_1 = 0.0
        estado_bajo_2 = 0.0
        for x in banda:
            estado_bajo_1 = _paso_pasa_bajos(x, estado_bajo_1, 1650.0, rate)
            estado_bajo_2 = _paso_pasa_bajos(estado_bajo_1, estado_bajo_2,
                                             1650.0, rate)
            filtrado.append(estado_bajo_2)
        samples = _bucle_sin_clic(filtrado, rate, fundido_ms=40.0)
    elif name == "impacto_tension":
        # AUD-546 — receta del dueño: onda senoidal con caída de tono de
        # 80Hz a 30Hz en 400ms, ADSR 5ms/800ms/0/150ms, recorte suave
        # (soft clip) en los primeros 100ms para el "golpe" percusivo
        # inicial. El golpe de sub-graves de la Fase 4, justo después del
        # silencio absoluto — se siente, no sólo se oye.
        ataque = max(1, int(rate * 0.005))
        decaimiento = int(rate * 0.800)
        relajacion = int(rate * 0.150)
        fase = 0.0
        samples = []
        for i in range(n):
            t = i / rate
            if t < 0.4:
                # Caída exponencial de 80 a 30Hz a lo largo de 400ms — un
                # chirrido descendente, integrado en fase para que la
                # frecuencia cambie de verdad y no salga con artefactos.
                freq = 30.0 + 50.0 * math.exp(-5.0 * t / 0.4)
            else:
                freq = 30.0
            fase += 2.0 * math.pi * freq / rate
            onda = math.sin(fase)
            if i < ataque:
                env = i / ataque
            elif i < ataque + decaimiento:
                env = 1.0 - 0.92 * (i - ataque) / decaimiento
            else:
                j = i - ataque - decaimiento
                env = max(0.0, 0.08 * (1.0 - j / max(1, relajacion)))
            valor = onda * env
            if t < 0.1:
                # Saturación leve sólo en los primeros 100ms: el golpe
                # percusivo antes de que quede sólo el zumbido grave.
                valor = _recorte_suave(valor * 1.4)
            samples.append(valor * 0.9)
    elif name == "footstep_lodo":
        # AUD-551 — GAP-070 punto 1: ruido marrón (pasa-bajos pesado
        # sobre ruido blanco, el mismo idioma del resto de este fichero)
        # 80% + seno a 80Hz 20%, pasa-bajos 700-800Hz aleatorio, ADSR
        # 11/70/0/90ms, pitch ±10% aleatorio para que ningún paso suene
        # idéntico ("efecto metralleta").
        variacion = random.uniform(0.9, 1.1)
        corte = random.uniform(700.0, 800.0)
        estado = 0.0
        ataque = max(1, int(rate * 0.011))
        decaimiento = int(rate * 0.070)
        relajacion = max(1, int(rate * 0.090))
        samples = []
        for i in range(n):
            t = i / rate
            crudo = random.uniform(-1.0, 1.0)
            estado = _paso_pasa_bajos(crudo, estado, corte, rate)
            seno = math.sin(2.0 * math.pi * 80.0 * variacion * t)
            valor = estado * 0.8 + seno * 0.2
            if i < ataque:
                env = i / ataque
            elif i < ataque + decaimiento:
                env = 1.0 - 0.9 * (i - ataque) / decaimiento
            else:
                j = i - ataque - decaimiento
                env = max(0.0, 0.1 * (1.0 - j / relajacion))
            samples.append(valor * env * 0.55)
    elif name == "grillo":
        # AUD-551 — GAP-070 punto 6: cuadrada de ancho de pulso angosto
        # (5-10%), 4000-6000Hz, micro-ADSR 1/30/0/10ms por "clic", LFO
        # de amplitud a 40Hz ("fragmenta el decaimiento, la fricción
        # rápida de las alas"), ráfaga de 3-4 clics seguidos — el hueco
        # entre ráfagas lo da el temporizador de `sonidos_aislados`.
        freq_base = random.uniform(4000.0, 6000.0)
        n_chirps = random.randint(3, 4)
        espaciado_s = 0.13
        samples = [0.0] * n
        ataque = max(1, int(rate * 0.001))
        decaimiento = int(rate * 0.030)
        relajacion = max(1, int(rate * 0.010))
        n_chirp = ataque + decaimiento + relajacion
        for c in range(n_chirps):
            inicio_i = int(c * espaciado_s * rate)
            for k in range(n_chirp):
                idx = inicio_i + k
                if idx >= n:
                    break
                t = k / rate
                onda = _square(freq_base, t, 0.07)
                tremolo = 0.6 + 0.4 * math.sin(2.0 * math.pi * 40.0 * t)
                if k < ataque:
                    env = k / ataque
                elif k < ataque + decaimiento:
                    env = 1.0 - (k - ataque) / decaimiento
                else:
                    j = k - ataque - decaimiento
                    env = max(0.0, 1.0 - j / relajacion)
                samples[idx] += onda * env * tremolo * 0.3
    elif name == "rey_terciopelo":
        # AUD-551 — GAP-070 "Diálogo de la Serpiente": ruido rosa +
        # batimiento de dos senoidales muy cercanas (440/446Hz),
        # pasa-banda aproximado (pasa-altos 3000Hz seguido de pasa-bajos
        # 7000Hz — no hay un pasa-banda de verdad en este fichero, se
        # compone de los dos que ya existen) centrado alrededor de
        # 5000Hz, LFO de amplitud a 25Hz ("sisea a velocidad
        # sobrehumana"), ADSR 200/300/60%/1200ms.
        rosa = _ruido_rosa(n)
        crudo = []
        for i in range(n):
            t = i / rate
            batimiento = (math.sin(2.0 * math.pi * 440.0 * t)
                          + math.sin(2.0 * math.pi * 446.0 * t)) * 0.5
            crudo.append(rosa[i] * 0.5 + batimiento * 0.5)
        alto = _pasa_altos(crudo, 3000.0, rate)
        estado = 0.0
        filtrado = []
        for v in alto:
            estado = _paso_pasa_bajos(v, estado, 7000.0, rate)
            filtrado.append(estado)
        ataque = max(1, int(rate * 0.200))
        decaimiento = int(rate * 0.300)
        relajacion = max(1, int(rate * 1.200))
        samples = []
        for i, v in enumerate(filtrado):
            t = i / rate
            tremolo = 0.5 + 0.5 * math.sin(2.0 * math.pi * 25.0 * t)
            if i < ataque:
                env = i / ataque
            elif i < ataque + decaimiento:
                env = 1.0 - 0.4 * (i - ataque) / decaimiento  # 1.0 → 0.6
            else:
                j = i - ataque - decaimiento
                env = max(0.0, 0.6 * (1.0 - j / relajacion))
            samples.append(v * env * tremolo * 0.6)
    elif name == "gavilan":
        # AUD-551 — GAP-070 "Diálogo del Halcón": diente de sierra 70% +
        # cuadrada 30% a 1800Hz, modulado en frecuencia (FM) por una
        # senoidal a 50Hz, ADSR 10/150/40%/500ms, seco — sin
        # reverberación a propósito, "posado directamente sobre la
        # cámara". Fase acumulada, no `t*freq`: con la frecuencia
        # variando por la FM, `t*freq` saltaría de ciclo en ciclo.
        ataque = max(1, int(rate * 0.010))
        decaimiento = int(rate * 0.150)
        relajacion = max(1, int(rate * 0.500))
        fase = 0.0
        samples = []
        for i in range(n):
            t = i / rate
            freq = 1800.0 + math.sin(2.0 * math.pi * 50.0 * t) * 90.0
            fase += 2.0 * math.pi * freq / rate
            ciclo = (fase / (2.0 * math.pi)) % 1.0
            sierra = 2.0 * ciclo - 1.0
            cuadrada = 1.0 if ciclo < 0.5 else -1.0
            onda = sierra * 0.7 + cuadrada * 0.3
            if i < ataque:
                env = i / ataque
            elif i < ataque + decaimiento:
                env = 1.0 - 0.6 * (i - ataque) / decaimiento  # 1.0 → 0.4
            else:
                j = i - ataque - decaimiento
                env = max(0.0, 0.4 * (1.0 - j / relajacion))
            samples.append(onda * env * 0.5)
    elif name == "footstep_grava":
        # AUD-554 — GAP-070 "Pasos sobre Tierra/Grava" (Fase 1 del 4-1):
        # 85% ruido rosa + 15% pulso cuadrado corto, pasa-banda ~1200Hz
        # (pasa-altos seguido de pasa-bajos, mismo idioma que
        # `rey_terciopelo`), centro aleatorizado ±150Hz por generación
        # para que ningún paso suene idéntico, ADSR 2/45/0/15ms.
        centro = random.uniform(1050.0, 1350.0)
        rosa = _ruido_rosa(n)
        crudo = [rosa[i] * 0.85 + _square(60.0, i / rate, 0.5) * 0.15
                 for i in range(n)]
        alto = _pasa_altos(crudo, max(1.0, centro - 400.0), rate)
        estado = 0.0
        filtrado = []
        for v in alto:
            estado = _paso_pasa_bajos(v, estado, centro + 400.0, rate)
            filtrado.append(estado)
        ataque = max(1, int(rate * 0.002))
        decaimiento = int(rate * 0.045)
        relajacion = max(1, int(rate * 0.015))
        samples = []
        for i, v in enumerate(filtrado):
            if i < ataque:
                env = i / ataque
            elif i < ataque + decaimiento:
                env = 1.0 - (i - ataque) / decaimiento
            else:
                j = i - ataque - decaimiento
                env = max(0.0, 1.0 - j / relajacion) if relajacion else 0.0
            samples.append(v * env * 0.5)
    elif name == "footstep_ahogado":
        # AUD-554 — GAP-070 "Pasos Ahogados" (Fase 5 del 4-1): ruido
        # marrón (pasa-bajos pesado sobre blanco, mismo idioma que
        # `footstep_lodo`), corte estricto en 250Hz, ADSR 15/50/0/30ms.
        # "Control de Dinámica": tope de volumen al 30% — horneado en la
        # amplitud final, no en un parámetro de reproducción aparte.
        estado = 0.0
        ataque = max(1, int(rate * 0.015))
        decaimiento = int(rate * 0.050)
        relajacion = max(1, int(rate * 0.030))
        samples = []
        for i in range(n):
            crudo = random.uniform(-1.0, 1.0)
            estado = _paso_pasa_bajos(crudo, estado, 250.0, rate)
            if i < ataque:
                env = i / ataque
            elif i < ataque + decaimiento:
                env = 1.0 - (i - ataque) / decaimiento
            else:
                j = i - ataque - decaimiento
                env = max(0.0, 1.0 - j / relajacion) if relajacion else 0.0
            samples.append(estado * env * 0.3)
    elif name == "venado_ancestral":
        # AUD-554 — GAP-070 "La Voz del Bosque" (Venado, receta propia en
        # vez del timbre de marcador de posición de AUD-263): diente de
        # sierra + seno a 60Hz para el tamaño, LFO de vibrato en el pitch
        # a 12Hz, ADSR 600/200/80%/2000ms, pasa-banda barriendo 150→400Hz
        # (envolvente en el filtro — se acerca con pasa-altos fijo en
        # 150Hz seguido de un pasa-bajos cuyo corte sube linealmente de
        # 150 a 400Hz, mismo idioma de "bandpass compuesto" que ya usa
        # `rey_terciopelo`), reverberación masiva para que "suene como si
        # todo el nivel estuviera hablando a la vez". Fase acumulada como
        # en `gavilan`: con el vibrato variando la frecuencia instante a
        # instante, `t * freq` saltaría de ciclo en ciclo.
        ataque = max(1, int(rate * 0.600))
        decaimiento = int(rate * 0.200)
        relajacion = max(1, int(rate * 2.000))
        fase = 0.0
        crudo = []
        for i in range(n):
            t = i / rate
            freq = 60.0 * (1.0 + 0.03 * math.sin(2.0 * math.pi * 12.0 * t))
            fase += 2.0 * math.pi * freq / rate
            ciclo = (fase / (2.0 * math.pi)) % 1.0
            sierra = 2.0 * ciclo - 1.0
            seno = math.sin(2.0 * math.pi * 60.0 * t)
            crudo.append(sierra * 0.6 + seno * 0.4)
        alto = _pasa_altos(crudo, 150.0, rate)
        estado = 0.0
        filtrado = []
        for i, v in enumerate(alto):
            corte = 150.0 + (400.0 - 150.0) * min(1.0, i / n)
            estado = _paso_pasa_bajos(v, estado, corte, rate)
            filtrado.append(estado)
        samples = []
        for i, v in enumerate(filtrado):
            if i < ataque:
                env = i / ataque
            elif i < ataque + decaimiento:
                env = 1.0 - 0.2 * (i - ataque) / decaimiento  # 1.0 → 0.8
            else:
                j = i - ataque - decaimiento
                env = max(0.0, 0.8 * (1.0 - j / relajacion))
            samples.append(v * env * 0.6)
        samples = _aplicar_reverberacion(samples, rate, decaimiento=0.7,
                                          retardo_ms=90.0, ecos=14, cola_extra_s=2.5)
    elif name.startswith("paso_de_luz_"):
        # AUD-551 — GAP-070 "Pisadas de Energía Verde": seno 80% +
        # triángulo 20%, ADSR 15/200/30%/1200ms, una nota fija por
        # variante — la tríada de Re menor (293.66/349.23/440.00Hz);
        # `Stage4_1` elige el fichero al azar en cada grieta que termina
        # de encenderse. Lleva cola de reverberación horneada (GAP-070
        # punto 7, "bus" de la Fase 6): la receta pide ~3500ms de
        # decaimiento y 60ms de pre-delay, pero `_aplicar_reverberacion`
        # es un comb filter de ecos discretos, no una cola continua —
        # estirarlo a 3500ms de verdad sonaría a cañón, no a santuario.
        # Se usa el mismo criterio de gusto que ya fijó AUD-515 para
        # `despertar_profundo`: menos ecos, más juntos, con la cola
        # extra dando la sensación de espacio sin el eco discreto.
        freq = {"paso_de_luz_re": 293.66, "paso_de_luz_fa": 349.23,
                "paso_de_luz_la": 440.00}[name]
        ataque = max(1, int(rate * 0.015))
        decaimiento = int(rate * 0.200)
        relajacion = max(1, int(rate * 1.200))
        samples = []
        for i in range(n):
            t = i / rate
            onda = math.sin(2.0 * math.pi * freq * t) * 0.8 + _tri(freq, t) * 0.2
            if i < ataque:
                env = i / ataque
            elif i < ataque + decaimiento:
                env = 1.0 - 0.7 * (i - ataque) / decaimiento  # 1.0 → 0.3
            else:
                j = i - ataque - decaimiento
                env = max(0.0, 0.3 * (1.0 - j / relajacion))
            samples.append(onda * env * 0.5)
        samples = _aplicar_reverberacion(samples, rate, decaimiento=0.6,
                                          retardo_ms=60.0, ecos=10, cola_extra_s=2.0)
    elif name == "liberacion_espiritu":
        # AUD-568 — propuesta "nivel cine": un acorde propio, distinto de
        # cualquier otro cue del nivel, en el instante exacto en que un
        # espíritu se libera de verdad (`Stage4_1._espiritu_liberado`
        # pasando a `True` tras el botón de usar, AUD-474). Misma tríada
        # de Re menor que ya ancla "algo despierta" en `paso_de_luz_*`
        # —mismo lenguaje armónico, el mismo despertar—, pero una octava
        # más grave (D3/F3/A3, no D4/F4/A4) y con una envolvente mucho
        # más lenta: 250ms de ataque en vez de 15, así que crece como un
        # alivio sostenido, no como una campanilla que llama la atención.
        frecuencias = (146.83, 174.61, 220.00)  # D3, F3, A3
        ataque = max(1, int(rate * 0.25))
        sostenido = int(rate * 0.25)
        relajacion = max(1, int(rate * 1.2))
        samples = []
        for i in range(n):
            t = i / rate
            onda = sum(
                math.sin(2.0 * math.pi * f * t) * 0.8 + _tri(f, t) * 0.2
                for f in frecuencias
            ) / len(frecuencias)
            if i < ataque:
                env = i / ataque
            elif i < ataque + sostenido:
                env = 1.0
            else:
                j = i - ataque - sostenido
                env = max(0.0, 1.0 - j / relajacion)
            samples.append(onda * env * 0.45)
        samples = _aplicar_reverberacion(samples, rate, decaimiento=0.65,
                                          retardo_ms=70.0, ecos=10, cola_extra_s=2.0)
    elif name == "timer_alert_pulse":
        # AUD-553 — un "tick" de alarma, no el timbre de recompensa que ya
        # usan checkpoint/heart_restore/stage_complete (esos suben de tono
        # y premian; esto tiene que sonar a advertencia, plano y seco).
        # Cuadrada a 1200Hz con ataque instantáneo y decaimiento corto, más
        # un seno grave (200Hz) por debajo para darle cuerpo sin suavizarlo.
        ataque = max(1, int(rate * 0.003))
        samples = []
        for i in range(n):
            t = i / rate
            if i < ataque:
                env = i / ataque
            else:
                env = max(0.0, 1.0 - (i - ataque) / (n - ataque))
            samples.append(_square(1200, t, 0.5) * env * 0.35
                            + math.sin(2.0 * math.pi * 200 * t) * env * 0.15)
    else:
        samples = [0.0] * n

    return samples

def _gen_all_sfx():
    print("  SFX...")
    for cat, names in SFX_CATEGORIES.items():
        for name in names:
            sdir = A / "sfx" / cat
            samples = _gen_sfx(name)
            destino = sdir / f"sfx_{cat}_{name}.wav"
            # AUD-546 — `rafaga_viento` devuelve (izquierda, derecha) en
            # vez de una lista plana: es el único SFX en estéreo de
            # verdad de este proyecto (ver `_write_wav_stereo`).
            if isinstance(samples, tuple):
                _write_wav_stereo(destino, *samples)
            else:
                _write_wav(destino, samples)


# ════════════════════════════════════════
# AUD-596 — stingers de fase de jefe y risa de Paburu (GAP-067)
# ════════════════════════════════════════
#
# Los cuatro `.wav` de `assets/sfx/stingers/` y la risa de
# `assets/sfx/voz/sfx_voz_paburu_risa.wav` nacieron en AUD-541 como
# placeholders desechables sin generador comprometido. La decisión del dueño
# (2026-08-21) los acepta como definitivos **procedimentales**: la receta del
# propio GAP pedía que «el stinger debe crecer en tensión con el número de
# fase» — cada fase acumula capa, longitud y graves — y una risa de verdad
# tiene estallidos irregulares con tono que sube y baja. Viven fuera del
# catálogo porque sus nombres (`stinger_boss_phase_N`, `sfx_voz_*`) rompen la
# convención `sfx_<categoria>_<nombre>` y sus rutas son contrato con
# `boss_base.py` y `menu_sfx.py`.

#: Duración (s) por fase: 0.9 → 1.7. La curva que mide la prueba.
STINGER_DURACION = (0.9, 1.15, 1.4, 1.7)

#: Nota más grave de cada fase (Hz): a partir de la fase 1 es un **colchón
#: continuo** bajo todo lo demás, que baja de tono y sube de volumen con la
#: fase — la energía de graves creciente es lo que mide la prueba.
STINGER_GRAVE = (164.81, 98.0, 73.42, 55.0)

#: Volumen del colchón de graves por fase (la fase 0 no tiene).
STINGER_COLCHON = (0.0, 0.18, 0.30, 0.45)

#: Rumor de 50 Hz — el mismo tono en todas las fases con volumen creciente.
#: Es la capa que mide la prueba (Goertzel a 50 Hz): un tono FIJO que
#: crece no se confunde con los colchones que bajan de nota ni con la
#: normalización de cada fichero.
STINGER_SUB = (0.0, 0.12, 0.26, 0.42)


def _gen_stinger_de_fase(fase, rate=SAMPLE_RATE):
    """Stinger del cambio de fase `fase` (0-3), tensión creciente.

    Capas acumulativas — la fase n lleva todo lo que llevaba la n-1 más su
    propia voz:

    0 «aviso»     dos notas (mi→si), seno+cuadrada suave;
    1 «inquietud» tríada menor arpegiada + trémolo de 8 Hz + aliento de
                  ruido rosa filtrado;
    2 «alarma»    tritono sostenido + refuerzo una octava abajo + oleada
                  creciente de ruido;
    3 «pánico»    clúster + caída de subgraves (90→38 Hz) + reverberación
                  larga (`_aplicar_reverberacion`).
    """
    dur = STINGER_DURACION[fase]
    n = int(rate * dur)
    grave = STINGER_GRAVE[fase]
    salida = [0.0] * n

    def _nota(inicio_s, largo_s, freq, vol=0.5):
        i0, i1 = int(rate * inicio_s), min(n, int(rate * (inicio_s + largo_s)))
        for i in range(i0, i1):
            t = i / rate - inicio_s
            env = min(1.0, t / 0.02) * max(0.0, 1.0 - t / largo_s) ** 1.5
            salida[i] += (_tri(freq, i / rate) * 0.6 +
                          _square(freq * 2, i / rate, 0.4) * 0.18) * env * vol

    # Fase 0+: el motivo de dos notas está siempre.
    _nota(0.02, dur * 0.38, 164.81)
    _nota(dur * 0.45, dur * 0.5, 246.94)

    if fase >= 1:  # colchón de graves + rumor de 50 Hz + tríada + trémolo
        vol_colchon = STINGER_COLCHON[fase]
        for i in range(n):
            salida[i] += math.sin(2 * math.pi * grave * i / rate) * vol_colchon
        for i in range(n):
            salida[i] += math.sin(2 * math.pi * 50.0 * i / rate) * STINGER_SUB[fase]
        for k, f in enumerate((220.0, 261.63, 329.63)):
            _nota(dur * (0.12 + 0.16 * k), dur * 0.34, f, vol=0.32)
        trem_state = 0.0
        for i in range(n):
            trem_state += (math.sin(2 * math.pi * 8 * i / rate) *
                           math.sin(2 * math.pi * 6.3 * i / rate)) * 0.04
            if 0 <= i < n:
                salida[i] += trem_state

    if fase >= 2:  # tritono + octava abajo + oleada de ruido
        for i in range(int(rate * dur * 0.25), n):
            t = i / rate
            env = 0.35 * min(1.0, (t - dur * 0.25) / 0.15)
            salida[i] += (_square(grave * 2, t, 0.5) * 0.22 +
                          _square(grave * 2 ** (6 / 12), t, 0.5) * 0.2) * env
        rosa = _ruido_rosa(n)
        estado = 0.0
        for i in range(n):
            avance = i / n
            estado_filtro = _paso_pasa_bajos(rosa[i], estado, 1600.0, rate)
            estado = estado_filtro
            salida[i] += estado_filtro * 0.07 * avance

    if fase >= 3:  # clúster + caída de subgraves + cola
        for i in range(int(rate * dur * 0.35), n):
            t = i / rate
            env = min(1.0, (t - dur * 0.35) / 0.1) * max(
                0.0, 1.0 - (t - dur * 0.35) / (dur * 0.65)) ** 1.2
            salida[i] += (_tri(233.08, t) * 0.28 + _tri(246.94, t) * 0.28 +
                          _tri(220.0, t) * 0.24) * env
        for i in range(n):
            t = i / rate
            if t < 0.55:
                f = 90.0 + (38.0 - 90.0) * (t / 0.55)
                env = min(1.0, t / 0.03) * max(0.0, 1.0 - t / 0.55)
                salida[i] += math.sin(2 * math.pi * f * t) * env * 0.85

    if fase == 3:
        salida = _aplicar_reverberacion(salida, rate, decaimiento=0.62,
                                        ecos=9, cola_extra_s=0.5)
    return salida


def _gen_risa_paburu(rate=SAMPLE_RATE):
    """La risa de Paburu (GAP-067, AUD-596): seis estallidos irregulares.

    Cada estallido tiene contorno de tono propio — alterna caída y subida,
    como cualquier risa grabada — sobre un paseo aleatorio de tono base
    (300-520 Hz) con un formante barriendo 700↔1400 Hz. Los huecos entre
    estallidos no son metronómicos: aceleran y se frenan.
    """
    rng = random.Random(20260821)          # semilla fija: reproducible
    gaps = (0.075, 0.135, 0.095, 0.165, 0.115)   # 6 estallidos, 5 huecos
    salidas = []
    tono = 380.0
    arranque = 0.06                        # aire antes de la primera sílaba
    cursor = arranque
    for k in range(len(gaps) + 1):
        largo = rng.uniform(0.055, 0.085)
        n_est = int(rate * largo)
        tono = max(300.0, min(520.0, tono + rng.uniform(-70, 70)))
        sube = (k % 2 == 0)
        f_inicio = tono * (0.82 if sube else 1.14)
        f_fin = tono * (1.16 if sube else 0.84)
        est = []
        for i in range(n_est):
            frac = i / max(1, n_est - 1)
            f = f_inicio + (f_fin - f_inicio) * frac
            formante = 1050.0 + 350.0 * math.sin(math.pi * frac + k)
            crudo = _square(f, cursor + i / rate, 0.42) * 0.7 + \
                _tri(f * 2.01, cursor + i / rate) * 0.3
            paso = _paso_pasa_bajos(crudo, est[-1] if est else 0.0,
                                    formante, rate)
            env = min(1.0, frac / 0.15) * max(0.0, 1.0 - frac) ** 0.8
            est.append(paso * env * (0.75 + 0.25 * rng.random()))
        # Cada sílaba se normaliza al mismo pico antes de mezclar: sin
        # esto, la resonancia del formante de una sílaba afortunada
        # dispara el techo del envolvente y las demás quedan por debajo
        # de cualquier umbral de segmentación (y suenan desiguales).
        pico_est = max(abs(x) for x in est) or 1.0
        est = [x / pico_est * 0.5 for x in est]
        salidas.append(est)
        if k < len(gaps):
            cursor += largo + gaps[k]
    total = int(rate * (cursor + 0.12))
    mezcla = [0.0] * total
    # AUD-596 — la posición de partida de la mezcla es el ARRANQUE fijo,
    # no `cursor`: cuando el bucle de generación termina, `cursor` ya vale
    # «principio de la última sílaba» (~1 s), y usarlo aquí apilaba las
    # seis sílabas al final del fichero, fuera de `total`.
    cursor_muestras = int(rate * arranque)
    for est, gap in zip(salidas, [*gaps, 0], strict=True):
        for i, s in enumerate(est):
            j = cursor_muestras + i
            if j < total:
                mezcla[j] += s
        cursor_muestras += len(est) + int(rate * gap)
    pico = max(abs(x) for x in mezcla) or 1.0
    return [x / pico * 0.8 for x in mezcla]


def _gen_stingers_y_risa():
    print("  Stingers de fase y risa de Paburu (AUD-596)...")
    for fase in range(4):
        destino = A / "sfx" / "stingers" / f"stinger_boss_phase_{fase}.wav"
        _ensure(destino)
        _write_wav(destino, _gen_stinger_de_fase(fase))
    destino = A / "sfx" / "voz" / "sfx_voz_paburu_risa.wav"
    _ensure(destino)
    _write_wav(destino, _gen_risa_paburu())


# ════════════════════════════════════════
# AUD-597 — variantes `_combat` de las pistas de zona (GAP-068)
# ════════════════════════════════════════
#
# `_get_track_for_intensity` busca `{bgm}_combat` antes que `{bgm}_traverse`
# desde siempre, pero ningún fichero llevaba ese nombre: el combate sonaba
# idéntico a la calma. Decisión del dueño (2026-08-21): no habrá composición
# propia, así que la variante se **deriva** de la pista que ya existe — la
# misma pieza con una capa rítmica horneada encima (bombo con caída de
# tono a cada pulso, hi-hats de ruido en los contratiempos, BPM 132), sin
# tocar código del motor. Quedan fuera los `bgm_zoneN_boss` (su base YA es
# combate permanente) y los mp3 de autor del 4-1/4-1b (cada fase trae su
# propia curva compuesta).

#: Pistas base que ganan su `_combat`.
PISTAS_DE_COMBAT = (
    "bgm_stage0",
    "bgm_zone1", "bgm_zone2", "bgm_zone3",
    "bgm_zone1_traverse", "bgm_zone2_traverse", "bgm_zone3_traverse",
)

BPM_COMBAT = 132


def _gen_combat_desde(nombre, rate=SAMPLE_RATE):
    """Hornea `assets/music/<nombre>_combat.wav` desde `<nombre>.wav`.

    Misma duración, mismos canales y mismo sample rate que la fuente — es
    la misma pieza. La capa rítmica se funde a cero en los últimos 100 ms
    para que la vuelta del bucle no haga clic con un bombo cortado.
    """
    import wave as _wave

    origen = A / "music" / f"{nombre}.wav"
    with _wave.open(str(origen), "rb") as wf:
        canales = wf.getnchannels()
        rate_src = wf.getframerate()
        bruto = wf.readframes(wf.getnframes())
    # El ritmo se deriva del rate de la fuente: hay pistas a 22050 y otras
    # a 44100 — la capa tiene que quedar sincronizada en ambas.
    rate = rate_src
    enteros = struct.unpack(f"<{len(bruto) // 2}h", bruto)
    if canales == 2:
        izq = enteros[0::2]
        der = enteros[1::2]
    else:
        izq = der = enteros
    n = len(izq)
    escala = 16384.0

    muestras_beat = int(rate * 60.0 / BPM_COMBAT)
    medio = muestras_beat // 2
    cola_fade = int(rate * 0.10)
    estado_hat = 0.0
    salida_izq = [0.0] * n
    salida_der = [0.0] * n
    for i in range(n):
        # Fuente, apenas adelgazada para dejar sitio al golpe.
        v_i = izq[i] / escala * 0.85
        v_d = der[i] / escala * 0.85
        pos = i % muestras_beat
        t_rel = (i % muestras_beat) / rate
        # Bombo: caída de tono 130→42 Hz en los primeros 90 ms del pulso.
        if pos < int(rate * 0.09):
            f = 130.0 + (42.0 - 130.0) * (pos / (rate * 0.09))
            env = max(0.0, 1.0 - pos / (rate * 0.11)) ** 1.4
            golpe = math.sin(2 * math.pi *
                             (f * t_rel + 0.5 * (f - 42.0) * t_rel * t_rel /
                              max(1e-9, 0.09))
                             ) * env * 0.55
            v_i += golpe
            v_d += golpe
        # Hi-hat en el contratiempo: ruido por primera diferencia (pasa-altos
        # pobre pero suficiente para lo que pide el timbre).
        if medio <= pos < medio + int(rate * 0.03):
            crudo = random.uniform(-1.0, 1.0)
            estado_hat += 0.35 * (crudo - estado_hat)
            chasquido = (crudo - estado_hat) * 0.32
            v_i += chasquido
            v_d += chasquido
        # Fundido de la capa al final del bucle (la fuente sigue entera).
        restante = n - i
        if restante < cola_fade:
            factor = restante / cola_fade
            base_i = izq[i] / escala
            base_d = der[i] / escala
            v_i = base_i + (v_i - base_i) * factor
            v_d = base_d + (v_d - base_d) * factor
        salida_izq[i] = math.tanh(v_i)
        salida_der[i] = math.tanh(v_d)
    destino = A / "music" / f"{nombre}_combat.wav"
    _ensure(destino)
    mx = max(max(abs(x) for x in salida_izq),
             max(abs(x) for x in salida_der)) or 1.0
    norm_i = [int(x / mx * 16383) for x in salida_izq]
    norm_d = [int(x / mx * 16383) for x in salida_der]
    with _wave.open(str(destino), "w") as wf:
        wf.setnchannels(canales)
        wf.setsampwidth(2)
        wf.setframerate(rate)
        if canales == 2:
            intercalado = [v for par in zip(norm_i, norm_d, strict=True)
                           for v in par]
        else:
            intercalado = norm_i
        wf.writeframes(struct.pack(f"<{len(intercalado)}h", *intercalado))


def _gen_pistas_de_combat():
    print("  Variantes _combat de zona (AUD-597)...")
    for nombre in PISTAS_DE_COMBAT:
        _gen_combat_desde(nombre)

# ════════════════════════════════════════
# MAIN
# ════════════════════════════════════════

def main():
    print("=" * 60)
    print("  Legacy of InFest — Complete Asset Generator")
    print("=" * 60)
    print("\nTotal asset count target: ~250+ files")

    print("\n[1/9] Player sprites...")
    _gen_player_all()

    _gen_stingers_y_risa()

    print("\n[2/9] Enemy sprites...")
    _gen_all_enemies()
    _gen_pez_abismal_sheet(A / "sprites" / "enemies" / "stage4_1b" / "enemy_pez_abismal.png")
    _gen_cangrejo_sheet(A / "sprites" / "enemies" / "stage4_1b" / "enemy_cangrejo.png")
    _gen_medusa_sheet(A / "sprites" / "enemies" / "stage4_1b" / "enemy_medusa.png")

    print("\n[3/9] Boss sprites...")
    _gen_all_bosses()
    
    print("\n[4/9] Tilesets...")
    _gen_all_tilesets()
    
    print("\n[5/9] Backgrounds...")
    _gen_all_backgrounds()
    
    print("\n[6/9] UI sprites...")
    _gen_ui_portraits()
    _gen_dialogue_portraits()
    _gen_ui_banners()
    _gen_ui_misc()
    _gen_ui_fonts()
    
    print("\n[7/9] Shared sprites...")
    _gen_shared()
    
    print("\n[8/9] Music...")
    _gen_all_music()
    
    print("\n[9/9] SFX...")
    _gen_all_sfx()
    
    # Count generated files
    total = sum(1 for _ in A.rglob("*") if _.is_file() and _.name != ".gitkeep")
    print(f"\n{'=' * 60}")
    print(f"  Asset generation complete! Total files: {total}")
    print(f"{'=' * 60}")

if __name__ == "__main__":
    main()
