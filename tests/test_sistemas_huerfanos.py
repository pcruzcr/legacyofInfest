"""AUD-233 — que ningún subsistema vuelva a quedarse sin invocar en silencio.

El modo de fallo que vigila esta prueba
=======================================
Este repositorio tiene uno propio, y ya se ha repetido seis veces: **un
subsistema se escribe entero, se prueba, se documenta como entregado, y nadie
lo llama desde el juego**. No falla nada. Sus pruebas pasan, en aislamiento. La
revisión de código no lo ve, porque el fichero que falta no está en el diff.

`SoundBank` sin una sola llamada a `play_sfx` (GAP-003). El sistema de diálogo,
completo y dibujado, que no se abría nunca (AUD-127). `check_player_contact` en
cuatro enemigos: las flechas no hacían daño (AUD-149). `SpeedrunTimer.save()`,
con una pantalla de récords que rellenaba el hueco con tiempos inventados
(AUD-202). `BossRushMode`, construido y abandonado, con la spec declarándolo
«✅ Complete — scoring, health carry-over» (AUD-232).

Los tres últimos aparecieron esta semana, revisando a mano. Esta prueba existe
para que el siguiente no haga falta encontrarlo a mano.

Qué se comprueba, y qué no
--------------------------
No se exige que todo símbolo público tenga un llamador: eso sería ruido y
llevaría a borrar cosas que hacen falta —`docs/63` ya cometió ese error—. Se
exige algo más estrecho y verificable: que **ningún módulo declarado terminado
por un documento oficial** tenga símbolos que sólo ejercitan las pruebas sin que
alguien haya mirado el caso y escrito el motivo.
"""
from __future__ import annotations

import importlib.util
import pathlib

RAIZ = pathlib.Path(__file__).resolve().parent.parent
GUARDIAN = RAIZ / "scripts" / "check_orphan_systems.py"


def _cargar():
    spec = importlib.util.spec_from_file_location("check_orphan_systems", GUARDIAN)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def test_el_guardian_existe_y_se_puede_ejecutar() -> None:
    assert GUARDIAN.is_file(), f"falta {GUARDIAN.relative_to(RAIZ).as_posix()}"
    assert _cargar().huerfanos(), (
        "el barrido no encuentra ni un símbolo: algo se rompió en el análisis, "
        "porque huérfanos hay — lo que no puede es dar cero"
    )


def test_ningun_modulo_declarado_completo_esconde_un_huerfano_sin_mirar() -> None:
    """La puerta. Falla con lo que nadie ha clasificado todavía."""
    m = _cargar()
    declarados = m.modulos_declarados_completos()
    sin_clasificar: list[str] = []
    for nombre, ruta in m.huerfanos().items():
        if nombre in m.VERIFICADOS or nombre in m.PENDIENTES:
            continue
        rel = ruta.relative_to(m.RAIZ).as_posix()
        if rel in declarados:
            sin_clasificar.append(f"  {rel}: {nombre} "
                                  f"(lo declara {', '.join(sorted(declarados[rel]))})")

    assert not sin_clasificar, (
        "hay símbolos que las pruebas ejercitan, el juego no invoca, y un "
        "documento da por entregados:\n" + "\n".join(sorted(sin_clasificar))
        + "\n\nAbre cada fichero y decide: si no es un defecto, va a "
        "VERIFICADOS con el motivo; si lo es, se conecta o se deja de "
        "documentar como entregado y va a PENDIENTES con su GAP."
    )


def test_las_dos_listas_no_se_solapan() -> None:
    """Un símbolo es «no es un defecto» o «lo es y está anotado». No ambas."""
    m = _cargar()
    solapan = sorted(set(m.VERIFICADOS) & set(m.PENDIENTES))
    assert not solapan, f"clasificados como las dos cosas: {solapan}"


def test_las_listas_no_acumulan_nombres_muertos() -> None:
    """Una exención de algo que ya no existe es una mentira que nadie relee."""
    m = _cargar()
    definidos = set(m.definiciones())
    fantasmas = sorted((set(m.VERIFICADOS) | set(m.PENDIENTES)) - definidos)
    assert not fantasmas, (
        f"estas exenciones nombran símbolos que ya no se definen en src/: "
        f"{fantasmas}. Bórralas o el guardián protege a fantasmas"
    )
