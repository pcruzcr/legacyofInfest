#!/usr/bin/env python3
"""
Clase 5 · Mecatronica — percepcion pick-and-place: de la camara a la orden.

El sistema de referencia del dominio mecatronica. Recorre la cadena completa
del bloque encadenando las piezas de las clases 1 a 4, sin contenido nuevo:

    ADQUISICION -> PREPROCESAMIENTO -> SEGMENTACION/DETECCION -> EXTRACCION
                 -> ML/DL -> ANALISIS -> VISUALIZACION -> INTERACCION

La pregunta que decide el sistema: *¿que pieza agarro, en que orden, y en
que coordenadas?* — y la respuesta es una lista de ORDENES DE AGARRE en
milimetros, no una tabla de etiquetas.

Tres decisiones de integracion, cada una con su por que:

1. **El pipeline no clasifica para informar: clasifica para agarrar.** La
   salida de la etapa ML/DL es la clase y su probabilidad, pero la INTERACCION
   las convierte en la secuencia fisica del robot: agarrar primero la pieza
   defectuosa (retirarla de la celda) y dejar las buenas para el ensamble. La
   probabilidad decide: con confianza baja el robot no agarra, pide otra toma.
2. **La localizacion es una calibracion, no una etiqueta.** El centroide del
   componente (la Clase 3) se convierte a milimetros con el factor px/mm de la
   escena, porque el brazo recibe milimetros, no pixeles. La escena compone
   piezas del dataset sintetico (la Clase 3) cuya posicion se conoce por
   construccion, y contra esa verdad se mide el error de localizacion.
3. **El orden de agarre es una politica, y se dice.** Con dos piezas malas, el
   robot NO agarra en orden de aparicion: retira primero la que esta mas cerca
   de la salida de la celda (primera en salir del campo de vision). Esa
   eleccion se declara porque es la parte del sistema que el cliente
   discute, no la arquitectura interna.

Ejecutar:
    python examples/class05_integration/mechatronics/percepcion_pick_and_place.py
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
SEMILLA = 42            # particion del curso, fija
SEMILLA_CELDA = 3456    # las piezas que hay HOY en la celda: otras semillas

COLUMNAS = (
    "area", "perimeter", "width", "height", "aspect_ratio",
    "circularity", "eccentricity", "solidity", "extent",
)

#: Piezas que se colocan en la celda: (clase, defecto o ""). Las piezas NO_OK
#: son las que el robot debe retirar; las OK son el ensamble que sigue.
PIEZAS_EN_CELDA = (
    ("OK", ""),
    ("NO_OK", "grieta"),
    ("OK", ""),
    ("NO_OK", "mota"),
    ("OK", ""),
)

mm_por_px: float = 0.0   # se llena en la calibracion (etapa 3)
FONDO_CELDA = 60         # la mesa de la celda, oscura
TAMANO_PIEZA = 128
CONFIANZA_MINIMA = 0.80  # debajo: el robot no agarra, pide otra toma


# ── 0. MODELO (pieza reutilizada de la Clase 4, entrenada una sola vez) ─────

def entrenar_modelo() -> tuple[np.ndarray, np.ndarray]:
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
                filas.extend(
                    features.caracteristicas_de_mascara(
                        mascara > 0, etiqueta_de_clase=registro["clase"]
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


# ── 1. ADQUISICION ────────────────────────────────────────────────────────

def adquirir_celda() -> tuple[np.ndarray, list[tuple[float, float, str]]]:
    """Compone la escena de la celda con piezas del generador y devuelve la
    verdad: (centro_x, centro_y, clase) por pieza. Como en la Clase 4, las
    piezas se colocan con semillas que no participaron en el entrenamiento."""
    ancho = len(PIEZAS_EN_CELDA) * TAMANO_PIEZA + (len(PIEZAS_EN_CELDA) + 1) * 24
    lienzo = np.full((TAMANO_PIEZA + 48, ancho), FONDO_CELDA, dtype=np.uint8)
    verdad: list[tuple[float, float, str]] = []
    x = 24
    for i, (clase, defecto) in enumerate(PIEZAS_EN_CELDA):
        pieza, _ = synthetic.pieza_individual(
            tamano=TAMANO_PIEZA, clase=clase, defecto=defecto or None,
            ruido=4.0, semilla=8000 + i,
        )
        lienzo[24:24 + TAMANO_PIEZA, x:x + TAMANO_PIEZA] = pieza
        verdad.append((x + TAMANO_PIEZA / 2.0, 24 + TAMANO_PIEZA / 2.0, clase))
        x += TAMANO_PIEZA + 24
    return lienzo, verdad


# ── 2. PREPROCESAMIENTO ───────────────────────────────────────────────────

def preprocesar(escena: np.ndarray) -> np.ndarray:
    """Suavizado 5x5 antes de umbralizar: la Clase 2 demostro que el ruido de
    la banda se limpia y no se fragmenta la pieza."""
    return cv2.GaussianBlur(escena, (5, 5), 1.0)


# ── 3. SEGMENTACION / DETECCION + CALIBRACION ─────────────────────────────

def detectar(limpia: np.ndarray) -> tuple[list[tuple[int, int, int, int, int]], float]:
    """Otsu + cierre morfologico + componentes conexas. Devuelve las regiones
    ordenadas por izquierda (la cinta avanza de izquierda a derecha: la pieza
    que sale primero es la de x menor) y el factor px -> mm, de la pieza mas
    ancha.

    El cierre 3x3 es la decision de integracion que este fotograma exige: la
    grieta de la pieza defectuosa cruza la pieza entera y el umbral la
    convierte en un hueco, asi que sin morfologia Otsu entrega DOS componentes
    por una pieza (6 detectadas donde hay 5). El defecto esta DENTRO de la
    pieza: no separa piezas, y el cierre lo devuelve al interior de la
    silueta antes de contar. Es la misma fractura por umbral que la Clase 3
    demostro: la segmentacion lista para contar no sale del umbral, sale de
    umbral + la morfologia que el problema exige."""
    _, mascara = cv2.threshold(limpia, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    mascara = cv2.morphologyEx(mascara, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    n, _, stats, _ = cv2.connectedComponentsWithStats(mascara, 8)
    regiones = [
        (int(stats[i, cv2.CC_STAT_AREA]), int(stats[i, cv2.CC_STAT_LEFT]),
         int(stats[i, cv2.CC_STAT_TOP]), int(stats[i, cv2.CC_STAT_WIDTH]),
         int(stats[i, cv2.CC_STAT_HEIGHT]))
        for i in range(1, n)
        if stats[i, cv2.CC_STAT_AREA] > 1000
    ]
    regiones.sort(key=lambda r: r[1])

    # La esfera de calibracion del curso: la pieza mas ancha de la escena mide
    # 60 mm en el plano real (el generador la dibuja a 0,82*tamano: 105 px).
    # De ahi sale el factor que convierte el centroide en una orden.
    ancho_px = max(r[3] for r in regiones)
    return regiones, 60.0 / ancho_px


# ── 4. EXTRACCION ─────────────────────────────────────────────────────────

def extraer(escena: np.ndarray, region) -> features.Caracteristicas:
    """Las 9 caracteristicas de la Clase 3 sobre la mascara de la pieza.

    El contrato entre etapas: la extraccion mide la silueta que la
    SEGMENTACION decidio (Otsu), no un recorte re-umbralizado con otro
    criterio: dos umbrales distintos cambian las caracteristicas y el
    clasificador ve piezas que no son las del entrenamiento."""
    _area, izq, arr, w, h = region
    recorte = escena[arr:arr + h, izq:izq + w]
    filas = features.caracteristicas_de_mascara(recorte > FONDO_CELDA + 20, area_minima=50)
    return max(filas, key=lambda f: f.area)


# ── 5. ML / DL ────────────────────────────────────────────────────────────

def clasificar(modelo, fila: features.Caracteristicas) -> tuple[str, float]:
    """Clase y probabilidad del modelo de la Clase 4."""
    from src.framework.processing.pattern_recognition_tools import PatternRecognitionTools

    X, _, _ = features.a_matriz([fila], columnas=COLUMNAS)
    prediccion = PatternRecognitionTools.classify(X[:1], modelo)
    probabilidad = PatternRecognitionTools.classify_proba(X[:1], modelo)
    return prediccion, max(probabilidad.values())


# ── 6. ANALISIS + 8. INTERACCION ──────────────────────────────────────────

def plan_de_agarre(
    escena: np.ndarray,
    regiones: list[tuple[int, int, int, int, int]],
    modelo,
) -> tuple[list[dict[str, object]], np.ndarray]:
    """La politica del robot: por cada pieza, clase y posicion en mm; y la
    secuencia final — retirar las NO_OK en el orden en que salen de la celda,
    con la confianza como condicion de agarre."""
    anotada = cv2.cvtColor(escena, cv2.COLOR_GRAY2RGB)
    piezas: list[dict[str, object]] = []
    for area, izq, arr, w, h in regiones:
        clase, confianza = clasificar(modelo, extraer(escena, (area, izq, arr, w, h)))
        cx, cy = izq + w / 2.0, arr + h / 2.0
        piezas.append({
            "clase": clase, "confianza": confianza,
            "x_mm": cx * mm_por_px, "y_mm": cy * mm_por_px,
            "izq": izq, "arr": arr, "w": w, "h": h,
        })
        color = (0, 220, 0) if clase == "OK" else (0, 40, 220)
        cv2.rectangle(anotada, (izq, arr), (izq + w, arr + h), color, 2)
        cv2.putText(
            anotada, f"{clase} {confianza:.2f}", (izq, arr - 6),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2,
        )

    retirar = sorted(
        (p for p in piezas if p["clase"] == "NO_OK" and p["confianza"] >= CONFIANZA_MINIMA),
        key=lambda p: p["x_mm"],   # politica: la primera en salir, primero
    )
    return retirar, anotada


def main() -> int:
    global mm_por_px
    SALIDA.mkdir(parents=True, exist_ok=True)
    etapas: list[tuple[str, float]] = []

    print("=" * 68)
    print("PERCEPCION PICK-AND-PLACE -- Clase 5 · mecatronica")
    print("=" * 68)

    t0 = time.perf_counter()
    escena, verdad = adquirir_celda()
    etapas.append(("1. ADQUISICION", time.perf_counter() - t0))
    print(f"\n1. ADQUISICION: celda con {len(verdad)} piezas "
          f"(semilla {SEMILLA_CELDA}); la posicion real se conoce por construccion")

    t0 = time.perf_counter()
    limpia = preprocesar(escena)
    etapas.append(("2. PREPROCESAMIENTO", time.perf_counter() - t0))

    t0 = time.perf_counter()
    regiones, mm_por_px = detectar(limpia)
    etapas.append(("3. SEGMENTACION", time.perf_counter() - t0))
    print(f"\n3. SEGMENTACION: {len(regiones)} piezas detectadas "
          f"({len(verdad)} colocadas)")
    print(f"   CALIBRACION: {mm_por_px:.4f} mm/px (los milimetros de la orden "
          "salen de aqui)")

    t0 = time.perf_counter()
    filas = [extraer(limpia, r) for r in regiones]
    etapas.append(("4. EXTRACCION", time.perf_counter() - t0))
    print(f"\n4. EXTRACCION: {len(filas)} filas x {len(COLUMNAS)} "
          "caracteristicas (las 9 de la Clase 3)")

    print("\n5. ML: modelo de la Clase 4, entrenado con el dataset del curso")
    X, y = entrenar_modelo()
    from sklearn.model_selection import train_test_split
    from src.framework.processing.pattern_recognition_tools import PatternRecognitionTools

    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=SEMILLA, stratify=y
    )
    modelo = PatternRecognitionTools.train(X_tr, y_tr, model_type="knn")
    evaluacion = PatternRecognitionTools.evaluate(modelo, X_te, y_te)
    print(f"   KNN: acc en test {evaluacion.accuracy:.3f} "
          f"(datos que no entrenaron: {X_te.shape[0]} piezas)")

    retirar, anotada = plan_de_agarre(escena, regiones, modelo)

    print("\n6+8. ORDENES DE AGARRE (la interaccion del sistema):")
    if not retirar:
        print("   ninguna pieza defectuosa con confianza suficiente: la celda"
              " solo tiene ensamble")
    for i, orden in enumerate(retirar):
        cv2.circle(anotada, (int(orden["x_mm"] / mm_por_px), int(orden["y_mm"] / mm_por_px)),
                   6, (0, 165, 255), 2)
        cv2.putText(
            anotada, f"#{i + 1}", (int(orden["x_mm"] / mm_por_px) + 8,
                                   int(orden["y_mm"] / mm_por_px)),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 165, 255), 2,
        )
        print(
            f"   orden #{i + 1}: agarrar NO_OK en ({orden['x_mm']:6.1f}, "
            f"{orden['y_mm']:6.1f}) mm, confianza {orden['confianza']:.2f}"
        )
    print("   La politica: retirar las defectuosas en orden de salida de la"
          " celda (x creciente)")

    errores: list[float] = []
    for region in regiones:
        _area, izq, arr, w, h = region
        cx, cy = (izq + w / 2.0) * mm_por_px, (arr + h / 2.0) * mm_por_px
        verdad_cercana = min(verdad, key=lambda v: np.hypot(cx - v[0] * mm_por_px, cy - v[1] * mm_por_px))
        errores.append(np.hypot(cx - verdad_cercana[0] * mm_por_px, cy - verdad_cercana[1] * mm_por_px))
    print(f"\nMETROLOGIA: error de localizacion medio {np.mean(errores):.2f} mm, "
          f"maximo {np.max(errores):.2f} mm (contra la verdad del generador)")

    ruta = viz.guardar(
        viz.comparar(
            escena,
            anotada,
            titulo_antes="celda del robot (5 piezas, dos defectuosas)",
            titulo_despues="clasificadas y ordenes de agarre en milimetros",
            titulo_general="Clase 5 · mecatronica -- percepcion pick-and-place",
        ),
        SALIDA / "percepcion_pick_and_place.png",
    )
    print(f"\n7. VISUALIZACION: {ruta}")
    print("\nTiempo por etapa (medido en esta misma ejecucion):")
    for nombre, segundos in etapas:
        print(f"    {nombre:24s} {segundos * 1000:8.2f} ms")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())