"""AUD-827 — la rejilla de sombras se reconstruía por foco y por fotograma.

Medido con Stage0 real a 1280x720: `render_map` construye en la rama half-res
una lista `obs_h` nueva en cada foco y cada fotograma, y como
`ProyectorDeSombras` invalida su índice por identidad de lista, la
`RejillaEspacial` se reconstruía ~4,5 veces por fotograma con decenas de miles
de llamadas a `_celdas_de`. La geometría no cambia entre fotogramas: la lista
escalada se puede cachear e invalidar en `set_obstaculos`.
"""
from __future__ import annotations

import pygame
import pytest


@pytest.fixture(autouse=True)
def _video():
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((800, 600))


def test_la_rejilla_no_se_reconstruye_por_fotograma() -> None:
    from src.framework.stage import rejilla as rejilla_mod
    from src.framework.vfx.lighting import LightSource, LightSystem

    construidas = {"n": 0}
    original = rejilla_mod.RejillaEspacial.__init__

    def espiar(self, rects, lado=rejilla_mod.LADO_DE_CELDA) -> None:
        construidas["n"] += 1
        original(self, rects, lado)

    rejilla_mod.RejillaEspacial.__init__ = espiar  # type: ignore[method-assign]
    try:
        sistema = LightSystem()
        sistema.set_obstaculos([pygame.Rect(x, 500, 32, 32) for x in range(0, 1280, 64)])
        sistema.add_light(LightSource(
            pygame.Vector2(640, 300), radius=200.0, flicker=True,
        ))
        for _ in range(8):
            sistema.render_map((1280, 720), pygame.Vector2(0, 0))
    finally:
        rejilla_mod.RejillaEspacial.__init__ = original  # type: ignore[method-assign]
    assert construidas["n"] <= 1, (
        f"la rejilla se construyó {construidas['n']} veces en 8 fotogramas "
        "con la misma geometría"
    )


def test_cambiar_la_geometria_invalida_la_cache() -> None:
    from src.framework.stage import rejilla as rejilla_mod
    from src.framework.vfx.lighting import LightSource, LightSystem

    construidas = {"n": 0}
    original = rejilla_mod.RejillaEspacial.__init__

    def espiar(self, rects, lado=rejilla_mod.LADO_DE_CELDA) -> None:
        construidas["n"] += 1
        original(self, rects, lado)

    rejilla_mod.RejillaEspacial.__init__ = espiar  # type: ignore[method-assign]
    try:
        sistema = LightSystem()
        sistema.set_obstaculos([pygame.Rect(0, 500, 32, 32)])
        sistema.add_light(LightSource(
            pygame.Vector2(640, 300), radius=200.0, flicker=True,
        ))
        sistema.render_map((1280, 720), pygame.Vector2(0, 0))
        # Geometría nueva: la sombra debe recalcularse, no reusar la vieja.
        sistema.set_obstaculos([pygame.Rect(600, 500, 32, 32)])
        sistema.render_map((1280, 720), pygame.Vector2(0, 0))
    finally:
        rejilla_mod.RejillaEspacial.__init__ = original  # type: ignore[method-assign]
    assert construidas["n"] == 2, (
        f"se esperaban 2 construcciones (una por geometría), hubo {construidas['n']}"
    )
