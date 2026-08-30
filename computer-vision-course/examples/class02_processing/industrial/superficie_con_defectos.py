#!/usr/bin/env python3
"""
Clase 2 · Industrial — ruido de sensor, filtrado y candidatos a defecto.

La historia de este ejemplo es la de una cámara de inspección que ve una
pieza **como la ve de verdad**: con ruido gaussiano del sensor y con «sal y
pimienta» de píxeles muertos. El defecto —una grieta fina— está ahí, pero
Canny sin filtrado previo encuentra bordes por todas partes y nadie sabe
cuál es el defecto.

El flujo es el del temario:

    superficie con ruido -> filtrado -> Canny -> candidatos a defecto

Y la pregunta es de ingeniería: *¿qué filtro, y con qué fuerza, deja que el
borde de la grieta sobreviva?* Se responde midiendo, no mirando:

* **IoU contra la referencia** — los bordes de la misma pieza **limpia**
  (ruido cero). Sabemos cuáles deberían salir, porque el generador sintético
  nos da la pieza antes de ensuciarla. El IoU de los bordes detectados contra
  esa referencia es la medida honesta de «el filtrado funcionó».
* **Candidatos** — los píxeles de borde que quedan **dentro** de la pieza.
  Con filtrado, la grieta es un racimo de bordes; sin él, el ruido llena la
  pieza de falsos candidatos.

La moraleja con número: el ruido gaussiano se va con el gaussiano o la
mediana, pero la «sal y pimienta» **sólo** se va con la mediana. Un filtro
promedio la convierte en manchas grises, que Canny detecta igual.

Ejecutar:
    python examples/class02_processing/industrial/superficie_con_defectos.py
"""
from __future__ import annotations

import sys
from pathlib import Path

CURSO = Path(__file__).resolve().parents[3]
for _ruta in (CURSO, CURSO.parent):
    if str(_ruta) not in sys.path:
        sys.path.insert(0, str(_ruta))

import cv2
import numpy as np

from cvcourse import synthetic, viz

SALIDA = CURSO / "outputs" / "clase02"

UMBRAL_BAJO, UMBRAL_ALTO = 40.0, 120.0


def en_gris(imagen: np.ndarray) -> np.ndarray:
    return np.clip(
        0.299 * imagen[..., 0] + 0.587 * imagen[..., 1] + 0.114 * imagen[..., 2],
        0, 255,
    ).astype(np.uint8) if imagen.ndim == 3 else imagen


def sal_y_pimienta(gris: np.ndarray, proporcion: float, semilla: int) -> np.ndarray:
    """Píxeles muertos del sensor: algunos en 0, otros en 255, el resto igual.

    Se elige con un generador propio en vez de `skimage.util.random_noise`
    para que se vea exactamente qué se está metiendo: la «sal» es un píxel que
    se queda clavado en 255 y la «pimienta» uno clavado en 0, sin ninguna
    relación con lo que había delante. Es un ruido **no aditivo**: no suma,
    sustituye.
    """
    rng = np.random.default_rng(semilla)
    sucia = gris.copy()
    mascara = rng.random(gris.shape) < proporcion
    valores = rng.random(mascara.sum()) < 0.5
    sucia[mascara] = np.where(valores, 0, 255)
    return sucia


def bordes_canny(gris: np.ndarray) -> np.ndarray:
    return cv2.Canny(gris, UMBRAL_BAJO, UMBRAL_ALTO)


def iou_de_bordes(detectado: np.ndarray, referencia: np.ndarray) -> float:
    """IoU entre dos mapas de borde, castigado por las dos direcciones.

    Un detector que marcara el 90 % de la referencia pero añadiera el doble
    de ruido por fuera tendría un IoU bajo: se premia la cobertura y se
    castiga el exceso, que es exactamente el balance de un criterio de
    inspección.
    """
    union = float((detectado | referencia).sum())
    return float((detectado & referencia).sum()) / union if union else 1.0


def main() -> int:
    SALIDA.mkdir(parents=True, exist_ok=True)

    # La pieza con grieta y su versión limpia: la referencia la da el
    # generador, no hay que etiquetar nada a mano.
    limpia, _ = synthetic.pieza_individual(
        tamano=256, clase="NO_OK", defecto="grieta", ruido=0.0, semilla=3
    )
    gris_limpia = en_gris(limpia)
    referencia = bordes_canny(gris_limpia)

    rng = np.random.default_rng(3)
    gris_sucia = np.clip(
        gris_limpia.astype(float) + rng.normal(0, 3, gris_limpia.shape), 0, 255
    ).astype(np.uint8)
    gris_sucia = sal_y_pimienta(gris_sucia, 0.02, semilla=3)

    print("SUPERFICIE CON DEFECTO + RUIDO (gaussiano sigma 3 y 2% sal y pimienta)")
    print(f"  grieta: la referencia marca {int((referencia > 0).sum())} px de borde en la pieza limpia")

    # Canny sobre la imagen sucia, sin filtrado previo: el «ingenuo».
    bordes_ingenuo = bordes_canny(gris_sucia)

    estrategias = {
        "sin filtrar": gris_sucia,
        "gaussiano 5x5": cv2.GaussianBlur(gris_sucia, (5, 5), 1.1),
        "mediana 5x5": cv2.medianBlur(gris_sucia, 5),
        "promedio 5x5": cv2.blur(gris_sucia, (5, 5)),
        "gaussiano + mediana": cv2.medianBlur(cv2.GaussianBlur(gris_sucia, (5, 5), 1.1), 5),
    }

    print(f"\n{'estrategia':18s} {'IoU vs limpia':>14s} {'px borde':>9s} {'candidatos':>11s}")
    print("-" * 58)
    figuras: list[np.ndarray] = []
    titulos: list[str] = []
    for nombre, filtrada in estrategias.items():
        bordes = bordes_canny(filtrada)
        iou = iou_de_bordes(bordes > 0, referencia > 0)

        # Candidatos a defecto: bordes DENTRO de la pieza. Fuera de ella está
        # la banda transportadora, que también tiene bordes propios y no es
        # un defecto de la pieza.
        mascara_pieza = gris_limpia > 90
        candidatos = bordes > 0
        candidatos &= mascara_pieza

        print(
            f"{nombre:18s} {iou:>14.3f} {int((bordes > 0).sum()):>9d} "
            f"{int(candidatos.sum()):>11d}"
        )
        figuras.append(bordes)
        titulos.append(f"{nombre}\nIoU {iou:.2f}")

    ruta = viz.guardar(
        viz.rejilla(
            [gris_sucia] + figuras, ["imagen tal cual llega del sensor"] + titulos,
            columnas=3,
            titulo_general="Canny sobre la misma superficie con cinco estrategias",
        ),
        SALIDA / "superficie_con_defectos.png",
    )
    print(f"\nFigura: {ruta}")

    print(
        "\nPara discutir: solo la mediana aguanta el IoU, y el 'gaussiano +\n"
        "mediana' es PEOR que la mediana sola. El gaussiano esparce la sal y\n"
        "la pimienta en manchas de varios pixeles; despues, la mediana ya no\n"
        "puede distinguir la mancha del defecto real. El orden y la eleccion\n"
        "del filtro no son intercambiables: cada ruido tiene su filtro, y\n"
        "poner el equivocado antes del correcto destruye lo que el correcto\n"
        "iba a salvar. La grieta en si es el mas tenue de los tres defectos\n"
        "del generador (mota, deformacion, grieta): el que obliga a este\n"
        "preprocesado. En la Clase 3, esos candidatos pasan a ser\n"
        "componentes conexas y se deciden por area y forma."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())