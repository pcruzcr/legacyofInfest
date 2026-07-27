"""
Module: _cli_paths
System: scripts
Academic Unit: N/A

Rutas para mensajes de consola, sin reventar.

AUD-084 — por qué existe este módulo
------------------------------------
`grade_stage.py` y `validate_tmx.py` hacían ``ruta.relative_to(_PROJECT_ROOT)``
sólo para imprimir un nombre bonito. `Path.relative_to` lanza `ValueError` si
una ruta es relativa y la otra absoluta, así que ambas herramientas se caían
con un traceback en cuanto alguien escribía lo natural:

    python scripts/validate_tmx.py mi_escenario.tmx

Funcionaban únicamente con rutas absolutas, o a través de `--ci`, que pasa
rutas ya resueltas. Es decir: la herramienta que existe para que un estudiante
revise su propio mapa antes de entregarlo se rompía en el primer intento, y el
calificador del profesor también.

Un nombre de archivo en un mensaje no es motivo para terminar un programa. Si
no se puede acortar, se imprime tal cual.
"""
from __future__ import annotations

from pathlib import Path


def display_path(path: Path, root: Path) -> str:
    """Devuelve `path` relativa a `root` si se puede, y si no, tal cual.

    Acepta rutas relativas, absolutas, con enlaces simbólicos o fuera del
    proyecto por completo —un profesor puede tener las entregas en otra unidad
    de disco— y nunca lanza.
    """
    try:
        return str(Path(path).resolve().relative_to(Path(root).resolve()))
    except (ValueError, OSError):
        return str(path)
