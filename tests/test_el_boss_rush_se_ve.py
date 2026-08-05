"""AUD-274 — el Boss Rush se jugaba a ciegas.

Lo que faltaba
==============
AUD-261 conectó el modo entero: marcador, recuento de golpes, arrastre de vida
con curación declarada. Y el jugador **no veía nada de eso**. `docs/44` §4 lo
dejó como la única fila en ❌: «rótulos de jefe, marcador en pantalla,
pantallas intermedias».

El resultado era raro de explicar: la puntuación se calculaba bien, los golpes
se contaban bien, la vida se arrastraba bien, y nada de ello aparecía en
pantalla. Un modo con marcador invisible es, para quien juega, un modo sin
marcador.

Lo que se añade
---------------
Una franja de una línea en la parte alta: **en qué combate va, contra quién, y
cuántos golpes lleva**. Nada más — el Boss Rush es un modo de concentración y
una interfaz que tape la arena trabaja en contra del propio modo.

Se dibuja **sólo con el modo activo**, así que la partida normal no puede
notarlo. Ésa es la propiedad que fija la última prueba.
"""
from __future__ import annotations

import pygame
import pytest

from src.framework.stage.boss_rush_mode import BossRushMode, BossRushStage


@pytest.fixture(autouse=True)
def _video():
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((800, 600))


@pytest.fixture
def hud(event_bus):
    from src.engine.ui.hud import HUD

    return HUD(event_bus)


def _modo(n: int = 4) -> BossRushMode:
    m = BossRushMode()
    for i in range(n):
        m.add_stage(BossRushStage(f"boss{i}", f"JEFE {i}", scene_builder=None))
    m.start()
    return m


class TestElHudSabeDelModo:
    def test_tiene_donde_recibirlo(self, hud) -> None:
        assert hasattr(hud, "set_boss_rush")

    def test_por_defecto_no_dibuja_nada(self, hud) -> None:
        """La partida normal no puede ver la franja del Boss Rush."""
        superficie = pygame.Surface((800, 600))
        superficie.fill((20, 20, 20))

        hud._draw_boss_rush(superficie)

        assert superficie.get_at((400, 22))[:3] == (20, 20, 20)

    def test_con_el_modo_activo_dibuja(self, hud) -> None:
        superficie = pygame.Surface((800, 600))
        superficie.fill((20, 20, 20))
        m = _modo()
        hud.set_boss_rush(m.progress, m.current_name, m.score, 0)

        hud._draw_boss_rush(superficie)

        pinta = any(
            superficie.get_at((x, y))[:3] != (20, 20, 20)
            for x in range(0, 800, 4) for y in range(18, 34)
        )
        assert pinta, "la franja del Boss Rush no pinta un solo píxel"

    def test_apagarlo_lo_quita(self, hud) -> None:
        superficie = pygame.Surface((800, 600))
        superficie.fill((20, 20, 20))
        hud.set_boss_rush(_modo().progress, "JEFE 0", 0, 0)
        hud.set_boss_rush("", "", 0, 0)

        hud._draw_boss_rush(superficie)

        assert superficie.get_at((400, 22))[:3] == (20, 20, 20)


class TestLoQueDice:
    def test_el_progreso_cuenta_desde_uno(self) -> None:
        """«1/4» y no «0/4»: nadie llama primero al combate cero."""
        assert _modo().progress == "1/4"

    def test_avanza_al_acreditar(self) -> None:
        m = _modo()
        m.acreditar_combate(salud_restante=3.0, medidor=0.0)

        assert m.progress == "2/4"

    def test_da_el_nombre_del_jefe_actual(self) -> None:
        assert _modo().current_name == "JEFE 0"


class TestLaEscenaSeLoPasa:
    """La comprobación que lo habría evitado: alguien tiene que llamarlo."""

    def test_alguien_alimenta_el_hud_en_produccion(self) -> None:
        from pathlib import Path

        raiz = Path(__file__).resolve().parents[1] / "src"
        usos = [
            p.name for p in raiz.rglob("*.py")
            if p.name != "hud.py" and "set_boss_rush(" in p.read_text(encoding="utf-8")
        ]
        assert usos, (
            "el HUD sabe dibujar la franja y nadie le pasa los datos: el "
            "marcador vuelve a ser invisible"
        )
