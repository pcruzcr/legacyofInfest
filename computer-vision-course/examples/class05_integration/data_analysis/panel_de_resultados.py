#!/usr/bin/env python3
"""
Clase 5 · Data analytics — panel de resultados: del CSV a la decision.

El sistema de referencia del dominio analisis de datos. Recorre la cadena
completa del bloque encadenando las piezas de las clases 1 a 4, sin contenido
nuevo — pero la ADQUISICION no es una camara: es un fichero. El panel
«adquiere» el CSV que midio la Clase 3 (`outputs/clase03/features.csv`, o el
lote desde el generador si no existe), lo valida, lo resume, compara cinco
modelos y cierra con el reporte escrito: las cifras que deciden.

    ADQUISICION -> PREPROCESAMIENTO -> SEGMENTACION/DETECCION -> EXTRACCION
                 -> ML/DL -> ANALISIS -> VISUALIZACION -> INTERACCION

La pregunta que decide el sistema: *¿que modelo se despliega esta semana, y
con que numeros?* — la interaccion es un informe, no un actuador.

Tres decisiones de integracion, cada una con su por que:

1. **Los datos no se regeneran: se adquieren.** El CSV de la Clase 3 es un
   artefacto medido (puede tener filas partidas por el umbral: la Clase 3 lo
   aviso). El panel lo lee tal cual esta, lo valida y reporta lo que encuentre;
   solo si el fichero no existe se degrada a medir el lote con el mismo
   metodo. Un panellista no decide que datos existen: decide que hacer con
   los que hay.
2. **La segmentacion del analisis es separar por clase y detectar objetos
   falsos.** El panel agrupa las filas por su etiqueta (OK / NO_OK) y aparta
   las filas extremas que la clase 3 aviso (piezas que se partieron son
   objetos que no existen). Medir con filtro o sin el es una decision con
   consecuencia: el filtro sube el accuracy de TODO modelo y eso hay que
   decirlo, no ocultarlo.
3. **La interaccion es el reporte escrito con la cifra correcta.** El panel
   no entrena «el mejor modelo»: entrena los cinco, los compara contra la
   linea base y el coste de cada error (FN = pieza mala que pasa, FP = buena
   descartada), y escribe la recomendacion. La cifra que decide no es la
   maxima accuracy: es la accuracy menos la linea base (cuanto aporta el
   modelo de verdad) y el coste del turno que ese modelo deja pasar.

Ejecutar:
    python examples/class05_integration/data_analysis/panel_de_resultados.py
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

from cvcourse import features, synthetic, viz

SALIDA = CURSO / "outputs" / "clase05"

TEST_SIZE = 0.3
SEMILLA = 42                      # particion honesta del curso, fija
CSV_DE_LA_CLASE_3 = CURSO / "outputs" / "clase03" / "features.csv"
LOTE_SINTETICO = (CURSO / "datasets" / "synthetic_parts" / "verdad_terreno.csv").exists()

COLUMNAS = features.COLUMNAS[:9]  # las 9 geometricas: ids, centroides y etiqueta no entran

MODELOS = ("knn", "tree", "forest", "svm", "logreg")

COSTE_FN = 20.0   # pieza mala que pasa: llega al cliente (la Clase 5 industrial)
COSTE_FP = 1.0    # pieza buena rechazada: se descarta y se rehace


# ── 1. ADQUISICION ────────────────────────────────────────────────────────

def adquirir_datos() -> tuple[list[dict[str, str]], str]:
    """El CSV de la Clase 3 si existe; si no, el lote medido con el mismo
    metodo. Devuelve los registros y el origen, para que el reporte diga
    de donde salio cada numero."""
    if CSV_DE_LA_CLASE_3.exists():
        with CSV_DE_LA_CLASE_3.open(encoding="utf-8", newline="") as f:
            return list(csv.DictReader(f)), f"CSV de la Clase 3 ({CSV_DE_LA_CLASE_3.name})"
    if LOTE_SINTETICO:
        base = CURSO / "datasets" / "synthetic_parts"
        with (base / "verdad_terreno.csv").open(encoding="utf-8", newline="") as f:
            registros = list(csv.DictReader(f))
        medidos: list[dict[str, str]] = []
        for registro in registros:
            gris = cv2.imread(str(base / registro["fichero"]), cv2.IMREAD_GRAYSCALE)
            mascara = cv2.threshold(gris, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1] > 0
            for medida in features.caracteristicas_de_mascara(
                mascara, etiqueta_de_clase=registro["clase"]
            ):
                medidos.append({c: str(getattr(medida, c)) for c in COLUMNAS} | {"label": medida.label})
        return medidos, "lote de datasets/synthetic_parts medido ahora"
    imagenes, verdades = synthetic.lote_de_piezas(n=120, semilla=20260805)
    registros = []
    for imagen, verdad in zip(imagenes, verdades, strict=True):
        filas = features.caracteristicas_de_mascara(
            imagen.astype(np.uint8) > 90, etiqueta_de_clase=verdad.clase
        )
        for f in filas:
            registros.append({**{c: getattr(f, c) for c in COLUMNAS}, "label": f.label})
    return registros, "mini-lote sintetico"


# ── 2. PREPROCESAMIENTO ───────────────────────────────────────────────────

def validar(registros: list[dict[str, str]]) -> tuple[list[dict[str, str]], int]:
    """Filas utiles: con etiqueta y sin valores vacios. Las que no, se cuentan
    y se reportan; nadie las inventa."""
    utiles = [
        r for r in registros
        if r.get("label", "").strip()
        and all(r.get(c, "").strip() for c in COLUMNAS)
    ]
    return utiles, len(registros) - len(utiles)


# ── 3. SEGMENTACION / DETECCION (del analisis) ────────────────────────────

def separar_por_clase(registros: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    """Los «objetos» del panel: las filas de cada clase. Conteo por clase es
    la deteccion: cuan balanceado llega el lote."""
    grupos: dict[str, list[dict[str, str]]] = {}
    for r in registros:
        grupos.setdefault(r["label"], []).append(r)
    return grupos


# ── 4. EXTRACCION ─────────────────────────────────────────────────────────

def resumen_por_clase(grupos: dict[str, list[dict[str, str]]]) -> dict[str, dict[str, dict[str, float]]]:
    """Media y desviacion de cada columna por clase: lo que un analista mira
    antes de entrenar nada (la pregunta de la Clase 3, ahora con numeros)."""
    resumen: dict[str, dict[str, dict[str, float]]] = {}
    for clase, filas in grupos.items():
        caja = resumen.setdefault(clase, {})
        for c in COLUMNAS:
            valores = np.asarray([float(f[c]) for f in filas], dtype=float)
            caja[c] = {"media": float(valores.mean()), "std": float(valores.std())}
    return resumen


# ── 5. ML / DL ────────────────────────────────────────────────────────────

def a_matriz(registros: list[dict[str, str]]) -> tuple[np.ndarray, np.ndarray]:
    X, y, _ = features.a_matriz(
        [
            features.Caracteristicas(
                object_id=0,
                area=float(r["area"]),
                perimeter=float(r["perimeter"]),
                width=float(r["width"]),
                height=float(r["height"]),
                aspect_ratio=float(r["aspect_ratio"]),
                circularity=float(r["circularity"]),
                eccentricity=float(r["eccentricity"]),
                solidity=float(r["solidity"]),
                extent=float(r["extent"]),
                centroid_x=0.0,
                centroid_y=0.0,
                label=r["label"],
            )
            for r in registros
        ],
        columnas=COLUMNAS,
    )
    return X, y


def evaluar(
    X_tr: np.ndarray, y_tr: np.ndarray, X_te: np.ndarray, y_te: np.ndarray,
) -> list[dict[str, object]]:
    """Los cinco modelos del curso, con su tabla de metricas."""
    from src.framework.processing.pattern_recognition_tools import PatternRecognitionTools
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler

    filas: list[dict[str, object]] = []
    for tipo in MODELOS:
        t0 = time.perf_counter()
        if tipo == "logreg":
            estimador = Pipeline([
                ("scaler", StandardScaler()),
                ("clf", LogisticRegression(random_state=SEMILLA, max_iter=2000)),
            ]).fit(X_tr, y_tr)
        else:
            estimador = PatternRecognitionTools.train(X_tr, y_tr, model_type=tipo)
        t_entreno = time.perf_counter() - t0

        if tipo == "logreg":
            y_pred = estimador.predict(X_te)
        else:
            y_pred = estimador.estimator.predict(X_te)
        fn = int(np.sum((y_pred == "OK") & (y_te == "NO_OK")))
        fp = int(np.sum((y_pred == "NO_OK") & (y_te == "OK")))
        filas.append({
            "modelo": tipo,
            "acc": float(np.mean(y_pred == y_te)),
            "fn": fn, "fp": fp,
            "coste": fn * COSTE_FN + fp * COSTE_FP,
            "t_entreno_s": t_entreno,
        })
    return filas


# ── 7. VISUALIZACION ──────────────────────────────────────────────────────

def panel(
    X: np.ndarray, y: np.ndarray, resumen, tabla: list[dict[str, object]]
) -> np.ndarray:
    """Dos figuras: la nube de la Clase 3 (dos medidas) y el rendimiento por
    modelo contra la linea base."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    linea_base = max((y == c).sum() for c in set(y.tolist())) / len(y)

    fig, (eje_izq, eje_der) = plt.subplots(1, 2, figsize=(11, 4.2))
    columna_x = list(COLUMNAS).index("circularity")
    columna_y = list(COLUMNAS).index("area")
    for clase in ("OK", "NO_OK"):
        ej = y == clase
        eje_izq.scatter(X[ej, columna_x], X[ej, columna_y], s=18, label=clase)
    eje_izq.set_xlabel("circularidad")
    eje_izq.set_ylabel("area")
    eje_izq.set_title("las dos medidas de la Clase 3")
    eje_izq.legend()

    nombres = [f["modelo"] for f in tabla]
    accs = [f["acc"] for f in tabla]
    eje_der.bar(nombres, accs, color="#4c72b0")
    eje_der.axhline(linea_base, color="gray", linestyle="--", label=f"linea base {linea_base:.2f}")
    eje_der.set_ylim(0.4, 1.05)
    eje_der.set_ylabel("accuracy en test")
    eje_der.set_title("cual modelo gana")
    eje_der.legend()
    fig.suptitle("Clase 5 · data analytics -- panel de resultados del analista")
    fig.tight_layout()
    return fig


