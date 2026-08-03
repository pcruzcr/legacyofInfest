#!/usr/bin/env python3
"""
Complete procedural asset generator for Legacy of InFest.
Generates ALL 250+ professor-owned assets per the Asset Bible (20_ASSET_BIBLE.md).
"""
from __future__ import annotations

import math
import random
import struct
import wave
from pathlib import Path

from PIL import Image, ImageDraw

PROJECT_ROOT = Path(__file__).resolve().parent.parent
A = PROJECT_ROOT / "assets"

W, H = 320, 224
SAMPLE_RATE = 22050
random.seed(42)

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

# ════════════════════════════════════════
# SECTION 1: PLAYER SPRITES (32x32, 9 sheets)
# ════════════════════════════════════════

def _pixel_art(draw, x, y, data, palette):
    """Draw pixel art from string data: '.'=transparent, '0'-'9'=palette index."""
    lines = data.strip().split("\n")
    for row_idx, line in enumerate(lines):
        for col_idx, ch in enumerate(line):
            if ch != '.':
                color = palette.get(int(ch), (255,0,255))
                draw.point((x + col_idx, y + row_idx), fill=color)

PLAYER_PAL = {
    0: (60, 60, 80, 255), 1: (80, 80, 110, 255), 2: (140, 140, 170, 255),
    3: (220, 180, 140, 255), 4: (180, 140, 100, 255), 5: (20, 30, 60, 255),
    6: (40, 50, 90, 255), 7: (100, 80, 50, 255), 8: (60, 50, 30, 255),
    9: (200, 180, 100, 255),
}

# ── Base poses: 32 rows × 32 cols, '.'=transparent, digit=palette index ──

PLAYER_IDLE = """
................................
................................
...........55555.............
..........5566655............
..........5311135............
..........5397935............
..........5311135............
...........55555.............
..........556655.............
........5566..6655...........
.......55..55..55............
......55...55...55............
......55..113355..55..........
......55..113355..55..........
......55..113355..55..........
......55..113355..55..........
.......55..99..55............
.......5555995555............
........55.99.55.............
........55.55.55.............
.......55..55..55............
.......55..55..55............
......55...55...55............
......55...55...55............
.....55....55....55............
.....55....55....55............
....555....55....555...........
....55....5555....55...........
...55.....55..55....55..........
................................
................................
................................
"""

PLAYER_WALK_A = """
................................
................................
...........55555.............
..........5566655............
..........5311135............
..........5397935............
..........5311135............
...........55555.............
..........556655.............
........5566..6655...........
.......55..55..55............
......55...55...55............
......55..113355..55..........
......55..113355..55..........
......55..113355..55..........
......55..113355..55..........
.......55..99..55............
.......5555995555............
........55.99.55.............
........55.55.55.............
......55..55..55..............
......55..55..55..............
.....55...55...55..............
.....55...55...55..............
....55....55....55..............
....55....55....55..............
...555....55....555............
..55.....5555.....55...........
..55.....55..55...55............
................................
................................
................................
"""

PLAYER_WALK_B = """
................................
................................
...........55555.............
..........5566655............
..........5311135............
..........5397935............
..........5311135............
...........55555.............
..........556655.............
........5566..6655...........
.......55..55..55............
......55...55...55............
......55..113355..55..........
......55..113355..55..........
......55..113355..55..........
......55..113355..55..........
.......55..99..55............
.......5555995555............
........55.99.55.............
........55.55.55.............
.......55..55..55............
.......55..55..55............
......55...55...55............
......55...55...55............
.....55....55....55............
.....55....55....55............
....555....55....555...........
...55.....5555.....55..........
...55.....55..55....55.........
................................
................................
................................
"""

PLAYER_JUMP = """
................................
................................
...........55555.............
..........5566655............
..........5311135............
..........5397935............
..........5311135............
...........55555.............
..........556655.............
........5566..6655...........
.......55..55..55............
......55...55...55............
......55001155................
......55..113355................
......55..113355................
......55..113355................
.......55..99..55............
.......5555995555............
........55.99.55.............
........55.55.55.............
.......55..55..55............
.......55..55..55............
......55...55...55............
.....55....55....55............
.....55....55....55............
....55......55......55..........
....55......55......55..........
................................
................................
................................
................................
................................
"""

