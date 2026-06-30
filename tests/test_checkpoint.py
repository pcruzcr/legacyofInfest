"""
Module: test_checkpoint
System: tests
Academic Unit: N/A
Description: Tests for Checkpoint single-activation and event emission.
"""
import pygame

from src.engine.core.event_bus import EventBus
from src.framework.stage.checkpoint import Checkpoint


class TestCheckpointActivation:
    """Tests for checkpoint behavior."""

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
