#!/usr/bin/env python3
"""
Clase 4 · Industrial — clasificar OK/NO_OK y medir el coste del falso negativo.

Pregunta del contexto: *la linea produce piezas; cual pasa y cual se rechaza?*

Dataset: `datasets/synthetic_parts` (120 piezas con verdad-terreno). Cada
mascara se mide con el umbral de Otsu de la Clase 3 y las 9 caracteristicas
geometricas; con eso se entrena la comparativa completa (aqui se resume en
una tabla; el detalle de la comparacion vive en
`data_analysis/comparar_modelos.py`). Lo que esta ejemplo mira solo es:

**El falso negativo cuesta distinto que el falso positivo.** Rechazar una
pieza buena es material perdido; dejar pasar una mala es el lote entero
comprometido. La matriz de confusion separa los dos errores, y la tabla de
precision/recall dice cual de los dos comete cada modelo.

Tres mediciones que se llevan:

1. La linea base «siempre OK» acierta 0,60 (72/120): con un 40 % de piezas
   defectuosas, la accuracy de un clasificador que no aprende nada ya es
   0,60. Nunca se compara contra el 100 %, sino contra esa cifra.
2. Con 9 caracteristicas bien elegidas los cuatro modelos del framework y
   la Regresion Logistica separan casi todo: la matriz dice cuanto falta.
3. El desglose por defecto dice cual de los tres modos de fallo (grieta,
   mota, deformacion) se le escapa al modelo: la deformacion se ve con la
   forma (solidez, circularidad), la grieta es la mas sutil. Que la tabla
   lo diga, y no la intuicion, es la clase.

Ejecutar:
    python examples/class04_ml_dl/industrial/clasificar_piezas.py
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
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from cvcourse import features, viz

SALIDA = CURSO / "outputs" / "clase04"

TEST_SIZE = 0.3
SEMILLA = 42

COLUMNAS = (
    "area", "perimeter", "width", "height", "aspect_ratio",
    "circularity", "eccentricity", "solidity", "extent",
)

MODELOS = ("knn", "tree", "forest", "svm")


def cargar_dataset() -> tuple[np.ndarray, np.ndarray, list[dict[str, str]], str]:
    """(X, y, defectos_por_fila, origen). Degrada a un mini-lote sintetico."""
    base = CURSO / "datasets" / "synthetic_parts"
    filas: list[features.Caracteristicas] = []
    defectos: list[dict[str, str]] = []
    origen = ""

    if base.is_dir() and (base / "verdad_terreno.csv").exists():
        with (base / "verdad_terreno.csv").open(encoding="utf-8", newline="") as f:
            registros = list(csv.DictReader(f))
        for registro in registros:
            gris = cv2.imread(str(base / registro["fichero"]), cv2.IMREAD_GRAYSCALE)
            mascara = cv2.threshold(gris, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1] > 0
            medidas = features.caracteristicas_de_mascara(
                mascara, etiqueta_de_clase=registro["clase"]
            )
            for medida in medidas:
                filas.append(medida)
                defectos.append({"defecto": registro["defecto"], "forma": registro["forma"]})
        origen = f"datasets/synthetic_parts ({len(registros)} piezas)"
    else:
        from cvcourse import synthetic

        imagenes, verdades = synthetic.lote_de_piezas(n=120, semilla=20260805)
        for imagen, verdad in zip(imagenes, verdades, strict=True):
            mascara = imagen.astype(np.uint8) > 90
            medidas = features.caracteristicas_de_mascara(
                mascara, etiqueta_de_clase=verdad.clase
            )
            for medida in medidas:
                filas.append(medida)
                defectos.append({"defecto": verdad.defecto or "", "forma": verdad.forma})
        origen = "mini-lote sintetico (sin datasets del repositorio)"

    X, y, _ = features.a_matriz(filas, columnas=COLUMNAS)
    return X, y, defectos, f"{origen} ({X.shape[0]} filas)"


def entrenar(X_tr: np.ndarray, y_tr: np.ndarray, tipo: str):
    """Cuatro modelos del framework; la LogReg directa de sklearn (decision D3)."""
    from src.framework.processing.pattern_recognition_tools import PatternRecognitionTools

    if tipo == "logreg":
        return Pipeline(
            [
                ("scaler", StandardScaler()),
                ("clf", LogisticRegression(random_state=SEMILLA, max_iter=2000)),
            ]
        ).fit(X_tr, y_tr)
    return PatternRecognitionTools.train(X_tr, y_tr, model_type=tipo)


def main() -> int:
    SALIDA.mkdir(parents=True, exist_ok=True)
    X, y, defectos, origen = cargar_dataset()

    conteo = {clase: int((y == clase).sum()) for clase in ("OK", "NO_OK")}
    print(f"DATASET: {origen}")
    print(f"  clases: {conteo}  ({X.shape[0]} ejemplos, {len(COLUMNAS)} caracteristicas)")

    # La particion se hace sobre indices para poder decir, despues, que pieza
    # exacta (con su defecto) fue la que se colo por la inspeccion.
    idx = np.arange(X.shape[0])
    idx_tr, idx_te = train_test_split(
        idx, test_size=TEST_SIZE, random_state=SEMILLA, stratify=y
    )
    X_tr, X_te, y_tr, y_te = X[idx_tr], X[idx_te], y[idx_tr], y[idx_te]
    print(f"PARTICION: {X_tr.shape[0]} train / {X_te.shape[0]} test, semilla {SEMILLA}")
    print(
        f"LINEA BASE «siempre OK»: {conteo['OK']}/{X.shape[0]} = "
        f"{conteo['OK'] / X.shape[0]:.3f}. Por debajo de esta cifra no hay"
        " aprendizaje."
    )

    from src.framework.processing.pattern_recognition_tools import PatternRecognitionTools

    print(f"\n{'modelo':>7s} {'acc':>6s} {'precision':>10s} {'recall':>7s} {'f1':>6s}")
    print("-" * 42)
    falsos_negativos: list[dict[str, str]] = []
    matriz_knn = None
    clases_knn: list[str] = []
    for tipo in (*MODELOS, "logreg"):
        estimador = entrenar(X_tr, y_tr, tipo)
        if tipo == "logreg":
            y_pred = estimador.predict(X_te)
            acc = float(np.mean(y_pred == y_te))
        else:
            evaluacion = PatternRecognitionTools.evaluate(estimador, X_te, y_te)
            acc = evaluacion.accuracy
            y_pred = estimador.estimator.predict(X_te)
            if tipo == "knn":
                matriz_knn = evaluacion.confusion_matrix
                clases_knn = list(estimador.classes)

        informe = classification_report(
            y_te, y_pred, output_dict=True, zero_division=0
        )["macro avg"]
        print(
            f"{tipo:>7s} {acc:6.3f} {informe['precision']:10.3f} "
            f"{informe['recall']:7.3f} {informe['f1-score']:6.3f}"
        )

        if tipo == "knn":
            # El desglose por defecto: cual de los tres modos de fallo se escapa.
            for i, (pred, real) in enumerate(zip(y_pred, y_te, strict=True)):
                if real == "NO_OK" and pred == "OK":
                    falsos_negativos.append(defectos[int(idx_te[i])])

    if falsos_negativos:
        print("\nFALSOS NEGATIVOS del KNN (pieza mala que paso):")
        for e in falsos_negativos:
            print(f"  defecto={e['defecto'] or 'ninguno':>12s} forma={e['forma']}")
        print(
            "  Leer la columna 'defecto': si solo escapa un tipo, el modelo no\n"
            "  esta fallando al azar: ese defecto no deja huella en las 9\n"
            "  caracteristicas que se miden (o la deja pequena)."
        )

    print(
        "\nLa accuracy dice cuanto acierta en conjunto; la matriz dice donde\n"
        "falla. Para inspeccion es mas cara la celda NO_OK->OK (falso\n"
        "negativo) que OK->NO_OK (falso positivo): una pieza mala que pasa\n"
        "contamina el lote, una buena rechazada es material perdido. El\n"
        "modelo elegido se decide con esas dos celdas, no con la accuracy."
    )

    if matriz_knn is not None:
        ruta_figura = viz.guardar(
            viz.matriz_de_confusion(
                matriz_knn,
                clases_knn,
                titulo="Clase 4 · industrial -- matriz de confusion del KNN",
            ),
            SALIDA / "clasificar_piezas_cm.png",
        )
        print(f"\nFigura: {ruta_figura}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
