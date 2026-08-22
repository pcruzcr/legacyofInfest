"""AUD-583 — GAP-063, los eventos que faltaban en la Planicie de los
Muertos: la procesión que se acerca cada ciclo lunar y la multitud que
desaparece sin explicación.

AUD-513 dejó el gancho (`_dibujar_figura_de_la_luna`, una figura que sólo
se ve a oscuras) y el diseño pide el catálogo: *«una procesión lejana que
está más cerca la próxima vez que vuelve la luna»* (punto 16) y *«una
multitud de figuras que desaparece sin explicación»* (punto 20).

Las dos reglas de oro del nivel valen aquí: son presencia, no evento —
sin sonido, sin disparador, sin estado que guardar— y lo sobrenatural no
se anuncia: la procesión avanza sólo cuando nadie ve (con la luna
oculta), y la multitud se esfuma justo cuando llegas a verla bien.
"""
from __future__ import annotations

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


LUNA_ALTA = 0.48   # ambiente con la luna en cima (AMBIENTE_MAX_LUNA)
LUNA_BAJA = 0.20   # ambiente con la luna escondida (AMBIENTE_MIN_LUNA)


def _ciclo(escena, oculta: bool) -> None:
    """Un medio paso del ciclo lunar, sin esperar los 6 s del periodo."""
    escena._ambiente_base = LUNA_BAJA if oculta else LUNA_ALTA
    escena._actualizar_procesion(1 / 60)


class TestLaProcesion:
    def test_con_la_luna_alta_no_hay_nada(self, escena) -> None:
        _posicionar_sin_fisica(escena, 640)
        _ciclo(escena, oculta=False)
        assert not escena._procesion_visible

    def test_aparece_cuando_la_luna_se_esconde(self, escena) -> None:
        _posicionar_sin_fisica(escena, 640)
        _ciclo(escena, oculta=False)
        _ciclo(escena, oculta=True)
        assert escena._procesion_visible, (
            "la luna se ocultó y la procesión no asomó")

    def test_se_va_cuando_vuelve_la_luz(self, escena) -> None:
        _posicionar_sin_fisica(escena, 640)
        _ciclo(escena, oculta=True)
        _ciclo(escena, oculta=False)
        assert not escena._procesion_visible

    def test_cada_ciclo_esta_mas_cerca(self, escena) -> None:
        _posicionar_sin_fisica(escena, 640)
        _ciclo(escena, oculta=True)
        primero = escena._paralaje_de_la_procesion()
        _ciclo(escena, oculta=False)
        _ciclo(escena, oculta=True)
        segundo = escena._paralaje_de_la_procesion()
        assert segundo > primero, (
            f"la procesión no avanzó entre ciclos: {primero} -> {segundo}")

    def test_tras_varios_ciclos_ya_no_vuelven(self, escena) -> None:
        _posicionar_sin_fisica(escena, 640)
        for _ in range(escena.CICLOS_DE_LA_PROCESION):
            _ciclo(escena, oculta=True)
            _ciclo(escena, oculta=False)
        _ciclo(escena, oculta=True)
        assert not escena._procesion_visible, (
            "tras todos los ciclos la procesión volvió a asomar: la "
            "procesión que se acerca tiene que llegar alguna vez")

    def test_dibujarla_no_explota(self, escena) -> None:
        _posicionar_sin_fisica(escena, 640)
        _ciclo(escena, oculta=True)
        lienzo = pygame.Surface(
            (settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT))
        escena._dibujar_procesion(lienzo, pygame.Vector2(0.0, 0.0))


class TestLaMultitud:
    @staticmethod
    def _offset_sobre_la_multitud() -> pygame.Vector2:
        """El offset de cámara que pone la columna de la multitud en el
        centro de la pantalla, deshecho el paralaje 0.85 con que se
        dibuja."""
        from src.stages.stage4_1 import trazado

        mundo_x = trazado.COLUMNA_DE_LA_MULTITUD * settings.TILE_SIZE
        return pygame.Vector2((mundo_x - 400) / 0.85, 0.0)

    def test_estan_junto_a_su_tumba_mientras_nadie_llega(
        self, escena,
    ) -> None:
        from src.stages.stage4_1 import trazado

        _posicionar_sin_fisica(escena, trazado.COLUMNA_DE_LA_MULTITUD - 40)
        assert escena._multitud_presente
        lienzo = pygame.Surface(
            (settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT))
        escena._dibujar_multitud(lienzo, self._offset_sobre_la_multitud())
        assert _hay_tinta(lienzo)

    def test_se_esfuman_al_acercarse(self, escena) -> None:
        from src.stages.stage4_1 import trazado

        _posicionar_sin_fisica(escena, trazado.COLUMNA_DE_LA_MULTITUD)
        escena._actualizar_multitud()
        assert not escena._multitud_presente, (
            "la multitud aguantó la mirada de cerca: su gracia es "
            "desaparecer sin explicación")
        lienzo = pygame.Surface(
            (settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT))
        escena._dibujar_multitud(lienzo, self._offset_sobre_la_multitud())
        assert not _hay_tinta(lienzo)

    def test_no_vuelven(self, escena) -> None:
        from src.stages.stage4_1 import trazado

        _posicionar_sin_fisica(escena, trazado.COLUMNA_DE_LA_MULTITUD)
        escena._actualizar_multitud()
        _posicionar_sin_fisica(escena, trazado.COLUMNA_DE_LA_MULTITUD - 60)
        for _ in range(30):
            escena.update(1 / 60)
        assert not escena._multitud_presente


def _hay_tinta(lienzo: pygame.Surface) -> bool:
    ancho, alto = lienzo.get_size()
    for y in range(alto // 2, alto - 10, 6):
        for x in range(0, ancho, 8):
            if lienzo.get_at((x, y))[:3] != (0, 0, 0):
                return True
    return False
