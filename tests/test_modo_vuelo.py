"""El modo vuelo: AUD-335 — la física de un juego aéreo, declarada y servida.

`PhysicsProfile.vuelo()` ya era el plan de AUD-333 («el perfil lo declara,
pero el integrador del jugador aún no tiene una integración de vuelo que lo
consuma»). Esta suite es ese consumidor: el jugador lee el `modo` del perfil
para elegir integración — sin gravedad, dos ejes libres, velocidad desde la
entrada, igual que la cenital, porque la física del vuelo ES esa — y el
resolutor trata el vuelo como lo que es: un modo sin suelo, donde las
repisas de un sentido y las cuestas no se resuelven.

Lo que estas pruebas fijan, en hechos:
- el vuelo no cae sin entrada ni acumula velocidad vertical;
- la entrada mueve en los dos ejes a la velocidad del perfil;
- las repisas de un sentido se atraviesan (semántica de plataformas);
- el suelo sólido sigue frenando (la colisión es universal);
- las cuestas no pegan (terreno pintado, como en cenital).
"""
from __future__ import annotations

import pygame
import pytest

from src.engine.input.action_map import Action
from src.engine.input.input_manager import InputManager
from src.framework.entities.player import Player
from src.framework.physics.perfil import VUELO, PhysicsProfile
from src.framework.stage.pendientes import Pendiente

DT = 1.0 / 60.0


@pytest.fixture(autouse=True)
def _video():
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((800, 600))


def _hold(*actions: Action) -> InputManager:
    im = InputManager()
    for action in actions:
        for key in im._bindings.get(action, []):
            im._held.add(key)
    return im


def _en_vuelo(x: float = 100.0, y: float = 100.0) -> Player:
    player = Player(pygame.Vector2(x, y))
    player.perfil = PhysicsProfile.vuelo()
    return player


class TestElPresetVuelo:
    def test_declara_un_modo_sin_gravedad_ni_salto(self) -> None:
        perfil = PhysicsProfile.vuelo()
        assert perfil.modo == VUELO
        assert perfil.gravedad == 0.0
        assert perfil.max_caida == 0.0
        assert perfil.salto_impulso == 0.0
        assert perfil.coyote_frames == 0
        assert perfil.saltos_aereos == 0

    def test_la_velocidad_es_la_declarada_por_el_contexto(self) -> None:
        perfil = PhysicsProfile.vuelo()
        perfil.velocidad_suelo = 300.0
        player = _en_vuelo()
        player.perfil = perfil
        player.update(DT, [], _hold(Action.MOVE_UP))
        assert player.velocity.y == pytest.approx(-300.0)


class TestLaIntegracionDelVuelo:
    def test_sin_entrada_no_cae(self) -> None:
        player = _en_vuelo()
        antes = player.position.y
        for _ in range(120):
            player.update(DT, [])
        assert player.position.y == pytest.approx(antes), (
            "en vuelo sin entrada el jugador cayó: hay gravedad residual"
        )

    def test_arriba_mueve_hacia_arriba(self) -> None:
        player = _en_vuelo()
        player.update(DT, [], _hold(Action.MOVE_UP))
        assert player.velocity.y < 0.0
        assert player.position.y < 100.0

    def test_la_velocidad_vertical_no_acumula(self) -> None:
        """Soltar la tecla frena en el acto: no hay inercia de caída."""
        player = _en_vuelo()
        player.update(DT, [], _hold(Action.MOVE_UP))
        player.update(DT, [])
        assert player.velocity.y == pytest.approx(0.0)

    def test_abajo_es_movimiento_y_no_caida(self) -> None:
        player = _en_vuelo()
        player.update(DT, [], _hold(Action.MOVE_DOWN))
        assert player.velocity.y > 0.0


class TestElVueloContraElMundo:
    def test_atraviesa_las_repisas_de_un_sentido(self) -> None:
        """Las repisas son semántica de plataformas: en vuelo no existen."""
        plat = pygame.Rect(100, 50, 64, 16)
        player = _en_vuelo(y=10.0)
        for _ in range(120):
            player.update(DT, [], _hold(Action.MOVE_DOWN),
                          one_way_rects=[plat])
        assert player.position.y > plat.bottom, (
            "la repisa de un sentido frenó al jugador en vuelo"
        )

    def test_el_suelo_solido_sigue_frenando(self) -> None:
        """La colisión contra sólidos es universal: existe en todo modo.

        No se fija la `y` absoluta: `MOVE_DOWN` dispara CROUCH en la
        máquina de estados y el alto del rect cambia. Lo que importa es
        que los pies descansen en el suelo y no haya túnel.
        """
        suelo = pygame.Rect(0, 300, 400, 200)
        player = _en_vuelo(y=100.0)
        for _ in range(300):
            player.update(DT, [suelo], _hold(Action.MOVE_DOWN))
            if player.rect.bottom >= suelo.top:
                break
        assert player.rect.bottom == suelo.top, (
            "el jugador atravesó o no llegó al suelo sólido volando"
        )
        assert player.velocity.y == pytest.approx(0.0)

    def test_la_cuesta_no_pega_en_vuelo(self) -> None:
        """Sin gravedad la rampa es terreno pintado: ni glue ni aterrizaje."""
        rampa = Pendiente(pygame.Rect(0, 200, 64, 32))
        player = _en_vuelo(x=16.0, y=186.0)
        player._pendientes = [rampa]
        player.update(DT, [], one_way_rects=[])
        assert player.position.y == pytest.approx(186.0), (
            "la cuesta pegó al jugador en vuelo"
        )
