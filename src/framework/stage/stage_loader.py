"""
Module: stage_loader
System: framework/stage
Academic Unit: Stage system
Description: StageLoader parses TMX files into StageData dataclasses.
Supports entity factory registration so stages can be extended with
custom entity types without modifying the loader.
Implements the contract from 22_API_CONTRACTS.md §11.3 and
06_TMX_SPEC.md §3–6.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Type

import pygame

from src.framework.entities.base_entity import BaseEntity
from src.framework.stage.checkpoint import Checkpoint

if TYPE_CHECKING:
    pass


# ── Data class ──────────────────────────────────────────────────────────


@dataclass
class StageData:
    """Complete parsed stage data ready for the stage scene to consume.

    All positions/rects are in world-space (TMX pixel coordinates).
    """

    map_layer: Any
    collision_rects: list[pygame.Rect] = field(default_factory=list)
    entity_list: list[BaseEntity] = field(default_factory=list)
    checkpoints: list[Checkpoint] = field(default_factory=list)
    spawn_point: pygame.Vector2 = field(
        default_factory=lambda: pygame.Vector2(0, 0)
    )
    next_trigger: pygame.Rect | None = None
    background_layers: list[pygame.Surface] = field(default_factory=list)
    stage_id: str = ""
    stage_name: str = ""
    time_limit: int = 0
    bgm_track: str = ""


# ── Exception ───────────────────────────────────────────────────────────


class FrameworkUsageError(Exception):
    """Raised when student/stage code misuses the framework API.

    Examples: missing required TMX layer, missing PlayerSpawn,
    duplicate PlayerSpawn objects.
    """


# ── Loader ──────────────────────────────────────────────────────────────


class StageLoader:
    """Parses TMX files into StageData.

    Usage::

        # Before loading any TMX, register the entity types you need:
        StageLoader.register_entity("Walker", EnemyWalker)
        StageLoader.register_entity("Flying", EnemyFlying)
        StageLoader.register_entity("Shooter", EnemyShooter)
        StageLoader.register_entity("Checkpoint", Checkpoint)

        # Load a stage:
        data = StageLoader.load(Path("src/stages/stage0/stage0.tmx"))
    """

    _entity_registry: dict[str, Type[BaseEntity]] = {}

    # ── Registration ───────────────────────────────────────────────

    @classmethod
    def register_entity(
        cls, type_name: str, entity_class: Type[BaseEntity]
    ) -> None:
        """Register an entity class for a TMX object type name.

        Args:
            type_name: The ``type`` attribute used in Tiled objects
                       (e.g. ``"Walker"``, ``"Flying"``).
            entity_class: The concrete entity class to instantiate.
        """
        cls._entity_registry[type_name] = entity_class

    # ── Main load ───────────────────────────────────────────────────

    @classmethod
    def load(cls, tmx_path: Path) -> StageData:
        """Parse a TMX file and return a fully populated StageData.

        Args:
            tmx_path: Path to the ``.tmx`` file.

        Returns:
            A :class:`StageData` instance with all parsed data.

        Raises:
            FrameworkUsageError: If a required layer is missing or
                                 the ``PlayerSpawn`` object is absent
                                 or duplicated.
        """
        import pytmx
        from pyscroll import BufferedRenderer, PyscrollGroup, data
        from src.engine.core.settings import INTERNAL_HEIGHT, INTERNAL_WIDTH

        if not tmx_path.exists():
            raise FrameworkUsageError(
                f"TMX file not found: {tmx_path}"
            )

        tmx: pytmx.TiledMap = pytmx.load_pygame(str(tmx_path))

        # 1. Validate required layers (06_TMX_SPEC.md §3.1)
        required_layers: list[str] = [
            "BG_Far",
            "BG_Mid",
            "BG_Near",
            "Terrain",
            "Terrain_Detail",
            "Objects",
            "Collision",
            "FG_Overlay",
        ]
        for layer_name in required_layers:
            try:
                layer = tmx.get_layer_by_name(layer_name)
            except ValueError:
                layer = None
            if layer is None:
                raise FrameworkUsageError(
                    f"Required TMX layer '{layer_name}' "
                    f"missing from {tmx_path.name}. "
                    "All §3.1 layers must be present."
                )

        # 2. Extract map-level properties
        stage_id: str = cls._get_str_prop(tmx, "stage_id", "")
        stage_name: str = cls._get_str_prop(tmx, "stage_name", "")
        time_limit: int = cls._get_int_prop(tmx, "time_limit", 0)
        bgm_track: str = cls._get_str_prop(tmx, "bgm_track", "")

        # 3. Build pyscroll render pipeline from tile layers
        map_data = data.TiledMapData(tmx)
        renderer = BufferedRenderer(
            map_data,
            size=(INTERNAL_WIDTH, INTERNAL_HEIGHT),
            clamp_camera=True,
        )
        map_layer = PyscrollGroup(renderer, default_layer=4)

        # 4. Parse Objects layer
        objects_layer = tmx.get_layer_by_name("Objects")
        spawn_point: pygame.Vector2 = pygame.Vector2(0, 0)
        next_trigger: pygame.Rect | None = None
        entity_list: list[BaseEntity] = []
        checkpoints: list[Checkpoint] = []

        player_spawn_count: int = 0

        for obj in objects_layer:
            obj_type: str = obj.type or ""
            obj_name: str = obj.name or ""
            obj_x: float = obj.x
            obj_y: float = obj.y
            obj_w: float = getattr(obj, "width", 0) or 0
            obj_h: float = getattr(obj, "height", 0) or 0

            if obj_type == "PlayerSpawn":
                player_spawn_count += 1
                if player_spawn_count > 1:
                    raise FrameworkUsageError(
                        f"Duplicate PlayerSpawn in {tmx_path.name}: "
                        f"'{obj_name}'. Exactly one required."
                    )
                spawn_point = pygame.Vector2(obj_x, obj_y)

            elif obj_type == "NextTrigger":
                next_trigger = pygame.Rect(obj_x, obj_y, obj_w, obj_h)

            elif obj_type == "Checkpoint":
                props = obj.properties
                cp_id_val = props.get("checkpoint_id")
                if cp_id_val is None:
                    raise FrameworkUsageError(
                        f"Checkpoint '{obj_name}' missing "
                        "'checkpoint_id' property."
                    )
                cp_rect = pygame.Rect(obj_x, obj_y, obj_w, obj_h)
                cp = Checkpoint(
                    position=pygame.Vector2(obj_x, obj_y),
                    rect=cp_rect,
                    checkpoint_id=int(cp_id_val),
                )
                checkpoints.append(cp)

            elif obj_type in cls._entity_registry:
                entity_cls = cls._entity_registry[obj_type]
                props = obj.properties
                entity = cls._build_entity(
                    entity_cls, obj_x, obj_y, props
                )
                entity_list.append(entity)

        if player_spawn_count == 0:
            raise FrameworkUsageError(
                f"No PlayerSpawn in {tmx_path.name}. "
                "Exactly one PlayerSpawn object is required."
            )

        # 5. Parse Collision layer
        collision_layer = tmx.get_layer_by_name("Collision")
        collision_rects: list[pygame.Rect] = []
        for obj in collision_layer:
            cx = obj.x
            cy = obj.y
            cw = getattr(obj, "width", 0) or 0
            ch = getattr(obj, "height", 0) or 0
            if cw > 0 and ch > 0:
                collision_rects.append(pygame.Rect(cx, cy, cw, ch))

        # Sort checkpoints by id for sequential activation
        checkpoints.sort(key=lambda cp: cp.checkpoint_id)

        return StageData(
            map_layer=map_layer,
            collision_rects=collision_rects,
            entity_list=entity_list,
            checkpoints=checkpoints,
            spawn_point=spawn_point,
            next_trigger=next_trigger,
            stage_id=stage_id,
            stage_name=stage_name,
            time_limit=time_limit,
            bgm_track=bgm_track,
        )

    # ── Private helpers ────────────────────────────────────────────

    @classmethod
    def _build_entity(
        cls,
        entity_cls: Type[BaseEntity],
        x: float,
        y: float,
        props: dict[str, object],
    ) -> BaseEntity:
        """Instantiate *entity_cls* from TMX object properties."""
        import inspect

        sig = inspect.signature(entity_cls.__init__)
        param_names = {
            name
            for name, param in sig.parameters.items()
            if param.kind
            in (
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
                inspect.Parameter.KEYWORD_ONLY,
            )
            and name not in ("self", "spawn_position")
        }

        kwargs: dict[str, object] = {}
        for param in param_names:
            if param in props:
                kwargs[param] = props[param]

        return entity_cls(
            spawn_position=pygame.Vector2(x, y), **kwargs
        )

    @staticmethod
    def _get_str_prop(
        tmx: Any, name: str, default: str
    ) -> str:
        """Read a string property from a TiledMap."""
        val = tmx.properties.get(name)
        return str(val) if val is not None else default

    @staticmethod
    def _get_int_prop(
        tmx: Any, name: str, default: int
    ) -> int:
        """Read an int property from a TiledMap."""
        val = tmx.properties.get(name)
        return int(val) if val is not None else default
