"""
CollisionLabScene — Interactive AABB Collision Theory Laboratory

Teaches Unit VI concepts:
  - Axis-separated vs Y-first collision resolution
  - prev_bottom / tile.top landing condition
  - One-way platform detection

Modes:
  0: No collision (player passes through everything)
  1: Y-first resolution (shows the wall-climb bug)
  2: X-first (axis-separated, correct)

Controls:
  arrows  — move player
  TAB     — cycle resolution mode
  B       — auto-demonstrate the wall-climb bug
  R       — reset player position
  ESC     — back to demo menu
"""
from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from src.engine.core import settings
from src.engine.input.action_map import Action
from src.engine.scene.base_scene import BaseScene
from src.engine.scenes.demo_common import (
    COLOR_BG, COLOR_TEXT, COLOR_HIGHLIGHT, COLOR_ACCENT, COLOR_ERROR,
    COLOR_TOP_BAR_BG, COLOR_BOTTOM_BAR_BG, COLOR_DIVIDER,
    FONT_SMALL, FONT_MEDIUM, FONT_LARGE,
    draw_top_bar, draw_bottom_bar,
)
from src.engine.utils.asset_loader import AssetLoader

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext


MODE_NAMES = ["NO COLLISION", "Y-FIRST (BUG)", "X-FIRST (CORRECT)"]
PLAYER_SPEED = 120.0
GRAVITY = 600.0
JUMP_FORCE = -280.0
TILE_SIZE = 32
PLAYER_W = 20
PLAYER_H = 32


