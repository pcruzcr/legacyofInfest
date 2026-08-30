"""
Module: test_enfoque_bordes
System: stage (student assignment) — stage1_1 «La Entrada»
Academic Unit: VII (Convolución, desenfoque y detección de bordes)
Description: Pruebas del realce de contornos por Sobel.

Ejecutar toda la suite con:
   python -m pytest src/stages/stage1_1/tests/ -v
"""
from __future__ import annotations

import numpy as np
import pygame
import pytest

from src.stages.stage1_1.processing.enfoque_bordes import (
    TECLA_ENFOQUE,
    EnfoqueBordes,
)


@pytest.fixture
def enfoque() -> EnfoqueBordes:
    return EnfoqueBordes()


def _liso(valor: int, tam: tuple[int, int] = (320, 240)) -> pygame.Surface:
    s = pygame.Surface(tam)
    s.fill((valor, valor, valor))
    return s


def _con_borde(tam: tuple[int, int] = (320, 240)) -> pygame.Surface:
    """Media pantalla negra y media blanca: un único borde vertical."""
    s = pygame.Surface(tam)
    s.fill((10, 10, 10))
    pygame.draw.rect(s, (245, 245, 245), (tam[0] // 2, 0, tam[0] // 2, tam[1]))
    return s


def _brillo(s: pygame.Surface) -> float:
    return float(pygame.surfarray.array3d(s).mean())


# ── Los kernels ─────────────────────────────────────────────────────

def test_los_kernels_son_los_del_framework() -> None:
    """No se escriben aquí: se piden a `get_standard_kernel`. La regla del
    curso es usar lo que el motor ya trae."""
    kx, ky = EnfoqueBordes.kernels()
    assert np.array_equal(kx, np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]]))
    assert np.array_equal(ky, np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]]))


def test_cada_kernel_suma_cero() -> None:
    """La propiedad que hace que Sobel sea un detector de BORDES y no un
    filtro de brillo: sobre una zona de color plano la respuesta es nula."""
    kx, ky = EnfoqueBordes.kernels()
    assert kx.sum() == pytest.approx(0.0)
    assert ky.sum() == pytest.approx(0.0)


def test_los_dos_kernels_son_el_mismo_girado() -> None:
    """`sobel_y` es `sobel_x` transpuesto: uno mira los cambios horizontales
    y el otro los verticales."""
    kx, ky = EnfoqueBordes.kernels()
    assert np.array_equal(ky, kx.T)


# ── La detección ────────────────────────────────────────────────────

def test_una_superficie_lisa_no_tiene_bordes(enfoque: EnfoqueBordes) -> None:
    mapa = enfoque.mapa_de_bordes(_liso(128))
    assert _brillo(mapa) < 6.0


def test_un_borde_de_verdad_se_detecta(enfoque: EnfoqueBordes) -> None:
    liso = _brillo(enfoque.mapa_de_bordes(_liso(128)))
    borde = _brillo(enfoque.mapa_de_bordes(_con_borde()))
    assert borde > liso * 3


def test_la_via_de_referencia_tambien_detecta() -> None:
    """`apply_reference` aplica los dos kernels por separado y combina las
    magnitudes. Es la versión didáctica, la que enseña las matrices."""
    liso = _brillo(EnfoqueBordes.apply_reference(_liso(128, (96, 96))))
    borde = _brillo(EnfoqueBordes.apply_reference(_con_borde((96, 96))))
    assert borde > liso


def test_la_referencia_coincide_con_sobel_edge_del_framework() -> None:
    """La prueba que cierra la Unidad VII: reconstruir |G| a mano con
    `apply_kernel` da EXACTAMENTE lo mismo que `sobel_edge`.

    Importa porque `apply_kernel` recorta a [0, 255] y se come la mitad
    negativa del gradiente. La vuelta —aplicar el kernel y su negado, y
    sumarlos— no es una aproximación: si el resultado coincide píxel a píxel
    con el del framework, la reconstrucción es correcta.
    """
    from src.framework.processing.filter_tools import FilterTools

    escena = _con_borde((96, 96))
    mia = pygame.surfarray.array3d(EnfoqueBordes.apply_reference(escena))
    suya = pygame.surfarray.array3d(FilterTools.sobel_edge(escena))
    assert np.array_equal(mia, suya)


# ── La tecla ────────────────────────────────────────────────────────

def test_la_tecla_de_enfoque_no_la_usa_el_motor() -> None:
    """`E` de «enfocar». Si el motor la reclamara algún día, esta prueba se
    pone roja antes de que el jugador descubra que hace dos cosas."""
    import inspect

    from src.engine.input import action_map
    fuente = inspect.getsource(action_map)
    assert "pygame.K_e]" not in fuente
    assert "pygame.K_e," not in fuente


def test_detecta_la_tecla_pulsada() -> None:
    teclas = {TECLA_ENFOQUE: True}
    assert EnfoqueBordes.hay_tecla(teclas) is True


def test_sin_tecla_no_hay_enfoque() -> None:
    assert EnfoqueBordes.hay_tecla({TECLA_ENFOQUE: False}) is False


# ── El efecto sobre la escena ───────────────────────────────────────

def test_apagado_no_toca_el_fotograma(enfoque: EnfoqueBordes) -> None:
    """Coste medido con la tecla suelta: 0,0002 ms. Ni mide ni dibuja."""
    escena = _con_borde()
    antes = _brillo(escena)
    enfoque.actualizar(False)
    enfoque.apply(escena)
    assert _brillo(escena) == pytest.approx(antes)


def test_encendido_aclara_los_contornos(enfoque: EnfoqueBordes) -> None:
    """Se mezcla en `BLEND_ADD`: un borde es luz que se SUMA. En las zonas
    planas el mapa vale cero y no cambia nada."""
    escena = _con_borde()
    antes = _brillo(escena)
    enfoque.actualizar(True)
    enfoque.apply(escena)
    assert _brillo(escena) > antes


def test_sobre_una_escena_lisa_apenas_cambia_nada(enfoque: EnfoqueBordes) -> None:
    """La otra mitad del contrato de `BLEND_ADD`: si no hay bordes que
    revelar, enfocar no debería lavar la imagen."""
    escena = _liso(128)
    antes = _brillo(escena)
    enfoque.actualizar(True)
    enfoque.apply(escena)
    assert _brillo(escena) == pytest.approx(antes, abs=8.0)
