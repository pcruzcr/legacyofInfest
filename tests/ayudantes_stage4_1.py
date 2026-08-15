"""Cómo se monta el 4-1 en una prueba. Un solo sitio (AUD-492).

Por qué existe este módulo
==========================
Las pruebas del 4-1 ya no caben en un fichero: `test_stage4_1.py` cubre la
geometría y las seis fases, y los GAP que se van cerrando traen los suyos
(`test_el_escenario_observa.py`, `test_la_musica_del_4_1_entra_tarde.py`).
Todos necesitan el mismo escenario montado igual.

Compartir el *fixture* importándolo de otro módulo de pruebas funciona en
pytest pero ruff lo marca como redefinición (F811) en cada test que lo
recibe como parámetro — una vez por prueba. Y copiar el montaje en cada
fichero es peor: son cuatro sistemas (audio, entrada, escenas, guardado) y
una cutscene que saltar, y el día que cambie uno habría que acordarse de
tres sitios.

Así que el montaje vive aquí, como función normal, y cada fichero de
pruebas declara su propio fixture de una línea encima.
"""
from __future__ import annotations

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame


def preparar_video() -> None:
    """Deja pygame listo para dibujar sin pantalla real."""
    pygame.init()
    pygame.font.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((800, 600))


def construir_escena():
    """Un `Stage4_1` cargado, con jugador, listo para recibir `update`.

    La cutscene de introducción bloquea el juego hasta que el jugador
    confirma. Como estas pruebas no simulan pulsaciones reales de tecla, se
    salta a mano; que el guion se parsee sin errores lo cubre
    `TestLaCutsceneDeIntroduccion` en `test_stage4_1.py`.
    """
    from src.engine.audio.audio_manager import AudioManager
    from src.engine.core.event_bus import EventBus
    from src.engine.core.game_context import GameContext
    from src.engine.core.save_manager import SaveManager
    from src.engine.input.input_manager import InputManager
    from src.engine.scene.scene_manager import SceneManager
    from src.framework.entities import entity_factory
    from src.stages.stage4_1.stage4_1 import Stage4_1

    entity_factory.ensure_registered()
    ctx = GameContext(
        input_manager=InputManager(), audio_manager=AudioManager(),
        scene_manager=None, event_bus=EventBus(), clock=None,
        save_manager=SaveManager(),
    )
    ctx.scene_manager = SceneManager(ctx)
    sc = Stage4_1(ctx)
    ctx.scene_manager.push(sc)
    if getattr(sc, "_cutscenes", None) is not None:
        sc._cutscenes._activos.clear()
    return sc
