"""AUD-266 — terminar un nivel elegido en el mapa del mundo tiraba a los créditos.

El defecto
==========
El mapa del mundo abre el escenario con
`scene_manager.replace(cls(self.context))` y **nunca toca la cola de
escenarios**. Esa cola sólo la escriben `story_scene` (campaña nueva),
`load_game_scene` (partida cargada) y `boss_rush_entry`.

Cuando el nivel termina, `SceneManager._on_stage_complete` hace:

    self._stage_index += 1
    self._enter_next_stage()

y `_enter_next_stage` compara el índice contra una cola **vacía**, así que cae
por la rama de «no quedan escenarios» y **reemplaza la escena por los créditos
finales**.

Medido: el jugador entra al mapa del mundo, elige *2-2 Entrada y Antenas*, lo
completa, y el juego le pone los créditos. Si la cola venía de una partida
cargada, es peor: le manda a un nivel que no tiene nada que ver con el que
acaba de jugar.

La corrección
-------------
El mapa declara la cola entera —los escenarios en el orden del registro, que es
el mismo que dibuja— y coloca el índice en el nodo elegido. A partir de ahí el
encadenado es el de siempre: terminar 2-2 lleva a 2-3, y terminar el último
lleva a los créditos porque **de verdad** no queda nada.

No se inventa una cola nueva: es exactamente la misma lista que `story_scene`
pone al empezar la campaña. Un solo orden de juego, no dos.
"""
from __future__ import annotations

import pygame
import pytest


@pytest.fixture
def app():
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((800, 600))
    from src.engine.core.app import App

    return App(use_gl=False)


@pytest.fixture
def mapa(app):
    from src.engine.scenes.world_map_scene import WorldMapScene

    escena = WorldMapScene(app.context)
    escena.on_enter()
    for n in escena._nodes:
        n["unlocked"] = True
    return escena


class TestLaColaQuedaDeclarada:
    def test_entrar_declara_la_cola_completa(self, mapa, app) -> None:
        gestor = app.context.scene_manager
        gestor.set_stage_queue([])

        mapa._entrar(mapa._nodes[0])

        assert len(gestor._stage_queue) == len(mapa._nodes), (
            "el mapa abre un nivel sin declarar la cola: al terminarlo, "
            "SceneManager cree que no quedan escenarios y pone los créditos"
        )

    def test_el_indice_apunta_al_nodo_elegido(self, mapa, app) -> None:
        gestor = app.context.scene_manager
        elegido = 4

        mapa._entrar(mapa._nodes[elegido])

        assert gestor.stage_index == elegido

    def test_terminar_lleva_al_siguiente_y_no_a_los_creditos(self, mapa, app) -> None:
        """La comprobación que define el defecto."""
        from src.engine.core.events import Events

        gestor = app.context.scene_manager
        elegido = 2
        mapa._entrar(mapa._nodes[elegido])
        esperada = mapa._nodes[elegido + 1]["scene"]

        app.context.event_bus.emit(
            Events.STAGE_COMPLETE, stage_id=mapa._nodes[elegido]["id"])
        app.context.event_bus.dispatch()

        assert isinstance(gestor.current, esperada), (
            f"tras completar el nivel elegido, la escena es "
            f"{type(gestor.current).__name__} y debería ser {esperada.__name__}"
        )

    def test_terminar_el_ultimo_si_lleva_a_los_creditos(self, mapa, app) -> None:
        """Los créditos siguen estando donde deben: al final de verdad."""
        from src.engine.core.events import Events

        gestor = app.context.scene_manager
        ultimo = len(mapa._nodes) - 1
        mapa._entrar(mapa._nodes[ultimo])

        app.context.event_bus.emit(
            Events.STAGE_COMPLETE, stage_id=mapa._nodes[ultimo]["id"])
        app.context.event_bus.dispatch()

        assert type(gestor.current).__name__ == "EndCreditsScene"

    def test_un_nodo_bloqueado_no_toca_la_cola(self, mapa, app) -> None:
        gestor = app.context.scene_manager
        gestor.set_stage_queue([])
        mapa._nodes[3]["unlocked"] = False

        assert mapa._entrar(mapa._nodes[3]) is False
        assert gestor._stage_queue == []


class TestLaNavegacionSigueLaRejilla:
    """Arriba y abajo tienen que moverse **una fila**, no dos nodos.

    El zigzag coloca tres nodos por fila (`_serpiente`), y `update()` sumaba
    ±2 al índice — una constante que sobrevivió de cuando la lista estaba
    escrita a mano con cinco nodos. Con dieciséis, bajar te dejaba en un sitio
    que no está debajo de nada.
    """

    def test_el_salto_vertical_es_el_ancho_de_la_fila(self) -> None:
        from src.engine.scenes.world_map_scene import NODOS_POR_FILA, WorldMapScene

        assert WorldMapScene._SALTO_VERTICAL == NODOS_POR_FILA

    def test_el_zigzag_usa_esa_misma_constante(self) -> None:
        """Si alguien cambia una y no la otra, la navegación miente otra vez."""
        from src.engine.scenes.world_map_scene import NODOS_POR_FILA, _serpiente

        # Dos nodos separados por una fila comparten columna sólo si el
        # zigzag y el salto hablan del mismo ancho.
        filas = [_serpiente(i, 12)[1] for i in range(12)]
        assert filas[0] != filas[NODOS_POR_FILA], "no cambia de fila al saltar"
        assert filas[0] == filas[NODOS_POR_FILA - 1], "la fila no tiene ese ancho"
