#!/usr/bin/env python3
"""
Genera los datasets del curso. Deterministas y reproducibles.

Por qué existe este guion y no unas carpetas commiteadas
--------------------------------------------------------
Es el mismo criterio que `scripts/train_reference_model.py` del motor: **se
distribuye el guion y la fuente, no el resultado**. Un dataset commiteado pesa,
se desincroniza del código que lo produjo y nadie puede saber cómo se hizo.
Uno generado se regenera en cualquier máquina y se compara por hash.

Los tres datasets
-----------------
* **D2a — fotogramas de sprites del motor.** Cada hoja de `assets/sprites/` se
  recorta en sus fotogramas y se etiqueta por carpeta: `player`, `enemies`,
  `bosses`. Es el dataset del contexto *videojuego* de las Clases 3 y 4.
* **D2b — fotogramas de escena del motor.** Capturas reales de las tres
  escenas-laboratorio (Unidades VII, VIII y IX), tomadas sin abrir ventana.
  Son las imágenes de partida de las Clases 1 y 2.
* **D3 — piezas industriales sintéticas.** Con verdad-terreno exacta y semilla
  fija. Es el contexto *industrial* de las Clases 3 y 4.

Uso
---
    python computer-vision-course/scripts/build_datasets.py            # generar
    python computer-vision-course/scripts/build_datasets.py --check    # verificar

`--check` regenera todo en un directorio temporal y compara los hashes con el
manifiesto. Es lo que convierte «es determinista» en una afirmación
comprobable y no en una intención.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path


def _fijar_semilla_de_hash() -> None:
    """Rearranca el intérprete con `PYTHONHASHSEED=0` si no lo estaba.

    Sin esto, D2b **no es reproducible**, y la causa está en el motor:
    `pattern_demo_scene._class_color` (línea 724) hace
    ``hash(label) % len(CLASS_COLORS)``. El hash de las cadenas en Python está
    aleatorizado por proceso desde la 3.3, así que cada clase sale de un color
    distinto en cada arranque. Dos capturas de la misma escena difieren en
    1.794 píxeles: los mismos textos, las mismas predicciones, otros colores.

    Se fija aquí y no se arregla en el motor por dos razones. La primera es de
    alcance: el curso no modifica el motor (decisión D4). La segunda es que
    el arreglo de verdad —usar un índice estable en vez de `hash`— es un
    defecto del motor con su propio `AUD-NNN`, y taparlo desde el curso lo
    dejaría escondido.

    La variable tiene que estar puesta **antes** de arrancar el intérprete: la
    lee el runtime al inicializarse, y ponerla en `os.environ` a mitad de
    ejecución no cambia nada. Por eso se relanza.

    Ojo con cómo se relanza: **no** se usa `os.execve`. En Windows Python la
    emula lanzando un proceso hijo y suicidando al padre, y esa emulación ha
    llegado a morir con 0xC0000005 al azar (medido: 2 de 5 ejecuciones, sin
    *faulthandler* de por medio). Un `subprocess.call` hace lo mismo —hijo con
    la variable ya puesta, padre que espera— sin pasar por esa trampa.
    """
    if os.environ.get("PYTHONHASHSEED") == "0":
        return
    import subprocess

    entorno = dict(os.environ, PYTHONHASHSEED="0")
    raise SystemExit(subprocess.call([sys.executable, *sys.argv], env=entorno))

RAIZ_DEL_CURSO = Path(__file__).resolve().parent.parent
if str(RAIZ_DEL_CURSO) not in sys.path:
    sys.path.insert(0, str(RAIZ_DEL_CURSO))

import numpy as np
from PIL import Image

from cvcourse import engine_bridge, synthetic

#: Las tres escenas-laboratorio del taller, con la unidad que ilustran.
ESCENAS = {"filter": "VII", "vision": "VIII", "pattern": "IX"}

#: Cuántos fotogramas se capturan de cada escena.
FOTOGRAMAS_POR_ESCENA = 4

#: Piezas sintéticas y su semilla. La semilla vive aquí y no en el notebook:
#: si cada cuaderno eligiera la suya, dos estudiantes compararían resultados de
#: datasets distintos sin saberlo.
PIEZAS_POR_LOTE = 120
SEMILLA = 20260805

#: Categorías de sprite y su etiqueta. El nombre de la carpeta *es* la clase.
CATEGORIAS_DE_SPRITE = ("player", "enemies", "bosses")

#: Un fotograma con menos de este porcentaje de píxeles opacos se descarta.
#: Las hojas de animación traen huecos —fotogramas en blanco al final de una
#: tira—, y un ejemplo vacío etiquetado como «boss» le enseña al modelo que un
#: rectángulo transparente es un jefe.
OPACIDAD_MINIMA = 0.02


def _hash(ruta: Path) -> str:
    return hashlib.sha256(ruta.read_bytes()).hexdigest()[:16]


# ── D2a — fotogramas de sprites ───────────────────────────────────────────

def _fotogramas_de_hoja(ruta: Path) -> list[Image.Image]:
    """Recorta una hoja de animación en sus fotogramas.

    El tamaño del fotograma se deduce de la **altura** de la hoja, no de una
    tabla fija. `tools/export_individual_frames.py` del motor mantiene una
    (`FRAME_SIZES`), pero está desactualizada para varias hojas: las del
    Gavilán miden 40 px de alto y la tabla dice 48, así que recortar por tabla
    parte los fotogramas por la mitad. La altura de la hoja no puede
    equivocarse.

    Las hojas cuyo ancho no es múltiplo exacto de la altura pierden el resto
    del último fotograma. Se acepta y se documenta: son 9 de 74 hojas, y el
    trozo perdido es siempre menor que un fotograma.
    """
    hoja = Image.open(ruta).convert("RGBA")
    ancho, alto = hoja.size
    if ancho < alto:
        return []
    return [
        hoja.crop((x, 0, x + alto, alto))
        for x in range(0, (ancho // alto) * alto, alto)
    ]


def _tiene_contenido(fotograma: Image.Image) -> bool:
    alfa = np.asarray(fotograma)[:, :, 3]
    return float((alfa > 0).mean()) >= OPACIDAD_MINIMA


def construir_sprites(destino: Path) -> dict[str, int]:
    """D2a. Devuelve cuántos ejemplos quedaron por clase."""
    conteo: dict[str, int] = {}
    for categoria in CATEGORIAS_DE_SPRITE:
        carpeta = destino / categoria
        carpeta.mkdir(parents=True, exist_ok=True)
        usados: set[str] = set()
        n = 0
        # `sorted` no es cosmético: sin él, el orden de `rglob` depende del
        # sistema de ficheros y los nombres de salida cambian de máquina en
        # máquina, con lo que el hash del manifiesto dejaría de significar nada.
        for hoja in sorted(engine_bridge.recursos("sprites")):
            if categoria not in hoja.parts:
                continue
            for i, fotograma in enumerate(_fotogramas_de_hoja(hoja)):
                if not _tiene_contenido(fotograma):
                    continue
                nombre = f"{hoja.stem}_{i:02d}"
                if nombre in usados:
                    # Dos hojas comparten stem: `enemies/enemy_fly_zone1.png`
                    # y `enemies/zone1/enemy_fly_zone1.png` (otras hojas de la
                    # zona 1 viven en subcarpetas sin chocar con ninguna de la
                    # raiz). Sin desambiguar, la hoja anidada pisa a la otra:
                    # medido en el dataset, el manifiesto contaba 116 fotogramas
                    # de enemigo mientras enumeraba 112 en sus hashes. El orden
                    # sorted decide cual se queda el nombre limpio; la segunda
                    # lleva el nombre de su carpeta delante.
                    nombre = f"{hoja.parent.name}_{nombre}"
                usados.add(nombre)
                fotograma.save(carpeta / f"{nombre}.png")
                n += 1
        conteo[categoria] = n
    return conteo


# ── D2b — fotogramas de escena ────────────────────────────────────────────

def construir_escenas(destino: Path) -> dict[str, int]:
    """D2b. Capturas reales del motor en marcha, sin abrir ventana."""
    destino.mkdir(parents=True, exist_ok=True)
    conteo: dict[str, int] = {}
    for clave, unidad in ESCENAS.items():
        fotogramas = engine_bridge.capturar_escena(clave, fotogramas=FOTOGRAMAS_POR_ESCENA)
        for i, imagen in enumerate(fotogramas):
            Image.fromarray(imagen).save(destino / f"unidad{unidad}_{clave}_{i:02d}.png")
        conteo[clave] = len(fotogramas)
    return conteo


# ── D3 — piezas sintéticas ────────────────────────────────────────────────

def construir_piezas(destino: Path) -> dict[str, int]:
    """D3. Piezas con defecto y sin él, más su verdad-terreno en CSV."""
    import csv

    destino.mkdir(parents=True, exist_ok=True)
    imagenes, verdades = synthetic.lote_de_piezas(
        n=PIEZAS_POR_LOTE, tamano=128, proporcion_defectuosas=0.4, semilla=SEMILLA
    )

    conteo = {"OK": 0, "NO_OK": 0}
    filas = []
    for imagen, verdad in zip(imagenes, verdades, strict=True):
        carpeta = destino / verdad.clase
        carpeta.mkdir(exist_ok=True)
        nombre = f"pieza_{verdad.id:03d}.png"
        Image.fromarray(imagen).save(carpeta / nombre)
        conteo[verdad.clase] += 1
        filas.append({
            "fichero": f"{verdad.clase}/{nombre}",
            "clase": verdad.clase,
            "defecto": verdad.defecto or "",
            "forma": verdad.forma,
            "bbox_f0": verdad.bbox[0], "bbox_c0": verdad.bbox[1],
            "bbox_f1": verdad.bbox[2], "bbox_c1": verdad.bbox[3],
            "area_verdadera": int(verdad.metadatos["area_verdadera"]),
        })

    with (destino / "verdad_terreno.csv").open("w", newline="", encoding="utf-8") as f:
        escritor = csv.DictWriter(f, fieldnames=list(filas[0]))
        escritor.writeheader()
        escritor.writerows(filas)

    # El caso de watershed de la Clase 3: piezas que se tocan. Se guarda aparte
    # porque no es un ejemplo de clasificación, es un ejemplo de separación.
    tocandose, verdades_tocandose = synthetic.piezas_en_contacto(n=5, semilla=SEMILLA)
    Image.fromarray(tocandose).save(destino / "piezas_en_contacto.png")
    conteo["en_contacto"] = len(verdades_tocandose)
    return conteo


# ── Orquestación ──────────────────────────────────────────────────────────

def construir_todo(raiz: Path) -> dict[str, object]:
    """Genera los tres datasets bajo `raiz` y devuelve el manifiesto."""
    if not engine_bridge.hay_motor():
        raise RuntimeError("hacen falta el repositorio del motor y sus assets")

    sprites = construir_sprites(raiz / "engine_sprites")
    escenas = construir_escenas(raiz / "engine_frames")
    piezas = construir_piezas(raiz / "synthetic_parts")

    # README.md sale del manifiesto por el mismo motivo que MANIFIESTO.json:
    # la regeneracion de verificacion se hace en un directorio temporal que
    # no contiene la documentacion del curso, y si el README entrara en los
    # hashes, --check fallaria siempre en cuanto alguien tocara el texto.
    ficheros = sorted(
        p for p in raiz.rglob("*")
        if p.is_file() and p.name not in ("MANIFIESTO.json", "README.md")
    )
    return {
        "semilla": SEMILLA,
        "conteos": {"engine_sprites": sprites, "engine_frames": escenas, "synthetic_parts": piezas},
        "n_ficheros": len(ficheros),
        "hashes": {str(p.relative_to(raiz)).replace("\\", "/"): _hash(p) for p in ficheros},
    }


def verificar(raiz: Path) -> bool:
    """Regenera en un temporal y compara con el manifiesto ya escrito.

    Es la comprobación que cierra la Fase 2: «determinista» sólo significa algo
    si alguien lo ejecuta dos veces y compara.
    """
    manifiesto = raiz / "MANIFIESTO.json"
    if not manifiesto.exists():
        print(f"ERROR: no hay manifiesto en {manifiesto}. Genera primero.", file=sys.stderr)
        return False

    esperado = json.loads(manifiesto.read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory() as tmp:
        obtenido = construir_todo(Path(tmp))

    if esperado["hashes"] == obtenido["hashes"]:
        print(f"OK: {obtenido['n_ficheros']} ficheros, hashes idénticos. Reproducible.")
        return True

    solo_esperado = set(esperado["hashes"]) - set(obtenido["hashes"])
    solo_obtenido = set(obtenido["hashes"]) - set(esperado["hashes"])
    distintos = [
        k for k in set(esperado["hashes"]) & set(obtenido["hashes"])
        if esperado["hashes"][k] != obtenido["hashes"][k]
    ]
    print("ERROR: la regeneración no coincide con el manifiesto.", file=sys.stderr)
    for titulo, lista in (
        ("faltan ahora", solo_esperado), ("sobran ahora", solo_obtenido), ("cambiaron", distintos),
    ):
        if lista:
            print(f"  {titulo} ({len(lista)}): {sorted(lista)[:5]}", file=sys.stderr)
    return False


def main() -> int:
    _fijar_semilla_de_hash()   # no vuelve: rearranca el proceso si hacía falta

    parser = argparse.ArgumentParser(description="Genera los datasets del curso de visión.")
    parser.add_argument("--check", action="store_true",
                        help="regenera en un temporal y compara hashes; no escribe nada")
    parser.add_argument("--destino", type=Path, default=RAIZ_DEL_CURSO / "datasets",
                        help="dónde escribir (por defecto computer-vision-course/datasets)")
    argumentos = parser.parse_args()

    if argumentos.check:
        return 0 if verificar(argumentos.destino) else 1

    for sub in ("engine_sprites", "engine_frames", "synthetic_parts"):
        # Se borra antes de generar: si no, un fichero de una ejecución
        # anterior con otros parámetros sobrevive, entra en el manifiesto y
        # nadie sabe de dónde salió.
        shutil.rmtree(argumentos.destino / sub, ignore_errors=True)

    manifiesto = construir_todo(argumentos.destino)
    (argumentos.destino / "MANIFIESTO.json").write_text(
        json.dumps(manifiesto, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    print(f"Generado en {argumentos.destino}")
    for grupo, conteos in manifiesto["conteos"].items():  # type: ignore[union-attr]
        print(f"  {grupo}: {conteos}")
    print(f"  {manifiesto['n_ficheros']} ficheros. Manifiesto en MANIFIESTO.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
