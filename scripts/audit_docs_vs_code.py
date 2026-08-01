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

    return definidos, usados, cadenas, declarados


def auditar() -> list[dict]:
    definidos, usados, cadenas, declarados = _inventario()
    conocidos = set(definidos) | cadenas | _BUILTINS | _CONVENCIONES

    informe: list[dict] = []
    for doc in sorted((RAIZ / "docs").rglob("*.md")):
        texto = doc.read_text(encoding="utf-8", errors="replace")
        citados = {
            m for m in _CITA.findall(texto)
            # Sólo lo que parece un identificador del proyecto.
            if (m[0].isupper() and any(c.islower() for c in m)) or "_" in m
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
