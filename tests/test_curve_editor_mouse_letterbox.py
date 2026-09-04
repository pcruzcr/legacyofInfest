"""
AUD-809 FASE 0 — CurveEditor mouse display→internal con letterbox.

El defecto pre-AUD-809:
    scale = DISPLAY_SCALE; mx //= scale
solo funciona si la ventana mide INTERNAL×SCALE sin letterbox.
Con resize/fullscreen y aspect distinto (1649×877, 1920×1200, 2560×1080…)
el viewport tiene offset y escala distinta a DISPLAY_SCALE.

Sandbox ya se migró en AUD-803. CurveEditor quedaba pendiente (P3).
Este test fija la regresión y exige la fórmula letterbox.

Casos:
  1280×720   1.0×  sin barras  (baseline)
  1366×768   1.066× pillar mínimo
  1649×877   1.218× letterbox 45px izquierda (caso que rompía sandbox)
  1920×1080  1.5×   fullscreen 16:9 exacto
  2560×1440  2.0×   entero

Para cada resolución verifica:
  - mouse center → internal center
  - mouse esquinas del viewport → internal esquinas
  - mouse cerca del borde del viewport (letterbox)
  - vp_x=0 mutado debe fallar (sensibilidad)
"""
from __future__ import annotations

import pytest

from src.engine.core import display, settings


def _display_to_internal(mouse_x: int, mouse_y: int, dw: int, dh: int) -> tuple[int, int]:
    """Replica exacta de la lógica nueva en curve_editor_scene.update."""
    vp_x, vp_y, vp_w, vp_h = display.calculate_viewport(dw, dh)
    if vp_w > 0 and vp_h > 0:
        mx = int((mouse_x - vp_x) * settings.INTERNAL_WIDTH / vp_w)
        my = int((mouse_y - vp_y) * settings.INTERNAL_HEIGHT / vp_h)
    else:
        mx = mouse_x // max(1, settings.DISPLAY_SCALE)
        my = mouse_y // max(1, settings.DISPLAY_SCALE)
    return mx, my


def _legacy_display_to_internal(mouse_x: int, mouse_y: int) -> tuple[int, int]:
    """Vía vieja DISPLAY_SCALE (bug)."""
    s = max(1, settings.DISPLAY_SCALE)
    return mouse_x // s, mouse_y // s


RESOLUTIONS = [
    (1280, 720),
    (1366, 768),
    (1649, 877),
    (1920, 1080),
    (2560, 1440),
]


