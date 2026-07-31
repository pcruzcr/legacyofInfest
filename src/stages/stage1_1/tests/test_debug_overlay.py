"""
Module: test_debug_overlay
System: stage (student assignment) — stage1_1 «La Entrada»
Academic Unit: II (Vectores), III (Curvas) — visualizacion
Description: Overlay de depuracion: curvas, puntos de control y radios.

Ejecutar toda la suite con:
   python -m pytest src/stages/stage1_1/tests/ -v
"""
from __future__ import annotations

import pygame

from src.stages.stage1_1.entities.canopy_bird import CanopyBird
from src.stages.stage1_1.entities.jungle_frog import JungleFrog
from src.stages.stage1_1.overlays.debug_overlay import DebugOverlay

CTRL = [(100.0, 80.0), (140.0, 40.0), (180.0, 120.0), (220.0, 60.0)]


def _ave(**kw) -> CanopyBird:
    kw.setdefault("waypoints", list(CTRL))
    return CanopyBird(pygame.Vector2(CTRL[0]), **kw)


def _lienzo(color=(128, 128, 128), tam=(64, 48)) -> pygame.Surface:
    s = pygame.Surface(tam)
    s.fill(color)
    return s

# ════════════════════════════════════════════════════════════════════
# DebugOverlay — evidencia visual para el README (tecla F1)
# ════════════════════════════════════════════════════════════════════

def test_el_overlay_arranca_apagado() -> None:
    assert DebugOverlay().enabled is False


def test_el_overlay_se_enciende_y_se_apaga() -> None:
    ov = DebugOverlay()
    ov.toggle(True)
    assert ov.enabled is True
    ov.toggle(False)
    assert ov.enabled is False


def test_la_conversion_a_pantalla_resta_el_offset_de_camara() -> None:
    """pantalla = mundo − offset_camara. Es la transformación que aplica
    todo el motor (camera.world_to_screen)."""
    puntos = [(100.0, 200.0), (150.5, 260.9)]
    off = pygame.Vector2(40.0, 60.0)

    assert DebugOverlay.to_screen(puntos, off) == [(60, 140), (110, 200)]


def test_la_conversion_a_pantalla_devuelve_enteros() -> None:
    salida = DebugOverlay.to_screen([(1.7, 2.9)], pygame.Vector2(0.0, 0.0))
    assert all(isinstance(c, int) for c in salida[0])


def test_apagado_no_dibuja_nada() -> None:
    ov = DebugOverlay()
    ave = _ave()
    lienzo = _lienzo((0, 0, 0), (320, 224))
    antes = pygame.image.tobytes(lienzo, "RGB")

    ov.draw(lienzo, pygame.Vector2(0, 0), [ave], [])

    assert pygame.image.tobytes(lienzo, "RGB") == antes


def test_encendido_dibuja_la_curva_del_ave() -> None:
    ov = DebugOverlay()
    ov.toggle(True)
    ave = _ave()
    lienzo = _lienzo((0, 0, 0), (320, 224))
    antes = pygame.image.tobytes(lienzo, "RGB")

    ov.draw(lienzo, pygame.Vector2(0, 0), [ave], [])

    assert pygame.image.tobytes(lienzo, "RGB") != antes


def test_encendido_dibuja_el_radio_de_la_rana() -> None:
    ov = DebugOverlay()
    ov.toggle(True)
    rana = JungleFrog(pygame.Vector2(120.0, 100.0), detection_range_x=48.0)
    lienzo = _lienzo((0, 0, 0), (320, 224))
    antes = pygame.image.tobytes(lienzo, "RGB")

    ov.draw(lienzo, pygame.Vector2(0, 0), [], [rana])

    assert pygame.image.tobytes(lienzo, "RGB") != antes


def test_dibujar_sin_entidades_no_revienta() -> None:
    ov = DebugOverlay()
    ov.toggle(True)
    ov.draw(_lienzo(tam=(320, 224)), pygame.Vector2(0, 0), [], [])
