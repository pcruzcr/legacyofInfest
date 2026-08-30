"""
Module: collectible
System: stages.stage2_1_oficinas

DataChip — coleccionable de datos ("monedas/puntos") de este stage.

No es un `BaseEntity`/`EnemyBase` a propósito: los objetos de `entity_list`
sólo reciben `.update(dt)` y comprobación de contacto con el jugador si son
`EnemyBase` (ver `stage_scene.py`, el bucle de `_update_gameplay` filtra por
`isinstance(entity, EnemyBase)`); convertir un coleccionable en un
enemigo sólo para que lo actualicen heredaría daño de contacto y estados de
combate que no tienen sentido aquí. En vez de eso, `Stage21Oficinas` los
posee directamente (mismo patrón que `SecurityMonitor`) y hace su propia
comprobación de colisión contra el jugador.
"""
from __future__ import annotations

import math

import pygame

CHIP_SIZE = 14


class DataChip:
    """Chip de datos flotante. Desaparece al tocarlo; cuenta para el HUD."""

    def __init__(self, position: tuple[float, float], chip_id: int) -> None:
        self.position = pygame.Vector2(position)
        self.rect = pygame.Rect(0, 0, CHIP_SIZE, CHIP_SIZE)
        self.rect.center = (int(position[0]), int(position[1]))
        self.chip_id = chip_id
        self.collected = False
        # Fase distinta por chip para que el bobbing no se vea sincronizado
        # en los que están cerca uno de otro.
        self._t = (chip_id * 1.7) % (2 * math.pi)
        # Animación de recolección: anillo que se expande y se desvanece en
        # vez de que el chip desaparezca de golpe (Unidad de Animación —
        # transición, no sólo un blit que deja de llamarse).
        self._collect_fade: float = 0.0
        self.done = False

    def update(self, dt: float) -> None:
        if self.collected:
            if self._collect_fade > 0.0:
                self._collect_fade = max(0.0, self._collect_fade - dt / 0.35)
            else:
                self.done = True
            return
        self._t += dt * 2.4

    def check_pickup(self, player_rect: pygame.Rect) -> bool:
        if self.collected:
            return False
        if self.rect.colliderect(player_rect):
            self.collected = True
            self._collect_fade = 1.0
            return True
        return False

    def draw(self, surface: pygame.Surface, camera_offset: pygame.Vector2) -> None:
        if self.collected:
            if self._collect_fade <= 0.0:
                return
            cx = int(self.position.x - camera_offset.x)
            cy = int(self.position.y - camera_offset.y)
            t = 1.0 - self._collect_fade  # 0 -> 1 según se expande
            r = int(4 + t * 22)
            alpha = int(200 * self._collect_fade)
            ring = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(ring, (150, 235, 255, alpha), (r, r), r, 2)
            surface.blit(ring, (cx - r, cy - r), special_flags=pygame.BLEND_RGBA_ADD)
            return
        bob = math.sin(self._t) * 3.0
        cx = int(self.position.x - camera_offset.x)
        cy = int(self.position.y - camera_offset.y + bob)

        glow_r = 11
        glow = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
        pulse = 0.5 + 0.5 * math.sin(self._t * 1.6)
        pygame.draw.circle(glow, (90, 220, 255, int(60 + pulse * 40)), (glow_r, glow_r), glow_r)
        surface.blit(glow, (cx - glow_r, cy - glow_r), special_flags=pygame.BLEND_RGBA_ADD)

        # Rombo/chip, dos tonos de cian con un núcleo brillante — legible a
        # 800x600 sin depender de una hoja de sprites.
        r = 6
        pts = [(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)]
        pygame.draw.polygon(surface, (30, 140, 170, 255), pts)
        inner = [(cx, cy - r + 2), (cx + r - 2, cy), (cx, cy + r - 2), (cx - r + 2, cy)]
        pygame.draw.polygon(surface, (140, 235, 255, 255), inner)
        pygame.draw.polygon(surface, (255, 255, 255, 220),
                             [(cx, cy - 2), (cx + 2, cy), (cx, cy + 2), (cx - 2, cy)])
