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

logger = logging.getLogger(__name__)

class SoundBank:
    """Registry of named sounds with lazy loading."""

    SFX_DIR = settings.ASSETS_DIR / "sfx"

    def __init__(self) -> None:
        self._sounds: dict[str, pygame.mixer.Sound | None] = {}

    def load_all(self) -> None:
        """Scan assets/sfx/ recursively and register every .wav file."""
        if not self.SFX_DIR.is_dir():
            logger.warning("SoundBank: SFX dir not found: %s", self.SFX_DIR)
            return
        if pygame.mixer.get_init() is None:
            logger.warning("SoundBank: pygame.mixer not initialized, skipping load_all")
            return
        try:
            for wav_path in self.SFX_DIR.rglob("*.wav"):
                try:
                    name = wav_path.stem
                    self._sounds[name] = AssetLoader.load_sound(wav_path)
                except (pygame.error, PermissionError, OSError) as e:
                    logger.warning("SoundBank: failed to load %s: %s", wav_path, e)
        except PermissionError as e:
            logger.warning("SoundBank: cannot scan SFX dir: %s", e)
        try:
            for ogg_path in self.SFX_DIR.rglob("*.ogg"):
                try:
                    name = ogg_path.stem
                    self._sounds[name] = AssetLoader.load_sound(ogg_path)
                except (pygame.error, PermissionError, OSError) as e:
                    logger.warning("SoundBank: failed to load %s: %s", ogg_path, e)
        except PermissionError as e:
            logger.warning("SoundBank: cannot scan SFX dir: %s", e)

    def load(self, name: str, path: str | Path) -> None:
        """Register a sound by name, loading from the given path."""
        try:
            sound = AssetLoader.load_sound(path)
            self._sounds[name] = sound
        except (pygame.error, PermissionError, OSError) as e:
            logger.warning("SoundBank: failed to load sound '%s' from %s: %s", name, path, e)
            self._sounds[name] = None

    def get(self, name: str) -> pygame.mixer.Sound | None:
        """Retrieve a registered sound by name. Returns None if not found."""
        return self._sounds.get(name)

    _MAX_PITCH_CACHE = 20

    def play(self, name: str, loops: int = 0, volume: float = 1.0,
             pitch: float = 1.0, pan: tuple[float, float] | None = None) -> None:
        """Play a registered sound at the given volume and pitch. Silently skip if not found."""
        if pitch <= 0.0:
            logger.warning("SoundBank: invalid pitch %f for '%s', using 1.0", pitch, name)
            pitch = 1.0
        sound = self._sounds.get(name)
        if sound is not None:
            try:
                sound.set_volume(max(0.0, min(1.0, volume)))
                if pitch != 1.0:
                    import numpy as np
                    import pygame.sndarray
                    pitch_key = f"{name}_p{round(pitch, 2) * 100:.0f}"
                    pitched = self._sounds.get(pitch_key)
                    if pitched is None:
                        if sum(1 for k in self._sounds if k.endswith("_p")) >= self._MAX_PITCH_CACHE:
                            for k in list(self._sounds):
                                if k.endswith("_p"):
                                    del self._sounds[k]
                                    break
                        arr = pygame.sndarray.samples(sound)
                        if arr.ndim == 1:
                            arr = arr.reshape(-1, 1)
                        src_len = arr.shape[0]
                        dst_len = int(src_len / pitch)
                        indices = (np.arange(dst_len) * pitch).astype(np.int32)
                        indices = np.clip(indices, 0, src_len - 1)
                        pitched_arr = arr[indices]
                        pitched = pygame.sndarray.make_sound(pitched_arr)
                        self._sounds[pitch_key] = pitched
                    channel = pitched.play(loops=loops)
                else:
                    channel = sound.play(loops=loops)
                if channel is not None:
                    if pan is not None:
                        channel.set_volume(max(0.0, pan[0]), max(0.0, pan[1]))
            except (ImportError, ValueError, IndexError, TypeError) as _exc:
                logger.warning("SoundBank: pitch shift failed for '%s': %s", name, _exc)
                channel = sound.play(loops=loops)
                if channel is not None and pan is not None:
                    channel.set_volume(max(0.0, pan[0]), max(0.0, pan[1]))

    def contains(self, name: str) -> bool:
        """Check if a sound name is registered."""
        return name in self._sounds

    def clear(self) -> None:
        """Clear all loaded sounds."""
        self._sounds.clear()
