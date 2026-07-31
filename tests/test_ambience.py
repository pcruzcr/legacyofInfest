"""
Module: test_ambience
System: tests
Academic Unit: V

Clima y partículas de ambiente: existían y no se veían.

* **F1.3a** — `AmbientParticleSystem.set_effect` **no la llamaba nadie**, así
  que el ritmo se quedaba en 0,0 toda la partida. Medido en Stage 0 tras tres
  segundos: 0 partículas. El sistema estaba instanciado, se actualizaba cada
  fotograma y se dibujaba; no tenía nada que dibujar.
* **F1.3b** — con ritmo 0, `1.0 / max(rate, 0.1)` daba un intervalo de 10 s: el
  sistema "apagado" soltaba una mota cada diez segundos. Peor que nada, porque
  aparece sola y no se puede relacionar con nada.
* **F1.3c** — la lluvia se evaporaba a media pantalla. Con 280 px/s y gravedad
  980, una gota recorre 344 px en 0,6 s sobre una pantalla de 600. Medido: las
  gotas vivían entre y = -6 y y = 239.
* **F1.3d** — el viento de la tormenta era una sentencia sin efecto:
  `random.choice([-1, 1]) * random.uniform(50, 100)`, calculada y asignada a
  nada. La tormenta caía tan recta como la lluvia mansa.
"""
from __future__ import annotations

import pygame
import pytest

from src.framework.vfx.ambient_particles import AmbientParticleSystem
from src.framework.vfx.weather_system import WeatherSystem

SIN_CAMARA = None   # se crea en el fixture, pygame tiene que estar iniciado


@pytest.fixture(scope="module")
def display():
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((800, 600))
    yield pygame.display.get_surface()


@pytest.fixture
def origen(display):
    return pygame.Vector2(0, 0)


class TestLasParticulasDeAmbienteExisten:
    """F1.3a — el sistema no había emitido una sola partícula."""

    @pytest.mark.parametrize("tipo", AmbientParticleSystem.TIPOS)
    def test_cada_tipo_produce_particulas(self, origen, tipo):
        sistema = AmbientParticleSystem()
        sistema.set_effect(tipo, rate=20.0)
        for _ in range(120):          # dos segundos
            sistema.update(1 / 60, origen)
        assert sistema.count > 5, (
            f"'{tipo}' produjo {sistema.count} partículas en dos segundos a 20/s"
        )

    def test_el_ritmo_cero_apaga_de_verdad(self, origen):
        """F1.3b — 'apagado' soltaba una mota cada diez segundos."""
        sistema = AmbientParticleSystem()
        sistema.set_effect("dust", rate=0.0)
        for _ in range(60 * 30):       # treinta segundos
            sistema.update(1 / 60, origen)
        assert sistema.count == 0, (
            f"con ritmo 0 aparecieron {sistema.count} partículas"
        )

    def test_mas_ritmo_da_mas_particulas(self, origen):
        conteos = {}
        for ritmo in (5.0, 30.0):
            sistema = AmbientParticleSystem()
            sistema.set_effect("spores", rate=ritmo)
            for _ in range(120):
                sistema.update(1 / 60, origen)
            conteos[ritmo] = sistema.count
        assert conteos[30.0] > conteos[5.0] * 2, conteos

    def test_un_salto_grande_de_tiempo_no_desborda(self, origen):
        """Tras una pausa o un punto de ruptura, `dt` puede valer segundos."""
        sistema = AmbientParticleSystem()
        sistema.set_effect("dust", rate=60.0)
        sistema.update(5.0, origen)     # cinco segundos de golpe
        assert sistema.count <= AmbientParticleSystem._MAX_SPAWNS_PER_FRAME, (
            f"un fotograma creó {sistema.count} partículas"
        )

    def test_las_particulas_se_dibujan(self, origen):
        sistema = AmbientParticleSystem()
        sistema.set_effect("embers", rate=60.0)
        for _ in range(90):
            sistema.update(1 / 60, origen)
        lienzo = pygame.Surface((800, 600))
        lienzo.fill((0, 0, 0))
        sistema.draw(lienzo, origen)
        pintados = (pygame.surfarray.array3d(lienzo).max(axis=2) > 0).sum()
        assert pintados > 0, "hay partículas vivas pero no se pinta ninguna"


