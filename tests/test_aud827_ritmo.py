"""AUD-827 — ritmo a 60 FPS y marcha a 120 px/s (decisión del dueño, 2026-09-09).

Causa A (diseño): 90 px/s = 14,2 s por pantalla de 1280. Causa B (rendimiento):
presupuesto 8,33 ms inalcanzable en CPU (medido 15,5 ms P50); el propio
`settings` declaraba 60 como recomendado y AUD-390 diseñó los mapas para
`FIXED_DT = 1/60`. El cambio devuelve el paso que los mapas suponían y la
mitad de pasos de simulación por segundo.
"""
from __future__ import annotations

import pygame
import pytest

from src.engine.core import settings


@pytest.fixture(autouse=True)
def _video():
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((800, 600))


def test_el_objetivo_es_60_fps() -> None:
    from src.engine.core import clock

    assert settings.TARGET_FPS == 60
    assert clock.FIXED_DT == pytest.approx(1.0 / 60)


def test_la_marcha_es_120_px_por_segundo() -> None:
    assert settings.PLAYER_WALK_SPEED == pytest.approx(120.0)
    assert 1280.0 / settings.PLAYER_WALK_SPEED == pytest.approx(10.7, abs=0.1)


def test_caminar_un_segundo_avanza_la_marcha() -> None:
    """Runtime con `Player` real: 60 pasos de 1/60 con derecha sostenida."""
    from src.engine.input.action_map import Action
    from src.framework.entities.player import Player

    class Mando:
        def is_action_held(self, a):
            return a in (Action.MOVE_RIGHT,)

        def is_action_pressed(self, a):
            return False

        def is_action_just_pressed(self, a):
            return False

        def pulsada_en_buffer(self, a):
            return False

    jugador = Player(pygame.Vector2(100.0, 100.0))
    suelo = [pygame.Rect(0, 132, 2000, 40)]
    for _ in range(240):
        jugador.update(1.0 / 60.0, suelo, Mando())
    x0 = jugador.position.x
    for _ in range(60):
        jugador.update(1.0 / 60.0, suelo, Mando())
    assert jugador.position.x - x0 == pytest.approx(120.0, abs=6.0)
