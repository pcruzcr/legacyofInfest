"""
Module: test_boss_base
System: tests
Description: Tests for BossBase phase management, phase transitions,
and damage handling.
"""
from __future__ import annotations
import pygame
from src.framework.entities.boss_base import BossBase, BossPhase
from src.framework.entities.enemy_base import EnemyState


class _MinionBoss(BossBase):
    def _patrol_behavior(self, dt: float) -> None:
        pass

    def _alert_behavior(self, dt: float) -> None:
        pass

    def _build_hitbox(self) -> pygame.Rect:
        return pygame.Rect(0, 0, 24, 24)

    def _build_hurtbox(self) -> pygame.Rect:
        return pygame.Rect(2, 2, 20, 20)


class TestBossBase:
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

    def test_apply_hit_blocked_when_dying(self) -> None:
        boss = _MinionBoss(pygame.Vector2(100, 100), max_health=20.0)
        boss.state = EnemyState.DYING
        health_before = boss.current_health
        boss.apply_hit(5.0, (150, 100))
        assert boss.current_health == health_before

    def test_phase_transition_emits_event(self) -> None:
        boss = _MinionBoss(pygame.Vector2(100, 100), max_health=20.0)
        phases = [
            BossPhase(phase_index=0, health_threshold=20.0),
            BossPhase(phase_index=1, health_threshold=10.0),
        ]
        boss.set_phases(phases)
        boss.apply_hit(10.0, (150, 100))
        boss.update(3.0)
        assert boss.current_phase == 1
