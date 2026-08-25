#!/usr/bin/env python3
"""
Clase 2 · Videojuego — limpiar y encontrar bordes, dentro de 16,6 ms.

Un juego a 60 fps tiene 16,6 ms por fotograma para **todo**: física, IA,
dibujo y lo que sea que este curso le añada. Un filtro que tarde 14 ms no
deja sitio a nada más. Esta es la pregunta del contexto: *¿qué filtros y qué
detección de bordes caben en el presupuesto, y cuáles hay que descartar?*

El flujo es el del temario, aplicado a un fotograma real del motor:

    escena del motor -> gaussiano -> mediana -> Sobel -> Canny

Y cada paso va con su cronómetro, sobre el mismo fotograma de 800x600. La
tabla de tiempos es la parte reproducible del ejemplo: misma imagen, mismo
número de pasadas, mediana de los tiempos.

Los filtros de OpenCV caben holgados; la implementación didáctica del motor
(`edge_detection.py`) no, y **por eso existe la versión OpenCV**: nadie puso
la lenta en el juego. Aprender el algoritmo no obliga a pagarlo en
producción; el cronómetro existe para que la diferencia se mida y no se
discuta.

Ejecutar:
    python examples/class02_processing/game/bordes_de_escena.py
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

CURSO = Path(__file__).resolve().parents[3]
for _ruta in (CURSO, CURSO.parent):
    if str(_ruta) not in sys.path:
        sys.path.insert(0, str(_ruta))

import cv2
import numpy as np

from cvcourse import engine_bridge, synthetic, viz

SALIDA = CURSO / "outputs" / "clase02"

FPS_OBJETIVO = 60
PRESUPUESTO_MS = 1000.0 / FPS_OBJETIVO


def fotograma_del_juego() -> tuple[np.ndarray, str]:
    """Un fotograma real de la escena-laboratorio, o una pieza si no hay motor."""
    if engine_bridge.hay_motor():
        return engine_bridge.capturar_escena("filter", fotogramas=1)[0], "escena del motor"
    pieza, _ = synthetic.pieza_individual(tamano=256, clase="NO_OK", defecto="grieta", semilla=3)
    return pieza, "pieza sintetica (sin motor)"


def cronometrar(funcion, pasadas: int = 10) -> float:
    """Mediana de los tiempos, en milisegundos.

    Mediana y no media porque una sola pasada que sufra un «stop-the-world»
    del recolector de basura desviaría la media entera. Con la mediana, un
    valor raro no cambia el resultado: eso es lo que hace reproducible a la
    tabla entre dos máquinas distintas.
    """
    funcion()
    tiempos = []
    for _ in range(pasadas):
        t0 = time.perf_counter()
        funcion()
        tiempos.append((time.perf_counter() - t0) * 1000.0)
    return float(np.median(tiempos))


def en_gris(imagen: np.ndarray) -> np.ndarray:
    """Luminancia BT.601, uint8 — el convenio de OpenCV para sus filtros."""
    return np.clip(
        0.299 * imagen[..., 0] + 0.587 * imagen[..., 1] + 0.114 * imagen[..., 2],
        0, 255,
    ).astype(np.uint8)


def main() -> int:
    SALIDA.mkdir(parents=True, exist_ok=True)
    imagen, origen = fotograma_del_juego()
    gris = en_gris(imagen)

    print(f"Fotograma: {origen}  {gris.shape}   presupuesto a {FPS_OBJETIVO} fps: {PRESUPUESTO_MS:.1f} ms")

    filtros = {
        "gaussiano (cv2, sigma 1.4)": lambda: cv2.GaussianBlur(gris, (5, 5), 1.4),
        "mediana (cv2, 5x5)": lambda: cv2.medianBlur(gris, 5),
        "sobel (cv2)": lambda: cv2.magnitude(
            cv2.Sobel(gris, cv2.CV_32F, 1, 0, ksize=3),
            cv2.Sobel(gris, cv2.CV_32F, 0, 1, ksize=3),
        ),
        "canny (cv2, 50-150)": lambda: cv2.Canny(gris, 50, 150),
    }

    print(f"\n{'filtro':28s} {'ms por fotograma':>17s}  cabe a 60 fps")
    print("-" * 68)
    resultados: dict[str, np.ndarray] = {}
    for nombre, filtro in filtros.items():
        ms = cronometrar(filtro)
        cabe = "SI" if ms < PRESUPUESTO_MS else "NO"
        print(f"{nombre:28s} {ms:>15.2f}  {cabe}")
        resultados[nombre] = np.clip(filtro(), 0, 255).astype(np.uint8)

    # La misma escena con la implementación didáctica: sin OpenCV, paso a
    # paso, como la van a leer los estudiantes. Sólo está disponible con el
    # repositorio del motor.
    if not engine_bridge.hay_motor():
        print(
            "\n(sin motor: el 'canny propio' del módulo edge_detection no está\n"
            "disponible; la comparación queda en los cuatro filtros de OpenCV)"
        )
    else:
        from src.framework.processing import edge_detection

        ms_propio = cronometrar(lambda: edge_detection.canny(imagen))
        print(f"{'canny propio (didactico)':28s} {ms_propio:>15.2f}  "
              f"{'SI' if ms_propio < PRESUPUESTO_MS else 'NO'}")
        print(
            f"\nEl presupuesto es de {PRESUPUESTO_MS:.1f} ms y el canny propio tarda "
            f"{ms_propio:.1f} ms: ocupa el {ms_propio / PRESUPUESTO_MS * 100:.0f} % del "
            "fotograma. Aprender como funciona no obliga a pagarlo en el juego."
        )

    ruta = viz.guardar(
        viz.rejilla(
            [gris, resultados["gaussiano (cv2, sigma 1.4)"],
             resultados["mediana (cv2, 5x5)"], resultados["sobel (cv2)"],
             resultados["canny (cv2, 50-150)"]],
            ["original", "gaussiano", "mediana", "sobel", "canny"],
            columnas=5,
            titulo_general=f"Clase 2 · videojuego — {origen}, {gris.shape[1]}x{gris.shape[0]}",
        ),
        SALIDA / "bordes_de_escena.png",
    )
    print(f"\nFigura: {ruta}")

    print(
        "\nPara discutir: el gaussiano desenfoca los bordes (los suaviza) y la\n"
        "mediana no, pero la mediana es la única que mata el ruido 'sal y\n"
        "pimienta'. Si el juego solo tuviera ese tipo de ruido, ¿cuál de los\n"
        "dos habría que poner ANTES de Canny? Y lo que no cabe en 16,6 ms en\n"
        "esta maquina, ¿quiza si cabe en la del estudiante? La tabla es la\n"
        "misma en todas, pero el reloj es de cada maquina."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())