#!/usr/bin/env python3
"""
Clase 1 · Solución de referencia del laboratorio (T1–T4 y el reto).

Para el profesor y los ayudantes. Se ejecuta entera y produce todas las
figuras y todas las cifras que se piden en `docs/clase01_guia.md` §5.

No es la única solución válida. Es **una** solución completa, con las cifras
que un grupo bien orientado debería obtener, para poder comparar sin tener que
rehacer el laboratorio en cada corrección.

Ejecutar:
    python solutions/clase01_solucion.py
"""
from __future__ import annotations

import sys
from pathlib import Path

CURSO = Path(__file__).resolve().parents[1]
REPO = CURSO.parent
for _ruta in (CURSO, REPO):
    if str(_ruta) not in sys.path:
        sys.path.insert(0, str(_ruta))

import numpy as np

from cvcourse import acquisition, engine_bridge, synthetic, viz

SALIDA = CURSO / "outputs" / "clase01_solucion"


# ── T1 — Adquisición ──────────────────────────────────────────────────────

def t1_adquisicion() -> list[tuple[str, np.ndarray]]:
    """Tres procedencias. Se anota la forma **esperada** antes de mirarla.

    La predicción es parte del ejercicio: acertar demuestra que se entendió el
    convenio (alto, ancho, canales); fallar y darse cuenta vale casi lo mismo.
    """
    print("=" * 74)
    print("T1 — ADQUISICIÓN")
    print("=" * 74)

    imagenes: list[tuple[str, np.ndarray]] = []

    # Predicción: `player_idle.png` es una hoja de 128×32 px, y el convenio del
    # curso es (alto, ancho, canales) → (32, 128, 3).
    #
    # Se nombra el fichero en vez de usar `FuenteMotor("sprites")` a propósito:
    # esa fuente entrega el primer sprite en orden alfabético, que hoy es otro
    # y mañana puede cambiar. Una predicción sólo vale si se sabe exactamente
    # sobre qué se predice.
    with acquisition.FuenteArchivo(REPO / "assets/sprites/player/player_idle.png") as fuente:
        sprite = fuente.leer()
    assert sprite is not None
    print(f"  predicción sprite: (32, 128, 3)   real: {sprite.shape}")
    imagenes.append(("sprite del motor", sprite))

    # Predicción: la resolución interna del motor es 800×600 → (600, 800, 3).
    fotograma = engine_bridge.capturar_escena("filter", fotogramas=1)[0]
    print(f"  predicción escena: (600, 800, 3)  real: {fotograma.shape}")
    imagenes.append(("fotograma de escena", fotograma))

    # Predicción: pieza sintética de 128 px, replicada a 3 canales.
    with acquisition.FuenteSintetica(n=1, tamano=128) as fuente:
        pieza = fuente.leer()
    assert pieza is not None
    print(f"  predicción pieza:  (128, 128, 3)  real: {pieza.shape}")
    imagenes.append(("pieza sintética", pieza))

    print(f"\n  {'imagen':22s} {'forma':>16s} {'media':>7s} {'rango':>6s} {'sat%':>6s} {'neg%':>6s}")
    print("  " + "-" * 68)
    for nombre, imagen in imagenes:
        gris = imagen.mean(axis=2)
        print(
            f"  {nombre:22s} {imagen.shape!s:>16s} {gris.mean():>7.1f} "
            f"{gris.max() - gris.min():>6.0f} {(gris >= 254).mean() * 100:>6.2f} "
            f"{(gris <= 1).mean() * 100:>6.2f}"
        )
    return imagenes


# ── T2 — Diagnóstico ──────────────────────────────────────────────────────

