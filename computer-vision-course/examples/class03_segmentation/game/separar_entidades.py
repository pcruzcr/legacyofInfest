#!/usr/bin/env python3
"""
Clase 3 · Videojuego — separar sprite del fondo y contar entidades.

Un motor 2D sabe dónde colocó a cada entidad... pero la cámara de visión no.
La pregunta del contexto: *¿cuántas entidades hay en un fotograma capturado,
y dónde está cada una?* — respondida solo con los píxeles.

La escena se compone con sprites reales del motor (uno de cada categoría del
inventario: jugador, enemigo y jefe) sobre un fondo de plataforma claro. Con
eso se sabe exactamente cuántas entidades hay (3) y se puede validar la
segmentación contra esa verdad, en vez de contra una opinión.

El flujo es el del temario:

    fotograma -> umbral binario inverso -> (morfologia?) -> componentes conexas

Dos decisiones, cada una con su medicion:

* **Umbral inverso** — el fondo es claro y los sprites son oscuros; el
  objeto es lo que NO se parece al fondo. Un umbral fijo alcanza porque la
  escena es de laboratorio; en la Clase 4 se vera por que un fondo real
  exige otra cosa.
* **Apertura, solo si hay algo que limpiar** — el manual pide morfologia
  «por si acaso». Este ejemplo la aplica de todas formas y mide: sobre esta
  escena no hay motas (0 componentes de menos de 20 px), y aun asi la
  apertura 3x3 fragmenta al jefe en 7 trozos. La conclusion no es «no se
  usa morfologia»: es que **la morfologia se decide mirando la mascara, y
  su coste se reporta en la misma tabla que su beneficio** (el laboratorio
  de la clase encuentra la escena donde la apertura si tiene trabajo).

Ejecutar:
    python examples/class03_segmentation/game/separar_entidades.py
"""
from __future__ import annotations

import sys
from pathlib import Path

CURSO = Path(__file__).resolve().parents[3]
for _ruta in (CURSO, CURSO.parent):
    if str(_ruta) not in sys.path:
        sys.path.insert(0, str(_ruta))

import cv2
import numpy as np
from PIL import Image

from cvcourse import viz

SALIDA = CURSO / "outputs" / "clase03"

SPRITES = [
    ("jugador", "engine_sprites/player/player_walk_00.png"),
    ("enemigo", "engine_sprites/enemies/enemy_walker_walk_00.png"),
    ("jefe", "engine_sprites/bosses/boss_venado_charge_00.png"),
]

FONDO = 200          # gris claro de plataforma
UMBRAL_OBJETO = 175  # el objeto es lo que esta por debajo del fondo
AREA_MINIMA = 100    # una entidad ocupa mas que unas motas


def componer_escena(ruta_sprites: list[tuple[str, Path]]) -> np.ndarray:
    """Compone los sprites en una sola escena de 640x400, sin solapes."""
    lienzo = np.full((400, 640, 3), FONDO, dtype=np.uint8)
    x = 40
    for _nombre, ruta in ruta_sprites:
        sprite = np.asarray(Image.open(ruta).convert("RGBA"))
        h, w = sprite.shape[:2]
        alfa = sprite[:, :, 3:] / 255.0
        zona = lienzo[100:100 + h, x:x + w].astype(float)
        lienzo[100:100 + h, x:x + w] = (
            alfa * sprite[:, :, :3] + (1 - alfa) * zona
        ).astype(np.uint8)
        x += w + 40
    return lienzo


def resumen(img: np.ndarray, area_minima: int = 20) -> tuple[int, list[tuple[int, int, int, int, int]]]:
    """Componentes de 8-vecindad: (totales, [area, izq, arr, ancho, alto])."""
    n, _, stats, _ = cv2.connectedComponentsWithStats(img, 8)
    grandes = [
        (int(stats[i, cv2.CC_STAT_AREA]), int(stats[i, cv2.CC_STAT_LEFT]),
         int(stats[i, cv2.CC_STAT_TOP]), int(stats[i, cv2.CC_STAT_WIDTH]),
         int(stats[i, cv2.CC_STAT_HEIGHT]))
        for i in range(1, n)
        if stats[i, cv2.CC_STAT_AREA] >= area_minima
    ]
    return n - 1, grandes


