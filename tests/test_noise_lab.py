"""
Module: test_noise_lab
System: tests
Academic Unit: V/VIII

El laboratorio de ruido corría a 3,4 FPS y nadie lo había medido.

Estas pruebas nacen de una medición, no de una sospecha. Al recorrer todas las
teclas de `test_scene_survives_input` la suite se quedaba colgada en
`NoiseLabScene`: cada `update()` tardaba ~295 ms porque `_generate_noise`
recorría 57.600 píxeles con bucles de Python y `_param_changed` nunca volvía a
`False`.

Lo que se prueba aquí:

* **AUD-073** — la bandera se apaga: un `update()` sin teclas no regenera nada.
* **AUD-074** — un mapa completo cabe holgadamente en un fotograma.
* Equivalencia numérica: la versión vectorizada produce **el mismo mapa** que el
  código escalar antiguo, que se conserva abajo como referencia ejecutable. Sin
  esto, "lo hice más rápido" sería indistinguible de "lo rompí más rápido".
* **AUD-075** — Perlin ya no sale medio negro.
"""
from __future__ import annotations

import time

import numpy as np
import pygame
import pytest

from src.engine.scenes.noise_lab_scene import NoiseLabScene


@pytest.fixture(scope="module")
def display():
    pygame.init()
    pygame.font.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((480, 270))
    yield pygame.display.get_surface()


@pytest.fixture
def context(display):
    """El mismo contexto que usa el arnés de humo, para no probar otro juego."""
    from src.engine.audio.audio_manager import AudioManager
    from src.engine.core.event_bus import EventBus
    from src.engine.core.game_context import GameContext
    from src.engine.core.save_manager import SaveManager
    from src.engine.input.input_manager import InputManager
    from src.engine.scene.scene_manager import SceneManager

    ctx = GameContext(
        input_manager=InputManager(),
        audio_manager=AudioManager(),
        scene_manager=None,
        event_bus=EventBus(),
        clock=None,
        save_manager=SaveManager(),
    )
    ctx.scene_manager = SceneManager(ctx)
    return ctx


# ---------------------------------------------------------------------------
# Referencia: el generador escalar original, copiado tal cual.
# ---------------------------------------------------------------------------
def _reference_value_noise(w, h, scale, rng, signed):
    grid_w = grid_h = max(2, int(1.0 / (scale * 2)))
    grid = rng.rand(grid_h + 1, grid_w + 1).astype(np.float32)
    if signed:
        grid = grid * 2.0 - 1.0
    out = np.zeros((h, w), dtype=np.float32)
    for y in range(h):
        for x in range(w):
            fx = x * scale
            fy = y * scale
            gx = int(fx * grid_w)
            gy = int(fy * grid_h)
            lx = (fx * grid_w) - gx
            ly = (fy * grid_h) - gy
            gx = min(gx, grid_w)
            gy = min(gy, grid_h)
            v00 = grid[gy, gx]
            v01 = grid[gy, min(gx + 1, grid_w)]
            v10 = grid[min(gy + 1, grid_h), gx]
            v11 = grid[min(gy + 1, grid_h), min(gx + 1, grid_w)]
            v0 = v00 + (v10 - v00) * ly
            v1 = v01 + (v11 - v01) * ly
            out[y, x] = v0 + (v1 - v0) * lx
    return out


def _reference_dot_grad(gi, x, y):
    grads = [(1, 0), (-1, 0), (0, 1), (0, -1),
             (1, 1), (-1, 1), (1, -1), (-1, -1)]
    gx, gy = grads[gi % 8]
    return gx * x + gy * y


def _reference_perlin(w, h, scale, rng):
    perm = rng.permutation(256).astype(np.int32)
    perm = np.concatenate([perm, perm])
    out = np.zeros((h, w), dtype=np.float32)
    for y in range(h):
        for x in range(w):
            fx = x * scale * 10
            fy = y * scale * 10
            x0 = int(fx)
            y0 = int(fy)
            sx = fx - x0
            sy = fy - y0
            gi00 = perm[(perm[x0 & 255] + y0) & 255] & 7
            gi01 = perm[(perm[x0 & 255] + y0 + 1) & 255] & 7
            gi10 = perm[(perm[(x0 + 1) & 255] + y0) & 255] & 7
            gi11 = perm[(perm[(x0 + 1) & 255] + y0 + 1) & 255] & 7
            n00 = _reference_dot_grad(gi00, sx, sy)
            n01 = _reference_dot_grad(gi01, sx, sy - 1.0)
            n10 = _reference_dot_grad(gi10, sx - 1.0, sy)
            n11 = _reference_dot_grad(gi11, sx - 1.0, sy - 1.0)
            u = sx * sx * (3.0 - 2.0 * sx)
            v = sy * sy * (3.0 - 2.0 * sy)
            nx0 = n00 + (n10 - n00) * u
            nx1 = n01 + (n11 - n01) * u
            out[y, x] = nx0 + (nx1 - nx0) * v
    return out


