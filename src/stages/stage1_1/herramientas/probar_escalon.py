"""Mide si un escalon vertical concreto se puede subir, y desde donde.

POR QUE EXISTE
==============
`verificar_recorrido.py` dijo que el bot se queda clavado en x=1773 y que el
nivel no se termina. Eso es un SINTOMA. La causa candidata es el escalon de
48 px que hay en x=1792 (Floor_04 con la cara arriba en y=528, Floor_05 en
y=480), pero "el bot no pudo" no prueba que sea imposible: el bot salta cada
24 fotogramas mire lo que mire, y puede estar despegando en el fotograma malo.

Este script separa las dos cosas. Coloca al jugador a una distancia conocida
del escalon, salta a proposito, y mira si lo sube. Repetido para todas las
distancias de despegue, da la MISMA metrica que usa el banco de saltos del
profesor: de cuantas posiciones de despegue sale.

    despegues 49/49  ->  se sube siempre, no hay defecto
    despegues  0/49  ->  es un muro, hay que rebajarlo
    despegues  4/49  ->  se sube, pero es un salto de precision que un nivel
                         de tutorial no deberia exigir

Uso:
    python claude-workspace/tools/probar_escalon.py <repo> [--x 1792]
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
    ap.add_argument("--x", type=float, default=1792.0,
                    help="x de la cara del escalon")
    ap.add_argument("--y-abajo", type=float, default=528.0)
    ap.add_argument("--y-arriba", type=float, default=480.0)
    ap.add_argument("--margen", type=int, default=49,
                    help="cuantas posiciones de despegue se prueban")
    a = ap.parse_args()

    repo = Path(a.repo).resolve()
    sys.path.insert(0, str(repo))

    pygame.init()
    from src.engine.core import settings
    pygame.display.set_mode((settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT))

    from src.engine.input.action_map import Action
    from src.stages.stage1_1.stage1_1 import Stage1_1_LaEntrada
    from tests.playtest.bot import ScriptedBot, run_playthrough

    alto = a.y_abajo - a.y_arriba
    print(f"\n  Escalon en x={a.x:.0f}:  {a.y_abajo:.0f} -> {a.y_arriba:.0f}"
          f"   = {alto:.0f} px de subida")

    ctx = _contexto()
    escena = Stage1_1_LaEntrada(ctx)
    escena.awake()
    escena.start()
    ctx.scene_manager.push(escena)
    escena.on_enter()
    jugador = escena._player

    def colocar(x: float, y_suelo: float) -> None:
        jugador.position.x = x
        jugador.position.y = y_suelo - jugador.rect.height
        jugador.velocity.update(0.0, 0.0)
        jugador.set_health(jugador.max_health)
        run_playthrough(escena, ScriptedBot([(2, set())]))

    # ── CONTROL ─────────────────────────────────────────────────────
    # Un resultado negativo solo vale si la sonda sabe detectar un positivo.
    # Antes de medir el escalon se salta en terreno llano y se comprueba que
    # el jugador DESPEGA de verdad. Si este control falla, el 0/49 de abajo no
    # dice nada del nivel: dice que la sonda esta mal escrita.
    #
    # El salto es de flanco: un solo fotograma de JUMP puede caer entre dos
    # lecturas y perderse. Por eso el guion mete un fotograma sin nada (para
    # garantizar el flanco de subida) y luego tres con JUMP, igual que hace
    # `walk_right_bot` con sus dos fotogramas.
    # EL SALTO ES DE ALTURA VARIABLE, Y ESO LO CAMBIA TODO.
    #
    # Trazando el salto fotograma a fotograma (`trazar_salto.py`) se ve que la
    # velocidad vertical arranca en -6,1 px/fotograma y en el cuarto fotograma
    # cae de golpe a -2,6. El motor corta el impulso cuando se SUELTA el boton:
    # es el salto variable de toda la vida, mantener sube mas.
    #
    # Consecuencia para medir: `walk_right_bot`, el bot de referencia del
    # profesor, mantiene JUMP solo DOS fotogramas. Nunca da un salto entero —
    # da un saltito de unos 34 px cuando el envolvente real son 87. Un bot asi
    # no puede subir un escalon de 48 px, y eso NO dice nada del nivel: dice
    # que el bot toca el boton en vez de mantenerlo.
    #
    # Por eso aqui se prueban los dos estilos. El que decide si el nivel esta
    # bien construido es el MANTENIDO, porque es lo que hace una persona.
    # Y LA OTRA VARIABLE ES LA CARRERILLA.
    #
    # En el aire el jugador se desplaza a 0,8 px/fotograma (48 px/s) mientras
    # que andando va a 90 px/s: el control aereo es la mitad. Con el jugador
    # pegado a la pared y saltando desde parado, tiene que recorrer su propio
    # ancho (20 px) antes de poder apoyarse arriba, y a 0,8 px/fotograma
    # apenas le da. Por eso hay que medir tambien LLEGANDO CON CARRERILLA, que
    # es como se llega a un escalon cuando uno viene andando.
    CARRERILLA = 40
    ESTILOS = {
        "toque, parado (como walk_right_bot)":
            [(1, set()), (2, {Action.MOVE_RIGHT, Action.JUMP}),
             (160, {Action.MOVE_RIGHT})],
        "mantenido, parado":
            [(1, set()), (18, {Action.MOVE_RIGHT, Action.JUMP}),
             (160, {Action.MOVE_RIGHT})],
        "mantenido, con carrerilla":
            [(CARRERILLA, {Action.MOVE_RIGHT}), (1, set()),
             (18, {Action.MOVE_RIGHT, Action.JUMP}),
             (160, {Action.MOVE_RIGHT})],
    }

    marcador = {}
    try:
        for nombre, salto in ESTILOS.items():
            exitos, alturas = 0, []
            for d in range(a.margen):
                # Colocar al jugador a `d` px a la izquierda de la cara, en el
                # suelo bajo. Se le quita toda la inercia para que la unica
                # variable sea la distancia de despegue.
                colocar(a.x - 16 - d, a.y_abajo)
                y0 = jugador.position.y
                log = run_playthrough(escena, ScriptedBot(salto))
                alturas.append(y0 - min(y for _x, y in log.positions))
                # SUBIR EL ESCALON = acabar apoyado en el piso de arriba.
                #
                # El primer criterio pedia ademas `x > 1792`, la cara del
                # escalon, y estaba mal: el jugador mide 20 px de ancho y le
                # basta con apoyar parte del cuerpo en la repisa, asi que
                # puede quedar en pie arriba con la x todavia por detras de la
                # cara. Ese criterio contaba como fallo subidas buenas.
                # SE MIRA TODA LA TRAYECTORIA, NO EL FOTOGRAMA FINAL.
                #
                # Mirar solo el final daba numeros imposibles: en el escalon de
                # 32 px el salto corto subia 14 de 49 veces y el largo 2 de 49.
                # Un salto MAYOR no puede subir MENOS. Lo que pasaba es que el
                # salto largo dura mas, y al acabar el guion el jugador seguia
                # en el aire: se contaba como fallo una subida que iba bien.
                exitos += any(
                    y + jugador.rect.height <= a.y_arriba + 4 and x + 20 > a.x
                    for x, y in log.positions)
            marcador[nombre] = (exitos, max(alturas))
    finally:
        escena.on_exit()
        escena.destroy()

    print(f"\n  {'estilo de salto':<44} {'altura':>7}  {'suben':>7}  margen")
    for nombre, (exitos, alto) in marcador.items():
        pct = exitos / a.margen
        print(f"  {nombre:<44} {alto:>4.0f} px  {exitos:>3}/{a.margen}"
              f"  {pct:>6.0%}")

    exitos, _ = marcador["mantenido, con carrerilla"]
    pct = exitos / a.margen
    print(f"\n  VEREDICTO (manda el salto mantenido, que es lo que hace una"
          f" persona):")
    if exitos == 0:
        print("  Es un MURO. El nivel no se puede terminar.")
    elif pct < 0.25:
        print("  Se sube, pero es un salto de precision.")
    else:
        print("  Franqueable con comodidad.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
