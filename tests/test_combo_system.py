"""
Module: test_combo_system
System: tests
Description: Tests for combo counting, combo timer, and multiplier calculation.
"""
from __future__ import annotations
import pygame
from src.engine.core import settings
from src.framework.entities.player import Player
from src.framework.entities.player_states import (
    _reset_combo,
    _start_attack,
)


class TestComboSystem:
    def test_combo_count_increments(self) -> None:
        player = Player(pygame.Vector2(0, 0))
        assert player.combo_count == 0
        _start_attack(player, Player.SHORT_ATTACK)
        assert player.combo_count == 1
        _start_attack(player, Player.SHORT_ATTACK)
        assert player.combo_count == 2
        _start_attack(player, Player.SHORT_ATTACK)
        assert player.combo_count == 3

    def test_combo_resets_on_type_change(self) -> None:
        player = Player(pygame.Vector2(0, 0))
        _start_attack(player, Player.SHORT_ATTACK)
        assert player.combo_count == 1
        _start_attack(player, Player.LONG_ATTACK)
        assert player.combo_count == 1

    def test_combo_capped_at_max(self) -> None:
        player = Player(pygame.Vector2(0, 0))
        for _ in range(5):
            _start_attack(player, Player.SHORT_ATTACK)
        assert player.combo_count <= settings.COMBO_MAX

    def test_combo_timer_decrements(self) -> None:
        player = Player(pygame.Vector2(0, 0))
        _start_attack(player, Player.SHORT_ATTACK)
        assert player.combo_timer == settings.COMBO_WINDOW
        player.combo_timer = 0.01
        player._tick_timers(0.02)
        assert player.combo_timer <= 0
        assert not player.combo_active
        assert player.combo_count == 0

    def test_combo_active_flag(self) -> None:
        player = Player(pygame.Vector2(0, 0))
        _start_attack(player, Player.SHORT_ATTACK)
        assert player.combo_active
        _reset_combo(player)
        assert not player.combo_active
        assert player.combo_count == 0

    def test_last_attack_type_tracked(self) -> None:
        player = Player(pygame.Vector2(0, 0))
        _start_attack(player, Player.SHORT_ATTACK)
        assert player.last_attack_type == "SHORT_ATTACK"
        _start_attack(player, Player.LONG_ATTACK)
        assert player.last_attack_type == "LONG_ATTACK"

    def test_combo_within_window(self) -> None:
        player = Player(pygame.Vector2(0, 0))
        _start_attack(player, Player.SHORT_ATTACK)
        player.combo_timer = 0.1
        _start_attack(player, Player.SHORT_ATTACK)
        assert player.combo_count == 2

    def test_combo_expired_window_resets(self) -> None:
        player = Player(pygame.Vector2(0, 0))
        _start_attack(player, Player.SHORT_ATTACK)
        player.combo_timer = 0.0
        player.combo_active = False
        player.combo_count = 0
        _start_attack(player, Player.SHORT_ATTACK)
        assert player.combo_count == 1

    def test_current_attack_damage_scales_with_combo(self) -> None:
        player = Player(pygame.Vector2(0, 0))
        _start_attack(player, Player.SHORT_ATTACK)
        player.combo_count = 2
        player.combo_active = True
        from src.framework.entities.player_states import ShortAttackState
        player._state_instance = ShortAttackState()
        player._active_hitbox = pygame.Rect(0, 0, 10, 10)
        dmg = player.current_attack_damage
        expected_base = 0.5
        idx = min(1, len(settings.COMBO_DAMAGE_MULT) - 1)
        assert dmg == expected_base * settings.COMBO_DAMAGE_MULT[idx]
