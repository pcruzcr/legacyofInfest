"""
VectorLabScene — Interactive Vector Mathematics Laboratory

Teaches Unit II concepts:
  - Vector arithmetic (addition, subtraction, scaling)
  - Vector normalization (unit vectors)
  - Dot product and angle between vectors
  - Distance calculation
  - Pursuit movement using normalized vectors

Controls:
  arrows      — move Player
  WASD        — move Enemy target
  TAB         — cycle visualization mode
  N           — toggle normalized vector display
  R           — reset positions
  ESC         — back to demo menu
"""
from __future__ import annotations

from typing import TYPE_CHECKING

import math
import pygame

from src.engine.core import settings
from src.engine.input.action_map import Action
from src.engine.scene.base_scene import BaseScene
from src.engine.scenes.demo_common import (
    COLOR_BG, COLOR_TEXT, COLOR_HIGHLIGHT, COLOR_ACCENT,
    FONT_SMALL, FONT_MEDIUM,
    draw_top_bar, draw_bottom_bar,
)
from src.engine.utils.asset_loader import AssetLoader
from src.engine.utils.math_utils import vec2_dot

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext


MODE_NAMES = ["FREE MOVE", "CHASE (normalized)", "ORBIT (dot product)", "DISTANCE CHECK"]

DOT_COLORS = {
    "player": (80, 200, 120),
    "enemy": (200, 80, 80),
    "vector": (255, 220, 80),
    "normalized": (100, 180, 255),
    "projection": (200, 120, 255),
}


