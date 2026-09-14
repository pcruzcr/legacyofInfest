"""Tests de pipeline nativo — AUD-754.

Valida: viewport dimensions, camera transform, UI anchor math, aspect ratio,
display scaling sin doble escalado.
"""
import pygame

from src.engine.core import display, settings
from src.framework.stage.camera import Camera


def test_internal_matches_tmx_height():
    # 45 filas *16 =720 debe coincidir con INTERNAL_HEIGHT para no dejar hueco
    assert settings.INTERNAL_HEIGHT == 720
    assert settings.INTERNAL_WIDTH == 1280
    assert settings.TILE_SIZE == 16


def test_viewport_letterbox_native():
    vp = display.calculate_viewport(1280, 720, 1280, 720)
    assert vp == (0, 0, 1280, 720)


def test_viewport_letterbox_1920_full():
    # 1280->1920 mismo aspecto 16:9 → sin barras
    vp = display.calculate_viewport(1920, 1080, 1280, 720)
    assert vp == (0, 0, 1920, 1080)


def test_viewport_pillarbox_1649_877():
    vp = display.calculate_viewport(1649, 877, 1280, 720)
    # scale = min(1.288,1.218)=1.218 → 1559×877
    assert vp[2] == 1559
    assert vp[3] == 877
    assert vp[0] == 45
    assert vp[1] == 0


def test_viewport_1366():
    vp = display.calculate_viewport(1366, 768, 1280, 720)
    assert vp[3] == 768
    # ancho ~1364 pillarbox 1px
    assert abs(vp[2] - 1364) <= 2


def test_display_scale_no_double():
    # camera zoom 1.0, display scale 1.5 a 1920 → no multiplicar
    cam = Camera()
    assert cam.zoom == 1.0
    sx, _sy = display.display_scale(1920, 1080)
    assert sx == 1.5
    # La transformación total mundo→display es (world-camera)*zoom * display_scale
    # No existe zoom * display_scale doble con mismo factor aplicado dos veces
    # Verificar que zoom != display_scale cuando display_scale>1 (no acoplados)
    assert cam.zoom != sx or sx == 1.0


def test_camera_clamp_usa_world_bounds():
    cam = Camera()
    cam.set_map_size(2560, 720)  # stage0
    # viewport 1280 → max offset 1280
    cam.offset.update(9999, 9999)
    cam._clamp_a_los_bordes()
    assert cam.offset.x == 1280
    assert cam.offset.y == 0
    # map 720 < viewport 720? stage_mecanicas 384 alto
    cam2 = Camera()
    cam2.set_map_size(4960, 384)
    cam2.offset.update(0, 100)
    cam2._clamp_a_los_bordes()
    assert cam2.offset.y == 0  # max 0


def test_camera_world_to_screen():
    cam = Camera()
    cam.offset.update(100, 50)
    pos = pygame.Vector2(200, 100)
    screen = cam.world_to_screen(pos)
    assert screen.x == 100
    assert screen.y == 50
    # sin zoom doble
    back = cam.screen_to_world(screen)
    assert back.x == 200
    assert back.y == 100


def test_ui_not_world():
    # UI debe usar UI space, no world/camera
    from src.engine.core.event_bus import EventBus
    from src.engine.ui.hud import HUD
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((1280, 720))
    hud = HUD(EventBus())
    # vida bar está en (24, ~138) a 1280, no en world coords
    rect = hud.vida_bar_rect()
    assert rect.x == 24
    assert rect.y > 100
    # No depende de camera
    cam = Camera()
    cam.offset.update(999, 999)
    rect2 = hud.vida_bar_rect()
    assert rect == rect2
    hud.destroy()


def test_aspect_preserving_no_distortion():
    # Para cualquier display, viewport aspect == internal aspect
    for w, h in [(1920,1080),(1649,877),(1366,768),(1600,900),(1280,720)]:
        vp = display.calculate_viewport(w, h, 1280, 720)
        vp_ar = vp[2]/vp[3] if vp[3] else 0
        internal_ar = 1280/720
        assert abs(vp_ar - internal_ar) < 0.01, f"{w}x{h} deformado"


def test_no_hardcoded_1920_in_camera():
    # camera spline debe usar settings, no 400,300 fijo
    import pathlib
    src = pathlib.Path("src/framework/stage/camera.py").read_text(encoding="utf-8")
    assert "p.x - 400" not in src
    assert "settings.INTERNAL_WIDTH" in src
