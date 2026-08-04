"""Pruebas de la pasada de rayos de luz volumétricos (AUD-226).

En este entorno y en CI **no hay contexto OpenGL**: `SDL_VIDEODRIVER=dummy` da
una superficie de software, así que ni se puede compilar el shader ni leer un
píxel de vuelta. Saltar la prueba entera cuando no hay GPU dejaría una prueba
que nunca falla, y `CLAUDE.md` §6 dice por escrito que eso no es una prueba.

La salida es un doble de `moderngl.Context` lo bastante fiel para que
`GLRenderer.render()` se ejecute de principio a fin sin tocar una GPU. Con él
se comprueba lo que de verdad se puede romper sin tarjeta:

* que la pasada esté apagada por defecto y no cueste nada en ese estado,
* que se salte cuando no hay mapa de luz,
* dónde cae en la cadena respecto a bloom y a la iluminación,
* que el mapa de luz se suba **una sola vez** por fotograma aunque lo usen dos
  pasadas,
* y que los uniformes que fija Python existan de verdad en el GLSL — un nombre
  mal escrito lo descarta `_run_shader_pass` en silencio, sin error.

Lo que no se puede comprobar aquí: que el shader compile en un driver real y
que el resultado se vea bien. Eso necesita una máquina con GPU.
"""
from __future__ import annotations

import re
from typing import Any

import pygame
import pytest

from src.engine.core import settings
from src.engine.render import shaders
from src.engine.render.gl_pipeline import GLRenderConfig, GLRenderer

# ── Doble de moderngl ────────────────────────────────────────────────────
#
# Sólo implementa la superficie de la API que `render()` usa. Si el día de
# mañana la tubería empieza a llamar a algo que no está aquí, la prueba falla
# con AttributeError, que es exactamente el aviso que se quiere.

_UNIFORM_RE = re.compile(r"^\s*uniform\s+\w+\s+(\w+)\s*(?:\[\d+\])?\s*;", re.MULTILINE)


class _FakeUniform:
    def __init__(self) -> None:
        self.value: Any = None
        self.written: bytes | None = None

    def write(self, data: bytes) -> None:
        self.written = data


class _FakeProgram:
    """Programa cuyos uniformes son los que declara el GLSL, ni uno más.

    Ésa es la parte que hace útil al doble: `_run_shader_pass` comprueba
    `if key in program` antes de asignar, así que un uniforme mal escrito en
    Python no da error, simplemente no llega. Aquí sí se nota.
    """

    def __init__(self, fragment_shader: str) -> None:
        self.source = fragment_shader
        self.uniforms = {name: _FakeUniform() for name in _UNIFORM_RE.findall(fragment_shader)}
        self.released = False

    def __contains__(self, key: str) -> bool:
        return key in self.uniforms

    def __getitem__(self, key: str) -> _FakeUniform:
        return self.uniforms[key]

    def release(self) -> None:
        self.released = True


class _FakeTexture:
    def __init__(self, size: tuple[int, int]) -> None:
        self.size = size
        self.released = False
        self.bound_to: int | None = None

    def use(self, location: int = 0) -> None:
        self.bound_to = location

    def write(self, data: bytes) -> None:
        pass

    def read(self) -> bytes:
        return b"\x00" * (self.size[0] * self.size[1] * 4)

    def release(self) -> None:
        self.released = True


class _FakeFramebuffer:
    def __init__(self, color_attachments: list[_FakeTexture]) -> None:
        self.color_attachments = color_attachments
        self.released = False

    def use(self) -> None:
        pass

    def release(self) -> None:
        self.released = True


class _FakeBuffer:
    def __init__(self) -> None:
        self.released = False

    def release(self) -> None:
        self.released = True


class _FakeVAO:
    def __init__(self) -> None:
        self.renders = 0

    def render(self, mode: Any = None) -> None:
        self.renders += 1

    def release(self) -> None:
        pass


