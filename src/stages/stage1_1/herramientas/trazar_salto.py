"""Traza el salto fotograma a fotograma para ver que lo esta recortando.

POR QUE EXISTE
==============
`probar_escalon.py` dice que en la hondonada el jugador solo se eleva 56 px
cuando el banco del profesor mide un envolvente de 87,1. La primera hipotesis
—que la plataforma `Plat_02` colgaba encima y le pegaba en la cabeza— se probo
acortandola y NO cambio nada: seguia en 56 px y 1/49.

O sea que la causa es otra, y suponer ya costo un intento. Esto mide.

Compara dos saltos identicos:

    LIBRE   en campo abierto, sin nada encima ni al lado
    MURO    pegado a la pared de la hondonada

Si los dos suben lo mismo, el salto esta bien y el problema es horizontal (el
jugador no consigue DESPLAZARSE sobre el escalon). Si el de muro sube menos,
algo del contacto con la pared esta cortando el salto.

Uso:
    python claude-workspace/tools/trazar_salto.py <repo>
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame  # noqa: E402


def _contexto():
    from src.engine.audio.audio_manager import AudioManager
    from src.engine.core.event_bus import EventBus
    from src.engine.core.game_context import GameContext
    from src.engine.core.save_manager import SaveManager
    from src.engine.input.input_manager import InputManager
    from src.engine.scene.scene_manager import SceneManager
    from src.framework.entities import entity_factory

    entity_factory.ensure_registered()
    ctx = GameContext(
        input_manager=InputManager(), audio_manager=AudioManager(),
        scene_manager=None, event_bus=EventBus(), clock=None,
        save_manager=SaveManager(),
    )
    ctx.scene_manager = SceneManager(ctx)
    return ctx


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("repo", nargs="?", default=".")
    a = ap.parse_args()

    repo = Path(a.repo).resolve()
    sys.path.insert(0, str(repo))

    pygame.init()
    from src.engine.core import settings
    pygame.display.set_mode((settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT))

    from src.engine.input.action_map import Action
    from src.stages.stage1_1.stage1_1 import Stage1_1_LaEntrada
    from tests.playtest.bot import ScriptedBot, run_playthrough

    ctx = _contexto()
    escena = Stage1_1_LaEntrada(ctx)
    escena.awake()
    escena.start()
    ctx.scene_manager.push(escena)
    escena.on_enter()
    jugador = escena._player

    print(f"\n  alto del jugador: {jugador.rect.height} px"
          f"   ancho: {jugador.rect.width} px")

    guion = [(1, set()), (3, {Action.MOVE_RIGHT, Action.JUMP}),
             (60, {Action.MOVE_RIGHT})]

    def salto(nombre: str, x: float, y_suelo: float):
        jugador.position.x = x
        jugador.position.y = y_suelo - jugador.rect.height
        jugador.velocity.update(0.0, 0.0)
        jugador.set_health(jugador.max_health)
        run_playthrough(escena, ScriptedBot([(4, set())]))
        y0 = jugador.position.y
        x0 = jugador.position.x
        log = run_playthrough(escena, ScriptedBot(guion))
        subida = y0 - min(y for _x, y in log.positions)
        avance = max(x for x, _y in log.positions) - x0
        print(f"\n  {nombre}")
        print(f"    arranca en x={x0:.0f} y={y0:.0f}")
        print(f"    sube {subida:.0f} px    avanza {avance:.0f} px")
        print(f"    {'f':>3}  {'x':>7}  {'y':>6}  {'dx':>5}  {'dy':>5}")
        px, py = x0, y0
        for i, (x1, y1) in enumerate(log.positions[:34]):
            print(f"    {i:>3}  {x1:>7.1f}  {y1:>6.1f}"
                  f"  {x1 - px:>5.1f}  {y1 - py:>5.1f}")
            px, py = x1, y1
        return subida, avance

    try:
        # Campo abierto: Floor_03 va de 1120 a 1664 con el techo en 480, y tras
        # acortar Plat_02 (acaba en 1728) no hay nada encima de x=1500.
        libre, av_libre = salto("LIBRE  (Floor_03, x=1500, sin techo)", 1500, 480)
        muro, av_muro = salto("MURO   (hondonada, pegado a la pared)", 1776, 528)
    finally:
        escena.on_exit()
        escena.destroy()

    print("\n  " + "=" * 56)
    print(f"  salto LIBRE : sube {libre:.0f} px, avanza {av_libre:.0f} px")
    print(f"  salto MURO  : sube {muro:.0f} px, avanza {av_muro:.0f} px")
    if libre - muro > 8:
        print("  -> el contacto con la pared RECORTA el salto")
    else:
        print("  -> el salto es el mismo; el problema no es la altura")
    return 0


if __name__ == "__main__":
    sys.exit(main())
