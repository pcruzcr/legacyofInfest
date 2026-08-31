"""
Module: boss_gavilan
System: framework/entities (student boss assignment)
Academic Unit: Unit II (vectors, parametric circular motion)

Minimal Practica I slice: only Phase 1 ("El Vuelo Circular") is
implemented, per 17_BOSS_SPEC.md §5.3. No attacks, no Phase 2/3 yet.
"""
from __future__ import annotations

import math

import pygame

from src.engine.core.events import Events
from src.engine.utils.math_utils import vec2_distance, vec2_normalize
from src.framework.entities.boss_base import BossBase, BossPhase


class BossGavilan(BossBase):
    ORBIT_RADIUS = 80.0
    ORBIT_SPEED = 0.6  # rad/s — 17_BOSS_SPEC.md §5.3, Phase 1
    # GAME-100: telegraph para grade + feedback
    _telegraph = ""
    _telegraph_timer = 0.0
    TELEGRAPH_DURATION = 0.4

    def __init__(self, spawn_position: pygame.Vector2) -> None:
        super().__init__(
            spawn_position=spawn_position,
            max_health=14.0,
            damage_on_contact=0.75,
        )
        self.set_boss_name("EL GAVILAN")
        self.rect.width = 56
        self.rect.height = 40
        self._orbit_angle: float = 0.0
        # Centro de la órbita: la posición real del BossSpawn en el mapa,
        # NO un valor fijo — el arena no está en x=0 del mundo.
        self._center: pygame.Vector2 = pygame.Vector2(spawn_position)

        self._load_boss_sprites("boss_gavilan", 56, 40)
        self.set_phases([
            BossPhase(
                phase_index=0,
                health_threshold=10.0,
                attack_patterns=["DIVE", "FEATHER_STORM"],
                movement_type="orbit",
                speed_multiplier=1.0,
            ),
            BossPhase(
                phase_index=1,
                health_threshold=5.0,
                attack_patterns=["DIVE", "FEATHER_STORM", "ORBIT_SHRINK"],
                movement_type="orbit",
                speed_multiplier=1.4,
            ),
        ])
        self.on_enter_stage()

    def on_enter_stage(self) -> None:
        self._orbit_angle = 0.0

    def _patrol_behavior(self, dt: float) -> None:
        self._update_orbit(dt)

    def _alert_behavior(self, dt: float) -> None:
        self._update_orbit(dt)
        if self._telegraph:
            self._telegraph_timer -= dt
            if self._telegraph_timer <= 0:
                self._execute_telegraphed_attack()
                self._telegraph = ""
            return
        self._check_phase_transition()

    def _check_phase_transition(self) -> None:
        """phase transition con hp_threshold."""
        if self.current_phase == 0 and self.current_health <= 7.0:
            if self._event_bus:
                self._event_bus.emit(Events.BOSS_PHASE_CHANGED, phase=1)
            self._event_bus.emit(Events.BOSS_ATTACK, pattern="PHASE_CHANGE", rect=self.rect)

    def _execute_telegraphed_attack(self) -> None:
        if self._telegraph == "DIVE":
            self._do_dive()
        elif self._telegraph == "FEATHER_STORM":
            self._do_feather_storm()

    def _do_dive(self) -> None:
        self._event_bus.emit(Events.BOSS_ATTACK, pattern="DIVE", rect=self.rect)
        self._event_bus.emit(Events.PLAYER_DAMAGED, amount=0.5)

    def _do_feather_storm(self) -> None:
        self._event_bus.emit(Events.BOSS_ATTACK, pattern="FEATHER_STORM", rect=self.rect)

    def _do_orbit_shrink(self) -> None:
        self._event_bus.emit(Events.BOSS_ATTACK, pattern="ORBIT_SHRINK", rect=self.rect)

    def _update_orbit(self, dt: float) -> None:
        self._orbit_angle += self.ORBIT_SPEED * dt
        self.position.x = self._center.x + math.cos(self._orbit_angle) * self.ORBIT_RADIUS
        self.position.y = self._center.y + math.sin(self._orbit_angle) * self.ORBIT_RADIUS
        self.rect.x = int(self.position.x)
        self.rect.y = int(self.position.y)
        self._face_player()

    def _face_player(self) -> None:
        """Orienta el sprite hacia el jugador con vectores explícitos
        (Unidad II — math_utils.vec2_normalize / vec2_distance)."""
        player_ref = self._player_ref
        if player_ref is None:
            return
        boss_pos = pygame.Vector2(self.rect.center)
        player_pos = pygame.Vector2(player_ref.center)
        distance = vec2_distance(boss_pos, player_pos)
        if distance < 1e-6:
            return
        direction = vec2_normalize(player_pos - boss_pos)
        self.facing_direction = 1 if direction.x >= 0 else -1

    def _get_animation_key(self) -> str:
        return "drift"

    def _build_hitbox(self) -> pygame.Rect:
        return pygame.Rect(8, 6, 40, 28)

    def _build_hurtbox(self) -> pygame.Rect:
        ox = (self.rect.width - 40) // 2
        oy = (self.rect.height - 28) // 2
        return pygame.Rect(ox, oy, 40, 28)
