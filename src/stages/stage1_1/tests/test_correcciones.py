"""
Module: test_correcciones
System: stage (student assignment) — stage1_1 «La Entrada»
Academic Unit: N/A
Description: Pruebas de las correcciones que el escenario aplica desde su
propia carpeta a comportamientos defectuosos del motor.

Ninguna toca src/engine ni src/framework: todas verifican código propio de
`Stage1_1_LaEntrada` que compensa el fallo desde fuera.

Ejecutar toda la suite con:
   python -m pytest src/stages/stage1_1/tests/ -v
"""
from __future__ import annotations

import pygame
import pytest

from src.stages.stage1_1.entities.canopy_bird import CanopyBird
from src.stages.stage1_1.entities.jungle_frog import JungleFrog
from src.stages.stage1_1.stage1_1 import Stage1_1_LaEntrada


class _RelojFalso:
    def __init__(self, time_scale: float = 1.0) -> None:
        self.time_scale = time_scale


# ════════════════════════════════════════════════════════════════════
# Bug 1 — la cámara lenta se quedaba pegada para siempre
# ════════════════════════════════════════════════════════════════════
#
# Este escenario llevaba un `restaurar_velocidad` propio que devolvía
# `time_scale` a 1.0 al expirar el hitstop, porque `StageScene.update()`
# capturaba `original_time_scale` al INICIO del fotograma y lo reponía al
# final: como el hitstop dura varios fotogramas, el segundo capturaba el
# valor YA ralentizado y lo devolvía, y el juego se quedaba en cámara lenta
# para siempre tras el primer golpe conectado.
#
# El profesor lo corrigió: `CollisionSystem.update_hitstop` es ahora el
# único dueño de `time_scale`. El parche se retiró.
#
# Lo que queda es esta prueba, y no sobra: si una versión futura del motor
# reintroduce el fallo, quien se entera es este escenario. Verificar la
# propiedad —«al acabar el congelado el reloj vuelve a 1.0»— sigue siendo
# válido aunque quien la cumpla ya no sea código propio.

def test_el_motor_devuelve_la_velocidad_al_acabar_el_hitstop() -> None:
    from src.framework.stage.collision_system import CollisionSystem

    colisiones = CollisionSystem()
    reloj = _RelojFalso(1.0)

    colisiones.trigger_hitstop(0.10)
    colisiones.update_hitstop(0.02, reloj)
    assert reloj.time_scale == pytest.approx(0.0), "durante el hitstop se congela"

    # Se agota el congelado con dt REAL, no escalado: pasarle el escalado es
    # lo que producía el bloqueo permanente (AUD-001 en el motor).
    for _ in range(10):
        colisiones.update_hitstop(0.02, reloj)

    assert reloj.time_scale == pytest.approx(1.0), (
        "al expirar el hitstop el reloj tiene que volver a 1.0; si esto falla, "
        "el motor reintrodujo la cámara lenta permanente"
    )


def test_el_hitstop_se_mantiene_mientras_dura() -> None:
    """El hitstop es un efecto deseado de 4-6 fotogramas al conectar un
    golpe. Solo hay que deshacerlo cuando termina."""
    from src.framework.stage.collision_system import CollisionSystem

    colisiones = CollisionSystem()
    reloj = _RelojFalso(1.0)

    colisiones.trigger_hitstop(0.10)
    colisiones.update_hitstop(0.02, reloj)

    assert colisiones.is_hitstopped
    assert reloj.time_scale == pytest.approx(0.0)


def test_sin_reloj_no_revienta() -> None:
    from src.framework.stage.collision_system import CollisionSystem

    colisiones = CollisionSystem()
    colisiones.trigger_hitstop(0.05)
    colisiones.update_hitstop(0.02, None)


# ════════════════════════════════════════════════════════════════════
# Bug 2 — el jugador nacía en el aire con una partida guardada vieja
# ════════════════════════════════════════════════════════════════════

SOLIDOS = [pygame.Rect(0, 400, 2000, 200)]


def test_un_spawn_apoyado_en_el_suelo_es_valido() -> None:
    pies_en_el_suelo = pygame.Vector2(300, 400 - 32)
    assert Stage1_1_LaEntrada.spawn_es_valido(pies_en_el_suelo, 32, SOLIDOS)


def test_un_spawn_a_poca_altura_sigue_siendo_valido() -> None:
    """Caer 40 px al empezar es aceptable: no hay que ser tan estricto."""
    algo_elevado = pygame.Vector2(300, 400 - 32 - 40)
    assert Stage1_1_LaEntrada.spawn_es_valido(algo_elevado, 32, SOLIDOS)


def test_un_spawn_muy_alto_es_invalido() -> None:
    """El checkpoint guardado apuntaba 269 px por encima del suelo nuevo:
    el jugador aparecía cayendo desde el cielo."""
    en_el_cielo = pygame.Vector2(300, 100)
    assert not Stage1_1_LaEntrada.spawn_es_valido(en_el_cielo, 32, SOLIDOS)


def test_un_spawn_sin_suelo_debajo_es_invalido() -> None:
    fuera_del_mapa = pygame.Vector2(5000, 300)
    assert not Stage1_1_LaEntrada.spawn_es_valido(fuera_del_mapa, 32, SOLIDOS)


def test_un_spawn_bajo_el_suelo_es_invalido() -> None:
    enterrado = pygame.Vector2(300, 560)
    assert not Stage1_1_LaEntrada.spawn_es_valido(enterrado, 32, SOLIDOS)


# ════════════════════════════════════════════════════════════════════
# Bug 3 — el alcance del ataque del motor es de solo 16-26 px
# ════════════════════════════════════════════════════════════════════

def test_el_hurtbox_de_la_rana_cubre_todo_su_cuerpo() -> None:
    """No se puede tocar `player_states.py` para alargar el ataque, pero sí
    hacer que las entidades propias sean lo más golpeables posible: el
    hurtbox cubre el cuerpo entero, sin margen muerto."""
    rana = JungleFrog(pygame.Vector2(100.0, 200.0))
    local = rana._build_hurtbox()

    assert local.x <= 0
    assert local.y <= 0
    assert local.width >= rana.rect.width
    assert local.height >= rana.rect.height


def test_el_hurtbox_del_ave_cubre_todo_su_cuerpo() -> None:
    ave = CanopyBird(
        pygame.Vector2(100.0, 100.0),
        waypoints=[(100.0, 100.0), (200.0, 100.0)],
    )
    local = ave._build_hurtbox()

    assert local.x <= 0
    assert local.y <= 0
    assert local.width >= ave.rect.width
    assert local.height >= ave.rect.height
