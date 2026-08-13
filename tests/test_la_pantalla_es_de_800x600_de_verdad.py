"""AUD-460 — la ventana promete 800×600 y no la medía.

`pygame.SCALED` delegaba en SDL el tamaño y el escalado del marco, y cada
plataforma lo interpreta a su manera: en unas la ventana se agrandaba para
llenar el escritorio, en otras se quedaba como está. El resultado es que la
pantalla no medía lo que `settings` prometía ni lo que `LOI_DISPLAY_SCALE`
anuncia: un defecto que cambia de aspecto según la máquina.

Aquí se exige lo inverso: la ventana se crea al tamaño **real**
(interior × `DISPLAY_SCALE`, sin SCALED) y el blit de publicación escala el
fotograma interno manualmente. Con `DISPLAY_SCALE=1` la ventana es 800×600
exactos; con `2`, 1600×1200, y ambas medidas se comprueban.
"""
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame
import pytest

from src.engine.core import settings


@pytest.fixture(scope="module")
def _video():
    pygame.init()
    yield


def _app_minimo():
    from src.engine.core.app import App

    return object.__new__(App)


class TestLaVentanaMideLoQuePromete:
    def test_la_ventana_software_mide_800x600(self, _video) -> None:
        app = _app_minimo()
        app._abrir_ventana_software()
        assert pygame.display.get_surface().get_size() == (
            settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT,
        ), (
            "la ventana no mide la resolución interna: SDL la está "
            "agrandando o encogiendo por su cuenta"
        )

    def test_display_scale_agranda_la_ventana_de_verdad(self, _video, monkeypatch) -> None:
        monkeypatch.setattr(settings, "DISPLAY_SCALE", 2)
        app = _app_minimo()
        app._abrir_ventana_software()
        assert pygame.display.get_surface().get_size() == (
            settings.INTERNAL_WIDTH * 2, settings.INTERNAL_HEIGHT * 2,
        ), (
            "LOI_DISPLAY_SCALE no cambia el tamaño de la ventana: la "
            "configuración existe pero no se muestra"
        )

    def test_no_se_delega_en_scaled(self) -> None:
        """`pygame.SCALED` es la fuente de la indeterminación: fuera."""
        from pathlib import Path

        fuente = (
            Path(__file__).resolve().parent.parent
            / "src/engine/core/app.py"
        ).read_text(encoding="utf-8")
        assert "pygame.SCALED" not in fuente, (
            "la ventana software vuelve a escalarse por SDL"
        )


class TestElPublicadoEscalaAlTamanoReal:
    def test_el_blit_llena_la_ventana(self, _video) -> None:
        from src.engine.core.app import _publicar_software

        origen = pygame.Surface((settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT))
        origen.fill((5, 5, 5))
        origen.set_at((origen.get_width() - 1, origen.get_height() - 1), (255, 0, 0))
        destino = pygame.Surface((settings.INTERNAL_WIDTH * 2, settings.INTERNAL_HEIGHT * 2))
        _publicar_software(origen, destino)
        assert destino.get_at((destino.get_width() - 2, destino.get_height() - 2))[:3] == (
            255, 0, 0,
        ), (
            "el fotograma no llega a la esquina de la ventana agrandada: "
            "quedaría recortado"
        )

    def test_a_misma_resolucion_no_se_escala(self, _video) -> None:
        from src.engine.core.app import _publicar_software

        origen = pygame.Surface((settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT))
        origen.fill((5, 5, 5))
        origen.set_at((origen.get_width() - 1, origen.get_height() - 1), (255, 0, 0))
        destino = pygame.Surface((settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT))
        _publicar_software(origen, destino)
        assert destino.get_at((destino.get_width() - 1, destino.get_height() - 1))[:3] == (
            255, 0, 0,
        )