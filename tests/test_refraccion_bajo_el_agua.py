"""AUD-216 — la pasada de refracción de la tubería GL.

Aquí no hay contexto OpenGL: `SDL_VIDEODRIVER=dummy` da una superficie de
software, no una GPU, así que ni CI ni el entorno local pueden compilar el
shader ni leer un píxel refractado. Lo que sí es verificable sin GPU —y es
justamente donde esto se tuerce— es todo lo demás:

* la conversión de un rectángulo de pygame a coordenadas UV de la textura GL,
  que lleva el eje Y invertido porque la escena se sube con
  `pygame.image.tostring(..., True)`;
* que la pasada no cueste nada cuando no hay agua en pantalla;
* el orden de la pasada dentro de la cadena;
* que los uniforms que escribe la tubería existan de verdad en el GLSL.

Ninguna de estas pruebas se salta nunca. Una prueba que nunca falla no es una
prueba (CLAUDE.md §6), y una marcada `skipif(no hay GPU)` sería exactamente eso
en esta suite.
"""
from __future__ import annotations

import os
import re
from typing import Any

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

from src.engine.core import settings
from src.engine.render.gl_pipeline import GLRenderConfig, GLRenderer, region_to_gl_uv
from src.engine.render.shaders import refraction_frag

W = settings.INTERNAL_WIDTH
H = settings.INTERNAL_HEIGHT


# ── El eje Y invertido ──────────────────────────────────────────────────


