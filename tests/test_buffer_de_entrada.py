"""AUD-373 — el buffer de entrada existía sólo para el salto. Cierra GAP-040.

El defecto
==========
El juego ya perdonaba al jugador que se adelanta, pero **sólo al saltar**. El
mecanismo estaba escrito a mano dentro del jugador —`_pending_jump` y su
temporizador, armados desde `AirborneState`— y servía a una acción. Ninguna
otra lo tenía: pulsar dash o atacar un fotograma antes de aterrizar se perdía,
porque el estado que recibe la pulsación decide que no puede ejecutarla y la
tira al suelo sin más.

Es la misma queja del jugador —«lo pulsé, no salió»— con dos respuestas
distintas según qué botón fuera.

Qué cambia
==========
La primitiva sube a `InputManager`, que es donde vive el problema: esto es
entrada, no física. Cuenta en **fotogramas** de `pump()` y no en segundos,
porque el buffer es una concesión al tiempo de reacción humano —los 8 por
defecto son ~133 ms a 60 Hz— y porque desde AUD-390 la simulación avanza a
paso fijo, así que contar fotogramas es determinista.

El salto pasa a usarla en vez de su mecanismo propio. Tener dos buffers
haciendo lo mismo era la alternativa peor: la que produce que uno de los dos
se quede sin mantener.
"""
from __future__ import annotations

import pygame
import pytest

from src.engine.input.action_map import DEFAULT_KEY_BINDINGS, Action
from src.engine.input.input_manager import InputManager


def _tecla(action: Action) -> int:
    return DEFAULT_KEY_BINDINGS[action][0]


def _pulsar(im: InputManager, action: Action) -> None:
    im.pump([pygame.event.Event(pygame.KEYDOWN, key=_tecla(action))])


def _soltar(im: InputManager, action: Action) -> None:
    im.pump([pygame.event.Event(pygame.KEYUP, key=_tecla(action))])


def _fotograma_vacio(im: InputManager, veces: int = 1) -> None:
    for _ in range(veces):
        im.pump([])


@pytest.fixture
def im() -> InputManager:
    if not pygame.display.get_init():
        pygame.display.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((1, 1))
    return InputManager()


class TestLaPrimitiva:
    def test_una_pulsacion_queda_en_el_buffer(self, im: InputManager) -> None:
        _pulsar(im, Action.JUMP)
        assert im.pulsada_en_buffer(Action.JUMP)

    def test_sigue_estando_unos_fotogramas_despues(self, im: InputManager) -> None:
        """La razón de ser del buffer: la acción sobrevive al fotograma."""
        _pulsar(im, Action.JUMP)
        _soltar(im, Action.JUMP)
        _fotograma_vacio(im, 3)
        assert im.pulsada_en_buffer(Action.JUMP), (
            "la pulsación se perdió a los 4 fotogramas: quien se adelanta al "
            "aterrizaje se queda sin saltar"
        )

    def test_caduca(self, im: InputManager) -> None:
        """Si no caducara, un salto pulsado hace tres segundos saldría solo."""
        _pulsar(im, Action.JUMP)
        _soltar(im, Action.JUMP)
        _fotograma_vacio(im, InputManager.VENTANA_DE_BUFFER + 2)
        assert not im.pulsada_en_buffer(Action.JUMP)

    def test_consumir_lo_vacia(self, im: InputManager) -> None:
        """Sin consumo, la acción saldría en cada fotograma de la ventana."""
        _pulsar(im, Action.JUMP)
        im.consumir_buffer(Action.JUMP)
        assert not im.pulsada_en_buffer(Action.JUMP)

    def test_una_accion_no_contamina_a_otra(self, im: InputManager) -> None:
        _pulsar(im, Action.JUMP)
        assert not im.pulsada_en_buffer(Action.DASH)

    def test_sin_pulsar_nada_el_buffer_esta_vacio(self, im: InputManager) -> None:
        _fotograma_vacio(im, 5)
        assert not im.pulsada_en_buffer(Action.JUMP)

    def test_la_ventana_se_puede_afinar_por_accion(self, im: InputManager) -> None:
        """Un dash perdonado medio segundo se sentiría fantasmal; el salto no.

        La primitiva acepta ventana propia para que eso sea ajustable sin
        tocar el mecanismo.
        """
        _pulsar(im, Action.DASH)
        _soltar(im, Action.DASH)
        _fotograma_vacio(im, 3)
        assert im.pulsada_en_buffer(Action.DASH, ventana=8)
        assert not im.pulsada_en_buffer(Action.DASH, ventana=2)


