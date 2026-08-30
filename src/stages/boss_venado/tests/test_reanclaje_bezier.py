"""TDD (B-041, REGISTRO-DE-BUGS.md): reanclaje de `_bezier_t` al reanudar el
vuelo bezier de fase 2 tras salir de una ventana plantada.

Contexto y causa raíz (evidencia: campaña bughunt_20260823, sonda
`barrer_saltos.py` -- 18 saltos > 50px por pelea, máx. 501,1px en f8426,
todos en fase 2, todos al expirar la recuperación de una ventana plantada).
En la rama bezier de `_update_movement` (boss_venado.py ~L730-748),
`self.position.x = px` toma la X de `CurveTools.sample_path(self._bezier_path,
self._bezier_t)` sin límite ni interpolación. Mientras el jefe está plantado
-- recuperación de la pared de CHARGE (`_charge_recover > 0`, ~L943-949) o
enraizado del barrido (`_sweep_rooted > 0`, ~L950-954) -- ese mismo método
retorna ANTES de avanzar `_bezier_t` (el `return` anticipado de ~L698), que
queda CONGELADO apuntando a donde iba la curva cuando arrancó la ventana,
mientras el cuerpo real del jefe se movió a la pared o al suelo.
`_t_mas_cercano_en_ruta` (el fix de H-24/B-028) sólo se invoca al ENTRAR a
fase 2 (`_finish_phase_transition`, ~L1431), nunca al reanudar el vuelo tras
salir de una ventana plantada -- así que el primer fotograma de vuelo
reanudado salta de golpe al punto viejo de la curva, sin importar cuán lejos
quede del cuerpo real.

Fix esperado (mismo remedio que H-24/B-028, aplicado en el otro punto de
reanudación): re-anclar `_bezier_t` con `_t_mas_cercano_en_ruta` en el
instante EXACTO en que la ventana plantada expira (`_charge_recover` o
`_sweep_rooted` llegan a 0), antes de que `_update_movement` vuelva a leer
la ruta -- sólo si la fase activa usa movimiento bezier y ya tiene una ruta
calculada.
"""
import pygame
import pytest

from src.stages.boss_venado import boss_venado as bv
from src.stages.boss_venado.boss_venado import BossVenado

DT = 1.0 / 60.0

# Mismo criterio de "salto de teletransporte" que usó la sonda de la campaña
# (`reports/bughunt_20260823/ocular/_probe/barrer_saltos.py --umbral 50`),
# con un margen más generoso (40px < 50px) porque este test no mide la
# magnitud del bug -- sólo que el reanclaje deja el primer fotograma
# reanudado dentro de un paso de movimiento normal, no un salto de cientos
# de px como los que medía la sonda.
UMBRAL_SALTO_PX = 40.0


def make_boss():
    """Mismo constructor que el resto de la suite: spawn dentro de la arena."""
    return BossVenado(pygame.Vector2(3168, 240))


def _preparar_fase2_con_ruta_lejos_del_cuerpo(boss) -> None:
    """Deja el jefe en fase 2 con la ruta bezier real ya calculada (mismo
    atajo que ``test_figure8_path_inside_arena_and_reachable`` en
    ``test_boss_venado.py``: ``_build_figure8_path()`` directo, sin pasar
    por la transición completa -- forzar ``current_phase = 1`` a mano ya es
    un patrón aceptado en la suite, ver boss_venado.py ~L528) y con
    ``_bezier_t`` apuntando al CENTRO de la figura en ocho mientras el
    CUERPO real (``position``) se deja pegado a la pared izquierda --
    exactamente la desincronización que produce una ventana plantada real
    (CHARGE contra la pared / SWEEP_ROOTED en el suelo): el cuerpo se mueve
    a otra parte de la arena mientras ``_bezier_t`` sigue congelado en el
    punto donde iba la curva cuando arrancó la ventana."""
    boss.current_phase = 1
    boss._bezier_path = boss._build_figure8_path()
    boss._bezier_dir = 1
    boss._bezier_t = 0.5   # centro de la figura en ocho
    boss.position.update(bv.ARENA_X0 + 40.0, boss._base_y)
    boss.rect.x, boss.rect.y = int(boss.position.x), int(boss.position.y)


def test_reanclaje_tras_charge_recover_no_teletransporta():
    """CASO 1 (post-CHARGE): al expirar ``_charge_recover``, el primer
    fotograma de vuelo reanudado no debe saltar más de ``UMBRAL_SALTO_PX``.

    Con el código de hoy (sin el fix) el salto mide cientos de px -- la
    distancia real entre la pared izquierda (donde quedó el cuerpo) y el
    centro de la figura en ocho (donde seguía apuntando ``_bezier_t``)."""
    boss = make_boss()
    _preparar_fase2_con_ruta_lejos_del_cuerpo(boss)
    boss._charge_recover = DT / 2.0   # a punto de expirar en este mismo tick
    boss._y_recovering = False

    pos_congelada = pygame.Vector2(boss.position)
    boss._update_attack_state(DT)                 # expira la ventana -- debe reanclar _bezier_t aquí
    assert boss._charge_recover <= 0.0, "el montaje del test no expiró la ventana de CHARGE"
    assert boss._y_recovering, "el fix no debe tocar el propio candado de _y_recovering"
    boss._update_movement(DT)                     # primer fotograma de vuelo reanudado

    salto = boss.position.distance_to(pos_congelada)
    assert salto < UMBRAL_SALTO_PX, (
        f"B-041: el venado saltó {salto:.1f}px al reanudar el vuelo bezier "
        f"tras la recuperación de CHARGE (máximo tolerado {UMBRAL_SALTO_PX}px)")


def test_reanclaje_tras_sweep_rooted_no_teletransporta():
    """CASO 2 (post-SWEEP_ROOTED): mismo mecanismo, otra ventana plantada."""
    boss = make_boss()
    _preparar_fase2_con_ruta_lejos_del_cuerpo(boss)
    boss._sweep_rooted = DT / 2.0
    boss._y_recovering = False

    pos_congelada = pygame.Vector2(boss.position)
    boss._update_attack_state(DT)
    assert boss._sweep_rooted <= 0.0, "el montaje del test no expiró la ventana de SWEEP_ROOTED"
    assert boss._y_recovering, "el fix no debe tocar el propio candado de _y_recovering"
    boss._update_movement(DT)

    salto = boss.position.distance_to(pos_congelada)
    assert salto < UMBRAL_SALTO_PX, (
        f"B-041: el venado saltó {salto:.1f}px al reanudar el vuelo bezier "
        f"tras el enraizado de SWEEP_ROOTED (máximo tolerado {UMBRAL_SALTO_PX}px)")


def test_reanclaje_elige_el_punto_mas_cercano_de_la_ruta():
    """Candado más fino: no basta con que el salto sea pequeño -- el
    ``_bezier_t`` nuevo debe corresponder de verdad al punto de la polilínea
    más cercano al cuerpo (mismo contrato que ya cubre
    ``test_entrar_en_fase_2_reanuda_la_ruta_sin_teletransporte`` en
    ``test_boss_venado.py`` para el caso de ENTRADA a fase 2 -- este
    candado cubre el caso de REANUDACIÓN)."""
    boss = make_boss()
    _preparar_fase2_con_ruta_lejos_del_cuerpo(boss)
    esperado = boss._t_mas_cercano_en_ruta(boss._bezier_path)
    boss._charge_recover = DT / 2.0
    boss._y_recovering = False

    boss._update_attack_state(DT)

    assert boss._bezier_t == pytest.approx(esperado)
