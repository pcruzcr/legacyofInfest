"""Track C — la chimenea se corona: START → WALL CHAIN → LEDGE → BALCÓN.

Gate: dos muros de 186 px (y 134-320, interior 40 px) con balcones a
y=118 y moneda. Ni el salto (90 px) ni el doble (~154 px) llegan al
borde (186 px): sólo la cadena de muro + agarre sube. Caer devuelve al
suelo (abierto): fail con recovery. Los balcones laterales dejan libre
la zona de chequeo del grab (el dintel corrido la tapaba).
"""
from __future__ import annotations

import xml.etree.ElementTree as ET

import pygame

from src.engine.input.action_map import Action

TMX = "assets/maps/stage_mecanicas/stage_mecanicas.tmx"
DT = 1.0 / 60.0

#: Geometría del gate, espejo del TMX (ids 916-922).
MURO_IZQ = pygame.Rect(4416, 134, 16, 186)
MURO_DER = pygame.Rect(4472, 134, 16, 186)
SUELO = pygame.Rect(4300, 320, 500, 64)
BALCON_IZQ = pygame.Rect(4368, 118, 48, 8)
BALCON_DER = pygame.Rect(4488, 118, 48, 8)


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


def _jugador_en_chimenea():
    from src.framework.entities.player import Player
    from src.framework.entities.states import FallingState

    # Cayendo ya pegado al muro derecho a media altura: el gate se examina,
    # no la carrerilla (vx de marcha 45 px/s: cruzar andando no es la mecánica).
    jugador = Player(pygame.Vector2(4452.0, 220.0))
    jugador.rect.topleft = (4452, 220)
    jugador.is_grounded = False
    jugador._coyote_counter = 99.0
    jugador.velocity.update(0.0, 100.0)
    jugador._change_state_instance(FallingState(), force=True)
    jugador._habilidades_libres = True
    return jugador


def test_el_tmx_tiene_la_chimenea_completa() -> None:
    r = ET.parse(TMX).getroot()
    objetos = [
        (
            o.get("name"),
            o.get("type"),
            float(o.get("x")),
            float(o.get("y")),
            float(o.get("width")),
            float(o.get("height")),
        )
        for og in r.iter("objectgroup")
        for o in og.iter("object")
    ]
    muros = [v for v in objetos if v[1] == "Solid" and v[5] >= 180]
    assert len(muros) >= 2, "la chimenea perdió un muro"
    xs = sorted(v[2] for v in muros[-2:])
    interior = xs[1] - (xs[0] + 16)
    assert 40 <= interior <= 70, f"interior {interior}: ni abrazo ni travesía"
    assert any(
        v[1] == "Pickup" and v[3] < 130 for v in objetos
    ), "sin recompensa sobre la chimenea"
    assert any(
        v[1] == "MessageTrigger_Once" and 4300 <= v[2] <= 4460
        for v in objetos
    ), "sin lectura visual a la entrada"


def test_doble_salto_no_supera_el_borde() -> None:
    """Bypass imposible: con todo el repertorio aéreo menos el muro no se llega."""
    jugador = _jugador_en_chimenea()
    # A cielo abierto, lejos de los muros.
    jugador.position.update(4350.0, 270.0)
    jugador.rect.topleft = (4350, 270)
    jugador.is_grounded = False
    jugador._coyote_counter = 99.0
    solidos = [SUELO]
    pies_min = jugador.position.y + jugador.rect.height
    for _ in range(240):
        entrada = _Entrada(
            held=frozenset({Action.MOVE_RIGHT}),
            pressed=frozenset({Action.JUMP}),
        )
        jugador.update(DT, solidos, entrada)
        pies_min = min(pies_min, jugador.position.y + jugador.rect.height)
        if jugador.is_grounded and jugador.position.y + jugador.rect.height >= 319:
            pass
    assert pies_min > 139.0, (
        f"pies hasta y={pies_min}: el borde (y=134) se alcanza sin muro, "
        "el gate no exige nada"
    )


