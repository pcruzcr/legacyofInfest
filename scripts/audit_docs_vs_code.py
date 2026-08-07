#!/usr/bin/env python3
"""
Cada documento contra el código: qué promete y qué existe de verdad.

Por qué existe
==============
Este mes, **tres** documentos resultaron describir cosas que no existen:

* `07_STAGE0_DESIGN.md` especificaba un mapa de 240 × 14 con 27 mensajes y 12
  enemigos. El mapa real mide 100 × 38. De esa ficción salió un generador que
  llevaba meses listo para borrar el escenario bueno.
* `03_ARCHITECTURE.md` prometía un `transitions.py` con cinco clases y cero
  usos.
* El README decía 1.333 pruebas en español y 640 en inglés; había 2.020.

Un documento que miente es peor que uno que falta: el que falta se nota, y el
que miente se cree. `docs/60` tiene 22 pruebas que atan sus cifras al código;
los otros 94 documentos no tienen nada. Esto es el barrido que los cubre a
todos, aunque sea con menos precisión.

Cómo evita ser otro calificador que castiga trabajo correcto
=============================================================
La primera versión de este script daba **65 documentos con hallazgos** y casi
todo era ruido: marcaba `ValueError`, `None`, `BG_Far` —que es el nombre de una
capa de Tiled, no un identificador de Python—, `StandardScaler` de scikit-learn
y los nombres de los parámetros de las funciones.

Un informe así se lee una vez y se ignora para siempre, que es exactamente lo
que pasó con las seis herramientas de calificación que este mes hubo que
arreglar por castigar trabajo correcto. Así que se descuenta, en este orden:

1. **Los builtins de Python.** `ValueError` no lo define este proyecto.
2. **Las cadenas literales de `src/`.** Los nombres de capa, de tipo de objeto
   y de propiedad TMX viven como cadenas, no como identificadores.
3. **Los atributos de clase.** `Events.PLAYER_DIED` es un atributo, no una
   asignación de módulo.
4. **Los nombres de parámetro.** Un documento que cita `damage_amount` está
   citando la firma de una función, y eso es documentación correcta.
5. **Los módulos de terceros importados.** `Pipeline` es de scikit-learn.

Lo que queda son identificadores que el documento presenta como del proyecto y
que el proyecto no tiene, o que tiene y nadie usa.

Uso
---
    python scripts/audit_docs_vs_code.py            # informe legible
    python scripts/audit_docs_vs_code.py --json     # para automatizar
"""
from __future__ import annotations

import argparse
import ast
import builtins
import json
import pathlib
import re
import sys

RAIZ = pathlib.Path(__file__).resolve().parent.parent

#: Identificadores citados entre comillas invertidas en Markdown.
_CITA = re.compile(r"`([A-Za-z_][A-Za-z0-9_]{2,})`")

#: Lo que no cuenta como "del proyecto" aunque aparezca citado.
_BUILTINS: frozenset[str] = frozenset(dir(builtins))

#: Palabras que aparecen citadas y son convenciones, no código.
_CONVENCIONES: frozenset[str] = frozenset({
    "PascalCase", "snake_case", "UPPER_SNAKE_CASE", "camelCase", "kebab_case",
    # AUD-312 — teclas. Las guías dicen «mantén `Shift` para correr» y
    # «`Espacio` salta», y el barrido las leía como símbolos por venir en
    # mayúscula inicial entre acentos graves. No hay forma de que existan en
    # el código con ese nombre: `pygame` las llama `K_LSHIFT` y `K_SPACE`.
    "Alt", "Shift", "Ctrl", "Tab", "Esc", "Enter", "Espacio", "Space",
    "Intro", "Supr", "Del", "Backspace", "Arriba", "Abajo", "Izquierda",
    "Derecha",
    # Etiquetas de estado del índice maestro, no identificadores.
    "Current", "Historical", "Superseded",
})


def _ficheros_de_codigo() -> list[pathlib.Path]:
    carpetas = ("src", "tests", "scripts", "tools")
    ficheros: list[pathlib.Path] = []
    for carpeta in carpetas:
        ficheros.extend((RAIZ / carpeta).rglob("*.py"))
    return [f for f in ficheros if "__pycache__" not in f.parts]