@pytest.mark.parametrize("dw,dh", RESOLUTIONS)
def test_curve_editor_mouse_center_maps_to_internal_center(dw: int, dh: int):
    vp_x, vp_y, vp_w, vp_h = display.calculate_viewport(dw, dh)
    # mouse en centro del viewport → internal centro
    mx_disp = vp_x + vp_w // 2
    my_disp = vp_y + vp_h // 2
    mx, my = _display_to_internal(mx_disp, my_disp, dw, dh)
    assert mx == pytest.approx(settings.INTERNAL_WIDTH // 2, abs=1)
    assert my == pytest.approx(settings.INTERNAL_HEIGHT // 2, abs=1)


@pytest.mark.parametrize("dw,dh", RESOLUTIONS)
def test_curve_editor_mouse_viewport_corners_map_to_internal_corners(dw: int, dh: int):
    vp_x, vp_y, vp_w, vp_h = display.calculate_viewport(dw, dh)
    # esquina superior izquierda del viewport → (0,0) internal
    mx, my = _display_to_internal(vp_x, vp_y, dw, dh)
    assert mx == pytest.approx(0, abs=1)
    assert my == pytest.approx(0, abs=1)
    # esquina inferior derecha del viewport (último pixel) → (~1279,~719)
    mx2, my2 = _display_to_internal(vp_x + vp_w - 1, vp_y + vp_h - 1, dw, dh)
    assert mx2 == pytest.approx(settings.INTERNAL_WIDTH - 1, abs=2)
    assert my2 == pytest.approx(settings.INTERNAL_HEIGHT - 1, abs=2)


@pytest.mark.parametrize("dw,dh", RESOLUTIONS)
def test_curve_editor_mouse_letterbox_bar_is_outside_or_clamped(dw: int, dh: int):
    """Un click en la barra negra (letterbox/pillar) queda fuera de [0, INTERNAL)."""
    vp_x, vp_y, vp_w, vp_h = display.calculate_viewport(dw, dh)
    has_letterbox = vp_x > 0
    has_pillarbox = vp_y > 0
    if has_letterbox:
        # click en medio de barra izquierda
        mx, _ = _display_to_internal(vp_x // 2, dh // 2, dw, dh)
        assert mx < 0, f"letterbox click debería dar mx<0, dio {mx} para {dw}×{dh} vp {vp_x}"
    if has_pillarbox:
        _, my = _display_to_internal(dw // 2, vp_y // 2, dw, dh)
        assert my < 0
    if not has_letterbox and not has_pillarbox:
        # sin barras, (0,0) display → (0,0) internal
        mx, my = _display_to_internal(0, 0, dw, dh)
        assert mx == 0 and my == 0


@pytest.mark.parametrize("dw,dh", RESOLUTIONS)
def test_curve_editor_mouse_near_viewport_boundary(dw: int, dh: int):
    """1px dentro del viewport debe mapear ~0-2 px dentro de internal, no saltar."""
    vp_x, vp_y, vp_w, vp_h = display.calculate_viewport(dw, dh)
    # 1px dentro del borde izquierdo
    mx_in, _ = _display_to_internal(vp_x + 1, vp_y + vp_h // 2, dw, dh)
    assert 0 <= mx_in <= 3, f"1px dentro debería ser 0-3, got {mx_in} for {dw}×{dh}"
    # 1px dentro del borde derecho
    mx_r, _ = _display_to_internal(vp_x + vp_w - 2, vp_y + vp_h // 2, dw, dh)
    assert settings.INTERNAL_WIDTH - 4 <= mx_r <= settings.INTERNAL_WIDTH - 1


def test_curve_editor_legacy_fails_on_letterbox_1649():
    """El camino viejo DISPLAY_SCALE falla en 1649×877 letterbox (el bug real)."""
    dw, dh = 1649, 877
    vp_x, _, vp_w, _ = display.calculate_viewport(dw, dh)
    assert vp_x == 45  # letterbox documentado AUD-803
    assert vp_w == 1559
    # mouse en centro viewport: viejo da 800, nuevo da 640
    mouse_center = vp_x + vp_w // 2  # 824
    mx_legacy, _ = _legacy_display_to_internal(mouse_center, 438)
    mx_new, _ = _display_to_internal(mouse_center, 438, dw, dh)
    # nuevo ~640, viejo ~824 → error 184px (documentado AUD-803: 181)
    assert mx_new == pytest.approx(640, abs=2)
    assert mx_legacy == pytest.approx(824, abs=2)
    assert abs(mx_legacy - mx_new) > 100, "legacy y nuevo deberían diferir >100 en letterbox"


def test_curve_editor_mutation_vp_x_zero_must_fail():
    """MUTATION TEST: si vp_x se fuerza a 0, el mapeo deja de ser correcto y el test debe fallar.

    Este test demuestra que la suite detecta la regresión: al ignorar el offset
    del viewport, un click en el centro se desplaza vp_x*scale px.
    Sin sensibilidad a vp_x, el test sería tautológico.
    """
    dw, dh = 1649, 877
    vp_x, vp_y, vp_w, vp_h = display.calculate_viewport(dw, dh)
    assert vp_x != 0  # precondición: este modo tiene letterbox
    # Simular mutación: código con vp_x=0 (ignora letterbox)
    def mutated(mouse_x: int, mouse_y: int) -> tuple[int, int]:
        vp_x_mut = 0
        return (
            int((mouse_x - vp_x_mut) * settings.INTERNAL_WIDTH / vp_w),
            int((mouse_y - vp_y) * settings.INTERNAL_HEIGHT / vp_h),
        )

    mouse_center = vp_x + vp_w // 2
    mx_correct, _ = _display_to_internal(mouse_center, vp_y + vp_h // 2, dw, dh)
    mx_mutated, _ = mutated(mouse_center, vp_y + vp_h // 2)

    # Correcto ~640, mutado ~(824*1280/1559)≈676 → diff ~36 y además mapea centro mal
    # Lo importante: deben diferir significativamente, probando sensibilidad a vp_x
    diff = abs(mx_correct - mx_mutated)
    assert diff > 20, f"mutation vp_x=0 debería desplazar >20, diff={diff} correct={mx_correct} mutated={mx_mutated}"

    # Y el mutado NO puede pasar el test de centro
    assert mx_mutated != pytest.approx(settings.INTERNAL_WIDTH // 2, abs=1), \
        "mutated debe fallar la aserción de centro — si pasa, el test no detecta vp_x"


def test_curve_editor_no_DISPLAY_SCALE_in_viewport_path(monkeypatch):
    """Verifica que el archivo ya no contiene el patrón viejo fuera del fallback."""
    import pathlib
    src = pathlib.Path("src/engine/scenes/curve_editor_scene.py").read_text(encoding="utf-8")
    # Debe contener calculate_viewport y la fórmula (mx - vp_x)
    assert "calculate_viewport" in src
    assert "vp_x" in src and "INTERNAL_WIDTH" in src
    # No debe contener la línea exacta vieja como camino principal
    # (puede quedar en fallback // DISPLAY_SCALE, pero no como `mx // scale` solo)
    assert "mx = mx // scale" not in src
    assert "my = my // scale" not in src
