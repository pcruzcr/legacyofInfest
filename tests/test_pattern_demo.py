"""
Module: test_pattern_demo
System: tests
Academic Unit: VIII

La demo de reconocimiento de patrones no funcionaba al abrirla.

No fallaba de forma ruidosa: el `except` de `_compute_result` convertía el
error en un `logger.warning`, así que la escena arrancaba, no se caía, pasaba
el arnés de humo —que sólo comprueba que no haya excepciones— y mostraba
"Error: subsurface rectangle outside surface area" en bucle. Se descubrió
midiendo el coste por fotograma de todas las escenas: el aviso salía por
consola tres veces por segundo.

Lo que se prueba aquí es el contrato que el arnés de humo no cubre: **que la
demo produzca un resultado**, no sólo que sobreviva.
"""
from __future__ import annotations

import logging

import pygame
import pytest

from src.engine.scenes.pattern_demo_scene import PANEL_SIZE, TOP_BAR_H, PatternDemoScene


@pytest.fixture(scope="module")
def display():
    pygame.init()
    pygame.font.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((800, 600))
    yield pygame.display.get_surface()


@pytest.fixture
def escena(display):
    from src.engine.audio.audio_manager import AudioManager
    from src.engine.core.event_bus import EventBus
    from src.engine.core.game_context import GameContext
    from src.engine.core.save_manager import SaveManager
    from src.engine.input.input_manager import InputManager
    from src.engine.scene.scene_manager import SceneManager

    ctx = GameContext(
        input_manager=InputManager(),
        audio_manager=AudioManager(),
        scene_manager=None,
        event_bus=EventBus(),
        clock=None,
        save_manager=SaveManager(),
    )
    ctx.scene_manager = SceneManager(ctx)
    s = PatternDemoScene(ctx)
    s.awake()
    s.start()
    s.on_enter()
    return s


class TestElRecuadroDeAnalisisCabeEnLaImagen:
    """AUD-079 — se recortaba contra el panel, no contra la imagen."""

    def test_el_recuadro_inicial_esta_dentro_de_la_fuente(self, escena):
        fuente = escena._sources.current_source
        assert fuente is not None, "sin fuente no hay nada que probar"
        limites = pygame.Rect((0, 0), fuente.get_size())
        recuadro = pygame.Rect(
            escena._rect_x, escena._rect_y, escena._rect_size, escena._rect_size)
        escena._clamp_analysis_rect()
        recuadro = pygame.Rect(
            escena._rect_x, escena._rect_y, escena._rect_size, escena._rect_size)
        assert limites.contains(recuadro), (
            f"recuadro {tuple(recuadro)} fuera de la imagen {fuente.get_size()}"
        )

    def test_subsurface_no_lanza_con_el_recuadro_recortado(self, escena):
        escena._clamp_analysis_rect()
        fuente = escena._sources.current_source
        # Esta es la llamada exacta que fallaba.
        fuente.subsurface(pygame.Rect(
            escena._rect_x, escena._rect_y, escena._rect_size, escena._rect_size))

    @pytest.mark.parametrize(
        ("x", "y", "lado"),
        [(-500, -500, 32), (9999, 9999, 32), (0, 0, 9999), (0, 0, 1), (10, 10, 80)],
    )
    def test_cualquier_posicion_absurda_se_recorta(self, escena, x, y, lado):
        """El estudiante mantiene W o D pulsado hasta que se aburre."""
        escena._rect_x, escena._rect_y, escena._rect_size = x, y, lado
        escena._clamp_analysis_rect()
        fuente = escena._sources.current_source
        limites = pygame.Rect((0, 0), fuente.get_size())
        recuadro = pygame.Rect(
            escena._rect_x, escena._rect_y, escena._rect_size, escena._rect_size)
        assert limites.contains(recuadro)
        assert escena._rect_size >= 1
        fuente.subsurface(recuadro)   # no debe lanzar

    def test_cambiar_de_fuente_vuelve_a_recortar(self, escena):
        """Las fuentes no miden todas lo mismo; el recuadro tiene que seguirlas."""
        escena._clamp_analysis_rect()
        fuente = escena._sources.current_source
        original = fuente.get_size()
        pequena = pygame.Surface((8, 8))
        escena._sources._sources_by_name = getattr(
            escena._sources, "_sources_by_name", {})

        # Sustituimos la fuente por una más pequeña sin tocar el recuadro.
        escena._rect_x, escena._rect_y, escena._rect_size = 0, 0, min(original)
        original_prop = type(escena._sources).current_source
        try:
            type(escena._sources).current_source = property(lambda self: pequena)
            escena._compute_result()          # debe recortar por dentro
            assert escena._rect_size <= 8
            pequena.subsurface(pygame.Rect(
                escena._rect_x, escena._rect_y, escena._rect_size, escena._rect_size))
        finally:
            type(escena._sources).current_source = original_prop


