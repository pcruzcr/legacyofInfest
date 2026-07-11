from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Difficulty(Enum):
    EASY = "easy"
    NORMAL = "normal"
    HARD = "hard"


@dataclass
class DifficultyConfig:
    label: str
    incoming_damage_mult: float = 1.0
    outgoing_damage_mult: float = 1.0
    enemy_health_mult: float = 1.0
    heal_mult: float = 1.0
    knockback_mult: float = 1.0
    parry_window: float = 0.25
    invincibility_duration: float = 1.5
    combo_window: float = 0.5
    damage_scaling: list[float] = field(default_factory=lambda: [1.0, 1.5, 2.0])


DIFFICULTY_PRESETS: dict[Difficulty, DifficultyConfig] = {
    Difficulty.EASY: DifficultyConfig(
        label="Easy",
        incoming_damage_mult=0.5,
        outgoing_damage_mult=1.5,
        enemy_health_mult=0.7,
        heal_mult=1.5,
        knockback_mult=0.7,
        parry_window=0.3,
        invincibility_duration=2.0,
        combo_window=0.6,
        damage_scaling=[1.0, 1.8, 2.5],
    ),
    Difficulty.NORMAL: DifficultyConfig(
        label="Normal",
        incoming_damage_mult=1.0,
        outgoing_damage_mult=1.0,
        enemy_health_mult=1.0,
        heal_mult=1.0,
        knockback_mult=1.0,
        parry_window=0.2,
        invincibility_duration=1.5,
        combo_window=0.5,
        damage_scaling=[1.0, 1.5, 2.0],
    ),
    Difficulty.HARD: DifficultyConfig(
        label="Hard",
        incoming_damage_mult=1.5,
        outgoing_damage_mult=0.75,
        enemy_health_mult=1.5,
        heal_mult=0.5,
        knockback_mult=1.3,
        parry_window=0.15,
        invincibility_duration=1.0,
        combo_window=0.35,
        damage_scaling=[1.0, 1.2, 1.5],
    ),
}


_current_difficulty: Difficulty = Difficulty.NORMAL


def get_difficulty() -> Difficulty:
    return _current_difficulty


def set_difficulty(d: Difficulty) -> None:
    global _current_difficulty
    _current_difficulty = d


def get_config(d: Difficulty | None = None) -> DifficultyConfig:
    return DIFFICULTY_PRESETS[d or _current_difficulty]
