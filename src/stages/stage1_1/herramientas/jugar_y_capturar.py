"""Juega el nivel con el bot del profesor y captura fotogramas reales.

POR QUE EXISTE
==============
Todo lo que se habia verificado hasta ahora era ESTATICO: el .tmx renderizado
a PNG, las pruebas unitarias, el calificador. Nada de eso dice si el juego
CORRE bien: si el jugador avanza, si se atasca, si muere, si los filtros de la
Unidad VII se ven como deben con la camara en movimiento.

Ese hueco no lo cierra un servidor ni un protocolo: lo cierra tener un bot que
juegue y una superficie donde dibujar. Las dos cosas ya estan en el repo.

`tests/playtest/bot.py` (del profesor) inyecta las acciones directamente en el
`InputManager` en vez de mover el raton del sistema. Su propia cabecera explica
por que, y la razon vale igual aqui: funciona SIN PANTALLA, es determinista, y
es unas 73.000 veces mas rapido que automatizar el escritorio.

QUE HACE
========
Monta la escena como lo hacen las pruebas de QA del repo, la juega por tramos
con `walk_right_bot`, y guarda un fotograma **ya dibujado** al final de cada
tramo — con el cielo, el sol, el tinte de la Unidad V, la auto-exposicion y,
si se pide, el realce de bordes de la Unidad VII.

Uso:
    python claude-workspace/tools/jugar_y_capturar.py <ruta_repo> [--segundos 30]
                                                      [--tramos 12] [--enfoque]
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


def _contacto(fotogramas, columnas: int = 4) -> pygame.Surface:
    """Hoja de contactos con todos los fotogramas y su marca de tiempo."""
    pygame.font.init()
    fuente = pygame.font.Font(None, 24)
    if not fotogramas:
        return pygame.Surface((10, 10))
    ancho, alto = fotogramas[0][1].get_size()
    escala = 0.5
    w, h = int(ancho * escala), int(alto * escala)
    filas = (len(fotogramas) + columnas - 1) // columnas
    hoja = pygame.Surface((columnas * (w + 4), filas * (h + 22)))
    hoja.fill((18, 18, 22))
    for i, (etiqueta, sup) in enumerate(fotogramas):
        x, y = (i % columnas) * (w + 4), (i // columnas) * (h + 22)
        hoja.blit(pygame.transform.scale(sup, (w, h)), (x, y + 20))
        hoja.blit(fuente.render(etiqueta, True, (235, 235, 225)), (x + 4, y + 2))
    return hoja


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("repo", nargs="?", default=".")
    ap.add_argument("--segundos", type=float, default=30.0)
    ap.add_argument("--tramos", type=int, default=12)
    ap.add_argument("--enfoque", action="store_true",
                    help="mantiene la tecla de enfoque (Unidad VII) todo el rato")
    a = ap.parse_args()

    repo = Path(a.repo).resolve()
    sys.path.insert(0, str(repo))
    destino = repo.parent / "claude-workspace" / "render" / "jugado"
    destino.mkdir(parents=True, exist_ok=True)

    pygame.init()
    from src.engine.core import settings
    pantalla = pygame.display.set_mode((settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT))

    from src.stages.stage1_1.stage1_1 import Stage1_1_LaEntrada
    from tests.playtest.bot import run_playthrough, walk_right_bot

    ctx = _contexto()
    escena = Stage1_1_LaEntrada(ctx)
    escena.awake()
    escena.start()
    ctx.scene_manager.push(escena)
    escena.on_enter()

    if a.enfoque:
        escena._enfoque.actualizar(True)

    x0 = escena._player.position.x
    por_tramo = a.segundos / a.tramos
    fotogramas, resumen = [], []
    try:
        for i in range(a.tramos):
            log = run_playthrough(escena, walk_right_bot(seconds=por_tramo),
                                  surface=pantalla)
            if a.enfoque:
                escena._enfoque.actualizar(True)
            escena.draw(pantalla)
            t = (i + 1) * por_tramo
            x = escena._player.position.x
            etiqueta = f"{t:.0f}s  x={x:.0f}px"
            fotogramas.append((etiqueta, pantalla.copy()))
            pygame.image.save(pantalla, destino / f"jugado_{i:02d}.png")
            resumen.append((t, x, log.deaths, log.damage_events, log.stuck_frames,
                            escena._adaptacion.media, escena._adaptacion.factor))
    finally:
        escena.on_exit()
        escena.destroy()

    pygame.image.save(_contacto(fotogramas), destino / "CONTACTOS.png")

    print(f"\n  Recorrido de {a.segundos:.0f} s"
          + ("  CON la tecla de enfoque pulsada" if a.enfoque else ""))
    print(f"  {'t':>5}  {'x':>7}  {'avance':>8}  {'muertes':>8}  {'golpes':>7}"
          f"  {'atasco':>7}  {'luminancia':>11}  {'factor':>7}")
    for t, x, muertes, golpes, atasco, media, factor in resumen:
        print(f"  {t:>4.0f}s  {x:>7.0f}  {x - x0:>8.0f}  {len(muertes):>8}"
              f"  {len(golpes):>7}  {atasco:>7}  {media:>11.1f}  {factor:>7.3f}")
    print(f"\n  Fotogramas en {destino}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
