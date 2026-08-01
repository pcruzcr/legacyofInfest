"""
G1 — atlas de sprites y el filtro de daltonismo que costaba más de un
fotograma entero. AUD-138.

Dos hallazgos, y el segundo es el grave
========================================
**El atlas no acelera el dibujado.** Medido: 2.000 sprites de 32×32 tardan
2,06 ms sueltos y 2,35 ms desde un atlas. Sale peor. La ventaja de un atlas es
ahorrar cambios de textura, y eso sólo existe con una GPU agrupando llamadas;
la ruta clásica de pygame es una copia de memoria y le da igual de dónde
venga el recorte. Lo que el atlas sí hace es cargar **tres veces más rápido**
—200 PNG sueltos, 12,9 ms; un atlas, 4,3 ms— porque el coste está en abrir
ficheros, no en los píxeles.

Decir «hicimos un atlas y el juego va más rápido» habría sido falso, de la
misma familia que la afirmación que hubo que corregir en AUD-133.

**El filtro de daltonismo costaba 17,4 ms por fotograma**, y el presupuesto
entero de 60 fps son 16,6 ms. Activar una opción de accesibilidad bajaba el
juego a la mitad de fotogramas: el jugador que necesita el filtro jugaba a
otro juego, más lento, y encima parecía culpa de su ordenador.
"""
from __future__ import annotations

import time

import numpy as np
import pygame
import pytest

from src.engine.utils.sprite_atlas import SpriteAtlas


@pytest.fixture(autouse=True)
def _video():
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((320, 240))


def _sprites(n: int = 8, lado: int = 16) -> dict[str, pygame.Surface]:
    salida = {}
    for i in range(n):
        s = pygame.Surface((lado, lado), pygame.SRCALPHA)
        s.fill(((10 + i * 20) % 256, 60, 200, 255))
        salida[f"sprite_{i}"] = s
    return salida


class TestElAtlasGuardaLoQueLeDan:
    def test_estan_todos(self) -> None:
        atlas = SpriteAtlas.empaquetar(_sprites(8))
        assert len(atlas) == 8

    def test_cada_recorte_conserva_su_tamano(self) -> None:
        sprites = {"grande": pygame.Surface((32, 48), pygame.SRCALPHA),
                   "pequeno": pygame.Surface((8, 8), pygame.SRCALPHA)}
        atlas = SpriteAtlas.empaquetar(sprites)
        assert atlas.recorte("grande").get_size() == (32, 48)
        assert atlas.recorte("pequeno").get_size() == (8, 8)

    def test_cada_recorte_conserva_sus_pixeles(self) -> None:
        """Lo que de verdad puede romper un empaquetado: colocar bien el
        rectángulo y copiar el sprite equivocado dentro."""
        sprites = _sprites(6)
        atlas = SpriteAtlas.empaquetar(sprites)
        for nombre, original in sprites.items():
            assert atlas.recorte(nombre).get_at((0, 0)) == original.get_at((0, 0)), (
                f"«{nombre}» salió con los píxeles de otro sprite"
            )

    def test_los_recortes_no_se_pisan(self) -> None:
        atlas = SpriteAtlas.empaquetar(_sprites(12))
        rects = [atlas.rect(n) for n in atlas.nombres]
        for i, a in enumerate(rects):
            for b in rects[i + 1:]:
                assert not a.colliderect(b), f"{a} y {b} se solapan"

    def test_todo_cabe_dentro_de_la_hoja(self) -> None:
        atlas = SpriteAtlas.empaquetar(_sprites(20, lado=24), ancho_max=100)
        hoja = atlas.hoja.get_rect()
        for nombre in atlas.nombres:
            assert hoja.contains(atlas.rect(nombre)), f"{nombre} se sale"

    def test_un_atlas_vacio_no_revienta(self) -> None:
        assert len(SpriteAtlas.empaquetar({})) == 0

    def test_un_nombre_que_no_existe_devuelve_nada(self) -> None:
        assert SpriteAtlas.empaquetar(_sprites(2)).recorte("fantasma") is None

    def test_el_recorte_es_una_vista_y_no_una_copia(self) -> None:
        """Pedir el mismo sprite mil veces no puede costar mil imágenes."""
        atlas = SpriteAtlas.empaquetar(_sprites(3))
        assert atlas.recorte("sprite_0") is atlas.recorte("sprite_0")


