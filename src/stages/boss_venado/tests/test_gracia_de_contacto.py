"""Fase RED — Cambio 4 (fairness): gracia de contacto durante la transición de fase.

Contexto y causa raíz (evidencia: corrida v4_recert_competent, teleport f5717
-> golpe de contacto -0.75 exacto f5739). Al cruzar el umbral de fase,
``BossVenado._start_phase_transition`` (boss_venado.py ~L958-988) llama a
``super()._start_phase_transition()`` (boss_base.py ~L367-380: pone
``is_transitioning=True``, ``_invincibility_timer=inf``,
``transition_timer=2.5``) y LUEGO teletransporta al venado al centro de la
arena con ``teletransportar()``. El jefe queda invulnerable a golpes del
jugador, pero ``_check_player_contact`` -- ni el override de boss_venado.py
(~L878-916, que añade proyectil/stomp/sweep y siempre delega en
``super()._check_player_contact(player)`` al final) ni ``EnemyBase``
(enemy_base.py ~L756-800) -- consulta ``is_transitioning`` en ningún punto de
esa cadena. El resultado: ``damage_on_contact`` (0.75) sigue vivo durante los
2.5s de la ventana de quietud. La ficha del jefe pide perdonar el contacto de
esta primera pelea; la fase 2 debe castigar la esquiva pasiva, NO el hecho de
estar de pie cuando el venado cambia de forma.

Los proyectiles ya en vuelo quedan explícitamente FUERA de este alcance
(riesgo 3 del dictamen AMARILLO) -- no se tocan ni se prueban aquí.

Nota sobre el solape usado en los tests 2 y 3 (premisa a contrastar con el
enunciado, ver handoff): ``_update_rects()`` -- que sincroniza ``hurtbox``
con ``position`` -- sólo corre dentro de ``EnemyBase.update()`` cuando
``BossBase._pre_update`` NO está en transición (boss_base.py ~L430-439: con
``is_transitioning`` en True, ``_pre_update`` devuelve ``True`` de inmediato
y ``EnemyBase.update()`` corta antes de llegar a ``_update_rects()``,
enemy_base.py ~L222-227). ``teletransportar()`` (boss_venado.py L988) mueve
``rect``/``position`` en el acto, pero NO toca ``hurtbox`` -- así que durante
TODA la ventana de 2.5s ``boss.hurtbox`` queda CONGELADA en el punto donde
estaba justo antes del golpe que disparó la transición, no en el destino
nuevo. Esa hurtbox congelada es la superficie real (y la única) que
``_check_player_contact`` consulta (``self.hurtbox.colliderect(...)`` en
enemy_base.py:768), y es la lectura fiel del bug documentado: el jugador que
acaba de aterrizar el golpe que cruza el umbral sigue de pie justo ahí, al
alcance de un cuerpo que a sus ojos ya "saltó" al otro lado de la arena. Por
eso el jugador de los tests 2 y 3 se coloca sobre ``boss.hurtbox`` tal cual
queda tras la transición, y no sobre ``boss.rect``/``position`` (que sí
reflejan el destino nuevo, pero que ``_check_player_contact`` no consulta).

Nota de estado (Cambio 4 ya llegó a GREEN y está en producción:
``_check_player_contact`` ya tiene el guard ``if self.is_transitioning:
return`` al inicio -- boss_venado.py ~L917-918 -- el resto de este
docstring describe fielmente la causa raíz original, sólo el título "Fase
RED" y la frase "este test falla en rojo limpio" del test 2 quedaron
desactualizados).

Adaptación Cambio 5 (fairness, dictamen doc-guardian AMARILLO vigente,
orden del usuario 2026-08-18): el teletransporte de fase deja de ser
instantáneo -- el venado se desvanece ``FADE_TELETRANSPORTE`` (~0.55s) en
su posición VIEJA antes de saltar (ver ``test_teletransporte_ux.py``). El
test 2 ajusta su montaje para avanzar el reloj tras ``apply_hit`` antes de
comprobar que el venado terminó moviéndose -- la gracia de contacto en sí
(lo que este archivo vigila) no depende de en qué instante exacto ocurra
el salto dentro de la ventana, sólo de que ``is_transitioning`` siga en
True y ``hurtbox`` siga congelada, lo que no cambia con este Cambio.
"""
import pygame

