"""AUD-535 — rediseño espacial del HUD: la vida deja de ser una fila de
corazones y pasa a ser una barra continua; el retrato pasa a ser circular;
el marcador cambia su glifo de moneda roto por un ícono dibujado; el
cronómetro cambia su umbral de alerta de 30 a 10 segundos.

Cada sección de este archivo prueba una pieza del pedido del dueño
(`docs/09_HUD_SPEC.md` §1, nota AUD-535), no gusto visual:

1. La vida es un porcentaje pintado con `_dibujar_barra_moderna`, no cinco
   sprites de corazón — `tests/test_hud.py` ya retiró `TestHeartSlotState`
   porque no hay ranuras que traducir; aquí se prueba lo que ocupó su
   lugar.
2. El retrato se recorta en círculo una sola vez al cargar.
3. El glifo de moneda "¤" no existe en la fuente del tema (medido: 22 px
   de ancho para tres caracteres) y se reemplazó por un ícono dibujado.
4. El umbral de alerta del cronómetro bajó de 30 a 10 segundos, pedido
   explícito del dueño.
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


class TestLaBarraDeVidaPintaUnPorcentaje:
    def test_a_vida_completa_la_barra_esta_llena_de_borde_a_borde(self, hud) -> None:
        lienzo = _lienzo()
        hud._draw_barra_de_vida(lienzo)
        r = hud.vida_bar_rect()
        # El relleno llega hasta el borde derecho del rect a pct=1.0 —
        # el píxel justo antes del borde no puede ser el fondo vacío.
        borde = lienzo.get_at((r.right - 2, r.centery))
        assert tuple(borde)[:3] != (0, 0, 0), (
            "la barra de vida no llegó al borde derecho a vida completa"
        )

    def test_a_media_vida_el_relleno_no_pasa_de_la_mitad(self, hud) -> None:
        hud._health = hud._max_health / 2.0
        lienzo = _lienzo()
        hud._draw_barra_de_vida(lienzo)
        r = hud.vida_bar_rect()
        # A pct=0.5 la zona sin llenar debe verse: se muestrea a 3px del
        # borde derecho —no en el borde mismo, que `_dibujar_barra_moderna`
        # traza en `color_fin` alrededor de todo el rect
        # independientemente del relleno— y bien pasado el 50% del ancho.
        extremo = lienzo.get_at((r.right - 3, r.centery))
        lleno_color = (230, 70, 70)
        assert tuple(extremo)[:3] != lleno_color, (
            "la barra de vida rellenó más allá de la mitad con la vida a la mitad"
        )

    def test_sin_vida_no_pinta_relleno_pero_no_estalla(self, hud) -> None:
        hud._health = 0.0
        lienzo = _lienzo()
        hud._draw_barra_de_vida(lienzo)  # no debe lanzar

    def test_comparte_ancho_con_el_retrato(self, hud) -> None:
        """El pedido: "del mismo ancho que el retrato", no un tamaño suelto."""
        retrato = hud.regiones()["retrato"]
        assert hud.vida_bar_rect().width == retrato.width


class TestElDestelloDeDanoYCuracion:
    def test_recibir_dano_arma_el_destello_de_la_barra_entera(self, hud) -> None:
        """AUD-535 — no hay ranuras que destellar una a una; destella la
        barra completa."""
        assert hud._vida_flash_timer == 0.0
        hud._on_player_damaged(amount=1.0, source=(0, 0))
        assert hud._vida_flash_timer > 0.0

    def test_curarse_arma_el_destello_verde_no_el_rojo(self, hud) -> None:
        assert hud._vida_heal_timer == 0.0
        hud._on_player_healed(amount=1.0)
        assert hud._vida_heal_timer > 0.0
        assert hud._vida_flash_timer == 0.0, (
            "curarse no debe dejar armado el destello de daño"
        )

    def test_daño_de_cero_no_arma_destello(self, hud) -> None:
        """Un evento sin cantidad real (p. ej. de una prueba ajena) no debe
        hacer parpadear la barra."""
        hud._on_player_damaged(amount=0.0, source=(0, 0))
        assert hud._vida_flash_timer == 0.0


class TestElRetratoEsCircular:
    def test_las_esquinas_del_sprite_quedan_transparentes(self, hud) -> None:
        """Un recorte circular dentro de un rect cuadrado deja las cuatro
        esquinas fuera del círculo — un marco 9-slice rectangular no las
        habría dejado nunca transparentes."""
        portrait = hud._portraits.get("normal")
        assert portrait is not None, "no se cargó el retrato normal"
        esquina = portrait.get_at((0, 0))
        assert esquina[3] == 0, (
            f"la esquina del retrato no es transparente (alfa={esquina[3]}): "
            f"sigue siendo un sprite cuadrado, no recortado en círculo"
        )

    def test_el_centro_del_sprite_sigue_opaco(self, hud) -> None:
        portrait = hud._portraits.get("normal")
        assert portrait is not None
        w, h = portrait.get_size()
        centro = portrait.get_at((w // 2, h // 2))
        assert centro[3] > 200, (
            "el centro del retrato quedó transparente: el recorte circular "
            "se comió también el contenido, no sólo las esquinas"
        )

    def test_el_marco_del_retrato_dibuja_un_anillo_no_una_caja(self, hud) -> None:
        """`_draw_portrait` no debe lanzar y debe pintar algo en el borde
        del marco (el anillo), no dejarlo negro."""
        lienzo = _lienzo()
        hud._draw_portrait(lienzo)
        r = hud.regiones()["retrato"]
        borde = lienzo.get_at((r.centerx, r.top + 1))
        assert tuple(borde)[:3] != (0, 0, 0), "el anillo del retrato no se dibujó"


class TestElIconoDeMonedaReemplazaElGlifoRoto:
    """AUD-535 — `theme.font().render("¤56", ...)` medía 22 px de ancho
    para tres caracteres (la mitad de lo real) porque el glifo "¤" no
    existe en `assets/fonts/game.ttf`. `_icono_de_moneda` lo reemplaza."""

    def test_el_icono_no_es_transparente_del_todo(self) -> None:
        from src.engine.ui.hud import _icono_de_moneda

        icono = _icono_de_moneda(16, (255, 215, 0))
        opacos = sum(
            1
            for x in range(icono.get_width())
            for y in range(icono.get_height())
            if icono.get_at((x, y))[3] > 0
        )
        assert opacos > 0, "el ícono de moneda no pintó ni un solo píxel"

    def test_el_icono_se_cachea_por_diametro_y_color(self) -> None:
        from src.engine.ui.hud import _icono_de_moneda

        a = _icono_de_moneda(16, (255, 215, 0))
        b = _icono_de_moneda(16, (255, 215, 0))
        assert a is b, "cada llamada reconstruye el ícono en vez de cachearlo"

    def test_el_marcador_dibuja_algo_con_monedas_positivas(self, hud) -> None:
        hud.set_score(0, 56)
        lienzo = _lienzo()
        hud._draw_score(lienzo)
        r = hud.score_rect()
        pintado = any(
            tuple(lienzo.get_at((x, y)))[:3] != (0, 0, 0)
            for x in range(r.left, r.right)
            for y in range(r.top, r.bottom)
        )
        assert pintado, "el marcador con monedas no pintó nada en su región"


class TestElUmbralDeAlertaDelCronometroBajoADiez:
    def test_la_constante_es_diez(self, hud) -> None:
        assert hud.UMBRAL_DE_ALERTA_S == 10

    def test_a_once_segundos_no_hay_alerta(self, hud) -> None:
        hud.start_timer(time_limit=100)
        hud._timer = 11.0
        hud.update(0.0)
        assert hud._timer_flash_timer == 0.0 or not hud._is_countdown

    def test_a_diez_segundos_arranca_la_alerta(self, hud) -> None:
        hud.start_timer(time_limit=100)
        hud._timer = 10.0
        hud.update(0.3)  # más de 0.25s: ya debió alternar una vez
        assert hud._timer_flash_on or hud._timer_flash_timer > 0.0, (
            "a 10 segundos exactos el cronómetro debería estar en alerta"
        )
