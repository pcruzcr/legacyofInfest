"""
F5.5–F5.8 — tiempo bala, scroll forzado, nado, parry del jefe y bullet hell.

Éstas son las mecánicas que **llegan al jugador**, y por eso se prueban por
efecto y no por existencia: que el reloj se ralentice de verdad, que el jugador
entre en `SwimmingState`, que el jefe se quede aturdido. Este proyecto lleva un
mes encontrando sistemas correctos que nadie podía alcanzar —la iluminación, las
demos, el ultimate, el nado— y la única defensa que ha funcionado es probar el
camino entero.
"""
from __future__ import annotations

import numpy as np
import pygame
import pytest

from src.framework.ecs.bullet_swarm import EnjambreDeBalas
from src.framework.ecs.components import ZonaDeAgua
from src.framework.ecs.world import World
from src.framework.stage.level_mechanics import (
    ControlDeNado,
    ScrollForzado,
    TiempoBala,
)

FRAME = 1.0 / 60.0


@pytest.fixture(scope="module", autouse=True)
def _pg():
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((320, 240))
    yield


# ══════════════════════════════════════════════════════════════
# F5.5 — tiempo bala
# ══════════════════════════════════════════════════════════════


class TestTiempoBala:
    def test_ralentiza_el_reloj_de_verdad(self):
        """Que el objeto exista no sirve: tiene que llegar al `Clock`."""
        from src.engine.core.clock import DeltaClock as Clock

        reloj, tb = Clock(), TiempoBala(escala=0.3)
        tb.update(FRAME, quiere=True, reloj=reloj)
        assert tb.activo
        assert reloj.time_scale == pytest.approx(0.3)

    def test_al_soltarlo_el_reloj_vuelve_a_la_normalidad(self):
        from src.engine.core.clock import DeltaClock as Clock

        reloj, tb = Clock(), TiempoBala()
        tb.update(FRAME, quiere=True, reloj=reloj)
        tb.update(FRAME, quiere=False, reloj=reloj)
        assert reloj.time_scale == pytest.approx(1.0)

    def test_la_reserva_se_gasta_y_se_agota(self):
        tb = TiempoBala(reserva_maxima=0.5)
        for _ in range(60):
            tb.update(FRAME, quiere=True, reloj=None)
        assert tb.reserva == 0.0
        assert not tb.activo, "sigue activo con la reserva a cero"

    def test_la_reserva_se_recupera_al_no_usarla(self):
        tb = TiempoBala(reserva_maxima=2.0, reserva=0.5, recarga=1.0)
        for _ in range(60):
            tb.update(FRAME, quiere=False, reloj=None)
        assert tb.reserva > 0.5

    def test_tras_agotarla_hay_una_espera_antes_de_recargar(self):
        """Evita el parpadeo de encender y apagar cuando queda una décima."""
        tb = TiempoBala(reserva_maxima=0.1, espera_tras_agotar=1.0, recarga=10.0)
        for _ in range(10):
            tb.update(FRAME, quiere=True, reloj=None)
        assert tb.reserva == 0.0
        tb.update(FRAME, quiere=False, reloj=None)
        assert tb.reserva == 0.0, "recargó sin esperar"

    def test_se_gasta_con_tiempo_real_y_no_con_el_escalado(self):
        """Con el `dt` escalado, a 0,1x la reserva sería casi infinita."""
        rapido, lento = TiempoBala(), TiempoBala()
        for _ in range(60):
            rapido.update(FRAME, quiere=True, reloj=None)
            lento.update(FRAME * 0.35, quiere=True, reloj=None)
        assert rapido.reserva < lento.reserva


# ══════════════════════════════════════════════════════════════
# F5.5 — scroll forzado
# ══════════════════════════════════════════════════════════════


