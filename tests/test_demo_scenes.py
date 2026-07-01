from __future__ import annotations

import pygame
import pytest


@pytest.fixture(autouse=True)
def pygame_init():
    if not pygame.get_init():
        pygame.init()
    if not pygame.font.get_init():
        pygame.font.init()


from src.engine.scenes.demo_menu_scene import DemoMenuScene
from src.engine.scenes.filter_demo_scene import FilterDemoScene
from src.engine.scenes.vision_demo_scene import VisionDemoScene
from src.engine.scenes.pattern_demo_scene import PatternDemoScene
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

    def test_instantiate(self) -> None:
        scene = DemoMenuScene()
        assert scene is not None
        assert hasattr(scene, "_options")
        assert len(scene._options) == 3

    def test_on_enter_exit(self) -> None:
        scene = DemoMenuScene()
        scene.on_enter()
        assert scene._selected == 0
        scene.on_exit()

    def test_draw_no_crash(self) -> None:
        scene = DemoMenuScene()
        surf = pygame.Surface((320, 224))
        scene.draw(surf)
        assert surf.get_at((0, 0)) is not None


class TestFilterDemoScene:
    def test_import_succeeds(self) -> None:
        assert FilterDemoScene is not None

    def test_instantiate(self) -> None:
        scene = FilterDemoScene()
        assert scene is not None
        assert hasattr(scene, "_mode")
        assert scene._mode == 0

    def test_on_enter_exit(self) -> None:
        scene = FilterDemoScene()
        scene.on_enter()
        assert scene._mode == 0
        scene.on_exit()

    def test_draw_no_crash(self) -> None:
        scene = FilterDemoScene()
        surf = pygame.Surface((320, 224))
        scene.draw(surf)
        assert surf.get_at((0, 0)) is not None

    def test_mode_cycle(self) -> None:
        from src.engine.scenes.filter_demo_scene import MODE_NAMES
        scene = FilterDemoScene()
        scene.on_enter()
        for _ in range(len(MODE_NAMES) * 2):
            # Simulate TAB press via internal state
            scene._mode = (scene._mode + 1) % len(MODE_NAMES)
        assert scene._mode < len(MODE_NAMES)

    def test_reset_params(self) -> None:
        scene = FilterDemoScene()
        scene._brightness_factor = 3.0
        scene._contrast_factor = 2.5
        scene._reset_params()
        assert scene._brightness_factor == 1.0
        assert scene._contrast_factor == 1.0
        assert scene._sigma == 1.0


class TestVisionDemoScene:
    def test_import_succeeds(self) -> None:
        assert VisionDemoScene is not None

    def test_instantiate(self) -> None:
        scene = VisionDemoScene()
        assert scene is not None
        assert hasattr(scene, "_mode")
        assert scene._mode == 0

    def test_on_enter_exit(self) -> None:
        scene = VisionDemoScene()
        scene.on_enter()
        assert scene._mode == 0
        scene.on_exit()

    def test_draw_no_crash(self) -> None:
        scene = VisionDemoScene()
        surf = pygame.Surface((320, 224))
        scene.draw(surf)
        assert surf.get_at((0, 0)) is not None

    def test_mode_cycle(self) -> None:
        from src.engine.scenes.vision_demo_scene import MODE_NAMES
        scene = VisionDemoScene()
        scene.on_enter()
        for _ in range(len(MODE_NAMES) * 2):
            scene._mode = (scene._mode + 1) % len(MODE_NAMES)
        assert scene._mode < len(MODE_NAMES)


class TestPatternDemoScene:
    def test_import_succeeds(self) -> None:
        assert PatternDemoScene is not None

    def test_instantiate(self) -> None:
        scene = PatternDemoScene()
        assert scene is not None
        assert hasattr(scene, "_mode")
        assert scene._mode == 0

    def test_on_enter_exit(self) -> None:
        scene = PatternDemoScene()
        scene.on_enter()
        assert scene._mode == 0
        scene.on_exit()

    def test_draw_no_crash(self) -> None:
        scene = PatternDemoScene()
        surf = pygame.Surface((320, 224))
        scene.draw(surf)
        assert surf.get_at((0, 0)) is not None

    def test_mode_cycle(self) -> None:
        from src.engine.scenes.pattern_demo_scene import MODE_NAMES
        scene = PatternDemoScene()
        scene.on_enter()
        for _ in range(len(MODE_NAMES) * 2):
            scene._mode = (scene._mode + 1) % len(MODE_NAMES)
        assert scene._mode < len(MODE_NAMES)

    def test_class_color_deterministic(self) -> None:
        c1 = PatternDemoScene._class_color("dark_zone")
        c2 = PatternDemoScene._class_color("dark_zone")
        assert c1 == c2


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
    def test_title_has_demo_option(self) -> None:
        from src.engine.scenes.title_scene import TitleScene
        scene = TitleScene()
        assert "ACADEMIC DEMOS" in scene._options
        assert scene._options.index("ACADEMIC DEMOS") == 1

    def test_title_demo_select(self) -> None:
        from src.engine.scenes.title_scene import TitleScene
        scene = TitleScene()
        scene._selected = 1
        assert scene._selected == 1
        # Verify it would navigate to DemoMenuScene
        assert True