def test_la_cadena_de_muro_si_sube() -> None:
    """Tres wall-jumps alternos ganan altura real en la chimenea."""
    from src.framework.entities.player import PlayerState

    jugador = _jugador_en_chimenea()
    solidos = [SUELO, MURO_IZQ, MURO_DER]
    direccion = Action.MOVE_RIGHT
    pies_ini = jugador.position.y + jugador.rect.height
    # El WallSlide parpadea (contacto→vx=0→Falling→reenganche): como un
    # jugador real, se mantiene JUMP pulsado en el aire y el buffer (8f)
    # lo entrega en un fotograma de WallSlide. Cada wall-jump resta 1
    # de `_wall_jump_count` (3 por vuelo).
    saltos_de_muro = 0
    cuenta_previa = 3
    alternancias = 0
    mejor = pies_ini
    # Mash como un jugador real (el WallSlide parpadea a 30 Hz): cada
    # wall-jump resta de `_wall_jump_count` y exige el muro opuesto.
    for _ in range(60 * 20):
        pressed = frozenset({Action.JUMP})
        jugador.update(
            DT, solidos,
            _Entrada(held=frozenset({direccion}), pressed=pressed),
        )
        cuenta = int(getattr(jugador, "_wall_jump_count", 3))
        if cuenta < cuenta_previa:
            saltos_de_muro += cuenta_previa - cuenta
            # Tras cada salto se empuja hacia el muro opuesto.
            direccion = (
                Action.MOVE_LEFT if direccion == Action.MOVE_RIGHT
                else Action.MOVE_RIGHT
            )
            alternancias += 1
        cuenta_previa = cuenta
        pies = jugador.position.y + jugador.rect.height
        mejor = min(mejor, pies)
        if pies <= 150.0:
            break
    # AUD-839 — con la marcha a 120 (AUD-827) el re-enganche al muro
    # opuesto llega antes y la coronación cabe en los 3 wall-jumps de un
    # mismo vuelo (_wall_jump_count arranca en 3): la cadena engancha con
    # 3; lo que sigue demostrando altura y alternancia es lo de abajo.
    assert saltos_de_muro >= 3, (
        f"sólo {saltos_de_muro} wall-jumps: la cadena no engancha"
    )
    assert alternancias >= 2, "los saltos no alternan de muro"
    assert mejor <= 175.0, (
        f"mejor pies y={mejor}: la cadena no gana altura (salida {pies_ini})"
    )
    assert jugador.state != PlayerState.DYING


def test_el_bot_corona_la_chimenea() -> None:
    """CIMA: START → WALL CHAIN → LEDGE GRAB → BALCÓN, sin teletransporte.

    Técnica honesta: empujar para entrar en slide, SOLTAR tras cada
    salto (el aire fija vx=±22.5 si se mantiene y mata el impulso ∓90),
    re-empujar al llegar al muro opuesto. El grab entra solo al rozar
    el borde y el hop (mash) posa en el balcón.
    """
    jugador = _jugador_en_chimenea()
    solidos = [SUELO, MURO_IZQ, MURO_DER]
    balcones = [BALCON_IZQ, BALCON_DER]
    direccion = Action.MOVE_RIGHT
    cuenta_previa = 3
    soltar_hasta = -1
    saltos = grabs = 0
    cima = None
    for cuadro in range(60 * 60):
        nombre = type(jugador._state_instance).__name__
        held = (
            frozenset()
            if cuadro < soltar_hasta
            else frozenset({direccion})
        )
        if "LedgeGrab" in nombre:
            grabs += 1
        jugador.update(
            DT, solidos,
            _Entrada(held=held, pressed=frozenset({Action.JUMP})),
        )
        cuenta = int(getattr(jugador, "_wall_jump_count", 3))
        if cuenta < cuenta_previa:
            saltos += cuenta_previa - cuenta
            direccion = (
                Action.MOVE_LEFT if direccion == Action.MOVE_RIGHT
                else Action.MOVE_RIGHT
            )
            soltar_hasta = cuadro + 10
        cuenta_previa = cuenta
        pies = jugador.position.y + jugador.rect.height
        for balcon in balcones:
            if (pies <= balcon.y + 8
                    and balcon.x <= jugador.rect.centerx <= balcon.x + balcon.width
                    and jugador.velocity.y >= 0):
                jugador.update(
                    DT, [*solidos, balcon], _Entrada(held=frozenset())
                )
                if abs((jugador.position.y + jugador.rect.height) - balcon.y) <= 10:
                    cima = balcon.x
                    break
        if cima is not None:
            break
    assert cima is not None, (
        f"el bot no coronó: {saltos} wall-jumps, {grabs} grabs. "
        "Ver Track C del reporte para la técnica."
    )
    assert saltos >= 3, "la cima no usó la cadena de muro"
    assert grabs >= 1, "la cima no pasó por el agarre de repisa"
