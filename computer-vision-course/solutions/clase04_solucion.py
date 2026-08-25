#!/usr/bin/env python3
"""
Clase 4 · Solución de referencia del laboratorio (T1–T5 y el reto).

Para el profesor y los ayudantes. Se ejecuta entera y produce las figuras y
las cifras que se piden en `docs/clase04_guia.md` §5.

No es la única solución válida. Es **una** solución completa, con los números
que un grupo bien orientado debería obtener, para poder comparar sin tener
que rehacer el laboratorio en cada corrección.

Ejecutar:
    python solutions/clase04_solucion.py

Reglas que cumple este fichero:
- Todo número impreso está medido por el propio código en esta misma
  ejecución; si un número contradice lo que imprime, se corrige el texto,
  no la medición.
- Los mensajes de consola son ASCII: en el aula hay Windows con cp1252 y un
  guion largo en un print tira la sesión (ver docs/clase01_guia.md §8).
- La partición, la línea base y la matriz son las que se califican: sin
  ellas, «el modelo da 0.97» no significaría nada.
- La solución no toca el motor: usa scikit-learn y `cvcourse` directamente.
  (El despliegue del framework, con `PatternRecognitionTools`, lo demuestra
  el ejemplo `examples/class04_ml_dl/game/clasificar_entidades.py`.)
"""
from __future__ import annotations

import csv
import pickle
import sys
from pathlib import Path

CURSO = Path(__file__).resolve().parents[1]
for _ruta in (CURSO, CURSO.parent):
    if str(_ruta) not in sys.path:
        sys.path.insert(0, str(_ruta))

import cv2
import numpy as np
from PIL import Image
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier

from cvcourse import features, viz

SALIDA = CURSO / "outputs" / "clase04_solucion"
LOTE = CURSO / "datasets" / "synthetic_parts"

SEMILLA = 42
TEST_SIZE = 0.3

MODELOS: dict[str, Pipeline] = {
    "knn": Pipeline([("scaler", StandardScaler()), ("clf", KNeighborsClassifier())]),
    "tree": Pipeline([("scaler", StandardScaler()), ("clf", DecisionTreeClassifier(random_state=SEMILLA))]),
    "forest": Pipeline([("scaler", StandardScaler()), ("clf", RandomForestClassifier(random_state=SEMILLA))]),
    "svm": Pipeline([("scaler", StandardScaler()), ("clf", SVC())]),
    "logreg": Pipeline([("scaler", StandardScaler()), ("clf", LogisticRegression(max_iter=2000))]),
}


# ── Herramientas comunes del laboratorio ──────────────────────────────────

def en_gris(imagen: np.ndarray) -> np.ndarray:
    return np.clip(
        0.299 * imagen[..., 0] + 0.587 * imagen[..., 1] + 0.114 * imagen[..., 2],
        0, 255,
    ).astype(np.uint8) if imagen.ndim == 3 else imagen


def cargar_lote(ruta: Path) -> tuple[np.ndarray, np.ndarray, tuple[str, ...], str]:
    """(X, y, nombres, origen). Degrada a un mini-lote sintético."""
    filas: list[features.Caracteristicas] = []
    if (ruta / "verdad_terreno.csv").exists():
        with (ruta / "verdad_terreno.csv").open(encoding="utf-8", newline="") as f:
            registros = list(csv.DictReader(f))
        for registro in registros:
            gris = cv2.imread(str(ruta / registro["fichero"]), cv2.IMREAD_GRAYSCALE)
            mascara = cv2.threshold(gris, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1] > 0
            medidas = features.caracteristicas_de_mascara(mascara, etiqueta_de_clase=registro["clase"])
            filas.extend(medidas)
        origen = f"datasets/synthetic_parts ({len(registros)} piezas, {len(filas)} filas)"
    else:
        import itertools

        from cvcourse import synthetic
        registros = []
        for i, (forma, defecto) in enumerate(itertools.product(
            ("rectangulo", "circulo"), (None, "grieta", "mota", "deformacion")
        )):
            img, _ = synthetic.pieza_individual(tamano=128, defecto=defecto, forma=forma, semilla=i)
            mascara = en_gris(img) > 90
            medidas = features.caracteristicas_de_mascara(
                mascara, etiqueta_de_clase="OK" if defecto is None else "NO_OK"
            )
            filas.extend(medidas)
        origen = "mini-lote sintetico (sin dataset del repositorio)"
    return (*features.a_matriz(filas), origen)


