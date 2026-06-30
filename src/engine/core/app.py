"""
Module: app
System: engine.core
Academic Unit: N/A
Description: Main application class. Owns the game loop, display,
clock, event bus, input, audio, and scene management.
"""
from __future__ import annotations
import pygame
import sys

from src.engine.core import settings
from src.engine.core.clock import DeltaClock
from src.engine.core.event_bus import EventBus
from src.engine.input.input_manager import InputManager
from src.engine.audio.audio_manager import AudioManager
from src.engine.scene.scene_manager import SceneManager


class App:
    """Owns the game loop, display, and all engine subsystems.
    Stores class-level references so subsystems (Player, scenes) can access shared state."""

    _instance: App | None = None
    _input_manager: InputManager | None = None

    def __init__(self) -> None:
        pygame.init()
        pygame.mixer.init()

        self.window_surface: pygame.Surface = pygame.display.set_mode(
            (settings.INTERNAL_WIDTH * settings.DISPLAY_SCALE,
             settings.INTERNAL_HEIGHT * settings.DISPLAY_SCALE),
            pygame.SCALED,
        )
        pygame.display.set_caption("Legacy of InFest")

        self.internal_surface: pygame.Surface = pygame.Surface(
            (settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT)
        )

        self.clock: DeltaClock = DeltaClock()
        self.event_bus: type[EventBus] = EventBus
        self.input_manager: InputManager = InputManager()
        App._input_manager = self.input_manager
        self.audio_manager: AudioManager = AudioManager()
        self.scene_manager: SceneManager = SceneManager()
        App._instance = self

        # Push SplashScene as the first scene
        from src.engine.scenes.splash_scene import SplashScene
        self.scene_manager.push(SplashScene())

        self._running: bool = False

    def run(self) -> None:
        """Main game loop. The order of operations is sacred — do not reorder."""
        self._running = True
        while self._running:
            # 1. Process OS events
            events = pygame.event.get()
            for e in events:
                if e.type == pygame.QUIT:
                    self._running = False

            # 2. Pump input
            self.input_manager.pump(events)

            # 3. Dispatch queued events (before update)
            self.event_bus.dispatch()

            # 4. Compute delta time
            dt = self.clock.tick()

            # 5. Update current scene
            self.scene_manager.current.update(dt)

            # 6. Fill internal surface (background never black)
            self.internal_surface.fill(settings.BG_COLOR)

            # 7. Draw current scene
            self.scene_manager.current.draw(self.internal_surface)

            # 8. Scale and present
            scaled = pygame.transform.scale(
                self.internal_surface,
                self.window_surface.get_size(),
            )
            self.window_surface.blit(scaled, (0, 0))
            pygame.display.flip()

        pygame.quit()
        sys.exit(0)


def _get_scene_manager() -> SceneManager | None:
    """Helper function for scenes to access the SceneManager."""
    if App._instance is not None:
        return App._instance.scene_manager
    return None
