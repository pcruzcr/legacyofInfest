"""AUD-398 — el azar de los tres últimos módulos, aislado. Cierra GAP-042.

Qué quedaba
===========
`GAP-042` se fue cerrando por partes: AUD-374 dio su generador a
`WorldSimulation`, AUD-375 sembró el global del proceso y lo dejó escrito en el
registro, y AUD-385 corrigió que NumPy mantiene **otro** global que
`random.seed()` no toca. Quedaban tres módulos tirando del `random` de módulo:
`vfx/ambient_particles.py`, `vfx/weather_system.py` y `stage/camera.py`.

Por qué importa si ya estaban sembrados
=======================================
Ésta es la parte que no es obvia, porque desde AUD-375 esos tres **ya eran
reproducibles**: el global está sembrado y sus 46 usos heredan esa
reproducibilidad sin tocarlos.

Lo que no eran es **independientes**. Compartiendo un solo generador, el orden
de las llamadas entre módulos forma parte del resultado: añadir una partícula
de ambiente más desplaza la secuencia que después leen el clima y la cámara, y
la misma semilla pasa a dar otra sacudida. Un determinismo que se rompe al
tocar un módulo vecino no sirve para lo que se pidió —reproducir un fallo desde
un informe, validar el fantasma del speedrun contra una repetición— porque
cualquier cambio en cualquier sitio lo invalida.

`azar.generador()` ya existía para esto y su docstring lo dice: «un sistema que
recibe el suyo se puede fijar en una prueba sin tocar el azar de nadie más».
Esto es aplicarlo a los tres que faltaban.
"""
from __future__ import annotations

import ast
import inspect
import random
from pathlib import Path

import pygame
import pytest

_RAIZ = Path(__file__).resolve().parent.parent

#: Los tres del hueco.
MODULOS = [
    "src.framework.vfx.ambient_particles",
    "src.framework.vfx.weather_system",
    "src.framework.stage.camera",
]


@pytest.fixture(autouse=True)
def _video():
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((320, 240))


def _usos_del_global(nombre_modulo: str) -> list[str]:
    """Llamadas a `random.X(...)` de módulo, por AST.

    Por AST y no por texto: `import random` y el tipo `random.Random | None` de
    la firma son legítimos y un `grep` los contaría como infracciones, que es
    la clase de falso positivo que hace que se desactive la comprobación.
    """
    import importlib

    modulo = importlib.import_module(nombre_modulo)
    arbol = ast.parse(inspect.getsource(modulo))
    malos: list[str] = []
    for n in ast.walk(arbol):
        if (isinstance(n, ast.Call)
                and isinstance(n.func, ast.Attribute)
                and isinstance(n.func.value, ast.Name)
                and n.func.value.id == "random"
                # `random.Random(...)` construye un generador propio: es
                # justamente lo que se quiere, no lo que se persigue.
                and n.func.attr != "Random"):
            malos.append(f"{nombre_modulo}:{n.lineno} random.{n.func.attr}()")
    return malos


@pytest.mark.parametrize("modulo", MODULOS)
def test_ya_no_tiran_del_azar_global(modulo: str) -> None:
    """El cable trampa del hueco."""
    usos = _usos_del_global(modulo)
    assert not usos, (
        f"siguen usando el generador global: {usos}. Compartirlo hace que "
        "añadir azar en un módulo cambie el resultado de los otros, y un "
        "determinismo así no reproduce ningún fallo"
    )


def _sacudida(semilla: int, calentar: object = None) -> list[float]:
    """La secuencia de desplazamientos de una sacudida, fotograma a fotograma.

    Dos cosas que el primer intento se dejó, y las dos hacían que la prueba
    comparase listas de ceros y pasara con el azar roto:

    * `update()` **sale temprano sin objetivo** al que seguir, así que hay que
      darle uno o no llega a sacudir nada.
    * Se lee `_shake_offset` y no `offset`: el segundo es la posición de la
      cámara, y la sacudida se guarda aparte desde BUG-043.
    """
    from src.framework.stage.camera import Camera

    class _Objetivo:
        def __init__(self) -> None:
            self.rect = pygame.Rect(400, 300, 20, 30)
            self.velocity = pygame.Vector2(0, 0)

    cam = Camera(rng=random.Random(semilla))
    cam.set_map_size(4000, 2000)
    cam.follow(_Objetivo())
    cam.apply_shake(8.0, 0.5)
    salida: list[float] = []
    for _ in range(20):
        cam.update(1 / 60)
        salida.append(round(cam._shake_offset.x, 6))
    return salida


class TestLaCamara:
    def test_la_misma_semilla_da_la_misma_sacudida(self) -> None:
        assert _sacudida(1234) == _sacudida(1234)

    def test_semillas_distintas_dan_sacudidas_distintas(self) -> None:
        """Sin esto, «siempre devuelve lo mismo» pasaría la prueba de arriba.

        Y no es hipotético: el primer intento leía `cam.offset.x`, que sin
        objetivo al que seguir vale 0,0 siempre, así que las dos pruebas
        comparaban listas de ceros y pasaban con el azar roto. La sacudida se
        lee de `_shake_offset`, que es donde está.
        """
        assert _sacudida(1) != _sacudida(2)


class TestElAislamiento:
    """Lo que de verdad compra el lote: que un módulo no mueva al de al lado."""

    def test_gastar_azar_en_las_particulas_no_cambia_la_camara(self) -> None:
        from src.framework.vfx.ambient_particles import AmbientParticleSystem

        def sacudida(con_particulas: bool) -> list[float]:
            if con_particulas:
                # Un vecino consumiendo azar a base de bien.
                particulas = AmbientParticleSystem(rng=random.Random(7))
                particulas.set_effect("dust", rate=60.0)
                for _ in range(30):
                    particulas.update(1 / 60, pygame.Vector2(0, 0))
            return _sacudida(99)

        assert sacudida(False) == sacudida(True), (
            "las partículas de ambiente desplazaron la secuencia de la cámara: "
            "los dos siguen compartiendo generador, y entonces cualquier "
            "cambio en un módulo invalida la reproducibilidad del otro"
        )


class TestElClima:
    def test_la_misma_semilla_da_el_mismo_viento(self) -> None:
        from src.framework.vfx.weather_system import WeatherSystem

        uno = WeatherSystem("storm", rng=random.Random(5))
        otro = WeatherSystem("storm", rng=random.Random(5))
        assert uno._wind == otro._wind

    def test_sin_semilla_sigue_funcionando(self) -> None:
        """El camino normal del juego: nadie le pasa generador."""
        from src.framework.vfx.weather_system import WeatherSystem

        assert WeatherSystem("rain") is not None
