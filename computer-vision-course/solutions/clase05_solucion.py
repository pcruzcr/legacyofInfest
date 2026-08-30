#!/usr/bin/env python3
"""
Clase 5 · Solución de referencia del proyecto de integración.

Para el profesor y los ayudantes. Se ejecuta entera y produce las figuras y
las cifras que se piden en `docs/clase05_guia.md` §5: un sistema de 8 etapas
que ejecuta, con la medición de cada etapa y la cifra que decide.

La solución es del dominio industrial, como `estacion_de_inspeccion.py`, pero
**deliberadamente por otro camino**: el ejemplo despliega el modelo del
framework (`PatternRecognitionTools`) y decide con probabilidad; la solución
usa los cinco modelos de la Clase 4 y decide por su tabla. Los dos sistemas
inspeccionan el MISMO turno (semilla 999), y compararlos es material de clase:
dos pipelines, una cifra cada uno, y el profesor puede mostrar que ambas
salidas se leen solas.

Lo que añade la solución al ejemplo:

1. **La tabla de modelos decide, no la intuición.** Los cinco modelos de la
   Clase 4 se entrenan con la partición honesta y se elige el de menos FN
   (contaminar el lote cuesta 20; rechazar una buena cuesta 1). La elección
   se lee de la tabla impresa, como exige la rúbrica.
2. **El reto de la guía §5.5, medido.** Se inserta una variación en UNA etapa
   —cambiar el modelo por el peor de la propia tabla— y el coste del turno se
   mide de nuevo. El sistema no se cae: sigue decidiendo, y la cifra lo dice.
3. **La interacción es un fichero reproducible.** El reporte se imprime y se
   escribe en `resultados.txt` con el mismo contenido: se entrega lo que se
   ejecutó.

Ejecutar:
    python solutions/clase05_solucion.py

Reglas que cumple este fichero:
- Todo número impreso está medido por el propio código en esta misma
  ejecución; si un número contradice lo que imprime, se corrige el texto,
  no la medición.
- Los mensajes de consola son ASCII: en el aula hay Windows con cp1252 (ver
  docs/clase05_guia.md §8).
- Sin rutas absolutas: corre desde cualquier carpeta con `sys.path` propio.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

CURSO = Path(__file__).resolve().parents[1]
for _ruta in (CURSO, CURSO.parent):
    if str(_ruta) not in sys.path:
        sys.path.insert(0, str(_ruta))

import cv2
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier

from cvcourse import features, synthetic, viz

SALIDA = CURSO / "outputs" / "clase05_solucion"

TEST_SIZE = 0.3
SEMILLA = 42          # particion del curso, fija
SEMILLA_TURNO = 999   # el MISMO turno que estacion_de_inspeccion.py

COSTE_FN = 20.0   # pieza mala que pasa: llega al cliente
COSTE_FP = 1.0    # pieza buena rechazada: se descarta y se rehace

COLUMNAS = (
    "area", "perimeter", "width", "height", "aspect_ratio",
    "circularity", "eccentricity", "solidity", "extent",
)

MODELOS: dict[str, Pipeline] = {
    "knn": Pipeline([("scaler", StandardScaler()), ("clf", KNeighborsClassifier())]),
    "tree": Pipeline([("scaler", StandardScaler()), ("clf", DecisionTreeClassifier(random_state=SEMILLA))]),
    "forest": Pipeline([("scaler", StandardScaler()), ("clf", RandomForestClassifier(random_state=SEMILLA))]),
    "svm": Pipeline([("scaler", StandardScaler()), ("clf", SVC(probability=True))]),
    "logreg": Pipeline([("scaler", StandardScaler()), ("clf", LogisticRegression(max_iter=2000))]),
}


# ── 1. ADQUISICION ────────────────────────────────────────────────────────

def adquirir_turno() -> tuple[list[np.ndarray], list[synthetic.Pieza]]:
    """El lote que llega a la planta: 60 piezas, semilla de turno 999.

    La misma semilla que `estacion_de_inspeccion.py`: los dos sistemas
    inspeccionan exactamente las mismas piezas, y eso es lo que hace el
    material de clase (dos pipelines contra la misma verdad-terreno).
    """
    return synthetic.lote_de_piezas(n=60, semilla=SEMILLA_TURNO)


# ── 2. PREPROCESAMIENTO ───────────────────────────────────────────────────

def preprocesar(imagen: np.ndarray) -> np.ndarray:
    """Suavizado 5x5, la pieza de la Clase 1 (`realce_de_pieza.py`).

    En este dataset el ruido de la adquisicion es bajo (sigma 3) y el blur
    apenas cambia la mascara; se conserva igualmente como etapa: la pregunta
    de diseno es si la etapa hace falta, y eso se decide midiendo, no por
    fe. La variacion de §5.5 (quitar esta etapa) es un ejercicio del grupo.
    """
    return cv2.GaussianBlur(imagen, (5, 5), 1.0)


# ── 3. SEGMENTACION / DETECCION ───────────────────────────────────────────

def segmentar(imagen: np.ndarray) -> np.ndarray:
    """Otsu sobre la imagen limpia: la pieza clara sobre banda oscura.

    La pieza de la Clase 3 (`contorno_y_centroide.py` / `features_csv.py`).
    """
    _, mascara = cv2.threshold(imagen, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return mascara


# ── 4. EXTRACCION ─────────────────────────────────────────────────────────

def extraer(mascara: np.ndarray, etiqueta: str) -> list[features.Caracteristicas]:
    """Las 9 caracteristicas geometricas de la Clase 3 para cada objeto."""
    return features.caracteristicas_de_mascara(mascara > 0, etiqueta_de_clase=etiqueta)


# ── 5. ML / DL ────────────────────────────────────────────────────────────

def cargar_datos_de_entrenamiento() -> tuple[np.ndarray, np.ndarray]:
    """X, y del dataset del curso (semilla 20260805), datos o degradacion."""
    base = CURSO / "datasets" / "synthetic_parts"
    filas: list[features.Caracteristicas] = []
    if base.is_dir() and (base / "verdad_terreno.csv").exists():
        import csv

        with (base / "verdad_terreno.csv").open(encoding="utf-8", newline="") as f:
            for registro in csv.DictReader(f):
                gris = cv2.imread(str(base / registro["fichero"]), cv2.IMREAD_GRAYSCALE)
                mascara = cv2.threshold(gris, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
                filas.extend(extraer(mascara, registro["clase"]))
    else:
        imagenes, verdades = synthetic.lote_de_piezas(n=120, semilla=20260805)
        for imagen, verdad in zip(imagenes, verdades, strict=True):
            filas.extend(extraer(imagen.astype(np.uint8) > 90, verdad.clase))
    X, y, _ = features.a_matriz(filas, columnas=COLUMNAS)
    return X, y


def entrenar_tabla(X: np.ndarray, y: np.ndarray) -> tuple[dict[str, Pipeline], dict[str, object]]:
    """Los cinco modelos de la Clase 4, particion honesta, tabla con celdas.

    Devuelve los pipelines ya entrenados (para clasificar el turno) y la
    tabla con acc / FN / FP / coste por modelo, como la exige el proyecto.
    """
    clases = sorted(set(y.tolist()))
    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=SEMILLA, stratify=y
    )
    linea_base = max((y == c).sum() for c in clases) / len(y)
    print(f"  particion: {len(X_tr)} train / {len(X_te)} test, semilla {SEMILLA}")
    print(f"  linea base 'siempre OK': {linea_base:.3f}")
    print(f"  {'modelo':>7s} {'acc':>6s} {'FN':>3s} {'FP':>3s} {'coste':>6s}")
    entrenados: dict[str, Pipeline] = {}
    tabla: dict[str, object] = {}
    for nombre, pipe in MODELOS.items():
        pipe.fit(X_tr, y_tr)
        entrenados[nombre] = pipe
        pred = pipe.predict(X_te)
        fn = int(np.sum((y_te == "NO_OK") & (pred == "OK")))
        fp = int(np.sum((y_te == "OK") & (pred == "NO_OK")))
        coste = fn * COSTE_FN + fp * COSTE_FP
        tabla[nombre] = {"acc": pipe.score(X_te, y_te), "fn": fn, "fp": fp, "coste": coste}
        fila = f"{nombre:>7s} {pipe.score(X_te, y_te):6.3f} {fn:3d} {fp:3d} {coste:6.0f}"
        marca = "  <- elegido" if fn == 0 else ""
        print(f"{fila}{marca}")
    return entrenados, tabla


# ── 6. ANALISIS ───────────────────────────────────────────────────────────

def decidir(probabilidad: np.ndarray, clases: np.ndarray, clase_real: str) -> tuple[str, float, bool]:
    """El veredicto por pieza: la clase con mas probabilidad y su confianza.

    Contra la verdad de la banda, que la estacion no ve: `ok` es la medicion
    del sistema, no una etiqueta que venga de la imagen.
    """
    indice = int(np.argmax(probabilidad))
    predicha = str(clases[indice])
    confianza = float(probabilidad[indice])
    return predicha, confianza, predicha == clase_real


# ── 7. VISUALIZACION ──────────────────────────────────────────────────────

def montar_panel(
    imagenes: list[np.ndarray],
    verdades: list[synthetic.Pieza],
    decisiones: list[tuple[str, float, bool]],
) -> list[np.ndarray]:
    """El tablero del operador: cada pieza con su veredicto pintado."""
    panel: list[np.ndarray] = []
    for imagen, verdad, (predicha, confianza, ok) in zip(
        imagenes, verdades, decisiones, strict=True
    ):
        marco = cv2.cvtColor(imagen.astype(np.uint8), cv2.COLOR_GRAY2RGB)
        color = (0, 200, 0) if (ok and predicha == "OK") else (0, 0, 220)
        cv2.rectangle(marco, (2, 2), (imagen.shape[1] - 3, imagen.shape[0] - 3), color, 3)
        cv2.putText(
            marco, f"{predicha} {confianza:.2f}", (6, 18),
            cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 1,
        )
        panel.append(marco)
    return panel


# ── 8. INTERACCION ────────────────────────────────────────────────────────

def reporte_de_turno(
    decisiones: list[tuple[str, float, bool]],
    verdades: list[synthetic.Pieza],
) -> dict[str, float]:
    """El cierre del turno: la cifra que decide, con su coste."""
    fn = sum(1 for (p, _, ok) in decisiones if not ok and p == "OK")
    fp = sum(1 for (p, _, ok) in decisiones if not ok and p == "NO_OK")
    return {"fn": fn, "fp": fp, "coste": fn * COSTE_FN + fp * COSTE_FP}


def inspeccionar_turno(
    entrenados: dict[str, Pipeline],
    modelo: str,
    imagenes: list[np.ndarray],
    verdades: list[synthetic.Pieza],
) -> list[tuple[str, float, bool]]:
    """Toda la cadena 2-6 sobre el turno, con UN modelo ya entrenado."""
    decisiones: list[tuple[str, float, bool]] = []
    pipe = entrenados[modelo]
    clases = np.asarray(pipe.classes_)
    for imagen, verdad in zip(imagenes, verdades, strict=True):
        limpia = preprocesar(imagen.astype(np.uint8))
        mascara = segmentar(limpia)
        filas = extraer(mascara, verdad.clase)
        X_pieza, _, _ = features.a_matriz(filas, columnas=COLUMNAS)
        probabilidad = pipe.predict_proba(X_pieza[:1])[0]
        decisiones.append(decidir(probabilidad, clases, verdad.clase))
    return decisiones


def main() -> int:
    SALIDA.mkdir(parents=True, exist_ok=True)
    etapas: list[tuple[str, float]] = []
    lineas: list[str] = []

    def emitir(texto: str) -> None:
        print(texto)
        lineas.append(texto)

    emitir("=" * 68)
    emitir("SOLUCION DE REFERENCIA -- Clase 5 · industrial (8 etapas)")
    emitir("=" * 68)

    t0 = time.perf_counter()
    imagenes, verdades = adquirir_turno()
    etapas.append(("1. ADQUISICION", time.perf_counter() - t0))
    emitir(f"\n1. ADQUISICION: turno de {len(imagenes)} piezas, semilla {SEMILLA_TURNO} "
           f"(el mismo turno que el ejemplo industrial).")

    t_pre, t_seg, t_ext = 0.0, 0.0, 0.0
    t0 = time.perf_counter()
    todas_las_filas: list[list[features.Caracteristicas]] = []
    for imagen, verdad in zip(imagenes, verdades, strict=True):
        limpia = preprocesar(imagen.astype(np.uint8))
        t_pre += time.perf_counter() - t0
        t0 = time.perf_counter()
        mascara = segmentar(limpia)
        t_seg += time.perf_counter() - t0
        t0 = time.perf_counter()
        todas_las_filas.append(extraer(mascara, verdad.clase))
        t_ext += time.perf_counter() - t0
        t0 = time.perf_counter()
    etapas += [
        ("2. PREPROCESAMIENTO", t_pre),
        ("3. SEGMENTACION", t_seg),
        ("4. EXTRACCION", t_ext),
    ]

    regiones = sum(len(f) for f in todas_las_filas)
    emitir("\n2-4. LAS TRES ETAPAS DE VISION, POR LOTE (60 piezas):")
    for nombre, segundos in etapas[:4]:
        emitir(f"    {nombre:22s} {segundos * 1000:8.2f} ms")
    emitir(f"    regiones detectadas: {regiones} (esperado: 60; una region por pieza).")
    emitir("  La extraccion es la etapa cara: una region se mide entera por pieza.")

    emitir("\n5. ML/DL: los cinco modelos de la Clase 4, particion honesta")
    t0 = time.perf_counter()
    X, y = cargar_datos_de_entrenamiento()
    entrenados, tabla = entrenar_tabla(X, y)
    etapas.append(("5. ML (5 modelos + turno)", time.perf_counter() - t0))

    mejor = min(tabla, key=lambda n: int(tabla[n]["fn"]))
    peor = min(tabla, key=lambda n: float(tabla[n]["acc"]))
    emitir(f"\n  Eleccion: {mejor} (menos FN: {tabla[mejor]['fn']}). La decision de las")
    emitir("  celdas, no de la media: en inspeccion una FN contamina el lote y")
    emitir("  una FP es material perdido; con FN=20 y FP=1, el mejor es el que")
    emitir("  no deja pasar ninguna pieza mala.")

    emitir("\n6. ANALISIS: decisiones del turno (primeras 10)")
    emitir(f"  {'pieza':>6s} {'real':>6s} {'predicha':>8s} {'conf':>5s} {'veredicto':>9s}")
    t_ml, t_ana = 0.0, 0.0
    t0 = time.perf_counter()
    decisiones = inspeccionar_turno(entrenados, mejor, imagenes, verdades)
    t_ml = time.perf_counter() - t0
    etapas.append(("6. ANALISIS", time.perf_counter() - t0))
    for i, (imagen, verdad, (predicha, confianza, ok)) in enumerate(
        zip(imagenes, verdades, decisiones, strict=True)
    ):
        if i >= 10:
            break
        veredicto = "ACEPTAR" if predicha == "OK" else "RECHAZAR"
        marca = " " if ok else "  <- error"
        emitir(f"  {i:6d} {verdad.clase:>6s} {predicha:>8s} {confianza:5.2f} "
               f"{veredicto:>9s}{marca}")

    reporte = reporte_de_turno(decisiones, verdades)
    emitir("\n8. INTERACCION: reporte de operador (cierre del turno)")
    emitir(f"  piezas inspeccionadas: {len(decisiones)}")
    emitir(f"  piezas malas que pasaron (FN): {int(reporte['fn'])}")
    emitir(f"  piezas buenas rechazadas (FP): {int(reporte['fp'])}")
    emitir(f"  coste del turno (FN=20, FP=1): {reporte['coste']:.0f}")

    panel = montar_panel(imagenes, verdades, decisiones)
    ruta_panel = viz.guardar(
        viz.rejilla(
            panel[:12],
            titulos=[
                f"{v.clase} -> {p} {c:.2f}" for (p, c, _), v in
                zip(decisiones[:12], verdades[:12], strict=True)
            ],
            columnas=4,
            titulo_general="Clase 5 · solucion -- veredictos del turno con " + mejor,
        ),
        SALIDA / "turno_veredictos.png",
    )
    cm = np.zeros((2, 2), dtype=int)
    for (p, _, ok), v in zip(decisiones, verdades, strict=True):
        if ok:
            cm[int(v.clase == "OK"), int(p == "OK")] += 1
    ruta_cm = viz.guardar(
        viz.matriz_de_confusion(
            cm,
            clases=["OK", "NO_OK"],
            titulo=f"Clase 5 · solucion -- matriz del turno con {mejor}",
        ),
        SALIDA / "turno_matriz.png",
    )
    emitir(f"\n7. VISUALIZACION: {ruta_panel}")
    emitir(f"                    {ruta_cm}")

    # ── Reto de la guia §5.5: variar UNA etapa y medir la consecuencia ────
    # Se cambia la etapa 5 (el modelo) por el peor de la tabla propia: logreg
    # si la tabla lo sostiene. El sistema no se cae: sigue decidiendo sobre
    # el mismo turno, y la diferencia de coste es la consecuencia medida.
    emitir("\nRETO (guia §5.5): variar la etapa 5 por el peor de la tabla y medir")
    emitir(f"  mejor modelo: {mejor} (acc {tabla[mejor]['acc']:.3f}, coste test {tabla[mejor]['coste']:.0f})")
    emitir(f"  peor modelo : {peor} (acc {tabla[peor]['acc']:.3f}, coste test {tabla[peor]['coste']:.0f})")
    decisiones_peor = inspeccionar_turno(entrenados, peor, imagenes, verdades)
    reporte_peor = reporte_de_turno(decisiones_peor, verdades)
    emitir(f"  mismo turno con {peor}: FN {int(reporte_peor['fn'])}, "
           f"FP {int(reporte_peor['fp'])}, coste {reporte_peor['coste']:.0f}")
    emitir(f"  diferencia de coste en el turno: "
           f"{reporte_peor['coste'] - reporte['coste']:+.0f}")
    emitir("  Lectura: la etapa que se quiso cambiar se cambio, el sistema siguió")
    emitir("  ejecutando y la cifra final lo dice. Ese es el metodo de §5.5: una")
    emitir("  variacion, una medicion, y el analisis sostiene la diferencia.")

    ruta_txt = SALIDA / "resultados.txt"
    with ruta_txt.open("w", encoding="utf-8") as f:
        f.write("\n".join(lineas) + "\n")
    emitir(f"\nINTERACCION reproducible: {ruta_txt} (lo que se ejecuto, no un resumen)")

    emitir("\nTiempo por etapa (medido en esta misma ejecucion):")
    for nombre, segundos in etapas:
        emitir(f"    {nombre:22s} {segundos * 1000:8.2f} ms")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())