"""
Module: test_enemy_shooter
System: tests
Description: Tests for EnemyShooter firing, projectile creation,
aiming (atan2), and fire rate limiting.
"""
from __future__ import annotations
import pygame
from src.framework.entities.enemy_shooter import EnemyShooter, Projectile
from src.framework.entities.enemy_base import EnemyState


class TestShooterFiring:
    def test_fires_toward_player(self) -> None:
        shooter = EnemyShooter(
            pygame.Vector2(0.0, 0.0),
            projectile_speed=100.0,
        )
        player_rect = pygame.Rect(100, -50, 20, 32)
        shooter.set_player_ref(player_rect)
        shooter._fire()
        assert len(shooter.get_projectiles()) == 1
        proj = shooter.get_projectiles()[0]
        assert proj.velocity.x > 0
        assert proj.velocity.y < 0

    def test_fire_rate_limits_projectiles(self) -> None:
        shooter = EnemyShooter(
            pygame.Vector2(0.0, 0.0),
            fire_rate=10.0,
        )
        player_rect = pygame.Rect(100, 0, 20, 32)
        shooter.set_player_ref(player_rect)
        for _ in range(20):
            shooter._run_state_machine(0.15)
        projectiles = shooter.get_projectiles()
        assert len(projectiles) <= 3
        assert len(projectiles) == 3

    def test_projectile_lifetime(self) -> None:
        proj = Projectile(
            pygame.Vector2(0.0, 0.0),
            pygame.Vector2(10.0, 0.0),
            damage=0.5,
            lifetime=0.1,
        )
        assert proj.is_active is True
        proj.update(0.2)
        assert proj.is_active is False

    def test_projectile_moves(self) -> None:
        proj = Projectile(
            pygame.Vector2(0.0, 0.0),
            pygame.Vector2(100.0, 0.0),
            damage=0.5,
        )
        proj.update(1.0 / 60.0)
        assert proj.position.x > 0.0

    def test_projectile_collision_expires(self) -> None:
        proj = Projectile(
            pygame.Vector2(0.0, 0.0),
            pygame.Vector2(10.0, 0.0),
            damage=0.5,
        )
        proj.on_collision()
        assert proj.is_active is False


class TestShooterState:
    def test_damage_reduces_health(self) -> None:
        shooter = EnemyShooter(
            pygame.Vector2(0.0, 0.0), max_health=3.0
        )
        shooter.apply_hit(1.0, (0.0, 0.0))
        assert abs(shooter.current_health - 2.0) < 0.01

    def test_damage_triggers_hurt_state(self) -> None:
        shooter = EnemyShooter(
            pygame.Vector2(0.0, 0.0), max_health=3.0
        )
        shooter.state = EnemyState.PATROL
        shooter.apply_hit(1.0, (0.0, 0.0))
        assert shooter.state == EnemyState.HURT

    def test_zero_health_triggers_dying(self) -> None:
        shooter = EnemyShooter(
            pygame.Vector2(0.0, 0.0), max_health=1.0
        )
        shooter.apply_hit(1.0, (0.0, 0.0))
        assert shooter.state == EnemyState.DYING
        assert shooter.is_alive is False

    def test_transitions_from_alert_to_telegraphing(self) -> None:
        shooter = EnemyShooter(
            pygame.Vector2(0.0, 0.0), fire_rate=1.0
        )
        player_rect = pygame.Rect(100, 0, 20, 32)
        shooter.set_player_ref(player_rect)
        shooter.state = EnemyState.ALERT
        shooter._alert_behavior(1.0)
        assert shooter.state == EnemyState.TELEGRAPHING
