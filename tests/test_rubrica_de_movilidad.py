"""
Module: test_rubrica_de_movilidad
System: tests
Academic Unit: N/A

AUD-192 — el calificador penalizaba usar las mecánicas del motor.

Qué pasaba
----------
`grade_stage.py` puntúa `design_completable` con 12 de 130 puntos, y lo decide
`level_metrics.exit_is_reachable`, que construye un grafo de **saltos**. Su
propio docstring reconoce el límite:

    «no modela dash, salto de pared ni plataformas móviles»

Tampoco resortes, lianas ni tirolesas. Así que un nivel cuyo camino pasa por un
`Spring` sale marcado como imposible de terminar.

Medido antes del arreglo: `stage_mecanicas.tmx` —el escenario que el propio
motor usa para enseñar las once mecánicas, con 11 objetos de movilidad—
sacaba **0 de 12** en esa categoría. Con él, cualquier alumno que resolviera un
tramo con un resorte en lugar de con un salto.

La corrección no afirma que el nivel sea completable: dice que esta métrica no
puede juzgarlo, no cobra por ello, y avisa por escrito de que hay que
comprobarlo jugando. Es la misma decisión que ya estaba tomada para las arenas
de jefe, y por la misma razón — aplicar la rúbrica equivocada y suspender por
ella es peor que no medir.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent


def _calificar(ruta: str) -> dict:
    salida = subprocess.run(
        [sys.executable, "scripts/grade_stage.py", ruta, "--json"],
        cwd=RAIZ, capture_output=True, text=True, encoding="utf-8",
        env={"SDL_VIDEODRIVER": "dummy", "SDL_AUDIODRIVER": "dummy",
             "PYGAME_HIDE_SUPPORT_PROMPT": "1", "PATH": ""},
        check=False,
    ).stdout
    datos = json.loads(salida[salida.index("["):salida.rindex("]") + 1])
    return datos[0]


@pytest.fixture(scope="module")
def mecanicas() -> dict:
    """Calificar arranca un subproceso con pygame: se hace una vez."""
    return _calificar("assets/maps/stage_mecanicas/stage_mecanicas.tmx")


class TestUnNivelConMecanicasNoSeSuspende:

    def test_no_pierde_los_doce_puntos_de_completable(self, mecanicas) -> None:
        categoria = mecanicas["categories"]["design_completable"]
        assert categoria["score"] == categoria["max"], (
            f"el nivel escaparate de las mecánicas saca "
            f"{categoria['score']}/{categoria['max']} por usarlas: "
            f"{categoria['msg']}"
        )

    def test_avisa_de_que_la_ruta_no_se_pudo_verificar(self, mecanicas) -> None:
        """No cobrar por ello no es lo mismo que decir que está bien.

        El aviso es la parte honesta del arreglo: sin él, un nivel de verdad
        roto pasaría la categoría en silencio.
        """
        avisos = " ".join(mecanicas["warnings"]).lower()
        assert "movilidad" in avisos or "resortes" in avisos, (
            f"no se avisa de que la ruta no se ha podido juzgar: "
            f"{mecanicas['warnings']}"
        )
        assert "jugando" in avisos, (
            "el aviso no dice que haya que comprobarlo jugando"
        )

    def test_no_se_declara_alcanzable_lo_que_no_se_ha_comprobado(
        self, mecanicas,
    ) -> None:
        """La medición cruda se conserva tal cual: el informe sigue diciendo
        que el grafo de saltos no llegó a la salida. Lo que cambia es la nota,
        no el dato."""
        assert mecanicas["design"]["exit_reachable"] is False


class TestUnNivelSinMecanicasSigueJuzgandose:
    def test_stage0_conserva_su_nota_perfecta(self) -> None:
        """La contraparte: sin objetos de movilidad, la métrica sí aplica y
        stage0 la pasa por la vía normal, no por la excepción."""
        stage0 = _calificar("assets/maps/stage0/stage0.tmx")
        categoria = stage0["categories"]["design_completable"]

        assert categoria["score"] == categoria["max"]
        assert "andando" in categoria["msg"], (
            f"stage0 no debería pasar por la excepción de movilidad: "
            f"{categoria['msg']}"
        )
        assert stage0["design"]["exit_reachable"] is True


class TestLaDeteccionDeMovilidad:
    def test_reconoce_los_componentes_por_su_clase(self) -> None:
        """Se mira el resultado de la carga, no el XML: `Conveyor` y
        `FrictionZone` son el mismo componente, y mantener una lista de nombres
        del TMX en dos sitios es una desincronización esperando a ocurrir."""
        sys.path.insert(0, str(RAIZ))
        from importlib import import_module

        modulo = import_module("scripts.grade_stage")
        assert "Resorte" in modulo.COMPONENTES_DE_MOVILIDAD
        assert "Tirolesa" in modulo.COMPONENTES_DE_MOVILIDAD
        assert "PlataformaMovil" in modulo.COMPONENTES_DE_MOVILIDAD

    def test_un_escenario_sin_componentes_no_tiene_movilidad(self) -> None:
        sys.path.insert(0, str(RAIZ))
        from importlib import import_module

        modulo = import_module("scripts.grade_stage")

        class Vacio:
            componentes: list = []

        assert modulo._tiene_movilidad(Vacio()) is False
