"""Benchmark: application startup time.

Measures the cost of importing core modules and creating an App instance.
This establishes a baseline for P1-04 (Lazy Loading).
"""
from __future__ import annotations

import pytest

# pytest-benchmark is an optional dev dependency (`pip install -e ".[dev]"`).
# Without it the `benchmark` fixture does not exist and every test in this
# module ERRORs rather than skipping — which made a plain `pytest` run look
# broken on a minimal install. Skip cleanly instead.
pytest.importorskip("pytest_benchmark")


def test_cold_import_time(benchmark) -> None:
    """Time to import the five heaviest modules (cold)."""

    def _import_core() -> None:
        import importlib
        for mod in [
            "src.engine.core.app",
            "src.engine.core.event_bus",
            "src.engine.scene.scene_manager",
            "src.framework.scenes.stage_scene",
            "src.framework.entities.player",
        ]:
            importlib.import_module(mod)

    # Warm up cache so benchmark measures re-import, not first-load
    _import_core()

    def _reload() -> None:
        import importlib
        for mod in [
            "src.engine.core.app",
            "src.engine.scene.scene_manager",
            "src.framework.scenes.stage_scene",
        ]:
            importlib.reload(importlib.import_module(mod))

    benchmark(_reload)


def test_module_load_count(benchmark) -> None:
    """Count modules loaded during a fresh Python import sequence."""

    def _count_loaded() -> int:
        import sys
        len(sys.modules)
        from src.engine.core import app  # noqa: F401
        return len(sys.modules)

    benchmark(_count_loaded)
