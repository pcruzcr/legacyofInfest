"""
Module: test_composicion_de_sprites_en_gpu
System: tests
Academic Unit: IX

AUD-342 — fase 5 lote 2: la pasada de composición de sprites de GPU en
`GLRenderer` y el canal de `gpu_effects` que la activa por contexto.

El lote 1 (AUD-340) entregó `SpriteBatchGPU` aislado: dibuja a un FBO que el
llamador selecciona, y quién compone el resultado con el resto del fotograma
quedó dicho que era el lote 2. Ese es este trabajo: la escena rellena el lote
que le da `GameContext.lote_de_sprites`, lo publica por `gpu_effects`, `App`
se lo pasa al renderer, y la pasada de composición mezcla los sprites sobre la
escena justo después de que entre y antes de la refracción.

Se prueba sin tarjeta, como `test_cada_pasada_ejecuta_su_shader.py`: un
contexto falso que graba qué programas se ejecutaron y en qué orden. La causa
que un fallo de aquí tendría es de cableado, no de píxeles, y el cableado se
comprueba en cualquier runner.
"""
from __future__ import annotations

from typing import Any

import pygame
import pytest

from src.engine.core import gpu_effects, settings
from src.engine.render.gl_pipeline import GLRenderConfig, GLRenderer
from src.engine.render.gpu_sprite_batch import SpriteBatchGPU


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


def _nombre_del_shader(fuente: str) -> str:
    from src.engine.render import shaders

    for nombre in dir(shaders):
        valor = getattr(shaders, nombre)
        if isinstance(valor, str) and valor == fuente:
            return nombre
    return f"desconocido:{fuente[:40]!r}"


class _VAO:
    """Un VAO recuerda con qué programa se construyó — como el de moderngl."""

    def __init__(self, programa: _Programa) -> None:
        self.programa = programa
        self.dibujados: list[str] = []

    def render(self, _modo: Any = None, **_kw: Any) -> None:
        self.dibujados.append(self.programa.nombre)

    def release(self) -> None:
        pass


class _Textura:
    def __init__(self, size: tuple[int, int]) -> None:
        self.size = size
        self.filter: Any = None

    def use(self, _loc: int = 0) -> None:
        pass

    def write(self, _d: bytes) -> None:
        pass

    def read(self) -> bytes:
        return b"\x00" * (self.size[0] * self.size[1] * 4)

    def release(self) -> None:
        pass


class _Buffer:
    def __init__(self) -> None:
        self.datos = b""

    def write(self, datos: bytes, _offset: int = 0) -> None:
        self.datos = datos

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
        self._vaos: list[_VAO] = []

    def enable(self, _f: Any) -> None:
        pass

    def clear(self, *_a: float) -> None:
        pass

    def texture(self, size: tuple[int, int], _c: int, _datos: bytes | None = None,
                **_kw: Any) -> _Textura:
        return _Textura(size)

    def depth_texture(self, size: tuple[int, int]) -> _Textura:
        return _Textura(size)

    def framebuffer(self, color_attachments: list[_Textura],
                    depth_attachment: _Textura | None = None) -> _FBO:
        return _FBO(color_attachments)

    def program(self, vertex_shader: str, fragment_shader: str) -> _Programa:
        return _Programa(_nombre_del_shader(fragment_shader))

    def buffer(self, _data: bytes | None = None, reserve: int = 0) -> _Buffer:
        return _Buffer()

    def copy_framebuffer(self, _dst: _FBO, _src: _FBO) -> None:
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
    r._initialized = True
    return r, ctx


def _superficie() -> pygame.Surface:
    s = pygame.Surface((settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT))
    s.fill((60, 60, 80))
    return s


def _programas_ejecutados(r: GLRenderer, ctx: _Contexto) -> list[str]:
    r.render(_superficie(), _superficie())
    ejecutados: list[str] = []
    for vao in ctx._vaos:
        ejecutados.extend(vao.dibujados)
    return ejecutados


def _lote_con_una_orden(ctx: _Contexto) -> SpriteBatchGPU:
    lote = SpriteBatchGPU(ctx, settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT)
    hoja = pygame.Surface((32, 32), pygame.SRCALPHA)
    hoja.fill((200, 100, 50, 255))
    atlas_id = lote.registrar_atlas(hoja)
    lote.dibujar(atlas_id, (100, 100), pygame.Rect(0, 0, 32, 32))
    return lote


@pytest.fixture(autouse=True)
def _pygame():
    if not pygame.get_init():
        pygame.init()
    yield
    gpu_effects.reset()


# ── El canal de gpu_effects ──────────────────────────────────────────────


class TestElCanalDelLoteDeSprites:
    def test_publicar_y_leer(self) -> None:
        lote = object()
        assert gpu_effects.published_lote_de_sprites() is None
        gpu_effects.publish_lote_de_sprites(lote)
        assert gpu_effects.published_lote_de_sprites() is lote

    def test_begin_frame_lo_olvida(self) -> None:
        gpu_effects.publish_lote_de_sprites(object())
        gpu_effects.begin_frame()
        assert gpu_effects.published_lote_de_sprites() is None

    def test_reset_lo_olvida(self) -> None:
        gpu_effects.publish_lote_de_sprites(object())
        gpu_effects.reset()
        assert gpu_effects.published_lote_de_sprites() is None

    def test_es_estado_de_proceso_no_importa_la_clase(self) -> None:
        """El canal lleva un dato opaco: `engine.core` no puede importar la
        clase, que vive en `engine.render` y arrastra ModernGL."""
        gpu_effects.publish_lote_de_sprites(("cualquier", "cosa"))
        assert gpu_effects.published_lote_de_sprites() == ("cualquier", "cosa")


