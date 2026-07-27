"""
Module: stage_loader
System: framework.stage
Academic Unit: Unit II (Collision Detection), Unit IV (Game Architecture)
Description: Parses TMX map files using pytmx and pyscroll to assemble
a complete stage environment: tile layers, entity spawn points, collision
zones, checkpoints, and the next-trigger portal.
"""
from __future__ import annotations

import logging
import warnings
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pygame
import pyscroll
import pyscroll.data
from pytmx.util_pygame import load_pygame

from src.engine.core import settings
from src.engine.utils.asset_loader import AssetLoader
from src.framework import FrameworkUsageError
from src.framework.entities.base_entity import BaseEntity

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from src.framework.stage.checkpoint import Checkpoint


@dataclass
class MessageTrigger:
    rect: pygame.Rect
    text: str
    triggered: bool = False


@dataclass
class HazardZone:
    rect: pygame.Rect
    damage: float = 0.25
    cooldown: float = 0.5
    timer: float = 0.5


@dataclass
class DeathPit:
    rect: pygame.Rect


@dataclass
class CameraLock:
    rect: pygame.Rect
    lock_x: bool = False
    lock_y: bool = False


@dataclass
class StageData:
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
    zone: int = 0
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


_NUMERIC_PROPS: tuple[str, ...] = (
    "max_health", "damage_on_contact", "patrol_length",
    "fire_rate", "projectile_speed", "projectile_damage",
    "sine_amplitude", "sine_frequency", "flight_speed",
    "patrol_speed", "alert_speed", "contact_knockback",
    "detection_range_x", "detection_range_y", "charge_speed",
)


