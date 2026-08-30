"""TDD (B-043, REGISTRO-DE-BUGS.md, addendum del paquete B-039-C, dictamen
doc-guardian AMARILLO 2026-08-23): rampa de arranque (despegue) del vuelo
bezier tras el enraizado del barrido (``SWEEP_ROOTED``), y fantasmas de
sprite durante el picado/despegue.

Contexto y causa raíz (evidencia: campaña bughunt_20260823, playtest del
propio arnés -- ``winnable`` del competent RED, jefe con HP 2.9 al agotar
15000f). B-041 ya corrigió el TELETRANSPORTE del primer fotograma al
reanudar el vuelo bezier (``_reanclar_bezier_al_reanudar``, ver
``test_reanclaje_bezier.py``), pero no tocó la VELOCIDAD a la que arranca
ese vuelo reanudado: en cuanto ``_sweep_rooted`` llega a cero, la rama
bezier de ``_update_movement`` vuelve a avanzar ``_bezier_t`` a plena
velocidad (~450 px/s medidos) desde el punto donde el jugador acababa de
castigar la ventana plantada -- exactamente donde el diseño quiere que
esté parado. El resultado: el jefe sale disparado y lo atropella en el
mismo instante en que la jugada correcta debía premiarlo.

Fix: ``SWEEP_DESPEGUE`` (constante de módulo) arranca un temporizador
propio (``self._sweep_despegue``) en el mismo instante en que expira
``_sweep_rooted``, DESPUÉS de que ``_reanclar_bezier_al_reanudar()`` ya
fijó el nuevo ``_bezier_t``. Mientras dura, ``_update_movement`` escala el
avance de ``_bezier_t`` con un factor ease-in cuadrático (0 al arrancar, 1
al cerrar la ventana) -- mismo espíritu de "nunca de golpe" que
``_approach_y``/``_actualizar_picado_de_barrido``, aplicado esta vez a la
VELOCIDAD en lugar de a la distancia.

Convenciones de la suite vecina (test_reanclaje_bezier.py,
test_picado_barrido.py): DT = 1/60, ``make_boss()`` spawnea dentro de la
arena, forzar ``current_phase = 1``/``_bezier_path`` a mano es un patrón ya
aceptado, y ``_update_attack_state``/``_update_movement`` se llaman
DIRECTAMENTE (no ``boss.update()``) para aislar la máquina de movimiento
del resto del pipeline -- exactamente el mismo orden en que ``update()``
real los invoca dentro de cada fotograma.
"""
import pygame
import pytest

from src.stages.boss_venado import boss_venado as bv
from src.stages.boss_venado.boss_venado import BossVenado
from src.stages.boss_venado.efectos_venado import EfectosRegistrados

DT = 1.0 / 60.0


def make_boss() -> BossVenado:
    """Mismo constructor que el resto de la suite: spawn dentro de la arena."""
    return BossVenado(pygame.Vector2(3168, 240))


def _preparar_fase2_con_ruta_lejos_del_cuerpo(boss: BossVenado) -> None:
    """Idéntico a ``test_reanclaje_bezier.py::_preparar_fase2_con_ruta_lejos_del_cuerpo``
    (duplicado a propósito -- mismo criterio de independencia entre archivos
    de test que ya usa el resto de la suite, ver ``test_gracia_de_contacto.py
    ::_fade_teletransporte``): deja el jefe en fase 2 con la ruta bezier real
    ya calculada y el CUERPO pegado a la pared izquierda mientras ``_bezier_t``
    apunta al centro de la figura en ocho -- la misma desincronización que
    deja una ventana plantada real al expirar."""
    boss.current_phase = 1
    boss._bezier_path = boss._build_figure8_path()
    boss._bezier_dir = 1
    boss._bezier_t = 0.5
    boss.position.update(bv.ARENA_X0 + 40.0, boss._base_y)
    boss.rect.x, boss.rect.y = int(boss.position.x), int(boss.position.y)


def _expirar_sweep_rooted(boss: BossVenado) -> None:
    """Deja ``_sweep_rooted`` a un tick de expirar y corre el fotograma que
    lo cierra -- mismo montaje que ``test_reanclaje_tras_sweep_rooted_no_teletransporta``."""
    boss._sweep_rooted = DT / 2.0
    boss._y_recovering = False
    boss._update_attack_state(DT)


# ──────────────────────────────────────────────
# Orden: el despegue arranca DESPUÉS del reanclaje B-041
# ──────────────────────────────────────────────

