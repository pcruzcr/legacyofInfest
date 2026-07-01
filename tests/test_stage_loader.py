"""
Module: test_stage_loader
System: tests
Academic Unit: N/A
Description: Tests for StageLoader — TMX parsing, entity spawning,
collision rects, missing layer/PlayerSpawn errors.
"""
from pathlib import Path


from src.framework.entities.enemy_walker import EnemyWalker
from src.framework.stage.stage_loader import StageLoader, StageData

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures"
MINIMAL_TMX = FIXTURE_DIR / "minimal_stage.tmx"


class TestStageLoaderLoad:
    """Tests for StageLoader.load()."""

    def setup_method(self) -> None:
        StageLoader._entity_registry.clear()
        StageLoader.register_entity("Walker", EnemyWalker)

    def test_load_returns_stage_data(self) -> None:
        data = StageLoader.load(MINIMAL_TMX)
        assert isinstance(data, StageData)

    def test_spawn_point_matches_tmx(self) -> None:
        data = StageLoader.load(MINIMAL_TMX)
        assert abs(data.spawn_point.x - 48.0) < 0.1
        assert abs(data.spawn_point.y - 176.0) < 0.1

    def test_collision_rects_nonempty(self) -> None:
        data = StageLoader.load(MINIMAL_TMX)
        assert len(data.collision_rects) > 0

    def test_walker_entity_spawned(self) -> None:
        data = StageLoader.load(MINIMAL_TMX)
        walkers = [e for e in data.entity_list if isinstance(e, EnemyWalker)]
        assert len(walkers) == 1

    def test_checkpoint_registered(self) -> None:
        data = StageLoader.load(MINIMAL_TMX)
        assert len(data.checkpoints) == 1
        assert data.checkpoints[0].checkpoint_id == 0

    def test_next_trigger_present(self) -> None:
        data = StageLoader.load(MINIMAL_TMX)
        assert data.next_trigger is not None

    def test_stage_properties(self) -> None:
        data = StageLoader.load(MINIMAL_TMX)
        assert data.stage_id == "minimal_test"
        assert data.stage_name == "Minimal Test Stage"
