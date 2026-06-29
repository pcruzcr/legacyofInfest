"""
Module: hud
System: engine.ui
Academic Unit: N/A
Description: Heads-Up Display showing hearts (health), timer, and stage info.
Subscribes to PLAYER_DAMAGED, PLAYER_HEALED, PLAYER_DIED via EventBus.
"""
from __future__ import annotations
import pygame
from src.engine.core import settings
from src.engine.core.event_bus import EventBus
from src.engine.utils.math_utils import clamp


def _heart_slot_state(health: float, slot: int) -> str:
    """Pure function: returns 'full', 'three_quarter', 'half', 'quarter', or 'empty'
    based on the health value for the given heart slot."""
    v = max(0.0, min(1.0, health - slot))
    if v >= 1.0:
        return "full"
    if v >= 0.75:
        return "three_quarter"
    if v >= 0.50:
        return "half"
    if v >= 0.25:
        return "quarter"
    return "empty"


class HUD:
    """Heads-up display: hearts, timer, portrait."""

    def __init__(self) -> None:
        self._health: float = settings.PLAYER_MAX_HEALTH
        self._max_health: float = settings.PLAYER_MAX_HEALTH
        self._timer: float = 0.0
        self._timer_running: bool = False
        self._time_limit: int = 0  # 0 = ascending timer, >0 = countdown

        # Layout constants (from docs/09_HUD_SPEC.md §2.1)
        self._portrait_rect = pygame.Rect(2, 2, 34, 34)
        self._hearts_x: int = 38
        self._hearts_y: int = 6
        self._heart_spacing: int = 16
        self._heart_size: tuple[int, int] = (14, 8)
        self._timer_rect = pygame.Rect(272, 2, 46, 12)

        # Subscribe to events
        EventBus.subscribe("PLAYER_DAMAGED", self._on_player_damaged)
        EventBus.subscribe("PLAYER_HEALED", self._on_player_healed)

    def _on_player_damaged(self, **data: object) -> None:
        amount = float(data.get("amount", 1.0))
        self._health = max(0.0, self._health - amount)

    def _on_player_healed(self, **data: object) -> None:
        amount = float(data.get("amount", 1.0))
        self._health = min(self._max_health, self._health + amount)

    def bind_player(self, player: object) -> None:
        """Link to a player entity to read health. Optional — HUD works
        standalone via EventBus subscription."""
        pass

    def start_timer(self, time_limit: int = 0) -> None:
        """Start the timer. time_limit=0 means ascending timer."""
        self._timer = 0.0
        self._time_limit = time_limit
        self._timer_running = True

    def stop_timer(self) -> None:
        self._timer_running = False

    def update(self, dt: float) -> None:
        if self._timer_running:
            self._timer += dt

    def draw(self, surface: pygame.Surface) -> None:
        self._draw_hearts(surface)
        self._draw_timer(surface)

    def _draw_hearts(self, surface: pygame.Surface) -> None:
        """Draw heart containers."""
        slot_count = int(self._max_health)
        for slot in range(slot_count):
            state = _heart_slot_state(self._health, slot)
            x = self._hearts_x + slot * self._heart_spacing
            y = self._hearts_y

            if state == "empty":
                color = (100, 0, 0)
                border = (80, 0, 0)
            else:
                color = (200, 0, 0)
                border = (255, 50, 50)

            rect = pygame.Rect(x, y, self._heart_size[0], self._heart_size[1])
            pygame.draw.rect(surface, color, rect)
            pygame.draw.rect(surface, border, rect, 1)

    def _draw_timer(self, surface: pygame.Surface) -> None:
        """Draw the timer display."""
        if not self._timer_running:
            return

        total_seconds = int(self._timer)
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        time_str = f"{minutes}:{seconds:02d}"

        font = pygame.font.Font(None, 12)
        text = font.render(time_str, True, (200, 200, 200))
        tx = self._timer_rect.x + (self._timer_rect.width - text.get_width()) // 2
        ty = self._timer_rect.y + (self._timer_rect.height - text.get_height()) // 2
        surface.blit(text, (tx, ty))

    @property
    def current_time(self) -> float:
        return self._timer
