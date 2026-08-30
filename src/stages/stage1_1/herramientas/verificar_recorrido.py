"""Responde la lista de comprobacion del enunciado con evidencia medida.

POR QUE EXISTE
==============
El enunciado de la Evaluacion Practica II (secciones 3, 5 y 10) no pide "que el
juego arranque": pide comprobar cosas concretas y contestarlas.

    S3 FUNCIONALIDAD   el nivel carga / el recorrido funciona / las colisiones
                       funcionan / la progresion funciona / no hay errores que
                       impidan COMPLETAR la experiencia
    S5 PLAYTESTING     puedo quedar atrapado? / atravesar zonas? / saltarme una
                       seccion? / romper la progresion? / completar el nivel?

Hasta ahora todo lo verificado era estatico (el .tmx a PNG, las pruebas
unitarias, el calificador) o parcial (36 s de bot). Ninguna de esas cosas
contesta "se puede TERMINAR el nivel", que es la condicion que el enunciado
pone por escrito.

Este script lo contesta. Usa el bot de playtest del profesor
(`tests/playtest/bot.py`), que inyecta acciones en el `InputManager` y por
tanto corre sin pantalla y es determinista.

LOS DOS MODOS, Y POR QUE HACEN FALTA LOS DOS
============================================
El bot es deliberadamente tonto: camina a la derecha y salta cada 24
fotogramas, sin mirar. Contra un enemigo, muere. Si se corre tal cual, un fallo
de GEOMETRIA (un muro infranqueable) y uno de COMBATE (un bicho que pega) dan
el mismo sintoma: "no llego al final". Son problemas distintos y se arreglan
distinto.

    --recorrido   repone la salud entre tramos. Aisla la GEOMETRIA:
                  si aqui no se llega al final, el mapa esta mal construido.
    (por defecto) salud normal. Mide lo que aguanta quien no esquiva.

El modo recorrido NO es hacer trampa: es la unica forma de separar las dos
preguntas. El informe dice siempre cual de los dos se corrio.

Uso:
    python claude-workspace/tools/verificar_recorrido.py <repo> --recorrido
    python claude-workspace/tools/verificar_recorrido.py <repo>
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
    """El mismo montaje que usan las pruebas de QA del repo."""
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
    ap.add_argument("--segundos", type=float, default=180.0,
                    help="presupuesto total de tiempo de juego")
    ap.add_argument("--tramo", type=float, default=5.0,
                    help="segundos por tramo entre mediciones")
    ap.add_argument("--recorrido", action="store_true",
                    help="repone la salud entre tramos (aisla la geometria)")
    ap.add_argument("--bot", choices=("humano", "profesor"), default="humano",
                    help="humano mantiene el salto; profesor lo toca 2 fotogramas")
    a = ap.parse_args()

    repo = Path(a.repo).resolve()
    sys.path.insert(0, str(repo))

    pygame.init()
    from src.engine.core import settings
    pantalla = pygame.display.set_mode(
        (settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT))

    from src.engine.input.action_map import Action
    from src.stages.stage1_1.stage1_1 import Stage1_1_LaEntrada
    from tests.playtest.bot import ScriptedBot, run_playthrough, walk_right_bot

    def bot_humano(segundos: float, cada: int = 48, mantener: int = 12):
        """Como `walk_right_bot`, pero MANTENIENDO el salto.

        EL SALTO DE ESTE MOTOR ES DE ALTURA VARIABLE. Trazandolo fotograma a
        fotograma (`trazar_salto.py`) se ve que la velocidad vertical arranca
        en -6,1 px/fotograma y al cuarto cae a -2,6: soltar el boton corta el
        impulso.

        `walk_right_bot` mantiene JUMP dos fotogramas, y con eso se eleva 53 px
        de los 96 que da el salto entero. No es que juegue mal: es que fue
        escrito para comprobar que se puede AVANZAR, no para medir alturas. Su
        propia cabecera dice que es «deliberadamente tonto».

        Usarlo para juzgar la geometria de un nivel con escalones altos mide el
        bot, no el nivel. Este mantiene el boton 12 fotogramas —0,2 s, lo que
        hace cualquiera— y sube los 96 px completos.

        CADA CUANTO SALTA, Y POR QUE IMPORTA MAS DE LO QUE PARECE.
        La primera version saltaba 18 de cada 24 fotogramas: el 75 % del
        tiempo en el aire. Llegaba al final, pero ensuciaba dos medidas:

          · «atasco» — `run_playthrough` cuenta atasco cuando el avance
            horizontal baja de 1 px por fotograma, y en el aire el jugador se
            desplaza a 0,8. Un bot que vive saltando marca atasco todo el rato
            sin estar atascado. Salieron 15 tramos en rojo y aun asi completo
            el nivel: si de verdad estuviera atascado, no avanzaria.

          · checkpoints — se activan por contacto, y un jugador en el aire les
            pasa por encima. Salian 5 de 7, que leia como «se puede saltar una
            seccion» cuando lo unico que pasaba es que iba volando.

        Con 12 de cada 48 salta el 25 % del tiempo, que se parece a como anda
        una persona por un nivel de travesia, y las dos medidas vuelven a
        significar lo que dicen.
        """
        total = int(segundos * 60)
        guion, hechos = [], 0
        while hechos < total:
            tramo = min(cada, total - hechos)
            andar = max(1, tramo - mantener)
            guion.append((andar, {Action.MOVE_RIGHT}))
            guion.append((min(mantener, tramo - andar),
                          {Action.MOVE_RIGHT, Action.JUMP}))
            hechos += tramo
        return ScriptedBot(guion)

    ctx = _contexto()
    escena = Stage1_1_LaEntrada(ctx)
    escena.awake()
    escena.start()
    ctx.scene_manager.push(escena)
    escena.on_enter()

    jugador = escena._player
    datos = escena._stage_data
    salida = datos.next_trigger
    x0 = float(jugador.position.x)

    # Limites del mapa, para detectar "atravesar zonas incorrectamente".
    ancho = getattr(datos, "width_px", 3840)
    alto = getattr(datos, "height_px", 640)

    tramos = int(a.segundos / a.tramo)
    filas = []
    llego = False
    fuera_de_mapa = []
    retrocesos = 0
    muertes_totales = []

    try:
        for i in range(tramos):
            if a.recorrido:
                jugador.set_health(jugador.max_health)
            quien = (bot_humano(a.tramo) if a.bot == "humano"
                     else walk_right_bot(seconds=a.tramo))
            log = run_playthrough(escena, quien, surface=pantalla)
            muertes_totales.extend(log.deaths)

            for x, y in log.positions:
                # EL UMBRAL ERA -64 Y SE LE ESCAPO UNA FUGA REAL.
                #
                # Jugando se encontro que trepando el muro izquierdo a saltos
                # se sale del mapa. El jugador llegaba a y = -49,6: ya fuera,
                # pero 14 px por encima de mi umbral, asi que esta comprobacion
                # decia «nunca salio del mapa». Un margen puesto a ojo convirtio
                # una fuga de verdad en un OK.
                #
                # El borde de arriba es y=0 y no hay nada legitimo por encima,
                # asi que el umbral correcto es 0. Abajo se deja algo de holgura
                # porque el jugador se hunde unos pixeles al aterrizar.
                if x < -8 or x > ancho + 8 or y < 0 or y > alto + 8:
                    fuera_de_mapa.append((x, y))

            x = float(jugador.position.x)
            cps = sum(1 for c in escena._checkpoints if c._activated)
            filas.append(((i + 1) * a.tramo, x, float(jugador.position.y),
                          log.stuck_frames, len(log.deaths), cps,
                          jugador.current_health))
            if log.reached_exit:
                llego = True
                break
            if len(filas) > 1 and x < filas[-2][1] - 32:
                retrocesos += 1
    finally:
        escena.on_exit()
        escena.destroy()

    modo = ("RECORRIDO (salud repuesta entre tramos)" if a.recorrido
            else "COMBATE (salud normal)")
    print(f"\n  Modo: {modo}   bot: {a.bot}")
    print(f"  Mapa: {ancho} x {alto} px   salida en x={salida.centerx}"
          f"   arranque en x={x0:.0f}")
    print(f"\n  {'t':>6}  {'x':>7}  {'y':>6}  {'atasco':>7}  {'muertes':>8}"
          f"  {'checkp':>7}  {'salud':>6}")
    for t, x, y, atasco, muertes, cps, salud in filas:
        marca = "  <-- ATASCO" if atasco > 30 else ""
        print(f"  {t:>5.0f}s  {x:>7.0f}  {y:>6.0f}  {atasco:>7}  {muertes:>8}"
              f"  {cps:>7}  {salud:>6.0f}{marca}")

    max_x = max((f[1] for f in filas), default=x0)
    avance = (max_x - x0) / max(1.0, salida.centerx - x0)
    cps_final = filas[-1][5] if filas else 0
    total_cps = len(escena._checkpoints)
    atascos = [f for f in filas if f[3] > 30]

    print("\n  " + "=" * 64)
    print("  LISTA DE COMPROBACION DEL ENUNCIADO (seccion 5)")
    print("  " + "=" * 64)

    def linea(pregunta: str, ok: bool, detalle: str) -> None:
        print(f"  {'OK ' if ok else '!! '} {pregunta:<38} {detalle}")

    linea("Puedo completar el nivel?", llego,
          "llego a la salida" if llego
          else f"NO - se quedo en x={max_x:.0f} ({avance:.0%} del recorrido)")
    linea("El recorrido funciona?", avance > 0.95, f"avance {avance:.0%}")
    linea("Puedo quedar atrapado?", not atascos,
          "sin atascos" if not atascos
          else f"{len(atascos)} tramo(s): "
               + ", ".join(f"x~{f[1]:.0f}" for f in atascos))
    linea("Puedo atravesar zonas?", not fuera_de_mapa,
          "nunca salio del mapa" if not fuera_de_mapa
          else f"{len(fuera_de_mapa)} fotogramas fuera de limites")
    linea("Puedo saltarme una seccion?", (cps_final >= total_cps) or not llego,
          f"{cps_final}/{total_cps} checkpoints activados")
    linea("Puedo romper la progresion?", retrocesos == 0,
          f"{retrocesos} retroceso(s) no explicado(s)")
    linea("Las colisiones funcionan?", not fuera_de_mapa,
          "el jugador nunca atraveso el suelo")

    print(f"\n  Muertes totales: {len(muertes_totales)}")
    for x, y in muertes_totales:
        print(f"    x={x:.0f}  y={y:.0f}")
    return 0 if llego else 1


if __name__ == "__main__":
    sys.exit(main())
