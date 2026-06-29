"""
Module: base_scene
System: engine.scene
Academic Unit: N/A
Description: Abstract base class for all scenes. Defines the lifecycle
interface: on_enter, on_exit, update, draw, plus optional on_pause/on_resume.
"""
from __future__ import annotations
import abc
import pygame


class BaseScene(abc.ABC):
    """Abstract scene that all game scenes must implement."""

    @abc.abstractmethod
    def on_enter(self) -> None:
        """Called when the scene becomes active."""
        ...

    @abc.abstractmethod
    def on_exit(self) -> None:
        """Called when the scene is removed from the stack."""
        ...

    @abc.abstractmethod
    def update(self, dt: float) -> None:
        """Update logic. Called once per frame while active."""
        ...

    @abc.abstractmethod
    def draw(self, surface: pygame.Surface) -> None:
        """Render the scene onto the given surface."""
        ...

    def on_pause(self) -> None:
        """Called when another scene is pushed on top of this one."""
        pass

    def on_resume(self) -> None:
        """Called when the scene on top is popped and this one becomes active again."""
        pass
