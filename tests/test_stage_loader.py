"""
Tests for StageLoader (T7.3, T7.4, T7.5).
Per 24_TEST_PLAN.md §9.1.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pygame

import pytest

from src.framework.stage.stage_loader import (
    StageLoader,
    StageData,
    FrameworkUsageError,
)
from src.framework.entities.enemy_walker import EnemyWalker


# Headless pygame required for pytmx image loading
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
pygame.init()
pygame.display.set_mode((1, 1))


# ── Helpers ──────────────────────────────────────────────────────────────

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "minimal_stage.tmx"


def _register_walker() -> None:
    """Ensure Walker entity type is registered for TMX object parsing."""
    StageLoader.register_entity("Walker", EnemyWalker)


# ── Tests ────────────────────────────────────────────────────────────────


class TestStageLoader:
    """Coverage per 24_TEST_PLAN.md §9.1."""

    def test_load_returns_stage_data(self) -> None:
        """StageLoader.load(fixture) returns a StageData instance."""
        _register_walker()
        data = StageLoader.load(FIXTURE_PATH)
        assert isinstance(data, StageData)

    def test_spawn_point_matches_tmx(self) -> None:
        """StageData.spawn_point matches the fixture PlayerSpawn coords."""
        _register_walker()
        data = StageLoader.load(FIXTURE_PATH)
        assert data.spawn_point.x == pytest.approx(32.0)
        assert data.spawn_point.y == pytest.approx(192.0)

    def test_collision_rects_nonempty(self) -> None:
        """StageData.collision_rects has entries from the Collision layer."""
        _register_walker()
        data = StageLoader.load(FIXTURE_PATH)
        assert len(data.collision_rects) >= 1

    def test_walker_entity_spawned(self) -> None:
        """Entity list contains exactly one EnemyWalker at TMX coords."""
        _register_walker()
        data = StageLoader.load(FIXTURE_PATH)
        walkers = [e for e in data.entity_list if isinstance(e, EnemyWalker)]
        assert len(walkers) == 1
        assert walkers[0].position.x == pytest.approx(120.0)
        assert walkers[0].position.y == pytest.approx(192.0)

    def test_checkpoint_registered(self) -> None:
        """StageData.checkpoints contains Checkpoint with correct id."""
        _register_walker()
        data = StageLoader.load(FIXTURE_PATH)
        assert len(data.checkpoints) == 1
        assert data.checkpoints[0].checkpoint_id == 0

    def test_missing_player_spawn_raises(self) -> None:
        """TMX with no PlayerSpawn raises FrameworkUsageError."""
        _register_walker()
        tmx = _build_tmx(include_player_spawn=False)
        with pytest.raises(FrameworkUsageError, match="No PlayerSpawn"):
            StageLoader.load(tmx)

    def test_missing_required_layer_raises(self) -> None:
        """TMX missing a required layer raises FrameworkUsageError."""
        _register_walker()
        tmx = _build_tmx(missing_layer="Terrain")
        with pytest.raises(FrameworkUsageError, match="missing"):
            StageLoader.load(tmx)

    def test_duplicate_player_spawn_raises(self) -> None:
        """TMX with two PlayerSpawn objects raises FrameworkUsageError."""
        _register_walker()
        tmx = _build_tmx(duplicate_spawn=True)
        with pytest.raises(FrameworkUsageError, match="Duplicate"):
            StageLoader.load(tmx)

    def test_stage_metadata_extracted(self) -> None:
        """Map-level properties are extracted into StageData."""
        _register_walker()
        data = StageLoader.load(FIXTURE_PATH)
        assert data.stage_id == "minimal"
        assert data.stage_name == "Minimal Stage"
        assert data.time_limit == 120
        assert data.bgm_track == "bgm_test"

    def test_next_trigger_parsed(self) -> None:
        """NextTrigger object becomes StageData.next_trigger rect."""
        _register_walker()
        data = StageLoader.load(FIXTURE_PATH)
        assert data.next_trigger is not None
        assert data.next_trigger.x == pytest.approx(280.0)
        assert data.next_trigger.width == pytest.approx(40.0)


# ── TMX builders for error cases ──────────────────────────────────────


def _build_tmx(
    include_player_spawn: bool = True,
    missing_layer: str | None = None,
    duplicate_spawn: bool = False,
) -> Path:
    """Write a minimal TMX to a temp file and return its Path."""
    layers = [
        "BG_Far",
        "BG_Mid",
        "BG_Near",
        "Terrain",
        "Terrain_Detail",
        "Objects",
        "Collision",
        "FG_Overlay",
    ]
    if missing_layer:
        layers.remove(missing_layer)

    flat_empty = ",".join(["0"] * 20 * 14)
    layer_xml = ""
    for name in layers:
        layer_xml += (
            f'  <layer name="{name}" width="20" height="14">\n'
            f"    <data encoding=\"csv\">{flat_empty}</data>\n"
            f"  </layer>\n"
        )

    objects = []
    if include_player_spawn:
        objects.append(
            '<object id="1" type="PlayerSpawn" name="P1"'
            ' x="0" y="0"/>'
        )
    if duplicate_spawn:
        objects.append(
            '<object id="2" type="PlayerSpawn" name="P2"'
            ' x="10" y="0"/>'
        )
    objects.append(
        '<object id="3" type="NextTrigger" name="NT1"'
        ' x="0" y="0" width="16" height="32"/>'
    )

    collision = (
        '<object id="10" name="Solid"'
        ' x="0" y="0" width="16" height="16"/>'
    )

    tmx = f"""<?xml version="1.0" encoding="UTF-8"?>
<map version="1.10" orientation="orthogonal" renderorder="right-down"
     width="20" height="14" tilewidth="16" tileheight="16">
{layer_xml}
  <objectgroup name="Objects">
    {chr(10).join(objects)}
  </objectgroup>
  <objectgroup name="Collision">
    {collision}
  </objectgroup>
</map>
"""

    fd, path = tempfile.mkstemp(suffix=".tmx")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(tmx)
    except Exception:
        os.close(fd)
        raise
    return Path(path)
