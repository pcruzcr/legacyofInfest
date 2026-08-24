"""
Module: test_el_estado_de_los_jefes_es_real
System: tests
Academic Unit: N/A

AUD-311 — la tabla de «qué de esto existe hoy» de `17_BOSS_SPEC.md` envejeció.

Qué pasaba
==========
`17_BOSS_SPEC.md` describe cuatro jefes y unos cuarenta patrones de ataque, y
la mayoría es **diseño por construir** — eso está bien, es lo que una
especificación debe contener. Por eso AUD-150 le puso delante una sección 0 que
dice qué existe de verdad, para que nadie confunda las dos cosas.

Esa sección es lo que envejeció. Decía «tres clases de jefe y nueve patrones»
cuando ya había **cuatro clases y 17 patrones**: apareció `BossGavilan` y
`BossPaburu` pasó de una forma a cuatro. La tabla también daba al Gavilán por
inexistente y a Paburu por tener una sola forma.

Nadie lo notó porque el aviso *parecía* actualizado: llevaba su `AUD-150` y su
tono de medición. Un aviso de estado que no se comprueba envejece igual que el
documento al que precede, y encima con más autoridad.

Qué fija esta prueba
====================
Que los dos números de la cabecera —cuántas clases de jefe y cuántos patrones—
sean los que salen de `src/stages/`, contados con AST y no con una expresión
regular sobre el texto. Si alguien escribe un jefe nuevo, esta prueba señala la
línea exacta que hay que actualizar.

No comprueba la tabla fila a fila a propósito: esa tabla dice también **qué está
sólo diseñado**, y eso no se puede deducir del código — es justo la información
que un humano añade.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
SPEC = RAIZ / "docs" / "17_BOSS_SPEC.md"
STAGES = RAIZ / "src" / "stages"


def _arboles():
    for fichero in STAGES.rglob("*.py"):
        try:
            yield fichero, ast.parse(fichero.read_text(encoding="utf-8", errors="replace"))
        except SyntaxError:      # una entrega rota no debe tumbar esta prueba
            continue


@pytest.fixture(scope="module")
def clases_de_jefe() -> set[str]:
    encontradas = set()
    for _, arbol in _arboles():
        for nodo in ast.walk(arbol):
            if isinstance(nodo, ast.ClassDef) and any(
                (b.id if isinstance(b, ast.Name) else getattr(b, "attr", "")) == "BossBase"
                for b in nodo.bases
            ):
                encontradas.add(nodo.name)
    return encontradas


@pytest.fixture(scope="module")
def patrones() -> set[str]:
    """Los nombres que aparecen en algún `attack_patterns=[...]`."""
    encontrados: set[str] = set()
    for fichero in STAGES.rglob("*.py"):
        texto = fichero.read_text(encoding="utf-8", errors="replace")
        for bloque in re.findall(r"attack_patterns=\[([^\]]*)\]", texto):
            encontrados |= set(re.findall(r'"([A-Z_]+)"', bloque))
    return encontrados


@pytest.fixture(scope="module")
def cabecera() -> str:
    """La sección 0, que es donde vive el aviso de estado."""
    texto = SPEC.read_text(encoding="utf-8")
    return texto.split("## 1. Overview")[0]


def test_el_numero_de_clases_de_jefe_coincide(cabecera, clases_de_jefe) -> None:
    numeros = {int(n) for n in re.findall(r"\*\*(\d+) clases de jefe\*\*", cabecera)}
    numeros |= {
        {"tres": 3, "cuatro": 4, "cinco": 5, "seis": 6}[p]
        for p in re.findall(r"\*\*(tres|cuatro|cinco|seis) clases de jefe\*\*", cabecera)
    }

    assert numeros, "la sección 0 ya no dice cuántas clases de jefe hay"
    assert numeros == {len(clases_de_jefe)}, (
        f"la sección 0 de 17_BOSS_SPEC.md dice {numeros} clases de jefe y en "
        f"src/stages/ hay {len(clases_de_jefe)}: {sorted(clases_de_jefe)}"
    )


def test_el_numero_de_patrones_coincide(cabecera, patrones) -> None:
    numeros = {int(n) for n in re.findall(r"\*\*(\d+) patrones\*\*", cabecera)}

    assert numeros, "la sección 0 ya no dice cuántos patrones hay implementados"
    assert numeros == {len(patrones)}, (
        f"la sección 0 dice {numeros} patrones implementados y en src/stages/ "
        f"hay {len(patrones)}: {sorted(patrones)}"
    )


def test_los_jefes_citados_como_existentes_existen(cabecera, clases_de_jefe) -> None:
    """La tabla nombra la clase de cada jefe implementado. Si nombra una que no
    existe, el estudiante la busca y no la encuentra."""
    # `BossBase`, `BossPhase` y `BossSpawn` son la infraestructura del motor,
    # no jefes: viven en `src/framework` y en el cargador de TMX, así que
    # nunca aparecerán entre las subclases de `src/stages/`.
    INFRAESTRUCTURA = {"BossBase", "BossPhase", "BossSpawn", "BossRush", "BossKit"}
    citadas = set(re.findall(r"`(Boss[A-Z]\w+)`", cabecera)) - INFRAESTRUCTURA
    fantasma = sorted(citadas - clases_de_jefe)

    assert not fantasma, (
        f"la sección 0 nombra clases de jefe que no existen en src/stages/: "
        f"{fantasma}"
    )
