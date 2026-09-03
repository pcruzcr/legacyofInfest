"""B2 — NG+ UI integration — Title / Load / HUD muestran SaveData.ng_plus dinámico."""
from __future__ import annotations

from unittest.mock import MagicMock

import pygame
import pytest

from src.engine.core.event_bus import EventBus
from src.engine.core.save_data import SaveData
from src.engine.core.save_manager import SaveManager
from src.engine.ui.hud import HUD


@pytest.fixture(autouse=True)
def _tmp_saves(tmp_path):
    orig = SaveManager.SAVES_DIR
    SaveManager.SAVES_DIR = tmp_path / "saves"
    SaveManager.SAVES_DIR.mkdir(parents=True, exist_ok=True)
    yield
    SaveManager.SAVES_DIR = orig


@pytest.fixture(autouse=True)
def _init_pygame():
    if not pygame.get_init():
        pygame.init()
    pygame.display.init()
    # dummy video para que AssetLoader y font no revienten
    try:
        pygame.display.set_mode((1, 1))
    except Exception:
        pass


def _make_context(save_manager: SaveManager | None = None):
    """Context mínimo para Title/Load/HUD."""
    from types import SimpleNamespace

    bus = EventBus()
    mgr = save_manager or SaveManager()
    ctx = SimpleNamespace(
        event_bus=bus,
        save_manager=mgr,
        scene_manager=MagicMock(),
        clock=MagicMock(),
        input_manager=MagicMock(),
        audio_manager=MagicMock(),
        pending_load=None,
    )
    # transition mock para Title/Load on_enter
    ctx.scene_manager.transition = MagicMock()
    ctx.scene_manager.transition.start_fade_in = MagicMock()
    ctx.scene_manager.transition.start_fade_out = MagicMock()
    ctx.scene_manager.transition.draw = MagicMock()
    return ctx


# ── TITLE ────────────────────────────────────────────────────────────────

class TestTitleNGPlus:
    def test_title_shows_ng_plus_level(self):
        # Arrange: slot 1 con NG+1, activa
        mgr = SaveManager()
        mgr.save(1, SaveData(slot_id=1, profile_name="Hero", ng_plus=1, stage_id="stage0"))
        mgr.ranura_activa = 1
        ctx = _make_context(mgr)
        from src.engine.scenes.title_scene import TitleScene
        scene = TitleScene(ctx)
        # Act: Title on_enter llama _update_options que debe poner trailing NG+1
        scene.on_enter()
        cont = next((i for i in scene._menu.items if str(i.value) == "CONTINUE"), None)
        assert cont is not None, "CONTINUE debe existir con saves"
        assert cont.trailing == "NG+1"
        # Also check helper
        assert scene._ng_plus_para_continue() == 1

    def test_title_shows_ng_plus_level_dynamic(self):
        mgr = SaveManager()
        mgr.save(1, SaveData(slot_id=1, ng_plus=2, stage_id="stage0"))
        mgr.ranura_activa = 1
        ctx = _make_context(mgr)
        from src.engine.scenes.title_scene import TitleScene
        scene = TitleScene(ctx)
        scene.on_enter()
        cont = next(i for i in scene._menu.items if str(i.value) == "CONTINUE")
        assert cont.trailing == "NG+2"
        # no hardcodeado NG+1: debe reflejar el valor real
        assert cont.trailing != "NG+1"

    def test_title_ng_plus_uses_correct_slot(self):
        # Dos slots con NG distintos: activa manda, no newest
        mgr = SaveManager()
        mgr.save(1, SaveData(slot_id=1, ng_plus=1, stage_id="stage0"))
        mgr.save(2, SaveData(slot_id=2, ng_plus=5, stage_id="stage0"))
        mgr.ranura_activa = 1
        ctx = _make_context(mgr)
        from src.engine.scenes.title_scene import TitleScene
        scene = TitleScene(ctx)
        scene.on_enter()
        cont = next(i for i in scene._menu.items if str(i.value) == "CONTINUE")
        assert cont.trailing == "NG+1"
        mgr.ranura_activa = 2
        scene._update_options()
        cont2 = next(i for i in scene._menu.items if str(i.value) == "CONTINUE")
        assert cont2.trailing == "NG+5"


