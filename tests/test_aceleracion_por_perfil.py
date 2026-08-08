"""AUD-336 — aceleración y fricción por perfil: la inercia, declarada.

El perfil declara `aceleracion` (px/s²) y `friccion` (px/s²), y el jugador
las consume en `_aplicar_friccion_y_aceleracion`: la velocidad que fija la
máquina de estados pasa a ser un **objetivo** al que la velocidad real se
acerca a ritmo acotado.

Lo que estas pruebas fijan, en hechos:
- el perfil por defecto no cambia nada: la velocidad ES la del estado;
- con `aceleracion`, la velocidad crece gradualmente hasta la del estado;
- sin entrada, el jugador frena a ritmo de `friccion` (o de `aceleracion`);
- `acercarse_a` (el paso puro) no rebasa el objetivo ni retrocede;
- `set_spawn` deja la inercia en cero.
"""
from __future__ import annotations

import pygame
import pytest

from src.engine.input.action_map import Action
from src.engine.input.input_manager import InputManager
from src.framework.entities.player import Player
from src.framework.physics.perfil import PhysicsProfile
from src.framework.physics.resolucion import acercarse_a

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


def _piso() -> list[pygame.Rect]:
    """El suelo bajo el jugador: sin él, el estado cae a FALLING y la
    velocidad objetivo del andar aéreo es la mitad de la del suelo.

    El borde superior toca EXACTAMENTE los pies del spawn (100+32=132):
    el resolutor aterriza sólo si `prev_bottom <= tile.top + 1`, y un
    solapamiento de 2 px rompe esa condición.
    """
    return [pygame.Rect(0, 132, 1000, 200)]


def _perfil_con(aceleracion: float, friccion: float = 0.0) -> PhysicsProfile:
    perfil = PhysicsProfile.plataformas()
    perfil.aceleracion = aceleracion
    perfil.friccion = friccion
    return perfil


def _jugador(perfil: PhysicsProfile | None = None) -> Player:
    player = Player(pygame.Vector2(100.0, 100.0))
    if perfil is not None:
        player.perfil = perfil
    player.is_grounded = True
    return player


class TestElPasoPuro:
    def test_mueve_hacia_el_objetivo_sin_pasarse(self) -> None:
        assert acercarse_a(0.0, 10.0, 3.0) == 3.0
        assert acercarse_a(9.0, 10.0, 3.0) == 10.0
        assert acercarse_a(0.0, -10.0, 3.0) == -3.0
        assert acercarse_a(-9.0, -10.0, 3.0) == -10.0

    def test_ya_en_el_objetivo_no_se_mueve(self) -> None:
        assert acercarse_a(5.0, 5.0, 3.0) == 5.0

    def test_delta_no_positiva_no_cambia_nada(self) -> None:
        assert acercarse_a(1.0, 5.0, 0.0) == 1.0
        assert acercarse_a(1.0, 5.0, -2.0) == 1.0


class TestElPerfilPorDefectoNoCambiaNada:
    def test_declara_inercia_cero(self) -> None:
        perfil = PhysicsProfile.plataformas()
        assert perfil.aceleracion == 0.0
        assert perfil.friccion == 0.0

    def test_andar_sigue_siendo_instantaneo(self) -> None:
        player = _jugador()
        player.update(DT, _piso(), _hold(Action.MOVE_RIGHT))
        assert player.velocity.x == pytest.approx(player.walk_speed), (
            "con el perfil por defecto la velocidad debe ser la del estado"
        )

    def test_parar_sigue_siendo_instantaneo(self) -> None:
        player = _jugador()
        player.update(DT, _piso(), _hold(Action.MOVE_RIGHT))
        player.update(DT, _piso(), _hold())
        assert player.velocity.x == pytest.approx(0.0), (
            "soltar la entrada no debe dejar inercia con el perfil por defecto"
        )


class TestLaAceleracionPorPerfil:
    def test_la_velocidad_crece_hacia_la_del_estado(self) -> None:
        player = _jugador(_perfil_con(aceleracion=400.0))
        player.update(DT, _piso(), _hold(Action.MOVE_RIGHT))
        assert player.velocity.x < player.walk_speed, (
            "el primer fotograma no puede llegar al objetivo: hay aceleración"
        )
        assert player.velocity.x > 0.0

    def test_alcanza_la_velocidad_del_estado(self) -> None:
        player = _jugador(_perfil_con(aceleracion=400.0))
        for _ in range(240):
            player.update(DT, _piso(), _hold(Action.MOVE_RIGHT))
        assert player.velocity.x == pytest.approx(player.walk_speed, abs=0.01), (
            "la velocidad debe converger a la del estado"
        )

    def test_sin_entrada_frena_a_ritmo_de_aceleracion(self) -> None:
        player = _jugador(_perfil_con(aceleracion=400.0))
        for _ in range(240):
            player.update(DT, _piso(), _hold(Action.MOVE_RIGHT))
        player.update(DT, _piso(), _hold())
        assert 0.0 < player.velocity.x < player.walk_speed, (
            "soltar la entrada debe frenar gradualmente, no en seco"
        )

    def test_con_friccion_declarada_frena_mas_rapido(self) -> None:
        player = _jugador(_perfil_con(aceleracion=400.0, friccion=1600.0))
        for _ in range(240):
            player.update(DT, _piso(), _hold(Action.MOVE_RIGHT))
        for _ in range(5):
            player.update(DT, _piso(), _hold())
        assert player.velocity.x == pytest.approx(0.0, abs=0.01), (
            "a 1600 px/s² (26,67 px/s por fotograma) cinco fotogramas "
            "bastan para detenerse desde 90 px/s"
        )

    def test_sin_aceleracion_friccion_solo_frena(self) -> None:
        """`friccion` sin `aceleracion`: andar es instantáneo, soltar frena."""
        player = _jugador(_perfil_con(aceleracion=0.0, friccion=400.0))
        player.update(DT, _piso(), _hold(Action.MOVE_RIGHT))
        assert player.velocity.x == pytest.approx(player.walk_speed), (
            "sin aceleración, andar sigue siendo instantáneo"
        )
        player.update(DT, _piso(), _hold())
        assert 0.0 < player.velocity.x < player.walk_speed, (
            "pero soltar la entrada ya frena a ritmo de `friccion`"
        )


class TestLaInerciaYLosReposicionamientos:
    def test_set_spawn_deja_la_inercia_en_cero(self) -> None:
        player = _jugador(_perfil_con(aceleracion=400.0))
        for _ in range(240):
            player.update(DT, _piso(), _hold(Action.MOVE_RIGHT))
        player.set_spawn(pygame.Vector2(50.0, 50.0))
        player.update(DT, _piso(), _hold())
        assert player.velocity.x == pytest.approx(0.0), (
            "reaparecer no puede conservar la inercia del fotograma anterior"
        )
