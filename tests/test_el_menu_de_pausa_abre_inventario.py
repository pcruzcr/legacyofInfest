"""AUD-533 — `InventoryScene` y `SkillTreeScene` estaban completas y
probadas, y sólo se podían abrir desde el título: el mismo patrón de
"sistema construido, camino real inexistente" que ya se vio con
`SwimmingState` (AUD-528) y `WaterEffect` (AUD-525). El menú de pausa de
una partida en curso no ofrecía ninguna de las dos.

Estas pruebas conducen el camino real: pausar una partida, abrir el
inventario desde el menú de pausa, y volver — sin que "volver" signifique
"perder la partida y aparecer en el título", que era el defecto simétrico
del lado de `InventoryScene` (salía siempre con
`replace(TitleScene(...))`, sin importar quién la hubiera abierto).
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


class TestElInventarioSeAbreEnPausa:
    def test_seleccionar_inventario_empuja_la_escena_sin_perder_la_partida(
        self, _video,
    ) -> None:
        from src.engine.scenes.inventory_scene import InventoryScene

        ctx, sc = _partida()
        sc._paused = True
        sc._pause_selected = sc._pause_options.index("Inventario")

        sc._abrir_inventario()

        assert isinstance(ctx.scene_manager.current, InventoryScene), (
            "elegir «Inventario» en pausa no abre InventoryScene"
        )
        # La partida sigue en la pila, no se perdió — sólo quedó debajo.
        assert ctx.scene_manager.stack_size == 2

    def test_cancelar_el_inventario_vuelve_a_la_partida_pausada_no_al_titulo(
        self, _video,
    ) -> None:
        from src.engine.scenes.title_scene import TitleScene

        ctx, sc = _partida()
        sc._paused = True
        sc._abrir_inventario()

        # Dentro de InventoryScene: cancelar. `.input` es una propiedad de
        # sólo lectura que lee `context.input_manager` — se sustituye ahí.
        inv = ctx.scene_manager.current
        im_falso = type("IM", (), {
            "is_action_just_pressed": lambda self, a: a == Action.CANCEL,
        })()
        ctx.input_manager = im_falso
        inv.update(0.016)

        assert ctx.scene_manager.current is sc, (
            f"cancelar el inventario lleva a {type(ctx.scene_manager.current).__name__}, "
            f"no de vuelta a la partida pausada"
        )
        assert not isinstance(ctx.scene_manager.current, TitleScene)
        # La partida sigue pausada — «Reanudar» es una elección explícita,
        # no algo que cancelar el inventario deba decidir por el jugador.
        assert sc._paused is True

    def test_seleccionar_arbol_de_habilidades_empuja_la_escena(
        self, _video,
    ) -> None:
        from src.engine.scenes.skill_tree_scene import SkillTreeScene

        ctx, sc = _partida()
        sc._paused = True

        sc._abrir_arbol_de_habilidades()

        assert isinstance(ctx.scene_manager.current, SkillTreeScene)
        assert ctx.scene_manager.stack_size == 2


class TestElMenuDePausaEstaEnEspanol:
    def test_ninguna_opcion_de_pausa_esta_en_ingles(self, _video) -> None:
        """AUD-533 — de paso: el menú tenía "Resume"/"Save & Quit"/
        "Quit to Title" en inglés, violando la invariante 5 de CLAUDE.md
        ("todo en español, sin excepciones") — `_draw_pause_menu` dibuja
        cada opción tal cual, sin pasar por el catálogo de i18n."""
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

        ascii_ingles = {"Resume", "Save & Quit", "Quit to Title"}
        assert not (set(sc._pause_options) & ascii_ingles), (
            f"el menú de pausa sigue teniendo texto en inglés: {sc._pause_options}"
        )