class TestLaDemoProduceUnResultado:
    """Sobrevivir no es funcionar. El arnés de humo sólo medía lo primero."""

    def test_ningun_aviso_de_calculo_en_treinta_fotogramas(self, escena, caplog):
        superficie = pygame.Surface((800, 600))
        with caplog.at_level(logging.WARNING, logger="src.engine.scenes.pattern_demo_scene"):
            for _ in range(30):
                escena.update(1 / 60)
                escena.draw(superficie)
        avisos = [r.message % r.args if r.args else r.message for r in caplog.records]
        problemas = [m for m in avisos if "compute error" in m or "subsurface failed" in m]
        assert not problemas, f"la demo se queja mientras se juega: {problemas[:3]}"

    def test_no_queda_mensaje_de_error_en_pantalla(self, escena):
        superficie = pygame.Surface((800, 600))
        for _ in range(30):
            escena.update(1 / 60)
            escena.draw(superficie)
        assert not escena._error_msg, f"error visible: {escena._error_msg!r}"

    def test_el_calculo_deja_un_vector_de_caracteristicas(self, escena):
        escena._compute_result()
        assert escena._cached_feature is not None
        assert len(escena._cached_feature) > 0

    @pytest.mark.parametrize("modo", [0, 1, 2, 3, 4, 5])
    def test_todos_los_modos_calculan_sin_quejarse(self, escena, caplog, modo):
        escena._mode = modo
        with caplog.at_level(logging.WARNING, logger="src.engine.scenes.pattern_demo_scene"):
            escena._compute_result()
        problemas = [
            r.message % r.args if r.args else r.message
            for r in caplog.records
            if "compute error" in r.message or "subsurface failed" in r.message
        ]
        assert not problemas, f"modo {modo}: {problemas}"


class TestElRecuadroSeDibujaDondeApunta:
    """AUD-081 — el recuadro guía estaba en la escala equivocada."""

    @staticmethod
    def _pixeles_amarillos(superficie):
        amarillo = (255, 220, 80)
        return [
            (x, y)
            for x in range(PANEL_SIZE[0])
            for y in range(TOP_BAR_H, min(600, TOP_BAR_H + PANEL_SIZE[1]))
            if superficie.get_at((x, y))[:3] == amarillo
        ]

    def test_el_recuadro_amarillo_cubre_la_parte_proporcional_del_panel(self, escena):
        """Medio ancho de imagen debe pintarse como medio ancho de panel.

        El recuadro se elige a media escala a propósito: uno que cubriera toda
        la imagen quedaría exactamente debajo del borde del panel y no se
        vería, y la prueba pasaría por la razón equivocada.
        """
        fuente = escena._sources.current_source
        ancho, alto = fuente.get_size()
        escena._rect_x = escena._rect_y = 0
        escena._rect_size = max(1, min(ancho, alto) // 2)

        superficie = pygame.Surface((800, 600))
        escena.draw(superficie)

        puntos = self._pixeles_amarillos(superficie)
        assert puntos, "el recuadro guía no se dibuja"
        ancho_pintado = max(x for x, _ in puntos) - min(x for x, _ in puntos)
        esperado = escena._rect_size * PANEL_SIZE[0] / ancho
        assert abs(ancho_pintado - esperado) <= 3, (
            f"el recuadro mide {ancho_pintado} px en pantalla y debería medir "
            f"~{esperado:.0f}; se está dibujando en coordenadas de la imagen "
            "en vez de las del panel"
        )

    def test_el_recuadro_se_desplaza_al_moverlo(self, escena):
        """Mover el recuadro en la imagen debe moverlo en pantalla."""
        fuente = escena._sources.current_source
        ancho, _alto = fuente.get_size()
        escena._rect_size = max(1, ancho // 4)

        escena._rect_x = 0
        escena._clamp_analysis_rect()
        s1 = pygame.Surface((800, 600))
        escena.draw(s1)
        izquierda = min(x for x, _ in self._pixeles_amarillos(s1))

        escena._rect_x = ancho - escena._rect_size
        escena._clamp_analysis_rect()
        s2 = pygame.Surface((800, 600))
        escena.draw(s2)
        derecha = min(x for x, _ in self._pixeles_amarillos(s2))

        desplazamiento = derecha - izquierda
        esperado = (ancho - escena._rect_size) * PANEL_SIZE[0] / ancho
        assert abs(desplazamiento - esperado) <= 3, (
            f"al mover el recuadro a la derecha se desplazó {desplazamiento} px "
            f"y debería desplazarse ~{esperado:.0f}"
        )

    def test_el_recuadro_no_se_sale_del_panel(self, escena):
        fuente = escena._sources.current_source
        escena._rect_x, escena._rect_y = fuente.get_width(), fuente.get_height()
        escena._clamp_analysis_rect()
        superficie = pygame.Surface((800, 600))
        escena.draw(superficie)
        amarillo = (255, 220, 80)
        fuera = [
            (x, y)
            for x in range(800)
            for y in range(0, TOP_BAR_H)
            if superficie.get_at((x, y))[:3] == amarillo
        ]
        assert not fuera, f"el recuadro invade la barra superior en {fuera[:3]}"
