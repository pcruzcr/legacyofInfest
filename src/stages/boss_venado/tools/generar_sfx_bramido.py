"""Módulo: generar_sfx_bramido
Sistema: tools (generación de assets)
Descripción: sintetiza sfx_bosses_venado_bramido_lejano.wav -- un bramido
    grave y lejano (Tarea 5 del plan de peregrinación), sin depender de
    ningún asset externo. Wav mono 44.1kHz 16-bit PCM vía el módulo stdlib
    `wave` (sin pygame, para poder correr headless sin inicializar el
    mixer). SoundBank.load_all() (sound_bank.py:34-43) registra CUALQUIER
    .wav bajo assets/sfx/ por su stem de archivo -- este nombre de archivo
    ES el nombre de sonido que _play_sfx_spatial() recibirá.

    Síntesis: dos ondas seno graves (55Hz y 82.5Hz, quinta grave) más ruido
    filtrado, con una envolvente ADSR simple (ataque rápido, caída larga) --
    un "bramido" grave y difuso, no un tono puro."""
from __future__ import annotations

import struct
import wave
from pathlib import Path

import numpy as np

_AQUI = Path(__file__).resolve()
RUTA_SALIDA = _AQUI.parents[4] / "assets" / "sfx" / "bosses" / "sfx_bosses_venado_bramido_lejano.wav"

_SAMPLE_RATE = 44100
_DURACION_S = 1.8


def _envolvente(n: int) -> np.ndarray:
    """Ataque de 80ms, sostenido breve, caída exponencial larga."""
    t = np.linspace(0.0, _DURACION_S, n, endpoint=False)
    ataque = np.clip(t / 0.08, 0.0, 1.0)
    caida = np.exp(-((t - 0.08).clip(min=0.0)) * 2.2)
    return ataque * caida


def generar(destino: Path = RUTA_SALIDA) -> None:
    n = int(_SAMPLE_RATE * _DURACION_S)
    t = np.linspace(0.0, _DURACION_S, n, endpoint=False)
    fundamental = np.sin(2.0 * np.pi * 55.0 * t)
    quinta = 0.5 * np.sin(2.0 * np.pi * 82.5 * t)
    rng = np.random.default_rng(20260824)
    ruido = rng.normal(0.0, 1.0, n)
    # Filtro paso-bajo simple (media móvil) para que el ruido suene a
    # "aliento grave", no a estática.
    ventana = 40
    kernel = np.ones(ventana) / ventana
    ruido_grave = np.convolve(ruido, kernel, mode="same") * 0.35
    señal = (fundamental + quinta + ruido_grave) * _envolvente(n)
    señal = señal / max(1e-6, np.max(np.abs(señal))) * 0.85
    pcm = (señal * 32767.0).astype(np.int16)
    destino.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(destino), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(_SAMPLE_RATE)
        w.writeframes(struct.pack(f"<{n}h", *pcm.tolist()))


def main() -> None:
    generar()
    print(f"sfx -> {RUTA_SALIDA}")


if __name__ == "__main__":
    main()
