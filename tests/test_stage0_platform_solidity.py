"""Regression tests: Stage 0 platform solidity per 07_STAGE0_DESIGN.

- Zone A/C platforms are SOLID: walking into them blocks (forces a jump).
- Zone E pit cover is ONE-WAY: walking off the floor edge falls into the
  pit; only a jump from below lands on top ("Jump up through it").
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
    return StageLoader.load(STAGE0_TMX)


class TestZoneAPlatformsAreSolid:
    def test_walking_right_is_blocked_by_platform_a1(self, stage) -> None:
        player = Player(pygame.Vector2(*stage.spawn_point))
        move_right = _hold(Action.MOVE_RIGHT)
        for _ in range(300):
            player.update(DT, stage.collision_rects, move_right, stage.one_way_rects)
        assert player.rect.right <= 272 + 1
        assert player.rect.right >= 272 - 4
        assert abs(player.position.y - 160.0) < 1.0
        assert player.is_grounded

    def test_jump_lands_on_top_of_platform_a1(self, stage) -> None:
        player = Player(pygame.Vector2(226, 160))
        for _ in range(5):
            player.update(DT, stage.collision_rects, _hold(Action.MOVE_RIGHT), stage.one_way_rects)
        player.update(DT, stage.collision_rects, _jump_frame(Action.MOVE_RIGHT), stage.one_way_rects)
        for _ in range(25):
            player.update(
                DT, stage.collision_rects, _hold(Action.MOVE_RIGHT, Action.JUMP), stage.one_way_rects
            )
        for _ in range(70):
            player.update(DT, stage.collision_rects, _hold(Action.MOVE_RIGHT), stage.one_way_rects)
        assert 272 <= player.position.x <= 368
        assert abs(player.position.y - 128.0) < 1.0
        assert player.is_grounded


class TestZoneEPitPlatformIsOneWay:
    def test_walking_off_floor_edge_falls_into_pit(self, stage) -> None:
        player = Player(pygame.Vector2(2180, 160))
        move_right = _hold(Action.MOVE_RIGHT)
        fell = False
        for _ in range(200):
            player.update(DT, stage.collision_rects, move_right, stage.one_way_rects)
            if player.position.y > 192:
                fell = True
                break
        assert fell

    def test_jump_from_floor_lands_on_pit_platform(self, stage) -> None:
        player = Player(pygame.Vector2(2210, 160))
        for _ in range(5):
            player.update(DT, stage.collision_rects, _hold(Action.MOVE_RIGHT), stage.one_way_rects)
        player.update(DT, stage.collision_rects, _jump_frame(Action.MOVE_RIGHT), stage.one_way_rects)
        for _ in range(20):
            player.update(
                DT, stage.collision_rects, _hold(Action.MOVE_RIGHT, Action.JUMP), stage.one_way_rects
            )
        landed = False
        for _ in range(90):
            player.update(DT, stage.collision_rects, _hold(Action.MOVE_RIGHT), stage.one_way_rects)
            if player.is_grounded and abs((player.position.y + player.rect.height) - 176.0) < 1.0:
                landed = True
                break
        assert landed
        for _ in range(30):
            player.update(DT, stage.collision_rects, _hold(Action.MOVE_RIGHT), stage.one_way_rects)
            if player.position.x < 2300:
                assert player.is_grounded
                assert abs((player.position.y + player.rect.height) - 176.0) < 1.0


class TestStage0CollisionTyping:
    def test_only_the_pit_cover_is_one_way(self, stage) -> None:
        assert len(stage.one_way_rects) == 1
        plat = stage.one_way_rects[0]
        assert (plat.x, plat.y, plat.width) == (2240, 176, 80)
