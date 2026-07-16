"""
Module: cutscene_system
System: framework.stage
Academic Unit: N/A
Description: Scripted cutscene system supporting camera moves, dialogue,
animations, and scene transitions.
"""
from __future__ import annotations
import pygame
from typing import Any, Callable
from src.engine.core import settings


class CutsceneAction:
    """Base class for cutscene actions."""

    def start(self) -> None:
        ...

    def update(self, dt: float) -> bool:
        """Returns True when complete."""
        return True

    def draw(self, surface: pygame.Surface) -> None:
        ...


class WaitAction(CutsceneAction):
    """Wait for a duration in seconds."""

    def __init__(self, duration: float) -> None:
        self._duration = duration
        self._elapsed = 0.0

    def start(self) -> None:
        self._elapsed = 0.0

    def update(self, dt: float) -> bool:
        self._elapsed += dt
        return self._elapsed >= self._duration


class FadeAction(CutsceneAction):
    """Fade in or out."""

    def __init__(self, duration: float, fade_in: bool = True) -> None:
        self._duration = duration
        self._fade_in = fade_in
        self._elapsed = 0.0
        self._surface = pygame.Surface(
            (settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT)
        )
        self._surface.fill((0, 0, 0))

    def start(self) -> None:
        self._elapsed = 0.0

    def update(self, dt: float) -> bool:
        self._elapsed += dt
        return self._elapsed >= self._duration

    def draw(self, surface: pygame.Surface) -> None:
        if self._elapsed >= self._duration:
            return
        progress = self._elapsed / self._duration
        alpha = int((1.0 - progress) * 255) if self._fade_in else int(progress * 255)
        self._surface.set_alpha(max(0, min(255, alpha)))
        surface.blit(self._surface, (0, 0))


class CameraMoveAction(CutsceneAction):
    """Move camera to target position."""

    def __init__(self, target_x: float, target_y: float, duration: float,
                 camera: Any) -> None:
        self._tx = target_x
        self._ty = target_y
        self._duration = duration
        self._camera = camera
        self._elapsed = 0.0
        self._start_x = 0.0
        self._start_y = 0.0

    def start(self) -> None:
        self._elapsed = 0.0
        if self._camera:
            self._start_x = self._camera.offset.x
            self._start_y = self._camera.offset.y

    def update(self, dt: float) -> bool:
        self._elapsed += dt
        if self._camera:
            t = min(1.0, self._elapsed / self._duration)
            self._camera.offset.x = self._start_x + (self._tx - self._start_x) * t
            self._camera.offset.y = self._start_y + (self._ty - self._start_y) * t
        return self._elapsed >= self._duration


class DialogueAction(CutsceneAction):
    """Show dialogue text box."""

    def __init__(self, text: str, duration: float = 0.0,
                 speaker: str = "") -> None:
        self._text = text
        self._duration = duration
        self._speaker = speaker
        self._elapsed = 0.0
        self._completed = False
        self._font = pygame.font.Font(None, 14)
        self._box_surf = pygame.Surface((settings.INTERNAL_WIDTH - 40, 60), pygame.SRCALPHA)
        self._box_surf.fill((0, 0, 0, 200))
        self._hint_surf = self._font.render("[ENTER]", True, (140, 140, 150))
        self._prev_speaker = None
        self._prev_text = None
        self._speaker_surf = None
        self._text_surf = None

    def start(self) -> None:
        self._elapsed = 0.0
        self._completed = False

    def update(self, dt: float) -> bool:
        im = pygame.key.get_just_pressed()
        if self._duration > 0:
            self._elapsed += dt
            if self._elapsed >= self._duration:
                return True
            return False
        if im and (pygame.K_RETURN in im or pygame.K_SPACE in im):
            return True
        return False

    def draw(self, surface: pygame.Surface) -> None:
        if self._speaker != self._prev_speaker or self._text != self._prev_text:
            self._prev_speaker = self._speaker
            self._prev_text = self._text
            if self._speaker:
                self._speaker_surf = self._font.render(self._speaker, True, (255, 220, 150))
            else:
                self._speaker_surf = None
            self._text_surf = self._font.render(self._text, True, (220, 220, 220))
        surface.blit(self._box_surf, (20, settings.INTERNAL_HEIGHT - 80))
        if self._speaker and self._speaker_surf:
            surface.blit(self._speaker_surf, (30, settings.INTERNAL_HEIGHT - 75))
        if self._text_surf:
            surface.blit(self._text_surf, (30, settings.INTERNAL_HEIGHT - 55))
        surface.blit(self._hint_surf, (settings.INTERNAL_WIDTH - 60, settings.INTERNAL_HEIGHT - 30))


class CutsceneScript:
    """A list of actions that play sequentially."""

    def __init__(self, actions: list[CutsceneAction] | None = None) -> None:
        self._actions: list[CutsceneAction] = actions or []
        self._index: int = 0
        self._active: bool = False
        self._callback: Callable[[], None] | None = None

    def add_action(self, action: CutsceneAction) -> None:
        self._actions.append(action)

    def start(self, callback: Callable[[], None] | None = None) -> None:
        self._index = 0
        self._active = True
        self._callback = callback
        if self._actions:
            self._actions[0].start()

    def update(self, dt: float) -> None:
        if not self._active or self._index >= len(self._actions):
            return
        if self._actions[self._index].update(dt):
            self._index += 1
            if self._index < len(self._actions):
                self._actions[self._index].start()
            else:
                self._active = False
                if self._callback:
                    self._callback()

    def draw(self, surface: pygame.Surface) -> None:
        if not self._active:
            return
        for i in range(self._index, len(self._actions)):
            self._actions[i].draw(surface)

    @property
    def active(self) -> bool:
        return self._active