class TestElSaltoSigueIgual:
    """Regresión: migrar el mecanismo no puede cambiar el game feel.

    Las tres cosas que el salto con buffer hacía antes de AUD-373 y tiene que
    seguir haciendo. Si alguna de éstas cae, la migración salió mal aunque la
    primitiva funcione.
    """

    def _jugador_en_el_suelo(self):
        from src.framework.entities.player import Player

        suelo = [pygame.Rect(0, 160, 400, 40)]
        jugador = Player(pygame.Vector2(100, 100))
        for _ in range(120):
            jugador.update(1 / 60, suelo, None)
        assert jugador.is_grounded, "no llegó a aterrizar"
        return jugador, suelo

    def test_al_aterrizar_el_salto_guardado_se_ejecuta(self, im: InputManager) -> None:
        """La pulsación va **en el aire**, y el salto sale al tocar suelo.

        Pulsarla con el jugador ya apoyado no probaría nada: saldría por el
        camino normal —`GroundedState` la ve el mismo fotograma— y la prueba
        pasaría con el buffer roto. Fue el primer intento de esta prueba.
        """
        jugador, suelo = self._jugador_en_el_suelo()
        jugador.is_grounded = False
        jugador.position.y -= 4
        _pulsar(im, Action.JUMP)
        _soltar(im, Action.JUMP)

        for _ in range(6):
            if jugador.is_grounded and jugador.velocity.y < 0:
                break
            jugador.update(1 / 60, suelo, im)
            im.pump([])
        assert jugador.velocity.y < 0, (
            "el salto guardado no se disparó al tocar suelo: el jugador que "
            "se adelanta un fotograma se queda sin saltar"
        )

    def test_el_salto_guardado_no_se_dispara_dos_veces(self, im: InputManager) -> None:
        """Sin consumo saldría en cada fotograma de la ventana."""
        jugador, suelo = self._jugador_en_el_suelo()
        jugador.is_grounded = False
        jugador.position.y -= 4
        _pulsar(im, Action.JUMP)
        _soltar(im, Action.JUMP)

        for _ in range(6):
            jugador.update(1 / 60, suelo, im)
            im.pump([])
        assert not im.pulsada_en_buffer(Action.JUMP), (
            "el salto se ejecutó y la pulsación sigue en el buffer"
        )

    def test_el_buffer_caduca_en_el_aire(self, im: InputManager) -> None:
        from src.framework.entities.player import Player

        jugador = Player(pygame.Vector2(100, 100))
        jugador.is_grounded = False
        _pulsar(im, Action.JUMP)
        _soltar(im, Action.JUMP)
        for _ in range(30):
            jugador.update(1 / 60, [], im)
            im.pump([])
        assert not im.pulsada_en_buffer(Action.JUMP)


class TestLoQueGanaElResto:
    """GAP-040 en una frase: que el dash tenga lo que el salto ya tenía."""

    def test_el_dash_pulsado_antes_de_aterrizar_no_se_pierde(
        self, im: InputManager
    ) -> None:
        """El defecto que cierra el hueco.

        Antes: se pulsa dash en el aire, `AirborneState` comprueba
        `_can_dash`, no puede, y la pulsación se tira. Al tocar suelo no queda
        nada. Ahora la pulsación sigue en el buffer y el estado del suelo la
        encuentra.
        """
        _pulsar(im, Action.DASH)
        _soltar(im, Action.DASH)
        _fotograma_vacio(im, 3)
        assert im.pulsada_en_buffer(Action.DASH), (
            "la pulsación de dash no sobrevive al fotograma en que se hizo, "
            "así que sigue sin poder recogerla el estado que sí puede "
            "ejecutarla"
        )

    def test_el_dash_guardado_se_ejecuta_al_tocar_suelo(
        self, im: InputManager
    ) -> None:
        """Y no sólo sobrevive: sale.

        La prueba de arriba comprueba la primitiva; ésta, que hay alguien
        escuchándola. Sin este par, GAP-040 se cerraría con un buffer correcto
        que nadie consulta — el modo de fallo de esta casa.
        """
        from src.framework.entities.player import Player
        from src.framework.entities.states import DashingState

        suelo = [pygame.Rect(0, 160, 400, 40)]
        jugador = Player(pygame.Vector2(100, 100))
        for _ in range(120):
            jugador.update(1 / 60, suelo, None)
        assert jugador.is_grounded, "no llegó a aterrizar"
        jugador._habilidades_libres = True
        jugador._dash_cooldown = 0.0

        jugador.is_grounded = False
        jugador.position.y -= 4
        _pulsar(im, Action.DASH)
        _soltar(im, Action.DASH)

        visto = False
        for _ in range(6):
            jugador.update(1 / 60, suelo, im)
            im.pump([])
            if isinstance(jugador._state_instance, DashingState):
                visto = True
                break
        assert visto, (
            "el dash pulsado justo antes de aterrizar no salió: es el defecto "
            "que GAP-040 describe — el salto lo perdonaba y ninguna otra "
            "acción tenía ese perdón"
        )
