"""
Module: test_postprocesado_no_se_duplica
System: tests
Academic Unit: VII

AUD-222 — en una máquina con GPU, el post-procesado se pagaba dos veces.

`App` arranca con `use_gl=True` y `GLRenderer` aplica en la tarjeta bloom,
viñeta, iluminación, corrección de color, desenfoque de movimiento y
daltonismo. Pero `StageScene.draw` llamaba a `PostProcessing.apply(surface)`
**sin mirar si había GL**, y esa misma superficie se subía después como textura
al mismo renderizador. Resultado medido sobre el papel de las dos tuberías:

* **la viñeta se dibujaba dos veces** — la de CPU oscurecía las esquinas, y el
  sombreador volvía a multiplicar por su propia rampa;
* **el bloom se calculaba en la CPU (1,55 ms de los 2,18 del post-procesado,
  según `docs/62_ESTADO_DEL_PROYECTO.md`) para que el sombreador lo repitiera**.

Lo que estas pruebas fijan no es «el bloom desapareció»: es el **reparto**. Un
efecto lo hace la GPU o lo hace la CPU, nunca los dos, y el que no le toca
tiene que seguir funcionando igual en el camino software —que es el único que
existe en CI, en cualquier máquina sin ModernGL (es un extra opcional) y en las
26 entregas de los estudiantes.
"""
from __future__ import annotations

import time

import numpy as np
import pygame
import pytest

from src.engine.core import gpu_effects, user_settings
from src.engine.core import settings as _settings
from src.framework.vfx.post_processing import PostProcessing

