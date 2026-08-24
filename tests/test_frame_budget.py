"""
Module: test_frame_budget
System: tests
Academic Unit: VII

Ninguna escena debe perder un fotograma, y menos la primera que se ve.

Estas pruebas existen porque la suite anterior medía si una escena *se caía*,
nunca si iba *rápida*. Con eso pasaron desapercibidos dos defectos que un
jugador nota de inmediato:

* **AUD-082** — `TitleScene` tenía una mediana de 0,70 ms por fotograma y **un
  fotograma de 376 ms**: numba compila su núcleo de partículas en la primera
  llamada, y esa llamada caía en la pantalla de título. Veintidós fotogramas
  perdidos de golpe en la primera pantalla del juego.
* **AUD-073/074** — el laboratorio de ruido regeneraba 57.600 píxeles en cada
  `update()`: 295 ms por fotograma, tres fotogramas por segundo, siempre.

Sobre los umbrales: son deliberadamente flojos. Estas pruebas corren en la
integración continua, en máquinas compartidas y de velocidad desconocida, y una
prueba de rendimiento que falla por ruido se acaba desactivando. El objetivo no
es medir milisegundos con precisión, es cazar diferencias de dos órdenes de
magnitud, que son las que se ven jugando.
"""
from __future__ import annotations

import itertools
import time

import pygame
import pytest

# Presupuesto real a 60 FPS. Se admite hasta cuatro veces por la varianza de la
# integración continua: un fallo aquí significa "esto va cien veces más lento de
# lo que debería", no "esto va un 10 % lento".
PRESUPUESTO_MS = 1000.0 / 60.0
TOLERANCIA = 4.0
FOTOGRAMAS = 90


@pytest.fixture(scope="module")
def display():
    pygame.init()
    pygame.font.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((800, 600))
    yield pygame.display.get_surface()


@pytest.fixture
def hacer_contexto(display):
    from src.engine.audio.audio_manager import AudioManager
    from src.engine.core.event_bus import EventBus
    from src.engine.core.game_context import GameContext
    from src.engine.core.save_manager import SaveManager
    from src.engine.input.input_manager import InputManager
    from src.engine.scene.scene_manager import SceneManager

    def fabrica():
        ctx = GameContext(
            input_manager=InputManager(),
            audio_manager=AudioManager(),
            scene_manager=None,
            event_bus=EventBus(),
            clock=None,
            save_manager=SaveManager(),
        )
        ctx.scene_manager = SceneManager(ctx)
        return ctx

    return fabrica


def _medir(escena, fotogramas: int = FOTOGRAMAS) -> list[float]:
    """Devuelve el coste en ms de cada fotograma, update + draw."""
    superficie = pygame.Surface((800, 600))
    escena.awake()
    escena.start()
    escena.on_enter()
    tiempos = []
    try:
        for _ in range(fotogramas):
            t0 = time.perf_counter()
            escena.update(1 / 60)
            escena.draw(superficie)
            tiempos.append((time.perf_counter() - t0) * 1000)
    finally:
        escena.on_exit()
    return tiempos


