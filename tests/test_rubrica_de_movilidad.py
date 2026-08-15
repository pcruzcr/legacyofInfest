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


class TestLosSlopesNoSonRepechosImposibles:
    """AUD-472 — el mismo defecto que AUD-192, con otra mecánica.

    `Slope` (AUD-297) no entra en `collision_rects` a propósito
    (`pendientes.py`: «si entrara, el eje X la trataría como pared»), así
    que ni `reachable_platforms` ni `analyse_geometry` sabían que existía.
    Medido sobre el 4-1 reconstruido (AUD-467…471, `feature/stage4_1-
    cementerio-sagrado`): una loma real de 160 px —transitable de sobra,
    comprobado con un recorrido físico simulado que sí sube— salía como
    «repecho imposible» y hundía `design_geometry` a 1/10, con
    `exit_reachable` en falso.

    A diferencia de AUD-192 (que excusa la nota sin corregir el dato), aquí
    se corrige el dato: `reachable_platforms`/`analyse_geometry` reciben la
    lista de `Pendiente` y tratan sus dos extremos como conectados sin
    pasar por la envolvente de salto, porque subir una rampa caminando no
    es saltar.
    """

    def _plano_con_loma(self):
        """Dos plataformas a distinta altura, unidas por una `Pendiente` —
        la misma forma que la loma real del 4-1, en miniatura.

        `alta` se solapa en `x` con `baja` a propósito: es exactamente la
        forma que tenía el defecto real —una meseta elevada directamente
        encima de una parte del suelo llano— y es lo que hace que
        `analyse_geometry` la trate como «repecho» en vez de como dos
        plataformas separadas por un hueco (esa otra forma la cubren ya los
        huecos, no los repechos). El desnivel (300 px) es a propósito mucho
        mayor que cualquier salto razonable de este motor (~90 px, medido
        en `trazado.py` del 4-1): si el «control» sin rampa no fallara, la
        prueba de abajo no demostraría nada.
        """
        import pygame as pg

        from src.framework.stage.pendientes import Pendiente

        baja = pg.Rect(0, 320, 300, 20)      # suelo llano, x:0-300, y=320
        alta = pg.Rect(100, 20, 100, 20)     # meseta elevada, x:100-200, y=20
        rampa = Pendiente(rect=pg.Rect(50, 20, 50, 300), sube_a_la_derecha=True)
        return [baja, alta], [rampa]

    def test_sin_la_pendiente_el_repecho_es_imposible(self) -> None:
        """Control: sin decirle al analizador que hay una rampa, el mismo
        mapa sale roto — así se sabe que la prueba de abajo mide lo que
        dice medir, no un montaje que siempre pasaría."""
        from src.framework.stage.level_metrics import analyse_geometry

        rects, _rampa = self._plano_con_loma()
        informe = analyse_geometry(rects)
        assert len(informe.impossible_ledges) == 1

    def test_con_la_pendiente_no_hay_repecho(self) -> None:
        from src.framework.stage.level_metrics import analyse_geometry

        rects, rampa = self._plano_con_loma()
        informe = analyse_geometry(rects, pendientes=rampa)
        assert informe.impossible_ledges == [], (
            f"la rampa no bastó para conectar las dos plataformas: "
            f"{informe.impossible_ledges}"
        )

    def test_la_meseta_es_alcanzable_con_la_pendiente(self) -> None:
        import pygame as pg

        from src.framework.stage.level_metrics import reachable_platforms

        rects, rampa = self._plano_con_loma()
        spawn = pg.Vector2(10, 310)
        sin_rampa = reachable_platforms(rects, spawn)
        con_rampa = reachable_platforms(rects, spawn, pendientes=rampa)
        assert sin_rampa == {0}, "control: sin la rampa sólo se alcanza el suelo llano"
        assert con_rampa == {0, 1}, "con la rampa debería alcanzarse también la meseta"

    def test_stage4_1_reconstruido_es_completable_de_verdad(self) -> None:
        """Extremo a extremo, contra el escenario real que descubrió el
        defecto — no la nota excusada de AUD-192, la medición honesta."""
        datos = _calificar("assets/maps/stage4_1/stage4_1.tmx")
        assert datos["design"]["exit_reachable"] is True
        assert datos["design"]["impossible_ledges"] == 0
        assert datos["categories"]["design_completable"]["msg"] == (
            "la salida es alcanzable andando desde el spawn"
        ), "debería colarse por la ruta honesta, no por la excusa de movilidad"


