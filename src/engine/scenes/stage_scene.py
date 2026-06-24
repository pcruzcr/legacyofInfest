"""
Module: stage_scene
System: engine
Academic Unit: Stage system
Description: Runtime scene that consumes StageData and renders a playable
stage. Wires together Player, Camera, Enemies, Checkpoints, and tile layers.
"""

from __future__ import annotations

from pathlib import Path

import pygame

from src.engine.core.settings import INTERNAL_HEIGHT, INTERNAL_WIDTH
from src.engine.scene.base_scene import BaseScene
from src.framework.stage.camera import Camera
from src.framework.stage.stage_loader import StageLoader
from src.framework.entities.enemy_walker import EnemyWalker
from src.framework.entities.enemy_flying import EnemyFlying
from src.framework.entities.enemy_shooter import EnemyShooter
from src.framework.entities.player import Player


class StageScene(BaseScene):
    """Playable stage scene that loads and renders a TMX stage."""

    def __init__(self, tmx_path: Path) -> None:
        """Create the stage scene.

        Args:
            tmx_path: Path to the ``.tmx`` file to load.
        """
        self._tmx_path: Path = tmx_path
        self._data = None
        self._player: Player | None = None
        self._camera: Camera | None = None
        self._enemies: list = []
        self._checkpoints: list = []

    # ── Lifecycle ────────────────────────────────────────────────────

    def on_enter(self) -> None:
        """Load the TMX stage and spawn all runtime objects."""
        # Register enemy types for entity factory
        StageLoader.register_entity("Walker", EnemyWalker)
        StageLoader.register_entity("Flying", EnemyFlying)
        StageLoader.register_entity("Shooter", EnemyShooter)

        # Load stage data
        self._data = StageLoader.load(self._tmx_path)

        # Spawn player at TMX spawn point
        sp = self._data.spawn_point
        self._player = Player(sp.x, sp.y)

        # Create camera and attach to player
        self._camera = Camera()
        self._camera.follow(self._player)

        # Spawn enemies from entity list
        self._enemies = list(self._data.entity_list)

        # Store checkpoints
        self._checkpoints = list(self._data.checkpoints)

    def on_exit(self) -> None:
        """Cleanup when leaving the stage."""
        self._data = None
        self._player = None
        self._camera = None
        self._enemies.clear()
        self._checkpoints.clear()

    # ── Update ───────────────────────────────────────────────────────

    def update(self, dt: float) -> None:
        """Run one frame of stage logic."""
        if self._player is None or self._camera is None or self._data is None:
            return

        # Update camera
        self._camera.update(dt)

        # Update player with stage collision rects
        self._player.update(dt, collision_rects=self._data.collision_rects)

        # Update enemies
        for enemy in self._enemies:
            if hasattr(enemy, "set_collision_rects"):
                enemy.set_collision_rects(self._data.collision_rects)
            enemy.update(dt)

        # Activate checkpoints on player overlap
        player_rect = self._player.rect
        for cp in self._checkpoints:
            cp.try_activate(player_rect)

        # Check next trigger for stage transition
        if self._data.next_trigger is not None:
            if player_rect.colliderect(self._data.next_trigger):
                # Future: transition to next stage
                pass

    # ── Render ───────────────────────────────────────────────────────

    def draw(self, surface: pygame.Surface) -> None:
        """Render the stage to *surface*."""
        if self._data is None:
            return

        # Clear
        surface.fill((0, 0, 0))

        # Draw tile layers via pyscroll group
        # pyscroll handles camera offset internally when we set the layer's
        # view; we compensate by passing the negative camera offset.
        offset = self._camera.offset if self._camera else pygame.Vector2(0, 0)
        if self._camera is not None:
            # pyscroll uses a center-point camera, not a top-left offset.
            # Convert our top-left offset to center coordinates.
            cx = offset.x + INTERNAL_WIDTH / 2
            cy = offset.y + INTERNAL_HEIGHT / 2
            self._data.map_layer.center = (cx, cy)
        self._data.map_layer.draw(surface)

        # Draw entities (sorted by layer depth if needed)
        for enemy in self._enemies:
            if hasattr(enemy, "is_active") and not enemy.is_active:
                continue
            enemy.draw(surface, offset)

        # Draw player
        if self._player is not None:
            self._player.draw(surface, offset)

        # Draw checkpoints (debug / visual marker)
        for cp in self._checkpoints:
            cp.draw(surface, offset)
