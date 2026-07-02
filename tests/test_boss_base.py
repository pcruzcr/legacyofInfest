import pygame

from src.framework.entities.boss_base import BossBase, BossPhase


class _MinionBoss(BossBase):
    """Minimal concrete subclass for testing BossBase directly."""

    def _patrol_behavior(self, dt: float) -> None:
        pass

    def _alert_behavior(self, dt: float) -> None:
        pass

    def _get_animation_state(self) -> str:
        return "idle"

    def _build_hitbox(self) -> pygame.Rect:
        return pygame.Rect(0, 0, 24, 24)

    def _build_hurtbox(self) -> pygame.Rect:
        return pygame.Rect(2, 2, 20, 20)


class TestBossBase:
    """Tests for BossBase phase management."""

    def test_initial_state(self) -> None:
        boss = _MinionBoss(pygame.Vector2(100, 100), max_health=20.0)
        assert boss.current_health == 20.0
        assert boss.current_phase == 0
        assert boss.is_alive is True
        assert boss.is_transitioning is False

    def test_set_phases(self) -> None:
        boss = _MinionBoss(pygame.Vector2(100, 100), max_health=20.0)
        phases = [
            BossPhase(phase_index=0, health_threshold=20.0, attack_patterns=["idle"]),
            BossPhase(phase_index=1, health_threshold=10.0, attack_patterns=["enrage"]),
        ]
        boss.set_phases(phases)
        assert len(boss.phases) == 2
        assert boss.phase_count == 2

    def test_phase_transition_on_damage(self) -> None:
        boss = _MinionBoss(pygame.Vector2(100, 100), max_health=20.0)
        phases = [
            BossPhase(phase_index=0, health_threshold=20.0),
            BossPhase(phase_index=1, health_threshold=10.0),
        ]
        boss.set_phases(phases)
        boss.apply_hit(10.0, (150, 100))
        assert boss.current_phase == 0
        assert boss.is_transitioning is True
        boss.update(3.0)
        assert boss.is_transitioning is False
        assert boss.current_phase == 1

    def test_transition_to_phase_one(self) -> None:
        boss = _MinionBoss(pygame.Vector2(100, 100), max_health=20.0)
        phases = [
            BossPhase(phase_index=0, health_threshold=20.0),
            BossPhase(phase_index=1, health_threshold=10.0),
        ]
        boss.set_phases(phases)
        boss.apply_hit(11.0, (150, 100))
        assert boss.current_phase == 0
        assert boss.is_transitioning is True
        boss.update(3.0)
        assert boss.current_phase == 1
        assert boss.is_alive is True

    def test_boss_name(self) -> None:
        boss = _MinionBoss(pygame.Vector2(100, 100))
        boss.set_boss_name("TEST BOSS")
        assert boss.boss_name == "TEST BOSS"

    def test_invincibility_during_transition(self) -> None:
        boss = _MinionBoss(pygame.Vector2(100, 100), max_health=20.0)
        phases = [
            BossPhase(phase_index=0, health_threshold=20.0),
            BossPhase(phase_index=1, health_threshold=10.0),
        ]
        boss.set_phases(phases)
        boss.apply_hit(10.0, (150, 100))
        assert boss.is_transitioning is True
        health_before = boss.current_health
        boss.apply_hit(5.0, (150, 100))
        assert boss.current_health == health_before

    def test_draw_placeholder(self) -> None:
        boss = _MinionBoss(pygame.Vector2(100, 100), max_health=20.0)
        surf = pygame.Surface((320, 224))
        boss.draw(surf, pygame.Vector2(0, 0))
        assert surf.get_at((100, 100)) != (0, 0, 0, 255)


class TestBossVenado:
    """Tests for El Venado Sagrado concrete boss."""

    def test_import(self) -> None:
        from src.stages.boss_venado.boss_venado import BossVenado
        assert BossVenado is not None

    def test_instantiate(self) -> None:
        from src.stages.boss_venado.boss_venado import BossVenado
        boss = BossVenado(pygame.Vector2(160, 100))
        assert boss.boss_name == "VENADO SAGRADO"
        assert boss.current_health == 12.0

    def test_phases_set_on_init(self) -> None:
        from src.stages.boss_venado.boss_venado import BossVenado
        boss = BossVenado(pygame.Vector2(160, 100))
        boss.set_phases()
        assert len(boss.phases) == 2
        assert boss.phase_count == 2

    def test_update(self) -> None:
        from src.stages.boss_venado.boss_venado import BossVenado
        boss = BossVenado(pygame.Vector2(160, 100))
        boss.set_phases()
        boss.update(1.0 / 60.0)
        assert boss.position.x != 160 or boss._elapsed > 0

    def test_projectile_creation(self) -> None:
        from src.stages.boss_venado.boss_venado import BossVenado
        boss = BossVenado(pygame.Vector2(160, 100))
        boss.set_phases()
        boss._do_vine_toss(pygame.Rect(200, 100, 20, 32))
        assert len(boss._projectiles) == 1

    def test_projectile_clears_after_lifetime(self) -> None:
        from src.stages.boss_venado.boss_venado import BossVenado
        boss = BossVenado(pygame.Vector2(160, 100))
        boss.set_phases()
        boss._do_mushroom_spore()
        assert len(boss._projectiles) == 3
        for _ in range(200):
            boss._update_projectiles(1.0 / 60.0)
        alive = [p for p in boss._projectiles if p.get("alive")]
        assert len(alive) == 0

    def test_draw_no_crash(self) -> None:
        from src.stages.boss_venado.boss_venado import BossVenado
        boss = BossVenado(pygame.Vector2(160, 100))
        boss.set_phases()
        surf = pygame.Surface((320, 224))
        boss.draw(surf, pygame.Vector2(0, 0))

    def test_phase_transition_health(self) -> None:
        from src.stages.boss_venado.boss_venado import BossVenado
        boss = BossVenado(pygame.Vector2(160, 100))
        boss.set_phases()
        boss.apply_hit(6.0, (180, 100))
        assert boss.is_transitioning is True
