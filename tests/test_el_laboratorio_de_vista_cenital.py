"""AUD-383 — el motor sabía jugar desde arriba y ningún mapa lo declaraba.

El hueco
========
`vista=cenital` existe desde AUD-129: quita la gravedad, deja el movimiento en
dos ejes y trae los tres modos de cámara. Tiene su preset de física
(`PhysicsProfile.cenital()`), sus pruebas unitarias (`test_vista_cenital.py`) y
su documentación.

Y **ningún mapa del repositorio lo declaraba**, así que era un modo de juego
entero que el estudiante no podía descubrir: no lo ve jugando, no lo encuentra
abriendo un mapa en Tiled, y sólo podía enterarse leyendo la especificación.
Lo destapó AUD-378 al arreglar el punto ciego del guardián de cobertura.

Qué fija esta prueba, y por qué no basta con las que ya había
=============================================================
`test_vista_cenital.py` comprueba la **física** en aislamiento: un jugador con
`vista_cenital = True` no cae. Eso seguiría pasando con el mapa borrado.

Lo que falta comprobar es el camino entero —TMX → cargador → escena → jugador—,
que es donde estaba el hueco: la propiedad existía y nadie la escribía. Es el
mismo razonamiento que `TestLaAtmosferaLlegaAlJuego` en `test_ambience.py`, y
por el mismo motivo: las pruebas en aislamiento no ven que la escena no conecte
las dos cosas.
"""
from __future__ import annotations

import pygame
import pytest


@pytest.fixture(scope="module")
def display():
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((800, 600))
    yield pygame.display.get_surface()


@pytest.fixture
def datos(display):
    from src.framework.stage.stage_loader import StageLoader

    return StageLoader.load("assets/maps/stage_cenital/stage_cenital.tmx")


class TestElMapaDeclaraLoQueVieneADemostrar:
    """Las cuatro propiedades que ningún otro mapa declaraba."""

    def test_la_vista_es_cenital(self, datos):
        assert datos.vista == "cenital", (
            "el laboratorio de vista cenital no declara la vista cenital, que "
            "es lo único que viene a demostrar"
        )

    def test_declara_un_modo_de_camara(self, datos):
        from src.framework.stage.stage_data import MODOS_DE_CAMARA

        assert datos.camara in MODOS_DE_CAMARA

    def test_declara_el_rango_de_profundidad(self, datos):
        """Plano a propósito: una vista en planta pura no escala con la Y."""
        assert datos.profundidad_min == datos.profundidad_max == 1.0


class TestSeJuegaDeVerdad:
    """El camino completo. Sin esto, el mapa podría cargar y no ser jugable."""

    @pytest.fixture
    def contexto(self, display):
        from src.engine.audio.audio_manager import AudioManager
        from src.engine.core.event_bus import EventBus
        from src.engine.core.game_context import GameContext
        from src.engine.core.save_manager import SaveManager
        from src.engine.input.input_manager import InputManager
        from src.engine.scene.scene_manager import SceneManager
        from src.framework.entities import entity_factory

        entity_factory.ensure_registered()
        ctx = GameContext(
            input_manager=InputManager(), audio_manager=AudioManager(),
            scene_manager=None, event_bus=EventBus(), clock=None,
            save_manager=SaveManager(),
        )
        ctx.scene_manager = SceneManager(ctx)
        return ctx

    @staticmethod
    def _jugar(escena, segundos: float = 1.0):
        lienzo = pygame.Surface((800, 600))
        escena.awake()
        escena.start()
        escena.on_enter()
        for _ in range(int(segundos * 60)):
            escena.update(1 / 60)
            escena.draw(lienzo)
        return escena

    def test_el_jugador_no_cae(self, contexto):
        """La prueba que define la vista, hecha sobre el escenario real.

        En lateral, un segundo de caída libre son cientos de píxeles. Aquí la
        Y no puede moverse sola: si se mueve, la escena no le pasó la vista al
        jugador y el mapa no demuestra nada.
        """
        from src.stages.stage_cenital.stage_cenital import StageCenital

        escena = StageCenital(contexto)
        self._jugar(escena)
        y = escena._player.position.y
        assert abs(y - escena._stage_data.spawn_point.y) < 8.0, (
            f"tras un segundo el jugador está en y={y:.0f} y nació en "
            f"{escena._stage_data.spawn_point.y:.0f}: está cayendo, o sea que "
            "la vista cenital no llegó desde el TMX hasta el jugador"
        )

    def test_el_jugador_recibe_el_perfil_cenital(self, contexto):
        from src.framework.physics.perfil import CENITAL
        from src.stages.stage_cenital.stage_cenital import StageCenital

        escena = StageCenital(contexto)
        self._jugar(escena, segundos=0.2)
        assert escena._player.perfil.modo == CENITAL


def test_el_escenario_se_descubre():
    """Un escenario que el registro no encuentra es un escenario que no existe.

    Es la lección de `stage_mecanicas`: el mapa puede estar perfecto y no
    aparecer en ninguna parte desde la que se pueda abrir.
    """
    import importlib

    modulo = importlib.import_module("src.stages.stage_cenital.stage_cenital")
    from src.engine.scene.base_scene import BaseScene

    escenas = [
        obj for nombre in dir(modulo)
        if isinstance(obj := getattr(modulo, nombre), type)
        and issubclass(obj, BaseScene) and obj is not BaseScene
    ]
    assert escenas, "el módulo no expone ninguna escena que el registro pueda hallar"
