"""AUD-453 — media interfaz seguía maquetada para la pantalla de 320×224.

AUD-451 encontró el problema en el HUD y lo arregló ahí. Pero la resolución
vieja había dejado más huellas, y todas del mismo tipo: números escritos para
una pantalla de 320 de ancho y 224 de alto, dibujados sin escalar sobre una de
800×600.

Medido antes de tocar nada:

* el cuadro de mensajes medía **28 px de alto** —el 12 % de la pantalla de
  diseño, el 4,7 % de la real— y se dibujaba en y=64;
* la franja del título de escenario, 40 px de alto en y=88;
* los subtítulos, anclados a 150 px del borde inferior con 18 px entre líneas.

Los tres son texto que se lee jugando, y los tres salían a menos de la mitad
del tamaño que les corresponde.

Dónde vive la escala
--------------------
En `theme`, no en `hud`. Es el módulo de los tokens de diseño —de donde ya
salen los colores, los espaciados y la escala tipográfica— y la relación entre
la maqueta original y la pantalla real es exactamente eso: un token. Tenerla
en `hud.py` obligaba a los otros tres a importar del HUD para colocarse, que
es una dependencia que no significa nada.
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
def _video():
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT))
    yield


class TestLaEscalaEsUnTokenDelTema:
    def test_el_tema_la_publica(self) -> None:
        from src.engine.ui import theme

        assert hasattr(theme, "ESCALA_DE_INTERFAZ")
        assert hasattr(theme, "escalar")

    def test_sale_de_la_resolucion_y_no_de_un_numero(self) -> None:
        from src.engine.ui.theme import ANCHO_DE_DISENO, ESCALA_DE_INTERFAZ

        assert ESCALA_DE_INTERFAZ == pytest.approx(
            settings.INTERNAL_WIDTH / ANCHO_DE_DISENO)

    def test_a_800_agranda(self) -> None:
        from src.engine.ui.theme import ESCALA_DE_INTERFAZ

        assert ESCALA_DE_INTERFAZ > 1.0

    def test_el_hud_usa_la_del_tema(self) -> None:
        """Una segunda escala sería una segunda verdad."""
        from src.engine.ui import hud, theme

        assert hud.ESCALA_DEL_HUD == theme.ESCALA_DE_INTERFAZ


class TestElCuadroDeMensajes:
    def test_ocupa_lo_que_le_toca(self, _video) -> None:
        from src.engine.core.event_bus import EventBus
        from src.engine.ui.message_box import MessageBox

        caja = MessageBox(EventBus())
        r = caja.caja_rect()
        assert r.height >= settings.INTERNAL_HEIGHT * 0.08, (
            f"el cuadro de mensajes mide {r.height} px de alto en una pantalla "
            f"de {settings.INTERNAL_HEIGHT}: sigue a escala de 320×224"
        )
        assert r.width == settings.INTERNAL_WIDTH

    def test_no_se_sale(self, _video) -> None:
        from src.engine.core.event_bus import EventBus
        from src.engine.ui.message_box import MessageBox

        r = MessageBox(EventBus()).caja_rect()
        assert r.bottom <= settings.INTERNAL_HEIGHT
        assert r.top >= 0


class TestLaFranjaDelEscenario:
    def test_ocupa_lo_que_le_toca(self, _video) -> None:
        from src.engine.ui.screen_banner import ScreenBanner

        banner = ScreenBanner()
        assert banner.alto >= settings.INTERNAL_HEIGHT * 0.12, (
            f"la franja mide {banner.alto} px de alto: sigue a escala de 320"
        )

    def test_esta_centrada_y_dentro(self, _video) -> None:
        from src.engine.ui.screen_banner import ScreenBanner

        banner = ScreenBanner()
        assert banner.y_superior > 0
        assert banner.y_superior + banner.alto <= settings.INTERNAL_HEIGHT

    def test_la_costura_no_tacha_el_nombre(self, _video) -> None:
        """AUD-526: `banner_top.png` y `banner_bottom.png` se generaban como
        un rectángulo cerrado cada una (borde en las cuatro caras). Pegadas
        sin hueco (`ScreenBanner.draw`), el borde inferior de arriba y el
        borde superior de abajo caían en la misma fila de píxeles — una
        línea doble justo donde se centra el nombre del escenario, que se
        leía como texto tachado. Cada mitad dibuja ahora sólo sus tres lados
        exteriores: la costura del medio tiene que quedar sin trazo.
        """
        from src.engine.utils.asset_loader import AssetLoader

        top = AssetLoader.load_image(
            settings.ASSETS_DIR / "ui" / "banner_top.png")
        bottom = AssetLoader.load_image(
            settings.ASSETS_DIR / "ui" / "banner_bottom.png")

        # El interior, lejos de las esquinas donde sí hay borde lateral
        # legítimo: si aquí hay algo que no sea el relleno de fondo, es la
        # costura.
        fondo_top = top.get_at((10, top.get_height() // 2))
        costura_top = top.get_at((top.get_width() // 2, top.get_height() - 1))
        assert costura_top == fondo_top, (
            f"banner_top.png dibuja algo en su borde inferior "
            f"({costura_top}) distinto del fondo ({fondo_top}): esa fila "
            f"cae justo en la costura con banner_bottom.png"
        )

        fondo_bottom = bottom.get_at((10, bottom.get_height() // 2))
        costura_bottom = bottom.get_at((bottom.get_width() // 2, 0))
        assert costura_bottom == fondo_bottom, (
            f"banner_bottom.png dibuja algo en su borde superior "
            f"({costura_bottom}) distinto del fondo ({fondo_bottom}): esa "
            f"fila cae justo en la costura con banner_top.png"
        )


class TestLosSubtitulos:
    def test_se_anclan_en_proporcion_a_la_pantalla(self, _video) -> None:
        from src.engine.core.event_bus import EventBus
        from src.engine.ui.subtitle_overlay import SubtitleOverlay

        overlay = SubtitleOverlay(EventBus())
        y = overlay.y_de_la_banda(1)
        assert 0 < y < settings.INTERNAL_HEIGHT
        # Por encima del borde inferior, con sitio para leerlos.
        assert y < settings.INTERNAL_HEIGHT - 40

    def test_varias_lineas_siguen_cabiendo(self, _video) -> None:
        from src.engine.core.event_bus import EventBus
        from src.engine.ui.subtitle_overlay import SubtitleOverlay

        overlay = SubtitleOverlay(EventBus())
        assert overlay.y_de_la_banda(3) > 0


class TestNadaSeQuedaEn320:
    #: Ficheros de interfaz que se dibujan durante la partida. Se comprueba que
    #: no queden números de la maqueta vieja escritos a pelo.
    _FICHEROS = (
        "src/engine/ui/message_box.py",
        "src/engine/ui/screen_banner.py",
        "src/engine/ui/subtitle_overlay.py",
    )

    @pytest.mark.parametrize("ruta", _FICHEROS)
    def test_la_maqueta_se_deriva(self, ruta: str) -> None:
        """No basta con que el resultado sea el bueno: tiene que derivarse.

        Si alguien vuelve a escribir los píxeles del 800×600 a mano, el día
        que la resolución cambie pasará otra vez lo mismo — y esta vez ya
        sabemos cuánto tarda en notarse: 2,5 veces de desfase sin que saltara
        nada.
        """
        import pathlib

        raiz = pathlib.Path(__file__).resolve().parent.parent
        fuente = (raiz / ruta).read_text(encoding="utf-8")
        assert "escalar(" in fuente, (
            f"{ruta} no deriva su maqueta de la escala del tema"
        )
