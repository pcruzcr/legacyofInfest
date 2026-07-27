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

import random
from typing import TYPE_CHECKING

import numpy as np
import pygame

from src.engine.core import settings
from src.engine.input.action_map import Action
from src.engine.scene.base_scene import BaseScene
from src.engine.scenes.demo_common import (
    BOTTOM_BAR_Y,
    COLOR_ACCENT,
    COLOR_BG,
    COLOR_HIGHLIGHT,
    COLOR_TEXT,
    FONT_MEDIUM,
    FONT_SMALL,
    draw_bottom_bar,
    draw_top_bar,
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

        # AUD-076: aquí había una `_grad_table` de 256 gradientes construida en
        # cada `__init__` y que **nadie leía nunca**. Peor que el coste: un
        # estudiante que abriera este archivo para entender Perlin habría
        # estudiado una tabla que no participa en el resultado. Los gradientes
        # reales son los ocho de `_GRADS`.

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

    # Tabla de gradientes de Perlin. Ocho direcciones: los cuatro ejes y las
    # cuatro diagonales. Es la tabla clásica de Perlin en 2D.
    _GRADS = np.array(
        [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, 1), (1, -1), (-1, -1)],
        dtype=np.float32,
    )

    NOISE_W = 320
    NOISE_H = 180

    def _generate_noise(self) -> None:
        """Rellena `_cached_noise` con el mapa del modo activo.

        AUD-073/074 — por qué esto es vectorizado
        -----------------------------------------
        La versión anterior recorría los 320x180 = 57.600 píxeles con dos
        bucles `for` de Python y tardaba **295 ms** por mapa. Como
        `_param_changed` nunca volvía a `False` (AUD-073), esto se ejecutaba en
        *cada fotograma*: el laboratorio de ruido corría a 3,4 FPS desde el
        instante en que se abría. Medido, no supuesto.

        Ahora cada modo se calcula con operaciones de numpy sobre la rejilla
        completa. La aritmética es la misma —interpolación bilineal sobre una
        rejilla de valores, y producto punto contra gradientes en el caso de
        Perlin—, sólo que expresada como álgebra de matrices en vez de píxel a
        píxel. `tests/test_noise_lab.py` compara el resultado contra una copia
        literal del código escalar antiguo, así que la equivalencia numérica
        está probada, no prometida.
        """
        w, h = self.NOISE_W, self.NOISE_H
        rng = np.random.RandomState(self._seed)

        if self._mode == 0:  # RUIDO DE VALOR
            noise_map = self._value_noise(w, h, self._scale, rng, signed=False)

        elif self._mode == 1:  # RUIDO PERLIN
            noise_map = self._perlin_noise(w, h, self._scale, rng)
            # AUD-075: Perlin vive en [-1, 1]. El código anterior lo recortaba
            # directamente contra [0, 1], lo que convertía la mitad negativa de
            # la imagen en negro plano. Se remapea, igual que ya hacía el modo
            # fractal.
            noise_map = (noise_map + 1.0) * 0.5

        else:  # RUIDO FRACTAL (modo 2)
            noise_map = np.zeros((h, w), dtype=np.float32)
            amp = 1.0
            freq = self._scale
            max_amp = 0.0
            for _ in range(self._octaves):
                max_amp += amp
                amp *= self._persistence
            amp = 1.0
            for _o in range(self._octaves):
                noise_map += self._value_noise(w, h, freq, rng, signed=True) * amp
                amp *= self._persistence
                freq *= self._lacunarity
            noise_map /= max_amp
            noise_map = (noise_map + 1.0) * 0.5

        self._cached_noise = np.clip(noise_map, 0.0, 1.0)
        # AUD-073: apagar la bandera. Sin esta línea el mapa se regeneraba en
        # cada `update()` aunque nadie hubiera tocado un parámetro.
        self._param_changed = False

    @staticmethod
    def _lattice(n: int, scale: float, cells: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Índices de celda y peso de interpolación para un eje.

        Devuelve `(i0, i1, t)`: la celda de la izquierda, la de la derecha y
        cuánto hemos avanzado entre las dos, con `t` en [0, 1).
        """
        u = np.arange(n, dtype=np.float32) * np.float32(scale) * cells
        i_raw = u.astype(np.int32)
        t = u - i_raw
        i0 = np.minimum(i_raw, cells)
        i1 = np.minimum(i_raw + 1, cells)
        return i0, i1, t

    @classmethod
    def _value_noise(
        cls, w: int, h: int, scale: float, rng: np.random.RandomState, *, signed: bool,
    ) -> np.ndarray:
        """Ruido de valor: rejilla aleatoria + interpolación bilineal."""
        cells = max(2, int(1.0 / (scale * 2)))
        grid = rng.rand(cells + 1, cells + 1).astype(np.float32)
        if signed:
            grid = grid * 2.0 - 1.0

        gx0, gx1, lx = cls._lattice(w, scale, cells)
        gy0, gy1, ly = cls._lattice(h, scale, cells)

        # Las cuatro esquinas de la celda que contiene a cada píxel.
        v00 = grid[gy0[:, None], gx0[None, :]]
        v01 = grid[gy0[:, None], gx1[None, :]]
        v10 = grid[gy1[:, None], gx0[None, :]]
        v11 = grid[gy1[:, None], gx1[None, :]]

        ly_col = ly[:, None]
        lx_row = lx[None, :]
        v0 = v00 + (v10 - v00) * ly_col
        v1 = v01 + (v11 - v01) * ly_col
        return (v0 + (v1 - v0) * lx_row).astype(np.float32)

    @classmethod
    def _perlin_noise(
        cls, w: int, h: int, scale: float, rng: np.random.RandomState,
    ) -> np.ndarray:
        """Perlin: gradientes por vértice y suavizado con 3t^2 - 2t^3."""
        perm = rng.permutation(256).astype(np.int32)

        fx = np.arange(w, dtype=np.float32) * np.float32(scale * 10)
        fy = np.arange(h, dtype=np.float32) * np.float32(scale * 10)
        x0 = fx.astype(np.int32)
        y0 = fy.astype(np.int32)
        sx = (fx - x0)[None, :]
        sy = (fy - y0)[:, None]

        px0 = perm[x0 & 255]
        px1 = perm[(x0 + 1) & 255]
        # Índice de gradiente para cada vértice de la celda.
        gi00 = perm[(px0[None, :] + y0[:, None]) & 255] & 7
        gi01 = perm[(px0[None, :] + y0[:, None] + 1) & 255] & 7
        gi10 = perm[(px1[None, :] + y0[:, None]) & 255] & 7
        gi11 = perm[(px1[None, :] + y0[:, None] + 1) & 255] & 7

        def dot(gi: np.ndarray, dx: np.ndarray, dy: np.ndarray) -> np.ndarray:
            g = cls._GRADS[gi]
            return g[..., 0] * dx + g[..., 1] * dy

        n00 = dot(gi00, sx, sy)
        n01 = dot(gi01, sx, sy - 1.0)
        n10 = dot(gi10, sx - 1.0, sy)
        n11 = dot(gi11, sx - 1.0, sy - 1.0)

        u = sx * sx * (3.0 - 2.0 * sx)
        v = sy * sy * (3.0 - 2.0 * sy)
        nx0 = n00 + (n10 - n00) * u
        nx1 = n01 + (n11 - n01) * u
        return (nx0 + (nx1 - nx0) * v).astype(np.float32)

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

