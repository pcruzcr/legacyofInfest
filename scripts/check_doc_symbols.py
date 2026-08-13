#!/usr/bin/env python3
"""Comprueba que los símbolos que citan las especificaciones existan — AUD-365.

Por qué existe
==============

AUD-307 midió `docs/22_API_CONTRACTS.md` con un comprobador AST **de usar y
tirar**: de 381 símbolos citados, **50 no existían**. Se corrigieron trece
entradas y el comprobador se borró. O sea: el defecto se arregló y el guardián
que impedía que volviera, no.

Esto es el guardián. Es la misma familia que AUD-353 (el gate de ruff que sólo
se comprobaba por estar escrito en `ci.yml`) y AUD-356 (el `--json` que nadie
parseaba): una verificación que ocurre una vez no es una verificación, es una
foto.

Qué mira, y qué no
==================

Mira los identificadores citados **entre acentos graves** en los documentos de
especificación. Un nombre entre acentos graves en una spec es una promesa: dice
«esto existe en el código y se llama así».

No mira, y cada exclusión tiene su motivo:

* **Bloques de código cercados** (```). Ahí hay pseudocódigo, ejemplos de TMX,
  salidas de consola y órdenes de shell. Un `pip install` no es una promesa.
* **Bloques `<!-- cita-historica -->`**. Son citas de documentación vieja que se
  conservan **a propósito** para explicar qué se prometió y por qué no existe
  (AUD-150, AUD-307). Marcarlas obligaría a borrar la historia para callar al
  guardián, que es exactamente lo que no se quiere.
* **Palabras que no parecen identificadores**: prosa entre acentos graves,
  nombres de fichero, rutas, valores. El filtro es conservador a propósito: es
  mejor dejar pasar una promesa dudosa que inundar el informe. Un guardián
  ruidoso se desactiva (AUD-106).

Cómo se usa
===========

    python scripts/check_doc_symbols.py            # informe
    python scripts/check_doc_symbols.py --ci       # falla si hay promesas rotas

`tests/test_los_simbolos_de_las_specs_existen.py` lo ejecuta en cada suite.
"""
from __future__ import annotations

import argparse
import ast
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

RAIZ = Path(__file__).resolve().parent.parent
DOCS = RAIZ / "docs"

# Ejecutado como `python scripts/check_doc_symbols.py`, la raíz del
# repositorio no está en `sys.path` y los imports de `src` fallan. La
# primera versión los envolvía en un `except ImportError` que devolvía un
# conjunto vacío: el vocabulario de Tiled se perdía **en silencio** y el
# informe daba siete falsos positivos con toda naturalidad. Un respaldo
# mudo que convierte un fallo de entorno en un resultado plausible es peor
# que la excepción que evita.
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

#: Las especificaciones que prometen API. No entran las guías, el roadmap ni
#: los informes de auditoría: ésos hablan **de** la API, no la declaran.
SPECS: tuple[str, ...] = (
    "22_API_CONTRACTS.md",
    "04_PLAYER_SPEC.md",
    "05_ENEMY_SPEC.md",
    "09_HUD_SPEC.md",
    "17_BOSS_SPEC.md",
    "23_DATA_SCHEMAS.md",
)

#: De dónde salen los símbolos que existen. Entra `src/` **entero**,
#: incluidas las entregas: `17_BOSS_SPEC` promete `BossGavilan` y
#: `BossPaburu`, que viven en `src/stages/`. Esto sólo **lee** para
#: comprobar existencia, así que no roza la invariante 1 de CLAUDE.md — que
#: prohíbe refactorizar y relintear las entregas, no mirarlas.
ORIGENES = (RAIZ / "src",)

#: Un identificador de Python, posiblemente cualificado (`Clase.metodo`).
_CITA = re.compile(r"`([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*)`")

