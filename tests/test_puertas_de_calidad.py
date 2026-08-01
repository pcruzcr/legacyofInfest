"""
Las puertas de calidad del CI existen, apuntan a algo real y no retroceden.

AUD-124 y AUD-125 — el hallazgo
================================
Dos herramientas estaban **declaradas y no ejecutándose**:

* `mypy` tenía once líneas de configuración en `pyproject.toml` y **ningún
  paso de CI**. Un tipado que nadie comprueba es documentación con sintaxis de
  código, y envejece igual de mal. Las tres primeras cosas que encontró al
  ejecutarlo por fin eran anotaciones que mentían: un `dict[str, int]` que
  guardaba una lista, un atributo sin anotar que mypy infería como `None`, y
  un caché cuya clave declarada era un entero y en realidad era una tupla.
* No había **ningún** escaneo de vulnerabilidades. Ni `pip-audit`, ni
  Dependabot, ni CodeQL, sobre quince dependencias que arrastran numpy, scipy,
  scikit-learn, opencv y pygame.

Es la misma familia de defecto que este proyecto lleva un mes persiguiendo:
algo correcto, escrito, y que nunca se ejecuta. Lo que cambia es que aquí el
huérfano era una **herramienta de calidad**, y esas fallan en silencio por
partida doble — no sólo no protegen, sino que su presencia en el repositorio
hace creer que sí.

Qué vigila esta suite
---------------------
Que las puertas sigan enchufadas. No comprueba que el código pase mypy —eso lo
hace el propio CI, que tiene tiempo para ello— sino que el paso exista, que la
lista de paquetes sea real y que nadie la vacíe para poner el CI en verde.
"""
from __future__ import annotations

import pathlib

import pytest

RAIZ = pathlib.Path(__file__).resolve().parent.parent
CI = RAIZ / ".github" / "workflows" / "ci.yml"
ALCANCE = RAIZ / "mypy_scope.txt"

#: Tamaño del trinquete cuando se creó. Sólo puede subir.
#:
#: Un número escrito a mano es exactamente lo que este proyecto ha estado
#: retirando de otros sitios, pero aquí es el punto: la prueba **tiene** que
#: fallar cuando alguien quita un paquete, y para eso hace falta recordar
#: cuántos había. Subirlo al añadir es parte del trabajo de añadir.
PAQUETES_MINIMOS = 2


def _paquetes_del_alcance() -> list[str]:
    lineas = ALCANCE.read_text(encoding="utf-8").splitlines()
    return [
        linea.strip() for linea in lineas
        if linea.strip() and not linea.lstrip().startswith("#")
    ]


class TestElComprobadorDeTipos:
    def test_el_fichero_de_alcance_existe(self) -> None:
        assert ALCANCE.exists(), (
            "falta mypy_scope.txt: sin él, el paso de CI comprueba la cadena "
            "vacía y pasa siempre"
        )

    def test_el_alcance_no_esta_vacio(self) -> None:
        paquetes = _paquetes_del_alcance()
        assert paquetes, (
            "el alcance quedó vacío. `mypy` sobre nada devuelve éxito, así que "
            "el CI seguiría en verde sin comprobar una sola línea"
        )

    def test_el_trinquete_no_retrocede(self) -> None:
        paquetes = _paquetes_del_alcance()
        assert len(paquetes) >= PAQUETES_MINIMOS, (
            f"el alcance bajó de {PAQUETES_MINIMOS} a {len(paquetes)} paquetes. "
            f"Si un paquete dejó de pasar mypy, se arregla el paquete; sacarlo "
            f"de la lista es apagar el detector de humo porque suena"
        )

    @pytest.mark.parametrize("indice", range(PAQUETES_MINIMOS))
    def test_cada_paquete_del_alcance_existe_de_verdad(self, indice) -> None:
        """Una ruta mal escrita hace que mypy no compruebe nada y no avise."""
        paquetes = _paquetes_del_alcance()
        ruta = RAIZ / paquetes[indice]
        assert ruta.exists(), (
            f"«{paquetes[indice]}» está en el alcance y no existe en el árbol"
        )

    def test_el_alcance_no_incluye_codigo_de_estudiantes(self) -> None:
        """`src/stages/` se califica con la rúbrica, no con el motor."""
        malos = [p for p in _paquetes_del_alcance() if p.startswith("src/stages")]
        assert not malos, (
            f"el alcance incluye entregas de estudiantes: {malos}. Se califican "
            f"con `grade_stage.py`, no con el comprobador de tipos del motor"
        )

    def test_el_ci_ejecuta_mypy(self) -> None:
        texto = CI.read_text(encoding="utf-8")
        assert "mypy" in texto, (
            "el paso de mypy desapareció del CI. La configuración en "
            "pyproject.toml volvería a ser decorativa, que es como estaba"
        )
        assert "mypy_scope.txt" in texto, (
            "el CI ejecuta mypy pero ya no lee el alcance: o comprueba de más "
            "y sale rojo siempre, o de menos y no comprueba nada"
        )


class TestElEscaneoDeVulnerabilidades:
    def test_el_ci_audita_las_dependencias(self) -> None:
        texto = CI.read_text(encoding="utf-8")
        assert "pip-audit" in texto, (
            "no hay escaneo de vulnerabilidades. Quince dependencias que "
            "arrastran numpy, scipy, scikit-learn, opencv y pygame, y un CVE "
            "en cualquiera pasaría desapercibido"
        )

    def test_dependabot_esta_configurado(self) -> None:
        """`pip-audit` sólo mira cuando alguien empuja código.

        Entre semestres nadie toca el repositorio durante meses, que es
        precisamente cuando un CVE tiene tiempo de envejecer sin que nadie
        mire.
        """
        cfg = RAIZ / ".github" / "dependabot.yml"
        assert cfg.exists(), "falta .github/dependabot.yml"
        texto = cfg.read_text(encoding="utf-8")
        assert "package-ecosystem" in texto and "pip" in texto


class TestLasPuertasQueYaExistian:
    """Regresión de las que este proyecto ya se ganó a pulso.

    `ruff` sobre `src/stages/` no entra en el CI a propósito (AUD-106) y esa
    exclusión también hay que protegerla: alguien con buena intención podría
    ampliarla a todo el árbol y dejar el CI permanentemente rojo, que es como
    se pierde la costumbre de mirarlo.
    """

    def test_ruff_sigue_en_el_ci(self) -> None:
        assert "ruff check" in CI.read_text(encoding="utf-8")

    def test_ruff_no_se_aplica_a_las_entregas(self) -> None:
        """Se miran las órdenes, no los comentarios.

        La primera versión buscaba la cadena en el fichero entero y falló al
        primer intento: el CI **documenta** en un comentario cómo revisar las
        entregas al calificar (`ruff check src/stages/`), y la prueba lo leyó
        como si fuera la orden. Buscar texto en un fichero de configuración sin
        distinguir código de comentario es la misma clase de error que
        comparar cifras dentro de un bloque de código.
        """
        ordenes = "\n".join(
            linea for linea in CI.read_text(encoding="utf-8").splitlines()
            if not linea.lstrip().startswith("#")
        )
        assert "ruff check src/stages/" not in ordenes, (
            "el CI lintea las entregas de los estudiantes: traen 164 avisos "
            "de estilo y el CI quedaría rojo para siempre"
        )

    def test_los_validadores_siguen_en_el_ci(self) -> None:
        texto = CI.read_text(encoding="utf-8")
        for validador in ("check_dependency_sync.py", "validate_tmx.py"):
            assert validador in texto, f"{validador} salió del CI"
