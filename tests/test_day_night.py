"""
Module: test_day_night
System: tests
Academic Unit: VI

El ciclo día/noche, y el límite que lo hace jugable.

Un ciclo de iluminación es fácil de escribir y fácil de escribir mal. Los dos
modos de fallo son opuestos y los dos se han medido aquí:

* **El ciclo no llega a la pantalla.** Es el patrón que ha aparecido cinco
  veces en este proyecto: el sistema existe, se actualiza, y nadie aplica su
  resultado. Se prueba cargando Stage 0 de verdad y comprobando que los píxeles
  cambian con la hora.
* **El ciclo hace el juego injugable.** Medido: con el factor nocturno
  original de 0,35 sobre el `ambient_light` 0,70 de Stage 0, el brillo medio de
  pantalla a medianoche caía a 12,7 sobre 255 y sólo el 31 % de los píxeles
  superaba el umbral de legibilidad. Una noche realista en la que no se ven los
  enemigos es un defecto, no una decisión artística.
"""
from __future__ import annotations

import numpy as np
import pygame
import pytest

from src.framework.stage.day_night import (
    HORAS_POR_DIA,
    PARADAS,
    RelojDeMundo,
    luz_a_las,
)


@pytest.fixture(scope="module")
def display():
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((800, 600))
    yield pygame.display.get_surface()


class TestLaCurvaDeLuzEsCoherente:
    def test_el_mediodia_es_mas_claro_que_la_medianoche(self):
        assert luz_a_las(12).factor_ambiente > luz_a_las(0).factor_ambiente

    def test_el_mediodia_no_tiñe(self):
        r, g, b = luz_a_las(12).color
        assert min(r, g, b) > 240, f"el mediodía tiñe la escena: {(r, g, b)}"

    def test_la_noche_es_azul_y_el_atardecer_calido(self):
        noche = luz_a_las(23).color
        assert noche[2] > noche[0], f"la noche no es fría: {noche}"
        tarde = luz_a_las(18).color
        assert tarde[0] > tarde[2], f"la tarde no es cálida: {tarde}"

    def test_la_interpolacion_es_continua(self):
        """Un salto brusco de color se ve como un parpadeo."""
        anterior = luz_a_las(0.0)
        for paso in range(1, 24 * 20):
            actual = luz_a_las(paso / 20.0)
            salto = max(abs(a - b) for a, b in zip(anterior.color, actual.color, strict=True))
            assert salto <= 12, (
                f"salto de color de {salto} a las {paso / 20.0:.2f} h"
            )
            anterior = actual

    def test_el_ciclo_cierra_sobre_si_mismo(self):
        """Las 24:00 y las 00:00 son el mismo instante."""
        assert luz_a_las(0.0).color == luz_a_las(24.0).color
        assert luz_a_las(23.999).color[2] > 150

    def test_horas_fuera_de_rango_se_normalizan(self):
        assert luz_a_las(25.0).color == luz_a_las(1.0).color
        assert luz_a_las(-1.0).color == luz_a_las(23.0).color

    def test_de_noche_se_realza_mas(self):
        """Con menos luz de fondo, el bloom compite con menos y se nota más."""
        assert luz_a_las(23).bloom_extra > luz_a_las(12).bloom_extra

    def test_las_paradas_cubren_el_dia_completo(self):
        horas = [h for h, _ in PARADAS]
        assert horas[0] == 0.0
        assert horas[-1] == HORAS_POR_DIA
        assert horas == sorted(horas), "las paradas no están en orden"


