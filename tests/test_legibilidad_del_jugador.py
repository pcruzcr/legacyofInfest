"""
Module: test_legibilidad_del_jugador
System: tests
Academic Unit: N/A

AUD-190 — el jugador desaparecía contra el fondo.

La medición
-----------
Contraste de luminancia (fórmula WCAG) entre el jugador y el fondo que lo
rodea, sobre los 16 escenarios: **1,01 a 1,18 en quince de ellos**. Un
contraste de 1,0 significa indistinguible. Sólo `boss_venado` llegaba a 1,98.

En un plataformas es el defecto de legibilidad más caro que existe: si no ves
dónde estás, no puedes calcular un salto, y el jugador culpa a los controles.

La corrección
-------------
Un contorno de un píxel alrededor del sprite, como cualquier juego 2D con
fondos oscuros. No toca los sprites: dibuja la misma imagen teñida de claro en
cuatro desplazamientos, detrás.

Sobre la trampa de medir esto
-----------------------------
La primera versión de la medición comparaba el rectángulo del jugador contra
`rect.inflate(24, 24)` — un área que **contiene al jugador**. Comparar algo
consigo mismo da 1,0 hagas lo que hagas, así que el número no se movía ni
después de arreglar el dibujado, y por poco me lleva a dar el arreglo por
inútil. Aquí se compara contra el **anillo**, con el hueco del jugador
recortado.
"""
from __future__ import annotations

import numpy as np
import pygame
import pytest

#: Por debajo de esto la figura se funde con el decorado. No es un valor
#: cosmético: 1,0 es literalmente indistinguible, y en las capturas previas al
#: arreglo el personaje sólo se encontraba porque uno sabía dónde mirar.
CONTRASTE_MINIMO = 1.6


def _luminancia(rgb: np.ndarray) -> np.ndarray:
    c = np.asarray(rgb, dtype=float) / 255.0
    c = np.where(c <= 0.03928, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    return 0.2126 * c[..., 0] + 0.7152 * c[..., 1] + 0.0722 * c[..., 2]


def _contraste(claro: float, oscuro: float) -> float:
    return (max(claro, oscuro) + 0.05) / (min(claro, oscuro) + 0.05)


@pytest.fixture
def sprite_del_jugador():
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((800, 600))
    from src.framework.entities.player import _silueta_de

    sprite = pygame.Surface((32, 32), pygame.SRCALPHA)
    # Un personaje oscuro, que es el caso real: los sprites del juego son
    # siluetas apagadas pensadas para un fondo que resultó ser igual de apagado.
    sprite.fill((0, 0, 0, 0))
    pygame.draw.rect(sprite, (34, 30, 44, 255), pygame.Rect(8, 4, 16, 26))
    return sprite, _silueta_de


class TestElContornoSeparaLaFiguraDelFondo:
    def test_la_silueta_es_mas_clara_que_el_sprite(self, sprite_del_jugador) -> None:
        """El fallo que tuvo la primera versión: `BLEND_RGBA_MIN` sobre un
        sprite oscuro devuelve el propio oscuro, así que se dibujaban cuatro
        copias de la misma sombra y no cambiaba nada."""
        sprite, silueta_de = sprite_del_jugador
        silueta = silueta_de(sprite)

        cuerpo = pygame.surfarray.array3d(sprite)[8:24, 4:30]
        borde = pygame.surfarray.array3d(silueta)[8:24, 4:30]

        assert _luminancia(borde).mean() > _luminancia(cuerpo).mean() * 3, (
            "la silueta no es más clara que el sprite: el contorno sería "
            "invisible sobre un fondo oscuro"
        )

    def test_el_contorno_contrasta_con_un_fondo_oscuro(
        self, sprite_del_jugador,
    ) -> None:
        """El escenario real: fondo apagado, personaje apagado."""
        sprite, silueta_de = sprite_del_jugador
        fondo_oscuro = (26, 24, 38)

        borde = pygame.surfarray.array3d(silueta_de(sprite))[8:24, 4:30]
        ratio = _contraste(
            float(_luminancia(borde).mean()),
            float(_luminancia(np.array(fondo_oscuro)).mean()),
        )
        assert ratio >= CONTRASTE_MINIMO, (
            f"el contorno contrasta {ratio:.2f} contra el fondo del juego, "
            f"por debajo del mínimo de {CONTRASTE_MINIMO}"
        )

    def test_la_silueta_conserva_la_forma_recortada(
        self, sprite_del_jugador,
    ) -> None:
        """Si el teñido tocara el alfa, el contorno sería un cuadrado y el
        jugador iría dentro de una caja blanca."""
        sprite, silueta_de = sprite_del_jugador
        original = pygame.surfarray.array_alpha(sprite)
        tenida = pygame.surfarray.array_alpha(silueta_de(sprite))

        assert np.array_equal(original, tenida), (
            "el teñido ha alterado el alfa: el contorno dejaría de seguir la "
            "silueta del personaje"
        )

    def test_las_siluetas_se_cachean(self, sprite_del_jugador) -> None:
        """Se dibujan cuatro por fotograma; recalcularlas sería tirar trabajo."""
        sprite, silueta_de = sprite_del_jugador
        assert silueta_de(sprite) is silueta_de(sprite)