def test_sweep_despegue_arranca_en_el_mismo_fotograma_del_reanclaje():
    """El despegue se arma en el MISMO fotograma en que expira
    ``_sweep_rooted`` -- y usa el ``_bezier_t`` YA reanclado (B-041), no el
    valor viejo congelado: si el orden estuviera invertido (armar el
    despegue antes de reanclar), este candado seguiría en verde por
    accidente porque ambos ocurren en la misma llamada -- lo que de verdad
    fija es que las DOS cosas queden ciertas a la vez al cerrar este
    fotograma."""
    boss = make_boss()
    _preparar_fase2_con_ruta_lejos_del_cuerpo(boss)
    esperado = boss._t_mas_cercano_en_ruta(boss._bezier_path)

    _expirar_sweep_rooted(boss)

    assert boss._sweep_rooted <= 0.0
    assert boss._bezier_t == pytest.approx(esperado), (
        "el _bezier_t del fotograma del despegue debe ser el YA reanclado")
    assert boss._sweep_despegue == pytest.approx(bv.SWEEP_DESPEGUE), (
        "el despegue debe armarse a SWEEP_DESPEGUE completo en el mismo "
        "fotograma en que expira el enraizado")


# ──────────────────────────────────────────────
# (a) Candado de velocidad media -- rojo hoy: ~450 px/s
# ──────────────────────────────────────────────

def test_despegue_arranca_lento_tras_el_enraizado_del_barrido():
    """(a) B-043: la velocidad horizontal MEDIA del primer 0.2s tras
    expirar SWEEP_ROOTED debe quedar por debajo de 250 px/s -- con el
    código de ayer (reanudación del vuelo bezier a plena velocidad, sin
    rampa) medía ~450 px/s, suficiente para atropellar al jugador que
    acababa de castigar la ventana plantada."""
    boss = make_boss()
    _preparar_fase2_con_ruta_lejos_del_cuerpo(boss)
    _expirar_sweep_rooted(boss)
    assert boss._sweep_despegue > 0.0, "montaje del test: se esperaba que el despegue arrancara"

    ventana = 0.2
    n_frames = int(round(ventana / DT))
    desplazamiento_total = 0.0
    for _ in range(n_frames):
        x_antes = boss.position.x
        boss._update_attack_state(DT)
        boss._update_movement(DT)
        desplazamiento_total += abs(boss.position.x - x_antes)

    velocidad_media = desplazamiento_total / ventana
    assert velocidad_media < 250.0, (
        f"B-043: el despegue arrancó a {velocidad_media:.1f} px/s de media "
        f"en los primeros {ventana}s tras el enraizado (esperado < 250 px/s)")


# ──────────────────────────────────────────────
# (b) Candado de salto por fotograma -- mismo umbral que B-041
# ──────────────────────────────────────────────

def test_despegue_nunca_salta_mas_de_50px_por_fotograma():
    """(b) Ningún fotograma posterior al enraizado -- ni el propio
    reanclaje (ya cubierto por test_reanclaje_bezier.py con un umbral de
    40px) ni ningún paso de la rampa de despegue -- debe mover el cuerpo
    más de 50px de golpe en un solo fotograma (mismo umbral que usó la
    sonda de la campaña, ``barrer_saltos.py --umbral 50``). Corre 2s
    completos: cubre el despegue entero (0.45s) y el vuelo normal después,
    para que un bug que sólo se manifieste al cerrar la rampa tampoco pase
    desapercibido."""
    boss = make_boss()
    _preparar_fase2_con_ruta_lejos_del_cuerpo(boss)
    _expirar_sweep_rooted(boss)

    pos_anterior = pygame.Vector2(boss.position)
    for _ in range(120):
        boss._update_attack_state(DT)
        boss._update_movement(DT)
        pos_actual = pygame.Vector2(boss.position)
        salto = pos_actual.distance_to(pos_anterior)
        assert salto <= 50.0, (
            f"B-043: salto de {salto:.1f}px en un solo fotograma durante/"
            f"después del despegue")
        pos_anterior = pos_actual


def test_sweep_despegue_decrece_y_se_apaga_solo():
    """Candado de regresión sobre el propio temporizador: debe decrecer con
    cada fotograma y llegar exactamente a 0.0 (nunca negativo) al cabo de
    SWEEP_DESPEGUE segundos."""
    boss = make_boss()
    _preparar_fase2_con_ruta_lejos_del_cuerpo(boss)
    _expirar_sweep_rooted(boss)

    n_frames = int(round(bv.SWEEP_DESPEGUE / DT)) + 5
    for _ in range(n_frames):
        boss._update_attack_state(DT)
    assert boss._sweep_despegue == 0.0