#: Palabras entre acentos graves que **no** son promesas de API. Cada una está
#: aquí porque se comprobó que su cita es de otra cosa: un tipo de objeto de
#: Tiled, una clave de un JSON de datos, un término del dominio o una palabra
#: reservada de Python.
NO_SON_API: frozenset[str] = frozenset({
    # Palabras de Python y tipos primitivos.
    "None", "True", "False", "int", "float", "str", "bool", "dict", "list",
    "tuple", "set", "bytes", "object", "Any", "type", "self", "cls", "id",
    "len", "min", "max", "abs", "round", "sum", "print", "range", "enumerate",
    "property", "staticmethod", "classmethod", "dataclass", "Enum", "Path",
    "NotImplementedError", "ValueError", "TypeError", "KeyError",
    "IndexError", "RuntimeError", "AttributeError", "FileNotFoundError",
    "DeprecationWarning",
    "Exception", "isinstance", "frozenset",
    # Capas de Tiled y vocabulario del formato: son nombres de datos, no de
    # código, y los vigilan `validate_tmx.py` y `check_tmx_coverage.py`.
    "Collision", "Objects", "Background", "Foreground", "Decoration",
    "Tiled", "TMX", "JSON", "GID", "gid", "px", "dt", "fps", "FPS",
    "png", "jpg", "ogg", "wav", "json", "tmx", "tsx", "csv", "yaml",
    "toml",
    "x", "y", "w", "h", "r", "g", "b", "a", "n", "i", "j", "k", "v",
    # Bibliotecas externas. Sus símbolos existen, pero no en este repositorio:
    # comprobarlos aquí sería comprobar pygame, que ya se comprueba solo.
    "Surface", "Rect", "Vector2", "Color", "Font", "Sound", "Group",
    "ndarray", "int32", "uint8", "float32", "float64", "array",
    "atan2", "sqrt", "sin", "cos", "hypot", "pi", "inf", "nan",
    "pytmx", "numpy", "pygame", "moderngl", "orjson", "sklearn", "cv2",
    "Pipeline", "string", "sine", "patrol", "bezier",
    "pytweening", "pydantic", "pydub", "lupa", "ModernGL",
    # Métodos y formatos de pygame (22_API_CONTRACTS los cita como
    # operaciones de superficie) y de pydantic: existen, pero no aquí.
    "subsurface", "blits", "blit", "ttf", "BaseModel",
    # Convenciones de nombres, no nombres.
    "snake_case", "PascalCase", "camelCase", "kebab_case",
    # Valores de datos y nombres de módulos de curso, no símbolos de código.
    "critical", "normal",
    "interpolacion", "ruido",
    # Clave del payload de BOSS_PHASE_CHANGED: dato, no símbolo.
    "new_max_health",
    # Nombres que 22_API_CONTRACTS cita para explicar que **no** existen
    # (nombres antiguos o de otro código), y el uniform de un sombreador.
    "_begin_phase_transition", "move_toward", "approach", "colorMatrix",
})


def simbolos_del_codigo() -> set[str]:
    """Todo nombre que el motor define: clases, funciones, atributos y constantes.

    Se recoge **plano**, sin el módulo ni la clase que lo contiene. Comprobar
    la ruta completa daría un guardián más estricto y también uno que falla
    cada vez que un símbolo se mueve de fichero, que en este repositorio pasa
    a menudo y a propósito (AUD-350, 351, 352). Lo que interesa es si el
    nombre **existe**; que esté en el sitio que dice el documento lo comprueba
    quien lea el documento.
    """
    encontrados: set[str] = set()
    for base in ORIGENES:
        for ruta in base.rglob("*.py"):
            if "__pycache__" in ruta.parts:
                continue
            try:
                arbol = ast.parse(ruta.read_text(encoding="utf-8"))
            except (SyntaxError, UnicodeDecodeError, OSError):
                continue
            for nodo in ast.walk(arbol):
                if isinstance(nodo, (ast.FunctionDef, ast.AsyncFunctionDef,
                                     ast.ClassDef)):
                    encontrados.add(nodo.name)
                    encontrados.update(
                        a.arg for a in getattr(nodo, "args", ast.arguments(
                            posonlyargs=[], args=[], kwonlyargs=[],
                            kw_defaults=[], defaults=[])).args)
                elif isinstance(nodo, ast.Name) and isinstance(nodo.ctx, ast.Store):
                    encontrados.add(nodo.id)
                elif isinstance(nodo, ast.Attribute) and isinstance(nodo.ctx, ast.Store):
                    encontrados.add(nodo.attr)
                elif isinstance(nodo, ast.arg):
                    encontrados.add(nodo.arg)
                elif isinstance(nodo, ast.AnnAssign) and isinstance(nodo.target, ast.Name):
                    encontrados.add(nodo.target.id)
            encontrados.add(ruta.stem)
    return encontrados


def vocabulario_de_tiled() -> set[str]:
    """Los tipos de objeto que el cargador reconoce, y las capas obligatorias.

    Una spec que cita `Walker`, `NextTrigger` o `PlayerSpawn` **no** está
    prometiendo una clase de Python: está nombrando un tipo de objeto de
    Tiled, que es dato. Existe, y quien lo vigila es `check_tmx_coverage.py`.
    Se lee del motor —no de una lista copiada aquí— para que añadir un tipo no
    obligue a tocar dos sitios.
    """
    from src.framework.entities import entity_factory
    from src.framework.stage.stage_data import REQUIRED_LAYERS
    from src.framework.stage.stage_loader import StageLoader
    from src.framework.stage.tmx_diagnostics import (
        COLLISION_OBJECT_TYPES,
        known_object_types,
    )

    entity_factory.ensure_registered()
    return (set(known_object_types(list(StageLoader._entity_registry)))
            | set(COLLISION_OBJECT_TYPES) | set(REQUIRED_LAYERS))


