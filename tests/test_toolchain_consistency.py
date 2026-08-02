"""
Module: test_toolchain_consistency
System: tests
Academic Unit: N/A

Impide que las herramientas del proyecto vuelvan a contradecirse entre sí.

Por qué existe
--------------
El editor reportaba sobre `src/engine/core/save_data.py`::

    E0401  Unable to import 'orjson'                (Pylint)
           Import "pydantic" could not be resolved  (Pylance)
    C0114  Missing module docstring   (en un archivo que empieza con docstring)
    C0116  Missing function docstring (en métodos que sí lo tienen)

Ninguno de los cuatro señalaba un defecto del código:

* Los dos primeros venían de analizar con el Python global en lugar del
  `.venv` del proyecto, donde orjson y pydantic **sí** están instalados.
* Los otros dos venían de Pylint sin configurar, cuyos valores por defecto
  piden docstring en cada método público — algo que ruff, el linter que sí
  corre en CI, no exige. Además apuntaban a líneas que ya no se corresponden
  con el archivo, señal de que eran diagnósticos caducados.

La lección no es "ignorar al linter": es que un repositorio con varios
linters que piden cosas distintas produce avisos que nadie va a atender, y
avisos que nadie atiende enseñan a ignorar todos los avisos. Estas pruebas
fijan que las tres configuraciones coincidan y que las dependencias
declaradas sean las que el juego comprueba al arrancar.
"""
from __future__ import annotations

import ast
import configparser
import re
from pathlib import Path

import pytest

try:  # Python 3.11+, que es lo que el proyecto declara soportar
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - sólo en intérpretes 3.10
    try:
        import tomli as tomllib  # type: ignore[no-redef]
    except ModuleNotFoundError:
        tomllib = None  # type: ignore[assignment]

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def pyproject() -> dict:
    if tomllib is None:
        pytest.skip("tomllib requiere Python 3.11+")
    return tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))


class TestLintersAgree:
    """Un solo criterio de estilo, dicho tres veces sin contradecirse."""

    def test_line_length_matches_across_every_linter(self, pyproject) -> None:
        """882 líneas correctas fallaban porque ruff decía 88 y flake8 120."""
        ruff = pyproject["tool"]["ruff"]["line-length"]
        pylint = pyproject["tool"]["pylint"]["format"]["max-line-length"]

        parser = configparser.ConfigParser()
        parser.read(ROOT / ".flake8", encoding="utf-8")
        flake8 = int(parser["flake8"]["max-line-length"])

        assert ruff == pylint == flake8, (
            f"los linters discrepan sobre la anchura: ruff={ruff}, "
            f"pylint={pylint}, flake8={flake8}"
        )

    def test_pylint_does_not_demand_what_ruff_does_not(self, pyproject) -> None:
        disabled = set(pyproject["tool"]["pylint"]["messages control"]["disable"])
        # Las convenciones de docstring son la fuente principal del ruido: ruff
        # no las exige, así que Pylint tampoco debe hacerlo o el editor pedirá
        # cambios que CI nunca va a pedir.
        for message in (
            "missing-module-docstring",
            "missing-class-docstring",
            "missing-function-docstring",
        ):
            assert message in disabled, f"pylint aún exige {message}"

    def test_flake8_declares_itself_retired(self) -> None:
        """Si se queda, tiene que decir que no es la fuente de verdad."""
        text = (ROOT / ".flake8").read_text(encoding="utf-8")
        assert "ruff" in text.lower(), (
            ".flake8 no menciona ruff; alguien puede seguirlo creyendo que "
            "es la configuración vigente"
        )

    def test_ci_lints_with_ruff(self) -> None:
        """La afirmación de CONTRIBUTING tiene que ser cierta."""
        workflows = list((ROOT / ".github" / "workflows").glob("*.yml"))
        assert workflows, "no hay workflows de CI"
        joined = "\n".join(w.read_text(encoding="utf-8") for w in workflows)
        assert "ruff check" in joined


