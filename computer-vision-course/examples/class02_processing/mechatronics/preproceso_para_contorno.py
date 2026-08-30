#!/usr/bin/env python3
"""
Clase 2 · Mecatrónica — el preprocesado que hace posible el contorno.

El robot de pick-and-place de la Clase 3 no necesita los bordes de la pieza:
necesita **un** contorno, cerrado, que sea el de la pieza. Esta es la
pregunta del contexto: *¿qué hay que hacerle a la imagen para que la etapa
siguiente (contorno, centroide) tenga una sola línea continua en vez de un
cableado?*

El flujo es el del temario, y el criterio de «funcionó» no es estético:

    toma -> preprocesado -> Canny -> calidad del contorno

Tres medidas, cada una una promesa hacia la Clase 3:

* **componentes conexas del mapa de borde** — el contorno de una pieza es
  UNA línea cerrada. Si Canny devuelve 400 trozos, `find_contours` de la
  Clase 3 encontrará 400 contornos y ninguno será la pieza. La cuenta debe
  caer cerca de 1-3 (contorno + grieta si la hay);
* **IoU contra el borde de la verdad-terreno** — el generador sintético
  entrega la máscara exacta de la pieza; su frontera es el contorno que el
  robot necesita. Cuanto más cerca del IoU 1, mejor;
* **cobertura** — el trozo más grande del mapa de borde debería ser el
  contorno de la pieza, no un fragmento suelto.

La toma es la de una célula real: pieza sobre banda, con ruido gaussiano y
de sal y pimienta. Lo que se demuestra es que a la Clase 3 hay que llegar
con la imagen lista, y que la lista de cosas que la hacen lista se decide y
se mide en esta clase.

Ejecutar:
    python examples/class02_processing/mechatronics/preproceso_para_contorno.py
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
from skimage.measure import label

from cvcourse import synthetic, viz

SALIDA = CURSO / "outputs" / "clase02"


def en_gris(imagen: np.ndarray) -> np.ndarray:
    return np.clip(
        0.299 * imagen[..., 0] + 0.587 * imagen[..., 1] + 0.114 * imagen[..., 2],
        0, 255,
    ).astype(np.uint8) if imagen.ndim == 3 else imagen


def calidad_del_contorno(bordes: np.ndarray, frontera_verdad: np.ndarray) -> dict[str, float]:
    """Las tres medidas que la Clase 3 va a necesitar.

    `bordes` es un mapa uint8 con 0/255. Se etiquetan las componentes conexas
    (8-vecindad) y se mira: cuántas son, qué fracción de los píxeles de borde
    está en la más grande, y cuánto coincide el mapa entero con la frontera
    de la pieza verdadera.
    """
    activos = bordes > 0
    if not activos.any():
        return {"componentes": float("inf"), "cobertura_%": 0.0, "iou": 0.0}

    etiquetas = label(activos)
    conteo, _ = np.unique(etiquetas, return_counts=True)
    tamanos = np.bincount(etiquetas.ravel())[1:]
    mayor = int(tamanos.max())
    total = int(tamanos.sum())
    union = float((activos | frontera_verdad).sum())
    iou = float((activos & frontera_verdad).sum()) / union if union else 1.0
    return {
        "componentes": float(len(conteo)),
        "cobertura_%": mayor / total * 100.0,
        "iou": iou,
    }


def main() -> int:
    SALIDA.mkdir(parents=True, exist_ok=True)

    # Verdad-terreno: la máscara de la pieza, y su frontera. (La de la Clase
    # 3 es bbox y máscara; aquí el contorno buscado es la frontera de esa
    # máscara, que es lo que pide un centroide.)
    limpia, verdad = synthetic.pieza_individual(
        tamano=256, clase="OK", forma="rectangulo", ruido=0.0, semilla=5
    )
    gris_limpio = en_gris(limpia)
    mascara = gris_limpio > 90
    frontera = np.zeros_like(mascara)
    frontera[1:, :] |= mascara[:-1, :]
    frontera[:-1, :] |= mascara[1:, :]
    frontera[:, 1:] |= mascara[:, :-1]
    frontera[:, :-1] |= mascara[:, 1:]
    frontera &= ~mascara

    # La toma de la célula: la misma pieza con ruido de sensor.
    rng = np.random.default_rng(5)
    sucia = np.clip(gris_limpio.astype(float) + rng.normal(0, 3, gris_limpio.shape), 0, 255)
    sucia = sucia.astype(np.uint8)
    granos = rng.random(sucia.shape) < 0.03
    sucia[granos] = np.where(rng.random(granos.sum()) < 0.5, 0, 255)

    escenarios = {
        "sin preprocesado": sucia,
        "mediana 3x3": cv2.medianBlur(sucia, 3),
        "mediana 5x5": cv2.medianBlur(sucia, 5),
        "mediana 5x5 + gaussiano": cv2.GaussianBlur(cv2.medianBlur(sucia, 5), (5, 5), 1.1),
    }

    print("TOMA DE LA CELULA: pieza sobre banda, ruido gaussiano + sal y pimienta")
    print(f"  la frontera verdadera de la pieza tiene {int(frontera.sum())} px")

    print(f"\n{'escenario':24s} {'componentes':>11s} {'cobertura%':>10s} {'IoU':>6s}")
    print("-" * 58)
    figuras: list[np.ndarray] = []
    titulos: list[str] = []
    for nombre, lista in escenarios.items():
        bordes = cv2.Canny(lista, 40, 120)
        c = calidad_del_contorno(bordes, frontera)
        print(
            f"{nombre:24s} {c['componentes']:>11.0f} {c['cobertura_%']:>10.1f} {c['iou']:>6.3f}"
        )
        figuras.append(bordes)
        titulos.append(f"{nombre}\n{c['componentes']:.0f} trozos, IoU {c['iou']:.2f}")

    ruta = viz.guardar(
        viz.rejilla(
            [sucia, frontera.astype(np.uint8) * 255] + figuras,
            ["la toma tal cual", "frontera verdadera (lo que el robot necesita)"] + titulos,
            columnas=3,
            titulo_general="Del cableado al contorno: el preprocesado decide cuantos trozos hay",
        ),
        SALIDA / "preproceso_para_contorno.png",
    )
    print(f"\nFigura: {ruta}")

    buena = calidad_del_contorno(cv2.Canny(escenarios["mediana 5x5"], 40, 120), frontera)
    print(
        "\nEl criterio de la Clase 3: 'componentes' es cuantos contornos va a\n"
        f"encontrar find_contours. Con la mediana 5x5 son {buena['componentes']:.0f};\n"
        "sin preprocesado, uno por mota de ruido. La cobertura dice si el trozo\n"
        "grande es la pieza. Y IoU mide si el contorno coincide con la\n"
        "verdad: es la misma medida que la Clase 3 usara para calificar el\n"
        "resultado de la segmentacion."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())