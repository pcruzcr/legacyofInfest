"""
Module: test_el_zoom_llega_al_mundo
System: tests
Description: AUD-825 (P18) — el zoom cinematográfico se compone en
`dibujar_mundo` (camino software), no sólo en `draw`. El camino software
de `App` llama a `dibujar_mundo` + `dibujar_ui` directamente: con el zoom
sólo en `draw`, las `CameraZoomZone` no se veían en producción.
"""
from __future__ import annotations

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame
import pytest

from src.engine.core import settings


@pytest.fixture(scope="module")
def display():
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT))
    yield
    pygame.quit()


@pytest.fixture
def escena(display):
    from src.engine.audio.audio_manager import AudioManager
    from src.engine.core.event_bus import EventBus
    from src.engine.core.game_context import GameContext
    from src.engine.core.save_manager import SaveManager
    from src.engine.input.input_manager import InputManager
    from src.engine.scene.scene_manager import SceneManager
    from src.framework.entities import entity_factory
    from src.stages.stage0.stage0 import Stage0

    entity_factory.ensure_registered()
    ctx = GameContext(
        input_manager=InputManager(), audio_manager=AudioManager(),
        scene_manager=None, event_bus=EventBus(), clock=None,
        save_manager=SaveManager(),
    )
    ctx.scene_manager = SceneManager(ctx)
    s = Stage0(ctx)
    s.awake()
    s.start()
    s.on_enter()
    assert not getattr(ctx, "usar_gl", False), (
        "este test cubre la composición software; la ruta GL no corre sin GPU"
    )
    return s


def _fotogramas_diferentes(a: pygame.Surface, b: pygame.Surface) -> int:
    wa, ha = a.get_size()
    return sum(
        1
        for x in range(0, wa, 2)
        for y in range(0, ha, 2)
        if tuple(a.get_at((x, y)))[:3] != tuple(b.get_at((x, y)))[:3]
    )


class TestElZoomLlegaAlMundo:
    def test_dibujar_mundo_con_zoom_difiere_de_sin_zoom(
        self, escena,
    ) -> None:
        """P18 — `dibujar_mundo` con zoom 1.5 debe componer distinto que con
        1.0. Antes el zoom sólo vivía en `draw` y esta comparación daba 0."""
        w, h = settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT
        escena._camera.fijar_zoom(1.0)
        base = pygame.Surface((w, h))
        escena.dibujar_mundo(base)
        escena._camera.fijar_zoom(1.5)
        acercado = pygame.Surface((w, h))
        escena.dibujar_mundo(acercado)
        distintos = _fotogramas_diferentes(base, acercado)
        # Muestreo 1:2 → ~230k píxeles; el zoom mueve casi todo el cuadro
        # (medido ~867k/921k por `draw`); el flicker de focos son miles.
        assert distintos > 25_000, (
            f"sólo {distintos} px difieren entre zoom 1.0 y 1.5: "
            "el zoom no llega a `dibujar_mundo` (P18)"
        )
