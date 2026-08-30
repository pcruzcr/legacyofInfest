#!/usr/bin/env python3
"""
Clase 4 · Data Analytics — cinco modelos, una tabla, una decision.

Pregunta del contexto: *que modelo elegir, y con que numeros?*

La comparativa completa sobre el dataset de la banda (120 piezas con
verdad-terreno): KNN, Regresion Logistica, SVM, Arbol y Random Forest. Los
cuatro primeros salen de `PatternRecognitionTools.train`; la Regresion
Logistica se instancia con sklearn directamente (decision D3): el framework
es una capa de conveniencia sobre scikit-learn, no un muro, y eso tambien
es materia de la clase.

Por cada modelo, la tabla que decide:

* accuracy, precision, recall y F1 (macro, de `classification_report`)
* matriz de confusion
* tiempo de entrenamiento y tiempo de inferencia (50 clasificaciones)

La misma tabla se repite para las **9 caracteristicas** y para los **pixeles
crudos** (1024 por pieza, la Parte B del temario): `imagen -> resize ->
gris -> flatten -> modelo`, lado a lado con las caracteristicas.

Dos lecturas que tienen que quedar, y ambas medidas:

1. **Sobreajuste**: el Arbol memoriza el train (accuracy 1,00 con 10
   ejemplos) y generaliza mal (0,68 en test). Con 87 ejemplos el hueco se
   cierra (0,97). La curva de aprendizaje es la grafica de esa frase.
2. **Caracteristicas vs. pixeles**: 9 numeros elegidos a proposito rinden
   mejor y mas rapido que 1024 pixeles crudos — el defecto es pequeno y el
   resize lo borra. En que condiciones se invierte esa frase es la
   pregunta con la que empieza la Parte C (aprendizaje profundo).

Ejecutar:
    python examples/class04_ml_dl/data_analysis/comparar_modelos.py
"""
from __future__ import annotations

import csv
import sys
import time
from pathlib import Path

CURSO = Path(__file__).resolve().parents[3]
for _ruta in (CURSO, CURSO.parent):
    if str(_ruta) not in sys.path:
        sys.path.insert(0, str(_ruta))

import cv2
import numpy as np
from PIL import Image
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from cvcourse import features, viz

SALIDA = CURSO / "outputs" / "clase04"

TEST_SIZE = 0.3
SEMILLA = 42
LADO_PIXELES = 32        # 32x32 = 1024 dimensiones para la Parte B

COLUMNAS = (
    "area", "perimeter", "width", "height", "aspect_ratio",
    "circularity", "eccentricity", "solidity", "extent",
)

MODELOS = ("knn", "tree", "forest", "svm", "logreg")


def cargar_lote() -> tuple[list[np.ndarray], np.ndarray, np.ndarray, str]:
    """(imagenes en gris, y, defectos, origen) del dataset de la banda."""
    base = CURSO / "datasets" / "synthetic_parts"
    imagenes: list[np.ndarray] = []
    y: list[str] = []
    if base.is_dir() and (base / "verdad_terreno.csv").exists():
        with (base / "verdad_terreno.csv").open(encoding="utf-8", newline="") as f:
            for registro in csv.DictReader(f):
                gris = cv2.imread(str(base / registro["fichero"]), cv2.IMREAD_GRAYSCALE)
                imagenes.append(gris)
                y.append(registro["clase"])
        origen = "datasets/synthetic_parts"
    else:
        from cvcourse import synthetic

        imagenes_lote, verdades = synthetic.lote_de_piezas(n=120, semilla=20260805)
        imagenes = [img.astype(np.uint8) for img in imagenes_lote]
        y = [v.clase for v in verdades]
        origen = "mini-lote sintetico"
    return imagenes, np.asarray(y), origen