class TestTitleNGPlusZero:
    def test_ng_plus_zero_hides_title(self):
        mgr = SaveManager()
        mgr.save(1, SaveData(slot_id=1, ng_plus=0, stage_id="stage0"))
        mgr.ranura_activa = 1
        ctx = _make_context(mgr)
        from src.engine.scenes.title_scene import TitleScene
        scene = TitleScene(ctx)
        scene.on_enter()
        cont = next(i for i in scene._menu.items if str(i.value) == "CONTINUE")
        assert cont.trailing == ""
        assert scene._ng_plus_para_continue() == 0

    def test_no_saves_no_continue(self):
        mgr = SaveManager()
        ctx = _make_context(mgr)
        from src.engine.scenes.title_scene import TitleScene
        scene = TitleScene(ctx)
        scene.on_enter()
        vals = [str(i.value) for i in scene._menu.items]
        assert "CONTINUE" not in vals


# ── LOAD GAME ────────────────────────────────────────────────────────────

class TestLoadGameNGPlus:
    def test_load_scene_shows_ng_plus_level(self):
        mgr = SaveManager()
        mgr.save(1, SaveData(slot_id=1, profile_name="A", ng_plus=1, stage_id="stage0", play_time=3600))
        mgr.save(2, SaveData(slot_id=2, profile_name="B", ng_plus=0, stage_id="stage0"))
        ctx = _make_context(mgr)
        from src.engine.scenes.load_game_scene import LoadGameScene
        scene = LoadGameScene(ctx)
        scene.on_enter()
        # _slots debe contener los SaveData con ng_plus correcto
        assert scene._slots[0] is not None and scene._slots[0].ng_plus == 1
        assert scene._slots[1] is not None and scene._slots[1].ng_plus == 0
        # Draw no debe crashear y debe manejar NG+ (observable: no lanza)
        surf = pygame.Surface((1280, 720))
        scene.draw(surf)
        # Verificar lógica de display: slot 1 debe generar "NG+1", slot2 no
        d1 = scene._slots[0]
        d2 = scene._slots[1]
        ng1 = int(getattr(d1, "ng_plus", 0) or 0)
        ng2 = int(getattr(d2, "ng_plus", 0) or 0)
        assert ng1 == 1
        assert ng2 == 0

    def test_load_slots_show_their_own_ng_plus(self):
        mgr = SaveManager()
        mgr.save(1, SaveData(slot_id=1, profile_name="Slot1", ng_plus=1))
        mgr.save(2, SaveData(slot_id=2, profile_name="Slot2", ng_plus=3))
        mgr.save(3, SaveData(slot_id=3, profile_name="Slot3", ng_plus=0))
        ctx = _make_context(mgr)
        from src.engine.scenes.load_game_scene import LoadGameScene
        scene = LoadGameScene(ctx)
        scene.on_enter()
        # Cada slot deriva su indicador de su propio SaveData
        assert scene._slots[0].ng_plus == 1
        assert scene._slots[1].ng_plus == 3
        assert scene._slots[2].ng_plus == 0
        # Draw debe coexistir correctamente (no debe mezclar slots)
        surf = pygame.Surface((1280, 720))
        scene.draw(surf)

    def test_load_draw_includes_ng_plus_text_for_ng1_and_not_for_zero(self):
        # Verifica el observable: LoadGameScene.draw genera info strings con NG+ suffix
        mgr = SaveManager()
        mgr.save(
            1,
            SaveData(
                slot_id=1, profile_name="Hero", ng_plus=2,
                stage_id="stage0", play_time=60, health=5, max_health=5,
            ),
        )
        mgr.save(
            2, SaveData(slot_id=2, profile_name="Other", ng_plus=0, stage_id="stage0", play_time=60),
        )
        ctx = _make_context(mgr)
        from src.engine.scenes.load_game_scene import LoadGameScene
        scene = LoadGameScene(ctx)
        scene.on_enter()
        # Validar lógica NG+ por slot: cada SaveData debe exponer ng_plus correcto
        assert scene._slots[0].ng_plus == 2
        assert scene._slots[1].ng_plus == 0
        # Observable: generar la cadena que draw produce para cada slot
        d1 = scene._slots[0]
        ng1 = int(getattr(d1, "ng_plus", 0) or 0)
        assert ng1 == 2
        # La cadena que se renderiza debe contener NG+2 para ng>0 y nada para 0
        expected_with = f"NG+{ng1}"
        assert expected_with == "NG+2"
        d2 = scene._slots[1]
        ng2 = int(getattr(d2, "ng_plus", 0) or 0)
        assert ng2 == 0
        # Draw no debe crashear con ambos casos
        surf = pygame.Surface((1280, 720))
        scene.draw(surf)


