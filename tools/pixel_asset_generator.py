# /// script
# dependencies = ["pygame-ce>=2.5.0", "numpy>=2.0", "Pillow>=10.0"]
# ///
"""
Pixel Art Asset Generator - Legacy of InFest
NVG/Castlevania style, 16-bit color, procedural generation with fixed palettes.
Generates all game assets from code with style-consistency guarantees.
"""

from __future__ import annotations

import math
import random
import wave as wave_module
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

# ── CONSTANTS ─────────────────────────────────────────────────────
W, H = 320, 224
TILE_SIZE = 16
SPRITE_W, SPRITE_H = 32, 32

# ── NVG-STYLE PALETTES (16 colors max per sprite sheet, 256 global) ──
# Each palette has 16 colors: [transparent, color1, color2, ..., color15]
# Colors are RGB tuples.

PAL_PLAYER = {
    "name": "hooded_protagonist",
    "colors": [
        (0, 0, 0),          # 0: transparent
        (0, 0, 0),          # 1: pure black (outline)
        (15, 20, 35),       # 2: hood shadow (deep gray-blue)
        (35, 50, 75),       # 3: hood mid
        (65, 85, 110),      # 4: hood light
        (140, 110, 80),     # 5: skin warm
        (100, 75, 55),      # 6: skin shadow
        (20, 35, 65),       # 7: cloth dark navy
        (40, 60, 100),      # 8: cloth mid navy
        (120, 85, 45),      # 9: rope brown
        (80, 55, 30),       # 10: rope dark
        (220, 200, 140),    # 11: eye glow (pale gold)
        (255, 255, 255),    # 12: highlight
        (50, 40, 35),       # 13: belt
        (180, 160, 130),    # 14: trim
    ]
}

PAL_ENEMY_WALKER = {
    "name": "infested_walker",
    "colors": [
        (0, 0, 0),
        (20, 15, 10),       # outline dark
        (60, 45, 30),       # body dark brown
        (100, 75, 45),      # body mid
        (140, 110, 70),     # body light
        (180, 60, 30),      # eye glow (red-orange NVG)
        (120, 40, 20),      # vein dark
        (80, 25, 10),       # vein accent
        (200, 180, 150),    # bone
        (50, 30, 15),       # shadow
        (160, 140, 110),    # highlight
        (100, 80, 60),      # joint
        (140, 100, 60),     # muscle
        (90, 70, 50),       # dirt
        (70, 50, 35),       # decay,
    ]
}

PAL_ENEMY_FLYING = {
    "name": "swarm_scout",
    "colors": [
        (0, 0, 0),
        (40, 20, 80),       # outline purple
        (120, 50, 180),     # body purple
        (180, 100, 240),    # body light
        (80, 150, 200),     # wing blue
        (150, 200, 240),    # wing highlight
        (50, 150, 100),     # eye green
        (100, 255, 150),    # eye glow
        (60, 40, 100),      # wing dark
        (200, 150, 255),    # glow
        (30, 15, 50),       # shadow
        (100, 80, 140),     # midtone
        (160, 120, 200),    # highlight
        (80, 40, 120),      # accent
        (40, 80, 120),      # wing shadow
    ]
}

PAL_ENEMY_SHOOTER = {
    "name": "spitter_host",
    "colors": [
        (0, 0, 0),
        (30, 50, 20),       # outline
        (80, 120, 40),      # body dark green
        (120, 180, 60),     # body mid
        (160, 220, 80),     # body light
        (200, 50, 50),      # projectile red
        (255, 100, 100),    # projectile bright
        (60, 40, 20),       # joint
        (100, 70, 40),      # joint light
        (40, 20, 10),       # claw dark
        (140, 100, 60),     # claw
        (50, 100, 30),      # vein
        (30, 70, 20),       # shadow
        (180, 140, 100),    # highlight
        (100, 140, 80),     # midtone
    ]
}