PLAYER_CROUCH = """
................................
................................
...........55555.............
..........5566655............
..........5311135............
..........5397935............
..........5311135............
...........55555.............
..........556655.............
........5566..6655...........
.......55..55..55............
......55..113355..55..........
......55..113355..55..........
......55..113355..55..........
.......55..99..55............
.......5555995555............
........55.99.55.............
........55.55.55.............
.......55..55..55............
......55...55...55............
.....55....55....55............
....555....55....555...........
....55....5555....55...........
...55.....55..55....55..........
................................
................................
................................
................................
................................
................................
................................
"""

PLAYER_ATTACK = """
................................
................................
...........55555.............
..........5566655............
..........5311135............
..........5397935............
..........5311135............
...........55555.............
..........556655.............
........5566..6655...........
.......55..55..55............
......55...113355..55..........
......55...113355..55..........
......55...113355..55..........
......55...113355..55..........
.......55..99..55............
.......5555995555............
........55.99.55.............
........55.55.55.............
.......55..55..55............
.......55..55..55............
......55...55...55............
......55...55...55............
.....55....55....55............
.....55....55....55............
....555....55....555...........
....55....5555....55...........
...55.....55..55....55..........
...55.....55..55....55..........
................................
................................
................................
"""

def _gen_player_sprite(frames, base_data, fw=32, fh=32):
    """Generate multi-frame player sprite from base pixel data."""
    result = []
    for _fi in range(frames):
        img = Image.new("RGBA", (fw, fh), (0,0,0,0))
        draw = ImageDraw.Draw(img)
        _pixel_art(draw, 0, 0, base_data, PLAYER_PAL)
        result.append(img)
    return result

def _gen_player_walk(frames=8, fw=32, fh=32):
    """Generate walk frames alternating between leg-forward poses."""
    result = []
    for fi in range(frames):
        base = PLAYER_WALK_A if fi % 2 == 0 else PLAYER_WALK_B
        img = Image.new("RGBA", (fw, fh), (0,0,0,0))
        draw = ImageDraw.Draw(img)
        _pixel_art(draw, 0, 0, base, PLAYER_PAL)
        result.append(img)
    # Add subtle body bob per frame
    for i, img in enumerate(result):
        offset = [0, -1, 0, 1, 0, -1, 0, 1][i] if i < 8 else 0
        if offset != 0:
            shifted = Image.new("RGBA", (fw, fh), (0,0,0,0))
            shifted.paste(img, (0, offset))
            result[i] = shifted
    return result

def _gen_player_slashing(sheet_name, frames, fw=32, fh=32):
    """Generate attack frames with progressive arm/sword extension."""
    result = []
    for fi in range(frames):
        data = PLAYER_ATTACK if fi < frames // 2 else PLAYER_IDLE
        img = Image.new("RGBA", (fw, fh), (0,0,0,0))
        draw = ImageDraw.Draw(img)
        _pixel_art(draw, 0, 0, data, PLAYER_PAL)
        # Add sword arc on the right side
        sword_x = 26 + fi * 2
        if sword_x < 34:
            for sy in range(10, 18):
                draw.point((sword_x, sy), fill=(200, 180, 100, 255))
        result.append(img)
    return result

def _gen_player_die(frames=8, fw=32, fh=32):
    """Generate death frames: character collapses."""
    result = []
    for fi in range(frames):
        img = Image.new("RGBA", (fw, fh), (0,0,0,0))
        draw = ImageDraw.Draw(img)
        # Gradually shrink and rotate by cropping
        1.0 - (fi / frames) * 0.5
        _pixel_art(draw, 0, int(8 * fi / frames), PLAYER_IDLE, PLAYER_PAL)
        result.append(img)
    return result