def vocabulario_de_audio() -> set[str]:
    """Las claves del banco de sonidos.

    `sfx_enemies_die_small` existe: es una **clave de dato**, no un símbolo de
    Python, y vive como cadena en la tabla de `stage_parts/sonido.py`. Se lee
    de ahí, que es su única fuente de verdad, en vez de copiarla: una lista
    duplicada aquí se desincronizaría al añadir un sonido.
    """
    import re as _re

    ruta = RAIZ / "src" / "framework" / "scenes" / "stage_parts" / "sonido.py"
    if not ruta.exists():
        return set()
    return set(_re.findall(r'"(sfx_[a-z0-9_]+)"',
                           ruta.read_text(encoding="utf-8")))


def vocabulario_de_herramientas() -> set[str]:
    """Los nombres de los guiones de `scripts/` y `tools/`.

    AUD-369 — una spec que cita `grade_boss` o `check_doc_symbols` nombra una
    **herramienta**, y existe. Se añaden sólo los nombres de fichero, no sus
    símbolos internos: una spec no promete la API interna de un guion del
    profesor, y meterla entera debilitaría la comprobación de lo que sí
    promete.
    """
    nombres: set[str] = set()
    for base in (RAIZ / "scripts", RAIZ / "tools"):
        if base.is_dir():
            nombres |= {r.stem for r in base.rglob("*.py")}
    return nombres


def _sin_ruido(texto: str) -> str:
    """Quita los bloques de código y las citas históricas."""
    texto = re.sub(r"```.*?```", "", texto, flags=re.DOTALL)
    texto = re.sub(r"<!-- cita-historica -->.*?<!-- /cita-historica -->", "",
                   texto, flags=re.DOTALL)
    return texto


def promesas(doc: Path) -> dict[str, int]:
    """Símbolo citado -> primera línea donde aparece."""
    bruto = doc.read_text(encoding="utf-8")
    limpio = _sin_ruido(bruto)
    #: Se recorre el texto limpio pero se buscan las líneas en el original,
    #: para que el informe apunte a donde el humano tiene que ir a mirar.
    lineas = bruto.splitlines()
    salida: dict[str, int] = {}
    for m in _CITA.finditer(limpio):
        cita = m.group(1)
        hoja = cita.split(".")[-1]
        if (hoja in NO_SON_API or len(hoja) < 3
                or (hoja.isupper() and "." not in cita)):
            # Los nombres de una sola pieza en MAYÚSCULAS son constantes de
            # eventos y de settings, que sí se comprueban aparte por sus
            # propias pruebas; aquí darían falsos positivos por las claves de
            # los diccionarios de datos.
            continue
        if hoja in salida:
            continue
        for n, linea in enumerate(lineas, 1):
            if f"`{cita}`" in linea:
                salida[hoja] = n
                break
    return salida


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ci", action="store_true",
                    help="salir con error si alguna spec promete lo que no existe")
    args = ap.parse_args()

    existen = (simbolos_del_codigo() | vocabulario_de_tiled()
               | vocabulario_de_audio() | vocabulario_de_herramientas())
    total = rotas = 0
    for nombre in SPECS:
        doc = DOCS / nombre
        if not doc.exists():
            print(f"  [FALTA] {nombre}")
            rotas += 1
            continue
        citas = promesas(doc)
        malas = {s: n for s, n in citas.items() if s not in existen}
        total += len(citas)
        rotas += len(malas)
        estado = "OK  " if not malas else "ROTO"
        print(f"  [{estado}] {nombre}: {len(citas)} símbolos citados, "
              f"{len(malas)} sin existir")
        for simbolo, linea in sorted(malas.items(), key=lambda kv: kv[1]):
            print(f"           {nombre}:{linea}  `{simbolo}`")

    print(f"\n  {total} símbolos citados en {len(SPECS)} especificaciones; "
          f"{rotas} no existen en el código.")
    if args.ci and rotas:
        print(
            "\nUna spec que promete un símbolo inexistente manda a quien la lee "
            "a programar contra algo que no está.\nO se corrige el documento, o "
            "se escribe el símbolo, o se mueve la cita a un bloque\n"
            "<!-- cita-historica --> explicando que no existe y por qué.",
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
