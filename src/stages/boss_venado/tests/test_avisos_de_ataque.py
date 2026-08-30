"""Fase RED — campaña de fairness (Cambio 1): avisos de ataque para VINE_TOSS/MUSHROOM_SPORE.

Hoy (dictamen doc-guardian AMARILLO vigente) ``_try_attack`` dispara VINE_TOSS y
MUSHROOM_SPORE de forma INSTANTÁNEA (llama ``_do_vine_toss``/``_do_mushroom_spore``
directo, sin telegraph), a diferencia de STOMP/CHARGE/VINE_SWEEP, que arman
``self._telegraph``/``self._telegraph_timer`` y sólo se resuelven cuando ese
temporizador expira dentro de ``_update_attack_state``. El bot dodger no tiene
ninguna ventana previa para leer estos dos ataques.

Este módulo describe el comportamiento DESEADO (fase GREEN todavía sin
implementar): ambos ataques pasan al mismo patrón windup -> disparo, con
constantes nuevas ``SPORE_TELEGRAPH``/``TOSS_TELEGRAPH``, y -- riesgo 2 del
dictamen -- el disparo real debe releer ``self._player_ref`` FRESCO en el
instante en que expira el telegraph, no una posición capturada al armarlo.

Todos los asserts están escritos para fallar limpio (AssertionError) contra el
código de HOY, nunca por ImportError/AttributeError: las constantes nuevas se
leen con ``getattr(bv, "...", <default>)`` porque todavía no existen.
"""
import pygame

from src.engine.core.event_bus import EventBus
from src.stages.boss_venado import boss_venado as bv
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


def _pasos_para(segundos: float) -> int:
    """Cantidad de pasos de ``DT`` para cubrir de sobra una duración dada."""
    return int(segundos / DT) + 3


# ──────────────────────────────────────────────
# 1-2 — _try_attack arma, no dispara
# ──────────────────────────────────────────────

def test_mushroom_spore_arma_telegraph_sin_disparar():
    """Hoy ``_try_attack("MUSHROOM_SPORE")`` llama ``_do_mushroom_spore`` de
    inmediato: no hay ningún windup que el bot dodger pueda leer."""
    boss, _ = make_boss()
    pr = pygame.Rect(int(boss.rect.centerx) - 60, 528, 20, 32)
    boss.set_player_ref(pr)

    boss._try_attack("MUSHROOM_SPORE")

    assert boss._telegraph == "MUSHROOM_SPORE", (
        "MUSHROOM_SPORE debe armar un telegraph visible, no disparar directo")
    assert boss._telegraph_timer > 0, "el temporizador del windup debe quedar corriendo"
    # B-040 (REGISTRO-DE-BUGS.md): desde la opción A decidida por el usuario,
    # armar el telegraph SÍ deja algo en _projectiles -- un marcador INERTE
    # (inert=True, sin daño) que satisface el contrato del profesor
    # (test_boss_encounter.py::test_every_attack_produces_something_observable,
    # que espera algo observable en este mismo frame). Lo que sigue prohibido,
    # y es lo que este assert protege de verdad, es que el ataque REAL --
    # el que sí puede dañar -- se dispare antes de tiempo.
    reales = [p for p in boss._projectiles if not p.get("inert")]
    assert reales == [], (
        "MUSHROOM_SPORE disparó un proyectil REAL al instante en vez de esperar a que expire el telegraph")


def test_toss_arma_telegraph_sin_disparar():
    """Gemelo del anterior para VINE_TOSS (hoy: ``_do_vine_toss`` directo)."""
    boss, _ = make_boss()
    pr = pygame.Rect(int(boss.rect.centerx) - 60, 528, 20, 32)
    boss.set_player_ref(pr)

    boss._try_attack("VINE_TOSS")

    assert boss._telegraph == "VINE_TOSS", (
        "VINE_TOSS debe armar un telegraph visible, no disparar directo")
    assert boss._telegraph_timer > 0, "el temporizador del windup debe quedar corriendo"
    # B-040: mismo criterio que el gemelo de MUSHROOM_SPORE arriba -- armar el
    # telegraph deja un marcador INERTE (contrato del profesor), pero el
    # proyectil REAL con daño no debe existir todavía.
    reales = [p for p in boss._projectiles if not p.get("inert")]
    assert reales == [], (
        "VINE_TOSS disparó un proyectil REAL al instante en vez de esperar a que expire el telegraph")


# ──────────────────────────────────────────────
# 3-4 — el disparo real ocurre al expirar el telegraph, no antes
# ──────────────────────────────────────────────