class TestScrollForzado:
    def _camara(self):
        from src.framework.stage.camera import Camera
        c = Camera()
        c.set_map_size(4000, 600)
        return c

    def test_la_camara_avanza_sola(self):
        cam = self._camara()
        sf = ScrollForzado(velocidad=pygame.Vector2(100, 0))
        sf.arrancar(cam)
        x0 = cam.offset.x
        for _ in range(60):
            sf.update(FRAME, cam)
        assert cam.offset.x == pytest.approx(x0 + 100.0, abs=2.0)

    def test_quedarse_atras_se_detecta_con_margen(self):
        cam = self._camara()
        sf = ScrollForzado(margen_de_gracia=24.0)
        sf.arrancar(cam)
        cam.offset.x = 500.0
        assert not sf.se_quedo_atras(pygame.Rect(480, 0, 16, 16), cam), (
            "el margen de gracia no se está aplicando: morir con el sprite aún "
            "visible se lee como injusticia"
        )
        assert sf.se_quedo_atras(pygame.Rect(400, 0, 16, 16), cam)

    def test_parado_no_mata_a_nadie(self):
        cam = self._camara()
        sf = ScrollForzado()
        assert not sf.se_quedo_atras(pygame.Rect(-9999, 0, 16, 16), cam)

    def test_se_detiene_en_el_limite(self):
        cam = self._camara()
        sf = ScrollForzado(velocidad=pygame.Vector2(500, 0), parar_en_x=100.0)
        sf.arrancar(cam)
        for _ in range(60):
            sf.update(FRAME, cam)
        assert cam.offset.x == pytest.approx(100.0)
        assert not sf.activo


# ══════════════════════════════════════════════════════════════
# F5.6 — el nado, que era inalcanzable
# ══════════════════════════════════════════════════════════════


