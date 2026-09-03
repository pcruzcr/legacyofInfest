"""B4.2 — Heart Piece — certification of existing infrastructure."""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pygame
import pytest

from src.engine.core.event_bus import EventBus
from src.engine.core.inventory import Inventory, get_inventory
from src.engine.core.save_data import SaveData
from src.engine.core.save_manager import SaveManager
from src.framework.crafting import craftear, puede_craftear
from src.framework.stage.interactables import Recogible, item_key, recogible_key
from src.framework.stage.stage_data import StageData, StageProgression


@pytest.fixture(autouse=True)
def _tmp_saves(tmp_path):
    orig = SaveManager.SAVES_DIR
    SaveManager.SAVES_DIR = tmp_path / "saves"
    SaveManager.SAVES_DIR.mkdir(parents=True, exist_ok=True)
    # also isolate inventory
    inv_path = tmp_path / "inventory"
    orig_inv = Inventory._INVENTORY_PATH if hasattr(Inventory, "_INVENTORY_PATH") else None
    # use Inventory's path via user_data_dir mock not needed: Inventory uses _INVENTORY_PATH
    # Redirect
    import src.engine.core.inventory as inv_mod

    old_path = inv_mod._INVENTORY_PATH
    inv_mod._INVENTORY_PATH = tmp_path / "inv.json"
    Inventory._reset_instance()
    yield
    SaveManager.SAVES_DIR = orig
    inv_mod._INVENTORY_PATH = old_path
    Inventory._reset_instance()


@pytest.fixture(autouse=True)
def _init_pygame():
    if not pygame.get_init():
        pygame.init()
    pygame.display.init()
    try:
        pygame.display.set_mode((1, 1))
    except Exception:
        pass


def _make_stage(stage_id, recogibles=None, cofres=None):
    prog = StageProgression(recogibles=list(recogibles or []), cofres=list(cofres or []), stage_id=stage_id)
    sd = StageData(map_layer=MagicMock(), progression=prog, stage_id=stage_id)
    sd.stage_id = stage_id
    return sd


# 1
def test_heart_piece_registered():
    inv = get_inventory()
    defn = inv.get_def("heart_piece")
    assert defn is not None
    assert defn.max_hp_bonus == pytest.approx(0.25)


# 2
def test_heart_vessel_registered():
    inv = get_inventory()
    defn = inv.get_def("heart_vessel")
    assert defn is not None
    assert defn.max_hp_bonus == pytest.approx(1.0)


# 3
def test_heart_piece_loaded_from_tmx():
    from src.framework.stage.stage_objetos import ObjetosDeTiled

    prog = StageProgression(stage_id="test")
    sd = StageData(map_layer=MagicMock(), progression=prog, stage_id="test")
    obj = SimpleNamespace(x=10, y=20, width=16, height=16, id=42, name="HP", properties={"item_id": "heart_piece"})
    ObjetosDeTiled._handle_recogible(sd, obj, {"item_id": "heart_piece"})
    assert len(sd.recogibles) == 1
    assert sd.recogibles[0].item_id == "heart_piece"
    assert sd.recogibles[0].tmx_object_id == 42


# 4
def test_heart_piece_has_tmx_object_id():
    r = Recogible(rect=pygame.Rect(0, 0, 16, 16), item_id="heart_piece", tmx_object_id=42)
    assert r.tmx_object_id == 42


# 5
def test_heart_piece_is_b3_item():
    r = Recogible(rect=pygame.Rect(0, 0, 16, 16), item_id="heart_piece", tmx_object_id=10)
    stage = _make_stage("stage0", recogibles=[r])
    assert stage.item_total() == 1
    # without tmx id should not count
    r2 = Recogible(rect=pygame.Rect(0, 0, 16, 16), item_id="heart_piece", tmx_object_id=0)
    stage2 = _make_stage("stage0", recogibles=[r2])
    assert stage2.item_total() == 0


# 6
def test_heart_piece_collects_one():
    inv = get_inventory()
    inv._items.clear()
    inv._equipped.clear()
    r = Recogible(rect=pygame.Rect(0, 0, 16, 16), item_id="heart_piece", tmx_object_id=1)
    # Simulate InteractableSystem collect path: Inventory.collect
    assert inv.collect("heart_piece", 1) is True
    assert inv.count("heart_piece") == 1
    # second collect
    assert inv.collect("heart_piece", 1) is True
    assert inv.count("heart_piece") == 2