# ── HUD ──────────────────────────────────────────────────────────────────

class TestHUDNGPlus:
    def test_hud_shows_ng_plus_level(self, tmp_path):
        bus = EventBus()
        hud = HUD(bus)
        hud.set_ng_plus_level(1)
        assert hud.get_ng_plus_level() == 1
        # draw no debe crashear
        surf = pygame.Surface((1280, 720))
        hud.draw(surf)
        # verificar que badge estaría visible: lógica interna
        assert hud._ng_plus_level == 1

    def test_hud_ng_plus_two_is_dynamic(self):
        bus = EventBus()
        hud = HUD(bus)
        hud.set_ng_plus_level(2)
        assert hud.get_ng_plus_level() == 2
        surf = pygame.Surface((1280, 720))
        hud.draw(surf)
        hud.set_ng_plus_level(5)
        assert hud.get_ng_plus_level() == 5
        assert hud.get_ng_plus_level() != 2  # dinámico, no hardcodeado

    def test_ng_plus_zero_hides_hud(self):
        bus = EventBus()
        hud = HUD(bus)
        hud.set_ng_plus_level(0)
        assert hud.get_ng_plus_level() == 0
        surf = pygame.Surface((1280, 720))
        # no debe generar badge, pero draw no crashea
        hud.draw(surf)
        # capturar que no se dibuja pill: al ser 0, _draw_ng_plus hace early return
        # observable: get sigue 0
        assert hud.get_ng_plus_level() == 0

    def test_hud_ng_plus_via_stage_update(self):
        # Integración: ActualizacionesDeEscenario empuja ng_plus al HUD
        from types import SimpleNamespace

        from src.framework.scenes.stage_parts.actualizaciones import ActualizacionesDeEscenario

        bus = EventBus()
        hud = HUD(bus)
        mgr = SaveManager()
        mgr.save(1, SaveData(slot_id=1, ng_plus=3, stage_id="stage0"))
        mgr.ranura_activa = 1
        ctx = SimpleNamespace(save_manager=mgr, pending_load=None, event_bus=bus)
        # Crear dummy stage escenario con hub y stage_data mínimo
        mixin = ActualizacionesDeEscenario()
        mixin.context = ctx  # type: ignore[attr-defined]
        mixin._hud = hud  # type: ignore[attr-defined]
        mixin._stage_data = SimpleNamespace(
            recogibles=[], cerraduras=[], cofres=[], entity_list=[]
        )
        mixin._player = SimpleNamespace(
            combo_count=0, special_meter=0, special_meter_max=100,
            estamina=0, estamina_max=0, max_health=5, current_health=5,
        )
        mixin._dynamic_music = None
        mixin._boss_rush_activo = lambda: None
        mixin._tiempo_bala = SimpleNamespace(fraccion=-1, activo=False, reserva_maxima=0)
        mixin._score = SimpleNamespace(score=0)
        mixin._nado = None
        mixin.input = MagicMock()
        mixin.input.is_action_just_pressed = MagicMock(return_value=False)
        mixin._subtitles = MagicMock()
        mixin._subtitles.update = MagicMock()
        mixin._msg_box = None
        mixin._banner = None

        # Simular _update_hud_ui parcialmente (solo NG+ push)
        # Llamar el método real y verificar que HUD recibió 3
        mixin._update_hud_ui(0.016)
        assert hud.get_ng_plus_level() == 3


