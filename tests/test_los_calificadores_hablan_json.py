"""AUD-356: `--json` de los calificadores tiene que ser JSON, y no lo era.

El hallazgo
===========

`CLAUDE.md` §2 y `docs/69_PROMPT_AUDITORIA_MAESTRO.md` §3 listan estas dos
órdenes entre los gates que CI ejecuta::

    python scripts/grade_stage.py assets/maps/ --json
    python scripts/grade_boss.py src/stages/boss_venado/boss_venado.py --json

Las dos imprimen el JSON **y después** el resumen humano de siempre::

    ...
      }
    ]

    ==================================================
      Total graded: 16
      Average grade: 79.9%
    ==================================================

Por la salida estándar, todo junto. El resultado es que la bandera que existe
para que otra herramienta lea la nota no sirve para eso:
`grade_stage.py assets/maps/ --json | jq` falla con *Extra data*, igual que
`json.loads`. Medido en el árbol del commit 3902137.

Por qué nadie se enteró
-----------------------

Porque el gate «pasa» igual: el CI mira el código de salida, que es 0, y el
resumen humano tapaba la avería justo donde se miraba. Es la misma familia que
AUD-124 (mypy configurado y sin ejecutar) y GAP-034 (el paso de ruff
comprobado por su presencia en `ci.yml` y no por su resultado): una
herramienta que parece verificar y no verifica. Aquí el `--json` era, en la
práctica, un `--json-y-además-otra-cosa`.

La corrección manda el resumen a **stderr** en modo `--json` en vez de
callarlo: quien califica a mano sigue viendo la media en su terminal, y quien
pipa la salida recibe un documento JSON y nada más. Callar el resumen habría
arreglado el parseo rompiendo el uso humano de la bandera, que es real —así se
saca la media de las 26 entregas.
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys

import pytest

RAIZ = pathlib.Path(__file__).resolve().parent.parent

#: Un solo mapa, no `assets/maps/` entero: la avería es de formato de salida y
#: se demuestra igual con un mapa que con dieciséis, en 1,7 s en vez de 20.
CASOS = [
    ("grade_stage.py", "assets/maps/stage0"),
    ("grade_boss.py", "src/stages/boss_venado/boss_venado.py"),
]


@pytest.mark.parametrize(("script", "objetivo"), CASOS)
def test_la_salida_de_json_se_puede_parsear(script: str, objetivo: str) -> None:
    proceso = subprocess.run(
        [sys.executable, f"scripts/{script}", objetivo, "--json"],
        capture_output=True, text=True, cwd=str(RAIZ), timeout=300, check=False,
    )
    assert proceso.returncode == 0, proceso.stderr[-2000:]

    datos = json.loads(proceso.stdout)
    assert isinstance(datos, list) and datos, "el JSON no trae ninguna nota"
    assert "percentage" in datos[0], datos[0].keys()


@pytest.mark.parametrize(("script", "objetivo"), CASOS)
def test_el_resumen_humano_no_se_pierde(script: str, objetivo: str) -> None:
    """No se arregla callando: la media sigue saliendo, por stderr."""
    proceso = subprocess.run(
        [sys.executable, f"scripts/{script}", objetivo, "--json"],
        capture_output=True, text=True, cwd=str(RAIZ), timeout=300, check=False,
    )
    assert "Average grade" in proceso.stderr, proceso.stderr[-2000:]


@pytest.mark.parametrize(("script", "objetivo"), CASOS)
def test_sin_json_el_resumen_sigue_donde_estaba(script: str, objetivo: str) -> None:
    """Quien califica a mano no nota el cambio: sin `--json`, todo en stdout."""
    proceso = subprocess.run(
        [sys.executable, f"scripts/{script}", objetivo],
        capture_output=True, text=True, cwd=str(RAIZ), timeout=300, check=False,
    )
    assert "Average grade" in proceso.stdout, proceso.stdout[-2000:]
