"""AUD-301 y AUD-302 — `SpriteBatch`, con la medición que lo justifica.

Lo que la medición dijo, con las dos tarjetas
---------------------------------------------
`scripts/bench_sprite_batch.py` (AUD-301) midió las tres rutas en las **dos**
tarjetas del equipo, y la diferencia entre ellas resultó ser la mitad del
asunto. Milisegundos:

    sprites   CPU blits()   Intel GPU   Quadro GPU   Quadro +bajar
        500         0,651       1,145        0,202           1,906
      2.000         4,014       2,109        0,330           1,454
      8.000        16,882       5,177        0,898           2,020

* `blits()` gana siempre a los blits sueltos. Eso es esta clase.
* **La Quadro dibuja 8.000 sprites en 0,898 ms; la Intel tarda 5,177.** Y el
  juego coge la Intel salvo que se dé de alta `python.exe` como «alto
  rendimiento»: ni SDL ni ModernGL eligen la dedicada por su cuenta.
* **Predije mal la lectura de vuelta.** Escribí que en una tarjeta discreta
  sería peor por cruzar el bus PCIe; medido, es tres veces mejor. Con la
  Quadro, la GPU gana también con lectura a partir de unos 1.500 sprites.

No hay ruta de GPU en el motor, y ahora por el motivo correcto: **el juego no
llega a esos números**. Un escenario real dibuja unas veinte entidades, y a 500
sprites la CPU todavía gana. El día que el fotograma entero viva en la tarjeta
—sin lectura de vuelta— la GPU gana desde el primer sprite: 4,2× con 500.

En el juego, medido en nuestros dos mapas
------------------------------------------
`stage4_1` pasa de **6,42 a 5,93 ms** de dibujado (1,08×) y `stage0` se queda
dentro del ruido. La diferencia entre los dos no es casualidad: el lote se usa
donde el número de llamadas **crece con el contenido** —un degradado por foco y
una sombra por entidad—, y 4-1 tiene más focos.
"""
from __future__ import annotations

import pygame
import pytest

from src.engine.render.sprite_batch import SpriteBatch


@pytest.fixture(autouse=True)
def _video():
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((800, 600))


@pytest.fixture
def destino() -> pygame.Surface:
    s = pygame.Surface((100, 100))
    s.fill((0, 0, 0))
    return s


def _cuadro(color: tuple[int, int, int], lado: int = 10) -> pygame.Surface:
    s = pygame.Surface((lado, lado))
    s.fill(color)
    return s


class TestLoQueDibuja:
    def test_un_lote_vacio_no_dibuja_nada(self, destino) -> None:
        assert SpriteBatch().volcar(destino) == 0
        assert destino.get_at((5, 5))[:3] == (0, 0, 0)

    def test_dibuja_lo_encolado(self, destino) -> None:
        lote = SpriteBatch()
        lote.dibujar(_cuadro((255, 0, 0)), (0, 0))
        assert lote.volcar(destino) == 1
        assert destino.get_at((5, 5))[:3] == (255, 0, 0)

    def test_da_el_mismo_resultado_que_blit_a_blit(self) -> None:
        """La condición para poder sustituir un bucle por un lote."""
        piezas = [(_cuadro((10 * i, 200 - 10 * i, 50)), (i * 7, i * 3))
                  for i in range(8)]

        uno = pygame.Surface((100, 100))
        uno.fill((0, 0, 0))
        for origen, pos in piezas:
            uno.blit(origen, pos)

        otro = pygame.Surface((100, 100))
        otro.fill((0, 0, 0))
        lote = SpriteBatch()
        for origen, pos in piezas:
            lote.dibujar(origen, pos)
        lote.volcar(otro)

        assert pygame.image.tobytes(uno, "RGBA") == pygame.image.tobytes(otro, "RGBA")

    def test_respeta_el_orden(self, destino) -> None:
        """El orden es el de encolado, igual que llamando a `blit` seguido.
        Ordenar por profundidad sigue siendo de quien dibuja."""
        lote = SpriteBatch()
        lote.dibujar(_cuadro((255, 0, 0)), (0, 0))
        lote.dibujar(_cuadro((0, 255, 0)), (0, 0))
        lote.volcar(destino)
        assert destino.get_at((5, 5))[:3] == (0, 255, 0)

    def test_admite_origenes_distintos(self, destino) -> None:
        """Un lote puede llevar catorce degradados distintos: lo que se ahorra
        no es el cambio de textura, son las catorce vueltas del intérprete."""
        lote = SpriteBatch()
        lote.dibujar(_cuadro((255, 0, 0)), (0, 0))
        lote.dibujar(_cuadro((0, 0, 255)), (20, 0))
        assert lote.volcar(destino) == 2
        assert destino.get_at((5, 5))[:3] == (255, 0, 0)
        assert destino.get_at((25, 5))[:3] == (0, 0, 255)

    def test_admite_area_y_banderas(self, destino) -> None:
        lote = SpriteBatch()
        lote.dibujar(_cuadro((100, 100, 100), 20), (0, 0),
                     pygame.Rect(0, 0, 5, 5), pygame.BLEND_RGB_ADD)
        assert lote.volcar(destino) == 1
        assert destino.get_at((2, 2))[:3] == (100, 100, 100)
        assert destino.get_at((10, 10))[:3] == (0, 0, 0), "el área no se respetó"


