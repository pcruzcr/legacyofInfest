"""
Module: test_enemy_walker
System: tests
Description: Tests for EnemyWalker patrol reversal, ledge detection,
and charge attack.
"""
from __future__ import annotations
import pygame
from src.framework.entities.enemy_walker import EnemyWalker
from src.framework.entities.enemy_base import EnemyState


class TestWalkerPatrolReversal:
    def test_reverses_after_patrol_half_length(self) -> None:
        w = EnemyWalker(pygame.Vector2(100.0, 0.0), patrol_length=96.0)
        w.facing_direction = 1
        w.update(1.0 / 60.0)
        initial_dir = w.facing_direction
        w.position.x = w._patrol_origin.x + 48.0
        w.update(1.0 / 60.0)
        assert w.facing_direction == -initial_dir

    def test_starts_right_facing(self) -> None:
        w = EnemyWalker(pygame.Vector2(0.0, 0.0), facing="right")
        assert w.facing_direction == 1

    def test_starts_left_facing(self) -> None:
        w = EnemyWalker(pygame.Vector2(0.0, 0.0), facing="left")
        assert w.facing_direction == -1


class TestWalkerLedgeDetection:
    def test_no_collision_rects_no_crash(self) -> None:
        w = EnemyWalker(pygame.Vector2(100.0, 0.0))
        w.set_collision_rects([])
        w.update(1.0 / 60.0)

    def test_reverses_on_ledge(self) -> None:
        w = EnemyWalker(pygame.Vector2(100.0, 100.0), facing="right")
        initial_dir = w.facing_direction
        w.set_collision_rects([pygame.Rect(0, 200, 50, 32)])
        w.update(1.0 / 60.0)
        assert w.facing_direction == -initial_dir


class TestWalkerDamage:
    def test_apply_hit_reduces_health(self) -> None:
        w = EnemyWalker(pygame.Vector2(0.0, 0.0), max_health=2.0)
        w.apply_hit(1.0, (0.0, 0.0))
        assert abs(w.current_health - 1.0) < 0.01

    def test_damage_triggers_hurt_state(self) -> None:
        w = EnemyWalker(pygame.Vector2(0.0, 0.0), max_health=2.0)
        w.apply_hit(1.0, (0.0, 0.0))
        assert w.state == EnemyState.HURT

    def test_death_on_zero_health(self) -> None:
        w = EnemyWalker(pygame.Vector2(0.0, 0.0), max_health=1.0)
        w.apply_hit(1.0, (0.0, 0.0))
        assert w.state == EnemyState.DYING
        assert w.is_alive is True  # alive during death animation
        w._tick_cooldowns(0.6)
        assert w.is_alive is False

    def test_charge_attack_sets_state(self) -> None:
        w = EnemyWalker(pygame.Vector2(0.0, 0.0), alert_speed=75.0)
        player_rect = pygame.Rect(100, 0, 20, 32)
        w.set_player_ref(player_rect)
        w.state = EnemyState.ALERT
        w._charge_cooldown = 0.0
        w._alert_behavior(1.0 / 60.0)
        assert w._is_charging is True