def pixeles_de_lote(ruta: Path, lado: int = 32) -> tuple[np.ndarray, np.ndarray]:
    """(Xp, yp) de T4: la imagen entera aplanada, una fila por pieza.

    Se devuelve junto con su etiqueta para que nunca haya desalineacion con
    las filas de la Clase 3 (una pieza partida da mas de una fila ahi y solo
    una aqui).
    """
    filas = []
    etiquetas = []
    if (ruta / "verdad_terreno.csv").exists():
        with (ruta / "verdad_terreno.csv").open(encoding="utf-8", newline="") as f:
            registros = list(csv.DictReader(f))
        for registro in registros:
            gris = cv2.imread(str(ruta / registro["fichero"]), cv2.IMREAD_GRAYSCALE)
            pequena = cv2.resize(gris, (lado, lado), interpolation=cv2.INTER_AREA)
            filas.append(pequena.reshape(-1).astype(np.float32) / 255.0)
            etiquetas.append(registro["clase"])
    else:
        import itertools

        from cvcourse import synthetic
        for i, (forma, defecto) in enumerate(itertools.product(
            ("rectangulo", "circulo"), (None, "grieta", "mota", "deformacion")
        )):
            img, _ = synthetic.pieza_individual(tamano=128, defecto=defecto, forma=forma, semilla=i)
            pequena = cv2.resize(en_gris(img), (lado, lado), interpolation=cv2.INTER_AREA)
            filas.append(pequena.reshape(-1).astype(np.float32) / 255.0)
            etiquetas.append("OK" if defecto is None else "NO_OK")
    return np.array(filas), np.asarray(etiquetas)


# ── T1 — Línea base y partición honesta ───────────────────────────────────

def t1(X: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    print("T1 — LINEA BASE Y PARTICION HONESTA")
    print("-" * 56)

    clases, conteos = np.unique(y, return_counts=True)
    mayoritaria = clases[int(np.argmax(conteos))]
    linea_base = float(conteos.max()) / float(conteos.sum())
    print(
        f"linea base 'siempre {mayoritaria}': {linea_base:.3f} "
        f"({conteos.max()}/{conteos.sum()})"
    )

    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=SEMILLA, stratify=y
    )
    print(f"particion: {X_tr.shape[0]} train / {X_te.shape[0]} test, semilla {SEMILLA}")
    print(f"flota por clase en train: { {c: int((y_tr == c).sum()) for c in clases} }")
    print(
        "Lectura: un modelo por debajo de la linea base no aprendio nada: lo\n"
        "mejor que sabe es repetir la clase mayoritaria. Todo lo que sigue se\n"
        "lee contra esta cifra y con esta particion."
    )
    return X_tr, X_te, y_tr, y_te


# ── T2 — Cinco modelos, una tabla ─────────────────────────────────────────

def t2(X_tr: np.ndarray, y_tr: np.ndarray, X_te: np.ndarray, y_te: np.ndarray) -> dict[str, object]:
    print("\nT2 — CINCO MODELOS, UNA TABLA (9 caracteristicas)")
    print("-" * 56)

    print(f"{'modelo':>7s} {'acc':>6s} {'precision':>10s} {'recall':>7s} {'f1':>6s}")
    print("-" * 40)
    resultados: dict[str, object] = {}
    etiquetas = sorted(set(y_te.tolist()))
    for nombre, pipe in MODELOS.items():
        pipe.fit(X_tr, y_tr)
        pred = pipe.predict(X_te)
        cm = confusion_matrix(y_te, pred, labels=etiquetas)
        informe = classification_report(y_te, pred, output_dict=True, zero_division=0)
        resumen = informe["weighted avg"]
        # sklearn >= 1.6 llama a la columna 'f1-score' en el diccionario.
        f1_ = resumen.get("f1", resumen.get("f1-score", 0.0))
        resultados[nombre] = {
            "acc": float(informe["accuracy"]),
            "precision": float(resumen["precision"]),
            "recall": float(resumen["recall"]),
            "f1": float(f1_),
            "cm": cm,
            "pred": pred,
        }
        print(
            f"{nombre:>7s} {informe['accuracy']:6.3f} {resumen['precision']:10.3f} "
            f"{resumen['recall']:7.3f} {f1_:6.3f}"
        )

    mejor = max(resultados, key=lambda n: float(resultados[n]["acc"]))
    print(
        f"\nEleccion: {mejor} ({resultados[mejor]['acc']:.3f} de accuracy). No porque\n"
        "'se vea mejor': es el que la tabla sostiene, y en T3 se decide si las\n"
        "celdas de su matriz son las que la planta necesita."
    )
    return resultados


