"""
Module: __init__
System: framework.entities
Academic Unit: N/A
Description: Entity package initialization.
"""

from src.framework.entities.base_entity import BaseEntity
from src.framework.entities.boss_base import BossBase, BossPhase
from src.framework.entities.enemy_base import EnemyBase, EnemyState
from src.framework.entities.enemy_climber import EnemyClimber
from src.framework.entities.enemy_flying_bomber import EnemyFlyingBomber
from src.framework.entities.enemy_ice_skater import EnemyIceSkater
from src.framework.entities.enemy_parry_teacher import EnemyParryTeacher
from src.framework.entities.enemy_shielded import EnemyShielded
from src.framework.entities.enemy_summoner import EnemySummoner
from src.framework.entities.enemy_swimmer import EnemySwimmer
from src.framework.entities.enemy_terrain_shaper import EnemyTerrainShaper
from src.framework.entities.player import Player

__all__ = [
    "BaseEntity",
    "BossBase",
    "BossPhase",
    "EnemyBase",
    "EnemyClimber",
    "EnemyFlyingBomber",
    "EnemyIceSkater",
    "EnemyParryTeacher",
    "EnemyShielded",
    "EnemyState",
    "EnemySummoner",
    "EnemySwimmer",
    "EnemyTerrainShaper",
    "Player",
]
