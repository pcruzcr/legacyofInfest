"""
Module: audio_manager
System: engine
Academic Unit: N/A
Description: High-level audio playback interface. AudioManager
wraps a SoundBank and pygame.mixer to expose music and SFX
playback with volume control. Missing files are handled gracefully
(no crash — warning logged to stdout) during early development.
"""

from __future__ import annotations

import logging
import sys

import pygame

from src.engine.audio.sound_bank import SoundBank
from src.engine.utils.asset_loader import AssetLoader

_logger = logging.getLogger(__name__)


class AudioManager:
    """Music and SFX playback with volume control.

    Music is played via pygame.mixer.music (one stream channel).
    SFX are played via SoundBank / pygame.mixer.Sound on the
    available sound channels.
    """

    def __init__(self) -> None:
        """Create an AudioManager with an empty SoundBank."""
        self._sound_bank: SoundBank = SoundBank(AssetLoader)
        self._music_volume: float = 1.0
        self._sfx_volume: float = 1.0

    def _warn(self, message: str) -> None:
        """Print a warning to stdout (early-development fallback)."""
        print(f"[AudioManager] {message}", file=sys.stderr)
        _logger.warning(message)

    def play_music(
        self, name: str, loop: bool = True, fade_ms: int = 0
    ) -> None:
        """Play a music track by name.

        If the name is not registered or the file cannot be loaded,
        a warning is printed and the call is ignored (no exception).
        """
        try:
            path = self._sound_bank._names[name]
        except (KeyError, AttributeError):
            self._warn(f"Unknown music name: '{name}'")
            return
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(self._music_volume)
            if fade_ms > 0:
                pygame.mixer.music.play(fade_ms=fade_ms)
            else:
                pygame.mixer.music.play(-1 if loop else 0)
        except Exception as exc:
            self._warn(f"Cannot play music '{name}': {exc}")

    def stop_music(self, fade_ms: int = 0) -> None:
        """Stop the currently playing music track."""
        try:
            if fade_ms > 0:
                pygame.mixer.music.fadeout(fade_ms)
            else:
                pygame.mixer.music.stop()
        except Exception:
            pass

    def play_sfx(self, name: str, volume: float = 1.0) -> None:
        """Play a sound effect by name at volume (0.0-1.0).

        If the name is unknown or the sound cannot be loaded,
        a warning is printed and the call is ignored.
        """
        try:
            sound = self._sound_bank.get(name)
            sound.set_volume(max(0.0, min(1.0, volume)) * self._sfx_volume)
            sound.play()
        except (KeyError, AttributeError):
            self._warn(f"Unknown SFX name: '{name}'")
        except Exception as exc:
            self._warn(f"Cannot play SFX '{name}': {exc}")

    def set_music_volume(self, volume: float) -> None:
        """Set music volume, clamped to [0.0, 1.0]."""
        self._music_volume = max(0.0, min(1.0, volume))
        try:
            pygame.mixer.music.set_volume(self._music_volume)
        except Exception:
            pass

    def set_sfx_volume(self, volume: float) -> None:
        """Set SFX volume, clamped to [0.0, 1.0]."""
        self._sfx_volume = max(0.0, min(1.0, volume))

    def bind_sound_bank(self, sound_bank: SoundBank) -> None:
        """Replace the internal SoundBank (called during scene setup)."""
        self._sound_bank = sound_bank