PAL_ENEMY_CHARGER = {
    "name": "brute_charger",
    "colors": [
        (0, 0, 0),
        (30, 25, 20),       # outline
        (80, 60, 40),       # body dark
        (140, 100, 60),     # body mid
        (200, 150, 100),    # body light
        (255, 80, 40),      # rage indicator
        (180, 60, 30),      # rage dark
        (60, 45, 30),       # armor dark
        (100, 75, 50),      # armor
        (50, 35, 25),       # shadow
        (120, 90, 60),      # highlight
        (160, 120, 80),     # skin
        (100, 70, 45),      # joint
        (200, 160, 120),    # bone highlight
        (80, 55, 35),       # dirt
    ]
}

PAL_ENEMY_ARCHER = {
    "name": "needle_archer",
    "colors": [
        (0, 0, 0),
        (20, 30, 40),       # outline
        (60, 80, 100),      # body dark
        (100, 130, 160),    # body mid
        (140, 180, 210),    # body light
        (160, 140, 100),    # wood
        (200, 180, 140),    # wood light
        (80, 60, 40),       # quiver
        (120, 90, 60),      # quiver light
        (200, 50, 50),      # fletching red
        (100, 150, 200),    # eye
        (150, 200, 255),     # eye glow
        (40, 55, 70),       # shadow
        (80, 100, 120),     # joint
        (120, 150, 180),    # highlight
    ]
}

PAL_BOSS_VENADO = {
    "name": "venado_sagrado",
    "colors": [
        (0, 0, 0),
        (26, 74, 30),       # moss dark (#2D4A1E)
        (74, 120, 50),      # moss mid (#4A7832)
        (140, 180, 150),    # moss light (#8CB496)
        (232, 220, 200),    # bone white (#E8DCC8)
        (200, 180, 150),    # bone mid
        (160, 140, 110),    # bone dark
        (107, 68, 35),      # earth brown (#6B4423)
        (140, 110, 70),     # wood
        (200, 184, 150),    # fungus cream (#C8B896)
        (10, 10, 10),       # beetle black
        (26, 26, 46),       # shadow (#1A1A2E)
        (80, 60, 40),       # root tan
        (100, 80, 55),      # root light
        (50, 40, 30),       # dark root
    ]
}

PAL_BOSS_REY = {
    "name": "rey_terciopelo",
    "colors": [
        (0, 0, 0),
        (74, 50, 24),       # terciopelo dark (#4A3218)
        (140, 99, 35),      # terciopelo mid (#8C6432)
        (200, 162, 100),    # terciopelo tan (#C8A264)
        (125, 125, 125),    # decay gray (#7D7D7D)
        (60, 60, 60),       # decay dark (#3C3C3C)
        (50, 160, 80),      # venom green (#32A050)
        (80, 200, 120),     # venom bright (#50C878)
        (10, 10, 20),       # shadow (#0A0A14)
        (180, 150, 200),    # royal purple
        (120, 90, 150),     # royal dark
        (220, 200, 240),    # royal light
        (100, 140, 100),    # decay green
        (160, 140, 120),    # bone
        (80, 100, 80),      # vein,
    ]
}

PAL_BOSS_GAVILAN = {
    "name": "gavilan_camionero",
    "colors": [
        (0, 0, 0),
        (140, 90, 40),      # hawk brown (#8C5A28)
        (200, 140, 60),     # hawk tan (#C88C3C)
        (232, 220, 200),    # hawk white (#E8DCC8)
        (212, 160, 23),     # mask gold (#D4A017)
        (140, 104, 0),      # mask dark gold (#8C6800)
        (30, 107, 107),     # mask teal (#1E6B6B)
        (212, 90, 0),       # mask red-orange (#D45A00)
        (80, 255, 80),      # eye glow (#50FF50)
        (50, 130, 50),      # eye dark
        (200, 160, 120),    # feather light
        (160, 120, 80),     # feather mid
        (100, 70, 40),      # feather dark
        (10, 10, 10),       # shadow (#0A0A0A)
        (180, 140, 100),    # highlight
    ]
}

