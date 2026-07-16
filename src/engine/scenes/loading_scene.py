from __future__ import annotations

import logging
import threading
from typing import TYPE_CHECKING, Callable

import pygame

from src.engine.core import settings
from src.engine.scene.base_scene import BaseScene

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext


class LoadTask:
    def __init__(self, name: str, fn: Callable[[], None], weight: float = 1.0) -> None:
        self.name = name
        self.fn = fn
        self.weight = weight
        self.done = False


class LoadingScene(BaseScene):
    """Loading screen with progress bar for async asset loading."""

    def __init__(
        self,
        context: GameContext,
        next_scene: BaseScene | None = None,
        tasks: list[LoadTask] | None = None,
    ) -> None:
        super().__init__(context)
        self._next_scene = next_scene
        self._tasks = tasks or []
        self._progress: float = 0.0
        self._total_weight: float = max(sum(t.weight for t in self._tasks), 0.01)
        self._current_task_name: str = ""
        self._loading_done: bool = False
        self._thread: threading.Thread | None = None
        self._is_loading: bool = False
        self._startup_alpha: float = 0.0
        self._startup_done: bool = False
        self._fade_out: float = 0.0
        self._fading_out: bool = False
        self._fade_surf: pygame.Surface | None = None
        self._font_info = pygame.font.Font(None, 14)
        self._font_title = pygame.font.Font(None, 20)

    def set_next_scene(self, scene: BaseScene) -> None:
        self._next_scene = scene

    def add_task(self, task: LoadTask) -> None:
        self._tasks.append(task)
        self._total_weight = max(sum(t.weight for t in self._tasks), 0.01)

    def _load_worker(self) -> None:
        completed = 0.0
        for task in self._tasks:
            self._current_task_name = task.name
            try:
                task.fn()
            except Exception as e:
                logging.warning("loading_scene: task '%s' failed: %s", task.name, e)
                self._current_task_name = f"Error: {e}"
            task.done = True
            completed += task.weight
            self._progress = completed / self._total_weight
        self._loading_done = True

    def on_enter(self) -> None:
        self._progress = 0.0
        self._loading_done = False
        self._startup_alpha = 0.0
        self._startup_done = False
        self._fade_out = 1.0
        self._fading_out = False
        if self._tasks:
            self._is_loading = True
            self._thread = threading.Thread(target=self._load_worker, daemon=True)
            self._thread.start()
        else:
            self._loading_done = True

    def update(self, dt: float) -> None:
        if not self._startup_done:
            self._startup_alpha = min(1.0, self._startup_alpha + dt * 2.0)
            if self._startup_alpha >= 1.0:
                self._startup_done = True
            return

        if self._loading_done and not self._fading_out:
            self._fading_out = True

        if self._fading_out:
            self._fade_out = max(0.0, self._fade_out - dt * 1.5)
            if self._fade_out <= 0.0 and self._next_scene is not None:
                self.context.scene_manager.replace(self._next_scene)

    def draw(self, surface: pygame.Surface) -> None:
        w, h = settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT
        surface.fill((10, 10, 20))

        # Loading bar
        bar_w = 200
        bar_h = 16
        bx = (w - bar_w) // 2
        by = h // 2

        bg_rect = pygame.Rect(bx, by, bar_w, bar_h)
        pygame.draw.rect(surface, (30, 30, 50), bg_rect)
        pygame.draw.rect(surface, (60, 60, 80), bg_rect, 1)

        if self._progress > 0:
            fill_w = int(bar_w * self._progress)
            for i in range(bar_h):
                t = i / bar_h
                r = int(80 + t * 60)
                g = int(120 + t * 80)
                b = int(200 + t * 55)
                pygame.draw.line(surface, (r, g, b), (bx, by + i), (bx + fill_w, by + i))

        if self._current_task_name:
            label = self._font_info.render(f"Loading {self._current_task_name}...", True, (150, 150, 170))
        else:
            label = self._font_info.render("Loading...", True, (150, 150, 170))
        surface.blit(label, (bx, by - 18))

        pct = self._font_info.render(f"{int(self._progress * 100)}%", True, (200, 200, 220))
        px = bx + bar_w + 8
        surface.blit(pct, (px, by + 1))

        # Title
        title = self._font_title.render("LEGACY OF INFEST", True, (180, 180, 220))
        surface.blit(title, ((w - title.get_width()) // 2, by - 50))

        # Fade overlay
        if self._fade_surf is None or self._fade_surf.get_size() != (w, h):
            self._fade_surf = pygame.Surface((w, h))
        if not self._startup_done:
            self._fade_surf.set_alpha(int((1.0 - self._startup_alpha) * 255))
            self._fade_surf.fill((0, 0, 0))
            surface.blit(self._fade_surf, (0, 0))
        elif self._fading_out:
            self._fade_surf.set_alpha(int(self._fade_out * 255))
            self._fade_surf.fill((0, 0, 0))
            surface.blit(self._fade_surf, (0, 0))
