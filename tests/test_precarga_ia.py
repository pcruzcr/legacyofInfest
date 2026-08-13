"""AUD-457 — la precarga de la IA es síncrona y nunca hay dos importadores.

AUD-456 intentó cargar `ai_predictor` en un hilo daemon; AUD-457 retira el
hilo porque la importación concurrente de scipy 1.9 en CPython 3.14
deadlockea (`_DeadlockError` en `scipy.linalg.cython_blas` medido en el
arranque real, o un cuelgue permanente — el que el dueño veía). El flujo es
ahora:

1. Flujo normal: la splash paga la carga (AUD-088) con su mensaje visible.
2. Flujo `--stage` / `--boss`: `main.py` la paga antes del bucle.

En los dos es **el único importador** del árbol scipy en vuelo, y esa es la
garantía de que no deadlockea.

Lo que se fija aquí
-------------------
1. Que la precarga acabe importando `ai_predictor` sin lanzar.
2. Que `precargar_ia()` sea síncrona (bloquea hasta terminar) e idempotente
   (la segunda llamada no vuelve a importar).
3. Que en un intérprete limpio el contrato que usan la splash y `main.py`
   funciona completo: `precargar_ia()` → `esperar()` → `importada()`.
"""
from __future__ import annotations

import os
import subprocess
import sys
import time

import pytest


def _sklearn_disponible() -> bool:
    try:
        import sklearn  # noqa: F401

        return True
    except ImportError:
        return False


class TestPrecargaSincrona:
    def test_sin_sklearn_la_carga_no_rompe(self, monkeypatch) -> None:
        """Sin scikit-learn, la carga no lanza y `ia_lista` no miente.

        Se define PRIMERO a propósito: manipula `sys.modules` para simular la
        ausencia de sklearn sin desinstalar nada.
        """
        from src.framework.entities import precarga_ia

        # Defensivo: si otra prueba ya cargó, se restaura el estado global
        # para que esta simulación no haga creer que la carga real terminó.
        clave = "src.framework.entities.ai_predictor"
        previo = sys.modules.pop(clave, None)
        sys.modules[clave] = None  # import con None en sys.modules → ImportError
        precarga_ia._arrancada = False
        precarga_ia._terminado.clear()
        try:
            precarga_ia.precargar_ia()  # no debe lanzar
            assert precarga_ia.ia_lista()
            assert not precarga_ia.importada()
        finally:
            if previo is not None:
                sys.modules[clave] = previo
            else:
                sys.modules.pop(clave, None)
        # Restaura el estado global para las demás pruebas.
        precarga_ia._terminado.clear()
        precarga_ia._arrancada = False

    def test_precargar_es_sincrona_e_idempotente(self) -> None:
        if not _sklearn_disponible():
            pytest.skip("scikit-learn no está instalado; la IA usa su heurística")
        from src.framework.entities import precarga_ia

        if precarga_ia._arrancada:
            precarga_ia._terminado.clear()
            precarga_ia._arrancada = False
        precarga_ia.precargar_ia()  # primera llamada: bloquea y carga
        assert precarga_ia.ia_lista()
        assert precarga_ia.importada()
        t0 = time.perf_counter()
        precarga_ia.precargar_ia()  # segunda llamada: no vuelve a importar
        assert time.perf_counter() - t0 < 1.0, "la segunda precarga re-importó"
        assert precarga_ia.importada()


class TestUnSoloImportadorALaVez:
    def test_la_precarga_termina_y_publica_el_modulo(self) -> None:
        """AUD-457 — la carga de la IA es síncrona y deja el módulo listo.

        En un intérprete limpio (los locks de importlib son por intérprete y
        este proceso ya rozó `ai_predictor` en otros tests) se ejecuta el
        contrato que usan la splash y los flujos `--stage`/`--boss`:
        `precargar_ia()` bloquea, termina, y `esperar()`/`importada()` dicen
        la verdad. Dos importadores en paralelo reintroducirían el
        `_DeadlockError` de scipy 1.9 + CPython 3.14 en stderr, o colgarían
        el subproceso y lo delataría el timeout.
        """
        if not _sklearn_disponible():
            pytest.skip("scikit-learn no está instalado; la IA usa su heurística")

        codigo = (
            "import sys\n"
            "sys.path.insert(0, r'.')\n"
            "from src.framework.entities.precarga_ia import (\n"
            "    precargar_ia, esperar, importada,\n"
            ")\n"
            "precargar_ia()\n"
            "esperar()\n"
            "assert importada(), 'la precarga no publicó el módulo'\n"
            "print('OK')\n"
        )
        raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        resultado = subprocess.run(
            [sys.executable, "-c", codigo],
            capture_output=True, text=True, timeout=60, cwd=raiz,
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        )
        assert "OK" in resultado.stdout, (
            f"el contrato de AUD-457 falló:\nstdout: {resultado.stdout[-1500:]}\n"
            f"stderr: {resultado.stderr[-1500:]}"
        )
        assert "DeadlockError" not in resultado.stderr, (
            f"importlib detectó un ciclo de imports en el arranque:\n"
            f"{resultado.stderr[-1500:]}"
        )