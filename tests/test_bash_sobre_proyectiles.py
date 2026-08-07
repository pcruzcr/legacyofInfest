"""
Module: test_bash_sobre_proyectiles
System: tests
Academic Unit: II (vectores), III (máquinas de estado)

AUD-305 — el *bash*: golpear un proyectil marcado impulsa al jugador.

Qué es y por qué es opt-in
==========================
Es la pareja del pogo (AUD-134). El pogo convierte una fila de enemigos en un
camino; el *bash* hace lo mismo con lo que te disparan — Hollow Knight, Ori.

La decisión que fija este fichero es que **sólo lo admiten los proyectiles
marcados**. La alternativa —que valiera cualquier proyectil enemigo— es más
simple de aprender y cambia sola la dificultad de los dieciséis mapas ya
calificados: convierte a cada tirador en una plataforma, y con ella vuelve
franqueables huecos que hoy no lo son. Ninguna entrega se toca, y el autor del
escenario decide dónde el *bash* es parte del reto.

Es exactamente la misma forma que tuvo AUD-297 con las pendientes: la mecánica
entra entera, y no se ejecuta en ningún mapa que ya estuviera entregado.

La trampa de la propiedad booleana
==================================
`admite_bash` se declara desde Tiled, y Tiled entrega `"false"` como cadena si
el autor no marca el tipo `bool`. Una cadena no vacía es cierta en Python, así
que sin conversión explícita **escribir «false» encendía la propiedad**. Hay una
prueba para eso: es el peor fallo de los dos posibles, porque el estudiante
concluye que la opción no funciona cuando lo que pasa es que no se puede apagar.
"""
from __future__ import annotations

import pygame
import pytest

from src.framework.entities.enemy_shooter import Projectile
from src.framework.stage.collision_system import (
    BASH_IMPULSO_X,
    BASH_IMPULSO_Y,
    CollisionSystem,
)


@pytest.fixture(autouse=True)
def _pantalla():
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((320, 240))


class _JugadorFalso:
    """Lo mínimo que `_procesar_bash` toca del jugador."""

    def __init__(self) -> None:
        self.rect = pygame.Rect(100, 100, 20, 32)
        self.velocity = pygame.Vector2(0.0, 200.0)
        self.facing_direction = 1
        self._air_dash_count = 2
        self.position = pygame.Vector2(100, 100)


class _EscenarioFalso:
    def __init__(self, *entidades) -> None:
        self.entity_list = list(entidades)


def _proyectil(x: int, y: int, *, admite_bash: bool) -> Projectile:
    return Projectile(
        spawn_position=pygame.Vector2(x, y),
        velocity=pygame.Vector2(-60, 0),
        damage=0.5,
        admite_bash=admite_bash,
    )


class TestSoloLosProyectilesMarcados:
    def test_un_proyectil_normal_no_impulsa(self) -> None:
        """La invariante que protege a los dieciséis mapas entregados: en
        ninguno hay un proyectil marcado, así que en ninguno cambia nada."""
        sistema = CollisionSystem()
        jugador = _JugadorFalso()
        proyectil = _proyectil(140, 140, admite_bash=False)
        antes = pygame.Vector2(jugador.velocity)

        impulsado = sistema._procesar_bash(
            jugador, _EscenarioFalso(proyectil), pygame.Rect(130, 130, 40, 30))

        assert impulsado is False
        assert jugador.velocity == antes
        assert proyectil.is_active, "un proyectil sin marcar no se consume"

    def test_un_proyectil_marcado_impulsa(self) -> None:
        sistema = CollisionSystem()
        jugador = _JugadorFalso()
        proyectil = _proyectil(140, 140, admite_bash=True)

        impulsado = sistema._procesar_bash(
            jugador, _EscenarioFalso(proyectil), pygame.Rect(130, 130, 40, 30))

        assert impulsado is True
        assert jugador.velocity.y == BASH_IMPULSO_Y


