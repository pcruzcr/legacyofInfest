"""
Module: test_las_dos_tablas_de_enemigos
System: tests
Academic Unit: N/A

AUD-309 — `STAGE_CREATION.md` lista los arquetipos de enemigo dos veces.

Cómo se encontró
================
Al añadir `admite_bash` (AUD-305) se actualizó la tabla que produce
`scripts/generate_tmx_reference.py`, y `--check` dio «al día» — correctamente,
porque compara el bloque `GENERATED` contra el propio script.

Lo que no mira nadie es que el mismo documento trae, **doscientas líneas antes y
fuera del bloque**, una segunda tabla escrita a mano con los mismos arquetipos y
sus propiedades. Ésa se quedó sin `admite_bash`, y es la que un estudiante lee
primero: está en la sección de creación de spawns, donde uno va cuando está
poniendo enemigos.

Es el mismo modo de fallo que documenta AUD-182 sobre este mismo generador: un
gate que verifica que el documento coincida con una tabla, mientras la parte del
documento que nadie compara se va por su lado.

Qué fija esta prueba
====================
Que los arquetipos citados en las dos tablas sean los mismos, y que ninguna
propiedad publicada en la generada falte en la manual. Al revés no se exige: el
resumen puede citar una propiedad con menos detalle —la generada añade tipo y
valor por defecto entre paréntesis— pero no puede callarse una entera.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

DOC = Path(__file__).resolve().parent.parent / "docs" / "STAGE_CREATION.md"
INICIO = "<!-- BEGIN GENERATED: tipos de objeto -->"
FIN = "<!-- END GENERATED: tipos de objeto -->"


@pytest.fixture(scope="module")
def texto() -> str:
    return DOC.read_text(encoding="utf-8")


def _propiedades(celda: str) -> set[str]:
    """Los nombres entre backticks de una celda, sin los paréntesis de ayuda."""
    return set(re.findall(r"`([a-z_]+)`", celda))


def _tabla_manual(texto: str) -> dict[str, set[str]]:
    """La de «Enemy Spawns (Point)», anterior al bloque generado."""
    trozo = texto.split(INICIO)[0]
    filas = re.findall(r"^\|\s*`(\w+)`\s*\|([^|]*)\|([^|]*)\|\s*$",
                       trozo, re.M)
    return {nombre: _propiedades(req) | _propiedades(opt)
            for nombre, req, opt in filas}


def _tabla_generada(texto: str) -> dict[str, set[str]]:
    """La de «Arquetipos de enemigo», dentro del bloque."""
    dentro = texto.split(INICIO)[1].split(FIN)[0]
    seccion = dentro.split("### Arquetipos de enemigo")[1]
    seccion = seccion.split("\n### ")[0]
    filas = re.findall(r"^\|\s*`(\w+)`\s*\|([^|]*)\|\s*$", seccion, re.M)
    return {nombre: _propiedades(props) for nombre, props in filas}


class TestLasDosTablasNoSeContradicen:
    def test_las_dos_tablas_existen(self, texto) -> None:
        """Si alguien unifica el documento, esta prueba sobra y hay que
        borrarla — pero que sea una decisión, no un descuido."""
        assert _tabla_manual(texto), "no se encontró la tabla manual"
        assert _tabla_generada(texto), "no se encontró la tabla generada"

    def test_citan_los_mismos_arquetipos(self, texto) -> None:
        manual = set(_tabla_manual(texto))
        generada = set(_tabla_generada(texto))

        assert generada <= manual, (
            f"la tabla generada publica arquetipos que el resumen no menciona: "
            f"{sorted(generada - manual)}"
        )

    def test_ninguna_propiedad_publicada_falta_en_el_resumen(self, texto) -> None:
        """La que falló: `admite_bash` estaba en una tabla y no en la otra."""
        manual = _tabla_manual(texto)
        generada = _tabla_generada(texto)

        faltan = {
            nombre: sorted(props - manual.get(nombre, set()))
            for nombre, props in generada.items()
            if props - manual.get(nombre, set())
        }

        assert not faltan, (
            f"propiedades publicadas en la tabla generada y ausentes del "
            f"resumen que el estudiante lee primero: {faltan}"
        )
