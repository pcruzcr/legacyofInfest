"""
Module: app
System: engine
Academic Unit: Framework scaffold
Description: Main application class for Legacy of InFest.  Owns the game
loop, the internal render surface, and all top-level engine subsystems
(clock, event bus, asset loader, input, audio, scene manager).
"""

from __future__ import annotations

import sys

import pygame

from src.engine.core.clock import DeltaClock
from src.engine.core.event_bus import EventBus
from src.engine.core.settings import (
    DISPLAY_SCALE,
    INTERNAL_HEIGHT,
    INTERNAL_WIDTH,
)
from src.engine.scene.scene_manager import SceneManager
from src.engine.scenes.splash_scene import SplashScene

# ---------------------------------------------------------------------------
# Placeholder stubs for subsystems that do not yet exist.
# These will be replaced by their real implementations in later phases.
# See 25_IMPLEMENTATION_ROADMAP.md §4.
# ---------------------------------------------------------------------------


class AssetLoader:
    """Placeholder stub — replaced in Phase 2 (T2.2)."""

    @classmethod
    def load_image(cls, path: str | object) -> pygame.Surface:
        """Placeholder: returns a small dummy surface."""
        return pygame.Surface((16, 16))

    @classmethod
    def load_sound(cls, path: str | object) -> None:
        """Placeholder: no-op."""

    @classmethod
    def load_spritesheet(
        cls, path: str | object, frame_w: int, frame_h: int
    ) -> None:
        """Placeholder: no-op."""


class InputManager:
    """Placeholder stub — replaced in Phase 2 (T2.5)."""

    def pump(self, events: list[pygame.event.Event]) -> None:
        """Placeholder: no-op."""


class AudioManager:
    """Placeholder stub — replaced in Phase 2 (T2.7)."""

    def play_music(
        self, name: str, loop: bool = True, fade_ms: int = 0
    ) -> None:
        """Placeholder: no-op."""

    def stop_music(self, fade_ms: int = 0) -> None:
        """Placeholder: no-op."""

    def play_sfx(self, name: str, volume: float = 1.0) -> None:
        """Placeholder: no-op."""

    def set_music_volume(self, volume: float) -> None:
        """Placeholder: no-op."""

    def set_sfx_volume(self, volume: float) -> None:
        """Placeholder: no-op."""


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
        pygame.mixer.init(frequency=22050, size=-16, channels=2)

        # Internal (logical) resolution — everything is rendered here first.
        self.internal_surface: pygame.Surface = pygame.Surface(
            (INTERNAL_WIDTH, INTERNAL_HEIGHT)
        )

        # Window surface — scaled view of the internal surface.
        self.window_surface: pygame.Surface = pygame.display.set_mode(
            (
                INTERNAL_WIDTH * DISPLAY_SCALE,
                INTERNAL_HEIGHT * DISPLAY_SCALE,
            )
        )
        pygame.display.set_caption("Legacy of InFest")

        # Subsystems.
        self.clock: DeltaClock = DeltaClock()
        # EventBus is a static class — no instance needed.
        self.asset_loader: AssetLoader = AssetLoader()
        self.input_manager: InputManager = InputManager()
        self.audio_manager: AudioManager = AudioManager()
        self.scene_manager: SceneManager = SceneManager()

        # Push the splash scene so the scene stack is non-empty.
        self.scene_manager.push(SplashScene())

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

            # --- Frame timing ---
            dt = self.clock.tick()

            # --- Subsystem updates ---
            EventBus.dispatch()
            self.input_manager.pump(events)

            # --- Scene update & draw ---
            current_scene = self.scene_manager.current
            if current_scene is not None:
                current_scene.update(dt)
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