ANCHO, ALTO = _settings.INTERNAL_WIDTH, _settings.INTERNAL_HEIGHT
CENTRO_FOCO = (ANCHO // 2 - 100, ALTO // 2)  # dentro de la superficie interna
RADIO_FOCO = 90
FONDO = (40, 40, 50)
ESQUINA = (8, 8)


@pytest.fixture(autouse=True)
def _entorno():
    """Pantalla, preferencias conocidas y reparto limpio entre pruebas.

    El reparto es estado de proceso —lo fija la raíz de composición al arrancar
    y lo lee el post-procesado— así que una prueba que lo deje puesto
    contaminaría a las siguientes.
    """
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((ANCHO, ALTO))
    previas = user_settings.get()
    user_settings.set_settings(user_settings.UserSettings(colorblind_mode="off"))
    gpu_effects.reset()
    yield
    gpu_effects.reset()
    user_settings.set_settings(previas)


@pytest.fixture
def escena() -> pygame.Surface:
    s = pygame.Surface((ANCHO, ALTO))
    s.fill(FONDO)
    pygame.draw.circle(s, (230, 215, 180), CENTRO_FOCO, RADIO_FOCO)
    return s


def _aplicar(escena: pygame.Surface, *, vineta: float = 0.0, bloom: float = 0.0,
             fotogramas: int = 4) -> np.ndarray:
    """Devuelve los píxeles tras varios fotogramas de post-procesado.

    Varios y no uno porque el halo se recalcula cada dos fotogramas: con uno
    solo se mediría el arranque y no el régimen.
    """
    p = PostProcessing()
    p.set_vignette(vineta)
    p.set_base_bloom(bloom)
    for _ in range(fotogramas):
        c = escena.copy()
        p.apply(c)
    return pygame.surfarray.array3d(c).astype(float)


class TestElRepartoEntreLaCpuYLaGpu:
    def test_sin_gpu_el_bloom_lo_sigue_haciendo_la_cpu(self, escena):
        """El camino software es el de CI y el de las entregas. No se toca."""
        sin = _aplicar(escena)
        con = _aplicar(escena, bloom=0.25)
        assert con[CENTRO_FOCO].mean() > sin[CENTRO_FOCO].mean() + 10, (
            "sin GL el bloom tiene que seguir saliendo de la CPU"
        )

    def test_con_gpu_el_bloom_no_se_calcula_por_cpu(self, escena):
        """El defecto: 1,55 ms de halo por CPU que el sombreador repetía."""
        gpu_effects.set_effects_on_gpu({gpu_effects.BLOOM})
        original = pygame.surfarray.array3d(escena).astype(float)
        con = _aplicar(escena, bloom=0.25)
        np.testing.assert_allclose(con, original, atol=1, err_msg=(
            "la CPU sigue dibujando el halo aunque la GPU lo esté haciendo"
        ))

    def test_la_intensidad_del_bloom_viaja_a_la_gpu(self, escena):
        """Delegar no puede ser «apagarlo».

        El bloom de la CPU es dinámico —una ráfaga al cambiar de fase el jefe,
        un valor base por escenario— y el del sombreador venía fijo en la
        configuración. Sin publicar la intensidad, delegar cambiaría un efecto
        que responde al juego por un brillo constante también en los menús.
        """
        gpu_effects.set_effects_on_gpu({gpu_effects.BLOOM})
        _aplicar(escena, bloom=0.25)
        assert gpu_effects.published_bloom() == pytest.approx(0.25), (
            "la GPU no se entera de cuánto bloom pide la escena"
        )

    def test_sin_escena_que_lo_pida_la_gpu_no_pone_bloom(self):
        """`begin_frame` es lo que impide que el título herede el halo del
        nivel anterior: sin reinicio por fotograma, el último valor publicado
        se quedaría encendido en los menús, que no ejecutan post-procesado."""
        gpu_effects.publish_bloom(0.4)
        gpu_effects.begin_frame()
        assert gpu_effects.published_bloom() == 0.0

    def test_la_vineta_delegada_no_se_dibuja_por_cpu(self, escena):
        """El mecanismo es simétrico aunque hoy la viñeta no se delegue."""
        gpu_effects.set_effects_on_gpu({gpu_effects.BLOOM, gpu_effects.VIGNETTE})
        original = pygame.surfarray.array3d(escena).astype(float)
        con = _aplicar(escena, vineta=0.5)
        np.testing.assert_allclose(con, original, atol=1, err_msg=(
            "la viñeta de CPU se sigue dibujando sobre la del sombreador"
        ))

    def test_solo_se_puede_delegar_lo_que_las_dos_tuberias_saben_hacer(self):
        """Un nombre mal escrito no puede degradar en «no delegar nada».

        Es el modo de fallo de AUD-036: el ajuste se guardaba, el filtro leía
        otra variable, y nadie veía nunca un fotograma filtrado.
        """
        with pytest.raises(ValueError, match=r"daltonismo|colorblind"):
            gpu_effects.set_effects_on_gpu({"colorblind"})


class TestLoQueSeQuedaEnLaCpuYPorQue:
    """Cada efecto que NO se delega, con la razón por la que no se delega."""

    def test_el_destello_no_tiene_sombreador_equivalente(self, escena):
        gpu_effects.set_effects_on_gpu({gpu_effects.BLOOM, gpu_effects.VIGNETTE})
        p = PostProcessing()
        p.flash((255, 0, 0), alpha=200, duration=0.5)
        c = escena.copy()
        p.apply(c)
        antes = pygame.surfarray.array3d(escena).astype(float)
        despues = pygame.surfarray.array3d(c).astype(float)
        assert despues[..., 0].mean() > antes[..., 0].mean() + 5, (
            "el destello se ha perdido: no hay pasada de GL que lo haga"
        )

    def test_el_tinte_no_tiene_sombreador_equivalente(self, escena):
        gpu_effects.set_effects_on_gpu({gpu_effects.BLOOM, gpu_effects.VIGNETTE})
        p = PostProcessing()
        p.set_tint((0, 0, 255), 0.5)
        c = escena.copy()
        p.apply(c)
        despues = pygame.surfarray.array3d(c).astype(float)
        antes = pygame.surfarray.array3d(escena).astype(float)
        assert despues[..., 2].mean() > antes[..., 2].mean() + 5

    def test_el_filtro_de_daltonismo_se_queda_en_la_cpu(self, escena):
        """`colorblind_frag` existe, y **nadie le pasa nunca el modo**.

        `App` construye `GLRenderConfig()` sin tocar `colorblind_mode`, que vale
        0 —«off»— y ahí se queda: el sombreador está escrito y jamás se ejecuta.
        Además sus matrices no son las de la CPU (AUD-138), así que enchufarlo
        cambiaría lo que ve un jugador daltónico sin que nadie lo haya mirado en
        una pantalla. Se queda donde está y donde se comprueba.
        """
        from src.engine.render.gl_pipeline import GLRenderConfig

        assert GLRenderConfig().colorblind_mode == 0
        assert "colorblind" not in gpu_effects.DELEGABLES

        user_settings.set_settings(
            user_settings.UserSettings(colorblind_mode="deuteranopia"))
        gpu_effects.set_effects_on_gpu({gpu_effects.BLOOM, gpu_effects.VIGNETTE})
        c = escena.copy()
        PostProcessing().apply(c)
        despues = pygame.surfarray.array3d(c).astype(float)
        antes = pygame.surfarray.array3d(escena).astype(float)
        assert not np.allclose(despues, antes, atol=1), (
            "delegar el bloom y la viñeta ha apagado también el filtro de "
            "daltonismo, que la GPU no está aplicando"
        )


class TestLaConfiguracionDeGlDeclaraQueQuitaDeLaCpu:
    def test_el_reparto_sale_de_las_pasadas_que_estan_encendidas(self):
        """Una sola fuente de verdad: si se enciende la pasada, la CPU se
        calla. Así no hay dos listas que puedan desincronizarse."""
        from src.engine.render.gl_pipeline import GLRenderConfig

        # AUD-216 — el agua entró en el reparto al cablearse la refracción:
        # con GL la dibuja el sombreador y `WaterEffect` se calla.
        assert GLRenderConfig().cpu_effects_taken_over() == {
            gpu_effects.BLOOM, gpu_effects.WATER,
        }
        con_vineta = GLRenderConfig(vignette_enabled=True)
        assert gpu_effects.VIGNETTE in con_vineta.cpu_effects_taken_over()
        sin_nada = GLRenderConfig(bloom_enabled=False, refraction_enabled=False)
        assert sin_nada.cpu_effects_taken_over() == frozenset()

    def test_la_vineta_del_sombreador_viene_apagada(self):
        """No la hace la GPU porque la GPU no sabe cuánta vida le queda al
        jugador: `set_damage_vignette` la sube al recibir daño y la
        configuración de GL es estática. Delegarla apagaría esa señal."""
        from src.engine.render.gl_pipeline import GLRenderConfig

        assert not GLRenderConfig().vignette_enabled

    def test_el_bloom_del_sombreador_no_corre_a_intensidad_cero(self):
        """Con la intensidad publicada por la escena, un menú publica 0. Sin
        esta guarda, la pasada seguiría corriendo con el valor de la
        configuración y pondría halo donde el camino software no pone nada."""
        from src.engine.render.gl_pipeline import GLRenderConfig

        assert GLRenderConfig(bloom_intensity=0.3).bloom_active()
        assert not GLRenderConfig(bloom_intensity=0.0).bloom_active()
        assert not GLRenderConfig(bloom_enabled=False, bloom_intensity=0.3).bloom_active()


class TestLaRaizDeComposicionCablearElReparto:
    """`App` es el único sitio que sabe a la vez si hay GL y qué hace la CPU."""

    def test_app_registra_el_reparto_y_publica_la_intensidad(self):
        import inspect

        from src.engine.core import app

        fuente = inspect.getsource(app)
        assert "gpu_effects.set_effects_on_gpu" in fuente, (
            "nadie declara el reparto: el post-procesado de CPU volvería a "
            "correr entero debajo del de la GPU"
        )
        assert "gpu_effects.begin_frame" in fuente
        assert "published_bloom" in fuente, (
            "el reparto quita el bloom de la CPU y no se lo da a la GPU"
        )
        assert "published_lote_de_sprites" in fuente, (
            "el lote de sprites de GPU (AUD-342) no llega del canal de "
            "gpu_effects al renderer: una escena que lo publique no se "
            "compondría nunca"
        )


class TestLoQueCuestaCadaEfecto:
    """El reparto se decide por coste, así que el coste se mide."""

    def test_la_vineta_por_cpu_es_barata_y_el_bloom_no(self, escena):
        p = PostProcessing()
        p.set_vignette(0.4)
        for _ in range(4):
            p.apply(escena.copy())
        t0 = time.perf_counter()
        for _ in range(60):
            p.apply(escena.copy())
        ms_vineta = (time.perf_counter() - t0) / 60 * 1000

        p2 = PostProcessing()
        p2.set_vignette(0.4)
        p2.set_base_bloom(0.25)
        for _ in range(4):
            p2.apply(escena.copy())
        t0 = time.perf_counter()
        for _ in range(60):
            p2.apply(escena.copy())
        ms_ambos = (time.perf_counter() - t0) / 60 * 1000

        assert ms_ambos > ms_vineta, (
            f"viñeta {ms_vineta:.2f} ms, viñeta+bloom {ms_ambos:.2f} ms: si el "
            "bloom no cuesta nada, delegarlo no compensa la complejidad"
        )
