from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

import pygame
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PGGAME_DISABLE_SOUND", "1")

from src.engine.core import settings
from src.engine.core.app import App
from src.engine.scene.base_scene import BaseScene
from src.engine.scene.scene_manager import SceneManager
from src.engine.scenes.achievement_scene import AchievementScene
from src.engine.scenes.bestiary_scene import BestiaryScene
from src.engine.scenes.demo_menu_scene import DemoMenuScene
from src.engine.scenes.inventory_scene import InventoryScene
from src.engine.scenes.options_scene import OptionsScene
from src.engine.scenes.splash_scene import SplashScene
from src.engine.scenes.story_scene import StoryScene
from src.engine.scenes.title_scene import TitleScene
from src.engine.scenes.tutorial_scene import TutorialScene
from src.engine.scenes.world_map_scene import WorldMapScene

OK = "[OK]"
FAIL = "[FAIL]"
WARN = "[WARN]"

KEY_MAP = {
    "DOWN": pygame.K_DOWN,
    "UP": pygame.K_UP,
    "CONFIRM": pygame.K_RETURN,
    "CANCEL": pygame.K_ESCAPE,
    "RIGHT": pygame.K_RIGHT,
    "LEFT": pygame.K_LEFT,
}


def _fake_event(event_type: int, **kwargs: Any) -> pygame.event.Event:
    return pygame.event.Event(event_type, kwargs)


class ContextManager:
    def __init__(self) -> None:
        self.app = App(use_gl=False)
        self.surf = pygame.Surface((settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT))

    @property
    def sm(self) -> SceneManager:
        return self.app.scene_manager

    @property
    def current(self) -> BaseScene:
        return self.sm.current

    def step(self, n_frames: int = 1) -> None:
        for _ in range(n_frames):
            events = pygame.event.get()
            self.app.input_manager.pump(events)
            if self.sm.stack_size > 0:
                self.current.process_events(events)
            self.sm.update(0.016)
            self.sm.transition.update(0.016)
            if self.sm.stack_size > 0:
                self.current.draw(self.surf)

    def press_key(self, key_name: str) -> None:
        key = KEY_MAP.get(key_name.upper())
        if key is not None:
            pygame.event.post(_fake_event(pygame.KEYDOWN, key=key))
            pygame.event.post(_fake_event(pygame.KEYUP, key=key))

    def replace_to_title(self) -> None:
        title = TitleScene(self.app.context)
        self.sm.replace(title)
        self.step(10)

    def validate_scene(self, name: str, scene_type: type) -> None:
        assert self.sm.stack_size > 0, f"{name} -- no scene on stack!"
        assert isinstance(self.current, scene_type), (
            f"{name} -- expected {scene_type.__name__}, got {type(self.current).__name__}"
        )


@pytest.fixture
def ctx() -> ContextManager:
    c = ContextManager()
    c.app.context.running = True
    return c


def _navigate_to(ctx: ContextManager, target_idx: int) -> None:
    for _ in range(target_idx):
        ctx.press_key("DOWN")
        ctx.step(3)


def test_la_presentacion_entrega_a_la_pantalla_de_partidas(
    ctx: ContextManager,
) -> None:
    """AUD-445 — antes entregaba al título; ahora, a elegir partida.

    El cambio es deliberado: desde el título se abren el mundo, el inventario,
    las habilidades y la tienda, y todos ellos enseñan progreso. Abrirlos antes
    de saber **de qué partida** es ese progreso enseña el de la que quedara
    activa por casualidad.
    """
    from src.engine.scenes.load_game_scene import LoadGameScene

    ctx.validate_scene("SplashScene start", SplashScene)
    ctx.step(250)
    assert ctx.sm.stack_size > 0, "SplashScene -- stack empty after timeout"
    assert isinstance(ctx.current, LoadGameScene), (
        f"la presentación entregó a {type(ctx.current).__name__}: el juego "
        f"sigue empezando sin preguntar en qué partida"
    )


