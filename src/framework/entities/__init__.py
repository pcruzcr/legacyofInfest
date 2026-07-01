"""
Module: __init__
System: framework.entities
Academic Unit: N/A
Description: Entity package initialization.
"""

from src.framework.entities.base_entity import BaseEntity
from src.framework.entities.enemy_base import EnemyBase, EnemyState
from src.framework.entities.player import Player
from src.framework.entities.boss_base import BossBase, BossPhase

__all__ = [
    "BaseEntity",
    "EnemyBase",
    "EnemyState",
    "Player",
    "BossBase",
    "BossPhase",
]
