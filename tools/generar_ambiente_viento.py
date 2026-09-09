"""AUD-829 — genera el loop largo de viento para niebla y nieve.

`fog`/`snow` loopeaban `sfx_environment_wind_indoor.wav` (2,0 s): la
periodicidad corta se oye como un "chorro raro" mecánico, no como viento.
Este generador produce `sfx_environment_wind_loop.wav`: 8 s, mono 22050 Hz
16-bit como el resto de `assets/sfx/environment/`, con ruido marrón,
ráfagas lentas y empalme circular para que el bucle no clique.

Determinista (semilla fija): regenerar da el mismo fichero byte a byte.

Uso:
    python tools/generar_ambiente_viento.py
"""
from __future__ import annotations

import sys
import wave
from pathlib import Path

import numpy as np

RAIZ = Path(__file__).resolve().parent.parent
DESTINO = RAIZ / "assets" / "sfx" / "environment" / "sfx_environment_wind_loop.wav"

TASA = 22050
SEGUNDOS = 8
SEMILLA = 829


def generar() -> Path:
    rng = np.random.default_rng(SEMILLA)
    n = TASA * SEGUNDOS
    # Ruido marrón periódico: espectro 1/k con fases aleatorias en los bins
    # exactos de 8 s. La IFFT es periódica por construcción, así que dar la
    # vuelta no salta (ningún crossfade temporal cierra con ruido real).
    k = np.arange(1, n // 2)
    fases = rng.uniform(0.0, 2 * np.pi, size=k.shape)
    espectro = np.zeros(n // 2 + 1, dtype=np.complex128)
    espectro[1:n // 2] = (1.0 / k) * np.exp(1j * fases)
    marron = np.fft.irfft(espectro, n=n)
    marron /= max(1e-9, float(np.abs(marron).max()))
    # Ráfagas lentas con ciclos enteros en 8 s: la envolvente también es
    # periódica exacta y el empalme no cambia de nivel.
    t = np.arange(n) / TASA
    rafagas = (0.75 + 0.25 * np.sin(2 * np.pi * t / SEGUNDOS)
               + 0.1 * np.sin(2 * np.pi * 3 * t / SEGUNDOS + 1.0))
    senal = marron * rafagas
    senal *= 0.28 / max(1e-9, float(np.sqrt(np.mean(senal ** 2))))
    pcm = (np.clip(senal, -1.0, 1.0) * 32767).astype(np.int16)
    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(DESTINO), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(TASA)
        w.writeframes(pcm.tobytes())
    return DESTINO


def main() -> int:
    ruta = generar()
    print(f"escrito {ruta} ({SEGUNDOS} s @ {TASA} Hz)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
