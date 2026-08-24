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
    """Time to import the five heaviest modules (cold).

    AUD-164 — el benchmark anterior medía con `importlib.reload` de
    `src.framework.scenes.stage_scene` dentro del proceso de la suite. Un
    `reload` reejecuta el módulo y crea una clase `StageScene` **nueva**, distinta
    de la que ya heredaban los escenarios importados antes: desde esa prueba en
    adelante, `tests/test_ecs.py` veía identidades distintas y fallaba sólo en la
    suite completa. La medida se hace ahora en un **subproceso** (el coste real
    de un arranque en frío) y deja intactos los módulos de la suite.
    """
    import os
    import subprocess
    import sys
    from pathlib import Path

    RAIZ = Path(__file__).resolve().parents[2]
    MODULOS = [
        "src.engine.core.app",
        "src.engine.core.event_bus",
        "src.engine.scene.scene_manager",
        "src.framework.scenes.stage_scene",
        "src.framework.entities.player",
    ]

    def _importar_frio() -> float:
        """Interprete + importar los módulos, medido en el subproceso."""
        entorno = dict(os.environ)
        entorno.setdefault("SDL_VIDEODRIVER", "dummy")
        entorno.setdefault("SDL_AUDIODRIVER", "dummy")
        cuerpo = "; ".join(f"import {m}" for m in MODULOS)
        linea = (
            "import time; "
            f"t = time.perf_counter(); {cuerpo}; "
            "print((time.perf_counter() - t) * 1000)"
        )
        salida = subprocess.run(
            [sys.executable, "-c", linea],
            capture_output=True, text=True, cwd=str(RAIZ), env=entorno,
        )
        try:
            return float(salida.stdout.strip().splitlines()[-1])
        except (ValueError, IndexError):
            return float("nan")

    benchmark(_importar_frio)


def test_module_load_count(benchmark) -> None:
    """Count modules loaded during a fresh Python import sequence."""

    def _count_loaded() -> int:
        import sys
        len(sys.modules)
        from src.engine.core import app  # noqa: F401
        return len(sys.modules)

    benchmark(_count_loaded)