def _gen_player_all():
    print("  Player sprites...")
    base = _gen_player_sprite(6, PLAYER_IDLE)
    _save_sheet(A/"sprites"/"player"/"player_idle.png", base, 32, 32)

    walk = _gen_player_walk(8)
    _save_sheet(A/"sprites"/"player"/"player_walk.png", walk, 32, 32)

    jump = _gen_player_sprite(4, PLAYER_JUMP)
    _save_sheet(A/"sprites"/"player"/"player_jump.png", jump, 32, 32)

    fall = _gen_player_sprite(3, PLAYER_JUMP)
    _save_sheet(A/"sprites"/"player"/"player_fall.png", fall, 32, 32)

    crouch = _gen_player_sprite(3, PLAYER_CROUCH)
    _save_sheet(A/"sprites"/"player"/"player_crouch.png", crouch, 32, 32)

    s_atk = _gen_player_slashing("short_attack", 6)
    _save_sheet(A/"sprites"/"player"/"player_short_attack.png", s_atk, 32, 32)

    l_atk = _gen_player_slashing("long_attack", 10)
    _save_sheet(A/"sprites"/"player"/"player_long_attack.png", l_atk, 32, 32)

    hurt = _gen_player_sprite(4, PLAYER_IDLE)
    _save_sheet(A/"sprites"/"player"/"player_hurt.png", hurt, 32, 32)

    die = _gen_player_die(8)
    _save_sheet(A/"sprites"/"player"/"player_die.png", die, 32, 32)

# ════════════════════════════════════════
# SECTION 2: ENEMY SPRITES per zone
# ════════════════════════════════════════

