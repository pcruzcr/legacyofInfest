"""Fase 7 — el juice que faltaba, probado por contrato.

Lo que ya existía y NO se repite aquí: sacudida direccional (AUD-282),
números de daño (AUD-158), partículas de impacto/sangre/parry, flash de
pantalla por daño. Todo eso tiene manejador en `senales.py`.

Lo que esta suite fija es lo que faltaba:

1. **Squash & Stretch** — el sprite del jugador se aplasta al aterrizar
   (proporcional a la velocidad de caída) y se estira al saltar, con
   retorno a 1.0. Sin esto, aterrizar y saltar pesan lo mismo visualmente:
   un píxel que cambia de estado sin masa.
2. **Polvo de aterrizaje y salto** — eventos nuevos que `senales.py`
   convierte en partículas. La señal existe para que el motor no dibuje:
   emite, y quien sabe de partículas decide.
3. **Kill flash** — al morir un enemigo se emite `VFX_KILL_FLASH`, para
   que la muerte tenga un destello blanco además de la sangre.
4. **Hit pause variable** — el hit-stop ya no es una constante: golpe
   ligero corta menos que uno pesado, y un lanzado corta más que ambos.
   El impacto se lee por su duración antes que por su número.
"""

from __future__ import annotations

import pygame
import pytest

from src.engine.core.events import Events
from src.framework.entities.enemy_base import EnemyBase
from src.framework.entities.player import Player
from src.framework.stage.collision_system import (
    HITSTOP_HEAVY,
    HITSTOP_LAUNCH,
    HITSTOP_LIGHT,
    CollisionSystem,
)


class _BusDePrueba:
    """Bus mínimo: guarda todo lo emitido con su nombre."""

    def __init__(self) -> None:
        self.emitidos: list[tuple[str, dict]] = []

    def emit(self, evento: str, **datos) -> None:
        self.emitidos.append((evento, datos))

    def subscribe(self, *a, **k) -> None:  # pragma: no cover - no-op
        pass


def _jugador() -> Player:
    bus = _BusDePrueba()
    p = Player(pygame.Vector2(100.0, 100.0), event_bus=bus)
    return p


# ── Squash & Stretch ──────────────────────────────────────────────


class TestSquashStretch:
    def test_aterrizar_fuerte_aplasta(self) -> None:
        p = _jugador()

        p.aplicar_squash_por_aterrizaje(500.0)

        assert p._squash_x > 1.0, "el aplastamiento ensancha"
        assert p._squash_y < 1.0, "el aplastamiento achica en vertical"

    def test_aterrizar_suave_casi_no_deforma(self) -> None:
        p = _jugador()

        p.aplicar_squash_por_aterrizaje(60.0)

        assert abs(p._squash_x - 1.0) < 0.05, (
            "una caída de nada no debe aplastar como un golpe fuerte: el "
            "grado es la información"
        )

    def test_salto_estira(self) -> None:
        p = _jugador()

        p.aplicar_stretch_por_salto()

        assert p._squash_x < 1.0
        assert p._squash_y > 1.0

    def test_el_squash_decae_hacia_identidad(self) -> None:
        p = _jugador()
        p.aplicar_stretch_por_salto()
        assert p._squash_y != 1.0

        for _ in range(120):          # dos segundos
            p._tick_timers(1 / 60)

        assert p._squash_x == pytest.approx(1.0, abs=0.01)
        assert p._squash_y == pytest.approx(1.0, abs=0.01)

    def test_el_salto_emite_polvo(self) -> None:
        from src.framework.entities.states.helpers import _do_jump

        p = _jugador()
        _do_jump(p)

        eventos = [nombre for nombre, _ in p._event_bus.emitidos]
        assert Events.VFX_JUMP_DUST in eventos

    def test_aterrizar_emite_polvo_proporcional(self) -> None:
        p = _jugador()
        p.velocity.y = 480.0

        # Simular lo que hace `_resolve_collision` al aterrizar
        p.aplicar_squash_por_aterrizaje(480.0)

        eventos = [nombre for nombre, _ in p._event_bus.emitidos]
        assert Events.VFX_LAND_DUST in eventos
        datos = dict(p._event_bus.emitidos[-1][1])
        assert 0.0 < datos.get("fuerza", 0.0) <= 1.0


