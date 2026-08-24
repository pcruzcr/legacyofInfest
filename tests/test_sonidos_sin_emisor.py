"""AUD-255 — cuatro sonidos con fichero, con nombre y sin nadie que los pidiera.

El defecto
==========
`docs/52_EVENT_MAP.md` §3 lleva meses listando eventos «definidos y nunca
emitidos». La lista estaba desfasada —`SFX_PLAYER_PARRY`, `SFX_UI_GAME_OVER`,
`SFX_BOSS_HIT`, `SFX_BOSS_PHASE_CHANGE` y `MUSIC_STINGER` ya se emiten— pero
cuatro seguían siendo ciertos, y los cuatro son de juego base:

    SFX_PLAYER_HEAL                    curarse
    SFX_PLAYER_CROUCH                  agacharse
    SFX_ENVIRONMENT_ONE_WAY_PLATFORM   cruzar una plataforma de un sentido
    SFX_ENEMIES_PROJECTILE_HIT_WALL    proyectil contra pared

No es cableado de mentira: los cuatro **tienen su fichero en `assets/sfx/`** y
su entrada en la tabla de `senales.py`. Estaban a un `emit` de sonar, y ese
`emit` no existía en ninguna parte. Es la misma familia que AUD-149, AUD-206 y
AUD-243: la cadena escrita entera y desconectada por un extremo.

Lo que **no** se hizo aquí: emitir los cinco de jefe
(`SFX_BOSSES_GAVILAN_DIVE`, `_MASK_BEAM`, `SFX_BOSSES_PABURU_WAVE`,
`SFX_BOSSES_RELIC_APPEAR`, `SFX_BOSSES_REY_SPIT`, `_SPLIT`). Ésos pertenecen a
ataques concretos de jefes de estudiantes, y decidir en qué fotograma suena el
picado del Gavilán no es trabajo de una auditoría.
"""
from __future__ import annotations

import pygame
import pytest

from src.engine.core.event_bus import EventBus
from src.engine.core.events import Events


class _Espia:
    """Cuenta los eventos que pasan por el bus, sin tocar audio."""

    def __init__(self, bus: EventBus, evento: str) -> None:
        self.veces = 0
        self._evento = evento
        self._handler = self._anotar          # retención: el bus es débil
        bus.subscribe(evento, self._handler)
        self._bus = bus

    def _anotar(self, **_data: object) -> None:
        self.veces += 1

    def contar(self) -> int:
        self._bus.dispatch()
        return self.veces


@pytest.fixture
def jugador(event_bus):
    from src.framework.entities.player import Player

    p = Player(pygame.Vector2(100, 100))
    p.set_event_bus(event_bus)
    return p


class TestCurarseSuena:
    def test_curar_emite_su_sonido(self, jugador, event_bus) -> None:
        espia = _Espia(event_bus, Events.SFX_PLAYER_HEAL)
        jugador.set_health(1.0)

        jugador.heal(2.0)

        assert espia.contar() == 1

    def test_curar_a_salud_llena_no_suena(self, jugador, event_bus) -> None:
        """Sin esto, un pedestal de curación pisado dos veces sonaría dos veces
        mientras no cura nada: el sonido dejaría de significar «me he curado».
        """
        espia = _Espia(event_bus, Events.SFX_PLAYER_HEAL)
        jugador.set_health(jugador.max_health)

        jugador.heal(2.0)

        assert espia.contar() == 0


class TestAgacharseSuena:
    def test_entrar_en_agachado_emite_su_sonido(self, jugador, event_bus) -> None:
        from src.framework.entities.states import CrouchingState

        espia = _Espia(event_bus, Events.SFX_PLAYER_CROUCH)
        CrouchingState().enter(jugador)

        assert espia.contar() == 1


class TestElProyectilContraLaPared:
    def test_al_chocar_emite_su_sonido(self, event_bus) -> None:
        from src.framework.entities.enemy_shooter import Projectile

        proyectil = Projectile(
            pygame.Vector2(0, 0), pygame.Vector2(100, 0), damage=0.5,
        )
        proyectil.set_event_bus(event_bus)
        espia = _Espia(event_bus, Events.SFX_ENEMIES_PROJECTILE_HIT_WALL)

        proyectil.on_collision()

        assert espia.contar() == 1

    def test_sin_bus_no_revienta(self) -> None:
        """Un proyectil creado por una entrega puede no tener bus."""
        from src.framework.entities.enemy_shooter import Projectile

        proyectil = Projectile(
            pygame.Vector2(0, 0), pygame.Vector2(100, 0), damage=0.5,
        )
        proyectil.on_collision()          # no debe lanzar

        assert proyectil.is_active is False


class TestLaComprobacionQueLoHabriaEvitado:
    """Los cuatro tienen que tener emisor en `src/`, no sólo tabla de sonidos.

    La tabla de `senales.py` *parece* cableado y no lo es: mapea un evento a un
    nombre de muestra, y un evento que nadie emite no llega nunca a esa tabla.
    """

    @pytest.mark.parametrize("evento", [
        "SFX_PLAYER_HEAL",
        "SFX_PLAYER_CROUCH",
        "SFX_ENVIRONMENT_ONE_WAY_PLATFORM",
        "SFX_ENEMIES_PROJECTILE_HIT_WALL",
    ])
    def test_el_evento_tiene_emisor(self, evento: str) -> None:
        from pathlib import Path

        raiz = Path(__file__).resolve().parents[1] / "src"
        emisores = [
            p for p in raiz.rglob("*.py")
            if f"emit(Events.{evento}" in p.read_text(encoding="utf-8")
        ]
        assert emisores, (
            f"Events.{evento} tiene fichero de sonido y entrada en la tabla, "
            "y nadie lo emite: no suena nunca."
        )
