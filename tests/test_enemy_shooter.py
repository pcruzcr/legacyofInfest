"""
Module: test_enemy_shooter
System: tests
Academic Unit: N/A
Description: Tests for EnemyShooter firing, projectile creation,
aiming (atan2), and fire rate limiting.
"""

import pygame

from src.framework.entities.enemy_shooter import EnemyShooter, Projectile


class TestShooterFiring:
    """Tests for projectile firing mechanics."""

    def test_fires_toward_player(self) -> None:
        """Projectile velocity should point toward player."""
        shooter = EnemyShooter(
            pygame.Vector2(0.0, 0.0),
            projectile_speed=100.0,
        )
        # Player to the right and above
        player_rect = pygame.Rect(100, -50, 20, 32)
        shooter.set_player_ref(player_rect)
        shooter._fire()
        assert len(shooter.get_projectiles()) == 1
        proj = shooter.get_projectiles()[0]
        # Velocity should point roughly toward player
        assert proj.velocity.x > 0, "Should move right"
        assert proj.velocity.y < 0, "Should move up"

    def test_fire_rate_limits_projectiles(self) -> None:
        """Shooter should not exceed max projectiles (_max_projectiles=3)."""
        shooter = EnemyShooter(
            pygame.Vector2(0.0, 0.0),
            fire_rate=10.0,  # 0.1s cooldown
        )
        player_rect = pygame.Rect(100, 0, 20, 32)
        shooter.set_player_ref(player_rect)
        shooter.state = "ALERT"
        # Trigger alert behavior with enough dt to fire 5 times
        for _ in range(5):
            shooter._alert_behavior(0.15)  # 150ms > 100ms cooldown
        projectiles = shooter.get_projectiles()
        assert len(projectiles) <= 3, "Should not exceed max_projectiles"
        assert len(projectiles) == 3, "All 5 fires should be capped at 3"

    def test_projectile_lifetime(self) -> None:
        """Projectile expires after lifetime."""
        proj = Projectile(
            pygame.Vector2(0.0, 0.0),
            pygame.Vector2(10.0, 0.0),
            damage=0.5,
            lifetime=0.1,
        )
        assert proj.is_active is True
        proj.update(0.2)  # exceed lifetime
        assert proj.is_active is False

    def test_projectile_moves(self) -> None:
        """Projectile position changes based on velocity."""
        proj = Projectile(
            pygame.Vector2(0.0, 0.0),
            pygame.Vector2(100.0, 0.0),
            damage=0.5,
        )
        proj.update(1.0 / 60.0)
        assert proj.position.x > 0.0, "Projectile should move right"


class TestShooterState:
    """Tests for shooter state transitions."""

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
        shooter.state = "PATROL"
        shooter.apply_hit(1.0, (0.0, 0.0))
        assert shooter.state == "HURT"

    def test_zero_health_triggers_dying(self) -> None:
        shooter = EnemyShooter(
            pygame.Vector2(0.0, 0.0), max_health=1.0
        )
        shooter.apply_hit(1.0, (0.0, 0.0))
        assert shooter.state == "DYING"
        assert shooter.is_alive is False
