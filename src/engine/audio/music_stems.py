"""
Module: music_stems
System: engine.audio
Academic Unit: N/A
Description: Dynamic music stems with crossfading for adaptive music.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import pygame

logger = logging.getLogger(__name__)


class MusicStem:
    """A single stem (layer) of a dynamic music track."""

    def __init__(
        self,
        name: str,
        path: str | Path,
        loops: int = -1,
        volume: float = 1.0,
    ) -> None:
        self.name = name
        self.path = Path(path)
        self.loops = loops
        self.base_volume = max(0.0, min(1.0, volume))
        self._sound: pygame.mixer.Sound | None = None
        self._channel: pygame.mixer.Channel | None = None
        self._target_volume: float = 0.0
        self._current_volume: float = 0.0
        self._fade_speed: float = 1.0  # volume units per second
        self._fade_in: float = 0.0
        self._fade_out: float = 0.0

    def load(self) -> bool:
        """Load the stem audio file."""
        try:
            import pygame
            self._sound = pygame.mixer.Sound(str(self.path))
            return True
        except (pygame.error, FileNotFoundError, OSError) as e:
            logging.getLogger(__name__).warning(
                "MusicStem '%s' failed to load: %s", self.name, e
            )
            return False

    def play(self, loops: int = -1, fade_in: float = 0.0) -> None:
        """Start playing the stem."""
        import pygame
        if self._sound is None:
            import pygame
            self._sound = pygame.mixer.Sound(str(self.path))
        self._target_volume = self.base_volume
        self._fade_in = fade_in
        self._fade_out = 0.0
        if self._channel is None:
            self._channel = pygame.mixer.find_channel()
        if self._channel is not None:
            self._channel.play(self._sound, loops=loops)
            self._channel.set_volume(0.0 if fade_in > 0.0 else self.base_volume)
            self._fade_in = fade_in

    def stop(self, fade_out: float = 0.0) -> None:
        """Stop the stem with optional fade out."""
        self._fade_out = fade_out
        self._fade_in = 0.0
        self._target_volume = 0.0

    def set_volume(self, volume: float, fade_time: float = 0.0) -> None:
        """Set target volume with optional crossfade."""
        self._target_volume = max(0.0, min(1.0, volume))
        if fade_time > 0.0:
            self._fade_speed = abs(self._current_volume - self._target_volume) / fade_time
        else:
            self._current_volume = self._target_volume

    def update(self, dt: float) -> None:
        """Update fade in/out."""
        if self._channel is None:
            return

        if self._fade_in > 0.0:
            self._current_volume = min(self._target_volume, self._current_volume + dt / self._fade_in)
            self._fade_in -= dt
            if self._fade_in <= 0:
                self._fade_in = 0.0
        elif self._fade_out > 0.0:
            self._current_volume = max(0.0, self._current_volume - dt / self._fade_out)
            self._fade_out -= dt
            if self._fade_out <= 0:
                self._fade_out = 0.0
                if self._channel:
                    self._channel.stop()
                    self._channel = None

        if self._channel:
            self._channel.set_volume(self._current_volume)


class MusicStemManager:
    """Manages multiple music stems for dynamic adaptive music."""

    def __init__(self) -> None:
        self.stems: dict[str, Any] = {}
        self._active_stems: set[str] = set()

    def add_stem(self, name: str, path: str | Path,
                 loops: int = -1, volume: float = 1.0) -> None:
        """Add a new music stem."""
        from music_stems import MusicStem
        stem = MusicStem(name, path, loops=loops, volume=volume)
        if stem.load():
            self.stems[name] = stem

    def play_stem(self, name: str, fade_in: float = 2.0) -> bool:
        """Start playing a stem with fade-in."""
        stem = self.stems.get(name)
        if stem is None:
            return False
        stem.play(fade_in=fade_in)
        self._active_stems.add(name)
        return True

    def stop_stem(self, name: str, fade_out: float = 2.0) -> bool:
        """Stop a stem with fade-out."""
        stem = self.stems.get(name)
        if stem is None:
            return False
        stem.stop(fade_out=fade_out)
        self._active_stems.discard(name)
        return True

    def set_stem_volume(self, name: str, volume: float, fade_time: float = 2.0) -> bool:
        """Crossfade a stem to a new volume."""
        stem = self.stems.get(name)
        if stem is None:
            return False
        stem.set_volume(volume, fade_time=fade_time)
        return True

    def crossfade(self, from_name: str, to_name: str, duration: float = 3.0) -> bool:
        """Crossfade from one stem to another."""
        from_stem = self.stems.get(from_name)
        to_stem = self.stems.get(to_name)
        if from_stem is None or to_stem is None:
            return False

        from_stem.stop(fade_out=duration)
        to_stem.play(fade_in=duration)
        self._active_stems.discard(from_name)
        self._active_stems.add(to_name)
        return True

    def get_active_stems(self) -> list[str]:
        return list(self._active_stems)

    def update(self, dt: float) -> None:
        """Update all active stems (handle fades)."""
        from music_stems import MusicStem
        for stem in self.stems.values():
            if isinstance(stem, MusicStem) and (stem.name in self._active_stems or stem._channel is not None):
                stem.update(dt)

        # Clean up finished stems
        finished = [name for name, stem in self.stems.items()
                    if name not in self._active_stems and getattr(stem, '_channel', None) is None]
        for name in finished:
            self._active_stems.discard(name)

    def get_stem(self, name: str):
        return self.stems.get(name)

    def stop_all(self, fade_out: float = 2.0) -> None:
        """Stop all stems."""
        for stem in self.stems.values():
            if stem._channel:
                stem.stop(fade_out=fade_out)
        self._active_stems.clear()