class TestNado:
    """`SwimmingState` tenía CERO transiciones de entrada en todo `src/`."""

    def _jugador(self):
        from src.framework.entities.player import Player
        return Player(pygame.Vector2(50, 50))

    def _mundo_con_agua(self, rect: pygame.Rect | None = None):
        m = World()
        m.crear(ZonaDeAgua(rect if rect is not None else pygame.Rect(0, 0, 400, 400)))
        return m

    def test_entrar_en_el_agua_activa_el_estado_de_nado(self):
        """**El hallazgo.** Antes de esto nadie podía nadar."""
        from src.framework.entities.states import SwimmingState

        jugador, mundo, nado = self._jugador(), self._mundo_con_agua(), ControlDeNado()
        nado.update(FRAME, jugador, mundo, None)
        assert isinstance(jugador._state_instance, SwimmingState), (
            "el jugador está dentro del agua y no ha entrado en SwimmingState: "
            "el estado sigue siendo inalcanzable"
        )

    def test_salir_del_agua_saca_del_estado(self):
        from src.framework.entities.states import SwimmingState

        jugador, mundo, nado = self._jugador(), self._mundo_con_agua(), ControlDeNado()
        nado.update(FRAME, jugador, mundo, None)
        assert isinstance(jugador._state_instance, SwimmingState)

        jugador.rect.topleft = (5000, 5000)
        jugador.position.update(5000, 5000)
        nado.update(FRAME, jugador, mundo, None)
        assert not isinstance(jugador._state_instance, SwimmingState)

    def test_el_aire_baja_dentro_del_agua(self):
        jugador, mundo = self._jugador(), self._mundo_con_agua()
        nado = ControlDeNado(aire_maximo=5.0, aire=5.0)
        for _ in range(60):
            nado.update(FRAME, jugador, mundo, None)
        assert nado.aire < 5.0

    def test_sin_aire_se_pierde_vida(self):
        jugador, mundo = self._jugador(), self._mundo_con_agua()
        nado = ControlDeNado(aire_maximo=0.0, aire=0.0, dano_por_segundo=5.0)
        vida0 = jugador.current_health
        for _ in range(120):
            nado.update(FRAME, jugador, mundo, None)
        assert jugador.current_health < vida0, "sin aire no pasa nada"

    def test_el_aire_se_recupera_fuera(self):
        jugador, mundo = self._jugador(), self._mundo_con_agua(pygame.Rect(0, 0, 4, 4))
        nado = ControlDeNado(aire_maximo=10.0, aire=2.0)
        jugador.rect.topleft = (900, 900)
        for _ in range(60):
            nado.update(FRAME, jugador, mundo, None)
        assert nado.aire > 2.0

    def test_avisa_antes_de_quedarse_sin_aire(self):
        """Ahogarse sin haber podido saberlo no enseña nada."""
        nado = ControlDeNado(aire_maximo=30.0, aire=5.0, umbral_aviso=10.0)
        assert nado.avisando
        nado.aire = 25.0
        assert not nado.avisando

    def test_nadar_hacia_arriba_dentro_del_agua_no_expulsa(self):
        """AUD-572 — el criterio viejo (`SwimmingState._surface_y`, ya
        retirado) expulsaba a `JumpingState` en cuanto el jugador subía
        24px desde donde había entrado a nadar, sin importar si seguía
        dentro de la `ZonaDeAgua` — reproducido jugando 4-1b: "sigue
        saltando, no se siente como un nivel de nada". Con una zona de
        agua grande de verdad (400px de alto), subir 30px sigue estando
        muy lejos del borde real."""
        from src.framework.entities.states import SwimmingState

        jugador, mundo = self._jugador(), self._mundo_con_agua(pygame.Rect(0, 0, 400, 400))
        nado = ControlDeNado()
        for _ in range(30):  # ~0,5s a 60fps
            jugador.rect.y -= 1  # sube 1px por fotograma, 30px en total
            jugador.position.y = jugador.rect.y
            nado.update(FRAME, jugador, mundo, None)
        assert isinstance(jugador._state_instance, SwimmingState), (
            "se expulsó del nado sin haber salido de la zona de agua de verdad"
        )

    def test_salir_nadando_hacia_arriba_expulsa_hacia_jumping(self):
        """La otra mitad del mismo cambio: romper la superficie DE
        VERDAD —salir de la única `ZonaDeAgua`— mientras se sube sigue
        dando el mismo impulso hacia arriba que documentaba
        `docs/45_SWIMMING_SPEC.md`, sólo que ahora lo decide la geometría
        real, no un umbral fijo desde donde se entró a nadar."""
        from src.framework.entities.states import JumpingState, SwimmingState
        from src.framework.stage.level_mechanics import VELOCIDAD_EXPULSION_SUPERFICIE

        jugador, mundo = self._jugador(), self._mundo_con_agua(pygame.Rect(0, 0, 400, 100))
        nado = ControlDeNado()
        nado.update(FRAME, jugador, mundo, None)
        assert isinstance(jugador._state_instance, SwimmingState)

        jugador.velocity.y = -50.0  # subiendo
        jugador.rect.topleft = (0, 5000)  # fuera de la zona de agua
        jugador.position.update(0, 5000)
        nado.update(FRAME, jugador, mundo, None)
        assert isinstance(jugador._state_instance, JumpingState)
        assert jugador.velocity.y == VELOCIDAD_EXPULSION_SUPERFICIE

    def test_salir_sin_subir_cae_en_vez_de_expulsar(self):
        """Salir del agua caminando o hundiéndose no es "romper la
        superficie" — sigue siendo una caída normal, el comportamiento
        de siempre."""
        from src.framework.entities.states import FallingState, SwimmingState

        jugador, mundo = self._jugador(), self._mundo_con_agua(pygame.Rect(0, 0, 400, 100))
        nado = ControlDeNado()
        nado.update(FRAME, jugador, mundo, None)
        assert isinstance(jugador._state_instance, SwimmingState)

        jugador.velocity.y = 20.0  # hundiéndose, no subiendo
        jugador.rect.topleft = (0, 5000)
        jugador.position.update(0, 5000)
        nado.update(FRAME, jugador, mundo, None)
        assert isinstance(jugador._state_instance, FallingState)


