"""AUD-826 — la pausa de los stages, dimensionada y con panel.

El reporte hablaba de "menús pegados en todos los stages". La causa es la
pausa global (`DrawingSystem._draw_pause_panel`): tira de pestañas de 20 px
pegada a `(0, 0)` con texto en `y=1`, y lista "Menú" sin panel con paso 30
fijo y fuente fija de 20. Al ser código compartido, el síntoma sale igual en
los 26 stages sin que ningún stage tenga menú propio.
"""
from __future__ import annotations

import pygame
import pytest

from src.engine.core import settings
from src.framework.stage.drawing_system import DrawContext, DrawingSystem


@pytest.fixture(scope="module")
def display():
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((800, 600))
    yield pygame.display.get_surface()


def _lienzo_de_pausa(display) -> pygame.Surface:
    sistema = DrawingSystem()
    lienzo = pygame.Surface((settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT))
    ctx = DrawContext(
        surface=lienzo,
        pausa_tabs=("Menú", "Equipo", "Habilidades", "Mapa"),
        pausa_tab_index=0,
        pausa_pestana_activa=None,
        pausa_menu_opciones=("Continuar", "Guardar", "Salir"),
        pausa_menu_seleccion=0,
    )
    sistema._draw_pause_panel(lienzo, ctx)
    return lienzo


def test_la_tira_de_pestanas_no_mide_20_px(display) -> None:
    """La franja era de 20 px fijos (2,7 % de 720): ilegible y pegada."""
    lienzo = _lienzo_de_pausa(display)
    franja = (10, 10, 16)
    # A y=30 la franja antigua ya había terminado (fondo BG debajo).
    assert lienzo.get_at((settings.INTERNAL_WIDTH // 2, 30))[:3] == franja, (
        "la tira de pestañas sigue midiendo 20 px"
    )


def test_la_lista_de_pausa_vive_en_un_panel(display) -> None:
    """La lista se dibujaba cruda sobre el fondo, sin panel ni relieve."""
    from src.engine.ui.theme import Theme

    lienzo = _lienzo_de_pausa(display)
    panel = Theme.SURFACE[:3]
    relieve = Theme.SURFACE_RAISED[:3]
    pixeles = pygame.surfarray.array3d(lienzo)
    hay_panel = ((pixeles[:, :, 0] == panel[0])
                 & (pixeles[:, :, 1] == panel[1])
                 & (pixeles[:, :, 2] == panel[2])).any()
    hay_relieve = ((pixeles[:, :, 0] == relieve[0])
                   & (pixeles[:, :, 1] == relieve[1])
                   & (pixeles[:, :, 2] == relieve[2])).any()
    assert hay_panel and hay_relieve, (
        "la pestaña Menú no dibuja panel ni resalta la fila elegida"
    )
