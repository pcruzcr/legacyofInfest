"""
Module: test_el_spawn_deja_los_pies_en_el_suelo
System: tests
Description: AUD-819 (P14) — el cuerpo nace con su tamaño lógico (20×32) y
el spawn deja los pies en la Y del TMX, no 32 px dentro del suelo.
"""
from __future__ import annotations

import pygame

from src.framework.entities.player import Player


class TestElSpawnDejaLosPiesEnElSuelo:
    def test_el_cuerpo_nace_con_el_tamano_logico(self) -> None:
        """Ni 40×64 ni ningún otro tamaño del arte: de pie, 20×32."""
        jugador = Player(pygame.Vector2(48, 512))
        assert (jugador.rect.width, jugador.rect.height) == (
            Player.ANCHO_DE_PIE, Player.ALTO_DE_PIE,
        )

    def test_los_pies_nacen_en_la_y_del_spawn_mas_alto(self) -> None:
        """`spawn_point` ya trae `obj.y - ALTO_DE_PIE`: los pies
        (`rect.bottom`) quedan en `obj.y`, sin penetración que expulsar."""
        obj_y = 560.0
        spawn = pygame.Vector2(48, obj_y - Player.ALTO_DE_PIE)
        jugador = Player(spawn)
        assert jugador.rect.bottom == obj_y

    def test_el_primer_fotograma_no_desplaza_al_jugador(self) -> None:
        """Con el cuerpo lógico desde el fotograma cero, `_update_rect_size`
        no tiene nada que corregir: `position` no se mueve sola."""
        jugador = Player(pygame.Vector2(48, 528))
        antes = (jugador.position.x, jugador.position.y)
        jugador._update_rect_size()
        assert (jugador.position.x, jugador.position.y) == antes
        assert (jugador.rect.x, jugador.rect.y) == (int(antes[0]), int(antes[1]))
