"""
Module: test_hud
System: tests
Description: Tests for HUD: timer display, event-driven health updates.

AUD-535 — `TestHeartSlotState` (`_heart_slot_state`) se retiró de aquí:
la vida dejó de ser una fila de corazones en ranuras discretas y pasó a
ser una barra continua (`HUD._draw_barra_de_vida`), así que la función
que traducía "cuánta vida le queda a la ranura N" ya no tiene ranuras
que traducir. Ver `tests/test_el_barra_de_vida_reemplaza_corazones.py`
para las pruebas de la barra nueva.
"""
from __future__ import annotations

import pygame
import pytest

from src.engine.core import settings
from src.engine.core.event_bus import EventBus
from src.engine.ui.hud import HUD


@pytest.fixture(autouse=True)
def _init_pygame() -> None:
    if not pygame.get_init():
        pygame.init()


class TestHUD:
    def test_initial_health(self, event_bus: EventBus) -> None:
        hud = HUD(event_bus)
        assert hud._health == settings.PLAYER_MAX_HEALTH

    def test_damage_event(self, event_bus: EventBus) -> None:
        hud = HUD(event_bus)
        event_bus.emit("PLAYER_DAMAGED", amount=1.0, source=(0, 0))
        event_bus.dispatch()
        assert hud._health == settings.PLAYER_MAX_HEALTH - 1.0

    def test_heal_event(self, event_bus: EventBus) -> None:
        hud = HUD(event_bus)
        event_bus.emit("PLAYER_DAMAGED", amount=3.0, source=(0, 0))
        event_bus.dispatch()
        event_bus.emit("PLAYER_HEALED", amount=1.0)
        event_bus.dispatch()
        assert hud._health == settings.PLAYER_MAX_HEALTH - 2.0

    def test_damage_below_zero(self, event_bus: EventBus) -> None:
        hud = HUD(event_bus)
        event_bus.emit("PLAYER_DAMAGED", amount=100.0, source=(0, 0))
        event_bus.dispatch()
        assert hud._health == 0.0

    def test_heal_above_max(self, event_bus: EventBus) -> None:
        hud = HUD(event_bus)
        event_bus.emit("PLAYER_HEALED", amount=100.0)
        event_bus.dispatch()
        assert hud._health == settings.PLAYER_MAX_HEALTH

    def test_timer_starts_at_zero(self, event_bus: EventBus) -> None:
        hud = HUD(event_bus)
        hud.start_timer()
        assert hud.current_time == 0.0

    def test_timer_increases(self, event_bus: EventBus) -> None:
        hud = HUD(event_bus)
        hud.start_timer()
        hud.update(1.0)
        assert hud.current_time == pytest.approx(1.0)

    def test_draw_does_not_crash(self, event_bus: EventBus) -> None:
        """AUD-451 — la superficie y el punto salen del HUD, no de un 320×224.

        Antes se pintaba sobre una superficie de 320×224 y se miraba el píxel
        (3, 3), que caía dentro del marco del retrato. La maqueta ya no está
        escrita para esa pantalla: se escala a la resolución interna, así que
        el retrato empieza en (5, 5) y en una superficie de 320 de ancho ni
        siquiera cabría el cronómetro.
        """
        from src.engine.core import settings

        hud = HUD(event_bus)
        surface = pygame.Surface(
            (settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT))
        hud.draw(surface)
        retrato = hud.regiones()["retrato"]
        assert surface.get_at(retrato.center)[:3] != (0, 0, 0)


class TestHUDDestroy:
    def test_destroy_removes_subscriptions(self, event_bus: EventBus) -> None:
        hud = HUD(event_bus)
        before = event_bus.subscriber_count()
        hud.destroy()
        after = event_bus.subscriber_count()
        assert after == before - 6

    def test_destroy_is_idempotent(self, event_bus: EventBus) -> None:
        hud = HUD(event_bus)
        hud.destroy()
        count_after_first = event_bus.subscriber_count()
        hud.destroy()
        count_after_second = event_bus.subscriber_count()
        assert count_after_second == count_after_first

    def test_destroyed_hud_ignores_events(self, event_bus: EventBus) -> None:
        hud = HUD(event_bus)
        initial_health = hud._health
        hud.destroy()
        event_bus.emit("PLAYER_DAMAGED", amount=1.0, source=(0, 0))
        event_bus.dispatch()
        assert hud._health == initial_health