class _FakeContext:
    """Registro de todo lo que la tubería le pide a la GPU."""

    def __init__(self) -> None:
        self.screen = _FakeFramebuffer([])
        self.blend_func: Any = None
        self.programs: list[_FakeProgram] = []
        self.textures: list[_FakeTexture] = []
        self.buffers: list[_FakeBuffer] = []
        self.clears = 0

    def enable(self, _flags: Any) -> None:
        pass

    def clear(self, *_args: float) -> None:
        self.clears += 1

    def texture(self, size: tuple[int, int], _components: int, **_kw: Any) -> _FakeTexture:
        tex = _FakeTexture(size)
        self.textures.append(tex)
        return tex

    def depth_texture(self, size: tuple[int, int]) -> _FakeTexture:
        return _FakeTexture(size)

    def framebuffer(
        self,
        color_attachments: list[_FakeTexture],
        depth_attachment: _FakeTexture | None = None,
    ) -> _FakeFramebuffer:
        return _FakeFramebuffer(color_attachments)

    def program(self, vertex_shader: str, fragment_shader: str) -> _FakeProgram:
        prog = _FakeProgram(fragment_shader)
        self.programs.append(prog)
        return prog

    def buffer(self, _data: bytes) -> _FakeBuffer:
        # AUD-223 — antes devolvía `object()`. `destroy()` libera ahora los dos
        # búferes del cuadrado, y un `object` pelado no tiene `release`: el
        # doble tiene que parecerse a moderngl también en lo que se suelta, no
        # sólo en lo que se crea.
        buf = _FakeBuffer()
        self.buffers.append(buf)
        return buf

    def vertex_array(self, *_args: Any, **_kw: Any) -> _FakeVAO:
        return _FakeVAO()


def _renderer(config: GLRenderConfig) -> tuple[GLRenderer, _FakeContext, list[str]]:
    """Un `GLRenderer` cableado al doble, con la cadena de pasadas grabada.

    Devuelve también la lista donde se anota, en orden, el nombre del atributo
    del programa que ejecuta cada pasada. Eso es lo que permite afirmar dónde
    cae la pasada de rayos sin inspeccionar el estado interno de un FBO.
    """
    pygame.display.set_mode((64, 64))
    renderer = GLRenderer(config)
    ctx = _FakeContext()
    renderer.ctx = ctx  # type: ignore[assignment]
    w, h = settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT
    renderer._create_fbos(w, h)
    renderer._create_shaders()
    renderer._create_quad(w, h)
    renderer._initialized = True

    orden: list[str] = []
    programa_por_atributo = {
        id(getattr(renderer, nombre)): nombre
        for nombre in vars(renderer)
        if nombre.endswith("_prog") and getattr(renderer, nombre) is not None
    }
    original = renderer._run_shader_pass

    def _espia(program: Any, *args: Any, **kwargs: Any) -> None:
        orden.append(programa_por_atributo.get(id(program), "desconocido"))
        original(program, *args, **kwargs)

    renderer._run_shader_pass = _espia  # type: ignore[method-assign]
    return renderer, ctx, orden


def _superficie() -> pygame.Surface:
    return pygame.Surface((settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT))


# ── Cableado de configuración ────────────────────────────────────────────


class TestConfiguracionDeRayos:
    def test_los_rayos_vienen_apagados(self) -> None:
        """Coste cero mientras nadie los pida: es la exigencia de AUD-226."""
        cfg = GLRenderConfig()
        assert cfg.godray_enabled is False

    def test_el_numero_de_muestras_es_configurable(self) -> None:
        cfg = GLRenderConfig(godray_samples=8)
        assert cfg.godray_samples == 8
        assert GLRenderConfig().godray_samples == shaders.GODRAY_DEFAULT_SAMPLES

    def test_el_glsl_hornea_el_numero_de_muestras_pedido(self) -> None:
        """El bucle radial se compila con la cuenta como constante.

        Un `for` con límite en un uniform es legal en GLSL 330 pero impide al
        compilador desenrollarlo; con la constante horneada el driver puede.
        El precio es que cambiar la cuenta obliga a recompilar, y eso sólo
        pasa en `init()`/`resize()` — de ahí que se compruebe explícitamente.
        """
        fuente = shaders.godray_frag(8)
        assert "const int SAMPLES = 8;" in fuente
        assert "const int SAMPLES = 8;" not in shaders.godray_frag(16)

    def test_las_muestras_no_cambian_el_brillo(self) -> None:
        """`samples` es un mando de calidad, no de exposición.

        Si la acumulación no se normaliza por el número de muestras, subir la
        calidad quema la imagen y hay que retocar la exposición cada vez.
        """
        for n in (8, 32, 64):
            assert "exposure / float(SAMPLES)" in shaders.godray_frag(n)


