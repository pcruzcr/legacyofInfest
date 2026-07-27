"""
Module: boss_template
System: framework/entities (student boss assignment)
Academic Unit: See README.md front-matter for units_demonstrated.

STUDENT INSTRUCTIONS:
1. Copy this file to src/stages/<your_assignment_id>/<your_assignment_id>.py
2. Rename the class below from BossTemplate to your boss's name
   (e.g., class BossRey(BossBase): for El Rey Terciopelo).
3. Define your boss's phases via set_phases() with BossPhase objects.
4. Fill in every # TODO(student) marker.
5. See 17_BOSS_SPEC.md for the full design contract of your assigned boss.
6. Create a companion scene file <your_assignment_id>_scene.py that
   inherits from StageScene and points to your boss's arena TMX.

Test with:
   python main.py --boss <your_assignment_id>
"""
from __future__ import annotations

import pygame

from src.framework.entities.boss_base import BossBase, BossPhase


# TODO(student): Rename this class to match your assigned boss
class BossTemplate(BossBase):
    def __init__(self, spawn_position: pygame.Vector2) -> None:
        # TODO(student): Replace this single placeholder phase with the
        # full phase list from your boss's 17_BOSS_SPEC.md entry (or your
        # professor-approved design if not yet documented there).
        phases = [
            BossPhase(
                phase_index=0,
                health_threshold=0.0,
                attack_patterns=["PLACEHOLDER_ATTACK"],
                movement_type="stationary",
                speed_multiplier=1.0,
            ),
        ]
        super().__init__(
            spawn_position=spawn_position,
            # TODO(student): Set your boss's total health per its spec document
            max_health=10.0,
            damage_on_contact=0.5,
        )
        # TODO(student): Set your boss's display name (used in the boss HUD)
        self.set_boss_name("Untitled Boss")
        self.set_phases(phases)

    def _patrol_behavior(self, dt: float) -> None:
        # TODO(student): Implement this phase's idle/patrol movement.
        pass

    def _alert_behavior(self, dt: float) -> None:
        # TODO(student): Implement this phase's active-combat movement
        # and attack-pattern triggering, per your BossPhase.attack_patterns.
        pass

    def _get_animation_key(self) -> str:
        # TODO(student): Return the sprite animation key matching
        # self.state and self.current_phase (e.g., "drift", "idle").
        return "drift"

    def _build_hitbox(self) -> pygame.Rect:
        # TODO(student): Define your boss's attack hitbox in LOCAL space
        # (offset from self.position). See boss_venado.py for reference.
        return pygame.Rect(6, 4, 36, 44)

    def _build_hurtbox(self) -> pygame.Rect:
        # TODO(student): Define your boss's damage-receiving hurtbox in
        # LOCAL space.
        ox = (self.rect.width - 30) // 2
        oy = (self.rect.height - 40) // 2
        return pygame.Rect(ox, oy, 30, 40)