# ── 8. INTERACCION ────────────────────────────────────────────────────────

def reporte(
    origen: str,
    n_registros: int,
    invalidas: int,
    grupos: dict[str, list[dict[str, str]]],
    resumen,
    tabla: list[dict[str, object]],
    X_te: np.ndarray, y_te: np.ndarray,
) -> str:
    """El informe que se lleva el que decide: de donde salieron los datos,
    que dice cada numero y cual es la recomendacion con su cifra."""
    linea_base = max((y_te == c).sum() for c in set(y_te.tolist())) / len(y_te)
    mejor = max(tabla, key=lambda f: (f["acc"], -f["coste"]))
    aporte = mejor["acc"] - linea_base
    texto = []
    texto.append("= " * 30)
    texto.append("REPORTE DE DESPLIEGUE -- Clase 5 · data analytics")
    texto.append("= " * 30)
    texto.append(f"\n1. ORIGEN: {origen}")
    texto.append(f"2. VALIDACION: {n_registros} filas, {invalidas} invalidas "
                 f"descartadas (el CSV de la Clase 3 lo aviso)")
    texto.append("\n3. CONTEO POR CLASE (la deteccion del panel):")
    for clase, filas in sorted(grupos.items()):
        texto.append(f"   {clase:>6s}: {len(filas)} filas")
    texto.append("\n4. MEJOR Y PEOR COLUMNA POR CLASE (media +- std):")
    for clase, caja in sorted(resumen.items()):
        mejor_col = max(caja, key=lambda c: caja[c]["std"])
        texto.append(
            f"   {clase:>6s}: {mejor_col} {caja[mejor_col]['media']:.2f} "
            f"+- {caja[mejor_col]['std']:.2f}"
        )
    texto.append("\n5. MODELOS (test honesto, {} piezas):".format(len(y_te)))
    texto.append(f"   {'modelo':>7s} {'acc':>6s} {'FN':>4s} {'FP':>4s} "
                 f"{'coste':>7s} {'t_entreno':>11s}")
    for f in tabla:
        texto.append(
            f"   {f['modelo']:>7s} {f['acc']:6.3f} {f['fn']:4d} {f['fp']:4d} "
            f"{f['coste']:7.0f} {f['t_entreno_s']:10.3f}s"
        )
    texto.append(f"   linea base «siempre OK»: {linea_base:.3f}")
    texto.append(
        f"\n6. DECISION: {mejor['modelo']} (acc {mejor['acc']:.3f}); "
        f"aporta {aporte:+.3f} sobre la linea base"
    )
    if mejor["coste"] == 0:
        texto.append("   El turno de prueba se cerro sin FN ni FP: sin piezas\n"
                     "   malas al cliente y sin buenas descartadas.")
    else:
        texto.append(
            f"   Coste del turno: {mejor['coste']:.0f} (FN={COSTE_FN:.0f}, "
            f"FP={COSTE_FP:.0f}). El modelo NO es gratis: cuesta lo que deja pasar."
        )
    return "\n".join(texto)


