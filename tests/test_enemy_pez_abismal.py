"""AUD-519 — el pez abismal de 4.1b: aparece de la nada, persigue, no
puede tocar al jugador ni ser tocado por él.
"""
from __future__ import annotations

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame
import pytest

from src.framework.entities.enemy_pez_abismal import EnemyPezAbismal


@pytest.fixture(scope="module")
def _video() -> None:
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((320, 240))


class TestNoPuedeDanarAlJugador:
    def test_damage_on_contact_es_cero(self, _video) -> None:
        pez = EnemyPezAbismal(pygame.Vector2(0, 0))
        assert pez.damage_on_contact == 0.0


class TestNoSePuedeDanar:
    """Pedido explícito: que el jugador tampoco pueda hacerle nada — una
    criatura a la que se puede golpear deja de sentirse ineludible."""

    def test_apply_hit_no_cambia_la_vida(self, _video) -> None:
        pez = EnemyPezAbismal(pygame.Vector2(0, 0))
        vida_antes = pez.current_health
        pez.apply_hit(999.0, (0, 0))
        assert pez.current_health == vida_antes
        assert pez.is_alive is True

    def test_apply_hit_repetido_sigue_sin_matarlo(self, _video) -> None:
        pez = EnemyPezAbismal(pygame.Vector2(0, 0))
        for _ in range(50):
            pez.apply_hit(999.0, (0, 0))
        assert pez.is_alive is True


class TestPersigueConInercia:
    def test_sin_jugador_deriva_sin_reventar(self, _video) -> None:
        pez = EnemyPezAbismal(pygame.Vector2(100, 100))
        for _ in range(60):
            pez.update(1 / 60)
        # No hay excepción, y sigue vivo y sin objetivo.
        assert pez.is_alive is True

    def test_con_jugador_se_acerca(self, _video) -> None:
        # Dentro del alcance de detección (`EnemyFlying` fija 180 px en
        # X) — más lejos, el pez sigue en patrulla y el resultado no
        # dice nada sobre la persecución.
        pez = EnemyPezAbismal(pygame.Vector2(0, 100))
        pez.set_player_ref(pygame.Rect(120, 100, 16, 32))
        distancia_inicial = abs(pez.position.x - 120)
        for _ in range(180):  # 3 s
            pez.update(1 / 60)
        distancia_final = abs(pez.position.x - 120)
        assert distancia_final < distancia_inicial

    def test_entra_en_estado_de_persecucion(self, _video) -> None:
        from src.framework.entities.enemy_base import EnemyState

        pez = EnemyPezAbismal(pygame.Vector2(0, 100))
        pez.set_player_ref(pygame.Rect(50, 100, 16, 32))
        for _ in range(30):
            pez.update(1 / 60)
        assert pez.state in (EnemyState.ALERT, EnemyState.CHASE)


class TestDibujaSinReventar:
    def test_draw_no_revienta(self, _video) -> None:
        pez = EnemyPezAbismal(pygame.Vector2(50, 50))
        surface = pygame.Surface((320, 240))
        pez.draw(surface, pygame.Vector2(0, 0))

    def test_carga_su_propio_sprite_no_el_de_zona(self, _video) -> None:
        """No existe un volador de "zone4" y, de existir, sería un
        halcón/cuervo — no una criatura abisal."""
        pez = EnemyPezAbismal(pygame.Vector2(0, 0))
        assert "fly" in pez._sprite_frames
        assert len(pez._sprite_frames["fly"]) > 0
