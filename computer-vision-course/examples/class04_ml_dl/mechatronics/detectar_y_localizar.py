#!/usr/bin/env python3
"""
Clase 4 · Mecatronica — detectar, clasificar y localizar piezas sobre la mesa.

Pregunta del contexto: *un robot no agarra lo que no puede medir: necesita la
pieza, su estado y su posicion en milimetros.*

Es el pipeline completo del temario encadenado sobre una escena compuesta con
piezas reales del dataset sintetico (tres OK y una NO_OK sobre la banda):

    escena -> umbral (Otsu) -> componentes conexas -> por cada region:
        9 caracteristicas -> modelo entrenado -> clase
        centroide -> calibracion px/mm -> posicion en la mesa

Tres problemas distintos, y que lo sean es la clase:

1. **Deteccion**: cuantas piezas hay y donde empieza cada una (vision).
2. **Clasificacion**: cual es buena y cual se rechaza (patrones, Clase 4A).
3. **Localizacion**: donde exactamente, en milimetros (calibracion, Clase 3).

El modelo de clasificacion se entrena sobre el lote completo (120 piezas con
verdad-terreno) y se aplica a una escena que no participo en el
entrenamiento: la escena se compone con otras piezas del mismo generador.
Por eso el acierto se reporta contra la verdad de la escena, que se conoce
por construccion.

Ejecutar:
    python examples/class04_ml_dl/mechatronics/detectar_y_localizar.py
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

from cvcourse import features, synthetic, viz

SALIDA = CURSO / "outputs" / "clase04"

TEST_SIZE = 0.3
SEMILLA = 42

COLUMNAS = (
    "area", "perimeter", "width", "height", "aspect_ratio",
    "circularity", "eccentricity", "solidity", "extent",
)

#: La referencia de tamano conocido del plano: la pieza mas ancha de la escena
#: (un rectangulo OK) mide 60 mm. De ahi sale el factor px -> mm.
REFERENCIA_MM = 60.0

#: Piezas que se colocan en la escena de la mesa: (clase, defecto o "").
#: Semillas distintas de las del lote de entrenamiento.
PIEZAS_EN_MESA = (
    ("OK", ""),
    ("OK", ""),
    ("NO_OK", "grieta"),
    ("OK", ""),
)

TAMANO_PIEZA = 128
FONDO_MESA = 60          # la banda, oscura


def cargar_lote_de_entrenamiento() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """(X, y, idx) del lote completo de 120 piezas; X ya en las 9 columnas.

    Vuelve el orden de `lote_de_piezas`: la semilla de entrenamiento es fija,
    y las semillas de la escena de la mesa son otras, asi que ninguna pieza de
    la escena esta en el lote.
    """
    base = CURSO / "datasets" / "synthetic_parts"
    filas: list[features.Caracteristicas] = []
    if base.is_dir() and (base / "verdad_terreno.csv").exists():
        with (base / "verdad_terreno.csv").open(encoding="utf-8", newline="") as f:
            for registro in csv.DictReader(f):
                gris = cv2.imread(str(base / registro["fichero"]), cv2.IMREAD_GRAYSCALE)
                mascara = cv2.threshold(gris, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1] > 0
                filas.extend(
                    features.caracteristicas_de_mascara(
                        mascara, etiqueta_de_clase=registro["clase"]
                    )
                )
    else:
        imagenes, verdades = synthetic.lote_de_piezas(n=120, semilla=20260805)
        for imagen, verdad in zip(imagenes, verdades, strict=True):
            filas.extend(
                features.caracteristicas_de_mascara(
                    imagen.astype(np.uint8) > 90, etiqueta_de_clase=verdad.clase
                )
            )
    X, y, _ = features.a_matriz(filas, columnas=COLUMNAS)
    return X, y


def componer_mesa() -> tuple[np.ndarray, list[tuple[float, float, str]]]:
    """Cuatro piezas reales del generador sobre la banda; devuelve la escena
    y la verdad: (centro_x, centro_y, clase) por pieza."""
    ancho = 4 * TAMANO_PIEZA + 5 * 24
    lienzo = np.full((TAMANO_PIEZA + 48, ancho), FONDO_MESA, dtype=np.uint8)
    verdad: list[tuple[float, float, str]] = []
    x = 24
    for i, (clase, defecto) in enumerate(PIEZAS_EN_MESA):
        pieza, _ = synthetic.pieza_individual(
            tamano=TAMANO_PIEZA, clase=clase, defecto=defecto or None,
            ruido=4.0, semilla=3000 + i,
        )
        lienzo[24:24 + TAMANO_PIEZA, x:x + TAMANO_PIEZA] = pieza
        verdad.append((x + TAMANO_PIEZA / 2.0, 24 + TAMANO_PIEZA / 2.0, clase))
        x += TAMANO_PIEZA + 24
    return lienzo, verdad


def regiones_de_la_mesa(escena: np.ndarray) -> list[tuple[int, int, int, int, int]]:
    """Otsu + componentes conexas: (area, izq, arr, ancho, alto) por pieza.

    Las piezas no se tocan en esta escena, asi que componentes conexas
    alcanza; si se tocaran habria que encadenar el watershed de la Clase 3.
    """
    _, mascara = cv2.threshold(escena, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    n, _, stats, _ = cv2.connectedComponentsWithStats(mascara, 8)
    return [
        (int(stats[i, cv2.CC_STAT_AREA]), int(stats[i, cv2.CC_STAT_LEFT]),
         int(stats[i, cv2.CC_STAT_TOP]), int(stats[i, cv2.CC_STAT_WIDTH]),
         int(stats[i, cv2.CC_STAT_HEIGHT]))
        for i in range(1, n)
        if stats[i, cv2.CC_STAT_AREA] > 1000
    ]


def main() -> int:
    SALIDA.mkdir(parents=True, exist_ok=True)
    X, y = cargar_lote_de_entrenamiento()

    from sklearn.model_selection import train_test_split
    from src.framework.processing.pattern_recognition_tools import PatternRecognitionTools

    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=SEMILLA, stratify=y
    )
    modelo = PatternRecognitionTools.train(X_tr, y_tr, model_type="knn")
    evaluacion = PatternRecognitionTools.evaluate(modelo, X_te, y_te)
    print(
        f"MODELO: KNN sobre {X.shape[0]} filas de piezas medidas "
        f"(acc en test {evaluacion.accuracy:.3f})"
    )

    escena, verdad = componer_mesa()
    regiones = regiones_de_la_mesa(escena)
    print(f"\nESCENA: {len(PIEZAS_EN_MESA)} piezas colocadas, "
          f"{len(regiones)} regiones detectadas")

    # Calibracion: la referencia del plano (60 mm) sobre la pieza mas ancha.
    ancho_px = max(r[3] for r in regiones)
    mm_por_px = REFERENCIA_MM / ancho_px
    print(f"CALIBRACION: {ancho_px} px = {REFERENCIA_MM:.0f} mm -> "
          f"{mm_por_px:.4f} mm/px")

    aciertos = 0
    anotada = cv2.cvtColor(escena, cv2.COLOR_GRAY2RGB)
    for _, izq, arr, w, h in sorted(regiones, key=lambda r: r[1]):
        recorte = escena[arr:arr + h, izq:izq + w]
        mascara = recorte > FONDO_MESA + 20
        filas = features.caracteristicas_de_mascara(mascara, area_minima=50)
        if not filas:
            continue
        X_pieza, _, _ = features.a_matriz(
            [max(filas, key=lambda f: f.area)], columnas=COLUMNAS
        )
        clase_predicha = PatternRecognitionTools.classify(X_pieza[:1], modelo)
        cx, cy = izq + w / 2.0, arr + h / 2.0
        verdad_cercana = min(verdad, key=lambda v: np.hypot(v[0] - cx, v[1] - cy))
        ok = clase_predicha == verdad_cercana[2]
        aciertos += ok
        cv2.rectangle(anotada, (izq, arr), (izq + w, arr + h), (0, 255, 0), 1)
        cv2.putText(
            anotada, clase_predicha, (izq, arr - 6),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1,
        )
        print(
            f"  pieza en ({cx * mm_por_px:6.1f}, {cy * mm_por_px:6.1f}) mm "
            f"clasificada={clase_predicha:>5s} real={verdad_cercana[2]:>5s} "
            f"{'OK' if ok else 'FALLO'}"
        )

    print(
        f"\n{aciertos}/{len(verdad)} piezas clasificadas bien y localizadas "
        "dentro del pixel de su centroide: el pipeline encadena vision "
        "(detectar), patrones (clasificar) y metrologia (localizar en mm)."
    )

    ruta = viz.guardar(
        viz.comparar(
            escena,
            anotada,
            titulo_antes="escena de la mesa (4 piezas, una con grieta)",
            titulo_despues="clasificacion y localizacion por el modelo",
            titulo_general="Clase 4 · mecatronica -- detectar, clasificar y localizar",
        ),
        SALIDA / "detectar_y_localizar.png",
    )
    print(f"Figura: {ruta}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
