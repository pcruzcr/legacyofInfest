"""
Module: test_trails
System: tests
Academic Unit: VI

El intervalo de captura de las estelas no se usaba, y los jefes no dejaban rastro.

* **F1.4a** — `_capture_interval` valía 0,03 s y `_timer` acumulaba el tiempo,
  pero **nadie los comparaba nunca**. Se capturaba una imagen residual en cada
  fotograma: medido, veinte fotogramas de dash producían veinte residuos
  separados por un fotograma. Eso no se ve como una estela de imágenes
  residuales, se ve como un borrón sólido, y cuesta veinte superficies nuevas
  y veinte `blit` por fotograma. Es el mismo patrón que el viento de la
  tormenta: un valor calculado y guardado que nadie lee.
* **F1.4b** — el sistema de estelas sólo lo usaba el jugador, así que la
  embestida de un jefe —el movimiento más rápido y más peligroso del juego— no
  dejaba rastro. Ahí la estela no es decoración: es la información que permite
  leer de dónde viene el ataque.
* **F1.4c** — al conectarlo, el primer intento comprobaba `entity.velocity`.
  Los enemigos **no tienen ese atributo**: mueven `position` directamente, a
  diferencia del jugador. La comprobación nunca era cierta y la característica
  habría quedado como una que "no se nota".
"""
from __future__ import annotations

import pygame
import pytest

from src.framework.vfx.trail_system import TrailSystem


@pytest.fixture(scope="module")
def display():
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((800, 600))
    yield pygame.display.get_surface()


class _JugadorFalso:
    """Lo mínimo que `TrailSystem.capture` necesita de un jugador."""

    def __init__(self, x: float = 100.0, dashing: bool = True) -> None:
        self.position = pygame.Vector2(x, 200.0)
        self.rect = pygame.Rect(int(x), 200, 24, 32)
        self._dash_timer = 0.5 if dashing else 0.0


class TestElIntervaloDeCapturaSeRespeta:
    """F1.4a — se capturaba en cada fotograma."""

    def test_un_segundo_de_dash_no_produce_sesenta_residuos(self, display):
        sistema = TrailSystem()
        jugador = _JugadorFalso()
        for _ in range(60):
            jugador.position.x += 4
            sistema.capture(jugador)
            sistema.update(1 / 60)
        assert len(sistema._points) <= TrailSystem.MAX_POINTS, (
            f"{len(sistema._points)} residuos simultáneos"
        )

    def test_dos_capturas_seguidas_sin_tiempo_dan_una(self, display):
        sistema = TrailSystem()
        jugador = _JugadorFalso()
        sistema.update(1.0)          # dejar el temporizador vencido
        sistema.capture(jugador)
        sistema.capture(jugador)     # inmediatamente después, sin update
        assert len(sistema._points) == 1, (
            "la segunda captura no esperó al intervalo"
        )

    def test_tras_el_intervalo_vuelve_a_capturar(self, display):
        sistema = TrailSystem()
        jugador = _JugadorFalso()
        sistema.update(1.0)
        sistema.capture(jugador)
        sistema.update(sistema._capture_interval + 0.001)
        sistema.capture(jugador)
        assert len(sistema._points) == 2

    def test_hay_tope_de_residuos(self, display):
        sistema = TrailSystem()
        jugador = _JugadorFalso()
        for _ in range(200):
            sistema.update(1.0)      # forzar captura en cada vuelta
            sistema.capture(jugador)
        assert len(sistema._points) <= TrailSystem.MAX_POINTS


class TestLosResiduosSeDesvanecen:
    def test_el_alfa_baja_con_el_tiempo(self, display):
        sistema = TrailSystem()
        jugador = _JugadorFalso()
        sistema.update(1.0)
        sistema.capture(jugador)
        inicial = sistema._points[0].alpha
        for _ in range(10):
            sistema.update(1 / 60)
        assert sistema._points[0].alpha < inicial

    def test_acaban_desapareciendo(self, display):
        sistema = TrailSystem()
        jugador = _JugadorFalso()
        sistema.update(1.0)
        sistema.capture(jugador)
        for _ in range(120):
            sistema.update(1 / 60)
        assert sistema._points == []

    def test_los_residuos_se_dibujan_con_alfas_distintos(self, display):
        """Compartir la superficie cacheada no puede igualar todos los alfas."""
        sistema = TrailSystem()
        jugador = _JugadorFalso()
        for i in range(5):
            sistema.update(sistema._capture_interval + 0.001)
            jugador.position.x = 100.0 + i * 40
            sistema.capture(jugador)
        alfas = [p.alpha for p in sistema._points]
        assert len(set(alfas)) > 1, f"todos los residuos tienen el mismo alfa: {alfas}"

        lienzo = pygame.Surface((800, 600))
        lienzo.fill((0, 0, 0))
        sistema.draw(lienzo, pygame.Vector2(0, 0))
        pintado = pygame.surfarray.array3d(lienzo)
        valores = {int(v) for v in pintado[pintado.max(axis=2) > 0].flatten()}
        assert len(valores) > 1, (
            "todos los residuos se pintan con el mismo valor: el alfa por punto "
            "no llega al dibujo"
        )

    def test_las_siluetas_se_reutilizan(self, display):
        """Antes se creaba una Surface nueva por captura, 60 por segundo."""
        sistema = TrailSystem()
        jugador = _JugadorFalso()
        for _ in range(20):
            sistema.update(1.0)
            sistema.capture(jugador)
        assert len(sistema._cache) == 1, (
            f"{len(sistema._cache)} superficies para veinte capturas idénticas"
        )


