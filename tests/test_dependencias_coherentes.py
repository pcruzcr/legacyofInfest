"""
Lo que el proyecto promete instalar y lo que de verdad puede instalarse.

AUD-173 — el hallazgo
=====================
`pyproject.toml` declaraba `numpy>=1.26,<2` y `.github/workflows/ci.yml` corría
la matriz **3.11 / 3.12 / 3.13**. Las dos cosas no pueden ser ciertas a la vez:
la última numpy 1.x es la 1.26.4 y sus ruedas llegan hasta Python 3.12. En
3.13 no hay ninguna, así que `pip install -e ".[dev]"` intentaba compilar numpy
desde el código fuente y fallaba antes de ejecutar una sola prueba.

Un tercio de la matriz del CI no podía ni instalar el proyecto. Es el mismo
modo de fallo que AUD-010 —una promesa de compatibilidad que nadie había
ejecutado— sólo que esta vez la promesa estaba en el fichero de dependencias.

De dónde salía el tope
----------------------
De `numba`, que es un **extra opcional**: numba 0.60 exigía `numpy<2.1`. Un
acelerador que el juego no necesita estaba fijando el suelo de todo el
proyecto. La corrección fue subir `numba` a 0.62 dentro de su extra y quitar
el tope de la base.

Qué se vigila aquí
------------------
Tres cosas, y ninguna necesita red:

1. Que la matriz del CI y `requires-python` digan lo mismo.
2. Que ningún tope superior (`<`) viva en las dependencias base sin una razón
   escrita. Un tope sin porqué es una bomba de relojería: nadie recuerda si
   sigue haciendo falta, y quitarlo da miedo.
3. Que `requirements.txt` y `pyproject.toml` no sólo compartan **nombres**
   —eso ya lo comprueba `scripts/check_dependency_sync.py`— sino también los
   **rangos de versión**. Antes de esto, `requirements.txt` podía decir
   `numpy>=1.26,<2` mientras `pyproject.toml` decía otra cosa, y el CI seguía
   en verde.
"""
from __future__ import annotations

import pathlib
import re

import pytest

RAIZ = pathlib.Path(__file__).resolve().parent.parent
PYPROJECT = RAIZ / "pyproject.toml"
REQUIREMENTS = RAIZ / "requirements.txt"
CI = RAIZ / ".github" / "workflows" / "ci.yml"

#: Topes superiores tolerados en las dependencias base, con su razón.
#:
#: Añadir una entrada es afirmar «esta biblioteca se rompe por encima de esta
#: versión, y aquí está el porqué». Sin entrada, la prueba falla — que es lo
#: contrario de lo que pasaba con `numpy<2`, que llevaba meses sin dueño.
TOPES_JUSTIFICADOS: dict[str, str] = {}

#: Suelos que existen por seguridad, no por API: `nombre -> (versión, razón)`.
#:
#: AUD-176. `pip-audit` es el gate que detecta esto, pero corre con
#: `continue-on-error: true` a propósito (AUD-125) y sólo mira lo que hay
#: instalado *hoy*. Nada impedía que el manifiesto siguiera permitiendo la
#: versión vulnerable: quien instalara mañana con un resolutor distinto se la
#: llevaba otra vez. El suelo lo arregla en el manifiesto, que es donde vive
#: la promesa.
#:
#: Una entrada aquí se retira cuando la razón deja de aplicar, no cuando
#: molesta.
SUELOS_POR_SEGURIDAD: dict[str, tuple[str, str]] = {
    "pillow": (
        "12.3.0",
        "Pillow 12.2.0 y anteriores acumulan 10 vulnerabilidades publicadas "
        "(PYSEC-2026-2253..2257, 3451..3454, 3493..3496), todas corregidas en "
        "12.3.0. El proyecto la usa para decodificar imágenes en el pipeline "
        "de assets (tools/pixel_asset_generator.py, scripts/collect_palettes.py "
        "y las herramientas de tileset de los escenarios), o sea sobre ficheros "
        "que llegan de fuera: es exactamente la superficie que estos fallos "
        "atacan. El suelo `>=10.0` permitía instalar cualquiera de ellas.",
    ),
}