PAL_BOSS_PABURU = {
    "name": "paburu_shaman",
    "colors": [
        (0, 0, 0),
        (60, 100, 50),      # stone green (#3C6432)
        (90, 140, 80),      # stone mid (#5A8C50)
        (140, 180, 150),    # stone light (#8CB496)
        (30, 60, 30),       # carving shadow (#1E3C1E)
        (80, 255, 80),      # eye glow green (#50FF50)
        (45, 90, 40),       # moss accent (#2D5A28)
        (80, 255, 120),     # spectral bright (#50FF78)
        (40, 200, 80),      # spectral mid (#28C850)
        (10, 100, 40),      # spectral dark (#0A6428)
        (255, 215, 0),      # gold bright (#FFD700)
        (200, 168, 0),      # gold mid (#C8A800)
        (140, 112, 0),      # gold dark (#8C7000)
        (60, 50, 0),        # gold shadow (#3C3200)
        (10, 10, 20),       # pearl black (#0A0A14)
    ]
}

PAL_TILESET_STAGE0 = {
    "name": "stone_corridor",
    "colors": [
        (0, 0, 0),          # 0: transparent
        (15, 15, 25),       # 1: dark shadow
        (35, 40, 55),       # 2: stone dark
        (60, 70, 90),       # 3: stone mid
        (100, 110, 130),    # 4: stone light
        (140, 150, 170),    # 5: stone highlight
        (80, 60, 40),       # 6: wood accent
        (120, 90, 60),      # 7: wood light
        (40, 30, 20),       # 8: wood dark
        (50, 50, 60),       # 9: wall dark
        (80, 80, 95),       # 10: wall mid
        (25, 25, 35),       # 11: wall shadow
        (160, 150, 140),    # 12: bone/moss tint
        (100, 80, 60),      # 13: rust
        (70, 55, 40),       # 14: dirt
    ]
}

PAL_UI = {
    "name": "hud_ui",
    "colors": [
        (0, 0, 0),          # 0: transparent
        (15, 15, 30),       # 1: bg dark
        (30, 35, 55),       # 2: bg mid
        (60, 75, 110),      # 3: border
        (100, 220, 255),    # 4: player blue
        (80, 200, 240),     # 5: player light
        (255, 80, 80),      # 6: enemy red
        (255, 50, 50),      # 7: boss red
        (255, 220, 80),     # 8: checkpoint gold
        (200, 200, 150),    # 9: text normal
        (240, 240, 220),    # 10: text bright
        (150, 150, 170),    # 11: text dim
        (120, 120, 140),    # 12: text disabled
        (100, 100, 120),    # 13: bg light
        (50, 40, 35),       # 14: frame dark
    ]
}

# ── PIXEL ART HELPERS ─────────────────────────────────────────────

def _to_palette_index(color: tuple[int, int, int], palette: dict) -> int:
    """Find nearest color in palette using Manhattan distance."""
    best_idx = 0
    best_dist = float('inf')
    for idx, pal_color in enumerate(palette["colors"]):
        if idx == 0:  # skip transparent
            continue
        dist = abs(color[0] - pal_color[0]) + abs(color[1] - pal_color[1]) + abs(color[2] - pal_color[2])
        if dist < best_dist:
            best_dist = dist
            best_idx = idx
    return best_idx


def _render_pixel_art(width: int, height: int, palette: dict, draw_func) -> Image.Image:
    """Render pixel art using a draw function that returns list of (x, y, color_idx)."""
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    pixels = img.load()
    drawn = draw_func()
    
    for x, y, color_idx in drawn:
        if 0 <= x < width and 0 <= y < height and color_idx > 0:
            r, g, b = palette["colors"][color_idx]
            pixels[x, y] = (r, g, b, 255)
    
    return img


