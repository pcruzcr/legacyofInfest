"""
Module: action_map
System: engine.input
Academic Unit: N/A
Description: Action enum and keyboard bindings for abstract input actions.
"""
from __future__ import annotations

from enum import Enum, auto

import pygame


class Action(Enum):
    """Abstract game actions. Bindings map physical keys to these actions."""
    MOVE_LEFT = auto()
    MOVE_RIGHT = auto()
    MOVE_UP = auto()
    MOVE_DOWN = auto()
    JUMP = auto()
    CROUCH = auto()
    SHORT_ATTACK = auto()
    LONG_ATTACK = auto()
    DASH = auto()
    GRAB = auto()
    #: F4.2 — disparo con el arco. Los estudiantes pidieron un ataque a
    #: distancia; sin acción propia habría que reutilizar una existente y
    #: perder el ataque que ya tenía.
    RANGED_ATTACK = auto()
    CONFIRM = auto()
    CANCEL = auto()
    PAUSE = auto()
    # Learning overlay panels (ARC-034)
    LEARN_MATH = auto()
    LEARN_PHYSICS = auto()
    LEARN_COLLISION = auto()
    LEARN_FSM = auto()
    LEARN_RENDER = auto()
    LEARN_AUDIO = auto()
    LEARN_PERF = auto()
    LEARN_CONTROLS = auto()
    LEARN_HELP = auto()
    OPEN_BESTIARY = auto()
    # AUD-022: AudioManager.toggle_mute()/is_muted existed with no callers, so
    # the game had no working mute at all. M is the conventional binding.
    TOGGLE_MUTE = auto()
    #: AUD-260 — el tiempo bala. `TiempoBala` estaba entera desde F5 y **no
    #: tenía forma de encenderse**: sin acción propia habría que reutilizar
    #: una existente, y entonces se activaría al saltar o al correr sin
    #: querer. Sólo hace algo en los escenarios que declaran `tiempo_bala`.
    BULLET_TIME = auto()
    #: AUD-555 — cambiar de pestaña en el menú de pausa (Equipo/Habilidades/
    #: Mapa/Menú, `PausePanel`). No reutiliza `MOVE_LEFT`/`MOVE_RIGHT`
    #: a propósito: cada pestaña ya usa esas dos para su propia navegación
    #: interna (la rejilla del inventario, por ejemplo) — reutilizarlas
    #: cambiaría de pestaña sin querer cada vez que el jugador mueve el
    #: cursor dentro de una.
    TAB_PREV = auto()
    TAB_NEXT = auto()


