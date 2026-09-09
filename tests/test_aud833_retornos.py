"""AUD-833 — los retornos vuelven a la madre, no a una copia ni al título.

Jerarquía real: DemoMenu abre Progress y UnitTheory con `push`; Options abre
Keybinding con `replace`. Los tres volvían con `replace(...)`, que destruye
la escena de abajo y construye una nueva (se pierde selección y posición) o,
en Keybinding, cae al título perdiendo Opciones. El fix: `pop()` donde hubo
`push`, y memoria de origen donde hubo `replace`.
No se toca: rutas que ya vuelven bien, CANCEL de dos niveles (aborta
operación) ni el contrato embebido (AUD-533).
"""
from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "tests"))


def _ctx_con_demos():
    from test_menu_navigation import ContextManager

    from src.engine.scenes.demo_menu_scene import DemoMenuScene

    ctx = ContextManager()
    ctx.app.context.running = True
    ctx.sm.replace(DemoMenuScene(ctx.app.context))
    ctx.step(10)
    return ctx


def test_progreso_vuelve_al_mismo_temario() -> None:
    ctx = _ctx_con_demos()
    demos = ctx.current
    idx = next(i for i, e in enumerate(demos._entradas) if e.clave == "progress")
    for _ in range(idx):
        ctx.press_key("DOWN")
        ctx.step(3)
    ctx.press_key("CONFIRM")
    ctx.step(10)
    assert type(ctx.current).__name__ == "ProgressScene"
    ctx.press_key("CANCEL")
    ctx.step(10)
    assert ctx.current is demos, (
        "ESC en Progreso construyó un temario nuevo en vez de reanudar el de abajo"
    )


def test_teoria_vuelve_al_mismo_temario() -> None:
    from src.engine.scenes.unit_theory_scene import UnitTheoryScene

    ctx = _ctx_con_demos()
    demos = ctx.current
    entrada = next(e for e in demos._entradas if e.unidad_id)
    ctx.sm.push(UnitTheoryScene(ctx.app.context, entrada.unidad_id))
    ctx.step(10)
    assert type(ctx.current).__name__ == "UnitTheoryScene"
    ctx.press_key("CANCEL")
    ctx.step(10)
    assert ctx.current is demos, (
        "ESC en Teoría construyó un temario nuevo en vez de reanudar el de abajo"
    )


def test_controles_vuelve_a_opciones() -> None:
    from test_menu_navigation import ContextManager

    from src.engine.scenes.options_scene import OptionsScene

    ctx = ContextManager()
    ctx.app.context.running = True
    ctx.sm.replace(OptionsScene(ctx.app.context))
    ctx.step(10)
    opciones = ctx.current
    idx = next(i for i, it in enumerate(opciones._menu.items)
               if it.value == "CONTROLES")
    for _ in range(idx):
        ctx.press_key("DOWN")
        ctx.step(3)
    ctx.press_key("CONFIRM")
    ctx.step(10)
    assert type(ctx.current).__name__ == "KeybindingScene"
    ctx.press_key("CANCEL")
    ctx.step(10)
    assert ctx.current is opciones, (
        "ESC en Controles cayó al título y perdió Opciones"
    )


def test_en_examen_esc_vuelve_a_teoria() -> None:
    """Intencional y documentado: salir a mitad no cuenta como intento."""
    from src.engine.scenes.unit_theory_scene import EXAMEN, TEORIA, UnitTheoryScene

    ctx = _ctx_con_demos()
    entrada = next(e for e in ctx.current._entradas if e.unidad_id)
    escena = UnitTheoryScene(ctx.app.context, entrada.unidad_id)
    ctx.sm.push(escena)
    ctx.step(10)
    escena._modo = EXAMEN
    ctx.press_key("CANCEL")
    ctx.step(10)
    assert escena._modo == TEORIA
    assert ctx.current is escena
