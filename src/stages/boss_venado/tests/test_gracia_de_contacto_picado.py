"""TDD (B-043, REGISTRO-DE-BUGS.md, addendum del paquete B-039-C, dictamen
doc-guardian AMARILLO 2026-08-23): gracia de contacto cuerpo a cuerpo
ACOTADA durante el picado de barrido (B-039-C), el propio enraizado
(``SWEEP_ROOTED``) y la rampa de despegue posterior (B-043,
``test_despegue_barrido.py``) -- las tres piezas de una misma ventana:
"esto es VINE_SWEEP, desde que se arma hasta que el vuelo vuelve a ritmo
normal".

Contexto y causa raíz: el picado diagonal de VINE_SWEEP
(``_actualizar_picado_de_barrido``) hace que el CUERPO del jefe avance
activamente hacia el jugador durante todo el aviso -- si el contacto
corporal sigue doliendo mientras tanto, perseguir al jugador (jugada que el
propio diseño obliga al jefe a hacer) le regala un golpe gratis en el
mismo instante en que la ventana de castigo (``SWEEP_ROOTED``) debía
premiar al jugador por quedarse cerca. La rampa de despegue tiene el mismo
problema en sentido inverso: el jefe sale disparado desde donde el jugador
acaba de castigarlo.

Extensión al propio ``SWEEP_ROOTED`` (iteración 1 de verificación,
diagnóstico ``diag_ventana_muerte.py`` en
``reports\\bughunt_20260823\\fixes_verify\\b043_despegue\\``): la canónica
competent seed=1 moría en f7745 de la vida 1 -- entre sus 7 golpes de
contacto acumulados, uno (f7475) cayó exactamente mientras
``self._sweep_rooted > 0`` (boss plantado en (3172, 500), una oleada
todavía viva): el jugador que se quedó cerca para castigar la ventana de
enraizado -- la jugada que el propio diseño premia -- se llevó, además,
un golpe de contacto gratis por la superposición accidental de hurtboxes.
La ventana ROOTED existe precisamente para invitar al cuerpo a cuerpo; un
golpe de contacto durante ella castiga la jugada correcta igual que lo
hacían el picado y el despegue, así que cae bajo el mismo paraguas.

Mismo mecanismo que el Cambio 4 de la campaña de fairness (H-23,
``test_gracia_de_contacto.py``, FINDINGS.md líneas ~3591-3608): un guard
que suprime SÓLO el contacto de CUERPO
(``super()._check_player_contact(player)``). A diferencia de la gracia de
``is_transitioning`` -- que retorna de inmediato al principio del método,
suprimiendo TAMBIÉN proyectiles/stomp/esporas/oleadas -- esta gracia es más
angosta: sólo envuelve la llamada a ``super()`` al final de
``_check_player_contact``. Las crestas de ``OleadaDeLianas`` (el daño
oficial de 0.5 del barrido) y cualquier otro daño de proyectil siguen
aplicándose SIEMPRE, sin cambios -- perdonar el contacto corporal durante
un ataque que además dispara sus propias cajas de daño no debe perdonar
esas cajas. Esto es intencional incluso durante ROOTED: un jugador que se
queda plantado SIN golpear sigue en riesgo de comerse una cresta viajera.

Convenciones de la suite vecina (test_gracia_de_contacto.py,
test_picado_barrido.py): DT = 1/60, ``make_boss()`` spawnea dentro de la
arena, ``_JugadorFalso``/``_jugador_solapando`` duplicados a propósito
(mismo criterio de independencia entre archivos que ya usa el resto de la
suite).
"""
import pygame

from src.stages.boss_venado import boss_venado as bv
from src.stages.boss_venado.boss_venado import BossVenado

DT = 1.0 / 60.0


def make_boss() -> BossVenado:
    """Mismo constructor que el resto de la suite: spawn dentro de la arena."""
    return BossVenado(pygame.Vector2(3168, 240))


class _JugadorFalso:
    """Jugador duck-typed: sólo lo que ``_check_player_contact`` toca.
    Duplicado de ``test_gracia_de_contacto.py::_JugadorFalso`` -- ver ahí el
    porqué de no declarar ``_parry_active``/``_parry_window``."""

    def __init__(self, rect: pygame.Rect) -> None:
        self.rect = rect
        self.hurtbox = rect
        self.velocity = pygame.Vector2(0.0, 0.0)
        self.golpes: list[float] = []

    def apply_damage(self, amount, source_position, knockback_force=150.0) -> None:
        self.golpes.append(amount)


