"""AUD-386 — cada emisor de partículas con su propio azar. Parte de GAP-042b.

Qué falta después de AUD-375 y AUD-385
======================================
Los dos generadores globales ya se siembran, así que la partida **se repite**
mientras nadie toque el código. Lo que no hay es **aislamiento**: los seis
sorteos de `ParticleEmitter` salen del global de NumPy, compartido con todo lo
demás que lo use.

La consecuencia práctica, y es la que cuesta dinero: **añadir una tirada en un
sitio desplaza el resultado de todos los demás**. Una chispa más en el golpe
mueve la dispersión de la lluvia, y una prueba que fije la disposición de las
partículas de un sistema se pone roja porque cambió otro. Por eso hoy las
pruebas que tocan azar se escriben tolerantes, y una prueba tolerante deja
pasar las regresiones pequeñas — que es exactamente el coste que AUD-359 pagó.

Qué fija esta prueba
====================
Que dos emisores no se pisan. Es la propiedad que convierte «reproducible si no
tocas nada» en «reproducible por partes», y la que permite fijar una prueba
sobre un sistema sin atarla al resto del motor.
"""
from __future__ import annotations

import pygame
import pytest

from src.engine.core import azar
from src.framework.vfx.particle_system import ParticleEmitter


@pytest.fixture(scope="module", autouse=True)
def _pygame():
    pygame.init()
    yield


def _emitir(em: ParticleEmitter, count: int = 12) -> list[float]:
    em.emit_directed(
        100.0, 100.0, angle=90, speed=120, count=count, lifetime=1.0,
        size=(2, 4), color=(255, 255, 255),
    )
    n = em.count
    return [round(float(v), 6) for v in em.vx[:n]]


class TestCadaEmisorTieneElSuyo:
    def test_dos_emisores_con_la_misma_semilla_coinciden(self):
        a = ParticleEmitter(rng=azar.generador_numpy(9))
        b = ParticleEmitter(rng=azar.generador_numpy(9))
        assert _emitir(a) == _emitir(b)

    def test_semillas_distintas_dan_resultados_distintos(self):
        a = ParticleEmitter(rng=azar.generador_numpy(1))
        b = ParticleEmitter(rng=azar.generador_numpy(2))
        assert _emitir(a) != _emitir(b)

    def test_un_emisor_no_desplaza_a_otro(self):
        """**La** prueba de este lote.

        Se emite con `a`, luego con `b`, luego otra vez con `a`. La segunda
        tanda de `a` tiene que ser la misma que si `b` no hubiera existido. Con
        el generador global compartido no lo es: las tiradas de `b` consumen
        estado que a `a` le tocaba.
        """
        a = ParticleEmitter(rng=azar.generador_numpy(5))
        _emitir(a)
        segunda_sin_ruido = _emitir(a)

        a2 = ParticleEmitter(rng=azar.generador_numpy(5))
        ruidoso = ParticleEmitter(rng=azar.generador_numpy(99))
        _emitir(a2)
        for _ in range(3):
            _emitir(ruidoso)
        segunda_con_ruido = _emitir(a2)

        assert segunda_con_ruido == segunda_sin_ruido, (
            "las tiradas de otro emisor desplazaron las de éste: el azar "
            "sigue siendo compartido"
        )

    def test_sin_rng_sigue_funcionando(self):
        """Compatibilidad: quien construya un emisor a secas no se entera.

        Lo hacen `ParticleSystem.get_emitter`, `WeatherSystem`, las entregas y
        media suite. Sin `rng` el emisor saca uno derivado del global sembrado,
        así que hereda la reproducibilidad del proceso sin pedir nada.
        """
        azar.sembrar(4242)
        a = ParticleEmitter()
        primera = _emitir(a)
        azar.sembrar(4242)
        b = ParticleEmitter()
        assert _emitir(b) == primera


class TestElGeneradorDeNumpy:
    def test_devuelve_algo_reproducible(self):
        assert (azar.generador_numpy(3).uniform(0, 1, 4).tolist()
                == azar.generador_numpy(3).uniform(0, 1, 4).tolist())

    def test_no_toca_el_global(self):
        """Pedir uno propio no puede mover el azar de quien todavía usa el global."""
        import numpy as np

        azar.sembrar(11)
        esperado = np.random.uniform(0, 1, 3).tolist()

        azar.sembrar(11)
        propio = azar.generador_numpy(77)
        propio.uniform(0, 1, 50)
        assert np.random.uniform(0, 1, 3).tolist() == esperado
