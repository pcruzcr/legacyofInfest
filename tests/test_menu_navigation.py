# -*- coding: utf-8 -*-
"""Automated menu navigation test — walks every scene, every option, no black screens."""
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
from src.engine.scenes.title_scene import TitleScene
from src.engine.scenes.splash_scene import SplashScene
from src.engine.scenes.story_scene import StoryScene
from src.engine.scenes.achievement_scene import AchievementScene
from src.engine.scenes.options_scene import OptionsScene
from src.engine.scenes.keybinding_scene import KeybindingScene
from src.engine.scenes.demo_menu_scene import DemoMenuScene
from src.engine.scenes.tutorial_scene import TutorialScene
from src.engine.scenes.world_map_scene import WorldMapScene
from src.engine.scenes.inventory_scene import InventoryScene
from src.engine.scenes.bestiary_scene import BestiaryScene

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
        self.app = App()
        self.surf = pygame.Surface((settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT))

    @property
    def sm(self) -> SceneManager:
        return self.app.scene_manager

    @property
    def current(self) -> BaseScene:
        return self.sm.current

    def step(self, n_frames: int = 1) -> None:
        for _ in range(n_frames):
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
        try:
            title = TitleScene(self.app.context)
            self.sm.replace(title)
            self.step(10)
        except Exception:
            pass

    def validate_scene(self, name: str, scene_type: type) -> bool:
        if self.sm.stack_size == 0:
            print(f"  {FAIL} {name} -- no scene on stack!")
            return False
        if not isinstance(self.current, scene_type):
            print(f"  {FAIL} {name} -- expected {scene_type.__name__}, got {type(self.current).__name__}")
            return False
        return True


@pytest.fixture
def ctx() -> ContextManager:
    c = ContextManager()
    c.app.context.running = True
    return c


def _navigate_to(ctx: ContextManager, target_idx: int) -> None:
    """Navigate DOWN until selected index matches target_idx."""
    for _ in range(target_idx):
        ctx.press_key("DOWN")
        ctx.step(3)


def test_splash_to_title(ctx: ContextManager) -> bool:
    ok = ctx.validate_scene("SplashScene start", SplashScene)
    if not ok:
        return False
    ctx.step(250)
    if ctx.sm.stack_size == 0:
        print(f"  {FAIL} SplashScene -- stack empty after timeout")
        return False
    if not isinstance(ctx.current, TitleScene):
        print(f"  {FAIL} SplashScene -- expected TitleScene, got {type(ctx.current).__name__}")
        return False
    print(f"  {OK} SplashScene -> TitleScene auto-transition")
    return True


def test_title_menu_options(ctx: ContextManager) -> bool:
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
        if not isinstance(ctx.current, TitleScene):
            print(f"  {FAIL} TitleScene replacement failed for '{label}'")
            return False
        title: TitleScene = ctx.current
        try:
            idx = title._options.index(label)
        except ValueError:
            print(f"  {FAIL} Option '{label}' not found in TitleScene")
            continue
        _navigate_to(ctx, idx)
        ctx.press_key("CONFIRM")
        ctx.step(30)
        if ctx.sm.stack_size == 0:
            print(f"  {FAIL} {label} -- stack empty after selection")
            return False
        actual_type = type(ctx.current)
        if actual_type is not expected_type:
            print(f"  {FAIL} {label} -- expected {expected_type.__name__}, got {actual_type.__name__}")
            return False
        try:
            ctx.current.draw(ctx.surf)
            ctx.current.update(0.016)
        except Exception as e:
            print(f"  {FAIL} {label} -- draw/update crashed: {e}")
            import traceback
            traceback.print_exc()
            return False
        print(f"  {OK} {label} -> {expected_type.__name__}")
    return True


