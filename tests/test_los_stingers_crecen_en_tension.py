"""AUD-596 — GAP-067: los stingers de fase crecen en tensión, y la risa
de Paburu ríe como una risa.

Decisión del dueño (2026-08-21): el material de autor no va a llegar y los
placeholders procedimentales quedan aceptados **como definitivos** — pero
definitivo no significa el acorde ascendente plano de AUD-541 repetido
cuatro veces. La receta del propio GAP pedía que «el stinger debe crecer en
tensión con el número de fase», así que cada fase gana capa y longitud, y la
risa deja de ser cuatro estallidos idénticos descendentes: una risa de verdad
tiene estallidos irregulares y un contorno de tono que sube y baja.

Lo medible (todo sobre los `.wav` comprometidos, sin cargar el mezclador):
- duración estrictamente creciente por fase,
- energía de graves creciente (el pánico entra por debajo),
- pico de amplitud no decreciente,
- y en la risa: intervalos entre estallidos desiguales y tono no monótono.
"""
from __future__ import annotations

import math
import os
import struct
import wave

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

from itertools import pairwise
from pathlib import Path

from src.engine.core import settings

RATE = 22050


def _muestras(ruta: Path) -> list[float]:
    with wave.open(str(ruta), "rb") as wf:
        assert wf.getframerate() == RATE
        bruto = wf.readframes(wf.getnframes())
    return [s / 32768.0 for s in struct.unpack(f"<{len(bruto) // 2}h", bruto)]


def _stinger(fase: int) -> list[float]:
    return _muestras(settings.ASSETS_DIR / "sfx" / "stingers" /
                     f"stinger_boss_phase_{fase}.wav")


def _graves(muestras: list[float], freq: float = 50.0) -> float:
    """Proporción de energía en el bin exacto del rumor de 50 Hz.

    Relativa a propósito: `_write_wav` normaliza por el pico de cada
    fichero, así que una comparación absoluta mediría la normalización y no
    el material. El rumor es un tono FIJO que sólo cambia de volumen por
    fase (STINGER_SUB), así que su bin no se confunde con los colchones
    descendentes ni con nada más del arreglo.
    """
    n = len(muestras)
    k = round(n * freq / RATE)
    w = 2.0 * math.pi * k / n
    c = 2.0 * math.cos(w)
    s1 = s2 = 0.0
    energia_total = 0.0
    for x in muestras:
        s0 = x + c * s1 - s2
        s2, s1 = s1, s0
        energia_total += x * x
    bin_ = math.sqrt(max(0.0, s1 * s1 + s1 * s2 + s2 * s2)) / max(1e-9, n)
    return max(0.0, bin_ * bin_ / max(1e-12, energia_total / max(1, n)))


class TestElStingerCreceEnTension:
    def test_la_duracion_crece_con_la_fase(self) -> None:
        duraciones = [len(_stinger(n)) / RATE for n in range(4)]
        assert duraciones == sorted(duraciones), (
            f"la tensión no escala si la fase 3 dura lo mismo que la 0: "
            f"{[round(d, 2) for d in duraciones]}"
        )
        assert duraciones[-1] - duraciones[0] >= 0.4, (
            "fase 3 y fase 0 casi clavadas: la curva es decorativa"
        )

    def test_los_graves_entran_por_debajo_cada_fase(self) -> None:
        energia = [_graves(_stinger(n)) for n in range(4)]
        assert all(a < b for a, b in pairwise(energia)), (
            f"la proporción de graves no crece por fase: "
            f"{[f'{e:.5f}' for e in energia]}"
        )

    def test_el_pico_no_decrece(self) -> None:
        picos = [max(abs(x) for x in _stinger(n)) for n in range(4)]
        assert picos == sorted(picos), (
            f"la fase 3 suena más floja que las anteriores: "
            f"{[round(p, 3) for p in picos]}"
        )


class TestLaRisaDePaburuRisaDeVerdad:
    def _estallidos(self, m: list[float]) -> tuple[list[float], list[int]]:
        """Posición (s) e índice de inicio de cada estallido, segmentando
        sobre el **envolvente** (media móvil de |x| en 10 ms).

        Umbralar la forma de onda cruda fragmenta cada ciclo del oscilador
        en un "estallido" — cientos. El envolvente agrupa lo que el oído
        agrupa; los huecos menores de 30 ms se funden y los estallidos de
        menos de 20 ms se descartan.
        """
        ventana = RATE // 100
        env = [
            sum(abs(x) for x in m[i:i + ventana]) / ventana
            for i in range(0, max(1, len(m) - ventana), ventana // 2)
        ]
        techo = max(env) or 1e-9
        umbral = 0.25 * techo
        activos = [i * (ventana // 2) for i, e in enumerate(env) if e > umbral]
        grupos: list[list[int]] = []
        for i in activos:
            if grupos and i - grupos[-1][-1] <= int(RATE * 0.03):
                grupos[-1].append(i)
            else:
                grupos.append([i])
        grupos = [g for g in grupos if g[-1] - g[0] >= int(RATE * 0.02)]
        centros = [(g[0] + g[-1]) / 2 / RATE for g in grupos]
        return centros, [g[0] for g in grupos]

    def test_hay_seis_estallidos_y_no_son_un_metronomo(self) -> None:
        m = _muestras(settings.ASSETS_DIR / "sfx" / "voz" / "sfx_voz_paburu_risa.wav")
        centros, _ = self._estallidos(m)
        assert len(centros) == 6, (
            f"la receta son seis estallidos, detectados {len(centros)}"
        )
        intervalos = [b - a for a, b in pairwise(centros)]
        media = sum(intervalos) / len(intervalos)
        varianza = sum((d - media) ** 2 for d in intervalos) / len(intervalos)
        assert varianza > (media * 0.15) ** 2, (
            f"intervalos casi idénticos ({[round(d, 3) for d in intervalos]}): "
            "metrónomo, no risa — la irregularidad ES el timbre de la risa"
        )

    def test_el_tono_suba_y_baja(self) -> None:
        """Contorno de pitch por estallido vía tasa de cruces por cero.

        Una risa real alterna subidas y bajadas; los placeholders viejos
        sólo caían. Exigimos al menos una inversión de tendencia global.
        """
        m = _muestras(settings.ASSETS_DIR / "sfx" / "voz" / "sfx_voz_paburu_risa.wav")
        _, inicios = self._estallidos(m)
        tasas: list[float] = []
        for a, b in pairwise([*inicios, len(m)]):
            tramo = m[a:b]
            cruces = sum(
                1 for x, y in pairwise(tramo) if (x >= 0) != (y >= 0)
            )
            tasas.append(cruces / max(1, len(tramo)))
        direccion = [(t2 > t1) - (t2 < t1) for t1, t2 in pairwise(tasas)]
        assert set(direccion) == {1, -1}, (
            f"el tono sólo va en un sentido (tasas {[round(t, 4) for t in tasas]}): "
            "falta el vaivén que hace que una risa suene viva"
        )
