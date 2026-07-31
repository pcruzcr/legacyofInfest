"""
Module: test_sunset_light
System: stage (student assignment) — stage1_1 «La Entrada»
Academic Unit: V (Color y transparencia)
Description: Conversion HSV, mezcla alfa y equivalencia con la via rapida.

Ejecutar toda la suite con:
   python -m pytest src/stages/stage1_1/tests/ -v
"""
from __future__ import annotations

import pygame
import pytest

from src.framework.processing.color_tools import ColorTools
from src.stages.stage1_1.processing.sunset_light import SunsetLight

# ════════════════════════════════════════════════════════════════════
# SunsetLight — Unidad V: conversión de espacio y transparencia
# ════════════════════════════════════════════════════════════════════

def _lienzo(color=(128, 128, 128), tam=(64, 48)) -> pygame.Surface:
    s = pygame.Surface(tam)
    s.fill(color)
    return s


def test_el_ambar_se_deriva_por_conversion_a_hsv() -> None:
    """El tinte no es una constante escrita a mano: se obtiene desplazando
    el MATIZ en espacio HSV y volviendo a RGB. Al reconvertirlo debe
    reaparecer el matiz de atardecer."""
    luz = SunsetLight()
    ambar = luz.amber_for(1.0)

    h, _s, _v = ColorTools.rgb_to_hsv(*ambar)
    assert h == pytest.approx(SunsetLight.HUE_AMBAR, abs=2.0)


def test_el_ambar_es_calido_mas_rojo_que_azul() -> None:
    r, g, b = SunsetLight().amber_for(1.0)
    assert r > g > b


def test_al_avanzar_el_atardecer_se_satura_y_oscurece() -> None:
    """Conforme cae la tarde el matiz se mantiene, sube la saturación y
    baja el valor."""
    luz = SunsetLight()
    _h0, s0, v0 = ColorTools.rgb_to_hsv(*luz.amber_for(0.0))
    _h1, s1, v1 = ColorTools.rgb_to_hsv(*luz.amber_for(1.0))

    assert s1 > s0
    assert v1 < v0


# ── Intensidad en función del avance del jugador ────────────────────

def test_la_intensidad_va_de_cero_a_uno() -> None:
    luz = SunsetLight()
    assert luz.strength(0.0) == pytest.approx(0.0, abs=1e-9)
    assert luz.strength(1.0) == pytest.approx(1.0, abs=1e-9)


def test_la_intensidad_no_es_lineal_usa_easing() -> None:
    """k = ease_out_quad(avance): el atardecer cae rápido al principio."""
    luz = SunsetLight()
    assert luz.strength(0.5) != pytest.approx(0.5, abs=1e-3)
    assert luz.strength(0.5) > 0.5          # ease_out arranca acelerado


def test_la_intensidad_se_acota_fuera_del_rango() -> None:
    luz = SunsetLight()
    assert luz.strength(-3.0) == pytest.approx(0.0, abs=1e-9)
    assert luz.strength(9.0) == pytest.approx(1.0, abs=1e-9)


# ── Aplicación sobre la superficie ──────────────────────────────────

def test_al_inicio_del_nivel_el_pase_no_altera_la_imagen() -> None:
    """Con avance 0 la mezcla es totalmente transparente."""
    luz = SunsetLight()
    antes = _lienzo()
    despues = _lienzo()

    luz.apply(despues, 0.0)

    assert despues.get_at((10, 10)) == antes.get_at((10, 10))


def test_al_final_del_nivel_la_imagen_se_vuelve_calida() -> None:
    """El efecto tiene que ser VISUALMENTE OBSERVABLE, que es lo que
    exige la rúbrica."""
    luz = SunsetLight()
    lienzo = _lienzo((128, 128, 128))
    r0, g0, b0, _ = lienzo.get_at((10, 10))

    luz.apply(lienzo, 1.0)
    r1, g1, b1, _ = lienzo.get_at((10, 10))

    assert (r1 - b1) > (r0 - b0)        # se calienta: más rojo que azul
    assert (r1, g1, b1) != (r0, g0, b0)  # y cambia de verdad


def test_el_pase_conserva_el_tamano_de_la_superficie() -> None:
    luz = SunsetLight()
    lienzo = _lienzo(tam=(320, 224))
    luz.apply(lienzo, 0.8)
    assert lienzo.get_size() == (320, 224)


def test_el_pase_usa_alpha_blend_la_mezcla_es_parcial() -> None:
    """La composición es una mezcla, no un reemplazo: el resultado queda
    ENTRE la imagen original y la totalmente tintada."""
    luz = SunsetLight()
    original = (128, 128, 128)

    tintado_puro = ColorTools.apply_tint(_lienzo(original), luz.amber_for(1.0))
    tp = tintado_puro.get_at((10, 10))

    mezclado = _lienzo(original)
    luz.apply(mezclado, 1.0)
    mz = mezclado.get_at((10, 10))

    # el canal azul del resultado queda entre el tintado puro y el original
    assert tp.b < mz.b < original[2]


# ── Equivalencia entre la vía de referencia y la rápida ─────────────

@pytest.mark.parametrize("k", [0.15, 0.4, 0.65, 0.9, 1.0])
@pytest.mark.parametrize("color", [(128, 128, 128), (30, 200, 90), (240, 60, 15)])
def test_la_via_rapida_da_el_mismo_resultado_que_colortools(
    k: float, color: tuple[int, int, int],
) -> None:
    """apply() debe producir EXACTAMENTE lo mismo que la cadena de
    referencia con ColorTools, salvo redondeo.

    La identidad que lo permite:

        alpha_blend( apply_tint(F, A), F, α )
          = (F · A/255)·α + F·(1 − α)
          = F · ( α·A/255 + (1 − α) )
          = F · lerp(255, A, α) / 255
          = multiplicar F por el color  lerp(255, A, α)

    Es decir, la mezcla alfa de un tinte multiplicativo equivale a un
    ÚNICO tinte multiplicativo con el color interpolado hacia el blanco.
    """
    luz = SunsetLight()

    referencia = _lienzo(color)
    luz.apply_reference(referencia, k)

    rapida = _lienzo(color)
    luz.apply(rapida, k)

    r_ref, g_ref, b_ref, _ = referencia.get_at((10, 10))
    r_rap, g_rap, b_rap, _ = rapida.get_at((10, 10))

    assert abs(r_ref - r_rap) <= 2
    assert abs(g_ref - g_rap) <= 2
    assert abs(b_ref - b_rap) <= 2


def test_la_via_de_referencia_usa_colortools_de_verdad() -> None:
    """La cadena de referencia debe seguir existiendo y usando las dos
    operaciones de ColorTools, porque es la que documenta el README."""
    luz = SunsetLight()
    lienzo = _lienzo((128, 128, 128))
    r0, _g0, b0, _ = lienzo.get_at((10, 10))

    luz.apply_reference(lienzo, 1.0)
    r1, _g1, b1, _ = lienzo.get_at((10, 10))

    assert (r1 - b1) > (r0 - b0)
