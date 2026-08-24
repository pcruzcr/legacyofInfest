"""
Module: test_cada_pasada_ejecuta_su_shader
System: tests
Academic Unit: VII

AUD-223 — la tubería de GPU ejecutaba el sombreador de copia en todas las
pasadas, y por eso no hacía absolutamente nada.

`_create_quad` construía **un** `VertexArray` con `_passthrough_prog`:

    self._quad_vao = ctx.vertex_array(self._passthrough_prog, ...)

y `_run_shader_pass(program, ...)` fijaba los uniformes de `program` —el del
bloom, el de la viñeta, el de la iluminación…— para después dibujar
`self._quad_vao`. En moderngl el programa **vive dentro del VertexArray**: es
el que se ejecuta al llamar a `render()`, y el argumento `program` no influía
en nada. Ocho pasadas, un solo sombreador ejecutado, y era el que copia la
imagen tal cual.

Medido en la máquina de auditoría (Intel HD Graphics 530, OpenGL 4.6, contexto
real, no `SDL_VIDEODRIVER=dummy`): encendiendo bloom, iluminación, viñeta,
aberración cromática, refracción o rayos de luz, la imagen final salía **byte
a byte idéntica** a no encender ninguna —diferencia media 0,000, pico 0—. Tras
el arreglo, las seis cambian la imagen (diferencia media de 0,144 el bloom a
55,264 los rayos).

Nadie lo notó en cinco meses porque los mismos efectos existen por CPU en
`framework/vfx/post_processing.py`, y ésos sí se dibujaban: la pantalla se veía
bien y lo que la tarjeta aportaba era exactamente nada, cobrando una pasada de
pantalla completa por efecto.

Por qué esta prueba y no una de píxeles
---------------------------------------
Una prueba de píxeles necesitaría GPU, y en CI no la hay: `SDL_VIDEODRIVER=dummy`
no da contexto OpenGL. Lo que sí se puede fijar sin tarjeta es la propiedad que
falló: **cada pasada tiene que dibujar con el VAO de su propio programa**. Es
la causa, no el síntoma, y se comprueba en cualquier runner.
"""
from __future__ import annotations

from typing import Any

import pygame
import pytest

from src.engine.core import settings
from src.engine.render.gl_pipeline import GLRenderConfig, GLRenderer


def _nombre_del_shader(fuente: str) -> str:
    """El nombre de la constante de `shaders.py` que tiene este GLSL.

    Se resuelve contra el módulo real en vez de recortar el fuente: así el
    mensaje de un fallo dice «bloom_frag» y no treinta caracteres de GLSL, y
    además se cae solo si alguien renombra una constante.
    """
    from src.engine.render import shaders

    for nombre in dir(shaders):
        valor = getattr(shaders, nombre)
        if isinstance(valor, str) and valor == fuente:
            return nombre
    return f"desconocido:{fuente[:40]!r}"


class _Uniforme:
    def __init__(self) -> None:
        self.value: Any = None

    def write(self, data: bytes) -> None:
        self.value = data


class _Programa:
    def __init__(self, nombre: str) -> None:
        self.nombre = nombre
        self._uniformes: dict[str, _Uniforme] = {}

    def __contains__(self, key: str) -> bool:
        return True

    def __getitem__(self, key: str) -> _Uniforme:
        return self._uniformes.setdefault(key, _Uniforme())

    def release(self) -> None:
        pass


class _VAO:
    """Un VAO recuerda con qué programa se construyó — como el de moderngl."""

    def __init__(self, programa: _Programa) -> None:
        self.programa = programa
        self.dibujados: list[str] = []

    def render(self, _modo: Any = None) -> None:
        self.dibujados.append(self.programa.nombre)

    def release(self) -> None:
        pass


class _Textura:
    def __init__(self, size: tuple[int, int]) -> None:
        self.size = size

    def use(self, _loc: int = 0) -> None:
        pass

    def write(self, _d: bytes) -> None:
        pass

    def read(self) -> bytes:
        return b"\x00" * (self.size[0] * self.size[1] * 4)

    def release(self) -> None:
        pass


class _Buffer:
    def release(self) -> None:
        pass


class _FBO:
    def __init__(self, color_attachments: list[_Textura]) -> None:
        self.color_attachments = color_attachments

    def use(self) -> None:
        pass

    def release(self) -> None:
        pass


class _Contexto:
    def __init__(self) -> None:
        self.screen = _FBO([])
        self.blend_func: Any = None
        self.ejecutados: list[str] = []
        self._vaos: list[_VAO] = []

    def enable(self, _f: Any) -> None:
        pass

    def clear(self, *_a: float) -> None:
        pass

    def texture(self, size: tuple[int, int], _c: int, **_kw: Any) -> _Textura:
        return _Textura(size)

    def depth_texture(self, size: tuple[int, int]) -> _Textura:
        return _Textura(size)

    def framebuffer(self, color_attachments: list[_Textura],
                    depth_attachment: _Textura | None = None) -> _FBO:
        return _FBO(color_attachments)

    def program(self, vertex_shader: str, fragment_shader: str) -> _Programa:
        return _Programa(_nombre_del_shader(fragment_shader))

    def buffer(self, _data: bytes) -> _Buffer:
        return _Buffer()

    def copy_framebuffer(self, _dst: _FBO, _src: _FBO) -> None:
        # AUD-236 — el desenfoque de movimiento guarda el fotograma para el
        # siguiente copiándolo **dentro de la tarjeta**. Antes lo bajaba a la
        # CPU con `read()` y lo volvía a subir, y eso costaba 5,45 ms.
        pass

    def vertex_array(self, program: _Programa, *_a: Any, **_kw: Any) -> _VAO:
        vao = _VAO(program)
        self._vaos.append(vao)
        return vao


