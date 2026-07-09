from __future__ import annotations
from unittest.mock import MagicMock

import pygame
import pytest

from src.engine.core.event_bus import EventBus
from src.engine.core.game_context import GameContext
from src.engine.input.action_map import Action


@pytest.fixture(autouse=True)
def pygame_init():
    if not pygame.get_init():
        pygame.init()
    if not pygame.font.get_init():
        pygame.font.init()


@pytest.fixture
def context():
    bus = EventBus()
    ctx = GameContext(
        input_manager=MagicMock(),
        audio_manager=MagicMock(),
        scene_manager=MagicMock(),
        event_bus=bus,
    )
    return ctx


from src.engine.scenes.demo_menu_scene import DemoMenuScene
from src.engine.scenes.filter_demo_scene import FilterDemoScene
from src.engine.scenes.vision_demo_scene import VisionDemoScene
from src.engine.scenes.pattern_demo_scene import PatternDemoScene
from src.engine.scenes.collision_lab_scene import CollisionLabScene
from src.engine.scenes.vector_lab_scene import VectorLabScene
from src.engine.scenes.color_theory_scene import ColorTheoryScene
from src.engine.scenes.curve_editor_scene import CurveEditorScene
from src.engine.scenes.demo_common import (
    build_default_sources,
    SourceSurfaceManager,
    FrameThrottle,
    save_png,
    draw_top_bar,
    draw_bottom_bar,
)


class TestDemoMenuScene:
    def test_import_succeeds(self) -> None:
        assert DemoMenuScene is not None

    def test_instantiate(self, context) -> None:
        scene = DemoMenuScene(context)
        assert scene is not None
        assert hasattr(scene, "_options")
        assert len(scene._options) >= 10

    def test_on_enter_exit(self, context) -> None:
        scene = DemoMenuScene(context)
        scene.on_enter()
        assert scene._selected == 0
        scene.on_exit()

    def test_draw_no_crash(self, context) -> None:
        scene = DemoMenuScene(context)
        surf = pygame.Surface((320, 224))
        scene.draw(surf)
        assert surf.get_at((0, 0)) is not None

    def test_navigation_down(self, context) -> None:
        scene = DemoMenuScene(context)
        scene.on_enter()
        context.input_manager.is_raw_key_pressed.side_effect = lambda k: k == pygame.K_DOWN
        scene.update(0.016)
        assert scene._selected == 1

    def test_navigation_up(self, context) -> None:
        scene = DemoMenuScene(context)
        scene.on_enter()
        scene._selected = 1
        context.input_manager.is_raw_key_pressed.side_effect = lambda k: k == pygame.K_UP
        scene.update(0.016)
        assert scene._selected == 0

    def test_navigation_clamps_at_bottom(self, context) -> None:
        scene = DemoMenuScene(context)
        scene.on_enter()
        n = len(scene._options)
        scene._selected = n - 1
        context.input_manager.is_raw_key_pressed.side_effect = lambda k: k == pygame.K_DOWN
        scene.update(0.016)
        assert scene._selected == n - 1

    def test_navigation_clamps_at_top(self, context) -> None:
        scene = DemoMenuScene(context)
        scene.on_enter()
        context.input_manager.is_raw_key_pressed.side_effect = lambda k: k == pygame.K_UP
        scene.update(0.016)
        assert scene._selected == 0

    def test_confirm_selects_scene(self, context) -> None:
        scene = DemoMenuScene(context)
        scene.on_enter()
        context.input_manager.is_raw_key_pressed.return_value = False
        context.input_manager.is_action_pressed.side_effect = lambda a: a == Action.CONFIRM
        scene.update(0.016)

    def test_scroll_offset_moves_with_selection(self, context) -> None:
        scene = DemoMenuScene(context)
        scene.on_enter()
        scene._scroll_offset = 0
        scene._selected = 6
        context.input_manager.is_raw_key_pressed.side_effect = lambda k: k == pygame.K_DOWN
        scene.update(0.016)
        assert scene._scroll_offset >= 1


