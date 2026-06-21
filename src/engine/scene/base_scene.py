"""
Module: base_scene
System: engine
Academic Unit: Framework scaffold
Description: ``BaseScene`` is the abstract base class every scene
inherits from.  Concrete scenes must implement ``on_enter``,
``on_exit``, ``update`` and ``draw``; ``on_pause`` and ``on_resume``
have default no-op implementations and may be overridden as needed.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

import pygame


class BaseScene(ABC):
    """Abstract base class for all engine scenes."""

    @abstractmethod
    def on_enter(self) -> None:
        """Called once when this scene becomes the active scene."""

    @abstractmethod
    def on_exit(self) -> None:
        """Called once when this scene is removed from the stack."""

    @abstractmethod
    def update(self, dt: float) -> None:
        """Per-frame logic update.

        Args:
            dt: Delta time in seconds since the last frame.
        """

    @abstractmethod
    def draw(self, surface: pygame.Surface) -> None:
        """Render the scene to *surface*.

        Args:
            surface: The internal 320×224 render target.
        """

    def on_pause(self) -> None:
        """Called when another scene is pushed on top of this one.

        Optional override. Default: no-op.
        """

    def on_resume(self) -> None:
        """Called when the scene above this one is popped.

        Optional override. Default: no-op.
        """
