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

from typing import TYPE_CHECKING, Any

from src.engine.core.clock import DeltaClock
from src.engine.core.save_data import SaveData
from src.engine.core.save_manager import SaveManager

if TYPE_CHECKING:
    from src.engine.audio.audio_manager import AudioManager
    from src.engine.core.event_bus import EventBus
    from src.engine.input.input_manager import InputManager
    from src.engine.scene.scene_manager import SceneManager


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
        save_manager:    Save/load persistence (5 slots, JSON)
        pending_load:    SaveData to apply on next stage start (used by LoadGameScene)
        running:         Whether the game loop should continue
    """

    def __init__(
        self,
        input_manager: InputManager,
        audio_manager: AudioManager,
        scene_manager: SceneManager,
        event_bus: EventBus,
        clock: DeltaClock | None = None,
        save_manager: SaveManager | None = None,
    ) -> None:
        self.input_manager = input_manager
        self.audio_manager = audio_manager
        self.scene_manager = scene_manager
        self.event_bus = event_bus
        self.clock: DeltaClock | None = clock
        self.save_manager: SaveManager = save_manager if save_manager is not None else SaveManager()
        self.pending_load: SaveData | None = None
        self.running: bool = True
        # AUD-251 — las banderas de mundo que pone `set_flag:` en un guion de
        # diálogo. Viven aquí y no en la escena porque una bandera es lo que
        # queda **después** de hablar: sobrevive al cambio de sala y baja a
        # `SaveData.zone_flags` en el siguiente checkpoint. Ese campo existía
        # desde el principio y sólo lo escribían las pruebas.
        self.banderas: dict[str, bool] = {}

    @property
    def audio(self) -> Any:
        return self.audio_manager

    def quit(self) -> None:
        """Signal the game loop to exit."""
        self.running = False
