"""AUD-511 — los ambientes de bucle clicaban al dar la vuelta.

El defecto
==========
`weather_system.AMBIENTES` reproduce `wind_indoor` con
`AudioManager.play_ambient(loops=-1)` para los climas `"snow"` y `"fog"` — un
bucle real, indefinido mientras dure el clima. `tools/generate_all_assets.py`
generaba ese clip (y `jungle_ambient`, `datacenter_hum`, aunque ninguno de los
dos está cableado a una escena todavía) con una envolvente que decae a cero:

    samples = [random.uniform(-0.05, 0.05) * max(0, 1 - i/n) for i in range(n)]

Cada vuelta del bucle de 2 s cae en silencio y salta de golpe otra vez a
volumen lleno — un clic audible cada 2 segundos, indefinidamente. Es el mismo
defecto que AUD-271 ya documentó y corrigió para `rain_ambient` («un ambiente
que se apaga delata el bucle en cuanto da la vuelta»), sin arreglar aquí.

`cemetery_silence` es la excepción real, no un descuido: lo usa
`stage4_1._actualizar_silencio_y_shake` como un solo disparo («el clima calla
de golpe»), y decaer a silencio es exactamente el efecto que pide. La prueba
de abajo comprueba las dos cosas a la vez: que los de bucle ya no decaen, y
que el de un solo disparo sigue decayendo.
"""
from __future__ import annotations

import random
import sys
from pathlib import Path


def _importar_gen_sfx():
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
    from generate_all_assets import _gen_sfx
    return _gen_sfx


def _rms(muestras: list[float]) -> float:
    return (sum(x * x for x in muestras) / len(muestras)) ** 0.5


class TestLosAmbientesDeBucleNoDecaen:
    def _no_decae(self, nombre: str) -> None:
        gen_sfx = _importar_gen_sfx()
        random.seed(0)
        muestras = gen_sfx(nombre)
        n = len(muestras)
        decima = max(1, n // 10)
        inicio = _rms(muestras[:decima])
        final = _rms(muestras[-decima:])
        assert final > inicio * 0.5, (
            f"{nombre} decae hacia el final ({inicio=:.4f}, {final=:.4f}): "
            "un bucle infinito con esto clica cada vez que da la vuelta"
        )

    def test_wind_indoor_no_decae(self) -> None:
        """El que de verdad está en producción: `weather_system.AMBIENTES`
        lo reproduce en bucle para «snow» y «fog»."""
        self._no_decae("wind_indoor")

    def test_jungle_ambient_no_decae(self) -> None:
        self._no_decae("jungle_ambient")

    def test_datacenter_hum_no_decae(self) -> None:
        self._no_decae("datacenter_hum")

    def test_cemetery_silence_si_decae(self) -> None:
        """La excepción real: un solo disparo que debe apagarse él solo."""
        gen_sfx = _importar_gen_sfx()
        random.seed(0)
        muestras = gen_sfx("cemetery_silence")
        n = len(muestras)
        decima = max(1, n // 10)
        inicio = _rms(muestras[:decima])
        final = _rms(muestras[-decima:])
        assert final < inicio * 0.2, (
            "cemetery_silence es un solo disparo para «el clima calla de "
            "golpe» (stage4_1._actualizar_silencio_y_shake): quitarle la "
            "envolvente le cambia el sentido, no arregla nada"
        )
