"""
Module: test_lote_de_sprites_gpu
System: tests
Academic Unit: N/A

AUD-340 — la ruta de sprites en tarjeta (fase 5, lote 1): el lote instanciado,
las normales procedurales y la rama plana que mantiene el aspecto del blit.

Lo que se prueba y lo que no
----------------------------
Sin tarjeta no hay píxeles que comprobar: `SDL_VIDEODRIVER=dummy` no da
contexto OpenGL, y el aspecto de un shader hay que verlo lanzando el juego
(es el mismo límite, anotado, de la tubería de post-procesado). Lo que sí se
fija aquí, con un contexto falso que registra lo que se le pide:

* que cada orden se codifica en la fila de instancia correcta (posición,
  tamaño, recorte, tinte, bandera),
* que `volcar` hace UNA llamada de render con las N instancias y vacía,
* que el atlas se sube volteado y con su normal opcional,
* que la cámara y las luces llegan a los uniformes,
* y las propiedades matemáticas de las normales procedurales, que no
  necesitan GPU.
"""
from __future__ import annotations

from typing import Any

import numpy as np
import pygame
import pytest

from src.engine.render.gpu_sprite_batch import _INSTANCIA_COLS, SpriteBatchGPU
from src.engine.render.normales import generar_normales_desde_alfa
from src.engine.render.shaders import SPRITE_MAX_FOCOS

ANCHO, ALTO = 320, 240


class _Uniforme:
    def __init__(self) -> None:
        self.value: Any = None
        self.escrituras: list[bytes] = []

    def write(self, data: bytes) -> None:
        self.value = data
        self.escrituras.append(data)


class _Programa:
    def __init__(self) -> None:
        self._uniformes: dict[str, _Uniforme] = {}

    def __contains__(self, key: str) -> bool:
        return True

    def __getitem__(self, key: str) -> _Uniforme:
        return self._uniformes.setdefault(key, _Uniforme())

    def release(self) -> None:
        pass


class _Textura:
    def __init__(self, size: tuple[int, int], data: bytes = b"") -> None:
        self.size = size
        self.data = data
        self.filter: Any = None
        self.liberada = False

    def use(self, _lugar: int = 0) -> None:
        pass

    def release(self) -> None:
        self.liberada = True


class _VAO:
    def __init__(self, programa: _Programa) -> None:
        self.programa = programa
        self.renders: list[dict[str, Any]] = []
        self.liberado = False

    def render(self, _modo: Any = None, instances: int = 0) -> None:
        self.renders.append({"instances": instances})

    def release(self) -> None:
        self.liberado = True


class _Buffer:
    def __init__(self) -> None:
        self.escrituras: list[tuple[bytes, int]] = []

    def write(self, data: bytes, offset: int = 0) -> None:
        self.escrituras.append((data, offset))

    def release(self) -> None:
        pass


class _Contexto:
    def __init__(self) -> None:
        self.programas: list[_Programa] = []
        self.texturas: list[_Textura] = []
        self.vaos: list[_VAO] = []
        self.buffers: list[_Buffer] = []

    def program(self, vertex_shader: str, fragment_shader: str) -> _Programa:
        assert "#version 330" in vertex_shader, "shader de vértices raro"
        assert "#version 330" in fragment_shader
        p = _Programa()
        self.programas.append(p)
        return p

    def buffer(self, data: bytes | None = None, reserve: int = 0) -> _Buffer:
        b = _Buffer()
        self.buffers.append(b)
        return b

    def texture(
        self, size: tuple[int, int], _componentes: int,
        data: bytes | None = None, **_kw: Any,
    ) -> _Textura:
        t = _Textura(size, data or b"")
        self.texturas.append(t)
        return t

    def vertex_array(
        self, programa: _Programa, _atributos: list[Any],
        index_buffer: _Buffer | None = None,
    ) -> _VAO:
        vao = _VAO(programa)
        self.vaos.append(vao)
        return vao


@pytest.fixture
def lote() -> tuple[SpriteBatchGPU, _Contexto]:
    if not pygame.get_init():
        pygame.init()
    ctx = _Contexto()
    return SpriteBatchGPU(ctx, ANCHO, ALTO, max_ordenes=8), ctx  # type: ignore[arg-type]


