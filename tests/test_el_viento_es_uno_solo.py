"""AUD-374 — el viento del ambiente dejaba de existir en el camino.

El defecto
==========
`EnvironmentState.viento` se calculaba cada fotograma y **nadie lo leía**: cero
consumidores fuera del propio productor. Mientras tanto `WeatherSystem` se
inventaba su propio viento en `_set_climate_params`, con `random.uniform` y una
segunda tabla de valores por clima. Dos vientos derivados del mismo clima, uno
huérfano y otro invisible para el resto del motor.

Que las dos tablas coincidieran delata el origen: `CLIMAS["storm"]["viento"]`
vale 75, que es justo el centro del `uniform(50, 100)` del otro; `rain` vale 15
frente a `uniform(-15, 15)`; `snow`, 12 frente a `uniform(-12, 12)`. No eran
dos decisiones: era una decisión copiada, y copiada es como se desincroniza.

Es la misma especie que AUD-343 (la tubería GL era código muerto) y AUD-355 (la
verja de datos hostiles estaba en la puerta que nadie usa), y aparece en el
mismo fichero cuyo docstring documenta F1.3 —un viento calculado y asignado a
nada—. Se arregló el síntoma y quedó la causa.

Y un segundo defecto que el primero tapaba: el campo declara signo («negativo =
hacia la izquierda») y `CLIMAS` sólo tiene magnitudes positivas, así que el
viento del ambiente **nunca soplaba hacia la izquierda**. El contrato prometía
un rango que el productor no emitía.

Qué fija esta prueba
====================
Que hay **un** viento: lo produce la simulación, con signo, desde una sola
tabla, y el sistema de clima lo consume en vez de inventarlo.
"""
from __future__ import annotations

import random

import pygame
import pytest

from src.framework.vfx.weather_system import WeatherSystem
from src.framework.world import CLIMAS, EnvironmentState, WorldSimulation


@pytest.fixture(scope="module")
def display():
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((800, 600))
    yield pygame.display.get_surface()


class TestLaSimulacionProduceElViento:
    def test_el_viento_del_estado_lleva_signo(self):
        """Con `CLIMAS` sólo positivo, el viento jamás soplaba a la izquierda.

        Se siembra el azar para que la prueba sea reproducible: doce tormentas
        con semillas distintas tienen que dar las dos direcciones.
        """
        vientos = {
            WorldSimulation(clima="storm", rng=random.Random(s)).estado().viento
            for s in range(12)
        }
        assert any(v < 0 for v in vientos), (
            f"doce tormentas y ninguna sopla a la izquierda: {sorted(vientos)}"
        )
        assert any(v > 0 for v in vientos), (
            f"doce tormentas y ninguna sopla a la derecha: {sorted(vientos)}"
        )

    def test_la_magnitud_sale_de_climas(self):
        """La magnitud es la de la tabla, no una inventada aparte."""
        for clima, params in CLIMAS.items():
            viento = WorldSimulation(
                clima=clima, rng=random.Random(1)).estado().viento
            assert abs(viento) == pytest.approx(params["viento"]), (
                f"{clima}: el estado da {viento} y `CLIMAS` dice "
                f"{params['viento']}"
            )

    def test_el_viento_no_cambia_de_signo_cada_fotograma(self):
        """Sin esto la lluvia bailaría de lado a lado 60 veces por segundo."""
        mundo = WorldSimulation(clima="storm", rng=random.Random(3))
        primero = mundo.estado().viento
        for _ in range(120):
            mundo.update(1 / 60)
        assert mundo.estado().viento == primero, (
            "el viento se vuelve a sortear en cada consulta del estado"
        )

    def test_cambiar_de_clima_vuelve_a_sortear(self):
        mundo = WorldSimulation(clima="clear", rng=random.Random(5))
        assert mundo.estado().viento == 0.0
        mundo.set_clima("storm")
        assert abs(mundo.estado().viento) == pytest.approx(
            CLIMAS["storm"]["viento"])


class TestElClimaConsumeElViento:
    def test_acepta_el_viento_del_ambiente(self, display):
        """La entrada que no existía: nadie podía decirle cuánto viento hace."""
        sistema = WeatherSystem("storm")
        sistema.aplicar_viento(-40.0)
        assert sistema._angulo_con_viento() > 90.0, (
            "un viento negativo tiene que inclinar la lluvia hacia la izquierda"
        )
        sistema.aplicar_viento(40.0)
        assert sistema._angulo_con_viento() < 90.0

    def test_sin_ambiente_cae_de_la_misma_tabla(self, display):
        """El repliegue no reintroduce la segunda tabla: lee `CLIMAS`.

        Un `WeatherSystem` construido suelto —una prueba, `stage0`, una
        entrega— sigue inclinando la lluvia. Lo que ya no hace es inventarse
        números propios.
        """
        for clima, params in CLIMAS.items():
            sistema = WeatherSystem(clima)
            assert abs(sistema._wind) == pytest.approx(params["viento"]), (
                f"{clima}: el sistema de clima dice {sistema._wind} y la tabla "
                f"{params['viento']}"
            )

    def test_el_ambiente_manda_sobre_el_repliegue(self, display):
        sistema = WeatherSystem("storm")
        sistema.aplicar_viento(3.0)
        assert sistema._wind == pytest.approx(3.0)


