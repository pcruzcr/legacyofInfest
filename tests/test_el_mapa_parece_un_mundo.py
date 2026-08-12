"""AUD-448 — el mapa del mundo era una rejilla con una línea encima.

`_serpiente` colocaba los nodos en filas regulares alternando el sentido, así
que las columnas quedaban perfectamente alineadas y la línea que une los
escenarios era lo más llamativo de la pantalla. Se lee como una lista de
niveles doblada en zigzag, no como un mundo.

Lo que cambia:

* cada nodo se desplaza un poco de su casilla, de forma **estable**;
* la línea pasa a ser secundaria: más fina y más apagada que los marcadores;
* el marcador enfocado se distingue por tamaño y anillo, no sólo por color.

Estable, no aleatorio
---------------------
El desplazamiento sale del identificador del escenario, así que el mapa se
dibuja igual en todos los arranques. Un mapa que se recoloca cada vez que
abres el juego es peor que una rejilla: se pierde la memoria del sitio, que
es justo lo que hace que un mundo se sienta un mundo.
"""
from __future__ import annotations

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

from itertools import pairwise

import pytest

from src.engine.scenes.world_map_scene import construir_nodos, dispersion_de


@pytest.fixture(scope="module")
def nodos():
    ns = construir_nodos()
    if len(ns) < 4:
        pytest.skip("hacen falta varios escenarios para juzgar la disposición")
    return ns


class TestNoEsUnaRejilla:
    def test_las_columnas_no_estan_alineadas(self, nodos) -> None:
        """El síntoma exacto: en rejilla, muchos nodos comparten `nx`."""
        distintos = {round(n["nx"], 3) for n in nodos}
        assert len(distintos) >= len(nodos) * 0.8, (
            f"{len(distintos)} posiciones horizontales distintas para "
            f"{len(nodos)} escenarios: siguen en columnas"
        )

    def test_las_filas_tampoco(self, nodos) -> None:
        distintos = {round(n["ny"], 3) for n in nodos}
        assert len(distintos) >= len(nodos) * 0.5, (
            f"{len(distintos)} alturas distintas para {len(nodos)} escenarios"
        )


class TestSigueSiendoUsable:
    def test_los_nodos_no_se_salen(self, nodos) -> None:
        """Dispersar no puede empujar un escenario fuera de la pantalla."""
        for n in nodos:
            assert 0.0 <= n["nx"] <= 1.0, f"{n['id']} se sale por x: {n['nx']}"
            assert 0.0 <= n["ny"] <= 1.0, f"{n['id']} se sale por y: {n['ny']}"

    def test_los_nodos_no_se_pisan(self, nodos) -> None:
        """Dos marcadores encima no se pueden distinguir ni seleccionar."""
        for i, a in enumerate(nodos):
            for b in nodos[i + 1:]:
                distancia = ((a["nx"] - b["nx"]) ** 2
                             + (a["ny"] - b["ny"]) ** 2) ** 0.5
                assert distancia > 0.04, (
                    f"{a['id']} y {b['id']} caen casi encima ({distancia:.3f})"
                )

    def test_el_orden_de_juego_se_conserva(self, nodos) -> None:
        """Dispersar es cosmético: la cadena de desbloqueos no cambia."""
        for anterior, siguiente in pairwise(nodos):
            assert anterior["unlocks"] == [siguiente["id"]]


class TestElMapaNoSeMueveEntreArranques:
    def test_dos_construcciones_dan_lo_mismo(self) -> None:
        a = construir_nodos()
        b = construir_nodos()
        assert [(n["nx"], n["ny"]) for n in a] == [(n["nx"], n["ny"]) for n in b]

    def test_la_dispersion_depende_del_identificador(self) -> None:
        assert dispersion_de("stage0") == dispersion_de("stage0")
        assert dispersion_de("stage0") != dispersion_de("stage1_1")

    def test_la_dispersion_esta_acotada(self) -> None:
        """Sin tope, un escenario acabaría en la esquina opuesta a la suya."""
        for ident in ("stage0", "stage1_1", "hall", "boss_rey", "stage4_1"):
            dx, dy = dispersion_de(ident)
            assert abs(dx) <= 0.06 and abs(dy) <= 0.06, (
                f"{ident} se desplaza {dx:.3f},{dy:.3f}: demasiado"
            )
