"""
Module: test_cadena_de_niveles
System: tests
Academic Unit: N/A

AUD-183 — que el juego se pueda terminar.

Qué faltaba
-----------
`test_scene_manager.py` comprueba la cola de escenarios con dos escenas de
mentira (`_TestSceneA`, `_TestSceneB`), y `test_scene_smoke.py` arranca cada
escenario **por separado**. Entre las dos cosas no había ninguna que
recorriera la cadena de verdad: los 16 escenarios de `STAGE_ORDER`, en orden,
encadenados por el evento `STAGE_COMPLETE`, hasta los créditos.

Es el hueco clásico: cada pieza probada, el recorrido completo no. Un
escenario que no se pueda construir, un hueco en `STAGE_ORDER` o unos créditos
que no lleguen dejan el juego sin final, y ninguna prueba existente lo veía.

Por qué hace falta `dispatch()`
-------------------------------
`EventBus.emit` **encola**; quien invoca a los suscriptores es `dispatch()`,
una vez por fotograma desde el bucle principal. Es deliberado —da orden
predecible y hace imposible un bucle infinito de emisiones—, pero significa
que emitir `STAGE_COMPLETE` sin despachar no avanza de nivel. Una prueba que
lo olvide comprueba el silencio y pasa por la razón equivocada.
"""
from __future__ import annotations

import pygame
import pytest

from src.engine.core.events import Events
from src.engine.core.stage_registry import STAGE_ORDER, discover_stages


@pytest.fixture
def app_context():
    """Un `App` real: es quien cablea contexto, bus y gestor de escenas."""
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((320, 240))
    from src.engine.core.app import App

    app = App()
    yield app.context
    manager = app.context.scene_manager
    if hasattr(manager, "cleanup"):
        manager.cleanup()


class TestLaCadenaDeNiveles:
    def test_todo_id_declarado_tiene_su_escenario(self) -> None:
        """`discover_stages` se salta en silencio lo que no encuentra.

        Ese silencio es correcto en tiempo de ejecución —un escenario a medio
        hacer no debe impedir arrancar— pero significa que un identificador mal
        escrito en `STAGE_ORDER` acorta el juego sin avisar a nadie.
        """
        assert len(discover_stages()) == len(STAGE_ORDER), (
            f"{len(STAGE_ORDER)} escenarios declarados y sólo "
            f"{len(discover_stages())} encontrados: hay ranuras vacías en "
            f"STAGE_ORDER"
        )

    def test_se_recorren_los_dieciseis_y_se_llega_a_los_creditos(
        self, app_context,
    ) -> None:
        """El recorrido completo, como lo haría un jugador que termina."""
        manager = app_context.scene_manager
        superficie = pygame.Surface((320, 240))
        escenarios = discover_stages()

        manager.set_stage_queue(escenarios)
        manager.set_stage_index(0)
        manager._enter_next_stage()

        recorrido: list[str] = []
        for paso in range(len(escenarios) + 2):
            actual = type(manager.current).__name__
            recorrido.append(actual)
            if actual == "EndCreditsScene":
                break
            # Un fotograma de verdad: un escenario que revienta al dibujarse
            # está tan roto como uno que no se construye.
            manager.update(1 / 60)
            manager.current.draw(superficie)
            app_context.event_bus.emit(
                Events.STAGE_COMPLETE,
                stage_id=STAGE_ORDER[min(paso, len(STAGE_ORDER) - 1)],
            )
            app_context.event_bus.dispatch()

        assert recorrido[-1] == "EndCreditsScene", (
            f"la cadena no llega a los créditos; se quedó en {recorrido[-1]} "
            f"tras {len(recorrido)} escenarios: {recorrido}"
        )
        assert len(recorrido) == len(escenarios) + 1, (
            f"se esperaban {len(escenarios)} escenarios y los créditos; se "
            f"recorrieron {len(recorrido)}: {recorrido}"
        )

    def test_ningun_escenario_se_repite_en_el_recorrido(
        self, app_context,
    ) -> None:
        """Dos ranuras de `STAGE_ORDER` apuntando a la misma clase harían que
        el jugador repitiera un nivel y no llegara nunca al último."""
        nombres = [c.__name__ for c in discover_stages()]
        repetidos = {n for n in nombres if nombres.count(n) > 1}
        assert not repetidos, f"escenarios repetidos en la cadena: {repetidos}"


class TestElEventoQueAvanzaDeNivel:
    def test_stage_complete_sin_despachar_no_avanza(self, app_context) -> None:
        """Fija el contrato del bus, que es contraintuitivo y ya ha costado
        tiempo: `emit` encola, `dispatch` invoca.

        Si algún día `emit` pasara a invocar directamente, esta prueba falla y
        obliga a mirar el guard de reentrada de `dispatch`, que es lo que
        impide los bucles infinitos de emisión.
        """
        manager = app_context.scene_manager
        manager.set_stage_queue(discover_stages())
        manager.set_stage_index(0)
        manager._enter_next_stage()
        antes = manager.stage_index

        app_context.event_bus.emit(Events.STAGE_COMPLETE, stage_id="stage0")

        assert manager.stage_index == antes, (
            "emit() ha invocado al suscriptor sin dispatch(): el bus ya no "
            "difiere los eventos y el guard de reentrada deja de proteger"
        )

        app_context.event_bus.dispatch()
        assert manager.stage_index == antes + 1, (
            "tras dispatch() el escenario no avanzó"
        )
