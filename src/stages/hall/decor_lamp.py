"""
Module: decor_lamp
System: stages.hall
Academic Unit: Unit II — Vectors and interpolation

Purely decorative hanging lamp for Stage 3-2 "El Hall". Swings on a short
pendulum arc using src.engine.utils.math_utils (lerp + vec2 helpers) instead
of hand-rolled trigonometry, so the vector-math requirement is demonstrated
by an entity that actually uses the shared utility module.
"""
from __future__ import annotations

import pygame

from src.engine.utils import math_utils
from src.framework.entities.base_entity import BaseEntity


class SwingingLamp(BaseEntity):
    """A ceiling lamp that swings between two anchor points.

    Purely visual — no collision, no gameplay effect. Its position each
    frame is a `lerp` between the left and right anchor of its swing arc,
    driven by an eased oscillation so the motion settles at each end
    instead of moving at constant speed.
    """

    SWING_RADIUS_PX = 10.0
    PERIOD_SECONDS = 2.4

    def __init__(self, position: pygame.Vector2, event_bus=None, **_ignored) -> None:
        super().__init__(position, event_bus)
        self.rect = pygame.Rect(int(position.x) - 3, int(position.y), 6, 10)
        self.layer = 5
        # DrawingSystem._draw_entities checks is_alive on every entity in
        # entity_list, a convention EnemyBase follows but BaseEntity does not
        # define. A purely decorative entity is simply always alive.
        self.is_alive: bool = True

        self._anchor = pygame.Vector2(position)
        self._left = pygame.Vector2(self._anchor.x - self.SWING_RADIUS_PX, self._anchor.y + 14)
        self._right = pygame.Vector2(self._anchor.x + self.SWING_RADIUS_PX, self._anchor.y + 14)
        self._t = 0.0

    def update(self, dt: float) -> None:
        self._t += dt
        phase = (self._t % self.PERIOD_SECONDS) / self.PERIOD_SECONDS
        # Two eased half-swings (left->right, right->left) instead of a raw
        # sine, so the pendulum visibly decelerates at each end of its arc.
        if phase < 0.5:
            eased = math_utils.ease_in_out_quad(phase * 2.0)
            bob = pygame.Vector2(
                math_utils.lerp(self._left.x, self._right.x, eased),
                math_utils.lerp(self._left.y, self._right.y, eased),
            )
        else:
            eased = math_utils.ease_in_out_quad((phase - 0.5) * 2.0)
            bob = pygame.Vector2(
                math_utils.lerp(self._right.x, self._left.x, eased),
                math_utils.lerp(self._right.y, self._left.y, eased),
            )

        # Vector helpers from math_utils: how far and in what direction the
        # bob has drifted from its anchor this frame (used only to size the
        # swing-string stretch drawn below).
        offset = bob - self._anchor
        self._sway_length = math_utils.vec2_length(offset)
        self._sway_dir = math_utils.vec2_normalize(offset)

        self.position = bob
        self.rect.x = int(bob.x) - 3
        self.rect.y = int(bob.y)

    def draw(self, surface: pygame.Surface, camera_offset: pygame.Vector2) -> None:
        anchor_screen = self._anchor - camera_offset
        bob_screen = self.position - camera_offset
        pygame.draw.line(
            surface, (90, 80, 60),
            (int(anchor_screen.x), int(anchor_screen.y)),
            (int(bob_screen.x), int(bob_screen.y)), 1,
        )
        pygame.draw.circle(
            surface, (230, 200, 120),
            (int(bob_screen.x), int(bob_screen.y) + 6), 4,
        )
