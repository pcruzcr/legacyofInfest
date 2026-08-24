"""
El calificador de jefes premia usar el framework, no reimplementarlo.

AUD-104 — el hallazgo más caro de esta sesión
=============================================
El jefe de referencia —el que el profesor construyó y el que los estudiantes
copian— sacaba **63/100** en el calificador del propio profesor, con cuatro
suspensos:

    [FAIL] hp_thresholds      0/10  — No HP threshold checks
    [FAIL] hurt_damage_states 0/10  — No hurt/damage handler
    [FAIL] telegraph_state    0/10  — No telegraph state
    [WARN] attack_patterns    8/15  — Only 1 attack pattern

Ninguno era cierto. `BossVenado` declara dos `BossPhase(health_threshold=...)`,
tiene puntos débiles y hurtbox propia, usa el telegrafiado de `BossBase`, y
tiene ocho ataques. Lo que fallaba era el calificador:

- Exigía un método `take_damage` o `hurt`. **Esos nombres no existen en el
  framework**: la API de daño es `apply_hit` y `apply_hit_at`. Ningún jefe
  correcto podía pasar ese criterio, y el único que lo pasaría sería uno que
  se hubiera escrito su propio sistema de daño ignorando el motor — la
  lección contraria a la que enseña la asignatura.
- Buscaba ataques en métodos con «attack» o «pattern» en el nombre. El
  framework los llama `_do_stomp`, `_do_charge`, `_do_vine_toss`.
- Buscaba umbrales de vida en comparaciones sueltas contra `self.hp`, no en
  `BossPhase(health_threshold=...)`, que es como se declaran de verdad.

El daño real no es la nota del jefe de referencia: es que **cada estudiante
que use bien el framework habría sido penalizado por usarlo bien**, y quien
copiara y pegara todo en su fichero habría sacado más nota. Un calificador
así no mide: enseña a hacerlo mal.

Estas pruebas fijan las dos mitades: que un jefe correcto puntúe alto y que
uno vacío siga suspendiendo.
"""
from __future__ import annotations

import importlib.util
import pathlib
import sys

import pytest

RAIZ = pathlib.Path(__file__).resolve().parent.parent
JEFE_DE_REFERENCIA = RAIZ / "src" / "stages" / "boss_venado" / "boss_venado.py"


def _cargar_calificador():
    """Importa `scripts/grade_boss.py`, que no es un paquete."""
    ruta = RAIZ / "scripts" / "grade_boss.py"
    spec = importlib.util.spec_from_file_location("grade_boss", ruta)
    modulo = importlib.util.module_from_spec(spec)
    sys.modules["grade_boss"] = modulo
    spec.loader.exec_module(modulo)
    return modulo


@pytest.fixture(scope="module")
def calificador():
    return _cargar_calificador()


class TestElJefeDeReferenciaAprueba:
    """Si el ejemplo del profesor suspende, el criterio está mal, no el ejemplo."""

    def test_saca_la_nota_maxima(self, calificador):
        resultado = calificador.grade_boss(JEFE_DE_REFERENCIA)
        assert resultado["score"] == 100, (
            f"el jefe de referencia saca {resultado['score']}/100. "
            f"Suspensos: "
            + ", ".join(
                f"{k} ({v['score']}/{v['max']})"
                for k, v in resultado["categories"].items()
                if v["score"] < v["max"]
            )
        )

    def test_no_reporta_ningun_error(self, calificador):
        resultado = calificador.grade_boss(JEFE_DE_REFERENCIA)
        assert not resultado["errors"], resultado["errors"]

    @pytest.mark.parametrize("categoria", [
        "hp_thresholds", "hurt_damage_states", "telegraph_state", "attack_patterns",
    ])
    def test_las_cuatro_categorias_que_fallaban(self, calificador, categoria):
        """Las cuatro por su nombre, para que un fallo diga cuál volvió."""
        resultado = calificador.grade_boss(JEFE_DE_REFERENCIA)
        entrada = resultado["categories"][categoria]
        assert entrada["score"] == entrada["max"], (
            f"{categoria}: {entrada['score']}/{entrada['max']} — {entrada['msg']}"
        )