class TestElCicloDeVida:
    def test_volcar_vacia_el_lote(self, destino) -> None:
        lote = SpriteBatch()
        lote.dibujar(_cuadro((255, 0, 0)), (0, 0))
        lote.volcar(destino)
        assert len(lote) == 0
        assert lote.volcar(destino) == 0, "el lote repitió lo ya dibujado"

    def test_limpiar_tira_sin_dibujar(self, destino) -> None:
        lote = SpriteBatch()
        lote.dibujar(_cuadro((255, 0, 0)), (0, 0))
        lote.limpiar()
        lote.volcar(destino)
        assert destino.get_at((5, 5))[:3] == (0, 0, 0)

    def test_se_vacia_aunque_el_volcado_falle(self) -> None:
        """Un lote que conserva sus órdenes tras un error las repetiría al
        fotograma siguiente, y un sprite duplicado una vez cada mil fotogramas
        no se reproduce nunca."""
        class _Roto:
            def blits(self, *_a, **_k):
                raise pygame.error("superficie muerta")

        lote = SpriteBatch()
        lote.dibujar(_cuadro((255, 0, 0)), (0, 0))
        with pytest.raises(pygame.error):
            lote.volcar(_Roto())
        assert len(lote) == 0


class TestLasSombras:
    def test_la_elipse_se_reutiliza(self) -> None:
        """Antes se creaba una `Surface` y se rasterizaba una elipse por sombra
        y por fotograma, para pintar las mismas ocho del fotograma anterior."""
        from src.framework.vfx.sombras import Sombra

        sombra = Sombra()
        una = sombra._elipse(20, 7, 90)
        otra = sombra._elipse(20, 7, 90)
        assert una is otra

    def test_una_talla_distinta_es_otra_elipse(self) -> None:
        from src.framework.vfx.sombras import Sombra

        sombra = Sombra()
        assert sombra._elipse(20, 7, 90) is not sombra._elipse(24, 8, 90)

    def test_la_cache_no_crece_sin_fin(self) -> None:
        """En un salto se piden decenas de tallas: sin tope, la caché acabaría
        ocupando más que los sprites del juego."""
        from src.framework.vfx.sombras import _MAXIMO_DE_TALLAS, Sombra

        sombra = Sombra()
        for i in range(_MAXIMO_DE_TALLAS * 2):
            sombra._elipse(4 + i, 3 + i, 90)
        assert len(sombra._cache) <= _MAXIMO_DE_TALLAS

    def test_con_lote_encola_en_vez_de_dibujar(self, destino) -> None:
        from src.framework.vfx.sombras import Sombra

        lote = SpriteBatch()
        suelo = [pygame.Rect(0, 60, 100, 10)]
        Sombra().dibujar(destino, pygame.Rect(40, 40, 20, 20), suelo,
                         pygame.Vector2(0, 0), lote)
        assert len(lote) == 1
        assert destino.get_at((50, 60))[:3] == (0, 0, 0), "dibujó sin volcar"

    def test_sin_lote_dibuja_como_siempre(self, destino) -> None:
        """Las entregas llaman a esto por su cuenta y sin lote."""
        from src.framework.vfx.sombras import Sombra

        destino.fill((255, 255, 255))
        suelo = [pygame.Rect(0, 60, 100, 10)]
        Sombra().dibujar(destino, pygame.Rect(40, 40, 20, 20), suelo,
                         pygame.Vector2(0, 0))
        assert destino.get_at((50, 60))[:3] != (255, 255, 255)


class TestLaIluminacion:
    def test_con_obstaculos_no_se_agrupa(self) -> None:
        """Con sombras proyectadas, la de cada luz se resta justo después de
        sumarla (AUD-278). Agruparlas borraría la luz de focos que ese muro no
        tapa."""
        import inspect

        from src.framework.vfx import lighting

        fuente = inspect.getsource(lighting.LightSystem.render)
        assert "por_lotes = not self._obstaculos" in fuente

    def test_sin_obstaculos_los_focos_se_ven_igual(self) -> None:
        """La condición para haber podido agruparlos."""
        from src.framework.vfx.lighting import LightSource, LightSystem

        def pintar(por_lotes: bool) -> bytes:
            sistema = LightSystem()
            sistema.ambient_brightness = 0.5
            for x in (100, 300, 500):
                sistema.add_light(LightSource(
                    position=pygame.Vector2(x, 200), radius=80,
                    color=(255, 220, 180), intensity=0.8))
            if not por_lotes:
                # Se le da un obstáculo lejísimos: fuerza el camino de uno en
                # uno sin cambiar un solo píxel de las tres luces.
                sistema.set_obstaculos([pygame.Rect(-9000, -9000, 1, 1)])
            destino = pygame.Surface((800, 600))
            destino.fill((255, 255, 255))
            sistema.render(destino, pygame.Vector2(0, 0))
            return pygame.image.tobytes(destino, "RGB")

        assert pintar(True) == pintar(False)
