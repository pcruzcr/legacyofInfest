"""AUD-828 — los terrestres caen y bajan escalones; los voladores no.

El reporte: enemigos de piso caminando en el aire sin hacer las bajadas.
Causa: `EnemyBase` no integra gravedad (`enemy_base.py:892-899`) y el anclaje
(`_mantener_en_suelo`) sólo engancha a 2-4 px: un escalón de una baldosa
(16 px) ni baja ni cae. Sólo `Walker` mira el borde, y para invertir, no para
descender.
"""
from __future__ import annotations

import pygame
import pytest


@pytest.fixture(autouse=True)
def _video():
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((800, 600))


def _brute_fuera_del_suelo():
    from src.framework.entities.enemy_brute import EnemyBrute

    suelo = [pygame.Rect(0, 400, 120, 50)]
    enemigo = EnemyBrute(pygame.Vector2(200.0, 400.0 - 56))
    enemigo.set_collision_rects(suelo)
    return enemigo


def test_sin_suelo_debajo_cae_en_vez_de_flotar() -> None:
    enemigo = _brute_fuera_del_suelo()
    y0 = enemigo.position.y
    for _ in range(30):
        enemigo.update(1 / 60.0)
    assert enemigo.position.y > y0 + 5.0, (
        "el brute sigue a la misma altura fuera de la plataforma: flota"
    )


def test_el_escalon_de_16_px_se_baja_sin_caer() -> None:
    from src.framework.entities.enemy_brute import EnemyBrute

    suelo_bajo = [pygame.Rect(0, 416, 400, 50)]
    enemigo = EnemyBrute(pygame.Vector2(100.0, 400.0 - 56))
    enemigo.set_collision_rects(suelo_bajo)
    for _ in range(30):
        enemigo.update(1 / 60.0)
    assert enemigo.rect.bottom == pytest.approx(416.0, abs=1.0), (
        f"pies en {enemigo.rect.bottom}: no bajó el escalón de 16 px"
    )


def test_la_caida_acelera_y_tiene_tope() -> None:
    enemigo = _brute_fuera_del_suelo()
    for _ in range(120):
        enemigo.update(1 / 60.0)
    assert enemigo._caida_vy == pytest.approx(500.0), (
        f"vy de caída {enemigo._caida_vy}: sin tope o sin gravedad"
    )


def test_el_no_terrestre_no_cae() -> None:
    """`ice_skater` lleva `_hug_slopes=False`: el fix no le toca."""
    from src.framework.entities.enemy_ice_skater import EnemyIceSkater

    enemigo = EnemyIceSkater(pygame.Vector2(100.0, 300.0))
    enemigo.set_collision_rects([pygame.Rect(0, 400, 400, 50)])
    y0 = enemigo.position.y
    for _ in range(30):
        enemigo.update(1 / 60.0)
    assert enemigo.position.y == pytest.approx(y0), (
        "un no-terrestre recibió gravedad de terrestre"
    )


def test_el_walker_en_suelo_no_cambia() -> None:
    from src.framework.entities.enemy_walker import EnemyWalker

    suelo = [pygame.Rect(0, 400, 2000, 50)]
    enemigo = EnemyWalker(pygame.Vector2(100.0, 300.0), patrol_length=40)
    enemigo.position.y = 400.0 - enemigo.rect.height
    enemigo.set_collision_rects(suelo)
    for _ in range(120):
        enemigo.update(1 / 60.0)
    assert enemigo.rect.bottom == pytest.approx(400.0, abs=1.0)
