"""
Module: message_box
System: engine.ui
Academic Unit: N/A
Description: Scrolling message box with typewriter effect for tutorial
messages and dialog. Subscribes to SHOW_MESSAGE and HIDE_MESSAGE events.
"""
from __future__ import annotations
import pygame
from src.engine.core import settings
from src.engine.core.event_bus import EventBus


class MessageBox:
    """Typewriter message box with auto-dismiss."""

    def __init__(self) -> None:
        self._text: str = ""
        self._full_text: str = ""
        self._visible: bool = False
        self._char_timer: float = 0.0
        self._display_duration: float = 0.0
        self._elapsed: float = 0.0
        self._chars_per_second: float = 30.0
        self._font = pygame.font.Font(None, 12)

        EventBus.subscribe("SHOW_MESSAGE", self._on_show_message)
        EventBus.subscribe("HIDE_MESSAGE", self._on_hide_message)

    def _on_show_message(self, **data: object) -> None:
        self._full_text = str(data.get("text", ""))
        self._display_duration = float(data.get("duration", 3.0))
        self._text = ""
        self._char_timer = 0.0
        self._elapsed = 0.0
        self._visible = True

    def _on_hide_message(self, **data: object) -> None:
        self._visible = False
        self._text = ""
        self._full_text = ""

    def update(self, dt: float) -> None:
        if not self._visible:
            return

        # Typewriter effect
        if len(self._text) < len(self._full_text):
            self._char_timer += dt
            chars_to_add = int(self._char_timer * self._chars_per_second)
            self._text = self._full_text[:chars_to_add]
        else:
            # Auto-dismiss after duration
            self._elapsed += dt
            if self._elapsed >= self._display_duration:
                self._visible = False

    def draw(self, surface: pygame.Surface) -> None:
        if not self._visible or not self._text:
            return

        # Draw message box at bottom of screen
        box_height = 40
        box_rect = pygame.Rect(4, settings.INTERNAL_HEIGHT - box_height - 4,
                                settings.INTERNAL_WIDTH - 8, box_height)
        pygame.draw.rect(surface, (20, 20, 50), box_rect)
        pygame.draw.rect(surface, (100, 100, 150), box_rect, 1)

        # Render text
        text_surf = self._font.render(self._text, True, (220, 220, 220))
        surface.blit(text_surf, (box_rect.x + 4, box_rect.y + 4))

    @property
    def is_visible(self) -> bool:
        return self._visible
