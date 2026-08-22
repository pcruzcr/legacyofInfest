"""AUD-575 (GAP-071 resuelto) — el aviso de oxígeno llega al HUD.

`ControlDeNado.avisando` llevaba declarado «quedan menos de diez
segundos» desde el diseño del nado y nadie lo mostraba: el jugador se
ahogaba sin saberlo. La barra de oxígeno (bajo la estamina) se dibuja
sólo mientras se está bajo el agua (`ratio >= 0`) y, en el tramo de
aviso, parpadea y pulsa `Events.SFX_TIMER_ALERT_PULSE` — el mismo
sonido del cronómetro, que ya tiene consumidor.
"""
from __future__ import annotations

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame
import pytest

from src.engine.core import settings
from src.engine.core.event_bus import EventBus
from src.engine.core.events import Events


@pytest.fixture(scope="module")
def _video():
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT))
    yield


@pytest.fixture
def hud(_video):
    from src.engine.ui.hud import HUD

    return HUD(EventBus())


def _lienzo() -> pygame.Surface:
    surf = pygame.Surface((settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT))
    surf.fill((0, 0, 0))
    return surf


class TestLaBarraDeOxigeno:
    def test_sin_agua_no_se_dibuja(self, hud) -> None:
        lienzo = _lienzo()
        hud.draw(lienzo)
        rect = hud._oxigeno_bar_rect
        antes = pygame.image.tobytes(lienzo.subsurface(rect), "RGB")
        hud.set_oxigeno(-1.0, False)
        hud.draw(lienzo)
        despues = pygame.image.tobytes(lienzo.subsurface(rect), "RGB")
        assert despues == antes, (
            "la barra de oxígeno se dibujó en un nivel sin agua"
        )

    def test_con_agua_se_dibuja_sobre_la_estamina(self, hud) -> None:
        hud.set_oxigeno(0.5, False)
        lienzo = _lienzo()
        hud.draw(lienzo)
        rect = hud._oxigeno_bar_rect
        x = rect.x + rect.width // 2
        y = rect.y + rect.height // 2
        pixel = lienzo.get_at((x, y))[:3]
        assert pixel != (0, 0, 0), "el centro de la barra de oxígeno quedó vacío"
        assert rect.y > hud._estamina_bar_rect.y, (
            "la barra de oxígeno no quedó debajo de la de estamina"
        )

    def test_el_aviso_parpadea_y_pulsa_su_sonido(self, hud) -> None:
        pulsos = []

        def _al_pulso(**_k):
            pulsos.append(1)

        hud._event_bus.subscribe(Events.SFX_TIMER_ALERT_PULSE, _al_pulso)
        hud.set_oxigeno(0.05, True)  # quedan ~1,5 s: aviso pleno
        for _ in range(120):  # 2 s
            hud.update(1 / 60)
            hud._event_bus.dispatch()
        assert len(pulsos) >= 2, (
            f"el aviso bajo no pulsó su sonido (pulsos: {len(pulsos)})"
        )
        lienzo = _lienzo()
        hud.draw(lienzo)
        rect = hud._oxigeno_bar_rect
        x = rect.x + rect.width // 2
        y = rect.y + rect.height // 2
        assert lienzo.get_at((x, y))[:3] != (0, 0, 0), (
            "la barra nunca quedó visible: el parpadeo la borró para siempre"
        )

    def test_sin_aviso_no_hay_pulso(self, hud) -> None:
        pulsos = []

        def _al_pulso(**_k):
            pulsos.append(1)

        hud._event_bus.subscribe(Events.SFX_TIMER_ALERT_PULSE, _al_pulso)
        hud.set_oxigeno(0.8, False)
        for _ in range(120):
            hud.update(1 / 60)
            hud._event_bus.dispatch()
        assert pulsos == [], (
            "el pulso sonó con el aire en verde — el aviso tiene que ser "
            "del tramo bajo, no un ruido constante"
        )


class TestLaEscenaAlimentaElHud:
    def test_el_hud_ensena_el_aire_al_bucear(self, _video) -> None:
        from tests.test_stage4_1b import _construir_escena

        escena = _construir_escena()
        try:
            hud = escena._hud
            assert hud._oxigeno_ratio < 0.0, (
                "el jugador nace a flote: la barra no debería verse"
            )
            escena._player.position.x = 600.0
            escena._player.position.y = 320.0  # sumergido
            escena.update(1 / 60)
            assert 0.0 <= hud._oxigeno_ratio <= 1.0, (
                "sumergido, el HUD no recibió el ratio del aire"
            )
            # A la superficie de verdad: el andén seco del patio (S3).
            escena._player.position.x = 350.0 * 16
            escena._player.position.y = 60.0
            for _ in range(60):
                escena.update(1 / 60)
            assert hud._oxigeno_ratio < 0.0, (
                "fuera del agua, la barra de oxígeno sigue visible"
            )
        finally:
            escena.on_exit()