class TestElClimaSeVeYSeComporta:
    def test_la_lluvia_cruza_la_pantalla_entera(self, origen):
        """F1.3c — se evaporaba a 239 px de 600."""
        clima = WeatherSystem("rain")
        for _ in range(180):
            clima.update(1 / 60, origen)
        y_maxima = float(clima._emitter.y.max())
        assert y_maxima > 600, (
            f"la gota más avanzada llega a y = {y_maxima:.0f} sobre una pantalla "
            "de 600 px: la lluvia se evapora en el aire"
        )

    def test_la_tormenta_cae_inclinada(self, origen):
        """F1.3d — el viento era una sentencia sin efecto."""
        inclinaciones = [abs(WeatherSystem("storm")._angulo_con_viento() - 90.0)
                         for _ in range(12)]
        assert max(inclinaciones) > 8.0, (
            f"la inclinación máxima de doce tormentas es {max(inclinaciones):.1f} "
            "grados: el viento no llega a las partículas"
        )

    def test_la_calma_cae_recta(self):
        assert WeatherSystem("clear")._angulo_con_viento() == 90.0

    @pytest.mark.parametrize("clima", ["rain", "snow", "storm"])
    def test_los_climas_con_particulas_las_producen(self, origen, clima):
        sistema = WeatherSystem(clima)
        for _ in range(120):
            sistema.update(1 / 60, origen)
        assert sistema._emitter.count > 5, (
            f"'{clima}' tiene {sistema._emitter.count} partículas"
        )

    def test_la_calma_no_produce_nada(self, origen):
        sistema = WeatherSystem("clear")
        lienzo = pygame.Surface((800, 600))
        lienzo.fill((60, 60, 70))
        antes = pygame.surfarray.array3d(lienzo).copy()
        for _ in range(120):
            sistema.update(1 / 60, origen)
        sistema.draw(lienzo, origen)
        assert sistema._emitter.count == 0
        assert (pygame.surfarray.array3d(lienzo) == antes).all(), (
            "el clima 'clear' modifica la imagen"
        )

    @pytest.mark.parametrize("clima", ["fog", "storm", "snow"])
    def test_la_capa_de_color_tiñe_la_escena(self, origen, clima):
        sistema = WeatherSystem(clima)
        lienzo = pygame.Surface((800, 600))
        lienzo.fill((60, 60, 70))
        antes = pygame.surfarray.array3d(lienzo).astype(float)
        sistema.draw(lienzo, origen)
        despues = pygame.surfarray.array3d(lienzo).astype(float)
        assert abs(despues.mean() - antes.mean()) > 2.0, (
            f"'{clima}' no cambia el tono de la escena"
        )

    def test_la_capa_de_color_no_se_repinta_cada_fotograma(self, origen):
        """Rellenar 800x600 con alfa costaba más que el blit siguiente."""
        sistema = WeatherSystem("storm")
        lienzo = pygame.Surface((800, 600))
        sistema.draw(lienzo, origen)
        assert sistema._overlay_listo is True
        sistema.draw(lienzo, origen)
        assert sistema._overlay_listo is True

    def test_cambiar_de_clima_repinta_la_capa(self, origen):
        sistema = WeatherSystem("storm")
        lienzo = pygame.Surface((800, 600))
        sistema.draw(lienzo, origen)
        sistema.set_climate("fog")
        assert sistema._overlay_listo is False, (
            "la capa conserva el color de la tormenta tras pasar a niebla"
        )


class TestElEscenarioConfiguraLaAtmosferaDesdeElTmx:
    def test_el_cargador_valida_el_tipo_de_particula(self):
        from src.framework.stage.stage_loader import StageLoader

        assert StageLoader._parse_ambient_fx({}) == ""
        assert StageLoader._parse_ambient_fx({"ambient_fx": "none"}) == ""
        assert StageLoader._parse_ambient_fx({"ambient_fx": "SPORES"}) == "spores"
        # Una errata no puede pasar en silencio dejando el nivel sin partículas.
        assert StageLoader._parse_ambient_fx({"ambient_fx": "leafs"}) == ""

    def test_las_tablas_por_zona_cubren_las_cuatro_zonas(self):
        from src.framework.scenes.stage_scene import StageScene

        for zona in (0, 1, 2, 3):
            tipo, ritmo = StageScene.AMBIENT_FX_BY_ZONE[zona]
            assert tipo in AmbientParticleSystem.TIPOS, tipo
            assert ritmo > 0

    def test_los_dos_mapas_del_juego_declaran_atmosfera(self):
        """Un escenario de referencia que no usa la característica no la enseña."""
        import xml.etree.ElementTree as ET
        from pathlib import Path

        raiz_proyecto = Path(__file__).resolve().parent.parent
        for mapa in ("stage0/stage0.tmx", "boss_venado/boss_venado.tmx"):
            raiz = ET.parse(raiz_proyecto / "assets" / "maps" / mapa).getroot()
            props = {p.get("name"): p.get("value")
                     for p in raiz.findall("./properties/property")}
            assert "ambient_light" in props, f"{mapa} no declara ambient_light"
            luces = [o for o in raiz.iter("object")
                     if (o.get("type") or o.get("class")) == "Light"]
            assert luces, f"{mapa} no coloca ningún foco"

    def test_el_clima_declarado_en_el_tmx_llega_al_sistema_de_clima(self):
        """La propiedad `climate` del mapa manda sobre la estación.

        Esta prueba **exigía antes que `boss_venado.tmx` declarase
        `climate = storm`**, porque ese mapa era del profesor y su tormenta era
        la única prueba de que la propiedad se leía. Al sustituir la arena por
        la entrega de un estudiante —que no declara clima— la prueba se puso en
        rojo sin que nada del motor hubiera cambiado.

        Era una prueba mal apuntada: medía el **contenido** de un mapa
        concreto para demostrar algo del **motor**. Cualquier profesor que
        cambie el contenido del curso la rompe, y la única salida sería editarle
        el mapa a un alumno para que una prueba pase, que es exactamente al
        revés.

        Ahora se comprueba la regla directamente, sin depender del mapa de
        nadie: si el TMX declara un clima, ése es el que se usa.
        """
        from src.framework.scenes.stage_scene import StageScene
        from src.framework.stage.seasons import estacion

        class DatosFalsos:
            climate = "storm"
            season = "autumn"

        escena = StageScene.__new__(StageScene)
        escena._stage_data = DatosFalsos()
        escena._estacion = estacion("autumn")
        assert escena._clima_efectivo() == "storm", (
            "el clima escrito en el mapa no llega al sistema de clima"
        )

        DatosFalsos.climate = ""
        assert escena._clima_efectivo() == escena._estacion.clima, (
            "sin `climate` en el mapa manda la estación, no una tormenta "
            "aparecida de la nada"
        )


