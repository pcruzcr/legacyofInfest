"""Los doce estados de enemigo deben existir y hacer algo (AUD-051).

La máquina tenía siete estados; `docs/05_ENEMY_SPEC.md` §12 describe doce. Los
seis que faltaban no eran adornos — son los que hacen legible un combate:

* ``SEARCH``  — sin él, romper la línea de visión no sirve para nada: el enemigo
  te olvida en el fotograma exacto en que sales de rango.
* ``RECOVER`` — la ventana de castigo. Sin ella un enemigo puede cadenar
  ataques sin pausa y la única respuesta posible es evitarlo, nunca responderle.
* ``STUNNED`` — recompensa la defensa activa en lugar de premiar sólo esquivar.
* ``RETREAT`` — `SquadBrain` ya emitía esa táctica y ningún estado la
  representaba.
* ``IDLE``    — un enemigo estacionario estaba "patrullando" cero píxeles.
* ``CHASE``   — separado de ALERT para poder telegrafiar el "te vi".

Cada prueba comprueba **comportamiento observable**, no la existencia del enum.
Un estado que se alcanza y no cambia nada es lo mismo que no tenerlo, y ese es
exactamente el error que la auditoría encontró nueve veces en este proyecto.
"""
from __future__ import annotations

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame
import pytest

DT = 1 / 60


@pytest.fixture(scope="module")
def display():
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((320, 240))
    yield


@pytest.fixture
def walker(display):
    from src.framework.entities.enemy_walker import EnemyWalker

    enemy = EnemyWalker(pygame.Vector2(200.0, 300.0))
    enemy._charge_cooldown = 99.0  # aísla el estado de la carga
    return enemy


# ── el enum cubre la especificación ──────────────────────────────


BRIEF_STATES = [
    "IDLE", "PATROL", "SEARCH", "ALERT", "CHASE", "TELEGRAPHING",
    "FIRING", "RECOVER", "RETREAT", "STUNNED", "HURT", "DYING",
]


@pytest.mark.parametrize("name", BRIEF_STATES)
def test_state_exists(name: str) -> None:
    from src.framework.entities.enemy_base import EnemyState

    assert hasattr(EnemyState, name), f"falta el estado {name}"


# ── SEARCH: el enemigo recuerda dónde te vio ─────────────────────


class TestSearch:
    def test_losing_the_player_enters_search_not_patrol(self, walker) -> None:
        """Salir de rango debe llevar a SEARCH, no directamente a PATROL.

        Es la diferencia entre un enemigo con memoria y uno con amnesia
        instantánea. Sin SEARCH, esconderse tras una pared es gratis.
        """
        from src.framework.entities.enemy_base import EnemyState

        walker.set_player_ref(pygame.Rect(210, 300, 20, 32))
        walker._run_state_machine(DT)
        assert walker.state in (EnemyState.ALERT, EnemyState.CHASE)

        walker.set_player_ref(pygame.Rect(5000, 300, 20, 32))
        walker._run_state_machine(DT)
        assert walker.state == EnemyState.SEARCH, (
            f"tras perder al jugador el enemigo pasó a {walker.state} en lugar "
            f"de buscarlo"
        )

    def test_search_walks_toward_the_last_known_position(self, walker) -> None:
        from src.framework.entities.enemy_base import EnemyState

        walker.set_player_ref(pygame.Rect(260, 300, 20, 32))
        walker._run_state_machine(DT)          # ve al jugador, guarda la posición
        walker.set_player_ref(pygame.Rect(5000, 300, 20, 32))
        walker._run_state_machine(DT)          # lo pierde -> SEARCH

        assert walker.state == EnemyState.SEARCH
        start = walker.position.x
        for _ in range(30):
            walker._run_state_machine(DT)

        assert walker.position.x > start, (
            "en SEARCH el enemigo no avanzó hacia donde vio al jugador"
        )

    def test_search_expires_back_to_resting(self, walker) -> None:
        from src.framework.entities.enemy_base import EnemyState

        walker.set_player_ref(pygame.Rect(210, 300, 20, 32))
        walker._run_state_machine(DT)
        walker.set_player_ref(pygame.Rect(5000, 300, 20, 32))
        walker._run_state_machine(DT)
        assert walker.state == EnemyState.SEARCH

        for _ in range(int(walker.SEARCH_DURATION * 60) + 10):
            walker._run_state_machine(DT)

        assert walker.state in (EnemyState.PATROL, EnemyState.IDLE), (
            f"la búsqueda no expiró: sigue en {walker.state}"
        )

    def test_search_without_a_last_seen_position_is_safe(self, walker) -> None:
        from src.framework.entities.enemy_base import EnemyState

        walker.state = EnemyState.SEARCH
        walker._last_seen = None
        walker._search_behavior(DT)  # no debe lanzar

    def test_search_behavior_clamps_to_arena_bounds(self, walker) -> None:
        """AUD-615: SEARCH no puede sacar al enemigo de su arena."""
        from src.framework.entities.enemy_base import EnemyState

        walker.state = EnemyState.SEARCH
        # Arena de 800x600, enemigo en el centro
        arena = pygame.Rect(0, 0, 800, 600)
        walker.set_arena_bounds(arena)
        walker.position = pygame.Vector2(400.0, 300.0)
        walker.rect.center = (400, 300)
        # Última posición vista muy a la derecha (fuera de la arena)
        walker._last_seen = pygame.Vector2(2000.0, 300.0)

        walker._search_behavior(DT)

        # Con margen de 16 px, no debe pasar de 800 - 16 - 24 (ancho) = 760
        assert walker.position.x <= 760, (
            f"el enemigo se salió de la arena en SEARCH: x={walker.position.x}"
        )
        assert walker.rect.right <= 784, (
            f"el rect del enemigo se salió de la arena: right={walker.rect.right}"
        )