class TestElRelojAvanzaYSeCongela:
    def test_sin_duracion_el_reloj_no_se_mueve(self):
        reloj = RelojDeMundo(hora_inicial=8.0, duracion_dia=0.0)
        assert reloj.congelado
        for _ in range(600):
            reloj.update(1 / 60)
        assert reloj.hora == 8.0

    def test_un_dia_completo_dura_lo_declarado(self):
        reloj = RelojDeMundo(hora_inicial=0.0, duracion_dia=10.0)
        for _ in range(600):          # diez segundos a 60 fps
            reloj.update(1 / 60)
        # Tras un ciclo completo se vuelve a la hora de partida. La distancia
        # se mide sobre el círculo: la acumulación de 600 sumas en coma
        # flotante deja el reloj en 23:59:59, que está a un segundo de las
        # 00:00 y a 24 horas si se restan los números sin más.
        distancia = min(reloj.hora, HORAS_POR_DIA - reloj.hora)
        assert distancia < 0.1, f"tras un ciclo completo el reloj marca {reloj.hora}"

    def test_la_mitad_del_dia_deja_el_reloj_a_media_vuelta(self):
        reloj = RelojDeMundo(hora_inicial=0.0, duracion_dia=10.0)
        for _ in range(300):
            reloj.update(1 / 60)
        assert reloj.hora == pytest.approx(12.0, abs=0.2)

    def test_la_etiqueta_es_legible(self):
        assert RelojDeMundo(6.5).etiqueta() == "06:30"
        assert RelojDeMundo(0.0).etiqueta() == "00:00"
        assert RelojDeMundo(23.99).etiqueta() == "23:59"

    @pytest.mark.parametrize(
        ("entrada", "esperado"),
        [
            ("dawn", 7.0), ("DUSK", 19.0), ("midnight", 0.0),
            ("18:30", 18.5), ("6:15", 6.25),
            ("3.5", 3.5), ("25", 1.0),
            ("no_es_una_hora", 12.0), ("", 12.0), (None, 12.0),
        ],
    )
    def test_la_hora_admite_nombre_numero_y_reloj(self, entrada, esperado):
        assert RelojDeMundo.hora_desde_texto(entrada) == pytest.approx(esperado)


