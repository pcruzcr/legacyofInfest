"""AUD-533/549/550 — la pausa dejó de ser sólo "Reanudar / Guardar y
salir / Salir al título": `InventoryScene`, `SkillTreeScene`,
`WorldMapScene` (de sólo lectura) y `ShopScene` se volvieron alcanzables
desde ahí, cada una empujada como una escena aparte encima del nivel
pausado.

AUD-555 — pedido explícito del dueño: pestañas al estilo Ocarina of Time,
no una lista que empuja una pantalla por opción. Este archivo prueba el
panel nuevo (`PausaDeEscenario`, `stage_parts/pausa.py`): las tres
consultas (Equipo/Habilidades/Mapa) viven **embebidas** — nunca se
empujan a la pila real — y sólo la Tienda, en la pestaña "Menú", sigue
empujando una escena de verdad.
"""
from __future__ import annotations

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame
import pytest

from src.engine.input.action_map import Action


@pytest.fixture(scope="module")
def _video() -> None:
    pygame.init()
    pygame.font.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((800, 600))


def _partida():
    from src.engine.audio.audio_manager import AudioManager
    from src.engine.core.event_bus import EventBus
    from src.engine.core.game_context import GameContext
    from src.engine.core.save_manager import SaveManager
    from src.engine.input.input_manager import InputManager
    from src.engine.scene.scene_manager import SceneManager
    from src.framework.entities import entity_factory
    from src.stages.stage4_1b.stage4_1b import Stage4_1B

    entity_factory.ensure_registered()
    ctx = GameContext(
        input_manager=InputManager(), audio_manager=AudioManager(),
        scene_manager=None, event_bus=EventBus(), clock=None,
        save_manager=SaveManager(),
    )
    ctx.scene_manager = SceneManager(ctx)
    sc = Stage4_1B(ctx)
    ctx.scene_manager.push(sc)
    return ctx, sc


class _IM:
    """Entrada falsa: `is_action_just_pressed` dice sí sólo a la acción
    pedida, el resto de la interfaz de `InputManager` no hace falta para
    estas pruebas."""

    def __init__(self, *acciones: Action) -> None:
        self._acciones = set(acciones)

    def is_action_just_pressed(self, a: Action) -> bool:
        return a in self._acciones

    def is_action_held(self, a: Action) -> bool:
        return False

    def is_raw_key_pressed(self, k: int) -> bool:
        return False


class TestElPanelDePausaSeAbreEmbebido:
    """Pausar construye las tres pestañas de consulta — nunca las empuja
    a la pila real, a diferencia de como funcionaba antes de AUD-555."""

    def test_pausar_construye_las_tres_pestanas_sin_tocar_la_pila(
        self, _video,
    ) -> None:
        from src.engine.scenes.inventory_scene import InventoryScene
        from src.engine.scenes.skill_tree_scene import SkillTreeScene
        from src.engine.scenes.world_map_scene import WorldMapScene

        ctx, sc = _partida()
        sc._paused = True
        sc._abrir_panel_de_pausa()

        assert isinstance(sc._pausa_equipo, InventoryScene)
        assert isinstance(sc._pausa_habilidades, SkillTreeScene)
        assert isinstance(sc._pausa_mapa, WorldMapScene)
        # A diferencia de la lista vertical de antes, nada de esto se
        # empuja: la pila sigue teniendo sólo el nivel pausado.
        assert ctx.scene_manager.stack_size == 1
        assert ctx.scene_manager.current is sc

    def test_el_mapa_embebido_es_de_solo_lectura_y_no_es_independiente(
        self, _video,
    ) -> None:
        _ctx, sc = _partida()
        sc._paused = True
        sc._abrir_panel_de_pausa()

        assert sc._pausa_mapa._permitir_viajar is False
        assert sc._pausa_mapa._standalone is False

    def test_empieza_en_la_pestana_mapa(self, _video) -> None:
        _ctx, sc = _partida()
        sc._paused = True
        sc._abrir_panel_de_pausa()
        assert sc._pausa_tab == 0
        assert sc.PESTANAS_DE_PAUSA[sc._pausa_tab] == "Mapa"


