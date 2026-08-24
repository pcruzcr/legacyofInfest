from typing import Any

import pygame
import pytest

from src.engine.core import settings
from src.engine.core.event_bus import EventBus
from src.engine.core.events import Events
from src.framework.entities.player import Player, PlayerState


def test_initial_health() -> None:
    player = Player(pygame.Vector2(50.0, 0.0))
    assert player.current_health == settings.PLAYER_MAX_HEALTH


# AUD-308 bis — `heal` no lo defendía nadie: una mutación `Mult → Div` en
# `health + amount * heal_mult` pasaba la suite entera.
def test_heal_restaura_salud() -> None:
    player = Player(pygame.Vector2(50.0, 0.0))
    player.apply_damage(2.0, (50.0, 0.0))
    player.heal(1.0)
    assert player.current_health == settings.PLAYER_MAX_HEALTH - 1.0


def test_heal_no_pasa_de_la_vida_maxima() -> None:
    player = Player(pygame.Vector2(50.0, 0.0))
    player.apply_damage(0.5, (50.0, 0.0))
    player.heal(99.0)
    assert player.current_health == player.max_health


# AUD-309 — la fórmula de vida máxima (base + reliquias + árbol, con tope)
# no la defendía nadie: una mutación que restara los bonus pasaba la suite.
def test_max_health_suma_los_bonus() -> None:
    from src.engine.core import skill_tree

    player = Player(pygame.Vector2(50.0, 0.0))
    player._bonus_max_health = 2.0
    player._bonus_arbol_salud = 1.0
    assert player.max_health == settings.PLAYER_MAX_HEALTH + 3.0
    assert player.max_health <= skill_tree.CORAZONES_MAXIMOS


def test_max_health_respeta_el_tope() -> None:
    from src.engine.core import skill_tree

    player = Player(pygame.Vector2(50.0, 0.0))
    player._bonus_max_health = 20.0
    player._bonus_arbol_salud = 20.0
    assert player.max_health == skill_tree.CORAZONES_MAXIMOS


def test_damage_reduces_health() -> None:
    player = Player(pygame.Vector2(50.0, 0.0))
    initial = player.current_health
    player.apply_damage(0.5, (50.0, 0.0))
    assert player.current_health == pytest.approx(initial - 0.5)


def test_damage_clamped_at_zero() -> None:
    player = Player(pygame.Vector2(50.0, 0.0))
    player.apply_damage(100.0, (50.0, 0.0))
    assert player.current_health == 0.0


def test_damage_clamped_at_zero_exact_max() -> None:
    player = Player(pygame.Vector2(50.0, 0.0))
    player.apply_damage(settings.PLAYER_MAX_HEALTH, (50.0, 0.0))
    assert player.current_health == 0.0


def test_invincibility_blocks_repeat_damage() -> None:
    player = Player(pygame.Vector2(50.0, 0.0))
    player.apply_damage(0.5, (50.0, 0.0))
    health_after_first = player.current_health
    player.apply_damage(0.5, (50.0, 0.0))
    assert player.current_health == pytest.approx(health_after_first)


def test_invincibility_expires() -> None:
    player = Player(pygame.Vector2(50.0, 0.0))
    player.apply_damage(0.5, (50.0, 0.0))
    health_after_first = player.current_health
    player._invincibility_timer = 0.0
    player.apply_damage(0.5, (50.0, 0.0))
    assert player.current_health == pytest.approx(health_after_first - 0.5)


def test_zero_damage_is_noop() -> None:
    player = Player(pygame.Vector2(50.0, 0.0))
    initial = player.current_health
    player.apply_damage(0.0, (50.0, 0.0))
    assert player.current_health == pytest.approx(initial)


def test_damage_noop_when_invincible() -> None:
    player = Player(pygame.Vector2(50.0, 0.0))
    player._invincibility_timer = 999.0
    player.apply_damage(999.0, (50.0, 0.0))
    assert player.current_health == settings.PLAYER_MAX_HEALTH


def test_damage_noop_when_dying() -> None:
    player = Player(pygame.Vector2(50.0, 0.0))
    player.apply_damage(settings.PLAYER_MAX_HEALTH, (50.0, 0.0))
    assert player.state == PlayerState.DYING
    player.apply_damage(999.0, (50.0, 0.0))
    assert player.current_health == 0.0


def test_knockback_applied_on_damage() -> None:
    player = Player(pygame.Vector2(50.0, 0.0))
    player.apply_damage(0.5, (100.0, 0.0))
    assert player.velocity.x < 0
    assert player.velocity.y < 0


def test_knockback_direction_away_from_source() -> None:
    player = Player(pygame.Vector2(50.0, 0.0))
    player.apply_damage(0.5, (0.0, 0.0))
    assert player.velocity.x > 0
    assert player.velocity.y < 0


def test_knockback_magnitude() -> None:
    player = Player(pygame.Vector2(50.0, 0.0))
    player.apply_damage(0.5, (100.0, 0.0))
    assert player.velocity.x == pytest.approx(-150.0)
    assert player.velocity.y == pytest.approx(-200.0)


