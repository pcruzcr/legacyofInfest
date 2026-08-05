"""AUD-283 — la consola de depuración existía y no la abría nadie.

Dos defectos, uno encima del otro
---------------------------------
`engine/scenes/debug_overlay.py` estaba escrito entero —consola, cola de
eventos, árbol de módulos— y **no tenía un solo llamante en `src/engine`**.
Tampoco una prueba. `docs/87` §15.7 lo describió como si funcionara.

Y la tecla con la que se abría, F3, es `LEARN_PHYSICS` en el mapa de acciones:
aunque alguien lo hubiera conectado, habría abierto la lección de física.

Por qué esto no lo cazó el barrido de huérfanos
-----------------------------------------------
`check_orphan_systems.py` busca símbolos que **las pruebas ejercitan y el juego
no invoca**. Lo que no prueba nadie y no usa nadie le resulta invisible. Este
fichero cierra ese hueco para la consola: a partir de ahora hay una prueba que
la ejercita, así que si vuelve a quedarse sin llamante, el barrido lo dirá.
"""
from __future__ import annotations

import pygame
import pytest

from src.engine.core.event_bus import EventBus
from src.engine.input.action_map import DEFAULT_KEY_BINDINGS
from src.engine.scenes.debug_overlay import (
    TECLA_ARBOL,
    TECLA_CONSOLA,
    TREE_LEVELS,
    DebugOverlay,
)


class _EntradaFalsa:
    def __init__(self, *teclas: int) -> None:
        self._teclas = set(teclas)

    def is_raw_key_pressed(self, tecla: int) -> bool:
        return tecla in self._teclas


class TestLaTeclaEstaLibre:
    def test_no_choca_con_ninguna_accion(self) -> None:
        """El defecto original: F3 ya era `LEARN_PHYSICS`."""
        ocupadas = {t for teclas in DEFAULT_KEY_BINDINGS.values() for t in teclas}
        assert TECLA_CONSOLA not in ocupadas
        assert TECLA_ARBOL not in ocupadas

    def test_ni_con_los_gizmos_del_escenario(self) -> None:
        """F1 abre las cajas de colisión dentro de un nivel (AUD-285)."""
        assert TECLA_CONSOLA != pygame.K_F1
        assert TECLA_ARBOL != pygame.K_F1


class TestElInterruptor:
    def test_arranca_cerrada(self) -> None:
        assert DebugOverlay().visible is False

    def test_la_tecla_la_abre_y_la_cierra(self) -> None:
        overlay = DebugOverlay()
        overlay.handle_input(_EntradaFalsa(TECLA_CONSOLA))
        assert overlay.visible is True
        overlay.handle_input(_EntradaFalsa(TECLA_CONSOLA))
        assert overlay.visible is False

    def test_el_arbol_rota_solo_con_la_consola_abierta(self) -> None:
        overlay = DebugOverlay()
        overlay.handle_input(_EntradaFalsa(TECLA_ARBOL))
        assert overlay._tree_level == 0
        overlay.handle_input(_EntradaFalsa(TECLA_CONSOLA))
        overlay.handle_input(_EntradaFalsa(TECLA_ARBOL))
        assert overlay._tree_level == 1

    def test_el_arbol_da_la_vuelta(self) -> None:
        overlay = DebugOverlay()
        overlay.handle_input(_EntradaFalsa(TECLA_CONSOLA))
        for _ in range(len(TREE_LEVELS)):
            overlay.handle_input(_EntradaFalsa(TECLA_ARBOL))
        assert overlay._tree_level == 0

    def test_sin_gestor_de_entrada_no_revienta(self) -> None:
        DebugOverlay().handle_input(None)


class TestLoQueEnsena:
    @pytest.fixture(autouse=True)
    def _video(self):
        pygame.init()
        if pygame.display.get_surface() is None:
            pygame.display.set_mode((800, 600))

    def test_cerrada_no_dibuja_nada(self) -> None:
        superficie = pygame.Surface((800, 600))
        superficie.fill((0, 0, 0))
        DebugOverlay().draw(superficie, 60.0)
        assert superficie.get_at((10, 10))[:3] == (0, 0, 0)

    def test_abierta_dibuja(self) -> None:
        superficie = pygame.Surface((800, 600))
        superficie.fill((0, 0, 0))
        overlay = DebugOverlay(EventBus())
        overlay.handle_input(_EntradaFalsa(TECLA_CONSOLA))
        overlay.draw(superficie, 60.0)
        assert superficie.get_at((10, 10))[:3] != (0, 0, 0)

    def test_acepta_las_medidas_de_la_escena(self) -> None:
        """Un diccionario y no una estructura fija: un menú no tiene enemigos
        que contar y no debería inventarse ceros."""
        superficie = pygame.Surface((800, 600))
        overlay = DebugOverlay(EventBus())
        overlay.handle_input(_EntradaFalsa(TECLA_CONSOLA))
        overlay.draw(superficie, 60.0, {"Enemigos": "3 simulados de 9 vivos"})


class TestElCableadoEnApp:
    """Que exista y funcione no basta: es exactamente lo que ya pasaba."""

    def test_app_la_construye_y_la_lee(self) -> None:
        import inspect

        from src.engine.core import app

        fuente = inspect.getsource(app)
        assert "self.debug_overlay = DebugOverlay(" in fuente, (
            "App no construye la consola: sigue siendo un módulo sin llamante"
        )
        assert "self.debug_overlay.handle_input(" in fuente
        assert "self.debug_overlay.draw(" in fuente


class TestLasMedidasDeUnEscenario:
    @pytest.fixture(autouse=True)
    def _video(self):
        pygame.init()
        if pygame.display.get_surface() is None:
            pygame.display.set_mode((800, 600))

    @pytest.fixture
    def escena(self):
        from src.engine.audio.audio_manager import AudioManager
        from src.engine.core.game_context import GameContext
        from src.engine.core.save_manager import SaveManager
        from src.engine.input.input_manager import InputManager
        from src.engine.scene.scene_manager import SceneManager
        from src.framework.entities import entity_factory
        from src.stages.stage0.stage0 import Stage0

        entity_factory.ensure_registered()
        ctx = GameContext(
            input_manager=InputManager(),
            audio_manager=AudioManager(),
            scene_manager=None,
            event_bus=EventBus(),
            clock=None,
            save_manager=SaveManager(),
        )
        ctx.scene_manager = SceneManager(ctx)
        escena = Stage0(ctx)
        escena.awake()
        escena.start()
        escena.on_enter()
        yield escena
        escena.on_exit()

    def test_un_escenario_publica_sus_cuentas(self, escena) -> None:
        medidas = escena.medidas_de_depuracion()
        assert "Enemigos" in medidas
        assert "Partículas" in medidas
        assert "Escuadrón" in medidas

    def test_distingue_simulados_de_vivos(self, escena) -> None:
        """Con el culling de AUD-279 «cuántos hay» y «cuántos se simulan» ya no
        son el mismo número, y confundirlos es cómo se diagnostica al revés."""
        assert "simulados de" in str(medidas_enemigos := escena.medidas_de_depuracion()["Enemigos"])
        assert medidas_enemigos

    def test_un_menu_no_publica_nada(self) -> None:
        """El valor por defecto de `BaseScene`, sobre una escena real.

        Se coge el menú de título y no un doble: lo que interesa es que una
        pantalla que no mide nada siga sin medir nada, no que el método exista.
        """
        from src.engine.scenes.title_scene import TitleScene

        assert TitleScene.medidas_de_depuracion is not None
        assert TitleScene.medidas_de_depuracion(object.__new__(TitleScene)) == {}
