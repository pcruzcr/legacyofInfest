#!/usr/bin/env python3
"""AUD-814 — Audio nuevo del Stage 4.1 «La Entrada al Cementerio Sagrado».

Sintetiza desde cero (sin reutilizar audio anterior del stage):
  assets/music/mus_stage41_f1..f6.wav      (identidad musical por fase, en bucle)
  assets/sfx/environment/amb_stage41_f1..f6.wav  (cama ambiental por fase, en bucle)
  assets/sfx/environment/s41_trueno.wav, s41_despertar.wav, s41_liberacion.wav,
    s41_paso_luz.wav, s41_golpe_silencio.wav, s41_grito_halcon.wav

Todo en PCM 16 bit mono 22050 Hz con fundidos de bucle para que el ciclo no
chasquee. Niveles moderados (pico ~-6 dBFS) para no disparar check_loudness.

Uso:
    python tools/generar_stage41_audio.py
"""
from __future__ import annotations

import os
import sys
import wave

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SR = 22050


def _guardar(nombre: str, sub: str, x: np.ndarray) -> str:
    x = np.clip(x, -1.0, 1.0)
    x = (x * 28000).astype(np.int16)
    # AUD-814: `sub` ya viene como ruta relativa a RAIZ (p.ej. "assets/music").
    ruta = os.path.join(RAIZ, sub, nombre)
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with wave.open(ruta, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(x.tobytes())
    return ruta


def _bucle(x: np.ndarray, segundos: float = 0.5) -> np.ndarray:
    n = int(segundos * SR)
    n = min(n, len(x) // 4)
    rampa = np.linspace(0.0, 1.0, n)
    x[:n] = x[:n] * rampa + x[-n:] * (1.0 - rampa)
    return x[:len(x) - n]


def _tono(freq: float, dur: float, ataque: float = 0.05, decae: float = 0.3,
          arm: tuple = (1.0, 0.35, 0.12)) -> np.ndarray:
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = np.zeros(n)
    for i, a in enumerate(arm, start=1):
        x = x + a * np.sin(2 * np.pi * freq * i * t) / i
    na = max(1, int(ataque * SR))
    nd = max(1, int(decae * SR))
    env = np.ones(n)
    env[:na] = np.linspace(0, 1, na)
    env[-nd:] = np.linspace(1, 0, nd)
    return x * env / max(1e-6, np.abs(x).max())


def _acorde(frecs: list, dur: float, nivel: float = 0.2) -> np.ndarray:
    n = int(dur * SR)
    x = np.zeros(n)
    for f in frecs:
        x = x + _tono(f, dur, ataque=dur * 0.3, decae=dur * 0.4)
    return x / max(1e-6, np.abs(x).max()) * nivel


def _ruido_filtrado(dur: float, corte: float, nivel: float,
                    semilla: int) -> np.ndarray:
    rng = np.random.default_rng(semilla)
    n = int(dur * SR)
    x = rng.standard_normal(n)
    ventana = max(3, int(SR / max(50.0, corte)))
    kernel = np.ones(ventana) / ventana
    x = np.convolve(x, kernel, mode="same")
    return x / max(1e-6, np.abs(x).max()) * nivel


def _musica() -> None:
    dur = 16.0
    piezas = {
        # F1 cementerio: calidez mayor, arpegio lento.
        "mus_stage41_f1.wav": ([220.0, 277.18, 329.63, 440.0], [0.0, 2.0, 4.0, 6.0, 8.0, 10.0, 12.0]),
        # F2 venado: re menor suspendido, pulsos graves.
        "mus_stage41_f2.wav": ([146.83, 174.61, 220.0, 293.66], [0.0, 2.6, 5.2, 7.8, 10.4, 13.0]),
        # F3 serpiente: tensión, segundas menores sobre pedal.
        "mus_stage41_f3.wav": ([110.0, 116.54, 138.59, 164.81], [0.0, 1.8, 3.6, 5.4, 7.2, 9.0, 10.8, 12.6, 14.2]),
        # F4 halcón: hueco vintage, quintas abiertas + crepitación.
        "mus_stage41_f4.wav": ([196.0, 293.66, 392.0], [0.0, 3.2, 6.4, 9.6, 12.8]),
        # F5 planicie: canto grave + quintas, casi inmóvil.
        "mus_stage41_f5.wav": ([98.0, 146.83, 196.0], [0.0, 4.0, 8.0, 12.0]),
        # F6 Paburu: coral mayor solemne.
        "mus_stage41_f6.wav": ([261.63, 329.63, 392.0, 523.25], [0.0, 2.4, 4.8, 7.2, 9.6, 12.0]),
    }
    for nombre, (frecs, inicios) in piezas.items():
        n = int(dur * SR)
        x = np.zeros(n)
        for ini in inicios:
            trozo = _acorde(frecs, 3.2, nivel=0.16)
            a = int(ini * SR)
            b = min(n, a + len(trozo))
            x[a:b] = x[a:b] + trozo[:b - a]
        if nombre == "mus_stage41_f4.wav":
            rng = np.random.default_rng(77)
            x = x + (rng.standard_normal(n) > 0.998).astype(float) * 0.05
        x = _bucle(x / max(1e-6, np.abs(x).max()) * 0.5)
        _guardar(nombre, os.path.join("assets", "music"), x)
        print("musica", nombre, "%.1f s" % (len(x) / SR))


def _ambientes() -> None:
    dur = 12.0
    # F1: brisa suave + pájaros (chirridos FM escasos).
    n = int(dur * SR)
    a1 = _ruido_filtrado(dur, 400.0, 0.10, 11)
    t = np.arange(n) / SR
    for ini, f0 in ((1.5, 3200.0), (5.0, 2800.0), (9.0, 3500.0)):
        a = int(ini * SR)
        b = min(n, a + int(0.35 * SR))
        tt = np.arange(b - a) / SR
        chirr = np.sin(2 * np.pi * (f0 + 900 * np.sin(2 * np.pi * 9 * tt)) * tt)
        chirr = chirr * np.linspace(0, 1, b - a) * np.linspace(1, 0, b - a)
        a1[a:b] = a1[a:b] + chirr * 0.06
    _guardar("amb_stage41_f1.wav", os.path.join("assets", "sfx", "environment"), _bucle(a1))
    # F2: lluvia de bosque.
    a2 = _ruido_filtrado(dur, 2500.0, 0.22, 22) + _ruido_filtrado(dur, 300.0, 0.08, 23)
    _guardar("amb_stage41_f2.wav", os.path.join("assets", "sfx", "environment"), _bucle(a2))
    # F3: tormenta (lluvia densa + ráfagas).
    a3 = _ruido_filtrado(dur, 3500.0, 0.30, 33)
    env = 0.6 + 0.4 * np.sin(2 * np.pi * 0.25 * t + 1.0) ** 2
    a3 = a3 * env + _ruido_filtrado(dur, 150.0, 0.12, 34)
    _guardar("amb_stage41_f3.wav", os.path.join("assets", "sfx", "environment"), _bucle(a3))
    # F4: lluvia + ave lejana aislada.
    a4 = _ruido_filtrado(dur, 2000.0, 0.16, 44)
    a = int(7.0 * SR)
    b = min(n, a + int(0.8 * SR))
    tt = np.arange(b - a) / SR
    grito = np.sin(2 * np.pi * (1800 - 600 * tt) * tt) * np.linspace(1, 0, b - a)
    a4[a:b] = a4[a:b] + grito * 0.10
    _guardar("amb_stage41_f4.wav", os.path.join("assets", "sfx", "environment"), _bucle(a4))
    # F5: noche (grillos + canto lejano + viento).
    a5 = _ruido_filtrado(dur, 250.0, 0.06, 55)
    for ini in (2.0, 6.5, 10.0):
        a = int(ini * SR)
        b = min(n, a + int(1.2 * SR))
        tt = np.arange(b - a) / SR
        pulso = (np.sin(2 * np.pi * 22 * tt) > 0).astype(float)
        a5[a:b] = a5[a:b] + pulso * np.sin(2 * np.pi * 4300 * tt) * 0.03
    for ini, f in ((0.5, 196.0), (4.5, 164.81), (8.5, 174.61)):
        a = int(ini * SR)
        trozo = _tono(f, 2.6, ataque=0.8, decae=1.2)
        b = min(n, a + len(trozo))
        a5[a:b] = a5[a:b] + trozo[:b - a] * 0.10
    _guardar("amb_stage41_f5.wav", os.path.join("assets", "sfx", "environment"), _bucle(a5))
    # F6: solemnidad (brillo grave + aire).
    a6 = _acorde([130.81, 196.0, 261.63], dur, nivel=0.14)
    a6 = a6 + _ruido_filtrado(dur, 500.0, 0.05, 66)
    _guardar("amb_stage41_f6.wav", os.path.join("assets", "sfx", "environment"), _bucle(a6))
    # Fuego (F4 tras el tercer rayo): crepitación sobre brasa grave.
    n = int(dur * SR)
    rng = np.random.default_rng(77)
    base = _ruido_filtrado(dur, 900.0, 0.10, 78)
    chasquidos = np.zeros(n)
    for ini in rng.uniform(0, dur, 90):
        a = int(ini * SR)
        b = min(n, a + int(0.09 * SR))
        tt = np.arange(b - a) / SR
        chasquidos[a:b] += np.sin(2 * np.pi * rng.uniform(900, 2600) * tt) * np.exp(-tt * 60)
    fuego = base + chasquidos * 0.25 + _tono(55.0, dur, ataque=2.0, decae=2.0) * 0.3
    _guardar("amb_stage41_fuego.wav", os.path.join("assets", "sfx", "environment"),
             _bucle(fuego / max(1e-6, np.abs(fuego).max()) * 0.5))
    print("ambientes f1..f6 + fuego listos")


def _efectos() -> None:
    env = os.path.join("assets", "sfx", "environment")
    # Trueno: estallido grave con cola.
    n = int(2.8 * SR)
    rng = np.random.default_rng(99)
    x = rng.standard_normal(n)
    kernel = np.ones(400) / 400
    x = np.convolve(x, kernel, mode="same")
    t = np.arange(n) / SR
    x = x * np.exp(-t * 1.6) * (0.4 + 0.6 * np.exp(-t * 8))
    _guardar("s41_trueno.wav", env, x / np.abs(x).max() * 0.55)
    # Despertar: subida solemne.
    x = _tono(65.41, 3.0, ataque=1.6, decae=1.0) * 0.5
    x = x + _tono(130.81, 3.0, ataque=2.0, decae=0.8) * 0.3
    x = x + _tono(261.63, 3.0, ataque=2.4, decae=0.6) * 0.2
    _guardar("s41_despertar.wav", env, x)
    # Liberación: arpegio ascendente + brillo.
    x = np.zeros(int(2.2 * SR))
    for i, f in enumerate((392.0, 523.25, 659.25, 783.99)):
        trozo = _tono(f, 0.9, ataque=0.02, decae=0.7) * 0.3
        a = int(i * 0.28 * SR)
        x[a:a + len(trozo)] = x[a:a + len(trozo)] + trozo[:len(x) - a]
    _guardar("s41_liberacion.wav", env, x)
    # Paso de luz: pulso cálido corto.
    _guardar("s41_paso_luz.wav", env, _tono(880.0, 0.45, ataque=0.01, decae=0.4) * 0.35)
    # Golpe del silencio: impacto sordo breve (antes del shake).
    n2 = int(0.7 * SR)
    t2 = np.arange(n2) / SR
    x = np.sin(2 * np.pi * 55 * t2) * np.exp(-t2 * 9) * 0.6
    _guardar("s41_golpe_silencio.wav", env, x)
    # Grito del halcón: descendente áspero.
    n3 = int(1.1 * SR)
    t3 = np.arange(n3) / SR
    x = (np.sin(2 * np.pi * (2100 - 1100 * t3) * t3)
         + 0.4 * np.sin(2 * np.pi * (3200 - 1500 * t3) * t3))
    x = x * np.linspace(1, 0, n3) ** 0.7 * 0.3
    _guardar("s41_grito_halcon.wav", env, x)
    print("efectos s41 listos")


def main() -> None:
    _musica()
    _ambientes()
    _efectos()
    print("audio stage41 completo")


if __name__ == "__main__":
    main()