class TestConversionDeCoordenadas:
    """`region_to_gl_uv` es lógica pura: rectángulo de pygame → UV de la textura.

    El contrato: la entrada está en píxeles de la superficie interna, con el
    origen ARRIBA-izquierda (pygame). La salida es (u0, v0, u1, v1) en [0, 1]
    con el origen ABAJO-izquierda (OpenGL), porque la escena se sube volteada.
    """

    def test_una_banda_arriba_en_pygame_queda_arriba_en_uv(self) -> None:
        # Los 150 px superiores de la pantalla de pygame.
        uv = region_to_gl_uv((0, 0, W, 150), W, H)
        assert uv is not None
        u0, v0, u1, v1 = uv
        assert (u0, u1) == (0.0, 1.0)
        # Arriba en pygame es v ALTO en GL. Una implementación sin voltear
        # daría (0.0, 0.25) y pondría el agua en el borde contrario.
        assert v0 == 1.0 - 150 / H
        assert v1 == 1.0
        assert v0 > 0.5

    def test_una_banda_abajo_en_pygame_queda_abajo_en_uv(self) -> None:
        uv = region_to_gl_uv((0, H - 150, W, 150), W, H)
        assert uv is not None
        _, v0, _, v1 = uv
        assert v0 == 0.0
        assert v1 == 150 / H
        assert v1 < 0.5

    def test_las_dos_bandas_son_espejo_la_una_de_la_otra(self) -> None:
        arriba = region_to_gl_uv((0, 0, W, 150), W, H)
        abajo = region_to_gl_uv((0, H - 150, W, 150), W, H)
        assert arriba is not None and abajo is not None
        assert arriba[1] == 1.0 - abajo[3]
        assert arriba[3] == 1.0 - abajo[1]

    def test_la_x_no_se_toca(self) -> None:
        uv = region_to_gl_uv((200, 0, 100, H), W, H)
        assert uv is not None
        assert uv[0] == 200 / W
        assert uv[2] == 300 / W

    def test_acepta_un_rect_de_pygame(self) -> None:
        rect = pygame.Rect(200, 0, 100, H)
        assert region_to_gl_uv(rect, W, H) == region_to_gl_uv((200, 0, 100, H), W, H)

    def test_v0_siempre_es_menor_que_v1(self) -> None:
        for y in (0, 10, H // 3, H - 200, H - 1):
            uv = region_to_gl_uv((0, y, W, 60), W, H)
            assert uv is not None, y
            assert uv[1] < uv[3], y

    def test_la_region_se_recorta_a_la_pantalla(self) -> None:
        # Con la cámara movida el agua se sale por los bordes; el UV debe
        # quedarse dentro de [0, 1] o el shader muestrearía fuera de la textura.
        uv = region_to_gl_uv((-500, -500, W + 2000, H + 2000), W, H)
        assert uv == (0.0, 0.0, 1.0, 1.0)

    def test_una_region_totalmente_fuera_de_pantalla_no_existe(self) -> None:
        assert region_to_gl_uv((-400, 0, 100, H), W, H) is None
        assert region_to_gl_uv((W + 10, 0, 100, H), W, H) is None
        assert region_to_gl_uv((0, H + 10, W, 100), W, H) is None

    def test_una_region_degenerada_no_existe(self) -> None:
        assert region_to_gl_uv((0, 0, 0, H), W, H) is None
        assert region_to_gl_uv((0, 0, W, -5), W, H) is None
        assert region_to_gl_uv(None, W, H) is None


# ── Coste cero cuando no hay agua ───────────────────────────────────────


class TestPlomeriaDeConfiguracion:
    def test_disponible_por_defecto_pero_sin_coste(self) -> None:
        """Antes se exigía `refraction_enabled is False`, y ya no.

        Aquello se escribió cuando la pasada no estaba cableada a nada y
        dejarla apagada era la única forma de que no costara. Con el cableado
        de AUD-216 el interruptor pasó a significar otra cosa: **quién dibuja
        el agua**, el sombreador o `WaterEffect` por CPU. Y la pasada sigue
        sin costar nada mientras ninguna escena publique una región, que es lo
        que comprueba la prueba siguiente.

        Lo que este cambio protege está en el propio `cpu_effects_taken_over()`:
        si el interruptor viniera apagado, la CPU dibujaría sus ondas
        senoidales y el sombreador no haría nada — el agua se vería como antes
        en una máquina con tarjeta, que es justo el fallo de AUD-223.
        """
        cfg = GLRenderConfig()
        assert cfg.refraction_enabled is True
        assert GLRenderer(cfg).refraction_uniforms() is None

    def test_sin_region_no_hay_uniformes(self) -> None:
        r = GLRenderer(GLRenderConfig(refraction_enabled=True))
        assert r.refraction_uniforms() is None

    def test_con_region_pero_desactivada_no_hay_uniformes(self) -> None:
        r = GLRenderer(GLRenderConfig(refraction_enabled=False))
        r.set_refraction_region((0, 400, W, 200))
        assert r.refraction_uniforms() is None

    def test_con_region_y_activada_hay_uniformes(self) -> None:
        r = GLRenderer(GLRenderConfig(refraction_enabled=True))
        r.set_refraction_region((0, 400, W, 200))
        u = r.refraction_uniforms()
        assert u is not None
        assert u["region"] == region_to_gl_uv((0, 400, W, 200), W, H)

    def test_poner_la_region_a_none_la_apaga(self) -> None:
        r = GLRenderer(GLRenderConfig(refraction_enabled=True))
        r.set_refraction_region((0, 400, W, 200))
        assert r.refraction_uniforms() is not None
        r.set_refraction_region(None)
        assert r.refraction_uniforms() is None

    def test_el_tiempo_avanza_con_dt_y_escala_con_la_velocidad(self) -> None:
        cfg = GLRenderConfig(refraction_enabled=True, refraction_speed=2.0)
        r = GLRenderer(cfg)
        r.set_refraction_region((0, 400, W, 200), 0.5)
        primero = r.refraction_uniforms()
        assert primero is not None
        assert primero["time"] == 1.0
        r.set_refraction_region((0, 400, W, 200), 0.25)
        segundo = r.refraction_uniforms()
        assert segundo is not None
        assert segundo["time"] == 1.5

    def test_el_tiempo_no_avanza_solo(self) -> None:
        r = GLRenderer(GLRenderConfig(refraction_enabled=True))
        r.set_refraction_region((0, 400, W, 200))
        r.set_refraction_region((0, 400, W, 200))
        u = r.refraction_uniforms()
        assert u is not None
        assert u["time"] == 0.0


# ── El GLSL y la tubería hablan el mismo idioma ─────────────────────────


class TestContratoDelShader:
    def _uniformes_declarados(self) -> set[str]:
        return set(re.findall(r"^\s*uniform\s+\w+\s+(\w+)\s*;", refraction_frag, re.MULTILINE))

    def test_todo_uniforme_que_escribe_la_tuberia_existe_en_el_glsl(self) -> None:
        r = GLRenderer(GLRenderConfig(refraction_enabled=True))
        r.set_refraction_region((0, 400, W, 200))
        u = r.refraction_uniforms()
        assert u is not None
        declarados = self._uniformes_declarados()
        assert set(u) <= declarados, f"la tubería escribe {set(u) - declarados}, que el GLSL no declara"

    def test_el_shader_desplaza_la_muestra_en_vez_de_pintar_encima(self) -> None:
        # La diferencia entre esto y el `WaterEffect` de CPU es exactamente
        # ésta: aquí la coordenada de muestreo se mueve.
        assert "region" in refraction_frag
        cuerpo = refraction_frag[refraction_frag.index("void main"):]
        assert re.search(r"texture\(\s*scene\s*,\s*(?!uv\s*\))", cuerpo), (
            "el fragment shader debe muestrear la escena en una coordenada desplazada, no en uv"
        )

    def test_declara_la_version_glsl_de_la_tuberia(self) -> None:
        assert refraction_frag.lstrip().startswith("#version 330")


# ── El orden dentro de la cadena ────────────────────────────────────────


class _TexturaFalsa:
    def __init__(self, size: tuple[int, int]) -> None:
        self.size = size

    def write(self, data: Any) -> None: ...
    def use(self, unit: int = 0) -> None: ...
    def release(self) -> None: ...
    def read(self) -> bytes:
        return b""


class _FboFalso:
    def __init__(self, size: tuple[int, int]) -> None:
        self.color_attachments = [_TexturaFalsa(size)]

    def use(self) -> None: ...
    def release(self) -> None: ...


class _CtxFalso:
    def __init__(self, size: tuple[int, int]) -> None:
        self.screen = _FboFalso(size)

    def texture(self, size: tuple[int, int], components: int, data: Any = None,
                dtype: str = "f1") -> _TexturaFalsa:
        return _TexturaFalsa(size)

    def clear(self, *args: float) -> None: ...


def _renderer_instrumentado(cfg: GLRenderConfig) -> tuple[GLRenderer, list[str]]:
    """Un `GLRenderer` con la GPU sustituida por dobles, que anota el orden.

    No compila nada: sólo deja correr `render()` para observar qué programas
    se encadenan y en qué orden. Es lo máximo que se puede comprobar de la
    cadena sin un contexto GL.
    """
    r = GLRenderer(cfg)
    size = (W, H)
    r.ctx = _CtxFalso(size)  # type: ignore[assignment]
    r._initialized = True
    for nombre in ("_scene_fbo", "_temp_fbo", "_bloom_fbo", "_prev_fbo", "_light_fbo"):
        setattr(r, nombre, _FboFalso(size))
    # AUD-229/AUD-230 — `_upload_prog` (la pasada que coloca la escena recién
    # subida) y `_bloom_extract_prog` (la mitad cara del bloom, a media
    # resolución) son programas como los demás: sin ellos en esta lista el
    # renderizador se los salta y la cadena que observa la prueba no es la que
    # corre de verdad.
    for nombre in ("_passthrough_prog", "_upload_prog", "_bloom_prog",
                   "_bloom_extract_prog", "_color_grading_prog", "_vignette_prog",
                   "_motion_blur_prog", "_lighting_prog", "_colorblind_prog", "_refraction_prog"):
        setattr(r, nombre, nombre)

    orden: list[str] = []

    def _anotar(program: Any, source_tex: Any, uniforms: Any = None, target_fbo: Any = None) -> None:
        orden.append(program)

    r._run_shader_pass = _anotar  # type: ignore[method-assign]
    return r, orden


class TestOrdenDeLaCadena:
    @staticmethod
    def _escena() -> pygame.Surface:
        pygame.display.set_mode((W, H))
        return pygame.Surface((W, H))

    def test_sin_region_la_pasada_no_se_ejecuta(self) -> None:
        r, orden = _renderer_instrumentado(GLRenderConfig(refraction_enabled=True))
        r.render(self._escena())
        assert "_refraction_prog" not in orden

    def test_desactivada_la_pasada_no_se_ejecuta(self) -> None:
        r, orden = _renderer_instrumentado(GLRenderConfig(refraction_enabled=False))
        r.set_refraction_region((0, 400, W, 200))
        r.render(self._escena())
        assert "_refraction_prog" not in orden

    def test_con_agua_la_pasada_se_ejecuta_antes_del_bloom(self) -> None:
        # La refracción deforma la escena; el bloom, la iluminación y la
        # viñeta son post-proceso sobre lo ya deformado. Al revés se
        # difuminaría primero y se retorcería el difuminado.
        r, orden = _renderer_instrumentado(GLRenderConfig(refraction_enabled=True))
        r.set_refraction_region((0, 400, W, 200))
        r.render(self._escena())
        assert "_refraction_prog" in orden
        assert orden.index("_refraction_prog") < orden.index("_bloom_prog")

    def test_la_pasada_va_despues_de_subir_la_escena(self) -> None:
        r, orden = _renderer_instrumentado(GLRenderConfig(refraction_enabled=True))
        r.set_refraction_region((0, 400, W, 200))
        r.render(self._escena())
        assert orden[0] == "_passthrough_prog"
        assert orden[1] == "_refraction_prog"

    def test_la_region_no_es_pegajosa_entre_fotogramas(self) -> None:
        # Un escenario sin agua detrás de uno con agua no debe heredarla.
        r, orden = _renderer_instrumentado(GLRenderConfig(refraction_enabled=True))
        r.set_refraction_region((0, 400, W, 200))
        r.render(self._escena())
        assert "_refraction_prog" in orden
        orden.clear()
        r.set_refraction_region(None)
        r.render(self._escena())
        assert "_refraction_prog" not in orden


# ── Cableado: del TMX a la pasada ────────────────────────────────────────


class TestElAguaDelEscenarioLlegaALaPasada:
    """AUD-216 — la pasada existía y ninguna escena publicaba una región.

    Es el fallo de AUD-111 repetido: `fog_of_war` y `water_effect` estuvieron
    meses escritos, documentados y probados sin que nadie los instanciara. Una
    pasada que nadie enciende y una clase que nadie construye fallan igual.
    """

    def setup_method(self) -> None:
        from src.engine.core import gpu_effects
        gpu_effects.reset()

    teardown_method = setup_method

    def test_publicar_una_region_la_deja_disponible(self) -> None:
        from src.engine.core import gpu_effects
        assert gpu_effects.published_water_region() is None
        gpu_effects.publish_water_region((0, 40, 320, 180))
        assert gpu_effects.published_water_region() == (0, 40, 320, 180)

    def test_el_fotograma_nuevo_olvida_el_agua(self) -> None:
        """Sin esto, el estanque del nivel se queda en el menú de pausa."""
        from src.engine.core import gpu_effects
        gpu_effects.publish_water_region((0, 0, 800, 600))
        gpu_effects.begin_frame()
        assert gpu_effects.published_water_region() is None

    def test_app_le_pasa_la_region_al_renderizador(self) -> None:
        import inspect

        from src.engine.core import app

        fuente = inspect.getsource(app)
        assert "published_water_region" in fuente, (
            "nadie lee la región: la pasada de refracción nunca se enciende"
        )
        assert "set_refraction_region" in fuente

    def test_la_escena_publica_en_vez_de_dibujar_las_ondas(self) -> None:
        """Con GL, el agua la pinta el sombreador y `WaterEffect` se calla."""
        import inspect

        from src.framework.scenes import stage_scene

        fuente = inspect.getsource(stage_scene)
        assert "publish_water_region" in fuente
        assert "gpu_effects.WATER in gpu_effects.effects_on_gpu()" in fuente, (
            "la escena dibujaría las ondas de CPU encima de la refracción, "
            "que es la duplicación que AUD-222 quitó del bloom"
        )

    def test_el_agua_esta_en_el_reparto(self) -> None:
        from src.engine.core import gpu_effects
        assert gpu_effects.WATER in gpu_effects.DELEGABLES