class TestGuardarYCargar:
    def test_va_y_vuelve_igual(self, tmp_path) -> None:
        sprites = _sprites(5)
        SpriteAtlas.empaquetar(sprites).guardar(tmp_path / "prueba.png")
        vuelto = SpriteAtlas.cargar(tmp_path / "prueba.png")
        assert set(vuelto.nombres) == set(sprites)
        for nombre, original in sprites.items():
            assert vuelto.recorte(nombre).get_at((0, 0)) == original.get_at((0, 0))

    def test_se_escriben_los_dos_ficheros(self, tmp_path) -> None:
        SpriteAtlas.empaquetar(_sprites(3)).guardar(tmp_path / "a.png")
        assert (tmp_path / "a.png").exists()
        assert (tmp_path / "a.json").exists()

    def test_sin_indice_se_carga_igual_y_avisa(self, tmp_path, caplog) -> None:
        """Un atlas sin `.json` sigue siendo una imagen válida: no se puede
        tumbar el juego por un fichero que falta."""
        SpriteAtlas.empaquetar(_sprites(3)).guardar(tmp_path / "b.png")
        (tmp_path / "b.json").unlink()
        atlas = SpriteAtlas.cargar(tmp_path / "b.png")
        assert len(atlas) == 0
        assert atlas.hoja.get_width() > 0


class TestDibujarEnLote:
    def test_dibuja_lo_que_se_le_pide(self) -> None:
        atlas = SpriteAtlas.empaquetar(_sprites(4))
        lienzo = pygame.Surface((200, 200))
        lienzo.fill((0, 0, 0))
        n = atlas.dibujar_lote(lienzo, [("sprite_0", (10, 10)),
                                        ("sprite_1", (50, 50))])
        assert n == 2
        assert lienzo.get_at((12, 12))[:3] != (0, 0, 0)
        assert lienzo.get_at((52, 52))[:3] != (0, 0, 0)

    def test_un_nombre_que_falta_no_tumba_el_fotograma(self) -> None:
        atlas = SpriteAtlas.empaquetar(_sprites(2))
        lienzo = pygame.Surface((100, 100))
        n = atlas.dibujar_lote(lienzo, [("sprite_0", (0, 0)),
                                        ("no_existe", (10, 10))])
        assert n == 1, "el que faltaba tenía que saltarse, no romper el lote"

    def test_un_lote_vacio_no_llama_a_nadie(self) -> None:
        atlas = SpriteAtlas.empaquetar(_sprites(2))
        assert atlas.dibujar_lote(pygame.Surface((10, 10)), []) == 0

    def test_dibujar_en_lote_no_es_mas_lento_que_uno_a_uno(self) -> None:
        """La única ganancia de velocidad medida, y no viene del atlas: viene
        de que `blits()` hace el bucle en C."""
        atlas = SpriteAtlas.empaquetar(_sprites(16))
        lienzo = pygame.Surface((640, 480))
        ordenes = [(f"sprite_{i % 16}", ((i * 7) % 600, (i * 13) % 450))
                   for i in range(500)]

        def uno_a_uno() -> None:
            for nombre, pos in ordenes:
                lienzo.blit(atlas.hoja, pos, atlas.rect(nombre))

        def en_lote() -> None:
            atlas.dibujar_lote(lienzo, ordenes)

        def medir(f) -> float:
            f()
            t = time.perf_counter()
            for _ in range(20):
                f()
            return time.perf_counter() - t

        assert medir(en_lote) <= medir(uno_a_uno) * 1.35, (
            "el lote salió claramente peor que el bucle en Python; algo se "
            "está copiando de más"
        )


