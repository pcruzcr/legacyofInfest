"""AUD-832 — el indicador de scroll del título mentía.

El reporte ("no se puede entrar a opciones") no es un bloqueo: la ruta
TITLE→OPTIONS funciona (12 ABAJO + CONFIRM). Lo real es descubrimiento: 14
opciones con 4 visibles y la flecha de subida muerta —leía `_scroll_offset`,
fijo en 0 y que nadie actualiza—, así que nada indicaba que hubiera opciones
arriba. El fix lee la ventana real del kit (`MenuList.filas_visibles()`).
La ruta Title→Options no se toca.
"""
from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "tests"))

GRIS_FLECHA = (200, 200, 200)


def _titulo_abajo_del_todo():
    from test_menu_navigation import ContextManager

    ctx = ContextManager()
    ctx.app.context.running = True
    ctx.replace_to_title()
    for _ in range(12):
        ctx.press_key("DOWN")
        ctx.step(3)
    ctx.step(30)  # converge el desplazamiento del kit
    return ctx


def _hay_flecha_arriba(ctx) -> bool:
    titulo = ctx.current
    y = titulo.primera_fila_y() - 7
    x = ctx.surf.get_width() // 2
    titulo.draw(ctx.surf)
    return ctx.surf.get_at((x, y))[:3] == GRIS_FLECHA


def test_la_flecha_de_subida_aparece_abajo_del_todo() -> None:
    ctx = _titulo_abajo_del_todo()
    assert ctx.current._menu.items[ctx.current._menu.index].label == "OPTIONS"
    assert _hay_flecha_arriba(ctx), (
        "en OPTIONS (puesto 13 de 14) no hay flecha hacia arriba: el "
        "indicador no dice que haya opciones encima"
    )


def test_la_flecha_de_bajada_aparece_al_inicio() -> None:
    """Control: al inicio siempre hubo flecha hacia abajo."""
    from test_menu_navigation import ContextManager

    from src.engine.core import settings
    from src.engine.scenes.demo_common import BOTTOM_BAR_Y

    ctx = ContextManager()
    ctx.app.context.running = True
    ctx.replace_to_title()
    ctx.step(10)
    titulo = ctx.current
    titulo.draw(ctx.surf)
    fondo = BOTTOM_BAR_Y
    pixeles = ctx.surf
    columna = [pixeles.get_at((settings.INTERNAL_WIDTH // 2, y))[:3]
               for y in range(fondo - 4, fondo + 8)]
    assert GRIS_FLECHA in columna, "ni siquiera la flecha de bajada se dibuja"
