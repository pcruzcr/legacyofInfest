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
    return GameContext(
        MagicMock(),  # input_manager
        MagicMock(),  # audio_manager
        MagicMock(),  # scene_manager
        EventBus(),   # event_bus
        clock=MagicMock(),
    )


class TestStageTemplate:
    def test_import(self) -> None:
        from student_templates.stage_template.stage_template import StageTemplate
        assert StageTemplate is not None

    def test_can_instantiate(self, context) -> None:
        from student_templates.stage_template.stage_template import StageTemplate
        scene = StageTemplate(context)
        assert hasattr(scene, "_stage_data")

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

    def test_inherits_from_stage_scene(self, context) -> None:
        from student_templates.stage_template.stage_template import StageTemplate
        from src.framework.scenes.stage_scene import StageScene
        assert issubclass(StageTemplate, StageScene)

    def test_has_stage_scene_attributes(self, context) -> None:
        from student_templates.stage_template.stage_template import StageTemplate
        scene = StageTemplate(context)
        assert hasattr(scene, "_stage_data")
        assert hasattr(scene, "_player")
        assert hasattr(scene, "_camera")

    def test_has_stage_attrs(self) -> None:
        from student_templates.stage_template.stage_template import StageTemplate
        assert hasattr(StageTemplate, "STAGE_ID")
        assert hasattr(StageTemplate, "STAGE_NAME")
        assert hasattr(StageTemplate, "ZONE")

    def test_has_lifecycle_hooks(self, context) -> None:
        from student_templates.stage_template.stage_template import StageTemplate
        scene = StageTemplate(context)
        assert hasattr(scene, "on_stage_start")
        assert hasattr(scene, "on_player_landed")
        assert hasattr(scene, "on_enemy_died")
        assert hasattr(scene, "on_next_trigger_entered")
        assert hasattr(scene, "on_debug_toggle")


class TestBossTemplate:
    def test_import(self) -> None:
        from student_templates.boss_template.boss_template import BossTemplate
        assert BossTemplate is not None

    def test_constructs(self) -> None:
        import pygame
        from student_templates.boss_template.boss_template import BossTemplate
        boss = BossTemplate(pygame.Vector2(100, 100))
        assert boss is not None

    def test_inherits_from_boss_base(self) -> None:
        import pygame
        from student_templates.boss_template.boss_template import BossTemplate
        from src.framework.entities.boss_base import BossBase
        assert issubclass(BossTemplate, BossBase)
        boss = BossTemplate(pygame.Vector2(100, 100))
        assert boss is not None

    def test_has_required_methods(self) -> None:
        import pygame
        from student_templates.boss_template.boss_template import BossTemplate
        boss = BossTemplate(pygame.Vector2(100, 100))
        assert hasattr(boss, "_patrol_behavior")
        assert hasattr(boss, "_alert_behavior")
        assert hasattr(boss, "_get_animation_key")
        assert hasattr(boss, "_build_hitbox")
        assert hasattr(boss, "_build_hurtbox")

    def test_has_one_phase(self) -> None:
        import pygame
        from student_templates.boss_template.boss_template import BossTemplate
        boss = BossTemplate(pygame.Vector2(100, 100))
        assert len(boss.phases) == 1

    def test_has_boss_name(self) -> None:
        import pygame
        from student_templates.boss_template.boss_template import BossTemplate
        boss = BossTemplate(pygame.Vector2(100, 100))
        assert boss._boss_name == "Untitled Boss"

    def test_file_exists(self) -> None:
        f = Path("student_templates/boss_template/boss_template.py")
        assert f.exists()

    def test_readme_exists(self) -> None:
        f = Path("student_templates/boss_template/README_template.md")
        assert f.exists()

    def test_stage_readme_exists(self) -> None:
        f = Path("student_templates/stage_template/README_template.md")
        assert f.exists()