class TestCIToolsAreInstallable:
    """Toda herramienta que CI invoca tiene que venir de algún sitio.

    AUD-174. El paso «Type-check the ratcheted scope» ejecutaba `mypy`, pero
    `mypy` no estaba en ningún extra de `pyproject.toml` y el workflow instala
    exactamente `pip install -e ".[dev]"`. El paso terminaba en
    `mypy: command not found` — código 127 — así que el trinquete de tipos que
    AUD-124 puso en marcha llevaba desde entonces sin comprobar una sola línea.

    El modo de fallo es peor que un gate en rojo: el paso *parece* existir en
    el fichero del workflow y en CLAUDE.md, así que nadie vuelve a mirarlo.
    """

    #: Comandos del propio shell o del intérprete. No se instalan con pip, así
    #: que no exigen declaración. Todo lo que NO esté aquí se considera una
    #: herramienta de Python y tiene que estar declarada: así una herramienta
    #: nueva se detecta sola, en vez de depender de que alguien la añada a una
    #: lista blanca.
    _SHELL = frozenset({
        "python", "python3", "pip", "pip3", "echo", "cd", "export", "grep",
        "tr", "sed", "cat", "cp", "mv", "mkdir", "rm", "ls", "set", "source",
        "if", "then", "else", "fi", "for", "do", "done", "while", "true",
        "false", "exit", "sudo", "apt-get", "git", "chmod", "test",
    })

    @classmethod
    def _tools_invoked_by_ci(cls) -> dict[str, set[str]]:
        """Primer token de cada línea de un bloque `run:`, por workflow."""
        invoked: dict[str, set[str]] = {}
        for workflow in sorted((ROOT / ".github" / "workflows").glob("*.yml")):
            found: set[str] = set()
            in_run = False
            run_indent = 0
            continued = False
            for raw in workflow.read_text(encoding="utf-8").splitlines():
                stripped = raw.strip()
                indent = len(raw) - len(raw.lstrip())

                if not stripped:
                    continue
                if in_run and indent <= run_indent and not raw.startswith(" " * (run_indent + 1)):
                    in_run = False
                if re.match(r"^run:\s*\|?\s*$", stripped):
                    in_run, run_indent, continued = True, indent, False
                    continue
                if stripped.startswith("run:"):
                    stripped, in_run = stripped[4:].strip(), False
                elif not in_run:
                    continue

                was_continued, continued = continued, stripped.endswith("\\")
                if was_continued or stripped.startswith("#"):
                    continue

                token = stripped.split()[0]
                # `PAQUETES=$(...)` es una asignación, no una invocación.
                if "=" in token.split("(")[0] and not token.startswith("-"):
                    continue
                found.add(token)
            invoked[workflow.name] = found
        return invoked

    @staticmethod
    def _declared_anywhere(pyproject: dict) -> set[str]:
        specs = list(pyproject["project"]["dependencies"])
        for extra in pyproject["project"].get("optional-dependencies", {}).values():
            specs.extend(extra)
        return {re.split(r"[<>=!~\[]", spec)[0].strip().lower() for spec in specs}

    def test_every_tool_ci_runs_is_declared_or_installed_in_place(
        self, pyproject,
    ) -> None:
        declared = self._declared_anywhere(pyproject)

        for name, tools in self._tools_invoked_by_ci().items():
            text = (ROOT / ".github" / "workflows" / name).read_text(encoding="utf-8")
            for tool in sorted(tools - self._SHELL):
                installed_in_place = re.search(
                    rf"pip install .*\b{re.escape(tool)}\b", text,
                )
                assert tool in declared or installed_in_place, (
                    f"{name} ejecuta '{tool}', pero no está declarado en "
                    f"pyproject.toml ni se instala en el propio workflow. El "
                    f"paso terminará en 'command not found' en un runner limpio"
                )

    def test_the_type_checker_is_a_dev_dependency(self, pyproject) -> None:
        """El caso concreto de AUD-174, fijado aparte para que no se pierda.

        La prueba de arriba es la regla general; ésta nombra la herramienta,
        porque el trinquete de tipos de `mypy_scope.txt` no significa nada si
        el comprobador no llega a ejecutarse.
        """
        dev = pyproject["project"]["optional-dependencies"]["dev"]
        names = {re.split(r"[<>=!~\[]", spec)[0].strip().lower() for spec in dev}
        assert "mypy" in names, (
            "el extra 'dev' no declara mypy, y es lo único que CI instala"
        )


