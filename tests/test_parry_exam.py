"""T1-FINALIZATION — el parry tiene examen real en la sala Defensa.

Cadena: TEACH (tutorial_hub sala 3 + trigger 118) → OPPORTUNITY
(ParryTeacher en el TMX, telegraph 1,2 s) → COUNTERPLAY (parry en ventana)
→ FEEDBACK (STUNNED 2 s + VFX/SFX) → REWARD (castigo + pickup "¡Parry!").
"""
from __future__ import annotations

import xml.etree.ElementTree as ET

import pygame
import pytest

TMX = "assets/maps/tutorial_hub/tutorial_hub.tmx"


@pytest.fixture(autouse=True)
def _video():
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((320, 240))


class _Bus:
    def __init__(self) -> None:
        self.emitidos: list[str] = []

    def emit(self, evento: str, **_datos) -> None:
        self.emitidos.append(evento)

    def subscribe(self, *_a, **_k) -> None:
        pass


def _jugador(x: float = 1500.0, y: float = 292.0):
    from src.framework.entities.player import Player

    jugador = Player(pygame.Vector2(x, y))
    jugador._invincibility_timer = 0.0
    return jugador


def _profesor(jugador):
    from src.framework.entities.enemy_parry_teacher import EnemyParryTeacher

    prof = EnemyParryTeacher(pygame.Vector2(jugador.position.x, jugador.position.y))
    prof._event_bus = _Bus()
    prof._contact_cooldown = 0.0
    prof.position.update(jugador.position)
    prof.rect.center = jugador.rect.center
    prof._update_rects()
    return prof


def test_el_hub_coloca_un_profesor_en_la_sala_defensa() -> None:
    """La oportunidad existe en el nivel, no sólo en el código."""
    r = ET.parse(TMX).getroot()
    profs = [
        (o.get("name"), float(o.get("x")))
        for og in r.iter("objectgroup")
        for o in og.iter("object")
        if o.get("type") == "ParryTeacher"
    ]
    assert profs, "ningún ParryTeacher en tutorial_hub: el examen no existe"
    for nombre, x in profs:
        assert 1300.0 <= x <= 2100.0, (
            f"{nombre} en x={x}: fuera de la sala Defensa (1300-2100)"
        )


def test_el_profesor_esta_registrado_para_tmx() -> None:
    from src.framework.entities import entity_factory
    from src.framework.entities.enemy_parry_teacher import EnemyParryTeacher
    from src.framework.stage.stage_loader import StageLoader

    entity_factory.ensure_registered()
    assert StageLoader._entity_registry.get("ParryTeacher") is EnemyParryTeacher


def test_el_telegraph_es_generoso_frente_a_la_ventana() -> None:
    """1,2 s de aviso contra 0,25 s de ventana: se puede leer, no adivinar."""
    from src.framework.entities.states.ability import _ventana_de_parry

    jugador = _jugador()
    prof = _profesor(jugador)
    assert prof._telegraph_duration >= 4 * _ventana_de_parry(), (
        f"telegraph {prof._telegraph_duration} s contra ventana "
        f"{_ventana_de_parry()} s: el examen exige adivinar"
    )


def test_parry_acertado_aturde_dos_segundos_con_feedback() -> None:
    from src.framework.entities.enemy_base import EnemyState

    jugador = _jugador()
    prof = _profesor(jugador)
    jugador._parry_active = True
    jugador._parry_window = 0.2
    jugador._parry_success = False
    vida = jugador.current_health

    prof._check_player_contact(jugador)

    assert jugador._parry_success is True
    assert prof.state == EnemyState.STUNNED
    assert prof._stun_timer == pytest.approx(2.0), (
        f"stun de {prof._stun_timer}: el gancho _aturdimiento_por_parry no "
        "llega al profesor"
    )
    assert "VFX_PARRY" in prof._event_bus.emitidos
    assert "SFX_PLAYER_PARRY" in prof._event_bus.emitidos
    assert jugador.current_health == vida, "el parry no evitó el daño"


def test_sin_parry_el_profesor_si_hace_dano() -> None:
    """Sin counterplay hay fail: el examen puede suspenderse."""
    jugador = _jugador()
    prof = _profesor(jugador)
    jugador._parry_active = False
    jugador._parry_window = 0.0
    vida = jugador.current_health

    prof._check_player_contact(jugador)

    assert jugador.current_health < vida
