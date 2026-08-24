"""
Module: test_seasons
System: tests
Academic Unit: VI

Estaciones: una capa fina que no debe pisar a las de abajo.

El riesgo de una característica que modula a otras tres —clima, partículas y
color— no es que no funcione. Es que **se imponga**: que un autor escriba
`climate = fog` en un mapa de otoño y la estación se lo cambie a lluvia. La
mayoría de estas pruebas comprueban precedencias, no efectos.

La otra mitad comprueba lo de siempre: que el resultado llegue a los píxeles.
"""
from __future__ import annotations

import numpy as np
import pygame
import pytest

from src.framework.stage.seasons import (
    ESTACIONES,
    POR_DEFECTO,
    aplicar_tinte,
    es_valida,
    estacion,
)


@pytest.fixture(scope="module")
def display():
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((800, 600))
    yield pygame.display.get_surface()


class TestLaTablaDeEstacionesEsCoherente:
    def test_las_cuatro_estaciones_existen(self):
        assert set(ESTACIONES) == {"spring", "summer", "autumn", "winter"}

    def test_cada_estacion_usa_un_clima_y_unas_particulas_reales(self):
        from src.framework.vfx.ambient_particles import AmbientParticleSystem
        from src.framework.vfx.weather_system import WeatherSystem

        for nombre, est in ESTACIONES.items():
            assert est.clima in WeatherSystem.CLIMATE_PARAMS, (
                f"{nombre} pide el clima '{est.clima}', que no existe"
            )
            tipo, ritmo = est.particulas
            assert tipo in AmbientParticleSystem.TIPOS, (
                f"{nombre} pide partículas '{tipo}', que no existen"
            )
            assert ritmo > 0

    def test_el_invierno_es_frio_y_el_otono_calido(self):
        """El tinte es lo que hace reconocible una estación de un vistazo."""
        invierno = ESTACIONES["winter"].tinte
        otono = ESTACIONES["autumn"].tinte
        assert invierno[2] > invierno[0], f"el invierno no es frío: {invierno}"
        assert otono[0] > otono[2], f"el otoño no es cálido: {otono}"

    def test_los_tintes_no_apagan_la_escena(self):
        """Un multiplicador bajo oscurecería el nivel sin decirlo."""
        for nombre, est in ESTACIONES.items():
            assert min(est.tinte) > 0.7, (
                f"{nombre} multiplica un canal por {min(est.tinte)}: eso no es "
                "teñir, es apagar la luz por la puerta de atrás"
            )
            assert max(est.tinte) <= 1.0

    def test_un_nombre_desconocido_cae_al_valor_por_defecto(self):
        assert estacion("invierno") is ESTACIONES[POR_DEFECTO]
        assert estacion("") is ESTACIONES[POR_DEFECTO]
        assert estacion(None) is ESTACIONES[POR_DEFECTO]
        assert not es_valida("invierno")
        assert es_valida("WINTER")

    def test_el_tinte_se_compone_con_el_de_la_hora(self):
        blanco = (255, 255, 255)
        invierno = aplicar_tinte(blanco, ESTACIONES["winter"])
        assert invierno[2] > invierno[0], "sobre blanco, el invierno debe enfriar"

    def test_el_tinte_cambia_el_tono_pero_no_el_brillo(self):
        """El defecto que esto vigila: el otoño oscurecía por el color.

        El tinte de otoño era (1,00, 0,90, 0,78). Al aplicarlo a Stage 0 la
        legibilidad nocturna cayó del 44 % al 23 %, por debajo del mínimo
        jugable, y el suelo de `MIN_AMBIENTE` no lo frenó porque ese suelo
        protege el escalar de brillo y la pérdida venía por el color.
        """
        from src.framework.stage.seasons import _LUMA

        gris = (180, 180, 180)
        luma_original = sum(c * k for c, k in zip(gris, _LUMA, strict=True))
        for nombre in ESTACIONES:
            teñido = aplicar_tinte(gris, ESTACIONES[nombre])
            luma = sum(c * k for c, k in zip(teñido, _LUMA, strict=True))
            assert abs(luma - luma_original) < 3.0, (
                f"{nombre} cambia el brillo de {luma_original:.0f} a {luma:.0f}: "
                "un tinte tiene que dar tono, no quitar luz"
            )
            assert teñido != gris, f"{nombre} no tiñe nada"

    def test_factor_luz_es_la_unica_perilla_de_brillo(self):
        """Dos formas de oscurecer y un solo freno es un mal diseño."""
        for nombre, est in ESTACIONES.items():
            assert 0.85 <= est.factor_luz <= 1.15, (
                f"{nombre} usa factor_luz {est.factor_luz}: demasiado lejos de 1 "
                "para ser un matiz"
            )

    def test_el_tinte_no_se_sale_del_rango(self):
        for nombre in ESTACIONES:
            for base in ((0, 0, 0), (255, 255, 255), (12, 200, 90)):
                r, g, b = aplicar_tinte(base, ESTACIONES[nombre])
                assert 0 <= r <= 255 and 0 <= g <= 255 and 0 <= b <= 255


