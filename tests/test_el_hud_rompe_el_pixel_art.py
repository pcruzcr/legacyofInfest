"""AUD-527 — decisión del dueño (2026-08-17): modernizar el HUD de verdad,
rompiendo la convención SNES que `docs/09_HUD_SPEC.md` §1 mandaba hasta
aquí ("sin antialiasing, sin degradados, sin sombras mezcladas por alfa").

Estas pruebas no comprueban gusto — comprueban que la técnica cambió de
verdad: un relleno plano con un borde de 1 px tiene dos o tres colores
únicos y esquinas cuadradas; un degradado antialiased tiene decenas, y un
relleno con `border_radius` deja transparente el píxel exacto de la
esquina. Si alguien vuelve a un `pygame.draw.rect` plano por error, estas
pruebas lo notan.
"""
from __future__ import annotations

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

from pathlib import Path

import pygame
import pytest

from src.engine.core import settings


@pytest.fixture(scope="module", autouse=True)
def _video() -> None:
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((320, 224))


def _colores_unicos(surf: pygame.Surface) -> set[tuple[int, int, int, int]]:
    colores = set()
    for x in range(surf.get_width()):
        for y in range(surf.get_height()):
            colores.add(tuple(surf.get_at((x, y))))
    return colores


class TestElPanelDelHudLlevaDegradadoYHalo:
    def test_hud_frame_no_es_un_solo_color_plano(self) -> None:
        ruta = Path(settings.ASSETS_DIR) / "ui" / "hud_frame.png"
        surf = pygame.image.load(str(ruta)).convert_alpha()
        opacos = {c for c in _colores_unicos(surf) if c[3] > 200}
        assert len(opacos) > 10, (
            f"hud_frame.png tiene sólo {len(opacos)} colores casi opacos: "
            f"sigue siendo el relleno plano de antes"
        )


class TestLasBarrasSonRedondeadasConDegradado:
    def _barra(self):
        from src.engine.ui.hud import _dibujar_barra_moderna

        surf = pygame.Surface((100, 40), pygame.SRCALPHA)
        rect = pygame.Rect(10, 10, 80, 20)
        _dibujar_barra_moderna(surf, rect, 0.75, (20, 20, 200), (255, 220, 60))
        return surf, rect

    def test_la_esquina_exacta_del_rect_queda_transparente(self) -> None:
        """`border_radius` recorta la esquina — un `pygame.draw.rect` plano
        pinta hasta el último píxel del rectángulo, esquinas incluidas."""
        surf, rect = self._barra()
        esquina = surf.get_at((rect.left, rect.top))
        assert esquina[3] == 0, (
            f"la esquina superior-izquierda del rect no es transparente "
            f"({tuple(esquina)}): la barra sigue teniendo esquinas cuadradas"
        )

    def test_el_relleno_tiene_degradado_no_un_color_plano(self) -> None:
        surf, rect = self._barra()
        y_medio = rect.centery
        colores = {
            tuple(surf.get_at((x, y_medio)))
            for x in range(rect.left + 3, rect.left + int(rect.width * 0.7))
        }
        opacos = {c for c in colores if c[3] > 200}
        assert len(opacos) > 5, (
            f"el relleno de la barra tiene sólo {len(opacos)} colores a lo "
            f"ancho: sigue siendo un color plano, no un degradado"
        )


class TestElValidadorMideElHudModernoPorPresupuesto:
    """AUD-527 — `hud_frame.png` dejó de ser arte indexado (paleta fija) y
    pasó a ser pintado (degradado + antialiasing), el mismo caso que ya
    cubrían los tilesets. Sin este cambio, `scripts/validate_assets.py`
    lo marcaba como roto por tener más colores de los que su antigua
    paleta fija permitía — no porque el arte estuviera mal, sino porque
    la regla que lo describía quedó desactualizada (el mismo defecto de
    fondo que AUD-011 documenta).

    AUD-535 retiró `heart_*.png`: la vida dejó de ser sprites de corazón
    y pasó a ser una barra dibujada (`HUD._draw_barra_de_vida`), así que
    no queda arte de corazón que este validador deba medir — las pruebas
    que lo comprobaban se retiraron con el propio archivo.
    """

    def test_hud_frame_esta_en_el_presupuesto_de_color(self) -> None:
        import fnmatch

        import scripts.validate_assets as va

        assert any(
            fnmatch.fnmatch("ui/hud_frame.png", patron)
            for patron, _ in va.COLOR_BUDGETS
        ), "hud_frame.png no tiene presupuesto de color declarado"

    def test_los_retratos_siguen_siendo_paleta_estricta(self) -> None:
        """Lo que no se modernizó no debe colarse en el presupuesto libre:
        seguir midiéndolo por paleta fija es lo que detecta un color fuera
        de sitio en arte que sí debería seguir siendo indexado."""
        import fnmatch

        import scripts.validate_assets as va

        assert any(
            fnmatch.fnmatch("ui/portrait_normal.png", patron)
            for patron, _ in va.SPRITE_PALETTES
        ), "portrait_normal.png se salió de la validación de paleta estricta"


class TestLaEspecificacionRegistraElCambio:
    def test_el_documento_ya_no_manda_la_convencion_snes_como_regla_activa(self) -> None:
        """Invariante 6 de CLAUDE.md: los números y afirmaciones del doc son
        verificables — si el código ya no dibuja así, el doc no puede seguir
        diciendo que sí, ni siquiera como historia sin marcarla como tal."""
        raiz = Path(__file__).resolve().parent.parent
        spec = (raiz / "docs/09_HUD_SPEC.md").read_text(encoding="utf-8")
        assert "AUD-527" in spec, (
            "la spec no registra la reversión de la convención SNES"
        )