class TestLaEstelaGenericaSirveParaCualquiera:
    """F1.4b — `capture` exige un `Player`; un jefe no lo es."""

    def test_capture_at_acepta_posicion_tamano_y_color(self, display):
        sistema = TrailSystem()
        sistema.update(1.0)
        sistema.capture_at(300.0, 150.0, (48, 48), (255, 90, 70, 110))
        assert len(sistema._points) == 1
        assert sistema._points[0].surface.get_size() == (48, 48)

    def test_tambien_respeta_el_intervalo(self, display):
        sistema = TrailSystem()
        sistema.update(1.0)
        sistema.capture_at(0.0, 0.0, (16, 16), (255, 0, 0, 100))
        sistema.capture_at(0.0, 0.0, (16, 16), (255, 0, 0, 100))
        assert len(sistema._points) == 1


class TestLaEstelaLlegaAlJuego:
    """La prueba de cableado. Las anteriores pasarían con el sistema desconectado."""

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

    def test_el_dash_del_jugador_deja_estela(self, contexto):
        from src.stages.stage0.stage0 import Stage0

        escena = Stage0(contexto)
        lienzo = pygame.Surface((800, 600))
        escena.awake()
        escena.start()
        escena.on_enter()
        for _ in range(90):
            escena.update(1 / 60)
            escena.draw(lienzo)
        assert escena._trail_system._points == [], (
            "el jugador quieto deja estela"
        )
        escena._player._dash_timer = 1.0
        for _ in range(45):
            escena.update(1 / 60)
            escena.draw(lienzo)
        assert escena._trail_system._points, "el dash no deja estela"

    def test_la_embestida_del_jefe_deja_estela(self, contexto):
        """F1.4c — comprobar `entity.velocity` no funcionaba: no existe."""
        from src.stages.boss_venado.boss_venado_scene import BossVenadoScene

        escena = BossVenadoScene(contexto)
        lienzo = pygame.Surface((800, 600))
        escena.awake()
        escena.start()
        escena.on_enter()
        for _ in range(120):
            escena.update(1 / 60)
            escena.draw(lienzo)

        jefe = next(e for e in escena._stage_data.entity_list
                    if type(e).__name__.startswith("Boss"))
        # AUD-117 — la guarda original decía `not hasattr(jefe, "velocity")`.
        # Desde la fase 5 **todas** las entidades tienen `velocity`: se la da
        # el puente ECS. Pero los enemigos siguen moviendo `position` a mano,
        # así que su `velocity` se queda en (0, 0) para siempre.
        #
        # Eso es peor que antes. Antes, escribir `enemigo.velocity` lanzaba
        # `AttributeError` y te enterabas en el acto; ahora devuelve un cero
        # silencioso y la característica que dependa de ello simplemente no se
        # nota. Por eso `_capture_enemy_trails` deriva la velocidad del
        # desplazamiento entre fotogramas, y por eso esta prueba fija el hecho
        # incómodo en vez de esconderlo.
        antes_x = jefe.position.x
        jefe.position.x += 8
        assert jefe.position.x != antes_x
        assert jefe.velocity.length_squared() == 0.0, (
            "el jefe ya mantiene `velocity` de verdad: `_capture_enemy_trails` "
            "puede dejar de deducirla del desplazamiento, y esta prueba con "
            "ella"
        )
        jefe.position.x = antes_x
        # Se mide el máximo **durante** la embestida, no al final.
        #
        # La primera versión de esta prueba movía al jefe 45 fotogramas y
        # comprobaba después. Fallaba, y no por el código: 45 x 8 px son 360 px
        # sobre una arena de 640, así que el jefe topaba con la pared, dejaba de
        # desplazarse, y los residuos —que viven 0,45 s— caducaban antes del
        # `assert`. Una prueba que sólo mira el estado final de un efecto
        # transitorio mide el silencio que viene después.
        maximo = 0
        for _ in range(12):
            jefe.position.x += 8      # 480 px/s
            escena.update(1 / 60)
            escena.draw(lienzo)
            maximo = max(maximo, len(escena._enemy_trail_system._points))
        assert maximo > 0, (
            "una embestida a 480 px/s no deja estela en ningún momento"
        )

    def test_los_enemigos_lentos_no_dejan_estela(self, contexto):
        from src.stages.stage0.stage0 import Stage0

        escena = Stage0(contexto)
        lienzo = pygame.Surface((800, 600))
        escena.awake()
        escena.start()
        escena.on_enter()
        for _ in range(180):
            escena.update(1 / 60)
            escena.draw(lienzo)
        assert escena._enemy_trail_system._points == [], (
            "los enemigos en patrulla dejan estela; el umbral es demasiado bajo "
            "y la estela deja de significar 'ataque rápido'"
        )
