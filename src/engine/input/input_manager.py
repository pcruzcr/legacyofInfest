"""
Module: input_manager
System: engine.input
Academic Unit: N/A
Description: Unified keyboard + controller input manager. Tracks pressed/held/released
states for abstract Actions defined in action_map.py.
"""
from __future__ import annotations

import logging
from typing import Any

import pygame

from src.engine.input.action_map import (
    _CONTROLLER_BUTTON_MAP,
    CONTROLLER_AXIS_LEFT_X,
    CONTROLLER_AXIS_LEFT_Y,
    CONTROLLER_DEADZONE,
    DEFAULT_KEY_BINDINGS,
    Action,
)

logger = logging.getLogger(__name__)

#: Acciones que `hold_to_press` convierte en conmutador (AUD-126).
#:
#: Las direcciones quedan fuera a propósito: un jugador que pulsa «derecha» y
#: se queda andando para siempre está peor que antes de la ayuda. Sólo se
#: conmuta lo que el diseño pide sostener.
_ACCIONES_CONMUTABLES: frozenset[Action] = frozenset({
    Action.DASH,
    Action.GRAB,
    Action.CROUCH,
    Action.LONG_ATTACK,
})


def _conmutar_mantener() -> bool:
    """¿Está activada la ayuda de «mantener pulsado»?

    Se consulta en cada fotograma en lugar de guardarse: el jugador puede
    cambiarla desde el menú de pausa y esperar que surta efecto al volver, no
    al reiniciar.
    """
    from src.engine.core import user_settings

    return bool(user_settings.preferencia("hold_to_press", False))


