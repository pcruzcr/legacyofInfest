"""AUD-346 — el promedio esconde la varianza: cuantiles del fotograma.

El hueco
--------
El FPS instantáneo de la consola es un promedio de un segundo. 59 fotogramas
de 16 ms y uno de 250 ms dan «60 FPS» igual que una secuencia perfecta: el
promedio no distingue el juego estable del que va a trompicones, y ninguna
parte del motor guardaba el historial para preguntárselo.

Qué fija
--------
* El cálculo de cuantiles (P50/P95/P99, media, peor) es una función pura:
  la misma lista de milisegundos entra y los mismos cinco números salen.
* Es *nearest-rank*: quien tenga el fichero de tiempos lo puede reproducir.
* `DeltaClock` guarda el historial real de fotogramas (sin escala) y lo
  recorta solo: 180 entradas a lo sumo.
* La consola (F11) los muestra al lado del FPS y `App` se los pasa.
"""
from __future__ import annotations

import pytest

from src.engine.core.estadisticas import cuantiles


class TestLaFuncionPura:
    def test_una_serie_tipica(self) -> None:
        serie = [16.0] * 59 + [250.0]
        r = cuantiles(serie)
        assert r["p50"] == 16.0
        assert r["p95"] == 16.0
        assert r["peor"] == 250.0
        assert r["media"] == pytest.approx(
            (16.0 * 59 + 250.0) / 60, abs=1e-9)

    def test_el_p99_si_ve_al_fuera_de_serie(self) -> None:
        r = cuantiles([16.0] * 59 + [250.0])
        assert r["p99"] == 250.0, (
            "un 250 ms entre 60 fotogramas debe caer en el p99"
        )

    def test_la_variacion_normal_no_dispara_nada(self) -> None:
        r = cuantiles([16.0, 16.0, 17.0, 16.0, 15.0])
        assert r["p99"] <= 17.0

    def test_serie_vacia_devuelve_vacio(self) -> None:
        assert cuantiles([]) == {}

    def test_un_solo_dato_en_todos_los_huecos(self) -> None:
        r = cuantiles([12.5])
        assert set(r) == {"p50", "p95", "p99", "media", "peor"}
        assert all(v == 12.5 for v in r.values())

    def test_no_requiere_orden_previo(self) -> None:
        r = cuantiles([250.0] + [16.0] * 59)
        assert r["p50"] == 16.0 and r["p95"] == 16.0


class TestElReloj:
    def test_tick_alimenta_el_historial(self) -> None:
        from src.engine.core.clock import DeltaClock
        reloj = DeltaClock()
        reloj.tick()
        assert len(reloj.historial_ms()) == 1

    def test_el_historial_no_crece_sin_limite(self) -> None:
        from src.engine.core.clock import (
            FOTOGRAMAS_EN_EL_HISTORIAL,
            DeltaClock,
        )
        reloj = DeltaClock()
        for _ in range(FOTOGRAMAS_EN_EL_HISTORIAL * 2):
            reloj.tick()
        assert len(reloj.historial_ms()) == FOTOGRAMAS_EN_EL_HISTORIAL

    def test_estadisticas_salen_del_historial(self) -> None:
        from src.engine.core.clock import DeltaClock
        reloj = DeltaClock()
        for _ in range(10):
            reloj.tick()
        r = reloj.estadisticas()
        assert "p50" in r and "peor" in r
        assert r["peor"] >= r["media"]


class TestLaConsola:
    def test_draw_acepta_los_cuantiles(self) -> None:
        import pygame

        from src.engine.core.estadisticas import cuantiles
        from src.engine.scenes.debug_overlay import DebugOverlay

        superficie = pygame.Surface((64, 64))
        DebugOverlay().draw(
            superficie, 60.0,
            estadisticas=cuantiles([16.0] * 59 + [250.0]))

    def test_sin_estadisticas_sigue_siendo_valido(self) -> None:
        import pygame

        from src.engine.scenes.debug_overlay import DebugOverlay

        DebugOverlay().draw(pygame.Surface((64, 64)), 60.0)

    def test_la_app_las_pasa(self) -> None:
        import inspect

        from src.engine.core import app

        fuente = inspect.getsource(app)
        assert "self.clock.estadisticas()" in fuente