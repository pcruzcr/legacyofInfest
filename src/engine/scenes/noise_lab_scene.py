"""
NoiseLabScene — Interactive Noise & Procedural Generation Laboratory

Teaches Unit V/VIII concepts:
  - Value noise vs Perlin noise
  - Octaves, persistence, lacunarity
  - Seed-based generation
  - Procedural texture preview

Controls:
  LEFT/RIGHT  — adjust parameter value
  UP/DOWN     — cycle parameter to adjust
  SPACE       — randomize seed
  TAB         — cycle noise type
  R           — reset
  ESC         — back to demo menu
"""
from __future__ import annotations

from typing import TYPE_CHECKING

import math
import random
import pygame
import numpy as np

from src.engine.core import settings
from src.engine.input.action_map import Action
from src.engine.scene.base_scene import BaseScene
from src.engine.scenes.demo_common import (
    BOTTOM_BAR_Y,
    COLOR_BG, COLOR_TEXT, COLOR_HIGHLIGHT, COLOR_ACCENT,
    FONT_SMALL, FONT_MEDIUM,
    draw_top_bar, draw_bottom_bar,
    save_png,
)
from src.engine.utils.asset_loader import AssetLoader

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext


MODE_NAMES = ["VALUE NOISE", "PERLIN NOISE", "FRACTAL NOISE"]

PARAM_NAMES = ["Octaves", "Persistence", "Lacunarity", "Scale", "Seed"]


