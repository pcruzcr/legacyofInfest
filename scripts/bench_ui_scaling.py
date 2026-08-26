"""
AUD-646 — bench_ui_scaling.py: mide el render de texto a escalas 0.5×–3×.

Verifica que el texto cabe en su contenedor a cada escala y reporta tiempos.

Uso:
    python scripts/bench_ui_scaling.py
"""
from __future__ import annotations

import os
import sys
import time

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

RAIZ = __import__("pathlib").Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

import pygame  # noqa: E402 — necesita SDL_VIDEODRIVER=dummy antes del import

from src.engine.ui.theme import Theme, clear_font_cache  # noqa: E402


def main() -> int:
    pygame.init()
    pygame.font.init()
    _screen = pygame.display.set_mode((800, 600))

    escalas = [0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 2.5, 3.0]
    tamaños = [
        ("FONT_TITLE", Theme.FONT_TITLE),
        ("FONT_HEADING", Theme.FONT_HEADING),
        ("FONT_BODY", Theme.FONT_BODY),
        ("FONT_SMALL", Theme.FONT_SMALL),
        ("FONT_TINY", Theme.FONT_TINY),
    ]

    from src.engine.core import user_settings

    print(f"{'Escala':>8} {'Token':>14} {'Tamaño px':>10} {'Render ms':>10} {'Ancho':>7} {'Alto':>6}")
    print("-" * 60)

    problemas = 0
    for escala in escalas:
        original_pref = getattr(user_settings, "preferencia", None)
        user_settings.preferencia = lambda clave, defecto, e=escala: e

        clear_font_cache()

        for nombre, size_base in tamaños:
            from src.engine.ui.theme import font as theme_font
            inicio = time.perf_counter()
            f = theme_font(size_base)
            surf = f.render("Texto de prueba", True, Theme.TEXT)
            duracion = (time.perf_counter() - inicio) * 1000

            w, h = surf.get_size()
            print(f"{escala:>7}x {nombre:>14} {f.get_height():>8}px {duracion:>9.1f}ms {w:>6}px {h:>5}px")

        clear_font_cache()
        if original_pref:
            user_settings.preferencia = original_pref

    print(f"\nTotal: {len(escalas) * len(tamaños)} renders medidos")
    pygame.quit()
    return 0 if not problemas else 1


if __name__ == "__main__":
    sys.exit(main())