class TestCambiarDePestana:
    def test_tab_next_avanza_y_da_la_vuelta(self, _video) -> None:
        ctx, sc = _partida()
        sc._paused = True
        sc._abrir_panel_de_pausa()

        ctx.input_manager = _IM(Action.TAB_NEXT)
        for esperado in (1, 2, 3, 0):
            sc._handle_pause_input()
            assert sc._pausa_tab == esperado

    def test_tab_prev_retrocede_y_da_la_vuelta(self, _video) -> None:
        ctx, sc = _partida()
        sc._paused = True
        sc._abrir_panel_de_pausa()

        ctx.input_manager = _IM(Action.TAB_PREV)
        for esperado in (3, 2, 1, 0):
            sc._handle_pause_input()
            assert sc._pausa_tab == esperado


class TestLaEntradaSeDelegaALaPestanaActiva:
    """Navegar dentro de una pestaña (por ejemplo, moverse en el árbol de
    habilidades) tiene que mover el cursor de esa pestaña embebida, no el
    del panel."""

    def test_mover_en_habilidades_cambia_su_seleccion(self, _video) -> None:
        ctx, sc = _partida()
        sc._paused = True
        sc._abrir_panel_de_pausa()
        sc._pausa_tab = 2  # Habilidades
        # `_dt` lo fija `update()` antes de llamar a `_handle_pause_input`
        # en cada fotograma real (`self._dt = dt`); esta prueba lo salta
        # a propósito para no montar un fotograma entero, así que lo
        # fija a mano.
        sc._dt = 0.016

        antes = sc._pausa_habilidades._seleccion
        ctx.input_manager = _IM(Action.MOVE_DOWN)
        sc._handle_pause_input()

        assert sc._pausa_habilidades._seleccion != antes


class TestCancelarCierraElPanelEnteroDesdeCualquierPestana:
    """Cancelar es un solo botón que cierra la pausa completa, sea cual
    sea la pestaña activa — así cancela Ocarina of Time, y es la razón de
    ser de `standalone=False`: las pestañas embebidas no pueden decidir
    esto por su cuenta, porque no son ellas quienes están en la pila."""

    @pytest.mark.parametrize("pestana", [0, 1, 2, 3])
    def test_cancelar_en_cualquier_pestana_cierra_la_pausa(
        self, _video, pestana,
    ) -> None:
        ctx, sc = _partida()
        sc._paused = True
        sc._abrir_panel_de_pausa()
        sc._pausa_tab = pestana

        ctx.input_manager = _IM(Action.CANCEL)
        sc._handle_pause_input()

        assert sc._paused is False
        assert sc._pausa_equipo is None
        assert sc._pausa_habilidades is None
        assert sc._pausa_mapa is None
        # Nunca se tocó la pila real: nada que reventar al cerrar.
        assert ctx.scene_manager.stack_size == 1


class TestLasEscenasEmbebidasNoPuedenVaciarLaPilaPorSuCuenta:
    """El motivo técnico de `standalone`: si `InventoryScene` embebida
    llamara a `scene_manager.pop()` por su cuenta al cancelar, sacaría al
    propio `StageScene` pausado de la pila (es lo único que hay), no a sí
    misma. Con `standalone=False` no hace nada — el panel es quien
    decide cerrar."""

    def test_cancelar_dentro_del_inventario_embebido_no_toca_la_pila(
        self, _video,
    ) -> None:
        from src.engine.scenes.inventory_scene import InventoryScene

        ctx, sc = _partida()
        inv = InventoryScene(ctx, standalone=False)
        ctx.input_manager = _IM(Action.CANCEL)

        inv.update(0.016)

        assert ctx.scene_manager.stack_size == 1
        assert ctx.scene_manager.current is sc

    def test_inventario_independiente_si_hace_pop(self, _video) -> None:
        """El seguro de siempre: `standalone` por defecto es `True`, así
        que abierta desde el título (sin `PausePanel` de por medio) sigue
        saliendo con `pop()` como antes de AUD-555."""
        from src.engine.scenes.inventory_scene import InventoryScene

        ctx, sc = _partida()
        ctx.scene_manager.push(InventoryScene(ctx))
        ctx.input_manager = _IM(Action.CANCEL)

        ctx.scene_manager.current.update(0.016)

        assert ctx.scene_manager.current is sc
        assert ctx.scene_manager.stack_size == 1


