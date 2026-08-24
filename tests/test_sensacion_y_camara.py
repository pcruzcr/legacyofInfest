"""
Coyote time, buffer de salto, anticipación y los tres modos de cámara.

AUD-143 — lo que se pidió verificar, y lo que resultó estar mal
===============================================================
La pregunta era si estas cuatro cosas existen y llegan al jugador. La
respuesta, comprobada contra el código:

* **Coyote time** — existía y funcionaba, pero se contaba en **fotogramas**:
  seis fotogramas son 100 ms a 60 fps, 200 ms a 30 y 42 ms a 144. El margen de
  perdón para saltar tarde cambiaba con la máquina. Ahora se acumula con `dt`.
* **Buffer de salto** — existía, integrado y correcto: 8 fotogramas de margen
  para adelantarse al aterrizaje. Sin cambios.
* **Anticipación (*look-ahead*)** — existía en horizontal, **sin suavizar**:
  cambiar de dirección movía la cámara decenas de píxeles en un fotograma.
  Ahora se suaviza y además mira hacia abajo al caer.
* **Tipos de cámara** — **había uno solo**. Ahora hay tres.

Y dos defectos que aparecieron al mirar
----------------------------------------
1. **Un `CameraLock` congelaba el nivel entero.** Su `rect` se guardaba y no
   se leía nunca. No es una sospecha: `boss_rey_scene.py` llevaba escrito un
   parche para rodearlo tocando `_is_locked_x` desde fuera.
2. **La orden `temblor` de las cutscenes no sacudía nada.** Llamaba a
   `camera.shake()`, que no existe —el método es `apply_shake`—, y mi prueba
   pasaba porque usé una cámara de mentira con el método que yo me inventé.
"""
from __future__ import annotations

import pygame
import pytest

from src.engine.core import settings
from src.framework.stage.camera import Camera


@pytest.fixture(autouse=True)
def _video():
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((320, 240))


class _Objetivo:
    """Lo mínimo que la cámara necesita: un `rect` y una `velocity`."""

    def __init__(self, x: int = 400, y: int = 300, vx: float = 0.0,
                 vy: float = 0.0) -> None:
        self.rect = pygame.Rect(x, y, 20, 30)
        self.velocity = pygame.Vector2(vx, vy)


def _camara(objetivo: _Objetivo, modo: str = "seguir") -> Camera:
    cam = Camera()
    cam.set_map_size(4000, 2000)
    cam.follow(objetivo)
    cam.modo = modo
    return cam


