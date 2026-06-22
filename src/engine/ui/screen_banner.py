"""
Module: screen_banner
System: engine
Academic Unit: Framework scaffold
Description: A ``ScreenBanner`` draws a temporary overlay message
centered on the screen for a fixed duration (or until dismissed).
Used for stage-complete banners, death screens, and checkpoints.
"""

from __future__ import annotations

import pygame


class ScreenBanner:
    """Full-screen centered banner with optional auto-dismiss timer.

    Renders text with a built-in font back-up; calls ``on_exit`` when the
    banner is dismissed (either by timer expiry or by user action).
    """

    def __init__(self) -> None:
        """Initialise with an empty, inactive banner."""
        self._text: str = ""
        self._timer: float = 0.0
        self._on_exit: str = ""
        self._active: bool = False

    def show(self, text: str, duration: float, on_exit: str) -> None:
        """Activate a new banner.

        Args:
            text: Centered message.
            duration: Seconds until auto-dismiss (0 = sticky).
            on_exit: Event name emitted on dismiss.
        """
        self._text = text
        self._timer = duration
        self._on_exit = on_exit
        self._active = True

    def dismiss(self) -> None:
        """Dismiss immediately and emit the exit event."""
        if not self._active:
            return
        self._active = False
        from src.engine.core.event_bus import EventBus

        EventBus.emit(self._on_exit, source="ScreenBanner")

    def update(self, dt: float) -> None:
        """Count down the timer; auto-dismiss when it reaches zero."""
        if not self._active or self._timer <= 0:
            return
        self._timer -= dt
        if self._timer <= 0:
            self.dismiss()

    def draw(self, surface: pygame.Surface) -> None:
        """Draw a centered text overlay with a dark translucent back-drop."""
        if not self._active:
            return
        w, h = surface.get_size()
        try:
            font = pygame.font.SysFont("Arial", 16, bold=True)
        except Exception:
            font = pygame.font.Font(None, 18)

        text_surf = font.render(self._text, True, (255, 255, 255))
        rect = text_surf.get_rect(center=(w // 2, h // 2))
        pad = 8
        bg_rect = rect.inflate(pad * 2, pad * 2)
        bg = pygame.Surface((bg_rect.width, bg_rect.height))
        bg.fill((0, 0, 0, 180))
        bg.set_alpha(180)
        surface.blit(bg, bg_rect.topleft)
        surface.blit(text_surf, rect)

    @property
    def active(self) -> bool:
        """``True`` while the banner is visible."""
        return self._active
