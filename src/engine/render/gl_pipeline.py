from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import moderngl
import numpy as np
import pygame

from src.engine.core import gpu_effects, settings
from src.engine.render.shaders import (
    GODRAY_DEFAULT_SAMPLES,
    bloom_extract_frag,
    bloom_frag,
    chromatic_aberration_frag,
    color_grading_frag,
    colorblind_frag,
    default_vert,
    godray_frag,
    lighting_frag,
    motion_blur_frag,
    passthrough_frag,
    refraction_frag,
    upload_frag,
    vignette_frag,
)

# AUD-215: por debajo de esta intensidad la separación de canales es de
# centésimas de píxel — invisible, pero bastaría para mantener encendida una
# pasada de pantalla completa indefinidamente, porque un decaimiento
# exponencial nunca llega a 0. Se engancha a 0 exacto y la pasada vuelve a
# costar nada.
_CHROMATIC_ABERRATION_EPSILON = 1e-3

# AUD-216 — la región de agua entra en píxeles de la superficie interna, con
# el origen arriba a la izquierda: es el único sistema de coordenadas que una
# escena de pygame maneja. Convertirlo al de OpenGL es cosa de esta tubería y
# de nadie más.


def region_to_gl_uv(
    region: pygame.Rect | tuple[int, int, int, int] | None,
    surface_width: int,
    surface_height: int,
) -> tuple[float, float, float, float] | None:
    """Convierte un rectángulo de pygame a la caja UV de la textura de escena.

    AUD-216 — aquí es donde esto se tuerce si no se tiene cuidado. `render()`
    sube la escena con ``pygame.image.tostring(surface, "RGBA", True)``: ese
    tercer argumento voltea la imagen en vertical, porque OpenGL numera las
    filas de una textura de abajo arriba y pygame de arriba abajo. Resultado:
    la fila 0 de la textura es la fila ``height - 1`` de la superficie.

    Entra: (x, y, ancho, alto) en píxeles, origen ARRIBA-izquierda.
    Sale:  (u0, v0, u1, v1) en [0, 1], origen ABAJO-izquierda, con
           ``v0 < v1`` siempre.

    La X no se toca; la Y se refleja: ``v = 1 - y / alto``. Como reflejar
    intercambia cuál de los dos bordes es el menor, el borde SUPERIOR del
    rectángulo de pygame se convierte en el valor MAYOR de v.

    Devuelve ``None`` cuando no hay nada que refractar —región ausente,
    degenerada o entera fuera de pantalla—, y ese ``None`` es lo que hace que
    la pasada cueste cero cuando no hay agua en el fotograma.
    """
    if region is None:
        return None
    if isinstance(region, pygame.Rect):
        x, y, w, h = region.x, region.y, region.width, region.height
    else:
        x, y, w, h = region
    if w <= 0 or h <= 0 or surface_width <= 0 or surface_height <= 0:
        return None

    # Recortar a la pantalla: con la cámara movida el agua se sale por los
    # bordes, y un UV fuera de [0, 1] muestrearía fuera de la textura.
    left = max(0, min(int(x), surface_width))
    right = max(0, min(int(x) + int(w), surface_width))
    top = max(0, min(int(y), surface_height))
    bottom = max(0, min(int(y) + int(h), surface_height))
    if right <= left or bottom <= top:
        return None

    return (
        left / surface_width,
        1.0 - bottom / surface_height,
        right / surface_width,
        1.0 - top / surface_height,
    )


