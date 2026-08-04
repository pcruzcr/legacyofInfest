from __future__ import annotations

import pygame

from src.framework.entities.enemy_base import EnemyBase


class EnemyCharger(EnemyBase):
    """Charger enemy — rushes the player at high speed with wind-up.
    Phases: WIND_UP (telegraph) -> CHARGE (fast) -> STUN (recovery).
    """

    def __init__(
        self,
        spawn_position: pygame.Vector2,
        max_health: float = 4.0,
        damage_on_contact: float = 1.5,
        charge_speed: float = 250.0,
        zone: int = 0,
        **kwargs,
    ) -> None:
        super().__init__(
            spawn_position=spawn_position,
            max_health=max_health,
            damage_on_contact=damage_on_contact,
            detection_range_x=200.0,
            detection_range_y=48.0,
            hurt_duration=0.3,
            invincibility_duration=0.4,
        )

        self._patrol_origin: pygame.Vector2 = pygame.Vector2(spawn_position)
        self.rect.width = 28
        self.rect.height = 24
        self.position.y -= self.rect.height
        self.rect.y = int(self.position.y)

        # Charge state
        self._charge_speed: float = charge_speed
        self._charge_timer: float = 0.0
        self._charge_duration: float = 0.7
        self._wind_up_timer: float = 0.0
        self._wind_up_duration: float = 0.4
        # AUD-239 — antes esto se llamaba `_stun_timer` / `_stun_duration`, el
        # **mismo nombre** que usa `EnemyBase` para la rama `STUNNED`. Dos
        # dueños para una variable: la base la descuenta en su rama y el
        # charger en `_alert_behavior`. No chocaban porque hasta AUD-206 nadie
        # llamaba a `stun()` en producción. Esto es su recuperación tras
        # embestir, que es otra cosa.
        self._recuperacion_timer: float = 0.0
        self._recuperacion_duracion: float = 1.0
        self._is_charging: bool = False
        self._is_winding_up: bool = False
        self._is_stunned: bool = False
        self._charge_dir: int = 1

        self._load_zone_sprites(zone, 14, 12)

    def _patrol_behavior(self, dt: float) -> None:
        """Slow patrol back and forth."""
        speed = 30.0
        self.position.x += self.facing_direction * speed * dt
        distance = abs(self.position.x - self._patrol_origin.x)
        if distance >= 48:
            self.facing_direction *= -1

    def _cancelar_ataque_en_curso(self) -> None:
        """Un parry acertado cancela la embestida, no la aplaza (AUD-239).

        Sin esto, `stun()` cambiaba el estado de la base y dejaba
        `_is_charging = True`. Al volver a ALERT, `_alert_behavior` se
        encontraba la embestida a medias y la reanudaba — contra el jugador
        que se había acercado a castigar durante el aturdimiento. Con los
        0,3 s de HURT de antes de AUD-206 se confundía con un empujón; con
        0,9 s de aturdimiento es una trampa que enseña a no parar.
        """
        self._is_charging = False
        self._is_winding_up = False
        self._charge_timer = 0.0
        self._wind_up_timer = 0.0

    def _alert_behavior(self, dt: float) -> None:
        """Wind up telegraph, then charge at player."""
        self._face_player()

        if self._is_stunned:
            self._recuperacion_timer -= dt
            if self._recuperacion_timer <= 0:
                self._is_stunned = False
            return

        if self._is_winding_up:
            self._wind_up_timer -= dt
            if self._wind_up_timer <= 0:
                self._is_winding_up = False
                self._is_charging = True
                self._charge_timer = self._charge_duration
                self._charge_dir = self.facing_direction
            return

        if self._is_charging:
            self._charge_timer -= dt
            new_x = self.position.x + self._charge_dir * self._charge_speed * dt
            entity_rect = pygame.Rect(int(new_x), int(self.position.y), self.rect.width, self.rect.height)
            blocked = False
            collision_rects = self._collision_rects
            for tile in collision_rects:
                if entity_rect.colliderect(tile):
                    blocked = True
                    break
            if not blocked:
                self.position.x = new_x
            elif self._charge_timer < self._charge_duration * 0.5:
                self._charge_timer = 0.0
            if self._charge_timer <= 0:
                self._is_charging = False
                self._is_stunned = True
                self._recuperacion_timer = self._recuperacion_duracion
                self.damage_on_contact = 0.5
            return

        # Start wind-up when player in range
        if self._player_ref is not None:
            dx = self._player_ref.centerx - self.rect.centerx
            dist = abs(dx)
            if 40 <= dist <= 180:
                self._is_winding_up = True
                self._wind_up_timer = self._wind_up_duration
                self.damage_on_contact = 1.5

    def _get_animation_key(self) -> str:
        if self._is_winding_up:
            return "wind_up"
        if self._is_charging:
            return "charge"
        if self._is_stunned:
            return "stun"
        return "walk"

    def _build_hurtbox(self) -> pygame.Rect:
        # AUD-108: era el cuerpo desplazado 4 px, no una caja ajustada.
        return self.caja_ajustada(margen_x=2, margen_y=1)

    def _build_hitbox(self) -> pygame.Rect:
        return self._build_hurtbox()
