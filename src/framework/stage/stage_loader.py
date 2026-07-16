"""
Module: stage_loader
System: framework.stage
Academic Unit: Unit II (Collision Detection), Unit IV (Game Architecture)
Description: Parses TMX map files using pytmx and pyscroll to assemble
a complete stage environment: tile layers, entity spawn points, collision
zones, checkpoints, and the next-trigger portal.
"""
from __future__ import annotations
from typing import Any

import logging
from dataclasses import dataclass, field
from pathlib import Path

import pygame
import pyscroll
import pyscroll.data
from pytmx.util_pygame import load_pygame

from typing import TYPE_CHECKING

from src.engine.core import settings
from src.engine.utils.asset_loader import AssetLoader
from src.framework import FrameworkUsageError
from src.framework.entities.base_entity import BaseEntity

if TYPE_CHECKING:
    from src.framework.stage.checkpoint import Checkpoint


@dataclass
class MessageTrigger:
    """Tutorial message triggered when player enters a zone."""
    rect: pygame.Rect
    text: str
    triggered: bool = False


@dataclass
class HazardZone:
    """Area that deals damage to the player periodically."""
    rect: pygame.Rect
    damage: float = 0.25
    cooldown: float = 0.5
    timer: float = 0.0


@dataclass
class DeathPit:
    """Instant-death zone (bypasses damage)."""
    rect: pygame.Rect


@dataclass
class CameraLock:
    """Restrict camera movement during certain sections."""
    rect: pygame.Rect
    lock_x: bool = False
    lock_y: bool = False


@dataclass
class StageData:
    """Complete stage data structure returned by StageLoader.load()."""
    map_layer: pyscroll.PyscrollGroup
    map_pixel_size: tuple[int, int] = (0, 0)
    collision_rects: list[pygame.Rect] = field(default_factory=list)
    one_way_rects: list[pygame.Rect] = field(default_factory=list)
    entity_list: list[BaseEntity] = field(default_factory=list)
    checkpoints: list[Checkpoint] = field(default_factory=list)
    spawn_point: pygame.Vector2 = field(default_factory=lambda: pygame.Vector2(0, 0))
    next_trigger: pygame.Rect | None = None
    background_layers: list[pygame.Surface] = field(default_factory=list)
    message_triggers: list[MessageTrigger] = field(default_factory=list)
    hazard_zones: list[HazardZone] = field(default_factory=list)
    death_pits: list[DeathPit] = field(default_factory=list)
    camera_locks: list[CameraLock] = field(default_factory=list)
    stage_id: str = ""
    stage_name: str = ""
    time_limit: int = 0
    bgm_track: str = ""
    gravity_multiplier: float = 1.0
    climate: str = ""


REQUIRED_LAYERS: tuple[str, ...] = (
    "BG_Far", "BG_Mid", "BG_Near", "Terrain",
    "Terrain_Detail", "Objects", "Collision", "FG_Overlay",
)