# ── La pasada dentro de la cadena ────────────────────────────────────────


class TestPasadaDeRayos:
    def test_apagada_no_ejecuta_nada(self) -> None:
        renderer, _ctx, orden = _renderer(GLRenderConfig())
        renderer.render(_superficie(), _superficie())
        assert "_godray_prog" not in orden

    def test_encendida_se_ejecuta_una_vez(self) -> None:
        renderer, _ctx, orden = _renderer(GLRenderConfig(godray_enabled=True))
        renderer.render(_superficie(), _superficie())
        assert orden.count("_godray_prog") == 1

    def test_sin_mapa_de_luz_no_hay_rayos(self) -> None:
        """Los rayos se generan *a partir* del mapa de luz.

        Sin él no hay emisor, y la pasada tiene que saltarse en vez de leer una
        textura sin escribir (que en una GPU real da negro o basura).
        """
        renderer, _ctx, orden = _renderer(GLRenderConfig(godray_enabled=True))
        renderer.render(_superficie(), None)
        assert "_godray_prog" not in orden

    def test_los_rayos_no_dependen_de_la_pasada_de_iluminacion(self) -> None:
        """Encender rayos con la iluminación apagada tiene que funcionar.

        Comparten la textura de luz, no la condición: si la subida del mapa
        cuelga del `if` de la iluminación, este caso se queda a oscuras.
        """
        renderer, _ctx, orden = _renderer(
            GLRenderConfig(godray_enabled=True, lighting_enabled=False),
        )
        renderer.render(_superficie(), _superficie())
        assert "_lighting_prog" not in orden
        assert orden.count("_godray_prog") == 1

    def test_los_rayos_van_despues_de_la_iluminacion(self) -> None:
        """El orden de la cadena, que aquí no es cosmético.

        `lighting_frag` es multiplicativo (`color * light`). Cualquier cosa
        aditiva que se sume *antes* queda multiplicada por el mapa de luz, o
        sea aniquilada justo donde un rayo tiene que verse: en la sombra.
        """
        renderer, _ctx, orden = _renderer(
            GLRenderConfig(godray_enabled=True, lighting_enabled=True, bloom_enabled=True),
        )
        renderer.render(_superficie(), _superficie())
        assert orden.index("_godray_prog") > orden.index("_lighting_prog")
        assert orden.index("_godray_prog") > orden.index("_bloom_prog")

    def test_los_rayos_van_antes_del_grading_y_la_vineta(self) -> None:
        """Un rayo es luz de la escena: se colorea y se viñetea como el resto."""
        renderer, _ctx, orden = _renderer(
            GLRenderConfig(
                godray_enabled=True,
                color_grading_enabled=True,
                vignette_enabled=True,
            ),
        )
        renderer.render(_superficie(), _superficie())
        assert orden.index("_godray_prog") < orden.index("_color_grading_prog")
        assert orden.index("_godray_prog") < orden.index("_vignette_prog")


# ── Coste ────────────────────────────────────────────────────────────────


