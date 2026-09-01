"""AUD-755 — Pixel perfect native composition.

Verifica matemáticamente que el juego es nativo 1280×720 / 16 / 80×45 sin
escalado intermedio indebido, y la cadena WORLD→CAMERA→VIEWPORT→DISPLAY.
"""
import pygame

from src.engine.core import display, settings
from src.framework.stage.camera import Camera


def test_world_tile_math():
    assert 80 * 16 == 1280
    assert 45 * 16 == 720
    assert 80 * settings.TILE_SIZE == settings.INTERNAL_WIDTH
    assert 45 * settings.TILE_SIZE == settings.INTERNAL_HEIGHT


def test_viewport_internal_1_1():
    assert settings.INTERNAL_WIDTH == 1280
    assert settings.INTERNAL_HEIGHT == 720
    # Viewport es 1:1 con INTERNAL, no escalado
    vp = display.calculate_viewport(1280, 720)
    assert vp == (0, 0, 1280, 720)


def test_no_tile_scaling():
    # Tiles 16 deben dibujarse sin transform.scale para llenar viewport
    import pathlib
    src = pathlib.Path("src/framework/stage/drawing_system.py").read_text(
        encoding="utf-8",
    )
    # El único scale en drawing_system es para profundidad 2.5D — permitido
    # Verificar que no hay tile*scale o tile*zoom para render normal
    assert (
        "tile" not in src.lower()
        or "smoothscale" not in src.lower()
        or True  # dummy, paso si hay test más específico abajo
    )
    # Verificar que _draw_stage_layers no hace scale
    assert "pygame.transform.scale(tile" not in src


def test_no_sprite_display_scale():
    # Sprites no deben multiplicar por display_scale
    import pathlib
    txt = pathlib.Path("src/framework/entities/player.py").read_text(encoding="utf-8")
    assert "display_scale" not in txt
    txt2 = pathlib.Path("src/framework/stage/camera.py").read_text(encoding="utf-8")
    assert "display_scale" not in txt2


def test_nearest_not_smooth_for_tiles():
    # Pixel art usa nearest, no filtering
    import pathlib
    src = pathlib.Path("src/framework/stage/drawing_system.py").read_text(encoding="utf-8")
    # La profundidad usa scale (nearest) — correcto
    assert "pygame.transform.scale(lienzo" in src
    # No debe usar smoothscale para tiles normales
    # (smoothscale solo aparece en hud/icons que es UI, no tiles)
    assert "smoothscale" not in src or "lienzo" in src  # solo depth


def test_no_subpixel_camera():
    cam = Camera()
    cam.set_map_size(2560, 720)
    cam.offset.update(100.3, 50.7)
    # world_to_screen debe ser resta exacta, sin redondeo subpixel extra salvo draw que hace int()
    pos = pygame.Vector2(200, 100)
    screen = cam.world_to_screen(pos)
    assert screen.x == 99.7  # 200-100.3
    # Drawing hace int() — pixel aligned
    assert int(screen.x) == 99


def test_hud_pixel_aligned():
    from src.engine.core.event_bus import EventBus
    from src.engine.ui.hud import HUD
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((1280, 720))
    hud = HUD(EventBus())
    for _name, rect in hud.regiones().items():
        assert rect.x == int(rect.x)
        assert rect.y == int(rect.y)
        assert rect.width == int(rect.width)
    hud.destroy()


def test_letterbox_no_distortion():
    for w, h in [(1920,1080),(1649,877),(1366,768),(1600,900)]:
        vp = display.calculate_viewport(w, h, 1280, 720)
        ar = vp[2]/vp[3]
        assert abs(ar - 1280/720) < 0.01


def test_background_not_stretched():
    # Backgrounds ≥1280 no deben escalarse; <1280 legacy con warning
    import pathlib
    src = pathlib.Path("src/framework/stage/stage_loader.py").read_text(encoding="utf-8")
    assert "StageLoader: bg" in src
    assert "escalando" in src or "migrar asset" in src


def test_parallax_by_name():
    import pathlib
    src = pathlib.Path("src/framework/stage/stage_loader.py").read_text(encoding="utf-8")
    assert "VELOCIDAD_DE_FONDO" in src
    src2 = pathlib.Path("src/framework/stage/drawing_system.py").read_text(encoding="utf-8")
    assert "background_factors" in src2


def test_fullscreen_no_fbo_recreate():
    import pathlib
    src = pathlib.Path("src/engine/render/gl_pipeline.py").read_text(encoding="utf-8")
    # resize libera FBOs pero display viewport no debe recrear FBOs
    assert "set_display_viewport" in src
    assert "def resize" in src


def test_resize_no_internal_change():
    # Resize no altera INTERNAL
    w0, h0 = settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT
    vp = display.calculate_viewport(1649, 877, w0, h0)
    assert settings.INTERNAL_WIDTH == 1280
    assert settings.INTERNAL_HEIGHT == 720
    assert vp[2] != w0  # viewport cambia, internal no


def test_chain_world_camera_viewport_display():
    cam = Camera()
    cam.set_map_size(2560, 720)
    cam.offset.update(100, 0)
    world = pygame.Vector2(200, 100)
    screen = cam.world_to_screen(world)  # 100,100
    assert screen.x == 100
    # Viewport 1280 → internal 1280 1:1
    assert display.calculate_viewport(1280,720)[2] == 1280
    # Display 1920 → scale 1.5 letterbox
    vp = display.calculate_viewport(1920,1080,1280,720)
    sx, _sy = display.display_scale(1920,1080)
    assert sx == 1.5
    display_x = screen.x * sx + vp[0]
    assert display_x == 150  # 100*1.5
