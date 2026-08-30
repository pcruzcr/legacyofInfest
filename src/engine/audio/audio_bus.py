"""
AudioBus — mezcla con ducking para motor genérico.

Ya existe audio_manager.py con play_sfx/play_music y SFX_POISON_TICK,
pero sin buses separados. Este módulo aporta la capa que `sonido.py:31`
describe como rara: solo 4 eventos críticos hacen ducking.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class AudioBus:
    """Tres buses + ducking. Envuelve AudioManager sin romperlo."""

    def __init__(self, manager: object | None = None) -> None:
        self.manager = manager
        self.music_vol: float = 1.0
        self.sfx_vol: float = 1.0
        self.voice_vol: float = 1.0
        self._duck_t: float = 0.0
        self._duck_dur: float = 0.6
        self._duck_amount: float = 0.35  # música baja a 65%

    def set_volumes(self, music: float | None = None, sfx: float | None = None, voice: float | None = None) -> None:
        if music is not None:
            self.music_vol = max(0.0, min(1.0, music))
        if sfx is not None:
            self.sfx_vol = max(0.0, min(1.0, sfx))
        if voice is not None:
            self.voice_vol = max(0.0, min(1.0, voice))

    def trigger_ducking(self, duration: float | None = None) -> None:
        self._duck_t = float(duration or self._duck_dur)

    def update(self, dt: float) -> None:
        if self._duck_t > 0:
            self._duck_t = max(0.0, self._duck_t - dt)

    @property
    def music_gain(self) -> float:
        if self._duck_t <= 0:
            return self.music_vol
        # Fade lineal dentro del ducking
        k = self._duck_t / self._duck_dur
        return self.music_vol * (1.0 - self._duck_amount * k)

    def play_sfx(self, name: str, volume: float = 1.0, bus: str = "sfx") -> None:
        vol = volume * (self.sfx_vol if bus == "sfx" else self.voice_vol if bus == "voice" else 1.0)
        if self.manager is not None and hasattr(self.manager, "play_sfx"):
            try:
                self.manager.play_sfx(name, volume=vol)  # type: ignore[attr-defined]
            except Exception:
                logger.debug("AudioBus.play_sfx fallo %s", name, exc_info=True)

    def play_music(self, path: object, volume: float | None = None) -> None:
        v = (volume if volume is not None else 1.0) * self.music_gain
        if self.manager is not None and hasattr(self.manager, "play_music"):
            try:
                self.manager.play_music(path, volume=v)  # type: ignore[attr-defined]
            except Exception:
                logger.debug("AudioBus.play_music fallo", exc_info=True)