def _jugador_solapando(hurtbox: pygame.Rect) -> _JugadorFalso:
    """Jugador centrado exactamente en ``hurtbox``: solape garantizado."""
    rect = pygame.Rect(hurtbox.centerx - 10, hurtbox.centery - 10, 20, 20)
    return _JugadorFalso(rect)


# ──────────────────────────────────────────────
# 1. Control positivo (candado)
# ──────────────────────────────────────────────

def test_control_el_contacto_dana_en_fase_2_fuera_del_picado_y_el_despegue():
    """CONTROL POSITIVO -- debe pasar HOY y SIEMPRE (candado, no forma
    parte del rojo de este cambio). En fase 2, sin picado
    (``_telegraph != "VINE_SWEEP"``) ni despegue (``_sweep_despegue == 0``),
    el contacto corporal sigue doliendo -- fija que la gracia nueva no se
    sobre-extienda al resto de la fase 2 (p. ej. el vuelo normal en figura
    de ocho). Si este control fallara, el resultado de los tests 2/3
    (rojo) sería indistinguible de un montaje roto."""
    boss = make_boss()
    boss.current_phase = 1
    boss.update(DT)   # sincroniza hurtbox con position (EnemyBase._update_rects)

    assert boss._telegraph != "VINE_SWEEP" and boss._sweep_despegue <= 0.0
    assert boss.is_alive and not boss.is_transitioning

    jugador = _jugador_solapando(boss.hurtbox)
    assert boss.hurtbox.colliderect(jugador.hurtbox), "el montaje del test no logra un solape real"

    boss._check_player_contact(jugador)

    assert jugador.golpes == [boss.damage_on_contact]


# ──────────────────────────────────────────────
# 2. El rojo de hoy -- picado
# ──────────────────────────────────────────────

def test_el_contacto_no_dana_durante_el_picado_de_barrido():
    """EL ROJO DE HOY (picado). Mientras dura el aviso de VINE_SWEEP en
    fase 2 el jefe pica activamente hacia el jugador
    (``_actualizar_picado_de_barrido``) -- el contacto de cuerpo no debe
    doler durante esa persecución obligada por el propio diseño."""
    boss = make_boss()
    boss.current_phase = 1
    boss.set_player_ref(pygame.Rect(2900, 528, 20, 32))
    boss._try_attack("VINE_SWEEP")
    boss.update(DT)   # un fotograma dentro del picado; sincroniza hurtbox

    assert boss._telegraph == "VINE_SWEEP", "montaje del test: se esperaba seguir en el aviso"

    jugador = _jugador_solapando(boss.hurtbox)
    assert boss.hurtbox.colliderect(jugador.hurtbox), "el montaje del test no logra un solape real"

    boss._check_player_contact(jugador)

    assert jugador.golpes == [], (
        "el picado de barrido siguió haciendo daño de contacto corporal durante el aviso")


# ──────────────────────────────────────────────
# 3. El rojo de hoy -- despegue
# ──────────────────────────────────────────────

def test_el_contacto_no_dana_durante_el_despegue():
    """EL ROJO DE HOY (despegue). Mientras dura la rampa de arranque tras
    el enraizado (``_sweep_despegue > 0``, B-043) el jefe sale disparado
    desde donde el jugador acaba de castigar la ventana -- el contacto de
    cuerpo tampoco debe doler durante esa rampa."""
    boss = make_boss()
    boss.current_phase = 1
    boss.update(DT)   # sincroniza hurtbox antes de forzar el estado
    boss._sweep_despegue = bv.SWEEP_DESPEGUE

    jugador = _jugador_solapando(boss.hurtbox)
    assert boss.hurtbox.colliderect(jugador.hurtbox), "el montaje del test no logra un solape real"

    boss._check_player_contact(jugador)

    assert jugador.golpes == [], (
        "el despegue siguió haciendo daño de contacto corporal durante la rampa")


# ──────────────────────────────────────────────
# 4. El rojo de la iteración 1 -- el propio enraizado (SWEEP_ROOTED)
# ──────────────────────────────────────────────

