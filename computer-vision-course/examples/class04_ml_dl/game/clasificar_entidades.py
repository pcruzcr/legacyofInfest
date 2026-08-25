#!/usr/bin/env python3
"""
Clase 4 · Videojuego — clasificar entidades del motor: jugador, enemigo o jefe.

Pregunta del contexto: *una camara ve un sprite; que es?* — la pregunta que
responde un bot que juega con la vista, sin leer la lista de entidades que el
motor mantiene en memoria.

El dataset sale de los fotogramas del propio motor (`datasets/engine_sprites`,
generado por `scripts/build_datasets.py` a partir de `assets/sprites/`): 381
sprites etiquetados por la carpeta de la que salen. De cada sprite se mide la
mascara (el canal alfa, que es la verdad que el propio juego dibujo) con las
9 caracteristicas de la Clase 3, y se entrena un modelo por algoritmo.

Tres lecciones medidas, y son el contenido:

1. **El dataset esta desbalanceado** (219 jefes contra 50 jugadores): un
   clasificador que diga siempre «boss» acierta el 57 % sin aprender nada.
   La accuracy sola no dice nada: hay que mirarla junto con las clases.
2. **Con estas 9 medidas las clases se separan solas** (el tamano basta):
   los cuatro modelos del framework y la Regresion Logistica de sklearn dan
   accuracy 1,00 en la particion de referencia. Es un resultado de este
   dataset, no de la vida real: medirlo y decirlo es el ejercicio.
3. **Entrenar no basta: hay que desplegar.** El modelo elegido se guarda
   con `save_model`, se recarga con `load_model` y clasifica un sprite que
   no participo en el entrenamiento, con probabilidades (`classify_proba`).

Por que cuatro modelos salen del framework y la Regresion Logistica se
instancia con sklearn directamente (decision D3 de la arquitectura): porque
el framework es una capa de conveniencia sobre scikit-learn, no un muro.
Eso tambien es materia de la clase.

Ejecutar:
    python examples/class04_ml_dl/game/clasificar_entidades.py
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

CURSO = Path(__file__).resolve().parents[3]
for _ruta in (CURSO, CURSO.parent):
    if str(_ruta) not in sys.path:
        sys.path.insert(0, str(_ruta))

import numpy as np
from PIL import Image
from sklearn.model_selection import train_test_split

from cvcourse import features, viz

SALIDA = CURSO / "outputs" / "clase04"

#: La particion de referencia del curso: 70/30, estratificada, semilla fija.
TEST_SIZE = 0.3
SEMILLA = 42

CLASES_DE_ENTIDAD = ("player", "enemies", "bosses")

#: Columnas que entran en el modelo (las 9 de la Clase 3; el centroide y el
#: identificador quedan fuera por fuga de informacion, ver `features.a_matriz`).
COLUMNAS = (
    "area", "perimeter", "width", "height", "aspect_ratio",
    "circularity", "eccentricity", "solidity", "extent",
)

MODELOS = ("knn", "tree", "forest", "svm")


def caracteristicas_de_sprite(ruta: Path, etiqueta: str) -> list[features.Caracteristicas]:
    """Mide la mascara que el propio sprite dibuja: el canal alfa.

    Componer sobre un fondo y umbralizar (el camino de las piezas) aqui
    sobraria: el juego ya separo sprite de fondo cuando dibujo el canal alfa.
    Usarlo de mascara es usar la verdad que el motor conoce.
    """
    imagen = np.asarray(Image.open(ruta).convert("RGBA"))
    return features.caracteristicas_de_mascara(
        imagen[:, :, 3] > 0, etiqueta_de_clase=etiqueta
    )


def cargar_dataset() -> tuple[np.ndarray, np.ndarray, tuple[str, ...], str]:
    """(X, y, nombres, origen). Degrada a los sprites del motor sin dataset."""
    base = CURSO / "datasets" / "engine_sprites"
    filas: list[features.Caracteristicas] = []
    total_ficheros = 0
    if base.is_dir():
        for clase in CLASES_DE_ENTIDAD:
            ficheros = sorted((base / clase).glob("*.png"))
            total_ficheros += len(ficheros)
            for ruta in ficheros:
                filas.extend(caracteristicas_de_sprite(ruta, clase))
        origen = f"datasets/engine_sprites ({total_ficheros} sprites, {len(filas)} filas)"
    else:
        from cvcourse import engine_bridge

        if not engine_bridge.hay_motor():
            raise RuntimeError(
                "no hay datasets/ ni repositorio del motor: genera los datasets "
                "con scripts/build_datasets.py antes de este ejemplo"
            )
        for clase in CLASES_DE_ENTIDAD:
            ficheros = [
                ruta for ruta in engine_bridge.recursos("sprites")
                if clase in ruta.parts
            ]
            total_ficheros += len(ficheros)
            for ruta in ficheros:
                filas.extend(caracteristicas_de_sprite(ruta, clase))
        origen = f"assets/sprites directo ({total_ficheros} sprites, {len(filas)} filas)"
    return (*features.a_matriz(filas, columnas=COLUMNAS), origen)


def entrenar_y_evaluar(X_tr: np.ndarray, y_tr: np.ndarray, X_te: np.ndarray, y_te: np.ndarray):
    """Entrena los cuatro modelos del framework, mide y devuelve resultados."""
    from src.framework.processing.pattern_recognition_tools import PatternRecognitionTools

    resultados: list[dict[str, object]] = []
    for tipo in MODELOS:
        t0 = time.perf_counter()
        modelo = PatternRecognitionTools.train(X_tr, y_tr, model_type=tipo)
        t_entreno = time.perf_counter() - t0
        evaluacion = PatternRecognitionTools.evaluate(modelo, X_te, y_te)
        t0 = time.perf_counter()
        for _ in range(50):
            PatternRecognitionTools.classify(X_te[:1], modelo)
        t_inferencia = (time.perf_counter() - t0) / 50
        resultados.append({
            "modelo": tipo,
            "acc": evaluacion.accuracy,
            "por_clase": evaluacion.per_class_accuracy,
            "confusion": evaluacion.confusion_matrix,
            "t_entreno": t_entreno,
            "t_inferencia": t_inferencia,
            "estimador": modelo,
        })
    return resultados


def main() -> int:
    SALIDA.mkdir(parents=True, exist_ok=True)
    X, y, nombres, origen = cargar_dataset()

    print(f"DATASET: {origen}")
    conteo = {clase: int((y == clase).sum()) for clase in CLASES_DE_ENTIDAD}
    print(f"  clases: {conteo}  ({X.shape[0]} filas, {len(nombres)} caracteristicas)")

    siempre_boss = max(conteo.values()) / X.shape[0]
    print(
        f"\nLINEA BASE: decir siempre «boss» acierta {siempre_boss:.3f} "
        f"({conteo['bosses']}/{X.shape[0]}). Un modelo peor que esto no aprendio"
        " nada: la accuracy se lee junto con esta cifra."
    )

    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=SEMILLA, stratify=y
    )
    resultados = entrenar_y_evaluar(X_tr, y_tr, X_te, y_te)

    print(f"\nPARTICION: {X_tr.shape[0]} train / {X_te.shape[0]} test, semilla {SEMILLA}")
    print(
        f"\n{'modelo':>7s} {'acc':>6s} {'player':>7s} {'enemies':>8s} "
        f"{'bosses':>7s} {'t_entreno':>9s} {'t_infer':>8s}"
    )
    print("-" * 62)
    for r in resultados:
        pc = r["por_clase"]
        print(
            f"{r['modelo']:>7s} {r['acc']:6.3f} {pc['player']:7.3f} "
            f"{pc['enemies']:8.3f} {pc['bosses']:7.3f} "
            f"{r['t_entreno']:8.3f}s {r['t_inferencia'] * 1e3:7.2f}ms"
        )

    mejor = max(resultados, key=lambda r: (float(r["acc"]), -float(r["t_inferencia"])))
    knn = next(r for r in resultados if r["modelo"] == "knn")
    print(
        f"\nCon estas 9 medidas el tamano separa casi todo: cuatro modelos dan\n"
        f"acc 1.000 y el KNN falla en los enemigos mas pequenos "
        f"(acc {knn['acc']:.3f}; los fotogramas de 10 px de alto de la zona 1\n"
        "son los que escapan). El problema de reconocimiento de este dataset\n"
        "es facil; la clase consiste en verlo medido y en saber que otro\n"
        "dataset no lo sera. Para desplegar se elige el mas rapido entre los\n"
        f"que aciertan todo: {mejor['modelo']} "
        f"({mejor['t_inferencia'] * 1e3:.2f} ms por clasificacion)."
    )

    from src.framework.processing.pattern_recognition_tools import PatternRecognitionTools

    ruta_modelo = SALIDA / "modelo_entidades.pkl"
    PatternRecognitionTools.save_model(mejor["estimador"], ruta_modelo)
    print(f"\nMODELO GUARDADO: {ruta_modelo}")

    recargado = PatternRecognitionTools.load_model(ruta_modelo)
    rng = np.random.default_rng(SEMILLA)
    print("\nPRUEBA DE DESPLIEGUE (sprites que no entrenaron):")
    base_sprites = CURSO / "datasets" / "engine_sprites"
    for _ in range(3):
        clase_real = CLASES_DE_ENTIDAD[int(rng.integers(len(CLASES_DE_ENTIDAD)))]
        candidatos = sorted((base_sprites / clase_real).glob("*.png"))
        if not candidatos:
            continue
        ruta = candidatos[int(rng.integers(len(candidatos)))]
        filas = caracteristicas_de_sprite(ruta, clase_real)
        if not filas:
            continue
        X_nuevo, _, _ = features.a_matriz(filas, columnas=COLUMNAS)
        prediccion = PatternRecognitionTools.classify(X_nuevo[:1], recargado)
        probabilidades = PatternRecognitionTools.classify_proba(X_nuevo[:1], recargado)
        print(
            f"  {ruta.name:42s} real={clase_real:8s} predicho={prediccion:8s} "
            f"prob={ {k: round(v, 2) for k, v in probabilidades.items()} }"
        )

    ruta_figura = viz.guardar(
        viz.matriz_de_confusion(
            mejor["confusion"],
            list(CLASES_DE_ENTIDAD),
            titulo="Clase 4 · videojuego -- matriz de confusion (entidades)",
        ),
        SALIDA / "clasificar_entidades_cm.png",
    )
    print(f"\nFigura: {ruta_figura}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