class TestUnJefeVacioSigueSuspendiendo:
    """La otra mitad: relajar el criterio no puede volverlo inútil."""

    @pytest.fixture
    def jefe_vacio(self, tmp_path):
        ruta = tmp_path / "jefe_vago.py"
        ruta.write_text(
            "from src.framework.entities.boss_base import BossBase\n"
            "\n"
            "\n"
            "class JefeVago(BossBase):\n"
            "    def __init__(self) -> None:\n"
            "        super().__init__()\n",
            encoding="utf-8",
        )
        return ruta

    def test_suspende(self, calificador, jefe_vacio):
        resultado = calificador.grade_boss(jefe_vacio)
        assert resultado["score"] < 50, (
            f"un jefe que no hace nada saca {resultado['score']}/100"
        )

    def test_dice_que_le_falta_y_con_que_nombre(self, calificador, jefe_vacio):
        """El mensaje de error tiene que nombrar la API real.

        Antes decía «Add a take_damage or hurt method», mandando al estudiante
        a escribir un método que el framework nunca llama.
        """
        resultado = calificador.grade_boss(jefe_vacio)
        errores = " ".join(resultado["errors"])
        assert "apply_hit" in errores, (
            "el calificador no dice cuál es la API de daño de verdad"
        )
        assert "take_damage" not in errores.replace("no `take_damage`", ""), (
            "el calificador sigue mandando a escribir `take_damage`"
        )


class TestLoQueNoEsUnJefeNoSeCalifica:
    """Un `__init__.py` con 0/100 hunde la media de un paquete entregado."""

    def test_el_init_del_paquete_se_excluye(self, calificador, tmp_path, monkeypatch, capsys):
        paquete = tmp_path / "entrega"
        paquete.mkdir()
        (paquete / "__init__.py").write_text("", encoding="utf-8")
        (paquete / "mi_jefe.py").write_text(
            JEFE_DE_REFERENCIA.read_text(encoding="utf-8"), encoding="utf-8",
        )

        monkeypatch.setattr(sys, "argv", ["grade_boss.py", str(paquete)])
        calificador.main()
        salida = capsys.readouterr().out
        assert "__init__.py" not in salida
        assert "Total graded: 1" in salida, (
            "se calificó algo más que el único jefe del paquete"
        )

    def test_la_clase_base_del_framework_se_excluye(self, calificador, monkeypatch, capsys):
        """CI la calificaba en cada ejecución y sacaba 0/100."""
        base = RAIZ / "src" / "framework" / "entities" / "boss_base.py"
        monkeypatch.setattr(sys, "argv", ["grade_boss.py", str(base)])
        codigo = calificador.main()
        salida = capsys.readouterr().out
        assert codigo == 1
        assert "No hay ficheros de jefe" in salida


class TestElCriterioRefleiaLaApiDelFramework:
    """Si la API cambia de nombre, el calificador tiene que enterarse."""

    def test_la_api_de_dano_se_llama_apply_hit(self):
        """La premisa entera de AUD-104, comprobada y no supuesta."""
        from src.framework.entities.boss_base import BossBase

        assert hasattr(BossBase, "apply_hit")
        assert hasattr(BossBase, "apply_hit_at")
        assert not hasattr(BossBase, "take_damage"), (
            "si ahora existe `take_damage`, actualiza el calificador y esta prueba"
        )
        assert not hasattr(BossBase, "hurt")

    def test_las_fases_se_declaran_con_health_threshold(self):
        from src.framework.entities.boss_base import BossPhase

        campos = getattr(BossPhase, "__dataclass_fields__", {})
        assert "health_threshold" in campos, (
            "el calificador cuenta umbrales por `BossPhase(health_threshold=...)`"
        )
