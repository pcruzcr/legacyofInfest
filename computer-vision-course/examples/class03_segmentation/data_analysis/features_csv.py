#!/usr/bin/env python3
"""
Clase 3 · Data Analytics — de la máscara a `features.csv`, sin entrenar nada.

La Clase 4 le dará estas columnas a un modelo. La pregunta del contexto:
*¿qué información hay en una pieza medida, antes de que exista modelo alguno?*

Este ejemplo recorre el dataset completo de la banda (120 piezas reales de
`datasets/synthetic_parts`, con su verdad-terreno) y convierte cada máscara
en una fila de la tabla del temario:

    object_id, area, perimeter, width, height, aspect_ratio, circularity,
    eccentricity, solidity, extent, centroid_x, centroid_y, class

Dos decisiones deliberadas:

* **La máscara sale de un umbral por pieza** (Otsu). Es el pipeline que se
  enseñó en esta clase; la Clase 4 no recibe imágenes, recibe números.
* **No se entrena nada.** El objetivo es mirar las distribuciones y poder
  decir, con números, qué columnas prometen separar las clases y cuáles no.
  El modelo llega en la Clase 4 — y llegará sabiendo qué significan las
  columnas que le den.

El CSV se escribe con `cvcourse.features.guardar_csv` (biblioteca estándar,
sin pandas: el aula sin permisos termina la clase igual, y la Clase 4 lo lee
con pandas sin cambios).

Ejecutar:
    python examples/class03_segmentation/data_analysis/features_csv.py
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

CURSO = Path(__file__).resolve().parents[3]
for _ruta in (CURSO, CURSO.parent):
    if str(_ruta) not in sys.path:
        sys.path.insert(0, str(_ruta))

import cv2
import numpy as np
from PIL import Image

from cvcourse import features, viz

SALIDA = CURSO / "outputs" / "clase03"

COLUMNAS_A_MIRAR = ("area", "aspect_ratio", "circularity")


def mascara_de_pieza(ruta: Path) -> np.ndarray:
    """Umbral de Otsu por pieza: la pieza es lo que se sale de la banda."""
    gris = np.asarray(Image.open(ruta).convert("L"))
    _, mascara = cv2.threshold(gris, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return mascara > 0


def main() -> int:
    SALIDA.mkdir(parents=True, exist_ok=True)
    base = CURSO / "datasets" / "synthetic_parts"

    with (base / "verdad_terreno.csv").open(encoding="utf-8", newline="") as f:
        registros = list(csv.DictReader(f))

    filas: list[features.Caracteristicas] = []
    omisiones: list[str] = []
    for registro in registros:
        ruta = base / registro["fichero"]
        if not ruta.exists():
            omisiones.append(registro["fichero"])
            continue
        medidas = features.caracteristicas_de_mascara(
            mascara_de_pieza(ruta), etiqueta_de_clase=registro["clase"]
        )
        filas.extend(medidas)

    if omisiones:
        print(f"AVISO: faltan {len(omisiones)} ficheros del CSV (no se escriben filas):")
        for o in omisiones[:5]:
            print(f"  {o}")

    ruta_csv = features.guardar_csv(filas, SALIDA / "features.csv")
    print(f"CSV: {ruta_csv}")
    extra = len(filas) - len(registros)
    if extra:
        print(
            f"  {len(filas)} filas de {len(registros)} piezas: {extra} filas extra.\n"
            "  Son piezas cuya mascara quedo partida (el defecto se despega de\n"
            "  la pieza, o el umbral separo un trozo). La Clase 4 vera eso como\n"
            "  objetos falsos: ya es una pista de que el area minima importa."
        )
    else:
        print(f"  {len(filas)} filas, una por pieza.")

    por_clase: dict[str, dict[str, list[float]]] = {}
    for fila in filas:
        caja = por_clase.setdefault(fila.label, {c: [] for c in COLUMNAS_A_MIRAR})
        for c in COLUMNAS_A_MIRAR:
            caja[c].append(float(getattr(fila, c)))

    print(f"\n{'columna':>13s} {'clase':>6s} {'media':>8s} {'min':>8s} {'max':>8s}")
    print("-" * 50)
    for columna in COLUMNAS_A_MIRAR:
        for clase, caja in sorted(por_clase.items()):
            valores = caja[columna]
            print(
                f"{columna:>13s} {clase:>6s} {np.mean(valores):8.3f} "
                f"{np.min(valores):8.3f} {np.max(valores):8.3f}"
            )

    print(
        "\nLa pregunta de la clase: que columna separa a las clases? La\n"
        "circularidad distingue formas (un rectangulo da ~0,8 y un circulo\n"
        "~0,9); el area separa tamanos. Ninguna columna sola separa OK de\n"
        "NO_OK: los rangos se solapan. Esa frase --no se puede, con una\n"
        "sola medida-- es el contenido de esta clase, y la razon por la\n"
        "que la Clase 4 usa varias a la vez."
    )

    X, y, nombres = features.a_matriz(filas)
    ruta = viz.guardar(
        viz.nube_de_caracteristicas(
            X, y, nombres, eje_x="circularity", eje_y="area",
            titulo="Clase 3 · data analytics -- dos medidas, sin entrenar nada",
        ),
        SALIDA / "features_nube.png",
    )
    print(f"Figura: {ruta}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())