@dataclass
class GLRenderConfig:
    bloom_enabled: bool = True
    bloom_threshold: float = 0.8
    #: AUD-224 — separación entre muestras del kernel, en píxeles. Con 1.0 el
    #: halo medía ±4 px y era invisible: medido contra el bloom de CPU en una
    #: Intel HD 530, la GPU cambiaba la imagen 0,2 de media frente a 5,4–8,8
    #: de la CPU, o sea 30 veces menos. El de CPU difumina sobre una copia
    #: reducida, y eso es lo que le da un halo ancho; aquí se consigue lo
    #: mismo separando las muestras, sin pasadas ni FBOs extra.
    bloom_spread: float = 11.0
    #: AUD-222 — lo escribe `App` en cada fotograma con lo que pide la escena
    #: (`gpu_effects.published_bloom()`). Era un valor fijo, y un valor fijo
    #: convierte una ráfaga en un brillo permanente.
    bloom_intensity: float = 0.5

    # AUD-222 — venía en `True`, y la viñeta se dibujaba dos veces: la de CPU
    # sobre la superficie y ésta sobre la textura.
    #
    # De las dos, la que se apaga es ésta, y no al revés como con el bloom: la
    # viñeta de la CPU **crece cuando al jugador le queda poca vida**
    # (`set_damage_vignette`), y esta configuración es estática — la GPU no
    # tiene forma de enterarse. Delegarla apagaría esa señal de daño. Cuesta
    # además un `blit` de una superficie cacheada, no una pasada de numpy, así
    # que dejarla en la CPU no es lo caro.
    vignette_enabled: bool = False
    vignette_strength: float = 0.5
    vignette_radius: float = 0.7

    color_grading_enabled: bool = False
    color_matrix: tuple[float, ...] = (1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0)

    motion_blur_enabled: bool = False
    motion_blur_factor: float = 0.1

    # AUD-215: la aberración cromática no tiene interruptor `_enabled` a
    # propósito. Es un efecto de impacto, no un ajuste de vídeo: la intensidad
    # 0 ya significa "apagado" y ahorra la pasada, y el juego pasa la inmensa
    # mayoría de los fotogramas así. Un booleano aparte sólo daría dos formas
    # de decir lo mismo, que pueden contradecirse.
    chromatic_aberration_strength: float = 0.0
    # Constante de decaimiento en 1/s. Con 6.0 un golpe cae a ~5% en medio
    # segundo: se nota el impacto y no se arrastra sobre el siguiente.
    chromatic_aberration_decay: float = 6.0

    colorblind_mode: int = 0

    #: AUD-216 — encendida por defecto desde que existe el cableado: **no es
    #: un coste**. `refraction_uniforms()` devuelve None mientras ninguna
    #: escena publique una región de agua, y sin uniforms no hay pasada ni
    #: intercambio de FBOs. Lo que este interruptor decide de verdad es quién
    #: dibuja el agua —el sombreador o `WaterEffect` por CPU—, y eso se
    #: declara en `cpu_effects_taken_over()`.
    refraction_enabled: bool = True
    refraction_amplitude: float = 0.006
    refraction_frequency: float = 60.0
    refraction_speed: float = 1.5
    refraction_tint: tuple[float, float, float] = (0.55, 0.75, 1.0)
    refraction_tint_strength: float = 0.35
    refraction_edge_fade: float = 0.02

    lighting_enabled: bool = True

    # ── Rayos de luz volumétricos (AUD-226) ──────────────────────────────
    #
    # Apagados por defecto: es una pasada de pantalla completa con 33 lecturas
    # de textura por píxel y ningún escenario la pide todavía. Con
    # `godray_enabled = False` no se compila ni una muestra, no se sube el
    # mapa de luz por su culpa y no se reserva memoria extra — el coste es
    # literalmente cero.
    godray_enabled: bool = False
    #: Ver `shaders.GODRAY_DEFAULT_SAMPLES`. Se hornea en el GLSL al crear los
    #: programas, así que cambiarlo requiere volver a llamar a `init()`.
    godray_samples: int = GODRAY_DEFAULT_SAMPLES
    #: Foco del abanico, en coordenadas de textura (0..1), NO en píxeles. El
    #: centro es un valor por defecto neutro: quien encienda el efecto debe
    #: convertir la posición en pantalla de su foco a UV y escribirla aquí
    #: cada fotograma, o los rayos saldrán siempre del medio de la pantalla.
    godray_origin: tuple[float, float] = (0.5, 0.5)
    #: Fracción del trayecto píxel→foco que recorre el rayo. 1.0 llega hasta
    #: el foco; 0.6 deja el abanico corto y evita que los rayos converjan en
    #: un punto duro.
    godray_density: float = 0.6
    godray_weight: float = 1.0
    #: Atenuación por muestra. 0.95^32 ≈ 0.19: el rayo se apaga suavemente
    #: antes de agotar las muestras, que es lo que le da la forma cónica.
    godray_decay: float = 0.95
    #: Escala final. Con los valores de arriba y un mapa de luz típico deja el
    #: núcleo del rayo en torno a +0.2 sobre la escena. Es un punto de partida
    #: derivado de la aritmética del shader, no medido en una GPU: en este
    #: repositorio no hay una (ver AUD-226), así que hay que retocarlo la
    #: primera vez que se vea en pantalla.
    godray_exposure: float = 3.0
    #: Suelo de luz ambiental que se descuenta antes de emitir. Tiene que
    #: quedar por encima del `ambient_brightness` de `LightSystem` (0.3), o
    #: el ambiente entero emite y el efecto es una neblina plana.
    godray_threshold: float = 0.35

    vsync: bool = True
    display_scale: int = 1

    def cpu_effects_taken_over(self) -> frozenset[str]:
        """Qué efectos deja de tener que hacer `PostProcessing` con esta config.

        AUD-222 — se deriva de las pasadas encendidas en vez de mantenerse en
        una lista aparte. Con dos listas, encender una pasada y olvidarse de la
        otra devuelve la duplicación exactamente igual que antes, y sin que
        falle nada.
        """
        activos = set()
        if self.bloom_enabled:
            activos.add(gpu_effects.BLOOM)
        if self.vignette_enabled:
            activos.add(gpu_effects.VIGNETTE)
        if self.refraction_enabled:
            activos.add(gpu_effects.WATER)
        return frozenset(activos)

    def bloom_active(self) -> bool:
        """¿Hay que ejecutar la pasada de bloom en este fotograma?

        La intensidad la publica la escena, y un menú publica 0. Sin esta
        guarda la pasada correría igual con el valor de la configuración y
        pondría halo donde el camino software no pone ninguno.
        """
        return self.bloom_enabled and self.bloom_intensity > 0.0