# Default keyboard bindings: Action -> list of pygame key constants
# AUD-720 — teclado accesible: cada acción tiene alternativa flechas/WASD
# y el ratón (InputManager._mouse_map) y el mando (_CONTROLLER_BUTTON_MAP)
# cubren las mismas acciones, así que ninguna mecánica exige una mano sola.
DEFAULT_KEY_BINDINGS: dict[Action, list[int]] = {
    # Movimiento: flechas + WASD (izq=A/LEFT, der=D/RIGHT, arriba=W/UP, abajo=S/DOWN)
    Action.MOVE_LEFT: [pygame.K_LEFT, pygame.K_a],
    Action.MOVE_RIGHT: [pygame.K_RIGHT, pygame.K_d],
    Action.MOVE_UP: [pygame.K_UP, pygame.K_w],
    Action.MOVE_DOWN: [pygame.K_DOWN, pygame.K_s],
    # Salto: SPACE primario, W/UP alternativas (en cenital W es sólo mover)
    Action.JUMP: [pygame.K_SPACE, pygame.K_UP, pygame.K_w],
    Action.CROUCH: [pygame.K_DOWN, pygame.K_s],
    # AUD-720: DASH en LSHIFT/RALT + botón central ratón (ver InputManager)
    Action.DASH: [pygame.K_LSHIFT, pygame.K_RSHIFT, pygame.K_LALT],
    Action.GRAB: [pygame.K_g, pygame.K_c],
    # F: cerca de las teclas de movimiento con la mano izquierda, y libre.
    Action.RANGED_ATTACK: [pygame.K_f, pygame.K_v],
    # Ataques: Z/J y X/K — mano izq y der; ratón izq/der es la 3ª alternativa
    Action.SHORT_ATTACK: [pygame.K_z, pygame.K_j],
    Action.LONG_ATTACK: [pygame.K_x, pygame.K_k],
    Action.CONFIRM: [pygame.K_RETURN, pygame.K_SPACE, pygame.K_z],
    Action.CANCEL: [pygame.K_ESCAPE, pygame.K_x],
    Action.PAUSE: [pygame.K_ESCAPE, pygame.K_p],
    Action.LEARN_MATH: [pygame.K_F2],
    Action.LEARN_PHYSICS: [pygame.K_F3],
    Action.LEARN_COLLISION: [pygame.K_F4],
    Action.LEARN_FSM: [pygame.K_F5],
    Action.LEARN_RENDER: [pygame.K_F6],
    Action.LEARN_AUDIO: [pygame.K_F7],
    Action.LEARN_PERF: [pygame.K_F8],
    Action.LEARN_CONTROLS: [pygame.K_F9],
    Action.LEARN_HELP: [pygame.K_F10],
    Action.OPEN_BESTIARY: [pygame.K_TAB],
    Action.TOGGLE_MUTE: [pygame.K_m],
    # AUD-260 — `Q` y `R`: las dos libres, las dos alcanzables con la mano
    # izquierda sin soltar el movimiento, y ninguna ligada a saltar, correr o
    # atacar. Se **mantiene pulsada**, no se conmuta: la reserva se gasta
    # mientras dura, así que soltar tiene que devolver el tiempo al momento.
    Action.BULLET_TIME: [pygame.K_q, pygame.K_r],
    # AUD-555 — coma/punto: el par convencional de "anterior/siguiente" en
    # muchos juegos, y ninguna de las dos teclas está tomada por otra acción.
    # Ampliado para 1280×720@120: Q/E y LB/RB son los gatillos Ocarina
    # (izq/der) que el jugador espera; LEFT/RIGHT quedan para la pestaña
    # interna (inventario) pero también deben cambiar pestaña cuando no hay
    # foco interno — se resuelve en pausa.py vía fallback.
    Action.TAB_PREV: [pygame.K_COMMA, pygame.K_q, pygame.K_LEFTBRACKET],
    Action.TAB_NEXT: [pygame.K_PERIOD, pygame.K_e, pygame.K_RIGHTBRACKET],
}

# Controller axis/deadzone constants
CONTROLLER_DEADZONE: float = 0.25
CONTROLLER_AXIS_LEFT_X: int = 0
CONTROLLER_AXIS_LEFT_Y: int = 1
CONTROLLER_AXIS_RIGHT_X: int = 2
CONTROLLER_AXIS_RIGHT_Y: int = 3
CONTROLLER_AXIS_TRIGGER_LEFT: int = 4
CONTROLLER_AXIS_TRIGGER_RIGHT: int = 5
# AUD-720 — mapeo ampliado: antes 8 acciones, ahora 12; LT/RT y stick-click
# usan lo que queda libre sin pisar lo existente.
_CONTROLLER_BUTTON_MAP: dict[int, Action] = {
    0: Action.JUMP,           # A
    1: Action.SHORT_ATTACK,   # B
    2: Action.LONG_ATTACK,    # X
    3: Action.CROUCH,         # Y
    4: Action.GRAB,           # LB
    5: Action.RANGED_ATTACK,  # RB
    6: Action.CANCEL,         # SELECT/BACK
    7: Action.PAUSE,          # START
    8: Action.DASH,           # L-STICK
    9: Action.BULLET_TIME,    # R-STICK
    10: Action.TAB_PREV,      # extra (si existe)
    11: Action.TAB_NEXT,
}
