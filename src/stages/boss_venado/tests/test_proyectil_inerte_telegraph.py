"""Candado B-040 (REGISTRO-DE-BUGS.md): proyectil INERTE al armar el telegraph
de VINE_TOSS/MUSHROOM_SPORE.

Contexto
--------
El contrato del profesor (``test_boss_encounter.py::
test_every_attack_produces_something_observable``, ``game/tests/``) llama
``_try_attack("VINE_TOSS")``/``_try_attack("MUSHROOM_SPORE")`` y espera
encontrar algo en ``self._projectiles`` en el MISMO fotograma de la llamada.
Desde H-23 (campaña de fairness, ``TOSS_TELEGRAPH``/``SPORE_TELEGRAPH``)
ambos ataques telegrafían antes de disparar y el proyectil real sólo nace al
EXPIRAR el windup (``_update_attack_state``), lo que dejaba ese contrato en
rojo -- documentado como B-040. El usuario decidió la opción A: un proyectil
INERTE (sin daño, sin colisión, sin dibujo, marcado ``inert=True`` sin
ambigüedad) que se arma junto con el telegraph y se retira al resolverse
-- fuego real o cancelación -- conservando el windup de H-23 intacto.

Este módulo cubre el contrato en la suite propia y las tres propiedades que
lo hacen seguro: el inerte nunca daña, nunca se dibuja y su vida nunca excede
la del telegraph que lo armó. La co-calibración de los bots (que el inerte no
se lea como amenaza) vive en ``playtest\\tests\\test_b040_proyectil_inerte.py``
-- este módulo no puede importar ``playtest`` (su ``conftest.py`` fija
``sys.path``/``cwd`` a la raíz del motor, no a la del lab).
"""
import pygame

from src.stages.boss_venado import boss_venado as bv
from src.stages.boss_venado.boss_venado import BossVenado

DT = 1.0 / 60.0


def make_boss():
    """Mismo constructor que el resto de la suite: spawn dentro de la arena."""
    return BossVenado(pygame.Vector2(3168, 240))


def _pasos_para(segundos: float) -> int:
    """Cantidad de pasos de ``DT`` para cubrir de sobra una duración dada."""
    return int(segundos / DT) + 3


class _JugadorFalso:
    """Jugador duck-typed: sólo lo que ``_check_player_contact`` toca
    (mismo doble que ``test_boss_venado.py::FakePlayer``)."""

    def __init__(self, rect: pygame.Rect) -> None:
        self.rect = rect
        self.hurtbox = rect
        self.velocity = pygame.Vector2(0.0, 0.0)
        self.golpes: list[float] = []

    def apply_damage(self, amount, source_position, knockback_force=150.0) -> None:
        self.golpes.append(amount)


# ──────────────────────────────────────────────
# 1-2 — el contrato del profesor: algo observable en el MISMO frame
# ──────────────────────────────────────────────

def test_vine_toss_deja_un_proyectil_inerte_en_el_mismo_frame():
    """Espejo local de
    ``test_boss_encounter.py::test_every_attack_produces_something_observable``
    para VINE_TOSS -- si esto se rompe, ese contrato del profesor se rompe
    con él."""
    boss = make_boss()
    boss.set_player_ref(pygame.Rect(220, 180, 16, 24))

    boss._try_attack("VINE_TOSS")

    assert len(boss._projectiles) == 1, "VINE_TOSS debe dejar un proyectil de inmediato"
    proj = boss._projectiles[0]
    assert proj["type"] == "vine"
    assert proj.get("inert") is True, "el proyectil inmediato debe marcarse inerte sin ambigüedad"
    assert proj.get("damage", 0.0) == 0.0, "el inerte no debe llevar daño"


def test_mushroom_spore_deja_tres_proyectiles_inertes_en_el_mismo_frame():
    """Gemelo para MUSHROOM_SPORE: el contrato del profesor exige 3 esporas."""
    boss = make_boss()
    boss.set_player_ref(pygame.Rect(220, 180, 16, 24))

    boss._try_attack("MUSHROOM_SPORE")

    esporas = [p for p in boss._projectiles if p["type"] == "spore"]
    assert len(esporas) == 3, "MUSHROOM_SPORE debe dejar 3 marcadores de inmediato"
    assert all(p.get("inert") is True for p in esporas)
    assert all(p.get("damage", 0.0) == 0.0 for p in esporas)


