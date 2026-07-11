from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from src.engine.core.save_data import MAX_SLOTS, SaveData


class SaveManager:
    SAVES_DIR = Path("saves")

    def __init__(self) -> None:
        self.SAVES_DIR.mkdir(parents=True, exist_ok=True)

    def _slot_path(self, slot: int) -> Path:
        return self.SAVES_DIR / f"slot_{slot}.json"

    def save(self, slot: int, data: SaveData) -> str:
        if slot < 1 or slot > MAX_SLOTS:
            raise ValueError(f"Slot must be 1-{MAX_SLOTS}, got {slot}")
        data.slot_id = slot
        path = self._slot_path(slot)
        path.write_text(json.dumps(data.to_dict(), indent=2), encoding="utf-8")
        logging.info(f"SaveManager: saved slot {slot} -> {path}")
        return str(path)

    def load(self, slot: int) -> SaveData | None:
        path = self._slot_path(slot)
        if not path.exists():
            return None
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            raw = SaveData.migrate(raw)
            return SaveData.from_dict(raw)
        except Exception as e:
            logging.warning(f"SaveManager: corrupt save slot {slot}: {e}")
            return None

    def delete(self, slot: int) -> None:
        path = self._slot_path(slot)
        if path.exists():
            path.unlink()
            logging.info(f"SaveManager: deleted slot {slot}")

    def list_slots(self) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        for slot in range(1, MAX_SLOTS + 1):
            data = self.load(slot)
            if data is not None:
                result.append({
                    "slot": slot,
                    "stage_id": data.stage_id,
                    "timestamp": data.timestamp,
                    "health": data.health,
                    "max_health": data.max_health,
                })
        return result

    def has_saves(self) -> bool:
        for slot in range(1, MAX_SLOTS + 1):
            if self._slot_path(slot).exists():
                return True
        return False

    def newest_slot(self) -> int | None:
        best = None
        best_time = ""
        for slot in range(1, MAX_SLOTS + 1):
            data = self.load(slot)
            if data is not None and data.timestamp > best_time:
                best_time = data.timestamp
                best = slot
        return best

    def auto_save(self, stage_id: str, stage_index: int,
                  checkpoint_x: float, checkpoint_y: float,
                  health: float, max_health: float) -> str | None:
        from datetime import datetime
        slot = self.newest_slot() or 1
        data = SaveData(
            slot_id=slot,
            timestamp=datetime.now().isoformat(),
            stage_id=stage_id,
            stage_index=stage_index,
            checkpoint_x=checkpoint_x,
            checkpoint_y=checkpoint_y,
            health=health,
            max_health=max_health,
        )
        return self.save(slot, data)
