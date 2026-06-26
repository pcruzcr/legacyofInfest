"""
Module: app
System: engine
Academic Unit: N/A
Description: Main application class for Legacy of InFest. Owns the game loop, the internal render surface, and all top-level engine subsystems (clock, event bus, asset loader, input, audio, scene manager).
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

# Placeholder stubs for subsystems that do not yet exist.
# These will be replaced by their real implementations in later phases.
# See 25_IMPLEMENTATION_ROADMAP.md §4.


class _PlaceholderSceneManager:
    """Minimal SceneManager stub so App constructs."""

    def __init__(self) -> None:
        self._current = None

    @property
    def current(self):
        return self._current

    def push(self, scene) -> None:
        self._current = scene
        if hasattr(scene, "on_enter"):
            scene.on_enter()


class _PlaceholderInputManager:
    """Minimal InputManager stub so App constructs."""

    def __init__(self) -> None:
        pass

    def pump(self, events) -> None:
        pass

    def is_action_pressed(self, action) -> bool:
        return False

    def is_action_held(self, action) -> bool:
        return False

    def is_action_released(self, action) -> bool:
        return False


class _PlaceholderAudioManager:
    """Minimal AudioManager stub so App constructs."""

    def __init__(self) -> None:
        pass

    def play_music(self, name: str, loop: bool = True, fade_ms: int = 0) -> None:
        pass

    def stop_music(self, fade_ms: int = 0) -> None:
        pass

    def play_sfx(self, name: str, volume: float = 1.0) -> None:
        pass

    def set_music_volume(self, volume: float) -> None:
        pass

    def set_sfx_volume(self, volume: float) -> None:
        pass


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------


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
        self.scene_manager: _PlaceholderSceneManager = _PlaceholderSceneManager()
        self.input_manager: _PlaceholderInputManager = _PlaceholderInputManager()
        self.audio_manager: _PlaceholderAudioManager = _PlaceholderAudioManager()

        # Push a minimal splash scene so the scene stack is non-empty.
        # Real SplashScene will be wired in Phase 3.
        class _SplashStub:
            def on_enter(self) -> None:
                pass

            def on_exit(self) -> None:
                pass

            def update(self, dt: float) -> None:
                pass

            def draw(self, surface: pygame.Surface) -> None:
                surface.fill((15, 15, 40))  # dark navy — Rule 10

        self.scene_manager.push(_SplashStub())

    def run(self) -> None:
        """Enter the main game loop.

        The loop runs at *TARGET_FPS* frames per second and does not
        return until the user quits.  Each frame:
        1. Dispatches queued EventBus events.
        2. Pumps input.
        3. Updates the current scene.
        4. Draws the current scene to the internal surface.
        5. Scales and blits to the window surface.
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