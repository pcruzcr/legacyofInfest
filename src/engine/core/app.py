"""
Module: app
System: engine.core
Academic Unit: N/A
Description: Main application class. Owns the game loop, display,
clock, event bus, input, audio, and scene management.
"""
from __future__ import annotations
import os
import sys

import pygame

from src.engine.core import settings
from src.engine.core.clock import DeltaClock
from src.engine.core.event_bus import EventBus, set_default_bus
from src.engine.core.game_context import GameContext
from src.engine.input.input_manager import InputManager
from src.engine.audio.audio_manager import AudioManager
from src.engine.scene.scene_manager import SceneManager
from src.framework.entities.entity_factory import ensure_registered
from src.engine.scenes.transition_manager import TransitionManager
from src.engine.scenes.debug_overlay import DebugOverlay
from src.engine.scenes.scene_registry import register_demo_scenes

# Force nearest-neighbor scaling for pixel-art crispness (no bilinear from SDL2)
os.environ["SDL_HINT_RENDER_SCALE_QUALITY"] = "0"


class App:
    """Owns the game loop, display, and all engine subsystems."""

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
        self.event_bus = EventBus()
        set_default_bus(self.event_bus)
        self.input_manager: InputManager = InputManager()
        self.audio_manager: AudioManager = AudioManager()
        self.transition_manager: TransitionManager = TransitionManager()
        self.context = GameContext(
            input_manager=self.input_manager,
            audio_manager=self.audio_manager,
            scene_manager=None,
            event_bus=self.event_bus,
            clock=self.clock,
        )
        self.scene_manager: SceneManager = SceneManager(self.context)
        self.context.scene_manager = self.scene_manager

        # Register all known entity types before any scene loads
        ensure_registered()

        # Register all demo/lab scenes for the registry
        register_demo_scenes()

        # Debug overlay
        self._debug_overlay: DebugOverlay = DebugOverlay()

        # Push SplashScene as the first scene
        from src.engine.scenes.splash_scene import SplashScene
        self.scene_manager.push(SplashScene(self.context))

    def run(self) -> None:
        """Main game loop. The order of operations is sacred — do not reorder."""
        self.context.running = True
        while self.context.running:
            try:
                # 1. Process OS events
                events = pygame.event.get()
                for e in events:
                    if e.type == pygame.QUIT:
                        self.context.quit()

                # 2. Pump input
                self.input_manager.pump(events)

                # 3. Dispatch queued events (before update)
                self.context.event_bus.dispatch()

                # 4. Compute delta time
                dt = self.clock.tick()

                # 4a. Debug overlay input (before scene update, after dt)
                self._debug_overlay.handle_input(pygame.key.get_pressed(), dt)

                # 5. Update current scene (isolated per stage)
                try:
                    self.scene_manager.current.update(dt)
                except Exception:
                    import traceback
                    traceback.print_exc()

                # 5a. Update transitions (both App-level and scene-level)
                self.transition_manager.update(dt)
                self.scene_manager.transition.update(dt)

                # 6. Fill internal surface (background never black)
                self.internal_surface.fill(settings.BG_COLOR)

                # 7. Draw current scene (isolated per stage)
                try:
                    self.scene_manager.current.draw(self.internal_surface)
                except Exception:
                    import traceback
                    traceback.print_exc()

                # 7a. Draw transitions on top
                self.transition_manager.draw(self.internal_surface)

                # 7b. Debug overlay (F3-F6)
                self._debug_overlay.draw(self.internal_surface, self.clock.fps)

                # 8. Scale and present (nearest-neighbor for pixel-art)
                scaled = pygame.transform.scale_by(
                    self.internal_surface, settings.DISPLAY_SCALE,
                )
                pygame.display.get_surface().blit(scaled, (0, 0))
                pygame.display.flip()
            except Exception:
                import traceback
                traceback.print_exc()
                self.context.quit()

        self.scene_manager.cleanup()
        self.event_bus.clear()
        pygame.quit()
        sys.exit(0)
