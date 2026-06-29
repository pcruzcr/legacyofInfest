"""
Module: audio_manager
System: engine.audio
Academic Unit: N/A
Description: High-level audio manager for music playback and sound effects.
Never crashes on missing files — logs warning and continues silently.
"""
from __future__ import annotations
import logging
from pathlib import Path
import pygame

from src.engine.utils.asset_loader import AssetLoader
from src.engine.audio.sound_bank import SoundBank


class AudioManager:
    """Manages music and SFX playback. Graceful fallback on missing assets."""

    def __init__(self) -> None:
        self.sound_bank: SoundBank = SoundBank()
        self._current_music: str | None = None
        self._music_volume: float = 0.7
        self._sfx_volume: float = 1.0
        self._muted: bool = False

    def play_music(self, path: str | Path, loops: int = -1) -> None:
        """Play background music. -1 loops = infinite. Falls back silently."""
        path_str = str(path)
        try:
            pygame.mixer.music.load(path_str)
            pygame.mixer.music.set_volume(0.0 if self._muted else self._music_volume)
            pygame.mixer.music.play(loops=loops)
            self._current_music = path_str
        except pygame.error as e:
            logging.warning(f"AudioManager: no se pudo cargar música {path_str}: {e}")

    def stop_music(self) -> None:
        """Stop current music playback."""
        pygame.mixer.music.stop()
        self._current_music = None

    def pause_music(self) -> None:
        """Pause current music."""
        pygame.mixer.music.pause()

    def resume_music(self) -> None:
        """Resume paused music."""
        pygame.mixer.music.unpause()

    def play_sfx(self, name: str) -> None:
        """Play a sound effect from the sound bank."""
        if self._muted:
            return
        self.sound_bank.play(name)

    def set_music_volume(self, volume: float) -> None:
        """Set music volume (0.0 to 1.0)."""
        self._music_volume = max(0.0, min(1.0, volume))
        if not self._muted:
            pygame.mixer.music.set_volume(self._music_volume)

    def set_sfx_volume(self, volume: float) -> None:
        """Set SFX volume (0.0 to 1.0)."""
        self._sfx_volume = max(0.0, min(1.0, volume))

    def toggle_mute(self) -> None:
        """Toggle mute on/off."""
        self._muted = not self._muted
        pygame.mixer.music.set_volume(0.0 if self._muted else self._music_volume)

    @property
    def is_muted(self) -> bool:
        return self._muted

    @property
    def current_music(self) -> str | None:
        return self._current_music
