"""Módulo: test_tramos_venado
Sistema: tests
Descripción: tabla de actos narrativos del corredor pre-jefe (puro, sin pygame)."""
from __future__ import annotations

import pytest

from src.stages.boss_venado.tramos_venado import (
    TABLA,
    Tramo,
    avance_en_tramo,
    interpolar_grading,
    tramo_en,
)


def test_tabla_tiene_cuatro_actos_en_orden_creciente_de_x():
    assert len(TABLA) == 4
    xs = [t.x_inicio for t in TABLA]
    assert xs == sorted(xs)
    assert xs == [0.0, 1040.0, 1520.0, 2480.0]


def test_tramo_en_selecciona_por_x():
    assert tramo_en(0.0).nombre == "El hogar"
    assert tramo_en(500.0).nombre == "El hogar"
    assert tramo_en(1039.9).nombre == "El hogar"
    assert tramo_en(1040.0).nombre == "El abandono"
    assert tramo_en(1519.9).nombre == "El abandono"
    assert tramo_en(1520.0).nombre == "El umbral"
    assert tramo_en(2479.9).nombre == "El umbral"
    assert tramo_en(2480.0).nombre == "Lo sagrado"
    assert tramo_en(3280.0).nombre == "Lo sagrado"   # más allá del último tramo: se queda en el último


def test_tramo_en_antes_del_mapa_devuelve_el_primer_tramo():
    assert tramo_en(-50.0) is TABLA[0]


def test_avance_en_tramo_crece_de_0_a_1_dentro_del_tramo():
    assert avance_en_tramo(0.0) == pytest.approx(0.0)
    assert avance_en_tramo(1039.9) == pytest.approx(1.0, abs=1e-2)
    assert avance_en_tramo(1040.0) == pytest.approx(0.0)   # tramo nuevo: reinicia
    assert avance_en_tramo(3280.0) == 1.0   # último tramo: se satura en 1.0 (fin = x_inicio+1)


def test_interpolar_grading_extremos_son_identidad_y_destino():
    from src.stages.boss_venado.tramos_venado import IDENTIDAD, AMBAR
    assert interpolar_grading(None, AMBAR, 0.0) == IDENTIDAD
    assert interpolar_grading(None, AMBAR, 1.0) == AMBAR


def test_interpolar_grading_clampea_t_fuera_de_rango():
    # protege el clamp de la línea 107 de tramos_venado.py (max(0.0,
    # min(1.0, t))) contra refactors: t fuera de [0, 1] no debe extrapolar,
    # se satura en los extremos IDENTIDAD/AMBAR igual que en t=0.0/t=1.0.
    from src.stages.boss_venado.tramos_venado import IDENTIDAD, AMBAR
    assert interpolar_grading(None, AMBAR, -0.5) == IDENTIDAD
    assert interpolar_grading(None, AMBAR, 1.5) == AMBAR


def test_interpolar_grading_con_ease_no_es_lineal_a_medio_camino():
    from src.stages.boss_venado.tramos_venado import AMBAR, IDENTIDAD
    # CORRECCIÓN respecto al texto original del plan: la interpolación real
    # parte de IDENTIDAD (255,0,0,0,255,0,0,0,255), no de una base de ceros
    # -- eso ya lo exige test_interpolar_grading_extremos_son_identidad_y_destino
    # (interpolar_grading(None, AMBAR, 0.0) == IDENTIDAD, con 255 en la
    # diagonal). El "lineal" de referencia debe partir de esa misma base.
    lineal = tuple(round(IDENTIDAD[i] + (AMBAR[i] - IDENTIDAD[i]) * 0.5) for i in range(9))
    con_ease = interpolar_grading(None, AMBAR, 0.5)
    # ease_in_out_quad(0.5) == 0.5 exactamente (simétrico en el punto medio),
    # así que a t=0.5 SÍ coincide con lineal -- la prueba real de que hay
    # ease va en los extremos del tramo, no en el centro.
    assert con_ease == lineal


def test_interpolar_grading_ease_suaviza_cerca_de_los_bordes():
    from src.stages.boss_venado.tramos_venado import AMBAR, IDENTIDAD
    # CORRECCIÓN respecto al texto original del plan: el canal r (índice 0)
    # va de IDENTIDAD[0]=255 a AMBAR[0]=215 -- es una REDUCCIÓN, no un
    # ascenso desde 0. "Ease arranca lento" entonces significa quedarse MÁS
    # CERCA del punto de partida (255) que la interpolación lineal, es decir
    # un valor MAYOR (no menor) que el lineal a t=0.1.
    lineal_r = round(IDENTIDAD[0] + (AMBAR[0] - IDENTIDAD[0]) * 0.1)
    con_ease_r = interpolar_grading(None, AMBAR, 0.1)[0]
    assert con_ease_r > lineal_r
