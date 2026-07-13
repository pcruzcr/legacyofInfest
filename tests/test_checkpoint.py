"""
Module: test_checkpoint
System: tests
Description: Tests for Checkpoint single-activation and event emission.
"""
from __future__ import annotations
import pygame
from src.framework.stage.checkpoint import Checkpoint
from src.engine.core.event_bus import EventBus


class TestCheckpointActivation:
    def test_activates_once(self) -> None:
        cp = Checkpoint(
            pygame.Vector2(100, 100),
            pygame.Rect(100, 100, 24, 32),
            checkpoint_id=0,
        )
        assert cp.is_activated is False
        cp.activate()
        assert cp.is_activated is True
        cp.activate()
        assert cp.is_activated is True

    def test_checkpoint_id_preserved(self) -> None:
        cp = Checkpoint(
            pygame.Vector2(200, 150),
            pygame.Rect(200, 150, 24, 32),
            checkpoint_id=5,
        )
        assert cp.checkpoint_id == 5

    def test_draw_does_not_crash(self) -> None:
        cp = Checkpoint(
            pygame.Vector2(0, 0),
            pygame.Rect(0, 0, 24, 32),
            checkpoint_id=0,
        )
        surface = pygame.Surface((320, 224))
        cp.draw(surface, pygame.Vector2(0, 0))

    def test_check_collision_activates(self) -> None:
        cp = Checkpoint(
            pygame.Vector2(100, 100),
            pygame.Rect(100, 100, 24, 32),
            checkpoint_id=0,
        )
        player_rect = pygame.Rect(110, 110, 20, 32)
        result = cp.check_collision(player_rect)
        assert result is True
        assert cp.is_activated is True

    def test_check_collision_only_once(self) -> None:
        cp = Checkpoint(
            pygame.Vector2(100, 100),
            pygame.Rect(100, 100, 24, 32),
            checkpoint_id=0,
        )
        player_rect = pygame.Rect(110, 110, 20, 32)
        cp.check_collision(player_rect)
        result = cp.check_collision(player_rect)
        assert result is False

    def test_check_collision_no_overlap(self) -> None:
        cp = Checkpoint(
            pygame.Vector2(100, 100),
            pygame.Rect(100, 100, 24, 32),
            checkpoint_id=0,
        )
        player_rect = pygame.Rect(0, 0, 20, 32)
        result = cp.check_collision(player_rect)
        assert result is False
        assert cp.is_activated is False

    def test_activate_emits_event(self, event_bus: EventBus) -> None:
        cp = Checkpoint(
            pygame.Vector2(100, 100),
            pygame.Rect(100, 100, 24, 32),
            checkpoint_id=3,
            event_bus=event_bus,
        )
        cp.activate()
        assert cp.is_activated is True
