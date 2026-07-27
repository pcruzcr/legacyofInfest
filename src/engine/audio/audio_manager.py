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

from src.engine.audio.sound_bank import SoundBank
from src.engine.core import settings

logger = logging.getLogger(__name__)

class AudioManager:
    """Manages music and SFX playback. Graceful fallback on missing assets."""

    def __init__(self) -> None:
        if pygame.mixer.get_init() is not None:
            pygame.mixer.set_num_channels(16)
        self.sound_bank: SoundBank = SoundBank()
        self.sound_bank.load_all()
        self._current_music: str | None = None
        self._music_volume: float = 0.7
        self._sfx_volume: float = 1.0
        self._muted: bool = False

        # Dynamic music layers
        self._calm_channel: pygame.mixer.Channel | None = None
        self._combat_channel: pygame.mixer.Channel | None = None
        self._calm_sound: pygame.mixer.Sound | None = None
        self._combat_sound: pygame.mixer.Sound | None = None
        self._intensity: float = 0.0
        self._target_intensity: float = 0.0
        self._crossfade_speed: float = 1.0
        self._calm_volume: float = 1.0
        self._combat_volume: float = 0.0
        self._dynamic_music_active: bool = False

        # Ambient audio layers
        self._ambient_sound: pygame.mixer.Sound | None = None
        self._ambient_channel: pygame.mixer.Channel | None = None
        self._ambient_volume: float = 0.5
        self._ambient_active: bool = False
        self._ambient_sounds: dict[str, pygame.mixer.Sound] = {}

    # NOTE (AUD-022): play_dynamic_music / stop_dynamic_music /
    # set_music_intensity / update_dynamic_music used to live here. They were a
    # second, complete implementation of layered dynamic music that nothing ever
    # called — framework.audio.DynamicMusicSystem implements the same feature and
    # *is* wired into StageScene. Two rival implementations of one feature, one
    # of them dead, is worse than one: it doubles the surface that can rot and
    # makes it unclear which is authoritative. The dead copy has been removed.

    def play_music(self, path: str | Path, loops: int = -1) -> None:
        """Play background music. -1 loops = infinite. Falls back silently."""
        path_str = str(path)
        try:
            pygame.mixer.music.load(path_str)
            pygame.mixer.music.set_volume(0.0 if self._muted else self._music_volume)
            pygame.mixer.music.play(loops=loops)
            self._current_music = path_str
        except (pygame.error, FileNotFoundError, OSError) as e:  # BUG-074 FIX: pygame.error no atrapa FileNotFoundError
            logger.warning("AudioManager: no se pudo cargar música %s: %s", path_str, e)

    def stop_music(self) -> None:
        """Stop current music playback."""
        pygame.mixer.music.stop()
        self._current_music = None
        self._stop_layered_channels()

    def _stop_layered_channels(self) -> None:
        """Silence the calm/combat crossfade channels if they are running.

        Retained from the removed dynamic-music layer (see the note above
        ``play_music``) because the channels are still allocated in ``__init__``
        and must be stopped when music stops.
        """
        self._dynamic_music_active = False
        if self._calm_channel:
            self._calm_channel.stop()
        if self._combat_channel:
            self._combat_channel.stop()
        self._calm_sound = None
        self._combat_sound = None

    def pause_music(self) -> None:
        """Pause current music."""
        pygame.mixer.music.pause()

    def resume_music(self) -> None:
        """Resume paused music."""
        pygame.mixer.music.unpause()

    def play_sfx(self, name: str, volume: float = 1.0) -> None:
        """Play a sound effect from the sound bank at the current SFX volume."""
        if self._muted:
            return
        self.sound_bank.play(name, volume=self._sfx_volume * volume)

    def play_stinger(self, name: str, volume: float = 0.8) -> None:
        """Play a music stinger (short SFX overlay) without interrupting music."""
        if self._muted:
            return
        self.sound_bank.play(name, volume=self._sfx_volume * volume)

    def play_ambient(self, path: str | Path, volume: float = 0.5, loops: int = -1) -> None:
        """Play ambient audio layer (wind, rain, machinery) with crossfade."""
        try:
            if self._ambient_active:
                self.stop_ambient()
            path_str = str(path)
            if path_str in self._ambient_sounds:
                self._ambient_sound = self._ambient_sounds[path_str]
            else:
                self._ambient_sound = pygame.mixer.Sound(path_str)
                self._ambient_sounds[path_str] = self._ambient_sound
            self._ambient_channel = pygame.mixer.find_channel()
            if self._ambient_channel:
                self._ambient_channel.play(self._ambient_sound, loops=loops)
                self._ambient_volume = max(0.0, min(1.0, volume))
                self._ambient_active = True
                if not self._muted:
                    self._ambient_channel.set_volume(self._ambient_volume * self._sfx_volume)
        except (pygame.error, FileNotFoundError, OSError) as e:
            logger.warning("AudioManager: no se pudo cargar audio ambiental: %s", e)
            self._ambient_active = False

    def stop_ambient(self) -> None:
        """Stop ambient audio layer."""
        self._ambient_active = False
        if self._ambient_channel:
            self._ambient_channel.stop()
        self._ambient_sound = None
        self._ambient_channel = None

    def set_ambient_volume(self, volume: float) -> None:
        """Set ambient volume (0.0 to 1.0)."""
        self._ambient_volume = max(0.0, min(1.0, volume))
        if self._ambient_channel and self._ambient_active and not self._muted:
            self._ambient_channel.set_volume(self._ambient_volume * self._sfx_volume)

    def crossfade_ambient(self, path: str | Path, duration: float = 2.0, volume: float = 0.5) -> None:
        """Crossfade from current ambient to new ambient sound."""
        if self._muted:
            return
        old_channel = self._ambient_channel
        path_str = str(path)
        try:
            if path_str in self._ambient_sounds:
                new_sound = self._ambient_sounds[path_str]
            else:
                new_sound = pygame.mixer.Sound(path_str)
                self._ambient_sounds[path_str] = new_sound
            # Fade out old channel regardless of whether new channel is available
            if old_channel is not None:
                old_channel.fadeout(int(duration * 1000))
            new_channel = pygame.mixer.find_channel()
            if new_channel is not None:
                new_channel.play(new_sound, loops=-1)
                new_channel.set_volume(volume * self._sfx_volume)
                self._ambient_sound = new_sound
                self._ambient_channel = new_channel
                self._ambient_volume = volume
                self._ambient_active = True
        except pygame.error as e:
            logger.warning("AudioManager: no se pudo crossfade audio ambiental: %s", e)
            self._ambient_active = False

    def play_sfx_at(self, name: str, world_x: float, screen_center_x: float | None = None, volume: float = 1.0) -> None:
        """Play SFX with stereo pan based on X position relative to screen center."""
        if self._muted:
            return
        if screen_center_x is None or screen_center_x <= 0:
            screen_center_x = settings.INTERNAL_WIDTH / 2.0
        pan = max(-1.0, min(1.0, (world_x - screen_center_x) / screen_center_x))
        left = 1.0 - max(0.0, pan)
        right = 1.0 + min(0.0, pan)
        self.sound_bank.play(name, volume=self._sfx_volume * volume, pan=(left, right))

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
        if self._ambient_channel:
            self._ambient_channel.set_volume(0.0 if self._muted else self._ambient_volume * self._sfx_volume)

    @property
    def music_volume(self) -> float:
        return self._music_volume

    @music_volume.setter
    def music_volume(self, value: float) -> None:
        self.set_music_volume(value)

    @property
    def sfx_volume(self) -> float:
        return self._sfx_volume

    @sfx_volume.setter
    def sfx_volume(self, value: float) -> None:
        self.set_sfx_volume(value)

    @property
    def is_muted(self) -> bool:
        return self._muted

    @property
    def current_music(self) -> str | None:
        return self._current_music