# Rejilla reducida: la equivalencia es una propiedad de la aritmética, no del
# tamaño, y con 320x180 la referencia escalar tardaría 300 ms por caso.
SMALL_W, SMALL_H = 64, 36


def _como_se_ve(mapa: np.ndarray) -> np.ndarray:
    """El mapa tal y como llega a la pantalla: 8 bits por canal.

    Es la comparación que importa. Un desajuste de 1e-6 en float32 no existe
    para el estudiante que mira la imagen; un desajuste de un nivel de gris sí.
    """
    return (np.clip(mapa, 0.0, 1.0) * 255).astype(np.uint8)


class TestLaVersionVectorizadaCoincideConLaEscalar:
    """Si el mapa cambia, el laboratorio enseña otra cosa distinta.

    Sobre la tolerancia: la versión vectorizada agrupa `x * scale * cells` en
    una sola multiplicación, mientras que la escalar hacía `x * scale` y luego
    `* cells`. En float32 eso desplaza el último bit de la mantisa en algunos
    píxeles —la diferencia máxima medida es 3,5e-06, unas mil veces menor que
    un nivel de gris—. Por eso la comparación exacta se hace sobre la imagen
    de 8 bits, que es lo que se ve.
    """

    @pytest.mark.parametrize("scale", [0.005, 0.05, 0.2, 0.5])
    @pytest.mark.parametrize("signed", [False, True])
    def test_el_ruido_de_valor_es_identico(self, scale, signed):
        esperado = _reference_value_noise(
            SMALL_W, SMALL_H, scale, np.random.RandomState(42), signed)
        obtenido = NoiseLabScene._value_noise(
            SMALL_W, SMALL_H, scale, np.random.RandomState(42), signed=signed)
        assert obtenido.shape == esperado.shape
        np.testing.assert_allclose(obtenido, esperado, rtol=1e-4, atol=1e-5)
        np.testing.assert_array_equal(_como_se_ve(obtenido), _como_se_ve(esperado))

    @pytest.mark.parametrize("scale", [0.005, 0.05, 0.2, 0.5])
    def test_perlin_es_identico(self, scale):
        esperado = _reference_perlin(
            SMALL_W, SMALL_H, scale, np.random.RandomState(7))
        obtenido = NoiseLabScene._perlin_noise(
            SMALL_W, SMALL_H, scale, np.random.RandomState(7))
        np.testing.assert_allclose(obtenido, esperado, rtol=1e-4, atol=1e-5)
        np.testing.assert_array_equal(
            _como_se_ve((obtenido + 1.0) * 0.5), _como_se_ve((esperado + 1.0) * 0.5))

    def test_la_semilla_manda(self):
        """Dos semillas distintas deben dar mapas distintos, la misma el mismo."""
        a = NoiseLabScene._value_noise(
            SMALL_W, SMALL_H, 0.05, np.random.RandomState(1), signed=False)
        b = NoiseLabScene._value_noise(
            SMALL_W, SMALL_H, 0.05, np.random.RandomState(1), signed=False)
        c = NoiseLabScene._value_noise(
            SMALL_W, SMALL_H, 0.05, np.random.RandomState(2), signed=False)
        np.testing.assert_array_equal(a, b)
        assert not np.allclose(a, c)


