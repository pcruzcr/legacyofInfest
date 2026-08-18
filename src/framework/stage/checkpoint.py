"""
Module: checkpoint
System: framework.stage
Academic Unit: Unit II (Collision Detection), Unit IV (Event-Driven Systems)
Description: Checkpoint trigger zone. Activates once when the player
overlaps its rect, emitting CHECKPOINT_REACHED and changing visual
state from inactive (cool glow) to active (warm glow).
"""
from __future__ import annotations

import logging

import pygame

from src.engine.core.event_bus import EventBus
from src.engine.core.events import Events
from src.framework.entities.base_entity import BaseEntity
from src.framework.vfx.lighting import LightSource

logger = logging.getLogger(__name__)

#: AUD-523 — el haz de luz pasa de estilo opt-in (AUD-517, sólo 4.1/4.1b/4.1c)
#: a **el** checkpoint, en los 26 escenarios. Petición directa del dueño:
#: "eliminar el asset de los checkpoint y poner un haz de luz... que
#: indique que es un save". `assets/sprites/shared/checkpoint.png` y el
#: rectángulo de color plano de respaldo ya no existen — no hacía falta
#: conservar dos caminos de dibujo para un solo resultado final.
#:
#: Apagado mientras espera, dorado cálido al activarse.
_COLOR_INACTIVO: tuple[int, int, int] = (120, 150, 190)
_COLOR_ACTIVO: tuple[int, int, int] = (255, 215, 90)


class Checkpoint(BaseEntity):
    """Single-activation checkpoint zone."""

    def __init__(self, position: pygame.Vector2, rect: pygame.Rect, checkpoint_id: int,
                 event_bus: EventBus | None = None) -> None:
        super().__init__(position)
        self.rect = pygame.Rect(rect)
        self._checkpoint_id: int = checkpoint_id
        self._activated: bool = False
        self.layer = 3
        self._event_bus: EventBus | None = event_bus

        self._light: LightSource = LightSource(
            position=pygame.Vector2(self.rect.centerx, self.rect.centery),
            radius=28.0, color=_COLOR_INACTIVO, intensity=0.55,
            flicker=True, flicker_speed=1.6, flicker_amount=0.12,
        )

    def update(self, dt: float) -> None:
        """El único estado por fotograma que hace falta es el parpadeo del
        haz de luz — el resto lo dirige `check_collision()`."""
        self._light.update(dt)

    def check_collision(self, player_rect: pygame.Rect) -> bool:
        """Check if player overlaps this checkpoint rect. Returns True just-activated."""
        if self._activated:
            return False
        if self.rect.colliderect(player_rect):
            self.activate()
            return True
        return False

    def activate(self) -> None:
        """Activate this checkpoint and emit the event."""
        if self._activated:
            return
        self._activated = True
        # El brillo pasa de una espera fría a un dorado cálido y más
        # intenso. `get_cached_gradient` reconstruye el disco solo porque
        # cambian color/intensidad, no hace falta invalidar nada a mano.
        self._light.color = _COLOR_ACTIVO
        self._light.intensity = 0.95
        self._light.radius = 38.0
        self._light.flicker = False
        # AUD-019: no singleton fallback. A checkpoint without a bus simply
        # does not announce itself, which is visible in tests rather than
        # silently routed to a different bus than the listener uses.
        if self._event_bus is not None:
            self._event_bus.emit(Events.CHECKPOINT_REACHED, checkpoint_id=self._checkpoint_id)

    def draw(self, surface: pygame.Surface, camera_offset: pygame.Vector2) -> None:
        """Dibuja el disco de luz — aditivo, no el multiplicativo de
        `LightSystem`: ilumina su propio parche de pantalla, no oscurece el
        resto del nivel."""
        if not self.is_visible:
            return

        gradient = self._light.get_cached_gradient()
        gw, gh = gradient.get_size()
        centro_x = int(self.rect.centerx - camera_offset.x)
        centro_y = int(self.rect.centery - camera_offset.y)
        surface.blit(gradient, (centro_x - gw // 2, centro_y - gh // 2),
                     special_flags=pygame.BLEND_RGBA_ADD)

    def set_event_bus(self, event_bus: EventBus) -> None:
        """Set the event bus reference (needed when checkpoints are created before the bus is available)."""
        self._event_bus = event_bus

    @property
    def is_activated(self) -> bool:
        """Whether this checkpoint has been triggered."""
        return self._activated

    @property
    def checkpoint_id(self) -> int:
        """Unique checkpoint identifier within the stage."""
        return self._checkpoint_id