class StageLoader:
    _entity_registry: dict[str, type[BaseEntity]] = {}
    # (resolved path, mtime_ns, size) -> parsed pytmx map. See _parse_tmx.
    _tmx_cache: dict[tuple[str, int, int], Any] = {}

    @classmethod
    def register_entity(cls, type_name: str, entity_class: type[BaseEntity]) -> None:
        cls._entity_registry[type_name] = entity_class

    @classmethod
    def _parse_tmx(cls, tmx_path: Path) -> Any:
        """Parse a TMX file, reusing a previous parse when the file is unchanged.

        AUD-027: ``StageScene.respawn()`` calls ``on_enter()``, which called
        ``load()``, which re-parsed the entire TMX and re-decoded every tileset
        image on **every player death** — a guaranteed hitch at the worst
        possible moment for game feel.

        ``tmx_data`` is read-only map geometry; entities are constructed fresh
        from it on each load, so the parse result is safe to share. The cache is
        keyed on the file's modification time and size, so editing a map in
        Tiled and re-running still picks up the change — important, since this
        engine is used by students iterating on level design.
        """
        resolved = tmx_path.resolve()
        try:
            stat = resolved.stat()
            key = (str(resolved), stat.st_mtime_ns, stat.st_size)
        except OSError:
            key = (str(resolved), 0, 0)

        cached = cls._tmx_cache.get(key)
        if cached is not None:
            return cached

        tmx_data = load_pygame(str(resolved))
        # Only ever keep one parse in flight; stages are large and holding
        # several maps' tilesets resident is not worth the memory.
        cls._tmx_cache.clear()
        cls._tmx_cache[key] = tmx_data
        return tmx_data

    @classmethod
    def clear_tmx_cache(cls) -> None:
        """Drop the parsed-TMX cache (test teardown, or on low memory)."""
        cls._tmx_cache.clear()

    @classmethod
    def load(cls, tmx_path: Path) -> StageData:
        tmx_path = Path(tmx_path)
        if not tmx_path.exists():
            raise FrameworkUsageError(f"TMX file not found: {tmx_path}")

        tmx_data = cls._parse_tmx(tmx_path)
        cls._validate_layers(tmx_data)
        stage = cls._build_stage_data(tmx_data)

        cls._load_backgrounds(stage, tmx_data.properties.get("background_zone", ""))
        waypoints_by_owner = cls._build_waypoints(tmx_data)
        spawn_found = cls._process_objects(tmx_data, stage, waypoints_by_owner)

        if not spawn_found:
            raise FrameworkUsageError("No PlayerSpawn found in TMX")

        cls._load_collision(tmx_data, stage)
        return stage

    # ── Internal helpers ──────────────────────────────────────────

    @classmethod
    def _validate_layers(cls, tmx_data: Any) -> None:
        tmx_layer_names = {layer.name for layer in tmx_data.visible_layers}
        tmx_layer_names.update({layer.name for layer in tmx_data.layers})
        for name in REQUIRED_LAYERS:
            if name not in tmx_layer_names:
                raise FrameworkUsageError(f"Missing required layer: {name}")

    @classmethod
    def _build_stage_data(cls, tmx_data: Any) -> StageData:
        props = tmx_data.properties
        stage_id = props.get("stage_id", "")
        stage_name = props.get("stage_name", "")
        time_limit = cls._safe_int(props.get("time_limit", 0), "time_limit")
        bgm_track = props.get("bgm_track", "")
        gravity_multiplier = cls._safe_float(props.get("gravity_multiplier", 1.0), "gravity_multiplier")
        climate = props.get("climate", "")
        zone = cls._safe_int(props.get("zone", 0), "zone")

        map_data = pyscroll.data.TiledMapData(tmx_data)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            renderer = pyscroll.BufferedRenderer(
                map_data,
                (settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT),
                clamp_camera=True,
                alpha=True,
            )
        group = pyscroll.PyscrollGroup(map_layer=renderer, default_layer=4)

        map_w = tmx_data.width * tmx_data.tilewidth
        map_h = tmx_data.height * tmx_data.tileheight

        return StageData(
            map_layer=group,
            map_pixel_size=(map_w, map_h),
            stage_id=stage_id,
            stage_name=stage_name,
            time_limit=time_limit,
            bgm_track=bgm_track,
            gravity_multiplier=gravity_multiplier,
            climate=climate,
            zone=zone,
        )

    @classmethod
    def _load_backgrounds(cls, stage: StageData, background_zone: str) -> None:
        if not background_zone:
            return
        bg_dir = settings.ASSETS_DIR / "backgrounds" / background_zone
        if bg_dir.is_dir():
            for bg_name in ("far", "mid", "near"):
                bg_path = bg_dir / f"bg_{background_zone}_{bg_name}.png"
                cls._try_append_bg(stage, bg_path)
        else:
            for bg_name in ("far", "mid", "near"):
                bg_path = settings.ASSETS_DIR / "backgrounds" / f"bg_{background_zone}_{bg_name}.png"
                cls._try_append_bg(stage, bg_path)

    @classmethod
    def _try_append_bg(cls, stage: StageData, bg_path: Path) -> None:
        try:
            bg_surf = AssetLoader.load_image(
                bg_path, size=(settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT),
            )
            stage.background_layers.append(bg_surf)
        except (pygame.error, FileNotFoundError, PermissionError):
            logger.warning("StageLoader: missing bg %s", bg_path)

    @classmethod
    def _build_waypoints(cls, tmx_data: Any) -> dict[str, list[tuple[float, float]]]:
        waypoints_by_owner: dict[str, list[tuple[float, float]]] = {}
        for obj in tmx_data.get_layer_by_name("Objects"):
            obj_type = getattr(obj, "type", None) or ""
            if obj_type == "Waypoint":
                props = dict(obj.properties) if obj.properties else {}
                owner_id = props.get("owner_id", "")
                if owner_id:
                    waypoints_by_owner.setdefault(owner_id, []).append((float(obj.x), float(obj.y)))
        return waypoints_by_owner

    @classmethod
    def _process_objects(
        cls,
        tmx_data: Any,
        stage: StageData,
        waypoints_by_owner: dict[str, list[tuple[float, float]]],
    ) -> bool:
        player_spawn_found = False
        for obj in tmx_data.get_layer_by_name("Objects"):
            obj_type = getattr(obj, "type", None) or ""
            obj_name = getattr(obj, "name", "") or ""
            props = dict(obj.properties) if obj.properties else {}

            if obj_type == "PlayerSpawn":
                if player_spawn_found:
                    raise FrameworkUsageError("More than one PlayerSpawn object found")
                cls._handle_player_spawn(stage, obj)
                player_spawn_found = True

            elif obj_type == "MessageTrigger":
                cls._handle_message_trigger(stage, obj, props)

            elif obj_type == "MessageTrigger_Once":
                cls._handle_message_trigger(stage, obj, props)

            elif obj_type in cls._entity_registry:
                cls._handle_entity_spawn(stage, obj, obj_name, props, waypoints_by_owner)

            elif obj_type == "Checkpoint":
                cls._handle_checkpoint(stage, obj, props)

            elif obj_type == "NextTrigger":
                if obj.width > 0 and obj.height > 0:
                    stage.next_trigger = pygame.Rect(obj.x, obj.y, obj.width, obj.height)

            elif obj_type == "HazardZone":
                cls._handle_hazard_zone(stage, obj, props)

            elif obj_type == "DeathPit":
                if obj.width > 0 and obj.height > 0:
                    stage.death_pits.append(DeathPit(rect=pygame.Rect(obj.x, obj.y, obj.width, obj.height)))

            elif obj_type == "CameraLock":
                cls._handle_camera_lock(stage, obj, props)
        return player_spawn_found

    @classmethod
    def _handle_player_spawn(cls, stage: StageData, obj: Any) -> None:
        stage.spawn_point = pygame.Vector2(obj.x, obj.y - 32)

    @classmethod
    def _handle_message_trigger(cls, stage: StageData, obj: Any, props: dict[str, Any]) -> None:
        rect = pygame.Rect(obj.x, obj.y, obj.width or 32, obj.height or 32)
        text = props.get("text", "")
        stage.message_triggers.append(MessageTrigger(rect=rect, text=text))

    @classmethod
    def _handle_entity_spawn(
        cls,
        stage: StageData,
        obj: Any,
        obj_name: str,
        props: dict[str, Any],
        waypoints_by_owner: dict[str, list[tuple[float, float]]],
    ) -> None:
        obj_type = getattr(obj, "type", None) or ""
        entity_class = cls._entity_registry[obj_type]
        cleaned = cls._parse_entity_props(props)
        if obj_name and obj_name in waypoints_by_owner:
            cleaned["waypoints"] = waypoints_by_owner[obj_name]
        entity = entity_class(pygame.Vector2(obj.x, obj.y), **cleaned)
        stage.entity_list.append(entity)

    @classmethod
    def _parse_entity_props(cls, props: dict[str, Any]) -> dict[str, Any]:
        cleaned: dict[str, Any] = {}
        for k, v in props.items():
            if k in ("zone",):
                cleaned[k] = cls._safe_int(v, "zone")
            elif k in _NUMERIC_PROPS:
                cleaned[k] = cls._safe_float(v, k)
            else:
                cleaned[k] = v
        return cleaned

    @classmethod
    def _handle_checkpoint(cls, stage: StageData, obj: Any, props: dict[str, Any]) -> None:
        if "checkpoint_id" not in props:
            raise FrameworkUsageError("Checkpoint missing required property: checkpoint_id")
        rect = pygame.Rect(obj.x, obj.y, obj.width or 24, obj.height or 32)
        from src.framework.stage.checkpoint import Checkpoint
        cp = Checkpoint(pygame.Vector2(obj.x, obj.y), rect, int(props["checkpoint_id"]))
        stage.checkpoints.append(cp)

    @classmethod
    def _handle_hazard_zone(cls, stage: StageData, obj: Any, props: dict[str, Any]) -> None:
        if obj.width == 0 or obj.height == 0:
            return
        rect = pygame.Rect(obj.x, obj.y, obj.width, obj.height)
        damage = cls._safe_float(props.get("damage", 0.25), "hazard damage")
        stage.hazard_zones.append(HazardZone(rect=rect, damage=damage))

    @classmethod
    def _handle_camera_lock(cls, stage: StageData, obj: Any, props: dict[str, Any]) -> None:
        if obj.width == 0 or obj.height == 0:
            return
        rect = pygame.Rect(obj.x, obj.y, obj.width, obj.height)
        lock_x = props.get("lock_x", False) in (True, "true", "True", 1, "1")
        lock_y = props.get("lock_y", False) in (True, "true", "True", 1, "1")
        stage.camera_locks.append(CameraLock(rect=rect, lock_x=lock_x, lock_y=lock_y))

    @classmethod
    def _load_collision(cls, tmx_data: Any, stage: StageData) -> None:
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
            logger.warning("StageLoader: Collision layer not found")

    # ── Safe converters ───────────────────────────────────────────

    @classmethod
    def _safe_int(cls, value: Any, name: str) -> int:
        try:
            return int(value)
        except (ValueError, TypeError):
            logger.warning("StageLoader: invalid %s value '%s', using 0", name, value)
            return 0

    @classmethod
    def _safe_float(cls, value: Any, name: str) -> float:
        try:
            return float(value)
        except (ValueError, TypeError):
            logger.warning("StageLoader: invalid %s value '%s', using 0.0", name, value)
            return 0.0