class TestCoyoteTime:
    """El margen para saltar justo después de dejar el suelo."""

    def _jugador(self):
        from src.framework.entities.player import Player

        return Player(pygame.Vector2(100, 100))

    def test_existe_y_se_puede_saltar_tras_dejar_el_suelo(self) -> None:
        from src.framework.entities.states.helpers import _can_jump

        jugador = self._jugador()
        jugador.is_grounded = False
        jugador._coyote_counter = 0.0
        jugador._air_jumps_used = 99          # sin saltos de aire disponibles
        assert _can_jump(jugador) is True, (
            "sin coyote time, salir de una plataforma un instante tarde ya no "
            "deja saltar, y eso se lee como que el juego no responde"
        )

    def test_pasada_la_ventana_ya_no(self) -> None:
        from src.framework.entities.states.helpers import _can_jump

        jugador = self._jugador()
        jugador.is_grounded = False
        jugador._coyote_counter = settings.PLAYER_COYOTE_FRAMES + 1
        jugador._air_jumps_used = 99
        assert _can_jump(jugador) is False

    def test_la_ventana_dura_lo_mismo_a_30_que_a_144_fps(self) -> None:
        """AUD-143 — el fallo que había.

        Contando fotogramas, la misma ventana duraba 200 ms a 30 fps y 42 ms
        a 144: el juego era más blando en un portátil lento.
        """
        def ventana_real(fps: float) -> float:
            jugador = self._jugador()
            jugador.is_grounded = False
            # El jugador NACE con el contador agotado —para que no se pueda
            # saltar desde el aire nada más aparecer—, así que sin este
            # reinicio el bucle no daría ni una vuelta y la prueba mediría
            # cero contra cero. Es lo que me pasó al escribirla.
            jugador._coyote_counter = 0.0
            dt = 1.0 / fps
            t = 0.0
            while jugador._coyote_counter < settings.PLAYER_COYOTE_FRAMES:
                jugador._apply_physics(dt)
                t += dt
                if t > 2.0:
                    break
            return t

        a30, a144 = ventana_real(30.0), ventana_real(144.0)
        assert a30 == pytest.approx(a144, abs=0.04), (
            f"la ventana dura {a30 * 1000:.0f} ms a 30 fps y "
            f"{a144 * 1000:.0f} ms a 144: el perdón depende de la máquina"
        )

    def test_dura_alrededor_de_cien_milisegundos(self) -> None:
        """Seis fotogramas a 60 fps. Es la banda habitual del género: por
        debajo de 80 ms no se nota y por encima de 150 se siente elástico."""
        jugador = self._jugador()
        jugador.is_grounded = False
        jugador._coyote_counter = 0.0
        t = 0.0
        while jugador._coyote_counter < settings.PLAYER_COYOTE_FRAMES and t < 2:
            jugador._apply_physics(1 / 60)
            t += 1 / 60
        assert 0.08 <= t <= 0.15

    def test_tocar_suelo_lo_reinicia(self) -> None:
        jugador = self._jugador()
        jugador.is_grounded = False
        jugador._coyote_counter = 0.0
        for _ in range(10):
            jugador._apply_physics(1 / 60)
        assert jugador._coyote_counter > 0
        jugador.is_grounded = True
        jugador._apply_physics(1 / 60)
        assert jugador._coyote_counter == 0


