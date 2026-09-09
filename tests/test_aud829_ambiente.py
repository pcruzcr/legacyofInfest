"""AUD-829 — ruido más música: loop corto, muestra y fuga al salir.

El reporte: stages con ruido más la música. Triple causa verificada:
1. `fog`/`snow` loopeaban una muestra de 2,0 s: la periodicidad se oye como
   un "chorro raro" mecánico (ver `boss_paburu_scene.py:298-307`).
2. `StageScene.on_exit` paraba la música pero no el ambiente: el zumbido
   quedaba pegado en el siguiente escenario.
El volumen de arranque no se toca: el bus del jugador manda y el suelo sonoro
es decisión deliberada (AUD-402).
"""
from __future__ import annotations

import math
import wave
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


def _muestras(ruta: Path) -> tuple[list[float], int]:
    with wave.open(str(ruta), "rb") as w:
        n = w.getnframes()
        tasa = w.getframerate()
        crudo = w.readframes(n)
    assert w.getsampwidth() == 2 and w.getnchannels() == 1
    import array

    enteros = array.array("h", crudo)
    return [x / 32768.0 for x in enteros], tasa


def _rms(xs: list[float]) -> float:
    return math.sqrt(sum(x * x for x in xs) / len(xs))


def test_fog_y_snow_usam_un_loop_largo_sin_clic() -> None:
    from src.framework.vfx.weather_system import WeatherSystem

    for clima in ("fog", "snow"):
        ruta_rel = WeatherSystem.AMBIENTES[clima]
        assert ruta_rel, f"{clima} quedó sin ambiente"
        ruta = RAIZ / "assets" / ruta_rel
        assert ruta.exists(), f"el ambiente de {clima} no está en disco: {ruta}"
        muestras, tasa = _muestras(ruta)
        duracion = len(muestras) / tasa
        assert duracion >= 6.0, (
            f"el loop de {clima} dura {duracion:.1f} s: la periodicidad corta "
            "se oye como ruido mecánico"
        )
        decima = len(muestras) // 10
        assert _rms(muestras[-decima:]) > _rms(muestras[:decima]) * 0.5, (
            f"el loop de {clima} decae al final: clica al dar la vuelta"
        )
        borde = tasa // 4
        r_ini, r_fin = _rms(muestras[:borde]), _rms(muestras[-borde:])
        assert abs(r_fin - r_ini) / max(r_ini, 1e-9) < 0.3, (
            f"el loop de {clima} no empalma ({r_ini:.3f} vs {r_fin:.3f}): "
            "clica al dar la vuelta"
        )


def test_salir_del_stage_detiene_el_ambiente() -> None:
    """Con ambiente sonando, `on_exit` lo para (antes sólo la música)."""
    import sys

    sys.path.insert(0, str(RAIZ / "tests"))
    from test_menu_navigation import ContextManager

    from src.stages.stage0.stage0 import Stage0

    ctx = ContextManager()
    ctx.app.context.running = True
    ctx.sm.replace(Stage0(ctx.app.context))
    ctx.step(10)
    audio = ctx.app.context.audio
    ruta = RAIZ / "assets" / "sfx/environment/sfx_environment_wind_indoor.wav"
    audio.play_ambient(ruta, volume=0.3)
    assert audio._ambient_active, "el arnés no arrancó el ambiente"
    ctx.current.on_exit()
    assert not audio._ambient_active, (
        "on_exit paró la música pero dejó el ambiente sonando"
    )
