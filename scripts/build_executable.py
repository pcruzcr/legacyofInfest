"""
build_executable.py — empaqueta el juego en un ejecutable.

F3.3 — por qué hace falta
-------------------------
Para un no programador, «instala Python 3.12, luego `pip install -r
requirements.txt`, luego `python main.py`» ya es una barrera. Y el público al
que este proyecto puede llegar más allá del aula —otros profesores, un jurado
de proyecto fin de carrera, la familia de un estudiante— no va a cruzarla.

Este guion no sustituye al flujo de desarrollo: nadie que vaya a **modificar**
el juego debe usar el ejecutable. Sirve para enseñarlo.

Uso:
    pip install pyinstaller
    python scripts/build_executable.py
    python scripts/build_executable.py --limpiar     # borra dist/ y build/

El resultado queda en `dist/`. Un solo archivo en Windows, un directorio en
Linux y macOS: empaquetar en un archivo único multiplica el tiempo de arranque
porque descomprime en cada ejecución, y en un juego eso se nota.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

_RAIZ = Path(__file__).resolve().parent.parent

#: Carpetas que tienen que viajar con el ejecutable. Sin ellas el juego
#: arranca y no encuentra ni un mapa. `data/` entró con los catálogos de
#: texto (inventario, logros y bestiario): sin ellos la interfaz pierde los
#: nombres y el progreso de los jugadores.
DATOS = ("assets", "locale", "data", "student_templates")

#: Módulos que PyInstaller no detecta solo.
#:
#: Los tres primeros se importan de forma perezosa dentro de funciones —para
#: no pagarlos al arrancar— y el analizador estático de PyInstaller no los ve.
#: `numba` los carga por su cuenta en tiempo de ejecución.
OCULTOS = (
    "sklearn.neighbors", "sklearn.tree", "sklearn.pipeline",
    "sklearn.preprocessing", "scipy.ndimage", "numba",
    "pytmx.util_pygame", "pyscroll.data",
)


def comprobar_pyinstaller() -> bool:
    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        print("Falta PyInstaller. Instálalo con:")
        print("    pip install pyinstaller")
        return False
    return True


def construir(un_solo_archivo: bool) -> int:
    orden = [
        sys.executable, "-m", "PyInstaller",
        "--name", "LegacyOfInfest",
        "--noconfirm",
        "--windowed",           # sin consola: es un juego, no una herramienta
        str(_RAIZ / "main.py"),
    ]
    orden.append("--onefile" if un_solo_archivo else "--onedir")

    separador = ";" if sys.platform == "win32" else ":"
    for carpeta in DATOS:
        origen = _RAIZ / carpeta
        if origen.is_dir():
            orden += ["--add-data", f"{origen}{separador}{carpeta}"]
        else:
            print(f"  aviso: no existe {origen}, no se empaqueta")

    for modulo in OCULTOS:
        orden += ["--hidden-import", modulo]

    print("Ejecutando PyInstaller...\n  " + " ".join(orden[:6]) + " ...\n")
    return subprocess.call(orden, cwd=str(_RAIZ))


def main() -> int:
    parser = argparse.ArgumentParser(description="Empaqueta el juego")
    parser.add_argument("--limpiar", action="store_true",
                        help="borrar dist/ y build/ antes de empezar")
    parser.add_argument("--un-archivo", action="store_true",
                        help="forzar un ejecutable único (arranca más lento)")
    args = parser.parse_args()

    if args.limpiar:
        for d in ("dist", "build"):
            ruta = _RAIZ / d
            if ruta.exists():
                shutil.rmtree(ruta)
                print(f"borrado {d}/")

    if not comprobar_pyinstaller():
        return 1

    # En Windows un archivo único es lo que la gente espera recibir; en los
    # otros sistemas el coste de descomprimir en cada arranque no compensa.
    un_solo = args.un_archivo or sys.platform == "win32"
    codigo = construir(un_solo)
    if codigo == 0:
        print(f"\nListo. El ejecutable está en {_RAIZ / 'dist'}")
        print("Pruébalo antes de repartirlo: un empaquetado que no arranca en "
              "la máquina de destino es el fallo clásico de esta herramienta.")
    return codigo


if __name__ == "__main__":
    sys.exit(main())
