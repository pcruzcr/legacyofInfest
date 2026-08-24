"""AUD-214 — el dibujado de partículas, medido y comparado contra sí mismo.

`ParticleEmitter.draw` se reescribió para leer los arrays de una sola pasada
vectorizada en lugar de indexar numpy partícula a partícula. Un cambio así sólo
vale si se cumplen dos cosas a la vez, y aquí se comprueban las dos:

1. **Que dibuje exactamente lo mismo.** No «parecido»: los mismos bytes. Por
   eso la referencia de este módulo no es una lista de píxeles esperados
   escrita a mano —que sólo diría que el código hace lo que yo creía que
   hacía— sino la **implementación anterior, copiada literalmente**. Si el
   nuevo camino se desvía un píxel, el canal alfa o el recorte, salta.
2. **Que sea más rápido.** El umbral es una *proporción* contra esa misma
   referencia, no un número de milisegundos: los absolutos de esta máquina no
   se transfieren a un runner de CI ni al portátil de un estudiante, pero
   «tarda menos de la mitad que el bucle ingenuo» sí. Es el mismo criterio que
   `tests/benchmarks/test_performance_budget.py` razona en su cabecera.

Sin el cambio, `test_es_mas_rapido_que_el_bucle_ingenuo` compara el bucle
ingenuo consigo mismo y da 1,0×: falla.
"""
from __future__ import annotations

import os
import statistics
import time

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import numpy as np
import pygame
import pytest

from src.framework.vfx.hit_effects import HitEffects
from src.framework.vfx.particle_system import ParticleEmitter

DESTINO = (800, 600)


@pytest.fixture(autouse=True)
def _pygame() -> None:
    if not pygame.get_init():
        pygame.init()


def _dibujo_ingenuo(
    em: ParticleEmitter, surface: pygame.Surface, offset: pygame.Vector2,
) -> None:
    """La implementación previa a AUD-214, palabra por palabra.

    Es el patrón oro de este módulo. No la toques para «modernizarla»: si deja
    de ser la de antes, deja de demostrar nada.

    AUD-275 cambió **dos** cosas que este oráculo tenía que seguir, y sólo dos:
    el color pasó de `_colors[i]` —lista de tuplas— a la fila `i` del arreglo
    `colores`, y las partículas vivas están empaquetadas en `[:count]` en vez
    de ocupar todo el arreglo. Son la misma información leída de otro sitio;
    la aritmética de píxeles de abajo no se ha tocado una coma.
    """
    ox = int(offset.x)
    oy = int(offset.y)
    for i in range(em.count):
        if em.life[i] <= 0 or em.alpha[i] <= 0:
            continue
        sx = int(em.x[i]) - ox
        sy = int(em.y[i]) - oy
        c = (*em.colores[i], min(255, em.alpha[i]))
        sz = max(1, int(em.size[i]))
        pygame.draw.rect(surface, c, (sx - sz // 2, sy - sz // 2, sz, sz))


def _emisor_envejecido(pasos: int = 60) -> ParticleEmitter:
    """Partículas con alfa variado y algunas fuera de la pantalla.

    Emitir y ya está no sirve como caso de prueba: `emit` pone todos los alfa a
    255, así que un fallo en el canal alfa pasaría inadvertido. Aquí se
    intercala `update` para que convivan alfas de todo el rango, y se emite
    también fuera del destino para ejercitar el recorte.
    """
    em = ParticleEmitter()
    rng = np.random.default_rng(7)
    cfgs = [HitEffects.SPARK, HitEffects.BLOOD, HitEffects.PARRY, HitEffects.DEATH]
    for k in range(pasos):
        em.emit(
            float(rng.integers(-40, DESTINO[0] + 40)),
            float(rng.integers(-40, DESTINO[1] + 40)),
            cfgs[k % len(cfgs)],
        )
        em.update(0.02)
    return em


def _bytes_de(
    dibujar, em: ParticleEmitter, flags: int, offset: pygame.Vector2,
    clip: pygame.Rect | None = None,
) -> bytes:
    surface = pygame.Surface(DESTINO, flags)
    surface.fill((13, 17, 23, 255))
    if clip is not None:
        surface.set_clip(clip)
    dibujar(em, surface, offset)
    return bytes(surface.get_view("0").raw)


@pytest.mark.parametrize("flags", [0, pygame.SRCALPHA], ids=["opaco", "srcalpha"])
@pytest.mark.parametrize("offset", [(0, 0), (-37, 91), (120, -45)])
def test_dibuja_los_mismos_pixeles_que_el_bucle_ingenuo(
    flags: int, offset: tuple[int, int],
) -> None:
    em = _emisor_envejecido()
    assert em.count > 100, "el emisor de prueba se quedó sin carga"
    assert len(set(em.alpha.tolist())) > 5, "hacen falta alfas variados"

    off = pygame.Vector2(offset)
    esperado = _bytes_de(_dibujo_ingenuo, em, flags, off)
    obtenido = _bytes_de(ParticleEmitter.draw, em, flags, off)
    assert obtenido == esperado


@pytest.mark.parametrize("flags", [0, pygame.SRCALPHA], ids=["opaco", "srcalpha"])
def test_respeta_el_recorte_igual_que_el_bucle_ingenuo(flags: int) -> None:
    """`set_clip` es el caso donde `blits()` se desviaba; queda cubierto."""
    em = _emisor_envejecido()
    clip = pygame.Rect(100, 100, 300, 200)
    off = pygame.Vector2(0, 0)
    esperado = _bytes_de(_dibujo_ingenuo, em, flags, off, clip)
    obtenido = _bytes_de(ParticleEmitter.draw, em, flags, off, clip)
    assert obtenido == esperado


def test_un_emisor_vacio_no_dibuja_nada() -> None:
    em = ParticleEmitter()
    surface = pygame.Surface(DESTINO)
    surface.fill((13, 17, 23))
    antes = bytes(surface.get_view("0").raw)
    em.draw(surface, pygame.Vector2(0, 0))
    assert bytes(surface.get_view("0").raw) == antes


def _mediana_ms(fn, rondas: int = 25) -> float:
    for _ in range(5):
        fn()
    muestras = []
    for _ in range(rondas):
        inicio = time.perf_counter()
        fn()
        muestras.append((time.perf_counter() - inicio) * 1000.0)
    return statistics.median(muestras)


def test_es_mas_rapido_que_el_bucle_ingenuo() -> None:
    """Con carga de combate, el camino vectorizado tiene que ganar de calle.

    Medido en la máquina de auditoría (i7-6820HQ, Python 3.14.6, pygame-ce
    2.5.7, `SDL_VIDEODRIVER=dummy`): 1,97 ms el bucle ingenuo frente a 0,56 ms
    el vectorizado, 3,5×. El umbral se pone en 1,5× —menos de la mitad de lo
    medido— porque esto corre en runners compartidos donde el ruido manda, y
    lo que tiene que detectar es la vuelta al indexado por partícula, que
    devolvería la proporción a 1,0.
    """
    em = _emisor_envejecido(pasos=90)
    surface = pygame.Surface(DESTINO)
    off = pygame.Vector2(0, 0)

    ingenuo = _mediana_ms(lambda: _dibujo_ingenuo(em, surface, off))
    vectorizado = _mediana_ms(lambda: em.draw(surface, off))

    proporcion = ingenuo / vectorizado
    assert proporcion >= 1.5, (
        f"{em.count} partículas: ingenuo {ingenuo:.3f} ms, "
        f"actual {vectorizado:.3f} ms, sólo {proporcion:.2f}x"
    )