# ── RECOVER: la ventana de castigo ───────────────────────────────


class TestRecover:
    def test_begin_recovery_enters_the_state(self, walker) -> None:
        from src.framework.entities.enemy_base import EnemyState

        walker.begin_recovery()
        assert walker.state == EnemyState.RECOVER

    def test_recovery_holds_position(self, walker) -> None:
        """Quieto durante la recuperación: eso ES la ventana de castigo."""
        walker.set_player_ref(pygame.Rect(210, 300, 20, 32))
        walker.begin_recovery()
        start = walker.position.x
        for _ in range(int(walker.RECOVER_DURATION * 60) - 2):
            walker._run_state_machine(DT)
        assert walker.position.x == pytest.approx(start, abs=0.5), (
            "el enemigo se movió durante la recuperación, así que no hay hueco "
            "real para castigarlo"
        )

    def test_recovery_expires(self, walker) -> None:
        from src.framework.entities.enemy_base import EnemyState

        walker.set_player_ref(pygame.Rect(210, 300, 20, 32))
        walker.begin_recovery()
        for _ in range(int(walker.RECOVER_DURATION * 60) + 5):
            walker._run_state_machine(DT)
        assert walker.state != EnemyState.RECOVER

    def test_recovery_resumes_chase_if_player_still_near(self, walker) -> None:
        from src.framework.entities.enemy_base import EnemyState

        walker.set_player_ref(pygame.Rect(210, 300, 20, 32))
        walker.begin_recovery()
        for _ in range(int(walker.RECOVER_DURATION * 60) + 5):
            walker._run_state_machine(DT)
        assert walker.state in (EnemyState.CHASE, EnemyState.ALERT,
                                EnemyState.RETREAT)

    def test_a_corpse_cannot_recover(self, walker) -> None:
        from src.framework.entities.enemy_base import EnemyState

        walker.state = EnemyState.DYING
        walker.begin_recovery()
        assert walker.state == EnemyState.DYING


# ── STUNNED: la defensa activa se recompensa ─────────────────────


class TestStunned:
    def test_stun_interrupts_any_plan(self, walker) -> None:
        """Aturdir debe cortar el ataque en curso, o parar no sirve."""
        from src.framework.entities.enemy_base import EnemyState

        walker.state = EnemyState.TELEGRAPHING
        walker.stun(0.5)
        assert walker.state == EnemyState.STUNNED

    def test_stunned_does_not_move(self, walker) -> None:
        walker.set_player_ref(pygame.Rect(210, 300, 20, 32))
        walker.stun(0.5)
        start = walker.position.x
        for _ in range(20):
            walker._run_state_machine(DT)
        assert walker.position.x == pytest.approx(start, abs=0.5)

    def test_stun_leads_into_recovery_not_straight_back_to_attack(self, walker) -> None:
        """Salir del aturdimiento a RECOVER alarga la ventana de castigo.

        Si el aturdimiento devolviera directamente a CHASE, una parada bien
        ejecutada apenas valdría unas décimas.
        """
        from src.framework.entities.enemy_base import EnemyState

        walker.set_player_ref(pygame.Rect(210, 300, 20, 32))
        walker.stun(0.2)
        for _ in range(int(0.2 * 60) + 3):
            walker._run_state_machine(DT)
        assert walker.state == EnemyState.RECOVER

    def test_stun_does_not_extend_downward(self, walker) -> None:
        """Un aturdimiento corto no debe acortar uno largo en curso."""
        walker.stun(1.0)
        walker.stun(0.1)
        assert walker._stun_timer == pytest.approx(1.0)

    def test_a_corpse_cannot_be_stunned(self, walker) -> None:
        from src.framework.entities.enemy_base import EnemyState

        walker.state = EnemyState.DYING
        walker.stun(1.0)
        assert walker.state == EnemyState.DYING


