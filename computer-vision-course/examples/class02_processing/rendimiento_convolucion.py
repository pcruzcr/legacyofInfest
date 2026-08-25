#!/usr/bin/env python3
"""
Clase 2 · Rendimiento — la misma convolución en cuatro implementaciones.

La pregunta es de presupuesto, y la respuesta es una tabla reproducible:
*¿cuánto tarda una convolución 3x3 sobre una imagen de 800x600 según cómo
esté implementada?*

| Implementación | Qué es |
|---|---|
| `edge_detection.convolucionar` | una convolución en NumPy puro, con `np.pad` y suma de desplazamientos. Es la que los estudiantes pueden leer y modificar |
| `scipy.ndimage.convolve` | la misma operación, ya optimizada en C sobre el mismo kernel |
| `cv2.filter2D` | OpenCV: C optimizado, con kernels pequeños hasta tramas SIMD |
| `numba` (si está instalada) | el mismo bucle triple de toda la vida, compilado JIT. Se incluye para romper un mito: *vectorizado no siempre es más rápido que un bucle compilado* |

Por qué la tabla es reproducible y no un número suelto:

* misma imagen (se genera con semilla fija);
* mediana de las repeticiones, no la primera (una pasada casual no decide);
* las operaciones se cronometran **solas**, sin conversiones de superficie ni
  asignaciones de contexto que ensucien la medida.

Los dos presupuestos que se discuten: el del videojuego (60 fps => 16,6 ms
por fotograma) y el de la línea de producción (5 piezas por segundo => 200 ms
por imagen).

Abajo del todo se añade la pregunta que conecta con el juego: Canny entero
(cv2) sobre 800x600 cuesta menos de 3 ms. La convolución no es el cuello de
botella si se deja a quien la hace bien.

Ejecutar:
    python examples/class02_processing/rendimiento_convolucion.py
"""
from __future__ import annotations

import csv
import sys
import time
from pathlib import Path

CURSO = Path(__file__).resolve().parents[2]
REPO = CURSO.parent
for _ruta in (CURSO, REPO):
    if str(_ruta) not in sys.path:
        sys.path.insert(0, str(_ruta))

import numpy as np

from cvcourse import viz

SALIDA = CURSO / "outputs" / "clase02"

REPETICIONES = 25
TAMANO = (600, 800)


def cronometrar(fn, repeticiones: int = REPETICIONES) -> float:
    """Mediana de los tiempos de `fn`, en milisegundos."""
    fn()
    tiempos = []
    for _ in range(repeticiones):
        t0 = time.perf_counter()
        fn()
        tiempos.append((time.perf_counter() - t0) * 1000.0)
    return float(np.median(tiempos))