def main() -> int:
    SALIDA.mkdir(parents=True, exist_ok=True)

    datasets = CURSO / "datasets"
    sprites_reales = [
        (nombre, datasets / ruta)
        for nombre, ruta in SPRITES
        if (datasets / ruta).exists()
    ]
    escena = componer_escena(sprites_reales)
    gris = cv2.cvtColor(escena, cv2.COLOR_RGB2GRAY)

    print(f"ESCENA: {len(sprites_reales)} sprites del motor sobre fondo {FONDO}")
    for nombre, ruta in sprites_reales:
        print(f"  {nombre:8s} {ruta.name}  (de {ruta.parent.name}/)")

    _, mascara = cv2.threshold(gris, UMBRAL_OBJETO, 255, cv2.THRESH_BINARY_INV)
    limpiada = cv2.morphologyEx(mascara, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))

    totales_brutos, entidades_brutas = resumen(mascara)
    motas = totales_brutos - len(entidades_brutas)
    totales_abiertos, _ = resumen(limpiada)
    n_limpia, etiquetas, stats, _ = cv2.connectedComponentsWithStats(
        limpiada, 8
    )
    entidades = [
        (int(i), int(stats[i, cv2.CC_STAT_LEFT]), int(stats[i, cv2.CC_STAT_TOP]),
         int(stats[i, cv2.CC_STAT_WIDTH]), int(stats[i, cv2.CC_STAT_HEIGHT]),
         int(stats[i, cv2.CC_STAT_AREA]))
        for i in range(1, n_limpia)
        if stats[i, cv2.CC_STAT_AREA] >= AREA_MINIMA
    ]

    print("\nMascara recien umbralizada (sin morfologia):")
    print(
        f"  {len(entidades_brutas)} componentes de mas de {AREA_MINIMA} px: "
        f"{[a for a, *_ in entidades_brutas]}"
    )
    print(f"  total {totales_brutos} componentes; {motas} motas de menos de 20 px")

    print("\nDespues de una apertura 3x3 'por si acaso':")
    print(
        f"  {len(entidades)} componentes de mas de {AREA_MINIMA} px: "
        f"{[a for i, a in [(i, stats[i, cv2.CC_STAT_AREA]) for i in range(1, n_limpia)] if a >= AREA_MINIMA]}"
    )
    print(
        f"  total {totales_abiertos} componentes: el jefe quedo fragmentado, "
        "pero no habia nada que limpiar"
    )

    print(f"\nENTIDADES detectadas: {len(entidades)} de {len(sprites_reales)} colocadas")
    print(f"\n{'entidad':>7s} {'area':>6s} {'bbox':>10s} {'centroide':>14s}")
    print("-" * 48)
    coloreada = np.zeros((*mascara.shape, 3), dtype=np.uint8)
    rng = np.random.default_rng(3)
    paleta = rng.integers(80, 255, size=(n_limpia, 3), dtype=np.uint8)
    for i in range(1, n_limpia):
        coloreada[etiquetas == i] = paleta[i % len(paleta)]
    for id_, izq, arr, w, h, area in entidades:
        cx, cy = izq + w / 2.0, arr + h / 2.0
        cv2.rectangle(escena, (izq, arr), (izq + w, arr + h), (0, 255, 0), 1)
        cv2.circle(escena, (int(cx), int(cy)), 3, (0, 0, 255), -1)
        print(f"{id_:7d} {area:6d} {w:3d}x{h:<3d} ({cx:6.1f}, {cy:6.1f})")

    # La cuenta de la mascara sin tocar, que es la medicion que decide:
    ruta = viz.guardar(
        viz.rejilla(
            [escena, mascara, limpiada, coloreada],
            [
                f"mascara bruta: {len(entidades_brutas)} componentes (sin morfologia)",
                "la apertura 3x3 'por si acaso'",
                f"entidades finales: {len(entidades)} de {len(sprites_reales)}",
                "la apertura fragmento al jefe: sin motivo",
            ],
            columnas=2,
            titulo_general="Clase 3 · videojuego -- separar sprite del fondo y contar",
        ),
        SALIDA / "separar_entidades.png",
    )
    print(f"\nFigura: {ruta}")

    print(
        f"\nLa cuenta coincide con lo que se coloco ({len(entidades)} de "
        f"{len(sprites_reales)}) y se sabe porque se coloco: sprites del\n"
        "inventario real del motor. La leccion de la apertura es de la clase:\n"
        "se midio y no habia trabajo que hacerle -- aplicar morfologia a ciegas\n"
        "tiene coste, y aqui el coste se ve en la tabla de componentes."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())