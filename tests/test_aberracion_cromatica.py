"""AUD-215: la pasada de aberracion cromatica de la tuberia ModernGL.

Estas pruebas NO tocan la GPU. En CI y en cualquier entorno con
`SDL_VIDEODRIVER=dummy` no hay contexto OpenGL, asi que compilar el shader o
renderizar de verdad es imposible. Una prueba marcada `skipif` en ese caso
seria una prueba que nunca falla, y `CLAUDE.md` la considera inutil.

Lo que si es verificable sin GPU, y es lo que se comprueba aqui:

  * el cableado de configuracion (campo nuevo en `GLRenderConfig`),
  * la API de disparo y decaimiento de la intensidad,
  * que con intensidad 0 la pasada NO se ejecuta (coste cero por fotograma),
  * el ORDEN de la pasada dentro de la cadena, con un contexto falso que
    registra que programa se ejecuta y en que posicion,
  * la validez estatica del GLSL que puede comprobarse sin compilador.
"""
from __future__ import annotations

import os
import re

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

from unittest.mock import MagicMock

import pygame
import pytest

from src.engine.core import settings
from src.engine.render import shaders
from src.engine.render.gl_pipeline import GLRenderConfig, GLRenderer

# ── Utilidades: una tuberia con contexto falso ──────────────────────────────


#: Nombre de atributo del programa -> etiqueta legible para las aserciones de
#: orden. El diccionario es la unica fuente de verdad del test sobre que
#: pasadas existen, para que anadir una pasada nueva rompa aqui y no en
#: silencio.
_PROGRAM_ATTRS = {
    "_passthrough_prog": "passthrough",
    # AUD-229 — coloca la escena recien subida (volteo, orden de canales y
    # alfa). AUD-230 — la mitad cara del bloom, a media resolucion.
    "_upload_prog": "upload",
    "_bloom_prog": "bloom",
    "_bloom_extract_prog": "bloom_extract",
    "_lighting_prog": "lighting",
    "_color_grading_prog": "color_grading",
    "_chromatic_aberration_prog": "chromatic_aberration",
    "_vignette_prog": "vignette",
    "_colorblind_prog": "colorblind",
    "_motion_blur_prog": "motion_blur",
}


def _fake_renderer(config: GLRenderConfig) -> tuple[GLRenderer, list[str]]:
    """Devuelve un GLRenderer con contexto falso y la lista donde se registran
    las pasadas ejecutadas, en orden.
    """
    renderer = GLRenderer(config)
    renderer.ctx = MagicMock()
    renderer._quad_vao = MagicMock()
    renderer._screen_texture = MagicMock()

    for fbo_attr in ("_scene_fbo", "_temp_fbo", "_bloom_fbo", "_prev_fbo", "_light_fbo"):
        setattr(renderer, fbo_attr, MagicMock())

    label_by_program: dict[int, str] = {}
    for attr, label in _PROGRAM_ATTRS.items():
        prog = MagicMock()
        # `_run_shader_pass` hace `"scene" in program`; MagicMock devolveria un
        # booleano arbitrario, asi que se fija explicitamente.
        prog.__contains__ = lambda _self, _key: True
        setattr(renderer, attr, prog)
        label_by_program[id(prog)] = label

    executed: list[str] = []

    def _record(program, source_tex, uniforms=None, target_fbo=None):
        executed.append(label_by_program[id(program)])

    renderer._run_shader_pass = _record  # type: ignore[method-assign]
    renderer._initialized = True
    return renderer, executed


def _render_once(renderer: GLRenderer) -> None:
    w, h = settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT
    pygame.display.set_mode((w, h))
    renderer.render(pygame.Surface((w, h)))


# ── Cableado de configuracion ───────────────────────────────────────────────


class TestConfiguracion:
    def test_intensidad_por_defecto_es_cero(self) -> None:
        """Sin impacto no hay efecto: el juego pasa la mayoria de los
        fotogramas sin aberracion y por defecto debe estar apagada."""
        cfg = GLRenderConfig()
        assert cfg.chromatic_aberration_strength == 0.0

    def test_la_intensidad_es_ajustable_por_fotograma(self) -> None:
        cfg = GLRenderConfig(chromatic_aberration_strength=0.5)
        assert cfg.chromatic_aberration_strength == 0.5

    def test_hay_una_tasa_de_decaimiento_configurable(self) -> None:
        cfg = GLRenderConfig()
        assert cfg.chromatic_aberration_decay > 0.0