class TestLasCadenasDePendientes:
    """AUD-477 — el mismo defecto que AUD-472, con una forma nueva.

    AUD-472 conectaba **una** pendiente entre dos plataformas sólidas. Sirve
    para una rampa que sube hasta una meseta sólida. La reconstrucción de
    las lomas de la Fase 3 del 4-1 (`trazado.py::altura_de_colision`) ya no
    pone un bloque sólido en la cima: un recorrido real encontró que un
    bloque sólido justo al final de una rampa deja al jugador clavado en la
    unión (el AABB del fotograma usa la `y` con la que la rampa **aún no**
    llegó del todo a la altura de la meseta), así que ahora la cima es
    *otra* pendiente, casi plana. Sube → cima → baja son tres `Slope`
    encadenados por sus extremos, y ninguno de ellos toca directamente una
    plataforma sólida en ambos lados — sólo el primero y el último, cada
    uno por un extremo.
    """

    def _plano_con_loma_de_tres_tramos(self):
        """Sube, cima llana (también `Pendiente`, no plataforma sólida),
        baja — la misma forma que las lomas reconstruidas del 4-1, en
        miniatura y con las mismas dos alturas que ya usa
        `TestLosSlopesNoSonRepechosImposibles._plano_con_loma`."""
        import pygame as pg

        from src.framework.stage.pendientes import Pendiente

        baja = pg.Rect(0, 320, 500, 20)     # suelo llano a los dos lados
        subida = Pendiente(rect=pg.Rect(50, 20, 50, 300), sube_a_la_derecha=True)
        cima = Pendiente(rect=pg.Rect(100, 20, 100, 1), sube_a_la_derecha=True)
        bajada = Pendiente(rect=pg.Rect(200, 20, 50, 300), sube_a_la_derecha=False)
        return [baja], [subida, cima, bajada]

    def test_sin_las_pendientes_el_repecho_es_imposible(self) -> None:
        """Control: con una sola plataforma sólida no hay nada que conectar
        — así se sabe que la prueba de abajo mide la cadena, no un montaje
        que ya pasaría sin ella."""
        import pygame as pg

        from src.framework.stage.level_metrics import reachable_platforms

        rects, _pendientes = self._plano_con_loma_de_tres_tramos()
        spawn = pg.Vector2(10, 310)
        alcanzable = reachable_platforms(rects, spawn)
        assert alcanzable == {0}

    def test_la_cadena_completa_no_rompe_la_ruta(self) -> None:
        """Las tres pendientes encadenadas no deben desconectar nada: sigue
        siendo un único suelo llano, ahora con una loma en medio que se
        puede subir y bajar caminando."""
        import pygame as pg

        from src.framework.stage.level_metrics import analyse_geometry, reachable_platforms

        rects, pendientes = self._plano_con_loma_de_tres_tramos()
        spawn = pg.Vector2(10, 310)

        alcanzable = reachable_platforms(rects, spawn, pendientes=pendientes)
        assert alcanzable == {0}, (
            "sigue habiendo una sola plataforma sólida; la cadena no debería "
            "inventar ni perder ninguna"
        )
        informe = analyse_geometry(rects, pendientes=pendientes)
        assert informe.impossible_ledges == []

    def test_stage4_1_sigue_completable_con_lomas_de_tres_tramos(self) -> None:
        """Extremo a extremo, contra el mapa real: dos lomas, tres `Slope`
        cada una, ninguna toca una meseta sólida en su extremo alto."""
        datos = _calificar("assets/maps/stage4_1/stage4_1.tmx")
        assert datos["design"]["exit_reachable"] is True
        assert datos["design"]["orphan_platforms"] == 0


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