def _renderer(config: GLRenderConfig) -> tuple[GLRenderer, _Contexto]:
    pygame.display.set_mode((64, 64))
    r = GLRenderer(config)
    ctx = _Contexto()
    r.ctx = ctx  # type: ignore[assignment]
    w, h = settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT
    r._create_fbos(w, h)
    r._create_shaders()
    r._create_quad(w, h)
    # Sin esto `render()` se va al camino software y no ejecuta ni una pasada,
    # que es justamente lo que esta prueba mide.
    r._initialized = True
    return r, ctx


def _superficie() -> pygame.Surface:
    s = pygame.Surface((settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT))
    s.fill((60, 60, 80))
    return s


@pytest.fixture(autouse=True)
def _pygame():
    if not pygame.get_init():
        pygame.init()
    yield


def _programas_ejecutados(r: GLRenderer, ctx: _Contexto) -> list[str]:
    r.render(_superficie(), _superficie())
    ejecutados: list[str] = []
    for vao in ctx._vaos:
        ejecutados.extend(vao.dibujados)
    return ejecutados


class TestCadaPasadaDibujaConSuPropioPrograma:
    def test_el_vao_de_un_programa_lleva_ese_programa_dentro(self) -> None:
        """La propiedad mínima: `_vao_para(p).programa is p`.

        Antes del arreglo `_vao_para` no existía y todo salía del mismo VAO.
        """
        r, _ctx = _renderer(GLRenderConfig())
        for nombre in [n for n in vars(r) if n.endswith("_prog")]:
            prog = getattr(r, nombre)
            if prog is None:
                continue
            vao = r._vao_para(prog)
            assert vao is not None, nombre
            assert vao.programa is prog, (
                f"{nombre}: su pasada dibujaría con el shader de otro programa"
            )

    def test_encender_una_pasada_ejecuta_su_shader_y_no_el_de_copia(self) -> None:
        """El defecto, en una frase: encender el bloom no ejecutaba el bloom."""
        r, ctx = _renderer(GLRenderConfig(bloom_enabled=True, bloom_intensity=0.7))
        ejecutados = _programas_ejecutados(r, ctx)
        del r
        assert any("bloom" in e for e in ejecutados), (
            "ninguna de las pasadas ejecutó el sombreador de bloom; se "
            f"ejecutaron: {ejecutados}"
        )

    def test_cada_pasada_encendida_aporta_un_shader_distinto(self) -> None:
        """Con seis efectos encendidos tienen que correr seis shaders distintos.

        Es la forma agregada del mismo fallo: antes, con todo encendido, la
        lista de programas ejecutados tenía un solo elemento repetido.
        """
        cfg = GLRenderConfig(
            bloom_enabled=True, bloom_intensity=0.7,
            vignette_enabled=True, color_grading_enabled=True,
            motion_blur_enabled=True, colorblind_mode=1,
            chromatic_aberration_strength=0.5,
            godray_enabled=True, lighting_enabled=True,
        )
        r, ctx = _renderer(cfg)
        r.set_refraction_region(None)
        distintos = set(_programas_ejecutados(r, ctx))
        del r
        assert len(distintos) >= 7, (
            f"sólo se ejecutaron {len(distintos)} sombreadores distintos con "
            f"ocho pasadas encendidas: {distintos}"
        )

    def test_los_vaos_se_reutilizan_entre_fotogramas(self) -> None:
        """Un VAO por programa, no uno por pasada y fotograma.

        Sin caché esto reservaría diez VertexArray por fotograma —600 por
        segundo— en el bucle de dibujado.
        """
        r, ctx = _renderer(GLRenderConfig(bloom_enabled=True, bloom_intensity=0.7))
        r.render(_superficie(), _superficie())
        tras_uno = len(ctx._vaos)
        for _ in range(5):
            r.render(_superficie(), _superficie())
        assert len(ctx._vaos) == tras_uno, (
            f"se crearon {len(ctx._vaos) - tras_uno} VAOs extra en cinco "
            "fotogramas: la caché de `_vao_para` no está funcionando"
        )

    def test_destroy_libera_todos_los_vaos_no_solo_uno(self) -> None:
        r, ctx = _renderer(GLRenderConfig(bloom_enabled=True, bloom_intensity=0.7))
        r.render(_superficie(), _superficie())
        assert len(ctx._vaos) > 1, "el caso interesante es con varios VAOs"
        r.destroy()
        assert r._vaos == {}


class TestLaInterfazSeComponeDespuesDeLaCadena:
    """La pasada 9b: la UI de una escena con ruta de GPU (AUD-343).

    La interfaz se dibuja en una superficie aparte y el renderer la compone
    con una pasada de copia **después** de la cadena entera: la luz, el bloom
    y la viñeta ya se aplicaron sobre la escena y no tocan el HUD, igual que
    en el camino software (AUD-090). Sin overlay no se paga ni pasada ni
    textura.
    """

    def test_con_overlay_la_pasada_de_copia_corre_una_vez_mas(self) -> None:
        r1, c1 = _renderer(GLRenderConfig())
        r1.render(_superficie(), _superficie())
        sin_overlay = sum(len(v.dibujados) for v in c1._vaos)

        r2, c2 = _renderer(GLRenderConfig())
        r2.render(_superficie(), _superficie(), overlay=_superficie())
        con_overlay = sum(len(v.dibujados) for v in c2._vaos)
        assert con_overlay == sin_overlay + 1, (
            "el overlay no se compuso con su pasada de copia: el HUD quedaría "
            "sin dibujar en la ruta de GPU"
        )

    def test_sin_overlay_no_se_crea_ni_textura(self) -> None:
        r, _ = _renderer(GLRenderConfig())
        r.render(_superficie(), _superficie())
        assert r._overlay_texture is None
