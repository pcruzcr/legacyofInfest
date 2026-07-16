"""
Module: app
System: engine.core
Academic Unit: N/A
Description: Main application entry point. Owns the game loop:
process input -> dispatch events -> update -> draw -> present.
Standard Pygame loop with EventBus integration.
"""
from __future__ import annotations

import logging

import pygame

from src.engine.core import settings
from src.engine.core.clock import DeltaClock
from src.engine.core.event_bus import set_default_bus, EventBus
from src.engine.core.game_context import GameContext
from src.engine.scene.scene_manager import SceneManager
from src.engine.input.input_manager import InputManager
from src.engine.audio.audio_manager import AudioManager
from src.engine.core.save_manager import SaveManager


class App:
    """
    Top-level game application. Creates the window, initializes subsystems,
    and runs the main loop.
    """

    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("Legacy of InFest")
        pygame.mixer.init(frequency=44100, size=-16, channels=8, buffer=512)

        self.window_surface = pygame.display.set_mode(
            (settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT),
            pygame.SCALED,
        )
        self.internal_surface = pygame.Surface(
            (settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT),
        )
        self.clock = DeltaClock()
        self.running: bool = False

        self.event_bus = EventBus()
        set_default_bus(self.event_bus)

        self.input_manager = InputManager()
        self.audio_manager = AudioManager()
        self.save_manager = SaveManager()

        self.context = GameContext(
            input_manager=self.input_manager,
            audio_manager=self.audio_manager,
            scene_manager=None,
            event_bus=self.event_bus,
            clock=self.clock,
            save_manager=self.save_manager,
        )

        self.scene_manager = SceneManager(self.context)
        self.context.scene_manager = self.scene_manager

        from src.framework.entities.entity_factory import ensure_registered
        ensure_registered()
        from src.engine.scenes.scene_registry import register_demo_scenes
        register_demo_scenes()

        from src.engine.scenes.splash_scene import SplashScene
        self.scene_manager.push(SplashScene(self.context))

    def run(self) -> None:
        """Main game loop. Checks both App.running and GameContext.running
        so that scenes can signal quit via context.quit()."""
        self.running = True
        while self.running and self.context.running:
            dt = self.clock.tick()
            self._process_events()
            self.event_bus.dispatch()
            try:
                self.scene_manager.update(dt)
                self.scene_manager.transition.update(dt)
            except Exception:
                logging.error("Unhandled exception in scene update", exc_info=True)
                self._fallback_to_title()
            try:
                self._draw()
            except Exception:
                logging.error("Unhandled exception in scene draw", exc_info=True)
                self._fallback_to_title()
            pygame.display.flip()
        self._shutdown()

    def _process_events(self) -> None:
        """Collect pygame events, filter QUIT at app level, then
        pump the remainder through InputManager so scenes can
        handle CANCEL, CONFIRM, etc."""
        events = pygame.event.get()
        for e in events:
            if e.type == pygame.QUIT:
                self.running = False
                return
        self.input_manager.pump(events)

    def _draw(self) -> None:
        """Render the current scene onto the internal surface, then scale
        and present to the display.  The two-surface pipeline (internal →
        display) avoids driver inconsistencies with pygame.SCALED."""
        self.internal_surface.fill(settings.BG_COLOR)
        if self.scene_manager.stack_size > 0:
            self.scene_manager.current.draw(self.internal_surface)
        self.scene_manager.transition.draw(self.internal_surface)
        scaled = pygame.transform.scale_by(
            self.internal_surface, settings.DISPLAY_SCALE,
        )
        pygame.display.get_surface().blit(scaled, (0, 0))

    def _fallback_to_title(self) -> None:
        """Fallback to title screen on unhandled exception."""
        from src.engine.scenes.title_scene import TitleScene
        try:
            self.context.scene_manager.replace(TitleScene(self.context))
        except Exception:
            logging.error("Fallback to title also failed", exc_info=True)
            self.running = False

    def _shutdown(self) -> None:
        """Graceful shutdown."""
        self.context.quit()
        self.scene_manager.cleanup()
        pygame.quit()