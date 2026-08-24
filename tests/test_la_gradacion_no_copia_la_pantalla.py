"""AUD-496 — la gradación de color se comía dos tercios del fotograma.

`tests/test_stage4_1.py::TestCabeEnElPresupuestoDeFotograma` llevaba tiempo
en rojo (medido: ~47 ms de dibujo contra 15 de presupuesto, y 60 ms en el
commit AUD-476). Un perfil dijo dónde estaba: `post_processing.apply`, unos
28-30 ms, casi todo en la gradación.

El desglose de esos 30 ms fue lo interesante: la multiplicación de matrices
cuesta 5,4 ms y los otros ~25 son **mover los datos** —tres `astype(int32)`
sobre una vista no contigua de la superficie y tres escrituras de vuelta—.
Así que no había nada que ganar optimizando la aritmética: había que dejar
de copiar la pantalla tres veces.

Y no es sólo el 4-1: `DELEGABLES` (`src/engine/core/gpu_effects.py`) sólo
cubre bloom, viñeta y agua, así que la gradación corre en la CPU **también
con GL activo**, en cualquier escenario que la use.

Lo que se comprueba aquí
========================
Lo único que permite sustituir una implementación por otra: que den
exactamente el mismo píxel. Y que la matriz identidad —a la que se llega
interpolando hacia «color pleno»— no cueste una pasada entera de pantalla
para no cambiar nada.
"""
from __future__ import annotations

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import numpy as np
import pygame
import pytest

from src.framework.vfx.gradacion import (
    MATRIZ_IDENTIDAD,
    _con_numpy,
    acelerada,
    aplicar_gradacion,
    precalentar,
)

#: Las cinco matrices reales del 4-1 (`src/stages/stage4_1/fases.py`) más una
#: saturada a propósito, para que el recorte a 0-255 entre en juego.
MATRICES = {
    "blanco_y_negro": (87, 172, 33, 87, 172, 33, 87, 172, 33),
    "grises_neutros": (76, 150, 29, 76, 150, 29, 76, 150, 29),
    "sepia_vintage": (100, 196, 48, 89, 175, 43, 69, 136, 33),
    "nocturno_azulado": (71, 140, 26, 56, 110, 26, 51, 89, 140),
    "identidad": MATRIZ_IDENTIDAD,
    "desbordada": (400, 400, 400, 400, 400, 400, 400, 400, 400),
}


def _lienzo(ancho: int = 97, alto: int = 61) -> np.ndarray:
    """Ruido reproducible. Tamaño primo a propósito: un múltiplo de 8 o de 16
    escondería un error de borde en un núcleo que procese de a bloques."""
    rng = np.random.default_rng(20260815)
    return rng.integers(0, 256, (ancho, alto, 3), dtype=np.uint8)


class TestLasDosRutasDanElMismoPixel:
    """Si difieren aunque sea en un píxel, no se pueden intercambiar y el
    juego se vería distinto según qué extras tenga instalado quien juega."""

    @pytest.mark.parametrize("nombre", sorted(MATRICES))
    def test_identicas(self, nombre: str) -> None:
        matriz = MATRICES[nombre]
        base = _lienzo()
        por_numpy = base.copy()
        _con_numpy(por_numpy, matriz)
        por_la_rapida = base.copy()
        aplicar_gradacion(por_la_rapida, matriz)
        distintos = int(np.count_nonzero(por_numpy != por_la_rapida))
        assert distintos == 0, (
            f"{nombre}: {distintos} componentes distintos entre la ruta de "
            f"numpy y la acelerada"
        )

    def test_los_extremos_tambien(self) -> None:
        """Negro, blanco y los tres primarios puros: donde el recorte y la
        división entera se comportan distinto si el tipo no coincide."""
        base = np.array(
            [[(0, 0, 0), (255, 255, 255), (255, 0, 0)],
             [(0, 255, 0), (0, 0, 255), (128, 128, 128)]],
            dtype=np.uint8,
        )
        for matriz in MATRICES.values():
            a, b = base.copy(), base.copy()
            _con_numpy(a, matriz)
            aplicar_gradacion(b, matriz)
            assert np.array_equal(a, b), f"difieren con {matriz}"