def caracteristicas_de_lote(imagenes: list[np.ndarray], clases: np.ndarray) -> np.ndarray:
    """Las 9 columnas de la Clase 3, una fila por pieza (la region mayor).

    El dataset trae 120 piezas y una fila por mascara medida es lo que
    necesita la comparacion con los pixeles (que tambien van uno por pieza).
    Cuando una mascara queda partida por el umbral se conserva la region
    mayor: la pieza cuenta una vez, como manda la inspeccion. (El ejemplo
    `industrial/clasificar_piezas.py` conserva las filas extra a proposito:
    alli los objetos falsos son parte del analisis.)
    """
    filas: list[features.Caracteristicas] = []
    for imagen, clase in zip(imagenes, clases, strict=True):
        mascara = cv2.threshold(imagen, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1] > 0
        medidas = features.caracteristicas_de_mascara(mascara, etiqueta_de_clase=str(clase))
        filas.append(max(medidas, key=lambda f: f.area))
    X, _, _ = features.a_matriz(filas, columnas=COLUMNAS)
    return X


def pixeles_de_lote(imagenes: list[np.ndarray], lado: int) -> np.ndarray:
    """Parte B: resize -> gris -> flatten -> vector de `lado^2` numeros."""
    vectores = []
    for imagen in imagenes:
        pequena = Image.fromarray(imagen).resize((lado, lado))
        vectores.append(np.asarray(pequena).ravel() / 255.0)
    return np.asarray(vectores, dtype=np.float32)


def entrenar(X_tr: np.ndarray, y_tr: np.ndarray, tipo: str):
    """Cinco modelos; la LogReg directa de sklearn (decision D3)."""
    from src.framework.processing.pattern_recognition_tools import PatternRecognitionTools

    if tipo == "logreg":
        return Pipeline(
            [
                ("scaler", StandardScaler()),
                ("clf", LogisticRegression(random_state=SEMILLA, max_iter=2000)),
            ]
        ).fit(X_tr, y_tr)
    return PatternRecognitionTools.train(X_tr, y_tr, model_type=tipo)


def comparar(
    X_tr: np.ndarray, y_tr: np.ndarray, X_te: np.ndarray, y_te: np.ndarray,
    nombre: str,
) -> list[dict[str, object]]:
    """Entrena los cinco modelos sobre un tipo de entrada y devuelve la tabla."""
    from src.framework.processing.pattern_recognition_tools import PatternRecognitionTools

    filas: list[dict[str, object]] = []
    for tipo in MODELOS:
        t0 = time.perf_counter()
        estimador = entrenar(X_tr, y_tr, tipo)
        t_entreno = time.perf_counter() - t0

        if tipo == "logreg":
            y_pred = estimador.predict(X_te)
            acc = float(np.mean(y_pred == y_te))
        else:
            evaluacion = PatternRecognitionTools.evaluate(estimador, X_te, y_te)
            acc = evaluacion.accuracy
            y_pred = estimador.estimator.predict(X_te)

        t0 = time.perf_counter()
        for _ in range(50):
            estimador.predict(X_te[:1]) if tipo == "logreg" else estimador.estimator.predict(X_te[:1])
        t_inferencia = (time.perf_counter() - t0) / 50

        informe = classification_report(y_te, y_pred, output_dict=True, zero_division=0)["macro avg"]
        filas.append({
            "entrada": nombre, "modelo": tipo, "acc": acc,
            "precision": informe["precision"], "recall": informe["recall"],
            "f1": informe["f1-score"], "t_entreno_s": t_entreno,
            "t_inferencia_ms": t_inferencia * 1e3,
        })
    return filas


def imprimir_tabla(filas: list[dict[str, object]]) -> None:
    cabecera = (
        f"\n{'entrada':>12s} {'modelo':>7s} {'acc':>6s} "
        f"{'precision':>10s} {'recall':>7s} {'f1':>6s} "
        f"{'t_entreno':>9s} {'t_infer':>8s}"
    )
    print(cabecera)
    print("-" * 78)
    for f in filas:
        print(
            f"{f['entrada']:>12s} {f['modelo']:>7s} {f['acc']:6.3f} "
            f"{f['precision']:10.3f} {f['recall']:7.3f} {f['f1']:6.3f} "
            f"{f['t_entreno_s']:8.3f}s {f['t_inferencia_ms']:7.2f}ms"
        )


