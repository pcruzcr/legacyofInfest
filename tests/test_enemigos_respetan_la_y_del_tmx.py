"""AUD-455 — la Y del TMX es la esquina superior, no los pies.

Hasta AUD-455 todas las clases de enemigo de suelo restaban `self.rect.height`
al y del spawn, según la convención «la Y del mapa son los pies». Pero los
mapas del repo colocan cada enemigo con la base del objeto sobre el suelo —
semántica nativa de Tiled—, así que todos flotaban a la altura de su caja: el
Walker de stage0 (28 px de alto) quedaba con la hurtbox a 1 px de poder tocar
al jugador de pie, y nunca podía dañarlo.

Lo que se fija aquí
-------------------
1. Que construir un enemigo deje `position.y` / `rect.y` **exactamente** en el
   y del spawn, sin descuento.
2. Que con un suelo debajo, tras actualizar, los pies (`rect.bottom`) se
   apoyen en el techo del suelo: el `_post_update` sigue clavando la vertical
   a la que el autor la dibujó.
"""
from __future__ import annotations

import pygame
import pytest

from src.framework.entities.enemy_archer import EnemyArcher
from src.framework.entities.enemy_assassin import EnemyAssassin
from src.framework.entities.enemy_brute import EnemyBrute
from src.framework.entities.enemy_caster import EnemyCaster
from src.framework.entities.enemy_charger import EnemyCharger
from src.framework.entities.enemy_shooter import EnemyShooter
from src.framework.entities.enemy_walker import EnemyWalker


@pytest.fixture(autouse=True)
def _video():
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((800, 600))


#: (clase, alto del rect que declara). El alto importa: cada clase restaba el
#: suyo, así que sin el arreglo cada una flotaría a una altura distinta.
ESPECIES_DE_SUELO: list[tuple[type, int]] = [
    (EnemyWalker, 28),
    (EnemyArcher, 28),
    (EnemyCharger, 24),
    (EnemyBrute, 60),
    (EnemyAssassin, 24),
    (EnemyShooter, 24),
    (EnemyCaster, 28),
]


class TestLaYDelSpawnSeRespeta:
    @pytest.mark.parametrize("especie,alto", ESPECIES_DE_SUELO)
    def test_el_rect_se_queda_en_el_y_del_tmx(self, especie: type, alto: int) -> None:
        enemigo = especie(pygame.Vector2(100.0, 150.0))
        assert enemigo.position.y == 150.0, (
            f"{especie.__name__}: el y del spawn se modificó"
        )
        assert enemigo.rect.y == 150, (
            f"{especie.__name__}: el rect no respeta la esquina superior del TMX"
        )
        assert enemigo.rect.height == alto
        assert enemigo.rect.bottom == 150 + alto, (
            f"{especie.__name__}: la base del rect no está donde la dibujó el autor"
        )

    @pytest.mark.parametrize("especie,alto", ESPECIES_DE_SUELO)
    def test_los_pies_se_apoyan_en_el_suelo(self, especie: type, alto: int) -> None:
        """Con el suelo debajo, la vertical queda clavada al techo del suelo."""
        piso = pygame.Rect(0, 480, 800, 128)
        enemigo = especie(pygame.Vector2(100.0, 480.0 - alto))
        if hasattr(enemigo, "set_collision_rects"):
            enemigo.set_collision_rects([piso])
        for _ in range(60):
            enemigo.update(1 / 60.0)
        assert enemigo.rect.bottom == pytest.approx(480.0, abs=0.01), (
            f"{especie.__name__}: los pies quedaron {480 - enemigo.rect.bottom} px"
            " por encima del suelo"
        )

    def test_el_walker_de_stage0_puede_tocar_al_jugador_de_pie(self) -> None:
        """La regresión que motivó el arreglo: el Walker de stage0 (base en
        y=480) solapaba la hurtbox del jugador parado (que empieza en 452+4)
        por un solo píxel, y el contacto no se disparaba nunca."""
        from src.framework.entities.player import Player

        walker = EnemyWalker(pygame.Vector2(288.0, 452.0))
        walker.set_collision_rects([pygame.Rect(0, 480, 992, 128)])
        walker._update_rects()
        jugador = Player(pygame.Vector2(300.0, 448.0))
        assert walker.hurtbox.colliderect(jugador.hurtbox), (
            "el Walker flotante no solapa la hurtbox del jugador de pie"
        )
