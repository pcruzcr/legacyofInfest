"""B3 — Item Completion — 19 tests contract."""
from __future__ import annotations

import pygame
import pytest

from src.engine.core.event_bus import EventBus
from src.engine.core.save_data import SAVE_VERSION, SaveData
from src.engine.core.save_manager import SaveManager
from src.engine.ui.hud import HUD
from src.framework.stage.interactables import (
    Cerradura,
    Cofre,
    Fogata,
    Recogible,
    item_key,
)
from src.framework.stage.stage_data import StageData, StageProgression


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
    try:
        pygame.display.set_mode((1, 1))
    except Exception:
        pass


def _make_stage(stage_id: str, recogibles=None, cofres=None, cerraduras=None, secret_rooms=None):
    prog = StageProgression(
        recogibles=list(recogibles or []),
        cofres=list(cofres or []),
        cerraduras=list(cerraduras or []),
        secret_rooms=list(secret_rooms or []),
        stage_id=stage_id,
    )
    # StageData needs map_layer mock; use MagicMock group
    from unittest.mock import MagicMock

    mock_group = MagicMock()
    sd = StageData(map_layer=mock_group, progression=prog, stage_id=stage_id)
    # also set stage_id directly for compatibility
    sd.stage_id = stage_id
    return sd


# ── TOTAL ────────────────────────────────────────────────────────────────────

def test_total_items():
    r1 = Recogible(rect=pygame.Rect(0, 0, 16, 16), item_id="fragmento", tmx_object_id=1)
    r2 = Recogible(rect=pygame.Rect(0, 0, 16, 16), item_id="llave", tmx_object_id=2)
    c1 = Cofre(rect=pygame.Rect(0, 0, 16, 16), contenido="heart_vessel", tmx_object_id=3)
    d1 = Cerradura(rect=pygame.Rect(0, 0, 16, 16), key_id="llave")
    stage = _make_stage("stage0", recogibles=[r1, r2], cofres=[c1], cerraduras=[d1])
    assert stage.item_total() == 3
    # Door not counted
    assert stage.item_total() != 4


def test_chest_empty_not_counted():
    c_empty = Cofre(rect=pygame.Rect(0, 0, 16, 16), contenido="", tmx_object_id=10)
    stage = _make_stage("stage0", cofres=[c_empty])
    assert stage.item_total() == 0
    # with content counts
    c_full = Cofre(rect=pygame.Rect(0, 0, 16, 16), contenido="coin", tmx_object_id=10)
    stage2 = _make_stage("stage0", cofres=[c_full])
    assert stage2.item_total() == 1


def test_door_not_counted():
    d = Cerradura(rect=pygame.Rect(0, 0, 16, 16), key_id="k")
    stage = _make_stage("stage0", cerraduras=[d])
    assert stage.item_total() == 0


def test_bonfire_not_counted():
    f = Fogata(rect=pygame.Rect(0, 0, 16, 16))
    stage = _make_stage("stage0", recogibles=[], cofres=[])
    # Fogata lives in StageData.fogatas, not in item_total; ensure not counted
    stage.fogatas = [f]  # type: ignore[attr-defined]
    assert stage.item_total() == 0


def test_heart_piece_counts_as_one():
    r = Recogible(rect=pygame.Rect(0, 0, 16, 16), item_id="heart_piece", tmx_object_id=5)
    stage = _make_stage("stage0", recogibles=[r])
    assert stage.item_total() == 1


# ── COLLECTED / PERCENTAGE ──────────────────────────────────────────────────

def test_item_collected():
    r = Recogible(rect=pygame.Rect(0, 0, 16, 16), item_id="a", tmx_object_id=1)
    stage = _make_stage("stage0", recogibles=[r])
    assert stage.item_collected_count(set()) == 0
    r.recogido = True
    # collected via runtime flags not via set yet: use item_percentage with set containing key
    key = item_key("stage0", 1, "a")
    assert stage.item_collected_count({key}) == 1


def test_chest_collected():
    c = Cofre(rect=pygame.Rect(0, 0, 16, 16), contenido="heart_vessel", tmx_object_id=7)
    stage = _make_stage("stage0", cofres=[c])
    assert stage.item_collected_count(set()) == 0
    key = item_key("stage0", 7, "heart_vessel")
    assert stage.item_collected_count({key}) == 1


def test_percentage_zero():
    r1 = Recogible(rect=pygame.Rect(0, 0, 16, 16), item_id="a", tmx_object_id=1)
    r2 = Recogible(rect=pygame.Rect(0, 0, 16, 16), item_id="b", tmx_object_id=2)
    stage = _make_stage("stage0", recogibles=[r1, r2])
    # 0/2 → 0.0
    assert stage.item_percentage(set()) == 0.0