class TestLaPestanaDeMenu:
    """La cuarta pestaña: Tienda, Guardar y salir, Salir al título — la
    única que no es una consulta embebida."""

    def test_tienda_empuja_shopscene_de_verdad(self, _video) -> None:
        from src.engine.scenes.shop_scene import ShopScene

        ctx, sc = _partida()
        sc._paused = True
        sc._abrir_panel_de_pausa()
        sc._pausa_tab = 3
        sc._pausa_menu_seleccion = sc.OPCIONES_DEL_MENU_DE_PAUSA.index("Tienda")

        ctx.input_manager = _IM(Action.CONFIRM)
        sc._handle_pause_input()

        assert isinstance(ctx.scene_manager.current, ShopScene)
        assert ctx.scene_manager.stack_size == 2

    def test_cancelar_la_tienda_vuelve_al_panel_todavia_abierto(
        self, _video,
    ) -> None:
        """Cerrar la Tienda no debería cerrar también el panel de pausa
        que la abrió — el jugador vuelve a verlo, no al juego."""
        ctx, sc = _partida()
        sc._paused = True
        sc._abrir_panel_de_pausa()
        sc._pausa_tab = 3
        sc._pausa_menu_seleccion = sc.OPCIONES_DEL_MENU_DE_PAUSA.index("Tienda")
        ctx.input_manager = _IM(Action.CONFIRM)
        sc._handle_pause_input()

        tienda = ctx.scene_manager.current
        ctx.input_manager = _IM(Action.CANCEL)
        tienda.update(0.016)

        assert ctx.scene_manager.current is sc
        assert sc._paused is True
        assert sc._pausa_equipo is not None, (
            "cerrar la tienda no debería haber cerrado el panel de pausa"
        )

    def test_guardar_y_salir_llama_al_metodo_de_siempre(
        self, _video, monkeypatch,
    ) -> None:
        ctx, sc = _partida()
        sc._paused = True
        sc._abrir_panel_de_pausa()
        sc._pausa_tab = 3
        sc._pausa_menu_seleccion = sc.OPCIONES_DEL_MENU_DE_PAUSA.index("Guardar y salir")

        llamado = []
        monkeypatch.setattr(sc, "_save_and_quit", lambda: llamado.append(1))
        ctx.input_manager = _IM(Action.CONFIRM)
        sc._handle_pause_input()

        assert llamado == [1]

    def test_salir_al_titulo_llama_al_metodo_de_siempre(
        self, _video, monkeypatch,
    ) -> None:
        ctx, sc = _partida()
        sc._paused = True
        sc._abrir_panel_de_pausa()
        sc._pausa_tab = 3
        sc._pausa_menu_seleccion = sc.OPCIONES_DEL_MENU_DE_PAUSA.index("Salir al título")

        llamado = []
        monkeypatch.setattr(sc, "_quit_to_title", lambda: llamado.append(1))
        ctx.input_manager = _IM(Action.CONFIRM)
        sc._handle_pause_input()

        assert llamado == [1]


class TestElPanelDePausaEstaEnEspanol:
    def test_ninguna_pestana_ni_opcion_esta_en_ingles(self, _video) -> None:
        from src.framework.scenes.stage_scene import StageScene

        ascii_ingles = {
            "Equipment", "Skills", "Map", "Menu",
            "Resume", "Shop", "Save & Quit", "Quit to Title",
        }
        etiquetas = set(StageScene.PESTANAS_DE_PAUSA) | set(
            StageScene.OPCIONES_DEL_MENU_DE_PAUSA)
        assert not (etiquetas & ascii_ingles), (
            f"el panel de pausa tiene texto en inglés: {etiquetas}"
        )
