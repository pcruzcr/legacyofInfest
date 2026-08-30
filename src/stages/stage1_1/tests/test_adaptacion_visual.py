"""
Module: test_adaptacion_visual
System: stage (student assignment) — stage1_1 «La Entrada»
Academic Unit: VII (Histograma, brillo y contraste)
Description: Pruebas de la auto-exposición dirigida por el histograma.

Ejecutar toda la suite con:
   python -m pytest src/stages/stage1_1/tests/ -v
"""
from __future__ import annotations

import numpy as np
import pygame
import pytest

from src.stages.stage1_1.processing.adaptacion_visual import AdaptacionVisual


@pytest.fixture
def ojo() -> AdaptacionVisual:
    return AdaptacionVisual()


def _liso(valor: int, tam: tuple[int, int] = (320, 240)) -> pygame.Surface:
    s = pygame.Surface(tam)
    s.fill((valor, valor, valor))
    return s


# ── La media a partir de los cajones ────────────────────────────────

def test_la_media_de_un_histograma_conocido() -> None:
    """La suma ponderada, comprobada contra un caso hecho a mano.

    Cien píxeles a 10 y cien a 200 dan (100·10 + 100·200) / 200 = 105.
    """
    cajones = np.zeros(256, dtype=np.int64)
    cajones[10] = 100
    cajones[200] = 100
    media = AdaptacionVisual.luminancia_media(
        {"luminance": cajones, "total_pixels": 200})
    assert media == pytest.approx(105.0)


def test_la_media_de_un_gris_liso_es_ese_gris(ojo: AdaptacionVisual) -> None:
    assert ojo.medir(_liso(90)) == pytest.approx(90.0, abs=1.5)


def test_reducir_no_cambia_la_media(ojo: AdaptacionVisual) -> None:
    """El argumento que justifica medir en 200x150 en vez de en 800x600.

    Si reducir cambiara la media, medir barato sería medir mal. Se comprueba
    con un degradado, no con un liso: un liso saldría igual de cualquier modo
    y la prueba no diría nada.
    """
    grande = pygame.Surface((800, 600))
    for x in range(800):
        v = int(x / 799 * 255)
        pygame.draw.line(grande, (v, v, v), (x, 0), (x, 599))
    chico = pygame.transform.scale(grande, AdaptacionVisual.TAM_MUESTRA)

    from src.framework.processing.filter_tools import FilterTools
    m_grande = AdaptacionVisual.luminancia_media(FilterTools.compute_histogram(grande))
    m_chico = AdaptacionVisual.luminancia_media(FilterTools.compute_histogram(chico))
    assert m_chico == pytest.approx(m_grande, abs=2.0)


# ── La decisión que el histograma dirige ────────────────────────────

def test_una_escena_oscura_pide_aclarar(ojo: AdaptacionVisual) -> None:
    """Fuera de la banda por abajo: el tunel de roca."""
    assert ojo.factor_objetivo(ojo.medir(_liso(35))) > 1.0


def test_una_escena_lavada_pide_oscurecer(ojo: AdaptacionVisual) -> None:
    """Fuera de la banda por arriba."""
    assert ojo.factor_objetivo(ojo.medir(_liso(210))) < 1.0


@pytest.mark.parametrize("gris", [62, 79, 88, 100, 108])
def test_dentro_de_la_banda_no_se_toca_nada(ojo: AdaptacionVisual, gris: int) -> None:
    """La prueba que nace de un fallo medido jugando.

    La primera version corregia SIEMPRE hacia un objetivo unico de 118. Con el
    bot del profesor se midio que este nivel vive entre 79 y 88, o sea que la
    correccion se quedaba clavada en el tope de 1,45 y lavaba el cielo y las
    colinas enteras. Una auto-exposicion que se come el arte que viene a
    proteger esta mal calibrada.

    Los grises de aqui cubren la banda y sus dos bordes: en ninguno se toca.
    """
    assert ojo.factor_objetivo(ojo.medir(_liso(gris))) == pytest.approx(1.0)