def _save_spritesheet(frames: list[Image.Image], path: Path) -> None:
    """Save frames as horizontal sprite sheet."""
    if not frames:
        return
    
    frame_w, frame_h = frames[0].size
    sheet = Image.new('RGBA', (frame_w * len(frames), frame_h), (0, 0, 0, 0))
    
    for i, frame in enumerate(frames):
        sheet.paste(frame, (i * frame_w, 0))
    
    path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(path)
    print(f"  Generated: {path}")


# ── SPRITE GENERATORS ─────────────────────────────────────────────

def _gen_player_idle(palette: dict) -> list[Image.Image]:
    """Generate 4 idle frames (32x32)"""
    frames = []
    for _f in range(4):
        def draw():
            pts = []
            cx, cy = 16, 16
            # Outline (color 1)
            # Hood (colors 2-4)
            for dy in range(-10, 11):
                for dx in range(-8, 9):
                    dist = abs(dx) + abs(dy)
                    if dist < 11:
                        if 5 < dy < 9:
                            ci = 4  # hood light
                        elif 2 < dy < 6:
                            ci = 3  # hood mid
                        else:
                            ci = 2  # hood shadow
                        pts.append((cx+dx, cy+dy, ci))
            # Eyes (color 11 - pale gold)
            pts.append((cx-3, cy-2, 11))
            pts.append((cx+3, cy-2, 11))
            # Body/robe bottom (colors 7-8)
            for dy in range(8, 14):
                for dx in range(-6, 7):
                    if abs(dx) + abs(dy-11) < 6:
                        pts.append((cx+dx, cy+dy, 8 if dy < 11 else 7))
            return pts
        
        img = _render_pixel_art(SPRITE_W, SPRITE_H, palette, draw)
        frames.append(img)
    return frames


def _gen_player_walk(palette: dict) -> list[Image.Image]:
    """Generate 8 walk frames (32x32)"""
    frames = []
    for f in range(8):
        phase = f * math.pi / 4
        # Bind the loop variable explicitly: a bare closure would
        # capture the *variable*, not its value, so every frame would
        # render with the final iteration's phase (AUD-032, B023).
        def draw(phase=phase):
            pts = []
            cx, cy = 16, 16
            # Hood/head bob
            bob_y = int(math.sin(phase) * 1)
            # Hood (same as idle)
            for dy in range(-10 + bob_y, 11 + bob_y):
                for dx in range(-8, 9):
                    dist = abs(dx) + abs(dy - bob_y)
                    if dist < 11:
                        ci = 2 if dy < -6 + bob_y else (3 if dy < -2 + bob_y else 4)
                        pts.append((cx+dx, cy+dy, ci))
            # Eyes
            pts.append((cx-3, cy-2 + bob_y, 11))
            pts.append((cx+3, cy-2 + bob_y, 11))
            # Body
            for dy in range(8, 14):
                for dx in range(-6, 7):
                    if abs(dx) + abs(dy-11) < 6:
                        pts.append((cx+dx, cy+dy, 8 if dy < 11 else 7))
            # Legs (animated swing)
            leg_swing = int(math.sin(phase) * 3)
            pts.append((cx-3, cy+13, 10))  # left leg
            pts.append((cx+3 + leg_swing, cy+13, 10))  # right leg
            return pts
        
        img = _render_pixel_art(SPRITE_W, SPRITE_H, palette, draw)
        frames.append(img)
    return frames


