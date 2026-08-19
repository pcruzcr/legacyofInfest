"""AUD-547 — jugado, dos cosas del rediseño de AUD-535 seguían sin
resolverse: el retrato vivía a 5 px reales del borde de la pantalla —
casi pegado— y el minimapa, pese a su "recorte redondeado", seguía
siendo un rectángulo de 62×44 con las esquinas muy curvas. Pedido
explícito tras jugarlo: "nada quede pegado a la izquierda o a la
derecha o arriba y abajo" y (en ese momento) que el minimapa fuera
circular como el retrato. De paso, las tres barras del bloque de
identidad (vida/estamina/carga) dejaron de cambiar de color según el
nivel — ahora son rojo/amarillo/azul fijos, otro pedido explícito.

AUD-560 — el propio dueño revirtió la parte del minimapa: "que el
minimapa sea rectangular cuadrado", no circular. El recuadro se queda
cuadrado (eso es lo que pide "cuadrado"); lo que cambia es que ya no
hay máscara circular — vuelve a ser un rectángulo de esquinas rectas,
como antes de AUD-547.
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


class TestNingunElementoQuedaPegadoAUnBorde:
    """El margen mínimo, medido contra los cuatro bordes reales."""

    MARGEN_MINIMO_PX = 10  # generoso a propósito: sólo comprueba "no pegado"

    def test_el_retrato_no_toca_la_izquierda_ni_arriba(self, hud) -> None:
        r = hud.regiones()["retrato"]
        assert r.left >= self.MARGEN_MINIMO_PX, (
            f"el retrato empieza en x={r.left}: casi pegado al borde izquierdo"
        )
        assert r.top >= self.MARGEN_MINIMO_PX, (
            f"el retrato empieza en y={r.top}: casi pegado al borde superior"
        )

    def test_el_cronometro_no_toca_arriba(self, hud) -> None:
        r = hud.timer_rect()
        assert r.top >= self.MARGEN_MINIMO_PX, (
            f"el cronómetro empieza en y={r.top}: casi pegado al borde superior"
        )

    def test_el_minimapa_no_toca_la_derecha(self, hud) -> None:
        r = hud.minimap_rect()
        assert settings.INTERNAL_WIDTH - r.right >= self.MARGEN_MINIMO_PX, (
            f"el minimapa termina en x={r.right} de {settings.INTERNAL_WIDTH}: "
            f"casi pegado al borde derecho"
        )

    def test_ninguna_region_se_sale_de_la_pantalla(self, hud) -> None:
        """El seguro de siempre: un margen que empuja algo fuera de la
        pantalla por el lado contrario sería peor que el problema."""
        marco = pygame.Rect(0, 0, settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT)
        for nombre, region in hud.regiones().items():
            assert marco.contains(region), (
                f"la región {nombre!r} ({region}) se sale de la pantalla"
            )


class TestElMinimapaEsRectangularCuadrado:
    """AUD-560 — revierte AUD-547: pedido explícito del dueño, "que el
    minimapa sea rectangular cuadrado", no circular. El recuadro sigue
    siendo cuadrado (44×44, eso es lo que pide "cuadrado"); lo que
    cambia es que ya no hay máscara — el lienzo entero se pinta, sin
    recortar las esquinas en redondo."""

    def test_el_recuadro_del_minimapa_es_cuadrado(self, hud) -> None:
        r = hud.minimap_rect()
        assert r.width == r.height, (
            f"el recuadro del minimapa mide {r.width}×{r.height}: no es "
            f"cuadrado"
        )

    def test_las_esquinas_del_lienzo_tambien_se_pintan(self, hud) -> None:
        """Lo contrario de lo que pedía AUD-547: sin máscara circular,
        las cuatro esquinas del fondo del minimapa se pintan igual que
        el centro — no quedan vacías."""
        from src.engine.ui.minimap import Minimap

        mm = Minimap()
        mm.colocar(hud.minimap_rect())
        mm.set_map_size(2000, 500)
        mm.update((100.0, 100.0), 1, [], [], [], set())
        lienzo = _lienzo()
        mm.draw(lienzo)
        r = hud.minimap_rect()
        esquina = lienzo.get_at((r.left, r.top))
        assert tuple(esquina)[:3] != (0, 0, 0), (
            "la esquina del minimapa quedó vacía: sigue recortando en "
            "redondo en vez de pintar el rectángulo entero"
        )

    def test_el_centro_del_lienzo_tambien_se_pinta(self, hud) -> None:
        from src.engine.ui.minimap import Minimap

        mm = Minimap()
        mm.colocar(hud.minimap_rect())
        mm.set_map_size(2000, 500)
        mm.update((100.0, 100.0), 1, [], [], [], set())
        lienzo = _lienzo()
        mm.draw(lienzo)
        r = hud.minimap_rect()
        centro = lienzo.get_at(r.center)
        assert tuple(centro)[:3] != (0, 0, 0), (
            "el centro del minimapa no se pintó: el fondo no se dibujó"
        )


class TestLasTresBarrasTienenColorFijo:
    """AUD-547 — rojo/amarillo/azul, sin variante de urgencia."""

    def test_la_barra_de_vida_es_roja_a_cualquier_nivel(self, hud) -> None:
        colores = set()
        for salud in (100.0, 20.0, 5.0):
            hud._health = salud
            lienzo = _lienzo()
            hud._draw_barra_de_vida(lienzo)
            r = hud.vida_bar_rect()
            colores.add(tuple(lienzo.get_at((r.left + 2, r.centery)))[:3])
        assert len(colores) == 1, (
            f"la barra de vida cambia de color según el nivel: {colores}"
        )

    def test_la_barra_de_estamina_es_amarilla_a_cualquier_nivel(self, hud) -> None:
        colores = set()
        for actual in (100.0, 50.0, 5.0):
            hud.set_estamina(actual, 100.0)
            lienzo = _lienzo()
            hud._draw_estamina(lienzo)
            r = hud._estamina_bar_rect
            colores.add(tuple(lienzo.get_at((r.left + 2, r.centery)))[:3])
        assert len(colores) == 1, (
            f"la barra de estamina cambia de color según el nivel: {colores}"
        )

    def test_la_barra_de_carga_es_azul_a_cualquier_nivel(self, hud) -> None:
        """No compara bytes idénticos a propósito: al llegar a 100 %
        `_dibujar_barra_moderna` añade un halo aditivo ("lista") que
        aclara el color muestreado — una señal legítima y aparte de si
        el degradado sigue siendo azul. Lo que importa aquí es que en
        ningún nivel se vuelva dorado/ámbar, que era el comportamiento
        antiguo."""
        for actual in (10.0, 50.0, 90.0):  # <100 evita el halo de "listo"
            hud.set_special_meter(actual, 100.0)
            lienzo = _lienzo()
            hud._draw_special_meter(lienzo)
            r = hud._carga_bar_rect
            color = tuple(lienzo.get_at((r.left + 2, r.centery)))[:3]
            assert color[2] >= color[0] and color[2] >= color[1], (
                f"a {actual}% la barra de carga no lee azul: {color}"
            )


class TestLasBarrasComparteAnchoYGrosor:
    def test_las_tres_barras_tienen_el_mismo_ancho_que_el_retrato(self, hud) -> None:
        retrato = hud.regiones()["retrato"]
        assert hud.vida_bar_rect().width == retrato.width
        assert hud._estamina_bar_rect.width == retrato.width
        assert hud._carga_bar_rect.width == retrato.width

    def test_las_tres_barras_tienen_el_mismo_grosor(self, hud) -> None:
        alturas = {
            hud.vida_bar_rect().height,
            hud._estamina_bar_rect.height,
            hud._carga_bar_rect.height,
        }
        assert len(alturas) == 1, f"las barras no comparten grosor: {alturas}"

    def test_las_tres_barras_estan_apiladas_en_orden(self, hud) -> None:
        """Vida, luego estamina, luego carga — de arriba abajo, sin huecos
        raros ni superposición."""
        vida = hud.vida_bar_rect()
        estamina = hud._estamina_bar_rect
        carga = hud._carga_bar_rect
        assert vida.bottom <= estamina.top
        assert estamina.bottom <= carga.top
        assert vida.x == estamina.x == carga.x
