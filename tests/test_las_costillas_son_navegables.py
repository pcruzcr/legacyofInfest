"""AUD-582 — GAP-061, la mitad navegable de las osamentas.

AUD-513 construyó la mitad **visual** (`_vertebra_gigante` al fondo, el
rayo la revela); faltaba la navegable: *«costillas formando arcos,
puentes... plataformas»* (punto 4 del diseño). El puente de costillas es
la primera plataforma de verdad del nivel — arquitectura que se cruza por
arriba, no sólo se mira. Va en el llano entre las dos lomas (365-375),
donde el jugador tiene el ritmo tranquilo para notarla.
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


@pytest.fixture(scope="module")
def _video():
    preparar_video()


@pytest.fixture
def escena(_video):
    sc = construir_escena()
    yield sc
    sc.on_exit()


class TestElPuenteDeCostillas:
    def test_hay_una_plataforma_de_un_sentido_en_su_rectangulo(
        self, escena,
    ) -> None:
        from src.stages.stage4_1 import trazado

        col, ancho, fila_cima = trazado.COSTILLA_NAVEGABLE
        ts = settings.TILE_SIZE
        esperado = pygame.Rect(col * ts, fila_cima * ts, ancho * ts, 8)
        assert escena._stage_data.one_way_rects == [esperado], (
            f"se esperaba exactamente el puente {esperado}, hay "
            f"{escena._stage_data.one_way_rects}")

    def test_sostiene_al_jugador_encima(self, escena) -> None:
        """De pie sobre el arco sin tocar una tecla: el one-way lo sostiene
        — no se cae a través ni al empezar ni tras asentarse."""
        from src.stages.stage4_1 import trazado

        col, ancho, fila_cima = trazado.COSTILLA_NAVEGABLE
        ts = settings.TILE_SIZE
        x = (col + ancho // 2) * ts
        escena._player.rect.midbottom = (x, fila_cima * ts)
        # `position` es la esquina superior izquierda, no los pies.
        escena._player.position.update(
            float(x), float(fila_cima * ts - escena._player.rect.height))
        # El resolutor de repisas mira los pies del fotograma anterior
        # (`prev_foot_y <= plat.top + 1`): teletransportarlo sin actualizar
        # esa memoria dejaría la guarda mintiendo un fotograma.
        escena._player._prev_foot_y = float(fila_cima * ts)
        for _ in range(90):
            escena.update(1 / 60)
        assert abs(escena._player.rect.bottom - fila_cima * ts) <= 3, (
            f"el jugador no se quedó sobre el arco: bottom="
            f"{escena._player.rect.bottom}, esperado {fila_cima * ts}")

    def test_al_salir_del_arco_se_cae_al_suelo(self, escena) -> None:
        """Cruzado caminando hacia la derecha, el arco se acaba y el mundo
        lo recibe más abajo — es un puente, no un segundo piso. Justo tras
        su extremo derecho empieza la subida de la segunda loma
        (`trazado.py`: el llano intermedio es 365-375 y el puente ocupa
        366-374), así que lo que comprueba la salida es la mecánica —
        deja de ser sostenido por el one-way y aterriza sobre el terreno —
        y no una columna exacta."""
        from src.stages.stage4_1 import trazado

        col, _ancho, fila_cima = trazado.COSTILLA_NAVEGABLE
        ts = settings.TILE_SIZE
        x = (col + 1) * ts
        escena._player.rect.midbottom = (x, fila_cima * ts)
        escena._player.position.update(
            float(x), float(fila_cima * ts - escena._player.rect.height))
        escena._player._prev_foot_y = float(fila_cima * ts)

        im = escena.context.input_manager
        im.pump([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RIGHT)])
        salio = False
        for _ in range(120):
            escena.update(1 / 60)
            if escena._player.rect.bottom > (fila_cima + 1) * ts:
                salio = True
                break
        im.pump([pygame.event.Event(pygame.KEYUP, key=pygame.K_RIGHT)])
        assert salio, (
            f"nunca dejó el arco caminando: bottom="
            f"{escena._player.rect.bottom}")
        for _ in range(45):
            escena.update(1 / 60)
        assert escena._player.is_grounded, (
            "salió del arco y quedó suspendido en el aire")
        assert abs(escena._player.rect.bottom
                   - trazado.FILA_SUELO * ts) <= 16, (
            f"no aterrizó a la altura del terreno: "
            f"bottom={escena._player.rect.bottom}")

    def test_el_arco_se_dibuja_en_su_sitio(self, escena) -> None:
        from src.stages.stage4_1 import trazado
        from tests.test_stage4_1 import _posicionar_sin_fisica

        col, _ancho, _fila = trazado.COSTILLA_NAVEGABLE
        _posicionar_sin_fisica(escena, col)
        lienzo = pygame.Surface(
            (settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT))
        offset = pygame.Vector2(col * settings.TILE_SIZE - 100, 0.0)
        escena._dibujar_costillas_navegables(lienzo, offset)
        assert _hay_tinta(lienzo), (
            "el arco de costillas no se pintó con su columna en pantalla")

    def test_no_se_dibuja_fuera_de_la_fase_3(self, escena) -> None:
        from src.stages.stage4_1 import trazado

        col, _ancho, _fila = trazado.COSTILLA_NAVEGABLE
        lienzo = pygame.Surface(
            (settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT))
        offset = pygame.Vector2(col * settings.TILE_SIZE - 100, 0.0)
        _posicionar_en_fase_1(escena)
        escena._dibujar_costillas_navegables(lienzo, offset)
        assert not _hay_tinta(lienzo)


def _posicionar_en_fase_1(escena) -> None:
    from tests.test_stage4_1 import _posicionar_sin_fisica

    _posicionar_sin_fisica(escena, 40)


def _hay_tinta(lienzo: pygame.Surface) -> bool:
    ancho, alto = lienzo.get_size()
    for y in range(alto // 2, alto - 10, 6):
        for x in range(0, ancho, 8):
            if lienzo.get_at((x, y))[:3] != (0, 0, 0):
                return True
    return False