class TestElNadoEsOmnidireccionalDeVerdad:
    """AUD-528 — pedido explícito: "el botón de salto debe funcionar como
    impulso de nado... emulando la sensación de los niveles de agua
    clásicos de Super Mario Bros". El modelo anterior aplicaba gravedad
    constante y un único impulso de salto que se recargaba al tocar fondo
    (AUD-526): sin mantener la tecla, el jugador se hundía sin parar y se
    quedaba posado en el lecho, indistinguible de caminar — el reporte
    "camina sobre el agua", reproducido jugando 4-1b sin soltar ninguna
    tecla durante segundos.
    """

    def _jugador_nadando(self, y: float = 3000.0):
        from src.framework.entities.player import Player
        from src.framework.entities.states import SwimmingState

        jugador = Player(pygame.Vector2(100, y))
        jugador._change_state_instance(SwimmingState())
        # AUD-572 — el criterio de "romper la superficie" salió de
        # `SwimmingState` (vivía en `_surface_y`, un umbral fijo desde
        # donde se entró a nadar) hacia `ControlDeNado._salir`, que decide
        # por la salida real de la `ZonaDeAgua`. Esta prueba no pasa
        # ningún mundo/`ControlDeNado`, así que esa transición nunca se
        # dispara aquí — no hace falta neutralizarla a mano.
        return jugador

    def _im_con_salto_mantenido(self):
        from src.engine.input.action_map import DEFAULT_KEY_BINDINGS, Action
        from src.engine.input.input_manager import InputManager

        im = InputManager()
        tecla = DEFAULT_KEY_BINDINGS[Action.JUMP][0]
        im.pump([pygame.event.Event(pygame.KEYDOWN, key=tecla)])
        return im

    def test_mantener_salto_sigue_acelerando_no_es_un_solo_pulso(self) -> None:
        """El modelo viejo daba un único impulso de -120 px/s y ya: nada
        distinguía el primer fotograma pulsado del décimo. El nuevo debe
        seguir acelerando mientras la tecla sigue abajo."""
        jugador = self._jugador_nadando()
        im = self._im_con_salto_mantenido()
        velocidades = []
        for _ in range(10):
            jugador._state_instance.update(jugador, FRAME, im)
            im.pump([])  # mantiene el estado "held" sin volver a pulsar
            velocidades.append(jugador.velocity.y)
        # Estrictamente más negativa cada fotograma hasta el tope: si el
        # viejo modelo de un solo pulso volviera, la segunda mitad de la
        # lista sería idéntica a la primera en vez de seguir bajando.
        assert velocidades[4] < velocidades[0], (
            f"la velocidad no sigue acelerando con la tecla mantenida: {velocidades}"
        )

    def test_sin_tecla_frena_en_vez_de_seguir_acelerando(self) -> None:
        """Soltar todo debe frenar hacia flotar, no acelerar en caída
        libre — la diferencia entre "nadar" y "hundirse sin control"."""
        jugador = self._jugador_nadando()
        im = self._im_con_salto_mantenido()
        for _ in range(60):
            jugador._state_instance.update(jugador, FRAME, im)
            im.pump([])
        velocidad_subiendo = jugador.velocity.y
        assert velocidad_subiendo < 0.0, "no llegó a acelerar hacia arriba"

        from src.engine.input.input_manager import InputManager
        im_vacio = InputManager()
        for _ in range(20):
            jugador._state_instance.update(jugador, FRAME, im_vacio)
        assert jugador.velocity.y > velocidad_subiendo, (
            "sin tecla pulsada, la velocidad debería frenar hacia arriba "
            "(hacia 0), no seguir en la misma inercia"
        )
        assert jugador.velocity.y < 60.0, (
            f"sin tecla, el jugador cae a {jugador.velocity.y} px/s — eso "
            f"es caída libre, no un hundimiento suave"
        )

    def test_agachar_empuja_hacia_el_fondo(self) -> None:
        from src.engine.input.action_map import DEFAULT_KEY_BINDINGS, Action
        from src.engine.input.input_manager import InputManager

        jugador = self._jugador_nadando()
        im = InputManager()
        tecla = DEFAULT_KEY_BINDINGS[Action.CROUCH][0]
        im.pump([pygame.event.Event(pygame.KEYDOWN, key=tecla)])
        vy_inicial = jugador.velocity.y
        for _ in range(10):
            jugador._state_instance.update(jugador, FRAME, im)
            im.pump([])
        assert jugador.velocity.y > vy_inicial, (
            "mantener agachar no empuja hacia abajo"
        )

    def test_no_hay_contador_de_impulsos_que_se_agote(self) -> None:
        """El viejo `_swim_boosts` limitaba a un impulso por inmersión
        (recargado sólo al tocar fondo). Nadar arriba, soltar, y volver a
        nadar arriba debe funcionar las veces que haga falta."""
        jugador = self._jugador_nadando()
        im = self._im_con_salto_mantenido()
        for _ in range(30):
            jugador._state_instance.update(jugador, FRAME, im)
            im.pump([])
        primera_subida = jugador.velocity.y
        assert primera_subida < 0.0

        from src.engine.input.input_manager import InputManager
        im_vacio = InputManager()
        for _ in range(60):
            jugador._state_instance.update(jugador, FRAME, im_vacio)

        im2 = self._im_con_salto_mantenido()
        for _ in range(30):
            jugador._state_instance.update(jugador, FRAME, im2)
            im2.pump([])
        segunda_subida = jugador.velocity.y
        assert segunda_subida < 0.0, (
            "la segunda vez que se mantiene salto no empuja hacia arriba: "
            "sigue habiendo un límite de impulsos"
        )


