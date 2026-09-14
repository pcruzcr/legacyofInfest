"""AUD-830 — tirolesa del stage 0: cartel, radio y salida con abajo.

Tres causas apiladas (mismo patrón que Paburu R18): sin cartel que enseñe G,
radio de enganche 14 px a 160 px del suelo, y salida sólo con flanco fresco
de salto en 0,75 s de viaje. Hay una sola tirolesa (`Zipline_246`): no se
crea otra.
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

import pygame
import pytest

RAIZ = Path(__file__).resolve().parent.parent
TMX = RAIZ / "assets" / "maps" / "stage0" / "stage0.tmx"


def _objetos_por_tipo(tipo: str):
    raiz = ET.parse(TMX).getroot()
    encontrados = []
    for og in raiz.findall("objectgroup"):
        for o in og.findall("object"):
            if o.get("type") == tipo:
                props = {p.get("name"): p.get("value")
                         for p in o.findall("properties/property")}
                encontrados.append((o, props))
    return encontrados


@pytest.fixture(autouse=True)
def _video():
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((800, 600))


def test_la_tirolesa_tiene_radio_generoso() -> None:
    cables = _objetos_por_tipo("Zipline")
    assert len(cables) == 1, f"se esperaba 1 tirolesa, hay {len(cables)}"
    _, props = cables[0]
    assert float(props.get("radio_de_enganche", 14.0)) >= 30.0, (
        "radio 14 px a 160 px del suelo: hay que saltar y pulsar G en una "
        "franja mínima (Paburu R18 ya midió que 18 no perdona)"
    )


def test_la_zona_g_ensena_la_tirolesa() -> None:
    carteles = _objetos_por_tipo("MessageTrigger_Once")
    cercados = [
        props.get("text", "") or ""
        for o, props in carteles if float(o.get("x", 0)) > 1300
    ]
    assert cercados, "la zona G no tiene carteles"
    assert any("tirolesa" in t.lower() for t in cercados), (
        "ningún cartel de la zona G enseña la tirolesa ni la tecla G"
    )
    assert any("G" in t for t in cercados), (
        "el cartel debe decir la tecla (G)"
    )


def _cable_real():
    from src.framework.ecs.components import Tirolesa

    o, props = _objetos_por_tipo("Zipline")[0]
    x, y = float(o.get("x")), float(o.get("y"))
    return Tirolesa(
        origen=pygame.Vector2(x, y),
        destino=pygame.Vector2(x + float(props.get("destino_dx", 96.0)),
                               y + float(props.get("destino_dy", 64.0))),
        velocidad=float(props.get("velocidad", 190.0)),
        radio_de_enganche=float(props.get("radio_de_enganche", 14.0)),
    )


def test_se_engancha_a_25_px_del_cable() -> None:
    """Con radio 30, parado bajo el tramo medio se engancha; con 14 no."""
    from src.framework.ecs import World
    from src.framework.ecs import systems as S

    cable = _cable_real()
    mundo = World()
    mundo.crear(cable)
    medio = (cable.origen + cable.destino) / 2
    # Punto a 25 px exactos del cable, en perpendicular: con radio 14 no
    # engancha y con 30 sí.
    px, py = medio.x - 21.25, medio.y + 13.25
    rect = pygame.Rect(int(px - 10), int(py - 16), 20, 32)
    assert S.tirolesa_alcanzable(mundo, rect) is not None, (
        "a 25 px del cable no engancha: el radio sigue corto"
    )


def test_soltarse_con_abajo_deja_caer() -> None:
    from src.engine.input.action_map import Action
    from src.framework.entities.player import Player
    from src.framework.entities.states import FallingState, TirolesaState

    class MandoAbajo:
        def is_action_held(self, a):
            return a == Action.CROUCH

        def is_action_pressed(self, a):
            return False

        def is_action_just_pressed(self, a):
            return False

        def pulsada_en_buffer(self, a):
            return False

    cable = _cable_real()
    jugador = Player(pygame.Vector2(cable.origen.x - 20, cable.origen.y - 20))
    jugador._change_state_instance(TirolesaState(cable))
    for _ in range(30):
        jugador._state_instance.update(jugador, 1.0 / 60.0, MandoAbajo())
        if isinstance(jugador._state_instance, FallingState):
            break
    assert isinstance(jugador._state_instance, FallingState), (
        "mantener abajo no suelta la tirolesa: sólo sale con salto o al final"
    )


def test_el_viaje_termina_sin_enterrarse() -> None:
    from src.framework.entities.player import Player
    from src.framework.entities.states import FallingState, TirolesaState

    cable = _cable_real()
    jugador = Player(pygame.Vector2(cable.origen.x - 20, cable.origen.y - 20))
    jugador._change_state_instance(TirolesaState(cable))
    for _ in range(300):
        jugador._state_instance.update(jugador, 1.0 / 60.0, None)
        if isinstance(jugador._state_instance, FallingState):
            break
    else:
        pytest.fail("el viaje no terminó: la tirolesa no suelta al jinete")
    assert jugador.rect.bottom <= 608, (
        f"el viaje termina enterrado (pies {jugador.rect.bottom} > suelo 608)"
    )
