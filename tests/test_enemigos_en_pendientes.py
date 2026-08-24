"""AUD-325 — los enemigos respetan el suelo inclinado.

Hasta ahora las pendientes eran territorio exclusivo del jugador: los
enemigos ni las pisaban (un caminante atravesaba la cara empinada y era
absorbido hacia la hipotenusa) ni las subían (sus pies quedaban a la altura
a la que se colocaron, y una cuesta se convertía en un muro invisible).

Lo que se fija aquí
-------------------
1. Que el caminante siga la hipotenusa al subir y al bajar.
2. Que no atraviese la cara empinada.
3. Que los voladores no se peguen a las cuestas: ellos no las pisan.
4. Que sin pendientes el paso entero se salte — la condición de siempre
   para no tocar el comportamiento de los mapas ya calificados.
"""
from __future__ import annotations

import pygame
import pytest

from src.framework.entities.enemy_walker import EnemyWalker
from src.framework.stage.pendientes import Pendiente


@pytest.fixture(autouse=True)
def _video():
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((800, 600))


def _cuesta():
    # Sube a la derecha, de y=150 (pie) a y=50 (cima).
    return [Pendiente(pygame.Rect(0, 50, 200, 100), sube_a_la_derecha=True)]


class TestElCaminanteEnLaCuesta:
    def test_los_pies_siguen_la_hipotenusa(self) -> None:
        """Subiendo en patrulla, los pies se pegan a la superficie: una
        cuesta ya no es un muro invisible para los enemigos."""
        cuesta = _cuesta()
        # AUD-455: el y del spawn es la esquina superior (semántica de Tiled),
        # así que para que los pies partan de y=130 el y tiene que ser 130-28.
        enemigo = EnemyWalker(pygame.Vector2(30, 102), patrol_length=500)
        enemigo.set_collision_rects([])
        enemigo.set_pendientes(cuesta)
        for _ in range(200):
            enemigo.update(1 / 60.0)
        superficie = cuesta[0].altura_en(enemigo.rect.centerx)
        assert superficie is not None, "el caminante no llegó a pisar la cuesta"
        assert enemigo.rect.bottom == pytest.approx(superficie, abs=1.5)

    def test_no_atraviesa_la_cara_empinada(self) -> None:
        """La pared lateral del jugador (AUD-323) vale para los enemigos:
        caminando contra la cara, se frena en ella."""
        cuesta = _cuesta()
        # AUD-455: y del spawn = esquina superior → pies a 130 igual que antes.
        enemigo = EnemyWalker(
            pygame.Vector2(300, 102), patrol_length=1000, facing="left")
        enemigo.set_collision_rects([])
        enemigo.set_pendientes(cuesta)
        for _ in range(400):
            enemigo.update(1 / 60.0)
        assert enemigo.rect.left >= 200.0 - 1.0, (
            "el caminante atravesó la cara empinada de la rampa"
        )

    def test_sin_pendientes_el_paso_entero_se_salta(self) -> None:
        """La condición para las veintiséis entregas: sin `set_pendientes`
        nada cambia, ni siquiera se toca la geometría."""
        enemigo = EnemyWalker(pygame.Vector2(100, 100))
        enemigo.set_collision_rects([])
        y = enemigo.position.y
        for _ in range(60):
            enemigo.update(1 / 60.0)
        assert enemigo.position.y == y

    def test_los_voladores_no_se_pegan_a_las_cuestas(self) -> None:
        """Los voladores no pisan suelo: la bandera los excluye del paso."""
        from src.framework.entities.enemy_flying import EnemyFlying

        assert EnemyFlying(pygame.Vector2(100, 100))._hug_slopes is False
        assert EnemyWalker(pygame.Vector2(100, 100))._hug_slopes is True
