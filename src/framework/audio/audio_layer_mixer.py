"""
Module: audio_layer_mixer
System: framework.audio
Description: Mezclador de capas de audio narrativas — gestiona stems (instrumentos,
ambientes) que se revelan progresivamente según avance de fase/escena, no por
intensidad de combate. Complementa a DynamicMusicSystem.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

from src.engine.core import settings

if TYPE_CHECKING:
    from src.engine.audio.audio_manager import AudioManager
    from src.engine.audio.sound_bank import SoundBank


def resolver_pista_de_musica(nombre: str) -> Path | None:
    """Reutiliza la misma resolución que DynamicMusicSystem."""
    base = settings.ASSETS_DIR / "music"
    for suffix in (".ogg", ".wav", ".mp3"):
        candidato = base / f"{nombre}{suffix}"
        if candidato.exists():
            return candidato
    return None


@dataclass
class AudioLayer:
    """Una capa individual de audio (stem)."""
    nombre: str                 # p.ej. "piano", "cuerdas", "viento", "insectos"
    archivo: str                # nombre base sin extensión (resuelto via resolver_pista_de_musica)
    volumen_base: float = 1.0   # ganancia objetivo cuando está totalmente activa
    fade_ms: int = 2000         # duración del fundido de entrada/salida
    loop: bool = True           # si la capa repite
    canal_reservado: int | None = None  # canal de mixer asignado en runtime


@dataclass
class LayerSet:
    """Conjunto de capas para una zona/fase."""
    capas: dict[str, AudioLayer] = field(default_factory=dict)

    def agregar(self, layer: AudioLayer) -> None:
        self.capas[layer.nombre] = layer

    def obtener(self, nombre: str) -> AudioLayer | None:
        return self.capas.get(nombre)


class AudioLayerMixer:
    """Mezclador de capas narrativas aditivas.

    Diferencia con DynamicMusicSystem:
    - DynamicMusicSystem: UNA pista activa a la vez (calm/combat/boss), crossfade mutuo.
    - AudioLayerMixer: MÚLTIPLES capas simultáneas, cada una con su fade in/out
      independiente. Las capas se apilan (suman) para construir la banda sonora.

    Uso típico:
        mixer = AudioLayerMixer(audio_manager, sound_bank)
        mixer.cargar_fase("fase_1", {
            "piano": AudioLayer("piano", "bgm_piano", 0.4),
            "cuerdas": AudioLayer("cuerdas", "bgm_strings", 0.6),
            "ambiente": AudioLayer("ambiente", "amb_fase1", 0.5, loop=True),
        })
        mixer.activar("fase_1", ["piano"])           # entra el piano
        mixer.activar("fase_1", ["cuerdas"], 0.5)    # cuerdas al 50%
        mixer.desactivar("fase_1", ["piano"])        # sale el piano
        mixer.progreso("fase_1", 0.7)                # todas las capas al 70% de su volumen_base
    """

    def __init__(
        self,
        audio_manager: AudioManager,
        sound_bank: SoundBank,
    ) -> None:
        self._audio = audio_manager
        self._bank = sound_bank
        self._fases: dict[str, LayerSet] = {}
        self._fase_actual: str | None = None
        self._canales_activos: dict[str, Any] = {}  # layer_nombre -> canal pygame

    # ── carga / configuración ────────────────────────────────────

    def cargar_fase(self, fase_id: str, capas: dict[str, AudioLayer]) -> None:
        """Registra las capas disponibles para una fase/zona y carga sonidos al banco."""
        layer_set = LayerSet()
        for layer in capas.values():
            layer_set.agregar(layer)
            # Cargar el sonido en el SoundBank si no existe
            if self._bank.get(layer.nombre) is None:
                ruta = resolver_pista_de_musica(layer.archivo)
                if ruta is not None:
                    self._bank.load(layer.nombre, ruta)
        self._fases[fase_id] = layer_set

    def cargar_fase_desde_dict(self, fase_id: str, data: dict[str, dict]) -> None:
        """Carga desde dict plano: {'piano': {'archivo': 'bgm_piano', 'volumen_base': 0.4, ...}}"""
        capas = {k: AudioLayer(nombre=k, **v) for k, v in data.items()}
        self.cargar_fase(fase_id, capas)

    # ── control de reproducción ──────────────────────────────────

    def fase_actual(self, fase_id: str | None) -> None:
        """Cambia la fase activa. Capas de la fase anterior se funden out."""
        if fase_id == self._fase_actual:
            return
        # Fundir out fase anterior
        if self._fase_actual is not None:
            self._fundir_out_fase(self._fase_actual)
        self._fase_actual = fase_id

    def activar(self, fase_id: str, nombres: list[str], ganancia: float = 1.0) -> None:
        """Activa capas específicas de una fase con ganancia relativa (0-1)."""
        layer_set = self._fases.get(fase_id)
        if not layer_set:
            return
        for nombre in nombres:
            layer = layer_set.obtener(nombre)
            if layer:
                self._reproducir_capa(layer, ganancia)

    def progreso(self, fase_id: str, t: float) -> None:
        """Avanza todas las capas activas de una fase al factor t (0-1).

        t=0 → silencio; t=1 → volumen_base de cada capa. Interpolación lineal
        del volumen. Útil para transiciones narrativas suaves.
        """
        t = max(0.0, min(1.0, t))
        layer_set = self._fases.get(fase_id)
        if not layer_set:
            return
        for layer in layer_set.capas.values():
            if layer.nombre in self._canales_activos:
                canal = self._canales_activos[layer.nombre]
                vol = layer.volumen_base * t
                canal.set_volume(vol)

    def silenciar_todo(self, fade_ms: int | None = None) -> None:
        """Para todas las capas con fade opcional."""
        for canal in self._canales_activos.values():
            if fade_ms:
                canal.fadeout(fade_ms)
            else:
                canal.stop()
        self._canales_activos.clear()

    def desactivar(self, fase_id: str, nombres: list[str]) -> None:
        """Desactiva (fade out) capas específicas."""
        layer_set = self._fases.get(fase_id)
        if not layer_set:
            return
        for nombre in nombres:
            layer = layer_set.obtener(nombre)
            if layer and layer.nombre in self._canales_activos:
                canal = self._canales_activos.pop(layer.nombre)
                canal.fadeout(500)

    # ── internals ────────────────────────────────────────────────

    def _reproducir_capa(self, layer: AudioLayer, ganancia: float) -> None:
        canal = self._audio.play_layer(
            layer.nombre, volume=layer.volumen_base * ganancia, loops=-1 if layer.loop else 0
        )
        if canal:
            self._canales_activos[layer.nombre] = canal

    def _fundir_out_fase(self, fase_id: str) -> None:
        layer_set = self._fases.get(fase_id)
        if not layer_set:
            return
        for layer in layer_set.capas.values():
            if layer.nombre in self._canales_activos:
                canal = self._canales_activos.pop(layer.nombre)
                canal.fadeout(500)