class TestElCaminoCompleto:
    """La que importa: que la escena conecte las dos cosas.

    Las de arriba pasarían todas con la escena sin cablear, que es exactamente
    el defecto original — `EnvironmentState.viento` existía, se calculaba, y no
    llegaba a ningún sitio.
    """

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

    def test_el_viento_del_ambiente_llega_al_clima_de_la_escena(self, contexto):
        from src.stages.stage0.stage0 import Stage0

        class PrologoConTormenta(Stage0):
            def _clima_efectivo(self) -> str:
                return "storm"

        escena = PrologoConTormenta(contexto)
        lienzo = pygame.Surface((800, 600))
        escena.awake()
        escena.start()
        escena.on_enter()
        for _ in range(30):
            escena.update(1 / 60)
            escena.draw(lienzo)

        assert escena.ambiente.viento != 0.0, (
            "el ambiente de una tormenta no tiene viento"
        )
        assert escena._weather._wind == pytest.approx(escena.ambiente.viento), (
            f"la escena no le pasa el viento del ambiente al clima: el ambiente "
            f"dice {escena.ambiente.viento} y el sistema de clima "
            f"{escena._weather._wind}"
        )

    def test_el_campo_viento_tiene_consumidor(self):
        """El cable trampa contra la reincidencia.

        Un campo del estado que nadie lee vuelve a aparecer en cuanto alguien
        añade uno. Éste vigila el que ya se cayó una vez: si `_aplicar_hora`
        deja de repartir el viento, esto se pone rojo.
        """
        import inspect

        from src.framework.scenes.stage_parts.simulacion import (
            SimulacionDeEscenario,
        )

        reparto = inspect.getsource(SimulacionDeEscenario._aplicar_hora)
        assert "_aplicar_clima" in reparto, (
            "`_aplicar_hora` reparte luz, bloom, tinte y agarre, pero ya no el "
            "clima: el estado deja de llegar al VFX"
        )
        fuente = inspect.getsource(SimulacionDeEscenario._aplicar_clima)
        assert "viento" in fuente, (
            "`_aplicar_clima` ya no pasa el viento: el campo se ha vuelto a "
            "quedar huérfano"
        )


class TestElMundoMandaSobreElClima:
    """La costura que el viento destapó — AUD-374, GAP-050.

    Había **dos autoridades** sobre el mismo hecho. `WorldSimulation` calculaba
    `clima`, `humedad`, `viento` y `visibilidad`; y el sistema que de verdad
    dibuja la lluvia se alimentaba por otro lado, de la cadena `climate` del
    TMX vía `set_climate`. Mientras las dos coincidieran —los dieciséis mapas
    declaran su clima y la simulación arranca del mismo dato— no se notaba.

    Se notaba en cuanto el clima cambiaba **en marcha**, que es justo lo que la
    simulación sabe hacer y el TMX no. Medido con la secuencia real de
    `stage4_1` —mapa `fog`, acto `storm` pedido al VFX—::

        humedad 0,50 → suelo_mojado False

    Los actos de tormenta de ese escenario nunca resbalaron, con AUD-362
    entero construido y la escena consumiéndolo. El dato llegaba caducado.

    Lo que fija esta clase: **se le pide al mundo**, y el VFX se entera.
    """

    @staticmethod
    def _escena(mapa: str):
        """La escena mínima que reproduce la secuencia, sin cargar el TMX."""
        from src.framework.scenes.stage_parts.simulacion import (
            SimulacionDeEscenario,
        )
        from src.framework.vfx.weather_system import WeatherSystem

        class EscenaMinima(SimulacionDeEscenario):
            def __init__(self) -> None:
                self._simulacion = WorldSimulation(
                    clima=mapa, rng=random.Random(11))
                self._weather = WeatherSystem(mapa)
                self._lighting = _LuzFalsa()
                self._post_processing = _PostFalso()
                self._ambiente_base = 1.0
                self._bloom_base_escenario = 0.0

        return EscenaMinima()

    def test_pedirselo_al_mundo_cambia_la_simulacion(self, display):
        escena = self._escena("fog")
        escena._cambiar_clima("storm")
        assert escena._simulacion.clima == "storm"

    def test_el_vfx_se_entera_solo(self, display):
        """Nadie le habla al sistema de clima: lo lee del estado."""
        escena = self._escena("fog")
        escena._cambiar_clima("storm")
        assert escena._weather.climate == "storm", (
            "el sistema de clima sigue pintando niebla mientras el mundo está "
            "en tormenta"
        )

    def test_la_tormenta_del_acto_moja_el_suelo(self, display):
        """La consecuencia jugable, que es la que importa."""
        escena = self._escena("fog")
        escena._cambiar_clima("storm")
        assert escena.ambiente.suelo_mojado, (
            f"humedad {escena.ambiente.humedad}: los actos de tormenta nunca "
            "resbalaron"
        )

    def test_la_tormenta_del_acto_sopla(self, display):
        escena = self._escena("fog")
        escena._cambiar_clima("storm")
        assert escena._weather._wind != 0.0, (
            "la lluvia del acto cae completamente vertical"
        )

    def test_escampar_devuelve_el_suelo_seco(self, display):
        escena = self._escena("fog")
        escena._cambiar_clima("storm")
        escena._cambiar_clima("clear")
        assert not escena.ambiente.suelo_mojado
        assert escena._weather._wind == 0.0


class _LuzFalsa:
    ambient_brightness = 1.0
    ambient_color = (255, 255, 255)


class _PostFalso:
    _bloom_base = 0.0

    def set_base_bloom(self, valor: float) -> None:
        self._bloom_base = valor


def test_el_estado_neutro_no_tiene_viento():
    """Un menú, o una escena antes de `on_enter`, no sopla."""
    assert EnvironmentState.neutro().viento == 0.0
