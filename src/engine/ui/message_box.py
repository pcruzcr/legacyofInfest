"""
Module: message_box
System: engine
Academic Unit: Framework scaffold
Description: A ``MessageBox`` is a modal, text-based UI panel that
stops stage input and displays a line of text until the user presses
A or B.  It is used for story dialogue, sign-posts, and death messages.
"""

from __future__ import annotations

from typing import List

import pygame


class MessageBox:
    """Modal text box that blocks stage input until dismissed.

    Height is fixed at 48 px; width is the full internal width (320 px).
    Renders two lines of up to 36 characters each with a 12×12 pixel
    per-character font.

    See ``22_API_CONTRACTS.md`` §7.2 and ``09_HUD_SPEC.md`` §5.
    """

    ARCADE_CHAR_W: int = 12
    ARCADE_CHAR_H: int = 12
    CHARS_PER_LINE: int = 29
    MAX_LINES: int = 2
    BOX_HEIGHT: int = 48
    INTERNAL_WIDTH: int = 320

    def __init__(self) -> None:
        """Initialise with a visible, empty message."""
        self._text: str = ""
        self._char_index: int = 0
        self._active: bool = True
        self._finished: bool = False
        self._on_exit: str = ""

    def show(
        self,
        text: str,
        on_exit: str,
        on_finish: str = "",
    ) -> None:
        """Show a message with *text*.

        Args:
            text: Full message text (will be split to fit box).
            on_exit: Event name emitted when dismissed.
            on_finish: Optional event name emitted once typewriter
                render completes.
        """
        self._text = text
        self._char_index = 0
        self._active = True
        self._finished = False
        self._on_exit = on_exit

    def dismiss(self) -> None:
        """Dismiss the box and emit the stored exit event."""
        if not self._active or self._finished:
            return
        self._active = False
        self._finished = True
        from src.engine.core.event_bus import EventBus

        EventBus.emit(self._on_exit, source="MessageBox")

    def update(self, dt: float) -> None:
        """Advance the typewriter reveal; nothing else updates here."""
        if not self._active:
            return
        self._char_index += int(dt * 30.0)
        if self._char_index >= len(self._text):
            self._char_index = len(self._text)
            self._finished = True

    def handle_input(self, input_action: str) -> None:
        """Process an input action string.

        Dismisses the box on ``"confirm"``.
        """
        if not self._active:
            return
        if input_action == "confirm":
            self.dismiss()

    def draw(self, surface: pygame.Surface) -> None:
        """Render the message box onto *surface*.

        Uses ``fonts/arcade.png`` if available; falls back to a
        built-in font.
        """
        if not self._active:
            return
        box_y = surface.get_height() - self.BOX_HEIGHT
        bg = pygame.Surface(
            (self.INTERNAL_WIDTH, self.BOX_HEIGHT)
        )
        bg.fill((16, 16, 48, 220))
        bg.set_alpha(220)
        surface.blit(bg, (0, box_y))

        visible = self._text[: self._char_index]
        lines: List[str] = []
        for i in range(0, len(visible), self.CHARS_PER_LINE):
            lines.append(visible[i: i + self.CHARS_PER_LINE])
        lines = lines[: self.MAX_LINES]

        try:
            font = pygame.font.SysFont(
                "Courier New", 11, bold=True
            )
        except Exception:
            font = pygame.font.Font(None, 14)

        y = box_y + 6
        for line in lines:
            rendered = font.render(line, True, (255, 255, 255))
            surface.blit(rendered, (12, y))
            y += self.ARCADE_CHAR_H + 2

    @property
    def active(self) -> bool:
        """``True`` while the message box is on screen."""
        return self._active
