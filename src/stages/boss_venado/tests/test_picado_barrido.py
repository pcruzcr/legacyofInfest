"""TDD (B-039 opción C, REGISTRO-DE-BUGS.md, decisión del usuario 2026-08-23):
picado de aterrizaje del VINE_SWEEP de fase 2.

Contexto y causa raíz (playtest humano #2, `reports/aaa_parte2_playtest_humano`,
2026-08-22): en fase 2 el jugador hizo 0 daño en las dos sesiones grabadas
porque la ventana de enraizado (SWEEP_ROOTED) es inalcanzable a pie -- durante
el aviso de VINE_SWEEP (`boss_venado.py::_update_movement`, rama
``grounded_punish``) la X del jefe queda congelada, y con
``PLAYER_WALK_SPEED = 90 px/s`` el jugador recorre ~108px en 1.2s mientras el
gap real medido en pelea llegaba a ~555px.

Opción C (recomendada por el diseño, elegida por el usuario): durante el
propio aviso el jefe PICA en diagonal hacia el jugador -- desciende (ya lo
hacía, vía ``_approach_y`` hacia ``_y_de_suelo()``) Y avanza en X hacia un
punto a ``ATERRIZAJE_BARRIDO`` px del jugador, por el lado en que ya estaba
(nunca cruza por encima), con el destino recortado a los mismos márgenes de
pared que el resto del movimiento en el suelo. ``SWEEP_ROOTED`` sube de 1.2s
a 1.6s en el mismo cambio para que la ventana de castigo, ahora sí alcanzable,
tenga un margen real.

Convenciones de la suite vecina (test_boss_venado.py, test_reanclaje_bezier.py):
DT = 1/60, ``make_boss()`` spawnea dentro de la arena, forzar
``current_phase = 1`` a mano es un patrón ya aceptado (ver
test_reanclaje_bezier.py) porque VINE_SWEEP sólo vive en
``phases[1].attack_patterns``.
"""
import pygame
import pytest

from src.stages.boss_venado import boss_venado as bv
from src.stages.boss_venado.boss_venado import BossVenado

DT = 1.0 / 60.0

# Margen de redondeo de punto flotante para comparar contra el destino exacto
# del picado (no mide la magnitud del bug -- sólo evita falsos negativos por
# el paso acotado del último fotograma).
TOLERANCIA_GAP_PX = 2.0


def make_boss() -> BossVenado:
    """Mismo constructor que el resto de la suite: spawn dentro de la arena."""
    return BossVenado(pygame.Vector2(3168, 240))


def _correr_aviso_completo(boss: BossVenado) -> None:
    """Corre el ciclo real de ``update()`` (attack_state -> movimiento ->
    sincronización de rect) durante todo ``SWEEP_TELEGRAPH`` -- sin '+1': el
    disparo real cae exactamente en la última llamada, mismo criterio que
    ``test_vine_sweep_crea_dos_oleadas_con_direcciones_opuestas`` en
    test_boss_venado.py."""
    for _ in range(int(bv.SWEEP_TELEGRAPH / DT)):
        boss.update(DT)


def test_picado_de_barrido_cierra_el_gap_en_fase_2():
    """(1) Al expirar el aviso de VINE_SWEEP en fase 2, el gap horizontal
    entre los centros del jefe y el jugador debe quedar en, como mucho,
    ATERRIZAJE_BARRIDO -- hoy (X congelada durante todo el aviso) el gap se
    queda en la separación inicial, muy por encima."""
    boss = make_boss()
    boss.current_phase = 1
    jugador = pygame.Rect(2900, 528, 20, 32)
    boss.set_player_ref(jugador)

    gap_inicial = abs(boss.rect.centerx - jugador.centerx)
    assert gap_inicial > bv.ATERRIZAJE_BARRIDO + TOLERANCIA_GAP_PX, (
        "montaje del test: se esperaba un gap inicial grande para que el "
        "picado tenga algo que cerrar")

    boss._try_attack("VINE_SWEEP")
    _correr_aviso_completo(boss)

    gap = abs(boss.rect.centerx - jugador.centerx)
    assert gap <= bv.ATERRIZAJE_BARRIDO + TOLERANCIA_GAP_PX, (
        f"B-039-C: gap horizontal de {gap:.1f}px al expirar el aviso de "
        f"VINE_SWEEP (esperado <= {bv.ATERRIZAJE_BARRIDO}px)")