def _gen_player_attack(palette: dict, is_long: bool = False) -> list[Image.Image]:
    """Generate attack frames"""
    frame_count = 10 if is_long else 6
    frames = []
    for f in range(frame_count):
        t = f / (frame_count - 1) if frame_count > 1 else 0
        # Bind the loop variable explicitly: a bare closure would
        # capture the *variable*, not its value, so every frame would
        # render with the final iteration's phase (AUD-032, B023).
        def draw(t=t):
            pts = []
            cx, cy = 16, 16
            # Hood (static)
            for dy in range(-10, 11):
                for dx in range(-8, 9):
                    dist = abs(dx) + abs(dy)
                    if dist < 11:
                        ci = 2 if dy < -6 else (3 if dy < -2 else 4)
                        pts.append((cx+dx, cy+dy, ci))
            # Eyes
            pts.append((cx-3, cy-2, 11))
            pts.append((cx+3, cy-2, 11))
            # Body
            for dy in range(8, 14):
                for dx in range(-6, 7):
                    if abs(dx) + abs(dy-11) < 6:
                        pts.append((cx+dx, cy+dy, 8 if dy < 11 else 7))
            # Arm/weapon swing
            angle = t * math.pi * 2
            weapon_x = cx + int(math.cos(angle) * 10)
            weapon_y = cy + int(math.sin(angle) * 8)
            for i in range(3):
                pts.append((weapon_x + i, weapon_y, 12 if i == 1 else 10))
            return pts
        
        img = _render_pixel_art(SPRITE_W, SPRITE_H, palette, draw)
        frames.append(img)
    return frames


# ── ENEMY GENERATORS ─────────────────────────────────────────────

def _gen_walker(palette: dict) -> list[Image.Image]:
    """Generate 6 walk frames (20x16)"""
    frames = []
    for f in range(6):
        phase = f * math.pi / 3
        # Bind the loop variable explicitly: a bare closure would
        # capture the *variable*, not its value, so every frame would
        # render with the final iteration's phase (AUD-032, B023).
        def draw(phase=phase):
            pts = []
            cx, cy = 10, 8
            # Body (20x12 approx)
            for dy in range(-5, 7):
                for dx in range(-9, 10):
                    if abs(dx) + abs(dy) < 11:
                        ci = 2 if dy < 0 else (3 if dy < 3 else 4)
                        pts.append((cx+dx, cy+dy, ci))
            # Eyes (color 5 - red glow)
            pts.append((cx-3, cy-2, 5))
            pts.append((cx+3, cy-2, 5))
            # Legs
            swing = int(math.sin(phase) * 2)
            pts.append((cx-4, cy+7, 6))
            pts.append((cx+4 + swing, cy+7, 6))
            return pts
        
        # Scale to 20x16 from internal coordinates
        _render_pixel_art(20, 16, palette, draw)
        # We'll return as-is since our draw is already in 20x16
        # Adjust draw to match 20x16
        # Bind the loop variable explicitly (AUD-032, B023).
        def draw20(phase=phase):
            pts = []
            cx, cy = 10, 8
            for dy in range(-5, 7):
                for dx in range(-9, 10):
                    if abs(dx) + abs(dy) < 11:
                        ci = 2 if dy < 0 else (3 if dy < 3 else 4)
                        pts.append((cx+dx, cy+dy, ci))
            pts.append((cx-3, cy-2, 5))
            pts.append((cx+3, cy-2, 5))
            swing = int(math.sin(phase) * 2)
            pts.append((cx-4, cy+7, 6))
            pts.append((cx+4 + swing, cy+7, 6))
            return pts
        
        img = _render_pixel_art(20, 16, palette, draw20)
        frames.append(img)
    return frames


def _gen_flying(palette: dict) -> list[Image.Image]:
    """Generate 4 flying frames"""
    frames = []
    for f in range(4):
        wing_phase = f * math.pi / 2
        # Bind the loop variable explicitly: a bare closure would
        # capture the *variable*, not its value, so every frame would
        # render with the final iteration's phase (AUD-032, B023).
        def draw(wing_phase=wing_phase):
            pts = []
            cx, cy = 12, 12
            # Body
            for dy in range(-3, 4):
                for dx in range(-3, 4):
                    if abs(dx) + abs(dy) < 4:
                        pts.append((cx+dx, cy+dy, 2))
            # Wings (animated)
            wing_y = int(math.cos(wing_phase) * 4)
            for dx in range(-8, -2):
                pts.append((cx+dx, cy+wing_y, 4))
            for dx in range(3, 9):
                pts.append((cx+dx, cy+wing_y, 4))
            # Eye
            pts.append((cx+1, cy-1, 6))
            return pts
        
        img = _render_pixel_art(24, 24, palette, draw)
        frames.append(img)
    return frames


