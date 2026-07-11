from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pygame

from src.engine.core import settings

if TYPE_CHECKING:
    from src.engine.audio.audio_manager import AudioManager


class DynamicMusicSystem:
    """Crossfades between traverse/combat/boss music tracks based on intensity."""

    INTENSITY_CALM = 0
    INTENSITY_COMBAT = 1
    INTENSITY_BOSS = 2

    def __init__(self, audio_manager: AudioManager) -> None:
        self._audio = audio_manager
        self._current_intensity: int = self.INTENSITY_CALM
        self._current_zone: int = 0
        self._fade_duration: float = 0.5
        self._bgm_base: str = ""

    def set_zone(self, zone: int, bgm_track: str) -> None:
        """Set the current zone and base BGM track name."""
        self._current_zone = zone
        self._bgm_base = bgm_track

    def set_intensity(self, level: int) -> None:
        """Switch to a new intensity level with crossfade."""
        if level == self._current_intensity:
            return
        self._current_intensity = level
        track = self._get_track_for_intensity(level)
        if track is not None:
            pygame.mixer.music.fadeout(int(self._fade_duration * 1000))
            pygame.time.wait(int(self._fade_duration * 1000))
            self._audio.play_music(track)

    def detect_intensity_from_state(self, has_boss: bool, has_alive_enemies: bool) -> int:
        """Auto-detect intensity from game state."""
        if has_boss:
            return self.INTENSITY_BOSS
        if has_alive_enemies:
            return self.INTENSITY_COMBAT
        return self.INTENSITY_CALM

    def _get_track_for_intensity(self, level: int) -> Path | None:
        """Map zone + intensity to a music file path."""
        bgm = self._bgm_base
        if not bgm:
            return None
        if level == self.INTENSITY_BOSS:
            suffix = "_boss"
        elif level == self.INTENSITY_COMBAT:
            suffix = "_traverse"
        else:
            suffix = "_traverse"
        candidate = settings.ASSETS_DIR / "music" / f"{bgm}{suffix}.wav"
        if candidate.exists():
            return candidate
        return settings.ASSETS_DIR / "music" / f"{bgm}.wav"
