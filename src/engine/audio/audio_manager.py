"""
Module: audio_manager
System: engine.audio
Academic Unit: N/A
Description: High-level audio manager for music playback and sound effects.
Never crashes on missing files — logs warning and continues silently.
"""
from __future__ import annotations
import logging
import math
from pathlib import Path
import pygame

from src.engine.audio.sound_bank import SoundBank


class AudioManager:
    """Manages music and SFX playback. Graceful fallback on missing assets."""

    def __init__(self) -> None:
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

    def play_dynamic_music(self, calm_path: str | Path, combat_path: str | Path) -> None:
        """Start dynamic layered music with crossfade between calm and combat layers."""
        try:
            self._calm_sound = pygame.mixer.Sound(str(calm_path))
            self._combat_sound = pygame.mixer.Sound(str(combat_path))
            self._calm_channel = pygame.mixer.find_channel()
            self._combat_channel = pygame.mixer.find_channel()
            if self._calm_channel and self._combat_channel:
                self._calm_channel.play(self._calm_sound, loops=-1)
                self._combat_channel.play(self._combat_sound, loops=-1)
                self._calm_volume = 1.0
                self._combat_volume = 0.0
                self._intensity = 0.0
                self._target_intensity = 0.0
                self._dynamic_music_active = True
                self._calm_channel.set_volume(self._calm_volume * self._music_volume)
                self._combat_channel.set_volume(self._combat_volume * self._music_volume)
        except pygame.error as e:
            logging.warning(f"AudioManager: no se pudo cargar música dinámica: {e}")
            self._dynamic_music_active = False

    def stop_dynamic_music(self) -> None:
        """Stop dynamic music layers."""
        self._dynamic_music_active = False
        if self._calm_channel:
            self._calm_channel.stop()
        if self._combat_channel:
            self._combat_channel.stop()
        self._calm_sound = None
        self._combat_sound = None

    def set_music_intensity(self, target: float, crossfade_speed: float = 1.0) -> None:
        """Set target intensity (0.0=calm, 1.0=full combat) with crossfade speed."""
        self._target_intensity = max(0.0, min(1.0, target))
        self._crossfade_speed = crossfade_speed

    def update_dynamic_music(self, dt: float) -> None:
        """Update crossfade between music layers."""
        if not self._dynamic_music_active:
            return
        diff = self._target_intensity - self._intensity
        if abs(diff) > 0.01:
            self._intensity += math.copysign(self._crossfade_speed * dt, diff)
            self._intensity = max(0.0, min(1.0, self._intensity))
        else:
            self._intensity = self._target_intensity
        self._calm_volume = 1.0 - self._intensity
        self._combat_volume = self._intensity
        if self._calm_channel:
            self._calm_channel.set_volume(self._calm_volume * self._music_volume)
        if self._combat_channel:
            self._combat_channel.set_volume(self._combat_volume * self._music_volume)

    def stop_music(self) -> None:
        """Stop current music playback."""
        pygame.mixer.music.stop()
        self._current_music = None
        self.stop_dynamic_music()

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
        self.sound_bank.play(name, volume=self._music_volume * volume)

    def play_ambient(self, path: str | Path, volume: float = 0.5, loops: int = -1) -> None:
        """Play ambient audio layer (wind, rain, machinery) with crossfade."""
        try:
            if self._ambient_active:
                self.stop_ambient()
            self._ambient_sound = pygame.mixer.Sound(str(path))
            self._ambient_channel = pygame.mixer.find_channel()
            if self._ambient_channel:
                self._ambient_channel.play(self._ambient_sound, loops=loops)
                self._ambient_volume = max(0.0, min(1.0, volume))
                self._ambient_active = True
                if not self._muted:
                    self._ambient_channel.set_volume(self._ambient_volume * self._sfx_volume)
        except pygame.error as e:
            logging.warning(f"AudioManager: no se pudo cargar audio ambiental: {e}")
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
        old_channel = self._ambient_channel
        try:
            new_sound = pygame.mixer.Sound(str(path))
            new_channel = pygame.mixer.find_channel()
            if new_channel is not None:
                new_channel.play(new_sound, loops=-1)
                new_channel.set_volume(volume * self._sfx_volume)
                self._ambient_sound = new_sound
                self._ambient_channel = new_channel
                self._ambient_volume = volume
                self._ambient_active = True
                if old_channel is not None:
                    old_channel.fadeout(int(duration * 1000))
        except pygame.error as e:
            logging.warning(f"AudioManager: no se pudo crossfade audio ambiental: {e}")

    def play_sfx_at(self, name: str, world_x: float, screen_center_x: float = 160, volume: float = 1.0) -> None:
        """Play SFX with stereo pan based on X position relative to screen center."""
        if self._muted:
            return
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