class VectorLabScene(BaseScene):
    def __init__(self, context: GameContext) -> None:
        super().__init__(context)
        self._mode: int = 0
        self._player: pygame.Vector2 = pygame.Vector2(80.0, 120.0)
        self._enemy: pygame.Vector2 = pygame.Vector2(220.0, 100.0)
        self._speed: float = 100.0
        self._show_normalized: bool = False

        self._font_small = AssetLoader.load_font(
            settings.ASSETS_DIR / "fonts" / "game.ttf", FONT_SMALL)
        self._font_medium = AssetLoader.load_font(
            settings.ASSETS_DIR / "fonts" / "game.ttf", FONT_MEDIUM)

        self._status_msg: str = ""
        self._status_timer: float = 0.0

    def on_enter(self) -> None:
        self._mode = 0
        self._show_normalized = False

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

        # TAB — cycle modes
        if im.is_raw_key_pressed(pygame.K_TAB):
            self._mode = (self._mode + 1) % len(MODE_NAMES)
            self._status_msg = f"Mode: {MODE_NAMES[self._mode]}"
            self._status_timer = 1.5

        # N — toggle normalized vector
        if im.is_raw_key_pressed(pygame.K_n):
            self._show_normalized = not self._show_normalized

        # R — reset
        if im.is_raw_key_pressed(pygame.K_r):
            self._player = pygame.Vector2(80.0, 120.0)
            self._enemy = pygame.Vector2(220.0, 100.0)

        # ESC — back
        if im.is_action_just_pressed(Action.CANCEL):
            from src.engine.scenes.demo_menu_scene import DemoMenuScene
            self.context.scene_manager.replace(DemoMenuScene(self.context))
            return

        # Player movement (arrows)
        move_dir = pygame.Vector2(0.0, 0.0)
        if im.is_action_held(Action.MOVE_LEFT):
            move_dir.x -= 1.0
        if im.is_action_held(Action.MOVE_RIGHT):
            move_dir.x += 1.0
        if im.is_action_held(Action.JUMP):
            move_dir.y -= 1.0
        if im.is_action_held(Action.CROUCH):
            move_dir.y += 1.0

        self._player += move_dir * self._speed * dt
        self._player.x = max(10, min(settings.INTERNAL_WIDTH - 10, self._player.x))
        self._player.y = max(10, min(settings.INTERNAL_HEIGHT - 40, self._player.y))

        # Enemy movement (WASD via raw keys)
        enemy_dir = pygame.Vector2(0.0, 0.0)
        if im.is_raw_key_pressed(pygame.K_w):
            enemy_dir.y -= 1.0
        if im.is_raw_key_pressed(pygame.K_s):
            enemy_dir.y += 1.0
        if im.is_raw_key_pressed(pygame.K_a):
            enemy_dir.x -= 1.0
        if im.is_raw_key_pressed(pygame.K_d):
            enemy_dir.x += 1.0

        # Mode-specific behavior
        if self._mode == 1:
            # CHASE: enemy moves toward player using normalized vector
            to_player = self._player - self._enemy
            dist = to_player.length()
            if dist > 5.0:
                to_player.normalize_ip()
                self._enemy += to_player * self._speed * 0.6 * dt
            else:
                self._enemy += enemy_dir * self._speed * dt
        elif self._mode == 2:
            # ORBIT: enemy orbits around player (manually controlled)
            self._enemy += enemy_dir * self._speed * dt
        else:
            self._enemy += enemy_dir * self._speed * dt

        self._enemy.x = max(10, min(settings.INTERNAL_WIDTH - 10, self._enemy.x))
        self._enemy.y = max(10, min(settings.INTERNAL_HEIGHT - 40, self._enemy.y))

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(COLOR_BG)
        draw_top_bar(surface, "VECTOR LAB", "UNIT II")

        # Draw grid
        for x in range(0, settings.INTERNAL_WIDTH, 32):
            pygame.draw.line(surface, (20, 20, 40), (x, 0), (x, settings.INTERNAL_HEIGHT), 1)
        for y in range(0, settings.INTERNAL_HEIGHT, 32):
            pygame.draw.line(surface, (20, 20, 40), (0, y), (settings.INTERNAL_WIDTH, y), 1)

        # Draw vector from enemy to player
        pi = (int(self._player.x), int(self._player.y))
        ei = (int(self._enemy.x), int(self._enemy.y))

        # Vector AB (from enemy to player)
        vec_ab = self._player - self._enemy
        vec_len = vec_ab.length()
        vx, vy = vec_ab.x, vec_ab.y

        # Draw vector arrow
        if vec_len > 1.0:
            # Main vector line
            pygame.draw.line(surface, DOT_COLORS["vector"],
                             ei, pi, 2)
            # Arrow head
            if vec_len > 10.0:
                angle_rad = math.radians(-30)
                cos_a, sin_a = math.cos(angle_rad), math.sin(angle_rad)
                n = vec_ab.copy().normalize()
                ax1 = pi[0] + int((-n.x * cos_a - n.y * sin_a) * 8)
                ay1 = pi[1] + int((-n.y * cos_a + n.x * sin_a) * 8)
                rad2 = math.radians(30)
                cos_b, sin_b = math.cos(rad2), math.sin(rad2)
                ax2 = pi[0] + int((-n.x * cos_b - n.y * sin_b) * 8)
                ay2 = pi[1] + int((-n.y * cos_b + n.x * sin_b) * 8)
                pygame.draw.line(surface, DOT_COLORS["vector"], pi, (ax1, ay1), 2)
                pygame.draw.line(surface, DOT_COLORS["vector"], pi, (ax2, ay2), 2)

            # Normalized vector (if toggled)
            if self._show_normalized and vec_len > 5.0:
                nn = vec_ab.copy().normalize()
                n_end = (ei[0] + int(nn.x * 40), ei[1] + int(nn.y * 40))
                pygame.draw.line(surface, DOT_COLORS["normalized"],
                                 ei, n_end, 3)
                nlabel = self._font_small.render("normalized", True, DOT_COLORS["normalized"])
                surface.blit(nlabel, (n_end[0] + 4, n_end[1] - 8))

        # Draw Player and Enemy
        pygame.draw.circle(surface, DOT_COLORS["player"], pi, 8)
        pygame.draw.circle(surface, (255, 255, 255), pi, 8, 1)
        label_p = self._font_small.render("Player", True, DOT_COLORS["player"])
        surface.blit(label_p, (pi[0] + 12, pi[1] - 6))

        pygame.draw.circle(surface, DOT_COLORS["enemy"], ei, 8)
        pygame.draw.circle(surface, (255, 255, 255), ei, 8, 1)
        label_e = self._font_small.render("Enemy", True, DOT_COLORS["enemy"])
        surface.blit(label_e, (ei[0] + 12, ei[1] - 6))

        # Mode label
        mode_color = COLOR_HIGHLIGHT if self._mode >= 1 else COLOR_ACCENT
        mode_label = self._font_medium.render(
            f"  Mode: {MODE_NAMES[self._mode]}  ", True, mode_color)
        surface.blit(mode_label, (4, 24))

        # Math info panel
        info_y = 80
        dot_x = vec2_dot(vec_ab, pygame.Vector2(1, 0))
        angle = math.degrees(math.atan2(vec_ab.y, vec_ab.x)) if vec_len > 0.01 else 0.0
        info_lines = [
            f"Vector AB: ({vx:.0f}, {vy:.0f})",
            f"Length |AB|: {vec_len:.1f}",
        ]
        if self._show_normalized and vec_len > 1.0:
            nn = vec_ab.copy().normalize()
            info_lines.append(f"Normalized: ({nn.x:.3f}, {nn.y:.3f}) [length={nn.length():.1f}]")
        info_lines += [
            f"Dot(AB, X): {dot_x:.1f}",
            f"Angle from X: {angle:.0f}°",
            f"Distance: {vec_len:.1f} px",
        ]

        for i, line in enumerate(info_lines):
            txt = self._font_small.render(line, True, COLOR_TEXT)
            surface.blit(txt, (4, info_y + i * 16))

        # Controls hint
        hint = self._font_small.render(
            "  Arrows: Player  |  WASD: Enemy  |  TAB: mode  |  N: toggle norm  |"
            "  R: reset  |  ESC: exit", True, COLOR_TEXT)
        surface.blit(hint, (4, 50))

        # Status
        if self._status_msg:
            st = self._font_small.render(self._status_msg, True, COLOR_HIGHLIGHT)
            surface.blit(st, (4, settings.INTERNAL_HEIGHT - 20))

        draw_bottom_bar(surface, f"MODE: {MODE_NAMES[self._mode]}")