# ══════════════════════════════════════════════════════════════
# F5.7 — parry del jefe
# ══════════════════════════════════════════════════════════════


class TestParryDelJefe:
    """`ParryState` existía y no tenía con qué practicar."""

    def _planificador(self, parriable: bool = True):
        from src.framework.entities.boss_kit import AttackScheduler, BossAttack
        return AttackScheduler([
            BossAttack("GOLPE", windup=1.0, active=0.2, recover=0.5,
                       cooldown=2.0, parriable=parriable, aturde_al_parry=1.5),
        ])

    def test_un_ataque_parriable_se_puede_desviar_durante_el_aviso(self):
        s = self._planificador()
        s.update(0.01, distance=10.0, phase=0)
        assert s.se_puede_desviar
        assert s.desviar() == pytest.approx(1.5)

    def test_un_ataque_no_parriable_no_se_desvia(self):
        """Sin al menos uno imparable, el combate se resuelve quieto."""
        s = self._planificador(parriable=False)
        s.update(0.01, distance=10.0, phase=0)
        assert not s.se_puede_desviar
        assert s.desviar() == 0.0

    def test_desviar_cancela_el_ataque(self):
        s = self._planificador()
        s.update(0.01, distance=10.0, phase=0)
        s.desviar()
        assert s.current is None

    def test_desviar_deja_el_ataque_en_enfriamiento_completo(self):
        """Repetirlo al instante convertiría el acierto en castigo."""
        s = self._planificador()
        s.update(0.01, distance=10.0, phase=0)
        s.desviar()
        for _ in range(30):
            s.update(FRAME, distance=10.0, phase=0)
        assert s.current is None, "el jefe repitió el ataque desviado enseguida"

    def test_no_se_puede_desviar_en_la_ventana_de_castigo(self):
        """Permitirlo enseñaría al jugador a pulsar tarde."""
        from src.framework.entities.boss_kit import AttackTiming

        s = self._planificador()
        s.update(0.01, distance=10.0, phase=0)
        for _ in range(120):
            s.update(FRAME, distance=10.0, phase=0)
            if s.timing == AttackTiming.RECOVER:
                break
        assert s.timing == AttackTiming.RECOVER
        assert not s.se_puede_desviar