from src.engine.core.event_bus import EventBus
from src.framework.entities.enemy_base import EnemyState
from src.stages.boss_venado.boss_venado import BossVenado

DT = 1.0 / 60.0


def make_boss(with_bus: bool = False):
    """Mismo constructor que el resto de la suite: spawn dentro de la arena."""
    boss = BossVenado(pygame.Vector2(3168, 240))
    bus = None
    if with_bus:
        bus = EventBus()
        boss.set_event_bus(bus)
    return boss, bus


def _entrar_en_fase_2(boss) -> None:
    """Lleva al jefe hasta la fase 2 por el camino real (daño + transición).

    Mismo patrón que ``test_adopcion_v3.py::_entrar_en_fase_2``: 2.6s de
    ``update()`` cubren de sobra el ``transition_timer`` de 2.5s Y el
    fotograma extra que ``BossBase._pre_update`` necesita DESPUÉS de que
    ``is_transitioning`` vuelve a False para volver a ejecutar
    ``_update_rects()`` (boss_base.py ~L430-436: el fotograma en el que
    ``_finish_phase_transition()`` corre todavía devuelve ``True`` y se
    salta esa sincronización; hace falta un fotograma más).
    """
    boss.apply_hit(6.5, (0, 0))                 # 12 -> 5.5 <= umbral 6.0
    for _ in range(int(2.6 / DT)):
        boss.update(DT)
    assert boss.current_phase == 1 and not boss.is_transitioning


class _JugadorFalso:
    """Jugador duck-typed: sólo lo que ``_check_player_contact`` toca.

    Mismo patrón que ``test_adopcion_v3.py::_JugadorFalso``. No declara
    ``_parry_active``/``_parry_window`` a propósito: ``EnemyBase.
    _check_player_contact`` los lee con ``getattr(player, "_parry_active",
    False)`` / ``getattr(player, "_parry_window", 0)`` (enemy_base.py:770),
    así que un jugador sin esos atributos cae en la rama de daño normal, que
    es exactamente lo que estos tests quieren ejercitar.
    """

    def __init__(self, rect: pygame.Rect) -> None:
        self.rect = rect
        self.hurtbox = rect
        self.velocity = pygame.Vector2(0.0, 0.0)
        self.golpes: list[float] = []

    def apply_damage(self, amount, source_position, knockback_force=150.0) -> None:
        self.golpes.append(amount)


def _jugador_solapando(hurtbox: pygame.Rect) -> _JugadorFalso:
    """Jugador centrado exactamente en ``hurtbox``: solape garantizado sin
    depender de en qué punto de la arena esté parado el venado en ese
    instante (spawn, centro tras teletransporte, etc.)."""
    rect = pygame.Rect(hurtbox.centerx - 10, hurtbox.centery - 10, 20, 20)
    return _JugadorFalso(rect)


def _fade_teletransporte(boss) -> float:
    """Duración del desvanecimiento del Cambio 5 (``FADE_TELETRANSPORTE``),
    misma receta que ``test_adopcion_v3.py::_fade_teletransporte`` --
    duplicada aquí porque este módulo no importa el paquete como ``bv``.
    ``getattr`` con caída a 0.55 porque el dictamen no fija todavía si será
    una constante de módulo o un atributo de clase."""
    valor = getattr(boss, "FADE_TELETRANSPORTE", None)
    if valor is None:
        valor = getattr(type(boss), "FADE_TELETRANSPORTE", None)
    return float(valor) if valor is not None else 0.55


