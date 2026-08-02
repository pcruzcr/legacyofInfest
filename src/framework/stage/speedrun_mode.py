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
    """La grabación de una carrera: dónde estaba el jugador en cada fotograma.

    AUD-142 — estaba escrita entera y **no la usaba nadie**.

    Tenía `record`, `get_frame`, `save`, `load`, `clear` y `frame_count`, todo
    correcto, y cero llamadas en el proyecto: ni se grababa ni se reproducía.
    Es el mismo patrón que el sistema de diálogo (AUD-127) y el de escenas
    (AUD-136): la pieza estaba, faltaba quien la usara.

    Ahora `StageScene` graba mientras se juega y dibuja la carrera anterior.
    El fantasma es la forma más barata que existe de hacer que repetir un
    nivel tenga sentido: no hace falta un adversario, basta con quien fuiste.

    Grabación a intervalo fijo
    --------------------------
    Se graba cada `INTERVALO` segundos y no cada fotograma. A 60 fps, un nivel
    de tres minutos serían 10.800 puntos —un fichero de medio mega para dibujar
    un muñeco— y la diferencia no se ve: a 30 muestras por segundo el fantasma
    se mueve igual de fluido para el ojo, y el fichero baja a la mitad.
    """

    #: Segundos entre muestras. 1/30 basta: el ojo no distingue más.
    INTERVALO: float = 1.0 / 30.0

    def __init__(self) -> None:
        self._frames: list[dict[str, float]] = []
        self._t: float = 0.0
        self._desde_ultima: float = 0.0

    def grabar_si_toca(self, dt: float, x: float, y: float,
                       state: str = "") -> bool:
        """Graba una muestra si ha pasado el intervalo. Devuelve si grabó."""
        self._t += dt
        self._desde_ultima += dt
        if self._desde_ultima < self.INTERVALO:
            return False
        self._desde_ultima = 0.0
        self.record(x, y, state)
        return True

    def posicion_en(self, segundos: float) -> tuple[float, float] | None:
        """Dónde estaba el fantasma en ese instante de SU carrera.

        Devuelve `None` cuando la carrera grabada ya terminó, que es la señal
        de que el jugador va por detrás de su propio récord — y es justo la
        información que hace útil a un fantasma.
        """
        if not self._frames:
            return None
        indice = int(segundos / self.INTERVALO)
        if indice >= len(self._frames):
            return None
        marco = self._frames[max(0, indice)]
        return float(marco.get("x", 0.0)), float(marco.get("y", 0.0))

    @property
    def duracion(self) -> float:
        return len(self._frames) * self.INTERVALO

    def record(self, x: float, y: float, state: str) -> None:
        self._frames.append({"x": x, "y": y, "state": state})

    def get_frame(self, index: int) -> dict[str, float] | None:
        if 0 <= index < len(self._frames):
            return self._frames[index]
        return None

    def clear(self) -> None:
        self._frames.clear()
        self._t = 0.0
        self._desde_ultima = 0.0

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