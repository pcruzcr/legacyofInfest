from __future__ import annotations

from dataclasses import dataclass, field

import pygame

from src.engine.core.event_bus import EventBus
from src.framework.entities.enemy_base import EnemyBase


@dataclass
class BossPhase:
    """Definition of a single boss phase."""

    phase_index: int
    health_threshold: float
    attack_patterns: list[str] = field(default_factory=list)
    movement_type: str = "stationary"
    speed_multiplier: float = 1.0
    sprite_override: str | None = None
    filter_effect: str | None = None


class BossBase(EnemyBase):
    """
    Base class for all boss entities. Extends EnemyBase with phase management,
    phase transition protocol, and boss HUD integration.

    Subclasses define phases; this class handles health threshold checks,
    transition animation, and BOSS_PHASE_CHANGED event emission.
    """

    def __init__(
        self,
        spawn_position: pygame.Vector2,
        max_health: float = 20.0,
        damage_on_contact: float = 1.0,
    ) -> None:
        super().__init__(
            spawn_position=spawn_position,
            max_health=max_health,
            damage_on_contact=damage_on_contact,
            contact_knockback=0.0,
        )

        self.phases: list[BossPhase] = []
        self.current_phase: int = 0
        self.phase_health_thresholds: list[float] = []
        self.is_transitioning: bool = False
        self.transition_timer: float = 0.0
        self._phase_max_health: float = max_health
        self._boss_name: str = "BOSS"

    def set_phases(self, phases: list[BossPhase]) -> None:
        """Set the phase list and extract health thresholds."""
        self.phases = phases
        self.phase_health_thresholds = [p.health_threshold for p in phases]

    def set_boss_name(self, name: str) -> None:
        self._boss_name = name

    @property
    def boss_name(self) -> str:
        return self._boss_name

    @property
    def phase_count(self) -> int:
        return len(self.phases) if self.phases else 1

    def apply_hit(
        self,
        damage: float,
        source_position: tuple[float, float],
    ) -> None:
        if not self.is_alive or self.is_transitioning:
            return
        if self._invincibility_timer > 0:
            return
        super().apply_hit(damage, source_position)

        if self.is_alive:
            self._check_phase_transition()

    def _check_phase_transition(self) -> None:
        """Check if health dropped below the next phase threshold."""
        if self.current_phase >= len(self.phase_health_thresholds) - 1:
            return
        next_threshold = self.phase_health_thresholds[self.current_phase + 1]
        if self.current_health <= next_threshold:
            self._start_phase_transition()

    def _start_phase_transition(self) -> None:
        """Begin phase transition: invincible, timer starts."""
        self.is_transitioning = True
        self._invincibility_timer = float("inf")
        self.transition_timer = 2.5

    def _finish_phase_transition(self) -> None:
        """Complete phase transition: advance phase, emit event."""
        self.current_phase += 1
        self.is_transitioning = False
        self._invincibility_timer = 0.0

        phase = self.phases[self.current_phase]
        if phase.speed_multiplier != 1.0:
            pass

        EventBus.emit(
            "BOSS_PHASE_CHANGED",
            boss_name=self._boss_name,
            phase=self.current_phase,
            phase_count=self.phase_count,
            new_max_health=self._phase_max_health,
        )

    def update(self, dt: float) -> None:
        if self.is_transitioning:
            self.transition_timer -= dt
            if self.transition_timer <= 0:
                self._finish_phase_transition()
            return

        # Load phase-specific speed multiplier on phase properties
        if self.phases and self.current_phase < len(self.phases):
            phase = self.phases[self.current_phase]

        super().update(dt)

    def draw(
        self,
        surface: pygame.Surface,
        camera_offset: pygame.Vector2,
    ) -> None:
        if not self.is_visible or not self.is_alive:
            return

        # Draw placeholder boss (purple) vs normal enemy (red)
        screen_x = int(self.position.x - camera_offset.x)
        screen_y = int(self.position.y - camera_offset.y)

        color = (120, 40, 140) if not self.is_transitioning else (200, 200, 0)
        pygame.draw.rect(
            surface,
            color,
            (screen_x, screen_y, self.rect.width, self.rect.height),
        )
        pygame.draw.rect(
            surface,
            (255, 255, 255),
            (screen_x, screen_y, self.rect.width, self.rect.height),
            1,
        )
