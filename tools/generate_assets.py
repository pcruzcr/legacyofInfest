#!/usr/bin/env python3
"""
Procedural asset generator for Legacy of InFest.
Generates all sprites, backgrounds, UI, tilesets, music, and SFX
using Python's Pillow + wave + struct + math + random — no AI APIs needed.
"""

from __future__ import annotations

import json
import math
import os
import random
import struct
import wave
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageFilter

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ASSETS = PROJECT_ROOT / "assets"

W = 320  # internal width
H = 224  # internal height

random.seed(42)

# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

def _ensure(*paths: Path) -> None:
    for p in paths:
        p.parent.mkdir(parents=True, exist_ok=True)


def _gradient(w: int, h: int, top: tuple[int,int,int],
              bottom: tuple[int,int,int]) -> Image.Image:
    img = Image.new("RGB", (w, h))
    for y in range(h):
        t = y / max(h - 1, 1)
        r = int(top[0] + (bottom[0] - top[0]) * t)
        g = int(top[1] + (bottom[1] - top[1]) * t)
        b = int(top[2] + (bottom[2] - top[2]) * t)
        for x in range(w):
            img.putpixel((x, y), (r, g, b))
    return img


def _perlin_noise(w: int, h: int, scale: float = 12.0) -> list[list[float]]:
    """Simple value noise (Perlin-like) for procedural texture."""
    from random import Random
    rng = Random(42)
    grid_w = int(w / scale) + 2
    grid_h = int(h / scale) + 2
    grid = [[rng.random() for _ in range(grid_w)] for _ in range(grid_h)]
    noise = [[0.0] * w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            fx = x / scale
            fy = y / scale
            ix, iy = int(fx), int(fy)
            dx, dy = fx - ix, fy - iy
            dx = dx * dx * (3 - 2 * dx)
            dy = dy * dy * (3 - 2 * dy)
            n00 = grid[iy][ix]
            n10 = grid[iy][ix + 1]
            n01 = grid[iy + 1][ix]
            n11 = grid[iy + 1][ix + 1]
            nx0 = n00 + (n10 - n00) * dx
            nx1 = n01 + (n11 - n01) * dx
            noise[y][x] = nx0 + (nx1 - nx0) * dy
    return noise


def _apply_noise(img: Image.Image, noise: list[list[float]],
                 strength: float = 40) -> None:
    w, h = img.size
    for y in range(h):
        for x in range(w):
            r, g, b = img.getpixel((x, y))
            n = (noise[y][x] - 0.5) * strength
            img.putpixel((x, y), (
                max(0, min(255, int(r + n))),
                max(0, min(255, int(g + n))),
                max(0, min(255, int(b + n))),
            ))


def _draw_mountains(draw: ImageDraw, w: int, h: int,
                    color: tuple[int,int,int], offset_y: int = 80,
                    segments: int = 12) -> None:
    pts = []
    for i in range(segments + 1):
        x = i * w // segments
        y = offset_y + random.randint(-20, 20)
        pts.append((x, y))
    pts.append((w, h))
    pts.append((0, h))
    draw.polygon(pts, fill=color)


# ──────────────────────────────────────────────
# 1. Backgrounds
# ──────────────────────────────────────────────

def _bg_splash(path: Path) -> None:
    _ensure(path)
    img = _gradient(W, H, (10, 8, 25), (30, 20, 60))
    draw = ImageDraw.Draw(img)
    # Stars
    for _ in range(60):
        x, y = random.randint(0, W - 1), random.randint(0, H // 2)
        r = random.choice([(255, 255, 255, 180), (200, 220, 255, 100)])
        draw.ellipse((x, y, x + 2, y + 2), fill=r)
    # Mountains silhouette
    _draw_mountains(draw, W, H, (15, 12, 40), offset_y=130, segments=8)
    # Ground glow
    draw.ellipse((-40, H - 40, W + 40, H + 40), fill=(20, 15, 50))
    # Moon
    draw.ellipse((W - 80, 20, W - 50, 50), fill=(220, 220, 200, 40))
    draw.ellipse((W - 78, 22, W - 52, 48), fill=(255, 255, 230))
    # Horizontal glow bar
    for y in range(H - 50, H):
        alpha = 1.0 - (y - (H - 50)) / 50.0
        for x in range(W):
            r, g, b = img.getpixel((x, y))
            img.putpixel((x, y), (
                min(255, int(r + 20 * alpha)),
                min(255, int(g + 10 * alpha)),
                min(255, int(b + 30 * alpha)),
            ))
    img.save(path)
    print(f"  Created {path}")


def _bg_title(path: Path) -> None:
    _ensure(path)
    img = _gradient(W, H, (60, 25, 10), (20, 10, 5))
    draw = ImageDraw.Draw(img)
    # Sun/flare glow
    for r in range(60, 10, -5):
        a = 30 - (60 - r) // 2
        draw.ellipse((W // 2 - r, 30 - r, W // 2 + r, 30 + r),
                     fill=(200, 120, 40, a))
    # Ground
    draw.rectangle((0, H - 40, W, H), fill=(40, 25, 10))
    # Particles
    for _ in range(30):
        x, y = random.randint(0, W - 1), random.randint(0, H - 40)
        c = random.choice([(255, 200, 100, 60), (200, 100, 50, 40)])
        draw.ellipse((x, y, x + 2, y + 2), fill=c)
    # Horizontal bars
    for i in range(3):
        y = 60 + i * 30
        draw.line((0, y, W, y), fill=(80, 40, 20, 30), width=1)
    img.save(path)
    print(f"  Created {path}")


def _bg_story(path: Path, idx: int, colors: tuple) -> None:
    _ensure(path)
    top, bot, accent = colors
    img = _gradient(W, H, top, bot)
    draw = ImageDraw.Draw(img)
    n = _perlin_noise(W, H, scale=16.0)
    _apply_noise(img, n, strength=15)
    # Vignette
    for y in range(H):
        for x in range(W):
            dx = abs(x - W / 2) / (W / 2)
            dy = abs(y - H / 2) / (H / 2)
            d = max(dx, dy)
            if d > 0.5:
                t = (d - 0.5) / 0.5
                r, g, b = img.getpixel((x, y))
                img.putpixel((x, y), (
                    int(r * (1 - t * 0.5)),
                    int(g * (1 - t * 0.5)),
                    int(b * (1 - t * 0.5)),
                ))
    # Chapter-specific elements
    if idx == 1:
        # Forest silhouettes
        for i in range(8):
            tx = i * 50 - 10 + random.randint(-10, 10)
            draw.rectangle((tx, 120 + random.randint(-15, 15),
                            tx + 20 + random.randint(-5, 5), H),
                           fill=(0, 40, 20))
    elif idx == 2:
        # Path winding
        pts = [(0, H)]
        for i in range(5):
            pts.append((i * 80 + 20, 150 + random.randint(-20, 20)))
        pts.append((W, H))
        draw.polygon(pts, fill=(40, 20, 10))
    elif idx == 3:
        # Mountain peaks
        pts = [(0, H)]
        for i in range(10):
            x = i * W // 9
            y = 80 + random.randint(-30, 30)
            pts.append((x, y))
        pts.append((W, H))
        draw.polygon(pts, fill=(10, 20, 40))
    img.save(path)
    print(f"  Created {path}")


def _bg_stage0(path: Path) -> None:
    _ensure(path)
    img = _gradient(W, H, (100, 150, 255), (40, 80, 120))
    draw = ImageDraw.Draw(img)
    # Clouds
    for _ in range(5):
        cx = random.randint(0, W)
        cy = random.randint(10, 60)
        for r in range(12, 4, -2):
            draw.ellipse((cx - r, cy - r, cx + r, cy + r),
                         fill=(160, 200, 255, 60))
    # Mountains
    pts = [(0, H)]
    for i in range(12):
        x = i * W // 11
        y = 100 + random.randint(-25, 25)
        pts.append((x, y))
    pts.append((W, H))
    draw.polygon(pts, fill=(30, 60, 80))
    # Trees
    for i in range(10):
        tx = i * 35 + random.randint(-10, 10)
        ty = H - 30 - random.randint(0, 10)
        # Trunk
        draw.rectangle((tx - 2, ty - 10, tx + 2, ty), fill=(60, 40, 20))
        # Foliage
        for r in range(12, 4, -2):
            draw.ellipse((tx - r, ty - 15 - r, tx + r, ty - 15 + r),
                         fill=(20, 60 + r * 3, 20))
    img.save(path)
    print(f"  Created {path}")


# ──────────────────────────────────────────────
# 2. Sprites
# ──────────────────────────────────────────────

def _sprite_player(path: Path) -> None:
    _ensure(path)
    img = Image.new("RGBA", (24, 32), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # Body (blue tunic)
    draw.rectangle((6, 12, 18, 24), fill=(30, 80, 180))
    # Head
    draw.ellipse((7, 3, 17, 13), fill=(220, 180, 140))
    # Hair
    draw.ellipse((7, 2, 17, 8), fill=(80, 50, 20))
    # Eyes
    draw.rectangle((10, 7, 11, 8), fill=(255, 255, 255))
    draw.rectangle((13, 7, 14, 8), fill=(255, 255, 255))
    draw.rectangle((10, 7, 11, 7), fill=(0, 0, 0))
    draw.rectangle((13, 7, 14, 7), fill=(0, 0, 0))
    # Legs
    draw.rectangle((8, 24, 11, 30), fill=(50, 40, 80))
    draw.rectangle((13, 24, 16, 30), fill=(50, 40, 80))
    # Boots
    draw.rectangle((7, 28, 12, 32), fill=(80, 60, 40))
    draw.rectangle((12, 28, 17, 32), fill=(80, 60, 40))
    # Belt
    draw.rectangle((7, 21, 18, 22), fill=(140, 110, 40))
    img.save(path)
    print(f"  Created {path}")


def _sprite_enemy_walker(path: Path) -> None:
    _ensure(path)
    img = Image.new("RGBA", (24, 28), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # Body (red/orange)
    draw.ellipse((4, 8, 20, 22), fill=(180, 40, 30))
    # Shell/back pattern
    for dx in [-6, 0, 6]:
        draw.ellipse((10 + dx - 4, 9, 10 + dx + 4, 15), fill=(140, 30, 20))
    # Head
    draw.ellipse((8, 2, 16, 10), fill=(200, 50, 40))
    # Eyes
    draw.rectangle((9, 4, 11, 6), fill=(255, 255, 0))
    draw.rectangle((13, 4, 15, 6), fill=(255, 255, 0))
    draw.rectangle((9, 4, 10, 5), fill=(0, 0, 0))
    draw.rectangle((13, 4, 14, 5), fill=(0, 0, 0))
    # Legs
    for lx in [8, 12, 16]:
        draw.rectangle((lx - 1, 20, lx + 2, 26), fill=(100, 30, 20))
    img.save(path)
    print(f"  Created {path}")


# ──────────────────────────────────────────────
# 3. Logos
# ──────────────────────────────────────────────

def _logo(path: Path, text: str, width: int = 180, height: int = 50) -> None:
    _ensure(path)
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # Try to use a font, fall back to default
    try:
        fnt = ImageFont.truetype("arial.ttf", 18)
    except Exception:
        fnt = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), text, font=fnt)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    tx = (width - tw) // 2
    ty = (height - th) // 2
    # Shadow
    draw.text((tx + 2, ty + 2), text, fill=(0, 0, 0, 120), font=fnt)
    # Main text with gradient effect
    draw.text((tx, ty), text, fill=(255, 210, 0), font=fnt)
    # Subtle glow
    for r in range(3, 0, -1):
        draw.text((tx, ty), text, fill=(255, 210, 0, 20), font=fnt)
    # Decorative line
    draw.line((10, height - 8, width - 10, height - 8),
              fill=(255, 210, 0, 80), width=1)
    draw.line((10, height - 6, width - 10, height - 6),
              fill=(200, 160, 0, 40), width=1)
    img.save(path)
    print(f"  Created {path}")


# ──────────────────────────────────────────────
# 4. Tileset
# ──────────────────────────────────────────────

def _tileset(path: Path, tile_size: int = 16, cols: int = 8, rows: int = 8) -> None:
    """Generate a tileset: 0=empty, 1=grass, 2=dirt, 3=stone, 4=water, 5=bridge, etc."""
    _ensure(path)
    tw, th = tile_size * cols, tile_size * rows
    img = Image.new("RGBA", (tw, th), (0, 0, 0, 0))

    def _tile(draw: ImageDraw, gx: int, gy: int, ttype: int) -> None:
        ox, oy = gx * tile_size, gy * tile_size
        if ttype == 0:  # empty
            return
        elif ttype == 1:  # grass
            draw.rectangle((ox, oy, ox + tile_size - 1, oy + tile_size - 1),
                           fill=(60, 120, 40))
            # Grass tufts
            for _ in range(4):
                gx2 = ox + 4 + random.randint(0, 8)
                gy2 = oy + 4 + random.randint(0, 8)
                draw.line((gx2, gy2, gx2, gy2 - 3), fill=(40, 160, 40))
            # Border shade
            draw.rectangle((ox, oy, ox + tile_size - 1, oy + tile_size - 1),
                           outline=(40, 100, 30))
        elif ttype == 2:  # dirt
            draw.rectangle((ox, oy, ox + tile_size - 1, oy + tile_size - 1),
                           fill=(120, 80, 40))
            for _ in range(6):
                gx2 = ox + random.randint(2, tile_size - 3)
                gy2 = oy + random.randint(2, tile_size - 3)
                draw.rectangle((gx2, gy2, gx2 + 2, gy2 + 2), fill=(100, 65, 30))
            draw.rectangle((ox, oy, ox + tile_size - 1, oy + tile_size - 1),
                           outline=(80, 55, 25))
        elif ttype == 3:  # stone
            draw.rectangle((ox, oy, ox + tile_size - 1, oy + tile_size - 1),
                           fill=(100, 100, 110))
            # Crack
            draw.line((ox + 3, oy + 3, ox + 10, oy + 8),
                      fill=(70, 70, 80), width=1)
            draw.line((ox + 10, oy + 8, ox + 12, oy + 13),
                      fill=(70, 70, 80), width=1)
            draw.rectangle((ox, oy, ox + tile_size - 1, oy + tile_size - 1),
                           outline=(80, 80, 90))
        elif ttype == 4:  # water
            draw.rectangle((ox, oy, ox + tile_size - 1, oy + tile_size - 1),
                           fill=(30, 60, 130))
            for _ in range(3):
                gx2 = ox + random.randint(2, tile_size - 4)
                draw.line((gx2, oy + 4, gx2 + 6, oy + 4),
                          fill=(50, 100, 180, 100), width=1)
            draw.rectangle((ox, oy, ox + tile_size - 1, oy + tile_size - 1),
                           outline=(20, 40, 100))
        elif ttype == 5:  # bridge
            draw.rectangle((ox, oy, ox + tile_size - 1, oy + tile_size - 1),
                           fill=(100, 70, 40))
            for i in range(3):
                draw.line((ox + 2, oy + 2 + i * 6,
                           ox + tile_size - 3, oy + 2 + i * 6),
                          fill=(70, 50, 30), width=1)
            draw.rectangle((ox, oy, ox + tile_size - 1, oy + tile_size - 1),
                           outline=(60, 40, 20))
        elif ttype == 6:  # wall
            draw.rectangle((ox, oy, ox + tile_size - 1, oy + tile_size - 1),
                           fill=(80, 80, 90))
            for j in range(2):
                for i in range(2):
                    bx = ox + 1 + i * 7
                    by = oy + 1 + j * 7
                    draw.rectangle((bx, by, bx + 5, by + 5),
                                   fill=(90, 90, 105))
            draw.rectangle((ox, oy, ox + tile_size - 1, oy + tile_size - 1),
                           outline=(60, 60, 70))
        elif ttype == 7:  # spike
            draw.rectangle((ox, oy, ox + tile_size - 1, oy + tile_size - 1),
                           fill=(140, 40, 40))
            for i in range(3):
                sx = ox + 2 + i * 5
                draw.polygon([(sx, oy + tile_size - 2),
                              (sx + 2, oy + 2),
                              (sx + 4, oy + tile_size - 2)],
                             fill=(180, 60, 60))
            draw.rectangle((ox, oy, ox + tile_size - 1, oy + tile_size - 1),
                           outline=(100, 20, 20))

    draw = ImageDraw.Draw(img)
    tile_types = [0, 1, 2, 3, 4, 5, 6, 7]
    for gy in range(rows):
        for gx in range(cols):
            tidx = (gy * cols + gx) % len(tile_types)
            _tile(draw, gx, gy, tidx)
    img.save(path)
    print(f"  Created {path}")


# ──────────────────────────────────────────────
# 5. TMX Map (minimal valid pytmx-compatible XML)
# ──────────────────────────────────────────────

def _tmx_stage0(path: Path) -> None:
    _ensure(path)
    map_w, map_h = 40, 15
    tile_w = tile_h = 16

    # Simple map data: 0 = empty, 1 = grass, 2 = dirt floor
    data = [[0] * map_w for _ in range(map_h)]
    # Ground layer (bottom 2 rows)
    for y in range(map_h - 2, map_h):
        for x in range(map_w):
            data[y][x] = 1  # grass
    # Dirt floor (row above ground)
    for x in range(map_w):
        data[map_h - 3][x] = 2  # dirt
    # Platform
    for x in range(8, 18):
        data[8][x] = 2
    for x in range(22, 32):
        data[6][x] = 2

    csv_lines = []
    for y in range(map_h):
        csv_lines.append(",".join(str(data[y][x]) for x in range(map_w)))
    csv_data = "\n".join(csv_lines)

    tmx_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<map version="1.10" tiledversion="1.11.0" orientation="orthogonal"
     renderorder="right-down" width="{map_w}" height="{map_h}"
     tilewidth="{tile_w}" tileheight="{tile_h}" infinite="0"
     nextlayerid="2" nextobjectid="2">
 <tileset firstgid="1" name="tileset_stage0" tilewidth="{tile_w}"
          tileheight="{tile_h}" tilecount="64" columns="8">
  <image source="../../assets/tilesets/tileset_stage0.png"
         width="{tile_w * 8}" height="{tile_h * 8}"/>
 </tileset>
 <layer id="1" name="Ground" width="{map_w}" height="{map_h}">
  <data encoding="csv">
{csv_data}
  </data>
 </layer>
 <objectgroup id="2" name="Objects">
  <object id="1" name="PlayerSpawn" type="SpawnPoint" x="32" y="160"
          width="16" height="16"/>
 </objectgroup>
</map>"""
    path.write_text(tmx_content, encoding="utf-8")
    print(f"  Created {path}")


# ──────────────────────────────────────────────
# 6. Audio: Chiptune Music (.wav)
# ──────────────────────────────────────────────

SAMPLE_RATE = 22050

def _make_square(freq: float, t: float, duty: float = 0.5) -> float:
    p = (t * freq) % 1.0
    return 1.0 if p < duty else -1.0


def _make_saw(freq: float, t: float) -> float:
    return 2.0 * ((t * freq) % 1.0) - 1.0


def _make_triangle(freq: float, t: float) -> float:
    p = 2.0 * ((t * freq) % 1.0)
    return 2.0 * abs(p - 1.0) - 1.0


def _write_wav(path: Path, samples: list[float], rate: int = SAMPLE_RATE) -> None:
    _ensure(path)
    # Normalize
    mx = max(abs(s) for s in samples) or 1.0
    normalized = [int(s / mx * 16383) for s in samples]
    with wave.open(str(path), "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(rate)
        wf.writeframes(struct.pack(f"<{len(normalized)}h", *normalized))
    print(f"  Created {path}")


def _mix(*tracks: list[float]) -> list[float]:
    n = max(len(t) for t in tracks) if tracks else 0
    result = [0.0] * n
    for t in tracks:
        for i in range(len(t)):
            result[i] += t[i]
    return result


def _gen_music_splash(path: Path) -> None:
    """Atmospheric ambient — slow pad with gentle arpeggios."""
    rate = SAMPLE_RATE
    dur = 8.0
    n = int(rate * dur)
    bpm = 80
    beat = 60.0 / bpm

    # Drone
    drone = [0.0] * n
    for i in range(n):
        t = i / rate
        drone[i] = _make_square(55.0, t, 0.5) * 0.15 + _make_saw(55.0, t) * 0.05

    # Slow arpeggios (Am chord)
    notes = [110.0, 130.81, 164.81, 220.0]
    arp = [0.0] * n
    for i in range(n):
        t = i / rate
        note_idx = int(t / (beat * 2)) % len(notes)
        freq = notes[note_idx]
        arp[i] = _make_triangle(freq, t) * 0.08 * max(0, 1 - (t % (beat * 2)) / (beat * 2))

    # Pad
    pad = [0.0] * n
    for i in range(n):
        t = i / rate
        pad[i] = (_make_square(110.0, t, 0.3) * 0.04 +
                  _make_square(164.81, t, 0.3) * 0.03)

    result = _mix(drone, arp, pad)
    # Fade in/out
    fade = int(rate * 0.5)
    for i in range(fade):
        f = i / fade
        result[i] *= f
        result[n - 1 - i] *= f
    _write_wav(path, result)


def _gen_music_title(path: Path) -> None:
    """Upbeat chiptune — square wave melody + bass."""
    rate = SAMPLE_RATE
    dur = 12.0
    n = int(rate * dur)
    bpm = 130
    beat = 60.0 / bpm

    # Bass line (descending)
    bass = [0.0] * n
    bass_notes = [110.0, 98.0, 82.41, 73.42, 110.0, 98.0, 82.41, 73.42]
    for i in range(n):
        t = i / rate
        note_idx = int(t / (beat * 4)) % len(bass_notes)
        freq = bass_notes[note_idx]
        bass[i] = _make_square(freq, t, 0.5) * 0.2

    # Melody (pentatonic)
    melody_notes = [440.0, 523.25, 587.33, 659.25, 523.25,
                    587.33, 659.25, 783.99, 587.33, 523.25,
                    440.0, 523.25, 587.33, 659.25, 783.99, 880.0]
    melody = [0.0] * n
    for i in range(n):
        t = i / rate
        note_idx = int(t / (beat * 2)) % len(melody_notes)
        freq = melody_notes[note_idx]
        env = max(0, 1 - (t % (beat * 2)) / (beat * 2))
        melody[i] = _make_square(freq, t, 0.3) * 0.12 * env

    # Percussion (noise bursts)
    perc = [0.0] * n
    for i in range(n):
        t = i / rate
        beat_pos = t % beat
        if beat_pos < 0.02:
            perc[i] = random.uniform(-0.3, 0.3)
        elif beat_pos > beat * 0.5 and beat_pos < beat * 0.5 + 0.015:
            if int(t / beat) % 2 == 1:
                perc[i] = random.uniform(-0.15, 0.15)
        else:
            perc[i] = 0.0

    result = _mix(bass, melody, perc)
    fade = int(rate * 0.3)
    for i in range(fade):
        f = i / fade
        result[i] *= f
        result[n - 1 - i] *= f
    _write_wav(path, result)


def _gen_music_story(path: Path) -> None:
    """Melancholic piano-like — slow arpeggiated chords."""
    rate = SAMPLE_RATE
    dur = 10.0
    n = int(rate * dur)
    bpm = 70
    beat = 60.0 / bpm

    # Pads
    pads = [0.0] * n
    for i in range(n):
        t = i / rate
        pads[i] = (_make_triangle(220.0, t) * 0.06 +
                   _make_triangle(261.63, t) * 0.05 +
                   _make_triangle(329.63, t) * 0.04)

    # Arpeggio (slow)
    arp_notes = [261.63, 329.63, 392.0, 523.25, 392.0, 329.63]
    arp = [0.0] * n
    for i in range(n):
        t = i / rate
        note_idx = int(t / (beat * 3)) % len(arp_notes)
        freq = arp_notes[note_idx]
        env = max(0, 1 - (t % (beat * 3)) / (beat * 3))
        arp[i] = _make_square(freq, t, 0.4) * 0.10 * env

    # Bass drone
    drone = [0.0] * n
    for i in range(n):
        t = i / rate
        drone[i] = _make_saw(65.41, t) * 0.04

    result = _mix(pads, arp, drone)
    fade = int(rate * 0.5)
    for i in range(fade):
        f = i / fade
        result[i] *= f
        result[n - 1 - i] *= f
    _write_wav(path, result)


def _gen_sfx(path: Path, stype: str) -> None:
    """Generate sound effects."""
    rate = SAMPLE_RATE
    dur = 0.3
    n = int(rate * dur)

    if stype == "jump":
        samples = [0.0] * n
        for i in range(n):
            t = i / rate
            freq = 200.0 + 1200.0 * (t / dur)
            env = 1.0 - t / dur
            samples[i] = _make_square(freq, t, 0.5) * env * 0.3

    elif stype == "hit":
        samples = [0.0] * n
        for i in range(n):
            t = i / rate
            env = 1.0 - t / dur
            samples[i] = (_make_square(100.0, t, 0.5) * 0.2 +
                          random.uniform(-0.4, 0.4) * env * 0.5)

    elif stype == "coin":
        dur = 0.2
        n = int(rate * dur)
        samples = [0.0] * n
        for i in range(n):
            t = i / rate
            freq = 800.0 + 2400.0 * (t / dur)
            env = 1.0 - t / dur
            samples[i] = _make_triangle(freq, t) * env * 0.25

    elif stype == "select":
        dur = 0.1
        n = int(rate * dur)
        samples = [0.0] * n
        for i in range(n):
            t = i / rate
            env = 1.0 - t / dur
            samples[i] = _make_square(600.0, t, 0.5) * env * 0.2 + \
                         _make_square(800.0, t, 0.5) * env * 0.1

    elif stype == "powerup":
        dur = 0.6
        n = int(rate * dur)
        samples = [0.0] * n
        for i in range(n):
            t = i / rate
            freq = 300.0 + 1400.0 * (t / dur)
            env = max(0, 1.0 - (t / dur) ** 2)
            samples[i] = (_make_triangle(freq, t) * env * 0.15 +
                          _make_square(freq * 0.5, t, 0.5) * env * 0.1)

    elif stype == "damage":
        dur = 0.4
        n = int(rate * dur)
        samples = [0.0] * n
        for i in range(n):
            t = i / rate
            freq = 150.0 - 120.0 * (t / dur)
            env = 1.0 - t / dur
            samples[i] = (_make_square(max(30, freq), t, 0.5) * env * 0.3 +
                          random.uniform(-0.3, 0.3) * env * 0.4)

    else:
        samples = [0.0] * n

    _write_wav(path, samples)


# ──────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────

def main() -> None:
    print("=" * 60)
    print("  Legacy of InFest — Procedural Asset Generator")
    print("=" * 60)

    # 1. Backgrounds
    print("\n[1/7] Backgrounds...")
    _bg_splash(ASSETS / "splash" / "bck1.png")
    _bg_title(ASSETS / "title" / "bck1.png")
    _bg_story(ASSETS / "story" / "h01.png", 1, ((20, 30, 10), (5, 15, 5), (40, 100, 20)))
    _bg_story(ASSETS / "story" / "h02.png", 2, ((40, 20, 10), (15, 8, 5), (120, 60, 20)))
    _bg_story(ASSETS / "story" / "h03.png", 3, ((10, 15, 35), (5, 8, 20), (60, 80, 150)))
    _bg_stage0(ASSETS / "backgrounds" / "bg_stage0_far.png")
    _bg_stage0(ASSETS / "backgrounds" / "stage0.png")

    # 2. Sprites
    print("\n[2/7] Sprites...")
    _sprite_player(ASSETS / "sprites" / "player" / "player_idle.png")
    _sprite_enemy_walker(ASSETS / "sprites" / "enemies" / "enemy_walker_walk.png")

    # 3. Logos
    print("\n[3/7] Logos...")
    _logo(ASSETS / "splash" / "logo.png", "Legacy of InFest", 180, 50)
    _logo(ASSETS / "title" / "logo.png", "Legacy of InFest", 180, 50)

    # 4. Tileset
    print("\n[4/7] Tileset...")
    _tileset(ASSETS / "tilesets" / "tileset_stage0.png")
    _tileset(ASSETS / "tileset_stage0.png")  # root fallback copy

    # 5. TMX Map
    print("\n[5/7] Stage 0 TMX map...")
    _tmx_stage0(ASSETS / "maps" / "stage0" / "stage0.tmx")

    # 6. Music
    print("\n[6/7] Music tracks...")
    _gen_music_splash(ASSETS / "splash" / "bck.wav")
    _gen_music_title(ASSETS / "title" / "title.wav")
    _gen_music_story(ASSETS / "story" / "story.wav")

    # 7. SFX
    print("\n[7/7] Sound effects...")
    sfx_dir = ASSETS / "sfx"
    for name in ["jump", "hit", "coin", "select", "powerup", "damage"]:
        _gen_sfx(sfx_dir / f"{name}.wav", name)

    print("\n" + "=" * 60)
    print("  All assets generated successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