def main() -> int:
    SALIDA.mkdir(parents=True, exist_ok=True)
    etapas: list[tuple[str, float]] = []

    print("=" * 68)
    print("PANEL DE RESULTADOS -- Clase 5 · data analytics")
    print("=" * 68)

    t0 = time.perf_counter()
    registros, origen = adquirir_datos()
    etapas.append(("1. ADQUISICION", time.perf_counter() - t0))
    print(f"\n1. ADQUISICION: {origen} ({len(registros)} filas leidas)")

    t0 = time.perf_counter()
    utiles, invalidas = validar(registros)
    etapas.append(("2. PREPROCESAMIENTO", time.perf_counter() - t0))
    print(f"\n2. PREPROCESAMIENTO: {len(utiles)} utiles, {invalidas} invalidas")

    t0 = time.perf_counter()
    grupos = separar_por_clase(utiles)
    etapas.append(("3. DETECCION (por clase)", time.perf_counter() - t0))
    print("\n3. DETECCION del panel (separar por clase):")
    for clase, filas in sorted(grupos.items()):
        print(f"    {clase:>6s}: {len(filas)} filas")

    t0 = time.perf_counter()
    resumen = resumen_por_clase(grupos)
    etapas.append(("4. EXTRACCION (resumen)", time.perf_counter() - t0))
    print("\n4. EXTRACCION (media +- desviacion de cada medida):")
    for clase, caja in sorted(resumen.items()):
        mejor_col = max(caja, key=lambda c: caja[c]["std"])
        print(f"    {clase:>6s}: columna con mas dispersion {mejor_col}: "
              f"{caja[mejor_col]['media']:.2f} +- {caja[mejor_col]['std']:.2f}")

    X, y = a_matriz(utiles)
    print(f"\n5. ML: {X.shape[0]} filas x {X.shape[1]} columnas, cinco modelos")

    from sklearn.model_selection import train_test_split

    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=SEMILLA, stratify=y
    )
    t0 = time.perf_counter()
    tabla = evaluar(X_tr, y_tr, X_te, y_te)
    etapas.append(("5. ML (5 modelos)", time.perf_counter() - t0))

    print(f"\n6. ANALISIS ({len(y_te)} piezas en test, particion honesta):")
    print(f"    {'modelo':>7s} {'acc':>6s} {'FN':>4s} {'FP':>4s} {'coste':>7s} {'t_entreno':>11s}")
    for f in tabla:
        print(
            f"    {f['modelo']:>7s} {f['acc']:6.3f} {f['fn']:4d} {f['fp']:4d} "
            f"{f['coste']:7.0f} {f['t_entreno_s']:10.3f}s"
        )

    ruta_txt = SALIDA / "panel_de_resultados.txt"
    ruta_txt.write_text(
        reporte(origen, len(utiles), invalidas, grupos, resumen, tabla, X_te, y_te),
        encoding="utf-8",
    )
    fig = panel(X, y, resumen, tabla)
    ruta = viz.guardar(fig, SALIDA / "panel_de_resultados.png")
    print(f"\n7. VISUALIZACION: {ruta}")

    print("\n8. INTERACCION: el reporte escrito (lo que se lleva el que decide):")
    print(ruta_txt.read_text(encoding="utf-8"))
    print("\nTiempo por etapa (medido en esta misma ejecucion):")
    for nombre, segundos in etapas:
        print(f"    {nombre:24s} {segundos * 1000:8.2f} ms")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())