def _avanzar(boss, segundos: float) -> None:
    """Corre ``update(DT)`` durante ``segundos`` -- mismo patrón que
    ``_entrar_en_fase_2``, factorizado para el Cambio 5."""
    for _ in range(int(segundos / DT)):
        boss.update(DT)


# ──────────────────────────────────────────────
# 1. Control positivo (candado)
# ──────────────────────────────────────────────

def test_control_el_contacto_dana_fuera_de_transicion():
    """CONTROL POSITIVO -- debe pasar HOY y SIEMPRE (candado, no forma parte
    del rojo de esta campaña).

    Sin ninguna transición en curso, un jugador que solapa el cuerpo del
    venado recibe ``damage_on_contact`` al invocar ``_check_player_contact``
    directamente. Fija, con las condiciones REALES de
    ``EnemyBase._check_player_contact`` (enemy_base.py:756-800), que el fake
    de jugador y el solape que arman estos tests son genuinos:

    - ``self.is_alive`` True y ``self.state != DYING`` (enemy_base.py:763):
      un ``BossVenado`` recién construido cumple ambas por defecto.
    - ``self._contact_cooldown <= 0`` (enemy_base.py:765): arranca en 0.0 y
      sólo se descuenta cuando es > 0 (enemy_base.py:835-836), así que sigue
      en 0.0 tras un único ``update()``.
    - ``self.hurtbox.colliderect(player_hurtbox)`` (enemy_base.py:767-768):
      se verifica explícitamente antes de invocar al SUT para que un fallo
      de solape no se disfrace de "no hubo daño".

    Si este control fallara, el resultado del test 2 (rojo) sería
    indistinguible de un montaje roto -- por eso viaja junto a él en el mismo
    archivo.
    """
    boss, _ = make_boss()
    # Una sola pisada del bucle real: sincroniza hurtbox/hitbox con position
    # vía EnemyBase._update_rects (enemy_base.py:227), que en reposo (sin
    # transición) corre siempre -- boss.hurtbox arranca en Rect(0,0,0,0)
    # (enemy_base.py:169-170) hasta el primer update().
    boss.update(DT)

    assert boss.is_alive and boss.state != EnemyState.DYING
    assert boss._contact_cooldown <= 0.0
    assert not boss.is_transitioning

    jugador = _jugador_solapando(boss.hurtbox)
    assert boss.hurtbox.colliderect(jugador.hurtbox), "el montaje del test no logra un solape real"

    boss._check_player_contact(jugador)

    assert jugador.golpes == [boss.damage_on_contact]


# ──────────────────────────────────────────────
# 2. El rojo de hoy
# ──────────────────────────────────────────────

