"""AUD-593 — GAP-070 punto 5: la lluvia de la Fase 4 suena «a través de
una radio vieja».

La receta del dueño pide un filtro pasa-banda estrecho (~1500Hz) sobre la
lluvia **sólo en la Fase 4** — hoy el mismo bucle `rain_ambient` suena igual
en la Fase 2 que en la Fase 4, y la fase sepia del Gavilán pierde su
textura. Como en la tormenta paneada (AUD-592), cada `Fase` declara su
propio `sonido_ambiente`, así que la variante se hornea y se declara: sin
DSP en tiempo real y sin tocar el bucle genérico que usa el clima.
"""
from __future__ import annotations

import math
import os
import struct
import wave

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

from pathlib import Path

from src.engine.core import settings
from src.stages.stage4_1.fases import FASES

LLUVIA = settings.ASSETS_DIR / "sfx" / "environment" / (
    "sfx_environment_lluvia_de_radio.wav"
)

RATE = 22050


def _leer_mono(ruta: Path) -> list[int]:
    with wave.open(str(ruta), "rb") as wf:
        assert wf.getnchannels() == 1, "la variante de radio es mono"
        bruto = wf.readframes(wf.getnframes())
    return list(struct.unpack(f"<{len(bruto) // 2}h", bruto))


def _magnitud_goertzel(muestras: list[int], freq: float) -> float:
    """Magnitud espectral en una sola frecuencia, sin FFT.

    El fichero completo son 44k muestras; tres llamadas de Goertzel cuestan
    menos que cargar pygame, y para decir «la energía vive alrededor de
    1500Hz» no hace falta más resolución.
    """
    n = len(muestras)
    k = round(n * freq / RATE)
    w = 2.0 * math.pi * k / n
    coeff = 2.0 * math.cos(w)
    s1 = s2 = 0.0
    for x in muestras:
        s0 = x + coeff * s1 - s2
        s2, s1 = s1, s0
    return math.sqrt(s1 * s1 + s1 * s2 + s2 * s2)


class TestLaLluviaDeLaFase4PasaPorLaRadio:
    def test_la_fase_4_declara_su_propia_lluvia(self) -> None:
        """Deja de compartir el bucle limpio de la Fase 2 (`rain_ambient`)."""
        fase_4 = FASES[3]
        assert fase_4.sonido_ambiente is not None
        assert fase_4.sonido_ambiente.endswith(
            "sfx_environment_lluvia_de_radio.wav"
        ), f"la Fase 4 sigue con {fase_4.sonido_ambiente!r}"

    def test_el_fichero_existe_y_cierra_el_bucle(self) -> None:
        assert LLUVIA.exists(), f"falta hornear {LLUVIA.name}"
        m = _leer_mono(LLUVIA)
        inicio = sum(abs(x) for x in m[:64]) / 64.0
        final = sum(abs(x) for x in m[-64:]) / 64.0
        rms = sum(math.sqrt(x * x) for x in m[::16]) / len(m[::16])
        salto = abs(inicio - final)
        assert salto < rms * 0.25, (
            f"el bucle salta {salto:.0f} entre borde ({inicio:.0f}) y cola "
            f"({final:.0f}); RMS {rms:.0f} — clic audible cada vuelta"
        )

    def test_la_energia_vive_alrededor_de_1500hz(self) -> None:
        """Pasa-banda estrecho: pico en la banda, callado fuera de ella.

        La lluvia original es ruido paso-bajo ancho; tras la radio vieja la
        banda de 1500Hz debe dominar claramente sobre los graves (que el
        filtro quita) y sobre los agudos (que también).
        """
        m = _leer_mono(LLUVIA)
        centro = _magnitud_goertzel(m, 1500.0)
        grave = _magnitud_goertzel(m, 300.0)
        agudo = _magnitud_goertzel(m, 5000.0)
        assert centro > grave * 3.0, (
            f"quedan graves de más (300Hz={grave:.0f} vs 1500Hz={centro:.0f}): "
            "el pasa-banda no corta por abajo"
        )
        assert centro > agudo * 3.0, (
            f"quedan agudos de más (5000Hz={agudo:.0f} vs 1500Hz={centro:.0f}): "
            "el pasa-banda no corta por arriba"
        )