class TestCosteDeRayos:
    @staticmethod
    def _texturas_de_luz(ctx: _FakeContext) -> list[_FakeTexture]:
        w, h = settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT
        # La textura de escena se crea una vez y se reutiliza con write(); las
        # que se crean durante render() a tamaño completo son las del mapa de
        # luz. Se descuenta la de escena contando sólo a partir del render.
        return [t for t in ctx.textures if t.size == (w, h)]

    def test_el_mapa_de_luz_se_sube_una_sola_vez(self) -> None:
        """Dos pasadas consumidoras, una sola subida por fotograma.

        Subir 800x600x4 B dos veces por fotograma son 1,9 MB extra por el bus
        a 60 fps: 115 MB/s tirados por no reutilizar la textura que ya está.
        """
        renderer, ctx, _orden = _renderer(
            GLRenderConfig(godray_enabled=True, lighting_enabled=True),
        )
        # Un fotograma de calentamiento: la textura de escena se crea en el
        # primer `render()` y se reutiliza con `write()` a partir de ahí, así
        # que medir desde frío contaría también ésa. Lo que esta prueba fija
        # es el coste **por fotograma en régimen**, que es el que se paga
        # 60 veces por segundo.
        renderer.render(_superficie(), _superficie())
        antes = len(self._texturas_de_luz(ctx))
        renderer.render(_superficie(), _superficie())
        creadas = len(self._texturas_de_luz(ctx)) - antes
        # AUD-229 — antes se exigía exactamente 1. Ahora son **0**: la textura
        # del mapa de luz se crea una vez y se reescribe, en vez de crearse y
        # soltarse en cada fotograma (0,46 ms medidos, 27 ms por segundo a 60
        # fps en reservar memoria que ya se tenía). Lo que la prueba defiende
        # sigue siendo lo mismo —que dos pasadas consumidoras no dupliquen la
        # subida—, sólo que el listón bajó.
        assert creadas == 0, (
            f"el mapa de luz se subió {creadas} veces en un fotograma; "
            f"la textura tiene que reutilizarse entre fotogramas"
        )

    def test_la_textura_de_luz_no_se_filtra(self) -> None:
        """AUD-229 — antes se exigía soltarla en cada fotograma.

        Con la textura reutilizada eso sería exactamente lo contrario de lo
        que hay que hacer: soltarla destruiría la que se reescribe. La fuga
        que la prueba original perseguía sigue cubierta, pero por el otro
        lado: no se crea ninguna textura nueva por fotograma, y la única que
        hay se libera en `destroy()`.
        """
        renderer, ctx, _orden = _renderer(
            GLRenderConfig(godray_enabled=True, lighting_enabled=True),
        )
        renderer.render(_superficie(), _superficie())
        renderer.render(_superficie(), _superficie())
        tras_dos = len(self._texturas_de_luz(ctx))
        for _ in range(6):
            renderer.render(_superficie(), _superficie())
        crecimiento = len(self._texturas_de_luz(ctx)) - tras_dos
        renderer.destroy()
        # Se mide el CRECIMIENTO, no el total: en el arranque se crean las de
        # los FBOs y las dos persistentes, y contarlas no dice nada. Lo que
        # delata una fuga es que el número siga subiendo fotograma a fotograma.
        assert crecimiento == 0, (
            f"{crecimiento} texturas nuevas en seis fotogramas: algo se está "
            "creando por fotograma"
        )
        assert renderer._light_texture is None, "destroy() no soltó el mapa de luz"

    def test_apagada_no_sube_el_mapa_de_luz_ni_una_vez(self) -> None:
        """Coste cero de verdad: ni pasada, ni subida, ni conversión."""
        renderer, ctx, _orden = _renderer(
            GLRenderConfig(godray_enabled=False, lighting_enabled=False),
        )
        renderer.render(_superficie(), _superficie())  # calentamiento
        antes = len(self._texturas_de_luz(ctx))
        renderer.render(_superficie(), _superficie())
        assert len(self._texturas_de_luz(ctx)) == antes

    def test_los_rayos_no_reservan_fbo_propio(self) -> None:
        """La pasada se hace con el ping-pong que ya existe.

        Un FBO extra a 800x600 son otros 1,9 MB de VRAM permanentes por una
        pasada que está apagada por defecto.
        """
        base = GLRenderer(GLRenderConfig())
        conrayos = GLRenderer(GLRenderConfig(godray_enabled=True))
        assert {n for n in vars(base) if n.endswith("_fbo")} == {
            n for n in vars(conrayos) if n.endswith("_fbo")
        }


# ── Uniformes ────────────────────────────────────────────────────────────


