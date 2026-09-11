"""Track B — grab/throw queda UNDERUSED deliberado, no roto.

Evidencia: THROW hace 1.0 = LONG instantáneo pero en dos tiempos con
ventana; GRAB hace 0.0 (prepara); el combate no pasa canal
(`collision_system.py:263` llama sin `canal`), así que ni siquiera se
puede premiar el throw contra escudos sin cirugía certificada; contra
Shielded, rodear/parry es estrictamente mejor. Sin encounter donde
agarrar dé ventaja no equivalente → no se fabrica examen.
"""
from __future__ import annotations

import pygame
import pytest

from src.engine.input.action_map import Action


@pytest.fixture(autouse=True)
def _video():
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((320, 240))


class _Entrada:
    def __init__(self, held=frozenset(), pressed=frozenset()):
        self._held = set(held)
        self._pressed = set(pressed)

    def is_action_held(self, action):
        return action in self._held

    def is_action_pressed(self, action):
        return action in self._pressed

    def is_action_just_pressed(self, action):
        return action in self._pressed

    def pulsada_en_buffer(self, action, ventana=None):
        return action in self._pressed

    def consumir_buffer(self, action):
        self._pressed.discard(action)


def _jugador():
    from src.framework.entities.player import Player

    return Player(pygame.Vector2(200.0, 300.0))


def test_grab_no_dana_throw_dana_uno():
    """El grab prepara (0.0), el throw cierra (1.0 = un largo)."""
    from src.framework.entities.states import GrabState, ThrowState

    jugador = _jugador()
    jugador._change_state_instance(GrabState(), force=True)
    jugador._state_instance.update(jugador, 1 / 60, _Entrada())
    assert jugador.current_attack_damage == 0.0

    jugador._change_state_instance(ThrowState(), force=True)
    jugador._state_instance.update(jugador, 1 / 60, _Entrada())
    assert jugador.current_attack_damage == pytest.approx(1.0)


def test_grab_conectado_mas_ataque_lleva_a_throw():
    from src.framework.entities.player import PlayerState
    from src.framework.entities.states import GrabState

    jugador = _jugador()
    jugador._change_state_instance(GrabState(), force=True)
    # El sistema de colisión avisaría así al conectar la caja 20×16.
    jugador._hitbox_consumed = True
    jugador._state_instance.update(
        jugador, 1 / 60, _Entrada(pressed=frozenset({Action.SHORT_ATTACK}))
    )
    assert jugador._state_instance.state_enum == PlayerState.THROW


def test_contra_escudo_el_throw_frontal_no_gana_a_rodear():
    """UNDERUSED documentado: de frente el escudo recorta; por detrás
    entra entero. Agarrar no da ventaja no equivalente."""
    from src.framework.entities.enemy_shielded import EnemyShielded

    escudo = EnemyShielded(pygame.Vector2(300.0, 300.0))
    vida = escudo.current_health
    # Throw frontal (jugador a la izquierda, escudo mirando a la izquierda).
    escudo.facing_direction = -1
    escudo.apply_hit(1.0, (escudo.rect.centerx - 100.0, escudo.rect.centery))
    dano_frontal = vida - escudo.current_health

    escudo2 = EnemyShielded(pygame.Vector2(300.0, 300.0))
    vida2 = escudo2.current_health
    escudo2.facing_direction = -1
    escudo2.apply_hit(1.0, (escudo2.rect.centerx + 100.0, escudo2.rect.centery))
    dano_trasero = vida2 - escudo2.current_health

    assert dano_trasero > dano_frontal, (
        "rodear ya no premia: cambiaría el veredicto UNDERUSED"
    )
