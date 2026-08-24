"""AUD-275 — cada fotograma de partículas tiraba diez arreglos a la basura.

Lo que se midió antes de tocar nada
====================================
`ParticleEmitter.update` compactaba con máscara booleana::

    alive = self.life > 0
    self.x = self.x[alive]        # ← arreglo nuevo
    ...                           # ← diez veces
    self._colors = [self._colors[i] for i in idx]   # ← lista de 3.840 en Python

Diez asignaciones de arreglo **por emisor y por fotograma**, más una lista de
Python reconstruida elemento a elemento. Y `emit` hacía otras diez con
`np.concatenate`. El propio AUD-214 lo había visto de refilón —«el color vive
en una lista de tuplas, no en un array»— y lo dejó porque entonces tocaba otra
cosa.

Medido en esta máquina, ráfaga sostenida de 80 partículas por fotograma hasta
3.840 vivas: **0,658 ms/fotograma**.

Qué cambia
----------
Capacidad reservada y un contador de vivas, que es el patrón que
`EnjambreDeBalas` ya usa en este mismo repositorio:

* `emit` escribe en las ranuras libres; sólo se reserva memoria cuando de
  verdad hace falta más capacidad, y doblando, así que es amortizado;
* `update` compacta **en su sitio** con un único arreglo de índices y
  `np.take(..., out=...)`, en vez de diez arreglos nuevos;
* el color pasa a ser un arreglo `(capacidad, 3)` de enteros de 8 bits, así que
  la lista de Python desaparece del bucle de cada fotograma.

Lo que **no** cambia: `BurstConfig.color` sigue siendo una tupla, que es lo que
ven los escenarios. Lo que se reordena es la representación interna.
"""
from __future__ import annotations

import numpy as np
import pygame
import pytest

from src.framework.vfx.particle_system import BurstConfig, ParticleEmitter


@pytest.fixture(autouse=True)
def _video():
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((800, 600))


CONF = BurstConfig(count=40, speed=120.0, lifetime=0.8, size=(2, 4),
                   color=(255, 200, 120))


class TestSigueHaciendoLoMismo:
    def test_emitir_crea_las_particulas(self) -> None:
        em = ParticleEmitter()

        em.emit(400.0, 300.0, CONF)

        assert em.count == CONF.count

    def test_las_particulas_mueren_al_agotar_su_vida(self) -> None:
        em = ParticleEmitter()
        em.emit(400.0, 300.0, CONF)

        for _ in range(120):
            em.update(1 / 60)

        assert em.count == 0

    def test_dos_rafagas_se_acumulan(self) -> None:
        em = ParticleEmitter()

        em.emit(0.0, 0.0, CONF)
        em.emit(10.0, 10.0, CONF)

        assert em.count == CONF.count * 2

    def test_las_vivas_conservan_su_color(self) -> None:
        """La compactación no puede barajar los colores."""
        rojo = BurstConfig(count=5, speed=0.0, lifetime=9.0, size=(2, 2),
                           color=(255, 0, 0))
        azul = BurstConfig(count=5, speed=0.0, lifetime=0.05, size=(2, 2),
                           color=(0, 0, 255))
        em = ParticleEmitter()
        em.emit(0.0, 0.0, azul)          # éstas mueren enseguida
        em.emit(0.0, 0.0, rojo)

        for _ in range(10):
            em.update(1 / 60)

        assert em.count == 5
        assert np.all(em.colores[:em.count, 0] == 255), "quedaron azules vivas"

    def test_limpiar_lo_vacia(self) -> None:
        em = ParticleEmitter()
        em.emit(0.0, 0.0, CONF)

        em.clear()

        assert em.count == 0

    def test_dibujar_no_lanza(self) -> None:
        em = ParticleEmitter()
        em.emit(400.0, 300.0, CONF)
        em.update(1 / 60)

        em.draw(pygame.Surface((800, 600)), pygame.Vector2(0, 0))


class TestYaNoReasignaCadaFotograma:
    def test_los_arreglos_son_los_mismos_objetos_tras_actualizar(self) -> None:
        """La prueba que define el cambio: compactar no crea arreglos nuevos."""
        em = ParticleEmitter()
        em.emit(0.0, 0.0, CONF)
        em.update(1 / 60)
        antes = [id(em.x), id(em.y), id(em.vx), id(em.vy), id(em.life)]

        for _ in range(30):
            em.update(1 / 60)

        assert [id(em.x), id(em.y), id(em.vx), id(em.vy), id(em.life)] == antes

    def test_emitir_dentro_de_la_capacidad_no_reasigna(self) -> None:
        em = ParticleEmitter()
        em.emit(0.0, 0.0, CONF)          # fija una capacidad
        antes = id(em.x)

        em.update(1 / 60)
        em.emit(0.0, 0.0, CONF)

        assert id(em.x) == antes

    def test_el_color_ya_no_es_una_lista_de_python(self) -> None:
        em = ParticleEmitter()
        em.emit(0.0, 0.0, CONF)

        assert isinstance(em.colores, np.ndarray)

    def test_pasarse_de_capacidad_crece_y_no_pierde_nada(self) -> None:
        em = ParticleEmitter()
        grande = BurstConfig(count=500, speed=10.0, lifetime=9.0, size=(2, 2),
                             color=(1, 2, 3))

        for _ in range(6):
            em.emit(0.0, 0.0, grande)

        assert em.count == 3000
        assert np.all(em.colores[:em.count, 0] == 1), "se perdió color al crecer"


class TestElPresupuestoDeFotograma:
    def test_una_rafaga_sostenida_cabe_de_sobra(self) -> None:
        """Base medida antes de AUD-275: 0,658 ms/fotograma con 3.840 vivas.

        El techo es generoso a propósito: esto corre en las máquinas del
        laboratorio y en CI, y una prueba de milisegundos pegada al valor medido
        se vuelve un generador de fallos aleatorios. Lo que vigila es una
        regresión de las gordas — volver a reasignar por fotograma.
        """
        import time

        em = ParticleEmitter()
        for _ in range(120):
            em.emit(400.0, 300.0, CONF)
            em.update(1 / 60)

        t0 = time.perf_counter()
        for _ in range(300):
            em.emit(400.0, 300.0, CONF)
            em.emit(400.0, 300.0, CONF)
            em.update(1 / 60)
        ms = (time.perf_counter() - t0) * 1000.0 / 300

        assert ms < 2.0, f"{ms:.3f} ms/fotograma con {em.count} vivas"