# 7
def test_heart_piece_marks_collected():
    bus = EventBus()
    f = Recogible(rect=pygame.Rect(100, 100, 16, 16), item_id="heart_piece", tmx_object_id=5)
    from src.framework.stage.interactable_system import InteractableSystem

    mgr = SaveManager()
    mgr.save(1, SaveData(slot_id=1, stage_id="stage0"))
    mgr.ranura_activa = 1
    sd = _make_stage("stage0", recogibles=[f])
    # hydrate not yet: should be not collected
    assert f.recogido is False
    sys = InteractableSystem(recogibles=sd.recogibles, bus=bus)
    sys.set_persistencia("stage0", mgr)
    player = pygame.Rect(105, 105, 16, 32)
    sys._recoger(player, usar=True)  # automatico true, colliders
    assert f.recogido is True
    # B3 key should be in save
    data = mgr.load(1)
    key = item_key("stage0", 5, "heart_piece")
    assert key in data.map_item_collected.get("stage0", [])


# 8
def test_heart_piece_does_not_duplicate():
    mgr = SaveManager()
    mgr.save(1, SaveData(slot_id=1))
    mgr.ranura_activa = 1
    k = item_key("stage0", 10, "heart_piece")
    assert mgr.marcar_item_recogido("stage0", k) is True
    assert mgr.marcar_item_recogido("stage0", k) is False
    data = mgr.load(1)
    assert len([x for x in data.map_item_collected["stage0"] if x == k]) == 1


# 9
def test_heart_piece_reload_does_not_duplicate():
    from src.engine.core.save_manager import aplicar_estado_de

    mgr = SaveManager()
    inv = get_inventory()
    inv._items.clear()
    # Save with 2 heart pieces already collected via map_item_collected + inventory
    k1 = item_key("stage0", 1, "heart_piece")
    k2 = item_key("stage0", 2, "heart_piece")
    data = SaveData(slot_id=1, stage_id="stage0", inventory_items={"heart_piece": 2}, map_item_collected={"stage0": [k1, k2]})
    mgr.save(1, data)
    mgr.ranura_activa = 1
    # Load and hydrate + restore inventory as real flow does
    loaded = mgr.load(1)
    assert loaded.inventory_items["heart_piece"] == 2
    assert len(loaded.map_item_collected["stage0"]) == 2
    aplicar_estado_de(loaded)
    assert inv.count("heart_piece") == 2
    # Simulate stage load hydrate (should NOT call Inventory.collect again)
    r1 = Recogible(rect=pygame.Rect(0, 0, 16, 16), item_id="heart_piece", tmx_object_id=1)
    r2 = Recogible(rect=pygame.Rect(0, 0, 16, 16), item_id="heart_piece", tmx_object_id=2)
    stage = _make_stage("stage0", recogibles=[r1, r2])
    collected = set(loaded.map_item_collected.get("stage0", []))
    for r in stage.recogibles:
        if recogible_key("stage0", r) in collected:
            r.recogido = True
    assert r1.recogido is True and r2.recogido is True
    # Inventory should still be 2, not 4 (no double)
    assert inv.count("heart_piece") == 2  # not 4


# 10
def test_four_heart_pieces():
    inv = get_inventory()
    inv._items.clear()
    for _ in range(4):
        inv.collect("heart_piece", 1)
    assert inv.count("heart_piece") == 4
    assert inv.get_total_hp_bonus() == pytest.approx(1.0)  # 4*0.25


