"""
Module: sound_bank
System: engine.audio
Academic Unit: N/A
Description: Named sound registry. Maps logical sound names to loaded
pygame.mixer.Sound objects with graceful missing-file handling.
"""
from __future__ import annotations
import logging
from pathlib import Path
import pygame

from src.engine.core import settings
from src.engine.utils.asset_loader import AssetLoader


class SoundBank:
    """Registry of named sounds with lazy loading."""

    SFX_DIR = settings.ASSETS_DIR / "sfx"

    def __init__(self) -> None:
        self._sounds: dict[str, pygame.mixer.Sound | None] = {}

    def load_all(self) -> None:
        """Scan assets/sfx/ recursively and register every .wav file."""
        if not self.SFX_DIR.is_dir():
            logging.warning(f"SoundBank: SFX dir not found: {self.SFX_DIR}")
            return
        for wav_path in self.SFX_DIR.rglob("*.wav"):
            name = wav_path.stem  # e.g. "sfx_player_jump"
            self._sounds[name] = AssetLoader.load_sound(wav_path)

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