class CollisionLabScene(BaseScene):
    def __init__(self, context: GameContext) -> None:
        super().__init__(context)
        self._mode: int = 2  # start with correct mode
        self._px: float = 60.0
        self._py: float = 100.0
        self._vx: float = 0.0
        self._vy: float = 0.0
        self._is_grounded: bool = False
        self._prev_bottom: float = 0.0
        self._prev_top: float = 0.0
        self._collision_info: str = ""
        self._auto_bug: bool = False
        self._bug_timer: float = 0.0

        # Build a simple test level
        self._platforms = [
            pygame.Rect(0, 180, 160, 16),     # main floor (left)
            pygame.Rect(240, 180, 160, 16),    # main floor (right)
            pygame.Rect(160, 140, 16, 56),     # wall between platforms (the wall!)
            pygame.Rect(80, 80, 96, 16),       # high platform
        ]
        self._one_way_rects = [
            pygame.Rect(160, 160, 80, 8),      # one-way platform above wall gap
        ]

        self._spawn_x = 60.0
        self._spawn_y = 100.0

        # Fonts
        self._font_small = AssetLoader.load_font(
            settings.ASSETS_DIR / "fonts" / "game.ttf", FONT_SMALL)
        self._font_medium = AssetLoader.load_font(
            settings.ASSETS_DIR / "fonts" / "game.ttf", FONT_MEDIUM)

        # ErrorDisplay-like message
        self._status_msg: str = ""
        self._status_timer: float = 0.0
        self._horizontal_input: float = 0.0

    def on_enter(self) -> None:
        self._reset_player()

    def on_exit(self) -> None:
        pass

    def _reset_player(self) -> None:
        self._px = self._spawn_x
        self._py = self._spawn_y
        self._vx = 0.0
        self._vy = 0.0
        self._is_grounded = False
        self._auto_bug = False
        self._horizontal_input = 0.0

    def update(self, dt: float) -> None:
        im = self.input
        if im is None:
            return

        # Timers
        if self._status_timer > 0:
            self._status_timer -= dt
            if self._status_timer <= 0:
                self._status_msg = ""

        # TAB — cycle modes
        if im.is_raw_key_pressed(pygame.K_TAB):
            self._mode = (self._mode + 1) % len(MODE_NAMES)
            self._auto_bug = False
            self._status_msg = f"Mode: {MODE_NAMES[self._mode]}"
            self._status_timer = 1.5

        # R — reset
        if im.is_raw_key_pressed(pygame.K_r):
            self._reset_player()
            self._status_msg = "Player reset"
            self._status_timer = 1.0

        # B — auto-demonstrate wall-climb bug (only in Y-first mode)
        if im.is_raw_key_pressed(pygame.K_b):
            if self._mode != 1:
                self._status_msg = "Switch to Y-FIRST mode (TAB) first"
                self._status_timer = 2.0
            else:
                self._reset_player()
                self._auto_bug = True
                self._bug_timer = 0.0
                self._status_msg = "Auto-demo: walking right into wall..."
                self._status_timer = 4.0

        # ESC — back
        if im.is_action_pressed(Action.CANCEL):
            from src.engine.scenes.demo_menu_scene import DemoMenuScene
            self.context.scene_manager.replace(DemoMenuScene(self.context))
            return

        # Player input
        self._horizontal_input = 0.0
        if im.is_action_held(Action.MOVE_LEFT):
            self._horizontal_input = -1.0
        if im.is_action_held(Action.MOVE_RIGHT):
            self._horizontal_input = 1.0
        if im.is_action_just_pressed(Action.JUMP) and self._is_grounded:
            self._vy = JUMP_FORCE
            self._is_grounded = False

        # Auto-bug: force rightward movement
        if self._auto_bug:
            self._horizontal_input = 1.0
            self._bug_timer += dt
            if self._bug_timer > 5.0:
                self._auto_bug = False
                self._status_msg = "Bug complete — player climbed the wall!"
                self._status_timer = 3.0

        # Physics
        self._vx = self._horizontal_input * PLAYER_SPEED
        self._vy += GRAVITY * dt
        if self._vy > 500.0:
            self._vy = 500.0

        # Collision resolution based on mode
        if self._mode == 0:
            # NO COLLISION — just move
            self._px += self._vx * dt
            self._py += self._vy * dt
            self._is_grounded = False
            self._collision_info = "No collision — player passes through everything"
        elif self._mode == 1:
            self._resolve_y_first(dt)
        else:
            self._resolve_x_first(dt)

        # Keep in bounds
        self._px = max(0.0, min(settings.INTERNAL_WIDTH - PLAYER_W, self._px))
        if self._py > settings.INTERNAL_HEIGHT:
            self._py = self._spawn_y
            self._vy = 0.0

    def _resolve_y_first(self, dt: float) -> None:
        """Y-first resolution (the BUG from GAP-005)."""
        w, h = PLAYER_W, PLAYER_H
        player_rect = pygame.Rect(int(self._px), int(self._py), w, h)

        # --- Y first ---
        prev_bottom = self._py + h
        prev_top = self._py
        self._py += self._vy * dt
        self._is_grounded = False

        all_rects = list(self._platforms)
        py = pygame.Rect(int(self._px), int(self._py), w, h)
        for tile in all_rects:
            if py.colliderect(tile):
                if self._vy >= 0 and prev_bottom <= tile.top + 1:
                    py.bottom = tile.top
                    self._vy = 0.0
                    self._is_grounded = True
                elif self._vy < 0 and prev_top >= tile.bottom - 1:
                    py.top = tile.bottom
                    self._vy = 0.0
        self._py = float(py.y)

        # --- X second ---
        self._px += self._vx * dt
        px = pygame.Rect(int(self._px), int(self._py), w, h)
        for tile in all_rects:
            if px.colliderect(tile):
                v_overlap = min(px.bottom, tile.bottom) - max(px.top, tile.top)
                if v_overlap <= 2:
                    continue
                if self._vx > 0:
                    px.right = tile.left
                elif self._vx < 0:
                    px.left = tile.right
                else:
                    if (px.right - tile.left) < (tile.right - px.left):
                        px.right = tile.left
                    else:
                        px.left = tile.right
                self._vx = 0.0
        self._px = float(px.x)

        # Store info text
        self._prev_bottom = prev_bottom
        self._prev_top = prev_top
        self._collision_info = (
            f"Y-first: prev_bottom={prev_bottom:.0f} | "
            f"tile checks trigger landing if prev_bottom <= tile.top+1"
        )

    def _resolve_x_first(self, dt: float) -> None:
        """X-first axis-separated (correct) resolution."""
        w, h = PLAYER_W, PLAYER_H

        # --- X ---
        self._px += self._vx * dt
        px = pygame.Rect(int(self._px), int(self._py), w, h)
        for tile in self._platforms:
            if px.colliderect(tile):
                v_overlap = min(px.bottom, tile.bottom) - max(px.top, tile.top)
                if v_overlap <= 2:
                    continue
                if self._vx > 0:
                    px.right = tile.left
                elif self._vx < 0:
                    px.left = tile.right
                else:
                    if (px.right - tile.left) < (tile.right - px.left):
                        px.right = tile.left
                    else:
                        px.left = tile.right
                self._vx = 0.0
        self._px = float(px.x)

        # --- Y ---
        prev_bottom = self._py + h
        prev_top = self._py
        self._py += self._vy * dt
        was_grounded = self._is_grounded
        self._is_grounded = False

        py = pygame.Rect(int(self._px), int(self._py), w, h)
        for tile in self._platforms:
            if py.colliderect(tile):
                if self._vy >= 0 and prev_bottom <= tile.top + 1:
                    if not was_grounded and self._vy > 0:
                        pass  # would emit land sound
                    py.bottom = tile.top
                    self._vy = 0.0
                    self._is_grounded = True
                elif self._vy < 0 and prev_top >= tile.bottom - 1:
                    py.top = tile.bottom
                    self._vy = 0.0
        self._py = float(py.y)

        # One-way platforms
        if self._vy >= 0:
            player_rect = pygame.Rect(int(self._px), int(self._py), w, h)
            owb = player_rect.bottom - self._vy * dt
            for plat in self._one_way_rects:
                if player_rect.colliderect(plat) and owb <= plat.top:
                    player_rect.bottom = plat.top
                    self._vy = 0.0
                    self._is_grounded = True
                    self._py = float(player_rect.y)
                    break

        self._prev_bottom = prev_bottom
        self._prev_top = prev_top
        self._collision_info = (
            f"X-first: X resolved first, then Y with prev_bottom check | "
            f"prev_bottom={prev_bottom:.0f}"
        )

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(COLOR_BG)
        draw_top_bar(surface, "COLLISION LAB", "UNIT VI")
        cam_x = 0
        cam_y = 0

        # Draw platforms
        for tile in self._platforms:
            color = (80, 100, 80)  # solid green-gray
            pygame.draw.rect(surface, color,
                             (tile.x + cam_x, tile.y + cam_y, tile.w, tile.h))
            pygame.draw.rect(surface, (60, 80, 60),
                             (tile.x + cam_x, tile.y + cam_y, tile.w, tile.h), 1)

        for plat in self._one_way_rects:
            color = (60, 130, 200)  # blue for one-way
            pygame.draw.rect(surface, color,
                             (plat.x + cam_x, plat.y + cam_y, plat.w, plat.h))
            # Arrow indicating one-way direction
            mid_x = plat.x + plat.w // 2
            pygame.draw.polygon(surface, (100, 200, 255), [
                (mid_x + cam_x, plat.y + cam_y),
                (mid_x - 5 + cam_x, plat.y + 6 + cam_y),
                (mid_x + 5 + cam_x, plat.y + 6 + cam_y),
            ])

        # Draw player
        px = int(self._px)
        py = int(self._py)
        if self._mode == 1:
            player_color = (255, 120, 80)  # orange-red for bug mode
        elif self._mode == 0:
            player_color = (120, 120, 200)  # purple for no collision
        else:
            player_color = (80, 200, 120)  # green for correct

        pygame.draw.rect(surface, player_color,
                         (px + cam_x, py + cam_y, PLAYER_W, PLAYER_H))
        pygame.draw.rect(surface, (255, 255, 255),
                         (px + cam_x, py + cam_y, PLAYER_W, PLAYER_H), 1)

        # Grounded indicator
        if self._is_grounded:
            pygame.draw.line(surface, (255, 255, 100),
                             (px, py + PLAYER_H),
                             (px + PLAYER_W, py + PLAYER_H), 2)

        # Mode label
        mode_color = COLOR_HIGHLIGHT if self._mode == 2 else (
            COLOR_ERROR if self._mode == 1 else COLOR_ACCENT)
        mode_label = self._font_medium.render(
            f"  Mode: {MODE_NAMES[self._mode]}  ", True, mode_color)
        surface.blit(mode_label, (4, 24))

        # Controls hint
        hint = self._font_small.render(
            "  Arrows: move  |  SPACE: jump  |  TAB: mode  |  B: auto-bug  |  R: reset  |  ESC: exit",
            True, COLOR_TEXT)
        surface.blit(hint, (4, 42))

        # Collision info panel (bottom area)
        info_y = 60
        lines = [
            f"Player pos: ({self._px:.0f}, {self._py:.0f})",
            f"Velocity: ({self._vx:.1f}, {self._vy:.1f})",
            f"Grounded: {self._is_grounded}",
            f"",
        ]

        if self._mode == 1:
            lines += [
                "BUG: Y-first resolution treats ANY overlapping rect as floor.",
                "Walk right into the wall -> wall is treated as floor ->",
                "player teleports UP tile by tile -> passes through wall.",
                f"",
                self._collision_info,
            ]
        elif self._mode == 2:
            lines += [
                "CORRECT: X resolved first (wall stops X movement).",
                "Then Y resolved with prev_bottom check:",
                "  landing when prev_bottom <= tile.top + 1",
                "  bonk when prev_top >= tile.bottom - 1",
                f"",
                self._collision_info,
            ]
        else:
            lines += [
                "No collision — player moves freely through all geometry.",
                "Use this to observe path without collision interference.",
            ]

        if self._auto_bug:
            lines += ["", "[AUTO-BUG] Player walks right — watch the wall-climb!"]

        for i, line in enumerate(lines):
            txt = self._font_small.render(line, True, COLOR_TEXT)
            surface.blit(txt, (4, info_y + i * 14))

        # Status message
        if self._status_msg:
            st = self._font_small.render(self._status_msg, True, COLOR_HIGHLIGHT)
            surface.blit(st, (4, settings.INTERNAL_HEIGHT - 20))

        # Bottom bar
        bar_text = (
            f"MODE: {MODE_NAMES[self._mode]}  |  "
            f"[TAB] cycle  [B] bug demo  [R] reset  [ESC] menu"
        )
        draw_bottom_bar(surface, bar_text)