def test_percentage_partial():
    r1 = Recogible(rect=pygame.Rect(0, 0, 16, 16), item_id="a", tmx_object_id=1)
    r2 = Recogible(rect=pygame.Rect(0, 0, 16, 16), item_id="b", tmx_object_id=2)
    r3 = Recogible(rect=pygame.Rect(0, 0, 16, 16), item_id="c", tmx_object_id=3)
    stage = _make_stage("stage0", recogibles=[r1, r2, r3])
    # 1/3 → 33%
    k1 = item_key("stage0", 1, "a")
    assert stage.item_percentage({k1}) == pytest.approx(1 / 3)
    assert round(stage.item_percentage({k1}) * 100) == 33  # type: ignore[operator]
    k2 = item_key("stage0", 2, "b")
    # 2/3 → 67% round
    assert round(stage.item_percentage({k1, k2}) * 100) == 67  # type: ignore[operator]


def test_percentage_complete():
    r = Recogible(rect=pygame.Rect(0, 0, 16, 16), item_id="a", tmx_object_id=1)
    stage = _make_stage("stage0", recogibles=[r])
    k = item_key("stage0", 1, "a")
    assert stage.item_percentage({k}) == pytest.approx(1.0)


def test_total_zero_safe():
    stage = _make_stage("stage0", recogibles=[], cofres=[])
    assert stage.item_total() == 0
    assert stage.item_percentage(set()) is None
    assert stage.item_percentage(None) is None
    # No division by zero: ghost ids not in map → 0 collected, but total 0 → None
    stage2 = _make_stage("stage0", recogibles=[])
    assert stage2.item_percentage(set(["ghost"])) is None


# ── PERSISTENCE ──────────────────────────────────────────────────────────────

def test_map_item_persistence():
    mgr = SaveManager()
    key = item_key("stage0", 10, "frag")
    # Simulate collect → save → load
    mgr.save(1, SaveData(slot_id=1, stage_id="stage0"))
    mgr.ranura_activa = 1
    assert mgr.marcar_item_recogido("stage0", key) is True
    data = mgr.load(1)
    assert data is not None
    assert key in (data.map_item_collected.get("stage0") or [])
    # Hydrate new stage from save
    r2 = Recogible(rect=pygame.Rect(0, 0, 16, 16), item_id="frag", tmx_object_id=10)
    stage2 = _make_stage("stage0", recogibles=[r2])
    # hydrate logic as in StageScene
    collected = set(data.map_item_collected.get("stage0", []))
    for rr in stage2.recogibles:
        from src.framework.stage.interactables import recogible_key

        if recogible_key("stage0", rr) in collected:
            rr.recogido = True
    assert stage2.recogibles[0].recogido is True
    assert stage2.item_percentage(collected) == pytest.approx(1.0)


def test_map_items_do_not_mix_between_maps():
    mgr = SaveManager()
    mgr.save(1, SaveData(slot_id=1))
    mgr.ranura_activa = 1
    k0 = item_key("stage0", 1, "a")
    k1 = item_key("stage4_1b", 1, "a")  # same tmx id but different map
    mgr.marcar_item_recogido("stage0", k0)
    mgr.marcar_item_recogido("stage4_1b", k1)
    data = mgr.load(1)
    assert data is not None
    assert k0 in data.map_item_collected["stage0"]
    assert k1 in data.map_item_collected["stage4_1b"]
    # stage0 percentage should not be affected by stage4_1b set
    r = Recogible(rect=pygame.Rect(0, 0, 16, 16), item_id="a", tmx_object_id=1)
    s0 = _make_stage("stage0", recogibles=[r])
    assert s0.item_percentage(set(data.map_item_collected.get("stage0", []))) == pytest.approx(1.0)
    # stage4_1b with 1 item collected, stage0 not affected
    assert s0.item_percentage(set(data.map_item_collected.get("stage4_1b", []))) == 0.0


def test_new_save_without_item_state():
    data = SaveData(slot_id=1)
    assert data.map_item_collected == {}
    stage = _make_stage("stage0", recogibles=[Recogible(rect=pygame.Rect(0, 0, 16, 16), item_id="a", tmx_object_id=1)])
    assert stage.item_percentage(set(data.map_item_collected.get("stage0", []))) == 0.0