def test_damage_transitions_to_hurt_state() -> None:
    player = Player(pygame.Vector2(50.0, 0.0))
    player.apply_damage(0.5, (50.0, 0.0))
    assert player.state == PlayerState.HURT


def test_damage_transitions_to_dying_state_at_zero() -> None:
    player = Player(pygame.Vector2(50.0, 0.0))
    player.apply_damage(settings.PLAYER_MAX_HEALTH, (50.0, 0.0))
    assert player.state == PlayerState.DYING


def test_set_health_clamps_values() -> None:
    player = Player(pygame.Vector2(50.0, 0.0))
    player.set_health(999.0)
    assert player.current_health == settings.PLAYER_MAX_HEALTH
    player.set_health(-10.0)
    assert player.current_health == 0.0


def test_set_health_normal_value() -> None:
    player = Player(pygame.Vector2(50.0, 0.0))
    player.set_health(3.0)
    assert player.current_health == 3.0


def test_player_damaged_event_emitted() -> None:
    bus = EventBus()
    # AUD-019: the bus is injected, not installed as a process-wide default.
    player = Player(pygame.Vector2(50.0, 0.0), event_bus=bus)
    received: dict[str, Any] = {}
    def on_damaged(**data: Any) -> None:
        nonlocal received
        received = dict(data)
    bus.subscribe(Events.PLAYER_DAMAGED, on_damaged)
    player.apply_damage(1.5, (100.0, 0.0))
    bus.dispatch()
    assert received.get("amount") == pytest.approx(1.5)
    assert received.get("source") == (100.0, 0.0)


def test_player_died_event_on_zero_health() -> None:
    bus = EventBus()
    # AUD-019: the bus is injected, not installed as a process-wide default.
    player = Player(pygame.Vector2(50.0, 0.0), event_bus=bus)
    died = False
    def on_died() -> None:
        nonlocal died
        died = True
    bus.subscribe(Events.PLAYER_DIED, on_died)
    player.apply_damage(settings.PLAYER_MAX_HEALTH, (50.0, 0.0))
    bus.dispatch()
    assert died


def test_sfx_player_hurt_emitted_on_damage() -> None:
    bus = EventBus()
    # AUD-019: the bus is injected, not installed as a process-wide default.
    player = Player(pygame.Vector2(50.0, 0.0), event_bus=bus)
    hurt = False
    def on_hurt() -> None:
        nonlocal hurt
        hurt = True
    bus.subscribe(Events.SFX_PLAYER_HURT, on_hurt)
    player.apply_damage(0.5, (50.0, 0.0))
    bus.dispatch()
    assert hurt


def test_sfx_player_die_emitted_on_death() -> None:
    bus = EventBus()
    # AUD-019: the bus is injected, not installed as a process-wide default.
    player = Player(pygame.Vector2(50.0, 0.0), event_bus=bus)
    died = False
    def on_die() -> None:
        nonlocal died
        died = True
    bus.subscribe(Events.SFX_PLAYER_DIE, on_die)
    player.apply_damage(settings.PLAYER_MAX_HEALTH, (50.0, 0.0))
    bus.dispatch()
    assert died


def test_invincibility_blocks_event_emission() -> None:
    bus = EventBus()
    # AUD-019: the bus is injected, not installed as a process-wide default.
    player = Player(pygame.Vector2(50.0, 0.0), event_bus=bus)
    count = 0
    def on_damaged(**data: Any) -> None:
        nonlocal count
        count += 1
    bus.subscribe(Events.PLAYER_DAMAGED, on_damaged)
    player.apply_damage(0.5, (50.0, 0.0))
    player.apply_damage(0.5, (50.0, 0.0))
    bus.dispatch()
    assert count == 1


# ── GAP-033: el módulo del jugador estaba mal defendido ──────────────
#
# Las tres familias de mutaciones que sobrevivían —`and/or` de la guarda de
# golpe activo, `* → /` del combo, `* → /` del `heal` con dificultad no
# trivial— quedan aquí cerradas. AUD-308/309 ya blindaron coyote y vida
# máxima; esto blinda el daño ofensivo y la curación que la dificultad
# regula, donde la mutación es indistinguible bajo la config por defecto.


def _en_estado(state_type: Any, player: Player) -> None:
    """Pone el jugador en el estado de ataque dado, haciéndolo entrar."""
    player._state_instance = state_type()
    player._state_instance.enter(player)


def test_ataque_corto_sin_golpe_activo_no_hace_dano() -> None:
    """La guarda es `and`, no `or`: atacar con la caja apagada duele 0."""
    from src.framework.entities.states import ShortAttackState
    player = Player(pygame.Vector2(50.0, 0.0))
    _en_estado(ShortAttackState, player)
    player._active_hitbox = None
    assert player.current_attack_damage == 0.0


def test_ataque_largo_sin_golpe_activo_no_hace_dano() -> None:
    from src.framework.entities.states import LongAttackState
    player = Player(pygame.Vector2(50.0, 0.0))
    _en_estado(LongAttackState, player)
    player._active_hitbox = None
    assert player.current_attack_damage == 0.0


