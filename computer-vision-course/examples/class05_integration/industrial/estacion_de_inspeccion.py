#!/usr/bin/env python3
"""
Clase 5 · Industrial — estacion de inspeccion: de la banda a la decision.

El sistema de referencia del dominio industrial. Recorre la cadena completa
del bloque encadenando las piezas de las clases 1 a 4, sin contenido nuevo:

    ADQUISICION -> PREPROCESAMIENTO -> SEGMENTACION/DETECCION -> EXTRACCION
                 -> ML/DL -> ANALISIS -> VISUALIZACION -> INTERACCION

La pregunta que decide el sistema: *¿esta pieza pasa o no pasa?* — y la cifra
que lo decide es el coste del turno: las piezas malas que pasaron (FN) contra
las buenas que se rechazaron (FP), acumuladas en un reporte de operador.

Tres decisiones de integracion, cada una con su por que:

1. **El lote que llega no es el lote que entreno.** El modelo se entrena con
   la semilla 20260805 (el dataset del curso, particion honesta con semilla
   fija) y la estacion inspecciona un lote NUEVO con otra semilla: es la
   condicion del despliegue, y la unica forma de que la cifra final mida algo.
2. **La decision es por pieza y con probabilidad.** La etapa de analisis
   convierte las predicciones en ACCEPT/REJECT usando la probabilidad del
   modelo, no su etiqueta seca: el operador ve el veredicto y su confianza.
3. **El coste del turno se acumula.** El sistema no imprime una matriz: la
   suma los FN y FP como dinero (pieza mala que pasa = 20, buena rechazada =
   1) y ese numero cierra el reporte. Sin esa cifra, la estacion no decide
   nada: solo clasifica.

Ejecutar:
    python examples/class05_integration/industrial/estacion_de_inspeccion.py
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

CURSO = Path(__file__).resolve().parents[3]
for _ruta in (CURSO, CURSO.parent):
    if str(_ruta) not in sys.path:
        sys.path.insert(0, str(_ruta))

import cv2
import numpy as np

from cvcourse import features, synthetic, viz

SALIDA = CURSO / "outputs" / "clase05"

TEST_SIZE = 0.3
SEMILLA = 42          # particion del curso, fija
SEMILLA_TURNO = 999   # el lote que llega a la planta: nunca el de entrenamiento

COLUMNAS = (
    "area", "perimeter", "width", "height", "aspect_ratio",
    "circularity", "eccentricity", "solidity", "extent",
)

COSTE_FN = 20.0   # pieza mala que pasa: llega al cliente
COSTE_FP = 1.0    # pieza buena rechazada: se descarta y se rehace


# ── 1. ADQUISICION ────────────────────────────────────────────────────────

def adquirir_turno() -> tuple[list[np.ndarray], list[synthetic.Pieza]]:
    """El lote que llega a la planta: 60 piezas, semilla de turno."""
    return synthetic.lote_de_piezas(n=60, semilla=SEMILLA_TURNO)


# ── 2. PREPROCESAMIENTO ───────────────────────────────────────────────────

def preprocesar(imagen: np.ndarray) -> np.ndarray:
    """Suavizado 5x5: la Clase 2 demostro que la grieta se pierde si no se
    suaviza antes de derivar; aqui prepara la segmentacion."""
    return cv2.GaussianBlur(imagen, (5, 5), 1.0)


# ── 3. SEGMENTACION / DETECCION ───────────────────────────────────────────

def segmentar(imagen: np.ndarray) -> np.ndarray:
    """Otsu sobre la imagen limpia: la pieza clara sobre banda oscura."""
    _, mascara = cv2.threshold(imagen, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return mascara


# ── 4. EXTRACCION ─────────────────────────────────────────────────────────

def extraer(mascara: np.ndarray, etiqueta: str) -> list[features.Caracteristicas]:
    """Las 9 caracteristicas geometricas de la Clase 3 para cada objeto."""
    return features.caracteristicas_de_mascara(mascara > 0, etiqueta_de_clase=etiqueta)


# ── 5. ML / DL ────────────────────────────────────────────────────────────

def cargar_lote_de_entrenamiento() -> tuple[np.ndarray, np.ndarray]:
    """X, y del dataset del curso (semilla 20260805), desde datasets/ o en
    degradacion desde el generador. Mismo camino que las Clases 3 y 4."""
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


def entrenar_modelo(X: np.ndarray, y: np.ndarray):
    """KNN del curso, particion honesta, con la linea base al lado."""
    from sklearn.model_selection import train_test_split
    from src.framework.processing.pattern_recognition_tools import PatternRecognitionTools

    linea_base = max((y == c).sum() for c in set(y.tolist())) / len(y)
    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=SEMILLA, stratify=y
    )
    modelo = PatternRecognitionTools.train(X_tr, y_tr, model_type="knn")
    evaluacion = PatternRecognitionTools.evaluate(modelo, X_te, y_te)
    print(f"  linea base «siempre OK»: {linea_base:.3f}")
    print(
        f"  KNN: acc en test {evaluacion.accuracy:.3f} "
        f"(datos que no entrenaron: {X_te.shape[0]} piezas)"
    )
    return modelo


# ── 6. ANALISIS ───────────────────────────────────────────────────────────

def decidir(
    probabilidad: dict[str, float], clase_real: str
) -> tuple[str, float, bool]:
    """El veredicto por pieza: la clase con mas probabilidad, y la confianza
    con que se toma. Contra la verdad de la banda (que la estacion no ve)."""
    predicha = max(probabilidad, key=probabilidad.get)  # type: ignore[arg-type]
    confianza = max(probabilidad.values())
    ok = predicha == clase_real
    return predicha, confianza, ok


# ── 7. VISUALIZACION ──────────────────────────────────────────────────────

def montar_panel(
    imagenes: list[np.ndarray],
    verdades: list[synthetic.Pieza],
    decisiones: list[tuple[str, float, bool]],
) -> np.ndarray:
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
    coste = fn * COSTE_FN + fp * COSTE_FP
    return {"fn": fn, "fp": fp, "coste": coste}


def main() -> int:
    SALIDA.mkdir(parents=True, exist_ok=True)
    etapas: list[tuple[str, float]] = []

    print("=" * 68)
    print("ESTACION DE INSPECCION -- Clase 5 · industrial")
    print("=" * 68)

    t0 = time.perf_counter()
    imagenes, verdades = adquirir_turno()
    etapas.append(("1. ADQUISICION", time.perf_counter() - t0))
    print(f"\n1. ADQUISICION: llegan {len(imagenes)} piezas (semilla {SEMILLA_TURNO}), "
          f"generadas con verdad-terreno.")

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

    print("\n2-4. LAS TRES ETAPAS DE VISION, POR LOTE (60 piezas):")
    for nombre, segundos in etapas[:4]:
        print(f"    {nombre:22s} {segundos * 1000:8.2f} ms")
    print(
        "  La extraccion es la etapa cara (una region se mide por pieza);\n"
        "  el dato sirve para saber donde se gasta el turno antes de tocar nada."
    )

    print("\n5. MODELO: se entrena una sola vez con el dataset del curso")
    X, y = cargar_lote_de_entrenamiento()
    modelo = entrenar_modelo(X, y)

    from src.framework.processing.pattern_recognition_tools import PatternRecognitionTools

    decisiones: list[tuple[str, float, bool]] = []
    t_ml, t_ana = 0.0, 0.0
    t0 = time.perf_counter()
    for filas, verdad in zip(todas_las_filas, verdades, strict=True):
        X_pieza, _, _ = features.a_matriz(filas, columnas=COLUMNAS)
        probabilidad = PatternRecognitionTools.classify_proba(X_pieza[:1], modelo)
        t_ml += time.perf_counter() - t0
        t0 = time.perf_counter()
        decisiones.append(decidir(probabilidad, verdad.clase))
        t_ana += time.perf_counter() - t0
        t0 = time.perf_counter()
    etapas += [("5. ML (60 inferencias)", t_ml), ("6. ANALISIS", t_ana)]

    print("\n6. DECISIONES DEL TURNO (primeras 10):")
    print(f"  {'pieza':>6s} {'real':>6s} {'predicha':>8s} {'conf':>5s} {'veredicto':>9s}")
    for i, (imagen, verdad, (predicha, confianza, ok)) in enumerate(
        zip(imagenes, verdades, decisiones, strict=True)
    ):
        if i >= 10:
            break
        veredicto = "ACEPTAR" if predicha == "OK" else "RECHAZAR"
        marca = " " if ok else " <- error"
        print(
            f"  {i:6d} {verdad.clase:>6s} {predicha:>8s} {confianza:5.2f} "
            f"{veredicto:>9s}{marca}"
        )

    reporte = reporte_de_turno(decisiones, verdades)
    print("\n8. REPORTE DE OPERADOR (cierre del turno):")
    print(f"  piezas inspeccionadas: {len(decisiones)}")
    print(f"  piezas malas que pasaron (FN): {int(reporte['fn'])}")
    print(f"  piezas buenas rechazadas (FP): {int(reporte['fp'])}")
    print(
        f"  coste del turno (FN={COSTE_FN:.0f}, FP={COSTE_FP:.0f}): "
        f"{reporte['coste']:.0f}"
    )
    print(
        "  La cifra que decide: el coste. Un turno barato es un turno que"
        " inspecciono bien."
    )

    panel = montar_panel(imagenes, verdades, decisiones)
    ruta = viz.guardar(
        viz.rejilla(
            panel[:12],
            titulos=[
                f"{v.clase} -> {p} {c:.2f}" for (p, c, _), v in
                zip(decisiones[:12], verdades[:12], strict=True)
            ],
            columnas=4,
            titulo_general="Clase 5 · industrial -- estacion de inspeccion: veredictos del turno",
        ),
        SALIDA / "estacion_de_inspeccion.png",
    )
    print(f"\n7. VISUALIZACION: {ruta}")
    print("\nTiempo por etapa (medido en esta misma ejecucion):")
    for nombre, segundos in etapas:
        print(f"    {nombre:24s} {segundos * 1000:8.2f} ms")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
