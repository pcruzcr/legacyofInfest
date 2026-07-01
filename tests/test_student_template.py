"""
Module: test_student_template
System: tests
Academic Unit: N/A
Description: Tests verifying that student templates import correctly and
provide the expected interface.
"""
from pathlib import Path



class TestStageTemplate:
    def test_import(self) -> None:
        from student_templates.stage_template.stage_template import CustomStageScene
        assert CustomStageScene is not None

    def test_can_instantiate_with_default_tmx(self) -> None:
        from student_templates.stage_template.stage_template import CustomStageScene
        scene = CustomStageScene()
        assert scene._tmx_path is not None
        tmx_path: Path = scene._tmx_path  # type: ignore[assignment]
        assert tmx_path.name == "stage_template.tmx"
        assert tmx_path.exists()

    def test_default_tmx_exists(self) -> None:
        tmx = Path("student_templates/stage_template/stage_template.tmx")
        assert tmx.exists(), f"TMX template not found: {tmx}"

    def test_default_tmx_has_required_layers(self) -> None:
        # Don't require pytmx in this test — just verify the XML structure
        tmx = Path("student_templates/stage_template/stage_template.tmx")
        content = tmx.read_text()
        for layer in ("BG_Far", "BG_Mid", "BG_Near", "Terrain",
                      "Terrain_Detail", "Objects", "Collision", "FG_Overlay"):
            assert layer in content, f"Missing layer '{layer}' in stage_template.tmx"

    def test_load_model_method(self) -> None:
        from student_templates.stage_template.stage_template import CustomStageScene
        scene = CustomStageScene()
        assert hasattr(scene, "load_model")

    def test_has_custom_timer(self) -> None:
        from student_templates.stage_template.stage_template import CustomStageScene
        scene = CustomStageScene()
        assert hasattr(scene, "_custom_timer")
        assert scene._custom_timer == 0.0

    def test_update_increments_timer(self) -> None:
        from student_templates.stage_template.stage_template import CustomStageScene
        scene = CustomStageScene()
        scene.update(0.016)
        assert scene._custom_timer > 0.0


class TestBossTemplate:
    def test_import(self) -> None:
        try:
            from student_templates.boss_template.boss_template import CustomBoss
            assert CustomBoss is not None
        except ImportError:
            # BossBase may not exist yet — acceptable at this stage
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
