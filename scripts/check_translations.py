"""
check_translations.py — comprueba que los catálogos de idioma estén sanos.

F3.1 — un catálogo se pudre en silencio. Alguien renombra un título de
pantalla, la entrada del catálogo deja de coincidir con nada, y el juego sigue
funcionando: simplemente muestra esa cadena sin traducir. Nadie se entera hasta
que un estudiante pregunta por qué media pantalla está en inglés.

Este script compara los catálogos con las cadenas que el juego pide de verdad,
recorriendo el kit de interfaz. Comprueba tres cosas:

  1. Que los JSON sean válidos y no tengan claves vacías.
  2. Que no haya entradas **huérfanas**: traducciones de cadenas que ya no
     existen en el código.
  3. Que las cadenas que el juego pide y no están traducidas se listen, para
     que se pueda decidir si importan.

Uso:
    python scripts/check_translations.py
    python scripts/check_translations.py --ci    # falla si hay huérfanas
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

_RAIZ = Path(__file__).resolve().parent.parent
if str(_RAIZ) not in sys.path:
    sys.path.insert(0, str(_RAIZ))

from src.engine.core.i18n import IDIOMAS  # noqa: E402

#: Dónde buscar los literales que se muestran. Son los tres directorios cuyas
#: cadenas pasan por `draw_screen` o `draw_key_hints`.
_DIRECTORIOS = ("src/engine/scenes", "src/engine/ui", "src/framework/ui")

_TITULOS = re.compile(
    r'draw_(?:screen|top_bar)\s*\(\s*\w+\s*,\s*'
    r'("(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\')\s*'
    r'(?:,\s*("(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\'))?',
)
_PAR = re.compile(
    r'\(\s*("(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\')\s*,\s*'
    r'("(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\')\s*\)',
)


def cadenas_visibles() -> set[str]:
    """Literales que el juego pasa al kit de interfaz.

    Es el conjunto que *seguro* se traduce, y sirve para contar cuántas
    quedan sin traducir.
    """
    encontradas: set[str] = set()
    for d in _DIRECTORIOS:
        for f in sorted((_RAIZ / d).glob("*.py")):
            texto = f.read_text(encoding="utf-8", errors="replace")
            for m in _TITULOS.finditer(texto):
                for g in m.groups():
                    if g:
                        encontradas.add(g[1:-1])
            for bloque in re.findall(
                r"draw_key_hints\s*\([^)]*?\[(.*?)\]", texto, re.S,
            ):
                for m in _PAR.finditer(bloque):
                    encontradas.add(m.group(2)[1:-1])
    return {c for c in encontradas if c and not c.startswith(("{", "%"))}


def todos_los_literales() -> set[str]:
    """Cualquier literal de cadena del código de interfaz.

    Para detectar entradas huérfanas hace falta este conjunto y no el
    anterior. La primera versión de este script usaba sólo las cadenas que
    pasan por `draw_screen`, y marcaba como huérfanas diez entradas
    perfectamente vivas —«Resume», «Save & Quit», «Cancel»— porque llegan a la
    pantalla desde listas de opciones, no desde una llamada al kit.

    Una herramienta que da falsas alarmas se deja de mirar, y entonces deja de
    servir también para las verdaderas.
    """
    literales: set[str] = set()
    patron = re.compile(r'"((?:[^"\\]|\\.)*)"|\'((?:[^\'\\]|\\.)*)\'')
    for d in (*_DIRECTORIOS, "src/framework/scenes", "src/engine/core"):
        carpeta = _RAIZ / d
        if not carpeta.is_dir():
            continue
        for f in sorted(carpeta.rglob("*.py")):
            for m in patron.finditer(f.read_text(encoding="utf-8", errors="replace")):
                literales.add(m.group(1) if m.group(1) is not None else m.group(2))
    return literales


def main() -> int:
    parser = argparse.ArgumentParser(description="Comprueba los catálogos de idioma")
    parser.add_argument("--ci", action="store_true",
                        help="falla si hay entradas huérfanas")
    args = parser.parse_args()

    visibles = cadenas_visibles()
    literales = todos_los_literales()
    print(f"Cadenas del kit de interfaz: {len(visibles)}")
    print(f"Literales totales en el código de interfaz: {len(literales)}\n")

    problemas = 0
    for idioma in IDIOMAS:
        ruta = _RAIZ / "locale" / f"{idioma}.json"
        if not ruta.exists():
            print(f"[FALTA] {ruta}")
            problemas += 1
            continue
        try:
            catalogo = json.loads(ruta.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            print(f"[ROTO ] {ruta}: {e}")
            problemas += 1
            continue

        vacias = [k for k, v in catalogo.items() if not str(k).strip() or not str(v).strip()]
        huerfanas = sorted(set(catalogo) - literales)
        sin_traducir = sorted(visibles - set(catalogo))

        print(f"  {idioma}: {len(catalogo)} entradas")
        if vacias:
            print(f"    [ERROR] {len(vacias)} entrada(s) con clave o valor vacío")
            problemas += 1
        if huerfanas:
            # Huérfana = traducción de algo que ya no existe. Es el síntoma de
            # que alguien renombró una cadena y el catálogo se quedó atrás.
            print(f"    [AVISO] {len(huerfanas)} entrada(s) sin uso en el código:")
            for h in huerfanas[:8]:
                print(f"             {h!r}")
            if len(huerfanas) > 8:
                print(f"             ... y {len(huerfanas) - 8} más")
            if args.ci:
                problemas += 1
        if sin_traducir:
            # No todas las cadenas sin entrada son un hueco. El código fuente
            # es bilingüe: un literal que ya está en castellano no necesita
            # entrada en `es.json`, porque el respaldo lo muestra tal cual y
            # eso es exactamente lo correcto. Añadirle una entrada identidad
            # engordaría el catálogo y, peor, rompería la comprobación de ida
            # y vuelta de `test_i18n`: afirmaría que el original está en
            # castellano justo cuando `en.json` dice que está en inglés.
            print(f"    [nota ] {len(sin_traducir)} cadena(s) sin entrada "
                  "(se muestran tal cual; correcto si el original ya está "
                  "en este idioma)")

    # AUD-307 — la comprobación que faltaba, y que sí se puede hacer exacta.
    #
    # Lo de arriba explica por qué «sin entrada» no basta para acusar a nadie:
    # el código fuente es bilingüe y un literal ya castellano no necesita
    # entrada en `es.json`. Pero de ahí no se sigue que no haya nada que
    # comprobar, y durante seis cadenas no se comprobó nada.
    #
    # La regla exacta sale de para qué sirve cada catálogo. `es.json` traduce
    # del inglés al castellano, así que **una cadena que no está en `es.json`
    # es que ya estaba en castellano** — no hay heurística de idioma aquí, lo
    # dice el propio catálogo. Y una cadena en castellano tiene que tener su
    # entrada en `en.json`, o el jugador que juega en inglés la ve en español.
    #
    # Medido al escribir esto: seis la incumplían —'ESTUDIANTE', 'EXPERIENCIA',
    # 'Elegir', 'IDENTIFICACIÓN', 'Subir rango' y 'ÁRBOL DE HABILIDADES'—, y
    # las dos últimas son de AUD-293 y AUD-267. O sea, el modo de fallo no es
    # que alguien renombre una cadena: es que una **función nueva** llega con
    # sus textos y nadie se acuerda del catálogo. Eso es lo que esto vigila.
    ruta_es = _RAIZ / "locale" / "es.json"
    ruta_en = _RAIZ / "locale" / "en.json"
    if ruta_es.exists() and ruta_en.exists():
        cat_es = json.loads(ruta_es.read_text(encoding="utf-8"))
        cat_en = json.loads(ruta_en.read_text(encoding="utf-8"))
        castellanas = {s for s in visibles if s not in cat_es}
        sin_ingles = sorted(castellanas - set(cat_en))
        if sin_ingles:
            print(f"\n  [ERROR] {len(sin_ingles)} cadena(s) en castellano sin "
                  f"traducción en en.json — se verían en español jugando en "
                  f"inglés:")
            for s in sin_ingles:
                print(f"           {s!r}")
            problemas += 1

    print()
    if problemas:
        print(f"{problemas} problema(s) en los catálogos")
        return 1
    print("Catálogos en orden.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