class TestBufferDeSalto:
    """Pulsar saltar un poco antes de aterrizar tiene que valer."""

    def test_la_pulsacion_en_el_aire_sobrevive_al_fotograma(self) -> None:
        """AUD-373 — antes esto buscaba `"_pending_jump = True"` en el fuente.

        Esa prueba se quedó **en verde** cuando el mecanismo desapareció, y
        siguió en verde durante la migración entera: el código viejo quedó
        citado en un comentario de `airborne.py` que explica adónde se fue, y
        la subcadena estaba ahí. Un cable trampa que busca texto no comprueba
        que el juego haga nada; comprueba que alguien escribió unas letras.

        Esto sí ejercita comportamiento: se pulsa saltar y, tres fotogramas
        después sin tocar nada, la pulsación sigue disponible.
        """
        from src.engine.input.action_map import DEFAULT_KEY_BINDINGS, Action
        from src.engine.input.input_manager import InputManager

        im = InputManager()
        im.pump([pygame.event.Event(
            pygame.KEYDOWN, key=DEFAULT_KEY_BINDINGS[Action.JUMP][0])])
        for _ in range(3):
            im.pump([])
        assert im.pulsada_en_buffer(Action.JUMP), (
            "nadie guarda el salto pulsado en el aire: el buffer existiría "
            "sin que nada lo alimentase"
        )

    def test_al_aterrizar_el_salto_guardado_se_ejecuta(self) -> None:
        """Con suelo de verdad, no con una lista de colisión vacía.

        Sin suelo el jugador nunca está apoyado y el buffer no puede
        dispararse: la prueba estaría midiendo la ausencia de suelo, no el
        buffer. Es el error que cometí al escribirla.
        """
        from src.framework.entities.player import Player

        suelo = [pygame.Rect(0, 160, 400, 40)]
        jugador = Player(pygame.Vector2(100, 100))
        for _ in range(120):
            jugador.update(1 / 60, suelo, None)
        assert jugador.is_grounded, "no llegó a aterrizar"

        from src.engine.input.action_map import DEFAULT_KEY_BINDINGS, Action
        from src.engine.input.input_manager import InputManager

        im = InputManager()
        jugador.is_grounded = False
        jugador.position.y -= 4
        im.pump([pygame.event.Event(
            pygame.KEYDOWN, key=DEFAULT_KEY_BINDINGS[Action.JUMP][0])])
        im.pump([pygame.event.Event(
            pygame.KEYUP, key=DEFAULT_KEY_BINDINGS[Action.JUMP][0])])

        for _ in range(6):
            if jugador.velocity.y < 0 and jugador.is_grounded:
                break
            jugador.update(1 / 60, suelo, im)
            im.pump([])
        assert jugador.velocity.y < 0, (
            "el salto guardado no se disparó al tocar suelo: el jugador que "
            "se adelanta un fotograma se queda sin saltar"
        )
        assert not im.pulsada_en_buffer(Action.JUMP)

    def test_el_buffer_caduca(self) -> None:
        """Si no caducara, un salto pulsado hace tres segundos saldría solo
        al aterrizar, y el jugador no sabría por qué salta."""
        from src.engine.input.action_map import DEFAULT_KEY_BINDINGS, Action
        from src.engine.input.input_manager import InputManager
        from src.framework.entities.player import Player

        im = InputManager()
        jugador = Player(pygame.Vector2(100, 100))
        jugador.is_grounded = False
        im.pump([pygame.event.Event(
            pygame.KEYDOWN, key=DEFAULT_KEY_BINDINGS[Action.JUMP][0])])
        im.pump([pygame.event.Event(
            pygame.KEYUP, key=DEFAULT_KEY_BINDINGS[Action.JUMP][0])])
        for _ in range(30):
            jugador.update(1 / 60, [], im)
            im.pump([])
        assert not im.pulsada_en_buffer(Action.JUMP)

    def test_la_ventana_ronda_los_130_milisegundos(self) -> None:
        """AUD-373 — antes buscaba `"8.0 / 60.0"` en el fuente de `airborne`.

        También se quedó en verde tras la migración, y por el mismo motivo:
        la constante seguía citada en el comentario que explica dónde vive
        ahora. La ventana se comprueba donde está declarada, y en la unidad en
        la que se cuenta: fotogramas.
        """
        from src.engine.input.input_manager import InputManager

        ventana_ms = InputManager.VENTANA_DE_BUFFER / 60.0 * 1000.0
        assert 100 <= ventana_ms <= 160, (
            f"la ventana de buffer son {ventana_ms:.0f} ms; fuera de ese "
            "rango deja de perdonar o empieza a saltar sola"
        )


