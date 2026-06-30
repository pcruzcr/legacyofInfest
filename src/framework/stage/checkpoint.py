"""
Module: checkpoint
System: framework.stage
Academic Unit: Unit II (Collision Detection), Unit IV (Event-Driven Systems)
Description: Checkpoint trigger zone. Activates once when the player
overlaps its rect, emitting CHECKPOINT_REACHED and changing visual
state from inactive (grey) to active (gold).
"""
from __future__ import annotations

import pygame

from src.engine.core.event_bus import EventBus
from src.framework.entities.base_entity import BaseEntity


class Checkpoint(BaseEntity):
    """Single-activation checkpoint zone."""

    def __init__(self, position: pygame.Vector2, rect: pygame.Rect, checkpoint_id: int) -> None:
        super().__init__(position)
        self.rect = pygame.Rect(rect)
        self._checkpoint_id: int = checkpoint_id
        self._activated: bool = False
        self.layer = 3

    def update(self, dt: float) -> None:
        """Checks player overlap; emits CHECKPOINT_REACHED on first activation."""
        if self._activated:
            return

    def activate(self) -> None:
        """Activate this checkpoint and emit the event."""
        if self._activated:
            return
        self._activated = True
        EventBus.emit("CHECKPOINT_REACHED", checkpoint_id=self._checkpoint_id)

    def draw(self, surface: pygame.Surface, camera_offset: pygame.Vector2) -> None:
        """Draw checkpoint placeholder: grey when inactive, gold when active."""
        if not self.is_visible:
            return

        screen_x = int(self.rect.x - camera_offset.x)
        screen_y = int(self.rect.y - camera_offset.y)

        color = (255, 215, 0) if self._activated else (100, 100, 100)
        pygame.draw.rect(surface, color, (screen_x, screen_y, self.rect.width, self.rect.height))
        pygame.draw.rect(surface, (255, 255, 255), (screen_x, screen_y, self.rect.width, self.rect.height), 1)

    @property
    def is_activated(self) -> bool:
        """Whether this checkpoint has been triggered."""
        return self._activated

    @property
    def checkpoint_id(self) -> int:
        """Unique checkpoint identifier within the stage."""
        return self._checkpoint_id
