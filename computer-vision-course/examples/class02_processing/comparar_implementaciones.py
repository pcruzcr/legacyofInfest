#!/usr/bin/env python3
"""
Clase 2 · Demostración del profesor — qué hay dentro de Sobel y de Canny.

La pregunta que responde este ejemplo es la de la clase: *entre la imagen y el
resultado hay una caja negra con el nombre de un algoritmo. ¿Qué hace la caja?*

La respuesta se da de dos maneras a la vez:

1. **Paso a paso, con la implementación del motor** (`edge_detection.py`).
   Sobel son dos convoluciones y una magnitud; Canny es suavizado, gradiente,
   supresión no máxima e histéresis. Cada etapa es una función con nombre, y
   este ejemplo muestra la imagen intermedia de cada una.

2. **Biblioteca contra implementación.** `FilterTools.sobel_edge` y
   `canny_edge` llaman a OpenCV; `sobel_edge_propio` y `canny_edge_propio`
   llaman a `edge_detection.py`. Se comparan con dos medidas distintas a
   propósito: el **IoU** píxel a píxel (Sobel casi coincide) y la
   **coincidencia estructural** a un vecindario de 3×3 (Canny coincide en la
   estructura, no en el píxel exacto, porque el suavizado y la normalización
   del gradiente difieren). Los tiempos también se miden, y el resultado
   honesto es que a 800×600 la diferencia no es la del relato «OpenCV es
   veinte veces más rápido»: eso se ve en `rendimiento_convolucion.py`, donde
   se aíslan las convoluciones.

No hace falta cámara: la imagen de trabajo sale del motor (fotograma de escena
con bordes de interfaz y de sprites) y degrada a una pieza sintética si no hay
motor.

Ejecutar:
    python examples/class02_processing/comparar_implementaciones.py
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

CURSO = Path(__file__).resolve().parents[2]
for _ruta in (CURSO, CURSO.parent):
    if str(_ruta) not in sys.path:
        sys.path.insert(0, str(_ruta))

import numpy as np

from cvcourse import engine_bridge, synthetic, viz

SALIDA = CURSO / "outputs" / "clase02"


def escena_del_motor() -> np.ndarray | None:
    """El fotograma de la escena-laboratorio de la Unidad VII, o `None`."""
    if not engine_bridge.hay_motor():
        return None
    return engine_bridge.capturar_escena("filter", fotogramas=1)[0]


def coincidencia_estructural(a: np.ndarray, b: np.ndarray) -> float:
    """Fracción de píxeles de borde de `a` que caen a 1 px de uno de `b`.

    El IoU píxel a píxel castiga a dos implementaciones correctas que difieren
    en un píxel de desplazamiento del borde. Aquí se dilata primero, así que la
    pregunta es «¿encontraron la misma estructura?», que es la que de verdad
    importa. La dilatación es una operación de la Clase 3, sin más misterio:
    marca también los vecinos inmediatos.
    """
    from cv2 import dilate

    borde_a = (a.mean(axis=2) > 0).astype(np.uint8)
    borde_b = (b.mean(axis=2) > 0).astype(np.uint8)
    vecino_de_b = dilate(borde_b, np.ones((3, 3), np.uint8)) > 0
    total = float(borde_a.sum())
    return float((borde_a & vecino_de_b).sum()) / total if total else 1.0


def main() -> int:
    SALIDA.mkdir(parents=True, exist_ok=True)

    fotograma = escena_del_motor()
    if fotograma is not None:
        imagen, origen = fotograma, "fotograma de escena del motor"
    else:
        imagen, origen = synthetic.pieza_individual(
            tamano=256, clase="NO_OK", defecto="grieta", ruido=0.0, semilla=3
        )[0], "pieza sintética (sin motor)"
    print(f"Imagen de trabajo: {origen}  {imagen.shape}")

    engine_bridge.iniciar_pygame_headless()
    from src.framework.processing import edge_detection
    from src.framework.processing.filter_tools import FilterTools

    # ── Parte 1 — Sobel, disecado ─────────────────────────────────────────
    # KERNEL_X deriva en horizontal y por eso responde a bordes VERTICALES.
    # Es el error de signo más repetido al implementarlo a mano, y el motor lo
    # deja anotado en el propio módulo.
    gris = edge_detection.a_gris(imagen)
    gx = edge_detection.convolucionar(gris, edge_detection.KERNEL_X)
    gy = edge_detection.convolucionar(gris, edge_detection.KERNEL_Y)
    magnitud = np.hypot(gx, gy)

    print("\nPARTE 1 - SOBEL PASO A PASO")
    print("  KERNEL_X responde a bordes verticales; KERNEL_Y a horizontales.")
    print(f"  magnitud: media {magnitud.mean():.1f}, maximo {magnitud.max():.1f}")

    ruta = viz.guardar(
        viz.rejilla(
            [
                gris.astype(np.uint8),
                np.abs(gx).clip(0, 255).astype(np.uint8),
                np.abs(gy).clip(0, 255).astype(np.uint8),
                np.clip(magnitud, 0, 255).astype(np.uint8),
            ],
            ["gris", "Gx (bordes verticales)", "Gy (bordes horizontales)", "magnitud"],
            columnas=4, titulo_general="Sobel: dos derivadas y una magnitud",
        ),
        SALIDA / "sobel_paso_a_paso.png",
    )
    print(f"Figura: {ruta}")

    # ── Parte 2 — Canny, etapa por etapa ──────────────────────────────────
    sigma = 1.4
    suave = edge_detection.suavizar(gris, sigma)
    mag, ang = edge_detection.gradiente(suave)
    delgado = edge_detection.supresion_no_maxima(mag, ang)
    bordes = edge_detection.histeresis(delgado, 50.0, 150.0)

    print("\nPARTE 2 - CANNY ETAPA POR ETAPA")
    print(f"  tras el gradiente  : {int((mag > 40).sum()):>6d} pixeles de borde")
    print(f"  tras la supresion  : {int((delgado > 40).sum()):>6d}  (el borde se adelgaza)")
    print(f"  tras la histeresis : {int((bordes > 0).sum()):>6d}  (el ruido se descarta)")

    ruta = viz.guardar(
        viz.rejilla(
            [
                gris.astype(np.uint8),
                suave.astype(np.uint8),
                np.clip(mag, 0, 255).astype(np.uint8),
                np.clip(delgado, 0, 255).astype(np.uint8),
                bordes,
            ],
            ["gris", "1. suavizado gaussiano", "2. gradiente (magnitud)",
             "3. supresion no maxima", "4. histeresis"],
            columnas=5, titulo_general=f"Canny en cuatro pasos - sigma {sigma}",
        ),
        SALIDA / "canny_etapas.png",
    )
    print(f"Figura: {ruta}")

    # ── Parte 3 — Propio contra biblioteca ────────────────────────────────
    # Sobre una pieza limpia con grieta: geometría simple, ruido cero. Es el
    # mejor banco para comparar implementaciones porque no hay azar de por
    # medio: las diferencias que queden son del algoritmo, no del ruido.
    pieza, _ = synthetic.pieza_individual(
        tamano=256, clase="NO_OK", defecto="grieta", ruido=0.0, semilla=3
    )
    superficie = engine_bridge.array_a_superficie(pieza)

    def medir(funcion) -> tuple[np.ndarray, float]:
        t0 = time.perf_counter()
        resultado = funcion()
        return engine_bridge.superficie_a_array(resultado), time.perf_counter() - t0

    sob_opencv, t_sob_o = medir(lambda: FilterTools.sobel_edge(superficie))
    sob_propio, t_sob_p = medir(lambda: FilterTools.sobel_edge_propio(superficie))
    can_opencv, t_can_o = medir(lambda: FilterTools.canny_edge(superficie, 50, 150))
    can_propio, t_can_p = medir(
        lambda: FilterTools.canny_edge_propio(superficie, 50, 150, sigma=sigma)
    )

    def iou_pixel(a: np.ndarray, b: np.ndarray) -> float:
        act_a, act_b = a.mean(axis=2) > 0, b.mean(axis=2) > 0
        union = float((act_a | act_b).sum())
        return float((act_a & act_b).sum()) / union if union else 1.0

    sob_iou = iou_pixel(sob_propio, sob_opencv)
    can_est = coincidencia_estructural(can_propio, can_opencv)

    print("\nPARTE 3 - PROPIOS CONTRA OPENCV (pieza limpia con grieta)")
    print(
        f"  {'operacion':14s} {'propio (s)':>11s} {'OpenCV (s)':>11s} "
        f"{'concordancia':>13s}"
    )
    print(
        f"  {'sobel':14s} {t_sob_p:>11.4f} {t_sob_o:>11.4f} "
        f"{f'IoU {sob_iou:.3f}':>13s}"
    )
    print(
        f"  {'canny':14s} {t_can_p:>11.4f} {t_can_o:>11.4f} "
        f"{f'estructura {can_est:.3f}':>13s}"
    )

    ruta = viz.guardar(
        viz.rejilla(
            [pieza, sob_opencv, sob_propio, can_opencv, can_propio],
            ["pieza con grieta", "Sobel OpenCV", "Sobel propio",
             "Canny OpenCV", "Canny propio"],
            columnas=5, titulo_general="Propio contra biblioteca - la misma estructura",
        ),
        SALIDA / "propio_vs_opencv.png",
    )
    print(f"Figura: {ruta}")

    print(
        "\nPara discutir: Sobel coincide en casi todos los pixeles (IoU alto)\n"
        "porque es la misma matematica. Canny coincide en la estructura pero\n"
        "no en el pixel exacto: el suavizado gaussiano, la normalizacion del\n"
        "gradiente y la histeresis difieren en los detalles. Y los tiempos no\n"
        "son los del relato 'veinte veces mas rapido': a 800x600 el coste de\n"
        "conversion y de la propia surface lo enmascara. Eso se aísla en\n"
        "rendimiento_convolucion.py, que cronometra las convoluciones solas."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())