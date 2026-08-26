"""
AUD-645 — check_contrast.py: reporte CLI de contraste WCAG del Theme.

Uso:
    python scripts/check_contrast.py
    python scripts/check_contrast.py --level=AAA
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


def _lum(rgb):
    canal = []
    for v in rgb:
        s = v / 255.0
        canal.append(s / 12.92 if s <= 0.04045 else ((s + 0.055) / 1.055) ** 2.4)
    return 0.2126 * canal[0] + 0.7152 * canal[1] + 0.0722 * canal[2]


def _ratio(fg, bg):
    l1, l2 = sorted([_lum(fg), _lum(bg)], reverse=True)
    return (l1 + 0.05) / (l2 + 0.05)


def main() -> int:
    parser = argparse.ArgumentParser(description="Contraste WCAG del Theme")
    parser.add_argument("--level", choices=["AA", "AAA"], default="AA")
    args = parser.parse_args()

    sys.path.insert(0, str(RAIZ))
    from src.engine.ui.theme import Theme

    pares = [
        ("TEXT/BG", Theme.TEXT, Theme.BG),
        ("TEXT/SURFACE", Theme.TEXT, Theme.SURFACE),
        ("TEXT/SURFACE_RAISED", Theme.TEXT, Theme.SURFACE_RAISED),
        ("TEXT_MUTED/BG", Theme.TEXT_MUTED, Theme.BG),
        ("ACCENT/BG", Theme.ACCENT, Theme.BG),
        ("ACCENT/SURFACE", Theme.ACCENT, Theme.SURFACE),
        ("SUCCESS/BG", Theme.SUCCESS, Theme.BG),
        ("DANGER/BG", Theme.DANGER, Theme.BG),
    ]

    umbral_normal = 4.5 if args.level == "AA" else 7.0
    umbral_grande = 3.0 if args.level == "AA" else 4.5

    print(f"Contraste WCAG {args.level} -- umbral normal={umbral_normal}:1, grande={umbral_grande}:1\n")
    print(f"{'Par':<25} {'Ratio':>8} {'Normal':>8} {'Grande':>8} Estado")
    print("-" * 60)

    fallos = 0
    for nombre, fg, bg in pares:
        r = _ratio(fg, bg)
        ok_n = r >= umbral_normal
        ok_g = r >= umbral_grande
        estado = "PASS" if ok_g else ("LARGE" if ok_n else "FAIL")
        if not ok_n and not ok_g:
            fallos += 1
        print(f"{nombre:<25} {r:>7.2f}:1 {'OK' if ok_n else 'X':>6} {'OK' if ok_g else 'X':>6}   {estado}")

    print(f"\n{fallos} par(es) fallan WCAG {args.level}")
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())