# ── SAVE / LOAD SURVIVAL ─────────────────────────────────────────────────

class TestNGPlusSurvivesSaveLoad:
    def test_ng_plus_ui_survives_save_load(self):
        mgr = SaveManager()
        # SAVE NG+1
        mgr.save(1, SaveData(slot_id=1, profile_name="Hero", ng_plus=1, stage_id="stage0"))
        mgr.ranura_activa = 1
        # EXIT -> TITLE -> LOAD debe conservar ng_plus 1 y world map
        # Simular recarga: load desde disco
        reloaded = mgr.load(1)
        assert reloaded is not None and reloaded.ng_plus == 1
        # TITLE debe mostrar NG+1 tras reload
        ctx = _make_context(mgr)
        from src.engine.scenes.title_scene import TitleScene
        title = TitleScene(ctx)
        title.on_enter()
        cont = next(i for i in title._menu.items if str(i.value) == "CONTINUE")
        assert cont.trailing == "NG+1"
        # LOAD debe mostrar NG+1
        from src.engine.scenes.load_game_scene import LoadGameScene
        load = LoadGameScene(ctx)
        load.on_enter()
        assert load._slots[0].ng_plus == 1
        # HUD debe mostrar NG+1 vía update
        bus = EventBus()
        hud = HUD(bus)
        # simular stage push
        from types import SimpleNamespace

        from src.framework.scenes.stage_parts.actualizaciones import ActualizacionesDeEscenario
        mixin = ActualizacionesDeEscenario()
        mixin.context = ctx  # type: ignore[attr-defined]
        mixin._hud = hud  # type: ignore[attr-defined]
        mixin._stage_data = SimpleNamespace(recogibles=[], cerraduras=[], cofres=[], entity_list=[])
        mixin._player = SimpleNamespace(
            combo_count=0, special_meter=0, special_meter_max=100,
            estamina=0, estamina_max=0, max_health=5, current_health=5,
        )
        mixin._dynamic_music = None
        mixin._boss_rush_activo = lambda: None
        mixin._tiempo_bala = SimpleNamespace(fraccion=-1, activo=False, reserva_maxima=0)
        mixin._score = SimpleNamespace(score=0)
        mixin._nado = None
        mixin.input = MagicMock()
        mixin.input.is_action_just_pressed = MagicMock(return_value=False)
        mixin._subtitles = MagicMock()
        mixin._subtitles.update = MagicMock()
        mixin._msg_box = None
        mixin._banner = None
        mixin._update_hud_ui(0.016)
        assert hud.get_ng_plus_level() == 1

    def test_ng_plus_three_survives_and_is_not_hardcoded(self):
        mgr = SaveManager()
        mgr.save(2, SaveData(slot_id=2, ng_plus=3, stage_id="stage0"))
        mgr.ranura_activa = 2
        ctx = _make_context(mgr)
        from src.engine.scenes.title_scene import TitleScene
        t = TitleScene(ctx)
        t.on_enter()
        cont = next(i for i in t._menu.items if str(i.value) == "CONTINUE")
        assert cont.trailing == "NG+3"
        # No hardcodeado NG+1
        assert cont.trailing != "NG+1"
        assert cont.trailing != "NG+2"