class TestLaIdentidadNoCuesta:
    def test_no_toca_los_pixeles(self) -> None:
        base = _lienzo()
        copia = base.copy()
        aplicar_gradacion(copia, MATRIZ_IDENTIDAD)
        assert np.array_equal(base, copia)

    def test_post_processing_la_trata_como_ausencia(self) -> None:
        """Es a lo que se llega interpolando hacia «color pleno»: sin esto,
        todo el tramo final de la Fase 6 aplica una matriz sin efecto."""
        from src.framework.vfx.post_processing import PostProcessing

        pp = PostProcessing()
        pp.set_color_grading(*MATRIZ_IDENTIDAD)
        assert pp._color_grading is None, (
            "la identidad se guardó como gradación activa: cuesta una pasada "
            "por los 480 000 píxeles de la pantalla para no cambiar ninguno"
        )

    def test_una_matriz_de_verdad_si_se_guarda(self) -> None:
        """Sin esto, la prueba de arriba pasaría con un `set` que no guarda."""
        from src.framework.vfx.post_processing import PostProcessing

        pp = PostProcessing()
        pp.set_color_grading(*MATRICES["sepia_vintage"])
        assert pp._color_grading == MATRICES["sepia_vintage"]


class TestLaGradacionSigueDibujando:
    """El riesgo de acelerar algo es apagarlo sin querer."""

    def test_el_sepia_cambia_la_pantalla(self) -> None:
        base = _lienzo()
        despues = base.copy()
        aplicar_gradacion(despues, MATRICES["sepia_vintage"])
        assert not np.array_equal(base, despues)

    def test_el_blanco_y_negro_deja_los_tres_canales_iguales(self) -> None:
        """La comprobación de que hace lo que dice: una matriz de luminancia
        tiene que producir gris, no un color cualquiera."""
        base = _lienzo()
        aplicar_gradacion(base, MATRICES["blanco_y_negro"])
        assert np.array_equal(base[:, :, 0], base[:, :, 1])
        assert np.array_equal(base[:, :, 1], base[:, :, 2])

    def test_aplicado_sobre_una_superficie_real(self) -> None:
        """Lo que hace `PostProcessing.apply`: escribir en la vista de la
        superficie es escribir en la pantalla."""
        pygame.init()
        if pygame.display.get_surface() is None:
            pygame.display.set_mode((64, 64))
        surf = pygame.Surface((32, 32))
        surf.fill((200, 100, 50))
        vista = pygame.surfarray.pixels3d(surf)
        try:
            aplicar_gradacion(vista, MATRICES["blanco_y_negro"])
        finally:
            del vista
        r, g, b, _a = surf.get_at((5, 5))
        assert r == g == b, f"el gris no llegó a la superficie: {(r, g, b)}"


class TestLaRutaRapidaEsOpcional:
    def test_precalentar_no_revienta_sin_numba(self) -> None:
        """numba es un extra (`accel`). Sin él el juego funciona igual, sólo
        que más despacio — la misma regla que la invariante 7 aplica a
        scikit-learn."""
        assert precalentar() is acelerada()

    def test_sin_numba_sigue_habiendo_gradacion(self, monkeypatch) -> None:
        import src.framework.vfx.gradacion as modulo

        monkeypatch.setattr(modulo, "_nucleo", None)
        monkeypatch.setattr(modulo, "_numba_intentado", True)
        base = _lienzo()
        esperado = base.copy()
        _con_numpy(esperado, MATRICES["sepia_vintage"])
        obtenido = base.copy()
        modulo.aplicar_gradacion(obtenido, MATRICES["sepia_vintage"])
        assert np.array_equal(esperado, obtenido)
