"""
GameModes — Perfiles declarativos para plataforma y RPG.

Hace el framework 100% compatible con ambos géneros sin ramas en el motor.
Un stage declara `game_mode="rpg"` y el loader aplica el perfil correspondiente.
"""

from __future__ import annotations

from dataclasses import dataclass

from src.framework.physics.perfil import PhysicsProfile


@dataclass(frozen=True)
class GameMode:
    name: str
    physics: PhysicsProfile
    camera_mode: str  # seguir, zona_muerta, sala
    enable_combo: bool
    enable_quests: bool
    enable_inventory: bool


def plataforma() -> GameMode:
    return GameMode(
        name="plataforma",
        physics=PhysicsProfile.plataformas(),
        camera_mode="zona_muerta",
        enable_combo=True,
        enable_quests=False,
        enable_inventory=False,
    )


def rpg() -> GameMode:
    # RPG top-down usa cenital sin gravedad, con inventario/quests
    return GameMode(
        name="rpg",
        physics=PhysicsProfile.cenital(),
        camera_mode="sala",
        enable_combo=False,
        enable_quests=True,
        enable_inventory=True,
    )


MODOS: dict[str, GameMode] = {
    "plataforma": plataforma(),
    "rpg": rpg(),
    "cenital": rpg(),  # alias
    "lateral": plataforma(),
}