def _inventario() -> tuple[dict[str, set[str]], dict[str, set[str]],
                           set[str], dict[str, set[str]]]:
    """`(definidos, usados, cadenas, declarados)`.

    `definidos` es todo lo que hace que un nombre **exista**: clases,
    funciones, constantes, parámetros e imports. `declarados` es el
    subconjunto que tiene sentido buscar como huérfano —clases, funciones y
    constantes de módulo—.

    La distinción no es cosmética. La primera versión metía los parámetros en
    los dos conjuntos y daba **964 huérfanos**: un parámetro sólo se usa
    dentro de su propia función, así que la resta «usado fuera de donde se
    define» siempre salía vacía y todos aparecían muertos. Un informe con 964
    falsos positivos no lo lee nadie dos veces.
    """
    definidos: dict[str, set[str]] = {}
    declarados: dict[str, set[str]] = {}
    usados: dict[str, set[str]] = {}
    cadenas: set[str] = set()

    for f in _ficheros_de_codigo():
        try:
            arbol = ast.parse(f.read_text(encoding="utf-8", errors="replace"))
        except SyntaxError:
            continue
        ruta = str(f.relative_to(RAIZ))
        es_fuente = ruta.startswith("src")

        for n in ast.walk(arbol):
            if es_fuente:
                if isinstance(n, (ast.ClassDef, ast.FunctionDef,
                                  ast.AsyncFunctionDef)):
                    definidos.setdefault(n.name, set()).add(ruta)
                    if not n.name.startswith("_"):
                        declarados.setdefault(n.name, set()).add(ruta)
                    # Los parámetros también son API documentada.
                    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        for arg in [*n.args.args, *n.args.kwonlyargs]:
                            definidos.setdefault(arg.arg, set()).add(ruta)
                elif isinstance(n, ast.Assign):
                    for t in n.targets:
                        if isinstance(t, ast.Name):
                            definidos.setdefault(t.id, set()).add(ruta)
                            if t.id.isupper():
                                declarados.setdefault(t.id, set()).add(ruta)
                        elif isinstance(t, ast.Attribute):
                            definidos.setdefault(t.attr, set()).add(ruta)
                elif isinstance(n, ast.AnnAssign):
                    if isinstance(n.target, ast.Name):
                        definidos.setdefault(n.target.id, set()).add(ruta)
                    elif isinstance(n.target, ast.Attribute):
                        definidos.setdefault(n.target.attr, set()).add(ruta)
                elif isinstance(n, ast.Constant) and isinstance(n.value, str):
                    # Nombres de capa, de tipo TMX y de propiedad viven aquí.
                    if n.value.isidentifier():
                        cadenas.add(n.value)

            # AUD-312 — y las cadenas de `scripts/` también nombran cosas.
            #
            # `design_completable`, `file_parses`, `required_layers`… son las
            # categorías de la rúbrica de `grade_stage.py`, y existen como
            # claves de diccionario en ese script. La guía del motor las
            # documenta con razón —son lo que ve un estudiante en su nota— y el
            # barrido las daba por inventadas porque sólo miraba `src/`.
            elif not es_fuente and isinstance(n, ast.Constant) \
                    and isinstance(n.value, str) and n.value.isidentifier():
                cadenas.add(n.value)

            # AUD-312 — fuera de `src/` también se definen nombres que la
            # documentación cita con razón.
            #
            # `definidos` sólo se poblaba con `src/`, aunque el barrido lee
            # cuatro carpetas. Consecuencia medida: los documentos salían
            # acusados de citar `test_stage_template_import` (que vive en
            # `tests/`), `design_completable` o `file_parses` (categorías de
            # `scripts/grade_stage.py`) y `generar` (de `tools/`). Nada de eso
            # es un error del documento — es una carpeta que el inventario no
            # miraba, y contaba **decenas** de los supuestos fantasmas.
            #
            # Sólo entran en `definidos`, no en `declarados`: el barrido de
            # huérfanos sigue preguntándose por la API de `src/`, que es la que
            # tiene sentido buscar sin usos.
            elif not es_fuente and isinstance(
                    n, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                definidos.setdefault(n.name, set()).add(ruta)

            if isinstance(n, ast.Name):
                usados.setdefault(n.id, set()).add(ruta)
            elif isinstance(n, ast.Attribute):
                usados.setdefault(n.attr, set()).add(ruta)
            elif isinstance(n, ast.alias):
                # Un import de terceros cuenta como "existe": el documento
                # que cita `StandardScaler` no miente.
                nombre = (n.asname or n.name).split(".")[-1]
                definidos.setdefault(nombre, set()).add(ruta)
                usados.setdefault(nombre, set()).add(ruta)

    # AUD-312 — un módulo citado por su nombre existe.
    #
    # `75_BIBLIA_TECNICA.md` lista los ficheros de prueba —`test_color_tools`,
    # `test_boss_base`…— y los scripts —`check_bestiary`,
    # `check_dependency_sync`—. Son ficheros reales, pero el barrido buscaba
    # clases y funciones, así que los daba por inventados: **más de cien** de
    # sus supuestos fantasmas eran esto. Un documento que enumera la suite no
    # está mintiendo por no citarla con la extensión puesta.
    cadenas |= {f.stem for f in _ficheros_de_codigo()}
    cadenas |= {d.name for d in (RAIZ / "src" / "stages").iterdir()
                if d.is_dir() and not d.name.startswith("_")}
    cadenas |= _nombres_de_los_tmx()
    # AUD-312 — un asset citado por su nombre también existe.
    #
    # `20_ASSET_BIBLE.md` y `17_BOSS_SPEC.md` nombran fuentes (`banner_medium`),
    # sprites (`mask_frag`), pistas y efectos. Son ficheros de `assets/`, no
    # símbolos de Python, y el barrido los daba por inventados — acusando a la
    # biblia de assets de inventarse los assets.
    for asset in (RAIZ / "assets").rglob("*"):
        if asset.is_file() and asset.stem.isidentifier():
            cadenas.add(asset.stem)
    return definidos, usados, cadenas, declarados


def _nombres_de_los_tmx() -> set[str]:
    """Nombres que existen en los mapas y que ningún `.py` menciona (AUD-312).

    La documentación de TMX cita objetos por su `name` —`Checkpoint_01`,
    `Solid_Floor`, `Walker_01`—, capas por el suyo —`BG_Far`, `FG_Overlay`— y
    propiedades por el de la etiqueta. Nada de eso aparece en el código: vive
    en los `.tmx`. El barrido los daba por inexistentes y acusaba a
    `06_TMX_SPEC.md` de inventárselos, cuando el documento estaba describiendo
    exactamente lo que hay en los mapas.

    Se leen con expresiones regulares y no con un parser de XML a propósito:
    esto es un inventario de nombres, no una validación —de eso ya se encarga
    `validate_tmx.py`—, y un TMX a medio guardar no debe tumbar el informe.
    """
    nombres: set[str] = set()
    for carpeta in ("assets/maps", "student_templates"):
        base = RAIZ / carpeta
        if not base.exists():
            continue
        for tmx in base.rglob("*.tmx"):
            texto = tmx.read_text(encoding="utf-8", errors="replace")
            for atributo in ("name", "type", "value"):
                nombres |= set(re.findall(rf'{atributo}="([^"]+)"', texto))
    return {n for n in nombres if n.isidentifier()}


#: AUD-150 — marcas para citar un nombre **para decir que no existe**.
#:
#: Al corregir `05_ENEMY_SPEC.md` apareció una paradoja incómoda: la tabla que
#: dice «`detection_rect` no existe, es `detection_range_x`» hacía que el
#: barrido volviera a acusar al documento de citar `detection_rect`. El
#: documento quedaba peor **por haberse corregido**, y la única forma de
#: bajar el contador era dejar de explicar el error.
#:
#: Se resuelve con una marca explícita en vez de adivinando por el texto: un
#: `<!-- cita-historica -->` … `<!-- /cita-historica -->` alrededor de la
#: tabla de correcciones. Explícito y aburrido, que para esto es lo que hay
#: que ser: una heurística sobre las palabras «no existe» habría dejado fuera
#: las tablas escritas en inglés y las que no usan esa frase.
_ABRE_HISTORICA = "<!-- cita-historica -->"
_CIERRA_HISTORICA = "<!-- /cita-historica -->"

#: AUD-312 — marca para el **diseño que todavía no se ha construido**.
#:
#: Es distinta de `cita-historica` y conviene no confundirlas:
#:
#: * `cita-historica` envuelve un nombre citado **para desmentirlo** — «esto no
#:   existe, usa aquello». El nombre está ahí como advertencia.
#: * `diseno-pendiente` envuelve una **ficha de diseño**: los ataques del
#:   Gavilán, las formas del Paburu, las fases 2 y 3 del Rey. Nadie se ha
#:   equivocado al escribirlas; describen lo que hay que construir, y una
#:   especificación sin eso no es una especificación.
#:
#: Sin esta marca, las fichas de jefes producían ~130 de los «símbolos que no
#: existen», y el informe no servía para lo que sirve: encontrar documentación
#: que se ha quedado atrás. Un contador que mezcla las dos cosas obliga a
#: leerse los 500 nombres para saber cuáles importan, que es tanto como no
#: tener contador.
_ABRE_DISENO = "<!-- diseno-pendiente -->"
_CIERRA_DISENO = "<!-- /diseno-pendiente -->"


def auditar() -> list[dict]:
    definidos, usados, cadenas, declarados = _inventario()
    conocidos = set(definidos) | cadenas | _BUILTINS | _CONVENCIONES

    informe: list[dict] = []
    for doc in sorted((RAIZ / "docs").rglob("*.md")):
        texto = doc.read_text(encoding="utf-8", errors="replace")
        # AUD-150 — las líneas que DESMIENTEN un nombre no cuentan como cita.
        #
        # Al corregir `05_ENEMY_SPEC.md` apareció una paradoja incómoda: la
        # tabla que dice «`detection_rect` no existe, es `detection_range_x`»
        # hacía que el barrido volviera a acusar al documento de citar
        # `detection_rect`. El documento quedaba peor por haberse corregido.
        #
        # Una línea que contiene «no existe», «no exist» o un tachado de
        # markdown está haciendo exactamente lo que este registro pide: poner
        # la etiqueta. Se salta.
        lineas_utiles = []
        dentro = False
        for linea in texto.splitlines():
            if _ABRE_HISTORICA in linea or _ABRE_DISENO in linea:
                dentro = True
                continue
            if _CIERRA_HISTORICA in linea or _CIERRA_DISENO in linea:
                dentro = False
                continue
            if dentro or "~~" in linea:
                continue
            lineas_utiles.append(linea)
        citados = {
            m for m in _CITA.findall("\n".join(lineas_utiles))
            # Sólo lo que parece un identificador del proyecto.
            if ((m[0].isupper() and any(c.islower() for c in m)) or "_" in m)
            # AUD-312 — un token que **acaba** en `_` es un prefijo, no un
            # nombre. `06_TMX_SPEC.md` documenta la convención de capas —«las
            # de fondo llevan el prefijo `BG_`, las de primer plano `FG_`»— y
            # el orden de resolución por prefijo (`Death_`, `Solid_`,
            # `Hazard_`). Ninguno es un símbolo que pueda existir, así que
            # acusar al documento de citarlos es ruido puro.
            and not m.endswith("_")
        }
        inexistentes = sorted(citados - conocidos)
        huerfanos = sorted(
            m for m in citados
            if m in declarados
            and not (usados.get(m, set()) - declarados[m])
        )
        if inexistentes or huerfanos:
            informe.append({
                "documento": str(doc.relative_to(RAIZ)),
                "citados": len(citados),
                "no_existen": inexistentes,
                "sin_usos": huerfanos,
            })
    return informe


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    informe = auditar()
    if args.json:
        print(json.dumps(informe, ensure_ascii=False, indent=2))
        return 0

    total_inex = sum(len(f["no_existen"]) for f in informe)
    total_huer = sum(len(f["sin_usos"]) for f in informe)
    print(f"Documentos con hallazgos: {len(informe)}")
    print(f"  identificadores citados que no existen: {total_inex}")
    print(f"  identificadores citados sin ningún uso: {total_huer}\n")
    for f in informe:
        print(f"## {f['documento']}  ({f['citados']} citados)")
        if f["no_existen"]:
            print("   no existen:", ", ".join(f["no_existen"]))
        if f["sin_usos"]:
            print("   sin usos  :", ", ".join(f["sin_usos"]))
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
