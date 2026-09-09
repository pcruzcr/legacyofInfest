"""AUD-831 — la liana se agarra también con G sostenida.

El reporte ("la leña no se pudo usar", liana): la mecánica funciona pero sólo
entra con flanco de un fotograma. Quien salta hacia la liana manteniendo G —
el gesto natural de "quiero agarrarme"— llega con el flanco ya gastado y la
atraviesa. Se acepta `GRAB` sostenido además de los flancos; pasar corriendo
sin pulsar sigue sin agarrar (no es trampa: G no hace otra cosa en el aire).
"""
from __future__ import annotations

import pygame
import pytest

from src.engine.input.action_map import Action


@pytest.fixture(autouse=True)
def _video():
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((800, 600))


def _mundo_con_liana():
    from src.framework.ecs import World
    from src.framework.ecs.components import Liana
    from src.framework.scenes.stage_parts.mundo_ecs import MundoDelEscenario

    mundo = World()
    mundo.crear(Liana(rect=pygame.Rect(528, 432, 8, 80), ancho_de_agarre=12))
    escena = MundoDelEscenario()
    escena._mundo = mundo
    return escena


def _jugador_en_liana():
    from src.framework.entities.player import Player

    return Player(pygame.Vector2(520.0, 480.0))


class Mando:
    def __init__(self, sostenido=(), flanco=()):
        self._sostenido = set(sostenido)
        self._flanco = set(flanco)
        self._gastado = set()

    def is_action_held(self, a):
        return a in self._sostenido

    def is_action_pressed(self, a):
        return a in self._flanco and a not in self._gastado

    def is_action_just_pressed(self, a):
        return a in self._flanco and a not in self._gastado

    def pulsada_en_buffer(self, a):
        return False

    def consume(self, action):
        self._gastado.add(action)


def test_con_g_sostenida_se_agarra() -> None:
    from src.framework.entities.states.rope import TrepandoState

    escena = _mundo_con_liana()
    jugador = _jugador_en_liana()
    escena._actualizar_agarres(jugador, Mando(sostenido=(Action.GRAB,)))
    assert isinstance(jugador._state_instance, TrepandoState), (
        "con G sostenida junto a la liana no se agarra: sólo entra el flanco"
    )


def test_sin_pulsar_no_hay_trampa() -> None:
    from src.framework.entities.states.rope import TrepandoState

    escena = _mundo_con_liana()
    jugador = _jugador_en_liana()
    escena._actualizar_agarres(jugador, Mando())
    assert not isinstance(jugador._state_instance, TrepandoState), (
        "pasar junto a la liana sin pulsar no debe agarrar"
    )


def test_el_flanco_sigue_valiendo() -> None:
    from src.framework.entities.states.rope import TrepandoState

    escena = _mundo_con_liana()
    jugador = _jugador_en_liana()
    escena._actualizar_agarres(jugador, Mando(flanco=(Action.GRAB,)))
    assert isinstance(jugador._state_instance, TrepandoState)


def test_saltar_no_reengancha_en_el_mismo_fotograma() -> None:
    """La escena corre el agarre DESPUÉS del jugador: con el flanco vivo y la
    liana cerca, el salto re-enganchaba al instante y nunca se salía."""
    from src.framework.entities.states import JumpingState

    escena = _mundo_con_liana()
    jugador = _jugador_en_liana()
    mando = Mando(flanco=(Action.GRAB,))
    escena._actualizar_agarres(jugador, mando)
    jugador._state_instance._t = 0.5
    salto = Mando(flanco=(Action.JUMP,))
    jugador.update(1.0 / 60.0, [pygame.Rect(0, 512, 2000, 50)], salto)
    escena._actualizar_agarres(jugador, salto)
    assert isinstance(jugador._state_instance, JumpingState), (
        "el salto de la liana re-enganchó en el mismo fotograma"
    )