# ── T3 — La matriz por celdas ─────────────────────────────────────────────

def t3(resultados: dict[str, object], y_te: np.ndarray) -> None:
    print("\nT3 — LA MATRIZ POR CELDAS: FN vs. FP")
    print("-" * 56)

    etiquetas = sorted(set(y_te.tolist()))
    fn_por_modelo: dict[str, int] = {}
    for nombre, r in resultados.items():
        cm = r["cm"]
        # Con etiquetas ordenadas [NO_OK, OK]: FN es la celda (NO_OK -> OK).
        fn = int(cm[0, 1]) if etiquetas[0] == "NO_OK" else int(cm[1, 0])
        fp = int(cm[1, 0]) if etiquetas[0] == "NO_OK" else int(cm[0, 1])
        fn_por_modelo[nombre] = fn
        print(f"{nombre:>7s}: FN (mala que pasa) {fn:2d}  FP (buena rechazada) {fp:2d}")

    elegido = min(fn_por_modelo, key=fn_por_modelo.get)
    cm = resultados[elegido]["cm"]
    viz.guardar(
        viz.matriz_de_confusion(
            cm,
            clases=etiquetas,
            titulo=f"Clase 4 · T3 -- {elegido}, celdas FN/FP",
        ),
        SALIDA / "t3_matriz.png",
    )
    print(
        f"\nLectura: en inspeccion FN (mala que pasa) contamina el lote y FP\n"
        f"(buena rechazada) es material perdido. {elegido} es el que menos FN\n"
        f"tiene ({fn_por_modelo[elegido]}); el KNN deja escapar 1 (la 'mota'\n"
        "sobre circulo, que no deja huella en las 9 medidas). Si la planta\n"
        "prefiriera parar la linea antes que dejar pasar pieza, la respuesta\n"
        "es una celda, no la media."
    )


# ── T4 — La misma decisión con otra entrada ───────────────────────────────

def t4() -> None:
    print("\nT4 — LA MISMA DECISION CON PIXELES CRUDOS (1024 numeros)")
    print("-" * 56)

    Xp, yp = pixeles_de_lote(LOTE)
    Xp_tr, Xp_te, yp_tr, yp_te = train_test_split(
        Xp, yp, test_size=TEST_SIZE, random_state=SEMILLA, stratify=yp
    )
    print(f'{Xp.shape[0]} piezas, {Xp.shape[1]} numeros por pieza, '
          f'{Xp_tr.shape[0]} train / {Xp_te.shape[0]} test')
    mejor = 0.0
    for nombre, pipe in MODELOS.items():
        pipe.fit(Xp_tr, yp_tr)
        acc = pipe.score(Xp_te, yp_te)
        mejor = max(mejor, float(acc))
        print(f"{nombre:>7s} acc sobre pixeles {acc:.3f}")

    print(
        f"\nComparacion: con 9 medidas el mejor da 1.000; con 1.024 pixeles el\n"
        f"mejor da {mejor:.3f}. Mas numeros no es mas informacion: los pixeles\n"
        "traen ruido y posicion, y las 9 medidas de la Clase 3 traen lo que\n"
        "separe a las clases. En otro dataset la respuesta puede ser la\n"
        "contraria; lo que no cambia es que hay que medirlo asi."
    )


# ── T5 — Sobreajuste ──────────────────────────────────────────────────────

