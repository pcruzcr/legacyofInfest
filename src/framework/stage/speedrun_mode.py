"""
Module: speedrun_mode
System: framework.stage
Academic Unit: N/A
Description: Speedrun mode with global timer, splits per stage, and ghost data.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import orjson

from src.engine.core import settings

_DEFAULT_SAVE_PATH: Path = settings.PROJECT_ROOT / "saves/speedrun.json"


class SpeedrunTimer:
    """Global speedrun timer with per-stage splits."""

    def __init__(self) -> None:
        self._global_time: float = 0.0
        self._running: bool = False
        self._splits: list[dict[str, Any]] = []
        self._current_stage: str = ""

    def start(self) -> None:
        self._global_time = 0.0
        self._running = True
        self._splits = []

    def stop(self) -> None:
        self._running = False

    def reset(self) -> None:
        self._global_time = 0.0
        self._running = False
        self._splits = []
        self._current_stage = ""

    def update(self, dt: float) -> None:
        if self._running:
            self._global_time += dt

    def start_stage(self, stage_id: str) -> None:
        self._current_stage = stage_id

    def split(self, stage_id: str) -> None:
        self._splits.append({
            "stage_id": stage_id,
            "time": self._global_time,
        })

    def get_formatted_time(self, t: float | None = None) -> str:
        total_seconds = int(t if t is not None else self._global_time)
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def get_splits(self) -> list[dict[str, Any]]:
        return list(self._splits)

    def save(self, path: str | Path | None = None) -> None:
        data = {
            "global_time": self._global_time,
            "splits": self._splits,
        }
        path = Path(path) if path is not None else _DEFAULT_SAVE_PATH
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(orjson.dumps(data, option=orjson.OPT_INDENT_2))

    def load(self, path: str | Path | None = None) -> None:
        try:
            data = orjson.loads(Path(path).read_bytes() if path is not None else _DEFAULT_SAVE_PATH.read_bytes())
            self._global_time = data.get("global_time", 0.0)
            self._splits = data.get("splits", [])
        except (FileNotFoundError, orjson.JSONDecodeError):
            pass

    @property
    def global_time(self) -> float:
        return self._global_time

    @property
    def running(self) -> bool:
        return self._running


class GhostData:
    """Records player position over time for ghost replay."""

    def __init__(self) -> None:
        self._frames: list[dict[str, float]] = []

    def record(self, x: float, y: float, state: str) -> None:
        self._frames.append({"x": x, "y": y, "state": state})

    def get_frame(self, index: int) -> dict[str, float] | None:
        if 0 <= index < len(self._frames):
            return self._frames[index]
        return None

    def clear(self) -> None:
        self._frames.clear()

    def save(self, path: str | Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(orjson.dumps(self._frames, option=orjson.OPT_INDENT_2))

    def load(self, path: str | Path) -> None:
        try:
            self._frames = orjson.loads(Path(path).read_bytes())
        except (FileNotFoundError, orjson.JSONDecodeError):
            pass

    @property
    def frame_count(self) -> int:
        return len(self._frames)