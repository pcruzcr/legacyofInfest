"""Fase 1 del plan maestro — el núcleo de movimiento que faltaba.

Tres lotes, un defecto cada uno, y los tres se descubrieron leyendo la
máquina de estados real contra lo que promete `04_PLAYER_SPEC.md`:

1. **GAP-024 — el salto aéreo nunca dispara.** `_can_jump` tiene su rama
   aérea escrita desde siempre, pero el único estado que atiende
   `jump_pressed` en el aire (`AirborneState`) sólo lo hace dentro de la
   ventana de coyote. Pasada la ventana, pulsar salto no hace nada aunque
   queden saltos aéreos y la habilidad esté concedida.

2. **El pisotón aéreo no existe.** El plan maestro lo pide: cancelar el
   momentum horizontal en el aire, caer recto y soltar una onda de daño a
   ambos lados al tocar suelo. Hoy `AerialSlamState` hace un picado, pero
   sólo llega encadenando combo aéreo — no hay forma deliberada de pedirlo
   desde una caída cualquiera.

3. **El dash no se cancela con salto.** Con ataque sí (`DashAttackState`,
   en cualquier instante); con salto, nunca. La ventana de cancelación es
   lo que convierte el dash en una herramienta de posicionamiento y no en
   un carril fijo de 0,15 s.
"""

from __future__ import annotations

import pygame
import pytest

from src.engine.input.action_map import Action
from src.framework.entities.player import Player, PlayerState
from src.framework.entities.states import (
    DashingState,
    FallingState,
    GroundPoundState,
    IdleState,
    JumpingState,
)

_SKILL = "skill_ground_pound"
_SKILL_DOBLE = "skill_double_jump"


class _Entrada:
    """Doble mínimo de `InputManager` para manejar la máquina de estados.

    Suficiente para `_InputSnapshot`: held/pressed por acción, buffer vacío.
    """

    def __init__(
        self,
        held: frozenset[Action] = frozenset(),
        pressed: frozenset[Action] = frozenset(),
    ) -> None:
        self._held = set(held)
        self._pressed = set(pressed)

    def is_action_held(self, action: Action) -> bool:
        return action in self._held

    def is_action_pressed(self, action: Action) -> bool:
        return action in self._pressed

    def pulsada_en_buffer(self, action: Action) -> bool:
        return False

    def consumir_buffer(self, action: Action) -> None:
        return None


def _jugador_aereo(*, habilidades_libres: bool = True) -> Player:
    """Un jugador colgado en el aire, fuera de la ventana de coyote."""
    player = Player(pygame.Vector2(100.0, 100.0))
    player._habilidades_libres = habilidades_libres
    player.is_grounded = False
    player._coyote_counter = float(player.perfil.coyote_frames + 10)
    player._change_state_instance(FallingState(), force=True)
    return player


def _sin_doble_salto() -> None:
    """Garantiza que el inventario NO conoce `skill_double_jump`."""
    from src.engine.core.inventory import get_inventory

    inventario = get_inventory()
    testigo = inventario._items.get(_SKILL_DOBLE)
    inventario._items.pop(_SKILL_DOBLE, None)
    return testigo


# ── Lote 1: GAP-024 — el salto aéreo ──────────────────────────────


class TestSaltoAereo:
    def test_dispara_fuera_del_coyote_con_la_habilidad(self) -> None:
        player = _jugador_aereo()
        entrada = _Entrada(pressed=frozenset({Action.JUMP}))

        player._state_instance.update(player, 1 / 60, entrada)

        assert isinstance(player._state_instance, JumpingState)
        assert player._air_jumps_used == 1
        assert player.velocity.y == player.perfil.salto_impulso

    def test_sin_habilidad_no_dispara(self) -> None:
        testigo = _sin_doble_salto()
        try:
            player = _jugador_aereo(habilidades_libres=False)
            entrada = _Entrada(pressed=frozenset({Action.JUMP}))

            player._state_instance.update(player, 1 / 60, entrada)

            assert isinstance(player._state_instance, FallingState), (
                "el salto aéreo saltó el candado: sin `skill_double_jump` "
                "no hay segundo salto, ésa es toda la progresión"
            )
        finally:
            if testigo is not None:
                from src.engine.core.inventory import get_inventory

                get_inventory()._items[_SKILL_DOBLE] = testigo

    def test_el_coyote_no_consumir_salto_aereo(self) -> None:
        """Regresión de AUD-503: dentro de la ventana, el salto es el normal
        y NO gasta uno de los saltos aéreos."""
        player = _jugador_aereo()
        player._coyote_counter = float(player.perfil.coyote_frames - 2)
        entrada = _Entrada(pressed=frozenset({Action.JUMP}))

        player._state_instance.update(player, 1 / 60, entrada)

        assert isinstance(player._state_instance, JumpingState)
        assert player._air_jumps_used == 0, (
            "saltar dentro del coyote consumió un salto aéreo: el jugador "
            "pierde el doble salto por usar el perdón que ya tenía"
        )

    def test_agotado_no_hay_tercero(self) -> None:
        player = _jugador_aereo()
        player._air_jumps_used = int(player.perfil.saltos_aereos)
        entrada = _Entrada(pressed=frozenset({Action.JUMP}))

        player._state_instance.update(player, 1 / 60, entrada)

        assert isinstance(player._state_instance, FallingState)


# ── Lote 2: el pisotón aéreo ──────────────────────────────────────


