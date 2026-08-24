"""AUD-439 — los corazones que el jugador se ganaba no existían para el juego.

Lo medido
---------
`Player.max_health` suma la base, las reliquias y el árbol, con tope de diez
(AUD-293). Pero tres sitios seguían leyendo la **constante** `PLAYER_MAX_HEALTH`:

* `HUD.__init__` fija `_max_health` una vez y no hay forma de cambiarlo, así
  que el marcador dibuja cinco corazones pase lo que pase.
* `ProgressionSystem.process_checkpoints` cura hasta la constante, así que un
  jugador mejorado nunca se recupera del todo en un punto de control.
* El guardado anota `max_health=PLAYER_MAX_HEALTH`, y al recargar la partida
  el máximo declarado es el de fábrica.

Medido con el equipo completo: `max_health` = 10 y el HUD dibujaba 5.

Por qué importa más de lo que parece
------------------------------------
La tienda vende un casco con `max_hp_bonus` por 40 monedas. Comprarlo no
producía ningún cambio observable: ni un corazón nuevo en pantalla, ni más
vida al tocar un checkpoint. Desde el asiento del jugador eso no es un fallo
de interfaz, es una compra que no hace nada.
"""
from __future__ import annotations

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame
import pytest

from src.engine.core import settings
from src.engine.core.event_bus import EventBus
from src.engine.ui.hud import HUD


@pytest.fixture(scope="module")
def _video():
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT))
    yield


@pytest.fixture
def jugador(_video):
    from src.framework.entities.player import Player

    return Player(pygame.Vector2(0.0, 0.0))


# ── el marcador dibuja los corazones que hay ──────────────────────


def test_el_hud_dibuja_los_corazones_que_el_jugador_tiene(_video) -> None:
    hud = HUD(EventBus())
    assert hud.ranuras_de_corazon == int(settings.PLAYER_MAX_HEALTH)

    hud.set_salud_maxima(10.0)

    assert hud.ranuras_de_corazon == 10, (
        "el marcador sigue dibujando los corazones de fábrica: los que el "
        "jugador se ha ganado no aparecen"
    )


def test_el_maximo_del_hud_sigue_al_jugador(jugador, _video) -> None:
    """La ruta real: lo que el escenario empuja cada fotograma."""
    hud = HUD(EventBus())
    jugador._bonus_max_health = 2.0

    hud.set_salud_maxima(jugador.max_health)

    assert hud.ranuras_de_corazon == 7


def test_bajar_el_maximo_no_deja_la_vida_por_encima(_video) -> None:
    """Si el máximo baja —se quita una reliquia—, la vida no puede quedarse
    fuera del marcador: se verían corazones que no existen."""
    hud = HUD(EventBus())
    hud.set_salud_maxima(10.0)
    hud._health = 9.0

    hud.set_salud_maxima(5.0)

    assert hud.ranuras_de_corazon == 5
    assert hud._health <= 5.0


def test_el_hud_aguanta_un_maximo_absurdo(_video) -> None:
    """Un valor imposible no puede tumbar el fotograma ni pintar mil corazones.

    `max_health` sale de sumar bonificaciones, y una partida editada a mano
    puede traer cualquier cosa.
    """
    hud = HUD(EventBus())
    hud.set_salud_maxima(0.0)
    assert hud.ranuras_de_corazon >= 1
    hud.set_salud_maxima(-3.0)
    assert hud.ranuras_de_corazon >= 1


# ── el checkpoint cura hasta el máximo real ───────────────────────


def test_el_checkpoint_cura_hasta_el_maximo_del_jugador(jugador, _video) -> None:
    """El defecto estaba aquí, no en `Player.heal`.

    `Player.heal` ya respetaba `max_health`; quien se equivocaba era
    `ProgressionSystem`, que calculaba cuánto curar contra la **constante**.
    Con el tope real en 8, curaba 4 puntos en vez de 7 y dejaba al jugador
    mejorado permanentemente a medias.
    """
    from src.engine.core.event_bus import EventBus
    from src.engine.core.game_context import GameContext
    from src.framework.stage.progression_system import ProgressionSystem

    jugador._bonus_max_health = 3.0          # máximo real: 8
    jugador.set_health(1.0)

    class _GestorMinimo:
        """Lo único que `process_checkpoints` le pide al gestor de escenas."""

        stage_index = 0

    ctx = GameContext(
        input_manager=None, audio_manager=None, scene_manager=_GestorMinimo(),
        event_bus=EventBus(), clock=None, save_manager=None,
    )
    sistema = ProgressionSystem(ctx)

    class _Checkpoint:
        is_activated = False
        rect = pygame.Rect(0, 0, 32, 32)

        def check_collision(self, other: pygame.Rect) -> bool:
            return True

    class _Escenario:
        stage_id = "prueba"
        next_trigger = None
        entity_list: list = []

    sistema.process_checkpoints(
        jugador, _Escenario(), [_Checkpoint()], None, stage_key="prueba",
    )

    assert jugador.current_health == pytest.approx(jugador.max_health), (
        f"el checkpoint dejó al jugador en {jugador.current_health} de "
        f"{jugador.max_health}"
    )


def test_curar_nunca_pasa_del_maximo(jugador, _video) -> None:
    """El control del arreglo: subir el tope no puede volverse vida infinita."""
    jugador._bonus_max_health = 3.0
    jugador.set_health(1.0)
    jugador.heal(999.0)
    assert jugador.current_health == pytest.approx(jugador.max_health)
