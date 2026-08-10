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

#: Tamaño del trinquete. Sólo puede subir.
#:
#: AUD-371 lo llevó de 2 a 6. Los cuatro que entraron ya estaban limpios y
#: estaban fuera por inercia: la razón original —«el árbol entero daría
#: cientos de errores»— era cierta para el árbol y falsa para ellos.
#:
#: Un número escrito a mano es exactamente lo que este proyecto ha estado
#: retirando de otros sitios, pero aquí es el punto: la prueba **tiene** que
#: fallar cuando alguien quita un paquete, y para eso hace falta recordar
#: cuántos había. Subirlo al añadir es parte del trabajo de añadir.
PAQUETES_MINIMOS = 6


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

    def test_los_linters_van_fijados_y_no_con_mayor_o_igual(self) -> None:
        """AUD-369 / GAP-034 — la causa de fondo del gate rojo de AUD-353.

        Con `ruff>=0.6`, la definición de «verde» del proyecto la decidía quien
        publicara río arriba esa mañana. Y ocurrió: una regla que ruff movió a
        *preview* convirtió una supresión legítima en `RUF100` y dejó el gate
        de lint en rojo **sin que cambiara una línea del fichero afectado**.

        Fijar no congela: convierte subir el linter en un cambio revisable, con
        su commit y su `AUD-NNN`. Lo que esta prueba impide es volver a `>=`,
        que es la forma silenciosa de reabrir GAP-034.
        """
        import re

        texto = (RAIZ / "pyproject.toml").read_text(encoding="utf-8")
        m = re.search(r"^dev = \[(.*?)^\]", texto, re.M | re.S)
        assert m, "el extra `dev` de pyproject.toml ya no se puede leer"
        bloque = m.group(1)

        for herramienta in ("ruff", "mypy"):
            declarado = re.search(
                rf'"{herramienta}([^"]*)"', bloque)
            assert declarado, f"{herramienta} salió del extra `dev`"
            spec = declarado.group(1)
            assert spec.startswith("=="), (
                f"{herramienta} está declarado como `{herramienta}{spec}`. "
                f"Un linter sin versión fija puede poner el CI en rojo en "
                f"cualquier rama sin relación con el cambio que se revisa "
                f"(GAP-034). Súbelo a mano, con su commit"
            )

    def test_ninguna_orden_del_ci_se_traga_su_codigo_de_salida(self) -> None:
        """AUD-370 — «un gate que ejecute los gates», §5.3 del plan de cierre.

        AUD-353 (ruff comprobado por estar escrito) y AUD-356 (`--json` que
        nadie parseaba) eran el mismo defecto en dos sitios, y el plan avisaba
        de que habría más órdenes en `ci.yml` cuya salida nadie mira. Había
        dos:

        * `pip-audit --desc --strict || true` — el paso ya llevaba
          `continue-on-error: true`, que impide que tumbe el trabajo **y lo
          marca en amarillo**. El `|| true` encima lo dejaba en verde pase lo
          que pase: un escaneo de vulnerabilidades incapaz de avisar de una.
        * los dos calificadores, que salían con 0 tanto con 100/100 como con
          40/100.

        Lo que esta prueba impide es que vuelva a colarse un silenciador. No
        prohíbe `continue-on-error`, que es una decisión legítima y explicada;
        prohíbe **taparlo dos veces**.
        """
        ordenes = [
            linea for linea in CI.read_text(encoding="utf-8").splitlines()
            if not linea.lstrip().startswith("#")
        ]
        silenciadas = [
            linea.strip() for linea in ordenes
            if "|| true" in linea or "|| :" in linea
        ]
        assert not silenciadas, (
            "órdenes de CI que descartan su código de salida:\n"
            + "\n".join(silenciadas)
            + "\nUna orden que no puede fallar no es una comprobación."
        )

    def test_el_material_de_referencia_se_califica_con_suelo(self) -> None:
        """Calificar sin mínimo es informar, y CI necesita comprobar.

        El mapa y el jefe de referencia son los que los estudiantes copian: si
        su nota baja, es que el calificador y el material han dejado de estar
        de acuerdo. Eso hay que verlo antes de un día de entrega, que es lo
        que el comentario de AUD-104 lleva pidiendo desde que se escribió.
        """
        texto = CI.read_text(encoding="utf-8")
        for guion in ("grade_stage.py", "grade_boss.py"):
            lineas = [
                linea for linea in texto.splitlines()
                if guion in linea and not linea.lstrip().startswith("#")
            ]
            assert lineas, f"{guion} salió del CI"
            assert any("--minimo" in linea for linea in lineas), (
                f"{guion} se ejecuta en CI sin `--minimo`, así que sale con "
                f"éxito con cualquier nota y el paso no puede fallar nunca"
            )

    def test_ruff_esta_limpio_en_el_alcance_del_ci(self) -> None:
        """No que el paso exista: que el árbol lo pase, aquí y ahora.

        AUD-353 — las tres pruebas de arriba comprueban que la orden sigue
        escrita en `ci.yml`, y ninguna la ejecuta. Así que el repositorio
        pasó a `prod` con el linter en rojo y la suite entera en verde: un
        `# noqa: LOG004` de AUD-304 dejó de hacer falta cuando ruff movió esa
        regla a *preview*, RUF100 lo denunció como directiva inútil, y nadie
        se enteró hasta que alguien ejecutó el gate a mano.

        La causa de fondo es que `ruff>=0.6` no tiene tope: la definición de
        «verde» de este proyecto cambia sola cuando río arriba publican una
        versión. No se arregla poniendo un tope —eso congela también las
        correcciones— sino ejecutando el linter dentro de la suite, que es lo
        único que corre en cada máquina y en cada rama. Está registrado como
        GAP-034.

        El alcance se **lee del CI**, no se copia: una prueba con su propia
        lista de rutas se desincroniza del gate que dice proteger.
        """
        import re
        import subprocess
        import sys

        texto = CI.read_text(encoding="utf-8")
        m = re.search(r"^\s*ruff check (.+?)--output-format",
                      texto, re.MULTILINE | re.DOTALL)
        assert m, "el CI ya no invoca `ruff check`; esta prueba quedó ciega"
        rutas = m.group(1).replace("\\\n", " ").split()
        assert rutas, "el paso de ruff del CI no lintea ninguna ruta"

        proceso = subprocess.run(
            [sys.executable, "-m", "ruff", "check", *rutas],
            capture_output=True, text=True, cwd=str(RAIZ), check=False,
        )
        assert proceso.returncode == 0, (
            "el gate de ruff del CI está en rojo con la versión instalada "
            f"({' '.join(rutas)}):\n{proceso.stdout[-3000:]}"
        )