class TestPisotonAereo:
    @staticmethod
    def _pisar(player: Player, *, abajo: bool = True) -> None:
        held = {Action.CROUCH} if abajo else set()
        entrada = _Entrada(
            held=frozenset(held),
            pressed=frozenset({Action.SHORT_ATTACK}),
        )
        player._state_instance.update(player, 1 / 60, entrada)

    def test_entra_con_abajo_mas_ataque_en_el_aire(self) -> None:
        player = _jugador_aereo()

        self._pisar(player)

        assert isinstance(player._state_instance, GroundPoundState)
        assert player.state == PlayerState.GROUND_POUND

    def test_cancela_el_momentum_horizontal(self) -> None:
        player = _jugador_aereo()
        player.velocity.x = 200.0

        self._pisar(player)

        assert player.velocity.x == 0.0, (
            "el pisotón conserva la velocidad horizontal: cae en diagonal "
            "y deja de leerse como un pisotón"
        )

    def test_cae_recto_a_velocidad_constante(self) -> None:
        player = _jugador_aereo()
        self._pisar(player)

        estado = player._state_instance
        estado.update(player, 1 / 60, _Entrada())

        assert player.velocity.x == 0.0
        assert player.velocity.y > 300.0, (
            "la caída del pisotón va más lenta que una caída normal: no "
            "hay compromiso ni lectura de 'esto pega contra el suelo'"
        )

    def test_onda_al_aterrizar_y_sale_a_reposo(self) -> None:
        player = _jugador_aereo()
        self._pisar(player)
        # La física corre después del estado; simulamos el fotograma en
        # que el resolutor ya aterrizó al jugador.
        player.is_grounded = True

        # Fotograma 1: el estado DETECTA el aterrizaje y arranca la onda.
        player._state_instance.update(player, 1 / 60, _Entrada())

        # Fotograma 2: la onda está viva — caja ancha a ambos lados.
        player._state_instance.update(player, 1 / 60, _Entrada())
        assert player._active_hitbox is not None, (
            "aterrizar el pisotón sin onda de daño lo convierte en una "
            "caída lenta con otro sprite"
        )
        ancho = player._active_hitbox.width
        assert ancho >= player.rect.width * 2, (
            "la onda cubre menos que a ambos lados del cuerpo"
        )

        for _ in range(10):
            player._state_instance.update(player, 1 / 60, _Entrada())
        assert isinstance(player._state_instance, IdleState), (
            "el pisotón no termina: el jugador queda clavado en el estado"
        )

    def test_en_el_suelo_no_se_declara_pisoton(self) -> None:
        """Abajo + ataque en tierra es el ataque corto agachado de siempre;
        el pisotón sólo existe en el aire."""
        from src.framework.entities.states import CrouchingState

        player = Player(pygame.Vector2(100.0, 100.0))
        player._habilidades_libres = True
        player._change_state_instance(CrouchingState(), force=True)
        entrada = _Entrada(
            held=frozenset({Action.CROUCH}),
            pressed=frozenset({Action.SHORT_ATTACK}),
        )

        player._state_instance.update(player, 1 / 60, entrada)

        assert not isinstance(player._state_instance, GroundPoundState)


# ── Lote 3: cancelación del dash con salto ────────────────────────


_VENTANA_CANCELACION = 0.1


class TestCancelacionDelDash:
    @staticmethod
    def _dash(player: Player) -> DashingState:
        player.velocity.x = 200.0
        estado = DashingState()
        estado.enter(player)
        player._state_instance = estado
        return estado

    def test_dentro_de_la_ventana_el_salto_cancella(self) -> None:
        player = Player(pygame.Vector2(100.0, 100.0))
        estado = self._dash(player)
        entrada = _Entrada(pressed=frozenset({Action.JUMP}))

        estado.update(player, 1 / 60, entrada)

        assert isinstance(player._state_instance, JumpingState)
        assert player.velocity.x == pytest.approx(200.0), (
            "cancelar el dash con salto perdió el momentum horizontal: "
            "la cancelación pierde su razón de ser"
        )

    def test_pasada_la_ventana_no_cancella(self) -> None:
        player = Player(pygame.Vector2(100.0, 100.0))
        estado = self._dash(player)
        # Se avanza PASADA la ventana con pasos pequeños y SIN saltar: un
        # solo dt grande expiraría el dash por su duración natural (0,15 s)
        # y la prueba estaría midiendo el fin normal, no la ventana.
        # 6 x 0,02 = 0,12 s: pasado el umbral de 0,1, con el dash vivo
        # todavía (0,15 - 0,12 = 0,03 s le quedan).
        for _ in range(6):
            estado.update(player, 0.02, _Entrada())

        estado.update(player, 1 / 60, _Entrada(pressed=frozenset({Action.JUMP})))

        assert isinstance(player._state_instance, DashingState), (
            "el dash se puede cancelar con salto en cualquier momento: la "
            "ventana es la que separa una decisión de un spam"
        )

    def test_cancelar_deja_cooldown_de_dash(self) -> None:
        player = Player(pygame.Vector2(100.0, 100.0))
        estado = self._dash(player)

        estado.update(player, 1 / 60, _Entrada(pressed=frozenset({Action.JUMP})))

        assert player._dash_cooldown > 0.0, (
            "cancelar y re-dash en el mismo fotograma convierte la ventana "
            "en un dash infinito"
        )


# ── Contrato del enum ─────────────────────────────────────────────


def test_ground_pound_esta_en_el_enum_y_se_puede_construir() -> None:
    assert PlayerState.GROUND_POUND.value == "GROUND_POUND"
    instancia = GroundPoundState()
    assert instancia.state_enum == PlayerState.GROUND_POUND
