"""
Module: checkpoint
System: framework.stage
Academic Unit: Unit II (Collision Detection), Unit IV (Event-Driven Systems)
Description: Checkpoint trigger zone. Activates once when the player
overlaps its rect, emitting CHECKPOINT_REACHED and changing visual
state from inactive (grey) to active (gold).
"""
from __future__ import annotations

import logging
from pathlib import Path

import pygame

from src.engine.core import settings
from src.engine.core.event_bus import EventBus
from src.engine.core.events import Events
from src.engine.utils.asset_loader import AssetLoader
from src.framework.entities.base_entity import BaseEntity
from src.framework.vfx.lighting import LightSource

logger = logging.getLogger(__name__)

CHECKPOINT_SPRITE_PATH: Path = settings.ASSETS_DIR / "sprites/shared/checkpoint.png"

#: Colores del estilo `brillo` (AUD-517) — apagado mientras espera, dorado
#: cálido al activarse. Mismo lenguaje de color que el rectángulo de
#: respaldo (`(100,100,100)` / `(255,215,0)`), pero como luz, no como forma.
_BRILLO_COLOR_INACTIVO: tuple[int, int, int] = (120, 150, 190)
_BRILLO_COLOR_ACTIVO: tuple[int, int, int] = (255, 215, 90)


class Checkpoint(BaseEntity):
    """Single-activation checkpoint zone."""

    def __init__(self, position: pygame.Vector2, rect: pygame.Rect, checkpoint_id: int,
                 event_bus: EventBus | None = None, brillo: bool = False) -> None:
        super().__init__(position)
        self.rect = pygame.Rect(rect)
        self._checkpoint_id: int = checkpoint_id
        self._activated: bool = False
        self.layer = 3
        self._event_bus: EventBus | None = event_bus
        self._sprite: pygame.Surface | None = None
        self._grey_sprite: pygame.Surface | None = None

        # AUD-517 — estilo opt-in: un área que brilla en vez del sprite o el
        # rectángulo de color plano. Pedido para los niveles nuevos 4.1b/4.1c
        # (GAP-065 §4), donde el checkpoint tradicional "no tiene forma"; el
        # `brillo=False` por defecto deja los otros 25 escenarios exactamente
        # como estaban — nadie tiene que optar por salir de esto.
        self._brillo: bool = brillo
        self._light: LightSource | None = None
        if brillo:
            centro = pygame.Vector2(
                self.rect.centerx, self.rect.centery)
            self._light = LightSource(
                position=centro, radius=28.0,
                color=_BRILLO_COLOR_INACTIVO, intensity=0.55,
                flicker=True, flicker_speed=1.6, flicker_amount=0.12,
            )
            return

        try:
            sprite = AssetLoader.load_image(Path(CHECKPOINT_SPRITE_PATH))
            self._sprite = sprite
            grey = sprite.copy()
            grey_overlay = pygame.Surface(grey.get_size(), pygame.SRCALPHA)
            grey_overlay.fill((100, 100, 100, 180))
            grey.blit(grey_overlay, (0, 0))
            self._grey_sprite = grey
        except (pygame.error, FileNotFoundError, PermissionError):
            logger.warning("checkpoint: failed to load sprite %s", CHECKPOINT_SPRITE_PATH)
            self._sprite = None

    def update(self, dt: float) -> None:
        """El único estado por fotograma que hace falta es el parpadeo del
        estilo `brillo` — el resto lo dirige `check_collision()`."""
        if self._light is not None:
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
        if self._light is not None:
            # El brillo pasa de una espera fría a un dorado cálido y más
            # intenso — el mismo lenguaje gris→dorado del rectángulo de
            # respaldo, sólo que como luz. `get_cached_gradient` reconstruye
            # el disco solo porque cambian color/intensidad, no hace falta
            # invalidar nada a mano.
            self._light.color = _BRILLO_COLOR_ACTIVO
            self._light.intensity = 0.95
            self._light.radius = 38.0
            self._light.flicker = False
        # AUD-019: no singleton fallback. A checkpoint without a bus simply
        # does not announce itself, which is visible in tests rather than
        # silently routed to a different bus than the listener uses.
        if self._event_bus is not None:
            self._event_bus.emit(Events.CHECKPOINT_REACHED, checkpoint_id=self._checkpoint_id)

    def draw(self, surface: pygame.Surface, camera_offset: pygame.Vector2) -> None:
        """Draw checkpoint: glow disc (`brillo`), sprite, or colored rect."""
        if not self.is_visible:
            return

        screen_x = int(self.rect.x - camera_offset.x)
        screen_y = int(self.rect.y - camera_offset.y)

        if self._light is not None:
            gradient = self._light.get_cached_gradient()
            gw, gh = gradient.get_size()
            centro_x = int(self.rect.centerx - camera_offset.x)
            centro_y = int(self.rect.centery - camera_offset.y)
            # Aditivo, no el multiplicativo de `LightSystem`: este disco
            # ilumina su propio parche de pantalla, no oscurece el resto del
            # nivel — es un área que brilla, no una fuente que compite con
            # la iluminación ambiente del escenario.
            surface.blit(gradient, (centro_x - gw // 2, centro_y - gh // 2),
                         special_flags=pygame.BLEND_RGBA_ADD)
            return

        if self._sprite is not None:
            sprite = self._grey_sprite if not self._activated else self._sprite
            surface.blit(sprite, (screen_x, screen_y))
        else:
            color = (255, 215, 0) if self._activated else (100, 100, 100)
            pygame.draw.rect(surface, color, (screen_x, screen_y, self.rect.width, self.rect.height))
            pygame.draw.rect(surface, (255, 255, 255), (screen_x, screen_y, self.rect.width, self.rect.height), 1)

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