# ── API de disparo y decaimiento ────────────────────────────────────────────


class TestApiDeDisparo:
    def test_disparar_sube_la_intensidad(self) -> None:
        renderer = GLRenderer()
        renderer.trigger_chromatic_aberration(0.6)
        assert renderer.config.chromatic_aberration_strength == pytest.approx(0.6)

    def test_disparar_no_pisa_un_impacto_mas_fuerte_en_curso(self) -> None:
        """Dos impactos seguidos: el flojo no debe cancelar al fuerte."""
        renderer = GLRenderer()
        renderer.trigger_chromatic_aberration(0.8)
        renderer.trigger_chromatic_aberration(0.2)
        assert renderer.config.chromatic_aberration_strength == pytest.approx(0.8)

    def test_la_intensidad_se_recorta_al_maximo(self) -> None:
        renderer = GLRenderer()
        renderer.trigger_chromatic_aberration(99.0)
        assert renderer.config.chromatic_aberration_strength <= 1.0

    def test_una_intensidad_negativa_no_enciende_el_efecto(self) -> None:
        renderer = GLRenderer()
        renderer.trigger_chromatic_aberration(-1.0)
        assert renderer.config.chromatic_aberration_strength == 0.0

    def test_la_intensidad_decae_con_el_tiempo(self) -> None:
        renderer = GLRenderer()
        renderer.trigger_chromatic_aberration(1.0)
        renderer.update_chromatic_aberration(0.1)
        decaida = renderer.config.chromatic_aberration_strength
        assert 0.0 < decaida < 1.0

    def test_el_decaimiento_llega_exactamente_a_cero(self) -> None:
        """Un decaimiento exponencial puro nunca alcanza 0 y dejaria la pasada
        encendida para siempre a intensidad imperceptible. Debe engancharse a
        0 exacto para que la pasada vuelva a costar nada."""
        renderer = GLRenderer()
        renderer.trigger_chromatic_aberration(1.0)
        for _ in range(600):
            renderer.update_chromatic_aberration(1.0 / 60.0)
        assert renderer.config.chromatic_aberration_strength == 0.0

    def test_actualizar_sin_impacto_no_hace_nada(self) -> None:
        renderer = GLRenderer()
        renderer.update_chromatic_aberration(0.5)
        assert renderer.config.chromatic_aberration_strength == 0.0


# ── Coste cero cuando la intensidad es 0 ────────────────────────────────────


class TestLaPasadaSeSalta:
    def test_intensidad_cero_no_ejecuta_la_pasada(self) -> None:
        cfg = GLRenderConfig(chromatic_aberration_strength=0.0)
        renderer, executed = _fake_renderer(cfg)
        _render_once(renderer)
        assert "chromatic_aberration" not in executed

    def test_intensidad_positiva_ejecuta_la_pasada_una_vez(self) -> None:
        cfg = GLRenderConfig(chromatic_aberration_strength=0.4)
        renderer, executed = _fake_renderer(cfg)
        _render_once(renderer)
        assert executed.count("chromatic_aberration") == 1

    def test_sin_programa_compilado_la_pasada_no_revienta(self) -> None:
        """Si el shader no compilo, la tuberia sigue dibujando sin el efecto."""
        cfg = GLRenderConfig(chromatic_aberration_strength=0.4)
        renderer, executed = _fake_renderer(cfg)
        renderer._chromatic_aberration_prog = None
        _render_once(renderer)
        assert "chromatic_aberration" not in executed

    def test_la_pasada_recibe_la_intensidad_como_uniforme(self) -> None:
        cfg = GLRenderConfig(chromatic_aberration_strength=0.4)
        renderer, _ = _fake_renderer(cfg)
        capturado: dict[str, object] = {}
        prog = renderer._chromatic_aberration_prog

        def _record(program, source_tex, uniforms=None, target_fbo=None):
            if program is prog:
                capturado.update(uniforms or {})

        renderer._run_shader_pass = _record  # type: ignore[method-assign]
        _render_once(renderer)
        assert capturado.get("strength") == pytest.approx(0.4)