class TestNingunaEscenaSeAtasca:
    """El peor fotograma importa más que la media: es el que se ve."""

    def test_la_pantalla_de_titulo_no_da_un_tiron(self, hacer_contexto):
        """AUD-082 — aquí estaba el fotograma de 376 ms.

        La escena de inicio precompila el núcleo de partículas, así que para
        cuando se llega al título ya no queda nada que compilar. Se simula ese
        paso porque en el juego real siempre ocurre: `App` empuja `SplashScene`
        antes que nada.
        """
        from src.engine.scenes.splash_scene import SplashScene
        from src.engine.scenes.title_scene import TitleScene

        _medir(SplashScene(hacer_contexto()), fotogramas=4)   # el arranque real
        tiempos = _medir(TitleScene(hacer_contexto()))

        peor = max(tiempos)
        assert peor < PRESUPUESTO_MS * TOLERANCIA, (
            f"el peor fotograma del título costó {peor:.0f} ms; el jugador ve un "
            f"tirón de {peor / PRESUPUESTO_MS:.0f} fotogramas"
        )

    def test_el_laboratorio_de_ruido_va_a_velocidad_de_juego(self, hacer_contexto):
        """AUD-073/074 — regeneraba el mapa entero en cada `update()`."""
        from src.engine.scenes.noise_lab_scene import NoiseLabScene

        tiempos = _medir(NoiseLabScene(hacer_contexto()))
        mediana = sorted(tiempos)[len(tiempos) // 2]
        assert mediana < PRESUPUESTO_MS * TOLERANCIA, (
            f"mediana de {mediana:.0f} ms por fotograma: la escena corre a "
            f"{1000 / mediana:.0f} FPS"
        )

    @pytest.mark.parametrize(
        ("modulo", "clase"),
        [
            ("src.engine.scenes.demo_menu_scene", "DemoMenuScene"),
            ("src.engine.scenes.vector_lab_scene", "VectorLabScene"),
            ("src.engine.scenes.collision_lab_scene", "CollisionLabScene"),
            ("src.engine.scenes.transform_lab_scene", "TransformLabScene"),
            ("src.engine.scenes.interpolation_lab_scene", "InterpolationLabScene"),
            ("src.engine.scenes.curve_editor_scene", "CurveEditorScene"),
        ],
    )
    def test_los_laboratorios_caben_en_su_presupuesto(self, hacer_contexto, modulo, clase):
        import importlib

        escena_cls = getattr(importlib.import_module(modulo), clase)
        tiempos = _medir(escena_cls(hacer_contexto()), fotogramas=45)
        mediana = sorted(tiempos)[len(tiempos) // 2]
        assert mediana < PRESUPUESTO_MS * TOLERANCIA, (
            f"{clase}: mediana de {mediana:.0f} ms por fotograma"
        )


class TestElPrecalentamientoDeParticulasHaceLoQuePromete:
    """Una función de precalentamiento que no calienta nada es peor que ninguna."""

    def test_precalentar_deja_el_nucleo_listo(self):
        """Tras el precalentamiento, actualizar partículas debe ser barato."""
        import numpy as np

        from src.framework.vfx.particle_system import ParticleEmitter, warmup

        warmup()

        emisor = ParticleEmitter()
        emisor.x = np.ones(200, dtype=np.float32)
        emisor.y = np.ones(200, dtype=np.float32)
        emisor.vx = np.ones(200, dtype=np.float32)
        emisor.vy = np.ones(200, dtype=np.float32)
        emisor.life = np.ones(200, dtype=np.float32)
        emisor.max_life = np.ones(200, dtype=np.float32)
        emisor.alpha = np.full(200, 255, dtype=np.int32)
        emisor.size = np.ones(200, dtype=np.int32)
        emisor.gravity = np.zeros(200, dtype=np.float32)
        emisor.friction = np.ones(200, dtype=np.float32)
        emisor._colors = [(255, 255, 255)] * 200

        t0 = time.perf_counter()
        emisor.update(1 / 60)
        ms = (time.perf_counter() - t0) * 1000
        assert ms < PRESUPUESTO_MS, (
            f"la primera actualización real costó {ms:.0f} ms: el precalentamiento "
            "compiló una firma distinta de la que usa el emisor"
        )

    def test_es_idempotente(self):
        from src.framework.vfx.particle_system import warmup

        warmup()
        assert warmup() == 0.0, "la segunda llamada debe ser gratis"

    @staticmethod
    def _fotogramas_necesarios(escena_cls) -> int:
        """Cuántos fotogramas tarda el precalentado entero, con holgura.

        AUD-449 — cada paso consume **dos** fotogramas, no uno: se anuncia en
        el primero y se ejecuta en el segundo. Ese anuncio previo es el arreglo
        entero, porque el paso corre dentro de `update()` y el dibujo va
        después: ejecutándolo en el mismo fotograma en que se anuncia, el texto
        se pintaría cuando el bloqueo ya terminó.

        Se calcula en vez de escribirse para que añadir un tercer paso de
        precalentado no ponga esta prueba en rojo por una razón que no tiene
        nada que ver con lo que mide.
        """
        return escena_cls._WARMUP_AFTER_FRAMES + len(escena_cls._WARMUP_STEPS) * 2

    def test_la_escena_de_inicio_precalienta_sola(self, hacer_contexto):
        """Si nadie la llama, la función de precalentamiento no sirve de nada."""
        from src.engine.scenes.splash_scene import SplashScene

        escena = SplashScene(hacer_contexto())
        assert escena._warmed_up is False
        superficie = pygame.Surface((800, 600))
        escena.on_enter()
        for _ in range(self._fotogramas_necesarios(SplashScene)):
            escena.update(1 / 60)
            escena.draw(superficie)
        assert escena._warmed_up is True, (
            "la escena de inicio nunca precalienta: el tirón vuelve al título"
        )

    def test_precalentar_no_se_come_la_pantalla_de_inicio(self, hacer_contexto):
        """El anuncio previo no puede alargar el arranque de forma visible.

        Cuesta un fotograma por paso. La pantalla de inicio dura tres segundos
        —180 fotogramas—, así que el presupuesto tiene que quedarse muy por
        debajo: si algún día se acerca, el precalentado habrá dejado de caber
        donde se puso justamente para que no se notara.
        """
        from src.engine.scenes.splash_scene import SplashScene

        necesarios = self._fotogramas_necesarios(SplashScene)
        presupuesto = int(SplashScene.SPLASH_TIME * 60)
        assert necesarios < presupuesto // 4, (
            f"el precalentado necesita {necesarios} de los {presupuesto} "
            f"fotogramas que dura la pantalla de inicio"
        )

    def test_precalienta_un_paso_por_fotograma(self, hacer_contexto):
        """AUD-088 — hacerlo todo de golpe congelaba el logo 3,4 s.

        Ejecutar los dos precalentamientos en el mismo `update` sumaba más que
        la propia pantalla de inicio. Repartidos, entre uno y otro se dibuja un
        fotograma y el fundido sigue avanzando.
        """
        from src.engine.scenes.splash_scene import SplashScene

        escena = SplashScene(hacer_contexto())
        escena.on_enter()
        superficie = pygame.Surface((800, 600))
        indices = []
        for _ in range(self._fotogramas_necesarios(SplashScene)):
            escena.update(1 / 60)
            escena.draw(superficie)
            indices.append(escena._warmup_index)
        # El índice avanza de uno en uno, nunca de golpe.
        saltos = [b - a for a, b in itertools.pairwise(indices)]
        assert all(s <= 1 for s in saltos), f"avances por fotograma: {saltos}"
        assert escena._warmed_up is True

    def test_la_ia_queda_cargada_tras_la_pantalla_de_inicio(self, hacer_contexto):
        """AUD-088 — sklearn se importaba en el fotograma 16 de la partida.

        `squad_brain` importa `ai_predictor` la primera vez que un enemigo
        consulta al predictor, y ese import arrastra scikit-learn entero:
        2,3 s de congelación con el jugador ya moviéndose.
        """
        import sys

        from src.engine.scenes.splash_scene import SplashScene

        escena = SplashScene(hacer_contexto())
        escena.on_enter()
        superficie = pygame.Surface((800, 600))
        for _ in range(len(SplashScene._WARMUP_STEPS) + 2):
            escena.update(1 / 60)
            escena.draw(superficie)

        if "sklearn" not in sys.modules:
            pytest.skip("scikit-learn no está instalado; la IA usa su heurística")
        assert "src.framework.entities.ai_predictor" in sys.modules, (
            "la pantalla de inicio no cargó el predictor: el tirón vuelve a "
            "caer dentro de la partida"
        )

    def test_no_precalienta_en_el_primer_fotograma(self, hacer_contexto):
        """Compilar antes de dibujar dejaría la ventana en negro medio segundo."""
        from src.engine.scenes.splash_scene import SplashScene

        escena = SplashScene(hacer_contexto())
        escena.on_enter()
        escena.update(1 / 60)
        assert escena._warmed_up is False