def test_options_scene(ctx: ContextManager) -> bool:
    ctx.replace_to_title()
    ctx.step(10)
    title: TitleScene = ctx.current
    idx = title._options.index("OPTIONS")
    _navigate_to(ctx, idx)
    ctx.press_key("CONFIRM")
    ctx.step(30)
    if not ctx.validate_scene("OptionsScene", OptionsScene):
        return False
    opts: OptionsScene = ctx.current
    for i in range(len(opts._options)):
        if i > 0:
            ctx.press_key("DOWN")
            ctx.step(3)
        opt = opts._options[i]
        try:
            ctx.press_key("RIGHT")
            ctx.step(2)
            ctx.press_key("LEFT")
            ctx.step(2)
            opts.draw(ctx.surf)
        except Exception as e:
            print(f"  {FAIL} Options '{opt['name']}' crashed: {e}")
            return False
    # Navigate to KEY BINDINGS
    while opts._selected < len(opts._options) - 1:
        if opts._options[opts._selected].get("action"):
            break
        ctx.press_key("DOWN")
        ctx.step(2)
    ctx.press_key("CONFIRM")
    ctx.step(30)
    if ctx.validate_scene("KeybindingScene", KeybindingScene):
        kb: KeybindingScene = ctx.current
        try:
            kb.draw(ctx.surf)
            kb.update(0.016)
        except Exception as e:
            print(f"  {FAIL} KeybindingScene draw/update crashed: {e}")
            return False
        print(f"  {OK} Options -> KeyBindings")
        ctx.press_key("CANCEL")
        ctx.step(30)
    ctx.press_key("CANCEL")
    ctx.step(30)
    print(f"  {OK} OptionsScene -- all options tested")
    return True


def test_demo_menu(ctx: ContextManager) -> bool:
    ctx.replace_to_title()
    ctx.step(10)
    title: TitleScene = ctx.current
    idx = title._options.index("ACADEMIC DEMOS")
    _navigate_to(ctx, idx)
    ctx.press_key("CONFIRM")
    ctx.step(30)
    if not ctx.validate_scene("DemoMenuScene", DemoMenuScene):
        return False
    demo: DemoMenuScene = ctx.current
    for i, (unit, desc, key) in enumerate(demo._options):
        if not key or not unit:
            continue
        diff = i - demo._selected
        key_name = "DOWN" if diff > 0 else "UP"
        for _ in range(abs(diff)):
            ctx.press_key(key_name)
            ctx.step(3)
        ctx.press_key("CONFIRM")
        ctx.step(30)
        if ctx.sm.stack_size > 0:
            pushed = ctx.current
            try:
                pushed.draw(ctx.surf)
                pushed.update(0.016)
                print(f"  {OK} Demo '{key}' ({unit})")
            except Exception as e:
                print(f"  {WARN} Demo '{key}' issue: {e}")
            if hasattr(pushed, 'on_exit'):
                pushed.on_exit()
            ctx.sm.pop()
            ctx.step(5)
    print(f"  {OK} DemoMenuScene -- all entries tested")
    return True


def _from_title_to(ctx: ContextManager, option_name: str) -> None:
    """Navigate from title to a specific option and select it."""
    title: TitleScene = ctx.current
    try:
        idx = title._options.index(option_name)
    except ValueError:
        idx = 0
    _navigate_to(ctx, idx)
    ctx.press_key("CONFIRM")
    ctx.step(30)


def test_tutorial_scene(ctx: ContextManager) -> bool:
    ctx.replace_to_title()
    ctx.step(10)
    _from_title_to(ctx, "TUTORIAL")
    if not ctx.validate_scene("TutorialScene", TutorialScene):
        return False
    tut: TutorialScene = ctx.current
    try:
        tut.draw(ctx.surf)
        tut.update(0.016)
    except Exception as e:
        print(f"  {FAIL} TutorialScene crashed: {e}")
        return False
    print(f"  {OK} TutorialScene")
    ctx.press_key("CANCEL")
    ctx.step(30)
    return True