class StageLoader:
    """Loads TMX files and produces StageData with all entities spawned."""

    _entity_registry: dict[str, type[BaseEntity]] = {}

    @classmethod
    def register_entity(cls, type_name: str, entity_class: type[BaseEntity]) -> None:
        cls._entity_registry[type_name] = entity_class

    @classmethod
    def load(cls, tmx_path: Path) -> StageData:
        tmx_path = Path(tmx_path)
        if not tmx_path.exists():
            raise FrameworkUsageError(f"TMX file not found: {tmx_path}")

        tmx_data = load_pygame(str(tmx_path.resolve()))

        tmx_layer_names = {layer.name for layer in tmx_data.visible_layers}
        tmx_layer_names.update({layer.name for layer in tmx_data.layers})
        for name in REQUIRED_LAYERS:
            if name not in tmx_layer_names:
                raise FrameworkUsageError(f"Missing required layer: {name}")

        stage_id = tmx_data.properties.get("stage_id", "")
        stage_name = tmx_data.properties.get("stage_name", "")
        try:
            time_limit = int(tmx_data.properties.get("time_limit", 0))
        except ValueError:
            logging.warning("StageLoader: invalid time_limit value, using 0")
            time_limit = 0
        bgm_track = tmx_data.properties.get("bgm_track", "")
        background_zone = tmx_data.properties.get("background_zone", "")
        try:
            gravity_multiplier = float(tmx_data.properties.get("gravity_multiplier", 1.0))
        except ValueError:
            logging.warning("StageLoader: invalid gravity_multiplier value, using 1.0")
            gravity_multiplier = 1.0
        climate = tmx_data.properties.get("climate", "")

        map_data = pyscroll.data.TiledMapData(tmx_data)
        renderer = pyscroll.BufferedRenderer(
            map_data,
            (settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT),
            clamp_camera=True,
        )
        group = pyscroll.PyscrollGroup(map_layer=renderer, default_layer=4)

        map_w = tmx_data.width * tmx_data.tilewidth
        map_h = tmx_data.height * tmx_data.tileheight

        stage = StageData(
            map_layer=group,
            map_pixel_size=(map_w, map_h),
            stage_id=stage_id,
            stage_name=stage_name,
            time_limit=time_limit,
            bgm_track=bgm_track,
            gravity_multiplier=gravity_multiplier,
            climate=climate,
        )

        # Load parallax background images if zone is specified
        if background_zone:
            bg_dir = settings.ASSETS_DIR / "backgrounds" / background_zone
            if bg_dir.is_dir():
                for bg_name in ("far", "mid", "near"):
                    bg_path = bg_dir / f"bg_{background_zone}_{bg_name}.png"
                    try:
                        bg_surf = AssetLoader.load_image(
                            bg_path, size=(settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT),
                        )
                        stage.background_layers.append(bg_surf)
                    except (pygame.error, FileNotFoundError, PermissionError):
                        logging.warning("StageLoader: missing bg %s", bg_path)
                # Also try direct zone name (non-nested)
            else:
                for bg_name in ("far", "mid", "near"):
                    bg_path = settings.ASSETS_DIR / "backgrounds" / f"bg_{background_zone}_{bg_name}.png"
                    try:
                        bg_surf = AssetLoader.load_image(
                            bg_path, size=(settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT),
                        )
                        stage.background_layers.append(bg_surf)
                    except (pygame.error, FileNotFoundError, PermissionError):
                        logging.warning("StageLoader: missing bg %s", bg_path)

        # First pass: collect Waypoint objects grouped by owner name
        waypoints_by_owner: dict[str, list[tuple[float, float]]] = {}
        for obj in tmx_data.get_layer_by_name("Objects"):
            obj_type = getattr(obj, "type", None) or ""
            if obj_type == "Waypoint":
                props = dict(obj.properties) if obj.properties else {}
                owner_id = props.get("owner_id", "")
                if owner_id:
                    waypoints_by_owner.setdefault(owner_id, []).append((float(obj.x), float(obj.y)))

        player_spawn_found = False
        for obj in tmx_data.get_layer_by_name("Objects"):
            obj_type = getattr(obj, "type", None) or ""
            obj_name = getattr(obj, "name", "") or ""
            props = dict(obj.properties) if obj.properties else {}

            if obj_type == "PlayerSpawn":
                if player_spawn_found:
                    raise FrameworkUsageError("More than one PlayerSpawn object found")
                # TMX Y is the player's FEET position (§6.1); convert to top-left
                stage.spawn_point = pygame.Vector2(obj.x, obj.y - 32)
                player_spawn_found = True

            elif obj_type == "MessageTrigger":
                rect = pygame.Rect(obj.x, obj.y, obj.width or 32, obj.height or 32)
                text = props.get("text", "")
                stage.message_triggers.append(MessageTrigger(rect=rect, text=text))

            elif obj_type == "MessageTrigger_Once":
                rect = pygame.Rect(obj.x, obj.y, obj.width or 32, obj.height or 32)
                text = props.get("text", "")
                stage.message_triggers.append(MessageTrigger(rect=rect, text=text))

            elif obj_type in cls._entity_registry:
                entity_class = cls._entity_registry[obj_type]
                # Convert TMX string props to expected types
                cleaned: dict[str, Any] = {}
                for k, v in props.items():
                    if k in ("zone",):
                        try:
                            cleaned[k] = int(v)
                        except (ValueError, TypeError):
                            logging.warning("StageLoader: invalid zone value '%s', using 0", v)
                            cleaned[k] = 0
                    elif k in ("max_health", "damage_on_contact", "patrol_length",
                               "fire_rate", "projectile_speed", "projectile_damage",
                               "sine_amplitude", "sine_frequency", "flight_speed",
                               "patrol_speed", "alert_speed", "contact_knockback",
                               "detection_range_x", "detection_range_y",
                               "charge_speed"):
                        try:
                            cleaned[k] = float(v)
                        except (ValueError, TypeError):
                            logging.warning("StageLoader: invalid %s value '%s', using 0", k, v)
                            cleaned[k] = 0.0
                    else:
                        cleaned[k] = v
                # Inject waypoints if defined in the TMX
                if obj_name and obj_name in waypoints_by_owner:
                    cleaned["waypoints"] = waypoints_by_owner[obj_name]
                entity = entity_class(pygame.Vector2(obj.x, obj.y), **cleaned)
                stage.entity_list.append(entity)

            elif obj_type == "Checkpoint":
                if "checkpoint_id" not in props:
                    raise FrameworkUsageError("Checkpoint missing required property: checkpoint_id")
                rect = pygame.Rect(obj.x, obj.y, obj.width or 24, obj.height or 32)
                from src.framework.stage.checkpoint import Checkpoint
                cp = Checkpoint(pygame.Vector2(obj.x, obj.y), rect, int(props["checkpoint_id"]))
                stage.checkpoints.append(cp)

            elif obj_type == "NextTrigger":
                stage.next_trigger = pygame.Rect(obj.x, obj.y, obj.width, obj.height)

            elif obj_type == "HazardZone":
                rect = pygame.Rect(obj.x, obj.y, obj.width, obj.height)
                try:
                    damage = float(props.get("damage", 0.25))
                except (ValueError, TypeError):
                    logging.warning("StageLoader: invalid HazardZone damage, using 0.25")
                    damage = 0.25
                stage.hazard_zones.append(HazardZone(rect=rect, damage=damage))

            elif obj_type == "DeathPit":
                stage.death_pits.append(DeathPit(rect=pygame.Rect(obj.x, obj.y, obj.width, obj.height)))

            elif obj_type == "CameraLock":
                rect = pygame.Rect(obj.x, obj.y, obj.width, obj.height)
                lock_x = props.get("lock_x", False) in (True, "true", "True", 1, "1")
                lock_y = props.get("lock_y", False) in (True, "true", "True", 1, "1")
                stage.camera_locks.append(CameraLock(rect=rect, lock_x=lock_x, lock_y=lock_y))

        if not player_spawn_found:
            raise FrameworkUsageError("No PlayerSpawn found in TMX")

        try:
            collision_layer = tmx_data.get_layer_by_name("Collision")
            for obj in collision_layer:
                rect = pygame.Rect(obj.x, obj.y, obj.width, obj.height)
                if rect.width > 0 and rect.height > 0:
                    obj_type = getattr(obj, "type", None) or ""
                    if obj_type == "Platform":
                        stage.one_way_rects.append(rect)
                    else:
                        stage.collision_rects.append(rect)
        except ValueError:
            logging.warning("StageLoader: Collision layer not found")

        return stage
