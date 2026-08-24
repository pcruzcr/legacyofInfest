"""AUD-381 — el cono de visión no miraba si había una pared en medio.

El defecto
==========
`sistema_conos_de_vision` decide con dos cosas: distancia y ángulo. Nada más.
Un vigilante al otro lado de un muro **ve al jugador igual que si el muro no
existiera**, que es exactamente el defecto que AUD-278 arregló para la luz —la
luz atravesaba las paredes— y que aquí seguía abierto para la vista.

Se nota más que en la luz, porque cambia una regla del juego y no un píxel: el
sigilo con muros no funciona, y un nivel diseñado alrededor de esconderse
detrás de algo no se puede hacer.

Lo que hace que esto merezca su propio `AUD`
============================================
La pieza que lo resuelve estaba escrita **para esto**. `RejillaEspacial`
(AUD-276) justificaba su existencia diciendo: «no había forma de preguntar
"¿qué hay **entre** este punto y aquel otro?". Sin eso no se puede hacer la
línea de visión de un guardia». Se construyó `hay_vision()`, se probó, y
después se construyó el guardia sin llamarla.

Es la especie que domina esta fase —algo correcto que nadie consume— con la
vuelta de tuerca de que el consumidor previsto se escribió después y no la
usó. Y es la segunda vez en esta sesión que la rejilla aparece así: AUD-379
midió que su fase amplia no aportaba nada, y dejó dicho que su valor real eran
`rayo()` y `hay_vision()`. Éste es ese valor, cobrado.

Cómo llega la geometría al sistema
==================================
Por recurso del mundo, que es el canal que el ECS ya tiene (`poner_recurso`,
como `reloj_musical`). Un mundo sin ese recurso —una prueba, un escenario que
no publique geometría— se comporta **exactamente como antes**: ve por distancia
y ángulo. Eso mantiene en verde las tres pruebas de sigilo de `test_ecs.py` sin
tocarlas, y es lo correcto además: sin geometría publicada, el sistema no puede
inventarse que hay un muro.
"""
from __future__ import annotations

import pygame
import pytest

from src.framework.ecs import systems as S
from src.framework.ecs.components import (
    Alerta,
    ConoDeVision,
    EsJugador,
    Transform,
)
from src.framework.ecs.world import World
from src.framework.stage.rejilla import RejillaEspacial

FRAME = 1 / 60


@pytest.fixture(scope="module", autouse=True)
def _pygame():
    pygame.init()
    yield


def _guardia(mundo: World) -> int:
    return mundo.crear(
        Transform(pygame.Vector2(100, 100), pygame.Rect(100, 100, 16, 16)),
        ConoDeVision(mira=pygame.Vector2(1, 0), alcance=200.0, semiangulo=30.0),
        Alerta(),
    )


def _jugador(mundo: World, rect: pygame.Rect) -> int:
    return mundo.crear(Transform(pygame.Vector2(rect.topleft), rect), EsJugador())


class TestLaParedTapa:
    def test_un_muro_en_medio_impide_ver(self):
        """El caso que no funcionaba: escondido detrás de algo."""
        m = World()
        g = _guardia(m)
        _jugador(m, pygame.Rect(200, 100, 16, 16))
        muro = pygame.Rect(150, 60, 16, 120)
        m.poner_recurso("geometria", RejillaEspacial([muro]))

        S.sistema_conos_de_vision(m, FRAME)
        assert not m.obtener(g, ConoDeVision).ve_al_jugador, (
            "el vigilante ve al jugador a través de un muro de 16x120 px "
            "puesto justo en medio"
        )

    def test_sin_muro_sigue_viendo(self):
        """El arreglo no puede volver ciego a nadie."""
        m = World()
        g = _guardia(m)
        _jugador(m, pygame.Rect(200, 100, 16, 16))
        m.poner_recurso("geometria", RejillaEspacial([]))

        S.sistema_conos_de_vision(m, FRAME)
        assert m.obtener(g, ConoDeVision).ve_al_jugador

    def test_un_muro_fuera_de_la_linea_no_estorba(self):
        """Una pared que no está entre los dos no tapa nada."""
        m = World()
        g = _guardia(m)
        _jugador(m, pygame.Rect(200, 100, 16, 16))
        lejos = pygame.Rect(150, 300, 16, 120)
        m.poner_recurso("geometria", RejillaEspacial([lejos]))

        S.sistema_conos_de_vision(m, FRAME)
        assert m.obtener(g, ConoDeVision).ve_al_jugador


class TestSinGeometriaSeComportaComoAntes:
    """El contrato de compatibilidad, y por qué es el correcto.

    Sin geometría publicada el sistema no puede saber que hay un muro, así que
    inventarse uno sería peor que no mirar. Además mantiene en verde las tres
    pruebas de sigilo de `test_ecs.py`, que construyen mundos desnudos.
    """

    def test_sin_recurso_ve_por_distancia_y_angulo(self):
        m = World()
        g = _guardia(m)
        _jugador(m, pygame.Rect(200, 100, 16, 16))
        S.sistema_conos_de_vision(m, FRAME)
        assert m.obtener(g, ConoDeVision).ve_al_jugador

    def test_un_recurso_invalido_no_tumba_el_fotograma(self):
        """Una entrega puede publicar cualquier cosa con ese nombre.

        La misma decisión que toma el cargador con un clima mal escrito: el
        estudiante necesita ver su nivel para darse cuenta, no un error de
        arranque.
        """
        m = World()
        g = _guardia(m)
        _jugador(m, pygame.Rect(200, 100, 16, 16))
        m.poner_recurso("geometria", "esto no es una rejilla")
        S.sistema_conos_de_vision(m, FRAME)
        assert m.obtener(g, ConoDeVision).ve_al_jugador


class TestLaEscenaPublicaLaGeometria:
    """El cable trampa: sin esto el arreglo no llega al juego.

    Es la lección de AUD-050 y AUD-347 aplicada por adelantado — la lógica
    puede estar perfecta y no ejecutarse nunca porque nadie la alimenta.
    """

    def test_el_escenario_publica_el_recurso(self):
        import inspect

        from src.framework.scenes.stage_parts import mundo_ecs

        fuente = inspect.getsource(mundo_ecs)
        assert '"geometria"' in fuente, (
            "el escenario no publica la geometría en el mundo ECS: el cono de "
            "visión volverá a ver a través de las paredes"
        )