class TestLaAtmosferaLlegaAlJuego:
    """La prueba que faltaba, y que es la que importa.

    Todo lo anterior comprueba `AmbientParticleSystem` y `WeatherSystem` en
    aislamiento, y las propiedades del TMX por separado. Nada de eso detecta
    que **la escena no conecte las dos cosas**, que es exactamente el defecto
    original: `set_effect` existía, funcionaba, y nadie la llamaba.

    Verificado: al sustituir la llamada de la escena por `pass`, las 25 pruebas
    anteriores seguían en verde. Éstas no.
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

    @staticmethod
    def _jugar(escena, segundos: float = 3.0):
        lienzo = pygame.Surface((800, 600))
        escena.awake()
        escena.start()
        escena.on_enter()
        for _ in range(int(segundos * 60)):
            escena.update(1 / 60)
            escena.draw(lienzo)
        return lienzo

    def test_stage0_tiene_particulas_de_ambiente_vivas(self, contexto):
        from src.stages.stage0.stage0 import Stage0

        escena = Stage0(contexto)
        self._jugar(escena)
        assert escena._ambient_particles.rate > 0, (
            "la escena no configuró el ritmo: `set_effect` no se llama"
        )
        assert escena._ambient_particles.count > 5, (
            f"tras tres segundos hay {escena._ambient_particles.count} partículas "
            "de ambiente en pantalla"
        )

    def test_un_escenario_con_tormenta_acaba_con_gotas_en_pantalla(self, contexto):
        """El camino completo: clima del escenario → `WeatherSystem` → gotas.

        Antes esta prueba se apoyaba en que `boss_venado.tmx` declarase
        `climate = storm`. Ese mapa pasó a ser la entrega de un estudiante, que
        no declara clima, y la prueba se cayó sin que el motor hubiera
        cambiado: medía contenido para demostrar comportamiento.

        Ahora el clima se fuerza sobre un escenario real —el prólogo, que es
        del curso— sobreescribiendo el único punto donde se decide. Se sigue
        recorriendo `on_enter`, `update` y `draw` de verdad, que es lo que
        detectaba el defecto original —`set_climate` existía y nadie la
        llamaba—, pero ya no depende del mapa de nadie.
        """
        from src.stages.stage0.stage0 import Stage0

        class PrologoConTormenta(Stage0):
            def _clima_efectivo(self) -> str:
                return "storm"

        escena = PrologoConTormenta(contexto)
        self._jugar(escena)
        assert escena._weather.climate == "storm", (
            "la escena no le pasó su clima al sistema: `set_climate` no se llama"
        )
        assert escena._weather._emitter.count > 5, "la tormenta no tiene gotas"
        assert escena._ambient_particles.count > 3, (
            "el escenario no tiene partículas de ambiente"
        )

    def test_stage0_queda_iluminado_con_los_focos_del_mapa(self, contexto):
        from src.stages.stage0.stage0 import Stage0

        escena = Stage0(contexto)
        self._jugar(escena, segundos=1.0)
        assert escena._lighting.ambient_brightness < 1.0, (
            "el ambiente está en 1.0: la iluminación es invisible"
        )
        # Los focos del TMX más el que acompaña al jugador.
        assert len(escena._lighting.lights) >= 5, (
            f"sólo {len(escena._lighting.lights)} focos activos"
        )

    def test_el_post_procesado_queda_configurado(self, contexto):
        from src.stages.stage0.stage0 import Stage0

        escena = Stage0(contexto)
        self._jugar(escena, segundos=1.0)
        assert escena._post_processing._bloom_base > 0, (
            "el bloom base quedó en cero: la escena no lo configura"
        )
        assert escena._post_processing._vignette_strength > 0