def test_spore_dispara_al_expirar_el_telegraph():
    """Se recorre el windup en dos tramos: un tramo que se queda CORTO de
    ``SPORE_TELEGRAPH`` (nada debe haber salido todavía) y el resto, que sí
    debe cruzar la expiración y disparar el abanico completo.

    Hoy el ataque se resuelve en el mismo instante de ``_try_attack`` -- antes
    de que corra un solo paso de ``_update_attack_state`` -- así que el primer
    tramo ya encuentra 3 esporas en vuelo y este test falla limpio."""
    boss, _ = make_boss()
    pr = pygame.Rect(int(boss.rect.centerx) - 60, 528, 20, 32)
    boss.set_player_ref(pr)

    boss._try_attack("MUSHROOM_SPORE")

    duracion = getattr(bv, "SPORE_TELEGRAPH", 0.35)
    pasos_dentro_del_windup = max(1, int(duracion / DT) - 2)
    for _ in range(pasos_dentro_del_windup):
        boss._update_attack_state(DT)

    # B-040: filtra el marcador INERTE que _try_attack ya dejó armado (el
    # contrato del profesor) -- lo que este assert vigila es que ninguna
    # espora REAL (con daño) exista todavía dentro del windup.
    esporas_antes = [p for p in boss._projectiles
                      if p["type"] == "spore" and not p.get("inert")]
    assert esporas_antes == [], (
        "las esporas salieron antes de que expirara el telegraph de MUSHROOM_SPORE")
    assert boss._telegraph == "MUSHROOM_SPORE", "el telegraph debe seguir armado dentro del windup"

    for _ in range(_pasos_para(duracion)):
        boss._update_attack_state(DT)

    esporas_despues = [p for p in boss._projectiles if p["type"] == "spore"]
    assert len(esporas_despues) == 3, "el abanico de 3 esporas nunca se disparó"
    assert boss._telegraph == "", "el telegraph debe cerrarse al disparar"


def test_toss_dispara_al_expirar_el_telegraph():
    """Gemelo del anterior para VINE_TOSS (1 proyectil de liana)."""
    boss, _ = make_boss()
    pr = pygame.Rect(int(boss.rect.centerx) - 60, 528, 20, 32)
    boss.set_player_ref(pr)

    boss._try_attack("VINE_TOSS")

    duracion = getattr(bv, "TOSS_TELEGRAPH", 0.4)
    pasos_dentro_del_windup = max(1, int(duracion / DT) - 2)
    for _ in range(pasos_dentro_del_windup):
        boss._update_attack_state(DT)

    # B-040: mismo filtro que el gemelo de MUSHROOM_SPORE arriba.
    lianas_antes = [p for p in boss._projectiles
                     if p["type"] == "vine" and not p.get("inert")]
    assert lianas_antes == [], (
        "la liana salió antes de que expirara el telegraph de VINE_TOSS")
    assert boss._telegraph == "VINE_TOSS", "el telegraph debe seguir armado dentro del windup"

    for _ in range(_pasos_para(duracion)):
        boss._update_attack_state(DT)

    lianas_despues = [p for p in boss._projectiles if p["type"] == "vine"]
    assert len(lianas_despues) == 1, "el proyectil de liana nunca se disparó"
    assert boss._telegraph == "", "el telegraph debe cerrarse al disparar"


# ──────────────────────────────────────────────
# 5-6 — el disparo relee al jugador FRESCO, no la posición capturada al armar
# ──────────────────────────────────────────────

def test_spore_relee_al_jugador_al_disparar():
    """El jugador cruza al lado opuesto DESPUÉS de armar el telegraph pero
    ANTES de que expire: el abanico debe apuntar a la posición NUEVA.

    Hoy no hay ventana entre armar y disparar (se resuelven en la misma
    llamada), así que el abanico sale apuntando a la posición VIEJA
    (izquierda) y este test falla limpio."""
    boss, _ = make_boss()
    lado_izquierdo = pygame.Rect(int(boss.rect.centerx) - 200, 528, 20, 32)
    boss.set_player_ref(lado_izquierdo)

    boss._try_attack("MUSHROOM_SPORE")

    lado_derecho = pygame.Rect(int(boss.rect.centerx) + 200, 528, 20, 32)
    boss.set_player_ref(lado_derecho)

    duracion = getattr(bv, "SPORE_TELEGRAPH", 0.35)
    for _ in range(_pasos_para(duracion)):
        boss._update_attack_state(DT)

    esporas = [p for p in boss._projectiles if p["type"] == "spore"]
    assert len(esporas) == 3, "el abanico nunca se disparó"
    espora_central = esporas[1]["vel"]
    assert espora_central.x > 0, (
        "el abanico apuntó a la posición VIEJA (izquierda) capturada al armar el "
        "telegraph, en vez de releer al jugador NUEVO (derecha) al disparar")


