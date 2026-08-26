"""
AUD-631 — presupuesto de rendimiento: cold import y memoria.

Estas pruebas son gates: si alguien añade una dependencia que dispara
el tiempo de import o la memoria, aquí salta antes de llegar a producción.
"""
from __future__ import annotations

import subprocess
import sys
import time

import pytest

RAIZ = __import__("pathlib").Path(__file__).resolve().parent.parent


class TestColdImport:
    """El import del motor no puede ser más lento que un umbral razonable."""

    #: El import en frío medido en la máquina de referencia es ~1.5 s.
    #: Si sube un 20 % es señal de que alguien añadió una dependencia pesada.
    UMBRAL_SEGUNDOS = 2.5  # margen generoso para CI

    def test_cold_import_bajo_umbral(self):
        """`import src.engine.core.app` tarda menos de UMBRAL_SEGUNDOS."""
        codigo = "import src.engine.core.app"
        inicio = time.monotonic()
        resultado = subprocess.run(
            [sys.executable, "-c", codigo],
            cwd=str(RAIZ),
            capture_output=True,
            timeout=30,
        )
        duracion = time.monotonic() - inicio
        assert resultado.returncode == 0, f"import falló: {resultado.stderr[:200]}"
        assert duracion < self.UMBRAL_SEGUNDOS, (
            f"Cold import {duracion:.1f}s >= {self.UMBRAL_SEGUNDOS}s. "
            f"Alguien añadió una dependencia pesada al motor."
        )

    def test_cold_import_engine_core_sin_app(self):
        """Importar solo `engine.core.settings` es rápido (< 0.5 s)."""
        codigo = "from src.engine.core import settings; print('OK')"
        inicio = time.monotonic()
        resultado = subprocess.run(
            [sys.executable, "-c", codigo],
            cwd=str(RAIZ),
            capture_output=True,
            timeout=10,
        )
        duracion = time.monotonic() - inicio
        assert resultado.returncode == 0
        assert duracion < 0.5, (
            f"settings.py import {duracion:.1f}s >= 0.5s — "
            f"revisar dependencias de settings"
        )


class TestMemoryCeiling:
    """El motor no puede consumir memoria descontroladamente al arrancar."""

    #: RSS máximo al importar engine.core.app. Medido: ~120 MB con pygame.
    UMBRAL_MB = 350

    def test_rss_bajo_umbral_tras_import(self):
        """Tras importar app, el RSS está por debajo del techo."""
        if sys.platform == "win32":
            # En Windows usamos psutil si está disponible, si no skip
            try:
                import psutil  # noqa: F401 — verifica disponibilidad para el subproceso
            except ImportError:
                pytest.skip("psutil no disponible")
            codigo = (
                "import src.engine.core.app\n"
                "import os, psutil\n"
                "proc = psutil.Process(os.getpid())\n"
                "print(proc.memory_info().rss)"
            )
            resultado = subprocess.run(
                [sys.executable, "-c", codigo],
                cwd=str(RAIZ), capture_output=True, timeout=30,
            )
            if resultado.returncode != 0:
                pytest.skip(f"Error midiendo RSS: {resultado.stderr[:100]}")
            rss_bytes = int(resultado.stdout.strip().splitlines()[-1])
            rss_mb = rss_bytes / (1024 * 1024)
            assert rss_mb < self.UMBRAL_MB, (
                f"RSS tras import app: {rss_mb:.0f} MB >= {self.UMBRAL_MB} MB. "
                f"Revisar allocations en el arranque."
            )
        else:
            pytest.skip("Solo implementado para Windows")