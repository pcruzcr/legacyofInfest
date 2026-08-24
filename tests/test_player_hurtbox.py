"""
Module: test_player_hurtbox
System: tests
Academic Unit: N/A
Description: Tests for Player.hurtbox property dimensions and
position for standing and crouching states.
"""
import pygame

from src.framework.entities.player import Player
from src.framework.entities.states import CrouchingState


class TestPlayerHurtboxDimensions:
    """Hurtbox must match spec: standing 20x28 offY=4, crouching 20x18 offY=14."""

    def test_standing_hurtbox_size(self) -> None:
        player = Player(pygame.Vector2(50.0, 192.0))
        hb = player.hurtbox
        assert hb.width == 20, f"Expected width 20, got {hb.width}"
        assert hb.height == 28, f"Expected height 28, got {hb.height}"

    def test_standing_hurtbox_offset(self) -> None:
        player = Player(pygame.Vector2(50.0, 192.0))
        hb = player.hurtbox
        assert hb.top == player.rect.y + 4, (
            f"Standing hurtbox top {hb.top} != rect.y+4 ({player.rect.y + 4})"
        )

    def test_crouching_hurtbox_size(self) -> None:
        player = Player(pygame.Vector2(50.0, 192.0))
        player._change_state_instance(CrouchingState())
        hb = player.hurtbox
        assert hb.width == 20, f"Expected width 20, got {hb.width}"
        assert hb.height == 18, f"Expected height 18, got {hb.height}"

    def test_crouching_hurtbox_offset(self) -> None:
        player = Player(pygame.Vector2(50.0, 192.0))
        player._change_state_instance(CrouchingState())
        hb = player.hurtbox
        assert hb.top == player.rect.y + 14, (
            f"Crouching hurtbox top {hb.top} != rect.y+14 ({player.rect.y + 14})"
        )

    def test_bottom_aligned_to_rect_y_plus_32(self) -> None:
        """Both hurtboxes bottom at rect.y + 32 per spec."""
        player = Player(pygame.Vector2(50.0, 192.0))
        standing = player.hurtbox
        assert standing.bottom == player.rect.y + 32, (
            f"Standing hurtbox bottom {standing.bottom} != rect.y+32 ({player.rect.y + 32})"
        )
        player._change_state_instance(CrouchingState())
        crouching = player.hurtbox
        assert crouching.bottom == player.rect.y + 32, (
            f"Crouching hurtbox bottom {crouching.bottom} != rect.y+32 ({player.rect.y + 32})"
        )
