"""
Module: hud
System: engine.ui
Description: Heads-Up Display showing hearts (health), timer, and stage info.
Uses sprite-based hearts from assets/ui/ with font fallback.
"""
from __future__ import annotations
import pygame
from src.engine.core import settings
from src.engine.core.event_bus import EventBus
from src.engine.utils.asset_loader import AssetLoader


def _heart_slot_state(health: float, slot: int) -> str:
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
        self._time_limit: int = 0

        self._portrait_rect = pygame.Rect(2, 2, 32, 32)
        self._hearts_x: int = 38
        self._hearts_y: int = 6
        self._heart_spacing: int = 16
        self._timer_rect = pygame.Rect(272, 2, 46, 12)

        # Load heart sprites (graceful fallback to colored rects)
        self._heart_sprites: dict[str, pygame.Surface] = {}
        for state in ("full", "three_quarter", "half", "quarter", "empty"):
            path = settings.ASSETS_DIR / "ui" / f"heart_{state}.png"
            surf = AssetLoader.load_image(path)
            self._heart_sprites[state] = surf

        self._portrait: pygame.Surface | None = None
        portrait_path = settings.ASSETS_DIR / "ui" / "portrait_normal.png"
        self._portrait = AssetLoader.load_image(portrait_path, size=(32, 32))

        self._font = pygame.font.Font(None, 12)

        EventBus.subscribe("PLAYER_DAMAGED", self._on_player_damaged)
        EventBus.subscribe("PLAYER_HEALED", self._on_player_healed)
        EventBus.subscribe("PLAYER_DIED", self._on_player_died)

    def _on_player_damaged(self, **data: object) -> None:
        amount = float(data.get("amount", 1.0))
        self._health = max(0.0, self._health - amount)

    def _on_player_healed(self, **data: object) -> None:
        amount = float(data.get("amount", 1.0))
        self._health = min(self._max_health, self._health + amount)

    def _on_player_died(self, **data: object) -> None:
        self._health = 0.0
        self._timer_running = False

    def bind_player(self, player: object) -> None:
        self._player_ref = player

    def start_timer(self, time_limit: int = 0) -> None:
        self._timer = 0.0
        self._time_limit = time_limit
        self._timer_running = True

    def stop_timer(self) -> None:
        self._timer_running = False

    def pause_timer(self) -> None:
        self._timer_running = False

    def resume_timer(self) -> None:
        self._timer_running = True

    def update(self, dt: float) -> None:
        if self._timer_running:
            self._timer += dt

    def draw(self, surface: pygame.Surface) -> None:
        self._draw_portrait(surface)
        self._draw_hearts(surface)
        self._draw_timer(surface)

    def _draw_portrait(self, surface: pygame.Surface) -> None:
        if self._portrait:
            surface.blit(self._portrait, self._portrait_rect)
        else:
            pygame.draw.rect(surface, (60, 60, 80), self._portrait_rect)
            pygame.draw.rect(surface, (100, 100, 140), self._portrait_rect, 1)

    def _draw_hearts(self, surface: pygame.Surface) -> None:
        slot_count = int(self._max_health)
        for slot in range(slot_count):
            state = _heart_slot_state(self._health, slot)
            x = self._hearts_x + slot * self._heart_spacing
            y = self._hearts_y

            sprite = self._heart_sprites.get(state)
            if sprite and sprite.get_width() > 1:
                surface.blit(sprite, (x, y))
            else:
                color_map = {
                    "empty": (60, 0, 0),
                    "quarter": (120, 40, 40),
                    "half": (160, 80, 40),
                    "three_quarter": (180, 40, 40),
                    "full": (200, 20, 20),
                }
                color = color_map.get(state, (100, 0, 0))
                rect = pygame.Rect(x, y, 14, 8)
                pygame.draw.rect(surface, color, rect)
                pygame.draw.rect(surface, (255, 50, 50), rect, 1)

    def _draw_timer(self, surface: pygame.Surface) -> None:
        if not self._timer_running:
            return
        total_seconds = int(self._timer)
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        time_str = f"{minutes}:{seconds:02d}"
        text = self._font.render(time_str, True, (200, 200, 200))
        tx = self._timer_rect.x + (self._timer_rect.width - text.get_width()) // 2
        ty = self._timer_rect.y + (self._timer_rect.height - text.get_height()) // 2
        surface.blit(text, (tx, ty))

    @property
    def current_time(self) -> float:
        return self._timer
