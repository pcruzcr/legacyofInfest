"""Regression tests: Stage 0 platform solidity per 07_STAGE0_DESIGN.

History: all Stage 0 platforms were mistyped as one-way (type="Platform"),
so the player walked straight through the Zone A/C elevated platforms, and
the one-way straddle check auto-lifted a walking player over the Zone E
death pit. These tests pin the intended behavior:

- Zone A/C platforms are SOLID: walking into them blocks (forces a jump).
- Zone E pit cover is ONE-WAY: walking off the floor edge falls into the
  pit; only a jump from below lands on top ("Jump up through it").

These drive the player with a real InputManager (held keys), because the
state machine zeroes velocity without input — asserting on directly-set
velocity produces vacuous tests (see the wall-block test post-mortem).
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
        """Design §Zone A: elevated platforms the player must JUMP onto.
        Walking into platform A1 (x=272, y=160..176) must block, not
        pass through, and must not teleport the player vertically."""
        player = Player(pygame.Vector2(*stage.spawn_point))
        move_right = _hold(Action.MOVE_RIGHT)
        for _ in range(300):
            player.update(DT, stage.collision_rects, move_right, stage.one_way_rects)
        # Blocked flush against the platform's left face (272 - width 20).
        assert player.rect.right <= 272 + 1
        assert player.rect.right >= 272 - 4  # actually reached it
        # No vertical teleport (the old escalator/pass-through symptoms).
        assert abs(player.position.y - 160.0) < 1.0
        assert player.is_grounded

    def test_jump_lands_on_top_of_platform_a1(self, stage) -> None:
        player = Player(pygame.Vector2(226, 160))
        for _ in range(5):
            player.update(DT, stage.collision_rects, _hold(Action.MOVE_RIGHT), stage.one_way_rects)
        player.update(DT, stage.collision_rects, _jump_frame(Action.MOVE_RIGHT), stage.one_way_rects)
        # Hold JUMP during ascent so the jump-cut doesn't halve the arc.
        for _ in range(25):
            player.update(
                DT, stage.collision_rects, _hold(Action.MOVE_RIGHT, Action.JUMP), stage.one_way_rects
            )
        for _ in range(70):
            player.update(DT, stage.collision_rects, _hold(Action.MOVE_RIGHT), stage.one_way_rects)
        assert 272 <= player.position.x <= 368
        assert abs(player.position.y - 128.0) < 1.0  # feet on top (160 - 32)
        assert player.is_grounded


class TestZoneEPitPlatformIsOneWay:
    def test_walking_off_floor_edge_falls_into_pit(self, stage) -> None:
        """Design §Zone E message: "Jump up through it". A player who walks
        off the floor edge (feet y=192, platform top y=176) was never above
        the platform and must fall past it into the pit — no auto-lift."""
        player = Player(pygame.Vector2(2180, 160))
        move_right = _hold(Action.MOVE_RIGHT)
        fell = False
        for _ in range(200):
            player.update(DT, stage.collision_rects, move_right, stage.one_way_rects)
            if player.position.y > 192:
                fell = True
                break
        assert fell, "player was auto-lifted over the death pit while walking"

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
        assert landed, "player could not land on the one-way pit platform"
        # And remains stable while walking on it.
        for _ in range(30):
            player.update(DT, stage.collision_rects, _hold(Action.MOVE_RIGHT), stage.one_way_rects)
            if player.position.x < 2300:
                assert player.is_grounded
                assert abs((player.position.y + player.rect.height) - 176.0) < 1.0


class TestStage0CollisionTyping:
    def test_only_the_pit_cover_is_one_way(self, stage) -> None:
        """The generator maps tile 3 → Solid except the Zone E pit cover.
        If this fails, generate_stage0_tmx.py regressed to all-one-way."""
        assert len(stage.one_way_rects) == 1
        plat = stage.one_way_rects[0]
        assert (plat.x, plat.y, plat.width) == (2240, 176, 80)
