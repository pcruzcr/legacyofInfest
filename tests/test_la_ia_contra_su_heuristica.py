"""AUD-368: cuánto aporta la capa ML frente a la heurística. Medido.

El hallazgo P6, abierto desde la primera ronda de `docs/89`
==========================================================

*«La capa ML no tiene métrica de acierto.»* `docs/63` lo repetía y
`docs/69` §8 (D6) exige lo contrario sin rodeos: *«si propones ML, compara
contra la heurística determinista con una medición, no con una opinión»*.
Nadie había medido.

Lo que la medición encontró, y por qué se lee al revés
=====================================================

El modelo **se entrena exclusivamente con la salida de las propias reglas**:
`squad_brain.py:171-180` le da como etiqueta la decisión que la heurística
acaba de tomar, «para que aprenda de una política válida en lugar de de
ruido». Es deliberado y es sensato. Y tiene una consecuencia que no estaba
escrita en ninguna parte:

    el techo del modelo es imitar a la heurística.

No hay ninguna señal en el sistema que le diga que una acción funcionó y otra
no: no hay recompensa, ni resultado de combate, ni etiqueta humana. Así que el
acuerdo con las reglas **no es una nota de acierto: es una nota de fidelidad**,
y lo que le falte para el 100 % es degradación pura respecto a ejecutar las
reglas directamente.

Medido con `scripts/medir_ia.py` (2.000 ejemplos, semilla 42):

    Fidelidad a la heurística : 82,1 %

O sea: **casi uno de cada cinco enemigos hace algo distinto de lo que la
heurística habría decidido, y no hay ningún motivo para creer que sea mejor.**
Las desviaciones no son inocuas — `charge → attack_ranged` (43 casos) es un
enemigo cuerpo a cuerpo intentando disparar; `attack_melee → retreat` (25) es
uno que debía atacar y huye.

Qué NO se hace aquí, y por qué
==============================

No se apaga la capa ML. Su valor en este repositorio no es táctico: es
**docente** — es el material vivo de la unidad de Reconocimiento de Patrones,
y un estudiante que la abre ve un clasificador real sobre datos reales del
juego. Apagarla porque rinde peor sería optimizar el motor a costa de lo que
el proyecto es (`CLAUDE.md` §1).

Lo que sí cambia es que el coste está **medido y escrito**, que es lo que P6
pedía. La decisión de qué hacer con esos 17,9 % —dejarlos, preferir reglas en
partida y modelo en el laboratorio, o darle al modelo una señal de verdad— es
del dueño, y ahora se toma con un número delante.

Qué fija esta prueba
====================

Que la medición siga siendo posible y que el número no se desplome sin que
nadie se entere. El umbral es holgado (70 %) por la misma razón que el
presupuesto de la suite: un umbral apretado sobre un `random_state` fijo se
convierte en un test frágil que se acaba desactivando.
"""
from __future__ import annotations

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pytest

sklearn = pytest.importorskip(
    "sklearn",
    reason="scikit-learn es opcional en runtime (CLAUDE.md §3, invariante 7): "
           "sin él la IA cae a la heurística y no hay modelo que medir",
)

#: Suelo de fidelidad. Holgado a propósito: lo que se vigila es un desplome
#: —que alguien toque los rasgos o los hiperparámetros y el modelo deje de
#: parecerse a las reglas—, no la oscilación normal de un KNN.
SUELO_DE_FIDELIDAD = 0.70


@pytest.fixture(scope="module")
def medicion() -> dict:
    # Dentro de la función y no arriba: el `importorskip` de más arriba es
    # una sentencia, así que cualquier import posterior sería E402. Se
    # podría añadir este fichero a las exenciones de `pyproject.toml` —hay
    # cinco— pero una exención se pide cuando no hay alternativa, y aquí
    # la hay.
    from scripts.medir_ia import medir

    return medir(n_entreno=2000, n_prueba=1000, semilla=42)


class TestLaMedicionExiste:
    """P6 pedía un número. Esto es que el número se pueda sacar."""

    def test_el_modelo_llega_a_entrenarse(self, medicion) -> None:
        assert medicion["entrenado"] == 1.0

    def test_la_fidelidad_es_medible_y_no_se_desploma(self, medicion) -> None:
        fidelidad = medicion["fidelidad"]
        assert 0.0 <= fidelidad <= 1.0
        assert fidelidad >= SUELO_DE_FIDELIDAD, (
            f"la fidelidad del modelo a la heurística cayó a {fidelidad:.1%}. "
            f"Como el modelo se entrena con la salida de las reglas, todo lo "
            f"que le falte al 100 % es degradación, no aprendizaje"
        )


class TestElTechoEsLaHeuristica:
    """La propiedad estructural, que es el verdadero hallazgo."""

    def test_el_modelo_no_puede_superar_a_las_reglas(self, medicion) -> None:
        """Fidelidad < 100 % significa peor, nunca mejor.

        No es una afirmación sobre este modelo concreto: es sobre el montaje.
        Sin señal de recompensa, la única etiqueta que existe es la decisión
        de la heurística, así que el óptimo alcanzable es reproducirla.
        """
        assert medicion["fidelidad"] < 1.0, (
            "fidelidad del 100 %: si el modelo reprodujera exactamente las "
            "reglas, la capa ML no aportaría nada y sería sólo coste. "
            "Revisa la medición antes de celebrarlo"
        )

    def test_las_reglas_son_deterministas(self) -> None:
        """La otra mitad de la comparación tiene que ser estable, o no compara."""
        from src.framework.entities.ai_predictor import BehaviorPredictor

        p = BehaviorPredictor()
        caso = {"dist": 95.0, "health_pct": 0.8,
                "player_health_pct": 0.5, "has_ranged": False}
        primera = p.get_rule_based_action(**caso)
        assert all(p.get_rule_based_action(**caso) == primera for _ in range(20))


class TestElDesvioSeSabeDonde:
    def test_las_discrepancias_se_pueden_inspeccionar(self, medicion) -> None:
        """Un porcentaje sin el detalle no permite decidir nada.

        Saber que falla el 18 % no dice si son confusiones inocuas o si un
        enemigo cuerpo a cuerpo intenta disparar. Lo segundo se midió: es
        `charge -> attack_ranged`, la desviación más frecuente.
        """
        discrepancias = medicion["discrepancias"]
        assert isinstance(discrepancias, dict)
        assert discrepancias, "sin discrepancias no hay nada que explicar"
        for clave in discrepancias:
            assert " -> " in clave, clave
