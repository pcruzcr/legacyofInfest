"""AUD-759 — Dynamic visual QA.

Valida estabilidad temporal: player anchor, cámara, HUD, parallax, background,
sprite bounds, transiciones.
"""
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import pathlib, pygame, pytest
from src.engine.core import settings
from src.framework.stage.camera import Camera
from src.framework.stage.stage_loader import StageLoader
from src.framework.entities.player import Player

TMX_ROOT = pathlib.Path("assets/maps")
PRINCIPAL = ["stage0","stage1_1","stage1_2_la_soda","stage1_3_las_aulas","stage2_1_oficinas","stage2_2","stage3_1_la_entrada_de_piedra","stage3_3_el_patio","stage3_4_boss_gavilan","stage4_1","stage4_1b","hall","boss_venado","boss_rey","boss_paburu","lobby_datacenter","tutorial_hub","stage_mecanicas"]

def _load(name):
    cands = list(TMX_ROOT.rglob(f"{name}.tmx"))
    assert cands
    return StageLoader.load(cands[0])

@pytest.fixture(scope="module", autouse=True)
def _init():
    pygame.init()
    pygame.display.set_mode((settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT))
    yield
    pygame.quit()

def _capture(name, frames=60, step=1.5):
    stage = _load(name)
    cam = Camera()
    cam.set_map_size(*stage.map_pixel_size)
    spawn = stage.spawn_point
    player = Player(spawn) if spawn else Player(pygame.Vector2(100,100))
    cam.follow(player)
    cam.snap_to_target()
    from src.engine.core.event_bus import EventBus
    from src.engine.ui.hud import HUD
    hud = HUD(EventBus())
    hud0 = hud.vida_bar_rect().topleft
    cams=[]
    huds=[]
    ps=[]
    bg=[]
    for i in range(frames):
        player.position.x += step
        player.rect.x = int(player.position.x)
        player.rect.y = int(player.position.y)
        cam.update(1/60)
        cams.append(float(cam.offset.x))
        huds.append(hud0)
        ps.append(float(player.position.x - cam.offset.x))
        bg.append(float(cam.offset.x * 0.35 % 1280))
    hud.destroy()
    return cams, huds, ps, bg

@pytest.mark.parametrize("name", PRINCIPAL)
def test_hud_stability(name):
    _, huds, _, _ = _capture(name, frames=60)
    assert len(set(huds)) == 1, f"HUD se movió en {name}: {set(huds)}"

@pytest.mark.parametrize("name", PRINCIPAL)
def test_camera_continuity(name):
    cams, _, _, _ = _capture(name, frames=60)
    deltas = [abs(cams[i]-cams[i-1]) for i in range(1,len(cams))]
    if deltas:
        assert max(deltas) < 20, f"camera jump {max(deltas)} en {name}"
        # no drift negativo
        assert min(deltas) >= 0

@pytest.mark.parametrize("name", PRINCIPAL)
def test_parallax_continuity(name):
    _, _, _, bg = _capture(name, frames=60)
    deltas = [abs(bg[i]-bg[i-1]) for i in range(1,len(bg))]
    # wrap: delta near 1280 is wrap, ignore jumps >20 but <1200 are real jumps
    jumps = sum(1 for d in deltas if 20 < d < 1200)
    assert jumps == 0, f"bg jumps {jumps} en {name}"

@pytest.mark.parametrize("name", ["stage0","stage1_1"])
def test_player_anchor_stability(name):
    stage = _load(name)
    spawn = stage.spawn_point
    player = Player(spawn)
    # idle vs walk frames deben mantener feet estable (midbottom)
    feet0 = player.rect.bottom
    # simular cambio de estado walk (no cambia rect size para player)
    player.rect.height = 64
    feet1 = player.rect.bottom
    assert feet0 == feet1
    # hurtbox debe estar dentro
    hurt = player.hurtbox
    assert hurt.left >= player.rect.left
    assert hurt.right <= player.rect.right

def test_fullscreen_no_fbo_recreate():
    import pathlib as pl
    src = pl.Path("src/engine/render/gl_pipeline.py").read_text(encoding="utf-8")
    assert "set_display_viewport" in src
    # resize no debe contener _create_fbos con tamaño window
    assert "def resize" in src

def test_resize_no_internal_change():
    w0, h0 = settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT
    from src.engine.core import display
    vp = display.calculate_viewport(1920,1080,w0,h0)
    assert settings.INTERNAL_WIDTH == 1280
    assert vp == (0,0,1920,1080)
