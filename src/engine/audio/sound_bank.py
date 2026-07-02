"""
Module: sound_bank
System: engine.audio
Academic Unit: N/A
Description: Named sound registry. Maps logical sound names to loaded
pygame.mixer.Sound objects with graceful missing-file handling.
"""
from __future__ import annotations
from pathlib import Path
import pygame

from src.engine.utils.asset_loader import AssetLoader


class SoundBank:
    """Registry of named sounds with lazy loading."""

    def __init__(self) -> None:
        self._sounds: dict[str, pygame.mixer.Sound | None] = {}

    def load(self, name: str, path: str | Path) -> None:
        """Register a sound by name, loading from the given path."""
        sound = AssetLoader.load_sound(path)
        self._sounds[name] = sound

    def get(self, name: str) -> pygame.mixer.Sound | None:
        """Retrieve a registered sound by name. Returns None if not found."""
        return self._sounds.get(name)

    def play(self, name: str, loops: int = 0, volume: float = 1.0) -> None:
        """Play a registered sound at the given volume. Silently skip if not found."""
        sound = self._sounds.get(name)
        if sound is not None:
            sound.set_volume(max(0.0, min(1.0, volume)))
            sound.play(loops=loops)

    def contains(self, name: str) -> bool:
        """Check if a sound name is registered."""
        return name in self._sounds

    def clear(self) -> None:
        """Clear all loaded sounds."""
        self._sounds.clear()
