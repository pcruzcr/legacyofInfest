"""
Module: test_player_damage
System: tests
Academic Unit: N/A
Description: Tests for Player damage system: health reduction,
invincibility, knockback, and event emission.
"""
import pygame

from src.engine.core import settings
from src.engine.core.event_bus import subscribe, emit, dispatch, clear
from src.framework.entities.player import Player


class TestDamageApplication:
    """Tests for damage application and health tracking."""

    def test_damage_reduces_health(self) -> None:
        player = Player(pygame.Vector2(50.0, 0.0))
        initial = player.current_health
        player.apply_damage(0.5, (50.0, 0.0))
        assert abs(player.current_health - (initial - 0.5)) < 0.01, (
            f"Expected {initial - 0.5}, got {player.current_health}"
        )

    def test_damage_clamped_at_zero(self) -> None:
        player = Player(pygame.Vector2(50.0, 0.0))
        # Apply massive damage
        player.apply_damage(100.0, (50.0, 0.0))
        assert player.current_health >= 0.0, (
            f"Health should not be negative, got {player.current_health}"
        )
        assert abs(player.current_health) < 0.01, (
            f"Health should be 0, got {player.current_health}"
        )


class TestInvincibility:
    """Tests for invincibility frames after damage."""

    def test_invincibility_blocks_repeat_damage(self) -> None:
        player = Player(pygame.Vector2(50.0, 0.0))
        player.apply_damage(0.5, (50.0, 0.0))
        health_after_first = player.current_health
        # Second hit within invincibility window should be blocked
        player.apply_damage(0.5, (50.0, 0.0))
        assert abs(player.current_health - health_after_first) < 0.01, (
            "Second hit should be blocked by invincibility"
        )

    def test_invincibility_expires(self) -> None:
        player = Player(pygame.Vector2(50.0, 0.0))
        player.apply_damage(0.5, (50.0, 0.0))
        health_after_first = player.current_health
        # Simulate 1.5s of invincibility elapsing
        player._invincibility_timer = 0.0
        player.apply_damage(0.5, (50.0, 0.0))
        expected = health_after_first - 0.5
        assert abs(player.current_health - expected) < 0.01, (
            f"Expected {expected}, got {player.current_health}"
        )


class TestEvents:
    """Tests for event emission on damage."""

    def test_player_died_emitted_at_zero_health(self) -> None:
        clear()
        player = Player(pygame.Vector2(50.0, 0.0))
        died_emitted = False

        def _on_died() -> None:
            nonlocal died_emitted
            died_emitted = True

        subscribe("PLAYER_DIED", _on_died)
        player.apply_damage(settings.PLAYER_MAX_HEALTH, (50.0, 0.0))
        dispatch()
        assert died_emitted is True, "PLAYER_DIED should have been emitted"

    def test_player_damaged_always_emitted_on_successful_hit(self) -> None:
        clear()
        player = Player(pygame.Vector2(50.0, 0.0))
        damaged_data: dict = {}

        def _on_damaged(**data: object) -> None:
            nonlocal damaged_data
            damaged_data = dict(data)

        subscribe("PLAYER_DAMAGED", _on_damaged)
        player.apply_damage(0.5, (100.0, 0.0))
        dispatch()
        assert "amount" in damaged_data, "PLAYER_DAMAGED should have amount"
        assert abs(damaged_data["amount"] - 0.5) < 0.01, (
            f"Expected amount 0.5, got {damaged_data.get('amount')}"
        )


class TestKnockback:
    """Tests for knockback velocity on damage."""

    def test_knockback_velocity_applied(self) -> None:
        player = Player(pygame.Vector2(50.0, 0.0))
        # Damage from the right (source at x=100)
        player.apply_damage(0.5, (100.0, 0.0))
        # Knockback should be away from source (to the left = negative)
        assert player.velocity.x < 0, (
            f"Knockback should be leftward (negative), got {player.velocity.x}"
        )
        assert abs(player.velocity.x - (-150.0)) < 0.01, (
            f"Expected knockback x=-150, got {player.velocity.x}"
        )
        assert abs(player.velocity.y - (-200.0)) < 0.01, (
            f"Expected knockback y=-200, got {player.velocity.y}"
        )


class TestPlayerDraw:
    """Test draw fallback when sprite frames are empty."""

    def test_fallback_draw_does_not_crash(self) -> None:
        player = Player(pygame.Vector2(50.0, 0.0))
        # Clear all sprite frames to force the fallback code path
        player._sprite_frames = {}
        surface = pygame.Surface((320, 224))
        cam = pygame.Vector2(0, 0)
        player.draw(surface, cam)

    def test_fallback_draw_colored_rect(self) -> None:
        player = Player(pygame.Vector2(50.0, 0.0))
        player._sprite_frames = {}
        surface = pygame.Surface((320, 224))
        surface.fill((0, 0, 0))
        cam = pygame.Vector2(0, 0)
        player.draw(surface, cam)
        # Blue rect (0, 120, 255) should be drawn at (50, 0)
        px = surface.get_at((55, 10))[:3]
        assert px == (0, 120, 255), f"Expected blue fallback rect, got {px}"