def _hoja(color: tuple[int, int, int]) -> pygame.Surface:
    s = pygame.Surface((64, 64), pygame.SRCALPHA)
    s.fill(color)
    return s


class TestElLoteCodificaLasOrdenes:
    def test_una_orden_va_en_una_fila_con_sus_seis_campos(self, lote) -> None:
        lote_gpu, _ctx = lote
        atlas = lote_gpu.registrar_atlas(_hoja((200, 100, 50)))
        lote_gpu.dibujar(atlas, (12, 34), (8, 8, 16, 16),
                         tinte=(0.5, 1.0, 0.25, 0.9), iluminado=True)
        fila = lote_gpu._instancias[0]
        assert fila[0] == 12.0 and fila[1] == 34.0        # posición
        assert fila[2] == 16.0 and fila[3] == 16.0        # tamaño
        assert np.allclose(fila[4:8], (8 / 64, 1.0 - 24 / 64, 16 / 64, 16 / 64))
        assert np.allclose(fila[8:12], fila[4:8])          # sin normal: hereda
        assert np.allclose(fila[12:16], (0.5, 1.0, 0.25, 0.9))
        assert fila[16] == 1.0

    def test_sin_iluminar_la_bandera_es_cero(self, lote) -> None:
        lote_gpu, _ctx = lote
        atlas = lote_gpu.registrar_atlas(_hoja((10, 10, 10)))
        lote_gpu.dibujar(atlas, (0, 0), (0, 0, 16, 16))
        assert lote_gpu._instancias[0][16] == 0.0

    def test_el_tinte_por_defecto_es_blanco_opaco(self, lote) -> None:
        lote_gpu, _ctx = lote
        atlas = lote_gpu.registrar_atlas(_hoja((10, 10, 10)))
        lote_gpu.dibujar(atlas, (0, 0), (0, 0, 16, 16))
        assert np.allclose(lote_gpu._instancias[0][12:16], (1, 1, 1, 1))

    def test_el_recorte_normal_propio_es_distinto_del_color(self, lote) -> None:
        lote_gpu, _ctx = lote
        atlas = lote_gpu.registrar_atlas(_hoja((10, 10, 10)))
        lote_gpu.dibujar(atlas, (0, 0), (0, 0, 16, 16),
                         normales_recorte=(32, 32, 16, 16))
        fila = lote_gpu._instancias[0]
        assert not np.allclose(fila[8:12], fila[4:8])

    def test_volcar_hace_una_sola_llamada_con_todas_las_instancias(self, lote) -> None:
        lote_gpu, ctx = lote
        atlas = lote_gpu.registrar_atlas(_hoja((10, 10, 10)))
        for i in range(5):
            lote_gpu.dibujar(atlas, (i * 4, 0), (0, 0, 16, 16))
        assert len(ctx.vaos) == 1
        vao = ctx.vaos[0]
        vao.renders.clear()
        cuantas = lote_gpu.volcar()
        assert cuantas == 5
        assert vao.renders == [{"instances": 5}]
        assert len(lote_gpu) == 0

    def test_el_buffer_de_instancias_se_escribe_antes_de_dibujar(self, lote) -> None:
        lote_gpu, ctx = lote
        atlas = lote_gpu.registrar_atlas(_hoja((10, 10, 10)))
        lote_gpu.dibujar(atlas, (1, 2), (0, 0, 16, 16))
        lote_gpu.volcar()
        vbo = ctx.buffers[2]  # 0 esquinas, 1 índices, 2 instancias
        assert len(vbo.escrituras) == 1
        filas = np.frombuffer(vbo.escrituras[0][0], dtype="f4").reshape(
            -1, _INSTANCIA_COLS)
        assert filas.shape[0] == 1
        assert filas[0, 0] == 1.0 and filas[0, 1] == 2.0

    def test_volcar_vacio_no_llama_a_render(self, lote) -> None:
        lote_gpu, ctx = lote
        vao = ctx.vaos[0]
        vao.renders.clear()
        assert lote_gpu.volcar() == 0
        assert vao.renders == []

    def test_el_lote_crece_sin_perder_las_ordenes_acumuladas(self, lote) -> None:
        lote_gpu, _ctx = lote
        atlas = lote_gpu.registrar_atlas(_hoja((10, 10, 10)))
        for i in range(10):
            lote_gpu.dibujar(atlas, (i, 0), (0, 0, 16, 16))
        assert len(lote_gpu) == 10
        assert lote_gpu._instancias.shape[0] == 16
        for i in range(10):
            assert lote_gpu._instancias[i, 0] == i