def main() -> int:
    SALIDA.mkdir(parents=True, exist_ok=True)

    # Misma imagen para todos: un patrón con gradientes en las dos direcciones
    # y algo de ruido gaussiano. Semilla fija: reproducible en las 30 máquinas.
    rng = np.random.default_rng(0)
    filas, columnas = np.ogrid[: TAMANO[0], : TAMANO[1]]
    base = ((filas + columnas) % 120 + 60).astype(np.float32)
    imagen = np.clip(base + rng.normal(0, 3, TAMANO), 0, 255).astype(np.uint8)

    nucleo_3 = np.ones((3, 3), dtype=np.float32) / 9.0
    nucleo_5 = np.ones((5, 5), dtype=np.float32) / 25.0

    from scipy import ndimage
    import cv2

    from src.framework.processing import edge_detection

    filas_tabla: list[dict[str, object]] = []

    def numba_convolucionar(nucleo: np.ndarray):
        import numba

        @numba.njit
        def _convolucionar(imagen, nucleo):
            alto, ancho = imagen.shape
            r = nucleo.shape[0] // 2
            salida = np.zeros((alto, ancho), dtype=np.float32)
            for i in range(r, alto - r):
                for j in range(r, ancho - r):
                    acumulado = 0.0
                    for a in range(nucleo.shape[0]):
                        for b in range(nucleo.shape[0]):
                            acumulado += (
                                nucleo[a, b] * imagen[i - r + a, j - r + b]
                            )
                    salida[i, j] = acumulado
            return salida

        _convolucionar(imagen, nucleo)   # primera llamada: compila el JIT
        return lambda: _convolucionar(imagen, nucleo)

    numba_disponible = False
    try:
        numba_3 = numba_convolucionar(nucleo_3)
        numba_5 = numba_convolucionar(nucleo_5)
        numba_disponible = True
    except ImportError:
        numba_3 = numba_5 = None

    def con_nucleo(funcion, nucleo):
        """Cierra una llamada `funcion(imagen, nucleo)` sin argumentos."""
        return lambda: funcion(imagen, nucleo)

    def filtro2d(imagen, nucleo):
        """`cv2.filter2D` pide la profundidad del resultado entre los dos."""
        return cv2.filter2D(imagen, -1, nucleo)

    implementaciones: list[tuple[str, object]] = [
        ("convolucionar (numpy)", lambda k: con_nucleo(edge_detection.convolucionar, k)),
        ("scipy.ndimage.convolve", lambda k: con_nucleo(ndimage.convolve, k)),
        ("cv2.filter2D", lambda k: con_nucleo(filtro2d, k)),
    ]
    if numba_disponible:
        numbas = {id(nucleo_3): numba_3, id(nucleo_5): numba_5}

        def numba(nucleo):
            return numbas[id(nucleo)]

        implementaciones.append(("numba (bucle triple)", numba))

    for nombre, constructor in implementaciones:
        for nucleo, tam in ((nucleo_3, "3x3"), (nucleo_5, "5x5")):
            fn = constructor(nucleo)
            ms = cronometrar(fn)
            filas_tabla.append(
                {"implementacion": nombre, "kernel": tam, "ms": ms,
                 "cabe a 60 fps": ms < 16.6, "cabe en linea (200 ms)": ms < 200.0}
            )
            print(
                f"{nombre:26s} {tam:>4s} {ms:>8.2f} ms   "
                f"{'SI' if ms < 16.6 else 'NO':>3s} a 60 fps   "
                f"{'SI' if ms < 200.0 else 'NO':>3s} en linea"
            )

    # La tabla en CSV para que el laboratorio la cite con números exactos en
    # `analisis.md`. Se escribe con el módulo `csv` para que no dependa de
    # pandas — la Clase 3 sí lo usa, y pedirlo hoy sería capricho.
    ruta_tabla = SALIDA / "tabla_de_rendimiento.csv"
    with ruta_tabla.open("w", newline="", encoding="utf-8") as fichero:
        escritor = csv.DictWriter(fichero, fieldnames=filas_tabla[0].keys())
        escritor.writeheader()
        escritor.writerows(filas_tabla)
    print(f"\nTabla guardada: {ruta_tabla}")

    # La misma tabla como figura, para la rejilla de conclusiones.
    ruta_fig = viz.guardar(
        viz.rejilla(
            [imagen],
            [f"imagen de referencia {TAMANO[1]}x{TAMANO[0]}, semilla 0"],
            columnas=1, titulo_general="Imagen usada para todos los cronometrajes",
        ),
        SALIDA / "imagen_de_rendimiento.png",
    )
    print(f"Figura: {ruta_fig}")

    # Cierre con datos: el pipeline completo cabe en el presupuesto de un
    # juego, si las piezas pesadas se dejan a quien las hace bien.
    import cv2 as _cv2

    canny_ms = cronometrar(lambda: _cv2.Canny(imagen, 50, 150))
    print(
        f"\nCanny entero (cv2) sobre la misma imagen: {canny_ms:.2f} ms. La\n"
        "convolucion bien hecha no es el cuello de botella; el cuello de\n"
        "botella es hacerla uno mismo en el juego."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())