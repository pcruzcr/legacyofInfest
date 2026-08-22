"""AUD-581 — GAP-060 punto 15, la zona secundaria opcional de la Fase 2.

El diseño pedía *«una historia, una aparición o una tumba antigua»* —
basta una. La tumba antigua es la que encaja: el rastro de huellas del
Venado termina abruptamente (AUD-513) y la tumba explica el corte sin
decirlo — el Venado se detuvo ahí, ante la única piedra más vieja que el
cementerio.

Opcional **en atención**, no en camino (decisión del dueño, 2026-08-16:
pasillo horizontal, sin bifurcaciones): quien pase de largo no pierde
nada mecánico; quien se acerque a la piedra, se lleva una historia.
"""
from __future__ import annotations

import json
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame
import pytest

from src.engine.core import settings
from tests.ayudantes_stage4_1 import construir_escena, preparar_video
from tests.test_stage4_1 import _posicionar_sin_fisica


@pytest.fixture(scope="module")
def _video():
    preparar_video()


@pytest.fixture
def escena(_video):
    sc = construir_escena()
    yield sc
    sc.on_exit()


class TestLaTumba:
    def test_el_rastro_de_huellas_termina_junto_a_ella(self) -> None:
        """Las dos señales se amarran: las huellas no siguen de largo tras
        la tumba — el corte abrupto del rastro tiene dueño."""
        from src.stages.stage4_1 import trazado

        desde_fase2 = trazado.ANCHO_SECCION
        ultima_huella = desde_fase2 + max(trazado.HUELLAS_FASE2)
        columna = trazado.COLUMNA_TUMBA_ANTIGUA
        assert ultima_huella < columna <= ultima_huella + 6, (
            f"la tumba (col {columna}) no está junto al fin del rastro "
            f"(última huella en col {ultima_huella})")

    def test_hay_un_disparador_de_dialogo_a_los_pies(self, escena) -> None:
        from src.stages.stage4_1 import trazado

        disparadores = [
            o for o in escena._stage_data.message_triggers
            if getattr(o, "dialogue_tree_id", None) == "tumba_antigua"
        ]
        assert len(disparadores) == 1, (
            f"se esperaba un disparador de la tumba, hay "
            f"{len(disparadores)}")
        assert disparadores[0].rect.x == (
            trazado.COLUMNA_TUMBA_ANTIGUA * settings.TILE_SIZE)

    def test_el_dialogo_existe_y_cierra(self) -> None:
        """El árbol existe en `data/dialogues/stage4_1.json`, todos los
        nodos hablan, y toda opción lleva a un nodo que existe (o al
        final) — un diálogo roto sería un disparador que truena en cara
        del jugador."""
        ruta = ("data/dialogues/stage4_1.json")
        with open(ruta, encoding="utf-8") as f:
            arboles = json.load(f)
        arbol = next((a for a in arboles if a["id"] == "tumba_antigua"),
                     None)
        assert arbol is not None, (
            "falta el árbol 'tumba_antigua' en data/dialogues/stage4_1.json")
        nodos = arbol["nodes"]
        assert arbol["start"] in nodos
        for nodo in nodos.values():
            assert nodo.get("speaker"), "hay un nodo sin voz"
            assert nodo.get("text"), "hay un nodo sin texto"
            for _etiqueta, destino in nodo.get("choices", []):
                assert destino == "__end__" or destino in nodos, (
                    f"una opción lleva al nodo inexistente {destino!r}")

    def test_se_dibuja_cuando_esta_en_pantalla(self, escena) -> None:
        from src.stages.stage4_1 import trazado

        _posicionar_sin_fisica(escena, trazado.COLUMNA_TUMBA_ANTIGUA)
        lienzo = pygame.Surface(
            (settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT))
        offset = pygame.Vector2(
            trazado.COLUMNA_TUMBA_ANTIGUA * settings.TILE_SIZE - 100, 0.0)
        escena._dibujar_decoracion(lienzo, offset)
        assert _hay_tinta(lienzo), (
            "la tumba antigua no se pintó estando su columna en pantalla")

    def test_no_se_dibuja_fuera_de_la_fase_2(self, escena) -> None:
        from src.stages.stage4_1 import trazado

        _posicionar_sin_fisica(escena, 40)
        lienzo = pygame.Surface(
            (settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT))
        offset = pygame.Vector2(
            trazado.COLUMNA_TUMBA_ANTIGUA * settings.TILE_SIZE - 100, 0.0)
        escena._dibujar_decoracion(lienzo, offset)
        assert not _hay_tinta(lienzo)


def _hay_tinta(lienzo: pygame.Surface) -> bool:
    ancho, alto = lienzo.get_size()
    for y in range(alto // 2, alto - 30, 7):
        for x in range(0, ancho, 9):
            if lienzo.get_at((x, y))[:3] != (0, 0, 0):
                return True
    return False
