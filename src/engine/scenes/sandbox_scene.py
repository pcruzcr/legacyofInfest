"""
SandboxScene — Unrestricted experimentation playground.

Students can:
  - Spawn entities (player, enemies, collectibles)
  - Toggle god mode, physics, collision display
  - Test stage elements without consequences
  - Reset everything instantly
"""
from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from src.engine.core import settings
from src.engine.input.action_map import Action
from src.engine.scene.base_scene import BaseScene
from src.engine.scenes.demo_common import (
    BOTTOM_BAR_H,
    COLOR_ACCENT,
    COLOR_BG,
    COLOR_HIGHLIGHT,
    COLOR_TEXT,
    FONT_MEDIUM,
    FONT_SMALL,
    TOP_BAR_H,
    draw_bottom_bar,
    draw_top_bar,
)
from src.engine.utils.asset_loader import AssetLoader

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext


PLAYER_SPEED = 150.0
ENEMY_SPEED = 60.0


class SandboxScene(BaseScene):
    """Unrestricted playground for experimentation. Spawn enemies/collectibles, toggle physics, shoot projectiles."""

    def __init__(self, context: GameContext) -> None:
        """Initialize sandbox with player, empty enemy/collectible/projectile lists."""
        super().__init__(context)
        self._font_small = AssetLoader.load_font(
            settings.ASSETS_DIR / "fonts" / "game.ttf", FONT_SMALL)
        self._font_medium = AssetLoader.load_font(
            settings.ASSETS_DIR / "fonts" / "game.ttf", FONT_MEDIUM)

        self._player_pos = pygame.Vector2(200.0, 150.0)
        self._enemies: list[pygame.Vector2] = []
        self._collectibles: list[pygame.Vector2] = []
        self._projectiles: list[tuple[pygame.Vector2, pygame.Vector2]] = []

        self._show_grid: bool = True
        self._show_collision: bool = True
        self._god_mode: bool = False
        self._physics_enabled: bool = True
        self._mode: int = 0  # 0=move, 1=spawn enemies, 2=spawn collectibles, 3=shoot

    def on_enter(self) -> None:
        """Reset state on entering the sandbox."""

    def on_exit(self) -> None:
        """Cleanup on exit."""

    def update(self, dt: float) -> None:
        """Handle input: mode switching, spawning, movement, shooting, toggles."""
        im = self.input
        if im is None:
            return

        if im.is_action_just_pressed(Action.CANCEL):
            from src.engine.scenes.demo_menu_scene import DemoMenuScene
            self.context.scene_manager.replace(DemoMenuScene(self.context))
            return

        if im.is_raw_key_pressed(pygame.K_TAB):
            self._mode = (self._mode + 1) % 4

        if im.is_raw_key_pressed(pygame.K_g):
            self._god_mode = not self._god_mode

        if im.is_raw_key_pressed(pygame.K_c):
            self._show_collision = not self._show_collision

        if im.is_raw_key_pressed(pygame.K_r):
            self._enemies.clear()
            self._collectibles.clear()
            self._projectiles.clear()
            self._player_pos = pygame.Vector2(200.0, 150.0)

        if im.is_raw_key_pressed(pygame.K_SPACE):
            mouse_x, mouse_y = pygame.mouse.get_pos()
            mx = int(mouse_x / settings.DISPLAY_SCALE)
            my = int(mouse_y / settings.DISPLAY_SCALE)
            if self._mode == 1:
                self._enemies.append(pygame.Vector2(float(mx), float(my)))
            elif self._mode == 2:
                self._collectibles.append(pygame.Vector2(float(mx), float(my)))

        move = pygame.Vector2(0.0, 0.0)
        if im.is_action_held(Action.MOVE_LEFT):
            move.x -= 1.0
        if im.is_action_held(Action.MOVE_RIGHT):
            move.x += 1.0
        if im.is_action_held(Action.JUMP):
            move.y -= 1.0
        if im.is_action_held(Action.CROUCH):
            move.y += 1.0

        if self._physics_enabled:
            self._player_pos += move * PLAYER_SPEED * dt
        else:
            self._player_pos += move * PLAYER_SPEED * 3 * dt

        self._player_pos.x = max(8, min(settings.INTERNAL_WIDTH - 8, self._player_pos.x))
        self._player_pos.y = max(TOP_BAR_H + 8, min(settings.INTERNAL_HEIGHT - BOTTOM_BAR_H - 8, self._player_pos.y))

        if self._physics_enabled:
            for e in self._enemies:
                to_player = self._player_pos - e
                dist = to_player.length()
                if dist > 10.0 and dist < 300.0:
                    to_player.normalize_ip()
                    e += to_player * ENEMY_SPEED * dt

        for i in range(len(self._projectiles) - 1, -1, -1):
            pos, vel = self._projectiles[i]
            pos += vel * dt * 200
            if (pos.x < 0 or pos.x > settings.INTERNAL_WIDTH or
                    pos.y < 0 or pos.y > settings.INTERNAL_HEIGHT):
                self._projectiles.pop(i)

        if pygame.mouse.get_pressed()[0]:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            mx = float(mouse_x / settings.DISPLAY_SCALE)
            my = float(mouse_y / settings.DISPLAY_SCALE)
            dir_vec = pygame.Vector2(mx, my) - self._player_pos
            if dir_vec.length() > 5.0:
                dir_vec.normalize_ip()
                self._projectiles.append((
                    pygame.Vector2(self._player_pos.x, self._player_pos.y),
                    dir_vec,
                ))

    def draw(self, surface: pygame.Surface) -> None:
        """Render the sandbox: grid, entities, projectiles, mode/status info."""
        surface.fill(COLOR_BG)
        draw_top_bar(surface, "PLAYGROUND SANDBOX", "FREE MODE")

        mode_names = ["[MOVE]", "[SPAWN ENEMIES]", "[SPAWN COLLECTIBLES]", "[SHOOT]"]
        mode_color = COLOR_HIGHLIGHT if self._mode > 0 else COLOR_ACCENT

        if self._show_grid:
            for x in range(0, settings.INTERNAL_WIDTH, 32):
                pygame.draw.line(surface, (20, 20, 45), (x, TOP_BAR_H), (x, settings.INTERNAL_HEIGHT - BOTTOM_BAR_H), 1)
            for y in range(TOP_BAR_H, settings.INTERNAL_HEIGHT - BOTTOM_BAR_H, 32):
                pygame.draw.line(surface, (20, 20, 45), (0, y), (settings.INTERNAL_WIDTH, y), 1)

        if self._show_collision:
            for e in self._enemies:
                if self._player_pos.distance_to(e) < 32:
                    pygame.draw.line(surface, (255, 100, 100),
                                     (int(self._player_pos.x), int(self._player_pos.y)),
                                     (int(e.x), int(e.y)), 1)

        for c in self._collectibles:
            pygame.draw.circle(surface, (255, 220, 80), (int(c.x), int(c.y)), 6)
            pygame.draw.circle(surface, (255, 255, 200), (int(c.x), int(c.y)), 6, 1)

        for e in self._enemies:
            color = (200, 80, 80) if not self._god_mode else (100, 100, 200)
            pygame.draw.circle(surface, color, (int(e.x), int(e.y)), 10)
            pygame.draw.circle(surface, (255, 100, 100), (int(e.x), int(e.y)), 10, 1)

        player_color = (80, 200, 120) if not self._god_mode else (100, 255, 255)
        pygame.draw.circle(surface, player_color, (int(self._player_pos.x), int(self._player_pos.y)), 8)
        pygame.draw.circle(surface, (255, 255, 255), (int(self._player_pos.x), int(self._player_pos.y)), 8, 1)

        for pos, _vel in self._projectiles:
            pygame.draw.circle(surface, (255, 200, 50), (int(pos.x), int(pos.y)), 3)

        info_y = TOP_BAR_H + 4
        mode_text = self._font_medium.render(f"  Mode: {mode_names[self._mode]}", True, mode_color)
        surface.blit(mode_text, (4, info_y))
        info_y += 16

        toggles = []
        if self._god_mode:
            toggles.append("GOD MODE")
        if not self._physics_enabled:
            toggles.append("NO PHYSICS")
        if not self._show_collision:
            toggles.append("COLLISION OFF")
        if toggles:
            toggle_text = self._font_small.render(f"  {' | '.join(toggles)}", True, COLOR_ACCENT)
            surface.blit(toggle_text, (4, info_y))

        count_text = self._font_small.render(
            f"  Enemies: {len(self._enemies)}  |  "
            f"Collectibles: {len(self._collectibles)}  |  "
            f"Projectiles: {len(self._projectiles)}",
            True, COLOR_TEXT)
        surface.blit(count_text, (4, info_y + 16))

        draw_bottom_bar(surface, (
            "  [ARROWS] move  [TAB] mode  [SPACE] spawn  "
            "[MOUSE] shoot  [G] god mode  [C] collision  [R] reset  [ESC] exit"
        ))
