"""
Module: gpu_sprite_batch
System: engine.render
Academic Unit: N/A
Description: AUD-340 — la ruta de sprites en tarjeta (fase 5, lote 1).

Qué es esto
===========
Un `SpriteBatch` que en vez de `Surface.blits()` dibuja con **una** llamada
instanciada de OpenGL: un cuadrángulo por sprite, todos contra el atlas
subido una vez. Es la ruta que `scripts/bench_sprite_batch.py` venía midiendo
desde AUD-301 y que ahora existe de verdad en el motor, aislada y sin tocar
nada de lo que dibuja por CPU.

Dónde está su límite, dicho claro
---------------------------------
Este lote dibuja **en la tarjeta**: a un FBO que `volcar` ya encuentre
seleccionado. Quien lo use decide qué se dibuja detrás y qué delante, y quién
compone el resultado con el resto del fotograma es un asunto de la pasada
siguiente (el lote 2 de la fase 5). En un fotograma que se componga en CPU,
bajar los píxeles de vuelta para volcarlos en la superficie puede costar más
de lo que la tarjeta ahorró dibujando — la cuarta columna del benchmark existe
para que eso se mida y no se adivine.

Normal mapping
--------------
Cada atlas de color puede llevar un atlas de normales (ver
`src.engine.render.normales`, que lo genera del alfa del sprite). Una orden
dice si su sprite está iluminado: sin la bandera, el sprite se dibuja tal
cual —la rama plana del sombreador— y la ruta de GPU es indistinguible de un
blit. Con la bandera, la normal del mapa (o la plana (0,0,1), si no hay atlas
de normales) se modela con una luz ambiental, una direccional y hasta
`SPRITE_MAX_FOCOS` focos puntuales.

Sin mapa de normales y con la bandera puesta, la normal sale plana: el
sprite recibe el ambiente y el direccional como una lámina. Es un modo válido
para siluetas —sólo el direccional le da forma—, pero quien quiera volumen
encarga normales.
"""
from __future__ import annotations

import moderngl
import numpy as np
import pygame

from src.engine.render.normales import generar_normales_desde_alfa
from src.engine.render.shaders import SPRITE_MAX_FOCOS, sprite_frag, sprite_vert

#: Columnas de la fila de instancia: pos(2) tam(2) uv(4) nuv(4) tinte(4)
#: iluminado(1). El orden importa: es el del atributo en el VAO.
_INSTANCIA_COLS = 17
_TINTE_BLANCO = (1.0, 1.0, 1.0, 1.0)


