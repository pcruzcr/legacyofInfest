"""
Module: entrenar_vigia
System: stage (student assignment)
Academic Unit: Unidad IX — Reconocimiento de patrones.

Tuberia de entrenamiento del clasificador del Vigia, de punta a punta:
dataset -> caracteristicas -> entrenamiento -> evaluacion -> modelo .pkl.

Usa las APIs del motor, no implementaciones propias:
  - `tools.build_dataset.build_dataset()` del profesor para el .npz
  - `VisionTools.extract_features()` (dentro de la anterior) para las HOG
  - `PatternRecognitionTools.train()/evaluate()/save_model()` para el modelo

Por que se llama a `build_dataset()` desde aqui y no por linea de comandos
=========================================================================
`tools/build_dataset.py` carga las imagenes con `.convert()`, que en SDL exige
una pantalla abierta, y su `main()` nunca llama a `pygame.display.set_mode()`.
Ejecutado tal cual aborta con "No convert format has been set". Su funcion
`build_dataset()` en cambio esta bien: basta abrir la pantalla antes. Se
importa y se llama desde aqui en vez de tocar un fichero que no es mio.

Uso:
    python src/stages/stage3_3_el_patio/entrenar_vigia.py
"""
from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[3]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

import numpy as np  # noqa: E402
import pygame  # noqa: E402

AQUI = Path(__file__).resolve().parent
DATASET = AQUI / "dataset"
NPZ = DATASET / "patio_vigia.npz"
MODELO = AQUI / "models" / "vigia.pkl"

SEMILLA = 3
PROPORCION_PRUEBA = 0.30
CANDIDATOS = ("knn", "tree", "forest", "svm")


def separar(X: np.ndarray, y: np.ndarray):
    """Divide en entrenamiento/prueba manteniendo la proporcion por clase.

    Estratificado a mano y con semilla fija: con 2 clases desbalanceadas (48
    aereas frente a 87 terrestres) una division al azar puede dejar una clase
    casi fuera de la prueba, y entonces la precision no significa nada.
    """
    rng = np.random.default_rng(SEMILLA)
    idx_tr: list[int] = []
    idx_te: list[int] = []
    for clase in sorted(set(y.tolist())):
        idx = np.flatnonzero(y == clase)
        rng.shuffle(idx)
        corte = int(round(len(idx) * PROPORCION_PRUEBA))
        idx_te.extend(idx[:corte].tolist())
        idx_tr.extend(idx[corte:].tolist())
    return (X[idx_tr], y[idx_tr], X[idx_te], y[idx_te])


def main() -> int:
    pygame.init()
    pygame.display.set_mode((1, 1))  # ver el docstring de arriba

    from src.framework.processing.pattern_recognition_tools import PatternRecognitionTools
    from tools.build_dataset import build_dataset

    print("== 1. Dataset ==")
    build_dataset(DATASET, NPZ, method="hog")
    datos = np.load(NPZ, allow_pickle=True)
    X, y = datos["X"].astype(np.float32), datos["y"]
    print(f"   X={X.shape} ({X.dtype})   clases={sorted(set(y.tolist()))}")
    for clase in sorted(set(y.tolist())):
        print(f"   {clase:10s} {(y == clase).sum()} muestras")

    Xtr, ytr, Xte, yte = separar(X, y)
    print(f"\n== 2. Division ==\n   entrenamiento={len(ytr)}  prueba={len(yte)}")

    print("\n== 3. Comparacion de clasificadores ==")
    resultados = []
    for tipo in CANDIDATOS:
        try:
            modelo = PatternRecognitionTools.train(
                Xtr, ytr, tipo, feature_method="hog",
                **({"n_estimators": 40} if tipo == "forest" else {}))
            ev = PatternRecognitionTools.evaluate(modelo, Xte, yte)
        except Exception as exc:  # un clasificador que no cuadre no tumba la tanda
            print(f"   {tipo:8s} fallo: {exc}")
            continue
        resultados.append((ev.accuracy, tipo, modelo, ev))
        print(f"   {tipo:8s} entrenamiento={modelo.training_accuracy:.3f}  "
              f"prueba={ev.accuracy:.3f}")

    if not resultados:
        print("Ningun clasificador entreno.")
        return 1

    resultados.sort(key=lambda r: r[0], reverse=True)
    mejor_acc, mejor_tipo, mejor_modelo, mejor_ev = resultados[0]

    print(f"\n== 4. Ganador: {mejor_tipo} ==")
    print(f"   precision de prueba: {mejor_acc:.4f}  "
          f"({'CUMPLE' if mejor_acc >= 0.70 else 'NO LLEGA'} el minimo de 0,70)")
    print("   precision por clase:")
    for clase, acc in mejor_ev.per_class_accuracy.items():
        print(f"     {clase:10s} {acc:.3f}")
    print("\n   matriz de confusion (filas=real, columnas=predicho):")
    clases = mejor_modelo.classes
    print("              " + "".join(f"{c:>12s}" for c in clases))
    for i, c in enumerate(clases):
        fila = "".join(f"{v:>12d}" for v in mejor_ev.confusion_matrix[i])
        print(f"   {c:>10s} {fila}")
    print("\n   informe:")
    for linea in mejor_ev.report.splitlines():
        print("     " + linea)

    MODELO.parent.mkdir(parents=True, exist_ok=True)
    PatternRecognitionTools.save_model(mejor_modelo, MODELO)
    print(f"\n== 5. Modelo guardado ==\n   {MODELO.relative_to(RAIZ)}  "
          f"({MODELO.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