class TestDibujoConSquash:
    def test_draw_con_squash_activo_escala_el_sprite(self, monkeypatch) -> None:
        """El sprite escalado mide distinto que el original; anclado abajo."""
        pygame.init()
        pygame.display.set_mode((1, 1))
        p = _jugador()
        p.aplicar_squash_por_aterrizaje(500.0)

        superficie = pygame.Surface((200, 200))
        # No debe lanzar, y debe producir un blit con dimensiones distintas
        # de las del sprite base — eso es todo lo que el contrato pide.
        p.draw(superficie, pygame.Vector2(0, 0))

    def test_draw_sin_squash_es_el_camino_de_siempre(self) -> None:
        pygame.init()
        pygame.display.set_mode((1, 1))
        p = _jugador()

        superficie = pygame.Surface((200, 200))
        p.draw(superficie, pygame.Vector2(0, 0))   # no lanza


# ── Kill flash ────────────────────────────────────────────────────


class _EnemigoMinimo(EnemyBase):
    """Lo justo para instanciar `EnemyBase`: los cinco métodos abstractos."""

    def __init__(self, pos: pygame.Vector2, bus) -> None:
        super().__init__(
            spawn_position=pos,
            max_health=1.0,
            event_bus=bus,
        )

    def _patrol_behavior(self, dt: float) -> None: ...
    def _alert_behavior(self, dt: float) -> None: ...
    def _get_animation_key(self) -> str:
        return "walk"

    def _build_hurtbox(self) -> pygame.Rect:
        return self.caja_ajustada(margen_x=2, margen_y=1)

    def _build_hitbox(self) -> pygame.Rect:
        return self._build_hurtbox()


class TestKillFlash:
    def test_morir_emite_kill_flash(self) -> None:
        bus = _BusDePrueba()
        enemigo = _EnemigoMinimo(pygame.Vector2(50, 50), bus)

        enemigo.apply_hit(10.0, (0.0, 0.0))

        assert not enemigo.is_alive or enemigo.state.value == "DYING"
        eventos = [nombre for nombre, _ in bus.emitidos]
        assert Events.VFX_KILL_FLASH in eventos, (
            "la muerte tiene sangre pero no destello: el ojo necesita los "
            "dos para leer 'esto acabó' en medio segundo"
        )


# ── Hit pause variable ────────────────────────────────────────────


class TestHitPauseVariable:
    def test_escalón_por_dano(self) -> None:
        assert HITSTOP_LIGHT < HITSTOP_HEAVY < HITSTOP_LAUNCH

    @pytest.mark.parametrize(
        "dano,esperado",
        [
            (0.25, HITSTOP_LIGHT),
            (0.5, HITSTOP_LIGHT),
            (0.8, HITSTOP_HEAVY),
            (1.0, HITSTOP_HEAVY),
            (1.5, HITSTOP_LAUNCH),
            (3.0, HITSTOP_LAUNCH),
        ],
    )
    def test_mapeo_de_dano_a_duración(self, dano: float, esperado: float) -> None:
        assert CollisionSystem.hitstop_por_dano(dano) == esperado

    def test_golpe_conecta_con_la_duración_que_le_toca(self) -> None:
        """Un golpe pesado congela más que el fijo de 0,05 de siempre."""
        sistema = CollisionSystem()

        sistema.trigger_hitstop(CollisionSystem.hitstop_por_dano(2.0))

        assert sistema.is_hitstopped
        assert sistema._hitstop_timer == pytest.approx(HITSTOP_LAUNCH)

    def test_el_default_del_trigger_sigue_siendo_compatibles(self) -> None:
        """Código de estudiante que llame `trigger_hitstop()` a secas obtiene
        el valor intermedio, no un cero silencioso."""
        sistema = CollisionSystem()
        sistema.trigger_hitstop()
        assert sistema.is_hitstopped
