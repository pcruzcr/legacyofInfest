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
        from src.engine.core import settings

        h = self.hud
        # HD nativo 1920×1080 1:1 — sin escalado. Izquierda retrato 128, centro 800, derecha minimapa 280
        if settings.INTERNAL_WIDTH == 1920 and settings.INTERNAL_HEIGHT == 1080:
            MARGEN = 32
            h._portrait_frame_rect = pygame.Rect(MARGEN, MARGEN, 128, 128)  # type: ignore[attr-defined]
            h._portrait_sprite_rect = pygame.Rect(MARGEN + 6, MARGEN + 6, 116, 116)  # type: ignore[attr-defined]
            ancho = 128
            x = MARGEN
            y_barras = h._portrait_frame_rect.bottom + 18
            alto = 20
            paso = 30
            h._y_barras_bloque = y_barras
            h._paso_barra_bloque = paso
            h._vida_bar_rect = pygame.Rect(x, y_barras, ancho, alto)
            h._estamina_bar_rect = pygame.Rect(x, y_barras + paso, ancho, alto)
            h._mana_bar_rect = pygame.Rect(x, y_barras + paso * 2, ancho, alto)
            h._carga_bar_rect = pygame.Rect(x, y_barras + paso * 3, ancho, alto)
            h._oxigeno_bar_rect = pygame.Rect(x, y_barras + paso * 4, ancho, alto)
            cx = settings.INTERNAL_WIDTH // 2
            h._score_region = pygame.Rect(cx - 400, MARGEN, 800, 80)
            h._timer_bg_rect = pygame.Rect(cx - 380, MARGEN + 14, 220, 56)
            h._timer_icon_rect = pygame.Rect(cx - 370, MARGEN + 24, 36, 36)
            h._timer_rect = pygame.Rect(cx - 328, MARGEN + 24, 180, 36)
            return self
        if settings.INTERNAL_WIDTH == 1280 and settings.INTERNAL_HEIGHT == 720:
            MARGEN = 24
            h._portrait_frame_rect = pygame.Rect(MARGEN, MARGEN, 96, 96)  # type: ignore[attr-defined]
            h._portrait_sprite_rect = pygame.Rect(MARGEN + 4, MARGEN + 4, 88, 88)  # type: ignore[attr-defined]
            ancho = 96
            x = MARGEN
            y_barras = h._portrait_frame_rect.bottom + 14  # type: ignore[attr-defined]
            alto = 16
            paso = 24
            h._y_barras_bloque = y_barras  # type: ignore[attr-defined]
            h._paso_barra_bloque = paso  # type: ignore[attr-defined]
            h._vida_bar_rect = pygame.Rect(x, y_barras, ancho, alto)  # type: ignore[attr-defined]
            h._estamina_bar_rect = pygame.Rect(x, y_barras + paso, ancho, alto)  # type: ignore[attr-defined]
            h._mana_bar_rect = pygame.Rect(x, y_barras + paso * 2, ancho, alto)  # type: ignore[attr-defined]
            h._carga_bar_rect = pygame.Rect(x, y_barras + paso * 3, ancho, alto)  # type: ignore[attr-defined]
            h._oxigeno_bar_rect = pygame.Rect(x, y_barras + paso * 4, ancho, alto)  # type: ignore[attr-defined]
            cx = settings.INTERNAL_WIDTH // 2
            h._score_region = pygame.Rect(cx - 280, MARGEN, 560, 64)  # type: ignore[attr-defined]
            h._timer_bg_rect = pygame.Rect(cx - 260, MARGEN + 10, 160, 44)  # type: ignore[attr-defined]
            h._timer_icon_rect = pygame.Rect(cx - 252, MARGEN + 18, 28, 28)  # type: ignore[attr-defined]
            h._timer_rect = pygame.Rect(cx - 218, MARGEN + 18, 120, 28)  # type: ignore[attr-defined]
            return self
        # Fallback 800×600 y otros: escalado clásico 320→
        from src.engine.ui.hud import _rect_escalado

        MARGEN = 6
        h._portrait_frame_rect = _rect_escalado(MARGEN, MARGEN, 24, 24)  # type: ignore[attr-defined]
        h._portrait_sprite_rect = _rect_escalado(MARGEN + 1, MARGEN + 1, 22, 22)  # type: ignore[attr-defined]
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
        h._mana_bar_rect = pygame.Rect(x, y_barras + paso * 2, ancho, alto)  # type: ignore[attr-defined]
        h._carga_bar_rect = pygame.Rect(x, y_barras + paso * 3, ancho, alto)  # type: ignore[attr-defined]
        h._oxigeno_bar_rect = pygame.Rect(x, y_barras + paso * 4, ancho, alto)  # type: ignore[attr-defined]
        h._score_region = _rect_escalado(MARGEN + 30, MARGEN, 92, 24)  # type: ignore[attr-defined]
        h._timer_bg_rect = _rect_escalado(134, MARGEN, 52, 16)  # type: ignore[attr-defined]
        h._timer_icon_rect = _rect_escalado(137, MARGEN + 1, 12, 12)  # type: ignore[attr-defined]
        h._timer_rect = _rect_escalado(151, MARGEN, 34, 14)  # type: ignore[attr-defined]
        return self

    def build_assets(self) -> HUDBuilder:
        h = self.hud
        from src.engine.core import settings
        from src.engine.ui.hud import _e, _recortar_circular
        from src.engine.ui.theme import font
        from src.engine.utils.asset_loader import AssetLoader

        # 9-slice frame
        h._timer_fill = None  # type: ignore[attr-defined]
        h._timer_edges = {}  # type: ignore[attr-defined]
        try:
            raw_frame = AssetLoader.load_image(settings.ASSETS_DIR / "ui" / "hud_frame.png")
            fw, fh = raw_frame.get_size()
            if fw >= 6 and fh >= 6:
                c = 2
                esquinas = {
                    "tl": raw_frame.subsurface((0, 0, c, c)),
                    "tr": raw_frame.subsurface((fw - c, 0, c, c)),
                    "bl": raw_frame.subsurface((0, fh - c, c, c)),
                    "br": raw_frame.subsurface((fw - c, fh - c, c, c)),
                }
                src_edges = {
                    "top": raw_frame.subsurface((c, 0, fw - 2 * c, c)),
                    "bottom": raw_frame.subsurface((c, fh - c, fw - 2 * c, c)),
                    "left": raw_frame.subsurface((0, c, c, fh - 2 * c)),
                    "right": raw_frame.subsurface((fw - c, c, c, fh - 2 * c)),
                }
                ce = _e(c)
                h._frame_corners = {k: pygame.transform.scale(v, (ce, ce)) for k, v in esquinas.items()}  # type: ignore[attr-defined]
                h._frame_edges = src_edges  # type: ignore[attr-defined]
                src_fill = raw_frame.subsurface((c, c, fw - 2 * c, fh - 2 * c))
                h._frame_fill = src_fill  # type: ignore[attr-defined]
            else:
                h._frame_corners = {}  # type: ignore[attr-defined]
                h._frame_edges = {}  # type: ignore[attr-defined]
                h._frame_fill = None  # type: ignore[attr-defined]
        except Exception:
            logger.warning("hud: failed to load hud_frame.png")
            h._frame_corners = {}  # type: ignore[attr-defined]
            h._frame_edges = {}  # type: ignore[attr-defined]
            h._frame_fill = None  # type: ignore[attr-defined]
        # timer fill pre-scale
        try:
            h._timer_fill = pygame.transform.scale(
                h._frame_fill, (h._timer_bg_rect.width, h._timer_bg_rect.height)  # type: ignore[attr-defined]
            ) if isinstance(h._frame_fill, pygame.Surface) else None  # type: ignore[attr-defined]
        except Exception:
            h._timer_fill = None  # type: ignore[attr-defined]
        if getattr(h, "_frame_edges", None):
            tr = h._timer_bg_rect  # type: ignore[attr-defined]
            ce = _e(2)
            try:
                h._timer_edges = {  # type: ignore[attr-defined]
                    "top": pygame.transform.scale(h._frame_edges["top"], (tr.width - 2 * ce, ce)),
                    "bottom": pygame.transform.scale(h._frame_edges["bottom"], (tr.width - 2 * ce, ce)),
                    "left": pygame.transform.scale(h._frame_edges["left"], (ce, tr.height - 2 * ce)),
                    "right": pygame.transform.scale(h._frame_edges["right"], (ce, tr.height - 2 * ce)),
                }
            except Exception:
                h._timer_edges = {}  # type: ignore[attr-defined]
        # portraits
        h._portraits = {}  # type: ignore[attr-defined]
        for state in ("normal", "hurt", "critical", "dead"):
            path = settings.ASSETS_DIR / "ui" / f"portrait_{state}.png"
            try:
                destino = h._portrait_sprite_rect.size  # type: ignore[attr-defined]
                surf = AssetLoader.load_image(path, size=destino)
                h._portraits[state] = _recortar_circular(surf)  # type: ignore[attr-defined]
            except Exception:
                logger.warning("hud: failed to load portrait %s", state)
        h._font = font(_e(12))  # type: ignore[attr-defined]
        h._timer_digit_font = font(_e(12))  # type: ignore[attr-defined]
        return self

    def build(self) -> HUD:
        return self.hud