def test_el_contacto_no_dana_durante_la_transicion():
    """EL ROJO DE HOY.

    Mismo montaje que el control, pero con la transición de fase REAL activa:
    ``boss.apply_hit(6.5, (0, 0))`` cruza el umbral de 6.0, dispara
    ``_start_phase_transition`` (``is_transitioning=True``,
    ``_invincibility_timer=inf``) y teletransporta al venado al centro de la
    arena (boss_venado.py L983-988). Con el jugador solapando
    ``boss.hurtbox`` (ver nota del docstring del módulo sobre por qué es
    ``hurtbox`` y no ``rect``/``position``), invocar
    ``boss._check_player_contact(jugador)`` NO debe registrar ningún daño --
    ni de barrido, ni de contacto del cuerpo -- mientras dure la ventana.

    Hoy el override de boss_venado.py delega incondicionalmente en
    ``super()._check_player_contact(player)`` (L916) sin mirar
    ``is_transitioning``, así que el daño SÍ se aplica: este test falla en
    rojo limpio contra el código actual.

    Adaptación Cambio 5 (dictamen doc-guardian AMARILLO, orden del usuario
    2026-08-18): el salto ya no es inmediato al ``apply_hit`` -- el venado
    se queda desvaneciéndose en su posición vieja unos ``FADE_TELETRANSPORTE``
    (~0.55s) antes de saltar. Se adapta el montaje avanzando el reloj hasta
    después de ese desvanecimiento antes de comprobar que el venado
    terminó moviéndose, para no acoplar este test (que vigila la GRACIA de
    contacto, Cambio 4) a la mecánica de timing del salto (que vigila
    ``test_adopcion_v3.py``). La gracia de contacto en sí NO depende de en
    qué momento exacto ocurra el salto dentro de la ventana:
    ``is_transitioning`` se mantiene en True los 2.5s completos y
    ``hurtbox`` sigue CONGELADA todo ese tiempo (ver docstring del módulo),
    así que el jugador solapando esa hurtbox vieja sigue siendo el montaje
    correcto tanto antes como después del salto.
    """
    boss, _ = make_boss()
    boss.update(DT)                       # hurtbox real antes de la transición
    x_antes = boss.position.x
    jugador = _jugador_solapando(boss.hurtbox)

    boss.apply_hit(6.5, (0, 0))           # 12 -> 5.5 <= umbral 6.0: abre la transición
    assert boss.is_transitioning
    _avanzar(boss, _fade_teletransporte(boss) + 0.05)   # más allá del desvanecimiento

    assert boss.is_transitioning, "el salto no debe cerrar la ventana por sí solo"
    assert boss.position.x != x_antes, "el venado debía haberse teletransportado tras el desvanecimiento"
    assert boss.hurtbox.colliderect(jugador.hurtbox), "el montaje del test no logra un solape real"

    boss._check_player_contact(jugador)

    assert jugador.golpes == [], (
        "el venado invulnerable siguió haciendo daño de contacto durante la transición de fase"
    )


# ──────────────────────────────────────────────
# 3. Candado del camino de restauración
# ──────────────────────────────────────────────

def test_el_contacto_revive_al_cerrar_la_ventana():
    """Candado de regresión sobre el cierre de la ventana.

    Hoy pasa trivialmente: el código actual jamás bloquea el daño de
    contacto (ni dentro ni fuera de la transición), así que este test no
    distingue todavía la implementación vieja de la nueva -- su función es
    impedir que, al escribir el guard de ``is_transitioning`` en el cambio 4,
    éste quede "pegado" en True para siempre y deje al venado inmune al
    contacto por el resto del combate.

    Receta para cerrar la ventana de forma fiel al motor: la misma que usa
    ``test_adopcion_v3.py::_entrar_en_fase_2`` -- ``apply_hit`` para cruzar
    el umbral y 2.6s de ``update(DT)`` (156 fotogramas), que cubren de sobra
    el ``transition_timer`` de 2.5s (150 fotogramas) MÁS el fotograma extra
    que ``BossBase._pre_update`` necesita, con ``is_transitioning`` ya en
    False, para volver a correr ``_update_rects()`` y sincronizar
    ``hurtbox`` con la posición (boss_base.py ~L430-439).

    Se limpia el enjambre de esporas (``boss.esporas.limpiar()``) antes de
    montar el jugador porque `_finish_phase_transition` abre el anillo de
    esporas de la fase 2 alrededor del mismo centro donde queda el cuerpo
    (boss_venado.py L1009-1010): sin esta limpieza, un jugador parado sobre
    el cuerpo también recibiría daño de esporas y el test dejaría de medir
    únicamente el contacto del cuerpo, que es la única conducta bajo prueba
    aquí.
    """
    boss, _ = make_boss()
    _entrar_en_fase_2(boss)
    boss.esporas.limpiar()

    jugador = _jugador_solapando(boss.hurtbox)
    assert boss.hurtbox.colliderect(jugador.hurtbox), "el montaje del test no logra un solape real"

    boss._check_player_contact(jugador)

    assert jugador.golpes == [boss.damage_on_contact], (
        "el contacto debía volver a doler en cuanto se cerró la ventana de transición"
    )
