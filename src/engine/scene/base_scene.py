"""
Module: base_scene
System: engine.scene
Academic Unit: N/A
Description: Abstract base class for all scenes. Defines the lifecycle
interface: on_enter, on_exit, update, draw, plus optional on_pause/on_resume.

DI NOTE (Fase 1): Every scene now receives a GameContext via __init__,
eliminating global App._instance lookups. Subclasses must call super().__init__(context).
"""
from __future__ import annotations

import abc
from typing import TYPE_CHECKING, Any

import pygame

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext


class BaseScene(abc.ABC):
    """Abstract scene that all game scenes must implement."""

    def __init__(self, context: GameContext) -> None:
        """Every scene receives the shared GameContext for dependency injection."""
        self.context: GameContext = context
        self.params: dict[str, Any] = {}

    @property
    def input(self) -> Any:
        """Shortcut to the input manager."""
        return self.context.input_manager

    @property
    def audio(self) -> Any:
        """Shortcut to the audio manager."""
        return self.context.audio_manager

    @property
    def events(self) -> Any:
        """Shortcut to the event bus."""
        return self.context.event_bus

    def awake(self) -> None:
        """Called once when the scene is first instantiated (before on_enter)."""

    def start(self) -> None:
        """Called after awake, when the scene becomes active."""

    def process_events(self, events: list[pygame.event.Event]) -> None:
        """Called every frame with the raw pygame event list."""

    @abc.abstractmethod
    def on_enter(self) -> None:
        """Called when the scene becomes active."""
        ...

    def destroy(self) -> None:
        """Called when the scene is permanently removed. Override to clean up."""

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

    def medidas_de_depuracion(self) -> dict[str, object]:
        """Cuentas que esta escena quiere ver en la consola (F11) — AUD-283.

        Vacío por defecto: un menú no tiene nada que contar y obligarle a
        devolver ceros sólo llenaría la consola de ruido. Un escenario devuelve
        sus entidades, sus partículas y lo que esté midiendo esa semana.

        Se pregunta **sólo cuando la consola está abierta**, así que puede
        permitirse recorrer listas: no cuesta nada en una partida normal.
        """
        return {}

    def on_pause(self) -> None:
        """Called when another scene is pushed on top of this one."""
        pass

    def on_resume(self) -> None:
        """Called when the scene on top is popped and this one becomes active again."""
        pass