def test_el_contacto_no_dana_durante_el_enraizado_del_barrido():
    """EL ROJO DE LA ITERACIÓN 1 (enraizado). Mientras dura
    ``SWEEP_ROOTED`` el jefe está plantado invitando al cuerpo a cuerpo --
    un jugador que se acerca a golpear no debe llevarse, de regalo, un
    golpe de contacto por la superposición accidental de hurtboxes
    (evidencia: canónica competent seed=1, golpe de contacto en f7475 con
    ``_sweep_rooted=1.017`` -- ver el docstring del módulo)."""
    boss = make_boss()
    boss.current_phase = 1
    boss.update(DT)   # sincroniza hurtbox antes de forzar el estado
    boss._sweep_rooted = bv.SWEEP_ROOTED

    jugador = _jugador_solapando(boss.hurtbox)
    assert boss.hurtbox.colliderect(jugador.hurtbox), "el montaje del test no logra un solape real"

    boss._check_player_contact(jugador)

    assert jugador.golpes == [], (
        "el enraizado siguió haciendo daño de contacto corporal durante la ventana de castigo")


# ──────────────────────────────────────────────
# 5. Candado: las crestas siguen dañando siempre
# ──────────────────────────────────────────────

def test_las_crestas_de_la_oleada_siguen_danando_durante_el_picado():
    """Candado explícito del alcance: la gracia nueva SÓLO envuelve el
    contacto de CUERPO -- una cresta de ``OleadaDeLianas`` que solape al
    jugador durante el mismo picado debe seguir aplicando su 0.5 de daño
    oficial, sin cambios."""
    from src.stages.boss_venado.efectos_venado import OleadaDeLianas

    boss = make_boss()
    boss.current_phase = 1
    boss.set_player_ref(pygame.Rect(2900, 528, 20, 32))
    boss._try_attack("VINE_SWEEP")
    boss.update(DT)   # dentro del aviso -- la gracia de cuerpo está activa

    assert boss._telegraph == "VINE_SWEEP", "montaje del test: se esperaba seguir en el aviso"

    # A RAS DE SUELO a propósito, no sobre boss.hurtbox: durante el picado el
    # cuerpo del jefe todavía va descendiendo (_approach_y hacia _y_de_suelo())
    # y puede seguir en el aire -- la cresta de la oleada SIEMPRE viaja a ras
    # de FLOOR_Y (ver OleadaDeLianas.rect), así que el solape real de este
    # ataque contra un jugador de pie se arma ahí, no contra la posición
    # vertical del cuerpo en este fotograma concreto.
    jugador = _JugadorFalso(pygame.Rect(2900, int(bv.FLOOR_Y) - 32, 20, 32))
    oleada = OleadaDeLianas(float(jugador.rect.centerx), 1, bv.FLOOR_Y, bv.ARENA_X0, bv.ARENA_X1)
    assert oleada.rect.colliderect(jugador.hurtbox), "el montaje del test no logra un solape real"
    boss._oleadas = [oleada]

    boss._check_player_contact(jugador)

    assert jugador.golpes == [0.5], (
        "una cresta de la oleada debe seguir dañando durante el picado, "
        "aunque el contacto de cuerpo esté perdonado")


def test_las_crestas_de_la_oleada_siguen_danando_durante_el_enraizado():
    """Mismo candado de alcance que el anterior, para ROOTED: un jugador
    que se queda plantado SIN golpear (sin castigar) sigue en riesgo de
    comerse una cresta viajera -- perdonar el contacto de cuerpo durante la
    ventana de castigo no perdona quedarse parado en la trayectoria de la
    oleada."""
    from src.stages.boss_venado.efectos_venado import OleadaDeLianas

    boss = make_boss()
    boss.current_phase = 1
    boss.update(DT)
    boss._sweep_rooted = bv.SWEEP_ROOTED

    jugador = _JugadorFalso(pygame.Rect(2900, int(bv.FLOOR_Y) - 32, 20, 32))
    oleada = OleadaDeLianas(float(jugador.rect.centerx), 1, bv.FLOOR_Y, bv.ARENA_X0, bv.ARENA_X1)
    assert oleada.rect.colliderect(jugador.hurtbox), "el montaje del test no logra un solape real"
    boss._oleadas = [oleada]

    boss._check_player_contact(jugador)

    assert jugador.golpes == [0.5], (
        "una cresta de la oleada debe seguir dañando durante el enraizado, "
        "aunque el contacto de cuerpo esté perdonado")
