#!/usr/bin/env python3
"""
Clase 3 · Mecatrónica — contorno, centroide y la calibración píxel → mm.

Un robot de pick-and-place no agarra píxeles: agarra milímetros. La pregunta
del contexto: *¿dónde está la pieza en la mesa de trabajo, en unidades de
mundo real, y con qué tolerancia?*

El flujo es el del temario, tal cual se enseña:

    contorno -> centroide -> bbox -> calibración -> posición en mm

Y cada etapa responde una pregunta distinta que conviene no confundir:

* **Contorno** — la frontera cerrada. Su longitud es *cuánto borde hay*:
  el rectángulo de 82 px de lado mide 322 px de contorno.
* **Centroide** — *dónde está* la pieza. El error contra la verdad-terreno
  del generador sintético se reporta en la tabla: 0,7 px en el rectángulo y
  0,0 en el círculo.
* **Bounding box** — la caja que lo encierra: 82x82 y 81x81 px. Útil para
  rechazar piezas por tamaño sin mirar la forma.
* **Calibración** — convierte píxeles en milímetros dividiendo por un
  objeto de tamaño conocido. Aquí la pieza del plano mide 60 mm de ancho;
  con sus 82 px sale un factor de 0,7317 mm/px y el centroide en (63,5, 63,5)
  px está a (46,5, 46,5) mm del origen de la mesa.

La validación es contra la verdad del generador: sin ella, «el centroide
salió bien» sería una opinión; con ella, es una tabla.

Ejecutar:
    python examples/class03_segmentation/mechatronics/contorno_y_centroide.py
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


def medir(imagen: np.ndarray) -> tuple[dict[str, float], np.ndarray, np.ndarray]:
    """Contorno, centroide y bbox de la pieza. Devuelve también el contorno
    y la máscara usados, para dibujar la figura."""
    gris = imagen.astype(np.uint8)
    suavizada = cv2.GaussianBlur(gris, (5, 5), 1.0)
    _, mascara = cv2.threshold(suavizada, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    contornos, _ = cv2.findContours(mascara, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contorno = max(contornos, key=cv2.contourArea)
    momentos = cv2.moments(contorno)
    cx = momentos["m10"] / momentos["m00"]
    cy = momentos["m01"] / momentos["m00"]
    _, _, w, h = cv2.boundingRect(contorno)
    area = float(cv2.contourArea(contorno))
    perimetro = float(cv2.arcLength(contorno, True))
    return {
        "area": area,
        "perimetro": perimetro,
        "centroide_x": cx,
        "centroide_y": cy,
        "ancho": float(w),
        "alto": float(h),
        "circularidad": 4.0 * math.pi * area / (perimetro**2),
    }, contorno, mascara


def main() -> int:
    SALIDA.mkdir(parents=True, exist_ok=True)

    ancho_real_mm = 60.0  # la pieza del plano: 60 mm de ancho

    print("CELULA: pieza sobre mesa, camara cenital. Calibracion con la pieza")
    print(f"  del plano: {ancho_real_mm:.0f} mm de ancho.")
    print(f"\n{'pieza':>10s} {'area':>7s} {'perimetro':>9s} {'bbox':>8s} "
          f"{'centroide':>14s} {'error':>6s} {'circularidad':>12s}")
    print("-" * 84)

    figuras: list[np.ndarray] = []
    titulos: list[str] = []
    factores: list[float] = []
    errores_px: list[float] = []
    medidas: list[tuple[str, dict[str, float]]] = []

    for forma in ("rectangulo", "circulo"):
        limpia, verdad = synthetic.pieza_individual(
            forma=forma, tamano=128, ruido=4.0, semilla=7
        )
        m, contorno, _ = medir(limpia)
        medidas.append((forma, m))
        error = math.hypot(
            m["centroide_x"] - verdad.centro[1],
            m["centroide_y"] - verdad.centro[0],
        )
        errores_px.append(error)
        factor = ancho_real_mm / m["ancho"]
        factores.append(factor)

        dibujo = cv2.cvtColor(limpia, cv2.COLOR_GRAY2BGR)
        cv2.drawContours(dibujo, [contorno], -1, (0, 255, 0), 1)
        cv2.circle(dibujo, (int(m["centroide_x"]), int(m["centroide_y"])), 3, (0, 0, 255), -1)
        cv2.rectangle(
            dibujo,
            (int(m["centroide_x"] - m["ancho"] / 2), int(m["centroide_y"] - m["alto"] / 2)),
            (int(m["centroide_x"] + m["ancho"] / 2), int(m["centroide_y"] + m["alto"] / 2)),
            (255, 0, 255), 1,
        )
        pos_mm = (
            m["centroide_x"] * factor,
            m["centroide_y"] * factor,
        )
        figuras.append(dibujo)
        titulos.append(
            f"{forma}\ncentroide ({m['centroide_x']:.1f}, {m['centroide_y']:.1f}) px "
            f"= ({pos_mm[0]:.1f}, {pos_mm[1]:.1f}) mm"
        )

        print(
            f"{forma:>10s} {m['area']:7.0f} {m['perimetro']:9.0f} "
            f"{m['ancho']:3.0f}x{m['alto']:<3.0f} "
            f"({m['centroide_x']:6.1f},{m['centroide_y']:6.1f}) {error:6.1f} {m['circularidad']:12.3f}"
        )
        print(
            f"{'':10s}  verdad: centro ({verdad.centro[1]:.1f}, {verdad.centro[0]:.1f}) px, "
            f"radio/bbox segun generador -> factor {factor:.4f} mm/px"
        )

    print("\nPOSICION EN LA MESA (mm, origen = esquina superior izquierda):")
    for (forma, m), factor in zip(medidas, factores, strict=True):
        pos = (m["centroide_x"] * factor, m["centroide_y"] * factor)
        print(f"  {forma:>10s}: ({pos[0]:.1f}, {pos[1]:.1f}) mm")

    ruta = viz.guardar(
        viz.rejilla(
            figuras,
            titulos,
            columnas=2,
            titulo_general="Clase 3 · mecatronica -- contorno, centroide, bbox y calibracion",
        ),
        SALIDA / "contorno_y_centroide.png",
    )
    print(f"\nFigura: {ruta}")

    peor_error_mm = max(errores_px) * max(factores)
    print(
        f"\nEl robot agarra en el centroide, pero su pinza tiene tolerancia:\n"
        f"el peor error de medicion ({max(errores_px):.1f} px) convertido a mm "
        f"es {peor_error_mm:.2f} mm -- una fraccion de la tolerancia de\n"
        "cualquier pinza industrial. La circularidad del rectangulo vs. la\n"
        "del circulo (0,80 vs. 0,91) es el numero que la Clase 4 usara para\n"
        "distinguirlos sin mirarlos."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())