class TestElCicloLlegaALaPantalla:
    """La prueba de cableado. Todo lo anterior pasaría con el ciclo desconectado."""

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

    @staticmethod
    def _pintar(escena, hora: float) -> np.ndarray:
        escena._reloj._hora = hora
        escena._aplicar_hora()
        lienzo = pygame.Surface((800, 600))
        for _ in range(4):            # el halo del bloom se refresca cada dos
            escena.update(1 / 60)
            escena.draw(lienzo)
        return pygame.surfarray.array3d(lienzo).astype(float)

    def test_la_noche_se_ve_distinta_del_mediodia(self, escena):
        escena._reloj._duracion_dia = 0.0     # congelar para controlar la hora
        dia = self._pintar(escena, 12.0)
        noche = self._pintar(escena, 23.0)
        assert noche.mean() < dia.mean() * 0.75, (
            f"medianoche {noche.mean():.1f} frente a mediodía {dia.mean():.1f}: "
            "el ciclo no llega a los píxeles"
        )

    def test_la_noche_es_mas_azul_que_el_mediodia(self, escena):
        escena._reloj._duracion_dia = 0.0
        dia = self._pintar(escena, 12.0)
        noche = self._pintar(escena, 23.0)
        # Proporción de azul sobre rojo: sube de noche aunque baje el brillo.
        assert (noche[..., 2].mean() / max(noche[..., 0].mean(), 1)) > \
               (dia[..., 2].mean() / max(dia[..., 0].mean(), 1)), (
            "la noche no se lee como fría"
        )

    def test_de_noche_el_nivel_sigue_siendo_jugable(self, escena):
        """El límite que impide que el realismo arruine la partida.

        Medido antes del suelo: 12,7 de brillo medio y 31 % de píxeles
        legibles a medianoche. El jugador no veía a los enemigos.
        """
        escena._reloj._duracion_dia = 0.0
        for hora in (0.0, 3.0, 20.0, 23.0):
            pantalla = self._pintar(escena, hora)
            assert escena._lighting.ambient_brightness >= escena.MIN_AMBIENTE, (
                f"a las {hora:.0f}:00 el ambiente cae a "
                f"{escena._lighting.ambient_brightness:.2f}"
            )
            legible = (pantalla > 25).mean()
            assert legible > 0.30, (
                f"a las {hora:.0f}:00 sólo el {legible:.0%} de la pantalla es "
                "distinguible: el nivel no se puede jugar"
            )

    def test_un_mapa_sin_ciclo_se_comporta_como_antes(self, display):
        """La arena del jefe fija la hora al atardecer y no declara `day_length`.

        Es el caso que importa preservar: un combate no puede cambiar de luz a
        mitad de la pelea, y un escenario que no pide ciclo tiene que verse
        exactamente con el `ambient_light` que escribió su autor.
        """
        from src.engine.audio.audio_manager import AudioManager
        from src.engine.core.event_bus import EventBus
        from src.engine.core.game_context import GameContext
        from src.engine.core.save_manager import SaveManager
        from src.engine.input.input_manager import InputManager
        from src.engine.scene.scene_manager import SceneManager
        from src.framework.entities import entity_factory
        from src.stages.boss_venado.boss_venado_scene import BossVenadoScene

        entity_factory.ensure_registered()
        ctx = GameContext(
            input_manager=InputManager(), audio_manager=AudioManager(),
            scene_manager=None, event_bus=EventBus(), clock=None,
            save_manager=SaveManager(),
        )
        ctx.scene_manager = SceneManager(ctx)
        arena = BossVenadoScene(ctx)
        arena.awake()
        arena.start()
        arena.on_enter()

        assert arena._reloj.congelado, "el mapa no pidió ciclo y el reloj corre"
        antes = arena._lighting.ambient_brightness
        # La hora de partida es del autor del mapa, no de esta prueba. Antes se
        # exigía «19:00», que era la que había escrito yo en la arena de
        # referencia; al sustituirla por la entrega del estudiante —que no
        # declara `start_hour` y se queda en el mediodía por defecto— la prueba
        # se puso roja sin que el reloj hubiera cambiado de conducta. Lo que
        # hay que preservar es que **no se mueva**, no cuál sea.
        hora_inicial = arena._reloj.etiqueta()
        lienzo = pygame.Surface((800, 600))
        for _ in range(300):
            arena.update(1 / 60)
            arena.draw(lienzo)
        assert arena._lighting.ambient_brightness == pytest.approx(antes)
        assert arena._reloj.etiqueta() == hora_inicial, (
            "la hora fija de la arena se movió"
        )

    def test_stage0_si_pide_ciclo(self, escena):
        """El escenario de referencia tiene que enseñar la característica."""
        assert not escena._reloj.congelado, (
            "stage0 no declara `day_length`: nadie verá el ciclo día/noche"
        )
        assert escena._reloj.duracion_dia > 60, (
            f"un ciclo de {escena._reloj.duracion_dia:.0f} s pasa demasiado rápido "
            "para leerse como el paso del tiempo"
        )

    def test_con_ciclo_la_luz_cambia_sola(self, escena):
        escena._reloj._duracion_dia = 4.0     # un día cada cuatro segundos
        lienzo = pygame.Surface((800, 600))
        brillos = []
        for i in range(240):
            escena.update(1 / 60)
            escena.draw(lienzo)
            if i % 40 == 0:
                brillos.append(escena._lighting.ambient_brightness)
        assert max(brillos) - min(brillos) > 0.1, (
            f"la luz apenas se mueve en un ciclo completo: {brillos}"
        )


class TestElCargadorLeeElCiclo:
    def test_las_propiedades_por_defecto_congelan_el_reloj(self):
        from src.framework.stage.stage_loader import StageLoader

        hora, duracion = StageLoader._parse_day_night({})
        assert hora is None
        assert duracion == 0.0

    def test_se_admiten_nombre_numero_y_reloj(self):
        from src.framework.stage.stage_loader import StageLoader

        assert StageLoader._parse_day_night({"start_hour": "dusk"})[0] == 19.0
        assert StageLoader._parse_day_night({"start_hour": "6:30"})[0] == 6.5
        assert StageLoader._parse_day_night({"start_hour": 21})[0] == 21.0

    def test_la_duracion_se_recorta_a_un_rango_razonable(self):
        from src.framework.stage.stage_loader import StageLoader

        assert StageLoader._parse_day_night({"day_length": 300})[1] == 300.0
        assert StageLoader._parse_day_night({"day_length": -5})[1] == 0.0
        assert StageLoader._parse_day_night({"day_length": 999999})[1] == 36000.0
