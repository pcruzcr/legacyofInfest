"""
Module: test_canopy_bird
System: stage (student assignment) — stage1_1 «La Entrada»
Academic Unit: III (Curvas)
Description: Bezier cubica, muestreo, easing y recorrido en ping-pong.

Ejecutar toda la suite con:
   python -m pytest src/stages/stage1_1/tests/ -v
"""
from __future__ import annotations

import pygame
import pytest

from src.framework.processing.curve_tools import CurveTools
from src.stages.stage1_1.entities.canopy_bird import CanopyBird

# ════════════════════════════════════════════════════════════════════
# CanopyBird — Unidad III: curva de Bézier cúbica
# ════════════════════════════════════════════════════════════════════

CTRL = [(100.0, 80.0), (140.0, 40.0), (180.0, 120.0), (220.0, 60.0)]


def _ave(**kw) -> CanopyBird:
    kw.setdefault("waypoints", list(CTRL))
    return CanopyBird(pygame.Vector2(CTRL[0]), **kw)


def test_la_ruta_tiene_el_numero_de_muestras_pedido() -> None:
    ave = _ave(n_samples=64)
    assert len(ave.path) == 64


def test_la_ruta_es_exactamente_la_de_curvetools() -> None:
    """La rúbrica exige que la trayectoria salga de CurveTools, no de una
    implementación propia. Se compara punto a punto."""
    ave = _ave(n_samples=32)
    esperado = CurveTools.bezier(CTRL, 32)

    assert len(ave.path) == len(esperado)
    for (ax, ay), (ex, ey) in zip(ave.path, esperado, strict=False):
        assert ax == pytest.approx(ex, abs=1e-9)
        assert ay == pytest.approx(ey, abs=1e-9)


def test_la_bezier_interpola_los_extremos() -> None:
    """B(0) = P₀ y B(1) = P₃. Los puntos intermedios NO se tocan."""
    ave = _ave(n_samples=64)

    assert ave.path[0][0] == pytest.approx(CTRL[0][0], abs=1e-6)
    assert ave.path[0][1] == pytest.approx(CTRL[0][1], abs=1e-6)
    assert ave.path[-1][0] == pytest.approx(CTRL[3][0], abs=1e-6)
    assert ave.path[-1][1] == pytest.approx(CTRL[3][1], abs=1e-6)


def test_la_curva_no_sale_de_la_envolvente_de_los_puntos_de_control() -> None:
    """Propiedad de la envolvente convexa: toda la curva vive dentro del
    casco convexo de sus puntos de control. Se comprueba con la caja
    contenedora, que es una condición necesaria."""
    ave = _ave(n_samples=64)
    xs = [p[0] for p in CTRL]
    ys = [p[1] for p in CTRL]

    for x, y in ave.path:
        assert min(xs) - 1e-6 <= x <= max(xs) + 1e-6
        assert min(ys) - 1e-6 <= y <= max(ys) + 1e-6


def test_sin_waypoints_genera_puntos_de_control_por_defecto() -> None:
    """Si el TMX no trae Waypoint, la entidad NO debe quedar inerte."""
    ave = CanopyBird(pygame.Vector2(300.0, 90.0), waypoints=None)

    assert len(ave.control_points) >= 2
    assert len(ave.path) > 1


def test_un_solo_waypoint_tampoco_revienta() -> None:
    ave = CanopyBird(pygame.Vector2(300.0, 90.0), waypoints=[(300.0, 90.0)])
    assert len(ave.path) > 1


# ── Recorrido: el parámetro t ───────────────────────────────────────

def test_el_ave_se_mueve_a_lo_largo_de_la_curva() -> None:
    ave = _ave(flight_speed=0.5)
    inicio = pygame.Vector2(ave.position)

    ave.advance_along_path(0.5)

    assert (pygame.Vector2(ave.position) - inicio).length() > 1.0


def test_t_nunca_sale_del_intervalo_unitario() -> None:
    """t ∈ [0,1] es progreso normalizado del recorrido, no tiempo."""
    ave = _ave(flight_speed=0.9)
    for _ in range(200):
        ave.advance_along_path(0.1)
        assert 0.0 <= ave.t <= 1.0


def test_el_recorrido_hace_ping_pong() -> None:
    """Al llegar a t=1 el ave invierte el sentido en vez de teletransportarse."""
    ave = _ave(flight_speed=0.5)

    while ave.direction > 0:
        ave.advance_along_path(0.1)

    assert ave.direction == -1
    assert ave.t == pytest.approx(1.0, abs=1e-6)

    ave.advance_along_path(0.1)
    assert ave.t < 1.0


def test_el_easing_deforma_el_recorrido_pero_respeta_los_extremos() -> None:
    """u = ease_in_out_quad(t) acentúa el planeo: lento arriba, rápido al
    caer. En los extremos debe coincidir con t."""
    ave = _ave()

    ave.t = 0.0
    assert ave.eased_t() == pytest.approx(0.0, abs=1e-9)

    ave.t = 1.0
    assert ave.eased_t() == pytest.approx(1.0, abs=1e-9)

    ave.t = 0.25
    assert ave.eased_t() != pytest.approx(0.25, abs=1e-3)