# ──────────────────────────────────────────────
# 3-4 — el inerte jamás daña, aunque el jugador esté encima
# ──────────────────────────────────────────────

def test_el_inerte_de_vine_toss_nunca_hace_dano():
    boss = make_boss()
    jugador = _JugadorFalso(pygame.Rect(boss.rect.centerx, boss.rect.centery, 16, 24))
    boss.set_player_ref(jugador.rect)

    boss._try_attack("VINE_TOSS")
    # el jugador se superpone exactamente al jefe: si el inerte tuviera
    # colisión real, esto lo demostraría en el acto.
    for _ in range(10):
        boss._check_player_contact(jugador)

    assert jugador.golpes == [], (
        f"el proyectil inerte de VINE_TOSS hizo daño: {jugador.golpes}")


def test_el_inerte_de_mushroom_spore_nunca_hace_dano():
    boss = make_boss()
    jugador = _JugadorFalso(pygame.Rect(boss.rect.centerx, boss.rect.centery, 16, 24))
    boss.set_player_ref(jugador.rect)

    boss._try_attack("MUSHROOM_SPORE")
    for _ in range(10):
        boss._check_player_contact(jugador)

    assert jugador.golpes == [], (
        f"algún proyectil inerte de MUSHROOM_SPORE hizo daño: {jugador.golpes}")


# ──────────────────────────────────────────────
# 5 — el inerte es invisible: no agrega ruido visual nuevo
# ──────────────────────────────────────────────

def test_el_inerte_no_agrega_ruido_visual_a_draw_projectiles():
    """``_draw_projectiles`` no debe pintar nada por el marcador inerte -- el
    aviso visual del ataque ya lo cubre ``_draw_telegraphs``
    (``test_avisos_de_ataque.py`` #8); esto sólo prueba que no se agrega
    ADEMÁS un punto nuevo por el inerte."""
    boss = make_boss()
    boss.set_player_ref(pygame.Rect(220, 180, 16, 24))
    offset = pygame.Vector2(int(boss.rect.centerx) - 100, int(boss.rect.centery) - 100)

    sin_ataque = pygame.Surface((200, 200))
    sin_ataque.fill((10, 10, 10))
    boss._draw_projectiles(sin_ataque, offset)

    boss._try_attack("VINE_TOSS")
    con_inerte = pygame.Surface((200, 200))
    con_inerte.fill((10, 10, 10))
    boss._draw_projectiles(con_inerte, offset)

    assert pygame.image.tobytes(sin_ataque, "RGB") == pygame.image.tobytes(con_inerte, "RGB"), (
        "el marcador inerte de VINE_TOSS pintó algo en _draw_projectiles")


# ──────────────────────────────────────────────
# 6-7 — vida = duración del telegraph: se retira al disparar el real
# ──────────────────────────────────────────────

def test_el_inerte_de_vine_toss_se_retira_al_disparar_el_real():
    boss = make_boss()
    pr = pygame.Rect(int(boss.rect.centerx) - 60, 528, 20, 32)
    boss.set_player_ref(pr)

    boss._try_attack("VINE_TOSS")
    assert any(p.get("inert") for p in boss._projectiles)

    for _ in range(_pasos_para(bv.TOSS_TELEGRAPH)):
        boss._update_attack_state(DT)

    assert not any(p.get("inert") for p in boss._projectiles), (
        "el marcador inerte de VINE_TOSS sobrevivió al disparo real")
    lianas = [p for p in boss._projectiles if p["type"] == "vine"]
    assert len(lianas) == 1 and lianas[0].get("inert") is not True


def test_el_inerte_de_mushroom_spore_se_retira_al_disparar_el_real():
    boss = make_boss()
    pr = pygame.Rect(int(boss.rect.centerx) - 60, 528, 20, 32)
    boss.set_player_ref(pr)

    boss._try_attack("MUSHROOM_SPORE")
    assert any(p.get("inert") for p in boss._projectiles)

    for _ in range(_pasos_para(bv.SPORE_TELEGRAPH)):
        boss._update_attack_state(DT)

    assert not any(p.get("inert") for p in boss._projectiles), (
        "algún marcador inerte de MUSHROOM_SPORE sobrevivió al disparo real")
    esporas = [p for p in boss._projectiles if p["type"] == "spore"]
    assert len(esporas) == 3 and all(p.get("inert") is not True for p in esporas)