class TestElMapaSeGeneraUnaSolaVez:
    """AUD-073: la bandera `_param_changed` nunca se apagaba."""

    def test_generar_apaga_la_bandera(self, context):
        escena = NoiseLabScene(context)
        escena.on_enter()
        assert escena._param_changed is True
        escena._generate_noise()
        assert escena._param_changed is False, (
            "sin apagar la bandera, `update()` regenera el mapa en cada fotograma"
        )

    def test_un_update_en_reposo_no_regenera(self, context):
        escena = NoiseLabScene(context)
        escena.on_enter()
        escena.update(1 / 60)          # primer fotograma: sí genera
        primero = escena._cached_noise
        assert primero is not None

        llamadas = {"n": 0}
        original = NoiseLabScene._generate_noise

        def contar(self):
            llamadas["n"] += 1
            return original(self)

        NoiseLabScene._generate_noise = contar
        try:
            for _ in range(60):
                escena.update(1 / 60)
        finally:
            NoiseLabScene._generate_noise = original

        assert llamadas["n"] == 0, (
            f"el mapa se regeneró {llamadas['n']} veces en un segundo sin tocar "
            "ningún parámetro"
        )

    def test_cambiar_un_parametro_si_regenera(self, context):
        escena = NoiseLabScene(context)
        escena.on_enter()
        escena._generate_noise()
        antes = escena._cached_noise.copy()
        escena._seed = 999
        escena._adjust_param(0)        # marca la bandera
        escena.update(1 / 60)
        assert not np.array_equal(antes, escena._cached_noise)


class TestElLaboratorioCabeEnUnFotograma:
    """AUD-074: 295 ms por mapa es un congelamiento visible."""

    PRESUPUESTO_MS = 60.0

    @pytest.mark.parametrize("modo", [0, 1, 2])
    def test_generar_un_mapa_completo_es_rapido(self, context, modo):
        escena = NoiseLabScene(context)
        escena._mode = modo
        escena._generate_noise()       # calentar numpy
        t0 = time.perf_counter()
        escena._generate_noise()
        ms = (time.perf_counter() - t0) * 1000
        assert ms < self.PRESUPUESTO_MS, (
            f"modo {modo}: {ms:.0f} ms por mapa (presupuesto {self.PRESUPUESTO_MS:.0f} ms)"
        )

    def test_el_caso_mas_caro_tambien(self, context):
        """Ocho octavas es el máximo que permite la interfaz."""
        escena = NoiseLabScene(context)
        escena._mode = 2
        escena._octaves = 8
        escena._generate_noise()
        t0 = time.perf_counter()
        escena._generate_noise()
        ms = (time.perf_counter() - t0) * 1000
        assert ms < 150.0, f"fractal con 8 octavas: {ms:.0f} ms"


class TestElMapaEsVisible:
    """Un mapa correcto pero medio negro sigue siendo un mapa roto."""

    @pytest.mark.parametrize("modo", [0, 1, 2])
    def test_el_mapa_usa_el_rango_completo(self, context, modo):
        escena = NoiseLabScene(context)
        escena._mode = modo
        escena._generate_noise()
        mapa = escena._cached_noise
        assert mapa.shape == (NoiseLabScene.NOISE_H, NoiseLabScene.NOISE_W)
        assert 0.0 <= mapa.min() and mapa.max() <= 1.0
        assert mapa.std() > 0.02, f"modo {modo}: mapa casi plano (std={mapa.std():.4f})"

    def test_perlin_no_sale_medio_negro(self, context):
        """AUD-075: el recorte contra [0,1] mataba toda la mitad negativa."""
        escena = NoiseLabScene(context)
        escena._mode = 1
        escena._generate_noise()
        negros = float((escena._cached_noise <= 0.001).mean())
        assert negros < 0.15, (
            f"{negros:.0%} de la imagen es negro plano; Perlin debe remapearse "
            "de [-1,1] a [0,1], no recortarse"
        )

    @pytest.mark.parametrize("modo", [0, 1, 2])
    def test_todos_los_modos_producen_mapas_distintos(self, context, modo):
        escena = NoiseLabScene(context)
        mapas = []
        for m in (0, 1, 2):
            escena._mode = m
            escena._generate_noise()
            mapas.append(escena._cached_noise.copy())
        assert not np.allclose(mapas[0], mapas[1])
        assert not np.allclose(mapas[1], mapas[2])


class TestLaEscenaResisteLosExtremos:
    """Los estudiantes mantienen pulsada la flecha hasta el tope."""

    @pytest.mark.parametrize("modo", [0, 1, 2])
    def test_los_limites_de_cada_parametro_no_rompen_nada(self, context, modo):
        escena = NoiseLabScene(context)
        escena._mode = modo
        for extremo in (-1, 1):
            for idx in range(5):
                escena._param_idx = idx
                for _ in range(60):        # llegar al tope y quedarse ahí
                    escena._adjust_param(extremo)
                escena._generate_noise()
                mapa = escena._cached_noise
                assert np.isfinite(mapa).all(), (
                    f"modo {modo}, parámetro {idx} en el extremo {extremo}: NaN o infinito"
                )
