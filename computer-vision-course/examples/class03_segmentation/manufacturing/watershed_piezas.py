#!/usr/bin/env python3
"""
Clase 3 · Manufactura — watershed sobre piezas que se tocan.

En la banda salen piezas pegadas. La pregunta del contexto: *¿cuántas piezas
hay y dónde empieza cada una, cuando ninguna frontera las separa?*

La demostración central de la clase está en la primera medición:

    el umbral —fijo u Otsu, da igual— produce UNA componente conexa de
    10.360 px donde hay 5 piezas.

No es un fallo del umbral: es que contar objetos y separarlos son dos
problemas distintos, y las componentes conexas solo saben del primero.
Cuando dos círculos se tocan, su unión es un solo conjunto conexo, y ninguna
poda de umbrales va a separarlo.

El watershed separa la mancha usando la **transformada de distancia** —lejos
del borde, el centro de cada pieza— y un conjunto de marcadores. La única
decisión delicada es el umbral de marcadores, y tiene una explicación
geométrica: el eje medio de dos círculos de radio r con centros a distancia
d tiene un valle de profundidad √(r² − (d/2)²). Si el umbral no lo cruza,
los cinco marcadores se funden en uno y el watershed vuelve a contar 1. En
este dataset: r = 27 px, paso = 44,3 px ⇒ valle a 15,5 px; el umbral se
pone en el 65 % de la distancia máxima (17,3 px) y funciona.

El resultado se valida contra la verdad-terreno del generador: 5 regiones,
con un error medio de centroide de 3 px y un máximo de 6. Sin esa verdad,
«el watershed acertó» sería una opinión.

Ejecutar:
    python examples/class03_segmentation/manufacturing/watershed_piezas.py
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

CURSO = Path(__file__).resolve().parents[3]
for _ruta in (CURSO, CURSO.parent):
    if str(_ruta) not in sys.path:
        sys.path.insert(0, str(_ruta))

import cv2
import numpy as np

from cvcourse import synthetic, viz

SALIDA = CURSO / "outputs" / "clase03"

FRACCION_MARCADORES = 0.65  # umbral sobre la distancia maxima, en fraccion


def main() -> int:
    SALIDA.mkdir(parents=True, exist_ok=True)

    imagen, verdades = synthetic.piezas_en_contacto(
        n=5, tamano=256, ruido=3.0, semilla=20260805
    )
    gris = imagen.astype(np.uint8)
    radio = verdades[0].radio
    paso = 2.0 * radio * 0.82
    valle = math.sqrt(radio**2 - (paso / 2.0) ** 2)

    print(f"BANDA: {len(verdades)} piezas de radio {radio:.0f} px en cadena, "
          f"centros a {paso:.1f} px (solape asegurado: 2r = {2*radio:.0f} px)")

    # Paso 1: el umbral miente a proposito. Otsu incluido.
    _, mascara = cv2.threshold(gris, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    n_umbral, _, stats, _ = cv2.connectedComponentsWithStats(mascara, 8)
    areas = [int(stats[i, cv2.CC_STAT_AREA]) for i in range(1, n_umbral)]
    print(
        f"\n1. UMBRAL (Otsu): {n_umbral - 1} componente conexa de {sum(areas)} px "
        f"donde hay {len(verdades)} piezas."
    )

    # Paso 2: la transformada de distancia y su valle.
    suavizada = cv2.GaussianBlur(gris, (5, 5), 1.0)
    _, b2 = cv2.threshold(suavizada, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    dist = cv2.distanceTransform(b2, cv2.DIST_L2, 5)
    dmax = float(dist.max())
    print(
        f"\n2. DISTANCIA: maximo {dmax:.1f} px en los centros. El eje medio entre\n"
        f"   dos piezas de radio {radio:.0f} px separadas {paso:.1f} px cae a "
        f"{valle:.1f} px\n   (raiz de (r^2 - (paso/2)^2)). El umbral de marcadores "
        f"({FRACCION_MARCADORES:.0%} del maximo = {FRACCION_MARCADORES * dmax:.1f} px)\n"
        f"   tiene que pasar ese valle, o los 5 marcadores se funden."
    )

    # Paso 3: marcadores + watershed.
    _, seguros = cv2.threshold(
        dist, FRACCION_MARCADORES * dmax, 255, cv2.THRESH_BINARY
    )
    seguros = seguros.astype(np.uint8)  # threshold sobre float32 devuelve float32
    n_seguros, marcas = cv2.connectedComponents(seguros.astype(np.uint8), 8)
    desconocido = cv2.subtract(
        cv2.dilate(b2, np.ones((3, 3), np.uint8), iterations=3), seguros
    )
    marcas = marcas + 1
    marcas[desconocido == 255] = 0
    color = cv2.cvtColor(gris, cv2.COLOR_GRAY2BGR)
    marcas = cv2.watershed(color, marcas)

    regiones = [m for m in np.unique(marcas) if m > 1]
    print(
        f"\n3. WATERSHED: {n_seguros - 1} marcadores seguros -> {len(regiones)} "
        f"regiones separadas ({len(verdades)} esperadas)."
    )

    errores: list[float] = []
    print(f"\n{'region':>6s} {'centroide':>14s} {'verdad':>14s} {'error':>6s}")
    print("-" * 46)
    for m in sorted(regiones):
        ys, xs = np.nonzero(marcas == m)
        cx, cy = float(xs.mean()), float(ys.mean())
        verdad = min(
            verdades,
            key=lambda v: math.hypot(cx - v.centro[1], cy - v.centro[0]),
        )
        e = math.hypot(cx - verdad.centro[1], cy - verdad.centro[0])
        errores.append(e)
        print(
            f"{m:6d} ({cx:6.1f},{cy:6.1f}) ({verdad.centro[1]:6.1f},{verdad.centro[0]:6.1f}) "
            f"{e:6.1f}"
        )
    print(f"\nError medio {np.mean(errores):.1f} px, maximo {np.max(errores):.1f} px.")

    # Figura: la cadena de pasos completa, con las regiones coloreadas.
    rng = np.random.default_rng(5)
    paleta = rng.integers(60, 255, size=(marcas.max() + 1, 3), dtype=np.uint8)
    coloreada = np.zeros((*mascara.shape, 3), dtype=np.uint8)
    for m in regiones:
        coloreada[marcas == m] = paleta[m % len(paleta)]
    dibujo_marcas = cv2.cvtColor(gris, cv2.COLOR_GRAY2BGR)
    for m in range(1, n_seguros + 1):
        ys, xs = np.nonzero(marcas == m)
        if len(ys):
            cv2.circle(dibujo_marcas, (int(xs.mean()), int(ys.mean())), 2, (0, 0, 255), -1)

    ruta = viz.guardar(
        viz.rejilla(
            [gris, mascara, cv2.normalize(dist, None, 0, 255, cv2.NORM_MINMAX), dibujo_marcas, coloreada],
            [
                f"banda: {len(verdades)} piezas que se tocan",
                f"umbral: 1 componente de {sum(areas)} px (miente)",
                "distancia: el valle del eje medio es la clave",
                f"marcadores seguros ({n_seguros - 1})",
                f"watershed: {len(regiones)} regiones",
            ],
            columnas=3,
            titulo_general="Clase 3 · manufactura -- watershed sobre piezas que se tocan",
        ),
        SALIDA / "watershed_piezas.png",
    )
    print(f"\nFigura: {ruta}")

    print(
        "\nEl numero que cierra la clase: el valle del eje medio (15,5 px).\n"
        "Con el umbral de marcadores debajo de el, el watershed vuelve a\n"
        "contar 1; encima, cuenta 5. No hay magia: hay geometria, y se\n"
        "puede medir antes de correr nada."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())