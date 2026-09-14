"""T3-FINALIZATION — el Gavilán amenaza de verdad.

STATE (TELEGRAPHING→CHASE) → TELEGRAPH (anillo 0,4 s) → THREAT (picado
280 px/s con contacto 0,75 real; 3 plumas 150 px/s daño 0,5) →
COLLISION/DAMAGE (vía base + `apply_damage`, parry las desvía) →
COUNTERPLAY (esquiva lateral / parry) → FEEDBACK (BOSS_ATTACK + dive SFX
en disco + stinger de fase).
"""
from __future__ import annotations

import pygame
import pytest


@pytest.fixture(autouse=True)
def _video():
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((320, 240))


class _Bus:
    def __init__(self) -> None:
        self.emitidos: list[tuple] = []

    def emit(self, evento: str, **datos) -> None:
        self.emitidos.append((evento, datos))

    def subscribe(self, *_a, **_k) -> None:
        pass


def _gavilan(x: float = 800.0, y: float = 300.0):
    from src.stages.stage3_4_boss_gavilan.boss_gavilan import BossGavilan

    jefe = BossGavilan(pygame.Vector2(x, y))
    jefe._event_bus = _Bus()
    return jefe


def _jugador(x: float = 700.0, y: float = 300.0):
    from src.framework.entities.player import Player

    jugador = Player(pygame.Vector2(x, y))
    jugador._invincibility_timer = 0.0
    return jugador


def test_el_picado_se_telegrafia_y_sale_con_cuerpo() -> None:
    from src.framework.entities.enemy_base import EnemyState

    jefe = _gavilan()
    jefe._player_ref = pygame.Rect(700, 280, 20, 28)
    jefe._programar_ataque()
    assert jefe._telegraph == "DIVE"
    assert jefe.state == EnemyState.TELEGRAPHING

    jefe._telegraph_timer = 0.0
    jefe._alert_behavior(1 / 60)

    assert jefe._dive_timer > 0, "el picado no arrancó tras el telegraph"
    assert jefe._dive_vel.length() == pytest.approx(280.0)
    patrones = [p for p, _ in jefe._event_bus.emitidos]
    assert "BOSS_ATTACK" in patrones


def test_el_picado_no_fabrica_dano_falso() -> None:
    """El `PLAYER_DAMAGED amount=0.5` sin colisión mentía: sólo el contacto
    real (0,75 vía base) puede doler."""
    jefe = _gavilan()
    jefe._player_ref = pygame.Rect(700, 280, 20, 28)
    jefe._programar_ataque()
    jefe._telegraph_timer = 0.0
    jefe._alert_behavior(1 / 60)
    for evento, datos in jefe._event_bus.emitidos:
        if evento == "PLAYER_DAMAGED":
            assert "source" in datos or "pos" in datos, (
                "daño emitido sin origen ni colisión: feedback mentiroso"
            )


def test_fase_dos_dispara_plumas_reales_y_parables() -> None:
    jefe = _gavilan()
    jefe.current_phase = 1
    jefe._player_ref = pygame.Rect(700, 280, 20, 28)
    jefe._telegraph = "FEATHER_STORM"
    jefe._telegraph_timer = 0.0
    jefe._alert_behavior(1 / 60)

    assert len(jefe._plumas) == 3, "la tormenta no deja cuerpos"
    assert all(p.damage == 0.5 for p in jefe._plumas)

    # La pluma duele por colisión real…
    jugador = _jugador()
    pluma = jefe._plumas[0]
    pluma.rect.center = jugador.rect.center
    vida = jugador.current_health
    jefe._check_player_contact(jugador)
    assert jugador.current_health < vida

    # …y se puede parar como cualquier proyectil.
    jugador2 = _jugador()
    jugador2._parry_active = True
    jugador2._parry_window = 0.2
    jugador2._parry_success = False
    pluma2 = jefe._plumas[1]
    pluma2.rect.center = jugador2.rect.center
    jefe._contact_cooldown = 0.0
    jefe._check_player_contact(jugador2)
    assert jugador2._parry_success is True


def test_fase_dos_corre_mas_rapido() -> None:
    jefe = _gavilan()
    jefe.speed_multiplier = 1.4
    a0 = jefe._orbit_angle
    jefe._update_orbit(1.0)
    assert jefe._orbit_angle - a0 == pytest.approx(0.6 * 1.4)


def test_los_sfx_que_emite_existen_en_disco() -> None:
    import pathlib

    jefe = _gavilan()
    jefe._player_ref = pygame.Rect(700, 280, 20, 28)
    jefe._programar_ataque()
    jefe._telegraph_timer = 0.0
    jefe._alert_behavior(1 / 60)
    sonidos = [e for e, _ in jefe._event_bus.emitidos if e.startswith("SFX_")]
    assert "SFX_BOSSES_GAVILAN_DIVE" in sonidos, (
        f"el picado no usa su SFX propio: {sonidos}"
    )
    # El fichero existe en disco (antes: evento con tabla pero sin emisor).
    base = pathlib.Path("assets/sfx")
    assert (base / "bosses" / "sfx_bosses_gavilan_dive.wav").exists()
