from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


SAVE_VERSION = 2
MAX_SLOTS = 5


@dataclass
class SaveData:
    slot_id: int = 0
    timestamp: str = ""
    version: int = SAVE_VERSION

    stage_id: str = ""
    stage_index: int = 0
    checkpoint_x: float = 0.0
    checkpoint_y: float = 0.0

    health: float = 5.0
    max_health: float = 5.0

    zone_flags: dict[str, bool] = field(default_factory=dict)
    completed_stages: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "slot_id": self.slot_id,
            "timestamp": self.timestamp or datetime.now().isoformat(),
            "version": self.version,
            "stage_id": self.stage_id,
            "stage_index": self.stage_index,
            "checkpoint_x": round(self.checkpoint_x, 1),
            "checkpoint_y": round(self.checkpoint_y, 1),
            "health": round(self.health, 1),
            "max_health": round(self.max_health, 1),
            "zone_flags": dict(self.zone_flags),
            "completed_stages": list(self.completed_stages),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SaveData:
        return cls(
            slot_id=data.get("slot_id", 0),
            timestamp=data.get("timestamp", ""),
            version=data.get("version", SAVE_VERSION),
            stage_id=data.get("stage_id", ""),
            stage_index=data.get("stage_index", 0),
            checkpoint_x=float(data.get("checkpoint_x", 0.0)),
            checkpoint_y=float(data.get("checkpoint_y", 0.0)),
            health=float(data.get("health", 5.0)),
            max_health=float(data.get("max_health", 5.0)),
            zone_flags=data.get("zone_flags", {}),
            completed_stages=data.get("completed_stages", []),
        )

    @staticmethod
    def migrate(data: dict[str, Any]) -> dict[str, Any]:
        ver = data.get("version", 0)
        if ver < 1:
            data.setdefault("zone_flags", {})
            data["version"] = 1
        if ver < 2:
            data.setdefault("completed_stages", [])
            data["version"] = 2
        return data
