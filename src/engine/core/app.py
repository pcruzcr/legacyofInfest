"""
Module: app
System: engine
Academic Unit: N/A
Description: Main application class for Legacy of InFest. Owns the game
loop, the internal render surface, and all top-level engine subsystems
(clock, event bus, asset loader, input, audio, scene manager).
"""

import sys

import pygame

from src.engine.core.clock import DeltaClock
from src.engine.core.event_bus import EventBus
from src.engine.core.settings import (
    BACKGROUND_COLOR,
    DISPLAY_SCALE,
    INTERNAL_HEIGHT,
    INTERNAL_WIDTH,
)
from src.engine.input.input_manager import InputManager
from src.engine.audio.audio_manager import AudioManager
from src.engine.scene.scene_manager import SceneManager
from src.engine.scenes.splash_scene import SplashScene


class App:
    """Top-level application container for the Legacy of InFest engine.

    Owns the display surfaces, the clock, the event bus, and every
    subsystem manager.  Constructing an ``App`` initialises pygame and
    prepares the engine for the main loop; call ``run()`` to enter it.
    """

    def __init__(self) -> None:
        """Initialise pygame, create surfaces, and construct subsystems."""
        pygame.init()
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

        # Internal (logical) resolution — everything is rendered here first.
        self.internal_surface: pygame.Surface = pygame.Surface(
            (INTERNAL_WIDTH, INTERNAL_HEIGHT)
        )

        # Window surface — scaled view of the internal surface.
        self.window_surface: pygame.Surface = pygame.display.set_mode(
            (
                INTERNAL_WIDTH * DISPLAY_SCALE,
                INTERNAL_HEIGHT * DISPLAY_SCALE,
            ),
            pygame.SCALED | pygame.RESIZABLE,
        )
        pygame.display.set_caption("Legacy of InFest")

        # Subsystems.
        self.clock: DeltaClock = DeltaClock()
        # EventBus is a static class — no instance needed.
        self.scene_manager: SceneManager = SceneManager()
        self.input_manager: InputManager = InputManager()
        self.audio_manager: AudioManager = AudioManager()

        # Push the splash scene so the scene stack is non-empty.
        self.scene_manager.push(SplashScene())

    def run(self) -> None:
        """Enter the main game loop.

        The loop runs at TARGET_FPS frames per second and does not return until the
        user quits.  Each frame:
        1. Processes pygame events.
        2. Pumps input.
        3. Dispatches queued EventBus events.
        4. Updates the current scene.
        5. Clears internal surface with non-black background.
        6. Draws the current scene to the internal surface.
        7. Scales and blits to the window surface.
        8. Flips the display.
        """
        running = True
        while running:
            # --- Event processing ---
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    running = False

            # --- Subsystem updates ---
            self.input_manager.pump(events)
            EventBus.dispatch()

            # --- Frame timing ---
            dt = self.clock.tick()

            # --- Scene update & draw ---
            current_scene = self.scene_manager.current
            if current_scene is not None:
                current_scene.update(dt)
                self.internal_surface.fill(BACKGROUND_COLOR)
                current_scene.draw(self.internal_surface)

            # --- Present ---
            scaled = pygame.transform.scale(
                self.internal_surface,
                (
                    INTERNAL_WIDTH * DISPLAY_SCALE,
                    INTERNAL_HEIGHT * DISPLAY_SCALE,
                ),
            )
            self.window_surface.blit(scaled, (0, 0))
            pygame.display.flip()

        self.quit()

    def quit(self) -> None:
        """Cleanly shut down the engine and exit the process."""
        self.audio_manager.stop_music()
        pygame.quit()
        sys.exit(0)