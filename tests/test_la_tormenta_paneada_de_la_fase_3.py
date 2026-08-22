"""AUD-592 — GAP-070 punto 4: la tormenta de la Fase 3 ya se panea.

La receta del dueño pedía para la tormenta un **LFO de paneo oscilando
-0.8↔0.8** y un **LFO de filtro barriendo 400-2200Hz**. GAP-070 lo dejó
abierto con una pregunta de arquitectura («¿variantes horneadas o DSP en
tiempo real?») que el propio diseño del nivel respondió sin decirlo: cada
`Fase` declara su propio `sonido_ambiente`, así que la variante horneada es
el camino natural — el mismo que ya demostró `rafaga_viento` con
`_write_wav_stereo`, el primer `.wav` estéreo del proyecto.

Éste es el segundo. El bucle dura 2s y los dos LFO cierran ciclos enteros
dentro de él, así que la vuelta del bucle no hace clic: el paneo y el corte
valen lo mismo en la última muestra que en la primera.
"""
from __future__ import annotations

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import struct
import wave
from pathlib import Path

from src.engine.core import settings
from src.stages.stage4_1.fases import FASES

TORMENTA = settings.ASSETS_DIR / "sfx" / "environment" / (
    "sfx_environment_tormenta_paneada.wav"
)

#: El pico de paneo que pide la receta: ±0.8.
PICO_DE_PANEO = 0.8


def _leer_estereo(ruta: Path) -> tuple[int, list[tuple[int, int]]]:
    with wave.open(str(ruta), "rb") as wf:
        canales = wf.getnchannels()
        bruto = wf.readframes(wf.getnframes())
    muestras = [
        struct.unpack("<hh", bruto[i:i + 4])
        for i in range(0, len(bruto) - 3, 4)
    ]
    return canales, muestras


class TestLaTormentaDeLaFase3SePanea:
    def test_la_fase_3_declara_su_propia_tormenta(self) -> None:
        """Deja de compartir el bucle genérico del clima (`storm_ambient`)."""
        fase_3 = FASES[2]
        assert fase_3.sonido_ambiente is not None
        assert fase_3.sonido_ambiente.endswith(
            "sfx_environment_tormenta_paneada.wav"
        ), f"la Fase 3 sigue con {fase_3.sonido_ambiente!r}"

    def test_el_fichero_existe_y_es_estereo(self) -> None:
        assert TORMENTA.exists(), f"falta hornear {TORMENTA.name}"
        canales, _ = _leer_estereo(TORMENTA)
        assert canales == 2, (
            "un paneo de verdad necesita dos canales: el fichero salió mono"
        )

    def test_el_bucle_no_hace_clic(self) -> None:
        """Los dos LFO cierran ciclo dentro del bucle: el borde es continuo.

        Con muestras de 16 bits, un salto del orden del propio RMS del
        audio sería un chasquido audible; exigimos que el borde quede muy
        por debajo.
        """
        _, m = _leer_estereo(TORMENTA)
        inicio = sum(abs(a) + abs(b) for a, b in m[:64]) / 128.0
        final = sum(abs(a) + abs(b) for a, b in m[-64:]) / 128.0
        salto = abs(inicio - final)
        rms = sum((a * a + b * b) ** 0.5 / 2**0.5 for a, b in m[::16]) / len(m[::16])
        assert salto < rms * 0.25, (
            f"el bucle salta {salto:.0f} entre su borde ({inicio:.0f}) y su "
            f"cola ({final:.0f}); el RMS es {rms:.0f} — clic audible"
        )

    def test_el_paneo_visita_los_dos_lados(self) -> None:
        """En alguna ventana el canal dominante supera al otro con fuerza,
        y hay ventanas de los dos signos.

        Con `pan = ±0.8`, la amplitud entre canales en el pico vale
        (1+0.8)/(1-0.8) = 9× — energía 81×. Medimos el ratio máximo en
        ventanas de 50 ms (el LFO hace un ciclo entero por bucle, así que
        un tramo largo promedia el cruce por el centro) y exigimos una
        fracción holgada de ese pico.
        """
        _, m = _leer_estereo(TORMENTA)
        rate = 22050
        ventana = rate // 20
        mejor_izq = mejor_der = 1e-9
        for i in range(0, len(m) - ventana, ventana):
            tramo = m[i:i + ventana]
            e_izq = sum(a * a for a, _ in tramo) / len(tramo)
            e_der = sum(b * b for _, b in tramo) / len(tramo)
            mejor_izq = max(mejor_izq, e_izq / max(e_der, 1e-9))
            mejor_der = max(mejor_der, e_der / max(e_izq, 1e-9))
        excursión = max(mejor_izq, mejor_der)
        assert mejor_izq > 1.0 and mejor_der > 1.0, (
            "el paneo nunca cambia de canal dominante"
        )
        assert excursión >= 16.0, (
            f"la excursión de paneo es débil (ratio de energía "
            f"{excursión:.1f}); la receta pide oscilar hasta ±0.8, que da "
            "ratios muy por encima"
        )
