#!/usr/bin/env python3
"""
Export individual frames from sprite sheet PNGs as separate PNG files.
Output goes to custom_assets/ for editing in external tools (Corel, Adobe, etc.).

Usage:
    python tools/export_individual_frames.py                          # export all
    python tools/export_individual_frames.py sprites/player/idle.png  # export one
"""

import sys
from pathlib import Path

from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ASSETS_DIR = PROJECT_ROOT / "assets"
OUT_DIR = PROJECT_ROOT / "custom_assets"

FRAME_SIZES: dict[str, tuple[int, int]] = {
    "player": (32, 32),
    "enemies": (16, 12),
    "bosses": (48, 48),
    "tilesets": (16, 16),
    "backgrounds": (320, 224),
    "ui": (16, 16),
}


def _frames_from_sheet(sheet_path: Path, fw: int, fh: int) -> list[Image.Image]:
    sheet = Image.open(sheet_path).convert("RGBA")
    sw, sh = sheet.size
    frames = []
    for y in range(0, sh, fh):
        for x in range(0, sw, fw):
            if x + fw <= sw and y + fh <= sh:
                frame = sheet.crop((x, y, x + fw, y + fh))
                frames.append(frame)
    return frames


def _guess_frame_size(rel: Path) -> tuple[int, int]:
    for key, size in FRAME_SIZES.items():
        if key in rel.parts:
            return size
    return (32, 32)


def export_sheet(sheet_rel: Path) -> int:
    sheet_path = ASSETS_DIR / sheet_rel
    if not sheet_path.exists():
        print(f"  [SKIP] not found: {sheet_path}")
        return 0
    fw, fh = _guess_frame_size(sheet_rel)
    frames = _frames_from_sheet(sheet_path, fw, fh)
    out_folder = OUT_DIR / sheet_rel.with_suffix("")
    out_folder.mkdir(parents=True, exist_ok=True)
    for i, frame in enumerate(frames):
        out_path = out_folder / f"frame_{i:02d}.png"
        frame.save(out_path)
    print(f"  [OK] {sheet_rel} -> {len(frames)} frames -> {out_folder}")
    return len(frames)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    if len(sys.argv) > 1:
        rel = Path(sys.argv[1])
        export_sheet(rel)
        return 0

    total = 0
    for png in sorted(ASSETS_DIR.rglob("*.png")):
        rel = png.relative_to(ASSETS_DIR)
        if rel.parts[0] in ("sprites", "tilesets", "backgrounds", "ui"):
            total += export_sheet(rel)
    print(f"\nExported {total} total frames to {OUT_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
