"""Módulo para gestionar datos de guardado del juego.

Proporciona el modelo SaveData con validación, migración
y serialización/deserialización en JSON.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import orjson
from pydantic import BaseModel, Field, field_validator, model_validator

SAVE_VERSION = 2
MAX_SLOTS = 5


class SaveData(BaseModel):
    """Modelo de datos para una partida guardada.

    Incluye validación de campos, migración automática entre
    versiones de guardado y métodos de serialización.
    """
    slot_id: int = 0
    timestamp: str = ""
    version: int = SAVE_VERSION

    stage_id: str = ""
    stage_index: int = 0
    checkpoint_x: float = 0.0
    checkpoint_y: float = 0.0

    health: float = 5.0
    max_health: float = 5.0

    zone_flags: dict[str, bool] = Field(default_factory=dict)
    completed_stages: list[str] = Field(default_factory=list)

    @field_validator("health", "max_health")
    @classmethod
    def _round_health(cls, v: float) -> float:
        return round(v, 1)

    @field_validator("checkpoint_x", "checkpoint_y")
    @classmethod
    def _round_pos(cls, v: float) -> float:
        return round(v, 1)

    @model_validator(mode="before")
    @classmethod
    def _migrate_validator(cls, data: Any) -> Any:
        """Run schema migration before field validation.

        AUD-031: this used to carry its own copy of the migration ladder,
        duplicating :meth:`migrate`. The two already differed stylistically and
        would have drifted apart the first time a version 3 was added — with
        the validator path and the explicit path silently disagreeing about
        what a migrated save looks like. There is now exactly one ladder.

        Guards against non-dict input: pydantic passes ``model_validate`` an
        arbitrary object, and ``data.get`` on a ``SaveData`` instance raised
        ``AttributeError``.
        """
        if not isinstance(data, dict):
            return data
        return cls.migrate(dict(data))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SaveData:
        """Construye una instancia desde un diccionario."""
        return cls.model_validate(data)

    def to_dict(self) -> dict[str, Any]:
        """Convierte la instancia a diccionario, asignando timestamp si está vacío.

        El timestamp generado es UTC con zona horaria, para que ``newest_slot()``
        pueda ordenar ranuras comparando cadenas sin equivocarse en los cambios
        de horario de verano (AUD-014).
        """
        data = self.model_dump()
        if not data["timestamp"]:
            data["timestamp"] = datetime.now(timezone.utc).isoformat()
        return data

    @staticmethod
    def migrate(data: dict[str, Any]) -> dict[str, Any]:
        """Migra un diccionario de datos a la versión más reciente.

        Única fuente de verdad de la migración de esquema (AUD-031): el
        validador ``_migrate_validator`` delega aquí en lugar de repetir la
        escalera de versiones.

        Para añadir la versión N: añade un bloque ``if ver < N`` que rellene
        los campos nuevos y fije ``data["version"] = N``.
        """
        ver = data.get("version", 0)
        if ver < 1:
            data.setdefault("zone_flags", {})
            data["version"] = 1
        if ver < 2:
            data.setdefault("completed_stages", [])
            data["version"] = 2
        return data

    def to_json(self) -> bytes:
        """Serializa los datos a JSON binario."""
        return orjson.dumps(self.to_dict())

    @classmethod
    def from_json(cls, raw: bytes | str) -> SaveData:
        """Deserializa datos desde JSON (bytes o string)."""
        if isinstance(raw, str):
            raw = raw.encode("utf-8")
        data = orjson.loads(raw)
        return cls.from_dict(data)
