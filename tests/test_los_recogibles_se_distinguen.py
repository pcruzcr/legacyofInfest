"""Cada recogible se dibuja de su color — AUD-234.

El hueco
========
`DrawingSystem._draw_interactables` pintaba **todos** los recogibles con el
mismo `_COLOR_RECOGIBLE = (240, 210, 90)`. Una moneda de oro, una llave roja y
una vasija de corazón eran tres rectángulos idénticos en pantalla.

No es sólo estético. Desde AUD-218 los enemigos sueltan monedas, así que el
suelo de un nivel se llena de recogibles y el jugador ya no puede saber de un
vistazo si eso de ahí es la llave que le falta o el cambio de matar a un
esbirro. Y el dato para distinguirlos **ya existía**: `ItemDef.icon_color`
lleva desde el principio en `engine.core.inventory`, con un dorado para `coin`,
un rojo para `heart_vessel` y un color propio para cada prenda — y nadie lo
leía fuera del aviso de recogida.

Otra vez el patrón de este proyecto: el dato estaba, quien lo necesitaba
estaba, y no había camino entre los dos.

Lo que no cambia
----------------
Un `item_id` libre —`"llave_roja"`, `"tuerca"`, lo que un estudiante invente—
no está en el catálogo y **conserva el color de siempre**. Ese es el control:
las 26 entregas usan ids propios y sus niveles se ven exactamente igual.
"""
from __future__ import annotations

import pygame
import pytest

from src.framework.stage.drawing_system import DrawingSystem
from src.framework.stage.interactable_system import InteractableSystem
from src.framework.stage.interactables import Recogible


@pytest.fixture(autouse=True)
def _video():
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((320, 240))


def _pintar(item_id: str) -> tuple[int, int, int]:
    """Dibuja un recogible en (0,0) y devuelve el color de su centro."""
    sistema = InteractableSystem(recogibles=[
        Recogible(rect=pygame.Rect(0, 0, 16, 16), item_id=item_id),
    ])
    lienzo = pygame.Surface((64, 64))
    lienzo.fill((0, 0, 0))
    DrawingSystem._draw_interactables(
        DrawingSystem.__new__(DrawingSystem), lienzo, sistema,
        pygame.Vector2(0, 0),
    )
    return lienzo.get_at((8, 8))[:3]


class TestCadaObjetoSeVeDeSuColor:
    def test_la_moneda_es_dorada(self) -> None:
        from src.engine.core.inventory import get_inventory

        esperado = get_inventory().get_def("coin").icon_color
        assert _pintar("coin") == esperado, (
            "la moneda se pintaba del amarillo genérico de todos los "
            "recogibles; `ItemDef.icon_color` existía y nadie lo leía"
        )

    def test_la_vasija_de_corazon_es_roja(self) -> None:
        from src.engine.core.inventory import get_inventory

        esperado = get_inventory().get_def("heart_vessel").icon_color
        assert _pintar("heart_vessel") == esperado

    def test_dos_objetos_distintos_no_se_ven_iguales(self) -> None:
        """Lo que el jugador necesita: distinguirlos de un vistazo."""
        assert _pintar("coin") != _pintar("heart_vessel")

    def test_una_habilidad_de_jefe_tambien_tiene_el_suyo(self) -> None:
        """Desde AUD-238 caen al suelo junto a las monedas del jefe."""
        assert _pintar("skill_dash") != _pintar("coin")


class TestLasEntregasNoCambian:
    """El control. Un `item_id` inventado no está en el catálogo."""

    def test_una_llave_conserva_el_color_de_siempre(self) -> None:
        assert _pintar("llave_roja") == DrawingSystem._COLOR_RECOGIBLE

    def test_un_id_cualquiera_tambien(self) -> None:
        assert _pintar("tuerca_del_estudiante") == DrawingSystem._COLOR_RECOGIBLE

    def test_un_recogido_sigue_sin_dibujarse(self) -> None:
        sistema = InteractableSystem(recogibles=[
            Recogible(
                rect=pygame.Rect(0, 0, 16, 16), item_id="coin", recogido=True,
            ),
        ])
        lienzo = pygame.Surface((64, 64))
        lienzo.fill((0, 0, 0))
        DrawingSystem._draw_interactables(
            DrawingSystem.__new__(DrawingSystem), lienzo, sistema,
            pygame.Vector2(0, 0),
        )
        assert lienzo.get_at((8, 8))[:3] == (0, 0, 0)