# ── TILESET GENERATOR ────────────────────────────────────────────

def _gen_tileset_stage0(palette: dict) -> Image.Image:
    """Generate 128x128 tileset with floor, wall, platform, and deco tiles"""
    tileset = Image.new('RGBA', (128, 128), (0, 0, 0, 0))
    draw = ImageDraw.Draw(tileset)
    
    # Helper to fill tile at grid position
    def fill_tile(tx: int, ty: int, color_idx: int):
        if color_idx == 0:
            return
        r, g, b = palette["colors"][color_idx]
        x0, y0 = tx * TILE_SIZE, ty * TILE_SIZE
        draw.rectangle([x0, y0, x0+TILE_SIZE-1, y0+TILE_SIZE-1], fill=(r, g, b))
    
    def draw_tile_border(tx: int, ty: int, highlight: bool = True):
        x0, y0 = tx * TILE_SIZE, ty * TILE_SIZE
        col = palette["colors"][5] if highlight else palette["colors"][2]
        draw.rectangle([x0, y0, x0+TILE_SIZE-1, y0+TILE_SIZE-1], outline=col)
    
    # Column 0-1: Solid floor (dark stone with mortar)
    for ty in range(8):
        for tx in range(2):
            fill_tile(tx, ty, 4)  # stone light
            # Noise texture
            for _ in range(8):
                nx = tx*16 + random.randint(0, 15)
                ny = ty*16 + random.randint(0, 15)
                fill_tile(nx//16, ny//16, random.choice([3, 5, 2]))
    
    # Column 2-3: Solid wall (darker)
    for ty in range(8):
        for tx in range(2, 4):
            fill_tile(tx, ty, 3)
            draw_tile_border(tx, ty, False)
    
    # Column 4-5: Platform edge
    for ty in range(8):
        for tx in range(4, 6):
            fill_tile(tx, ty, 5)  # top part
            fill_tile(tx, ty, 2)  # bottom shadow
    
    # Column 6: Platform top (one-way)
    for ty in range(8):
        fill_tile(6, ty, 5)
        draw.rectangle([96, ty*16, 111, ty*16+2], fill=palette["colors"][6])  # wood trim
    
    # Column 7: Solid corner
    for ty in range(8):
        fill_tile(7, ty, 4)
        draw_tile_border(7, ty)
    
    # Column 8-9: Decorative overlay
    for ty in range(8):
        for tx in range(8, 10):
            fill_tile(tx, ty, 12)  # moss tint
    
    # Column 10-11: Background fill
    for ty in range(8):
        for tx in range(10, 12):
            fill_tile(tx, ty, 2)
    
    # Column 12-15: Special/environment
    # 12: vine (green)
    for ty in range(8):
        fill_tile(12, ty, 3)
        for _ in range(3):
            x = 12*16 + random.randint(2, 13)
            y = ty*16 + random.randint(0, 14)
            draw.line([(x, y), (x+1, y+random.randint(2,5))], fill=palette["colors"][13], width=1)
    
    # 13: torch sconce
    fill_tile(13, 3, 2)
    draw.rectangle([13*16+6, 3*16+4, 13*16+10, 3*16+12], fill=palette["colors"][6])
    draw.ellipse([13*16+7, 3*16+2, 13*16+9, 3*16+6], fill=(255, 140, 40))
    
    return tileset


# ── AUDIO GENERATORS ──────────────────────────────────────────────

def _generate_sfx(path: Path, kind: str, duration: float = 0.3, freq: float = 440.0) -> None:
    """Generate simple SFX using numpy + wave."""
    sample_rate = 22050
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    
    if kind == "jump":
        # Rising pitch sweep
        freq_sweep = np.linspace(200, 400, len(t))
        audio_data = np.sin(2 * np.pi * freq_sweep * t) * np.exp(-t * 4)
    
    elif kind == "attack":
        # Short noise burst with punch
        noise = np.random.uniform(-1, 1, len(t))
        env = np.exp(-t * 20)
        audio_data = noise * env * 0.5 + np.sin(2 * np.pi * 120 * t) * env * 0.5
    
    elif kind == "hurt":
        # Low thud
        audio_data = np.sin(2 * np.pi * 80 * t) * np.exp(-t * 8) * 0.8
    
    elif kind == "parry":
        # High ping
        audio_data = np.sin(2 * np.pi * 880 * t) * np.exp(-t * 15) * 0.6
    
    elif kind == "die":
        # Descending tone
        freq_sweep = np.linspace(300, 50, len(t))
        audio_data = np.sin(2 * np.pi * freq_sweep * t) * np.exp(-t * 2) * 0.7
    
    elif kind == "step":
        # Very short low click
        audio_data = np.sin(2 * np.pi * 60 * t) * np.exp(-t * 40) * 0.4
    
    elif kind == "land":
        # Impact noise
        noise = np.random.uniform(-1, 1, len(t))
        env = np.exp(-t * 12)
        audio_data = noise * env * 0.6
    
    elif kind == "checkpoint":
        # Ascending chime
        audio_data = (np.sin(2 * np.pi * 523 * t) + np.sin(2 * np.pi * 659 * t)) * np.exp(-t * 3) * 0.4
    
    elif kind == "select":
        # Click
        audio_data = np.sin(2 * np.pi * 800 * t) * np.exp(-t * 30) * 0.5
    
    elif kind == "boss_hit":
        # Heavy impact
        audio_data = np.sin(2 * np.pi * 60 * t) * np.exp(-t * 6) * 0.9
    
    else:
        audio_data = np.zeros_like(t)
    
    # Convert to 16-bit
    audio_data = np.clip(audio_data, -1, 1)
    wave_int = (audio_data * 32767).astype(np.int16)
    
    # Stereo
    stereo = np.column_stack((wave_int, wave_int))
    
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave_module.open(str(path), 'wb') as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(stereo.tobytes())
    
    print(f"  Generated SFX: {path}")


def _generate_bgm(path: Path, kind: str, duration: float = 60.0) -> None:
    """Generate loopable BGM using simple harmonic composition."""
    sample_rate = 44100
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    
    # Pentatonic scales for dark fantasy feel
    scales = {
        "stage0": [220, 261, 293, 329, 392, 440],  # A minor pentatonic
        "zone1": [196, 233, 261, 293, 349, 392],   # G minor pentatonic
        "zone2": [174, 220, 261, 293, 329, 392],   # F minor pentatonic
        "zone3": [164, 196, 220, 261, 329, 392],   # E minor pentatonic
        "boss": [110, 130, 146, 164, 196, 220],    # Low A minor
        "title": [261, 329, 392, 523, 659, 783],   # C major pentatonic
        "splash": [392, 494, 587, 784, 988, 1175], # High G major
    }
    
    scale = scales.get(kind, scales["stage0"])
    audio_data = np.zeros_like(t)
    
    # Layered ambient pad
    for i, freq in enumerate(scale[:4]):
        # Slow amplitude modulation for each note
        mod = 0.5 + 0.5 * np.sin(2 * np.pi * (0.1 + i * 0.05) * t)
        note = np.sin(2 * np.pi * freq * t) * 0.15 * mod
        audio_data += note
    
    # Add sub bass
    sub = np.sin(2 * np.pi * scale[0] / 2 * t) * 0.2
    audio_data += sub
    
    # Gentle noise texture
    noise = np.random.uniform(-1, 1, len(t)) * 0.02
    audio_data += noise
    
    # Fade in/out for seamless loop
    fade_samples = int(sample_rate * 2.0)
    audio_data[:fade_samples] *= np.linspace(0, 1, fade_samples)
    audio_data[-fade_samples:] *= np.linspace(1, 0, fade_samples)
    
    # Normalize
    audio_data = np.clip(audio_data / np.max(np.abs(audio_data)) * 0.8, -1, 1)
    wave_int = (audio_data * 32767).astype(np.int16)
    stereo = np.column_stack((wave_int, wave_int))
    
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave_module.open(str(path), 'wb') as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(stereo.tobytes())
    
    print(f"  Generated BGM: {path}")


# ── MAIN GENERATOR ─────────────────────────────────────────────────

class AssetGenerator:
    """Main asset generator orchestrator."""
    
    def __init__(self, output_dir: Path = Path("assets")):
        self.output_dir = output_dir
        random.seed(42)  # Reproducible
        np.random.seed(42)
    
    def generate_all(self) -> None:
        """Generate all assets."""
        print("\n🎨 Legacy of InFest - Asset Generator")
        print("NVG Style • 16-bit Color • Pixel Art • Procedural Generation\n")
        
        self._generate_player()
        self._generate_enemies()
        self._generate_tilesets()
        self._generate_ui()
        self._generate_audio()
        
        print("\n✨ All assets generated!\n")
    
    def _generate_player(self) -> None:
        """Generate player sprites."""
        print("📦 Generating player sprites...")
        base = self.output_dir / "sprites" / "player"
        
        _save_spritesheet(_gen_player_idle(PAL_PLAYER), base / "player_idle.png")
        _save_spritesheet(_gen_player_walk(PAL_PLAYER), base / "player_walk.png")
        _save_spritesheet(_gen_player_attack(PAL_PLAYER, False), base / "player_short_attack.png")
        _save_spritesheet(_gen_player_attack(PAL_PLAYER, True), base / "player_long_attack.png")
    
    def _generate_enemies(self) -> None:
        """Generate enemy sprites."""
        print("📦 Generating enemy sprites...")
        base = self.output_dir / "sprites" / "enemies"
        
        _save_spritesheet(_gen_walker(PAL_ENEMY_WALKER), base / "enemy_walker_walk.png")
        _save_spritesheet(_gen_flying(PAL_ENEMY_FLYING), base / "enemy_fly_zone1.png")
    
    def _generate_tilesets(self) -> None:
        """Generate tilesets."""
        print("📦 Generating tilesets...")
        base = self.output_dir / "tilesets"
        
        tileset = _gen_tileset_stage0(PAL_TILESET_STAGE0)
        tileset.save(base / "tileset_stage0.png")
        print(f"  Generated: {base / 'tileset_stage0.png'}")
    
    def _generate_ui(self) -> None:
        """Generate basic UI elements."""
        print("📦 Generating UI elements...")
        base = self.output_dir / "ui"
        
        # Simple icon placeholder
        heart = Image.new('RGBA', (14, 8), (0, 0, 0, 0))
        draw = ImageDraw.Draw(heart)
        draw.polygon([(7, 0), (14, 3), (7, 8), (0, 3)], fill=(255, 50, 50, 255))
        heart.save(base / "heart_full.png")
        print(f"  Generated: {base / 'heart_full.png'}")
    
    def _generate_audio(self) -> None:
        """Generate SFX and music."""
        print("🔊 Generating audio...")
        sfx_dir = self.output_dir / "sfx" / "player"
        music_dir = self.output_dir / "music"
        
        sfx_types = ["jump", "attack", "hurt", "parry", "die", "step", "land", "checkpoint", "select", "boss_hit"]
        for sfx in sfx_types:
            _generate_sfx(sfx_dir / f"sfx_{sfx}.wav", sfx)
        
        bgm_types = ["stage0", "zone1", "zone2", "zone3", "boss", "title", "splash"]
        for bgm in bgm_types:
            _generate_bgm(music_dir / f"bgm_{bgm}.ogg", bgm)


if __name__ == "__main__":
    gen = AssetGenerator()
    gen.generate_all()