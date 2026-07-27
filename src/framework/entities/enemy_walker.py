"""
Module: enemy_walker
System: framework.entities
Academic Unit: Unit II (Vectors, Collision), Unit III (State Machines)
Description: Ground-bound enemy that patrols horizontally along a defined
segment. Reverses at patrol limits or ledge edges. Accelerates toward
player when detected.
"""
from __future__ import annotations

import pygame

from src.framework.entities.enemy_base import EnemyBase


class EnemyWalker(EnemyBase):
    """
    Walker enemy — horizontal patrol with ledge detection.
    Inherits from EnemyBase. Implements _patrol_behavior and _alert_behavior.
    """

    def __init__(
        self,
        spawn_position: pygame.Vector2,
        patrol_length: float = 96.0,
        facing: str = "right",
        patrol_speed: float = 45.0,
        alert_speed: float = 75.0,
        damage_on_contact: float = 0.5,
        max_health: float = 2.0,
        zone: int = 0,
        **kwargs,
    ) -> None:
        """Initialize the walker enemy."""
        super().__init__(
            spawn_position=spawn_position,
            max_health=max_health,
            damage_on_contact=damage_on_contact,
            detection_range_x=160.0,
            detection_range_y=48.0,
        )

        self.patrol_length: float = patrol_length
        self.patrol_speed: float = patrol_speed
        self.alert_speed: float = alert_speed
        self._patrol_origin: pygame.Vector2 = pygame.Vector2(spawn_position)
        self._collision_rects: list[pygame.Rect] = []
        self._one_way_rects: list[pygame.Rect] = []

        # Set initial facing direction
        self.facing_direction = 1 if facing == "right" else -1

        # Set rect size
        self.rect.width = 24
        self.rect.height = 28
        self.position.y -= self.rect.height
        self.rect.y = int(self.position.y)

        # Load sprites
        self._load_zone_sprites(zone, 16, 12)

        # --- Charge attack state ---
        self._charge_timer: float = 0.0
        self._charge_duration: float = 0.6
        self._charge_cooldown: float = 0.0
        self._charge_speed: float = alert_speed * 3.0
        self._is_charging: bool = False
        self._charge_damage_mult: float = 1.5

        # Cached surfaces
        self._charge_warn_surf: pygame.Surface | None = None
        self._charge_warn_size: tuple[int, int] = (0, 0)

    def set_collision_rects(self, rects: list[pygame.Rect], one_way: list[pygame.Rect] | None = None) -> None:
        """Provide collision rects for ledge detection and Y-snapping."""
        self._collision_rects = rects
        self._one_way_rects = one_way or []

    @property
    def _all_ground_rects(self) -> list[pygame.Rect]:
        return self._collision_rects + self._one_way_rects

    # ──────────────────────────────────────────────
    # Behavior implementations
    # ──────────────────────────────────────────────

    def _patrol_behavior(self, dt: float) -> None:
        """Move at patrol speed. Reverse at patrol limit or ledge edge."""
        reversed_this_frame = False

        all_ground = self._all_ground_rects

        # Ledge detection: probe ahead and below before moving
        if all_ground:
            probe_x = self.position.x + (
                self.facing_direction * (self.rect.width // 2 + 2)
            )
            probe_y = self.position.y + self.rect.height + 2
            has_floor = any(
                r.collidepoint(probe_x, probe_y)
                for r in all_ground
            )
            if not has_floor:
                self.facing_direction *= -1
                reversed_this_frame = True

        # Patrol limit reversal (skip if already reversed for ledge)
        if not reversed_this_frame:
            distance = abs(self.position.x - self._patrol_origin.x)
            if distance >= self.patrol_length / 2:
                self.facing_direction *= -1

        # Move
        self.position.x += self.facing_direction * self.patrol_speed * dt

    def _post_update(self, dt: float) -> None:
        all_rects = self._all_ground_rects
        if all_rects:
            feet_y = self.position.y + self.rect.height
            for rect in all_rects:
                if (rect.top <= feet_y < rect.bottom
                        and rect.left < self.rect.centerx < rect.right):
                    self.position.y = rect.top - self.rect.height
                    break

    def _alert_behavior(self, dt: float) -> None:
        """Move toward player at alert speed. Use charge attack at range."""
        self._face_player()

        # Charge attack logic
        self._charge_cooldown = max(0.0, self._charge_cooldown - dt)
        if self._is_charging:
            self._charge_timer -= dt
            if self._charge_timer <= 0:
                self._is_charging = False
                self._charge_cooldown = 2.0
                self.damage_on_contact = 0.5
            else:
                self.position.x += self.facing_direction * self._charge_speed * dt
                return

        # Start charge when at medium range and cooldown ready
        if self._player_ref is not None:
            dx = self._player_ref.centerx - self.rect.centerx
            dist = abs(dx)
            if 60 <= dist <= 140 and self._charge_cooldown <= 0 and not self._is_charging:
                self._is_charging = True
                self._charge_timer = self._charge_duration
                self.damage_on_contact = 1.5
                return

        # AUD-050: la táctica que SquadBrain decidió para este enemigo modula la
        # dirección y el ritmo. Antes el walker sólo sabía avanzar hacia el
        # jugador, así que "retreat" y "evade" eran acciones que el predictor
        # podía emitir y nadie obedecía — el modelo estaba conectado a la nada.
        direction = self.facing_direction
        speed = self.alert_speed

        if self.tactic in ("retreat", "evade"):
            # Retrocede manteniendo la cara hacia el jugador: leerlo como huida
            # y no como despiste es lo que le permite al jugador presionar.
            direction = -self.facing_direction
            speed = self.alert_speed * (1.2 if self.tactic == "evade" else 0.9)
        elif self.tactic == "wait":
            speed = 0.0
        elif self.tactic == "circle":
            # Orbita: avanza a media velocidad, lo que abre hueco para que otro
            # enemigo flanquee. Es lo que hace que un grupo se lea como grupo.
            speed = self.alert_speed * 0.45
        elif self.tactic == "charge":
            speed = self.alert_speed * 1.35

        all_ground = self._all_ground_rects
        if all_ground and speed > 0.0:
            probe_x = self.position.x + (
                direction * (self.rect.width // 2 + 2)
            )
            probe_y = self.position.y + self.rect.height + 2
            has_floor = any(
                r.collidepoint(probe_x, probe_y)
                for r in all_ground
            )
            if not has_floor:
                # Un borde detiene la retirada en lugar de invertir el rumbo: un
                # enemigo que retrocede hacia el jugador al llegar a un borde se
                # lee como un bug, no como decisión.
                if self.tactic in ("retreat", "evade"):
                    speed = 0.0
                else:
                    self.facing_direction *= -1
                    direction = self.facing_direction

        self.position.x += direction * speed * dt

    def _get_animation_key(self) -> str:
        return "walk"

    def _build_hurtbox(self) -> pygame.Rect:
        return pygame.Rect(4, 2, 24, 28)

    def _build_hitbox(self) -> pygame.Rect:
        return self._build_hurtbox()

    def draw(self, surface: pygame.Surface, camera_offset: pygame.Vector2) -> None:
        super().draw(surface, camera_offset)
        if self._is_charging:
            progress = 1.0 - (self._charge_timer / self._charge_duration)
            sx = int(self.position.x - camera_offset.x - 16)
            sy = int(self.position.y - camera_offset.y - 20 - progress * 10)
            w = int(32 + progress * 16)
            h = 4
            alpha = int(180 + 75 * (1.0 - progress))
            size = (w, h)
            if (self._charge_warn_surf is None
                    or self._charge_warn_size != size):
                self._charge_warn_surf = pygame.Surface(size)
                self._charge_warn_size = size
            warn = self._charge_warn_surf
            warn.set_alpha(alpha)
            warn.fill((255, 50, 50))
            surface.blit(warn, (sx, sy))
