"""
MaxRects Atlas Packer + Manifest Generator
Educational: teaches texture packing, UV mapping, game engine integration
Deterministic: MaxRects bin packing, reproducible output
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from PIL import Image


@dataclass
class FrameRect:
    """Single frame rectangle in atlas"""
    name: str
    x: int
    y: int
    w: int
    h: int
    rotated: bool = False
    trimmed: bool = False
    source_w: int = 0
    source_h: int = 0
    offset_x: int = 0
    offset_y: int = 0

    def to_dict(self) -> dict:
        """TexturePacker compatible format"""
        d = asdict(self)
        d["frame"] = {"x": self.x, "y": self.y, "w": self.w, "h": self.h}
        d["rotated"] = self.rotated
        d["trimmed"] = self.trimmed
        d["spriteSourceSize"] = {"x": self.offset_x, "y": self.offset_y, "w": self.source_w, "h": self.source_h}
        d["sourceSize"] = {"w": self.source_w, "h": self.source_h}
        return d


@dataclass
class FreeRect:
    x: int
    y: int
    w: int
    h: int

    def contains(self, w: int, h: int) -> bool:
        return self.w >= w and self.h >= h


class MaxRectsPacker:
    """MaxRects Bin Packing - Best Area Fit heuristic"""
    
    def __init__(self, padding: int = 2):
        self.padding = padding
        self.free_rects: list[FreeRect] = []
        self.used_rects: list[tuple[int, int, int, int]] = []

    def reset(self, width: int, height: int):
        self.free_rects = [FreeRect(0, 0, width, height)]
        self.used_rects = []

    def _split_free_rect(self, free: FreeRect, placed: tuple[int, int, int, int]) -> list[FreeRect]:
        x, y, w, h = placed
        new_rects = []
        
        if not (x < free.x + free.w and x + w > free.x and y < free.y + free.h and y + h > free.y):
            return [free]
        
        if y > free.y:
            new_rects.append(FreeRect(free.x, free.y, free.w, y - free.y))
        if y + h < free.y + free.h:
            new_rects.append(FreeRect(free.x, y + h, free.w, free.y + free.h - y - h))
        if x > free.x:
            new_rects.append(FreeRect(free.x, free.y, x - free.x, free.h))
        if x + w < free.x + free.w:
            new_rects.append(FreeRect(x + w, free.y, free.x + free.w - x - w, free.h))
        
        return [r for r in new_rects if r.w > 0 and r.h > 0]

    def _prune_free_rects(self):
        i = 0
        while i < len(self.free_rects):
            j = 0
            while j < len(self.free_rects):
                if i != j:
                    r1, r2 = self.free_rects[i], self.free_rects[j]
                    if (r1.x >= r2.x and r1.y >= r2.y and 
                        r1.x + r1.w <= r2.x + r2.w and 
                        r1.y + r1.h <= r2.y + r2.h):
                        self.free_rects.pop(i)
                        i -= 1
                        break
                j += 1
            i += 1

    def pack(self, frames: list[tuple[int, Image.Image]], 
             max_width: int = 2048, max_height: int = 2048) -> tuple[Image.Image, list[FrameRect], int, int]:
        """
        Pack frames into atlas using MaxRects Best Area Fit.
        Returns: (atlas_image, frame_rects, atlas_width, atlas_height)
        """
        sorted_frames = sorted(
            enumerate(frames), 
            key=lambda x: x[1].width * x[1].height, 
            reverse=True
        )
        
        self.free_rects = [FreeRect(0, 0, max_width, max_height)]
        self.used_rects = []
        placements: dict[int, tuple[int, int]] = {}
        
        for idx, frame in sorted_frames:
            pw, ph = frame.width + self.padding, frame.height + self.padding
            
            best_score = float('inf')
            best_pos = None
            
            for _i, free in enumerate(self.free_rects):
                if free.w >= pw and free.h >= ph:
                    score = (free.w - pw) * (free.h - ph)
                    if score < best_score:
                        best_score = score
                        best_pos = (free.x, free.y)
            
            if best_pos is None:
                new_w = max(self.max_width * 2, pw) if hasattr(self, 'max_width') else max(pw, 256)
                new_h = max(self.max_height * 2, ph) if hasattr(self, 'max_height') else max(ph, 256)
                self.__init__(self.padding)
                return self.pack(frames, new_w, new_h)
            
            x, y = best_pos
            self.used_rects.append((x, y, pw, ph))
            
            new_free = []
            for free in self.free_rects:
                new_free.extend(self._split_free_rect(free, (best_pos[0], best_pos[1], pw, ph)))
            self.free_rects = [r for r in new_free if r.w > 0 and r.h > 0]
            self._prune_free_rects()
            
            placements[idx] = (x, y)
            self.max_width = max(getattr(self, 'max_width', 0), x + pw)
            self.max_height = max(getattr(self, 'max_height', 0), y + ph)
        
        atlas_w = max(x + frames[idx].width for idx, (x, y) in placements.items()) if placements else 0
        atlas_h = max(y + frames[idx].height for idx, (x, y) in placements.items()) if placements else 0
        
        atlas_w = ((atlas_w + 3) // 4) * 4
        atlas_h = ((atlas_h + 3) // 4) * 4
        
        atlas = Image.new('RGBA', (atlas_w, atlas_h), (0, 0, 0, 0))
        frame_rects = []
        
        for idx, frame in frames:
            x, y = placements[idx]
            atlas.paste(frame, (x, y))
            
            rect = FrameRect(
                name=f"frame_{idx:03d}",
                x=x, y=y,
                w=frame.width, h=frame.height,
                source_w=frame.width, source_h=frame.height
            )
            frame_rects.append(rect)
        
        return atlas, frame_rects, atlas_w, atlas_h


class SpriteAtlas:
    """High-level atlas generator with multi-format export"""
    
    def __init__(self, padding: int = 2):
        self.padding = padding
        self.packer = MaxRectsPacker(padding=padding)
        self.frames: list[Image.Image] = []
        self.frame_names: list[str] = []
    
    def add_frame(self, frame: Image.Image, name: str = ""):
        self.frames.append(frame)
        self.frame_names.append(name or f"frame_{len(self.frames)-1:03d}")
    
    def build(self) -> tuple[Image.Image, dict]:
        frames_list = list(enumerate(self.frames))
        atlas, rects, w, h = self.packer.pack(frames_list, 2048, 2048)
        
        manifest = {
            "meta": {
                "app": "Legacy of InFest Sprite Atlas Generator",
                "version": "1.0",
                "image": "atlas.png",
                "format": "RGBA8888",
                "size": {"w": w, "h": h},
                "scale": "1"
            },
            "frames": {}
        }
        
        for i, rect in enumerate(rects):
            name = self.frame_names[i] if i < len(self.frame_names) else f"frame_{i:03d}"
            manifest["frames"][name] = rect.to_dict()
        
        return atlas, manifest
    
    def save(self, atlas_path: Path, manifest_path: Path):
        atlas, manifest = self.build()
        atlas.save(atlas_path)
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        print(f"  Atlas saved: {atlas_path}")
        print(f"  Manifest saved: {manifest_path}")


# ─── Export Formats ───

def export_godot_spriteframes(manifest: dict, atlas_path: Path, output_path: Path, 
                               frame_w: int = 32, frame_h: int = 32):
    """Export Godot SpriteFrames .tres format"""
    lines = [
        '[gd_resource type="SpriteFrames" load_steps=2 format=3 uid=uid://xxx]',
        '',
        '[sub_resource type="AtlasTexture" id=1]',
        'atlas = ExtResource("1")',
        f'region = Rect2(0, 0, {frame_w}, {frame_h})',
        '',
        '[resource]',
        'animations = {',
    ]
    
    # Group frames by animation (simplified - assumes naming convention)
    animations = {}
    for name, _data in manifest["frames"].items():
        # Parse animation name from frame name (e.g., "walk_south_001" -> "walk_south")
        parts = name.split('_')
        if len(parts) >= 2:
            anim_name = '_'.join(parts[:-1])
        else:
            anim_name = "default"
        if anim_name not in animations:
            animations[anim_name] = []
        animations[anim_name].append(name)
    
    for anim_name, frames in animations.items():
        lines.append(f'  "{anim_name}": {{')
        lines.append('    frames = [')
        for fname in frames:
            data = manifest["frames"][fname]
            r = data["frame"]
            frame_dict = (
                f'{{"frame": {{"x": {r["x"]}, "y": {r["y"]}, "w": {r["w"]}, "h": {r["h"]}}}, '
                f'"duration": 0.1}}'
            )
            lines.append(f"      {frame_dict},")
        lines.append('    ],')
        lines.append('    "loop": true,')
        lines.append('    "speed": 10.0')
        lines.append('  },')
    
    lines.append('}')
    lines.append('')
    lines.append('[ext_resource path="res://' + atlas_path.name + '" type="Texture2D" id=1]')
    
    with open(output_path, 'w') as f:
        f.write('\n'.join(lines))
    
    print(f"  Godot SpriteFrames exported: {output_path}")


def export_unity_spriteatlas(manifest: dict, atlas_path: Path, output_path: Path):
    """Export Unity Sprite Atlas format (simplified)"""
    pass


def export_aseprite(manifest: dict, atlas_path: Path, output_path: Path):
    """Export Aseprite JSON format"""
    pass


def export_texturepacker(manifest: dict, atlas_path: Path, output_path: Path):
    """Export TexturePacker JSON format (already compatible)"""
    with open(output_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    print(f"  TexturePacker JSON exported: {output_path}")