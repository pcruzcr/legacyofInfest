"""
Module: base_entity
System: framework
Academic Unit: Framework scaffold
Description: ``BaseEntity`` is the abstract base class every entity
inherits from.  Concrete entities must implement ``update`` and
``draw``; ``on_enter``/``on_exit`` are optional life-cycle hooks.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

import pygame


class BaseEntity(ABC):
    """Abstract base class for all in-world entities."""

    @abstractmethod
    def update(self, dt: float) -> None:
        """Per-frame logic update.

        Args:
            dt: Delta time in seconds since the last frame.
        """

    @abstractmethod
    def draw(self, surface: pygame.Surface) -> None:
        """Render the entity to *surface*.

        Args:
            surface: The internal 320×224 render target.
        """

    def on_enter(self) -> None:
        """Called once when the entity is spawned.

        Optional override. Default: no-op.
        """

    def on_exit(self) -> None:
        """Called once when the entity is removed from the world.

        Optional override. Default: no-op.
        """
