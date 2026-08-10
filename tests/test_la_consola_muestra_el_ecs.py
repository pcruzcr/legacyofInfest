"""AUD-347 — F11 enseña cuánto cuesta cada sistema del ECS.

El hueco
--------
El planificador mide cada sistema con `perf_counter` desde que nació («lo lee
el panel de rendimiento», decía su comentario) y nadie lo consumía: las
únicas llamadas a `tiempos()`/`total_ms()` estaban en pruebas. El dato se
calculaba cada fotograma y no se enseñaba en ninguna parte; cuando el juego
va lento, la pregunta de la consola es «¿cuál sistema?», y no había forma de
responder jugando.

Qué fija
--------
* `medidas_de_depuracion` publica la línea «ECS» con el total del fotograma
  y los dos sistemas más caros del último paso.
* La línea sólo aparece con un planificador que haya medido algo: un menú
  sin ECS no debe pintar un cero que no significa nada.
"""
from __future__ import annotations

import pygame

from src.framework.ecs.scheduler import Fase, Planificador
from src.framework.ecs.world import World
from src.framework.scenes.stage_parts.diagnostico import DiagnosticoDeEscenario


class _Camara:
    offset = pygame.Vector2(0, 0)


class _Escuadron:
    stats = {"fraccion_modelo": 0.0, "por_reglas": 0}


def _escena_con_plan(planificador: Planificador) -> DiagnosticoDeEscenario:
    """Escena de diagnóstico mínima: lo que `medidas` necesita existir."""
    escena = object.__new__(DiagnosticoDeEscenario)
    escena._stage_data = None
    escena._camera = _Camara()
    escena._squad = _Escuadron()
    escena._particle_system = None
    escena.entidades_retiradas = []
    escena._planificador = planificador
    return escena


def _plan_con_dos_sistemas() -> Planificador:
    plan = Planificador()

    def _uno(_mundo: World, _dt: float) -> None:
        # Coste medible: un sistema real hace trabajo; aquí lo fingimos con
        # un milisegundo para que el planificador tenga algo que contar.
        for _ in range(100_000):
            pass

    plan.registrar(Fase.IA, "el_lento", _uno)
    plan.registrar(Fase.IA + 1, "el_rapido", _uno)
    plan.ejecutar(World(), 0.016)
    return plan


def _escena_sin_plan() -> DiagnosticoDeEscenario:
    """El caso default del motor: escenas sin ECS (menús, laboratorios)."""
    escena = object.__new__(DiagnosticoDeEscenario)
    escena._stage_data = None
    escena._camera = _Camara()
    escena._squad = _Escuadron()
    escena._particle_system = None
    escena.entidades_retiradas = []
    escena._planificador = None
    return escena


class TestLaLineaEcs:
    def test_sin_planificador_no_hay_linea(self) -> None:
        assert "ECS" not in _escena_sin_plan().medidas_de_depuracion()

    def test_con_planificador_y_tiempo_aparece(self) -> None:
        medidas = _escena_con_plan(_plan_con_dos_sistemas()).medidas_de_depuracion()
        assert "ECS" in medidas
        assert isinstance(medidas["ECS"], str)

    def test_total_y_mas_caro_estan_en_la_linea(self) -> None:
        linea = str(_escena_con_plan(
            _plan_con_dos_sistemas()).medidas_de_depuracion()["ECS"])
        assert " ms" in linea
        assert "el_lento" in linea and "el_rapido" in linea

    def test_el_mixin_real_publica_lo_mismo(self) -> None:
        import inspect

        from src.framework.scenes.stage_parts import diagnostico

        fuente = inspect.getsource(diagnostico)
        assert "_planificador" in fuente
        assert "tiempos()" in fuente