def _gen_enemy_sheet(path, w, h, frames, color, detail_color):
    """Generate simple enemy spritesheet."""
    imgs = []
    for _f in range(frames):
        img = Image.new("RGBA", (w, h), (0,0,0,0))
        draw = ImageDraw.Draw(img)
        # Body ellipse
        draw.ellipse((2, 2, w-3, h-3), fill=color, outline=detail_color)
        # Eyes
        draw.rectangle((w//4, h//4, w//4+2, h//4+2), fill=(255,255,255))
        draw.rectangle((w*3//4-2, h//4, w*3//4, h//4+2), fill=(255,255,255))
        draw.point((w//4+1, h//4+1), fill=(0,0,0))
        draw.point((w*3//4-1, h//4+1), fill=(0,0,0))
        # Legs
        draw.line((w//4, h-3, w//4-2, h), fill=detail_color)
        draw.line((w*3//4, h-3, w*3//4+2, h), fill=detail_color)
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
}

def _gen_gothic_tileset(path, ts=16, cols=8, rows=8):
    _ensure(path)
    img = Image.new("RGBA", (ts*cols, ts*rows), (0,0,0,0))
    for gy in range(rows):
        for gx in range(cols):
            ox, oy = gx * ts, gy * ts
            tile_idx = (gy * cols + gx) % len(_GOTHIC_TILES)
            tile_data = _GOTHIC_TILES[tile_idx]
            draw = ImageDraw.Draw(img)
            _pixel_art(draw, ox, oy, tile_data, TILESET_PAL)
    img.save(path)

def _gen_procedural_tileset(path, theme, ts=16, cols=8, rows=8):
    _ensure(path)
    img = Image.new("RGBA", (ts*cols, ts*rows), (0,0,0,0))
    draw = ImageDraw.Draw(img)
    for gy in range(rows):
        for gx in range(cols):
            ox, oy = gx * ts, gy * ts
            ttype = (gy * cols + gx) % 8
            if ttype == 0:
                draw.rectangle((ox, oy, ox+ts-1, oy+ts-1), fill=theme["floor"])
            elif ttype == 1:
                draw.rectangle((ox, oy, ox+ts-1, oy+ts-1), fill=theme["wall"])
                for i in range(3):
                    wc = tuple(min(255,c+20) for c in theme["wall"])
                    draw.line((ox+3+i*5, oy+2, ox+3+i*5, oy+ts-3), fill=wc)
            elif ttype == 2:
                draw.rectangle((ox, oy, ox+ts-1, oy+ts-1), fill=theme["floor"])
                draw.rectangle((ox+2, oy+2, ox+ts-3, oy+ts-3), fill=theme["deco"])
            elif ttype == 3:
                draw.rectangle((ox, oy, ox+ts-1, oy+ts-1), fill=theme["wall"])
                wc2 = tuple(min(255,c+30) for c in theme["wall"])
                draw.line((ox, oy, ox+ts-1, oy), fill=wc2)
            elif ttype == 4:
                draw.rectangle((ox, oy, ox+ts-1, oy+ts-1), fill=(30,60,130))
                for i in range(3):
                    draw.line((ox+2+i*5, oy+6, ox+6+i*5, oy+6), fill=(50,100,180))
            elif ttype == 5:
                draw.rectangle((ox, oy, ox+ts-1, oy+ts-1), fill=(100,70,40))
                for i in range(4):
                    draw.line((ox+2, oy+2+i*4, ox+ts-3, oy+2+i*4), fill=(70,50,30))
            elif ttype == 6:
                draw.rectangle((ox, oy, ox+ts-1, oy+ts-1), fill=(140,40,40))
                for i in range(4):
                    draw.polygon([(ox+2+i*4, oy+ts-2), (ox+4+i*4, oy+2), (ox+6+i*4, oy+ts-2)], fill=(180,60,60))
            elif ttype == 7:
                pass
            outline_color = tuple(min(255,c-20) for c in theme["wall"])
            draw.rectangle((ox, oy, ox+ts-1, oy+ts-1), outline=outline_color, width=1)
    img.save(path)

def _gen_all_tilesets():
    print("  Tilesets...")
    for name, theme in TILESET_THEMES.items():
        if theme == "gothic":
            _gen_gothic_tileset(A / "tilesets" / f"{name}.png")
        else:
            _gen_procedural_tileset(A / "tilesets" / f"{name}.png", theme)

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


def _gen_bg_final_far(path, w=320, h=224):
    """Capa lejana: cielo, estrellas, colinas y el círculo de piedra.

    No lleva luna. La dibuja la escena (`stage4_1.py::_dibujar_luna`), porque
    en este nivel la luna **baja acto a acto**: pintarla aquí la dejaría clavada
    en el sitio y el reloj del nivel dejaría de moverse.
    """
    _ensure(path)
    img = _gradient(w, h, CEM_CIELO_ALTO, CEM_CIELO_BAJO)
    draw = ImageDraw.Draw(img)
    rng = random.Random(410)
    horizonte = int(h * CEM_HORIZONTE)
    for _ in range(70):
        sx, sy = rng.randint(0, w - 1), rng.randint(0, int(horizonte * 0.8))
        br = rng.randint(90, 200)
        draw.point((sx, sy), fill=(br, br, int(br * 0.95)))

    # Colinas: dos crestas bajas, la de atrás más clara, para que el horizonte
    # tenga profundidad sin necesitar más capas.
    for cresta, tinte in ((horizonte - 16, (26, 20, 40)),
                          (horizonte, (18, 14, 30))):
        pts = [(0, h)]
        for i in range(13):
            pts.append((i * w // 12, cresta + rng.randint(-7, 7)))
        pts.append((w, h))
        draw.polygon(pts, fill=tinte)

    # El círculo de piedra del acto V (§1 del diseño): siete monolitos en la
    # línea del horizonte. Se ve desde el primer acto — es el sitio al que se
    # camina durante todo el nivel, así que tiene que asomar **por encima** del
    # campo de lápidas de la capa media, no perderse entre ellas.
    base = horizonte - 10
    for i, alto in enumerate((26, 36, 44, 50, 44, 36, 26)):
        mx = int(w * 0.56) + i * 11
        draw.rectangle((mx, base - alto, mx + 7, base), fill=(40, 36, 54))
        # El dintel: dos piedras de pie y una encima es lo que hace que se lea
        # como un círculo ceremonial y no como una valla.
        if i in (1, 4):
            draw.rectangle((mx - 2, base - alto - 5, mx + 20, base - alto),
                           fill=(46, 42, 60))
    img.save(path)


def _gen_bg_final_mid(path, w=640, h=224):
    """Capa media: el campo de lápidas, en silueta contra el cielo."""
    _ensure(path)
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    rng = random.Random(411)
    horizonte = int(h * CEM_HORIZONTE)

    # Dos hileras. La de atrás es más pequeña y más clara: la misma piedra a más
    # distancia, que es lo que convierte una fila de rectángulos en un campo.
    for fila, (base, escala, color) in enumerate((
        (horizonte - 14, 0.7, (44, 42, 56)),
        (horizonte + 2, 1.0, CEM_PIEDRA),
    )):
        x = rng.randint(0, 20)
        while x < w:
            alto = int(rng.randint(14, 26) * escala)
            ancho = int(rng.randint(7, 11) * escala)
            if rng.random() < 0.25:
                _cruz(draw, x, base, alto, color)
            else:
                _lapida(draw, x, base, ancho, alto, color)
            # Un resplandor verde muy tenue al pie de algunas: son las que
            # tienen nombre. El lore le pone al cementerio «luz espectral
            # verde», y esto es lo que la pone en el fondo y no sólo en las
            # partículas.
            if fila == 1 and rng.random() < 0.3:
                halo = Image.new("RGBA", (24, 12), (0, 0, 0, 0))
                ImageDraw.Draw(halo).ellipse((0, 0, 23, 11),
                                             fill=(*CEM_VERDE, 26))
                img.paste(halo, (x - 6, base - 5), halo)
            x += int(rng.randint(22, 40) * escala)

    # El suelo del fondo, para que las lápidas se apoyen en algo.
    draw.rectangle((0, horizonte + 2, w, h), fill=CEM_TIERRA)
    img.save(path)


def _gen_bg_final_near(path, w=960, h=224):
    """Capa cercana: árboles secos y la verja."""
    _ensure(path)
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    rng = random.Random(412)
    horizonte = int(h * CEM_HORIZONTE)
    tronco = (20, 16, 24)

    def _rama(x, y, angulo, largo, nivel):
        """Una rama que se parte en dos hasta agotarse. Tres niveles bastan
        para que el árbol se lea como seco y no como un poste."""
        if nivel == 0 or largo < 4:
            return
        x2 = x + math.cos(angulo) * largo
        y2 = y - math.sin(angulo) * largo
        draw.line((x, y, x2, y2), fill=tronco, width=max(1, nivel))
        _rama(x2, y2, angulo + rng.uniform(0.3, 0.7), largo * 0.62, nivel - 1)
        _rama(x2, y2, angulo - rng.uniform(0.3, 0.7), largo * 0.62, nivel - 1)

    for tx in range(30, w, 150):
        suelo = horizonte + 6
        alto = rng.randint(60, 90)
        draw.line((tx, suelo, tx, suelo - alto), fill=tronco, width=4)
        for _ in range(3):
            _rama(tx, suelo - alto + rng.randint(0, 12),
                  rng.uniform(0.6, 2.5), alto * 0.45, 3)

    # La verja: barrotes y pasamanos. Cierra el cementerio por delante.
    draw.rectangle((0, horizonte - 2, w, horizonte), fill=(26, 24, 32))
    for bx in range(0, w, 12):
        draw.rectangle((bx, horizonte - 10, bx + 1, horizonte), fill=(26, 24, 32))
    draw.rectangle((0, horizonte + 6, w, h), fill=CEM_TIERRA)
    img.save(path)


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

def _gen_ui_hearts():
    print("  UI hearts...")
    ui = A / "ui"
    _ensure(ui)
    states = {
        "heart_full.png": (200, 20, 20),
        "heart_three_quarter.png": (200, 80, 20),
        "heart_half.png": (180, 120, 20),
        "heart_quarter.png": (120, 80, 20),
        "heart_empty.png": (80, 20, 20),
    }
    for fname, color in states.items():
        img = Image.new("RGBA", (14, 8), (0,0,0,0))
        draw = ImageDraw.Draw(img)
        draw.ellipse((0, 0, 6, 6), fill=color, outline=(255,255,255,100))
        draw.ellipse((8, 0, 14, 6), fill=color, outline=(255,255,255,100))
        draw.polygon([(1,4), (7,8), (13,4)], fill=color, outline=(255,255,255,100))
        img.save(ui / fname)

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

def _gen_ui_banners():
    print("  UI banners...")
    ui = A / "ui"
    for fname in ["banner_top.png", "banner_bottom.png"]:
        img = Image.new("RGBA", (W, 24), (0,0,0,180))
        draw = ImageDraw.Draw(img)
        draw.rectangle((0, 0, W-1, 23), outline=(200, 180, 100, 200), width=1)
        img.save(ui / fname)

def _gen_ui_misc():
    print("  UI misc...")
    ui = A / "ui"
    items = {
        "hud_frame.png": (36, 36, (60, 60, 80)),
        "message_arrow.png": (5, 7, (255, 215, 0)),
        "menu_arrow.png": (5, 8, (255, 215, 0)),
        "heart_sparkle.png": (8, 8, (255, 255, 200)),
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
    # Checkpoint (16x32, 6 frames active)
    imgs = []
    for f in range(6):
        img = Image.new("RGBA", (16, 32), (0,0,0,0))
        draw = ImageDraw.Draw(img)
        color = (255, 215, 0) if f > 0 else (120, 120, 120)
        draw.rectangle((5, 0, 11, 28), fill=(80, 60, 40))
        draw.ellipse((2, 20, 14, 30), fill=color)
        imgs.append(img)
    _save_sheet(sd / "checkpoint.png", imgs, 16, 32)

    # Torch (8x16, 4 frames)
    imgs = []
    for f in range(4):
        img = Image.new("RGBA", (8, 16), (0,0,0,0))
        draw = ImageDraw.Draw(img)
        draw.rectangle((3, 10, 5, 16), fill=(60, 40, 20))
        flame = [(255, 200, 50), (255, 150, 30), (200, 100, 20), (150, 80, 10)][f]
        draw.ellipse((1, 2, 7, 12), fill=flame)
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

def _write_wav(path, samples, rate=SAMPLE_RATE):
    _ensure(path)
    mx = max(abs(s) for s in samples) or 1.0
    norm = [int(s / mx * 16383) for s in samples]
    with wave.open(str(path), "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(rate)
        wf.writeframes(struct.pack(f"<{len(norm)}h", *norm))

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
    "bgm_final_approach": {"bpm": 60, "dur": 10, "notes": [65.41, 82.41, 98, 130.81], "desc": "ritual"},
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

def _gen_all_music():
    print("  Music...")
    mdir = A / "music"
    _ensure(mdir)
    for name, defn in MUSIC_DEFS.items():
        samples = _gen_music_track(name, defn)
        _write_wav(mdir / f"{name}.wav", samples)

# ════════════════════════════════════════
# SECTION 9: SOUND EFFECTS
# ════════════════════════════════════════

SFX_CATEGORIES = {
    "player": ["jump", "land", "short_attack", "long_attack", "hit_connect", "hurt", "die", "crouch"],
    "enemies": ["hit", "die_small", "die_large", "projectile_fire", "projectile_hit_wall"],
    "bosses": ["venado_stomp", "venado_charge", "venado_vine", "rey_spit", "rey_split",
               "gavilan_dive", "gavilan_mask_beam", "paburu_eye_beam", "paburu_wave",
               "phase_change", "relic_appear"],
    "ui": ["menu_move", "menu_confirm", "menu_cancel", "checkpoint", "stage_banner",
           "game_over", "heart_restore", "stage_complete"],
    "environment": ["jungle_ambient", "datacenter_hum", "wind_indoor", "cemetery_silence",
                    "screen_shake", "hazard_zone", "one_way_platform"],
}

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
             "jungle_ambient": 2.0, "datacenter_hum": 2.0, "wind_indoor": 2.0, "cemetery_silence": 2.0}
    
    dur = t_dur.get(name, 0.3)
    n = int(rate * dur)
    
    if name in ("jungle_ambient", "datacenter_hum", "wind_indoor", "cemetery_silence"):
        samples = [random.uniform(-0.05, 0.05) * max(0, 1 - i/n) for i in range(n)]
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
    elif name in ("venado_stomp", "venado_charge", "rey_spit", "rey_split",
                  "gavilan_dive", "gavilan_mask_beam", "paburu_eye_beam", "paburu_wave"):
        samples = []
        for i in range(n):
            t = i / rate
            env = max(0, 1 - t / dur)
            samples.append(_square(100, t, 0.3) * 0.2 + _square(150, t, 0.3) * 0.15 + random.uniform(-0.2, 0.2) * env)
    else:
        samples = [0.0] * n
    
    return samples

def _gen_all_sfx():
    print("  SFX...")
    for cat, names in SFX_CATEGORIES.items():
        for name in names:
            sdir = A / "sfx" / cat
            samples = _gen_sfx(name)
            _write_wav(sdir / f"sfx_{cat}_{name}.wav", samples)

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
    
    print("\n[2/9] Enemy sprites...")
    _gen_all_enemies()
    
    print("\n[3/9] Boss sprites...")
    _gen_all_bosses()
    
    print("\n[4/9] Tilesets...")
    _gen_all_tilesets()
    
    print("\n[5/9] Backgrounds...")
    _gen_all_backgrounds()
    
    print("\n[6/9] UI sprites...")
    _gen_ui_hearts()
    _gen_ui_portraits()
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
