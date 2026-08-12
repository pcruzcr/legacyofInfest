"""AUD-446 — el menú de título enseñaba catorce opciones de golpe.

`MenuList.draw` pintaba **todas** las filas. En el título son catorce, y a
30 px por fila son 420 px de los 600 que hay: la pantalla se convierte en una
lista de la compra y el logo pelea por el sitio con las opciones.

Lo que se añade es una **ventana**: se ven tres o cuatro filas y la lista se
desliza para mantener la seleccionada dentro. No se quita ninguna opción —
quitar funciones para que quepan sería resolver el problema equivocado.

Es opcional a propósito
-----------------------
`visible_rows = None` mantiene el comportamiento de siempre, que es lo que
quieren las listas cortas: los logros, el inventario o la tienda caben
enteros, y hacerlas desplazarse sólo escondería filas que hoy se ven.

El desplazamiento es suave
--------------------------
Saltar de golpe cuando el foco cruza el borde de la ventana hace perder de
vista dónde estabas: el ojo no puede seguir un salto instantáneo de tres
filas. Se interpola, y por eso `update(dt)` deja de ser sólo un contador de
tiempo para el parpadeo del cursor.
"""
from __future__ import annotations

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame
import pytest

from src.engine.ui.widgets import MenuItem, MenuList


@pytest.fixture(scope="module")
def _video():
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((800, 600))
    yield


def _lista(n: int, visibles: int | None = None) -> MenuList:
    menu = MenuList(items=[MenuItem(f"OPCION {i}", value=str(i)) for i in range(n)])
    menu.visible_rows = visibles
    return menu


def _asentar(menu: MenuList, segundos: float = 2.0) -> None:
    for _ in range(int(segundos * 60)):
        menu.update(1 / 60)


class TestLaVentana:
    def test_sin_ventana_se_ven_todas(self, _video) -> None:
        """El control que impide romper las listas cortas."""
        menu = _lista(14)
        assert menu.filas_visibles() == list(range(14))

    def test_con_ventana_se_ven_solo_esas(self, _video) -> None:
        menu = _lista(14, visibles=4)
        assert len(menu.filas_visibles()) == 4

    def test_una_lista_mas_corta_que_la_ventana_no_se_estira(self, _video) -> None:
        menu = _lista(2, visibles=4)
        assert menu.filas_visibles() == [0, 1]


class TestElFocoSiempreSeVe:
    @pytest.mark.parametrize("destino", [0, 1, 5, 9, 13])
    def test_la_seleccionada_esta_dentro_de_la_ventana(self, _video, destino: int) -> None:
        """Lo único que la ventana no puede hacer nunca: esconder el foco."""
        menu = _lista(14, visibles=4)
        menu.index = destino
        _asentar(menu)
        assert destino in menu.filas_visibles(), (
            f"con el foco en {destino} se ven {menu.filas_visibles()}: el "
            f"jugador no ve qué tiene seleccionado"
        )

    def test_bajando_una_a_una_nunca_se_pierde_el_foco(self, _video) -> None:
        menu = _lista(14, visibles=4)
        for _ in range(20):                  # más que la lista: da la vuelta
            menu.move_down()
            _asentar(menu, 0.5)
            assert menu.index in menu.filas_visibles()

    def test_al_final_de_la_lista_la_ventana_no_se_pasa(self, _video) -> None:
        """Desplazarse más allá del final dejaría filas vacías abajo."""
        menu = _lista(14, visibles=4)
        menu.index = 13
        _asentar(menu)
        assert menu.filas_visibles() == [10, 11, 12, 13]


class TestElDesplazamientoEsSuave:
    def test_no_salta_de_golpe(self, _video) -> None:
        menu = _lista(14, visibles=4)
        menu.index = 0
        _asentar(menu)
        menu.index = 13

        menu.update(1 / 60)
        a_medias = menu.desplazamiento
        assert 0.0 < a_medias < 10.0, (
            f"en un fotograma el desplazamiento pasó a {a_medias}: el salto "
            f"instantáneo hace perder de vista dónde estabas"
        )

    def test_pero_llega(self, _video) -> None:
        """Suave no puede significar que nunca termina."""
        menu = _lista(14, visibles=4)
        menu.index = 13
        _asentar(menu)
        assert menu.desplazamiento == pytest.approx(10.0, abs=0.05)

    def test_dibujar_no_revienta_a_media_animacion(self, _video) -> None:
        menu = _lista(14, visibles=4)
        menu.index = 13
        superficie = pygame.Surface((800, 600))
        for _ in range(30):
            menu.update(1 / 60)
            menu.draw(superficie, 40, 100, 300)

    def test_dibujar_no_deja_el_recorte_puesto(self, _video) -> None:
        """La ventana recorta para que las filas no se salgan.

        Si el recorte se quedara puesto, todo lo que se dibujara después —los
        avisos de abajo, el logo— aparecería cortado por una región que no es
        suya. Es el tipo de fallo que se ve como «desapareció media pantalla».
        """
        menu = _lista(14, visibles=4)
        superficie = pygame.Surface((800, 600))
        superficie.set_clip(None)
        menu.draw(superficie, 40, 100, 300)
        assert superficie.get_clip() == superficie.get_rect()
