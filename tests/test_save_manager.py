from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from src.engine.core.save_data import MAX_SLOTS, SAVE_VERSION, SaveData
from src.engine.core.save_manager import SaveManager


@pytest.fixture
def save_manager(tmp_path: Path) -> SaveManager:
    sm = SaveManager()
    sm.SAVES_DIR = tmp_path / "saves"
    sm.SAVES_DIR.mkdir(parents=True, exist_ok=True)
    return sm


@pytest.fixture
def sample_data() -> SaveData:
    return SaveData(
        slot_id=1,
        timestamp="2026-07-08T12:00:00",
        stage_id="stage0",
        stage_index=0,
        checkpoint_x=100.0,
        checkpoint_y=200.0,
        health=4.5,
        max_health=5.0,
        zone_flags={"zone_a": True},
    )


class TestSaveData:
    def test_to_dict_roundtrip(self) -> None:
        data = SaveData(
            slot_id=2, stage_id="boss_venado", stage_index=1,
            checkpoint_x=50.0, checkpoint_y=80.0,
            health=3.0, max_health=5.0,
            zone_flags={"zone_a": True, "zone_b": False},
        )
        d = data.to_dict()
        restored = SaveData.from_dict(d)
        assert restored.slot_id == 2
        assert restored.stage_id == "boss_venado"
        assert restored.stage_index == 1
        assert restored.checkpoint_x == 50.0
        assert restored.checkpoint_y == 80.0
        assert restored.health == 3.0
        assert restored.max_health == 5.0
        assert restored.zone_flags == {"zone_a": True, "zone_b": False}

    def test_migrate_v0_to_v2(self) -> None:
        old = {"version": 0, "stage_id": "stage0"}
        migrated = SaveData.migrate(old)
        assert migrated["version"] == 2
        assert "zone_flags" in migrated
        assert migrated["zone_flags"] == {}
        assert "completed_stages" in migrated
        assert migrated["completed_stages"] == []

    def test_migrate_v1_to_v2(self) -> None:
        data = {"version": 1, "stage_id": "stage0", "zone_flags": {"a": True}}
        migrated = SaveData.migrate(data)
        assert migrated["version"] == 2
        assert migrated["zone_flags"] == {"a": True}
        assert migrated["completed_stages"] == []

    def test_migrate_already_v2(self) -> None:
        data = {"version": 2, "stage_id": "stage0", "zone_flags": {"a": True}, "completed_stages": []}
        migrated = SaveData.migrate(data)
        assert migrated["version"] == 2

    def test_timestamp_auto_fill(self) -> None:
        data = SaveData(stage_id="test")
        d = data.to_dict()
        assert d["timestamp"] != ""


class TestSaveManager:
    def test_save_and_load(self, save_manager: SaveManager, sample_data: SaveData) -> None:
        path = save_manager.save(1, sample_data)
        assert Path(path).exists()
        loaded = save_manager.load(1)
        assert loaded is not None
        assert loaded.stage_id == "stage0"
        assert loaded.health == 4.5
        assert loaded.checkpoint_x == 100.0

    def test_all_5_slots(self, save_manager: SaveManager, sample_data: SaveData) -> None:
        for slot in range(1, MAX_SLOTS + 1):
            d = SaveData(slot_id=slot, stage_id=f"stage{slot}")
            save_manager.save(slot, d)
        for slot in range(1, MAX_SLOTS + 1):
            loaded = save_manager.load(slot)
            assert loaded is not None
            assert loaded.stage_id == f"stage{slot}"

    def test_load_empty_slot(self, save_manager: SaveManager) -> None:
        assert save_manager.load(1) is None

    def test_delete(self, save_manager: SaveManager, sample_data: SaveData) -> None:
        save_manager.save(1, sample_data)
        assert save_manager.load(1) is not None
        save_manager.delete(1)
        assert save_manager.load(1) is None

    def test_list_slots(self, save_manager: SaveManager, sample_data: SaveData) -> None:
        save_manager.save(1, sample_data)
        d2 = SaveData(slot_id=2, stage_id="boss_venado", health=2.0, max_health=5.0)
        save_manager.save(2, d2)
        slots = save_manager.list_slots()
        assert len(slots) == 2
        assert slots[0]["slot"] == 1
        assert slots[1]["slot"] == 2
        assert slots[0]["stage_id"] == "stage0"
        assert slots[1]["stage_id"] == "boss_venado"

    def test_has_saves_false(self, save_manager: SaveManager) -> None:
        assert not save_manager.has_saves()

    def test_has_saves_true(self, save_manager: SaveManager, sample_data: SaveData) -> None:
        save_manager.save(1, sample_data)
        assert save_manager.has_saves()

    def test_newest_slot(self, save_manager: SaveManager, sample_data: SaveData) -> None:
        save_manager.save(1, sample_data)
        newer = SaveData(slot_id=2, timestamp="2026-07-08T13:00:00", stage_id="stage1")
        save_manager.save(2, newer)
        assert save_manager.newest_slot() == 2

    def test_newest_slot_empty(self, save_manager: SaveManager) -> None:
        assert save_manager.newest_slot() is None

    def test_auto_save_creates_slot(self, save_manager: SaveManager) -> None:
        result = save_manager.auto_save(
            stage_id="stage0", stage_index=0,
            checkpoint_x=10.0, checkpoint_y=20.0,
            health=5.0, max_health=5.0,
        )
        assert result is not None
        loaded = save_manager.load(1)
        assert loaded is not None
        assert loaded.stage_id == "stage0"

    def test_corrupt_save_returns_none(self, save_manager: SaveManager) -> None:
        path = save_manager._slot_path(1)
        path.write_text("not valid json", encoding="utf-8")
        assert save_manager.load(1) is None

    def test_invalid_slot_raises(self, save_manager: SaveManager, sample_data: SaveData) -> None:
        with pytest.raises(ValueError):
            save_manager.save(0, sample_data)
        with pytest.raises(ValueError):
            save_manager.save(6, sample_data)

    def test_overwrite_slot(self, save_manager: SaveManager, sample_data: SaveData) -> None:
        save_manager.save(1, sample_data)
        d2 = SaveData(slot_id=1, stage_id="boss_venado", health=1.0, max_health=5.0)
        save_manager.save(1, d2)
        loaded = save_manager.load(1)
        assert loaded is not None
        assert loaded.stage_id == "boss_venado"
        assert loaded.health == 1.0