class TestElAtlasSubeComoTieneQueSubir:
    def test_el_atlas_se_sube_volteado_y_del_tamano_justo(self, lote) -> None:
        lote_gpu, ctx = lote
        hoja = _hoja((80, 160, 40))
        lote_gpu.registrar_atlas(hoja)
        textura = ctx.texturas[1]  # [0] es la normal plana
        assert textura.size == (64, 64)
        esperado = pygame.image.tobytes(hoja, "RGBA", True)
        assert textura.data == esperado, (
            "el atlas tiene que subir volteado o los sprites salen cabeza abajo"
        )

    def test_sin_atlas_de_normales_se_registra_solo_el_de_color(self, lote) -> None:
        lote_gpu, ctx = lote
        lote_gpu.registrar_atlas(_hoja((10, 10, 10)))
        assert len(ctx.texturas) == 2  # plana + color

    def test_el_atlas_de_normales_opcional_se_sube_igual(self, lote) -> None:
        lote_gpu, ctx = lote
        color = _hoja((10, 10, 10))
        normal = _hoja((128, 128, 255))
        lote_gpu.registrar_atlas(color, normales=normal)
        assert len(ctx.texturas) == 3
        assert ctx.texturas[2].data == pygame.image.tobytes(normal, "RGBA", True)

    def test_atlas_de_normales_de_otro_tamano_es_error(self, lote) -> None:
        lote_gpu, _ctx = lote
        normal = pygame.Surface((32, 32), pygame.SRCALPHA)
        with pytest.raises(ValueError):
            lote_gpu.registrar_atlas(_hoja((10, 10, 10)), normales=normal)

    def test_destruir_libera_texturas_vao_y_buffers(self, lote) -> None:
        lote_gpu, ctx = lote
        atlas = lote_gpu.registrar_atlas(_hoja((10, 10, 10)))
        assert atlas == 1
        lote_gpu.dibujar(atlas, (0, 0), (0, 0, 16, 16))
        lote_gpu.volcar()
        lote_gpu.destruir()
        assert all(t.liberada for t in ctx.texturas)
        assert ctx.vaos[0].liberado


class TestLaCamaraYLuzesLleganAlShader:
    def test_la_camara_se_resta_en_el_sombreador_no_en_la_cpu(self, lote) -> None:
        lote_gpu, _ctx = lote
        lote_gpu.set_camara(50, 30)
        assert lote_gpu._programa["camara"].value == (50.0, 30.0)

    def test_la_direccional_se_normaliza_antes_de_subir(self, lote) -> None:
        lote_gpu, _ctx = lote
        lote_gpu.set_luz_direccional((3, 4, 0), (1, 1, 1))
        assert np.allclose(
            lote_gpu._programa["luz_dir_direccion"].value, (0.6, 0.8, 0.0))
        assert lote_gpu._programa["luz_dir_color"].value == (1, 1, 1)

    def test_los_focos_se_recortan_al_maximo_del_shader(self, lote) -> None:
        lote_gpu, _ctx = lote
        muchos = [((i * 10.0, 0.0), (1.0, 0.0, 0.0), 40.0, 20.0)
                  for i in range(SPRITE_MAX_FOCOS + 2)]
        lote_gpu.set_focos(muchos)
        programa = lote_gpu._programa
        assert programa["n_focos"].value == SPRITE_MAX_FOCOS
        for i in range(SPRITE_MAX_FOCOS):
            assert programa[f"foco_pos[{i}]"].value == (i * 10.0, 0.0)


