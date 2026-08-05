"""AUD-276 — buscar en la lista de sólidos era mirarla entera, siempre.

Por qué hace falta
==================
Todo lo que pregunta «¿qué hay aquí?» recorre `stage.collision_rects` de punta
a punta: la sombra bajo los pies (AUD-273), el suelo del jugador, las zonas de
daño. Un mapa como `stage4_1` trae **miles** de rectángulos, y la inmensa
mayoría están a pantallas de distancia de la pregunta.

Y no había forma de preguntar «¿qué hay entre este punto y aquel otro?». Sin
raycast no se puede hacer línea de visión de un guardia, ni un disparo
hitscan, ni comprobar si una plataforma tapa una luz — tres cosas que la hoja
de ruta pide y que hoy no se pueden ni empezar.

Qué es esto, y qué no
---------------------
Una rejilla uniforme: el mundo se parte en celdas y cada rectángulo se apunta
en las que toca. Preguntar por una zona mira **sólo** las celdas que la cubren.

Uniforme y no un árbol: los rectángulos de un TMX son estáticos y están
repartidos de forma bastante pareja, que es exactamente el caso en el que una
rejilla gana a un quadtree — y se explica en tres líneas, que en material de
curso cuenta.

**Es aditivo.** Nada del motor la usa todavía; se construye desde la lista que
el cargador ya produce y no cambia ningún contrato. Quien no la use no paga
nada.
"""
from __future__ import annotations

import pygame
import pytest

from src.framework.stage.rejilla import RejillaEspacial


@pytest.fixture(autouse=True)
def _video():
    pygame.init()


def _mundo() -> list[pygame.Rect]:
    """Un suelo largo y tres bloques sueltos, bien separados."""
    return [
        pygame.Rect(0, 500, 2000, 40),
        pygame.Rect(200, 400, 32, 32),
        pygame.Rect(900, 400, 32, 32),
        pygame.Rect(1800, 300, 32, 32),
    ]


class TestQueHayAqui:
    def test_encuentra_lo_que_toca_la_zona(self) -> None:
        r = RejillaEspacial(_mundo())

        cerca = r.cercanos(pygame.Rect(190, 390, 60, 60))

        assert pygame.Rect(200, 400, 32, 32) in cerca

    def test_no_devuelve_lo_que_esta_lejos(self) -> None:
        r = RejillaEspacial(_mundo())

        cerca = r.cercanos(pygame.Rect(190, 390, 60, 60))

        assert pygame.Rect(1800, 300, 32, 32) not in cerca

    def test_una_zona_vacia_no_devuelve_nada(self) -> None:
        r = RejillaEspacial(_mundo())

        assert r.cercanos(pygame.Rect(600, 100, 40, 40)) == []

    def test_lo_que_ocupa_varias_celdas_sale_una_sola_vez(self) -> None:
        """El suelo largo cruza muchas celdas: no puede salir repetido."""
        r = RejillaEspacial(_mundo())

        cerca = r.cercanos(pygame.Rect(0, 480, 1200, 80))

        assert cerca.count(pygame.Rect(0, 500, 2000, 40)) == 1

    def test_da_lo_mismo_que_mirar_la_lista_entera(self) -> None:
        """El patrón oro: la rejilla es una optimización, no otra respuesta."""
        mundo = _mundo()
        r = RejillaEspacial(mundo)
        for x in range(0, 2000, 97):
            zona = pygame.Rect(x, 280, 120, 260)
            ingenuo = {tuple(m) for m in mundo if m.colliderect(zona)}
            assert ingenuo <= {tuple(m) for m in r.cercanos(zona)}, (
                f"la rejilla se dejó algo en x={x}"
            )


class TestQueHayEnLinea:
    def test_el_rayo_choca_con_lo_que_tiene_delante(self) -> None:
        r = RejillaEspacial(_mundo())

        impacto = r.rayo(pygame.Vector2(150, 415), pygame.Vector2(400, 415))

        assert impacto is not None

    def test_el_rayo_pasa_por_donde_no_hay_nada(self) -> None:
        r = RejillaEspacial(_mundo())

        assert r.rayo(pygame.Vector2(400, 100), pygame.Vector2(800, 100)) is None

    def test_devuelve_el_primero_que_encuentra(self) -> None:
        """Con dos bloques en línea, gana el más cercano al origen."""
        cerca = pygame.Rect(300, 100, 20, 20)
        lejos = pygame.Rect(600, 100, 20, 20)
        r = RejillaEspacial([lejos, cerca])

        impacto = r.rayo(pygame.Vector2(0, 110), pygame.Vector2(900, 110))

        assert impacto == cerca

    def test_un_rayo_de_longitud_cero_no_revienta(self) -> None:
        r = RejillaEspacial(_mundo())

        r.rayo(pygame.Vector2(100, 100), pygame.Vector2(100, 100))

    def test_hay_linea_de_vision_si_no_hay_nada_en_medio(self) -> None:
        r = RejillaEspacial([pygame.Rect(300, 100, 20, 20)])

        assert r.hay_vision(pygame.Vector2(0, 400), pygame.Vector2(900, 400))

    def test_no_hay_linea_de_vision_a_traves_de_un_muro(self) -> None:
        r = RejillaEspacial([pygame.Rect(300, 100, 20, 400)])

        assert not r.hay_vision(pygame.Vector2(0, 200), pygame.Vector2(900, 200))


class TestCasosDeBorde:
    def test_una_rejilla_vacia_funciona(self) -> None:
        r = RejillaEspacial([])

        assert r.cercanos(pygame.Rect(0, 0, 100, 100)) == []
        assert r.rayo(pygame.Vector2(0, 0), pygame.Vector2(100, 100)) is None

    def test_coordenadas_negativas(self) -> None:
        """Un mapa puede tener geometría a la izquierda del origen."""
        bloque = pygame.Rect(-200, -100, 32, 32)
        r = RejillaEspacial([bloque])

        assert bloque in r.cercanos(pygame.Rect(-210, -110, 60, 60))
