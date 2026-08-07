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
