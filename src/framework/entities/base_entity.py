"""
Module: base_entity
System: framework.entities
Academic Unit: N/A
Description: Abstract base class for all game entities. Defines the lifecycle
contract (update/draw) that every entity in the framework must implement.
"""
from abc import ABC, abstractmethod

import pygame


class BaseEntity(ABC):
    """
    Root class for all game objects in the Legacy of InFest framework.
    Manages world position, a Pygame Rect for collision, visibility,
    active state, and the basic update/draw lifecycle.
    """

    def __init__(self, position: pygame.Vector2, event_bus=None) -> None:
        """Initialize the entity at the given world-space position."""
        self.position = pygame.Vector2(position)
        self.rect = pygame.Rect(0, 0, 0, 0)
        self.is_active: bool = True
        self.is_visible: bool = True
        self.layer: int = 4
        # AUD-019: entities used to fall back to a module-level singleton bus
        # when none was injected. In production App wired that singleton to the
        # real bus so it worked; under test it silently diverged, so an entity
        # emitted into one bus while the scene listened to another. Entities now
        # get an inert bus by default and must be given the real one explicitly
        # (StageScene does this for every entity it loads).
        from src.engine.core.event_bus import EventBus
        self._event_bus = event_bus if event_bus is not None else EventBus()

    def set_event_bus(self, bus) -> None:
        """Set the EventBus instance for this entity (late injection)."""
        self._event_bus = bus

    @abstractmethod
    def update(self, dt: float) -> None:
        """
        Update entity state. Must be overridden by subclasses.
        dt is delta time in seconds.
        """
        ...

    @abstractmethod
    def draw(self, surface: pygame.Surface,
             camera_offset: pygame.Vector2) -> None:
        """
        Draw the entity to the given surface.
        camera_offset must be subtracted from world position
        to compute screen position.
        """
        ...
