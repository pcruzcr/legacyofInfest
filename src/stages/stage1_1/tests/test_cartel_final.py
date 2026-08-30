"""
Module: test_cartel_final
System: stage (student assignment) — stage1_1 «La Entrada»
Academic Unit: N/A
Description: El cartel «STAGE COMPLETE» tiene que verse al terminar el nivel.

Estas pruebas nacen de una sesion de playtesting humano: al llegar al final el
juego se quedaba unos segundos sin hacer nada visible. El motor SI lanza el
cartel y SI lo dibuja, pero nunca lo anima, porque el bloque que actualiza la
interfaz esta guardado por la misma bandera que se acaba de poner
(`stage_scene.py:797`, `not self._progression.stage_complete`). El cartel se
queda en su desplazamiento inicial —dos anchos de pantalla— y se pinta fuera
de cuadro los 174 fotogramas que dura la espera.

`Stage1_1_LaEntrada._animar_cartel_final` llama al `update` que el motor se
salta. Sin esa llamada, las dos pruebas de aqui fallan.

Ejecutar con:
   python -m pytest src/stages/stage1_1/tests/test_cartel_final.py -v
"""
from __future__ import annotations

import pygame
import pytest

from src.engine.audio.audio_manager import AudioManager
from src.engine.core import settings
from src.engine.core.event_bus import EventBus
from src.engine.core.game_context import GameContext
from src.engine.core.save_manager import SaveManager
from src.engine.input.input_manager import InputManager
from src.engine.scene.scene_manager import SceneManager
from src.framework.entities import entity_factory
from src.stages.stage1_1.stage1_1 import Stage1_1_LaEntrada


@pytest.fixture
def escena_en_la_salida():
    """Escena montada con el jugador ya dentro del disparador de salida."""
    entity_factory.ensure_registered()
    ctx = GameContext(
        input_manager=InputManager(), audio_manager=AudioManager(),
        scene_manager=None, event_bus=EventBus(), clock=None,
        save_manager=SaveManager(),
    )
    ctx.scene_manager = SceneManager(ctx)
    escena = Stage1_1_LaEntrada(ctx)
    escena.awake()
    escena.start()
    ctx.scene_manager.push(escena)
    escena.on_enter()

    salida = escena._stage_data.next_trigger
    escena._player.position.x = float(salida.centerx)
    escena._player.position.y = float(salida.centery)
    escena._player.set_health(escena._player.max_health)
    try:
        yield escena
    finally:
        escena.on_exit()
        escena.destroy()


def _correr(escena, fotogramas: int) -> None:
    for _ in range(fotogramas):
        escena.update(1 / 60)


def test_el_cartel_final_entra_en_pantalla(escena_en_la_salida) -> None:
    """Lo que el jugador tiene que ver: el cartel, dentro del cuadro.

    `ScreenBanner.draw` pinta en `bx = offset - ANCHO`. Con el
    desplazamiento inicial (dos anchos) sale en `bx = ANCHO`: justo una
    pantalla a la derecha, invisible. Cuando la animacion llega a `hold` el
    desplazamiento vale un ancho y `bx` es 0 — pegado al borde izquierdo, que
    es donde se lee.
    """
    escena = escena_en_la_salida
    _correr(escena, 45)                      # 0,75 s: entrada (0,5 s) + margen

    banner = escena._banner
    assert banner is not None
    assert banner._state == "hold", (
        f"el cartel se quedo en {banner._state!r}: no llego a mostrarse")
    bx = banner._offset - settings.INTERNAL_WIDTH
    assert bx == pytest.approx(0.0, abs=1.0), (
        f"el cartel se dibuja en bx={bx:.0f}, fuera de la pantalla")


def test_el_cartel_final_recorre_toda_su_animacion(escena_en_la_salida) -> None:
    """Los tres estados, en orden, dentro de los 2,9 s que dura la espera.

    Las duraciones del cartel —0,5 de entrada, 2,0 de espera y 0,4 de salida—
    suman exactamente los 2,9 s de `ProgressionSystem._complete_timer`. Que
    cuadren no es casualidad: la espera existe para que el cartel se lea. Si
    el cartel no se anima, esos 2,9 s son tiempo muerto, que es justo como se
    veia jugando.
    """
    escena = escena_en_la_salida
    vistos = []
    for _ in range(174):                     # 2,9 s a 60 fps
        escena.update(1 / 60)
        estado = escena._banner._state
        if not vistos or vistos[-1] != estado:
            vistos.append(estado)

    assert vistos[:3] == ["slide_in", "hold", "slide_out"], (
        f"la animacion no siguio su curso: {vistos}")


def test_el_cartel_del_nombre_del_nivel_no_se_toca(escena_en_la_salida) -> None:
    """La correccion no debe alterar el caso que ya funcionaba.

    En el arranque la bandera de nivel completado es falsa, asi que el motor
    anima el cartel del nombre por su cuenta y aqui no hace falta ayudar. Esta
    prueba fija esa frontera: `_animar_cartel_final` no hace nada mientras el
    nivel no este completo.
    """
    escena = escena_en_la_salida
    escena._progression.reset()
    banner = escena._banner
    banner.play("PRUEBA", "PRUEBA")
    antes = banner._offset

    escena._animar_cartel_final(1 / 60)

    assert banner._offset == antes, (
        "sin el nivel completado, el escenario no debe adelantar el cartel")
