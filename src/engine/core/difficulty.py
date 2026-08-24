from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class Difficulty(Enum):
    EASY = "easy"
    NORMAL = "normal"
    HARD = "hard"


class DifficultyConfig(BaseModel):
    label: str
    incoming_damage_mult: float = Field(default=1.0, ge=0.0, le=3.0)
    outgoing_damage_mult: float = Field(default=1.0, ge=0.0, le=3.0)
    enemy_health_mult: float = Field(default=1.0, ge=0.0, le=3.0)
    heal_mult: float = Field(default=1.0, ge=0.0, le=3.0)
    knockback_mult: float = Field(default=1.0, ge=0.0, le=3.0)
    parry_window: float = Field(default=0.25, ge=0.0, le=1.0)
    invincibility_duration: float = Field(default=1.5, ge=0.0, le=5.0)
    combo_window: float = Field(default=0.5, ge=0.0, le=2.0)


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