# ── Orden dentro de la cadena ───────────────────────────────────────────────


class TestOrdenDeLaCadena:
    @staticmethod
    def _cadena_completa() -> list[str]:
        cfg = GLRenderConfig(
            bloom_enabled=True,
            lighting_enabled=True,
            color_grading_enabled=True,
            vignette_enabled=True,
            colorblind_mode=1,
            motion_blur_enabled=True,
            chromatic_aberration_strength=0.5,
        )
        renderer, executed = _fake_renderer(cfg)
        w, h = settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT
        pygame.display.set_mode((w, h))
        renderer.render(pygame.Surface((w, h)), light_surface=pygame.Surface((w, h)))
        return executed

    def test_va_despues_del_bloom(self) -> None:
        """Antes del bloom, el halo difuminaria las franjas de color y el
        efecto se perderia. Despues, el propio halo se separa en canales, que
        es como se ve un artefacto real de lente."""
        cadena = self._cadena_completa()
        assert cadena.index("chromatic_aberration") > cadena.index("bloom")

    def test_va_despues_de_la_iluminacion(self) -> None:
        """El mapa de luz esta alineado pixel a pixel con la geometria de la
        escena. Si se desplazaran los canales antes, la luz dejaria de casar
        con lo que ilumina."""
        cadena = self._cadena_completa()
        assert cadena.index("chromatic_aberration") > cadena.index("lighting")

    def test_va_antes_de_la_vineta(self) -> None:
        """La aberracion es maxima en los bordes, justo donde la vineta
        oscurece. Si fuese despues, quedarian franjas de color brillando
        encima de las esquinas ya oscurecidas."""
        cadena = self._cadena_completa()
        assert cadena.index("chromatic_aberration") < cadena.index("vignette")

    def test_va_antes_de_la_correccion_de_daltonismo(self) -> None:
        """La correccion de daltonismo remapea el color final que ve el
        jugador. Separar R y B despues reintroduciria exactamente la confusion
        de canales que la correccion existe para compensar."""
        cadena = self._cadena_completa()
        assert cadena.index("chromatic_aberration") < cadena.index("colorblind")

    def test_va_antes_del_motion_blur(self) -> None:
        """El motion blur acumula el fotograma ya compuesto; asi las franjas
        del impacto dejan estela en lugar de aparecer y desaparecer secas."""
        cadena = self._cadena_completa()
        assert cadena.index("chromatic_aberration") < cadena.index("motion_blur")


# ── Validez estatica del GLSL (sin compilador) ──────────────────────────────


class TestFuenteGlsl:
    def test_el_shader_existe(self) -> None:
        assert hasattr(shaders, "chromatic_aberration_frag")

    def test_declara_la_version(self) -> None:
        assert shaders.chromatic_aberration_frag.lstrip().startswith("#version 330")

    def test_declara_los_uniformes_que_la_tuberia_le_pasa(self) -> None:
        """El nombre del uniforme es un contrato entre `gl_pipeline` y el GLSL.
        `_run_shader_pass` ignora en silencio las claves que no existen en el
        programa, asi que una falta de ortografia aqui apagaria el efecto sin
        ningun error visible."""
        src = shaders.chromatic_aberration_frag
        assert re.search(r"uniform\s+sampler2D\s+scene\s*;", src)
        assert re.search(r"uniform\s+float\s+strength\s*;", src)

    def test_tiene_la_interfaz_del_resto_de_pasadas(self) -> None:
        src = shaders.chromatic_aberration_frag
        assert re.search(r"\bin\s+vec2\s+uv\s*;", src)
        assert re.search(r"\bout\s+vec4\s+fragColor\s*;", src)
        assert re.search(r"\bvoid\s+main\s*\(\s*\)", src)

    def test_las_llaves_y_parentesis_estan_balanceados(self) -> None:
        src = shaders.chromatic_aberration_frag
        assert src.count("{") == src.count("}")
        assert src.count("(") == src.count(")")

    def test_separa_los_canales_rojo_y_azul(self) -> None:
        """El efecto es, por definicion, muestrear R y B en coordenadas
        distintas. Un shader que muestrease una sola vez compilaria igual pero
        no seria aberracion cromatica."""
        src = shaders.chromatic_aberration_frag
        muestras = re.findall(r"texture\s*\(\s*scene\s*,", src)
        assert len(muestras) >= 3, "hacen falta al menos tres muestreos: R, G y B"
        assert ".r" in src and ".b" in src

    def test_el_desplazamiento_es_radial_desde_el_centro(self) -> None:
        """Un desplazamiento constante seria un desenfoque de color plano; la
        aberracion de lente crece con la distancia al centro."""
        src = shaders.chromatic_aberration_frag
        assert "0.5" in src, "el centro de la pantalla en coordenadas uv"
        assert re.search(r"\bstrength\b", src)