def test_old_save_migration():
    # v5 save without map_item_collected should migrate to v6 with {}
    old = {"version": 5, "stage_id": "stage0", "ng_plus": 1}
    migrated = SaveData.migrate(dict(old))
    assert migrated["version"] == SAVE_VERSION
    assert "map_item_collected" in migrated
    assert migrated["map_item_collected"] == {}
    # loading via from_dict should also migrate and not crash
    data = SaveData.from_dict({"slot_id": 1, "version": 5, "stage_id": "stage0"})
    assert data.version == 6
    assert data.map_item_collected == {}
    assert data.ng_plus == 0 or data.ng_plus == 0  # default


def test_duplicate_collection_ignored():
    mgr = SaveManager()
    mgr.save(1, SaveData(slot_id=1))
    mgr.ranura_activa = 1
    k = item_key("stage0", 1, "a")
    assert mgr.marcar_item_recogido("stage0", k) is True
    assert mgr.marcar_item_recogido("stage0", k) is False
    data = mgr.load(1)
    assert data is not None
    assert len(data.map_item_collected["stage0"]) == 1


def test_collected_gt_total_clamped():
    r = Recogible(rect=pygame.Rect(0, 0, 16, 16), item_id="a", tmx_object_id=1)
    stage = _make_stage("stage0", recogibles=[r])
    # Corrupt save with extra ghost ids
    ghost_set = {item_key("stage0", 1, "a"), item_key("stage0", 99, "ghost"), item_key("stage0", 100, "ghost2")}
    # item_percentage should clamp to 1.0
    assert stage.item_percentage(ghost_set) == pytest.approx(1.0)


def test_map_reload_without_save():
    # Collect without save → reload → lost (not exploit, but not duplicated)
    mgr = SaveManager()
    mgr.save(1, SaveData(slot_id=1))
    mgr.ranura_activa = 1
    r = Recogible(rect=pygame.Rect(0, 0, 16, 16), item_id="a", tmx_object_id=1)
    stage = _make_stage("stage0", recogibles=[r])
    # Simulate collect but NOT persisting (e.g., death before save)
    r.recogido = True
    assert stage.item_collected_count({item_key("stage0", 1, "a")}) == 1
    # Reload fresh stage without save → should be not collected
    r2 = Recogible(rect=pygame.Rect(0, 0, 16, 16), item_id="a", tmx_object_id=1)
    stage2 = _make_stage("stage0", recogibles=[r2])
    # No save, so collected set empty → not collected
    assert stage2.recogibles[0].recogido is False
    assert stage2.item_percentage(set()) == 0.0


def test_hud_shows_only_when_total_gt_0():
    bus = EventBus()
    hud = HUD(bus)
    # TOTAL 0 → None -> hud should hide
    hud.set_porcentaje_items(None)
    assert hud._porcentaje_items is None
    surf = pygame.Surface((1280, 720))
    hud.draw(surf)  # should not crash
    # TOTAL >0 with 0% → show 0%
    hud.set_porcentaje_items(0.0, 0, 3)
    assert hud._porcentaje_items == 0.0
    hud.draw(surf)
    # 100%
    hud.set_porcentaje_items(1.0, 3, 3)
    assert hud._porcentaje_items == 1.0
    hud.draw(surf)


def test_json_determinism():
    mgr = SaveManager()
    mgr.save(1, SaveData(slot_id=1))
    mgr.ranura_activa = 1
    k1 = item_key("stage0", 3, "c")
    k2 = item_key("stage0", 1, "a")
    k3 = item_key("stage0", 2, "b")
    mgr.marcar_item_recogido("stage0", k1)
    mgr.marcar_item_recogido("stage0", k2)
    mgr.marcar_item_recogido("stage0", k3)
    data = mgr.load(1)
    assert data is not None
    lst = data.map_item_collected["stage0"]
    assert lst == sorted(lst)
    # Save again and reload, ordering remains
    raw = data.to_json()
    data2 = SaveData.from_json(raw)
    assert data2.map_item_collected["stage0"] == sorted(lst)


def test_save_slot_isolation():
    mgr = SaveManager()
    mgr.save(1, SaveData(slot_id=1, profile_name="A"))
    mgr.save(2, SaveData(slot_id=2, profile_name="B"))
    mgr.ranura_activa = 1
    k = item_key("stage0", 1, "a")
    mgr.marcar_item_recogido("stage0", k)
    mgr.ranura_activa = 2
    k2 = item_key("stage0", 2, "b")
    mgr.marcar_item_recogido("stage0", k2)
    d1 = mgr.load(1)
    d2 = mgr.load(2)
    assert k in d1.map_item_collected["stage0"]
    assert k not in d2.map_item_collected.get("stage0", [])
    assert k2 in d2.map_item_collected["stage0"]
    assert k2 not in d1.map_item_collected.get("stage0", [])