class TestLaDireccionDelImpulso:
    def test_golpear_hacia_abajo_lanza_hacia_arriba(self) -> None:
        """El caso del pogo: la caja de golpe por debajo del jugador."""
        sistema = CollisionSystem()
        jugador = _JugadorFalso()
        proyectil = _proyectil(110, 140, admite_bash=True)

        # centery de la caja (145) por debajo del centro del jugador (116).
        sistema._procesar_bash(
            jugador, _EscenarioFalso(proyectil), pygame.Rect(100, 130, 40, 30))

        assert jugador.velocity.y == BASH_IMPULSO_Y
        assert jugador._air_dash_count == 0, (
            "sin recuperar el dash, el segundo proyectil de una cadena queda "
            "fuera de alcance y la mecánica no encadena"
        )

    def test_golpear_de_lado_empuja_hacia_atras(self) -> None:
        sistema = CollisionSystem()
        jugador = _JugadorFalso()
        jugador.facing_direction = 1
        proyectil = _proyectil(130, 105, admite_bash=True)

        # Caja a la altura del pecho: centery (110) por encima del centro (116).
        sistema._procesar_bash(
            jugador, _EscenarioFalso(proyectil), pygame.Rect(120, 100, 30, 20))

        assert jugador.velocity.x == -BASH_IMPULSO_X, (
            "mirando a la derecha, el impulso tiene que ir a la izquierda: en "
            "contra del ataque es lo que se siente como apoyarse"
        )

    def test_el_impulso_no_gana_al_salto(self) -> None:
        """Si el bash subiera más que saltar, el jugador dejaría de saltar. Es
        la misma razón por la que `POGO_IMPULSO` vale -300 y no -380."""
        from src.engine.core import settings

        assert abs(BASH_IMPULSO_Y) < abs(settings.PLAYER_JUMP_FORCE)


class TestElProyectilSeConsume:
    def test_rebotar_sobre_algo_no_deja_ese_algo_encima(self) -> None:
        """Si sobreviviera al golpe, el impulso te dejaría dentro de lo que
        acabas de golpear y te haría daño al fotograma siguiente."""
        sistema = CollisionSystem()
        proyectil = _proyectil(140, 140, admite_bash=True)

        sistema._procesar_bash(
            _JugadorFalso(), _EscenarioFalso(proyectil),
            pygame.Rect(130, 130, 40, 30))

        assert not proyectil.is_active

    def test_no_se_impulsa_dos_veces_con_el_mismo_golpe(self) -> None:
        sistema = CollisionSystem()
        jugador = _JugadorFalso()
        proyectil = _proyectil(140, 140, admite_bash=True)
        escenario = _EscenarioFalso(proyectil)
        caja = pygame.Rect(130, 130, 40, 30)

        assert sistema._procesar_bash(jugador, escenario, caja) is True
        assert sistema._procesar_bash(jugador, escenario, caja) is False


class TestLaPropiedadDesdeTiled:
    def test_la_cadena_false_apaga_la_propiedad(self) -> None:
        """Tiled entrega `"false"` si el autor no marca el tipo `bool`, y una
        cadena no vacía es cierta en Python. Sin conversión, escribir «false»
        encendía el bash."""
        from src.framework.stage.stage_loader import StageLoader

        limpio = StageLoader._parse_entity_props({"admite_bash": "false"})

        assert limpio["admite_bash"] is False

    def test_la_cadena_true_la_enciende(self) -> None:
        from src.framework.stage.stage_loader import StageLoader

        assert StageLoader._parse_entity_props(
            {"admite_bash": "true"})["admite_bash"] is True

    def test_el_tirador_se_la_pasa_a_sus_proyectiles(self) -> None:
        from src.framework.entities.enemy_shooter import EnemyShooter

        tirador = EnemyShooter(pygame.Vector2(0, 0), admite_bash=True)
        tirador._player_ref = pygame.Rect(80, 0, 20, 32)
        assert tirador._fire() is True

        assert tirador._active_projectiles[0].admite_bash is True

    def test_por_defecto_ningun_tirador_lo_admite(self) -> None:
        from src.framework.entities.enemy_shooter import EnemyShooter

        assert EnemyShooter(pygame.Vector2(0, 0)).admite_bash is False