class TestFasesDeJefe:
    def _jefe(self, **kw):
        from src.framework.entities.boss_base import BossBase, BossPhase

        class JefeDePrueba(BossBase):
            def _patrol_behavior(self, dt: float) -> None:
                pass

            def _alert_behavior(self, dt: float) -> None:
                pass

            def _get_animation_key(self):
                return "idle"

            def _build_hitbox(self):
                return pygame.Rect(0, 0, 16, 16)

            def _build_hurtbox(self):
                return pygame.Rect(0, 0, 16, 16)

        b = JefeDePrueba(pygame.Vector2(100, 100), max_health=20.0)
        b.set_phases([
            BossPhase(phase_index=0, health_threshold=20.0),
            BossPhase(phase_index=1, health_threshold=10.0, **kw),
        ])
        return b

    def test_una_fase_invulnerable_no_recibe_dano(self):
        jefe = self._jefe(invulnerable=True)
        jefe.current_phase = 1
        assert jefe.fase_invulnerable
        vida = jefe.current_health
        jefe.apply_hit(5.0, (200, 100))
        assert jefe.current_health == vida

    def test_una_fase_normal_si_lo_recibe(self):
        jefe = self._jefe()
        jefe.current_phase = 1
        assert not jefe.fase_invulnerable
        vida = jefe.current_health
        jefe.apply_hit(5.0, (200, 100))
        assert jefe.current_health < vida

    def test_la_escala_de_fase_se_lee(self):
        jefe = self._jefe(escala=2.5)
        jefe.current_phase = 1
        assert jefe.escala_de_fase == pytest.approx(2.5)

    def test_teletransportar_mueve_rect_y_posicion_a_la_vez(self):
        """Mover sólo uno es el error más repetido de las entregas.

        Y es el que se cometió al escribir el método: trataba el argumento como
        centro para el rect y como esquina para la posición, y `clamp_to_arena`
        —que hace `rect.x = int(position.x)`— deshacía la mitad. El jefe
        acababa doce píxeles a la derecha de donde se le mandaba.

        Se comprueban los dos a la vez, y que **coincidan entre sí**, que es la
        propiedad que de verdad importa: un jefe que se dibuja en un sitio y
        golpea desde otro parece un fallo de colisión.
        """
        jefe = self._jefe()
        jefe.set_arena_bounds(pygame.Rect(0, 0, 2000, 800))
        jefe.teletransportar(500.0, 300.0)
        assert jefe.rect.topleft == (500, 300)
        assert jefe.position.x == pytest.approx(500.0)
        assert jefe.rect.x == int(jefe.position.x), (
            "rect y position quedaron en desacuerdo tras el teletransporte"
        )


# ══════════════════════════════════════════════════════════════
# F5.8 — bullet hell
# ══════════════════════════════════════════════════════════════