def test_picado_de_barrido_no_saca_al_jefe_de_la_arena_pegado_a_cualquier_pared():
    """(2) Riesgo 4 del dictamen: con el jugador pegado a una pared y el
    jefe forzado al lado que empujaría el destino más allá de ella, el
    cuerpo debe quedarse SIEMPRE dentro de la arena -- no sólo al final, en
    todo fotograma del picado (el clamp EXPLÍCITO de
    _actualizar_picado_de_barrido muerde).

    Llama a ``_update_movement`` directamente (no ``boss.update``) a
    propósito: ``update()`` trae, al final, un candado de ÚLTIMO RECURSO
    genérico (B-035, ver el comentario en boss_venado.py justo antes de
    ``super().update()``) que re-clampea CUALQUIER posición fuera de la
    arena pase lo que pase durante el frame -- con él en medio, este test
    seguiría en verde aunque el clamp explícito del picado se borrara por
    completo (falso negativo verificado por mutación manual). Yendo directo
    a ``_update_movement`` se aísla el clamp bajo prueba. ``self.rect`` no
    se resincroniza fuera de ``update()``, así que se compara contra
    ``position.x`` + el ancho VIVO del rect (que sí es válido: no cambia
    entre fotogramas de este aviso)."""
    casos = (
        (-1, pygame.Rect(int(bv.ARENA_X0) + 10, 528, 20, 32)),   # pared izquierda
        (1, pygame.Rect(int(bv.ARENA_X1) - 30, 528, 20, 32)),    # pared derecha
    )
    for lado, jugador in casos:
        boss = make_boss()
        boss.current_phase = 1
        boss.set_player_ref(jugador)
        boss._try_attack("VINE_SWEEP")
        boss._sweep_lado_picado = lado   # fuerza el lado que empujaría el destino fuera de la arena
        ancho = float(boss.rect.width)
        for _ in range(int(bv.SWEEP_TELEGRAPH / DT)):
            boss._update_movement(DT)
            izquierda = boss.position.x
            derecha = boss.position.x + ancho
            assert izquierda >= bv.ARENA_X0 and derecha <= bv.ARENA_X1, (
                f"B-039-C: el venado salió de la arena durante el picado "
                f"(lado={lado}, position.x={boss.position.x:.1f})")


def test_picado_de_barrido_nunca_teletransporta():
    """(3) Paso acotado a VEL_PICADO*dt por fotograma -- mismo criterio que
    ``_approach_y``: el picado jamás debe saltar de golpe al destino."""
    boss = make_boss()
    boss.current_phase = 1
    boss.set_player_ref(pygame.Rect(2900, 528, 20, 32))
    boss._try_attack("VINE_SWEEP")

    paso_maximo = bv.VEL_PICADO * DT + 0.5   # margen de redondeo de punto flotante
    x_anterior = boss.position.x
    for _ in range(int(bv.SWEEP_TELEGRAPH / DT)):
        boss.update(DT)
        salto = abs(boss.position.x - x_anterior)
        assert salto <= paso_maximo, (
            f"B-039-C: el picado se movió {salto:.1f}px en un solo fotograma "
            f"(máximo tolerado {paso_maximo:.1f}px) -- no debe teletransportar")
        x_anterior = boss.position.x


def test_sweep_rooted_dura_1_6_segundos():
    """(4) SWEEP_ROOTED sube de 1.2s a 1.6s junto con el picado de
    aterrizaje: con el gap ahora cerrado durante el aviso, la ventana de
    castigo posterior gana el margen real que antes nunca se alcanzaba."""
    assert bv.SWEEP_ROOTED == pytest.approx(1.6)


def test_picado_de_barrido_solo_corre_durante_el_telegraph_no_durante_rooted():
    """Guardia de fase del diseño: el picado sólo se aplica MIENTRAS
    ``self._telegraph == "VINE_SWEEP"`` (el aviso) -- una vez que la oleada
    se dispara y arranca ``_sweep_rooted``, la X vuelve a quedar plantada tal
    como ya cubre ``test_vine_sweep_arma_sweep_rooted_y_planta_al_jefe`` en
    test_boss_venado.py. Este candado se limita a comprobar que, ya
    aterrizado (rooted), varios frames de ``_update_movement`` no mueven X."""
    boss = make_boss()
    boss.current_phase = 1
    boss.set_player_ref(pygame.Rect(2900, 528, 20, 32))
    boss._try_attack("VINE_SWEEP")
    _correr_aviso_completo(boss)
    assert boss._sweep_rooted > 0, "montaje del test: se esperaba entrar al enraizado tras el aviso"

    x_rooted = boss.rect.centerx
    for _ in range(10):
        boss._update_movement(DT)
    assert boss.rect.centerx == x_rooted, (
        "el jefe se movió en X durante el enraizado (_sweep_rooted) -- el "
        "picado debe limitarse al aviso")