def test_el_golpe_corto_activo_hace_su_dano_base() -> None:
    """Con el golpe conectado, el daño corto es 0,5 - la mutación `*`→`/`
    que dejaría la multiplicación por 0,5 dividida no puede sobrevivir a
    esta comprobación exacta."""
    from src.framework.entities.states import ShortAttackState
    player = Player(pygame.Vector2(50.0, 0.0))
    _en_estado(ShortAttackState, player)
    player._active_hitbox = pygame.Rect(60, 0, 10, 10)
    assert player.current_attack_damage == pytest.approx(0.5)


def test_el_golpe_largo_activo_hace_el_doble_que_el_corto() -> None:
    from src.framework.entities.states import LongAttackState
    player = Player(pygame.Vector2(50.0, 0.0))
    _en_estado(LongAttackState, player)
    player._active_hitbox = pygame.Rect(60, 0, 10, 10)
    assert player.current_attack_damage == pytest.approx(1.0)


def test_el_combo_multiplica_el_dano_base() -> None:
    """`COMBO_DAMAGE_MULT` se multiplica: una mutación `Mult→Div` dividiría
    el daño en vez de escalarlo.

    Con dificultad HARD (`outgoing = 0.75`) y un bonus de daño de 1,0, cada
    uno de los tres `*` de la línea 526 queda con un resultado distinto de
    la mutación: `1.125` frente a `0.5`, `2.0` y `0.28125`.
    """
    from src.engine.core.difficulty import Difficulty, set_difficulty
    from src.framework.entities.states import ShortAttackState
    set_difficulty(Difficulty.HARD)
    try:
        player = Player(pygame.Vector2(50.0, 0.0))
        player._bonus_damage = 1.0
        _en_estado(ShortAttackState, player)
        player._active_hitbox = pygame.Rect(60, 0, 10, 10)
        player.combo_count = 2
        player.combo_active = True
        idx = min(1, len(settings.COMBO_DAMAGE_MULT) - 1)
        assert player.current_attack_damage == pytest.approx(
            0.5 * settings.COMBO_DAMAGE_MULT[idx] * 0.75 * 2.0)
    finally:
        set_difficulty(Difficulty.NORMAL)


def test_el_dano_sin_combo_escala_los_multiplicadores() -> None:
    """El `*` de la línea 527 (daño sin combo por `outgoing * dmg_mult`)
    también debe ser verificable: con HARD y bonus de daño, `*→/` da
    `1.333` y `0.1875`, nunca `0.75`."""
    from src.engine.core.difficulty import Difficulty, set_difficulty
    from src.framework.entities.states import ShortAttackState
    set_difficulty(Difficulty.HARD)
    try:
        player = Player(pygame.Vector2(50.0, 0.0))
        player._bonus_damage = 1.0
        _en_estado(ShortAttackState, player)
        player._active_hitbox = pygame.Rect(60, 0, 10, 10)
        assert player.current_attack_damage == pytest.approx(0.5 * 0.75 * 2.0)
    finally:
        set_difficulty(Difficulty.NORMAL)


def test_heal_aplica_el_multiplicador_de_dificultad() -> None:
    """`heal_mult` != 1.0 hace verificable la mutación `*`→`/` de `heal`.

    Con dificultad HARD el multiplicador es 0.5; curar 1,0 debe añadir 0,5.
    Antes, con el 1,0 por defecto, ambas operaciones eran indistinguibles y
    el defecto nadaba en la suite.
    """
    from src.engine.core.difficulty import Difficulty, set_difficulty
    set_difficulty(Difficulty.HARD)
    try:
        player = Player(pygame.Vector2(50.0, 0.0))
        player.apply_damage(2.0, (50.0, 0.0))
        player.heal(1.0)
        # HARD: incoming 1.5 → quedan 2,0; heal_mult 0.5 → +0.5.
        assert player.current_health == pytest.approx(2.5)
    finally:
        set_difficulty(Difficulty.NORMAL)


def test_consumir_el_golpe_vacia_la_caja_activa() -> None:
    """`consume_hitbox()` es lo único que impide el multi-golpe por
    fotograma: `active_hitbox` debe volver a `None` aunque la caja siga
    dibujada en el estado de ataque (guarda `_hitbox_consumed`)."""
    from src.framework.entities.states import ShortAttackState
    player = Player(pygame.Vector2(50.0, 0.0))
    _en_estado(ShortAttackState, player)
    player._active_hitbox = pygame.Rect(60, 0, 10, 10)
    assert player.active_hitbox is not None
    player.consume_hitbox()
    assert player.active_hitbox is None


def test_la_guardia_de_consumido_aborta_la_caja_pintada() -> None:
    """Aísla el bit `_hitbox_consumed`: aunque la caja siga en su sitio, la
    guardia del flag es la que decide. La mutación `True → False` haría
    que `active_hitbox` devolviera la caja muerta y el multi-golpe volvería
    a existir."""
    player = Player(pygame.Vector2(50.0, 0.0))
    player._active_hitbox = pygame.Rect(60, 0, 10, 10)
    player._hitbox_consumed = True
    assert player.active_hitbox is None