class TestEnjambreDeBalas:
    def test_las_balas_se_mueven(self):
        e = EnjambreDeBalas(64)
        i = e.disparar(0, 0, 60.0, 0.0)
        for _ in range(60):
            e.update(FRAME)
        assert e.x[i] == pytest.approx(60.0, abs=1.0)

    def test_caducan_por_tiempo(self):
        e = EnjambreDeBalas(64)
        e.disparar(0, 0, 0.0, 0.0, vida=0.5)
        for _ in range(60):
            e.update(FRAME)
        assert e.contador == 0

    def test_caducan_al_salir_de_los_limites(self):
        e = EnjambreDeBalas(64)
        e.disparar(0, 0, 5000.0, 0.0, vida=99)
        for _ in range(10):
            e.update(FRAME, pygame.Rect(-50, -50, 200, 200))
        assert e.contador == 0

    def test_las_ranuras_se_reutilizan(self):
        """Sin reutilizarlas, el enjambre se llena y deja de disparar."""
        e = EnjambreDeBalas(4)
        for _ in range(4):
            e.disparar(0, 0, 0, 0, vida=0.1)
        assert e.lleno
        for _ in range(20):
            e.update(FRAME)
        assert not e.lleno
        assert e.disparar(0, 0, 0, 0) >= 0

    def test_el_abanico_reparte_direcciones(self):
        e = EnjambreDeBalas(256)
        assert e.abanico(0, 0, 24, 100.0) == 24
        vivas = np.flatnonzero(e.vivas)
        assert len({round(float(e.vx[i]), 1) for i in vivas}) > 5

    def test_el_tope_descarta_en_vez_de_crecer(self):
        """Un patrón mal calibrado no puede llenar la memoria."""
        e = EnjambreDeBalas(10)
        assert e.abanico(0, 0, 50, 100.0) == 10
        assert e.contador == 10

    def test_detecta_impactos_y_suma_el_dano(self):
        e = EnjambreDeBalas(64)
        e.disparar(50, 50, 0, 0, dano=2.0)
        e.disparar(50, 50, 0, 0, dano=3.0)
        e.disparar(900, 900, 0, 0, dano=99.0)
        assert e.dano_total_contra(pygame.Rect(40, 40, 20, 20)) == pytest.approx(5.0)

    def test_las_balas_que_impactan_se_consumen(self):
        e = EnjambreDeBalas(64)
        e.disparar(50, 50, 0, 0, dano=1.0)
        e.dano_total_contra(pygame.Rect(40, 40, 20, 20))
        assert e.contador == 0

    def test_limpiar_vacia_el_enjambre(self):
        e = EnjambreDeBalas(64)
        e.abanico(0, 0, 30, 100.0)
        e.limpiar()
        assert e.contador == 0
        assert not e.lleno

    def test_tres_mil_balas_caben_holgadamente_en_el_fotograma(self):
        """El benchmark que justifica no usar ECS aquí.

        Medido: con un objeto por bala, 2000 balas cuestan 12,94 ms —el 78 %
        del fotograma— y el enjambre 0,072 ms. Se exige un umbral flojo (2 ms)
        para que la prueba no sea frágil en máquinas lentas, pero el margen
        real es de dos órdenes de magnitud.
        """
        import time

        e = EnjambreDeBalas(4096)
        e.abanico(320, 240, 3000, 120.0, vida=99)
        objetivo = pygame.Rect(300, 220, 40, 40)
        limites = pygame.Rect(-500, -500, 2000, 2000)
        t0 = time.perf_counter()
        for _ in range(30):
            e.update(FRAME, limites)
            e.impactos_contra(objetivo)
        ms = (time.perf_counter() - t0) / 30 * 1000
        assert ms < 2.0, f"3000 balas cuestan {ms:.2f} ms de un presupuesto de 16,67"


