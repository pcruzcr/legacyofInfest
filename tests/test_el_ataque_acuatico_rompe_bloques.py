"""AUD-558 — GAP-069: el ataque acuático.

Decisión del dueño (KNOWN_GAPS.md GAP-069): un ataque nuevo mientras se
nada, no una ruptura por proximidad. `SwimmingState` no tenía ninguna
transición a un estado de ataque — comprobado leyendo el archivo
completo antes de este cambio — así que `BloqueDestructible` (el
sistema genérico que `StageScene.update()` ya consulta con
`player.active_hitbox` cada fotograma, sin cambios) nunca recibía un
golpe real bajo el agua.
"""
from __future__ import annotations

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame
import pytest

from src.engine.input.action_map import Action


@pytest.fixture(scope="module")
def _video() -> None:
    pygame.init()


class _IM:
    """`is_action_pressed` dice sí a las acciones pedidas — es lo que lee
    `_InputSnapshot.short_attack`, no `is_action_just_pressed`."""

    def __init__(self, *acciones: Action) -> None:
        self._acciones = set(acciones)

    def is_action_pressed(self, a: Action) -> bool:
        return a in self._acciones

    def is_action_held(self, a: Action) -> bool:
        return a in self._acciones

    def is_action_just_pressed(self, a: Action) -> bool:
        return a in self._acciones

    def pulsada_en_buffer(self, a: Action) -> bool:
        return False


def _jugador(_video):
    from src.framework.entities.player import Player
    return Player(pygame.Vector2(0.0, 0.0))


class TestNadarPuedeEntrarEnElAtaque:
    def test_pulsar_ataque_corto_cambia_a_swim_attack(self, _video) -> None:
        from src.framework.entities.player import PlayerState
        from src.framework.entities.states import SwimAttackState, SwimmingState

        jugador = _jugador(_video)
        jugador._change_state_instance(SwimmingState())

        jugador._state_instance.update(jugador, 0.016, _IM(Action.SHORT_ATTACK))

        assert isinstance(jugador._state_instance, SwimAttackState)
        assert jugador._state_instance.state_enum == PlayerState.SWIM_ATTACK

    def test_sin_pulsar_nada_se_queda_nadando(self, _video) -> None:
        from src.framework.entities.states import SwimmingState

        jugador = _jugador(_video)
        jugador._change_state_instance(SwimmingState())

        jugador._state_instance.update(jugador, 0.016, _IM())

        assert isinstance(jugador._state_instance, SwimmingState)


class TestElGolpeAbreYCierraLaCaja:
    """`active_hitbox` sólo existe en los fotogramas activos — el resto
    del tiempo `SistemaDeBloques.golpear` no debe recibir nada, o un
    golpe rompería bloques por los que el jugador sólo pasó nadando."""

    def _en_swim_attack(self, _video):
        from src.framework.entities.player import Player
        from src.framework.entities.states import SwimAttackState

        jugador = Player(pygame.Vector2(0.0, 0.0))
        estado = SwimAttackState()
        jugador._change_state_instance(estado)
        return jugador, estado

    def test_antes_del_primer_fotograma_activo_no_hay_caja(self, _video) -> None:
        jugador, estado = self._en_swim_attack(_video)
        # Recién entrado (fotograma 0 -> current_frame 1): 1 no está en
        # ACTIVE_FRAMES = (2, 3, 4).
        estado.update(jugador, 0.001, _IM())
        assert jugador.active_hitbox is None

    def test_en_un_fotograma_activo_hay_caja_real(self, _video) -> None:
        jugador, estado = self._en_swim_attack(_video)
        # Avanza lo suficiente para entrar en el segundo fotograma
        # (current_frame == 2, el primero de ACTIVE_FRAMES).
        paso = 1.0 / estado.FPS
        estado.update(jugador, paso * 1.5, _IM())
        assert jugador.active_hitbox is not None
        assert jugador.active_hitbox.width > 0
        assert jugador.active_hitbox.height > 0

    def test_al_terminar_los_seis_fotogramas_vuelve_a_nadar(self, _video) -> None:
        from src.framework.entities.states import SwimmingState

        jugador, estado = self._en_swim_attack(_video)
        paso = 1.0 / estado.FPS
        for _ in range(estado.TOTAL_FRAMES + 1):
            estado.update(jugador, paso, _IM())
            if not isinstance(jugador._state_instance, type(estado)):
                break
        assert isinstance(jugador._state_instance, SwimmingState)
        assert jugador.active_hitbox is None


class TestElGolpeAcuaticoRompeUnBloqueDeVerdad:
    """Punta a punta: el mismo camino que recorre `StageScene.update()`
    cada fotograma (`SistemaDeBloques.golpear(player.active_hitbox)`),
    sin mocks del sistema de bloques."""

    def test_un_bloque_dentro_de_la_caja_se_rompe(self, _video) -> None:
        from src.framework.entities.player import Player
        from src.framework.entities.states import SwimAttackState
        from src.framework.stage.bloques import BloqueDestructible, SistemaDeBloques

        jugador = Player(pygame.Vector2(0.0, 0.0))
        jugador.facing_direction = 1
        estado = SwimAttackState()
        jugador._change_state_instance(estado)
        # El bloque se coloca donde `_construir_hitbox` pondrá la caja:
        # centro del jugador + 8px en la dirección en la que mira.
        bloque = BloqueDestructible(
            rect=pygame.Rect(jugador.rect.centerx, jugador.rect.centery - 10, 20, 20),
        )
        sistema = SistemaDeBloques(destructibles=[bloque])

        paso = 1.0 / estado.FPS
        estado.update(jugador, paso * 1.5, _IM())  # entra en fotograma activo
        rotos = sistema.golpear(jugador.active_hitbox)

        assert rotos == 1
        assert bloque.roto is True


class TestSwimAttackEstaRegistrado:
    def test_es_uno_de_los_estados_del_jugador(self) -> None:
        from src.framework.entities.player import PlayerState

        assert PlayerState.SWIM_ATTACK.value == "SWIM_ATTACK"