# ── RETREAT: con poca vida se repliega ───────────────────────────


class TestRetreat:
    def test_low_health_triggers_retreat(self, walker) -> None:
        from src.framework.entities.enemy_base import EnemyState

        walker.current_health = walker.max_health * 0.1
        walker.set_player_ref(pygame.Rect(210, 300, 20, 32))
        walker._run_state_machine(DT)
        assert walker.state == EnemyState.RETREAT

    def test_retreat_moves_away_from_the_player(self, walker) -> None:
        walker.current_health = walker.max_health * 0.1
        # El jugador debe estar a la derecha Y dentro del rango de detección:
        # fuera de rango el enemigo nunca entra en RETREAT, y la primera versión
        # de este test lo puso a 400 px y comprobó un estado que no ocurría.
        walker.set_player_ref(pygame.Rect(270, 300, 20, 32))
        walker._run_state_machine(DT)
        assert walker.state.value == "RETREAT", (
            f"premisa del test inválida: el enemigo está en {walker.state}, "
            f"no en RETREAT, así que no se está midiendo el repliegue"
        )
        start = walker.position.x
        for _ in range(30):
            walker._run_state_machine(DT)
        assert walker.position.x < start, "el repliegue no alejó al enemigo"

    def test_healing_leaves_retreat(self, walker) -> None:
        from src.framework.entities.enemy_base import EnemyState

        walker.current_health = walker.max_health * 0.1
        walker.set_player_ref(pygame.Rect(210, 300, 20, 32))
        walker._run_state_machine(DT)
        assert walker.state == EnemyState.RETREAT

        walker.current_health = walker.max_health
        walker._run_state_machine(DT)
        assert walker.state != EnemyState.RETREAT

    def test_retreat_without_a_player_is_safe(self, walker) -> None:
        walker._player_ref = None
        walker._retreat_behavior(DT)  # no debe lanzar


# ── IDLE vs PATROL, y la regresión que introdujo ─────────────────


class TestRestingState:
    def test_stationary_enemy_rests_in_idle(self, display) -> None:
        from src.framework.entities.enemy_base import EnemyState
        from src.framework.entities.enemy_walker import EnemyWalker

        enemy = EnemyWalker(pygame.Vector2(100, 300), patrol_length=0.0)
        enemy._run_state_machine(DT)
        assert enemy.state == EnemyState.IDLE

    def test_patrolling_enemy_rests_in_patrol(self, display) -> None:
        from src.framework.entities.enemy_base import EnemyState
        from src.framework.entities.enemy_walker import EnemyWalker

        enemy = EnemyWalker(pygame.Vector2(100, 300), patrol_length=64.0)
        enemy._run_state_machine(DT)
        assert enemy.state == EnemyState.PATROL

    def test_flying_enemies_still_patrol_and_move(self, display) -> None:
        """Regresión de AUD-051.

        `_resting_state` usaba ``getattr(self, "patrol_length", 0.0)``. Los
        voladores no tienen ese atributo — se mueven por estrategia de vuelo —
        así que el 0.0 de reserva los mandaba a IDLE y **dejaban de volar por
        completo**. Lo detectó `test_sine_reverses_at_boundary`, que existía
        desde antes; la ausencia del atributo significa "esta clase no se rige
        por longitud de patrulla", no "está quieta".
        """
        from src.framework.entities.enemy_base import EnemyState
        from src.framework.entities.enemy_flying import EnemyFlying

        flyer = EnemyFlying(pygame.Vector2(100.0, 100.0))
        flyer._run_state_machine(DT)
        assert flyer.state == EnemyState.PATROL, (
            f"un volador quedó en {flyer.state}; si es IDLE, dejó de volar"
        )

        start = flyer.position.x
        for _ in range(30):
            flyer._run_state_machine(DT)
        assert flyer.position.x != start, "el volador no se movió"


# ── el conjunto sigue siendo coherente ───────────────────────────


def test_every_species_survives_all_state_transitions(display) -> None:
    """Las 21 especies deben tolerar cada estado sin lanzar.

    Fuerza cada estado en cada especie: es barato y cubre la combinación que
    ningún test escribiría a mano.
    """
    from src.framework.entities import bestiary_registry
    from src.framework.entities.enemy_base import EnemyState

    failures: list[str] = []
    for species_id, spec in bestiary_registry.SPECIES.items():
        for state in EnemyState:
            enemy = spec.build(pygame.Vector2(100.0, 100.0))
            enemy.set_player_ref(pygame.Rect(150, 100, 20, 32))
            enemy.state = state
            try:
                for _ in range(5):
                    enemy.update(DT)
            except Exception as exc:
                failures.append(f"{species_id} en {state.value}: "
                                f"{type(exc).__name__}: {exc}")
    assert not failures, "estados que revientan:\n  " + "\n  ".join(failures[:15])