class TestLasMecanicasDelEcsSeVen:
    """AUD-242 — `_dibujar_bloques` dice la regla: «los bloques se dibujan, y no
    es opcional». Se aplicaba a la familia de `bloques.py` y no a la del ECS.

    Medido antes de arreglarlo: `BloqueRitmico`, `ZonaLetalTemporizada`,
    `Resorte` y `PlataformaMovil` no se dibujaban en **ningún** sitio del árbol,
    y están puestos en los mapas — 7 bloques rítmicos (tres en `stage0`, el que
    copian los estudiantes) y 7 zonas letales que matan de un golpe.
    """

    def _mundo_con(self, *componentes):
        import pygame as pg

        from src.framework.ecs import Transform, World

        mundo = World()
        for comp in componentes:
            if hasattr(comp, "rect"):
                mundo.crear(comp)
            else:
                mundo.crear(
                    Transform(posicion=pg.Vector2(20, 20),
                              rect=pg.Rect(20, 20, 40, 16)),
                    comp,
                )
        return mundo

    def _pintado(self, mundo) -> bool:
        import pygame as pg

        from src.framework.scenes.stage_parts import dibujo_mecanicas

        lienzo = pg.Surface((200, 200))
        lienzo.fill((0, 0, 0))
        dibujo_mecanicas.dibujar_mecanicas_ecs(lienzo, mundo, pg.Vector2(0, 0))
        return any(
            lienzo.get_at((x, y))[:3] != (0, 0, 0)
            for x in range(0, 120) for y in range(0, 120)
        )

    def test_un_bloque_ritmico_presente_se_ve(self) -> None:
        from src.framework.ecs import BloqueRitmico

        mundo = self._mundo_con(BloqueRitmico(visible_seg=10.0, oculto_seg=0.0))
        assert self._pintado(mundo), (
            "un bloque rítmico invisible es un muro que aparece sin avisar"
        )

    def test_un_bloque_ritmico_ausente_deja_su_contorno(self) -> None:
        """Sin contorno, «desapareció el suelo» no se distingue de «nunca hubo
        suelo». El contorno es lo que dice «vuelve dentro de un momento»."""
        from src.framework.ecs import BloqueRitmico

        mundo = self._mundo_con(BloqueRitmico(visible_seg=0.0, oculto_seg=10.0))
        assert self._pintado(mundo)

    def test_un_laser_encendido_se_ve(self) -> None:
        import pygame as pg

        from src.framework.ecs import ZonaLetalTemporizada

        mundo = self._mundo_con(ZonaLetalTemporizada(
            rect=pg.Rect(20, 20, 40, 16), encendido=10.0, apagado=0.0))
        assert self._pintado(mundo), "mata de un golpe y no se veía"

    def test_un_resorte_se_ve(self) -> None:
        import pygame as pg

        from src.framework.ecs import Resorte

        assert self._pintado(self._mundo_con(Resorte(rect=pg.Rect(20, 20, 16, 16))))

    def test_una_plataforma_movil_se_ve(self) -> None:
        """Las baldosas no se mueven, así que una plataforma móvil **no puede**
        representarse pintando el mapa. O la dibuja el motor, o no se ve."""
        import pygame as pg

        from src.framework.ecs import PlataformaMovil

        mundo = self._mundo_con(PlataformaMovil(
            origen=pg.Vector2(20, 20), destino=pg.Vector2(80, 20)))
        assert self._pintado(mundo)

    def test_una_liana_se_ve(self) -> None:
        """AUD-509 — `Liana` tiene sistema de agarre y estado propio
        (`liana_alcanzable`, `TrepandoState`) desde F5.14 y no estaba en el
        barrido de AUD-242: el jugador subía por una cuerda invisible."""
        import pygame as pg

        from src.framework.ecs.components import Liana

        mundo = self._mundo_con(Liana(rect=pg.Rect(20, 20, 8, 60)))
        assert self._pintado(mundo)

    def test_una_hundible_se_ve(self) -> None:
        """AUD-509 — invisible incluso después de AUD-507/508, que le dieron
        detección de pisada y colisión atravesable de verdad: sin esto el
        jugador se hunde en un rectángulo que nunca vio."""
        from src.framework.ecs import PlataformaHundible

        mundo = self._mundo_con(PlataformaHundible(y_original=20.0))
        assert self._pintado(mundo)

    def test_una_hundible_sumergida_del_todo_no_se_ve(self) -> None:
        """Mientras `_ausente > 0` está fuera de juego: no hay nada que pintar
        hasta que vuelva a `y_original`."""
        from src.framework.ecs import PlataformaHundible

        mundo = self._mundo_con(PlataformaHundible(y_original=20.0, _ausente=1.0))
        assert not self._pintado(mundo)