# ── La pasada de composición ─────────────────────────────────────────────


class TestLaPasadaDeComposicion:
    def test_sin_lote_publicado_la_pasada_no_corre(self) -> None:
        """El camino de siempre: una escena de CPU no paga ni una pasada."""
        r, ctx = _renderer(GLRenderConfig())
        ejecutados = _programas_ejecutados(r, ctx)
        assert "sprite_frag" not in ejecutados, (
            f"sin lote publicado se ejecutó la pasada de sprites: {ejecutados}"
        )

    def test_con_ordenes_el_lote_se_compone(self) -> None:
        r, ctx = _renderer(GLRenderConfig())
        lote = _lote_con_una_orden(ctx)
        r.lote_de_sprites = lote
        ejecutados = _programas_ejecutados(r, ctx)
        assert "sprite_frag" in ejecutados, (
            f"el lote publicado no se compuso: {ejecutados}"
        )

    def test_llega_despues_de_que_entre_la_escena(self) -> None:
        """Los sprites van ENCIMA de la escena: se mezclan después de la
        subida, o el fondo les taparía (o les daría el alfa equivocado)."""
        r, ctx = _renderer(GLRenderConfig())
        lote = _lote_con_una_orden(ctx)
        r.lote_de_sprites = lote
        ejecutados = _programas_ejecutados(r, ctx)
        i_sprites = ejecutados.index("sprite_frag")
        assert i_sprites > 0, (
            f"la pasada de sprites corrió la primera, sin escena detrás: "
            f"{ejecutados}"
        )

    def test_llega_antes_de_la_refraccion(self) -> None:
        """La refracción deforma lo ya compuesto: si el agua se aplicara
        antes, los sprites quedarían como una capa rígida encima."""
        r, ctx = _renderer(GLRenderConfig())
        lote = _lote_con_una_orden(ctx)
        r.lote_de_sprites = lote
        r.set_refraction_region((0, 0, settings.INTERNAL_WIDTH,
                                 settings.INTERNAL_HEIGHT))
        ejecutados = _programas_ejecutados(r, ctx)
        i_sprites = ejecutados.index("sprite_frag")
        i_refraccion = ejecutados.index("refraction_frag")
        assert i_sprites < i_refraccion, (
            f"la refracción corrió antes que los sprites: {ejecutados}"
        )

    def test_un_lote_vacio_no_dibuja_nada(self) -> None:
        """`volcar` con cero órdenes no hace ni la llamada de render: un
        escenario que publica pero no dibuja sprites de GPU no paga nada."""
        r, ctx = _renderer(GLRenderConfig())
        lote = SpriteBatchGPU(ctx, settings.INTERNAL_WIDTH,
                              settings.INTERNAL_HEIGHT)
        r.lote_de_sprites = lote
        ejecutados = _programas_ejecutados(r, ctx)
        assert "sprite_frag" not in ejecutados, (
            f"un lote vacío dibujó algo: {ejecutados}"
        )

    def test_volcar_vacia_el_lote(self) -> None:
        """Una orden compuesta no vuelve a aparecer en el fotograma siguiente:
        quien la dibuja es `volcar`, que además deja el lote listo para el
        próximo reparto."""
        r, ctx = _renderer(GLRenderConfig())
        lote = _lote_con_una_orden(ctx)
        r.lote_de_sprites = lote
        r.render(_superficie(), _superficie())
        r.render(_superficie(), _superficie())
        ejecutados: list[str] = []
        for vao in ctx._vaos:
            ejecutados.extend(vao.dibujados)
        assert len(lote) == 0, (
            "después de componer el lote siguió habiendo órdenes: el "
            "fotograma siguiente dibujaría los sprites de éste"
        )


# ── La creación y el ciclo de vida ───────────────────────────────────────


class TestElCicloDeVidaDelLote:
    def test_crear_lote_devuelve_el_mismo_objeto(self) -> None:
        r, _ctx = _renderer(GLRenderConfig())
        primero = r.crear_lote_de_sprites()
        segundo = r.crear_lote_de_sprites()
        assert primero is segundo, (
            "dos llamadas crean dos lotes: la escena y el renderer acabarían "
            "trabajando sobre objetos distintos"
        )

    def test_crear_lote_comparte_el_contexto_del_renderer(self) -> None:
        r, _ctx = _renderer(GLRenderConfig())
        lote = r.crear_lote_de_sprites()
        assert lote.ctx is r.ctx

    def test_sin_contexto_no_hay_lote(self) -> None:
        r, _ctx = _renderer(GLRenderConfig())
        r.ctx = None  # type: ignore[assignment]
        with pytest.raises(RuntimeError):
            r.crear_lote_de_sprites()

    def test_destroy_libera_el_lote(self) -> None:
        r, _ctx = _renderer(GLRenderConfig())
        lote = r.crear_lote_de_sprites()
        r.destroy()
        assert r.lote_de_sprites is None
        assert lote._cuentas == 0