def t2_diagnostico(imagenes: list[tuple[str, np.ndarray]]) -> None:
    """Clasificar con cifras, no con impresiones.

    El diagnóstico correcto del sprite es el interesante: parece subexpuesto
    (media 20) y no lo está. Lo que tiene es un 58 % de píxeles que no existen
    y que el cargador convirtió en negros. Un grupo que escriba «subexpuesta»
    sin mirar el alfa ha diagnosticado un síntoma, no la causa.
    """
    print("\n" + "=" * 74)
    print("T2 — DIAGNÓSTICO")
    print("=" * 74)

    for nombre, imagen in imagenes:
        gris = imagen.mean(axis=2)
        media, rango = gris.mean(), gris.max() - gris.min()
        saturados, negros = (gris >= 254).mean() * 100, (gris <= 1).mean() * 100

        if saturados > 2:
            veredicto = f"sobreexpuesta ({saturados:.1f}% en 255)"
        elif rango < 60:
            veredicto = f"sin contraste (rango {rango:.0f})"
        elif negros > 30:
            veredicto = (
                f"NO es subexposición: {negros:.0f}% de negros con rango {rango:.0f}. "
                "Es transparencia convertida en negro"
            )
        elif media < 40:
            veredicto = f"subexpuesta (media {media:.0f})"
        else:
            veredicto = f"correcta (media {media:.0f}, rango {rango:.0f})"
        print(f"  {nombre:22s} -> {veredicto}")

        viz.guardar(
            viz.histograma(imagen, f"Histograma — {nombre}"),
            SALIDA / f"t2_histograma_{nombre.replace(' ', '_')}.png",
        )


# ── T3 — Criterio automático y su contraejemplo ───────────────────────────

def t3_criterio() -> None:
    """Umbrales que funcionan, y la imagen mala que se les cuela.

    El contraejemplo pedido es el ruido: se puede subir hasta ensuciar la
    imagen por completo sin tocar saturación, negros, rango ni media, porque
    el ruido es simétrico alrededor de cada valor y el histograma no sabe
    **dónde** está cada píxel.
    """
    print("\n" + "=" * 74)
    print("T3 — CRITERIO AUTOMÁTICO")
    print("=" * 74)

    sys.path.insert(0, str(CURSO / "examples" / "class01_acquisition" / "mechatronics"))
    from aceptacion_de_toma import Criterios, evaluar  # type: ignore[import-not-found]

    criterios = Criterios()
    buena, _ = synthetic.pieza_individual(tamano=192, semilla=11)
    rng = np.random.default_rng(11)

    casos = {
        "buena": buena,
        "oscura (mala)": np.clip(buena * 0.20, 0, 255).astype(np.uint8),
        "quemada (mala)": np.clip(buena.astype(float) * 2.5, 0, 255).astype(np.uint8),
        "CONTRAEJEMPLO: ruido": np.clip(
            buena.astype(float) + rng.normal(0, 17, buena.shape), 0, 255
        ).astype(np.uint8),
    }

    for nombre, imagen in casos.items():
        v = evaluar(imagen, criterios)
        estado = "ACEPTA" if v.aceptada else "RECHAZA"
        motivo = f" — {v.motivos[0]}" if v.motivos else ""
        print(f"  {nombre:24s} {estado}{motivo}")

    print(
        "\n  El contraejemplo pasa los cuatro criterios. El histograma cuenta\n"
        "  cuántos píxeles hay de cada valor y descarta dónde están; el ruido\n"
        "  sólo cambia el dónde. Lo que lo detecta es un filtro — Clase 2."
    )

    viz.guardar(
        viz.rejilla(list(casos.values()), list(casos), columnas=4,
                    titulo_general="T3 — el criterio y el caso que se le escapa"),
        SALIDA / "t3_criterio.png",
    )


# ── T4 — Realce medido ────────────────────────────────────────────────────

