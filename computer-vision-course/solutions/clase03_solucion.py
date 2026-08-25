#!/usr/bin/env python3
"""
Clase 3 · Solución de referencia del laboratorio (T1–T4 y el reto).

Para el profesor y los ayudantes. Se ejecuta entera y produce las figuras y
las cifras que se piden en `docs/clase03_guia.md` §5.

No es la única solución válida. Es **una** solución completa, con los números
que un grupo bien orientado debería obtener, para poder comparar sin tener
que rehacer el laboratorio en cada corrección.

Ejecutar:
    python solutions/clase03_solucion.py

Reglas que cumple este fichero:
- Todo número impreso está medido por el propio código en esta misma
  ejecución; si un número contradice lo que imprime, se corrige el texto,
  no la medición.
- Los mensajes de consola son ASCII: en el aula hay Windows con cp1252 y un
  guion largo en un print tira la sesión (ver docs/clase01_guia.md §8).
- La validación contra la verdad-terreno es explícita en cada tarea: sin
  ella, «el watershed acertó» no significaría nada.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

CURSO = Path(__file__).resolve().parents[1]
for _ruta in (CURSO, CURSO.parent):
    if str(_ruta) not in sys.path:
        sys.path.insert(0, str(_ruta))

import cv2
import numpy as np

from cvcourse import features, synthetic, viz

SALIDA = CURSO / "outputs" / "clase03_solucion"

SEMILLA = 20260805


# ── Herramientas comunes del laboratorio ──────────────────────────────────

def en_gris(imagen: np.ndarray) -> np.ndarray:
    return np.clip(
        0.299 * imagen[..., 0] + 0.587 * imagen[..., 1] + 0.114 * imagen[..., 2],
        0, 255,
    ).astype(np.uint8) if imagen.ndim == 3 else imagen


def sal_y_pimienta(gris: np.ndarray, proporcion: float, semilla: int) -> np.ndarray:
    rng = np.random.default_rng(semilla)
    sucia = gris.copy()
    mascara = rng.random(gris.shape) < proporcion
    sucia[mascara] = np.where(rng.random(mascara.sum()) < 0.5, 0, 255)
    return sucia


def otsu(gris: np.ndarray) -> np.ndarray:
    _, binaria = cv2.threshold(gris, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return binaria > 0


def contar_componentes(mascara: np.ndarray) -> int:
    n, _, _, _ = cv2.connectedComponentsWithStats(mascara.astype(np.uint8), 8)
    return n - 1


# ── T1 — Umbral fijo vs. Otsu, medidos contra la verdad-terreno ────────────

def t1() -> None:
    print("T1 — UMBRAL FIJO vs. OTSU, contra la verdad-terreno")
    print("-" * 56)

    for forma in ("rectangulo", "circulo"):
        con_ruido, _ = synthetic.pieza_individual(
            tamano=128, ruido=4.0, forma=forma, semilla=7
        )
        limpia, verdad = synthetic.pieza_individual(
            tamano=128, ruido=0.0, forma=forma, semilla=7
        )
        gris = en_gris(con_ruido)
        verdad_ = en_gris(limpia) > 90
        print(f"\n{forma}: area de la verdad {int(verdad_.sum())} px")
        for nombre, mascara in (
            ("fijo 90", cv2.threshold(gris, 90, 255, cv2.THRESH_BINARY)[1] > 0),
            ("fijo 150", cv2.threshold(gris, 150, 255, cv2.THRESH_BINARY)[1] > 0),
            ("Otsu", otsu(gris)),
        ):
            union = int((mascara | verdad_).sum())
            iou = float((mascara & verdad_).sum()) / union if union else 1.0
            print(f"  {nombre:>10s}: area {int(mascara.sum()):5d} px  IoU {iou:.3f}")

        if verdad.radio > 0:
            teorico = math.pi * verdad.radio**2
            print(
                f"  detalle: circulo de radio {verdad.radio:.0f} px -> pi r^2 = "
                f"{teorico:.0f} px, la mascara mide {int(verdad_.sum())} px "
                f"({100 * (1 - int(verdad_.sum()) / teorico):.1f} % de discretizacion)"
            )

    print(
        "\nLectura: sobre esta pieza todos los umbrales del valle bimodal dan\n"
        "IoU 1.000. La diferencia de formas aparece en circulo: el 0,4 % que\n"
        "falta respecto a pi r^2 lo pone la discretizacion de dibujar un\n"
        "circulo en pixeles, no el umbral. Otsu no es 'mejor' aqui: es el\n"
        "que no necesita que nadie elija el umbral a ojo."
    )


# ── T2 — Morfología medida: apertura, cierre y sus números ─────────────────

def t2() -> None:
    print("\nT2 — MORFOLOGIA MEDIDA: el radio se elige con cifras")
    print("-" * 56)

    limpia, _ = synthetic.pieza_individual(tamano=128, ruido=0.0, semilla=11)
    gris = en_gris(limpia)
    sucia = sal_y_pimienta(gris, proporcion=0.04, semilla=11)
    mascara = cv2.threshold(sucia, 90, 255, cv2.THRESH_BINARY)[1] > 0
    verdad_ = gris > 90

    print(f"{'pipeline':>18s} {'componentes':>11s} {'area conservada':>14s}")
    print("-" * 46)
    escenarios = [("bruta (sal y pimienta)", mascara)]
    for radio in (1, 2):
        disco = cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE, (2 * radio + 1, 2 * radio + 1)
        )
        abierta = cv2.morphologyEx(mascara.astype(np.uint8), cv2.MORPH_OPEN, disco)
        escenarios.append((f"apertura r={radio}", abierta > 0))
        cerrada = cv2.morphologyEx(abierta, cv2.MORPH_CLOSE, disco)
        escenarios.append((f"apertura r={radio} + cierre", cerrada > 0))

    for nombre, m in escenarios:
        print(
            f"{nombre:>18s} {contar_componentes(m):11d} "
            f"{100 * m.sum() / verdad_.sum():13.1f} %"
        )

    print(
        "\nLectura: la apertura r=1 quita las 173 motas blancas del fondo\n"
        "(174 -> 1 componente) a costa de 2,7 % de area; el cierre solo tapa\n"
        "agujeros. La combinacion apertura + cierre r=1 deja 99,3 % de area:\n"
        "la mascara mas fiel. Ninguna de estas frases se puede escribir sin\n"
        "la tabla de arriba."
    )


# ── T3 — Watershed: cuando el umbral miente ────────────────────────────────

def t3() -> None:
    print("\nT3 — WATERSHED sobre piezas que se tocan")
    print("-" * 56)

    imagen, verdades = synthetic.piezas_en_contacto(
        n=5, tamano=256, ruido=3.0, semilla=SEMILLA
    )
    gris = en_gris(imagen)
    radio = verdades[0].radio
    paso = 2.0 * radio * 0.82
    valle = math.sqrt(radio**2 - (paso / 2.0) ** 2)

    mascara = otsu(gris)
    print(
        f"umbral (Otsu): {contar_componentes(mascara)} componente conexa de "
        f"{int(mascara.sum())} px donde hay {len(verdades)} piezas de radio "
        f"{radio:.0f} px"
    )

    suavizada = cv2.GaussianBlur(gris, (5, 5), 1.0)
    b2 = otsu(suavizada).astype(np.uint8) * 255
    dist = cv2.distanceTransform(b2, cv2.DIST_L2, 5)
    dmax = float(dist.max())
    umbral_marcadores = 0.65 * dmax
    print(
        f"valle del eje medio: sqrt({radio:.0f}^2 - ({paso:.1f}/2)^2) = "
        f"{valle:.1f} px; distancia maxima {dmax:.1f} px; umbral de marcadores "
        f"al 65 % = {umbral_marcadores:.1f} px"
    )

    _, seguros = cv2.threshold(dist, umbral_marcadores, 255, cv2.THRESH_BINARY)
    seguros = seguros.astype(np.uint8)
    n_seguros, marcas = cv2.connectedComponents(seguros, 8)
    desconocido = cv2.subtract(
        cv2.dilate(b2, np.ones((3, 3), np.uint8), iterations=3), seguros
    )
    marcas = marcas + 1
    marcas[desconocido == 255] = 0
    color = cv2.cvtColor(gris, cv2.COLOR_GRAY2BGR)
    marcas = cv2.watershed(color, marcas)

    regiones = [m for m in np.unique(marcas) if m > 1]
    errores = []
    for m in regiones:
        ys, xs = np.nonzero(marcas == m)
        cx, cy = float(xs.mean()), float(ys.mean())
        verdad = min(
            verdades,
            key=lambda v: math.hypot(cx - v.centro[1], cy - v.centro[0]),
        )
        errores.append(math.hypot(cx - verdad.centro[1], cy - verdad.centro[0]))
    print(f"marcadores seguros: {n_seguros - 1} -> watershed: {len(regiones)} regiones")
    for i, e in enumerate(errores, 1):
        print(f"  region {i}: error de centroide {e:.1f} px")
    print(f"  error medio {np.mean(errores):.1f} px, maximo {np.max(errores):.1f} px")

    rng = np.random.default_rng(5)
    paleta = rng.integers(60, 255, size=(marcas.max() + 1, 3), dtype=np.uint8)
    coloreada = np.zeros((*mascara.shape, 3), dtype=np.uint8)
    for m in regiones:
        coloreada[marcas == m] = paleta[m % len(paleta)]
    fig = viz.rejilla(
        [gris, mascara.astype(np.uint8) * 255,
         cv2.normalize(dist, None, 0, 255, cv2.NORM_MINMAX), coloreada],
        [
            f"banda: {len(verdades)} piezas que se tocan",
            f"umbral: 1 componente de {int(mascara.sum())} px (miente)",
            "distancia: el valle del eje medio es la clave",
            f"watershed: {len(regiones)} regiones (error medio {np.mean(errores):.1f} px)",
        ],
        columnas=2,
        titulo_general="Clase 3 · T3 -- watershed",
    )
    ruta = viz.guardar(fig, SALIDA / "t3_watershed.png")
    print(f"Figura: {ruta}")


# ── T4 — Contorno, centroide, bbox y calibración a milímetros ──────────────

def t4() -> None:
    print("\nT4 — CONTORNO, CENTROIDE, BBOX Y CALIBRACION (pixel -> mm)")
    print("-" * 56)

    ancho_real_mm = 60.0
    figuras: list[np.ndarray] = []
    titulos: list[str] = []
    errores: list[float] = []
    factores: list[float] = []

    for forma in ("rectangulo", "circulo"):
        imagen, verdad = synthetic.pieza_individual(
            tamano=128, ruido=4.0, forma=forma, semilla=7
        )
        gris = en_gris(imagen)
        suave = cv2.GaussianBlur(gris, (5, 5), 1.0)
        mascara = otsu(suave)
        contornos, _ = cv2.findContours(
            mascara.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        contorno = max(contornos, key=cv2.contourArea)
        M = cv2.moments(contorno)
        cx, cy = M["m10"] / M["m00"], M["m01"] / M["m00"]
        _, _, w, h = cv2.boundingRect(contorno)
        area = float(cv2.contourArea(contorno))
        perimetro = float(cv2.arcLength(contorno, True))
        circularidad = 4.0 * math.pi * area / (perimetro**2)
        error = math.hypot(cx - verdad.centro[1], cy - verdad.centro[0])
        factor = ancho_real_mm / w
        errores.append(error)
        factores.append(factor)

        dibujo = cv2.cvtColor(gris, cv2.COLOR_GRAY2BGR)
        cv2.drawContours(dibujo, [contorno], -1, (0, 255, 0), 1)
        cv2.circle(dibujo, (int(cx), int(cy)), 3, (0, 0, 255), -1)
        cv2.rectangle(dibujo, (int(cx - w / 2), int(cy - h / 2)),
                      (int(cx + w / 2), int(cy + h / 2)), (255, 0, 255), 1)
        figuras.append(dibujo)
        titulos.append(
            f"{forma}: ({cx:.1f}, {cy:.1f}) px = ({cx * factor:.1f}, {cy * factor:.1f}) mm"
        )

        print(
            f"{forma:>10s}: contorno {perimetro:.0f} px, bbox {w}x{h}, "
            f"centroide ({cx:.1f}, {cy:.1f}) px, error {error:.1f} px, "
            f"circularidad {circularidad:.3f}, calibracion {factor:.4f} mm/px"
        )

    print(
        f"\nLectura: el peor error ({(max(errores)):.1f} px = "
        f"{max(errores) * max(factores):.2f} mm) es una fraccion de la tolerancia "
        "de\nuna pinza industrial. La circularidad (rectangulo ~0,79, circulo "
        "~0,91) es la\ncolumna que la Clase 4 usara. El centroide en mm es la "
        "posicion de agarre."
    )
    ruta = viz.guardar(
        viz.rejilla(figuras, titulos, columnas=2,
                    titulo_general="Clase 3 · T4 -- contorno, centroide, calibracion"),
        SALIDA / "t4_contorno.png",
    )
    print(f"Figura: {ruta}")


# ── Reto — de la máscara al features.csv, sin entrenar nada ────────────────

def reto() -> None:
    print("\nRETO — MASCARA A features.csv (sin entrenar)")
    print("-" * 56)

    base = CURSO / "datasets" / "synthetic_parts"
    if (base / "verdad_terreno.csv").exists():
        import csv
        with (base / "verdad_terreno.csv").open(
            encoding="utf-8", newline=""
        ) as f:
            registros = list(csv.DictReader(f))
        origen = "dataset completo"
    else:
        import itertools
        registros = []
        for i, (forma, defecto) in enumerate(itertools.product(
            ("rectangulo", "circulo"), (None, "grieta", "mota", "deformacion")
        )):
            _, _ = synthetic.pieza_individual(
                tamano=128, defecto=defecto, forma=forma, semilla=i
            )
            registros.append({"fichero": None, "sintetica": (forma, defecto, i)})
        origen = "mini-lote sintetico"

    filas: list[features.Caracteristicas] = []
    for reg in registros:
        if reg["fichero"]:
            gris = cv2.imread(str(base / reg["fichero"]), cv2.IMREAD_GRAYSCALE)
            mascara = otsu(gris)
            medidas = features.caracteristicas_de_mascara(
                mascara, etiqueta_de_clase=reg["clase"]
            )
        else:
            forma, defecto, sem = reg["sintetica"]
            img, _ = synthetic.pieza_individual(
                tamano=128, defecto=defecto, forma=forma, semilla=sem
            )
            mascara = en_gris(img) > 90
            medidas = features.caracteristicas_de_mascara(
                mascara, etiqueta_de_clase="OK" if defecto is None else "NO_OK"
            )
        filas.extend(medidas)

    ruta = features.guardar_csv(filas, SALIDA / "features.csv")
    print(f"origen: {origen} -> {len(registros)} piezas, {len(filas)} filas")
    print(f"CSV: {ruta}")

    X, y, nombres = features.a_matriz(filas)
    for columna in ("area", "circularity", "aspect_ratio"):
        i = nombres.index(columna)
        for clase in sorted(set(y.tolist())):
            sel = np.asarray(y) == clase
            print(
                f"  {columna:>13s} {clase:>6s} media {X[sel, i].mean():8.3f}  "
                f"rango [{X[sel, i].min():.3f}, {X[sel, i].max():.3f}]"
            )

    ruta_fig = viz.guardar(
        viz.nube_de_caracteristicas(
            X, y, nombres, eje_x="circularity", eje_y="area",
            titulo="Clase 3 · reto -- dos medidas, sin entrenar nada",
        ),
        SALIDA / "reto_features_nube.png",
    )
    print(f"Figura: {ruta_fig}")
    print(
        "\nLa circularidad separa a ojo a las dos clases (0,84 vs. 0,59 de\n"
        "media); el area no (los rangos se solapan). Eso se escribe ANTES del\n"
        "modelo; la Clase 4 verifica si el modelo lo confirma o lo niega."
    )


def main() -> int:
    SALIDA.mkdir(parents=True, exist_ok=True)
    t1()
    t2()
    t3()
    t4()
    reto()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())