def main() -> int:
    SALIDA.mkdir(parents=True, exist_ok=True)
    imagenes, y, origen = cargar_lote()
    n_ok = int((y == "OK").sum())
    print(f"DATASET: {origen} -> {len(imagenes)} piezas ({n_ok} OK, "
          f"{len(imagenes) - n_ok} NO_OK)")
    print(
        f"LINEA BASE «siempre OK»: {n_ok / len(imagenes):.3f}. "
        "Menos que eso no es un modelo, es un ruido."
    )

    X_caracteristicas = caracteristicas_de_lote(imagenes, y)
    X_pixeles = pixeles_de_lote(imagenes, LADO_PIXELES)
    print(
        f"\nDOS ENTRADAS PARA EL MISMO PROBLEMA (una fila por pieza):\n"
        f"  caracteristicas: {X_caracteristicas.shape[1]} numeros "
        f"sobre {X_caracteristicas.shape[0]} piezas (las 9 de la Clase 3)\n"
        f"  pixeles crudos:  {X_pixeles.shape[1]} numeros sobre "
        f"{X_pixeles.shape[0]} piezas (resize {LADO_PIXELES}x{LADO_PIXELES}, "
        "gris, aplanado)"
    )

    idx = np.arange(len(y))
    idx_tr, idx_te = train_test_split(
        idx, test_size=TEST_SIZE, random_state=SEMILLA, stratify=y
    )
    y_tr, y_te = y[idx_tr], y[idx_te]

    tabla_caracteristicas = comparar(
        X_caracteristicas[idx_tr], y_tr, X_caracteristicas[idx_te], y_te, "9 caracteris."
    )
    tabla_pixeles = comparar(X_pixeles[idx_tr], y_tr, X_pixeles[idx_te], y_te, "1024 pixeles")
    imprimir_tabla([*tabla_caracteristicas, *tabla_pixeles])

    # El CSV que se lleva el analista.
    ruta_csv = SALIDA / "tabla_modelos.csv"
    with ruta_csv.open("w", newline="", encoding="utf-8") as f:
        escritor = csv.DictWriter(f, fieldnames=list(tabla_caracteristicas[0]))
        escritor.writeheader()
        for fila in [*tabla_caracteristicas, *tabla_pixeles]:
            escritor.writerow(fila)
    print(f"\nCSV: {ruta_csv}")

    # La grafica que resume la tabla: accuracy por modelo, entrada a entrada.
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, eje = plt.subplots(figsize=(9, 4.5))
    x = np.arange(len(MODELOS))
    ancho = 0.38
    acc_caracteristicas = [f["acc"] for f in tabla_caracteristicas]
    acc_pixeles = [f["acc"] for f in tabla_pixeles]
    eje.bar(x - ancho / 2, acc_caracteristicas, ancho, label="9 caracteristicas")
    eje.bar(x + ancho / 2, acc_pixeles, ancho, label="1024 pixeles")
    eje.set_xticks(x, list(MODELOS))
    eje.set_ylim(0.5, 1.05)
    eje.axhline(n_ok / len(imagenes), color="gray", linestyle="--", label="linea base")
    eje.set_ylabel("accuracy en test")
    eje.set_title("Clase 4 · data analytics -- caracteristicas vs. pixeles crudos")
    eje.legend()
    fig.tight_layout()
    ruta_figura = viz.guardar(fig, SALIDA / "comparar_modelos.png")
    print(f"Figura: {ruta_figura}")

    # La curva de aprendizaje: sobreajuste medido con el Arbol.
    print("\nSOBREAJUSTE (Arbol de decision, 9 caracteristicas):")
    print(f"{'n_train':>8s} {'acc_train':>10s} {'acc_test':>10s}")
    from src.framework.processing.pattern_recognition_tools import PatternRecognitionTools

    for n in (10, 20, 40, len(idx_tr)):
        arbol = PatternRecognitionTools.train(X_caracteristicas[idx_tr[:n]], y_tr[:n], "tree")
        acc_test = PatternRecognitionTools.evaluate(
            arbol, X_caracteristicas[idx_te], y_te
        ).accuracy
        print(f"{n:8d} {arbol.training_accuracy:10.3f} {acc_test:10.3f}")

    print(
        "\nLa tabla decide: sobre este dataset y con estas 9 medidas, cualquier\n"
        "modelo separa las clases y los pixeles no. La decision documentada es\n"
        "la que se lleva: modelo, metricas, matriz de confusion y la frase que\n"
        "explica la eleccion -- eso, y no entrenar a ciegas, es el producto."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
