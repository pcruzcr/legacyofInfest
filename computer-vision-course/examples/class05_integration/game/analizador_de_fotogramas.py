#!/usr/bin/env python3
"""
Clase 5 · Videojuego — analizador de fotogramas: el motor se ve a si mismo.

El sistema de referencia del dominio videojuego. Recorre la cadena completa
del bloque, desde el fotograma hasta la alerta de juego:

    ADQUISICION -> PREPROCESAMIENTO -> SEGMENTACION/DETECCION -> EXTRACCION
                 -> ML/DL -> ANALISIS -> VISUALIZACION -> INTERACCION

La pregunta que decide el sistema: *¿que entidades hay en este fotograma y
que hace el juego con ellas?*

Tres decisiones de integracion, cada una con su por que:

1. **El modelo NO se entrena aqui: se despliega.** La etapa ML/DL carga el
   modelo que guardo la Clase 4 (`outputs/clase04/modelo_entidades.pkl`) con
   `PatternRecognitionTools.load_model`. Integrar es reutilizar el artefacto
   de la clase anterior, no repetirla. Si el fichero no existe, se reentrena
   un KNN con el mismo metodo y se guarda en `outputs/clase05/` — el sistema
   tiene que poder arrancar en una maquina sin las Clases 1-4 detras.
2. **El fotograma se compone con el inventario real del motor.** Las tres
   entidades salen de `datasets/engine_sprites` (sprites capturados del
   juego por el generador del curso); la escena es lo que veria una camara
   que mirara la pantalla. Se sabe que hay 3 entidades por construccion, y
   contra esa verdad se mide la deteccion.
3. **La interaccion es una accion de juego, no una etiqueta.** El analisis
   convierte las predicciones en decisiones: alerta si hay enemigos o jefe,
   silencio si solo hay jugador, y nunca actua sobre una entidad con
   confianza baja. El sistema no informa: decide.

Ejecutar:
    python examples/class05_integration/game/analizador_de_fotogramas.py
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
from PIL import Image

from cvcourse import features, viz

SALIDA = CURSO / "outputs" / "clase05"

COLUMNAS = (
    "area", "perimeter", "width", "height", "aspect_ratio",
    "circularity", "eccentricity", "solidity", "extent",
)

FONDO = 200           # gris claro de plataforma: objeto = lo oscuro
UMBRAL_OBJETO = 175   # Clase 3: umbral binario inverso sobre fondo claro
AREA_MINIMA = 100     # una entidad ocupa mas que unas motas
CONFIANZA_MINIMA = 0.80  # por debajo: el sistema no actua

#: El inventario del motor que compone el fotograma: (clase, ruta en el
#: dataset del curso). Sprites que NO entrenaron a este sistema en particular
#: (el modelo se entreno en otro proceso con otros fotogramas del mismo set).
SPRITES = [
    ("player", "engine_sprites/player/player_walk_00.png"),
    ("enemies", "engine_sprites/enemies/enemy_walker_walk_00.png"),
    ("bosses", "engine_sprites/bosses/boss_venado_charge_00.png"),
]


# ── 1. ADQUISICION ────────────────────────────────────────────────────────

def adquirir_fotograma() -> tuple[np.ndarray, list[tuple[str, Path]]]:
    """Compone el fotograma que veria la camara: sprites del motor sobre la
    plataforma. Devuelve la escena y la verdad (cuantos de cada clase)."""
    lienzo = np.full((400, 640, 3), FONDO, dtype=np.uint8)
    x = 40
    usados: list[tuple[str, Path]] = []
    for clase, ruta in SPRITES:
        archivo = CURSO / "datasets" / ruta
        if not archivo.exists():
            continue
        sprite = np.asarray(Image.open(archivo).convert("RGBA"))
        h, w = sprite.shape[:2]
        alfa = sprite[:, :, 3:] / 255.0
        zona = lienzo[100:100 + h, x:x + w].astype(float)
        lienzo[100:100 + h, x:x + w] = (
            alfa * sprite[:, :, :3] + (1 - alfa) * zona
        ).astype(np.uint8)
        usados.append((clase, archivo))
        x += w + 40
    return lienzo, usados


# ── 2. PREPROCESAMIENTO ───────────────────────────────────────────────────

def preprocesar(escena: np.ndarray) -> np.ndarray:
    """Gris solo: el fondo es claro y los sprites son oscuros, y en este
    fotograma de laboratorio no hay ruido que limpiar (medida de la Clase 3:
    aplicar morfologia a ciegas fragmenta sin trabajo que hacerle)."""
    return cv2.cvtColor(escena, cv2.COLOR_RGB2GRAY)


# ── 3. SEGMENTACION / DETECCION ───────────────────────────────────────────

def segmentar(gris: np.ndarray) -> tuple[list[tuple[int, int, int, int, int]], np.ndarray]:
    """Umbral inverso + componentes conexas. Devuelve la mascara y las
    regiones (area, izq, arr, ancho, alto) ordenadas por izquierda: el
    escaner de componentes viaja por filas, no por x, y la verdad del
    fotograma esta en orden de posicion — sin ordenar, el analisis
    emparejaria cada region con la entidad equivocada."""
    _, mascara = cv2.threshold(gris, UMBRAL_OBJETO, 255, cv2.THRESH_BINARY_INV)
    n, _, stats, _ = cv2.connectedComponentsWithStats(mascara, 8)
    regiones = [
        (int(stats[i, cv2.CC_STAT_AREA]), int(stats[i, cv2.CC_STAT_LEFT]),
         int(stats[i, cv2.CC_STAT_TOP]), int(stats[i, cv2.CC_STAT_WIDTH]),
         int(stats[i, cv2.CC_STAT_HEIGHT]))
        for i in range(1, n)
        if stats[i, cv2.CC_STAT_AREA] >= AREA_MINIMA
    ]
    return sorted(regiones, key=lambda r: r[1]), mascara


# ── 4. EXTRACCION ─────────────────────────────────────────────────────────

def extraer(mascara: np.ndarray, region) -> features.Caracteristicas:
    """Las 9 caracteristicas de la Clase 3 sobre la mascara de la entidad.

    La extraccion mide lo que la SEGMENTACION decidio, no re-umbraliza: un
    segundo umbral distinto (p. ej. 128 cuando la segmentacion uso 175)
    corta los pixeles claros del sprite, le cambia la silueta al clasificador
    y degrada las predicciones. La etapa de abajo consume la salida de la
    de arriba; ese es el contrato entre etapas."""
    _area, izq, arr, w, h = region
    recorte = mascara[arr:arr + h, izq:izq + w]
    filas = features.caracteristicas_de_mascara(recorte > 0, area_minima=50)
    return max(filas, key=lambda f: f.area)


# ── 5. ML / DL ────────────────────────────────────────────────────────────

def cargar_modelo_desplegado():
    """El modelo de la Clase 4 si existe; si no, se reentrena un KNN con el
    mismo metodo y se guarda. Integrar = reutilizar el artefacto, no repetir."""
    from src.framework.processing.pattern_recognition_tools import PatternRecognitionTools

    desplegado = CURSO / "outputs" / "clase04" / "modelo_entidades.pkl"
    if desplegado.exists():
        print(f"  modelo desplegado de la Clase 4: {desplegado}")
        return PatternRecognitionTools.load_model(desplegado)

    print("  no esta el modelo de la Clase 4: se reentrena un KNN en este mismo")
    filas: list[features.Caracteristicas] = []
    base = CURSO / "datasets" / "engine_sprites"
    for clase in ("player", "enemies", "bosses"):
        for ruta in sorted((base / clase).glob("*.png")):
            imagen = np.asarray(Image.open(ruta).convert("RGBA"))
            filas.extend(
                features.caracteristicas_de_mascara(
                    imagen[:, :, 3] > 0, etiqueta_de_clase=clase
                )
            )
    X, y, _ = features.a_matriz(filas, columnas=COLUMNAS)
    modelo = PatternRecognitionTools.train(X, y, model_type="knn")
    SALIDA.mkdir(parents=True, exist_ok=True)
    PatternRecognitionTools.save_model(modelo, SALIDA / "modelo_entidades.pkl")
    print(f"  {X.shape[0]} sprites medidos; KNN guardado en {SALIDA / 'modelo_entidades.pkl'}")
    return modelo


# ── 6. ANALISIS ───────────────────────────────────────────────────────────

def decidir(prediccion: str, probabilidad: dict[str, float]) -> str:
    """La accion de juego: la clase con mas probabilidad, y solo si la
    confianza alcanza. Un sistema que actua con confianza 0.40 es peor que
    uno que se calla."""
    confianza = max(probabilidad.values())
    if confianza < CONFIANZA_MINIMA:
        return "SILENCIO (confianza baja)"
    if prediccion == "player":
        return "IGNORAR (es el jugador)"
    return f"ALERTA: {prediccion} a la vista"


# ── 7. VISUALIZACION ──────────────────────────────────────────────────────

def anotar(
    escena: np.ndarray,
    regiones: list[tuple[int, int, int, int, int]],
    decisiones: list[tuple[str, float, str]],
) -> np.ndarray:
    """Fotograma con la caja, la clase y la decision de cada entidad."""
    anotada = escena.copy()
    for (_area, izq, arr, w, h), (clase, confianza, accion) in zip(
        regiones, decisiones, strict=True
    ):
        color = (0, 220, 0) if clase == "player" else (0, 0, 220)
        cv2.rectangle(anotada, (izq, arr), (izq + w, arr + h), color, 2)
        cv2.putText(
            anotada, f"{clase} {confianza:.2f}", (izq, arr - 6),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2,
        )
    return anotada


# ── 8. INTERACCION ────────────────────────────────────────────────────────

def informe_de_partida(decisiones: list[tuple[str, float, str]]) -> str:
    """El reporte que consumiria el resto del juego: cuentas por clase y la
    accion agregada del sistema."""
    alertas = [a for _, _, a in decisiones if a.startswith("ALERTA")]
    if alertas:
        return (f"{len(alertas)} alerta(s) activa(s): "
                f"{'; '.join(a for a in alertas)}")
    return "sin hostiles: el juego sigue su curso"


def main() -> int:
    SALIDA.mkdir(parents=True, exist_ok=True)
    etapas: list[tuple[str, float]] = []

    print("=" * 68)
    print("ANALIZADOR DE FOTOGRAMAS -- Clase 5 · videojuego")
    print("=" * 68)

    t0 = time.perf_counter()
    escena, verdades = adquirir_fotograma()
    etapas.append(("1. ADQUISICION", time.perf_counter() - t0))
    print(f"\n1. ADQUISICION: fotograma de {escena.shape[1]}x{escena.shape[0]} "
          f"con {len(verdades)} entidades del inventario del motor:")
    for clase, ruta in verdades:
        print(f"    {clase:8s} {ruta.parent.name}/{ruta.name}")

    t0 = time.perf_counter()
    gris = preprocesar(escena)
    etapas.append(("2. PREPROCESAMIENTO", time.perf_counter() - t0))

    t0 = time.perf_counter()
    regiones, mascara = segmentar(gris)
    etapas.append(("3. SEGMENTACION", time.perf_counter() - t0))
    print(
        f"\n3. SEGMENTACION: {len(regiones)} regiones de mas de {AREA_MINIMA} px "
        f"({len(verdades)} entidades colocadas)"
    )

    t0 = time.perf_counter()
    filas = [extraer(mascara, r) for r in regiones]
    etapas.append(("4. EXTRACCION", time.perf_counter() - t0))

    X, y, _ = features.a_matriz(filas, columnas=COLUMNAS)
    print(f"\n4. EXTRACCION: {X.shape[0]} filas x {X.shape[1]} caracteristicas "
          "(las 9 geometricas de la clase 3)")

    print("\n5. ML: se CARGA el modelo desplegado, no se entrena")
    from src.framework.processing.pattern_recognition_tools import PatternRecognitionTools

    modelo = cargar_modelo_desplegado()

    decisiones: list[tuple[str, float, str]] = []
    t0 = time.perf_counter()
    for i in range(X.shape[0]):
        prediccion = PatternRecognitionTools.classify(X[i:i + 1], modelo)
        probabilidad = PatternRecognitionTools.classify_proba(X[i:i + 1], modelo)
        decisiones.append((prediccion, max(probabilidad.values()),
                           decidir(prediccion, probabilidad)))
    etapas.append(("5. ML (inferencias)", time.perf_counter() - t0))

    print("\n6. ANALISIS (entidad por entidad, con accion de juego):")
    for i, (clase, confianza, accion) in enumerate(decisiones):
        real = verdades[i][0] if i < len(verdades) else "?"
        marca = "bien" if clase == real else "FALLO"
        print(f"    entidad {i}: predicha={clase:7s} conf={confianza:.2f} "
              f"real={real:7s} [{marca}] -> {accion}")

    print("\n8. INTERACCION: informe para el resto del motor:")
    print(f"    {informe_de_partida(decisiones)}")

    anotada = anotar(escena, regiones, decisiones)
    ruta = viz.guardar(
        viz.comparar(
            escena,
            anotada,
            titulo_antes="fotograma de la camara (3 entidades del motor)",
            titulo_despues="entidades clasificadas y decisiones del juego",
            titulo_general="Clase 5 · videojuego -- el motor se ve a si mismo",
        ),
        SALIDA / "analizador_de_fotogramas.png",
    )
    print(f"\n7. VISUALIZACION: {ruta}")
    print("\nTiempo por etapa (medido en esta misma ejecucion):")
    for nombre, segundos in etapas:
        print(f"    {nombre:24s} {segundos * 1000:8.2f} ms")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())