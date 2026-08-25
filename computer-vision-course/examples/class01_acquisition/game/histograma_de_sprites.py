#!/usr/bin/env python3
"""
Clase 1 · Videojuego — el histograma de un sprite miente, y hay que saber por qué.

El problema, en una frase
--------------------------
Los sprites del motor son PNG **RGBA**: tienen un cuarto canal que dice qué
píxeles son transparentes. Casi todo el software de visión trabaja en RGB y
descarta ese canal, y al descartarlo **lo transparente se vuelve negro**.

Un sprite de 32×32 con un personaje pequeño puede ser 60 % transparente. Al
pasarlo a RGB, ese 60 % aparece como un pico gigante en el valor 0, y a partir
de ahí:

* la media de brillo es falsa;
* el contraste medido es falso;
* Otsu elige un umbral que separa «fondo transparente» de «todo lo demás», que
  no es la pregunta que se quería hacer;
* y nada de esto lanza ninguna excepción.

Este ejemplo mide el engaño y enseña la corrección: **usar el canal alfa como
máscara** y calcular el histograma sólo sobre los píxeles que existen.

Usa la API real del motor (`FilterTools`), que es la que los estudiantes tienen
que conocer para sus escenarios.

Ejecutar:
    python examples/class01_acquisition/game/histograma_de_sprites.py
"""
from __future__ import annotations

import sys
from pathlib import Path

CURSO = Path(__file__).resolve().parents[3]
REPO = CURSO.parent
for _ruta in (CURSO, REPO):
    if str(_ruta) not in sys.path:
        sys.path.insert(0, str(_ruta))

import numpy as np
from PIL import Image

from cvcourse import engine_bridge, viz

SALIDA = CURSO / "outputs" / "clase01"

#: Sprites elegidos por su proporción de transparencia, de menos a más.
SPRITES = (
    "assets/sprites/player/player_idle.png",
    "assets/sprites/enemies/zone1/enemy_zone1_walk.png",
    "assets/sprites/bosses/boss_venado_charge.png",
)


def cargar_con_alfa(ruta: Path) -> tuple[np.ndarray, np.ndarray]:
    """Devuelve (RGB, máscara de opacidad).

    Se carga con Pillow y no con el motor a propósito: `engine_bridge` entrega
    RGB porque es lo que el resto del curso necesita, y aquí hace falta ver
    justamente lo que se pierde por el camino.
    """
    rgba = np.asarray(Image.open(ruta).convert("RGBA"))
    return rgba[:, :, :3].copy(), rgba[:, :, 3] > 0


def estadisticas(gris: np.ndarray, etiqueta: str) -> dict[str, float | str]:
    return {
        "cálculo": etiqueta,
        "n_pixeles": float(gris.size),
        "media": float(gris.mean()) if gris.size else 0.0,
        "desv": float(gris.std()) if gris.size else 0.0,
        "mediana": float(np.median(gris)) if gris.size else 0.0,
    }


def analizar(ruta_relativa: str) -> dict[str, object]:
    ruta = REPO / ruta_relativa
    rgb, opaco = cargar_con_alfa(ruta)
    gris = rgb.mean(axis=2)

    transparencia = float((~opaco).mean() * 100)
    ingenuo = estadisticas(gris.ravel(), "ingenuo (alfa descartado)")
    corregido = estadisticas(gris[opaco], "corregido (sólo píxeles opacos)")

    # La misma medida con la API del motor, que es la que usan las escenas de
    # demostración. `compute_histogram` trabaja sobre una Surface y tampoco
    # sabe nada del alfa: reproduce el cálculo ingenuo, y conviene que el
    # estudiante lo compruebe en vez de creérselo.
    engine_bridge.iniciar_pygame_headless()
    from src.framework.processing.filter_tools import FilterTools

    superficie = engine_bridge.array_a_superficie(rgb)
    histograma_motor = FilterTools.compute_histogram(superficie)

    return {
        "nombre": Path(ruta_relativa).name,
        "forma": rgb.shape,
        "transparencia_%": transparencia,
        "ingenuo": ingenuo,
        "corregido": corregido,
        "total_motor": histograma_motor["total_pixels"],
        "rgb": rgb,
        "opaco": opaco,
        "gris": gris,
    }


def main() -> int:
    if not engine_bridge.hay_motor():
        print("Este ejemplo necesita los assets del motor.")
        return 1

    SALIDA.mkdir(parents=True, exist_ok=True)
    resultados = [analizar(s) for s in SPRITES]

    print(f"\n{'sprite':30s} {'transp%':>8s} {'media ingenua':>14s} {'media real':>11s} {'error':>8s}")
    print("-" * 76)
    for r in resultados:
        ing = float(r["ingenuo"]["media"])      # type: ignore[index]
        cor = float(r["corregido"]["media"])    # type: ignore[index]
        error = (cor - ing) / cor * 100 if cor else 0.0
        print(
            f"{r['nombre']!s:30s} {float(r['transparencia_%']):>8.1f} "
            f"{ing:>14.1f} {cor:>11.1f} {error:>7.0f}%"
        )

    print(
        "\nLa columna 'error' es cuánto se equivoca la media de brillo por\n"
        "haber contado como negros unos píxeles que sencillamente no existen."
    )

    # Figura: el sprite, su máscara de opacidad y los dos histogramas.
    peor = max(resultados, key=lambda r: float(r["transparencia_%"]))
    imagenes = [
        peor["rgb"],
        (peor["opaco"] * 255).astype(np.uint8),      # type: ignore[operator]
        peor["gris"],
    ]
    ruta = viz.guardar(
        viz.rejilla(
            imagenes,
            ["RGB (lo transparente ya es negro)", "Canal alfa: qué existe de verdad", "Gris"],
            columnas=3,
            titulo_general=f"{peor['nombre']} — {float(peor['transparencia_%']):.0f} % transparente",
        ),
        SALIDA / "sprite_transparencia.png",
    )
    print(f"Figura: {ruta}")

    gris_peor = np.asarray(peor["gris"])
    opaco_peor = np.asarray(peor["opaco"])
    ruta = viz.guardar(
        viz.histograma(gris_peor.astype(np.uint8), "Histograma INGENUO — con el pico falso en 0"),
        SALIDA / "histograma_ingenuo.png",
    )
    print(f"Figura: {ruta}")
    ruta = viz.guardar(
        viz.histograma(gris_peor[opaco_peor].astype(np.uint8),
                       "Histograma CORREGIDO — sólo píxeles opacos", con_imagen=False),
        SALIDA / "histograma_corregido.png",
    )
    print(f"Figura: {ruta}")

    print(
        "\nPara discutir: el motor calcula el histograma sobre "
        f"{peor['total_motor']} píxeles,\nque son todos los del lienzo. "
        f"Sólo {int(opaco_peor.sum())} contienen dibujo. ¿Es un defecto de\n"
        "`FilterTools.compute_histogram`, o es que le estamos preguntando mal?"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
