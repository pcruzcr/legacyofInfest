#!/usr/bin/env python3
"""Snap sprite pixels onto the project's declared palettes.

Why (AUD-011)
-------------
``scripts/validate_assets.py`` enforces a fixed palette per sprite category, and
eight committed assets violated it — a step CI ran, and would have failed on,
had CI ever executed (AUD-010). The off-palette colours are not deliberate art
choices: the tilesets carry 21 near-black values like (0,0,0), (0,1,0), (1,1,1),
which is the signature of resampling or lossy re-encoding, not of a pixel artist
picking colours. The player sprites carry a handful of intermediate blues that
look like anti-aliasing introduced by a non-nearest-neighbour scale.

Rather than widen the palette to accept the artefacts — which would defeat the
constraint the course is teaching — this tool maps every offending pixel to its
nearest allowed colour in RGB space. Fully transparent pixels are left alone.

Usage
-----
    python tools/quantize_to_palette.py            # report only
    python tools/quantize_to_palette.py --write    # rewrite the offending files
"""
from __future__ import annotations

import argparse
import fnmatch
import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

logger = logging.getLogger(__name__)

ASSETS_DIR = PROJECT_ROOT / "assets"


def nearest(color: tuple[int, int, int],
            palette: list[tuple[int, int, int]]) -> tuple[int, int, int]:
    """Closest palette entry by squared Euclidean distance in RGB.

    Squared distance is sufficient (monotonic in the true distance) and avoids a
    square root per candidate. RGB rather than a perceptual space because the
    palettes are small and highly separated; the nearest entry is unambiguous.
    """
    cr, cg, cb = color
    best = palette[0]
    best_d = None
    for pr, pg, pb in palette:
        d = (cr - pr) ** 2 + (cg - pg) ** 2 + (cb - pb) ** 2
        if best_d is None or d < best_d:
            best_d, best = d, (pr, pg, pb)
    return best


def quantize(path: Path, palette: set[tuple[int, int, int]], write: bool) -> int:
    """Snap off-palette pixels in ``path``. Returns the number of pixels changed."""
    from PIL import Image

    img = Image.open(path).convert("RGBA")
    pixels = img.load()
    width, height = img.size
    allowed = list(palette)
    cache: dict[tuple[int, int, int], tuple[int, int, int]] = {}
    changed = 0

    for y in range(height):
        for x in range(width):
            r, g, b, a = pixels[x, y]
            if a == 0:
                continue  # fully transparent: colour is irrelevant
            rgb = (r, g, b)
            if rgb in palette:
                continue
            if rgb not in cache:
                cache[rgb] = nearest(rgb, allowed)
            nr, ng, nb = cache[rgb]
            pixels[x, y] = (nr, ng, nb, a)
            changed += 1

    if changed and write:
        img.save(path)
    return changed


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true",
                        help="rewrite files in place (default: report only)")
    args = parser.parse_args(argv)

    from scripts.validate_assets import SPRITE_PALETTES

    total_files = 0
    total_pixels = 0
    for pattern, palette in SPRITE_PALETTES:
        for path in sorted(ASSETS_DIR.rglob("*.png")):
            rel = path.relative_to(ASSETS_DIR).as_posix()
            if not fnmatch.fnmatch(rel, pattern):
                continue
            changed = quantize(path, palette, args.write)
            if changed:
                total_files += 1
                total_pixels += changed
                verb = "snapped" if args.write else "would snap"
                logger.info("  %s %6d px  %s", verb, changed, rel)

    if total_files == 0:
        logger.info("All sprites already conform to their palette.")
        return 0

    logger.info("%s %d pixel(s) across %d file(s)",
                "Snapped" if args.write else "Would snap", total_pixels, total_files)
    if not args.write:
        logger.info("Re-run with --write to apply.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