# ──────────────────────────────────────────────
# 8 — vida = duración del telegraph: se retira también si se cancela
# ──────────────────────────────────────────────

def test_el_inerte_de_vine_toss_se_retira_al_cancelar_el_telegraph():
    """Gemelo de
    ``test_avisos_de_ataque.py::test_la_transicion_cancela_el_telegraph_de_spore``,
    para VINE_TOSS (ese candado sólo cubre MUSHROOM_SPORE)."""
    boss = make_boss()
    pr = pygame.Rect(int(boss.rect.centerx) - 60, 528, 20, 32)
    boss.set_player_ref(pr)

    boss._try_attack("VINE_TOSS")
    boss._cancelar_ataques_en_vuelo()

    assert boss._telegraph == ""
    assert boss._projectiles == [], (
        "el marcador inerte de VINE_TOSS sobrevivió a la cancelación del telegraph")


# ──────────────────────────────────────────────
# 9-10 — el marcador no adelanta el golpe real (el windup de H-23 sigue intacto)
# ──────────────────────────────────────────────

def test_el_marcador_inerte_no_adelanta_el_golpe_real_de_toss():
    boss = make_boss()
    pr = pygame.Rect(int(boss.rect.centerx) - 60, 528, 20, 32)
    boss.set_player_ref(pr)

    boss._try_attack("VINE_TOSS")

    pasos_dentro_del_windup = max(1, int(bv.TOSS_TELEGRAPH / DT) - 2)
    for _ in range(pasos_dentro_del_windup):
        boss._update_attack_state(DT)

    reales = [p for p in boss._projectiles if not p.get("inert")]
    assert reales == [], "una liana REAL salió antes de que expirara el telegraph"
    assert boss._telegraph == "VINE_TOSS", "el telegraph debe seguir armado dentro del windup"


def test_el_inerte_de_mushroom_spore_no_revienta_update_vfx():
    """Regresión (detectada por la suite completa del arnés, no por los
    candados de este módulo):
    ``_update_vfx`` (rastro de polen, ~L1054) recorre ``_projectiles``
    buscando esporas VIVAS y leía ``proj["pos"]`` sin comprobar si el
    marcador era inerte -- disparaba ``KeyError: 'pos'`` cada 5 fotogramas
    (``cada_n_frames(self._frames_vfx, 5)``) mientras el telegraph seguía
    armado. Ninguno de los candados de arriba lo atrapó porque ninguno
    llama a ``boss.update()`` completo (que sí ejecuta ``_update_vfx``) con
    el telegraph todavía armado -- lo encontró
    ``playtest/tests/test_bots.py::test_el_dodger_esquiva_oleadas_reales_en_fase_2``,
    vía la simulación real de 130 fotogramas que arma ``session.reset()``
    antes de cada test del arnés."""
    boss = make_boss()
    pr = pygame.Rect(int(boss.rect.centerx) - 60, 528, 20, 32)
    boss.set_player_ref(pr)

    boss._try_attack("MUSHROOM_SPORE")
    # SPORE_TELEGRAPH (~0.35s, ~21 fotogramas) es de sobra para que 5
    # llamadas a update() toquen la cadencia -- el telegraph sigue armado
    # todo ese tramo.
    for _ in range(5):
        boss.update(DT)   # no debe reventar con KeyError: 'pos'

    assert boss._telegraph == "MUSHROOM_SPORE", "el telegraph debía seguir armado a los 5 fotogramas"


def test_el_marcador_inerte_no_adelanta_el_golpe_real_de_spore():
    boss = make_boss()
    pr = pygame.Rect(int(boss.rect.centerx) - 60, 528, 20, 32)
    boss.set_player_ref(pr)

    boss._try_attack("MUSHROOM_SPORE")

    pasos_dentro_del_windup = max(1, int(bv.SPORE_TELEGRAPH / DT) - 2)
    for _ in range(pasos_dentro_del_windup):
        boss._update_attack_state(DT)

    reales = [p for p in boss._projectiles if not p.get("inert")]
    assert reales == [], "una espora REAL salió antes de que expirara el telegraph"
    assert boss._telegraph == "MUSHROOM_SPORE", "el telegraph debe seguir armado dentro del windup"
