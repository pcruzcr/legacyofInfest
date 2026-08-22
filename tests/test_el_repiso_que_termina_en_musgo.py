"""AUD-580 — GAP-060 punto 8, el desafío de control de la Fase 2.

El dueño pidió *«una pendiente corta que termina en zona resbaladiza,
para que el jugador aprenda a frenar antes de entrar»*. Eso es el
repiso: subida corta, cima estrecha y bajada que aterriza **directo** en
un tramo de musgo — quien baje con velocidad entra patinando en la
inercia del musgo (AUD-522) y se pasa el punto de parada.

Las reglas de colisión son las mismas que las lomas de la Fase 3 por los
motivos ya documentados en `trazado.altura_de_colision` (AUD-470: bajo la
rampa no hay bloque sólido; AUD-477: la cima tampoco).
"""
from __future__ import annotations

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

from itertools import pairwise

import pygame
import pytest

from src.engine.core import settings
from tests.ayudantes_stage4_1 import construir_escena, preparar_video
from tests.test_stage4_1 import _llevar_a


@pytest.fixture(scope="module")
def _video():
    preparar_video()


@pytest.fixture
def escena(_video):
    sc = construir_escena()
    yield sc
    sc.on_exit()


class TestLaFormaDelRepiso:
    def test_sube_cima_estrecha_y_baja(self) -> None:
        from src.stages.stage4_1 import trazado

        inicio, ancho_subida, ancho_cima, ancho_bajada, fila_cima = (
            trazado.REPISO_FASE2)
        fin_subida = inicio + ancho_subida
        fin_cima = fin_subida + ancho_cima
        fin = fin_cima + ancho_bajada

        subida = [trazado.altura_del_suelo(c)
                  for c in range(inicio, fin_subida)]
        # No estricta: el perfil redondea (`round`), y con menos de una
        # fila por columna hay peldaños planos — igual que en las lomas,
        # cuya forma de verdad la prueba caminando, no la serie.
        assert all(a >= b for a, b in pairwise(subida)), (
            f"la subida no sube: {subida}")
        # La subida puede quedarse a un peldaño de `fila_cima` (el perfil
        # redondea por columna): que la cima sea llana en `fila_cima` es lo
        # que garantiza la altura de verdad, y eso se comprueba aquí abajo.

        cima = {trazado.altura_del_suelo(c)
                for c in range(fin_subida, fin_cima)}
        assert cima == {fila_cima}, f"la cima no es llana: {cima}"

        bajada = [trazado.altura_del_suelo(c)
                  for c in range(fin_cima, fin)]
        assert all(a <= b for a, b in pairwise(bajada)), (
            f"la bajada no baja: {bajada}")
        assert trazado.altura_del_suelo(fin) == trazado.FILA_SUELO, (
            "tras el repiso el suelo no vuelve al llano")

    def test_la_colision_bajo_la_rampa_es_plana(self) -> None:
        """La regla de AUD-470, ahora para el repiso: un escalón sólido por
        columna bloquearía el paso antes de que el `Slope` intervenga."""
        from src.stages.stage4_1 import trazado

        inicio, ancho_subida, *_resto = trazado.REPISO_FASE2
        alturas = {
            trazado.altura_de_colision(c)
            for c in range(inicio, inicio + ancho_subida)
        }
        assert alturas == {trazado.FILA_SUELO}

    def test_la_cima_tampoco_lleva_bloque_solido(self) -> None:
        """La regla de AUD-477: la cima es un `Pendiente` de altura cero,
        no un bloque — y sólo las columnas de la cima."""
        from src.stages.stage4_1 import trazado

        inicio, ancho_subida, ancho_cima, _ancho_bajada, _fila = (
            trazado.REPISO_FASE2)
        fin_subida = inicio + ancho_subida
        mesetas = {c for c in range(inicio - 2, fin_subida + ancho_cima + 2)
                   if trazado.es_meseta(c)}
        assert mesetas == set(range(fin_subida, fin_subida + ancho_cima))

    def test_el_musgo_recoge_la_bajada(self) -> None:
        """«Termina en zona resbaladiza»: el primer musgo después de la
        bajada empieza exactamente donde el repiso aterriza — sin llano
        intermedio que dé tiempo a frenar."""
        from src.stages.stage4_1 import trazado

        inicio, _subida, _cima, bajada, _fila = trazado.REPISO_FASE2
        aterrizaje = inicio + _subida + _cima + bajada
        segmento = next((s for s in trazado.SEGMENTOS_FASE2
                         if s[0] == aterrizaje), None)
        assert segmento is not None, (
            f"no hay ningún segmento de fricción que empiece en la columna "
            f"{aterrizaje}, donde aterriza el repiso")
        assert segmento[2] == "musgo", (
            "el desafío es de inercia (musgo), no de freno (lodo)")


class TestSeSubeDeVerdad:
    def test_se_suben_los_peldanos_caminando(self, escena) -> None:
        """Recorrido real con física: entra antes del repiso, camina a la
        derecha sin soltar, y mide que sube en el repiso y baja de vuelta
        al llano — y que lo cruza, sin quedarse clavado en la unión."""
        from src.stages.stage4_1 import trazado

        inicio, subida, cima, bajada, _fila = trazado.REPISO_FASE2
        fin = inicio + subida + cima + bajada

        _llevar_a(escena, inicio - 6)

        im = escena.context.input_manager
        im.pump([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RIGHT)])
        muestras: list[tuple[float, int]] = []
        for _ in range(900):
            escena.update(1 / 60)
            col = escena._player.rect.centerx / settings.TILE_SIZE
            muestras.append((col, escena._player.rect.centery))
        im.pump([pygame.event.Event(pygame.KEYUP, key=pygame.K_RIGHT)])

        base = muestras[0][1]
        en_repiso = [cy for col, cy in muestras if inicio <= col <= fin]
        assert en_repiso, "el recorrido nunca pisó el repiso"
        assert min(en_repiso) < base - 50, (
            f"no subió de verdad: base={base}, mínimo={min(en_repiso)}")

        al_final = muestras[-1]
        assert al_final[0] > fin + 3, (
            f"se quedó clavado antes de cruzar el repiso: "
            f"columna final={al_final[0]}")
        # El aterrizaje se mide **justo tras la bajada**, no al final del
        # recorrido: caminando sin soltar, el jugador sigue avanzando y se
        # sube a la siguiente elevación del terreno (fila 24 en vez del
        # llano 30) — eso es el nivel, no el repiso.
        aterrizajes = [cy for col, cy in muestras
                       if fin + 1 <= col <= fin + 10 and abs(cy - base) <= 8]
        assert aterrizajes, (
            f"no bajó de vuelta al llano tras el repiso: ninguna muestra en "
            f"las diez columnas posteriores vuelve a la altura de salida "
            f"(base={base})")

    def test_las_pendientes_del_repiso_viven_en_la_fase_2(self) -> None:
        from src.stages.stage4_1 import trazado

        inicio, _s, _c, _b, _f = trazado.REPISO_FASE2
        fin = inicio + _s + _c + _b
        for col in range(inicio, fin):
            assert trazado.fase_de_la_columna(col) == 2
