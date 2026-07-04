"""
Module: entity_factory
System: framework.entities
Academic Unit: N/A
Description: Centralized entity factory using the registry pattern.
All known enemy types are auto-registered on import, eliminating the need
for stage files to call StageLoader.register_entity() manually.

FACTORY PATTERN (Fase 4): Entity creation is centralized here rather than
scattered across stage files. StageLoader.load() looks up entity types in
StageLoader._entity_registry, which is populated by ensure_registered().
Adding a new enemy type requires only importing it in the registry dict below.
"""
from __future__ import annotations

from src.framework.entities.enemy_base import EnemyBase
from src.framework.entities.enemy_flying import EnemyFlying
from src.framework.entities.enemy_shooter import EnemyShooter
from src.framework.entities.enemy_walker import EnemyWalker
from src.framework.stage.stage_loader import StageLoader

_registered: bool = False


def ensure_registered() -> None:
    """
    Register all known entity types with StageLoader.
    Idempotent - safe to call multiple times.
    Call once before loading any stage (e.g., in App.__init__).
    Boss entities are imported lazily to avoid paying numpy/sklearn
    import cost at game startup (~3.4s).
    """
    global _registered
    if _registered:
        return

    from src.stages.boss_venado.boss_venado import BossVenado

    _ENTITY_REGISTRY: dict[str, type[EnemyBase]] = {
        "Walker": EnemyWalker,
        "Flying": EnemyFlying,
        "Shooter": EnemyShooter,
        "BossVenado": BossVenado,
    }

    for type_name, entity_class in _ENTITY_REGISTRY.items():
        StageLoader.register_entity(type_name, entity_class)
    _registered = True