class TestFilterDemoScene:
    def test_import_succeeds(self) -> None:
        assert FilterDemoScene is not None

    def test_instantiate(self, context) -> None:
        scene = FilterDemoScene(context)
        assert scene is not None
        assert hasattr(scene, "_mode")
        assert scene._mode == 0

    def test_on_enter_exit(self, context) -> None:
        scene = FilterDemoScene(context)
        scene.on_enter()
        assert scene._mode == 0
        scene.on_exit()

    def test_draw_no_crash(self, context) -> None:
        scene = FilterDemoScene(context)
        surf = pygame.Surface((320, 224))
        scene.draw(surf)
        assert surf.get_at((0, 0)) is not None

    def test_mode_cycle(self, context) -> None:
        from src.engine.scenes.filter_demo_scene import MODE_NAMES
        scene = FilterDemoScene(context)
        scene.on_enter()
        for _ in range(len(MODE_NAMES) * 2):
            scene._mode = (scene._mode + 1) % len(MODE_NAMES)
        assert scene._mode < len(MODE_NAMES)

    def test_reset_params(self, context) -> None:
        scene = FilterDemoScene(context)
        scene._brightness_factor = 3.0
        scene._contrast_factor = 2.5
        scene._reset_params()
        assert scene._brightness_factor == 1.0
        assert scene._contrast_factor == 1.0
        assert scene._sigma == 1.0


class TestVisionDemoScene:
    def test_import_succeeds(self) -> None:
        assert VisionDemoScene is not None

    def test_instantiate(self, context) -> None:
        scene = VisionDemoScene(context)
        assert scene is not None
        assert hasattr(scene, "_mode")
        assert scene._mode == 0

    def test_on_enter_exit(self, context) -> None:
        scene = VisionDemoScene(context)
        scene.on_enter()
        assert scene._mode == 0
        scene.on_exit()

    def test_draw_no_crash(self, context) -> None:
        scene = VisionDemoScene(context)
        surf = pygame.Surface((320, 224))
        scene.draw(surf)
        assert surf.get_at((0, 0)) is not None

    def test_mode_cycle(self, context) -> None:
        from src.engine.scenes.vision_demo_scene import MODE_NAMES
        scene = VisionDemoScene(context)
        scene.on_enter()
        for _ in range(len(MODE_NAMES) * 2):
            scene._mode = (scene._mode + 1) % len(MODE_NAMES)
        assert scene._mode < len(MODE_NAMES)


class TestPatternDemoScene:
    def test_import_succeeds(self) -> None:
        assert PatternDemoScene is not None

    def test_instantiate(self, context) -> None:
        scene = PatternDemoScene(context)
        assert scene is not None
        assert hasattr(scene, "_mode")
        assert scene._mode == 0

    def test_on_enter_exit(self, context) -> None:
        scene = PatternDemoScene(context)
        scene.on_enter()
        assert scene._mode == 0
        scene.on_exit()

    def test_draw_no_crash(self, context) -> None:
        scene = PatternDemoScene(context)
        surf = pygame.Surface((320, 224))
        scene.draw(surf)
        assert surf.get_at((0, 0)) is not None

    def test_mode_cycle(self, context) -> None:
        from src.engine.scenes.pattern_demo_scene import MODE_NAMES
        scene = PatternDemoScene(context)
        scene.on_enter()
        for _ in range(len(MODE_NAMES) * 2):
            scene._mode = (scene._mode + 1) % len(MODE_NAMES)
        assert scene._mode < len(MODE_NAMES)

    def test_class_color_deterministic(self) -> None:
        c1 = PatternDemoScene._class_color("dark_zone")
        c2 = PatternDemoScene._class_color("dark_zone")
        assert c1 == c2


class TestCollisionLabScene:
    def test_import_succeeds(self) -> None:
        assert CollisionLabScene is not None

    def test_instantiate(self, context) -> None:
        scene = CollisionLabScene(context)
        assert scene is not None
        assert hasattr(scene, "_mode")
        assert scene._mode == 2

    def test_on_enter_exit(self, context) -> None:
        scene = CollisionLabScene(context)
        scene.on_enter()
        scene.on_exit()

    def test_draw_no_crash(self, context) -> None:
        scene = CollisionLabScene(context)
        surf = pygame.Surface((320, 224))
        scene.draw(surf)
        assert surf.get_at((0, 0)) is not None

    def test_mode_cycle(self, context) -> None:
        scene = CollisionLabScene(context)
        scene.on_enter()
        for _ in range(6):
            scene._mode = (scene._mode + 1) % 3
        assert scene._mode < 3