class GLRenderer:
    def __init__(self, config: GLRenderConfig | None = None) -> None:
        self.config = config or GLRenderConfig()
        self.ctx: moderngl.Context | None = None
        self._initialized = False

        self._scene_fbo: moderngl.Framebuffer | None = None
        self._bloom_fbo: moderngl.Framebuffer | None = None
        self._temp_fbo: moderngl.Framebuffer | None = None
        self._prev_fbo: moderngl.Framebuffer | None = None
        self._light_fbo: moderngl.Framebuffer | None = None

        self._passthrough_prog: moderngl.Program | None = None
        self._bloom_prog: moderngl.Program | None = None
        #: AUD-230 — la mitad cara del bloom, que corre a media resolución.
        self._bloom_extract_prog: moderngl.Program | None = None
        self._color_grading_prog: moderngl.Program | None = None
        self._vignette_prog: moderngl.Program | None = None
        self._motion_blur_prog: moderngl.Program | None = None
        self._lighting_prog: moderngl.Program | None = None
        self._colorblind_prog: moderngl.Program | None = None
        self._chromatic_aberration_prog: moderngl.Program | None = None
        self._refraction_prog: moderngl.Program | None = None
        self._godray_prog: moderngl.Program | None = None
        # AUD-229 — el sombreador que coloca la escena recién subida, y el
        # orden de canales para el que se compiló. `None` = no se detectó un
        # formato conocido y se sube por el camino lento de `tostring`.
        self._upload_prog: moderngl.Program | None = None
        self._swizzle: bool | None = None
        #: Textura del mapa de luz, reutilizada entre fotogramas.
        self._light_texture: moderngl.Texture | None = None

        # AUD-216 — estado por fotograma de la refracción. Vive en el renderer
        # y no en la config porque la región cambia con la cámara en cada
        # fotograma, mientras que la config son los ajustes que no cambian.
        self._refraction_region: pygame.Rect | tuple[int, int, int, int] | None = None
        self._refraction_time: float = 0.0

        self._quad_vao: moderngl.VertexArray | None = None
        # AUD-223 — un VAO por programa. Ver `_vao_para` para el porqué.
        self._vaos: dict[int, moderngl.VertexArray] = {}
        self._quad_vbo: moderngl.Buffer | None = None
        self._quad_ibo: moderngl.Buffer | None = None
        self._screen_texture: moderngl.Texture | None = None

    def init(self, window_surface: pygame.Surface) -> None:
        display_w, display_h = window_surface.get_size()
        import os as _os
        _os.environ["SDL_WINDOW_OPENGL"] = "1"
        pygame.display.set_mode(
            (display_w, display_h),
            pygame.OPENGL | pygame.DOUBLEBUF,
        )
        self.ctx = moderngl.create_context()
        self.ctx.enable(moderngl.BLEND)
        self.ctx.blend_func = moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA
        w, h = settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT
        self._create_fbos(w, h)
        self._create_shaders()
        self._create_quad(w, h)
        self._initialized = True

    def _create_fbos(self, w: int, h: int) -> None:
        ctx = self.ctx
        if ctx is None:
            return

        self._scene_fbo = ctx.framebuffer(
            color_attachments=[ctx.texture((w, h), 4, dtype="f1")],
            depth_attachment=ctx.depth_texture((w, h)),
        )

        self._temp_fbo = ctx.framebuffer(
            color_attachments=[ctx.texture((w, h), 4, dtype="f1")],
        )

        self._bloom_fbo = ctx.framebuffer(
            color_attachments=[ctx.texture((w // 2, h // 2), 4, dtype="f1")],
        )

        self._prev_fbo = ctx.framebuffer(
            color_attachments=[ctx.texture((w, h), 4, dtype="f1")],
        )

        self._light_fbo = ctx.framebuffer(
            color_attachments=[ctx.texture((w, h), 4, dtype="f1")],
        )

    def _create_shaders(self) -> None:
        ctx = self.ctx
        if ctx is None:
            return
        self._passthrough_prog = ctx.program(
            vertex_shader=default_vert,
            fragment_shader=passthrough_frag,
        )
        self._bloom_prog = ctx.program(
            vertex_shader=default_vert,
            fragment_shader=bloom_frag,
        )
        self._bloom_extract_prog = ctx.program(
            vertex_shader=default_vert,
            fragment_shader=bloom_extract_frag,
        )
        self._color_grading_prog = ctx.program(
            vertex_shader=default_vert,
            fragment_shader=color_grading_frag,
        )
        self._vignette_prog = ctx.program(
            vertex_shader=default_vert,
            fragment_shader=vignette_frag,
        )
        self._motion_blur_prog = ctx.program(
            vertex_shader=default_vert,
            fragment_shader=motion_blur_frag,
        )
        self._lighting_prog = ctx.program(
            vertex_shader=default_vert,
            fragment_shader=lighting_frag,
        )
        self._colorblind_prog = ctx.program(
            vertex_shader=default_vert,
            fragment_shader=colorblind_frag,
        )
        self._chromatic_aberration_prog = ctx.program(
            vertex_shader=default_vert,
            fragment_shader=chromatic_aberration_frag,
        )
        self._refraction_prog = ctx.program(
            vertex_shader=default_vert,
            fragment_shader=refraction_frag,
        )
        # AUD-226: el único programa cuyo fuente depende de la configuración —
        # el número de muestras va horneado como constante para que el driver
        # pueda desenrollar el bucle radial. Por eso se compila aquí y no se
        # puede cambiar la cuenta sin volver a pasar por `init()`.
        self._godray_prog = ctx.program(
            vertex_shader=default_vert,
            fragment_shader=godray_frag(self.config.godray_samples),
        )
        # AUD-229 — el formato se decide con una superficie construida igual
        # que la que `App` va a mandar (`pygame.Surface((w, h))` sin banderas),
        # porque pygame lo elige según la plataforma y la pantalla. De 1x1: lo
        # que se consulta son las máscaras de canal, no los píxeles.
        self._swizzle = self._swizzle_de(pygame.Surface((1, 1)))
        if self._swizzle is not None:
            self._upload_prog = ctx.program(
                vertex_shader=default_vert,
                fragment_shader=upload_frag(self._swizzle),
            )

    def _create_quad(self, w: int, h: int) -> None:
        ctx = self.ctx
        if ctx is None:
            return
        vertices = np.array([
            -1.0, -1.0,  0.0, 0.0,
             1.0, -1.0,  1.0, 0.0,
            -1.0,  1.0,  0.0, 1.0,
             1.0,  1.0,  1.0, 1.0,
        ], dtype=np.float32)
        indices = np.array([0, 1, 2, 1, 3, 2], dtype=np.int32)
        self._quad_vbo = ctx.buffer(vertices.tobytes())
        self._quad_ibo = ctx.buffer(indices.tobytes())
        self._vaos = {}
        self._quad_vao = self._vao_para(self._passthrough_prog)

    def _vao_para(self, program: moderngl.Program | None) -> moderngl.VertexArray | None:
        """El `VertexArray` del cuadrado para *este* programa.

        AUD-223 — aquí estaba el fallo que dejaba toda la tubería en adorno.
        Había **un solo** VAO, construido con `_passthrough_prog`, y
        `_run_shader_pass` fijaba los uniforms del programa que le pasaban pero
        luego dibujaba ese VAO. En moderngl un `VertexArray` lleva el programa
        dentro: es lo que se ejecuta al llamar a `render()`, y el argumento
        `program` no pintaba nada.

        O sea que las ocho pasadas —bloom, iluminación, corrección de color,
        viñeta, daltonismo, desenfoque de movimiento y las nuevas— ejecutaban
        todas el sombreador de copia. Medido en una Intel HD 530 con OpenGL
        4.6: encendiendo cualquiera de ellas, la imagen final salía **byte a
        byte idéntica** a no encender ninguna. El coste sí se pagaba (una
        pasada de pantalla completa por efecto); el efecto no llegaba nunca.

        No se vio antes porque los mismos efectos existen por CPU en
        `framework/vfx/post_processing.py` y ésos sí se dibujan: la pantalla se
        veía correcta, y lo que la GPU aportaba era exactamente nada.

        Los VAOs se cachean por programa —construirlos por fotograma sería
        reservar y liberar en el bucle de dibujado— y comparten el mismo par
        de búferes, que es lo único que ocupa memoria de verdad.
        """
        ctx = self.ctx
        if ctx is None or program is None or self._quad_vbo is None:
            return None
        cacheado = self._vaos.get(id(program))
        if cacheado is None:
            cacheado = ctx.vertex_array(
                program,
                [(self._quad_vbo, "2f 2f", "in_position", "in_texcoord")],
                index_buffer=self._quad_ibo,
            )
            self._vaos[id(program)] = cacheado
        return cacheado

    #: Máscaras de canal que sabemos subir sin convertir, y si hay que
    #: intercambiar rojo y azul en el sombreador. La clave es (R, G, B): el
    #: alfa no importa porque la tubería trabaja en RGBA opaco.
    _FORMATOS_DIRECTOS: dict[tuple[int, int, int], bool] = {
        (0x00FF0000, 0x0000FF00, 0x000000FF): True,   # BGRA en memoria
        (0x000000FF, 0x0000FF00, 0x00FF0000): False,  # RGBA en memoria
    }

    @classmethod
    def _swizzle_de(cls, surface: pygame.Surface) -> bool | None:
        """¿Se puede subir esta superficie sin convertirla? ¿Con o sin swizzle?

        AUD-229 — devuelve `None` cuando el formato no es uno de los dos que
        sabemos leer, y entonces el renderizador usa `tostring`. No se asume el
        formato: pygame lo elige según la plataforma y la profundidad de la
        pantalla, y equivocarse aquí no da un error, da los colores cambiados.
        """
        if surface.get_bytesize() != 4:
            return None
        r, g, b, _a = surface.get_masks()
        return cls._FORMATOS_DIRECTOS.get((r, g, b))

    def _subida_directa(self, surface: pygame.Surface) -> bool:
        """¿Esta superficie sube sin convertir, con el sombreador compilado?"""
        return self._swizzle is not None and self._swizzle_de(surface) == self._swizzle

    def _subir(
        self, surface: pygame.Surface, textura: moderngl.Texture | None,
    ) -> moderngl.Texture | None:
        """Sube una superficie a su textura, reutilizándola entre fotogramas.

        AUD-229 — el camino rápido escribe la memoria de la superficie tal
        cual (`get_view("0")` es un `memoryview`, sin copia) y deja el volteo y
        el orden de canales para el sombreador de subida. El de reserva
        convierte con `tostring`, que es lo que se hacía siempre.

        La textura se reutiliza en vez de crearse cada fotograma: crear y
        soltar una de 800x600 cuesta 0,46 ms medidos, que a 60 fps son 27 ms
        por segundo tirados en reservar memoria que ya se tenía.
        """
        ctx = self.ctx
        if ctx is None:
            return textura
        tam = surface.get_size()
        # El sombreador de subida se compiló para UN orden de canales. Si esta
        # superficie concreta tiene otro —una escena puede pasar cualquier
        # cosa— se convierte, que es lento pero correcto. Preferir correcto.
        if self._swizzle is not None and self._swizzle_de(surface) == self._swizzle:
            datos: Any = surface.get_view("0")
        else:
            datos = pygame.image.tostring(surface, "RGBA", True)
        if textura is None or textura.size != tam:
            if textura is not None:
                textura.release()
            return ctx.texture(tam, 4, data=datos, dtype="f1")
        textura.write(datos)
        return textura

    def _run_shader_pass(
        self, program: moderngl.Program,
        source_tex: moderngl.Texture,
        uniforms: dict[str, Any] | None = None,
        target_fbo: moderngl.Framebuffer | None = None,
    ) -> None:
        ctx = self.ctx
        if ctx is None or self._quad_vao is None:
            return
        # AUD-223 — el VAO tiene que ser el de ESTE programa, no el del
        # passthrough; ver `_vao_para`.
        vao = self._vao_para(program)
        if vao is None:
            return

        if target_fbo is not None:
            target_fbo.use()
        elif ctx.screen is not None:
            ctx.screen.use()

        source_tex.use(0)
        if "scene" in program:
            program["scene"].value = 0

        if uniforms:
            for key, value in uniforms.items():
                if key in program:
                    v = program[key]
                    if isinstance(value, bytes):
                        v.write(value)
                    else:
                        v.value = value

        vao.render(moderngl.TRIANGLES)

    # ── AUD-216 — refracción bajo el agua ───────────────────────────────

    def set_refraction_region(
        self,
        region: pygame.Rect | tuple[int, int, int, int] | None,
        dt: float = 0.0,
    ) -> None:
        """Declara dónde hay agua en ESTE fotograma, y avanza la onda.

        `region` va en píxeles de la superficie interna, origen arriba a la
        izquierda —o sea, ya proyectada por la cámara: es el rectángulo que el
        agua ocupa en pantalla, no en el mundo—. `None` apaga la pasada.

        Se pide en cada fotograma en vez de recordarse porque la región no es
        un ajuste, es una consecuencia de dónde está la cámara; recordarla
        haría que el agua se quedase pegada al cambiar de escenario.
        """
        self._refraction_region = region
        if dt:
            self._refraction_time += dt * self.config.refraction_speed

    def refraction_uniforms(self) -> dict[str, Any] | None:
        """Los uniforms de la pasada, o `None` si no hay nada que refractar.

        Separado de `render()` para que la decisión —y la conversión de
        coordenadas, que es donde está el riesgo— se pueda probar sin GPU.
        """
        if not self.config.refraction_enabled:
            return None
        uv = region_to_gl_uv(
            self._refraction_region, settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT,
        )
        if uv is None:
            return None
        return {
            "region": uv,
            "time": self._refraction_time,
            "amplitude": self.config.refraction_amplitude,
            "frequency": self.config.refraction_frequency,
            "tint": self.config.refraction_tint,
            "tintStrength": self.config.refraction_tint_strength,
            "edgeFade": self.config.refraction_edge_fade,
        }

    def render(
        self,
        scene_surface: pygame.Surface,
        light_surface: pygame.Surface | None = None,
    ) -> None:
        if not self._initialized or self.ctx is None:
            self._software_fallback(scene_surface)
            return

        ctx = self.ctx
        # AUD-229 — ya no hacen falta el ancho y el alto aquí: `_subir` toma el
        # tamaño de la propia superficie, que es lo correcto —una escena podría
        # mandar otra resolución— y las texturas se reutilizan en vez de
        # recrearse con las constantes de `settings`.
        self._screen_texture = self._subir(scene_surface, self._screen_texture)

        read_fbo = self._scene_fbo
        write_fbo = self._temp_fbo

        # 1. La escena entra en la cadena, colocada.
        #
        # AUD-229 — con el camino rápido esta pasada usa `_upload_prog`, que
        # además de copiar voltea la imagen e intercambia rojo y azul; con el
        # camino de reserva usa el `passthrough` de siempre, porque entonces
        # `tostring` ya entregó los píxeles colocados. Es la misma pasada y el
        # mismo coste en los dos casos: lo que cambia es lo que se paga
        # *antes*, en la CPU.
        read_fbo.use()
        ctx.clear(0.06, 0.06, 0.16, 1.0)
        self._run_shader_pass(
            self._upload_prog if self._subida_directa(scene_surface)
            else self._passthrough_prog,
            self._screen_texture,
            target_fbo=read_fbo,
        )

        # 1.5. Refracción bajo el agua (AUD-216)
        #
        # Va aquí, sobre la escena cruda y antes de todo lo demás, porque
        # refractar es deformar la escena, no post-procesarla: el bloom, la
        # iluminación y la viñeta tienen que operar sobre lo ya deformado. Al
        # revés se difuminaría primero y luego se retorcería el difuminado,
        # que es un artefacto visible en los bordes brillantes.
        #
        # `refraction_uniforms()` devuelve None si la refracción está apagada
        # o si no hay agua en pantalla, y entonces no se encadena nada: un
        # escenario seco no paga ni una pasada ni un intercambio de FBOs.
        refraction = self.refraction_uniforms()
        if refraction is not None and self._refraction_prog:
            self._run_shader_pass(
                self._refraction_prog, read_fbo.color_attachments[0],
                uniforms=refraction,
                target_fbo=write_fbo,
            )
            read_fbo, write_fbo = write_fbo, read_fbo

        # 2. Bloom — extracción a media resolución y composición (AUD-230)
        if self.config.bloom_active() and self._bloom_prog and self._bloom_extract_prog:
            # 2a. El halo, en el FBO de media resolución.
            self._run_shader_pass(
                self._bloom_extract_prog, read_fbo.color_attachments[0],
                uniforms={
                    "threshold": self.config.bloom_threshold,
                    "spread": self.config.bloom_spread,
                },
                target_fbo=self._bloom_fbo,
            )
            # 2b. Escena + halo. El halo vuelve a tamaño completo por el
            # filtrado bilineal de la propia textura, que además lo suaviza.
            self._bloom_fbo.color_attachments[0].use(1)
            self._run_shader_pass(
                self._bloom_prog, read_fbo.color_attachments[0],
                # El sampler del halo va por el mismo camino que el resto de
                # uniformes en vez de asignarse a mano: `_run_shader_pass` ya
                # comprueba que el nombre exista en el programa, y así los
                # dobles de prueba —que no compilan GLSL— no tienen que
                # emular la indexación de un `moderngl.Program`.
                uniforms={"intensity": self.config.bloom_intensity, "halo": 1},
                target_fbo=write_fbo,
            )
            read_fbo, write_fbo = write_fbo, read_fbo

        # 3. Light map upload — shared by lighting and god rays.
        #
        # AUD-226: la subida estaba dentro del `if` de la iluminación. Los
        # rayos volumétricos leen el MISMO mapa, así que dejarla ahí obligaba
        # o a subirlo dos veces por fotograma (1,9 MB extra por el bus a
        # 800x600, ~115 MB/s a 60 fps) o a que los rayos sólo funcionaran con
        # la iluminación encendida, que son dos efectos independientes. Se
        # sube una vez si lo necesita alguien, y se libera al final.
        #
        # AUD-229 — y se sube igual que la escena: sin convertir cuando el
        # formato lo permite. La diferencia con la escena es que a este mapa no
        # lo lee una pasada de copia sino `lighting_frag` y `godray_frag`
        # directamente, así que hay que dejarlo colocado antes: se normaliza
        # con una pasada de `_upload_prog` a `_light_fbo`. Cuesta una pasada de
        # GPU (~0,2 ms) y ahorra los 3,5 ms de `tostring` en la CPU.
        #
        # Esa pasada también recupera `_light_fbo`, que se ataba y se limpiaba
        # aquí para nada: la pasada siguiente escribía en `write_fbo` y
        # deshacía el `use()` una línea después.
        light_tex: moderngl.Texture | None = None
        if light_surface is not None and (
            self.config.lighting_enabled or self.config.godray_enabled
        ):
            self._light_texture = self._subir(light_surface, self._light_texture)
            if self._subida_directa(light_surface) and self._upload_prog:
                self._run_shader_pass(
                    self._upload_prog, self._light_texture,
                    target_fbo=self._light_fbo,
                )
                light_tex = self._light_fbo.color_attachments[0]
            else:
                light_tex = self._light_texture

        # 3a. Lighting
        if self.config.lighting_enabled and light_tex is not None and self._lighting_prog:
            light_tex.use(1)
            self._lighting_prog["scene"].value = 0
            self._lighting_prog["lightMap"].value = 1
            self._run_shader_pass(
                self._lighting_prog, read_fbo.color_attachments[0],
                target_fbo=write_fbo,
            )
            read_fbo, write_fbo = write_fbo, read_fbo

        # 3b. God rays (AUD-226)
        #
        # Van DESPUÉS de la iluminación, y esa posición es el corazón del
        # arreglo. `lighting_frag` es multiplicativo (`color * light`): todo lo
        # que se sume antes queda multiplicado por el mapa de luz, o sea
        # aniquilado justo donde un rayo tiene que verse, que es la sombra.
        # Un rayo crepuscular es luz *dispersada por el aire* entre el foco y
        # la cámara; no es superficie iluminada y no debe atenuarse con ella.
        #
        # El precio de esta decisión es que el bloom (pasada 2) ya ha pasado y
        # no realza los rayos. Se acepta a sabiendas: la propia dispersión
        # radial es un operador de difusión y produce su propio halo, mientras
        # que colocar los rayos antes del bloom los borraría por completo en
        # las zonas oscuras. Efecto que sobrevive sin realce > efecto realzado
        # que no se ve. Reordenar bloom e iluminación arreglaría ambas cosas,
        # pero cambia el aspecto de todos los escenarios existentes y es una
        # decisión de otro AUD.
        #
        # Antes de grading y viñeta, en cambio, sí: un rayo es luz de la
        # escena y tiene que teñirse y viñetearse como el resto de la imagen.
        if self.config.godray_enabled and light_tex is not None and self._godray_prog:
            light_tex.use(1)
            self._godray_prog["lightMap"].value = 1
            self._run_shader_pass(
                self._godray_prog, read_fbo.color_attachments[0],
                uniforms={
                    "lightOrigin": self.config.godray_origin,
                    "density": self.config.godray_density,
                    "weight": self.config.godray_weight,
                    "decay": self.config.godray_decay,
                    "exposure": self.config.godray_exposure,
                    "emissionThreshold": self.config.godray_threshold,
                },
                target_fbo=write_fbo,
            )
            read_fbo, write_fbo = write_fbo, read_fbo

        # AUD-229 — aquí había un `light_tex.release()`. Ya no: la textura se
        # reutiliza entre fotogramas, y soltarla destruiría o bien la que se
        # reescribe cada fotograma o bien el adjunto de `_light_fbo`. Se libera
        # una sola vez, en `destroy()`.

        # 4. Color grading
        if self.config.color_grading_enabled and self._color_grading_prog:
            mat = np.array(self.config.color_matrix, dtype=np.float32).reshape(3, 3)
            self._run_shader_pass(
                self._color_grading_prog, read_fbo.color_attachments[0],
                uniforms={"colorMatrix": mat.tobytes()},
                target_fbo=write_fbo,
            )
            read_fbo, write_fbo = write_fbo, read_fbo

        # 5. Chromatic aberration
        #
        # AUD-215: el sitio en la cadena no es arbitrario. Va aquí porque:
        #
        #   * DESPUÉS del bloom — si fuese antes, el difuminado del bloom se
        #     comería las franjas de color y el golpe se vería como un simple
        #     destello. Al ir después, el propio halo se separa en canales, que
        #     es como se comporta una lente de verdad.
        #   * DESPUÉS de la iluminación — el mapa de luz está alineado píxel a
        #     píxel con la geometría de la escena. Desplazar los canales antes
        #     descuadraría la luz respecto de lo que ilumina.
        #   * ANTES de la viñeta — la aberración es máxima justo en los bordes,
        #     que es donde la viñeta oscurece. Al revés quedarían franjas de
        #     color brillando encima de unas esquinas ya apagadas.
        #   * ANTES de la corrección de daltonismo — esa pasada remapea el
        #     color final que ve el jugador; separar R y B después
        #     reintroduciría la confusión de canales que existe para compensar.
        #   * ANTES del motion blur — que acumula el fotograma ya compuesto,
        #     así las franjas del impacto dejan estela en vez de cortarse secas.
        #
        # La condición es `> 0.0`, no un booleano: con intensidad 0 no se gasta
        # una pasada de pantalla completa, que es el caso de casi todos los
        # fotogramas.
        if self.config.chromatic_aberration_strength > 0.0 and self._chromatic_aberration_prog:
            self._run_shader_pass(
                self._chromatic_aberration_prog, read_fbo.color_attachments[0],
                uniforms={"strength": self.config.chromatic_aberration_strength},
                target_fbo=write_fbo,
            )
            read_fbo, write_fbo = write_fbo, read_fbo

        # 6. Vignette
        if self.config.vignette_enabled and self._vignette_prog:
            self._run_shader_pass(
                self._vignette_prog, read_fbo.color_attachments[0],
                uniforms={
                    "strength": self.config.vignette_strength,
                    "radius": self.config.vignette_radius,
                },
                target_fbo=write_fbo,
            )
            read_fbo, write_fbo = write_fbo, read_fbo

        # 7. Colorblind correction
        if self.config.colorblind_mode > 0 and self._colorblind_prog:
            self._run_shader_pass(
                self._colorblind_prog, read_fbo.color_attachments[0],
                uniforms={"mode": self.config.colorblind_mode},
                target_fbo=write_fbo,
            )
            read_fbo, write_fbo = write_fbo, read_fbo

        # 8. Motion blur
        if self.config.motion_blur_enabled and self._motion_blur_prog:
            self._prev_fbo.color_attachments[0].use(1)
            self._run_shader_pass(
                self._motion_blur_prog, read_fbo.color_attachments[0],
                uniforms={
                    "blendFactor": self.config.motion_blur_factor,
                    "prevFrame": 1,
                },
                target_fbo=write_fbo,
            )
            # AUD-236 — guardar el fotograma para el siguiente, **sin sacarlo
            # de la tarjeta**.
            #
            # Aquí había esto:
            #
            #     prev_data = write_fbo.color_attachments[0].read()
            #     self._prev_fbo.color_attachments[0].write(prev_data)
            #
            # que baja 1,9 MB de la GPU a la CPU y los vuelve a subir, cada
            # fotograma. Un `read()` además **sincroniza**: obliga a la CPU a
            # esperar a que la tarjeta termine todo lo pendiente, así que no
            # sólo cuesta la copia, tira por tierra el trabajo en paralelo de
            # los dos procesadores.
            #
            # Medido en una Intel HD 530: encender el desenfoque de movimiento
            # costaba **5,45 ms**, el 33 % del presupuesto de 60 fps, cuando
            # ninguna otra pasada de la tubería pasa de 0,13 ms. Era, con
            # diferencia, lo más caro de todo el renderizado.
            #
            # `copy_framebuffer` hace la misma copia dentro de la tarjeta, sin
            # que los píxeles crucen el bus ni la CPU espere a nadie.
            ctx.copy_framebuffer(self._prev_fbo, write_fbo)
            read_fbo, write_fbo = write_fbo, read_fbo

        # 9. Blit to screen
        ctx.screen.use()
        ctx.clear(0.0, 0.0, 0.0, 1.0)
        self._run_shader_pass(
            self._passthrough_prog, read_fbo.color_attachments[0],
        )
        pygame.display.flip()

    def _software_fallback(self, surface: pygame.Surface) -> None:
        display_surf = pygame.display.get_surface()
        if display_surf:
            pygame.transform.scale_by(
                surface, self.config.display_scale, display_surf,
            )

    def trigger_chromatic_aberration(self, strength: float = 0.6) -> None:
        """Enciende la aberración cromática para un impacto fuerte.

        AUD-215: se queda con el máximo entre lo que ya había y lo pedido en
        vez de asignar. Dos golpes seguidos son lo normal en una pelea, y
        asignar haría que un impacto flojo cortase en seco el destello de uno
        fuerte que aún estaba decayendo — se vería como un parpadeo.

        `strength` se recorta a 0..1; el shader lo escala a un desplazamiento
        en pantalla, no es un valor en píxeles.
        """
        pedido = min(max(strength, 0.0), 1.0)
        self.config.chromatic_aberration_strength = max(
            self.config.chromatic_aberration_strength, pedido,
        )

    def update_chromatic_aberration(self, dt: float) -> None:
        """Deja decaer la intensidad. Llamar una vez por fotograma.

        AUD-215: el decaimiento es exponencial e independiente del framerate
        (`exp(-k*dt)`), no una resta fija por fotograma, que haría que el
        efecto durase el doble a 30 fps que a 60.
        """
        actual = self.config.chromatic_aberration_strength
        if actual <= 0.0:
            return
        actual *= math.exp(-self.config.chromatic_aberration_decay * max(dt, 0.0))
        if actual < _CHROMATIC_ABERRATION_EPSILON:
            actual = 0.0
        self.config.chromatic_aberration_strength = actual

    def resize(self, width: int, height: int) -> None:
        self._create_fbos(width, height)

    def destroy(self) -> None:
        for fbo_name in ("_scene_fbo", "_temp_fbo", "_bloom_fbo", "_prev_fbo", "_light_fbo"):
            fbo = getattr(self, fbo_name, None)
            if fbo is not None:
                fbo.release()
        # AUD-215: el programa de la aberración cromática se libera aquí. El
        # resto de programas de la tubería todavía no se liberan (queda
        # anotado); se añade el propio para no dejar el hueco más grande de lo
        # que ya es.
        if self._bloom_extract_prog is not None:
            self._bloom_extract_prog.release()
            self._bloom_extract_prog = None
        if self._chromatic_aberration_prog is not None:
            self._chromatic_aberration_prog.release()
            self._chromatic_aberration_prog = None
        if self._screen_texture:
            self._screen_texture.release()
            self._screen_texture = None
        # AUD-229 — la textura del mapa de luz vive tanto como el renderizador.
        if self._light_texture is not None:
            self._light_texture.release()
            self._light_texture = None
        if self._upload_prog is not None:
            self._upload_prog.release()
            self._upload_prog = None
        # AUD-223 — se liberan todos los VAOs, no sólo el del passthrough: al
        # haber uno por programa, soltar sólo `_quad_vao` dejaba los otros
        # nueve vivos en cada `destroy()`.
        for vao in self._vaos.values():
            vao.release()
        self._vaos.clear()
        self._quad_vao = None
        for buf_name in ("_quad_vbo", "_quad_ibo"):
            buf = getattr(self, buf_name, None)
            if buf is not None:
                buf.release()
                setattr(self, buf_name, None)
        # AUD-216 — el programa de refracción se libera aquí; el resto de
        # programas no se liberaban, y no los toco porque quedan fuera de
        # este hallazgo (queda anotado para quien audite `destroy()`).
        if self._refraction_prog is not None:
            self._refraction_prog.release()
            self._refraction_prog = None
        # AUD-226 — mismo caso que los dos de arriba.
        if self._godray_prog is not None:
            self._godray_prog.release()
            self._godray_prog = None
        self._refraction_region = None
        self._refraction_time = 0.0
        self._initialized = False