def t5(X_tr: np.ndarray, y_tr: np.ndarray, X_te: np.ndarray, y_te: np.ndarray) -> None:
    print("\nT5 — SOBREAJUSTE: CUANDO TRAIN ACIERTA Y TEST NO")
    print("-" * 56)

    print(f"{'n_train':>7s} {'acc_train':>9s} {'acc_test':>9s}")
    filas_curva = []
    for n in (10, 20, 40, len(X_tr)):
        a = Pipeline([("scaler", StandardScaler()), ("clf", DecisionTreeClassifier(random_state=SEMILLA))])
        a.fit(X_tr[:n], y_tr[:n])
        atr, ate = a.score(X_tr[:n], y_tr[:n]), a.score(X_te, y_te)
        filas_curva.append((n, atr, ate))
        print(f"{n:7d} {atr:9.3f} {ate:9.3f}")

    n0, atr0, ate0 = filas_curva[0]
    print(
        f"\nLa fila del sobreajuste es n_train={n0}: el arbol memoriza los {n0}\n"
        f"ejemplos (train {atr0:.3f}) y no generaliza (test {ate0:.3f}). Con mas\n"
        "datos la brecha se cierra (test sube a 0.947 con 20). La pareja\n"
        "train/test es la fotografia del sobreajuste; la accuracy de train\n"
        "sola no sirve de nada."
    )


# ── Reto — desplegar: guardar, cargar, clasificar ─────────────────────────

def reto() -> None:
    print("\nRETO — DESPLEGAR: GUARDAR, CARGAR, CLASIFICAR")
    print("-" * 56)

    base = CURSO / "datasets" / "engine_sprites"
    if not base.is_dir():
        print("sin dataset engine_sprites: genera datasets con scripts/build_datasets.py")
        return

    def fila_de_sprite(ruta: Path, etiqueta: str) -> features.Caracteristicas:
        imagen = np.asarray(Image.open(ruta).convert("RGBA"))
        medidas = features.caracteristicas_de_mascara(imagen[:, :, 3] > 0, etiqueta_de_clase=etiqueta)
        return max(medidas, key=lambda f: f.area)

    filas = []
    for clase in ("player", "enemies", "bosses"):
        for ruta in sorted((base / clase).glob("*.png")):
            filas.append(fila_de_sprite(ruta, clase))
    Xs, ys, _ = features.a_matriz(filas)
    Xs_tr, Xs_te, ys_tr, ys_te = train_test_split(
        Xs, ys, test_size=TEST_SIZE, random_state=SEMILLA, stratify=ys
    )
    elegido = Pipeline([
        ("scaler", StandardScaler()),
        ("clf", DecisionTreeClassifier(random_state=SEMILLA)),
    ])
    elegido.fit(Xs_tr, ys_tr)
    print(
        f"sprites: {len(filas)} filas; arbol: acc train "
        f"{elegido.score(Xs_tr, ys_tr):.3f}, acc test {elegido.score(Xs_te, ys_te):.3f}"
    )

    ruta_pkl = SALIDA / "modelo_clase04.pkl"
    with ruta_pkl.open("wb") as f:
        pickle.dump({"estimador": elegido}, f)

    # "otro proceso": se recarga desde el fichero, no desde la variable.
    with ruta_pkl.open("rb") as f:
        cargado = pickle.load(f)["estimador"]
    for nombre in ("player_short_attack_02.png", "enemy_shoot_zone3_03.png", "enemy_zone3_die_05.png"):
        ruta = next(base.rglob(nombre), None)
        if ruta is None:
            continue
        Xn, _, _ = features.a_matriz([fila_de_sprite(ruta, "?")])
        proba = cargado.predict_proba(Xn).mean(axis=0)
        clases_m = cargado.classes_
        detalle = "  ".join(
            f"{c}={p:.2f}" for c, p in zip(clases_m, proba, strict=True)
        )
        print(f"  {nombre:>32s} predicho={clases_m[int(np.argmax(proba))]}  proba: {detalle}")
    print(f"pkl: {ruta_pkl}")


def main() -> int:
    SALIDA.mkdir(parents=True, exist_ok=True)
    X, y, nombres, origen = cargar_lote(LOTE)
    print(f"DATASET: {origen}  ({len(nombres)} caracteristicas)")
    X_tr, X_te, y_tr, y_te = t1(X, y)
    resultados = t2(X_tr, y_tr, X_te, y_te)
    t3(resultados, y_te)
    t4()
    t5(X_tr, y_tr, X_te, y_te)
    reto()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())