# ──────────────────────────────────────────────
# Limpieza de estado (mismo patrón que _sweep_rooted/_fantasmas)
# ──────────────────────────────────────────────

def test_cancelar_ataques_en_vuelo_limpia_el_despegue():
    """El salto de teletransporte de fase invalida la rampa en curso igual
    que invalida ``_sweep_rooted``/los fantasmas -- sin esto, un despegue
    armado justo antes de un cambio de fase seguiría frenando el vuelo
    bezier en la posición NUEVA, donde nunca hubo ningún enraizado."""
    boss = make_boss()
    _preparar_fase2_con_ruta_lejos_del_cuerpo(boss)
    _expirar_sweep_rooted(boss)
    assert boss._sweep_despegue > 0.0

    boss._cancelar_ataques_en_vuelo()

    assert boss._sweep_despegue == 0.0


def test_on_defeated_limpia_el_despegue():
    """Misma razón que ``test_on_defeated_limpia_los_fantasmas``: la
    secuencia de derrota no debe heredar un temporizador de una ventana de
    ataque que ya no tiene sentido."""
    boss = make_boss()
    _preparar_fase2_con_ruta_lejos_del_cuerpo(boss)
    _expirar_sweep_rooted(boss)
    assert boss._sweep_despegue > 0.0

    boss.on_defeated()

    assert boss._sweep_despegue == 0.0


# ──────────────────────────────────────────────
# Animación: 'vine' se mantiene durante la rampa
# ──────────────────────────────────────────────

def test_get_animation_key_vine_durante_el_despegue():
    """La animación 'vine' se mantiene durante la rampa de despegue -- sin
    esto, el primer fotograma tras el enraizado volvía a 'drift'/
    'frenzy_drift' a mitad de una rampa que todavía se mueve casi al ritmo
    del barrido, rompiendo la continuidad visual del ataque."""
    boss = make_boss()
    boss.current_phase = 1
    boss._sweep_despegue = bv.SWEEP_DESPEGUE
    assert boss._get_animation_key() == "vine"


# ──────────────────────────────────────────────
# Fantasmas de sprite durante el picado y el despegue
# ──────────────────────────────────────────────

def test_fantasmas_se_agregan_durante_el_picado_de_barrido():
    """Mismo patrón que ``test_charge_active_vfx_solo_en_fase_2``
    (test_boss_venado.py): mientras dura el AVISO de VINE_SWEEP en fase 2
    (el picado diagonal, B-039-C) el jefe se desplaza de verdad -- merece
    el mismo rastro de sprite que ya lleva la embestida."""
    boss = make_boss()
    boss.current_phase = 1
    boss._telegraph = "VINE_SWEEP"
    boss._telegraph_timer = bv.SWEEP_TELEGRAPH
    boss.conectar_efectos(EfectosRegistrados())
    for _ in range(20):
        boss._frames_vfx += 1
        boss._update_vfx(DT)
    assert boss._fantasmas.cantidad() >= 1, (
        "el picado de barrido en fase 2 debe agregar fantasmas de sprite")


def test_fantasmas_se_agregan_durante_el_despegue():
    """Mismo criterio que el picado, para la rampa de despegue posterior."""
    boss = make_boss()
    boss.current_phase = 1
    boss._sweep_despegue = bv.SWEEP_DESPEGUE
    boss.conectar_efectos(EfectosRegistrados())
    for _ in range(20):
        boss._frames_vfx += 1
        boss._update_vfx(DT)
    assert boss._fantasmas.cantidad() >= 1, (
        "el despegue tras el enraizado debe agregar fantasmas de sprite")


def test_fantasmas_no_se_agregan_por_picado_fuera_de_fase_2():
    """Guardia de fase (mismo criterio que el resto del picado/despegue):
    ``VINE_SWEEP`` sólo vive en ``phases[1].attack_patterns``, pero este
    candado fija el gate explícito de todos modos -- forzar
    ``_telegraph == "VINE_SWEEP"`` en fase 0 no debe agregar fantasmas."""
    boss = make_boss()
    boss.current_phase = 0
    boss._telegraph = "VINE_SWEEP"
    boss._telegraph_timer = bv.SWEEP_TELEGRAPH
    boss.conectar_efectos(EfectosRegistrados())
    for _ in range(20):
        boss._frames_vfx += 1
        boss._update_vfx(DT)
    assert boss._fantasmas.cantidad() == 0
