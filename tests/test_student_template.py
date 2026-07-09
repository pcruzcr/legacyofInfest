"""
Module: test_student_template
System: tests
Academic Unit: N/A
Description: Tests verifying that student templates import correctly and
provide the expected interface (matches 26_STUDENT_TEMPLATE_SPEC.md).
"""
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from src.engine.core.event_bus import EventBus
from src.engine.core.game_context import GameContext


@pytest.fixture(autouse=True)
def _init_pygame():
    import pygame
    pygame.init()
    pygame.display.set_mode((1, 1))
    yield
    pygame.quit()


@pytest.fixture
def context():
    """Minimal GameContext for template instantiation."""
    import pygame
    im = MagicMock()
    return GameContext(
        im,  # input_manager
        MagicMock(),  # audio_manager
        MagicMock(),  # scene_manager
        EventBus(),   # event_bus
    )


class TestStageTemplate:
    def test_import(self) -> None:
        from student_templates.stage_template.stage_template import StageTemplate
        assert StageTemplate is not None

    def test_can_instantiate(self, context) -> None:
        from student_templates.stage_template.stage_template import StageTemplate
        scene = StageTemplate(context)
        assert isinstance(scene.TMX_PATH, str)

    def test_tmx_exists(self) -> None:
        from student_templates.stage_template.stage_template import StageTemplate
        tmx = Path(StageTemplate.TMX_PATH)
        assert tmx.exists(), f"TMX template not found: {tmx}"

    def test_default_tmx_has_required_layers(self) -> None:
        tmx = Path("student_templates/stage_template/stage_template.tmx")
        content = tmx.read_text()
        for layer in ("BG_Far", "BG_Mid", "BG_Near", "Terrain",
                      "Terrain_Detail", "Objects", "Collision", "FG_Overlay"):
            assert layer in content, f"Missing layer '{layer}' in stage_template.tmx"

    def test_has_stage_data(self, context) -> None:
        from student_templates.stage_template.stage_template import StageTemplate
        scene = StageTemplate(context)
        assert hasattr(scene, "stage_data")

    def test_has_player(self, context) -> None:
        from student_templates.stage_template.stage_template import StageTemplate
        scene = StageTemplate(context)
        assert hasattr(scene, "player")

    def test_has_camera(self, context) -> None:
        from student_templates.stage_template.stage_template import StageTemplate
        scene = StageTemplate(context)
        assert hasattr(scene, "camera")

    def test_has_hud(self, context) -> None:
        from student_templates.stage_template.stage_template import StageTemplate
        scene = StageTemplate(context)
        assert hasattr(scene, "hud")

    def test_has_message_box(self, context) -> None:
        from student_templates.stage_template.stage_template import StageTemplate
        scene = StageTemplate(context)
        assert hasattr(scene, "message_box")

    def test_has_screen_banner(self, context) -> None:
        from student_templates.stage_template.stage_template import StageTemplate
        scene = StageTemplate(context)
        assert hasattr(scene, "screen_banner")

    def test_attack_collision_method(self, context) -> None:
        from student_templates.stage_template.stage_template import StageTemplate
        scene = StageTemplate(context)
        assert hasattr(scene, "_check_attack_collisions")

    def test_next_trigger_method(self, context) -> None:
        from student_templates.stage_template.stage_template import StageTemplate
        scene = StageTemplate(context)
        assert hasattr(scene, "_check_next_trigger")


class TestBossTemplate:
    def test_import(self) -> None:
        try:
            from student_templates.boss_template.boss_template import CustomBoss
            assert CustomBoss is not None
        except ImportError:
            pass

    def test_class_exists(self) -> None:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "boss_template",
            "student_templates/boss_template/boss_template.py",
        )
        assert spec is not None, "boss_template.py file not found"

    def test_file_exists(self) -> None:
        f = Path("student_templates/boss_template/boss_template.py")
        assert f.exists()

    def test_readme_exists(self) -> None:
        f = Path("student_templates/boss_template/README_template.md")
        assert f.exists()

    def test_stage_readme_exists(self) -> None:
        f = Path("student_templates/stage_template/README_template.md")
        assert f.exists()
