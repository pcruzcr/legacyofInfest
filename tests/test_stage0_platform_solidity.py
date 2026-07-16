"""Regression tests: Stage 0 platform solidity (new demo layout 100x38).

- Zone A Platform (cols 6-11, row 30): SOLID — walking into it blocks.
- Zone D Pit Cover (cols 54-56, row 32): ONE-WAY at floor level — player
  walks onto it safely; jump-through from below works.
- Zone D High Platform (cols 58-62, row 27): reachable from floor.
"""
from __future__ import annotations
import os
import pygame
import pytest
from src.engine.input.action_map import Action
from src.engine.input.input_manager import InputManager
from src.framework.entities.player import Player
from src.framework.stage.stage_loader import StageLoader

STAGE0_TMX = "assets/maps/stage0/stage0.tmx"
DT = 1.0 / 60.0
TILE = 16

# Zone A Platform: cols 6-11, row 30
P1_C1, P1_C2 = 6, 11

# Zone D Pit Cover: cols 54-56, row 32 (floor level)
PIT_C1, PIT_C2 = 54, 56
PIT_ROW = 32

# Zone D High Platform: cols 58-62, row 30 (head-level, passable from below)
HP_C1, HP_C2 = 58, 62
HP_ROW = 30


def _hold(*actions: Action) -> InputManager:
    im = InputManager()
    for action in actions:
        for key in im._bindings.get(action, []):
            im._held.add(key)
    return im


def _jump_frame(*held: Action) -> InputManager:
    im = _hold(*held)
    for key in im._bindings.get(Action.JUMP, []):
        im._pressed_this_frame.add(key)
        im._held.add(key)
    return im


@pytest.fixture(scope="module")
def stage():
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((1, 1))
    from src.framework.entities import entity_factory
    entity_factory.ensure_registered()
    return StageLoader.load(STAGE0_TMX)


class TestZoneAPlatformsAreSolid:
    def test_walking_right_is_blocked_by_platform_a1(self, stage) -> None:
        # Player spawns at (64, 480), walks right until blocked at col 6 (x=96)
        player = Player(pygame.Vector2(*stage.spawn_point))
        move_right = _hold(Action.MOVE_RIGHT)
        for _ in range(300):
            player.update(DT, stage.collision_rects, move_right, stage.one_way_rects)
        p1_x = P1_C1 * TILE
        assert player.rect.right <= p1_x + 1
        assert player.rect.right >= p1_x - 4
        assert player.is_grounded

    def test_jump_lands_on_top_of_platform_a1(self, stage) -> None:
        # Start below-left of platform 1
        start_x = P1_C1 * TILE - 50
        start_y = (32 * TILE) - 32  # floor-level feet
        player = Player(pygame.Vector2(start_x, start_y))
        for _ in range(5):
            player.update(DT, stage.collision_rects, _hold(Action.MOVE_RIGHT), stage.one_way_rects)
        player.update(DT, stage.collision_rects, _jump_frame(Action.MOVE_RIGHT), stage.one_way_rects)
        for _ in range(25):
            player.update(
                DT, stage.collision_rects, _hold(Action.MOVE_RIGHT, Action.JUMP), stage.one_way_rects
            )
        for _ in range(70):
            player.update(DT, stage.collision_rects, _hold(Action.MOVE_RIGHT), stage.one_way_rects)
        p1_x1 = P1_C1 * TILE
        p1_x2 = P1_C2 * TILE
        plat_top = 30 * TILE
        assert p1_x1 <= player.position.x <= p1_x2 + TILE
        assert abs(player.position.y - (plat_top - 32)) < 2.0
        assert player.is_grounded


class TestZoneDPitPlatformIsOneWay:
    def test_walk_onto_pit_cover(self, stage) -> None:
        """Player walks from floor onto the one-way pit cover without falling."""
        start_x = (PIT_C1 - 1) * TILE + 4
        start_y = (32 * TILE) - 32
        player = Player(pygame.Vector2(start_x, start_y))
        move_right = _hold(Action.MOVE_RIGHT)
        for _ in range(60):
            player.update(DT, stage.collision_rects, move_right, stage.one_way_rects)
        assert player.is_grounded
        # Player should be on or past the pit cover
        assert player.rect.centerx >= PIT_C1 * TILE

    def test_pit_cover_prevents_falling(self, stage) -> None:
        """Walking onto the pit cover does NOT trigger fall/death."""
        start_x = (PIT_C1 - 1) * TILE + 4
        start_y = (32 * TILE) - 32
        player = Player(pygame.Vector2(start_x, start_y))
        move_right = _hold(Action.MOVE_RIGHT)
        fell = False
        for _ in range(120):
            player.update(DT, stage.collision_rects, move_right, stage.one_way_rects)
            if player.position.y > 32 * TILE + 16:
                fell = True
                break
        assert not fell, "Player should NOT fall when walking onto pit cover"
        assert player.is_grounded


class TestStage0CollisionTyping:
    def test_pit_cover_is_one_way(self, stage) -> None:
        pit_covers = [r for r in stage.one_way_rects if r.y == PIT_ROW * TILE]
        assert len(pit_covers) == 1
        plat = pit_covers[0]
        assert plat.x == PIT_C1 * TILE
        assert plat.y == PIT_ROW * TILE
        assert plat.width == (PIT_C2 - PIT_C1 + 1) * TILE

    def test_high_platform_is_one_way(self, stage) -> None:
        high_plats = [r for r in stage.one_way_rects if r.y == 30 * TILE]
        assert len(high_plats) == 1
        plat = high_plats[0]
        assert plat.x == 58 * TILE
        assert plat.width == 5 * TILE


class TestZoneDHighPlatform:
    def test_high_platform_is_reachable_from_below(self, stage) -> None:
        """Player on floor below col 58-62 can jump through one-way and land on top."""
        start_x = (HP_C1 + 2) * TILE  # x=960, centered under platform
        start_y = (32 * TILE) - 32  # floor level
        player = Player(pygame.Vector2(start_x, start_y))
        for _ in range(30):
            player.update(DT, stage.collision_rects, _hold(), stage.one_way_rects)
            if player.is_grounded:
                break
        player.update(DT, stage.collision_rects, _jump_frame(), stage.one_way_rects)
        for _ in range(20):
            player.update(DT, stage.collision_rects, _hold(Action.JUMP), stage.one_way_rects)
        for _ in range(90):
            player.update(DT, stage.collision_rects, _hold(), stage.one_way_rects)
            if player.is_grounded and abs(player.rect.bottom - HP_ROW * TILE) < 4:
                break
        plat_top = HP_ROW * TILE  # 480
        assert player.is_grounded, "Player must be grounded after jump"
        assert abs(player.rect.bottom - plat_top) < 4, \
            f"Player should land on row {HP_ROW} (bottom={player.rect.bottom}, expected ~{plat_top})"

    def test_archer_spawns_on_high_platform(self, stage) -> None:
        """The Archer enemy stands on the high platform."""
        archers = [e for e in stage.entity_list if type(e).__name__ == "EnemyArcher"]
        assert len(archers) == 1
        archer = archers[0]
        plat_top = HP_ROW * TILE  # 480
        assert abs(archer.rect.bottom - plat_top) < 4, \
            f"Archer bottom ({archer.rect.bottom}) should be at platform surface ({plat_top})"
