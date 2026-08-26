"""
Module: reverb_zones
System: engine.audio
Academic Unit: N/A
Description: Per-zone reverb using pre-baked variants.
"""
from __future__ import annotations

import logging

import pygame

logger = logging.getLogger(__name__)


class ReverbZone:
    """A zone with custom reverb parameters."""
    
    def __init__(
        self,
        rect: pygame.Rect,
        reverb_name: str,
        wet_level: float = 0.3,
        dry_level: float = 0.7,
        decay: float = 1.5,
        pre_delay: float = 0.02,
    ) -> None:
        self.rect = rect
        self.reverb_name = reverb_name
        self.wet_level = max(0.0, min(1.0, wet_level))
        self.dry_level = max(0.0, min(1.0, dry_level))
        self.decay = max(0.1, decay)
        self.pre_delay = max(0.0, pre_delay)


class ReverbZoneManager:
    """Manages reverb zones and applies them based on player position."""

    def __init__(self) -> None:
        self.zones: list = []
        self._active_zone = None
        self._current_reverb = "default"

    def add_zone(self, zone) -> None:
        """Add a reverb zone."""
        self.zones.append(zone)

    def remove_zone(self, zone) -> None:
        if zone in self.zones:
            self.zones.remove(zone)

    def update(self, player_pos = None) -> str | None:
        """Update active reverb zone based on player position.
        
        Returns the name of the active reverb, or None if none.
        """
        if not self.zones or player_pos is None:
            self._active_zone = None
            self._current_reverb = "default"
            return "default"

        px, py = player_pos
        player_pos_vec = (player_pos[0], player_pos[1])

        # Find the zone containing the player (first match)
        for zone in self.zones:
            if zone.rect.collidepoint(player_pos[0], player_pos[1]):
                if self._active_zone != zone:
                    self._active_zone = zone
                    self._current_reverb = zone.reverb_name
                    logging.getLogger(__name__).debug(f"Entered reverb zone: {zone.reverb_name}")
                return zone.reverb_name

        # No zone contains the player
        if self._active_zone is not None:
            logging.getLogger(__name__).debug("Left reverb zone, returning to default")
        self._active_zone = None
        self._current_reverb = "default"
        return "default"

    def get_active_reverb(self) -> str:
        return self._current_reverb

    def get_active_zone(self):
        return self._active_zone

    def get_zone_params(self) -> dict[str, float]:
        """Get parameters for the current active zone."""
        if self._active_zone is None:
            return {
                "wet": 0.0,
                "dry": 1.0,
                "decay": 0.0,
                "pre_delay": 0.0,
            }
        return {
            "wet": self._active_zone.wet_level,
            "dry": self._active_zone.dry_level,
            "decay": self._active_zone.decay,
            "pre_delay": self._active_zone.pre_delay,
        }