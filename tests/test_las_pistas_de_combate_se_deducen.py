"""AUD-597 — GAP-068: cada pista de zona tiene su variante `_combat`.

Decisión del dueño (2026-08-21): no va a llegar material de autor para las
pistas de combate, y el fallback (`{bgm}_traverse` sonando igual en calma
que en combate) se cierra **derivando proceduralmente** la variante desde
la pista que ya existe — capa rítmica horneada encima del original, sin
tocar código del motor: `_get_track_for_intensity` ya busca
`{bgm}_combat` primero, así que basta con que el fichero exista.

Quedan fuera con motivo: los tres `bgm_zoneN_boss` (su base ES música de
combate permanente) y los mp3 de autor del 4-1/4-1b (cada fase ya tiene su
propia curva de intensidad compuesta).

Lo medible sobre los ficheros: misma duración que la fuente (es la misma
pieza con capa), y más densidad de cruces por cero — los hi-hats añadidos
engrosan los agudos, y eso se oye y se cuenta.
"""
from __future__ import annotations

import os
import struct
import wave

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

from itertools import pairwise
from pathlib import Path

import pytest

from src.engine.core import settings

#: Las siete pistas base que ganan variante de combate.
BASES = (
    "bgm_stage0",
    "bgm_zone1",
    "bgm_zone2",
    "bgm_zone3",
    "bgm_zone1_traverse",
    "bgm_zone2_traverse",
    "bgm_zone3_traverse",
)

MUSICA = settings.ASSETS_DIR / "music"


def _leer(ruta: Path) -> tuple[int, int, list[float]]:
    """(canales, rate, muestras del canal izquierdo/mono normalizadas)."""
    with wave.open(str(ruta), "rb") as wf:
        canales, rate = wf.getnchannels(), wf.getframerate()
        bruto = wf.readframes(wf.getnframes())
    enteros = struct.unpack(f"<{len(bruto) // 2}h", bruto)
    if canales == 2:
        muestras = [enteros[i] / 32768.0 for i in range(0, len(enteros), 2)]
    else:
        muestras = [x / 32768.0 for x in enteros]
    return canales, rate, muestras


def _tasa_de_cruces(muestras: list[float], paso: int = 7) -> float:
    """Cruces por cero por muestra (submuestreado para que corra rápido).

    Los hi-hats de la capa rítmica viven en los agudos: más agudos, más
    cruces. La fuente sin capa es toda la referencia.
    """
    tramo = muestras[::paso]
    cruces = sum(
        1 for a, b in pairwise(tramo) if (a >= 0) != (b >= 0)
    )
    return cruces / max(1, len(tramo))


@pytest.mark.parametrize("base", BASES)
class TestLaVarianteDeCombateExiste:
    def test_el_fichero_existe_y_dura_igual(self, base: str) -> None:
        fuente = MUSICA / f"{base}.wav"
        combate = MUSICA / f"{base}_combat.wav"
        assert fuente.exists(), f"falta la fuente {fuente.name}"
        assert combate.exists(), (
            f"falta derivar {combate.name}: sin él, el combate de esta "
            "pista sigue sonando a traverse (GAP-068)"
        )
        with wave.open(str(fuente), "rb") as f, wave.open(str(combate), "rb") as c:
            dur_f = f.getnframes() / f.getframerate()
            dur_c = c.getnframes() / c.getframerate()
            assert c.getnchannels() == f.getnchannels(), (
                "la derivación cambió el número de canales"
            )
        assert abs(dur_c - dur_f) <= 0.25, (
            f"{combate.name} dura {dur_c:.2f}s y la fuente {dur_f:.2f}s: "
            "no es la misma pieza"
        )

    def test_tiene_mas_agudos_que_la_fuente(self, base: str) -> None:
        _, _, fuente = _leer(MUSICA / f"{base}.wav")
        _, _, combate = _leer(MUSICA / f"{base}_combat.wav")
        zcr_f = _tasa_de_cruces(fuente)
        zcr_c = _tasa_de_cruces(combate)
        assert zcr_c > zcr_f * 1.05, (
            f"la capa rítmica no se oye en {base}_combat "
            f"(zcr {zcr_c:.4f} vs fuente {zcr_f:.4f})"
        )


class TestElMotorLasEncuentra:
    @pytest.mark.parametrize("base", ["bgm_stage0", "bgm_zone2_traverse"])
    def test_intensidad_de_combate_resuelve_la_variante(self, base: str) -> None:
        from src.framework.audio.dynamic_music import DynamicMusicSystem

        dms = DynamicMusicSystem(audio_manager=None)  # type: ignore[arg-type]
        dms.set_zone(zone=0, bgm_track=base)
        pista = dms._get_track_for_intensity(DynamicMusicSystem.INTENSITY_COMBAT)
        assert pista is not None and pista.name == f"{base}_combat.wav", (
            f"con la variante en disco, INTENSITY_COMBAT debía resolver "
            f"{base}_combat.wav y resolvió {pista.name if pista else 'None'}"
        )
        # Y en calma sigue sonando la de traverse/base, no la de combate.
        calmada = dms._get_track_for_intensity(DynamicMusicSystem.INTENSITY_CALM)
        assert calmada is not None and "combat" not in calmada.name