class NoiseLabScene(BaseScene):
    def __init__(self, context: GameContext) -> None:
        super().__init__(context)
        self._mode: int = 0
        self._param_idx: int = 0
        self._octaves: int = 4
        self._persistence: float = 0.5
        self._lacunarity: float = 2.0
        self._scale: float = 0.05
        self._seed: int = 42
        self._cached_noise: np.ndarray | None = None
        self._param_changed: bool = True

        self._font_small = AssetLoader.load_font(
            settings.ASSETS_DIR / "fonts" / "game.ttf", FONT_SMALL)
        self._font_medium = AssetLoader.load_font(
            settings.ASSETS_DIR / "fonts" / "game.ttf", FONT_MEDIUM)

        self._status_msg: str = ""
        self._status_timer: float = 0.0

        self._grad_table: list[tuple[float, float]] = self._build_grad_table(256)

    @staticmethod
    def _build_grad_table(size: int) -> list[tuple[float, float]]:
        rng = random.Random(0)
        table = []
        for _ in range(size):
            angle = rng.random() * math.pi * 2
            table.append((math.cos(angle), math.sin(angle)))
        return table

    def on_enter(self) -> None:
        self._mode = 0
        self._param_changed = True

    def on_exit(self) -> None:
        pass

    def update(self, dt: float) -> None:
        im = self.input
        if im is None:
            return

        if self._status_timer > 0:
            self._status_timer -= dt
            if self._status_timer <= 0:
                self._status_msg = ""

        # TAB — cycle noise type
        if im.is_raw_key_pressed(pygame.K_TAB):
            self._mode = (self._mode + 1) % len(MODE_NAMES)
            self._param_changed = True
            self._status_msg = f"Noise: {MODE_NAMES[self._mode]}"
            self._status_timer = 1.5

        # SPACE — randomize seed
        if im.is_raw_key_pressed(pygame.K_SPACE):
            self._seed = random.randint(0, 9999)
            self._param_changed = True
            self._status_msg = f"Seed: {self._seed}"
            self._status_timer = 1.0

        # UP/DOWN — cycle parameter
        if im.is_raw_key_pressed(pygame.K_UP):
            self._param_idx = (self._param_idx + 1) % len(PARAM_NAMES)
            self._status_msg = f"Param: {PARAM_NAMES[self._param_idx]}"
            self._status_timer = 1.0
        if im.is_raw_key_pressed(pygame.K_DOWN):
            self._param_idx = (self._param_idx - 1) % len(PARAM_NAMES)
            self._status_msg = f"Param: {PARAM_NAMES[self._param_idx]}"
            self._status_timer = 1.0

        # LEFT/RIGHT — adjust parameter
        if im.is_raw_key_pressed(pygame.K_LEFT):
            self._adjust_param(-1)
        if im.is_raw_key_pressed(pygame.K_RIGHT):
            self._adjust_param(1)

        # R — reset
        if im.is_raw_key_pressed(pygame.K_r):
            self._octaves = 4
            self._persistence = 0.5
            self._lacunarity = 2.0
            self._scale = 0.05
            self._seed = 42
            self._param_changed = True
            self._status_msg = "Reset defaults"
            self._status_timer = 1.0

        # S — save screenshot
        if im.is_raw_key_pressed(pygame.K_s):
            ss = pygame.Surface((settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT))
            self.draw(ss)
            path = save_png("noise", MODE_NAMES[self._mode].lower(), ss)
            self._status_msg = f"Saved: {path.split('/')[-1].split(chr(92))[-1]}"
            self._status_timer = 2.0

        # ESC — back
        if im.is_action_just_pressed(Action.CANCEL):
            from src.engine.scenes.demo_menu_scene import DemoMenuScene
            self.context.scene_manager.replace(DemoMenuScene(self.context))
            return

        if self._param_changed:
            self._generate_noise()

    def _adjust_param(self, direction: int) -> None:
        self._param_changed = True
        if self._param_idx == 0:  # Octaves
            self._octaves = max(1, min(8, self._octaves + direction))
        elif self._param_idx == 1:  # Persistence
            self._persistence = round(max(0.0, min(1.0, self._persistence + direction * 0.05)), 2)
        elif self._param_idx == 2:  # Lacunarity
            self._lacunarity = round(max(1.0, min(8.0, self._lacunarity + direction * 0.25)), 2)
        elif self._param_idx == 3:  # Scale
            self._scale = round(max(0.005, min(0.5, self._scale + direction * 0.005)), 3)
        elif self._param_idx == 4:  # Seed
            self._seed = max(0, min(9999, self._seed + direction))
        self._status_msg = f"{PARAM_NAMES[self._param_idx]}: {self._get_param_value()}"
        self._status_timer = 1.0

    def _get_param_value(self) -> str:
        if self._param_idx == 0:
            return str(self._octaves)
        elif self._param_idx == 1:
            return f"{self._persistence:.2f}"
        elif self._param_idx == 2:
            return f"{self._lacunarity:.2f}"
        elif self._param_idx == 3:
            return f"{self._scale:.3f}"
        elif self._param_idx == 4:
            return str(self._seed)
        return ""

    def _generate_noise(self) -> None:
        w, h = 320, 180
        noise_map: np.ndarray = np.zeros((h, w), dtype=np.float32)
        rng = np.random.RandomState(self._seed)

        if self._mode == 0:  # VALUE NOISE
            grid_w = max(2, int(1.0 / (self._scale * 2)))
            grid_h = max(2, int(1.0 / (self._scale * 2)))
            grid = rng.rand(grid_h + 1, grid_w + 1).astype(np.float32)
            for y in range(h):
                for x in range(w):
                    fx = x * self._scale
                    fy = y * self._scale
                    gx = int(fx * grid_w)
                    gy = int(fy * grid_h)
                    lx = (fx * grid_w) - gx
                    ly = (fy * grid_h) - gy
                    gx = min(gx, grid_w)
                    gy = min(gy, grid_h)
                    v00 = grid[gy, gx]
                    v01 = grid[gy, min(gx + 1, grid_w)]
                    v10 = grid[min(gy + 1, grid_h), gx]
                    v11 = grid[min(gy + 1, grid_h), min(gx + 1, grid_w)]
                    v0 = v00 + (v10 - v00) * ly
                    v1 = v01 + (v11 - v01) * ly
                    noise_map[y, x] = v0 + (v1 - v0) * lx

        elif self._mode == 1:  # PERLIN NOISE
            grid_w = max(2, int(1.0 / (self._scale * 2)))
            grid_h = max(2, int(1.0 / (self._scale * 2)))
            perm = rng.permutation(256).astype(np.int32)
            perm = np.concatenate([perm, perm])
            for y in range(h):
                for x in range(w):
                    fx = x * self._scale * 10
                    fy = y * self._scale * 10
                    x0 = int(fx)
                    y0 = int(fy)
                    x1 = x0 + 1
                    y1 = y0 + 1
                    sx = fx - x0
                    sy = fy - y0
                    gi00 = perm[(perm[x0 & 255] + y0) & 255] & 7
                    gi01 = perm[(perm[x0 & 255] + y1) & 255] & 7
                    gi10 = perm[(perm[x1 & 255] + y0) & 255] & 7
                    gi11 = perm[(perm[x1 & 255] + y1) & 255] & 7
                    n00 = self._dot_grad(gi00, sx, sy)
                    n01 = self._dot_grad(gi01, sx, sy - 1.0)
                    n10 = self._dot_grad(gi10, sx - 1.0, sy)
                    n11 = self._dot_grad(gi11, sx - 1.0, sy - 1.0)
                    u = sx * sx * (3.0 - 2.0 * sx)
                    v = sy * sy * (3.0 - 2.0 * sy)
                    nx0 = n00 + (n10 - n00) * u
                    nx1 = n01 + (n11 - n01) * u
                    noise_map[y, x] = nx0 + (nx1 - nx0) * v

        else:  # FRACTAL NOISE (mode 2)
            amp = 1.0
            freq = self._scale
            max_amp = 0.0
            for _ in range(self._octaves):
                max_amp += amp
                amp *= self._persistence
            amp = 1.0
            for o in range(self._octaves):
                grid_w = max(2, int(1.0 / (freq * 2)))
                grid_h = max(2, int(1.0 / (freq * 2)))
                grid = rng.rand(grid_h + 1, grid_w + 1).astype(np.float32) * 2.0 - 1.0
                for y in range(h):
                    for x in range(w):
                        fx = x * freq
                        fy = y * freq
                        gx = int(fx * grid_w)
                        gy = int(fy * grid_h)
                        lx = (fx * grid_w) - gx
                        ly = (fy * grid_h) - gy
                        gx = min(gx, grid_w)
                        gy = min(gy, grid_h)
                        v00 = grid[gy, gx]
                        v01 = grid[gy, min(gx + 1, grid_w)]
                        v10 = grid[min(gy + 1, grid_h), gx]
                        v11 = grid[min(gy + 1, grid_h), min(gx + 1, grid_w)]
                        v0 = v00 + (v10 - v00) * ly
                        v1 = v01 + (v11 - v01) * ly
                        val = v0 + (v1 - v0) * lx
                        noise_map[y, x] += val * amp
                amp *= self._persistence
                freq *= self._lacunarity
            noise_map /= max_amp
            noise_map = (noise_map + 1.0) * 0.5

        noise_map = np.clip(noise_map, 0.0, 1.0)
        self._cached_noise = noise_map

    def _dot_grad(self, gi: int, x: float, y: float) -> float:
        grads = [(1, 0), (-1, 0), (0, 1), (0, -1),
                 (1, 1), (-1, 1), (1, -1), (-1, -1)]
        gx, gy = grads[gi % 8]
        return gx * x + gy * y

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(COLOR_BG)
        draw_top_bar(surface, "NOISE LAB", "UNIT V/VIII")

        label = self._font_medium.render(f"  {MODE_NAMES[self._mode]}  ", True, COLOR_HIGHLIGHT)
        surface.blit(label, (4, 24))

        # Noise map
        if self._cached_noise is not None:
            noise_8: np.ndarray = (self._cached_noise * 255).astype(np.uint8)
            noise_rgb = np.stack([noise_8] * 3, axis=-1)
            noise_surf = pygame.surfarray.make_surface(noise_rgb.transpose(1, 0, 2))
            noise_surf = pygame.transform.scale(noise_surf, (320, 180))
            surface.blit(noise_surf, (0, 40))
            pygame.draw.rect(surface, COLOR_ACCENT, (0, 40, 320, 180), 1)

        # Parameter panel
        param_y = 228
        for i, pname in enumerate(PARAM_NAMES):
            selected = i == self._param_idx
            prefix = ">" if selected else " "
            val = self._get_param_value_for(i)
            color = COLOR_HIGHLIGHT if selected else COLOR_TEXT
            txt = self._font_small.render(f"  {prefix} {pname}: {val}", True, color)
            surface.blit(txt, (4, param_y + i * 14))

        # Controls
        controls = ("  [UP/DOWN] param  |  [LEFT/RIGHT] value  |  "
                    "[SPACE] random seed  |  [TAB] mode  |  [R] reset")
        ct = self._font_small.render(controls, True, COLOR_TEXT)
        surface.blit(ct, (4, param_y + len(PARAM_NAMES) * 14 + 4))

        if self._status_msg:
            st = self._font_small.render(self._status_msg, True, COLOR_HIGHLIGHT)
            surface.blit(st, (4, BOTTOM_BAR_Y - 16))

        draw_bottom_bar(surface, f"MODE: {MODE_NAMES[self._mode]}")

    def _get_param_value_for(self, idx: int) -> str:
        if idx == 0:
            return str(self._octaves)
        elif idx == 1:
            return f"{self._persistence:.2f}"
        elif idx == 2:
            return f"{self._lacunarity:.2f}"
        elif idx == 3:
            return f"{self._scale:.3f}"
        elif idx == 4:
            return str(self._seed)
        return ""

