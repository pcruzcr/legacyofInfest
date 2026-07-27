from __future__ import annotations

import logging
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import orjson

from src.engine.core import settings
from src.engine.core.save_data import MAX_SLOTS, SaveData

logger = logging.getLogger(__name__)

class SaveManager:
    SAVES_DIR = settings.PROJECT_ROOT / "saves"

    def __init__(self) -> None:
        self.SAVES_DIR.mkdir(parents=True, exist_ok=True)

    def _slot_path(self, slot: int) -> Path:
        return self.SAVES_DIR / f"slot_{slot}.json"

    def save(self, slot: int, data: SaveData) -> str:
        if slot < 1 or slot > MAX_SLOTS:
            raise ValueError(f"Slot must be 1-{MAX_SLOTS}, got {slot}")
        data.slot_id = slot
        path = self._slot_path(slot)
        fd, tmp = tempfile.mkstemp(dir=str(self.SAVES_DIR), suffix=".tmp")
        try:
            try:
                f = os.fdopen(fd, "wb")
            except Exception:
                os.close(fd)
                os.unlink(tmp)
                raise
            with f:
                f.write(data.to_json())
                # Flush to the OS *and* to the platter before the rename.
                # os.replace is atomic w.r.t. the directory entry, but without
                # the fsync a power loss can leave the new entry pointing at
                # unwritten (zero-filled) blocks — i.e. the atomic rename
                # atomically installs a corrupt save over a good one.
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, str(path))
        except Exception:
            if os.path.exists(tmp):
                os.unlink(tmp)
            raise
        logger.info("SaveManager: saved slot %d -> %s", slot, path)
        return str(path)

    def load(self, slot: int) -> SaveData | None:
        if slot < 1 or slot > MAX_SLOTS:
            return None
        path = self._slot_path(slot)
        if not path.exists():
            return None
        try:
            raw = path.read_bytes()
            return SaveData.from_json(raw)
        except (orjson.JSONEncodeError, OSError, KeyError, ValueError) as e:
            logger.warning("SaveManager: corrupt save slot %d: %s", slot, e)
            return None

    def delete(self, slot: int) -> None:
        if slot < 1 or slot > MAX_SLOTS:
            return
        path = self._slot_path(slot)
        if path.exists():
            path.unlink()
            logger.info("SaveManager: deleted slot %d", slot)

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
        """Update the progress fields of the newest save, preserving the rest.

        AUD-005: this used to construct a brand-new ``SaveData`` from only the
        six arguments below and write it over the newest slot. Every field the
        arguments did not cover — ``completed_stages``, ``zone_flags`` — was
        silently reset to its default. Because ``SceneManager._on_stage_complete``
        appends to ``completed_stages``, saves, and *then* calls ``auto_save``
        on the same slot, the freshly recorded stage completion was erased
        microseconds after it was written. Players could never accumulate
        completed stages.

        The fix is read-modify-write: load whatever is already in the slot and
        mutate only the fields autosave actually owns.
        """
        slot = self.newest_slot()
        if slot is None:
            slot = 1

        data = self.load(slot)
        if data is None:
            data = SaveData(slot_id=slot)

        data.slot_id = slot
        # Timezone-aware and lexicographically sortable, so newest_slot()'s
        # string comparison stays correct across DST changes (AUD-014).
        data.timestamp = datetime.now(timezone.utc).isoformat()
        data.stage_id = stage_id
        data.stage_index = stage_index
        data.checkpoint_x = checkpoint_x
        data.checkpoint_y = checkpoint_y
        data.health = health
        data.max_health = max_health
        return self.save(slot, data)
