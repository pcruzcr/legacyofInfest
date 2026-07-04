from __future__ import annotations
import pygame
from src.engine.core import settings
from src.engine.core.event_bus import emit, subscribe, unsubscribe
from src.engine.core.events import Events
_MAX_LINES = 3
_MAX_CHARS_PER_LINE = 58


class MessageBox:
    """Typewriter message box with auto-dismiss and message queue."""

    def __init__(self) -> None:
        self._text: str = ""
        self._full_text: str = ""
        self._visible: bool = False
        self._char_timer: float = 0.0
        self._display_duration: float = 0.0
        self._elapsed: float = 0.0
        self._chars_per_second: float = 30.0
        self._dismiss_on_confirm: bool = False
        self._queue: list[dict] = []
        self._destroyed: bool = False

        self._font: pygame.font.Font = pygame.font.Font(None, 12)
        if hasattr(settings, "ASSETS_DIR"):
            try:
                self._font = pygame.font.Font(
                    settings.ASSETS_DIR / "fonts" / "game.ttf", 12,
                )
            except Exception:
                self._font = pygame.font.Font(None, 12)

        if hasattr(settings, "ASSETS_DIR"):
            try:
                from src.engine.utils.asset_loader import AssetLoader
                self._arrow = AssetLoader.load_image(
                    settings.ASSETS_DIR / "ui" / "message_arrow.png", size=(5, 7),
                )
            except Exception:
                self._arrow = None
        else:
            self._arrow = None
        self._arrow_timer: float = 0.0

        subscribe(Events.SHOW_MESSAGE, self._on_show_message)
        subscribe(Events.HIDE_MESSAGE, self._on_hide_message)

    def destroy(self) -> None:
        if self._destroyed:
            return
        self._destroyed = True
        unsubscribe(Events.SHOW_MESSAGE, self._on_show_message)
        unsubscribe(Events.HIDE_MESSAGE, self._on_hide_message)

    def _on_show_message(self, **data: object) -> None:
        if self._destroyed:
            return
        if self._visible:
            self._queue.append(dict(data))
            return
        self._show(data)

    def _show(self, data: dict) -> None:
        self._full_text = str(data.get("text", ""))
        self._display_duration = float(data.get("duration", 3.0))
        self._dismiss_on_confirm = self._display_duration <= 0
        self._text = ""
        self._char_timer = 0.0
        self._elapsed = 0.0
        self._arrow_timer = 0.0
        self._visible = True

    def _on_hide_message(self, **data: object) -> None:
        if self._destroyed:
            return
        self._visible = False
        self._text = ""
        self._full_text = ""

    def hide(self) -> None:
        self._visible = False
        self._text = ""
        self._full_text = ""
        emit(Events.HIDE_MESSAGE)

    @staticmethod
    def _wrap_text(text: str) -> list[str]:
        lines: list[str] = []
        current = ""
        for char in text:
            if char == "\n":
                lines.append(current)
                current = ""
                if len(lines) >= _MAX_LINES:
                    break
                continue
            if len(current) >= _MAX_CHARS_PER_LINE:
                lines.append(current)
                current = char if char != " " else ""
                if len(lines) >= _MAX_LINES:
                    break
                continue
            current += char
        if current and len(lines) < _MAX_LINES:
            lines.append(current)
        return lines

    def update(self, dt: float) -> None:
        if not self._visible:
            if self._queue:
                self._show(self._queue.pop(0))
            return

        # Typewriter effect
        if len(self._text) < len(self._full_text):
            self._char_timer += dt
            chars_to_add = int(self._char_timer * self._chars_per_second)
            chars_to_add = min(chars_to_add, len(self._full_text))
            self._text = self._full_text[:chars_to_add]
        elif not self._dismiss_on_confirm:
            self._elapsed += dt
            if self._elapsed >= self._display_duration:
                self._visible = False

        if self._dismiss_on_confirm and len(self._text) >= len(self._full_text):
            self._arrow_timer += dt

    def _render_text(self, text: str) -> pygame.Surface | None:
        lines = self._wrap_text(text)
        if not lines:
            return None
        chunks: list[pygame.Surface] = []
        for line in lines:
            chunks.append(self._font.render(line, True, (255, 255, 255)))
        total_h = sum(s.get_height() for s in chunks) + 2 * (len(chunks) - 1)
        w = max(s.get_width() for s in chunks) if chunks else 0
        if w == 0 or total_h == 0:
            return None
        surf = pygame.Surface((w, total_h))
        surf.set_colorkey((0, 0, 0))
        y = 0
        for s in chunks:
            surf.blit(s, (0, y))
            y += s.get_height() + 2
        return surf

    def draw(self, surface: pygame.Surface) -> None:
        if not self._visible or not self._text:
            return

        box_height = 28
        box_rect = pygame.Rect(0, 0,
                                settings.INTERNAL_WIDTH, box_height)
        overlay = pygame.Surface((box_rect.width, box_rect.height))
        overlay.set_alpha(180)
        overlay.fill((10, 10, 30))
        surface.blit(overlay, box_rect)
        pygame.draw.rect(surface, (200, 180, 100), box_rect, 1)

        # Render wrapped text
        text_surf = self._render_text(self._text)
        if text_surf:
            surface.blit(text_surf, (box_rect.x + 6, box_rect.y + 5))

        # Arrow indicator when waiting for confirm
        if self._dismiss_on_confirm and len(self._text) >= len(self._full_text):
            arrow_visible = int(self._arrow_timer * 4) % 2 == 0
            if arrow_visible and self._arrow:
                ax = box_rect.x + 6
                ay = box_rect.y + box_height - 10
                surface.blit(self._arrow, (ax, ay))

    @property
    def is_visible(self) -> bool:
        return self._visible

    @property
    def is_dismiss_on_confirm(self) -> bool:
        return self._dismiss_on_confirm