def _texto_pyproject() -> str:
    return PYPROJECT.read_text(encoding="utf-8")


def _sin_comentario(linea: str) -> str:
    return linea.split("#", 1)[0].strip()


def _dependencias_base() -> list[str]:
    """Las cadenas de `[project].dependencies`, sin comentarios.

    Se lee con expresiones regulares y no con `tomllib` para que la prueba
    funcione igual en 3.11 y en cualquier intérprete donde alguien la ejecute
    a mano; el bloque tiene una forma fija y muy simple.
    """
    texto = _texto_pyproject()
    bloque = re.search(r"^dependencies\s*=\s*\[(.*?)^\]", texto, re.S | re.M)
    assert bloque, "pyproject.toml ya no declara [project].dependencies"
    # Los comentarios del bloque citan órdenes entrecomilladas —`pip install
    # -e ".[dev]"`— y sin quitarlos primero se leerían como dependencias.
    util = "\n".join(_sin_comentario(linea) for linea in bloque.group(1).splitlines())
    return re.findall(r'"([^"]+)"', util)


def _dependencias_requirements() -> list[str]:
    lineas = []
    for cruda in REQUIREMENTS.read_text(encoding="utf-8").splitlines():
        linea = _sin_comentario(cruda)
        if linea and not linea.startswith("-"):
            lineas.append(linea)
    return lineas


def _canonico(spec: str) -> str:
    nombre = re.match(r"[A-Za-z0-9][A-Za-z0-9._-]*", spec)
    assert nombre, f"especificador ilegible: {spec!r}"
    return re.sub(r"[-_.]+", "-", nombre.group(0)).lower()


def _rango(spec: str) -> str:
    """El especificador sin el nombre y sin espacios: `numpy>=1.26` -> `>=1.26`."""
    return re.sub(r"\s+", "", spec[len(re.match(r"[A-Za-z0-9][A-Za-z0-9._-]*", spec).group(0)):])


class TestLaMatrizDelCIYElSueloDePython:
    def test_requires_python_declara_un_suelo(self) -> None:
        assert re.search(r'requires-python\s*=\s*">=3\.\d+"', _texto_pyproject()), (
            "pyproject.toml ya no declara un suelo de Python legible"
        )

    def test_todas_las_versiones_de_la_matriz_cumplen_el_suelo(self) -> None:
        suelo = re.search(r'requires-python\s*=\s*">=3\.(\d+)"', _texto_pyproject())
        assert suelo, "no se pudo leer requires-python"
        minimo = int(suelo.group(1))

        matriz = re.search(r'python-version:\s*\[([^\]]+)\]', CI.read_text(encoding="utf-8"))
        assert matriz, "ci.yml ya no declara una matriz de versiones de Python"
        versiones = [int(menor) for menor in re.findall(r'"3\.(\d+)"', matriz.group(1))]
        assert versiones, "la matriz del CI está vacía"

        bajas = [f"3.{v}" for v in versiones if v < minimo]
        assert not bajas, (
            f"el CI corre en {bajas} y pyproject.toml exige >=3.{minimo}: una de "
            f"las dos afirmaciones es falsa"
        )

    def test_el_suelo_de_python_se_cubre_en_la_matriz(self) -> None:
        """Si nadie ejecuta el intérprete mínimo, el mínimo es una suposición."""
        suelo = re.search(r'requires-python\s*=\s*">=3\.(\d+)"', _texto_pyproject())
        matriz = re.search(r'python-version:\s*\[([^\]]+)\]', CI.read_text(encoding="utf-8"))
        versiones = {int(v) for v in re.findall(r'"3\.(\d+)"', matriz.group(1))}
        assert int(suelo.group(1)) in versiones, (
            f"pyproject.toml declara >=3.{suelo.group(1)} y el CI no lo ejecuta: "
            f"corre {sorted(versiones)}"
        )