class TestNormalesProcedurales:
    def test_una_superficie_plana_da_normal_azul(self) -> None:
        s = pygame.Surface((32, 32), pygame.SRCALPHA)
        s.fill((255, 0, 0, 255))
        normal = generar_normales_desde_alfa(s)
        # Alfa uniforme: pendiente cero en todo el sprite, normal (0,0,1)
        # encodada como (0.5, 0.5, 1.0) → azul puro.
        px = pygame.image.tobytes(normal, "RGBA", False)[0:4]
        assert abs(px[0] - 128) <= 1, f"nx = {px[0]}"
        assert abs(px[1] - 128) <= 1, f"ny = {px[1]}"
        assert px[2] == 255

    @staticmethod
    def _canal(normal: pygame.Surface, canal: int) -> np.ndarray:
        """Un canal entero como array, fila a fila (píxel (x, y) = [y*W + x])."""
        rgba = pygame.image.tobytes(normal, "RGBA", False)
        return np.frombuffer(rgba[canal::4], np.uint8).astype(int)

    def test_un_escalon_vertical_inclina_la_normal_hacia_el_bulto(self) -> None:
        # Alfa 0 a la izquierda, 255 a la derecha: un bulto. En su cara
        # izquierda la pendiente baja hacia la derecha, y la normal debe
        # mirar hacia el bulto: nx < 0 → canal rojo por debajo de 128.
        s = pygame.Surface((64, 64), pygame.SRCALPHA)
        s.fill((255, 255, 255, 0))
        s.fill((255, 255, 255, 255), pygame.Rect(32, 0, 32, 64))
        rojo = self._canal(generar_normales_desde_alfa(s), 0)
        cara = [rojo[y * 64 + 31] for y in range(64)]
        assert float(np.mean(cara)) < 124, (
            "la cara izquierda del bulto tiene que mirar a la izquierda"
        )

    def test_un_escalon_horizontal_inclina_la_normal_hacia_arriba(self) -> None:
        # Alfa 0 arriba, 255 abajo: en la cara superior la normal mira hacia
        # arriba: ny > 0 → canal verde por encima de 128.
        s = pygame.Surface((64, 64), pygame.SRCALPHA)
        s.fill((255, 255, 255, 0))
        s.fill((255, 255, 255, 255), pygame.Rect(0, 32, 64, 32))
        verde = self._canal(generar_normales_desde_alfa(s), 1)
        cara = [verde[31 * 64 + x] for x in range(64)]
        assert float(np.mean(cara)) > 131, (
            "la cara superior del bulto tiene que mirar hacia arriba"
        )

    def test_la_fuerza_exagera_la_pendiente(self) -> None:
        s = pygame.Surface((64, 64), pygame.SRCALPHA)
        s.fill((255, 255, 255, 0))
        s.fill((255, 255, 255, 255), pygame.Rect(32, 0, 32, 64))
        rojo_1 = self._canal(generar_normales_desde_alfa(s, fuerza=1.0), 0)
        rojo_4 = self._canal(generar_normales_desde_alfa(s, fuerza=4.0), 0)
        cara_1 = [rojo_1[y * 64 + 31] for y in range(64)]
        cara_4 = [rojo_4[y * 64 + 31] for y in range(64)]
        dev_1 = abs(float(np.mean(cara_1)) - 128.0)
        dev_4 = abs(float(np.mean(cara_4)) - 128.0)
        assert dev_4 > dev_1 * 1.25, (
            f"más fuerza tiene que inclinar más la normal: {dev_1} → {dev_4}"
        )

    def test_las_normales_salen_unitarias(self) -> None:
        s = pygame.Surface((16, 16), pygame.SRCALPHA)
        s.fill((255, 255, 255, 255))
        for x in range(0, 16, 2):
            s.fill((255, 255, 255, 0), pygame.Rect(x, 0, 1, 16))
        normal = generar_normales_desde_alfa(s)
        rgba = np.frombuffer(
            pygame.image.tobytes(normal, "RGBA", False), np.uint8,
        ).reshape(-1, 4).astype(np.float32)
        n = rgba[:, :3] / 255.0 * 2.0 - 1.0
        norma = np.sqrt(np.sum(n * n, axis=1))
        assert float(np.max(np.abs(norma - 1.0))) < 1e-2

    def test_el_mapa_es_del_tamano_del_sprite_y_opaco(self) -> None:
        s = pygame.Surface((40, 30), pygame.SRCALPHA)
        s.fill((255, 255, 255, 255))
        normal = generar_normales_desde_alfa(s)
        assert normal.get_size() == (40, 30)
        alfa = np.frombuffer(
            pygame.image.tobytes(normal, "RGBA", False), np.uint8,
        )[3::4]
        assert float(np.min(alfa)) == 255