class InputManager:
    """Tracks keyboard + controller input with pressed/held/released semantics."""

    def __init__(self) -> None:
        self._bindings: dict[Action, list[int]] = {
            action: list(keys) for action, keys in DEFAULT_KEY_BINDINGS.items()
        }
        self._pressed_this_frame: set[int] = set()
        self._held: set[int] = set()
        self._released_this_frame: set[int] = set()
        self._consumed_actions: set[Action] = set()
        self._raw_keys_pressed: set[int] = set()
        #: Acciones que el jugador dejó conmutadas a «activa» (AUD-126).
        self._conmutadas: set[Action] = set()

        # Controller state
        self._joystick: Any | None = None
        self._init_joystick()
        self._controller_buttons_held: set[int] = set()
        self._controller_buttons_pressed: set[int] = set()
        self._controller_buttons_released: set[int] = set()
        self._controller_axis_left: float = 0.0
        self._controller_axis_right: float = 0.0
        self._controller_axis_up: bool = False
        self._controller_axis_down: bool = False
        #: AUD-320 — el mando y la navegación de menús.
        #:
        #: Los menús de este juego se manejan con
        #: `is_raw_key_pressed(K_UP/K_DOWN/...)`; el mando no genera teclas.
        #: En vez de reescribir escenas (los hay que leen las teclas en tres
        #: sitios) se sintetiza aquí, una sola vez: cuando el hat de la
        #: cruceta o el eje vertical cruzan la banda muerta, el fotograma
        #: lleva una flecha de más. Lo que nunca se hace es repetir la
        #: pulsación mientras se sostiene: un menú recorrería varias filas
        #: por toque.
        self._controller_hat: tuple[int, int] = (0, 0)
        self._hat_edge_up = self._hat_edge_down = False
        self._hat_edge_left = self._hat_edge_right = False
        self._hat_held_up = self._hat_held_down = False
        self._hat_held_left = self._hat_held_right = False
        self._axis_edge_up = self._axis_edge_down = False
        self._axis_edge_left = self._axis_edge_right = False

        #: AUD-373 — el buffer de entrada, para todas las acciones. Cierra GAP-040.
        #:
        #: El salto ya tenía buffer, cableado a mano dentro de `Player`
        #: (`_pending_jump` + su temporizador) y para una sola acción. Ninguna
        #: otra lo tenía: pulsar dash o atacar un fotograma antes de aterrizar
        #: se perdía sin más, porque el estado que recibe la pulsación decide
        #: que no puede ejecutarla y la tira.
        #:
        #: Vive aquí y no en el jugador porque es un problema de **entrada**,
        #: no de física: «lo pulsé, tú no lo viste» es la misma queja para
        #: saltar que para atacar, y resolverla una vez por acción es lo que
        #: evitaba que hubiera dos mecanismos distintos haciendo lo mismo.
        #:
        #: Se cuenta en fotogramas de `pump()` y no en segundos: el buffer es
        #: una concesión al tiempo de reacción humano medido en fotogramas
        #: —los 8 de aquí son ~133 ms a 60 Hz—, y desde AUD-390 la simulación
        #: avanza en pasos fijos, así que contar fotogramas es determinista y
        #: contar `dt` acumulado no lo era.
        self._fotograma: int = 0
        self._pulsada_en_fotograma: dict[Action, int] = {}

    #: Ventana por defecto, en fotogramas. Los 8 son los que ya usaba el salto
    #: (`8.0 / 60.0` en `AirborneState`), conservados tal cual para no
    #: re-calibrar de paso algo que ya estaba ajustado y probado.
    VENTANA_DE_BUFFER: int = 8

    def _init_joystick(self) -> None:
        """Initialize the first available joystick."""
        try:
            if pygame.joystick.get_count() > 0:
                self._joystick = pygame.joystick.Joystick(0)
                self._joystick.init()
        except pygame.error:
            logger.warning("input_manager: failed to init joystick")
            self._joystick = None

    def pump(self, events: list[pygame.event.Event]) -> None:
        """Process raw pygame events. Called once per frame by App."""
        self._pressed_this_frame.clear()
        self._released_this_frame.clear()
        self._consumed_actions.clear()
        self._raw_keys_pressed.clear()
        self._controller_buttons_pressed.clear()
        self._controller_buttons_released.clear()
        self._hat_edge_up = self._hat_edge_down = False
        self._hat_edge_left = self._hat_edge_right = False
        self._axis_edge_up = self._axis_edge_down = False
        self._axis_edge_left = self._axis_edge_right = False

        for e in events:
            if e.type == pygame.KEYDOWN:
                if e.key not in self._held:
                    self._pressed_this_frame.add(e.key)
                    self._raw_keys_pressed.add(e.key)
                self._held.add(e.key)
            elif e.type == pygame.KEYUP:
                self._held.discard(e.key)
                self._released_this_frame.add(e.key)
            elif e.type == pygame.JOYBUTTONDOWN:
                if e.button not in self._controller_buttons_held:
                    self._controller_buttons_pressed.add(e.button)
                self._controller_buttons_held.add(e.button)
            elif e.type == pygame.JOYBUTTONUP:
                self._controller_buttons_held.discard(e.button)
                self._controller_buttons_released.add(e.button)
            elif e.type == pygame.JOYAXISMOTION:
                self._poll_axes()
            elif e.type == pygame.JOYHATMOTION:
                self._poll_hat(e.value)

        # AUD-320 — una vez por fotograma, y aquí: los menús leen teclas
        # crudas, y éste es el único sitio donde el mando puede ponérselas.
        self._sintetizar_navegacion_por_mando()

        # AUD-126 — una vez por fotograma, y aquí: `is_action_held` es una
        # pregunta y una pregunta no debe tener efectos.
        self._actualizar_conmutadas()

        # AUD-373 — el sello de las pulsaciones de este fotograma, para el
        # buffer. Va al final de `pump` porque `_sintetizar_navegacion_por_mando`
        # todavía puede añadir pulsaciones, y una que llegue después del sello
        # no entraría en el buffer.
        self._fotograma += 1
        for accion in self._bindings:
            if self.is_action_just_pressed(accion):
                self._pulsada_en_fotograma[accion] = self._fotograma

    def is_action_just_pressed(self, action: Action) -> bool:
        """True only on the frame the action's key was first pressed."""
        if action in self._consumed_actions:
            return False
        keys = self._bindings.get(action, [])
        if any(k in self._pressed_this_frame for k in keys):
            return True
        return self._action_from_controller(action)

    def is_action_pressed(self, action: Action) -> bool:
        return self.is_action_just_pressed(action)

    def is_action_held(self, action: Action) -> bool:
        """True every frame while the action's key is held down.

        AUD-126 — «mantener pulsado» convertido en conmutador
        -----------------------------------------------------
        Con `hold_to_press` activado, una pulsación **activa** la acción y la
        siguiente la **desactiva**, en vez de exigir el dedo puesto. Para quien
        tiene temblor, artritis o usa un conmutador adaptado, mantener una
        tecla durante un tramo de plataformas es la diferencia entre jugar y no
        jugar.

        Se implementa aquí porque `is_action_held` es el único sitio por el que
        pasan las 42 consultas de acción mantenida del proyecto. Hacerlo en
        cada estado del jugador habría dependido de que 42 sitios se acordaran,
        y basta que uno se olvide para que el ajuste parezca roto.

        Las direcciones **no** se conmutan: un jugador que pulsa «derecha» y
        se queda andando para siempre está peor que antes. Sólo se conmutan las
        acciones que el diseño pide sostener.
        """
        if _conmutar_mantener() and action in _ACCIONES_CONMUTABLES:
            return action in self._conmutadas
        keys = self._bindings.get(action, [])
        if any(k in self._held for k in keys):
            return True
        return self._action_held_from_controller(action)

    def _actualizar_conmutadas(self) -> None:
        """Aplica los flancos de subida del fotograma a las acciones conmutadas.

        AUD-126 — por qué esto vive en `pump` y no en `is_action_held`
        --------------------------------------------------------------
        La primera versión conmutaba dentro de `is_action_held`. Parecía
        natural y estaba mal: **esa función se consulta varias veces por
        fotograma** —la máquina de estados del jugador, el HUD y el sistema de
        combate preguntan cada uno por su cuenta— así que una sola pulsación
        conmutaba dos o tres veces y la acción quedaba como estuviera, al azar
        según cuántos sistemas hubieran preguntado ese fotograma.

        Lo cazó `test_la_segunda_pulsacion_la_apaga` a la primera ejecución. Es
        la regla general: **una consulta no debe tener efectos**. Aquí se
        aplica una vez por fotograma, en el sitio donde ya se procesan los
        eventos, y `is_action_held` vuelve a ser una pregunta.

        Si la ayuda está apagada se limpia el conjunto: quien la prueba y la
        quita no debe quedarse corriendo sin tocar nada y sin forma de parar.
        """
        if not _conmutar_mantener():
            self._conmutadas.clear()
            return
        for action in _ACCIONES_CONMUTABLES:
            keys = self._bindings.get(action, [])
            if any(k in self._pressed_this_frame for k in keys):
                if action in self._conmutadas:
                    self._conmutadas.discard(action)
                else:
                    self._conmutadas.add(action)

    def is_action_released(self, action: Action) -> bool:
        """True only on the frame the action's key was released."""
        keys = self._bindings.get(action, [])
        if any(k in self._released_this_frame for k in keys):
            return True
        return self._action_released_from_controller(action)

    def pulsada_en_buffer(self, action: Action, ventana: int | None = None) -> bool:
        """¿Se pulsó esta acción en los últimos `ventana` fotogramas?

        AUD-373 — la primitiva que `GAP-040` pedía. Cierra ese hueco.

        Es lo que convierte «lo pulsé justo antes de tocar el suelo» en una
        acción que sale, en vez de en una que se pierde. El estado que no puede
        ejecutar la acción ahora **no** tiene que acordarse de guardarla: la
        pulsación sigue estando aquí unos fotogramas y el estado que sí pueda
        la recoge.

        La ventana se puede afinar por acción —un dash perdonado durante medio
        segundo se sentiría fantasmal, y un salto de dos fotogramas no
        perdonaría nada— pero el valor por defecto es el que ya estaba
        calibrado para el salto.
        """
        marca = self._pulsada_en_fotograma.get(action)
        if marca is None:
            return False
        ventana = self.VENTANA_DE_BUFFER if ventana is None else ventana
        return (self._fotograma - marca) < ventana

    def consumir_buffer(self, action: Action) -> None:
        """Da la pulsación por gastada, para que no salga dos veces.

        Sin esto, un salto con buffer se dispararía en cada fotograma de la
        ventana: el jugador tocaría suelo y saldría disparado ocho veces.
        Quien ejecuta la acción es quien la consume — la misma regla que
        `consume()` sigue para `is_action_just_pressed`.
        """
        self._pulsada_en_fotograma.pop(action, None)

    def consume(self, action: Action) -> None:
        """Consume an action so is_pressed returns False for the rest of the frame."""
        self._consumed_actions.add(action)

    def rebind(self, action: Action, keys: list[int]) -> None:
        """Rebind an action to a new list of key constants."""
        self._bindings[action] = list(keys)

    def is_raw_key_pressed(self, key: int) -> bool:
        """True only on the frame this physical key was first pressed."""
        return key in self._raw_keys_pressed

    def _poll_axes(self) -> None:
        """Poll joystick axes and update directional state."""
        if self._joystick is None:
            return
        try:
            prev_left = self._controller_axis_left
            prev_up = self._controller_axis_up
            prev_down = self._controller_axis_down
            x = self._joystick.get_axis(CONTROLLER_AXIS_LEFT_X)
            y = self._joystick.get_axis(CONTROLLER_AXIS_LEFT_Y)
            self._controller_axis_left = x if abs(x) > CONTROLLER_DEADZONE else 0.0
            self._controller_axis_right = 0.0
            self._controller_axis_up = y < -CONTROLLER_DEADZONE
            self._controller_axis_down = y > CONTROLLER_DEADZONE
            # AUD-320: el borde (cruzar la banda muerta) es la pulsación; el
            # eje sostenido en el mismo sitio no puede repetirla.
            self._axis_edge_up = self._controller_axis_up and not prev_up
            self._axis_edge_down = self._controller_axis_down and not prev_down
            self._axis_edge_left = self._controller_axis_left < 0 and prev_left >= 0
            self._axis_edge_right = self._controller_axis_left > 0 and prev_left <= 0
        except pygame.error:
            logger.warning("input_manager: failed to poll joystick axes")

    def _poll_hat(self, value: tuple[int, int]) -> None:
        """El hat de la cruceta: digital, y con borde por dirección.

        AUD-320 — un `JOYHATMOTION` se recibe cada vez que el valor cambia,
        así que el borde se calcula comparando con lo que había: la pulsación
        es el cambio, no el estado.
        """
        x, y = value
        self._hat_edge_up = y == 1 and not self._hat_held_up
        self._hat_edge_down = y == -1 and not self._hat_held_down
        self._hat_edge_left = x == -1 and not self._hat_held_left
        self._hat_edge_right = x == 1 and not self._hat_held_right
        self._hat_held_up = y == 1
        self._hat_held_down = y == -1
        self._hat_held_left = x == -1
        self._hat_held_right = x == 1
        self._controller_hat = (x, y)

    def _sintetizar_navegacion_por_mando(self) -> None:
        """Traduce hat y eje del mando a flechas del teclado, un fotograma.

        AUD-320 — los menús navegan con `is_raw_key_pressed(K_UP/...)` y
        nunca recibirían nada del mando. Esta es la única puerta entre los
        dos mundos: la cruceta o el palo en un menú se comportan como si
        hubiera una flecha pulsada durante ese fotograma.
        """
        if self._hat_edge_up or self._axis_edge_up:
            self._raw_keys_pressed.add(pygame.K_UP)
        if self._hat_edge_down or self._axis_edge_down:
            self._raw_keys_pressed.add(pygame.K_DOWN)
        if self._hat_edge_left or self._axis_edge_left:
            self._raw_keys_pressed.add(pygame.K_LEFT)
        if self._hat_edge_right or self._axis_edge_right:
            self._raw_keys_pressed.add(pygame.K_RIGHT)

    def _action_from_controller(self, action: Action) -> bool:
        """Check if any controller binding matches the action."""
        if action == Action.MOVE_LEFT:
            return self._controller_axis_left < 0 or self._hat_edge_left
        if action == Action.MOVE_RIGHT:
            return self._controller_axis_left > 0 or self._hat_edge_right
        if action == Action.MOVE_UP:
            return self._axis_edge_up or self._hat_edge_up
        if action == Action.MOVE_DOWN:
            return self._axis_edge_down or self._hat_edge_down
        if action == Action.JUMP:
            btn = next((b for b, a in _CONTROLLER_BUTTON_MAP.items() if a == Action.JUMP), None)
            return btn is not None and (btn in self._controller_buttons_pressed or self._controller_axis_up)
        if action == Action.CROUCH:
            btn = next((b for b, a in _CONTROLLER_BUTTON_MAP.items() if a == Action.CROUCH), None)
            return btn is not None and (btn in self._controller_buttons_held or self._controller_axis_down)
        btn = next((b for b, a in _CONTROLLER_BUTTON_MAP.items() if a == action), None)
        if btn is not None:
            return btn in self._controller_buttons_pressed
        return False

    def _action_held_from_controller(self, action: Action) -> bool:
        """Check if action is being held on controller."""
        if action == Action.MOVE_LEFT:
            return self._controller_axis_left < 0 or self._hat_held_left
        if action == Action.MOVE_RIGHT:
            return self._controller_axis_left > 0 or self._hat_held_right
        if action == Action.MOVE_UP:
            return self._controller_axis_up or self._hat_held_up
        if action == Action.MOVE_DOWN:
            return self._controller_axis_down or self._hat_held_down
        if action == Action.CROUCH:
            return self._controller_axis_down
        btn = next((b for b, a in _CONTROLLER_BUTTON_MAP.items() if a == action), None)
        if btn is not None:
            return btn in self._controller_buttons_held
        return False

    def _action_released_from_controller(self, action: Action) -> bool:
        """Check if action was released on controller."""
        if action in (Action.MOVE_LEFT, Action.MOVE_RIGHT):
            return abs(self._controller_axis_left) < CONTROLLER_DEADZONE and self._controller_hat[0] == 0
        if action == Action.MOVE_UP:
            return not self._controller_axis_up and not self._hat_held_up
        if action == Action.MOVE_DOWN:
            return not self._controller_axis_down and not self._hat_held_down
        if action == Action.CROUCH:
            return not self._controller_axis_down
        btn = next((b for b, a in _CONTROLLER_BUTTON_MAP.items() if a == action), None)
        if btn is not None:
            return btn in self._controller_buttons_released
        return False

    @staticmethod
    def is_raw_key_held(key: int) -> bool:
        """True every frame while this physical key is held down."""
        return bool(pygame.key.get_pressed()[key])