class TestEditorConfiguration:
    """El editor tiene que apuntar al intérprete del proyecto."""

    def test_vscode_pins_the_project_interpreter(self) -> None:
        """Sin esto, Pylance no resuelve orjson ni pydantic.

        No es cosmético: los dos paquetes están instalados y el juego arranca,
        pero el editor marca errores rojos sobre código correcto. Un archivo
        lleno de errores falsos es un archivo que se deja de leer.
        """
        settings = ROOT / ".vscode" / "settings.json"
        assert settings.exists(), "falta .vscode/settings.json"
        text = settings.read_text(encoding="utf-8")
        assert "python.defaultInterpreterPath" in text
        assert ".venv" in text

    def test_vscode_settings_parse_after_stripping_comments(self) -> None:
        """VS Code acepta comentarios (JSONC); el archivo debe seguir siendo válido."""
        import json

        text = (ROOT / ".vscode" / "settings.json").read_text(encoding="utf-8")
        stripped = re.sub(r"^\s*//.*$", "", text, flags=re.MULTILINE)
        data = json.loads(stripped)
        assert data["files.eol"] == "\n", (
            "el editor debe guardar LF; guardar CRLF fue lo que produjo un "
            "diff de 334 archivos sin un solo cambio real"
        )


class TestDeclaredDependencies:
    """Lo que el juego comprueba al arrancar y lo que se declara instalar."""

    @staticmethod
    def _preflight_packages() -> set[str]:
        """Lee `_REQUIRED_PACKAGES` de main.py sin importarlo.

        Importar `main` ejecutaría `sys.path.insert` y el bloque `__main__`.
        Se parsea el AST, que es suficiente para una tupla literal.
        """
        tree = ast.parse((ROOT / "main.py").read_text(encoding="utf-8"))
        for node in tree.body:
            targets = getattr(node, "targets", []) or [getattr(node, "target", None)]
            names = [t.id for t in targets if isinstance(t, ast.Name)]
            if "_REQUIRED_PACKAGES" in names and node.value is not None:
                pairs = ast.literal_eval(node.value)
                return {install for _, install in pairs}
        raise AssertionError("main.py ya no declara _REQUIRED_PACKAGES")

    def test_every_preflight_package_is_a_declared_dependency(
        self, pyproject,
    ) -> None:
        """Comprobar al arrancar algo que no se instala sería un falso bloqueo."""
        declared = {
            re.split(r"[<>=!~\[]", dep)[0].strip().lower()
            for dep in pyproject["project"]["dependencies"]
        }
        for package in self._preflight_packages():
            assert package.lower() in declared, (
                f"main.py exige '{package}' al arrancar pero pyproject.toml no "
                f"lo declara: quien siga las instrucciones de instalación no "
                f"podrá lanzar el juego"
            )

    def test_requirements_and_pyproject_do_not_drift(self, pyproject) -> None:
        declared = {
            re.split(r"[<>=!~\[]", dep)[0].strip().lower()
            for dep in pyproject["project"]["dependencies"]
        }
        requirements = {
            re.split(r"[<>=!~\[]", line)[0].strip().lower()
            for line in (ROOT / "requirements.txt").read_text(
                encoding="utf-8",
            ).splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        }
        missing = declared - requirements
        assert not missing, (
            f"en pyproject pero no en requirements.txt: {sorted(missing)}"
        )

    def test_the_preflight_lists_the_packages_that_actually_gate_startup(
        self,
    ) -> None:
        """orjson y pydantic son justamente los que rompieron el arranque."""
        packages = self._preflight_packages()
        for critical in ("pygame-ce", "pydantic", "orjson"):
            assert critical in packages, (
                f"'{critical}' no se comprueba antes de arrancar; su ausencia "
                f"daría un ModuleNotFoundError a media cadena de imports"
            )
