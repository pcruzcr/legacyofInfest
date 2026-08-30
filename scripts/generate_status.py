"""
AUD-643 — cifras vivas: genera docs/62_ESTADO_DEL_PROYECTO.md con datos medidos.

Uso:
    python scripts/generate_status.py           # imprime el informe
    python scripts/generate_status.py --write   # escribe en docs/62

Las cifras son:
- Número de tests recogidos (pytest --collect-only)
- GAPs resueltos y abiertos en KNOWN_GAPS.md
- Ficheros TMX en assets/maps/
- Líneas de código en src/
- Documentos en docs/
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


def contar_tests() -> int | None:
    """Número de tests que pytest recoge. None si pytest falla."""
    try:
        r = subprocess.run(
            [sys.executable, "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider"],
            cwd=str(RAIZ), capture_output=True, text=True, timeout=300,
        )
        for line in r.stdout.splitlines():
            if "tests collected" in line or " test collected" in line:
                return int(line.split()[0])
            if "error" in line.lower() and "collected" in line.lower():
                return None
        # Buscar el patrón "N tests collected"
        m = re.search(r"(\d+) tests? collected", r.stdout)
        return int(m.group(1)) if m else None
    except (subprocess.TimeoutExpired, Exception):
        return None


def contar_gaps() -> tuple[int, int]:
    """(resueltos, abiertos) en KNOWN_GAPS.md."""
    ruta = RAIZ / "KNOWN_GAPS.md"
    if not ruta.exists():
        return 0, 0
    texto = ruta.read_text(encoding="utf-8")
    resueltos = len(re.findall(r"## ~~\[GAP-\d+\]", texto))
    abiertos = len(re.findall(r"## \[GAP-\d+\]", texto))
    return resueltos, abiertos


def contar_tmx() -> int:
    """Ficheros TMX en assets/maps/."""
    maps = RAIZ / "assets" / "maps"
    if not maps.exists():
        return 0
    return len(list(maps.rglob("*.tmx")))


def contar_lineas_codigo() -> int:
    """Líneas de código Python en src/."""
    total = 0
    src = RAIZ / "src"
    for f in src.rglob("*.py"):
        if "__pycache__" in str(f):
            continue
        try:
            total += sum(1 for _ in open(f, encoding="utf-8", errors="replace"))
        except OSError:
            pass
    return total


def contar_docs() -> int:
    """Ficheros .md en docs/."""
    docs = RAIZ / "docs"
    if not docs.exists():
        return 0
    return len(list(docs.glob("*.md")))


def generar_informe() -> str:
    """Genera el informe de estado como markdown."""
    tests = contar_tests()
    resueltos, abiertos = contar_gaps()
    tmx = contar_tmx()
    loc = contar_lineas_codigo()
    docs = contar_docs()

    lineas = [
        "# Estado del proyecto",
        "",
        "_Generado automáticamente por `scripts/generate_status.py`_.",
        f"_Última regeneración: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')}_.",
        "",
        "| Métrica | Valor |",
        "|---------|-------|",
    ]

    if tests is not None:
        lineas.append(f"| Tests recogidos | {tests} |")
    else:
        lineas.append("| Tests recogidos | _no disponible_ |")

    lineas.extend([
        f"| GAPs resueltos | {resueltos} |",
        f"| GAPs abiertos | {abiertos} |",
        f"| Ficheros TMX | {tmx} |",
        f"| Líneas de código (src/) | {loc:,} |",
        f"| Documentos (docs/) | {docs} |",
    ])

    lineas.extend([
        "",
        "## Verificación CI",
        "",
        "| Check | Comando | Estado esperado |",
        "|-------|---------|----------------|",
        "| Ruff | `ruff check src/engine src/framework src/stages/stage0 tests/ scripts/ tools/` | 0 errores |",
        "| mypy | `mypy @mypy_scope.txt` | 0 issues |",
        "| Traducciones | `check_translations.py --ci` | exit 0 |",
        "| TMX coverage | `check_tmx_coverage.py --ci` | exit 0 |",
        "| Dependencies | `check_dependency_sync.py` | OK |",
        "| Import linter | `lint-imports` | 4 kept, 0 broken |",
    ])

    return "\n".join(lineas) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Genera el informe de estado del proyecto")
    parser.add_argument("--write", action="store_true", help="Escribe en docs/62_ESTADO_DEL_PROYECTO.md")
    args = parser.parse_args()

    informe = generar_informe()

    if args.write:
        destino = RAIZ / "docs" / "62_ESTADO_DEL_PROYECTO.md"
        destino.write_text(informe, encoding="utf-8")
        print(f"Escrito en {destino}")
    else:
        print(informe)

    return 0


if __name__ == "__main__":
    sys.exit(main())