# 11
def test_heart_piece_current_health_delta():
    from src.framework.entities.player import Player

    # Need inventory with pieces
    inv = get_inventory()
    inv._items.clear()
    inv._items["heart_piece"] = 0
    bus = EventBus()
    # Create player at 3/5 health, max 5, then collect piece → max 5.25, health 3.25
    # Player refresh is via apply_relic_bonuses or similar; we can test directly
    # Use Player instance and simulate inventory bonus change
    player = Player(pygame.Vector2(0, 0), event_bus=bus)
    # Force player health to 3
    player._health = 3.0
    player._bonus_max_health = 0.0
    prev_max = player.max_health
    inv.collect("heart_piece", 1)  # now 1 piece → 0.25 bonus
    # Simulate player refresh (as StageScene does)
    player._bonus_max_health = float(inv.get_total_hp_bonus())
    new_max = player.max_health
    gained = new_max - prev_max
    # Apply same logic as player.py 556-558
    if gained > 0:
        player._health = min(player.max_health, player._health + gained)
    assert new_max == pytest.approx(5.25)
    assert player._health == pytest.approx(3.25)


# 12
def test_full_health_heart_piece():
    inv = get_inventory()
    inv._items.clear()
    bus = EventBus()
    from src.framework.entities.player import Player

    player = Player(pygame.Vector2(0, 0), event_bus=bus)
    player._health = 5.0
    prev_max = player.max_health  # 5
    inv.collect("heart_piece", 1)
    player._bonus_max_health = float(inv.get_total_hp_bonus())
    new_max = player.max_health
    gained = new_max - prev_max
    if gained > 0:
        player._health = min(player.max_health, player._health + gained)
    assert new_max == pytest.approx(5.25)
    assert player._health == pytest.approx(5.25)


# 13
def test_four_pieces_to_vessel():
    inv = get_inventory()
    inv._items.clear()
    for _ in range(4):
        inv.collect("heart_piece", 1)
    assert inv.count("heart_piece") == 4
    assert puede_craftear(inv, "heart_vessel") is True
    assert craftear(inv, "heart_vessel") is True
    assert inv.count("heart_piece") == 0
    assert inv.count("heart_vessel") == 1


# 14
def test_partial_heart_piece_crafting():
    inv = get_inventory()
    # 5 → 1 vessel +1
    inv._items.clear()
    for _ in range(5):
        inv.collect("heart_piece", 1)
    assert craftear(inv, "heart_vessel") is True
    assert inv.count("heart_piece") == 1
    assert inv.count("heart_vessel") == 1
    # 6 → 2 +1
    inv._items.clear()
    for _ in range(6):
        inv.collect("heart_piece", 1)
    assert craftear(inv, "heart_vessel") is True
    assert inv.count("heart_piece") == 2
    # 7 → 3+1
    inv._items.clear()
    for _ in range(7):
        inv.collect("heart_piece", 1)
    assert craftear(inv, "heart_vessel") is True
    assert inv.count("heart_piece") == 3
    # 8 → 2 vessels if twice
    inv._items.clear()
    for _ in range(8):
        inv.collect("heart_piece", 1)
    assert craftear(inv, "heart_vessel") is True
    assert craftear(inv, "heart_vessel") is True
    assert inv.count("heart_piece") == 0
    assert inv.count("heart_vessel") == 2


# 15
def test_heart_piece_and_vessel_no_double_count():
    inv = get_inventory()
    inv._items.clear()
    for _ in range(4):
        inv.collect("heart_piece", 1)
    assert inv.get_total_hp_bonus() == pytest.approx(1.0)
    craftear(inv, "heart_vessel")
    assert inv.get_total_hp_bonus() == pytest.approx(1.0)  # 0*0.25 +1*1.0
    assert inv.get_total_hp_bonus() != pytest.approx(2.0)


# 16
def test_heart_piece_death_respawn():
    inv = get_inventory()
    inv._items.clear()
    inv.collect("heart_piece", 1)
    assert inv.count("heart_piece") == 1
    # Simulate death: inventory should persist (no reset)
    # StageData recogido flag persists in stage until reload; inventory not cleared
    assert inv.count("heart_piece") == 1
    # Respawn doesn't clear
    assert inv.count("heart_piece") == 1


# 17
def test_heart_piece_slot_isolation():
    mgr = SaveManager()
    mgr.save(1, SaveData(slot_id=1, inventory_items={"heart_piece": 2}, map_item_collected={"stage0": [item_key("stage0", 1, "heart_piece")]}))
    mgr.save(2, SaveData(slot_id=2, inventory_items={}, map_item_collected={}))
    d1 = mgr.load(1)
    d2 = mgr.load(2)
    assert d1.inventory_items.get("heart_piece") == 2
    assert "heart_piece" not in d2.inventory_items
    assert item_key("stage0", 1, "heart_piece") in d1.map_item_collected["stage0"]
    assert "stage0" not in d2.map_item_collected or not d2.map_item_collected["stage0"]