def t4_realce() -> None:
    """La conclusión que corrige a casi todos los grupos.

    El histograma mejora muchísimo y la tarea no se mueve, porque umbralizar
    es invariante a transformaciones monótonas. La única que cambia algo es la
    ecualización, y lo cambia **a peor** cuando hay ruido.
    """
    print("\n" + "=" * 74)
    print("T4 — REALCE MEDIDO")
    print("=" * 74)

    sys.path.insert(0, str(CURSO / "examples" / "class01_acquisition" / "industrial"))
    from realce_de_pieza import (  # type: ignore[import-not-found]
        calidad_de_la_tarea,
        calidad_del_histograma,
        ecualizar,
        estirar_contraste,
        subir_brillo,
        subir_contraste,
    )

    buena, verdad_pieza = synthetic.pieza_individual(
        tamano=192, clase="NO_OK", defecto="mota", semilla=4
    )
    f0, c0, f1, c1 = verdad_pieza.bbox
    verdad = np.zeros(buena.shape, dtype=bool)
    verdad[f0:f1, c0:c1] = True

    rng = np.random.default_rng(4)
    mala = np.clip(
        (buena.astype(float) + rng.normal(0, 14, buena.shape)) * 0.32 + 8, 0, 255
    ).astype(np.uint8)

    realces = {
        "sin realce": mala,
        "brillo +60": subir_brillo(mala),
        "contraste x2": subir_contraste(mala),
        "estirado": estirar_contraste(mala),
        "ecualizado": ecualizar(mala),
    }

    print(f"\n  {'realce':16s} {'rango':>6s} {'desv':>6s} {'ocup%':>6s} {'Otsu':>6s} {'IoU':>6s}")
    print("  " + "-" * 54)
    for nombre, imagen in realces.items():
        h = calidad_del_histograma(imagen)
        t = calidad_de_la_tarea(imagen, verdad)
        print(
            f"  {nombre:16s} {h['rango']:>6.0f} {h['desv']:>6.1f} "
            f"{h['ocupacion_%']:>6.1f} {t['umbral_otsu']:>6.0f} {t['iou']:>6.3f}"
        )

    print(
        "\n  Respuesta esperada en `analisis.md`: el histograma mejora mucho y\n"
        "  la tarea no. Un umbral compara cada píxel con un número, y estos\n"
        "  realces son funciones monótonas: no cambian el ORDEN de los píxeles,\n"
        "  así que la partición es la misma y sólo se mueve el valor del umbral.\n"
        "  La ecualización es la excepción, y empeora: colapsa niveles al\n"
        "  redondear a 8 bits, y con ruido reparte la escala según el fondo."
    )

    viz.guardar(
        viz.rejilla(list(realces.values()), list(realces), columnas=5,
                    titulo_general="T4 — cuatro realces, una sola tarea"),
        SALIDA / "t4_realce.png",
    )


# ── Reto — histograma consciente del canal alfa ───────────────────────────

def reto_alfa() -> None:
    print("\n" + "=" * 74)
    print("RETO — HISTOGRAMA CON CANAL ALFA")
    print("=" * 74)

    from PIL import Image

    ruta = REPO / "assets/sprites/player/player_idle.png"
    rgba = np.asarray(Image.open(ruta).convert("RGBA"))
    gris = rgba[:, :, :3].mean(axis=2)
    opaco = rgba[:, :, 3] > 0

    ingenua, correcta = gris.mean(), gris[opaco].mean()
    print(f"  media ingenua  : {ingenua:6.1f}   (sobre {gris.size} píxeles del lienzo)")
    print(f"  media correcta : {correcta:6.1f}   (sobre {int(opaco.sum())} píxeles con dibujo)")
    print(f"  error          : {(correcta - ingenua) / correcta * 100:5.0f} %")
    print(
        "\n  `FilterTools.compute_histogram` da la ingenua, y no es un defecto:\n"
        "  recibe una Surface RGB, donde el alfa ya se perdió. El error no está\n"
        "  en la función, está en preguntarle por una imagen que tiene píxeles\n"
        "  que no existen."
    )

    viz.guardar(
        viz.histograma(gris[opaco].astype(np.uint8),
                       "Histograma correcto — sólo píxeles opacos", con_imagen=False),
        SALIDA / "reto_histograma_alfa.png",
    )


def main() -> int:
    if not engine_bridge.hay_motor():
        print("La solución completa necesita el repositorio del motor.")
        return 1

    SALIDA.mkdir(parents=True, exist_ok=True)
    imagenes = t1_adquisicion()
    t2_diagnostico(imagenes)
    t3_criterio()
    t4_realce()
    reto_alfa()
    print(f"\nFiguras en: {SALIDA}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
