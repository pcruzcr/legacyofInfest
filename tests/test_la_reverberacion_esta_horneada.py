"""AUD-515 — la reverberación real que GAP-058 pedía para el silencio de la
Fase 4, sin mezclador DSP.

El mezclador de este motor (SDL mixer) no tiene DSP en tiempo real, así que
GAP-058 se dejó pendiente asumiendo que hacía falta uno. No hace falta: todo
el audio del proyecto ya se genera por código (`tools/generate_all_assets.py`),
así que la reverberación se hornea en el propio `.wav` — varias copias
retrasadas y cada vez más flojas del sonido, sumadas encima del original
(`_aplicar_reverberacion`), el mismo principio que un comb filter.

Se aplica a `cemetery_silence` (el silencio súbito de la Fase 4) y a un
sonido nuevo, `despertar_profundo` (la secuencia de despertar de la Fase 6,
GAP-064 punto 25, que antes tomaba prestado un cue de jefe sin relación).
"""
from __future__ import annotations

import sys
from pathlib import Path


def _importar():
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
    from generate_all_assets import SAMPLE_RATE, _aplicar_reverberacion, _gen_sfx
    return _aplicar_reverberacion, _gen_sfx, SAMPLE_RATE


class TestAplicarReverberacion:
    def test_alarga_el_clip_con_la_cola(self) -> None:
        aplicar, _gen_sfx, rate = _importar()
        seco = [1.0] * 100
        con_reverb = aplicar(seco, rate, cola_extra_s=0.5)
        assert len(con_reverb) == len(seco) + int(rate * 0.5)

    def test_hay_energia_despues_de_que_termine_el_sonido_seco(self) -> None:
        """La prueba de que hay eco de verdad: algo suena después del punto
        donde el clip original ya había terminado del todo."""
        aplicar, _gen_sfx, rate = _importar()
        seco = [1.0 if i < 50 else 0.0 for i in range(200)]
        con_reverb = aplicar(seco, rate, retardo_ms=5.0, ecos=4, decaimiento=0.6)
        despues_del_original = con_reverb[200:400]
        assert any(abs(x) > 1e-6 for x in despues_del_original), (
            "no hay ningún eco después de donde terminaba el sonido seco"
        )

    def test_los_ecos_decaen(self) -> None:
        """Cada eco debe sonar más flojo que el anterior, no más fuerte —
        si no, no es una cola que se apaga, es un sonido que crece."""
        aplicar, _gen_sfx, rate = _importar()
        seco = [0.0] * 10 + [1.0] + [0.0] * 200
        con_reverb = aplicar(seco, rate, retardo_ms=1.0, ecos=5, decaimiento=0.5)
        retardo_muestras = max(1, int(rate * 1.0 / 1000.0))
        picos = [
            abs(con_reverb[10 + retardo_muestras * eco])
            for eco in range(1, 5)
        ]
        assert picos == sorted(picos, reverse=True), (
            f"los ecos no decaen en orden: {picos}"
        )


class TestElSilencioDeLaFase4TieneReverberacion:
    def test_cemetery_silence_sigue_siendo_mas_largo_que_su_duracion_base(self) -> None:
        """Antes duraba exactamente 2,0 s (`t_dur["cemetery_silence"]`); con
        la cola de reverberación horneada debe durar más — la prueba
        externa, sin conocer los parámetros internos de la reverberación."""
        _aplicar, gen_sfx, rate = _importar()
        muestras = gen_sfx("cemetery_silence")
        duracion_base_s = 2.0
        assert len(muestras) > duracion_base_s * rate

    def test_sigue_decayendo_a_silencio_al_final_del_todo(self) -> None:
        """La cola de reverberación también se apaga: no deja un bucle
        infinito de eco, sólo alarga cuánto tarda en callarse del todo."""
        _aplicar, gen_sfx, _rate = _importar()
        muestras = gen_sfx("cemetery_silence")
        ultimo_decimo = muestras[-len(muestras) // 10:]
        rms_final = (sum(x * x for x in ultimo_decimo) / len(ultimo_decimo)) ** 0.5
        assert rms_final < 0.01, (
            f"la cola de reverberación no se apaga del todo: rms={rms_final:.4f}"
        )


class TestElDespertarProfundoExiste:
    def test_se_genera_sin_reventar(self) -> None:
        _aplicar, gen_sfx, _rate = _importar()
        muestras = gen_sfx("despertar_profundo")
        assert muestras
        assert all(-1.5 <= x <= 1.5 for x in muestras), (
            "las muestras de despertar_profundo se salen de rango antes de normalizar"
        )

    def test_tambien_lleva_cola_de_reverberacion(self) -> None:
        _aplicar, gen_sfx, rate = _importar()
        muestras = gen_sfx("despertar_profundo")
        duracion_base_s = 1.6
        assert len(muestras) > duracion_base_s * rate