def _title_option_index(title, label: str) -> int:
    """Índice de una opción del título por su etiqueta.

    AUD-068: la pantalla de título pasó de llevar `_options: list[str]` y un
    `_selected` propio a usar el `MenuList` compartido, para que su navegación
    dé la vuelta como la del resto del juego en vez de fijarse en los extremos.
    Estas pruebas preguntaban por la estructura interna; ahora preguntan por lo
    que se ve, que es lo que en realidad les importaba.
    """
    labels = [item.label for item in title._menu.items]
    assert label in labels, f"la opción {label!r} ya no existe en el título: {labels}"
    return labels.index(label)


def test_title_menu_options(ctx: ContextManager) -> None:
    checks = [
        ("START", StoryScene),
        ("TUTORIAL", TutorialScene),
        ("WORLD MAP", WorldMapScene),
        ("INVENTORY", InventoryScene),
        ("BESTIARY", BestiaryScene),
        ("ACHIEVEMENTS", AchievementScene),
        ("ACADEMIC DEMOS", DemoMenuScene),
        ("OPTIONS", OptionsScene),
    ]
    for label, expected_type in checks:
        ctx.replace_to_title()
        ctx.step(10)
        assert isinstance(ctx.current, TitleScene), f"TitleScene replacement failed for '{label}'"
        title: TitleScene = ctx.current
        idx = _title_option_index(title, label)
        _navigate_to(ctx, idx)
        ctx.press_key("CONFIRM")
        ctx.step(30)
        assert ctx.sm.stack_size > 0, f"{label} -- stack empty after selection"
        actual_type = type(ctx.current)
        assert actual_type is expected_type, (
            f"{label} -- expected {expected_type.__name__}, got {actual_type.__name__}"
        )
        ctx.current.draw(ctx.surf)
        ctx.current.update(0.016)


def test_options_scene(ctx: ContextManager) -> None:
    ctx.replace_to_title()
    ctx.step(10)
    title: TitleScene = ctx.current
    idx = _title_option_index(title, "OPTIONS")
    _navigate_to(ctx, idx)
    ctx.press_key("CONFIRM")
    ctx.step(30)
    ctx.validate_scene("OptionsScene", OptionsScene)
    ctx.press_key("CANCEL")
    ctx.step(30)


def test_demo_menu(ctx: ContextManager) -> None:
    ctx.replace_to_title()
    ctx.step(10)
    title: TitleScene = ctx.current
    idx = _title_option_index(title, "ACADEMIC DEMOS")
    _navigate_to(ctx, idx)
    ctx.press_key("CONFIRM")
    ctx.step(30)
    ctx.validate_scene("DemoMenuScene", DemoMenuScene)
    ctx.press_key("CANCEL")
    ctx.step(30)


def test_tutorial_scene(ctx: ContextManager) -> None:
    ctx.replace_to_title()
    ctx.step(10)
    _from_title_to(ctx, "TUTORIAL")
    ctx.validate_scene("TutorialScene", TutorialScene)
    ctx.current.draw(ctx.surf)
    ctx.current.update(0.016)
    ctx.press_key("CANCEL")
    ctx.step(30)


def test_world_map_scene(ctx: ContextManager) -> None:
    ctx.replace_to_title()
    ctx.step(10)
    _from_title_to(ctx, "WORLD MAP")
    ctx.validate_scene("WorldMapScene", WorldMapScene)
    ctx.current.draw(ctx.surf)
    ctx.current.update(0.016)
    ctx.press_key("CANCEL")
    ctx.step(30)


def test_inventory_scene(ctx: ContextManager) -> None:
    ctx.replace_to_title()
    ctx.step(10)
    _from_title_to(ctx, "INVENTORY")
    ctx.validate_scene("InventoryScene", InventoryScene)
    ctx.current.draw(ctx.surf)
    ctx.current.update(0.016)
    ctx.press_key("CANCEL")
    ctx.step(30)


