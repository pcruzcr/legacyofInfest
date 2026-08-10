"""AUD-363: dos guardias sobre la propia suite — el tiempo y las omisiones.

Por qué hacen falta
===================

Esta auditoría encontró tres veces el mismo defecto en sitios distintos: una
comprobación que **existe y no se ejecuta** (AUD-353, el gate de ruff), una que
**se ejecuta y no mira lo que dice** (AUD-356, el `--json` de los
calificadores) y una **protección sin llamantes** (AUD-355, la verja de
física). La suite tiene dos huecos de la misma familia, y son éstos.

**El tiempo.** La suite pasó de 342 s a 9.051 s en una sola ejecución de esta
sesión —por carga ajena, no por regresión— y nada lo habría dicho si hubiera
sido código. Una suite que se hace lenta poco a poco deja de ejecutarse antes
de cada commit, y entonces protege lo mismo que una que no existe.

**Las omisiones.** Siete pruebas se omiten en cada ejecución. Una omisión con
motivo es una decisión; una sin motivo es una prueba muerta que nadie va a
volver a mirar. Lo que se vigila no es que no haya omisiones —hay tres
legítimas por dependencia opcional— sino que **cada una diga por qué**.

Lo que NO se vigila, y por qué
------------------------------

No se pone un tope al **número** de omisiones. Un tope así se sube en cuanto
molesta, que es como se pierde la costumbre de mirarlo (el razonamiento de
AUD-106 con el lint de las entregas). Lo que importa es que cada omisión tenga
dueño, y eso sí se puede comprobar.
"""
from __future__ import annotations

import ast
import pathlib

import pytest

RAIZ = pathlib.Path(__file__).resolve().parent.parent
TESTS = RAIZ / "tests"

#: Presupuesto de la suite completa, en segundos. Generoso a propósito: la
#: medición limpia de esta máquina es ~342 s y el tope está en 2,6×. No busca
#: cazar una regresión de 20 s —eso lo taparía el ruido de una máquina
#: ocupada, como se midió el 2026-08-09 con la suite en 9.051 s por carga
#: ajena— sino el escalón que convierte la suite en algo que ya nadie corre
#: antes de commitear.
PRESUPUESTO_DE_SUITE_S: float = 900.0


class TestCadaOmisionTieneDueno:
    """Una omisión sin motivo escrito es una prueba muerta."""

    @staticmethod
    def _omisiones_sin_motivo(ruta: pathlib.Path) -> list[str]:
        try:
            arbol = ast.parse(ruta.read_text(encoding="utf-8"))
        except (SyntaxError, UnicodeDecodeError, OSError):
            return []
        fallos = []
        for nodo in ast.walk(arbol):
            if not isinstance(nodo, ast.Call):
                continue
            nombre = ""
            if isinstance(nodo.func, ast.Attribute):
                nombre = nodo.func.attr
            if nombre not in ("skip", "skipif", "xfail"):
                continue
            # `pytest.skip("motivo")` lleva el motivo en el primer argumento;
            # `skipif(cond, reason=...)` y `xfail(reason=...)`, por palabra
            # clave. Se acepta cualquiera de las dos formas: lo que se exige
            # es que haya texto, no dónde se pone.
            texto = ""
            if nombre == "skip" and nodo.args:
                texto = _literal(nodo.args[0])
            for kw in nodo.keywords:
                if kw.arg == "reason":
                    texto = _literal(kw.value)
            if not texto.strip():
                fallos.append(f"{ruta.name}:{nodo.lineno} {nombre}() sin motivo")
        return fallos

    def test_ninguna_omision_se_queda_sin_explicar(self) -> None:
        fallos = [
            f for ruta in sorted(TESTS.rglob("test_*.py"))
            for f in self._omisiones_sin_motivo(ruta)
        ]
        assert not fallos, (
            "una omisión sin motivo escrito es una prueba muerta que nadie va "
            "a volver a mirar:\n" + "\n".join(fallos)
        )


class TestElPresupuestoDeLaSuiteEstaDeclarado:
    """El tope existe, está en `conftest` y CI lo ejecuta.

    La medición la hace el gancho de `conftest.py`, que es el único sitio que
    sabe cuánto duró la sesión entera. Aquí sólo se comprueba que el gancho
    siga puesto: una prueba no puede medir la suite que la contiene.
    """

    def test_el_gancho_de_tiempo_sigue_en_conftest(self) -> None:
        texto = (TESTS / "conftest.py").read_text(encoding="utf-8")
        assert "pytest_sessionfinish" in texto, (
            "el gancho que mide la duración de la suite salió de conftest.py"
        )
        assert "PRESUPUESTO_DE_SUITE_S" in texto, (
            "conftest.py ya no consulta el presupuesto de esta suite"
        )

    def test_el_presupuesto_es_holgado_y_esta_razonado(self) -> None:
        """Un tope apretado se desactiva; uno holgado se respeta.

        La medición limpia ronda los 350 s. Si alguien baja esto a 400 s, la
        primera máquina ocupada lo pondrá en rojo sin que nadie haya roto
        nada, y a la tercera vez el guardia se quita.
        """
        assert PRESUPUESTO_DE_SUITE_S >= 600.0


def _literal(nodo: ast.AST) -> str:
    """El texto de un literal, o cadena vacía si no lo es.

    Un motivo construido en tiempo de ejecución (una f-string con el nombre
    del fichero que falta, por ejemplo) cuenta como motivo: lo que se persigue
    es la omisión muda, no la que se explica de otra forma.
    """
    if isinstance(nodo, ast.Constant) and isinstance(nodo.value, str):
        return nodo.value
    if isinstance(nodo, ast.JoinedStr):
        return "".join(
            v.value for v in nodo.values
            if isinstance(v, ast.Constant) and isinstance(v.value, str)
        ) or "f-string"
    return ""


@pytest.mark.parametrize("nombre", ["PRESUPUESTO_DE_SUITE_S"])
def test_el_modulo_publica_lo_que_conftest_importa(nombre: str) -> None:
    """`conftest.py` importa de aquí; que no se renombre sin darse cuenta."""
    assert nombre in globals()
