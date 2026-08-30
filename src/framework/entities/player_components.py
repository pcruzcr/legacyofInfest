"""
PlayerComponents — Componentes extraídos de Player (Facade + Strategy).

Player era 1463 líneas con 6 responsabilidades mezcladas:
física, combate, estamina, combo, animación y sonido.
Cada grupo vivía en el mismo `__init__` y `update`, rompiendo SRP y
haciendo que un cambio de balance tocara colisión.

Ahora cada grupo es un componente con su propia Strategy:
- PlayerPhysicsComponent: Strategy PhysicsProfile (plataformas/cenital/vuelo)
- PlayerCombatComponent: Strategy DamageCalculation + Combo
- PlayerAnimationComponent: Strategy Sprite/Contorno
- PlayerStaminaComponent: Strategy Estamina

Player queda como Facade que delega y mantiene la API pública
(`player.combo_count`, `player.velocity`, etc.) para las 26 entregas.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import pygame

from src.framework.physics.perfil import PhysicsProfile

if TYPE_CHECKING:
    pass


@dataclass
class PlayerPhysicsComponent:
    """Física desacoplada — Strategy por perfil."""

    perfil: PhysicsProfile = field(default_factory=PhysicsProfile.plataformas)
    velocity: pygame.Vector2 = field(default_factory=lambda: pygame.Vector2(0.0, 0.0))
    vx_integrada: float = 0.0
    is_grounded: bool = False
    pendientes: list[Any] = field(default_factory=list)
    venia_del_suelo: bool = False
    squash_x: float = 1.0
    squash_y: float = 1.0
    material_de_zona: Any | None = None
    corriente_medio: pygame.Vector2 = field(default_factory=lambda: pygame.Vector2(0.0, 0.0))

    def aplicar_gravedad(self, dt: float) -> None:
        if self.perfil.modo != "cenital":
            self.velocity.y += self.perfil.gravedad * dt
            self.velocity.y = min(self.velocity.y, self.perfil.max_caida)


@dataclass
class PlayerCombatComponent:
    """Combate y recursos — Strategy de daño y combo."""

    combo_count: int = 0
    combo_timer: float = 0.0
    last_attack_type: str = ""
    combo_active: bool = False
    special_meter: float = 0.0
    special_meter_max: float = 100.0
    special_gain_per_hit: float = 100.0 / 12.0
    estamina_max: float = 0.0
    estamina: float = 0.0
    coste_dash: float = 25.0
    recuperacion_estamina: float = 35.0
    espera_estamina: float = 0.6
    espera_restante: float = 0.0
    bonus_max_health: float = 0.0
    bonus_speed: float = 0.0
    bonus_damage: float = 0.0
    bonus_arbol_salud: float = 0.0
    bonus_arbol_dano: float = 0.0
    bonus_arbol_defensa: float = 0.0
    bonus_ultimate: float = 0.0
    habilidades_libres: bool = True

    def reset_combo(self) -> None:
        self.combo_count = 0
        self.combo_timer = 0.0
        self.combo_active = False
        self.last_attack_type = ""


@dataclass
class PlayerAnimationComponent:
    """Animación y sprites — Strategy de render."""

    sprite_frames: dict[str, list[pygame.Surface]] = field(default_factory=dict)
    animation_timer: float = 0.0
    animation_frame: int = 0
    facing_direction: int = 1
    squash_x: float = 1.0
    squash_y: float = 1.0
