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


class TestLosSpritesVanALaEscala:
    def test_el_corazon_entero_mide_35x20(self, hud) -> None:
        """AUD-459 — los rects estaban a ×2,5 y los sprites a pelo.

        El corazón de 14×8 px dentro de una hilera espaciada a 40 px es la
        mitad del defecto del «HUD desacomodado»: la maqueta prometía una
        silueta de 35×20 y en pantalla había una de 14×8.
        """
        from src.engine.ui.theme import escalar

        assert hud._heart_sprites["full"].get_size() == (
            escalar(14), escalar(8),
        )

    def test_el_retrato_va_a_la_escala_de_su_marco(self, hud) -> None:
        """AUD-499 — el número bajó de 32 a 22 de lado por decisión del dueño.

        AUD-459 subió el sprite a `escalar(32)` para que llenara un marco de
        34 de maqueta, y a ×2,5 eso daba una cara de 85×85: el elemento más
        grande de la franja. Se describió jugando como «muy grande». Lo que
        se comprueba aquí no es el número —ése es una decisión de diseño y
        puede volver a moverse— sino la relación que sí tiene que
        cumplirse: el sprite llena su marco y no lo desborda.
        """
        marco = hud.regiones()["retrato"]
        ancho, alto = hud._portraits["normal"].get_size()
        assert ancho <= marco.width and alto <= marco.height, (
            f"el retrato ({ancho}×{alto}) desborda su marco ({marco.size})"
        )
        assert ancho >= marco.width * 0.8, (
            f"el retrato ({ancho}) nada dentro de un marco de {marco.width}"
        )

    def test_el_retrato_no_se_come_la_franja(self, hud) -> None:
        """El sintoma reportado, medido: 85 px de 800 era el 10,6 % del ancho."""
        marco = hud.regiones()["retrato"]
        assert marco.width <= settings.INTERNAL_WIDTH * 0.09, (
            f"el retrato ocupa {marco.width / settings.INTERNAL_WIDTH:.1%} del "
            f"ancho de la pantalla"
        )

    def test_la_barra_del_jefe_ocupa_mas_de_la_mitad(self, hud) -> None:
        """La barra del jefe era la última maqueta sin escalar: 200 px a pelo."""
        hud.set_boss_hud("JEFE", 50.0, 100.0, 1, 0)
        lienzo = pygame.Surface((settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT))
        hud._draw_boss_hud(lienzo)
        rachas_anchas = []
        for y in range(lienzo.get_height()):
            racha = 0
            for x in range(lienzo.get_width()):
                if lienzo.get_at((x, y))[:3] != (0, 0, 0):
                    racha += 1
                elif racha:
                    rachas_anchas.append(racha)
                    racha = 0
            if racha:
                rachas_anchas.append(racha)
        assert rachas_anchas, "la barra del jefe no se dibujó"
        assert max(rachas_anchas) >= settings.INTERNAL_WIDTH // 2, (
            "la barra del jefe sigue a la escala de la maqueta de 320 px"
        )


class TestElHudMuestraLaFaseActualDelJefe:
    """AUD-512 — `set_boss_hud` recibía `phase` (la actual) y lo tiraba:
    sólo guardaba `phase_count` (el total), y `_draw_boss_hud` renderizaba
    ``f"PHASE {self._boss_phase_count}"`` — el total, fijo durante toda la
    pelea, en el sitio donde debía ir la fase actual. `src/stages/
    boss_venado/` traía un parche a nivel de escena para compensarlo
    (`_compensate_boss_hud_phase`, H-02); con el motor arreglado, ese parche
    se ha quitado — habría sobreescrito el `phase_count` correcto con el
    número de fase actual.
    """

    def test_set_boss_hud_guarda_la_fase_actual_y_no_solo_el_total(
        self, hud,
    ) -> None:
        hud.set_boss_hud("JEFE", 80.0, 100.0, 1, 3)
        assert hud._boss_phase == 1
        assert hud._boss_phase_count == 3

        hud.set_boss_hud("JEFE", 60.0, 100.0, 2, 3)
        assert hud._boss_phase == 2
        assert hud._boss_phase_count == 3, (
            "el total no debe cambiar sólo porque avanzó la fase"
        )

    def test_el_evento_boss_phase_changed_tambien_actualiza_la_fase_actual(
        self, hud,
    ) -> None:
        """La otra ruta: `BossBase.change_phase` emite `phase` 0-indexado
        (`self.current_phase`) y `phase_count`. `set_boss_hud`, en cambio, lo
        recibe ya 1-indexado desde `actualizaciones.py`. Las dos rutas deben
        acabar de acuerdo tras el mismo cambio de fase."""
        hud._on_boss_phase_changed(boss_name="JEFE", phase=1, phase_count=3,
                                   new_max_health=50.0)
        assert hud._boss_phase == 2, (
            "el evento manda `phase` 0-indexado; el HUD debe normalizarlo "
            "igual que `set_boss_hud` (que ya lo recibe +1)"
        )
        assert hud._boss_phase_count == 3


class TestElMinimapaTieneSuSitio:
    """AUD-499 — el minimapa se colocaba solo en el borde derecho, en píxeles
    de pantalla y sin pasar por la escala, mientras el cronómetro ocupaba el
    borde derecho de la maqueta. Se solapaban en 80×38 px, y la prueba de «no
    se pisan» no lo cazaba porque el minimapa no estaba en `regiones()`."""

    def test_esta_declarado_como_region(self, hud) -> None:
        assert "minimapa" in hud.regiones()

    def test_no_pisa_al_cronometro(self, hud) -> None:
        r = hud.regiones()
        assert not r["minimapa"].colliderect(r["cronometro"]), (
            f"el minimapa {r['minimapa']} está encima del reloj "
            f"{r['cronometro']}"
        )

    def test_el_minimapa_suelto_nace_en_el_hueco_del_hud(self, hud) -> None:
        """Un `Minimap()` sin argumentos —lo que hacen las pruebas y las
        entregas— tiene que caer donde el HUD dice, no donde él crea."""
        from src.engine.ui.minimap import Minimap

        m = Minimap()
        suyo = pygame.Rect(m._minimap_x, m._minimap_y, m._minimap_w, m._minimap_h)
        assert suyo == hud.minimap_rect()


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
