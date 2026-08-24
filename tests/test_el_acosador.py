"""AUD-610 — el `Stalker` (Acosador) estaba implementado de punta a punta y
sin una sola prueba que lo nombrara.

La auditoría mecánica uno a uno (43 tipos del catálogo) lo señaló como el
único sin dueño en `tests/`: cargador (`_handle_componente`, línea 952),
componente (`ecs/components.py::Acosador`) y sistema
(`sistema_acosador`) existían. Lo que nadie fijaba era su contrato:

* persigue al jugador marcado con `EsJugador`;
* es invulnerable siempre — no es una fase, es lo que es;
* si el jugador se aleja más de `distancia_retirada`, se retira
  `reaparicion` segundos;
* vuelve por detrás del jugador (el lado hacia el que NO mira).
"""
from __future__ import annotations

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame
import pytest


@pytest.fixture(scope="module")
def _video() -> None:
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((8, 8))


@pytest.fixture
def mundo(_video):
    from src.framework.ecs.components import EsJugador, Transform
    from src.framework.ecs.world import World

    w = World()
    jugador = w.crear()
    w.poner(jugador, Transform(posicion=pygame.Vector2(400, 300)))
    t_j = w.obtener(jugador, Transform)
    t_j.rect = pygame.Rect(392, 292, 16, 16)
    w.poner(jugador, EsJugador())
    return w


@pytest.fixture
def acosador(mundo):
    from src.framework.ecs.components import Acosador, Salud, Transform

    e = mundo.crear()
    mundo.poner(e, Transform(posicion=pygame.Vector2(360, 300)))
    t = mundo.obtener(e, Transform)
    t.rect = pygame.Rect(352, 292, 16, 16)
    salud = Salud()
    mundo.poner(e, salud)
    mundo.poner(e, Acosador(velocidad=100.0, distancia_retirada=200.0,
                            reaparicion=2.0))
    return e


@pytest.fixture
def transform_jugador(mundo):
    from src.framework.ecs.components import EsJugador, Transform

    entidad = next(iter(mundo.con(EsJugador, Transform)))
    return mundo.obtener(entidad, Transform)


class TestElAcosador:
    def test_persigue_al_jugador(self, mundo, acosador):
        from src.framework.ecs import systems as S
        from src.framework.ecs.components import Transform

        antes = pygame.Vector2(
            mundo.obtener(acosador, Transform).posicion)
        S.sistema_acosador(mundo, 0.1)

        despues = mundo.obtener(acosador, Transform).posicion
        assert despues.distance_to(pygame.Vector2(400, 300)) < \
            antes.distance_to(pygame.Vector2(400, 300))

    def test_es_invulnerable_siempre(self, mundo, acosador):
        from src.framework.ecs import systems as S
        from src.framework.ecs.components import Salud

        S.sistema_acosador(mundo, 0.016)

        assert mundo.obtener(acosador, Salud).invulnerable is True

    def test_si_lo_pierdes_se_retira(self, mundo, acosador,
                                     transform_jugador):
        from src.framework.ecs import systems as S
        from src.framework.ecs.components import Acosador

        # Jugador a 600 px: el triple de la distancia de retirada.
        transform_jugador.rect.center = (1000, 300)

        S.sistema_acosador(mundo, 0.1)

        acos = mundo.obtener(acosador, Acosador)
        assert acos._fuera > 0.0, (
            "con el jugador fuera de alcance el acosador debería haberse "
            "retirado"
        )

    def test_vuelve_por_detras_del_jugador(self, mundo, acosador,
                                           transform_jugador):
        from src.framework.ecs import systems as S
        from src.framework.ecs.components import Acosador, Transform

        transform_jugador.rect.center = (1000, 300)

        S.sistema_acosador(mundo, 0.1)
        acos = mundo.obtener(acosador, Acosador)
        # Agota la retirada: 2.0 s declarados.
        S.sistema_acosador(mundo, acos.reaparicion + 0.05)

        t_a = mundo.obtener(acosador, Transform)
        # El jugador mira a la derecha (viene acercándose desde la izquierda
        # del mapa): la reaparición cae a la IZQUIERDA del centro del jugador.
        assert t_a.posicion.x < transform_jugador.rect.centerx