class TestLaEstacionNoPisaLoQueElAutorDeclara:
    """El riesgo real: que la estación sobrescriba decisiones explícitas."""

    @pytest.fixture
    def escena(self, display):
        from src.engine.audio.audio_manager import AudioManager
        from src.engine.core.event_bus import EventBus
        from src.engine.core.game_context import GameContext
        from src.engine.core.save_manager import SaveManager
        from src.engine.input.input_manager import InputManager
        from src.engine.scene.scene_manager import SceneManager
        from src.framework.entities import entity_factory
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

    def _reconfigurar(self, escena, **props):
        for k, v in props.items():
            setattr(escena._stage_data, k, v)
        escena._setup_season()
        escena._setup_ambient_particles()
        escena._setup_day_night()

    def test_el_clima_del_mapa_gana_a_la_estacion(self, escena):
        """`climate = fog` en un mapa de otoño tiene que seguir siendo niebla."""
        self._reconfigurar(escena, season="autumn", climate="fog")
        assert escena._clima_efectivo() == "fog", (
            "la estación sobrescribió el clima que declaró el autor"
        )

    def test_sin_clima_declarado_manda_la_estacion(self, escena):
        self._reconfigurar(escena, season="winter", climate="")
        assert escena._clima_efectivo() == "snow"

    def test_las_particulas_del_mapa_ganan_a_la_estacion(self, escena):
        self._reconfigurar(escena, season="autumn", ambient_fx="embers",
                           ambient_fx_rate=None)
        assert escena._ambient_particles._particle_type == "embers", (
            "la estación sobrescribió las partículas que declaró el autor"
        )

    def test_sin_particulas_declaradas_manda_la_estacion(self, escena):
        self._reconfigurar(escena, season="autumn", ambient_fx="",
                           ambient_fx_rate=None)
        assert escena._ambient_particles._particle_type == "leaves"

    def test_sin_estacion_declarada_manda_la_tabla_por_zona(self, escena):
        """Un mapa que no habla de estaciones tiene que verse como antes."""
        self._reconfigurar(escena, season="", ambient_fx="", ambient_fx_rate=None)
        esperado, _ = escena.AMBIENT_FX_BY_ZONE.get(
            escena._stage_data.zone or 0, escena.AMBIENT_FX_DEFAULT)
        assert escena._ambient_particles._particle_type == esperado


class TestLaEstacionLlegaALaPantalla:
    @pytest.fixture
    def escena(self, display):
        from src.engine.audio.audio_manager import AudioManager
        from src.engine.core.event_bus import EventBus
        from src.engine.core.game_context import GameContext
        from src.engine.core.save_manager import SaveManager
        from src.engine.input.input_manager import InputManager
        from src.engine.scene.scene_manager import SceneManager
        from src.framework.entities import entity_factory
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

    def _tinte_con(self, escena, nombre: str) -> tuple[int, int, int]:
        escena._stage_data.season = nombre
        escena._setup_season()
        escena._reloj._hora = 12.0     # mediodía: el tinte de la hora no estorba
        escena._aplicar_hora()
        return escena._lighting.ambient_color

    def test_cada_estacion_produce_un_tinte_distinto(self, escena):
        tintes = {n: self._tinte_con(escena, n) for n in ESTACIONES}
        assert len(set(tintes.values())) == len(ESTACIONES), (
            f"dos estaciones dan el mismo color: {tintes}"
        )

    def test_el_invierno_enfria_y_el_otono_calienta_la_escena(self, escena):
        invierno = self._tinte_con(escena, "winter")
        otono = self._tinte_con(escena, "autumn")
        assert invierno[2] / max(invierno[0], 1) > otono[2] / max(otono[0], 1), (
            f"el invierno {invierno} no sale más frío que el otoño {otono}"
        )

    def test_la_estacion_cambia_los_pixeles(self, escena):
        lienzo = pygame.Surface((800, 600))

        def pintar(nombre):
            self._tinte_con(escena, nombre)
            for _ in range(4):
                escena.update(1 / 60)
                escena.draw(lienzo)
            return pygame.surfarray.array3d(lienzo).astype(float)

        verano = pintar("summer")
        invierno = pintar("winter")
        distintos = (np.abs(verano - invierno) > 2).mean()
        assert distintos > 0.20, (
            f"sólo el {distintos:.0%} de los píxeles cambia entre verano e "
            "invierno: la estación no llega al dibujo"
        )


class TestElCargadorLeeLaEstacion:
    def test_una_estacion_valida_se_acepta(self):
        from src.framework.stage.stage_loader import StageLoader

        assert StageLoader._parse_season({"season": "Winter"}) == "winter"

    def test_una_errata_no_revienta_y_cae_al_valor_por_defecto(self):
        from src.framework.stage.stage_loader import StageLoader

        assert StageLoader._parse_season({"season": "invierno"}) == ""
        assert StageLoader._parse_season({}) == ""
