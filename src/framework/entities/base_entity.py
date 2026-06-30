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

    def __init__(self, position: pygame.Vector2) -> None:
        """Initialize the entity at the given world-space position."""
        self.position = pygame.Vector2(position)
        self.rect = pygame.Rect(0, 0, 0, 0)
        self.is_active: bool = True
        self.is_visible: bool = True
        self.layer: int = 4

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