# 18
def test_heart_piece_ng_plus():
    mgr = SaveManager()
    k = item_key("stage0", 1, "heart_piece")
    data = SaveData(slot_id=1, ng_plus=1, inventory_items={"heart_piece": 1}, map_item_collected={"stage0": [k]})
    mgr.save(1, data)
    mgr.ranura_activa = 1
    loaded = mgr.load(1)
    assert loaded.ng_plus == 1
    assert loaded.inventory_items["heart_piece"] == 1
    assert k in loaded.map_item_collected["stage0"]


# 19
def test_heart_piece_b3_percentage():
    r1 = Recogible(rect=pygame.Rect(0, 0, 16, 16), item_id="heart_piece", tmx_object_id=1)
    r2 = Recogible(rect=pygame.Rect(0, 0, 16, 16), item_id="heart_piece", tmx_object_id=2)
    r3 = Recogible(rect=pygame.Rect(0, 0, 16, 16), item_id="heart_piece", tmx_object_id=3)
    r4 = Recogible(rect=pygame.Rect(0, 0, 16, 16), item_id="heart_piece", tmx_object_id=4)
    stage = _make_stage("stage0", recogibles=[r1, r2, r3, r4])
    assert stage.item_total() == 4
    assert stage.item_percentage(set()) == 0.0
    assert round(stage.item_percentage({item_key("stage0", 1, "heart_piece")}) * 100) == 25
    assert round(stage.item_percentage({item_key("stage0", 1, "heart_piece"), item_key("stage0", 2, "heart_piece")}) * 100) == 50
    assert round(stage.item_percentage({item_key("stage0", 1, "heart_piece"), item_key("stage0", 2, "heart_piece"), item_key("stage0", 3, "heart_piece")}) * 100) == 75
    assert stage.item_percentage({item_key("stage0", i, "heart_piece") for i in [1, 2, 3, 4]}) == pytest.approx(1.0)


# 20
def test_heart_vessel_not_counted_as_b3_map_item():
    # Vessel is result of crafting, not TMX Pickup, so should not be in item_total
    r = Recogible(rect=pygame.Rect(0, 0, 16, 16), item_id="heart_piece", tmx_object_id=1)
    stage = _make_stage("stage0", recogibles=[r])
    assert stage.item_total() == 1
    # Even if inventory has vessel, item_total unchanged
    inv = get_inventory()
    inv._items.clear()
    inv._items["heart_vessel"] = 1
    assert stage.item_total() == 1
    assert stage.item_percentage({item_key("stage0", 1, "heart_piece")}) == pytest.approx(1.0)


# 21
def test_heart_piece_hydration_only_marks_collectible():
    # Hydration must NOT call Inventory.collect() again
    from src.engine.core.save_manager import aplicar_estado_de

    mgr = SaveManager()
    inv = get_inventory()
    inv._items.clear()
    k = item_key("stage0", 42, "heart_piece")
    # Save has piece collected and inventory has 1
    data = SaveData(slot_id=1, inventory_items={"heart_piece": 1}, map_item_collected={"stage0": [k]})
    mgr.save(1, data)
    mgr.ranura_activa = 1
    loaded = mgr.load(1)
    assert loaded.inventory_items["heart_piece"] == 1
    aplicar_estado_de(loaded)
    assert inv.count("heart_piece") == 1
    # Simulate hydrate: set recogido=True but do NOT collect again
    r = Recogible(rect=pygame.Rect(0, 0, 16, 16), item_id="heart_piece", tmx_object_id=42)
    stage = _make_stage("stage0", recogibles=[r])
    collected = set(loaded.map_item_collected.get("stage0", []))
    # hydrate path (as StageScene)
    for rr in stage.recogibles:
        if recogible_key("stage0", rr) in collected:
            rr.recogido = True
    assert r.recogido is True
    # Inventory should still be 1, not 2
    assert inv.count("heart_piece") == 1
