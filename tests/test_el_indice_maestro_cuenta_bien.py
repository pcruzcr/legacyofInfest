"""AUD-365: el índice maestro dice cuántos documentos hay, y acierta.

El hallazgo (P3 de `docs/89`)
=============================

El encabezado de `docs/00_MASTER_INDEX.md` decía **69 documentos** y la tabla
tenía **75 filas**. Llevaba meses así y nadie sabía cuál de los dos números
era el bueno, porque no lo era ninguno: eran **dos formas distintas de contar**
sin declarar cuál se usaba.

Medido:

* 71 ficheros `.md` en `docs/`
* 70 de ellos con fila en la tabla — falta sólo el propio índice, que no se
  indexa a sí mismo
* 5 filas más para ficheros de la raíz (`README`, `CLAUDE`, `CONTRIBUTING`,
  `CHANGELOG`, `KNOWN_GAPS`), que también son documentación

70 + 5 = 75 filas. No sobraba ninguna ni faltaba ningún documento: sobraba la
cifra del encabezado, que nadie recontaba.

Por qué es una prueba y no una corrección
=========================================

La invariante 6 de `CLAUDE.md` lo dice sin rodeos: *«los números en la
documentación son verificables o no se escriben»*. Corregir 69 → 71 sin más
deja el mismo defecto para dentro de dos documentos nuevos. Lo que cierra el
agujero es que la cifra se recuente sola.

Es exactamente el mismo mecanismo que `test_documentacion_bilingue` usa con el
recuento de pruebas del README, y por el mismo motivo.
"""
from __future__ import annotations

import pathlib
import re

RAIZ = pathlib.Path(__file__).resolve().parent.parent
INDICE = RAIZ / "docs" / "00_MASTER_INDEX.md"

#: Documentación que vive en la raíz por convención (la ve quien clona) y que
#: también tiene fila en el índice. El índice las escribe con `../` porque
#: sus enlaces son relativos a `docs/`, y la etiqueta es el propio destino.
DE_LA_RAIZ = ("../README.md", "../CLAUDE.md", "../CONTRIBUTING.md",
              "../CHANGELOG.md", "../KNOWN_GAPS.md")


def _filas() -> list[str]:
    texto = INDICE.read_text(encoding="utf-8")
    return [m.group(1) for m in re.finditer(r"^\| \[`([^`]+)`\]\(", texto, re.M)]


def test_la_cifra_del_encabezado_es_la_real() -> None:
    texto = INDICE.read_text(encoding="utf-8")
    m = re.search(r"\*\*Documentos:\*\*\s*(\d+)\s+en\s+`docs/`", texto)
    assert m, "el encabezado ya no declara cuántos documentos hay en docs/"
    declarados = int(m.group(1))
    reales = len(list((RAIZ / "docs").glob("*.md")))
    assert declarados == reales, (
        f"el índice dice {declarados} documentos y en docs/ hay {reales}. "
        f"Es el defecto P3: dos formas de contar sin decir cuál"
    )


def test_todo_documento_de_docs_tiene_fila_menos_el_indice() -> None:
    """«Si un documento no aparece aquí, está mal puesto» — el índice, §1."""
    en_tabla = set(_filas())
    sin_fila = [
        p.name for p in sorted((RAIZ / "docs").glob("*.md"))
        if p.name not in en_tabla and p.name != INDICE.name
    ]
    assert not sin_fila, (
        "documentos en docs/ sin fila en el índice maestro, que se declara "
        f"lista autoritativa: {sin_fila}"
    )


def test_ninguna_fila_apunta_a_un_documento_que_no_existe() -> None:
    faltan = []
    for nombre in _filas():
        destino = ((RAIZ / nombre[3:]) if nombre in DE_LA_RAIZ
                   else (RAIZ / "docs" / nombre))
        if not destino.exists():
            faltan.append(nombre)
    assert not faltan, f"filas del índice que apuntan a la nada: {faltan}"


def test_las_cuentas_cuadran() -> None:
    """70 documentos + 5 ficheros de la raíz = las 75 filas de la tabla.

    La aritmética explícita, que es lo que faltaba: con ella, un desajuste
    dice **dónde** está en vez de sólo que existe.
    """
    filas = _filas()
    de_docs = [f for f in filas if f not in DE_LA_RAIZ]
    de_raiz = [f for f in filas if f in DE_LA_RAIZ]
    en_docs = len(list((RAIZ / "docs").glob("*.md")))

    assert len(de_raiz) == len(DE_LA_RAIZ), de_raiz
    assert len(de_docs) == en_docs - 1, (
        f"{len(de_docs)} filas de docs/ frente a {en_docs - 1} documentos "
        f"indexables ({en_docs} ficheros menos el propio índice)"
    )
    assert len(filas) == len(de_docs) + len(de_raiz)
