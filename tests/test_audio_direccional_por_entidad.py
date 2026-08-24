"""
Module: test_audio_direccional_por_entidad
System: tests
Description: AUD-489 — `sonido.py._make_sfx_handler` ya enruta a audio
posicional (`_play_sfx_spatial`) en cuanto un evento trae `pos` en sus datos;
lo que faltaba era que los emisores lo pasaran. Antes de este lote, siete
sitios calculaban una posición de mundo dos líneas más arriba —para otro
evento hermano, o para construir el propio proyectil— y no se la pasaban a su
propio evento de sonido. Esta prueba fija que cada uno la pasa ahora.

No hace falta un motor de audio real: `sonido.py` sólo despacha `pos` como
parte de los datos del evento, así que basta con espiar lo que
`event_bus.emit` recibe.
"""
from __future__ import annotations

import pygame
import pytest


class _BusEspiaConDatos:
    """Como `_BusEspia` de test_sonido_de_muerte_llega.py, pero guarda kwargs."""

    def __init__(self) -> None:
        self.emitidos: list[tuple[str, dict]] = []

    def emit(self, nombre: str, **datos) -> None:
        self.emitidos.append((nombre, datos))

    def subscribe(self, *_a, **_k) -> None:
        pass

    def unsubscribe(self, *_a, **_k) -> None:
        pass

    def datos_de(self, nombre: str) -> dict:
        for n, d in self.emitidos:
            if n == nombre:
                return d
        raise AssertionError(f"nunca se emitió {nombre}; emitidos: "
                              f"{[n for n, _ in self.emitidos]}")


@pytest.fixture(autouse=True)
def _video():
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((320, 240))


class TestElEnemigoBaseMandaPosicion:
    """`enemy_base.py` es la clase de la que heredan las 30 especies."""

    def test_morir_manda_pos(self) -> None:
        from src.framework.entities.enemy_walker import EnemyWalker

        enemigo = EnemyWalker(pygame.Vector2(40.0, 20.0))
        bus = _BusEspiaConDatos()
        enemigo._event_bus = bus
        enemigo._die()

        sonidos = [n for n, _ in bus.emitidos if n.startswith("SFX_ENEMY_DIE")]
        assert sonidos, "el enemigo murió sin sonido"
        datos = bus.datos_de(sonidos[0])
        assert datos.get("pos") == (40.0, 20.0)

    def test_el_parry_manda_pos(self) -> None:
        from src.framework.entities.enemy_walker import EnemyWalker
        from src.framework.entities.player import Player

        enemigo = EnemyWalker(pygame.Vector2(55.0, 30.0))
        enemigo._update_rects()  # hurtbox/hitbox se derivan de position, no de rect
        bus = _BusEspiaConDatos()
        enemigo._event_bus = bus
        enemigo._contact_cooldown = 0.0

        jugador = Player(pygame.Vector2(60.0, 20.0))
        jugador.rect.center = enemigo.hurtbox.center  # solapa de verdad
        jugador._parry_active = True
        jugador._parry_window = 1.0
        jugador._parry_success = False

        enemigo._check_player_contact(jugador)

        datos = bus.datos_de("SFX_PLAYER_PARRY")
        assert datos.get("pos") == (enemigo.position.x, enemigo.position.y)


class TestLosDisparosMandanPosicion:
    def test_archer_manda_pos(self) -> None:
        from src.framework.entities.enemy_archer import EnemyArcher

        archer = EnemyArcher(pygame.Vector2(10.0, 10.0))
        archer.rect.center = (10, 10)
        bus = _BusEspiaConDatos()
        archer._event_bus = bus
        archer.set_player_ref(pygame.Rect(100, -20, 20, 32))

        archer._fire_arc()

        datos = bus.datos_de("SFX_PROJECTILE_FIRE")
        assert datos.get("pos") == archer.rect.center

    def test_caster_manda_pos(self) -> None:
        from src.framework.entities.enemy_caster import EnemyCaster

        caster = EnemyCaster(pygame.Vector2(5.0, 5.0))
        caster.rect.center = (5, 5)
        bus = _BusEspiaConDatos()
        caster._event_bus = bus
        caster.set_player_ref(pygame.Rect(80, 0, 20, 32))

        caster._fire_orb()

        datos = bus.datos_de("SFX_PROJECTILE_FIRE")
        assert datos.get("pos") == caster.rect.center

    def test_shooter_manda_pos(self) -> None:
        from src.framework.entities.enemy_shooter import EnemyShooter

        shooter = EnemyShooter(pygame.Vector2(0.0, 0.0), projectile_speed=100.0)
        shooter.rect.center = (0, 0)
        bus = _BusEspiaConDatos()
        shooter._event_bus = bus
        shooter.set_player_ref(pygame.Rect(100, -50, 20, 32))

        shooter._fire()

        datos = bus.datos_de("SFX_PROJECTILE_FIRE")
        assert datos.get("pos") == shooter.rect.center


class TestElGolpeDeSueloDelBrutoMandaPosicion:
    def test_brute_manda_pos(self) -> None:
        from src.framework.entities.enemy_brute import EnemyBrute

        bruto = EnemyBrute(pygame.Vector2(12.0, 8.0))
        bruto.rect.center = (12, 8)
        bus = _BusEspiaConDatos()
        bruto._event_bus = bus

        bruto._firing_behavior(0.016)

        datos = bus.datos_de("SFX_HIT_CONNECT")
        assert datos.get("pos") == bruto.rect.center
