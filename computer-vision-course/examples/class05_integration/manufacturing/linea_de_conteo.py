#!/usr/bin/env python3
"""
Clase 5 · Manufactura — linea de conteo: el watershed dentro del sistema.

El sistema de referencia del dominio manufactura. Recorre la cadena completa
del bloque encadenando las piezas de las clases 1 a 4, sin contenido nuevo:

    ADQUISICION -> PREPROCESAMIENTO -> SEGMENTACION/DETECCION -> EXTRACCION
                 -> ML/DL -> ANALISIS -> VISUALIZACION -> INTERACCION

La pregunta que decide el sistema: *¿cuantas piezas pasaron por la linea y
cuantas de ellas hay que expulsar?* — y la cifra que lo decide es el conteo:
piezas contadas contra piezas que existieron, sin que el solape las robe.

Tres decisiones de integracion, cada una con su por que:

1. **El watershed de la Clase 3 es la etapa de segmentacion, no una
   curiosidad.** En la banda, cinco piezas circulares salen PEGADAS (solape
   asegurado por el generador), y el umbral —fijo u Otsu— entrega una sola
   mancha de 20.000 px donde hay 5. La transformada de distancia y los
   marcadores seguros (el 65 % del maximo, la fraccion de la Clase 3) separan
   la mancha; una sexta pieza separada no lo necesita y pasa por componentes
   conexas. La pieza de la Clase 3 se inserta donde le toca: solo en el
   fotograma que la necesita.
2. **La extraccion mide la mascara de la SEGMENTACION, no el fotograma.** La
   region se filtra por su id (los bboxes de piezas pegadas se solapan, y un
   recorte `> 0` mezclaria los pixeles del vecino: la pieza mediria mas area
   de la que tiene). La salida de una etapa es la entrada de la siguiente.
3. **Si la segmentacion cambia, el modelo se reajusta; eso se mide y se
   reporta.** El modelo de la Clase 4 se entreno con piezas INDIVIDUALES en su
   propio cuadro. El watershed entrega las piezas MORDIDAS por la linea de
   contacto (la silueta pierde un segmento donde toco a la vecina): el KNN de
   la Clase 4 clasifica esas siluetas como NO_OK — 5 de 5 bien clasificadas
   por el ojo humano y 5 de 5 rechazadas por el modelo. La respuesta no es
   «el modelo es malo»: es el contrato entre etapas, que manda reajustar el
   modelo con ejemplos del MISMO pipeline. Se reentrena el mismo KNN con
   bandas de contacto separadas por este mismo watershed y con las NO_OK del
   dataset del curso; el acierto sobre la banda salta de 1/6 a 6/6. La Clase 4
   termino con una decision documentada; la Clase 5 empieza con una etapa
   nueva que invalida esa decision, y reajustarla es el trabajo.

Ejecutar:
    python examples/class05_integration/manufacturing/linea_de_conteo.py
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
SEMILLA_BANDA = 777     # la banda que pasa HOY: otra semilla
SEMILLA_ENTRENO = 1000  # bandas de REENTRENO: ni la del turno ni las del curso

COLUMNAS = (
    "area", "perimeter", "width", "height", "aspect_ratio",
    "circularity", "eccentricity", "solidity", "extent",
)

FRACCION_MARCADORES = 0.65   # la fraccion de la Clase 3 (valle del eje medio)
AREA_MINIMA = 500            # una pieza de banda es mucho mas grande
GRIS_PIEZA = 185             # el metal claro del generador


# ── 1. ADQUISICION ────────────────────────────────────────────────────────

def adquirir_banda(semilla: int = SEMILLA_BANDA) -> tuple[np.ndarray, list[tuple[float, float, str]]]:
    """La banda con 5 piezas circulares en contacto (la escena de la Clase 3)
    y una sexta pieza defectuosa separada, que no necesita watershed.
    Devuelve la escena y la verdad: (fila, columna, clase) por pieza.

    El tamano de la banda es 389 y no 256 (el de la Clase 3) a proposito:
    con 256 las piezas miden radio 27 px, y el modelo de la Clase 4 se
    entreno con piezas de radio 41 px — fuera de esa distribucion, el KNN
    clasifica el circulo bueno como defectuoso aunque la segmentacion y la
    clasificacion sean correctas. La escena se compone dentro de lo que el
    curso midio. La foranea tambien: 128 px, el tamano del dataset del curso."""
    imagen, circulos = synthetic.piezas_en_contacto(
        n=5, tamano=389, ruido=3.0, semilla=semilla
    )
    escena = np.full((389, 590), 70, dtype=np.uint8)
    escena[:, :389] = imagen
    defectuosa, _ = synthetic.pieza_individual(
        tamano=128, clase="NO_OK", defecto="grieta", ruido=4.0, semilla=9001
    )
    escena[130:258, 413:541] = defectuosa

    verdad = [(c.centro[0], c.centro[1], "OK") for c in circulos]
    verdad.append((194.0, 477.0, "NO_OK"))
    return escena, verdad


# ── 2. PREPROCESAMIENTO ───────────────────────────────────────────────────

def preprocesar(escena: np.ndarray) -> np.ndarray:
    """Suavizado 5x5: la Clase 2 demostro que la grieta se pierde si no se
    suaviza antes de umbralizar; aqui limpia el ruido de la banda."""
    return cv2.GaussianBlur(escena, (5, 5), 1.0)


# ── 3. SEGMENTACION / DETECCION ───────────────────────────────────────────

def segmentar(limpia: np.ndarray) -> tuple[np.ndarray, list[tuple[int, int, int, int, int, int]], int]:
    """Otsu + watershed donde hace falta. Devuelve la mascara de regiones
    (id por pieza), las regiones (id, area, izq, arr, ancho, alto) y cuantas
    salieron del watershed.

    El watershed se aplica SOLO a la mancha que el umbral no supo separar (la
    de las 5 piezas pegadas, la componente mas grande). La sexta pieza,
    separada, se cuenta con componentes conexas directas. El sistema no hace
    watershed «porque es lo moderno»: lo hace en el fotograma que lo exige.

    El cierre 3x3 antes de contar es la misma decision de integracion del
    ejemplo de mecatronica: la grieta de la pieza foranea cruza la pieza
    entera y el umbral la convierte en un hueco, asi que sin morfologia Otsu
    entrega DOS componentes por una pieza (7 detectadas donde hay 6). El
    defecto esta DENTRO de la pieza: no separa piezas."""
    _, umbral = cv2.threshold(limpia, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    umbral = cv2.morphologyEx(umbral, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    n, _, stats, _ = cv2.connectedComponentsWithStats(umbral, 8)
    componentes = [
        (int(stats[i, cv2.CC_STAT_AREA]), int(stats[i, cv2.CC_STAT_LEFT]),
         int(stats[i, cv2.CC_STAT_TOP]), int(stats[i, cv2.CC_STAT_WIDTH]),
         int(stats[i, cv2.CC_STAT_HEIGHT]))
        for i in range(1, n)
        if stats[i, cv2.CC_STAT_AREA] >= AREA_MINIMA
    ]
    componentes.sort(key=lambda r: -r[0])
    mancha = componentes[0]        # la cadena de piezas pegadas, la mas grande
    separadas = componentes[1:]    # la pieza foranea, ya separada

    # Watershed (el metodo de la Clase 3) sobre la mancha pegada.
    _area, izq, arr, w, h = mancha
    recorte = limpia[arr:arr + h, izq:izq + w]
    _, b2 = cv2.threshold(recorte, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    dist = cv2.distanceTransform(b2, cv2.DIST_L2, 5)
    _, seguros = cv2.threshold(
        dist, FRACCION_MARCADORES * float(dist.max()), 255, cv2.THRESH_BINARY
    )
    seguros = seguros.astype(np.uint8)
    n_seguros, marcas = cv2.connectedComponents(seguros, 8)
    desconocido = cv2.subtract(cv2.dilate(b2, np.ones((3, 3), np.uint8), iterations=3), seguros)
    marcas = marcas + 1
    marcas[desconocido == 255] = 0
    marcas = cv2.watershed(cv2.cvtColor(recorte, cv2.COLOR_GRAY2BGR), marcas)

    # Mascara global: watershed en la mancha, umbral fuera de ella.
    mascara = np.zeros(limpia.shape, dtype=np.int32)
    regiones: list[tuple[int, int, int, int, int, int]] = []
    for m in range(2, n_seguros + 1):
        ys, xs = np.nonzero(marcas == m)
        if len(ys) == 0:
            continue
        mascara[arr + ys, izq + xs] = m
        regiones.append((
            m, int(len(ys)),
            int(izq + xs.min()), int(arr + ys.min()),
            int(xs.max() - xs.min() + 1), int(ys.max() - ys.min() + 1),
        ))
    for r in separadas:
        _area, x0, y0, w0, h0 = r
        mascara[y0:y0 + h0, x0:x0 + w0][mascara[y0:y0 + h0, x0:x0 + w0] == 0] = n_seguros + 1
        regiones.append((n_seguros + 1, _area, x0, y0, w0, h0))
    regiones.sort(key=lambda r: r[2])
    return mascara, regiones, n_seguros - 1


# ── 4. EXTRACCION ─────────────────────────────────────────────────────────

def extraer(mascara: np.ndarray, region) -> features.Caracteristicas:
    """Las 9 caracteristicas de la Clase 3 sobre la mascara de la pieza.

    La extraccion mide lo que la SEGMENTACION decidio: los pixeles que el
    watershed (o el umbral) le asignaron a la pieza, y SOLO esos. Con piezas
    pegadas los bboxes se solapan, y un recorte `> 0` mezclaria los pixeles
    del vecino: la pieza mediria mas area de la que tiene y la circularidad
    de una mancha doble. Por eso la region se filtra por su id. Ese es el
    contrato entre etapas: la extraccion consume la salida de la segmentacion,
    no un recorte del fotograma."""
    region_id, _area, izq, arr, w, h = region
    recorte = mascara[arr:arr + h, izq:izq + w]
    filas = features.caracteristicas_de_mascara(recorte == region_id, area_minima=50)
    return max(filas, key=lambda f: f.area)


# ── 5. ML / DL ────────────────────────────────────────────────────────────

def lote_del_curso() -> tuple[np.ndarray, np.ndarray]:
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


def reajuste(x_del_curso: np.ndarray, y_del_curso: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """El modelo de la Clase 4 mas ejemplos del MISMO pipeline: bandas de
    contacto separadas por este mismo watershed.

    Es el reajuste que el contrato entre etapas manda cuando una etapa
    cambia: el watershed entrega piezas mordidas por la linea de contacto, y
    el clasificador tiene que haber visto esa forma. Se anade una fila por
    region separada por el watershed de aqui (etiqueta OK) a las NO_OK del
    curso; las OK del curso no se mezclan: su silueta individual no existe en
    esta banda."""
    filas_ok: list[features.Caracteristicas] = []
    for semilla in range(8):
        escena, _ = adquirir_banda(semilla=SEMILLA_ENTRENO + semilla)
        mascara, regiones, _ = segmentar(preprocesar(escena))
        for region in regiones[:-1]:       # las 5 de la cadena, no la foranea
            filas_ok.append(extraer(mascara, region))
    X_ok, _y_ok, _ = features.a_matriz(filas_ok, columnas=COLUMNAS)
    y_ok = np.full(X_ok.shape[0], "OK")
    return np.vstack([X_ok, x_del_curso[y_del_curso == "NO_OK"]]), np.concatenate(
        [y_ok, y_del_curso[y_del_curso == "NO_OK"]]
    )


def entrenar(X: np.ndarray, y: np.ndarray, nombre: str):
    """KNN del curso con su particion honesta; devuelve el modelo y el acc."""
    from sklearn.model_selection import train_test_split
    from src.framework.processing.pattern_recognition_tools import PatternRecognitionTools

    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=SEMILLA, stratify=y
    )
    modelo = PatternRecognitionTools.train(X_tr, y_tr, model_type="knn")
    evaluacion = PatternRecognitionTools.evaluate(modelo, X_te, y_te)
    print(f"   {nombre}: KNN acc test {evaluacion.accuracy:.3f} "
          f"({X.shape[0]} filas, {X_te.shape[0]} en test)")
    return modelo


def clasificar(modelo, fila: features.Caracteristicas) -> tuple[str, float]:
    from src.framework.processing.pattern_recognition_tools import PatternRecognitionTools

    X, _, _ = features.a_matriz([fila], columnas=COLUMNAS)
    prediccion = PatternRecognitionTools.classify(X[:1], modelo)
    probabilidad = PatternRecognitionTools.classify_proba(X[:1], modelo)
    return prediccion, max(probabilidad.values())


# ── 8. INTERACCION ────────────────────────────────────────────────────────

def orden_de_expulsion(
    anotada: np.ndarray, regiones, decisiones: list[tuple[str, float]]
) -> tuple[list[tuple[float, float, float]], int]:
    """Las piezas NO_OK se expulsan en el orden en que pasan por el expulsor
    (izquierda a derecha). Devuelve las posiciones y cuantas salieron."""
    ordenes: list[tuple[float, float, float]] = []
    for region, (clase, confianza) in zip(regiones, decisiones, strict=True):
        _id, _area, izq, arr, w, h = region
        if clase != "NO_OK":
            continue
        cv2.rectangle(anotada, (izq, arr), (izq + w, arr + h), (0, 0, 220), 2)
        cv2.putText(
            anotada, "EXPULSAR", (izq, arr + h + 14),
            cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 220), 1,
        )
        ordenes.append((izq + w / 2.0, arr + h / 2.0, confianza))
    return ordenes, len(ordenes)


def main() -> int:
    SALIDA.mkdir(parents=True, exist_ok=True)
    etapas: list[tuple[str, float]] = []

    print("=" * 68)
    print("LINEA DE CONTEO -- Clase 5 · manufactura")
    print("=" * 68)

    t0 = time.perf_counter()
    escena, verdad = adquirir_banda()
    etapas.append(("1. ADQUISICION", time.perf_counter() - t0))
    print(f"\n1. ADQUISICION: banda con {len(verdad)} piezas "
          f"(5 pegadas en cadena + 1 foranea con grieta)")

    t0 = time.perf_counter()
    limpia = preprocesar(escena)
    etapas.append(("2. PREPROCESAMIENTO", time.perf_counter() - t0))

    t0 = time.perf_counter()
    mascara, regiones, n_watershed = segmentar(limpia)
    etapas.append(("3. SEGMENTACION", time.perf_counter() - t0))
    print(
        f"\n3. SEGMENTACION: {len(regiones)} piezas ({n_watershed} por "
        f"watershed sobre la mancha pegada, {len(regiones) - n_watershed} "
        f"por umbral) -- {len(verdad)} esperadas"
    )

    t0 = time.perf_counter()
    filas = [extraer(mascara, r) for r in regiones]
    etapas.append(("4. EXTRACCION", time.perf_counter() - t0))
    print(f"\n4. EXTRACCION: {len(filas)} filas x {len(COLUMNAS)} "
          "caracteristicas (las 9 de la Clase 3)")

    print("\n5. ML: primero el modelo DE LA CLASE 4, luego el reajustado")
    x_curso, y_curso = lote_del_curso()
    modelo_clase4 = entrenar(x_curso, y_curso, "modelo de la Clase 4")
    decision_clase4 = [clasificar(modelo_clase4, fila) for fila in filas]
    aciertos4 = sum(
        1 for (clase, _c), r, v in zip(decision_clase4, regiones, verdad)
        if clase == v[2]
    )
    print(
        f"   -> sobre la banda: {aciertos4}/{len(verdad)} bien. El watershed "
        f"entrega siluetas\n      mordidas por la linea de contacto, y el KNN "
        f"las ve como NO_OK: la etapa\n      cambio y el modelo no se "
        f"reajusto. Contrato entre etapas, y su coste medido."
    )

    x_reajuste, y_reajuste = reajuste(x_curso, y_curso)
    modelo = entrenar(x_reajuste, y_reajuste, "modelo reajustado")
    print("   El reajuste anade bandas de ENTRENAMIENTO separadas por este "
          "mismo watershed:")

    decisiones: list[tuple[str, float]] = []
    t0 = time.perf_counter()
    for fila in filas:
        decisiones.append(clasificar(modelo, fila))
    etapas.append(("5. ML (inferencias)", time.perf_counter() - t0))

    print("\n6. ANALISIS (pieza por pieza, contra la verdad de la banda):")
    aciertos = 0
    for region, (clase, confianza) in zip(regiones, decisiones, strict=True):
        _id, _area, izq, arr, w, h = region
        cx, cy = izq + w / 2.0, arr + h / 2.0
        real = min(verdad, key=lambda v: np.hypot(cx - v[1], cy - v[0]))
        ok = clase == real[2]
        aciertos += ok
        print(
            f"    pieza en ({cx:6.1f},{cy:6.1f}) predicha={clase:>5s} "
            f"conf={confianza:.2f} real={real[2]:>5s} "
            f"{'bien' if ok else 'FALLO'}"
        )
    print(f"    con el modelo reajustado: {aciertos}/{len(verdad)} bien, "
          f"contra {aciertos4}/{len(verdad)} del de la Clase 4")

    anotada = cv2.cvtColor(escena, cv2.COLOR_GRAY2RGB)
    for region, (clase, confianza) in zip(regiones, decisiones, strict=True):
        _id, _area, izq, arr, w, h = region
        color = (0, 220, 0) if clase == "OK" else (0, 0, 220)
        cv2.rectangle(anotada, (izq, arr), (izq + w, arr + h), color, 2)
        cv2.putText(
            anotada, f"{clase} {confianza:.2f}", (izq, arr - 6),
            cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1,
        )
    ordenes, n_expulsar = orden_de_expulsion(anotada, regiones, decisiones)

    print("\n8. INTERACCION: el expulsor y el reporte de turno")
    print(f"    {n_expulsar} pieza(s) expulsada(s) en el orden de paso:")
    for i, (ex, ey, confianza) in enumerate(ordenes):
        print(f"      #{i + 1}: expulsar en ({ex:.1f}, {ey:.1f}) px, "
              f"confianza {confianza:.2f}")
    print(
        f"    conteo: {len(regiones)} contadas / {len(verdad)} reales, "
        f"clasificacion {aciertos}/{len(verdad)} bien"
    )
    print("    La cifra que decide: el conteo, y la etiqueta de cada pieza.")
    print("    La leccion: la segmentacion cambio; el modelo se reajusto;")
    print("    ambas cosas se midieron antes de desplegar.")

    ruta = viz.guardar(
        viz.comparar(
            escena,
            anotada,
            titulo_antes="banda: 5 piezas pegadas + 1 foranea con grieta",
            titulo_despues="separadas, clasificadas y orden de expulsion",
            titulo_general="Clase 5 · manufactura -- linea de conteo con watershed",
        ),
        SALIDA / "linea_de_conteo.png",
    )
    print(f"\n7. VISUALIZACION: {ruta}")
    print("\nTiempo por etapa (medido en esta misma ejecucion):")
    for nombre, segundos in etapas:
        print(f"    {nombre:24s} {segundos * 1000:8.2f} ms")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())