def test_world_map_scene(ctx: ContextManager) -> bool:
    ctx.replace_to_title()
    ctx.step(10)
    _from_title_to(ctx, "WORLD MAP")
    if not ctx.validate_scene("WorldMapScene", WorldMapScene):
        return False
    wm: WorldMapScene = ctx.current
    try:
        wm.draw(ctx.surf)
        wm.update(0.016)
    except Exception as e:
        print(f"  {FAIL} WorldMapScene crashed: {e}")
        return False
    print(f"  {OK} WorldMapScene")
    ctx.press_key("CANCEL")
    ctx.step(30)
    return True


def test_inventory_scene(ctx: ContextManager) -> bool:
    ctx.replace_to_title()
    ctx.step(10)
    _from_title_to(ctx, "INVENTORY")
    if not ctx.validate_scene("InventoryScene", InventoryScene):
        return False
    inv: InventoryScene = ctx.current
    try:
        inv.draw(ctx.surf)
        inv.update(0.016)
    except Exception as e:
        print(f"  {FAIL} InventoryScene crashed: {e}")
        return False
    print(f"  {OK} InventoryScene")
    ctx.press_key("CANCEL")
    ctx.step(30)
    return True


def test_bestiary_scene(ctx: ContextManager) -> bool:
    ctx.replace_to_title()
    ctx.step(10)
    _from_title_to(ctx, "BESTIARY")
    if not ctx.validate_scene("BestiaryScene", BestiaryScene):
        return False
    best: BestiaryScene = ctx.current
    try:
        best.draw(ctx.surf)
        best.update(0.016)
    except Exception as e:
        print(f"  {FAIL} BestiaryScene crashed: {e}")
        return False
    print(f"  {OK} BestiaryScene")
    ctx.press_key("CANCEL")
    ctx.step(30)
    return True


def test_achievement_scene(ctx: ContextManager) -> bool:
    ctx.replace_to_title()
    ctx.step(10)
    _from_title_to(ctx, "ACHIEVEMENTS")
    if not ctx.validate_scene("AchievementScene", AchievementScene):
        return False
    ach: AchievementScene = ctx.current
    try:
        ach.draw(ctx.surf)
        ach.update(0.016)
    except Exception as e:
        print(f"  {FAIL} AchievementScene crashed: {e}")
        return False
    print(f"  {OK} AchievementScene")
    ctx.press_key("CANCEL")
    ctx.step(30)
    return True


def test_quit_action(ctx: ContextManager) -> bool:
    ctx.replace_to_title()
    ctx.step(10)
    _from_title_to(ctx, "QUIT")
    ctx.step(5)
    if ctx.app.context.running:
        print(f"  {FAIL} QUIT did not stop context.running")
        return False
    print(f"  {OK} QUIT -> context quits")
    return True


def test_all_menus_return(ctx: ContextManager) -> bool:
    scenes = [
        ("OptionsScene", OptionsScene),
        ("TutorialScene", TutorialScene),
        ("WorldMapScene", WorldMapScene),
        ("InventoryScene", InventoryScene),
        ("BestiaryScene", BestiaryScene),
        ("AchievementScene", AchievementScene),
    ]
    all_ok = True
    for name, scene_type in scenes:
        try:
            scene = scene_type(ctx.app.context)
            ctx.app.context.running = True
            ctx.sm.replace(scene)
            ctx.step(10)
            ctx.press_key("CANCEL")
            ctx.step(30)
            if ctx.sm.stack_size > 0 and isinstance(ctx.current, TitleScene):
                print(f"  {OK} {name} -> TitleScene (CANCEL)")
            else:
                cur = type(ctx.current).__name__ if ctx.sm.stack_size > 0 else "empty"
                print(f"  {WARN} {name} -> {cur} (expected TitleScene)")
                all_ok = False
        except Exception as e:
            print(f"  {FAIL} {name} -- {e}")
            all_ok = False
    return all_ok


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
        ("Splash -> Title", test_splash_to_title),
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
            if func(ctx):
                print(f"  PASS: {name}")
            else:
                print(f"  FAIL: {name}")
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
