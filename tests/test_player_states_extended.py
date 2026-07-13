"""Player instantiation tests."""
from __future__ import annotations

import pygame

from src.framework.entities.player import Player, PlayerState


class TestPlayerCreation:
    def test_create_player(self):
        p = Player(pygame.Vector2(100, 200))
        assert p is not None
        assert p.velocity == pygame.Vector2(0.0, 0.0)
        assert p.is_grounded is False

    def test_player_state_enum_count(self):
        assert len(PlayerState) == 19

    def test_player_has_state_instance(self):
        p = Player(pygame.Vector2(50, 50))
        assert p._state_instance is not None
