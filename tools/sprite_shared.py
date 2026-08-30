"""
Shared constants and utilities for sprite generation
Educational: centralizes shared constants, palettes, and base rendering functions
Used by: pixel_asset_generator, directional_sprites, animation_tween, etc.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from PIL import Image

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

# ... (other palettes would go here, but for brevity I'll include just the ones needed)

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

# ... (abbreviated for brevity - in real file would have all palettes)

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


def _render_pixel_art(width: int, height: int, palette: dict, draw_func: Callable) -> Image.Image:
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