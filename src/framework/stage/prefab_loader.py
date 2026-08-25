"""
Module: prefab_loader
System: framework.stage
Academic Unit: Unit IV (Level Design)
Description: Loads room prefab JSON files and applies them to the current stage.
AUD-636 — Prefab system for room templates.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import pygame

from src.engine.core import settings
from src.framework.stage.stage_data import StageData
from src.framework.stage.interactables import (
    Recogible,
    Cerradura,
    Cofre,
    Disparador,
    ZonaDeWarp,
    ZonaDeWarp,
    SecretExit,
    SecretRoom,
)
from src.framework.stage.bloques import BloqueEmpujable, BloqueDestructible
from src.framework.stage.hazard import HazardZone
from src.framework.entities import entity_factory

logger = logging.getLogger(__name__)

PREFAB_DIR = settings.ASSETS_DIR / "prefabs" / "rooms"

# Tipo -> handler de creación
_PREFAB_HANDLERS: dict[str, Any] = {}


def registrar_prefab(tipo: str):
    """Decorador para registrar handlers de prefab."""
    def decorator(fn):
        _PREFAB_HANDLERS[tipo] = fn
        return fn
    return decorator


def cargar_prefab(nombre: str) -> dict[str, Any] | None:
    """Carga un prefab JSON desde assets/prefabs/rooms/."""
    ruta = PREFAB_DIR / f"{nombre}.json"
    if not ruta.exists():
        logger.warning("Prefab no encontrado: %s", ruta)
        return None
    try:
        return json.loads(ruta.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        logger.error("Error cargando prefab %s: %s", nombre, e)
        return None


@registrar_prefab("PlayerSpawn")
def _spawn_player(prefab: dict[str, Any], stage: StageData, props: dict[str, Any]) -> None:
    stage.spawn_point = pygame.Vector2(prefab.get("x", 0), prefab.get("y", 0) - 32)


@registrar_prefab("Checkpoint")
def _spawn_checkpoint(prefab: dict[str, Any], stage: StageData, props: dict[str, Any]) -> None:
    from src.framework.stage.checkpoint import Checkpoint
    checkpoint_id = int(props.get("checkpoint_id", 0))
    rect = pygame.Rect(prefab.get("x", 0), prefab.get("y", 0),
                       prefab.get("width", 16), prefab.get("height", 32))
    stage.checkpoints.append(Checkpoint(pygame.Vector2(prefab.get("x", 0), prefab.get("y", 0)), rect, checkpoint_id))


@registrar_prefab("MessageTrigger")
def _spawn_message(prefab: dict[str, Any], stage: StageData, props: dict[str, Any]) -> None:
    from src.framework.stage.stage_data import MessageTrigger
    text = props.get("text", "")
    duration = float(props.get("duration", 5.0))
    rect = pygame.Rect(prefab.get("x", 0), prefab.get("y", 0),
                       prefab.get("width", 32), prefab.get("height", 32))
    stage.message_triggers.append(MessageTrigger(rect=rect, text=text, duration=duration))


@registrar_prefab("Walker")
def _spawn_walker(prefab: dict[str, Any], stage: StageData, props: dict[str, Any]) -> None:
    from src.framework.entities.enemy_walker import EnemyWalker
    pos = pygame.Vector2(prefab.get("x", 0), prefab.get("y", 0))
    cleaned = {k: v for k, v in props.items() if k not in ("x", "y", "width", "height")}
    entity = EnemyWalker(pygame.Vector2(prefab.get("x", 0), prefab.get("y", 0)), **cleaned)
    stage.entity_list.append(entity)


@registrar_prefab("Flying")
def _spawn_flying(prefab: dict[str, Any], stage: StageData, props: dict[str, Any]) -> None:
    from src.framework.entities.enemy_flying import EnemyFlying
    pos = pygame.Vector2(prefab.get("x", 0), prefab.get("y", 0))
    cleaned = {k: v for k, v in props.items() if k not in ("x", "y", "width", "height")}
    entity = EnemyFlying(pygame.Vector2(prefab.get("x", 0), prefab.get("y", 0)), **cleaned)
    stage.entity_list.append(entity)


@registrar_prefab("Shooter")
def _spawn_shooter(prefab: dict[str, Any], stage: StageData, props: dict[str, Any]) -> None:
    from src.framework.entities.enemy_shooter import EnemyShooter
    pos = pygame.Vector2(prefab.get("x", 0), prefab.get("y", 0))
    cleaned = {k: v for k, v in props.items() if k not in ("x", "y", "width", "height")}
    entity = EnemyShooter(pygame.Vector2(prefab.get("x", 0), prefab.get("y", 0)), **cleaned)
    stage.entity_list.append(entity)


def aplicar_prefab(nombre: str, stage: StageData, offset: pygame.Vector2 = pygame.Vector2(0, 0)) -> bool:
    """Aplica un prefab de sala al escenario actual.

    Args:
        nombre: nombre del archivo JSON (sin .json) en assets/prefabs/rooms/
        stage: StageData destino
        offset: desplazamiento en píxeles a aplicar a todas las posiciones

    Returns:
        True si se aplicó correctamente, False si hubo error.
    """
    data = cargar_prefab(nombre)
    if data is None:
        return False

    # Propiedades globales del mapa
    if "properties" in data:
        for key, value in data["properties"].items():
            if hasattr(stage, key):
                setattr(stage, key, value)

    # Capas de colisión y objetos
    layers = data.get("layers", {})
    objects = layers.get("Objects", [])

    for obj in objects:
        obj_type = obj.get("type", "")
        obj_props = obj.get("props", {})
        x = obj.get("x", 0) + offset.x
        y = obj.get("y", 0) + offset.y

        handler = _PREFAB_HANDLERS.get(obj.get("type", ""))
        if handler is None:
            logger.warning("Tipo de objeto desconocido en prefab: %s", obj.get("type"))
            continue

        try:
            # Crear dict de props con posición
            props = dict(obj.get("props", {}))
            handler({"type": obj.get("type", ""), "x": x, "y": obj.get("y", 0), "width": obj.get("width", 0), "height": obj.get("height", 0)}, None, props)
        except Exception as e:
            logger.error("Error aplicando objeto %s en prefab %s: %s", obj.get("type"), nombre, e)

    return True


def listar_prefabs_disponibles() -> list[str]:
    """Lista los prefabs disponibles en assets/prefabs/rooms/."""
    if not PREFAB_DIR.exists():
        return []
    return [f.stem for f in PREFAB_DIR.iterdir() if f.suffix == ".json"]


__all__ = [
    "cargar_prefab",
    "aplicar_prefab",
    "listar_prefabs_disponibles",
    "PREFAB_DIR",
]