class TestUniformesDeRayos:
    def test_el_glsl_declara_los_uniformes_que_fija_la_tuberia(self) -> None:
        """Un nombre mal escrito no da error: `_run_shader_pass` lo ignora.

        Por eso se comprueba que cada uniforme que la tubería intenta fijar
        llegó de verdad al programa con un valor distinto de None.
        """
        renderer, _ctx, _orden = _renderer(GLRenderConfig(godray_enabled=True))
        renderer.render(_superficie(), _superficie())
        prog = renderer._godray_prog
        assert prog is not None
        for nombre in ("scene", "lightMap", "lightOrigin", "density",
                       "weight", "decay", "exposure", "emissionThreshold"):
            assert nombre in prog, f"el GLSL de rayos no declara `{nombre}`"
            assert prog[nombre].value is not None, (
                f"la tubería nunca fijó `{nombre}`: el shader usaría basura"
            )

    def test_el_foco_se_pasa_en_coordenadas_de_textura(self) -> None:
        """El origen del abanico es un punto en UV, no en píxeles."""
        renderer, _ctx, _orden = _renderer(
            GLRenderConfig(godray_enabled=True, godray_origin=(0.25, 0.75)),
        )
        renderer.render(_superficie(), _superficie())
        assert renderer._godray_prog is not None
        assert renderer._godray_prog["lightOrigin"].value == pytest.approx((0.25, 0.75))

    def test_el_umbral_de_emision_supera_la_luz_ambiente(self) -> None:
        """`LightSystem` tiene un suelo ambiental (0.3 por defecto).

        Sin restarlo, cada muestra del rayo acumula ese suelo y el efecto deja
        de ser un abanico para ser una neblina aditiva uniforme.
        """
        assert GLRenderConfig().godray_threshold > 0.3


# ── Liberación ───────────────────────────────────────────────────────────


class TestLiberacionDeRayos:
    def test_destroy_libera_el_programa_de_rayos(self) -> None:
        renderer, _ctx, _orden = _renderer(GLRenderConfig(godray_enabled=True))
        prog = renderer._godray_prog
        assert prog is not None
        renderer.destroy()
        assert prog.released

    def test_destroy_sigue_siendo_idempotente(self) -> None:
        renderer, _ctx, _orden = _renderer(GLRenderConfig(godray_enabled=True))
        renderer.destroy()
        renderer.destroy()
        assert not renderer._initialized


# ── Cableado: del TMX y de la luz a la pasada ────────────────────────────


class TestLosRayosLleganDesdeElEscenario:
    """AUD-226 — la pasada necesita un foco, y la tubería no puede saberlo.

    Sólo ve una textura de luz ya compuesta: los focos que la formaron se
    perdieron al mezclarlos. Quien lo sabe es la escena, y por eso el foco
    viaja por `gpu_effects` como un dato más del fotograma.
    """

    def setup_method(self) -> None:
        from src.engine.core import gpu_effects
        gpu_effects.reset()

    teardown_method = setup_method

    def test_publicar_foco_y_fuerza(self) -> None:
        from src.engine.core import gpu_effects
        assert gpu_effects.published_god_rays() is None
        gpu_effects.publish_god_rays((0.25, 0.75), 3.5)
        assert gpu_effects.published_god_rays() == ((0.25, 0.75), 3.5)

    def test_el_fotograma_nuevo_los_apaga(self) -> None:
        from src.engine.core import gpu_effects
        gpu_effects.publish_god_rays((0.5, 0.5), 3.0)
        gpu_effects.begin_frame()
        assert gpu_effects.published_god_rays() is None

    def test_app_los_enciende_y_los_apaga_con_lo_publicado(self) -> None:
        import inspect

        from src.engine.core import app

        fuente = inspect.getsource(app)
        assert "published_god_rays" in fuente, (
            "nadie lee el foco: los rayos no se encienden nunca en el juego"
        )
        assert "godray_enabled" in fuente, (
            "sin apagarlos, el escenario siguiente heredaría los rayos"
        )

    def test_el_tmx_puede_pedirlos(self) -> None:
        from src.framework.stage.stage_loader import StageData

        assert hasattr(StageData("x", None, None, None), "god_rays") or True
        import dataclasses
        campos = {f.name for f in dataclasses.fields(StageData)}
        assert "god_rays" in campos, (
            "no hay forma de que un escenario pida los rayos"
        )

    def test_la_escena_elige_la_luz_que_manda(self) -> None:
        import inspect

        from src.framework.scenes import stage_scene

        fuente = inspect.getsource(stage_scene)
        assert "publish_god_rays" in fuente
        assert "get_current_intensity" in fuente, (
            "el foco tiene que salir de la luz dominante, no de una fija"
        )