def test_toss_relee_al_jugador_al_disparar():
    """Gemelo del anterior para VINE_TOSS: el punto objetivo de la liana
    (extremo de la curva Bézier) debe corresponder a la posición NUEVA."""
    boss, _ = make_boss()
    lado_izquierdo = pygame.Rect(int(boss.rect.centerx) - 200, 528, 20, 32)
    boss.set_player_ref(lado_izquierdo)

    boss._try_attack("VINE_TOSS")

    lado_derecho = pygame.Rect(int(boss.rect.centerx) + 200, 528, 20, 32)
    boss.set_player_ref(lado_derecho)

    duracion = getattr(bv, "TOSS_TELEGRAPH", 0.4)
    for _ in range(_pasos_para(duracion)):
        boss._update_attack_state(DT)

    lianas = [p for p in boss._projectiles if p["type"] == "vine"]
    assert len(lianas) == 1, "la liana nunca se disparó"
    objetivo = lianas[0]["path"][-1]         # último punto de la curva == objetivo predicho
    assert abs(objetivo[0] - lado_derecho.centerx) < 40.0, (
        "la liana persiguió la posición VIEJA del jugador, capturada al armar el "
        f"telegraph (objetivo real={objetivo[0]:.1f}, esperado cerca de "
        f"{lado_derecho.centerx})")


# ──────────────────────────────────────────────
# 7 — la transición de fase cancela el telegraph pendiente (candado M-1)
# ──────────────────────────────────────────────

def test_la_transicion_cancela_el_telegraph_de_spore():
    """``_cancelar_ataques_en_vuelo`` (candado M-1: FINDINGS.md, paquete H-18)
    debe poder abortar un windup de MUSHROOM_SPORE que todavía no disparó.

    Hoy ``_try_attack`` ya disparó el abanico ANTES de que el test alcance a
    llamar a la cancelación -- ``_cancelar_ataques_en_vuelo`` no vacía
    ``_projectiles`` (esa lista sólo contiene proyectiles ya en vuelo, cuya
    posición se sigue actualizando cuadro a cuadro; no es lo que este candado
    protege) -- así que la aserción de cero proyectiles falla limpio."""
    boss, _ = make_boss()
    pr = pygame.Rect(int(boss.rect.centerx) - 60, 528, 20, 32)
    boss.set_player_ref(pr)

    boss._try_attack("MUSHROOM_SPORE")
    boss._cancelar_ataques_en_vuelo()

    assert boss._telegraph == ""
    assert boss._telegraph_timer == 0.0
    assert boss._projectiles == [], (
        "una espora se disparó pese a cancelarse el telegraph antes de expirar")


# ──────────────────────────────────────────────
# 8 — aviso visual distinguible en _draw_telegraphs
# ──────────────────────────────────────────────

def test_el_aviso_visual_se_dibuja_para_los_ataques_nuevos():
    """``_draw_telegraphs`` (boss_venado.py ~L1205-1226) hoy sólo ramifica
    sobre STOMP/CHARGE/VINE_SWEEP -- MUSHROOM_SPORE y VINE_TOSS caen en
    ningún ``if``/``elif`` y no pintan nada, así que una superficie con el
    telegraph armado es idéntica, píxel a píxel, a una sin telegraph."""
    boss, _ = make_boss()
    offset = pygame.Vector2(int(boss.rect.centerx) - 100, int(boss.rect.centery) - 100)

    for patron in ("MUSHROOM_SPORE", "VINE_TOSS"):
        boss._telegraph = ""
        sin_aviso = pygame.Surface((200, 200))
        sin_aviso.fill((10, 10, 10))
        boss._draw_telegraphs(sin_aviso, offset)

        boss._telegraph = patron
        con_aviso = pygame.Surface((200, 200))
        con_aviso.fill((10, 10, 10))
        boss._draw_telegraphs(con_aviso, offset)

        assert pygame.image.tobytes(sin_aviso, "RGB") != pygame.image.tobytes(con_aviso, "RGB"), (
            f"_draw_telegraphs no dibuja ningún aviso distinguible para {patron}")


# ──────────────────────────────────────────────
# 9 — constantes de duración del windup
# ──────────────────────────────────────────────

def test_constantes_de_telegraph_nuevas():
    """``SPORE_TELEGRAPH``/``TOSS_TELEGRAPH`` todavía no existen en el módulo:
    ``getattr`` con default 0.0 evita un ImportError/AttributeError y deja el
    fallo como una comparación numérica limpia."""
    assert getattr(bv, "SPORE_TELEGRAPH", 0.0) >= 0.3, (
        "SPORE_TELEGRAPH debe existir y durar al menos 0.3s de aviso")
    assert getattr(bv, "TOSS_TELEGRAPH", 0.0) >= 0.3, (
        "TOSS_TELEGRAPH debe existir y durar al menos 0.3s de aviso")