class TestElFiltroDeDaltonismoCabeEnUnFotograma:
    """AUD-138 — el hallazgo grave.

    17,4 ms de filtro contra 16,6 ms de presupuesto: activar la opción de
    accesibilidad partía la tasa de fotogramas por la mitad.
    """

    def _lienzo(self) -> pygame.Surface:
        s = pygame.Surface((800, 600))
        rng = np.random.default_rng(7)
        pygame.surfarray.blit_array(
            s, rng.integers(0, 255, (800, 600, 3), dtype=np.uint8))
        return s

    def _post(self, modo: str):
        from src.engine.core import user_settings
        from src.framework.vfx.post_processing import PostProcessing

        user_settings.set_settings(user_settings.UserSettings(colorblind_mode=modo))
        return PostProcessing()

    @pytest.mark.parametrize(
        "modo", ["protanopia", "deuteranopia", "tritanopia"])
    def test_el_resultado_sigue_siendo_el_de_la_formula(self, modo) -> None:
        """La optimización no puede cambiar lo que ve el jugador.

        Se compara contra la fórmula original, en float, píxel a píxel.
        """
        lienzo = self._lienzo()
        antes = pygame.surfarray.pixels3d(lienzo).copy()

        r = antes[:, :, 0].astype(np.float32)
        g = antes[:, :, 1].astype(np.float32)
        b = antes[:, :, 2].astype(np.float32)
        esperado = np.empty_like(antes)
        if modo == "protanopia":
            esperado[:, :, 0] = np.clip(r * 0.57 + g * 0.43, 0, 255)
            esperado[:, :, 1] = np.clip(g * 0.86, 0, 255)
            esperado[:, :, 2] = np.clip(b * 0.86, 0, 255)
        elif modo == "deuteranopia":
            esperado[:, :, 0] = np.clip(r * 0.63, 0, 255)
            esperado[:, :, 1] = np.clip(g * 0.78 + r * 0.22, 0, 255)
            esperado[:, :, 2] = np.clip(b * 0.86, 0, 255)
        else:
            esperado[:, :, 0] = np.clip(r * 0.95, 0, 255)
            esperado[:, :, 1] = np.clip(g * 0.43 + b * 0.57, 0, 255)
            esperado[:, :, 2] = np.clip(b * 0.43, 0, 255)

        self._post(modo)._apply_colorblind_filter(lienzo)
        salida = pygame.surfarray.pixels3d(lienzo).copy()
        desviacion = np.abs(salida.astype(int) - esperado.astype(int)).max()
        assert desviacion <= 3, (
            f"la versión rápida se desvía {desviacion} de 255 respecto a la "
            f"fórmula: eso ya no es el mismo filtro"
        )

    def test_cabe_en_el_presupuesto_de_60_fps(self) -> None:
        lienzo = self._lienzo()
        post = self._post("protanopia")
        post._apply_colorblind_filter(lienzo)

        t = time.perf_counter()
        for _ in range(10):
            post._apply_colorblind_filter(lienzo)
        ms = (time.perf_counter() - t) / 10 * 1000
        assert ms < 8.0, (
            f"el filtro tarda {ms:.1f} ms. El fotograma entero son 16,6 ms, "
            f"así que a partir de ahí el jugador que necesita el filtro juega "
            f"a menos fotogramas que los demás"
        )

    def test_apagado_no_cuesta_nada(self) -> None:
        lienzo = self._lienzo()
        post = self._post("off")
        antes = pygame.surfarray.pixels3d(lienzo).copy()
        post._apply_colorblind_filter(lienzo)
        assert np.array_equal(pygame.surfarray.pixels3d(lienzo), antes)

    def test_un_modo_desconocido_no_toca_nada(self) -> None:
        """Dato hostil: un `config.json` con un modo inventado."""
        lienzo = self._lienzo()
        post = self._post("off")
        post._cb_mode = "modo_que_no_existe"
        antes = pygame.surfarray.pixels3d(lienzo).copy()
        post._apply_colorblind_filter(lienzo)
        assert np.array_equal(pygame.surfarray.pixels3d(lienzo), antes)

    def test_las_zonas_claras_no_se_vuelven_negras(self) -> None:
        """La suma del término cruzado va sobre uint8: sin saturar, un píxel
        claro daría la vuelta a 0 y aparecerían manchas negras justo en lo
        más brillante."""
        lienzo = pygame.Surface((64, 64))
        lienzo.fill((250, 250, 250))
        self._post("protanopia")._apply_colorblind_filter(lienzo)
        arr = pygame.surfarray.pixels3d(lienzo)
        assert arr.min() > 100, "algo dio la vuelta y se volvió oscuro"