def test_bestiary_scene(ctx: ContextManager) -> None:
    ctx.replace_to_title()
    ctx.step(10)
    _from_title_to(ctx, "BESTIARY")
    ctx.validate_scene("BestiaryScene", BestiaryScene)
    ctx.current.draw(ctx.surf)
    ctx.current.update(0.016)
    ctx.press_key("CANCEL")
    ctx.step(30)


def test_achievement_scene(ctx: ContextManager) -> None:
    ctx.replace_to_title()
    ctx.step(10)
    _from_title_to(ctx, "ACHIEVEMENTS")
    ctx.validate_scene("AchievementScene", AchievementScene)
    ctx.current.draw(ctx.surf)
    ctx.current.update(0.016)
    ctx.press_key("CANCEL")
    ctx.step(30)


def test_quit_action(ctx: ContextManager) -> None:
    ctx.replace_to_title()
    ctx.step(10)
    _from_title_to(ctx, "QUIT")
    ctx.step(5)
    assert not ctx.app.context.running, "QUIT did not stop context.running"


def test_all_menus_return(ctx: ContextManager) -> None:
    scenes = [
        ("OptionsScene", OptionsScene),
        ("TutorialScene", TutorialScene),
        ("WorldMapScene", WorldMapScene),
        ("InventoryScene", InventoryScene),
        ("BestiaryScene", BestiaryScene),
        ("AchievementScene", AchievementScene),
    ]
    for name, scene_type in scenes:
        ctx.replace_to_title()
        ctx.step(10)
        scene = scene_type(ctx.app.context)
        ctx.app.context.running = True
        ctx.sm.push(scene)
        ctx.step(80)
        ctx.press_key("CANCEL")
        ctx.step(100)
        assert ctx.sm.stack_size > 0, f"{name} -- stack empty after CANCEL"
        if not isinstance(ctx.current, TitleScene):
            ctx.step(100)
            assert ctx.sm.stack_size > 0, f"{name} -- stack empty after CANCEL (2nd attempt)"
            assert isinstance(ctx.current, TitleScene), (
                f"{name} -> {type(ctx.current).__name__} (expected TitleScene)"
            )


def _from_title_to(ctx: ContextManager, option_name: str) -> None:
    title: TitleScene = ctx.current
    try:
        idx = _title_option_index(title, option_name)
    except ValueError:
        idx = 0
    _navigate_to(ctx, idx)
    ctx.press_key("CONFIRM")
    ctx.step(30)


def main() -> int:
    print("=" * 60)
    print("LEGACY OF INFEST -- COMPREHENSIVE MENU NAVIGATION TEST")
    print("=" * 60)
    failed = 0
    total = 0
    ctx = ContextManager()
    print(f"App created: {ctx.sm.stack_size} scene(s) -- SplashScene")
    ctx.app.context.running = True

    tests = [
        ("Splash -> Partidas", test_la_presentacion_entrega_a_la_pantalla_de_partidas),
        ("Title menu options", test_title_menu_options),
        ("Options scene", test_options_scene),
        ("Demo menu", test_demo_menu),
        ("Tutorial scene", test_tutorial_scene),
        ("World map scene", test_world_map_scene),
        ("Inventory scene", test_inventory_scene),
        ("Bestiary scene", test_bestiary_scene),
        ("Achievement scene", test_achievement_scene),
        ("QUIT action", test_quit_action),
        ("All menus -> Title", test_all_menus_return),
    ]

    for name, func in tests:
        total += 1
        try:
            func(ctx)
            print(f"  PASS: {name}")
        except AssertionError as e:
            print(f"  FAIL: {name} -- {e}")
            failed += 1
        except Exception as e:
            print(f"  ERROR: {name} -- {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print(f"\n{'=' * 60}")
    print(f"RESULTS: {total - failed}/{total} passed, {failed} failed")
    print(f"{'=' * 60}")
    return 1 if failed > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
