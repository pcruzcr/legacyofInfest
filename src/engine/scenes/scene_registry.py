"""
Module: scene_registry
System: engine.scenes
Description: Centralized lazy-loading registry for all demo/lab scenes.
Replaces the _try_scene() elif chain with a register → build pattern.
"""
from __future__ import annotations

import logging
from collections.abc import Callable
from typing import TYPE_CHECKING, cast

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext
    from src.engine.scene.base_scene import BaseScene

SceneFactory = Callable[..., "BaseScene"]


class SceneRegistry:
    """Registry that maps scene keys to lazy-importing factory functions."""

    def __init__(self) -> None:
        self._builders: dict[str, SceneFactory] = {}

    def register(self, key: str, factory: SceneFactory) -> None:
        self._builders[key] = factory

    def build(self, key: str, ctx: GameContext) -> BaseScene | None:
        factory = self._builders.get(key)
        if factory is None:
            return None
        try:
            return factory(ctx)
        except (ImportError, RuntimeError, TypeError) as e:
            logger.warning("scene_registry: failed to build '%s': %s", key, e)
            return None

    @property
    def keys(self) -> frozenset[str]:
        return frozenset(self._builders.keys())


# Module-level singleton
_REGISTRY: SceneRegistry | None = None


def get_registry() -> SceneRegistry:
    global _REGISTRY
    if _REGISTRY is None:
        _REGISTRY = SceneRegistry()
    return _REGISTRY


def register_demo_scenes() -> None:
    """Register all known demo/lab scenes. Called once at app startup."""
    reg = get_registry()

    # Each registration is a closure with a lazy import inside
    reg.register("vector", lambda ctx: _build_scene(ctx, "vector_lab_scene", "VectorLabScene"))
    reg.register("transform", lambda ctx: _build_scene(ctx, "transform_lab_scene", "TransformLabScene"))
    reg.register("curve", lambda ctx: _build_scene(ctx, "curve_editor_scene", "CurveEditorScene"))
    reg.register("interpolate", lambda ctx: _build_scene(ctx, "interpolation_lab_scene", "InterpolationLabScene"))
    reg.register("color", lambda ctx: _build_scene(ctx, "color_theory_scene", "ColorTheoryScene"))
    reg.register("noise", lambda ctx: _build_scene(ctx, "noise_lab_scene", "NoiseLabScene"))
    reg.register("collision", lambda ctx: _build_scene(ctx, "collision_lab_scene", "CollisionLabScene"))
    reg.register("filter", lambda ctx: _build_scene(ctx, "filter_demo_scene", "FilterDemoScene"))
    reg.register("vision", lambda ctx: _build_scene(ctx, "vision_demo_scene", "VisionDemoScene"))
    reg.register("pattern", lambda ctx: _build_scene(ctx, "pattern_demo_scene", "PatternDemoScene"))
    reg.register("combo", lambda ctx: _build_scene(ctx, "combo_demo_scene", "ComboDemoScene"))
    reg.register("inventory", lambda ctx: _build_scene(ctx, "inventory_scene", "InventoryScene"))
    reg.register("shop", lambda ctx: _build_scene(ctx, "shop_scene", "ShopScene"))
    reg.register("achievement", lambda ctx: _build_scene(ctx, "achievement_scene", "AchievementScene"))
    reg.register("worldmap", lambda ctx: _build_scene(ctx, "world_map_scene", "WorldMapScene"))
    reg.register("bestiary", lambda ctx: _build_scene(ctx, "bestiary_scene", "BestiaryScene"))
    reg.register("progress", lambda ctx: _build_scene(ctx, "progress_scene", "ProgressScene"))
    reg.register("leaderboard", lambda ctx: _build_scene(ctx, "leaderboard_scene", "LeaderboardScene"))
    reg.register("pipeline", lambda ctx: _build_scene(ctx, "pipeline_builder_scene", "PipelineBuilderScene"))
    reg.register("sandbox", lambda ctx: _build_scene(ctx, "sandbox_scene", "SandboxScene"))
    reg.register("wizard", lambda ctx: _build_scene(ctx, "stage_wizard_scene", "StageWizardScene"))


def _build_scene(ctx: GameContext, module_name: str, class_name: str) -> BaseScene | None:
    import importlib
    mod = importlib.import_module(f"src.engine.scenes.{module_name}")
    cls = getattr(mod, class_name, None)
    if cls is None:
        return None
    return cast("BaseScene", cls(ctx))
