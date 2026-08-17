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


def _gen_pez_abismal_sheet(path, w=14, h=10, frames=4):
    """AUD-519 — el pez abismal de 4.1b: no un bicho con patas como
    `_gen_enemy_sheet` (esa silueta es de tierra firme, no de fosa), sino
    una forma alargada, casi sin rasgos, con un único punto que pulsa —el
    señuelo bioluminiscente— para que se lea como amenaza abisal y no
    como un pez de acuario. La regla de oro de 4-1 (cero enemigos, la
    atmósfera es el desafío) se traduce aquí en «una sola criatura, y que
    apenas se distinga»: el contorno importa menos que el punto de luz
    que se acerca en la oscuridad.

    14×10 por fotograma, no un tamaño propio: es lo que
    `EnemyFlying._load_zone_sprites` pide siempre (`self._sprite_fw/fh`),
    y `EnemyPezAbismal` no lo sobreescribe — cambiar el tamaño aquí sin
    tocar el otro lado descuadraría el recorte de la hoja de sprites.
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
        ondulacion = int(1 * math.sin(f / max(frames - 1, 1) * math.pi * 2))
        draw.ellipse((1, h // 2 - 3 + ondulacion, w - 4, h // 2 + 3 - ondulacion),
                     fill=cuerpo, outline=borde)
        # Cola, apenas un triángulo que se dobla con la ondulación.
        draw.polygon([
            (w - 4, h // 2 - 2),
            (w - 1, h // 2 + ondulacion),
            (w - 4, h // 2 + 2),
        ], fill=borde)
        # El señuelo: pulsa de tamaño, no de posición — es lo primero que
        # se ve venir en la oscuridad, antes que el cuerpo.
        pulso = 1 + (f % 2)
        cx, cy = 2, h // 2
        draw.ellipse((cx - pulso, cy - pulso, cx + pulso, cy + pulso), fill=luz)
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
    # AUD-519 — 4.1b, la variante acuática de 4-1: paleta abisal (nada de
    # verde ni marrón de superficie), lo bastante oscura para que el pez
    # abismal se lea como algo que sale de la propia oscuridad.
    "tileset_stage4_1b": {"floor": (18,32,42), "wall": (10,20,30), "deco": (26,52,58)},
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
    """La piedra de siempre: canto iluminado arriba y junta de mortero."""
    draw.rectangle((ox, oy, ox + ts - 1, oy + ts - 1), fill=base)
    draw.line((ox, oy, ox + ts - 1, oy), fill=luz)
    draw.line((ox, oy + 1, ox + ts - 1, oy + 1),
              fill=tuple((oscuro + claro) // 2
                         for oscuro, claro in zip(base, luz, strict=True)))
    draw.line((ox, oy + ts - 1, ox + ts - 1, oy + ts - 1), fill=CEM_LOSA_SOMBRA)
    # La junta vertical, desplazada, para que dos losas seguidas no se lean como
    # una sola plancha.
    draw.line((ox + ts // 3, oy + 3, ox + ts // 3, oy + ts - 2),
              fill=CEM_LOSA_SOMBRA)


def _gen_tileset_cementerio(path, ts=16, cols=8, rows=8):
    _ensure(path)
    img = Image.new("RGBA", (ts * cols, ts * rows), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    rng = random.Random(4341)

    for indice, clase in enumerate(CEM_ORDEN):
        ox, oy = (indice % cols) * ts, (indice // cols) * ts

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

    img.save(path)


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


def _gen_all_tilesets():
    print("  Tilesets...")
    for name, theme in TILESET_THEMES.items():
        if name == "tileset_cemetery":
            _gen_tileset_cementerio(A / "tilesets" / f"{name}.png")
        elif name == "tileset_stage4_1":
            _gen_tileset_stage4_1(A / "tilesets" / f"{name}.png")
        elif theme == "gothic":
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
    "player": ["jump", "land", "short_attack", "long_attack", "hit_connect", "hurt", "die", "crouch"],
    "enemies": ["hit", "die_small", "die_large", "projectile_fire", "projectile_hit_wall"],
    "bosses": ["venado_stomp", "venado_charge", "venado_vine", "rey_spit", "rey_split",
               "gavilan_dive", "gavilan_mask_beam", "paburu_eye_beam", "paburu_wave",
               "phase_change", "relic_appear"],
    "ui": ["menu_move", "menu_confirm", "menu_cancel", "checkpoint", "stage_banner",
           "game_over", "heart_restore", "stage_complete"],
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
                    "despertar_profundo"],
    # AUD-263 — las voces. GAP-031 decía «el motor sabe reproducir voz y no hay
    # ni un solo fichero», y se dejó así a propósito para no cablear mentiras.
    # Pero **todo** el audio de este juego está sintetizado aquí: los pasos, los
    # jefes, el menú. Una voz de marcador de posición generada por el mismo
    # camino no es una mentira, es la misma clase de recurso que el resto.
    #
    # Son las líneas del venado, el jefe de referencia, en sus dos cambios de
    # fase y en su muerte: lo justo para que `play_voz` tenga un demo real que
    # un estudiante pueda copiar para su propio jefe.
    "voz": ["venado_fase1", "venado_fase2", "venado_muerte"],
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
             "jungle_ambient": 2.0, "datacenter_hum": 2.0, "wind_indoor": 2.0, "cemetery_silence": 2.0,
             "venado_fase1": 0.9, "venado_fase2": 1.1, "venado_muerte": 1.4,
             "rain_ambient": 2.0, "storm_ambient": 2.0, "thunder": 1.6,
             "viento_de_bosque": 2.0, "grito_de_gavilan": 0.7,
             "canto_ancestral": 3.0, "resonancia_solemne": 4.0,
             "despertar_profundo": 1.6}
    
    dur = t_dur.get(name, 0.3)
    n = int(rate * dur)
    
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
    elif name in ("venado_stomp", "venado_charge", "rey_spit", "rey_split",
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
    elif name.startswith("venado_"):
        # AUD-263 — voz de marcador de posición: una vocalización grave con
        # formantes, no una palabra. Un gruñido con inflexión se lee como «una
        # criatura ha dicho algo» sin fingir un idioma, que es lo que hace falta
        # para probar la mezcla —el ducking de la música al 35 %— y para que el
        # estudiante oiga dónde encaja su propia grabación.
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
    _gen_pez_abismal_sheet(A / "sprites" / "enemies" / "stage4_1b" / "enemy_pez_abismal.png")

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