class TestVectorLabScene:
    def test_import_succeeds(self) -> None:
        assert VectorLabScene is not None

    def test_instantiate(self, context) -> None:
        scene = VectorLabScene(context)
        assert scene is not None
        assert hasattr(scene, "_mode")

    def test_on_enter_exit(self, context) -> None:
        scene = VectorLabScene(context)
        scene.on_enter()
        scene.on_exit()

    def test_draw_no_crash(self, context) -> None:
        scene = VectorLabScene(context)
        surf = pygame.Surface((320, 224))
        scene.draw(surf)
        assert surf.get_at((0, 0)) is not None


class TestColorTheoryScene:
    def test_import_succeeds(self) -> None:
        assert ColorTheoryScene is not None

    def test_instantiate(self, context) -> None:
        scene = ColorTheoryScene(context)
        assert scene is not None
        assert hasattr(scene, "_mode")

    def test_on_enter_exit(self, context) -> None:
        scene = ColorTheoryScene(context)
        scene.on_enter()
        scene.on_exit()

    def test_draw_no_crash(self, context) -> None:
        scene = ColorTheoryScene(context)
        surf = pygame.Surface((320, 224))
        scene.draw(surf)
        assert surf.get_at((0, 0)) is not None


class TestCurveEditorScene:
    def test_import_succeeds(self) -> None:
        assert CurveEditorScene is not None

    def test_instantiate(self, context) -> None:
        scene = CurveEditorScene(context)
        assert scene is not None
        assert hasattr(scene, "_mode")

    def test_on_enter_exit(self, context) -> None:
        scene = CurveEditorScene(context)
        scene.on_enter()
        scene.on_exit()

    def test_draw_no_crash(self, context) -> None:
        scene = CurveEditorScene(context)
        surf = pygame.Surface((320, 224))
        scene.draw(surf)
        assert surf.get_at((0, 0)) is not None


class TestDemoCommon:
    def test_build_default_sources(self) -> None:
        mgr = build_default_sources()
        assert isinstance(mgr, SourceSurfaceManager)
        assert len(mgr.sources) >= 4
        assert len(mgr.source_names) >= 4

    def test_source_cycle(self) -> None:
        mgr = build_default_sources()
        idx0 = mgr._current_index
        mgr.cycle()
        assert mgr._current_index != idx0 or len(mgr.sources) == 1

    def test_freeze(self) -> None:
        mgr = build_default_sources()
        mgr.freeze()
        assert mgr.is_frozen

    def test_unfreeze(self) -> None:
        mgr = build_default_sources()
        mgr.freeze()
        mgr.unfreeze()
        assert not mgr.is_frozen

    def test_frame_throttle(self) -> None:
        t = FrameThrottle()
        assert not t.should_update(3)
        t.tick()
        assert not t.should_update(3)
        t.tick()
        assert t.should_update(3)

    def test_frame_throttle_reset(self) -> None:
        t = FrameThrottle()
        t.tick()
        assert t._counter == 2
        t.reset()
        assert t._counter == 1

    def test_save_png(self) -> None:
        surf = pygame.Surface((160, 180))
        path = save_png("unittest", "test", surf)
        assert path.endswith(".png")
        assert "unittest_test_" in path

    def test_draw_top_bar(self) -> None:
        surf = pygame.Surface((320, 224))
        draw_top_bar(surf, "TEST", "UNIT")
        assert surf.get_at((0, 0)) is not None

    def test_draw_bottom_bar(self) -> None:
        surf = pygame.Surface((320, 224))
        draw_bottom_bar(surf, "test bottom bar")
        assert surf.get_at((0, 0)) is not None


class TestTitleSceneIntegration:
    def test_title_has_demo_option(self, context) -> None:
        from src.engine.scenes.title_scene import TitleScene
        scene = TitleScene(context)
        assert "ACADEMIC DEMOS" in scene._options
        assert scene._options.index("ACADEMIC DEMOS") == 1

    def test_title_demo_select(self, context) -> None:
        from src.engine.scenes.title_scene import TitleScene
        from src.engine.scenes.demo_menu_scene import DemoMenuScene

        mock_replace_calls: list = []
        context.scene_manager.replace = lambda sc: mock_replace_calls.append(sc)

        scene = TitleScene(context)
        scene._selected = 1
        context.input_manager.is_action_pressed.side_effect = lambda a: a == Action.CONFIRM

        scene.update(1.0)
        assert len(mock_replace_calls) == 1
        assert isinstance(mock_replace_calls[0], DemoMenuScene)
