"""
Module: game_context
System: engine.core
Academic Unit: N/A
Description: Dependency Injection container for all shared engine subsystems.
Created by App during startup and passed to every scene via BaseScene.__init__.

DI PATTERN: Explicit dependency injection eliminates global App._instance lookups.
Each subsystem (input, audio, scene manager, event bus) is provided explicitly
rather than accessed through global state.
"""
from __future__ import annotations

from src.engine.core.clock import DeltaClock


class GameContext:
    """
    Dependency injection container. Holds all shared engine subsystems.
    Passed to every scene via BaseScene.__init__(self, context).

    Attributes:
        input_manager:   Unified keyboard + controller input
        audio_manager:   Music and sound effect playback
        scene_manager:   Scene stack (push/pop/replace)
        event_bus:       Pub/sub event dispatch
        clock:           Global delta-time clock with time_scale
        running:         Whether the game loop should continue
    """

    def __init__(
        self,
        input_manager,
        audio_manager,
        scene_manager,
        event_bus,
        clock: DeltaClock | None = None,
    ) -> None:
        self.input_manager = input_manager
        self.audio_manager = audio_manager
        self.scene_manager = scene_manager
        self.event_bus = event_bus
        self.clock: DeltaClock | None = clock
        self.running: bool = True

    def quit(self) -> None:
        """Signal the game loop to exit."""
        self.running = False