class TestLosTopesDeVersion:
    @pytest.mark.parametrize("spec", _dependencias_base(), ids=_canonico)
    def test_ningun_tope_superior_sin_razon_escrita(self, spec: str) -> None:
        """AUD-173: `numpy<2` llevaba meses sin dueño y rompía Python 3.13."""
        if "<" not in spec:
            return
        nombre = _canonico(spec)
        assert nombre in TOPES_JUSTIFICADOS, (
            f"`{spec}` pone un tope superior y no está en TOPES_JUSTIFICADOS. "
            f"Un tope sin porqué nadie se atreve a quitarlo después: si hace "
            f"falta, escribe la razón; si no, quítalo. Fue lo que dejó a "
            f"Python 3.13 sin poder instalar el proyecto."
        )

    def test_ningun_tope_justificado_sobra(self) -> None:
        base = {_canonico(s) for s in _dependencias_base() if "<" in s}
        huerfanos = sorted(set(TOPES_JUSTIFICADOS) - base)
        assert not huerfanos, (
            f"estos topes ya no existen en pyproject.toml; retíralos de "
            f"TOPES_JUSTIFICADOS: {huerfanos}"
        )


class TestLosSuelosDeSeguridad:
    """Un suelo demasiado bajo es una vulnerabilidad que el manifiesto permite."""

    @staticmethod
    def _numeros(version: str) -> tuple[int, ...]:
        return tuple(int(p) for p in re.findall(r"\d+", version))

    @pytest.mark.parametrize("spec", _dependencias_base(), ids=_canonico)
    def test_el_suelo_declarado_deja_fuera_las_versiones_vulnerables(
        self, spec: str,
    ) -> None:
        registro = SUELOS_POR_SEGURIDAD.get(_canonico(spec))
        if registro is None:
            return
        minimo, razon = registro

        declarado = re.search(r">=\s*([0-9][0-9.]*)", _rango(spec))
        assert declarado, (
            f"`{spec}` no declara un suelo `>=`, así que pip puede resolver "
            f"cualquier versión, incluidas las vulnerables. {razon}"
        )
        assert self._numeros(declarado.group(1)) >= self._numeros(minimo), (
            f"`{spec}` permite instalar versiones por debajo de {minimo}.\n\n{razon}"
        )

    def test_ningun_suelo_de_seguridad_apunta_a_una_dependencia_retirada(self) -> None:
        base = {_canonico(s) for s in _dependencias_base()}
        huerfanos = sorted(set(SUELOS_POR_SEGURIDAD) - base)
        assert not huerfanos, (
            f"SUELOS_POR_SEGURIDAD nombra dependencias que ya no se declaran: "
            f"{huerfanos}. Una regla que vigila algo que no existe da una "
            f"sensación de cobertura que no es real"
        )

    def test_cada_suelo_de_seguridad_explica_su_porque(self) -> None:
        for nombre, (version, razon) in SUELOS_POR_SEGURIDAD.items():
            assert re.fullmatch(r"\d+(\.\d+)*", version), (
                f"{nombre}: '{version}' no es una versión legible"
            )
            assert len(razon) > 80, (
                f"{nombre}: la razón es demasiado corta para que alguien decida "
                f"dentro de un año si el suelo sigue haciendo falta"
            )


class TestRequirementsYPyprojectDicenLoMismo:
    """`check_dependency_sync.py` compara nombres. Esto compara los rangos."""

    def test_los_rangos_de_version_coinciden(self) -> None:
        en_pyproject = {_canonico(s): _rango(s) for s in _dependencias_base()}
        en_requirements = {_canonico(s): _rango(s) for s in _dependencias_requirements()}

        diferencias = [
            f"{nombre}: pyproject dice `{rango}` y requirements.txt `{en_requirements[nombre]}`"
            for nombre, rango in sorted(en_pyproject.items())
            if nombre in en_requirements and rango != en_requirements[nombre]
        ]
        assert not diferencias, (
            "los dos manifiestos declaran rangos distintos para la misma "
            "biblioteca:\n  " + "\n  ".join(diferencias)
            + "\n\npyproject.toml es la fuente de verdad; requirements.txt se "
              "genera de él."
        )

    def test_no_falta_ninguna_dependencia_en_requirements(self) -> None:
        faltan = sorted(
            {_canonico(s) for s in _dependencias_base()}
            - {_canonico(s) for s in _dependencias_requirements()}
        )
        assert not faltan, (
            f"requirements.txt no lista {faltan}; seguir el README con ese "
            f"fichero daría una instalación que no arranca (AUD-007)"
        )
