"""AUD-451 — el HUD estaba maquetado para una pantalla que ya no existe.

`docs/09_HUD_SPEC.md` §2 lo dice con todas las letras: «the HUD occupies fixed
regions of the 320×224 internal screen». Pero `settings.INTERNAL_WIDTH` y
`INTERNAL_HEIGHT` son **800×600** desde hace tiempo, y el HUD se dibuja sin
escalar. Medido: el marcador vive en `Rect(124, 2, 128, 14)` y el cronómetro
acaba en x=320, así que todo el HUD ocupa el 40 % del ancho y el 12 % del alto,
arrinconado arriba a la izquierda.

De ahí que el score y las monedas «se vean muy pequeños»: no es la tipografía
—que también, y va aparte—, es que la maqueta entera está al 40 % de su
tamaño. Los corazones, el retrato y el cronómetro tienen el mismo problema.

Es el patrón que AUD-187 ya encontró en el menú de título: «un número heredado
de cuando la superficie interna medía 320x240». Allí era el tamaño de fuente;
aquí es la maqueta completa.

Qué se hace
-----------
Las regiones pasan a derivarse de la resolución interna real a través de una
escala, en vez de estar escritas para una resolución concreta. Así el HUD deja
de tener que reescribirse el día que la resolución vuelva a cambiar, que es
exactamente lo que no se hizo la vez anterior.
"""
from __future__ import annotations

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame
import pytest

from src.engine.core import settings
from src.engine.core.event_bus import EventBus


@pytest.fixture(scope="module")
def _video():
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT))
    yield


@pytest.fixture
def hud(_video):
    from src.engine.ui.hud import HUD

    h = HUD(EventBus())
    h.set_score(123456, 789)
    return h


class TestElHudUsaLaPantallaQueHay:
    def test_el_marcador_no_se_queda_en_el_primer_tercio(self, hud) -> None:
        """El síntoma medido: el HUD acababa en x=320 de 800."""
        r = hud.score_rect()
        assert r.right > settings.INTERNAL_WIDTH * 0.5, (
            f"el marcador acaba en x={r.right} de {settings.INTERNAL_WIDTH}: "
            f"el HUD sigue maquetado para la pantalla de 320 px"
        )

    def test_la_banda_del_marcador_da_para_leerlo(self, hud) -> None:
        r = hud.score_rect()
        assert r.height >= 20, (
            f"la banda del marcador mide {r.height} px de alto: no cabe una "
            f"cifra legible a 800x600"
        )

    def test_el_cronometro_esta_pegado_al_borde_derecho(self, hud) -> None:
        assert hud.timer_rect().right > settings.INTERNAL_WIDTH * 0.8, (
            "el cronómetro sigue en el primer tercio de la pantalla"
        )

    def test_los_corazones_son_visibles(self, hud) -> None:
        assert hud.heart_row_rect().height >= 16, (
            "los corazones siguen a la escala de 320 px"
        )


class TestNoSeSaleDeLaPantalla:
    def test_nada_del_hud_se_sale(self, hud) -> None:
        """Escalar sin comprobar sólo cambia un defecto por otro."""
        marco = pygame.Rect(0, 0, settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT)
        for nombre, region in hud.regiones().items():
            assert marco.contains(region), (
                f"la región {nombre!r} ({region}) se sale de la pantalla"
            )

    def test_las_regiones_no_se_pisan(self, hud) -> None:
        """El retrato, los corazones, el marcador y el reloj se leen a la vez."""
        regiones = hud.regiones()
        nombres = sorted(regiones)
        for i, a in enumerate(nombres):
            for b in nombres[i + 1:]:
                assert not regiones[a].colliderect(regiones[b]), (
                    f"{a} y {b} se solapan: {regiones[a]} vs {regiones[b]}"
                )

    def test_una_cifra_larga_sigue_cabiendo(self, hud) -> None:
        """El marcador se alinea a la derecha justo para esto (AUD-219)."""
        hud.set_score(99999999, 9999)
        r = hud.score_rect()
        assert r.left >= 0
        assert r.right <= settings.INTERNAL_WIDTH


class TestLaEscalaSaleDeLaResolucion:
    def test_no_hay_numeros_de_320_escritos_a_mano(self) -> None:
        """La lección de AUD-187, aplicada.

        Si la maqueta vuelve a escribirse en píxeles de una resolución
        concreta, el día que la resolución cambie el HUD se quedará otra vez
        arrinconado y nadie lo notará hasta que alguien lo mire de cerca.
        """
        from src.engine.ui import hud as modulo

        assert hasattr(modulo, "ESCALA_DEL_HUD"), (
            "el HUD ya no deriva su maqueta de la resolución interna"
        )
        assert modulo.ESCALA_DEL_HUD > 1.0, (
            f"la escala es {modulo.ESCALA_DEL_HUD}: a 800x600 tiene que "
            f"agrandar respecto del diseño de 320"
        )


class TestElDocumentoDiceLaVerdad:
    def test_la_spec_no_sigue_hablando_de_320(self) -> None:
        """Invariante 6 de CLAUDE.md: los números del doc son verificables."""
        from pathlib import Path

        raiz = Path(__file__).resolve().parent.parent
        spec = (raiz / "docs/09_HUD_SPEC.md").read_text(encoding="utf-8")
        assert "320×224" not in spec and "320x224" not in spec, (
            "la especificación sigue declarando la pantalla de 320×224, que "
            "no es la que el juego usa"
        )
