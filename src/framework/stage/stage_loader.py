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
from dataclasses import dataclass, field
from pathlib import Path

import pygame
import pyscroll
import pyscroll.data
from pytmx.util_pygame import load_pygame

from src.engine.core import settings
from src.framework import FrameworkUsageError
from src.framework.entities.base_entity import BaseEntity


@dataclass
class StageData:
    """Complete stage data structure returned by StageLoader.load()."""
    map_layer: pyscroll.PyscrollGroup
    collision_rects: list[pygame.Rect] = field(default_factory=list)
    entity_list: list[BaseEntity] = field(default_factory=list)
    checkpoints: list = field(default_factory=list)
    spawn_point: pygame.Vector2 = field(default_factory=lambda: pygame.Vector2(0, 0))
    next_trigger: pygame.Rect | None = None
    background_layers: list[pygame.Surface] = field(default_factory=list)
    stage_id: str = ""
    stage_name: str = ""
    time_limit: int = 0
    bgm_track: str = ""


REQUIRED_LAYERS: tuple[str, ...] = (
    "BG_Far", "BG_Mid", "BG_Near", "Terrain",
    "Terrain_Detail", "Objects", "Collision", "FG_Overlay",
)


class StageLoader:
    """Loads TMX files and produces StageData with all entities spawned."""

    _entity_registry: dict[str, type[BaseEntity]] = {}

    @classmethod
    def register_entity(cls, type_name: str, entity_class: type[BaseEntity]) -> None:
        """Register an entity class for spawning from TMX objects."""
        cls._entity_registry[type_name] = entity_class

    @classmethod
    def load(cls, tmx_path: Path) -> StageData:
        """
        Load a TMX file and return a fully assembled StageData instance.
        Raises FrameworkUsageError on missing required layers or PlayerSpawn.
        """
        tmx_path = Path(tmx_path)
        if not tmx_path.exists():
            raise FrameworkUsageError(f"TMX file not found: {tmx_path}")

        tmx_data = load_pygame(str(tmx_path))

        # Validate required layers
        tmx_layer_names = {l.name for l in tmx_data.visible_layers}
        tmx_layer_names.update({l.name for l in tmx_data.layers})
        for name in REQUIRED_LAYERS:
            if name not in tmx_layer_names:
                raise FrameworkUsageError(f"Missing required layer: {name}")

        # Read map custom properties
        stage_id = tmx_data.properties.get("stage_id", "")
        stage_name = tmx_data.properties.get("stage_name", "")
        time_limit = int(tmx_data.properties.get("time_limit", 0))
        bgm_track = tmx_data.properties.get("bgm_track", "")

        # Build pyscroll
        map_data = pyscroll.data.TiledMapData(tmx_data)
        renderer = pyscroll.BufferedRenderer(
            map_data,
            (settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT),
            clamp_camera=True,
        )
        group = pyscroll.PyscrollGroup(map_layer=renderer, default_layer=4)

        stage = StageData(
            map_layer=group,
            stage_id=stage_id,
            stage_name=stage_name,
            time_limit=time_limit,
            bgm_track=bgm_track,
        )

        # Parse objects layer
        player_spawn_found = False
        for obj in tmx_data.get_layer_by_name("Objects"):
            obj_type = getattr(obj, "type", None) or ""
            obj_name = getattr(obj, "name", "") or ""

            if obj_type == "PlayerSpawn":
                if player_spawn_found:
                    raise FrameworkUsageError("More than one PlayerSpawn object found")
                stage.spawn_point = pygame.Vector2(obj.x, obj.y)
                player_spawn_found = True

            elif obj_type in cls._entity_registry:
                props = dict(obj.properties) if obj.properties else {}
                entity_class = cls._entity_registry[obj_type]
                entity = entity_class(pygame.Vector2(obj.x, obj.y), **props)
                stage.entity_list.append(entity)

            elif obj_type == "Checkpoint":
                props = dict(obj.properties) if obj.properties else {}
                if "checkpoint_id" not in props:
                    raise FrameworkUsageError("Checkpoint missing required property: checkpoint_id")
                rect = pygame.Rect(obj.x, obj.y, obj.width or 24, obj.height or 32)
                from src.framework.stage.checkpoint import Checkpoint
                cp = Checkpoint(pygame.Vector2(obj.x, obj.y), rect, props["checkpoint_id"])
                stage.checkpoints.append(cp)

            elif obj_type == "NextTrigger":
                stage.next_trigger = pygame.Rect(obj.x, obj.y, obj.width, obj.height)

        if not player_spawn_found:
            raise FrameworkUsageError("No PlayerSpawn found in TMX")

        # Parse collision layer
        try:
            collision_layer = tmx_data.get_layer_by_name("Collision")
            for obj in collision_layer:
                rect = pygame.Rect(obj.x, obj.y, obj.width, obj.height)
                if rect.width > 0 and rect.height > 0:
                    stage.collision_rects.append(rect)
        except ValueError:
            pass

        return stage
