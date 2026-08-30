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

from src.engine.ui.theme import font

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
        h._portrait_frame_rect = _rect_escalado(MARGEN, MARGEN, 24, 24)
        h._portrait_sprite_rect = _rect_escalado(MARGEN + 1, MARGEN + 1, 22, 22)
        # barras apiladas bajo retrato
        from src.engine.ui.hud import _e
        ancho = h._portrait_frame_rect.width
        x = h._portrait_frame_rect.x
        y_barras = h._portrait_frame_rect.bottom + _e(2)
        alto = _e(5)
        paso = alto + _e(1)
        h._y_barras_bloque = y_barras
        h._paso_barra_bloque = paso
        h._vida_bar_rect = pygame.Rect(x, y_barras, ancho, alto)
        h._estamina_bar_rect = pygame.Rect(x, y_barras + paso, ancho, alto)
        h._carga_bar_rect = pygame.Rect(x, y_barras + paso * 2, ancho, alto)
        h._oxigeno_bar_rect = pygame.Rect(x, y_barras + paso * 3, ancho, alto)
        h._score_region = _rect_escalado(MARGEN + 30, MARGEN, 92, 24)
        h._timer_bg_rect = _rect_escalado(134, MARGEN, 52, 16)
        h._timer_icon_rect = _rect_escalado(137, MARGEN + 1, 12, 12)
        h._timer_rect = _rect_escalado(151, MARGEN, 34, 14)
        return self

    def build_assets(self) -> HUDBuilder:
        from src.engine.core import settings as _s
        from src.engine.ui.hud import _recortar_circular
        from src.engine.utils.asset_loader import AssetLoader

        h = self.hud
        h._portraits = {}
        for state in ("normal", "hurt", "critical", "dead"):
            path = _s.ASSETS_DIR / "ui" / f"portrait_{state}.png"
            try:
                destino = h._portrait_sprite_rect.size
                surf = AssetLoader.load_image(path, size=destino)
                h._portraits[state] = _recortar_circular(surf)
            except Exception:
                logger.warning("hud: failed to load portrait %s", state)
        h._font = font(12)  # escalado vía theme.font, placeholder
        return self

    def build(self) -> HUD:
        return self.hud
