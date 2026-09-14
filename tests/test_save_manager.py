"""
Module: test_save_manager
System: tests
Academic Unit: N/A
Description: Tests for SaveManager and SaveData classes.
Covers: save/load round-trip, corrupt data, missing field defaults,
migration, max slots, and slot validation.
"""
from __future__ import annotations

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
    def test_stage4_1_variante_por_defecto_es_vacia(self) -> None:
        """AUD-518 — vacío significa «todavía no se sorteó», y también es
        lo que trae una partida guardada antes de que este campo existiera
        (aditivo, sin subir `SAVE_VERSION`)."""
        assert SaveData().stage4_1_variante == ""

    def test_stage4_1_variante_sobrevive_al_roundtrip(self) -> None:
        data = SaveData(stage4_1_variante="acuatico")
        restaurada = SaveData.from_dict(data.to_dict())
        assert restaurada.stage4_1_variante == "acuatico"

    def test_to_dict_roundtrip(self) -> None:
        data = SaveData(
            slot_id=2, stage_id="boss_venado", stage_index=1,
            checkpoint_x=50.0, checkpoint_y=80.0,
            health=3.0, max_health=5.0,
            zone_flags={"zone_a": True, "zone_b": False},
            completed_stages=["stage0"],
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
        assert restored.completed_stages == ["stage0"]

    def test_from_dict_missing_fields_get_defaults(self) -> None:
        data: dict = {}
        restored = SaveData.from_dict(data)
        assert restored.slot_id == 0
        assert restored.timestamp == ""
        assert restored.version == SAVE_VERSION
        assert restored.stage_id == ""
        assert restored.stage_index == 0
        assert restored.checkpoint_x == 0.0
        assert restored.checkpoint_y == 0.0
        assert restored.health == 5.0
        assert restored.max_health == 5.0
        assert restored.zone_flags == {}
        assert restored.completed_stages == []

    def test_from_dict_with_partial_data(self) -> None:
        data = {"slot_id": 3, "stage_id": "stage2", "health": 3.0}
        restored = SaveData.from_dict(data)
        assert restored.slot_id == 3
        assert restored.stage_id == "stage2"
        assert restored.health == 3.0
        assert restored.max_health == 5.0
        assert restored.zone_flags == {}

    def test_migrate_v0_a_la_ultima(self) -> None:
        old = {"version": 0, "stage_id": "stage0"}
        migrated = SaveData.migrate(old)
        assert migrated["version"] == SAVE_VERSION
        assert "zone_flags" in migrated
        assert migrated["zone_flags"] == {}
        assert "completed_stages" in migrated
        assert migrated["completed_stages"] == []
        assert migrated["inventory_items"] == {}

    def test_migrate_v1_a_la_ultima(self) -> None:
        data = {"version": 1, "stage_id": "stage0", "zone_flags": {"a": True}}
        migrated = SaveData.migrate(data)
        assert migrated["version"] == SAVE_VERSION
        assert migrated["zone_flags"] == {"a": True}
        assert migrated["completed_stages"] == []

    def test_migrate_v2_conserva_lo_que_traia(self) -> None:
        """AUD-292 — una partida de la versión 2 no pierde nada al subir."""
        data = {"version": 2, "stage_id": "stage0", "zone_flags": {"a": True},
                "completed_stages": ["stage0"], "exp_total": 400}
        migrated = SaveData.migrate(data)
        assert migrated["version"] == SAVE_VERSION
        assert migrated["completed_stages"] == ["stage0"]
        assert migrated["exp_total"] == 400
        assert migrated["score"] == 0

    def test_migrate_de_la_ultima_no_toca_nada(self) -> None:
        data = {"version": SAVE_VERSION, "stage_id": "stage0",
                "zone_flags": {"a": True}, "completed_stages": [], "score": 120}
        migrated = SaveData.migrate(data)
        assert migrated["version"] == SAVE_VERSION
        assert migrated["score"] == 120

    def test_timestamp_auto_fill(self) -> None:
        data = SaveData(stage_id="test")
        d = data.to_dict()
        assert d["timestamp"] != ""

    def test_max_slots_constant(self) -> None:
        assert MAX_SLOTS == 5

    def test_version_constant(self) -> None:
        """AUD-292 la subió a 3 -inventario, marcador y experiencia dentro de
        la partida-, AUD-438 a 4, que mete además los logros, AUD-NG+ a 5
        con `ng_plus` y B3 a 6 con `map_item_collected`.

        Existe para que subir la versión sea una decisión y no un descuido: si
        falla, hay un escalón nuevo en la escalera y toca comprobar que las
        partidas viejas siguen cargando sin perder nada.
        """
        assert SAVE_VERSION == 6


class TestSaveManager:
    def test_save_and_load(self, save_manager: SaveManager, sample_data: SaveData) -> None:
        path = save_manager.save(1, sample_data)
        assert Path(path).exists()
        loaded = save_manager.load(1)
        assert loaded is not None
        assert loaded.stage_id == "stage0"
        assert loaded.health == 4.5
        assert loaded.checkpoint_x == 100.0

    def test_round_trip_preserves_all_fields(self, save_manager: SaveManager, sample_data: SaveData) -> None:
        save_manager.save(1, sample_data)
        loaded = save_manager.load(1)
        assert loaded is not None
        assert loaded.slot_id == 1
        assert loaded.timestamp == "2026-07-08T12:00:00"
        assert loaded.stage_id == "stage0"
        assert loaded.stage_index == 0
        assert loaded.checkpoint_x == 100.0
        assert loaded.checkpoint_y == 200.0
        assert loaded.health == 4.5
        assert loaded.max_health == 5.0
        assert loaded.zone_flags == {"zone_a": True}

    def test_load_empty_slot_returns_none(self, save_manager: SaveManager) -> None:
        assert save_manager.load(1) is None

    def test_corrupt_save_returns_none(self, save_manager: SaveManager) -> None:
        path = save_manager._slot_path(1)
        path.write_text("not valid json", encoding="utf-8")
        assert save_manager.load(1) is None

    def test_corrupt_with_empty_file_returns_none(self, save_manager: SaveManager) -> None:
        path = save_manager._slot_path(1)
        path.write_text("", encoding="utf-8")
        assert save_manager.load(1) is None

    def test_all_5_slots(self, save_manager: SaveManager, sample_data: SaveData) -> None:
        for slot in range(1, MAX_SLOTS + 1):
            d = SaveData(slot_id=slot, stage_id=f"stage{slot}")
            save_manager.save(slot, d)
        for slot in range(1, MAX_SLOTS + 1):
            loaded = save_manager.load(slot)
            assert loaded is not None
            assert loaded.stage_id == f"stage{slot}"

    def test_invalid_slot_raises(self, save_manager: SaveManager, sample_data: SaveData) -> None:
        with pytest.raises(ValueError):
            save_manager.save(0, sample_data)
        with pytest.raises(ValueError):
            save_manager.save(6, sample_data)

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

    def test_overwrite_slot(self, save_manager: SaveManager, sample_data: SaveData) -> None:
        save_manager.save(1, sample_data)
        d2 = SaveData(slot_id=1, stage_id="boss_venado", health=1.0, max_health=5.0)
        save_manager.save(1, d2)
        loaded = save_manager.load(1)
        assert loaded is not None
        assert loaded.stage_id == "boss_venado"
        assert loaded.health == 1.0

    def test_fijar_variante_de_stage4_1_persiste_sin_tocar_lo_demas(
        self, save_manager: SaveManager, sample_data: SaveData,
    ) -> None:
        """AUD-518 — read-modify-write, como `auto_save`, pero sólo para
        este campo: el resto del progreso tiene que sobrevivir intacto."""
        save_manager.save(1, sample_data)
        save_manager.ranura_activa = 1

        save_manager.fijar_variante_de_stage4_1("acuatico")

        loaded = save_manager.load(1)
        assert loaded is not None
        assert loaded.stage4_1_variante == "acuatico"
        assert loaded.stage_id == "stage0"
        assert loaded.health == 4.5

    def test_fijar_variante_sin_ranura_activa_usa_la_mas_reciente(
        self, save_manager: SaveManager, sample_data: SaveData,
    ) -> None:
        save_manager.save(1, sample_data)
        # Sin `ranura_activa` declarada — el mismo respaldo que usa
        # `auto_save` (AUD-441).
        save_manager.fijar_variante_de_stage4_1("aereo")
        loaded = save_manager.load(1)
        assert loaded is not None
        assert loaded.stage4_1_variante == "aereo"

    def test_fijar_variante_sin_ninguna_partida_no_revienta(self, save_manager: SaveManager) -> None:
        save_manager.fijar_variante_de_stage4_1("cementerio")  # no debe lanzar
        assert list(save_manager.SAVES_DIR.glob("slot_*.json")) == []