# ── Liberacion de recursos ──────────────────────────────────────────────────


class TestDestroy:
    def test_destroy_libera_el_programa(self) -> None:
        renderer, _ = _fake_renderer(GLRenderConfig())
        prog = renderer._chromatic_aberration_prog
        renderer.destroy()
        prog.release.assert_called_once()

    def test_destroy_sin_inicializar_no_revienta(self) -> None:
        renderer = GLRenderer()
        renderer.destroy()
        assert not renderer._initialized


# ── Cableado: del impacto a la pasada ────────────────────────────────────


class TestElImpactoLlegaHastaLaPasada:
    """AUD-215 — la pasada existía y nadie la disparaba.

    Escrita y probada no es lo mismo que enchufada: es el modo de fallo que
    AUD-111 encontró en `fog_of_war` y `water_effect`, dos sistemas completos
    que ninguna escena instanciaba. El canal es `gpu_effects`, el mismo que
    usa el bloom, porque una escena de `framework/` no puede alcanzar el
    `GLRenderer` sin acoplarse a que exista contexto GL.
    """

    def setup_method(self) -> None:
        from src.engine.core import gpu_effects
        gpu_effects.reset()

    teardown_method = setup_method

    def test_pedir_y_recoger_un_golpe(self) -> None:
        from src.engine.core import gpu_effects
        assert gpu_effects.consume_chromatic_aberration() == 0.0
        gpu_effects.request_chromatic_aberration(0.6)
        assert gpu_effects.consume_chromatic_aberration() == pytest.approx(0.6)

    def test_recoger_vacia_el_impulso(self) -> None:
        """Si no se vaciara, un golpe reencendería el efecto para siempre."""
        from src.engine.core import gpu_effects
        gpu_effects.request_chromatic_aberration(0.6)
        gpu_effects.consume_chromatic_aberration()
        assert gpu_effects.consume_chromatic_aberration() == 0.0

    def test_dos_golpes_en_un_fotograma_son_el_mas_fuerte(self) -> None:
        from src.engine.core import gpu_effects
        gpu_effects.request_chromatic_aberration(0.3)
        gpu_effects.request_chromatic_aberration(0.8)
        gpu_effects.request_chromatic_aberration(0.4)
        assert gpu_effects.consume_chromatic_aberration() == pytest.approx(0.8)

    def test_la_intensidad_se_sujeta_a_0_1(self) -> None:
        from src.engine.core import gpu_effects
        gpu_effects.request_chromatic_aberration(5.0)
        assert gpu_effects.consume_chromatic_aberration() == 1.0
        gpu_effects.request_chromatic_aberration(-2.0)
        assert gpu_effects.consume_chromatic_aberration() == 0.0

    def test_app_recoge_el_impulso_y_lo_deja_decaer(self) -> None:
        import inspect

        from src.engine.core import app

        fuente = inspect.getsource(app)
        assert "consume_chromatic_aberration" in fuente, (
            "nadie recoge el golpe: la pasada nunca se enciende en el juego"
        )
        assert "trigger_chromatic_aberration" in fuente
        assert "update_chromatic_aberration" in fuente, (
            "sin el decaimiento, el primer impacto deja la lente rota para "
            "el resto de la partida"
        )

    def test_el_juego_lo_pide_al_recibir_dano(self) -> None:
        import inspect

        from src.framework.scenes.stage_parts import senales

        fuente = inspect.getsource(senales)
        assert "request_chromatic_aberration" in fuente, (
            "la pasada está enchufada a la tubería pero ningún suceso del "
            "juego la dispara"
        )