class SpriteBatchGPU:
    """Acumula órdenes de sprites y las suelta en una llamada instanciada.

    Uso::

        lote = SpriteBatchGPU(ctx, ancho, alto)
        hoja_id = lote.registrar_atlas(hoja_de_sprites)
        lote.dibujar(hoja_id, (120, 80), pygame.Rect(0, 0, 32, 32))
        lote.set_camara(camara.x, camara.y)
        fbo.use()
        lote.volcar()

    El orden de dibujado es el orden de `dibujar`, igual que el `SpriteBatch`
    de CPU: ordenar por profundidad sigue siendo cosa de quien dibuja.
    """

    def __init__(
        self,
        ctx: moderngl.Context,
        ancho: int,
        alto: int,
        max_ordenes: int = 8192,
    ) -> None:
        self.ctx = ctx
        self._ancho = ancho
        self._alto = alto

        self._programa = ctx.program(
            vertex_shader=sprite_vert, fragment_shader=sprite_frag,
        )
        self._programa["pantalla"].value = (float(ancho), float(alto))
        self._programa["atlas"].value = 0
        self._programa["normales"].value = 1

        # Las cuatro esquinas del cuadrángulo, compartidas por todas las
        # instancias; el resto de atributos es por instancia (sufijo /i).
        esquinas = np.array([[0, 0], [1, 0], [0, 1], [1, 1]], dtype="f4")
        self._vbo_esquinas = ctx.buffer(esquinas.tobytes())
        indice = np.array([0, 1, 2, 1, 3, 2], dtype="i4")
        self._ibo = ctx.buffer(indice.tobytes())

        self._instancias = np.zeros((max_ordenes, _INSTANCIA_COLS), dtype="f4")
        self._cuentas = 0
        self._vbo_instancias = ctx.buffer(reserve=self._instancias.nbytes)

        self._vao = ctx.vertex_array(
            self._programa,
            [
                (self._vbo_esquinas, "2f", "en_esquina"),
                (
                    self._vbo_instancias,
                    "2f 2f 4f 4f 4f 1f/i",
                    "en_pos", "en_tam", "en_uv", "en_nuv", "en_tinte",
                    "en_iluminado",
                ),
            ],
            index_buffer=self._ibo,
        )

        # AUD-340 — sin atlas de normales registrado el sampler `normales`
        # no puede quedarse sin textura: un texel de normal plana (0,0,1)
        # encodada, que es el neutral que deja la luz como si no hubiera
        # relieve.
        plano = pygame.Surface((1, 1), pygame.SRCALPHA)
        plano.fill((128, 128, 255))
        self._textura_normal_plana = ctx.texture(
            (1, 1), 4, pygame.image.tobytes(plano, "RGBA", True), dtype="f1",
        )
        self._textura_normal_plana.filter = (
            moderngl.NEAREST, moderngl.NEAREST,
        )
        self._textura_normal_plana.use(1)

        self._atlas: dict[
            int, tuple[moderngl.Texture, moderngl.Texture | None, int, int],
        ] = {}
        self._atlas_contador = 0
        self._texturas_a_release: list[moderngl.Texture] = []
        # AUD-342 — el atlas de cada orden encolada: `volcar` dibuja con un
        # solo sampler de atlas, así que saber qué atlas pidió cada orden es
        # lo que permite rechazar la mezcla con un error en vez de arte.
        self._atlas_de_cada_orden: list[int] = []

        self._luz_ambiental = (0.35, 0.35, 0.38)
        self._luz_dir_direccion = (0.0, 0.0, 1.0)
        self._luz_dir_color = (0.0, 0.0, 0.0)
        self._focos: list[tuple[tuple[float, float], tuple[float, float, float],
                                 float, float]] = []

    # ── Atlas ──────────────────────────────────────────────────────────────

    def registrar_atlas(
        self, superficie: pygame.Surface,
        normales: pygame.Surface | None = None,
    ) -> int:
        """Sube un atlas (y su mapa de normales, si lo hay) y devuelve su id.

        La subida voltea en vertical, igual que la del fotograma en la
        tubería (AUD-229): `tostring(..., True)` y el sombreador asume v
        creciendo hacia arriba. Sin el volteo los sprites saldrían cabeza
        abajo, que es el error más difícil de ver en pantalla porque un
        sprite simétrico no lo delata.

        `normales` es el atlas de normales, del MISMO tamaño que el de color
        y con los recortes en las mismas posiciones. Sin él, los sprites de
        este atlas se dibujan con la normal plana —y de todos modos la luz
        no los toca salvo que la orden lleve la bandera de iluminado.

        El sombreador tiene un sampler de atlas por llamada: quien dibuje
        con dos atlas distintos tiene que volcar entre ellos, porque
        `volcar` se niega a mezclar atlas (dibujarlos juntos leería la
        textura equivocada, que no da error: da arte).
        """
        color = self.ctx.texture(
            superficie.get_size(), 4,
            pygame.image.tobytes(superficie, "RGBA", True), dtype="f1",
        )
        color.filter = (moderngl.NEAREST, moderngl.NEAREST)
        self._texturas_a_release.append(color)

        normal_tex: moderngl.Texture | None = None
        if normales is not None:
            if normales.get_size() != superficie.get_size():
                raise ValueError(
                    "el atlas de normales y el de color tienen que medir lo "
                    f"mismo: {normales.get_size()} contra {superficie.get_size()}",
                )
            normal_tex = self.ctx.texture(
                normales.get_size(), 4,
                pygame.image.tobytes(normales, "RGBA", True), dtype="f1",
            )
            normal_tex.filter = (moderngl.NEAREST, moderngl.NEAREST)
            self._texturas_a_release.append(normal_tex)

        self._atlas_contador += 1
        self._atlas[self._atlas_contador] = (
            color, normal_tex, *superficie.get_size(),
        )
        return self._atlas_contador

    @staticmethod
    def normales_de(superficie: pygame.Surface, fuerza: float = 1.0) -> pygame.Surface:
        """Mapa de normales procedural para un sprite, sin fichero extra.

        Ver `generar_normales_desde_alfa` para el algoritmo y la convención
        de signos; este método es el acceso cómodo desde el lote.
        """
        return generar_normales_desde_alfa(superficie, fuerza)

    # ── Órdenes ────────────────────────────────────────────────────────────

    def dibujar(
        self,
        atlas_id: int,
        posicion: tuple[float, float],
        recorte: pygame.Rect | tuple[int, int, int, int],
        normales_recorte: pygame.Rect | tuple[int, int, int, int] | None = None,
        tinte: tuple[float, float, float, float] | None = None,
        iluminado: bool = False,
    ) -> None:
        """Encola un sprite. No dibuja nada hasta `volcar`.

        `posicion` es la esquina superior izquierda del sprite, en píxeles
        del MUNDO (la cámara se resta en el sombreador). `recorte` es la zona
        del atlas de color; `normales_recorte` la del atlas de normales, que
        si no se da hereda la del color.
        """
        # `_atlas[id]` lanza KeyError con un id desconocido en vez de dibujar
        # con la textura equivocada, que no daría error: daría arte.
        _color, _normales, ancho_atlas, alto_atlas = self._atlas[atlas_id]
        self._atlas_de_cada_orden.append(atlas_id)
        u0, v0, u1, v1 = _rect_a_uv(recorte, ancho_atlas, alto_atlas)
        if normales_recorte is not None:
            n0, m0, n1, m1 = _rect_a_uv(normales_recorte, ancho_atlas, alto_atlas)
        else:
            n0, m0, n1, m1 = u0, v0, u1, v1
        x, y = posicion
        tam_x, tam_y = recorte[2], recorte[3]
        tint = tinte or _TINTE_BLANCO

        fila = self._instancias[self._cuentas]
        fila[0], fila[1] = x, y
        fila[2], fila[3] = tam_x, tam_y
        fila[4:8] = (u0, v0, u1 - u0, v1 - v0)
        fila[8:12] = (n0, m0, n1 - n0, m1 - m0)
        fila[12:16] = tint
        fila[16] = 1.0 if iluminado else 0.0
        self._cuentas += 1

        if self._cuentas >= len(self._instancias):
            self._crecer()

    def volcar(self) -> int:
        """Dibuja todo lo encolado al FBO que esté seleccionado y vacía el lote.

        El destino lo elige quien llama: `ctx.screen.use()` para la pantalla,
        o `fbo.use()` para un búfer intermedio. Devuelve cuántas órdenes
        dibujó (0 si no había nada, que además evita una llamada de render
        vacía por fotograma en los escenarios sin sprites de GPU).

        AUD-342 — antes de dibujar enlaza el atlas de color en la unidad 0 y
        el de normales en la 1 (o la normal plana, si el atlas no trae mapa):
        sin el enlace el sampler lee la textura que haya quedado en la
        unidad, la de la escena, y los sprites salen invisibles sin ningún
        error.
        """
        cuantas = self._cuentas
        if cuantas == 0:
            return 0
        primero = self._atlas_de_cada_orden[0]
        for atlas_id in self._atlas_de_cada_orden[1:cuantas]:
            if atlas_id != primero:
                raise ValueError(
                    "un `volcar` no puede mezclar atlas: el sombreador tiene "
                    "un solo sampler y mezclarlos daría sprites con texturas "
                    "ajenas. Dibuja y vuelca por atlas, o sube una sola hoja."
                )
        color, normales_tex, _ancho, _alto = self._atlas[primero]
        color.use(0)
        if normales_tex is not None:
            normales_tex.use(1)
        else:
            self._textura_normal_plana.use(1)
        self._vbo_instancias.write(
            self._instancias[:cuantas].tobytes(), 0,
        )
        self._vao.render(moderngl.TRIANGLES, instances=cuantas)
        self._cuentas = 0
        self._atlas_de_cada_orden.clear()
        return cuantas

    def limpiar(self) -> None:
        """Tira lo encolado sin dibujarlo."""
        self._cuentas = 0
        self._atlas_de_cada_orden.clear()

    def __len__(self) -> int:
        return self._cuentas

    def _crecer(self) -> None:
        """Dobla el búfer de instancias. El nuevo búfer sustituye al anterior.

        moderngl no deja redimensionar un búfer; el VAO referencia el búfer
        por su nombre de objeto OpenGL, que en moderngl es el propio objeto
        `Buffer` — o sea que hay que recrear el VAO con el búfer nuevo.
        """
        duplicado = np.zeros((len(self._instancias) * 2, _INSTANCIA_COLS),
                             dtype="f4")
        duplicado[:self._cuentas] = self._instancias[:self._cuentas]
        self._instancias = duplicado
        self._vbo_instancias = self.ctx.buffer(reserve=self._instancias.nbytes)
        self._vao = self.ctx.vertex_array(
            self._programa,
            [
                (self._vbo_esquinas, "2f", "en_esquina"),
                (
                    self._vbo_instancias,
                    "2f 2f 4f 4f 4f 1f/i",
                    "en_pos", "en_tam", "en_uv", "en_nuv", "en_tinte",
                    "en_iluminado",
                ),
            ],
            index_buffer=self._ibo,
        )

    # ── Cámara y luces ─────────────────────────────────────────────────────

    def set_camara(self, x: float, y: float) -> None:
        """La esquina superior izquierda de la cámara, en píxeles del mundo."""
        self._programa["camara"].value = (float(x), float(y))

    def set_luz_ambiental(self, color: tuple[float, float, float]) -> None:
        """Luz que llega igual a todas las caras. Suelo de los escenarios."""
        self._luz_ambiental = color
        self._programa["luz_ambiental"].value = color

    def set_luz_direccional(
        self, direccion: tuple[float, float, float],
        color: tuple[float, float, float],
    ) -> None:
        """Una luz lejana con dirección, como el sol.

        `direccion` apunta HACIA la luz (del fragmento a la fuente), como
        espera el producto escalar de Lambert, y no hace falta normalizarla:
        este método lo hace.
        """
        norm = np.linalg.norm(direccion) or 1.0
        self._luz_dir_direccion = (direccion[0] / norm, direccion[1] / norm,
                                   direccion[2] / norm)
        self._luz_dir_color = color
        self._programa["luz_dir_direccion"].value = self._luz_dir_direccion
        self._programa["luz_dir_color"].value = color

    def set_focos(
        self,
        focos: list[tuple[tuple[float, float], tuple[float, float, float],
                          float, float]],
    ) -> None:
        """Focos puntuales: (posición en px del mundo, color, radio, altura).

        `altura` es la altura del foco sobre el plano del sprite en píxeles:
        un foco muy alto ilumina de plano (normal casi perpendicular a la
        luz) y uno raso raspa el relieve. Más de `SPRITE_MAX_FOCOS` se
        descartan: el sombreador tiene arrays fijos, y la escena ya elige
        qué focos mandan.
        """
        self._focos = list(focos[:SPRITE_MAX_FOCOS])
        programa = self._programa
        programa["n_focos"].value = len(self._focos)
        for i, (pos, color, radio, altura) in enumerate(self._focos):
            programa[f"foco_pos[{i}]"].value = pos
            programa[f"foco_color[{i}]"].value = color
            programa[f"foco_radio[{i}]"].value = float(radio)
            programa[f"foco_altura[{i}]"].value = float(altura)

    # ── Ciclo de vida ──────────────────────────────────────────────────────

    def destruir(self) -> None:
        for textura in self._texturas_a_release:
            textura.release()
        self._texturas_a_release.clear()
        self._atlas.clear()
        self._textura_normal_plana.release()
        self._vao.release()
        self._vbo_esquinas.release()
        self._vbo_instancias.release()
        self._ibo.release()
        self._programa.release()


def _rect_a_uv(
    recorte: pygame.Rect | tuple[int, int, int, int],
    ancho_atlas: int,
    alto_atlas: int,
) -> tuple[float, float, float, float]:
    """(u0, v0, u1, v1) del recorte, con v creciendo hacia arriba.

    La textura se subió volteada (`tostring(..., True)`), así que en memoria
    la fila 0 es la fila INFERIOR de la superficie y v = 1 es la superior.
    El fragmento del borde superior del sprite en pantalla (esquina.y = 0,
    la pantalla crece hacia abajo) muestrea v0, y ahí tiene que estar la
    fila superior del recorte: v0 = 1 - y/alto. Es el mismo reflejo que hace
    `region_to_gl_uv` en la tubería, y equivocarse aquí sale con los sprites
    cabeza abajo.
    """
    x, y, w, h = recorte
    return (
        x / ancho_atlas,
        1.0 - (y + h) / alto_atlas,
        (x + w) / ancho_atlas,
        1.0 - y / alto_atlas,
    )
