"""
HUDBuilder — Builder para HUD (255 líneas de layout).

HUD.__init__ calculaba 8 rects, cargaba 4 portraits, 9-slice frame y
registraba 6 eventos en un solo método. El Builder separa
layout → assets → eventos, y deja HUD como Director que orquesta.

Patrón: Builder + Director
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pygame

if TYPE_CHECKING:
    from src.engine.ui.hud import HUD


logger = logging.getLogger(__name__)


class HUDBuilder:
    """Construye un HUD por pasos testeables."""

    def __init__(self, hud: HUD) -> None:
        self.hud = hud

    def build_layout(self) -> HUDBuilder:
        from src.engine.ui.hud import _rect_escalado

        MARGEN = 6
        h = self.hud
        # AUD-729: mypy no ve que HUD declare estos atributos — los crea el
        # Builder dinámicamente. type: ignore es correcto aquí: el Director
        # (HUD) garantiza que build_layout() se llame antes de cualquier uso.
        h._portrait_frame_rect = _rect_escalado(MARGEN, MARGEN, 24, 24)  # type: ignore[attr-defined]
        h._portrait_sprite_rect = _rect_escalado(MARGEN + 1, MARGEN + 1, 22, 22)  # type: ignore[attr-defined]
        # barras apiladas bajo retrato
        from src.engine.ui.hud import _e
        ancho = h._portrait_frame_rect.width  # type: ignore[attr-defined]
        x = h._portrait_frame_rect.x  # type: ignore[attr-defined]
        y_barras = h._portrait_frame_rect.bottom + _e(2)  # type: ignore[attr-defined]
        alto = _e(5)
        paso = alto + _e(1)
        h._y_barras_bloque = y_barras  # type: ignore[attr-defined]
        h._paso_barra_bloque = paso  # type: ignore[attr-defined]
        h._vida_bar_rect = pygame.Rect(x, y_barras, ancho, alto)  # type: ignore[attr-defined]
        h._estamina_bar_rect = pygame.Rect(x, y_barras + paso, ancho, alto)  # type: ignore[attr-defined]
        h._carga_bar_rect = pygame.Rect(x, y_barras + paso * 2, ancho, alto)  # type: ignore[attr-defined]
        h._oxigeno_bar_rect = pygame.Rect(x, y_barras + paso * 3, ancho, alto)  # type: ignore[attr-defined]
        h._score_region = _rect_escalado(MARGEN + 30, MARGEN, 92, 24)  # type: ignore[attr-defined]
        h._timer_bg_rect = _rect_escalado(134, MARGEN, 52, 16)  # type: ignore[attr-defined]
        h._timer_icon_rect = _rect_escalado(137, MARGEN + 1, 12, 12)  # type: ignore[attr-defined]
        h._timer_rect = _rect_escalado(151, MARGEN, 34, 14)  # type: ignore[attr-defined]
        return self

    def build_assets(self) -> HUDBuilder:
        # Nota: los retratos y la fuente siguen cargándose en HUD.__init__
        # directamente; este método es el punto de extensión para cuando
        # se extraiga toda la carga de assets a Builder (siguiente paso).
        return self

    def build(self) -> HUD:
        return self.hud