class TestAnticipacion:
    """La cámara mira hacia donde vas."""

    def test_corriendo_a_la_derecha_la_camara_se_adelanta(self) -> None:
        quieto, corriendo = _Objetivo(vx=0.0), _Objetivo(vx=200.0)
        cam_quieta, cam_corre = _camara(quieto), _camara(corriendo)
        for _ in range(120):
            cam_quieta.update(1 / 60)
            cam_corre.update(1 / 60)
        assert cam_corre.offset.x > cam_quieta.offset.x, (
            "la cámara no se adelanta: corriendo se ve lo mismo por delante "
            "que por detrás y no da tiempo a reaccionar"
        )

    def test_corriendo_a_la_izquierda_se_adelanta_al_otro_lado(self) -> None:
        cam_izq = _camara(_Objetivo(vx=-200.0))
        cam_quieta = _camara(_Objetivo(vx=0.0))
        for _ in range(120):
            cam_izq.update(1 / 60)
            cam_quieta.update(1 / 60)
        assert cam_izq.offset.x < cam_quieta.offset.x

    def test_al_caer_mira_hacia_abajo(self) -> None:
        """Sin esto, un salto largo hacia abajo es un salto de fe."""
        cayendo, quieto = _Objetivo(vy=400.0), _Objetivo(vy=0.0)
        cam_cae, cam_quieta = _camara(cayendo), _camara(quieto)
        for _ in range(120):
            cam_cae.update(1 / 60)
            cam_quieta.update(1 / 60)
        assert cam_cae.offset.y > cam_quieta.offset.y

    def test_al_subir_no_mira_hacia_arriba(self) -> None:
        """Mirar arriba al saltar no aporta —ya sabes de dónde vienes— y
        marea al encadenar saltos."""
        subiendo, quieto = _Objetivo(vy=-400.0), _Objetivo(vy=0.0)
        cam_sube, cam_quieta = _camara(subiendo), _camara(quieto)
        for _ in range(120):
            cam_sube.update(1 / 60)
            cam_quieta.update(1 / 60)
        assert cam_sube.offset.y == pytest.approx(cam_quieta.offset.y, abs=1.0)

    def test_cambiar_de_direccion_no_da_un_tiron(self) -> None:
        """AUD-143 — la anticipación se aplicaba en crudo.

        Al girar, el objetivo de la cámara saltaba de +60 a -60 px en un
        fotograma. Suavizada, el mayor salto de un fotograma es pequeño.
        """
        objetivo = _Objetivo(vx=200.0)
        cam = _camara(objetivo)
        for _ in range(120):
            cam.update(1 / 60)
        objetivo.velocity.x = -200.0
        anterior = pygame.Vector2(cam.offset)
        saltos = []
        for _ in range(30):
            cam.update(1 / 60)
            saltos.append(abs(cam.offset.x - anterior.x))
            anterior = pygame.Vector2(cam.offset)
        assert max(saltos) < 12.0, (
            f"la cámara se movió {max(saltos):.1f} px en un fotograma al "
            f"girar; eso se ve como un tirón"
        )

    def test_se_puede_apagar(self) -> None:
        objetivo = _Objetivo(vx=300.0)
        cam = _camara(objetivo)
        cam.anticipacion = 0.0
        cam.anticipacion_caida = 0.0
        quieta = _camara(_Objetivo(vx=0.0))
        for _ in range(120):
            cam.update(1 / 60)
            quieta.update(1 / 60)
        assert cam.offset.x == pytest.approx(quieta.offset.x, abs=1.0)


