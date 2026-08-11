"""AUD-362: el ambiente deja de ser decoración y llega a las reglas.

Qué se fija aquí
===============

`test_el_estado_del_ambiente.py` fija el contrato y
`test_la_simulacion_del_mundo.py` fija quién lo produce. Los dos son puros: no
arrancan una escena. Faltaba lo único que demuestra que el sistema **sirve**:
que un escenario real lo monta y que un cambio en el mundo cambia una regla
del juego.

Sin este fichero, `WorldSimulation` sería exactamente el defecto que AUD-355
encontró en la verja de física: código escrito, probado y sin ningún
consumidor de producción. El detector de huérfanos lo dijo en voz alta en
cuanto apareció el paquete (`test_sistemas_huerfanos` en rojo), y eso es lo
que este fichero cierra.

El hilo completo, de punta a punta:

    clima del TMX → humedad → suelo mojado → frenado → PhysicsProfile.friccion

La última pieza es lo que hace la diferencia entre una lluvia bonita y una
lluvia que se juega: `PhysicsProfile.friccion` existe desde AUD-336 y **los
tres presets la dejaban en 0**. El ambiente es su primer consumidor.
"""
from __future__ import annotations

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame
import pytest

from src.engine.audio.audio_manager import AudioManager
from src.engine.core.event_bus import EventBus
from src.engine.core.game_context import GameContext
from src.engine.core.save_manager import SaveManager
from src.engine.input.input_manager import InputManager
from src.engine.scene.scene_manager import SceneManager
from src.framework.entities import entity_factory
from src.framework.world import EnvironmentState


@pytest.fixture(autouse=True)
def display():
    """El escenario construye fuentes y superficies: SDL tiene que estar vivo."""
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((800, 600))
    yield pygame.display.get_surface()


@pytest.fixture
def escena():
    from src.stages.stage0.stage0 import Stage0

    entity_factory.ensure_registered()
    ctx = GameContext(
        input_manager=InputManager(), audio_manager=AudioManager(),
        scene_manager=None, event_bus=EventBus(), clock=None,
        save_manager=SaveManager(),
    )
    ctx.scene_manager = SceneManager(ctx)
    s = Stage0(ctx)
    s.awake()
    s.start()
    s.on_enter()
    return s


class TestLaEscenaPublicaSuAmbiente:
    """La API que faltaba: cualquiera puede preguntar por el mundo."""

    def test_la_escena_expone_un_estado_de_ambiente(self, escena) -> None:
        assert isinstance(escena.ambiente, EnvironmentState)

    def test_el_estado_lleva_la_hora_del_escenario(self, escena) -> None:
        escena._reloj._hora = 3.0
        escena._aplicar_hora()
        assert escena.ambiente.hora == pytest.approx(3.0)
        assert escena.ambiente.es_de_noche

    def test_hay_un_solo_reloj(self, escena) -> None:
        """`_reloj` es el de la simulación, no una segunda copia.

        Dos relojes es el defecto que este sistema entero viene a cerrar: se
        desincronizan en cuanto alguien mueve uno.
        """
        assert escena._reloj is escena._simulacion.reloj

    def test_la_estacion_es_una_vista_y_no_una_copia(self, escena) -> None:
        """Cambiar la estación de la escena llega hasta la simulación.

        `ambiente` es la foto del fotograma, así que hay que pedir el
        siguiente (`_aplicar_hora`) para verla — igual que en el juego, donde
        lo hace el bucle. Lo que se comprueba aquí es que el cambio **llega**:
        antes de AUD-362 la escena guardaba su propia `Estacion` y componía la
        luz con ella, así que había dos copias del mismo hecho.
        """
        escena._estacion = "winter"
        escena._aplicar_hora()
        assert escena.ambiente.estacion == "winter"
        assert escena._estacion.clima == "snow"


class TestElClimaCambiaLasReglas:
    """El hilo entero: TMX → humedad → suelo mojado → control."""

    @staticmethod
    def _con_clima(escena, clima: str):
        """Deja el clima **ya establecido**, no a mitad de llegar.

        AUD-424 — desde que el clima transiciona, `set_clima` sólo fija el
        objetivo: la humedad tarda seis segundos en subir. Estas pruebas miran
        el estado establecido —«bajo tormenta el jugador derrapa»—, no el
        camino, así que piden el cambio inmediato. El camino tiene sus propias
        pruebas en `test_transiciones_de_clima.py`.
        """
        escena._simulacion.set_clima(clima, inmediato=True)
        escena._aplicar_hora()
        return escena

    def test_con_cielo_despejado_el_frenado_es_el_de_siempre(self, escena) -> None:
        """Cero significa instantáneo: los dieciséis escenarios no cambian."""
        self._con_clima(escena, "clear")
        assert escena.ambiente.suelo_mojado is False
        assert escena._player.perfil.friccion == 0.0

    def test_bajo_tormenta_el_jugador_derrapa(self, escena) -> None:
        self._con_clima(escena, "storm")
        assert escena.ambiente.suelo_mojado is True
        assert escena._player.perfil.friccion > 0.0

    def test_la_tormenta_derrapa_mas_que_la_lluvia(self, escena) -> None:
        self._con_clima(escena, "rain")
        lluvia = escena._player.perfil.friccion
        self._con_clima(escena, "storm")
        assert escena._player.perfil.friccion < lluvia, (
            "más agua tiene que frenar menos, no más"
        )

    def test_la_niebla_no_moja_el_suelo(self, escena) -> None:
        """Moja el aire, no el suelo: se ve peor, pero se anda igual.

        Es la distinción que se pierde en cuanto un consumidor pregunta por el
        nombre del clima en vez de por la humedad.
        """
        self._con_clima(escena, "fog")
        assert escena.ambiente.visibilidad < 0.75
        assert escena._player.perfil.friccion == 0.0

    def test_volver_al_cielo_raso_devuelve_el_agarre(self, escena) -> None:
        """El efecto no se queda pegado cuando escampa."""
        self._con_clima(escena, "storm")
        assert escena._player.perfil.friccion > 0.0
        self._con_clima(escena, "clear")
        assert escena._player.perfil.friccion == 0.0


class TestElDerrapeSeNotaEnElMovimiento:
    """No basta con que el número cambie: tiene que moverse distinto."""

    def test_al_soltar_el_mando_bajo_tormenta_la_velocidad_no_cae_de_golpe(
            self, escena) -> None:
        jugador = escena._player
        # AUD-424 — inmediato: se mide el derrape con la tormenta ya puesta,
        # no mientras llega.
        escena._simulacion.set_clima("storm", inmediato=True)
        escena._aplicar_hora()

        # El estado fija el objetivo a 0 (nadie pulsa nada) y la integración
        # de AUD-336 acerca la velocidad real a ritmo de `friccion`.
        jugador._vx_integrada = 200.0
        jugador.velocity.x = 0.0
        jugador._aplicar_friccion_y_aceleracion(1 / 60)

        assert jugador.velocity.x > 0.0, (
            "con el suelo mojado, soltar el mando no debería parar en seco"
        )

    def test_en_seco_soltar_el_mando_para_en_seco(self, escena) -> None:
        jugador = escena._player
        escena._simulacion.set_clima("clear")
        escena._aplicar_hora()

        jugador._vx_integrada = 200.0
        jugador.velocity.x = 0.0
        jugador._aplicar_friccion_y_aceleracion(1 / 60)

        assert jugador.velocity.x == 0.0, (
            "el comportamiento en seco es el de siempre y no debe cambiar"
        )
