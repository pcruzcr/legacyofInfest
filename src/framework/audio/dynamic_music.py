from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from src.engine.core import settings

if TYPE_CHECKING:
    from src.engine.audio.audio_manager import AudioManager


def resolver_pista_de_musica(nombre: str) -> Path | None:
    """Ruta de `assets/music/<nombre>` prefiriendo `.ogg` sobre `.wav`.

    AUD-485 — AUD-484 convirtió las 78 muestras de audio del proyecto a OGG
    Vorbis (10,3 MB → 577 KB en la pista más pesada), pero dejó el `.wav`
    original al lado de cada una: es la forma segura de convertir, no la de
    terminar la migración. Antes de este cambio, `stage_scene.py` y
    `_get_track_for_intensity` comprobaban `.wav` primero, así que con los
    dos ficheros presentes la conversión no ahorraba ni un byte de carga.

    Preferir `.ogg` aquí era **inseguro** hasta comprobarlo: AUD-159 dejó
    tres `.ogg` mal etiquetados a propósito (en realidad WAV, ver
    `tests/test_auditoria_157_160.py::TestLaMusicaSuena`) protegidos
    exactamente por ese orden — «wav gana» los volvía inalcanzables en vez
    de silenciar un escenario. Medido antes de tocar esto: hoy no hay ningún
    `.ogg` en `assets/music/` que no sea uno de los 78 recién convertidos por
    `tools/convert_audio.py`, todos con cabecera `OggS` real. La protección
    de AUD-159 no tenía nada que proteger ya.
    """
    base = settings.ASSETS_DIR / "music"
    for suffix in (".ogg", ".wav"):
        candidato = base / f"{nombre}{suffix}"
        if candidato.exists():
            return candidato
    return None


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
        """Switch to a new intensity level with fade-in on the new track.

        AUD-313 — `_fade_duration` se declaraba y nadie lo leía: cada
        transición calm↔combat reiniciaba la pista de golpe. SDL_mixer tiene
        un único canal de música, así que un *crossfade* verdadero (dos pistas
        sonando a la vez) no es posible; lo honesto es fundir la entrada de la
        nueva pista. El fundido se hace dentro del audio manager, que es quien
        habla con pygame.mixer.music.
        """
        if level == self._current_intensity:
            return
        track = self._get_track_for_intensity(level)
        if track is None:
            return
        self._current_intensity = level
        if self._audio is not None:
            self._audio.play_music(track, fundido_ms=int(self._fade_duration * 1000))

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
        sufijos: tuple[str, ...]
        if level == self.INTENSITY_BOSS:
            sufijos = ("_boss", "_traverse", "")
        elif level == self.INTENSITY_COMBAT:
            sufijos = ("_combat", "_traverse", "")
        else:
            sufijos = ("_traverse", "")
        for sufijo in sufijos:
            pista = resolver_pista_de_musica(f"{bgm}{sufijo}")
            if pista is not None:
                return pista
        return None
