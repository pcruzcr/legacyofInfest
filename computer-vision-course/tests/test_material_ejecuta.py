"""
El criterio de terminado del curso: **el material se ejecuta**.

Esta es la prueba que separa «los ficheros están generados» de «el material
funciona». Un `.py` de ejemplo que no corre, o un notebook cuya tercera celda
falla, no es material docente: es un fichero.

Cómo se ejecutan los notebooks sin Jupyter
-------------------------------------------
El entorno del motor no trae `nbformat` ni `nbclient` —y meterlos como
dependencia del curso para poder probarlo sería empezar por el tejado—, así
que las celdas de código se extraen del JSON y se ejecutan en orden en un solo
espacio de nombres. Es exactamente lo que hace un kernel, menos las magias de
IPython.

Por eso los notebooks del curso **no usan `!pip install` ni `%cd`**: además de
no ser verificables, sólo funcionan en Colab. El arranque se hace en Python
normal, que corre en los dos sitios.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from cvcourse import engine_bridge

CURSO = Path(__file__).resolve().parent.parent
EJEMPLOS = sorted((CURSO / "examples").rglob("*.py"))
SOLUCIONES = sorted((CURSO / "solutions").rglob("*.py"))
NOTEBOOKS = sorted((CURSO / "notebooks").glob("*.ipynb"))


def _entorno_headless() -> dict[str, str]:
    import os

    return {
        **os.environ,
        "SDL_VIDEODRIVER": "dummy",
        "SDL_AUDIODRIVER": "dummy",
        "PYGAME_HIDE_SUPPORT_PROMPT": "1",
        "MPLBACKEND": "Agg",
    }


# ── Los ejemplos y las soluciones ─────────────────────────────────────────

@pytest.mark.parametrize("guion", EJEMPLOS + SOLUCIONES, ids=lambda p: p.stem)
def test_el_guion_se_ejecuta_sin_error(guion: Path):
    """Cada `.py` del material corre de principio a fin y devuelve 0.

    En un subproceso y no con `exec` a propósito: es la forma en que un
    estudiante lo va a lanzar, y así se detectan también los problemas de
    `sys.path`, de codificación de consola y de rutas relativas, que son
    justo los que más clase cuestan.
    """
    if not engine_bridge.hay_motor():
        pytest.skip("sin el repositorio del motor (Colab)")

    resultado = subprocess.run(
        [sys.executable, str(guion)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=_entorno_headless(),
        cwd=str(CURSO),
        timeout=600,
        check=False,
    )
    assert resultado.returncode == 0, (
        f"{guion.name} terminó con código {resultado.returncode}\n"
        f"--- stdout ---\n{resultado.stdout[-2000:]}\n"
        f"--- stderr ---\n{resultado.stderr[-2000:]}"
    )


@pytest.mark.parametrize("guion", EJEMPLOS + SOLUCIONES, ids=lambda p: p.stem)
def test_el_guion_no_lleva_rutas_absolutas(guion: Path):
    """La rúbrica penaliza las rutas absolutas; el material no puede tenerlas.

    Una ruta como `C:\\Users\\profesor\\...` convierte un ejemplo en algo que
    sólo corre en una máquina, y es el defecto más común del material docente
    heredado.
    """
    texto = guion.read_text(encoding="utf-8")
    for patron in ("C:\\Users", "C:/Users", "/home/", "/Users/"):
        assert patron not in texto, f"{guion.name} contiene una ruta absoluta: {patron}"


# ── Los notebooks ─────────────────────────────────────────────────────────

def _celdas_de_codigo(notebook: Path) -> list[str]:
    datos = json.loads(notebook.read_text(encoding="utf-8"))
    return [
        "".join(celda["source"])
        for celda in datos["cells"]
        if celda["cell_type"] == "code"
    ]


@pytest.mark.parametrize("notebook", NOTEBOOKS, ids=lambda p: p.stem)
def test_el_notebook_es_json_valido(notebook: Path):
    datos = json.loads(notebook.read_text(encoding="utf-8"))
    assert datos["nbformat"] == 4
    assert datos["cells"], "el notebook no tiene celdas"
    for i, celda in enumerate(datos["cells"]):
        assert celda["cell_type"] in ("code", "markdown"), f"celda {i} de tipo raro"
        assert isinstance(celda["source"], list), f"celda {i}: `source` debe ser lista de líneas"


@pytest.mark.parametrize("notebook", NOTEBOOKS, ids=lambda p: p.stem)
def test_el_notebook_no_usa_magias_de_ipython(notebook: Path):
    """`!pip install` y `%cd` sólo funcionan en Colab y no se pueden verificar.

    El arranque de los notebooks del curso se hace en Python normal
    precisamente para que corra en los dos sitios y esta suite pueda probarlo.
    """
    for i, codigo in enumerate(_celdas_de_codigo(notebook)):
        for linea in codigo.splitlines():
            desnuda = linea.strip()
            assert not desnuda.startswith(("!", "%")), (
                f"{notebook.name}, celda de código {i}: magia de IPython -> {desnuda!r}"
            )


@pytest.mark.parametrize("notebook", NOTEBOOKS, ids=lambda p: p.stem)
def test_el_notebook_se_ejecuta_de_principio_a_fin(notebook: Path):
    """Todas las celdas de código, en orden, en un solo espacio de nombres."""
    if not engine_bridge.hay_motor():
        pytest.skip("sin el repositorio del motor (Colab)")

    celdas = _celdas_de_codigo(notebook)
    assert celdas, f"{notebook.name} no tiene ninguna celda de código"

    guion = "\n\n".join(
        f"# ── celda {i} ──\n{codigo}" for i, codigo in enumerate(celdas)
    )
    resultado = subprocess.run(
        [sys.executable, "-c", guion],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=_entorno_headless(),
        cwd=str(CURSO / "notebooks"),
        timeout=600,
        check=False,
    )
    assert resultado.returncode == 0, (
        f"{notebook.name} falló al ejecutarse\n"
        f"--- stdout ---\n{resultado.stdout[-2000:]}\n"
        f"--- stderr ---\n{resultado.stderr[-3000:]}"
    )


@pytest.mark.parametrize("notebook", NOTEBOOKS, ids=lambda p: p.stem)
def test_el_notebook_trae_la_estructura_didactica(notebook: Path):
    """Las secciones que el curso exige a todo cuaderno.

    No es burocracia: un notebook sin preguntas de análisis se convierte en un
    ejercicio de copiar código, que es justo lo que este curso no quiere.
    """
    datos = json.loads(notebook.read_text(encoding="utf-8"))
    texto = "\n".join(
        "".join(c["source"]) for c in datos["cells"] if c["cell_type"] == "markdown"
    ).lower()

    for seccion in ("objetivos", "experimento", "reto", "preguntas de análisis",
                    "conclusiones", "bibliografía"):
        assert seccion in texto, f"{notebook.name} no tiene sección '{seccion}'"
