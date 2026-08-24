"""
Post-processing utilities for sprite sheets
Adopted from agent-sprite-forge / sprite-gen best practices
Deterministic, offline, no AI - Educational focus
"""

from __future__ import annotations

import numpy as np
from PIL import Image


def chroma_key_remove(image: Image.Image, 
                      key_color: tuple[int, int, int] = (255, 0, 255),  # Magenta
                      tolerance: int = 30,
                      feather: int = 2,
                      decontaminate: bool = True) -> Image.Image:
    """
    Remove chroma key background with soft alpha edge.
    Educational: teaches chroma keying, alpha compositing, edge feathering.
    """
    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    
    arr = np.array(image, dtype=np.float32) / 255.0
    key = np.array(key_color, dtype=np.float32) / 255.0
    
    # Distance in RGB space
    diff = np.sqrt(np.sum((arr[:, :, :3] - key) ** 2, axis=2))
    alpha = np.clip((diff - tolerance / 255.0) / (feather / 255.0), 0, 1)
    alpha = 1 - alpha  # Invert: key color becomes transparent
    
    if decontaminate:
        # Remove color spill (color spill = key color bleeding into edges)
        key_rgb = np.array(key_color, dtype=np.float32) / 255.0
        for c in range(3):
            # Remove key color contamination
            spill = (1 - alpha) * key_rgb[c]
            arr[:, :, c] = np.clip(
                arr[:, :, c] - spill * (1 - alpha), 0, 1
            )
    
    arr[:, :, 3] = alpha
    result = (arr * 255).astype(np.uint8)
    return Image.fromarray(result, 'RGBA')


def extract_frames_from_sheet(sheet: Image.Image, 
                              frame_w: int, frame_h: int,
                              cols: int, rows: int,
                              spacing: int = 0,
                              margin: int = 0) -> list[Image.Image]:
    """
    Extract frames from sprite sheet with grid layout.
    Educational: teaches sprite sheet slicing, grid math.
    """
    frames = []
    for row in range(rows):
        for col in range(cols):
            x = margin + col * (frame_w + spacing)
            y = margin + row * (frame_h + spacing)
            if x + frame_w <= sheet.width and y + frame_h <= sheet.height:
                frame = sheet.crop((x, y, x + frame_w, y + frame_h))
                # Trim transparent pixels
                bbox = frame.getbbox()
                if bbox:
                    frame = frame.crop(bbox)
                frames.append(frame)
    return frames


def align_frames(frames: list[Image.Image], 
                 anchor: str = 'bottom-center') -> list[Image.Image]:
    """
    Align frames to common anchor point.
    Educational: teaches frame alignment, coordinate systems.
    """
    if not frames:
        return []
    
    # Find bounding box of all non-transparent pixels
    all_bbox = None
    for frame in frames:
        bbox = frame.getbbox()
        if bbox:
            if all_bbox is None:
                all_bbox = bbox
            else:
                all_bbox = (
                    min(all_bbox[0], bbox[0]),
                    min(all_bbox[1], bbox[1]),
                    max(all_bbox[2], bbox[2]),
                    max(all_bbox[3], bbox[3])
                )
    
    if not all_bbox:
        return frames
    
    # Calculate target anchor position
    max_w = max(f.width for f in frames)
    max_h = max(f.height for f in frames)
    
    if anchor == 'bottom-center':
        anchor_x = max_w // 2
        anchor_y = max_h
    elif anchor == 'center':
        anchor_x = max_w // 2
        anchor_y = max_h // 2
    elif anchor == 'bottom-left':
        anchor_x = 0
        anchor_y = max_h
    else:
        anchor_x = max_w // 2
        anchor_y = max_h
    
    for frame in frames:
        bbox = frame.getbbox() or (0, 0, frame.width, frame.height)
        frame_anchor_x = (bbox[0] + bbox[2]) // 2
        frame_anchor_y = bbox[3]  # bottom
        
        offset_x = anchor_x - frame_anchor_x
        offset_y = anchor_y - frame_anchor_y
        
        canvas = Image.new('RGBA', (max_w, max_h), (0, 0, 0, 0))
        canvas.paste(frame, (offset_x, offset_y))
        yield canvas


def slice_prop_pack(image: Image.Image, grid_w: int, grid_h: int,
                    tile_w: int, tile_h: int,
                    spacing: int = 0) -> list[Image.Image]:
    """
    Slice a prop pack (3x3, 4x4, etc.) into individual sprites.
    Educational: teaches prop packing, texture atlas concepts.
    """
    frames = []
    for row in range(grid_h):
        for col in range(grid_w):
            x = col * (tile_w + spacing)
            y = row * (tile_h + spacing)
            if x + tile_w <= image.width and y + tile_h <= image.height:
                tile = image.crop((x, y, x + tile_w, y + tile_h))
                bbox = tile.getbbox()
                if bbox:
                    tile = tile.crop(bbox)
                frames.append(tile)
    return frames


def export_godot_tileset(atlas: Image.Image, manifest: dict, 
                         output_path: str, tile_size: int = 16):
    """Export Godot TileSet .tres format (stub)"""
    pass


def extract_collision_zones(image: Image.Image, 
                           tile_size: int = 16,
                           solid_colors: list[tuple[int, int, int]] | None = None) -> list[dict]:
    """
    Extract collision zones from tileset.
    Educational: teaches collision detection, tilemap physics.
    """
    if solid_colors is None:
        # Default: non-transparent pixels are solid
        pass
    # Implementation would analyze each tile for collision
    pass