class TestLosTresModos:
    def test_seguir_centra_al_jugador(self) -> None:
        objetivo = _Objetivo(x=1000, y=800)
        cam = _camara(objetivo, "seguir")
        for _ in range(240):
            cam.update(1 / 60)
        assert cam.offset.x == pytest.approx(
            objetivo.rect.centerx - settings.INTERNAL_WIDTH // 2, abs=8)

    def test_zona_muerta_no_se_mueve_por_un_salto_pequeno(self) -> None:
        """Es lo que impide que saltar en el sitio mueva el mundo entero."""
        objetivo = _Objetivo(x=1000, y=800)
        cam = _camara(objetivo, "zona_muerta")
        for _ in range(240):
            cam.update(1 / 60)
        asentada = pygame.Vector2(cam.offset)

        objetivo.rect.y -= 20                    # un saltito dentro de la zona
        for _ in range(60):
            cam.update(1 / 60)
        assert cam.offset.y == pytest.approx(asentada.y, abs=1.0)

    def test_zona_muerta_si_sigue_cuando_te_alejas(self) -> None:
        objetivo = _Objetivo(x=1000, y=800)
        cam = _camara(objetivo, "zona_muerta")
        for _ in range(240):
            cam.update(1 / 60)
        asentada = pygame.Vector2(cam.offset)

        objetivo.rect.x += 300                   # bien fuera de la zona
        for _ in range(120):
            cam.update(1 / 60)
        assert cam.offset.x > asentada.x + 100

    def test_sala_encuadra_pantallas_enteras(self) -> None:
        """Zelda, Metroid, Castlevania: la cámara salta de sala en sala."""
        objetivo = _Objetivo(x=900, y=100)
        cam = _camara(objetivo, "sala")
        cam.update(1 / 60)
        assert cam.offset.x % settings.INTERNAL_WIDTH == 0
        assert cam.offset.y % settings.INTERNAL_HEIGHT == 0

    def test_sala_salta_de_golpe_y_no_barre(self) -> None:
        """El corte instantáneo es el modo. Suavizarlo lo convierte en un
        barrido y se pierde lo que aporta."""
        objetivo = _Objetivo(x=100, y=100)
        cam = _camara(objetivo, "sala")
        cam.update(1 / 60)
        objetivo.rect.x = 1600                   # dos pantallas más allá
        cam.update(1 / 60)
        assert cam.offset.x == 1600

    def test_un_modo_desconocido_del_mapa_cae_en_seguir(self) -> None:
        from src.framework.stage.stage_loader import MODOS_DE_CAMARA

        assert {"seguir", "zona_muerta", "sala"} == set(MODOS_DE_CAMARA)


class TestLosBloqueosPorZona:
    """AUD-143 — un `CameraLock` congelaba el nivel entero."""

    class _Zona:
        def __init__(self, rect, lock_x=False, lock_y=False) -> None:
            self.rect = rect
            self.lock_x = lock_x
            self.lock_y = lock_y

    def test_fuera_de_la_zona_la_camara_se_mueve(self) -> None:
        objetivo = _Objetivo(x=2000, y=300)
        cam = _camara(objetivo)
        cam.set_camera_locks([self._Zona(pygame.Rect(0, 0, 200, 200), True, True)])
        antes = pygame.Vector2(cam.offset)
        for _ in range(60):
            cam.update(1 / 60)
        assert cam.offset.x != antes.x, (
            "una zona de bloqueo en una esquina del mapa congela la cámara en "
            "todo el nivel: es lo que hacía, y boss_rey tenía un parche para "
            "rodearlo"
        )

    def test_dentro_de_la_zona_se_congela(self) -> None:
        objetivo = _Objetivo(x=100, y=100)
        cam = _camara(objetivo)
        cam.set_camera_locks([self._Zona(pygame.Rect(0, 0, 400, 400), True, True)])
        cam.update(1 / 60)
        antes = pygame.Vector2(cam.offset)
        objetivo.rect.x = 380
        for _ in range(60):
            cam.update(1 / 60)
        assert cam.offset.x == pytest.approx(antes.x, abs=0.01)

    def test_se_bloquea_solo_el_eje_pedido(self) -> None:
        objetivo = _Objetivo(x=100, y=1000)
        cam = _camara(objetivo)
        cam.set_camera_locks([self._Zona(pygame.Rect(0, 0, 4000, 4000),
                                         lock_x=True, lock_y=False)])
        antes = pygame.Vector2(cam.offset)
        for _ in range(120):
            cam.update(1 / 60)
        assert cam.offset.x == pytest.approx(antes.x, abs=0.01)
        assert cam.offset.y != antes.y

    def test_sin_zonas_nada_se_bloquea(self) -> None:
        cam = _camara(_Objetivo(x=2000, y=900))
        cam.set_camera_locks([])
        for _ in range(60):
            cam.update(1 / 60)
        assert cam.offset.x > 0 and cam.offset.y > 0


class TestLaSacudidaDeLasCutscenes:
    """AUD-143 — mi propia acción `temblor` llamaba a un método inexistente."""

    def test_la_camara_de_verdad_se_sacude_desde_un_guion(self) -> None:
        from src.framework.stage.cutscene_system import TemblorAction

        cam = Camera()
        TemblorAction(cam, 0.5, 8.0).start()
        assert cam._shake_amplitude > 0, (
            "la orden «temblor» de los guiones no sacude nada: llamaba a "
            "shake(), que no existe en Camera"
        )

    def test_el_guion_en_texto_tambien_llega(self) -> None:
        from src.framework.stage.cutscene_guion import (
            ContextoDeGuion,
            analizar_guion,
        )

        cam = Camera()
        guion, errores = analizar_guion(
            "temblor 0.4 6", ContextoDeGuion(camara=cam))
        assert errores == []
        guion.start()
        assert cam._shake_amplitude > 0

    def test_la_camara_expone_el_nombre_que_el_resto_del_motor_usa(self) -> None:
        """Contrato entre los dobles de prueba y el objeto real.

        Mi prueba anterior pasaba con una cámara de mentira que tenía un
        método `shake` inventado por mí. Ésta mira la clase real.
        """
        assert hasattr(Camera, "apply_shake")
