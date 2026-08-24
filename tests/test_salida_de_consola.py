"""
Que las herramientas no se caigan por la codificación de la consola.

AUD-177 — el hallazgo
=====================
`scripts/mutation_check.py --ci` se abortó a mitad del primer módulo::

    src/engine/audio/mixer_buses.py  (tests/test_buses_de_audio.py)
    Traceback (most recent call last):
      File "scripts/mutation_check.py", line 310, in medir
        print(f"    muere {descripcion}", flush=True)
      File "encodings/cp1252.py", line 19, in encode
        return codecs.charmap_encode(input, self.errors, encoding_table)[0]
    UnicodeEncodeError: 'charmap' codec can't encode character '→'

La consola de Windows usa **cp1252** por defecto, y `→` no existe en cp1252.
No es un detalle cosmético: el proceso **muere**, así que la herramienta no
termina su trabajo. CI corre en Ubuntu, donde la salida es UTF-8, así que el
fallo no aparece allí — pero `CLAUDE.md` §2 dice que el toolchain de este
proyecto vive en el `.venv` de Windows, que es donde trabajan el profesor y
los estudiantes. La herramienta se rompía justo en la máquina para la que está
escrita.

Es el mismo modo de fallo que AUD-084 (`display_path`) y el reverso exacto de
AUD-166, donde la misma herramienta se rompía en Linux por usar separadores de
Windows: código que sólo se ejecuta en un sistema operativo acumula supuestos
sobre él.

Qué se vigila aquí
------------------
1. Todo script de `scripts/` y `tools/` que imprima un carácter fuera de
   cp1252 tiene que fijar su salida a UTF-8 antes de imprimirlo.
2. Que ningún fichero de texto del repositorio contenga U+FFFD, el carácter de
   reemplazo. Un U+FFFD guardado no es un problema de consola: es texto que ya
   se perdió al escribirlo (AUD-178).
"""
from __future__ import annotations

import ast
import pathlib

import pytest

RAIZ = pathlib.Path(__file__).resolve().parent.parent

#: Los dos directorios de herramientas que alguien ejecuta a mano desde una
#: consola. `src/` no entra: el juego no escribe por stdout.
HERRAMIENTAS: list[pathlib.Path] = [
    *sorted((RAIZ / "scripts").glob("*.py")),
    *sorted((RAIZ / "tools").glob("*.py")),
]


def _fuera_de_cp1252(texto: str) -> set[str]:
    fuera = set()
    for caracter in set(texto):
        if ord(caracter) < 128:
            continue
        try:
            caracter.encode("cp1252")
        except UnicodeEncodeError:
            fuera.add(caracter)
    return fuera


def _literales_de_cadena(ruta: pathlib.Path) -> str:
    """Sólo las cadenas del código. Un `→` en un comentario no imprime nada."""
    arbol = ast.parse(ruta.read_text(encoding="utf-8"))
    return "".join(
        nodo.value
        for nodo in ast.walk(arbol)
        if isinstance(nodo, ast.Constant) and isinstance(nodo.value, str)
    )


@pytest.mark.parametrize("ruta", HERRAMIENTAS, ids=lambda r: r.name)
def test_toda_herramienta_que_imprime_fuera_de_cp1252_fija_su_salida(
    ruta: pathlib.Path,
) -> None:
    fuera = _fuera_de_cp1252(_literales_de_cadena(ruta))
    if not fuera:
        return

    texto = ruta.read_text(encoding="utf-8")
    assert "reconfigure(encoding=" in texto, (
        f"{ruta.relative_to(RAIZ)} imprime {sorted(fuera)!r}, que no existe en "
        f"cp1252 —la codificación por defecto de la consola de Windows— y no "
        f"reconfigura su salida. El proceso muere con UnicodeEncodeError en "
        f"mitad del trabajo, no al final. Añade junto a los imports:\n\n"
        f"    if hasattr(sys.stdout, 'reconfigure'):\n"
        f"        sys.stdout.reconfigure(encoding='utf-8')"
    )


#: Ficheros de texto donde un U+FFFD sería texto ya perdido. Se excluyen los
#: dos que hablan *sobre* el carácter, que son éste y el informe de auditoría.
_EXCLUIDOS = {"test_salida_de_consola.py", "70_INFORME_DE_AUDITORIA_VIVO.md"}


def test_ningun_fichero_guarda_el_caracter_de_reemplazo() -> None:
    """AUD-178: `tools/generate_demo_stage0.py` decía «�Saltos verticales!».

    Era un `¡` guardado con la codificación equivocada. A diferencia de
    AUD-177, aquí no se cae nada: el cartel del nivel de demostración
    simplemente muestra un rombo con un interrogante a todo el que juegue, y
    el texto original ya no está en ninguna parte para recuperarlo.
    """
    culpables = []
    for carpeta in ("scripts", "tools", "src", "tests", "docs"):
        for ruta in sorted((RAIZ / carpeta).rglob("*")):
            if ruta.suffix not in {".py", ".md"} or ruta.name in _EXCLUIDOS:
                continue
            if "�" in ruta.read_text(encoding="utf-8", errors="replace"):
                culpables.append(str(ruta.relative_to(RAIZ)))

    assert not culpables, (
        "estos ficheros guardan U+FFFD, el carácter de reemplazo. No es un "
        "problema de consola: el texto original se perdió al escribirlos y "
        "hay que reponerlo a mano:\n  " + "\n  ".join(culpables)
    )