def test_la_correccion_esta_acotada(ojo: AdaptacionVisual) -> None:
    """Sin topes, una pantalla casi negra pediría un factor enorme y el túnel
    se vería como un negativo velado."""
    assert ojo.factor_objetivo(1.0) <= AdaptacionVisual.FACTOR_MAX
    assert ojo.factor_objetivo(255.0) >= AdaptacionVisual.FACTOR_MIN


def test_la_escena_oscura_se_detecta(ojo: AdaptacionVisual) -> None:
    ojo.medir(_liso(30))
    assert ojo.escena_oscura is True
    ojo.medir(_liso(150))
    assert ojo.escena_oscura is False


# ── El ritmo ────────────────────────────────────────────────────────

def test_solo_mide_uno_de_cada_N_fotogramas(ojo: AdaptacionVisual) -> None:
    """Medir cuesta 3,1 ms; hacerlo en los 60 fotogramas se comería el 19%
    del presupuesto para nada, porque la corrección avanza despacio."""
    oscura = _liso(35)
    medidos = sum(ojo.actualizar(oscura) for _ in range(AdaptacionVisual.CADA_N * 4))
    assert medidos == 4


def test_el_factor_no_salta_de_golpe(ojo: AdaptacionVisual) -> None:
    """Una exposición que cambia de un fotograma al siguiente se ve como un
    parpadeo. El ojo tarda; esto también."""
    oscura = _liso(35)
    for _ in range(AdaptacionVisual.CADA_N):
        ojo.actualizar(oscura)
    tras_una_medicion = ojo.factor
    assert 1.0 < tras_una_medicion < AdaptacionVisual.FACTOR_MAX


def test_acaba_llegando_al_objetivo(ojo: AdaptacionVisual) -> None:
    oscura = _liso(35)
    for _ in range(AdaptacionVisual.CADA_N * 80):
        ojo.actualizar(oscura)
    assert ojo.factor == pytest.approx(AdaptacionVisual.FACTOR_MAX, abs=0.02)


def test_una_escena_normal_deja_el_factor_en_uno(ojo: AdaptacionVisual) -> None:
    """El caso de todos los dias: el nivel bien pintado no se corrige."""
    normal = _liso(84)
    for _ in range(AdaptacionVisual.CADA_N * 30):
        ojo.actualizar(normal)
    assert ojo.factor == pytest.approx(1.0, abs=0.01)


def test_reiniciar_deja_el_ojo_neutro(ojo: AdaptacionVisual) -> None:
    for _ in range(AdaptacionVisual.CADA_N * 10):
        ojo.actualizar(_liso(35))
    ojo.reiniciar()
    assert ojo.factor == pytest.approx(1.0)


# ── Las dos vías coinciden ──────────────────────────────────────────

@pytest.mark.parametrize("gris", [33, 60, 120, 200])
@pytest.mark.parametrize("factor", [0.82, 0.90, 1.20, 1.45])
def test_la_via_rapida_es_la_misma_multiplicacion_que_la_de_referencia(
        gris: int, factor: float) -> None:
    """La vía rápida no aproxima: **multiplica**, igual que
    `adjust_brightness`. Sólo se separa por el redondeo a entero.

    Esta prueba nació de un fallo real. La primera versión aclaraba con un
    `BLEND_ADD` de `(f-1)*255`, o sea **sumando una constante**. Medido sobre
    el túnel: la media pasaba de 33 a 148 cuando el objetivo eran 118. Sumar
    115 a un píxel de 33 no es multiplicarlo por 1,45, es lavar las sombras.

    La versión buena descompone el producto en `s + s*(f-1)`: una copia
    atenuada con `BLEND_MULT` y sumada con `BLEND_ADD`.
    """
    ojo = AdaptacionVisual()
    ojo._factor = factor

    base = _liso(gris, (64, 64))
    rapida = base.copy()
    ojo.apply(rapida)
    referencia = ojo.apply_reference(base)

    def media(s: pygame.Surface) -> float:
        return float(pygame.surfarray.array3d(s).mean())

    assert media(rapida) == pytest.approx(media(referencia), abs=1.5)
    assert media(rapida) == pytest.approx(min(255.0, gris * factor), abs=1.5)
