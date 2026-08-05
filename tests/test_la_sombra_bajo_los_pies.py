"""AUD-273 — nada proyectaba sombra, y sin sombra no se sabe dónde se cae.

Por qué hace falta
==================
En un plataformas 2D la sombra bajo los pies **no es decoración**: es el único
indicador de dónde va a aterrizar el jugador mientras está en el aire. Sin
ella, un salto largo sobre un hueco es una apuesta, y con la cámara siguiendo
al personaje el suelo suele quedar fuera de la vista útil.

El proyecto tenía luces, bloom, viñeta, rayos volumétricos y niebla — y ni una
sombra.

Cómo se dibuja, y por qué así
------------------------------
Una elipse oscura y translúcida en el suelo, **debajo de la entidad**, que se
encoge y se aclara con la altura. Elipse y no sprite porque tiene que valer
para cualquier tamaño de entidad sin pedir un asset por especie, y translúcida
porque una mancha opaca sobre un tileset con detalle se lee como un agujero.

El suelo se pasa por parámetro: el dibujado **no sabe** de colisiones, y
buscarlo aquí acoplaría dos sistemas que hoy no se conocen. Quien llama ya
tiene la lista de rects.
"""
from __future__ import annotations

import pygame
import pytest

from src.framework.vfx.sombras import ALTURA_DE_DESVANECIDO, Sombra, suelo_bajo


@pytest.fixture(autouse=True)
def _video():
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((800, 600))


SUELO = [pygame.Rect(0, 500, 800, 40)]


class TestDondeCaeLaSombra:
    def test_encuentra_el_suelo_de_debajo(self) -> None:
        cuerpo = pygame.Rect(100, 300, 32, 32)

        assert suelo_bajo(cuerpo, SUELO) == 500

    def test_ignora_lo_que_esta_por_encima(self) -> None:
        techo = pygame.Rect(0, 100, 800, 20)

        assert suelo_bajo(pygame.Rect(100, 300, 32, 32), [techo]) is None

    def test_se_queda_con_el_suelo_mas_alto_de_los_de_abajo(self) -> None:
        """Sobre una repisa, la sombra va en la repisa, no en el fondo del pozo."""
        repisa = pygame.Rect(80, 400, 100, 16)

        assert suelo_bajo(pygame.Rect(100, 300, 32, 32), [*SUELO, repisa]) == 400

    def test_sin_suelo_debajo_no_hay_sombra(self) -> None:
        assert suelo_bajo(pygame.Rect(100, 300, 32, 32), []) is None


class TestComoSeVe:
    def test_pinta_algo_en_el_suelo(self) -> None:
        superficie = pygame.Surface((800, 600))
        superficie.fill((120, 120, 120))
        sombra = Sombra()

        sombra.dibujar(superficie, pygame.Rect(100, 468, 32, 32), SUELO,
                       pygame.Vector2(0, 0))

        assert superficie.get_at((116, 500))[:3] != (120, 120, 120)

    def test_mas_alto_es_mas_pequena(self) -> None:
        sombra = Sombra()
        cerca = sombra.medidas(pygame.Rect(100, 468, 32, 32), 500)
        lejos = sombra.medidas(pygame.Rect(100, 300, 32, 32), 500)

        assert lejos[0] < cerca[0], "la sombra no se encoge con la altura"

    def test_mas_alto_es_mas_tenue(self) -> None:
        sombra = Sombra()
        _, _, alfa_cerca = sombra.medidas(pygame.Rect(100, 468, 32, 32), 500)
        _, _, alfa_lejos = sombra.medidas(pygame.Rect(100, 300, 32, 32), 500)

        assert alfa_lejos < alfa_cerca

    def test_muy_arriba_desaparece(self) -> None:
        """Una sombra que se ve desde cualquier altura deja de informar."""
        sombra = Sombra()
        altisimo = pygame.Rect(100, 500 - ALTURA_DE_DESVANECIDO - 50, 32, 32)

        assert sombra.medidas(altisimo, 500)[2] == 0

    def test_de_pie_sobre_el_suelo_es_del_ancho_del_cuerpo(self) -> None:
        sombra = Sombra()
        ancho, _, _ = sombra.medidas(pygame.Rect(100, 468, 32, 32), 500)

        assert 24 <= ancho <= 40


class TestNoRompeNada:
    def test_sin_suelo_no_dibuja_ni_lanza(self) -> None:
        superficie = pygame.Surface((800, 600))
        superficie.fill((120, 120, 120))

        Sombra().dibujar(superficie, pygame.Rect(100, 300, 32, 32), [],
                         pygame.Vector2(0, 0))

        assert superficie.get_at((116, 500))[:3] == (120, 120, 120)

    def test_respeta_el_desplazamiento_de_camara(self) -> None:
        superficie = pygame.Surface((800, 600))
        superficie.fill((120, 120, 120))

        Sombra().dibujar(superficie, pygame.Rect(400, 468, 32, 32), SUELO,
                         pygame.Vector2(300, 0))

        assert superficie.get_at((116, 500))[:3] != (120, 120, 120)
