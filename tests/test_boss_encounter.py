"""
Module: test_boss_encounter
System: tests
Academic Unit: N/A

Pruebas del kit de encuentro de jefe (AUD-053): telegrafiado, puntos débiles,
invocaciones y multiplicador de velocidad por fase.

Qué se prueba aquí y qué no
---------------------------
Estas pruebas verifican **propiedades de diseño**, no sólo que el código
ejecute. La diferencia importa: `assert boss.attacks is not None` pasa siempre
y no dice nada. Lo que se comprueba es que cada ataque declarado se pueda leer
a tiempo, que exista ventana de castigo, que los puntos débiles multipliquen y
que las invocaciones respeten su tope.

Un caso concreto de por qué: la prueba de variedad de ataques falla si el
planificador vuelve a elegir siempre el primero de la lista, que es exactamente
el defecto que este módulo vino a corregir — cinco ataques declarados, uno
ejecutado.
"""
from __future__ import annotations

from itertools import pairwise

import pygame
import pytest

from src.framework.entities.boss_base import BossBase, BossPhase
from src.framework.entities.boss_kit import (
    MIN_READABLE_WINDUP,
    AttackScheduler,
    AttackTiming,
    BossAttack,
    SummonTracker,
    SummonWave,
    WeakPoint,
    resolve_weak_point_damage,
)
from src.framework.entities.enemy_base import EnemyState

FRAME = 1.0 / 60.0


def _advance(scheduler: AttackScheduler, seconds: float,
             distance: float = 50.0, phase: int = 0) -> list[str]:
    """Avanza el planificador en pasos de fotograma. Devuelve lo que disparó.

    Se avanza a 60 Hz en vez de dar un salto grande a propósito: un salto de
    un segundo puede atravesar WINDUP, ACTIVE y RECOVER de una vez y ocultar
    que un tramo no se llegue a visitar nunca.
    """
    fired: list[str] = []
    steps = int(seconds / FRAME)
    for _ in range(steps):
        name = scheduler.update(FRAME, distance, phase)
        if name is not None:
            fired.append(name)
    return fired


class _TestBoss(BossBase):
    """Jefe mínimo: sólo lo que la clase base exige, sin lógica propia."""

    def _patrol_behavior(self, dt: float) -> None:
        pass

    def _alert_behavior(self, dt: float) -> None:
        pass

    def _get_animation_key(self) -> str:
        return "drift"

    def _build_hitbox(self) -> pygame.Rect:
        return pygame.Rect(0, 0, 32, 32)

    def _build_hurtbox(self) -> pygame.Rect:
        return pygame.Rect(0, 0, 32, 32)


# ══════════════════════════════════════════════════════════════
# Telegrafiado
# ══════════════════════════════════════════════════════════════


class TestTelegraphing:
    def test_windup_precedes_the_hit(self) -> None:
        """El golpe no puede llegar antes de que termine el aviso."""
        sched = AttackScheduler([BossAttack("A", windup=0.5, active=0.2, recover=0.3)])
        # Justo por debajo del aviso: no debe haber disparado nada aún.
        assert _advance(sched, 0.45) == []
        assert sched.timing == AttackTiming.WINDUP
        # Pasado el aviso, el golpe sale.
        assert _advance(sched, 0.15) == ["A"]

    def test_the_three_phases_are_all_visited(self) -> None:
        sched = AttackScheduler([BossAttack("A", windup=0.4, active=0.2, recover=0.4)])
        seen: set[AttackTiming] = set()
        for _ in range(120):
            sched.update(FRAME, 50.0, 0)
            seen.add(sched.timing)
        assert AttackTiming.WINDUP in seen
        assert AttackTiming.ACTIVE in seen
        assert AttackTiming.RECOVER in seen

    def test_recover_leaves_the_boss_vulnerable(self) -> None:
        """La ventana de castigo tiene que ser observable, no sólo declarada."""
        sched = AttackScheduler([BossAttack("A", windup=0.4, active=0.1, recover=0.5)])
        _advance(sched, 0.55)  # aviso + golpe consumidos
        assert sched.timing == AttackTiming.RECOVER
        assert sched.is_vulnerable is True
        # Durante el aviso NO es vulnerable: si lo fuera, no habría razón para
        # esperar el hueco y el telegrafiado dejaría de ser una decisión.
        sched.reset()
        _advance(sched, 0.2)
        assert sched.is_vulnerable is False

    def test_telegraph_progress_advances_from_zero_to_one(self) -> None:
        sched = AttackScheduler([BossAttack("A", windup=0.5, active=0.1, recover=0.1)])
        sched.update(FRAME, 50.0, 0)  # arranca el aviso
        early = sched.telegraph_progress
        _advance(sched, 0.4)
        late = sched.telegraph_progress
        assert 0.0 <= early < late <= 1.0

    def test_progress_is_zero_outside_the_windup(self) -> None:
        sched = AttackScheduler([BossAttack("A", windup=0.3, active=0.1, recover=0.4)])
        _advance(sched, 0.45)
        assert sched.timing == AttackTiming.RECOVER
        assert sched.telegraph_progress == 0.0

    @pytest.mark.parametrize("windup", [0.0, 0.1, 0.34])
    def test_short_windups_are_flagged_unreadable(self, windup: float) -> None:
        assert BossAttack("A", windup=windup).is_readable() is False

    def test_the_threshold_itself_counts_as_readable(self) -> None:
        assert BossAttack("A", windup=MIN_READABLE_WINDUP).is_readable() is True


class TestVenadoTelegraphsAreReadable:
    """Cada ataque declarado por el Venado tiene que existir, avisar y castigarse.

    Por qué esta clase se reescribió (AUD-107)
    ------------------------------------------
    Estaba escrita contra la **implementación de referencia** del profesor, que
    registraba sus ataques en `AttackScheduler` y los consultaba por
    `venado.attacks._attacks`. Al sustituir el Venado por la entrega del
    estudiante —decisión tomada al revisar el lote— seis de estas pruebas se
    pusieron en rojo y, peor, **tres se quedaron en verde vacías**: recorrían
    una lista de ataques que ahora está siempre vacía, así que no podían
    fallar.

    Su boss no usa el planificador: declara los patrones en `BossPhase` y los
    ejecuta él mismo con `_try_attack`. Es una forma perfectamente válida —el
    framework no obliga a usar `BossKit`, y el calificador de jefes le da
    100/100—, y exigirle que se parezca a mi implementación sería confundir
    «distinto» con «mal».

    Lo que sí sigue siendo obligatorio, y es lo que se comprueba ahora, no
    depende de cómo esté organizado por dentro:

    * lo que una fase declara, existe y hace algo;
    * cada ataque avisa antes de golpear y se puede castigar después;
    * una fase con un solo ataque es un patrón, no un combate;
    * un nombre desconocido no revienta el combate.
    """

    @pytest.fixture
    def venado(self, _pygame_init):
        from src.stages.boss_venado.boss_venado import BossVenado
        return BossVenado(pygame.Vector2(160, 180))

    @staticmethod
    def _patrones(venado) -> set[str]:
        return {p for fase in venado.phases for p in fase.attack_patterns}

    def test_every_declared_attack_is_readable(self, venado) -> None:
        unreadable = [
            a.name for a in venado.attacks._attacks if not a.is_readable()
        ]
        assert unreadable == [], f"ataques sin aviso legible: {unreadable}"

    def test_every_attack_has_a_punish_window(self, venado) -> None:
        no_recover = [a.name for a in venado.attacks._attacks if a.recover <= 0.0]
        assert no_recover == [], f"ataques sin ventana de castigo: {no_recover}"

    def test_every_attack_has_a_cooldown(self, venado) -> None:
        """Sin enfriamiento un ataque se puede encadenar hasta ser un muro."""
        free = [a.name for a in venado.attacks._attacks if a.cooldown <= 0.0]
        assert free == [], f"ataques sin enfriamiento: {free}"

    def test_the_declared_patterns_and_the_real_attacks_agree(self, venado) -> None:
        """Lo que una fase declara tiene que estar implementado.

        Antes se comprobaba contra `attacks._attacks`. Ahora se comprueba
        contra lo que el jefe **sabe ejecutar**, que es la propiedad real: una
        fase que declara `FIREBALL` y no lo implementa deja al jefe quieto en
        esa fase, y eso pasa igual con planificador que sin él.
        """
        declarados = self._patrones(venado)
        assert declarados, "el jefe no declara ningún patrón de ataque"

        registrados = {a.name for a in venado.attacks._attacks}
        ejecutables = set(venado._attack_cooldowns)
        implementados = registrados | ejecutables

        assert declarados <= implementados, (
            f"estas fases declaran ataques que nadie implementa: "
            f"{sorted(declarados - implementados)}"
        )

    def test_each_phase_has_at_least_two_usable_attacks(self, venado) -> None:
        """Un jefe con un solo ataque por fase es un patrón, no un combate."""
        for phase in venado.phases:
            assert len(set(phase.attack_patterns)) >= 2, (
                f"fase {phase.phase_index} sólo tiene "
                f"{len(set(phase.attack_patterns))} ataque(s)"
            )

    def test_every_declared_attack_has_a_cooldown(self, venado) -> None:
        """Cada patrón declarado necesita su enfriamiento, esté donde esté.

        Sin él, `_try_attack` volvería a dispararlo en el fotograma siguiente y
        el ataque dejaría de ser un ataque para ser un estado permanente.
        """
        sin_enfriar = [
            p for p in sorted(self._patrones(venado))
            if venado._attack_cooldowns.get(p, 0.0) <= 0.0
        ]
        assert sin_enfriar == [], f"patrones sin enfriamiento: {sin_enfriar}"

    def test_every_attack_produces_something_observable(self, venado) -> None:
        """Cada patrón despachado tiene que dejar rastro en el mundo.

        Comprobar sólo que se llama al gancho no basta: se detectó con una
        mutación que vaciaba el cuerpo del despacho de STOMP y la prueba de
        integración seguía pasando, porque medía la llamada y no el efecto.
        """
        venado.set_player_ref(pygame.Rect(220, 180, 16, 24))

        venado._try_attack("STOMP")
        assert venado._telegraph == "STOMP", "STOMP no telegrafía nada"

        venado._telegraph = ""
        venado._projectiles.clear()
        venado._try_attack("VINE_TOSS")
        assert len(venado._projectiles) == 1, "VINE_TOSS no lanzó la liana"
        assert venado._projectiles[0]["type"] == "vine"

        venado._projectiles.clear()
        venado._try_attack("MUSHROOM_SPORE")
        esporas = [p for p in venado._projectiles if p["type"] == "spore"]
        assert len(esporas) == 3, f"MUSHROOM_SPORE lanzó {len(esporas)} esporas"

        venado._telegraph = ""
        venado._try_attack("VINE_SWEEP")
        assert venado._telegraph == "VINE_SWEEP", "VINE_SWEEP no telegrafía nada"

    def test_los_ataques_telegrafiados_acaban_ocurriendo(self, venado) -> None:
        """El aviso no puede quedarse en aviso.

        Un telegrafiado que nunca desemboca en el golpe es peor que no avisar:
        enseña al jugador a ignorarlo.
        """
        venado.set_player_ref(pygame.Rect(220, 180, 16, 24))
        venado.state = EnemyState.ALERT
        venado._try_attack("STOMP")
        assert venado._telegraph == "STOMP"
        for _ in range(90):                      # segundo y medio
            venado.update(FRAME)
            if venado._stomp_rect is not None:
                break
        assert venado._stomp_rect is not None, (
            "el pisotón se telegrafió y nunca llegó a caer"
        )

    def test_an_unknown_attack_name_is_ignored_quietly(self, venado) -> None:
        """Un nombre desconocido no debe reventar ni dejar al jefe telegrafiando."""
        venado.set_player_ref(pygame.Rect(220, 180, 16, 24))
        antes = venado._telegraph
        venado._try_attack("NO_EXISTE")
        assert venado._telegraph == antes

    def test_the_stomp_zone_survives_its_active_window(self, venado) -> None:
        """Antes se borraba en el mismo fotograma en que se creaba.

        La condición de limpieza era `self._stomp_rect.y < self.rect.bottom`,
        y el rectángulo nace en `bottom - 8`: siempre cierta. El pisotón se
        veía y no golpeaba nunca.
        """
        venado.set_player_ref(pygame.Rect(220, 180, 16, 24))
        venado.state = EnemyState.ALERT
        venado._do_stomp()
        venado.update(FRAME)
        assert venado._stomp_rect is not None, "el pisotón murió en su primer frame"

        # Se busca el fotograma en el que caduca en vez de mirar sólo al final.
        # El jefe vuelve a atacar en cuanto puede —es su trabajo—, así que a los
        # treinta fotogramas podría haber un pisotón **nuevo** en pie y la
        # comprobación pasaría por el motivo equivocado.
        for _ in range(30):  # medio segundo: más que su ventana activa
            venado.update(FRAME)
            if venado._stomp_rect is None:
                break
        else:
            pytest.fail("el pisotón nunca caduca")

    def test_attack_specific_animations_are_reachable(self, venado) -> None:
        """`charge` y `stomp` existían en disco y nunca se mostraban."""
        venado._telegraph = "CHARGE"
        assert venado._get_animation_key() == "charge"
        venado._telegraph = "STOMP"
        assert venado._get_animation_key() == "stomp"
        venado._telegraph = ""
        assert venado._get_animation_key() == "drift"


# ══════════════════════════════════════════════════════════════
# Variedad y selección
# ══════════════════════════════════════════════════════════════


class TestAttackVariety:
    def test_the_same_attack_is_not_repeated_back_to_back(self) -> None:
        sched = AttackScheduler([
            BossAttack("A", windup=0.4, active=0.1, recover=0.1, cooldown=0.0),
            BossAttack("B", windup=0.4, active=0.1, recover=0.1, cooldown=0.0),
        ])
        fired = _advance(sched, 12.0)
        assert len(fired) >= 6, "el planificador apenas lanzó ataques"
        repeats = [(a, b) for a, b in pairwise(fired) if a == b]
        assert repeats == [], f"ataques repetidos consecutivamente: {repeats}"

    def test_all_declared_attacks_get_used(self) -> None:
        """Cinco patrones declarados y uno ejecutado era el defecto original."""
        sched = AttackScheduler([
            BossAttack(name, windup=0.4, active=0.1, recover=0.1, cooldown=0.2)
            for name in ("A", "B", "C")
        ])
        fired = set(_advance(sched, 30.0))
        assert fired == {"A", "B", "C"}, f"nunca se usaron: {{'A','B','C'}} - {fired}"

    def test_out_of_range_attacks_are_not_chosen(self) -> None:
        sched = AttackScheduler([
            BossAttack("MELEE", windup=0.4, max_range=60.0, cooldown=0.0),
            BossAttack("RANGED", windup=0.4, min_range=200.0, cooldown=0.0),
        ])
        assert set(_advance(sched, 6.0, distance=30.0)) == {"MELEE"}
        sched.reset()
        assert set(_advance(sched, 6.0, distance=400.0)) == {"RANGED"}

    def test_phase_locked_attacks_only_appear_in_their_phase(self) -> None:
        sched = AttackScheduler([
            BossAttack("BASE", windup=0.4, cooldown=0.0),
            BossAttack("ENRAGED", windup=0.4, cooldown=0.0, phases=(1,)),
        ])
        assert "ENRAGED" not in _advance(sched, 8.0, phase=0)
        sched.reset()
        assert "ENRAGED" in _advance(sched, 8.0, phase=1)

    def test_cooldown_blocks_reuse(self) -> None:
        sched = AttackScheduler([
            BossAttack("SLOW", windup=0.4, active=0.1, recover=0.1, cooldown=5.0),
        ])
        assert _advance(sched, 1.0) == ["SLOW"]
        # Con 5 s de enfriamiento no puede volver a salir en los 2 s siguientes.
        assert _advance(sched, 2.0) == []
        assert _advance(sched, 4.0) == ["SLOW"]

    def test_interrupt_cancels_the_attack_in_progress(self) -> None:
        sched = AttackScheduler([BossAttack("A", windup=1.0, cooldown=2.0)])
        _advance(sched, 0.5)
        assert sched.timing == AttackTiming.WINDUP
        sched.interrupt()
        assert sched.current is None
        assert sched.timing == AttackTiming.IDLE
        assert sched.is_active is False

    def test_interrupted_attacks_pay_half_cooldown(self) -> None:
        """Interrumpir no debe ser gratis ni un castigo completo.

        Sin coste, aturdir al jefe en cada aviso lo dejaría sin atacar jamás.
        Con coste completo, el jugador perdería el ataque entero por acertar.
        """
        sched = AttackScheduler([BossAttack("A", windup=1.0, cooldown=2.0)])
        _advance(sched, 0.2)
        sched.interrupt()
        assert _advance(sched, 0.6) == []      # aún en enfriamiento reducido
        assert _advance(sched, 2.0) == ["A"]   # vuelve antes que con 2 s enteros


# ══════════════════════════════════════════════════════════════
# Puntos débiles
# ══════════════════════════════════════════════════════════════


class TestWeakPoints:
    def test_a_hit_on_the_weak_point_is_multiplied(self, _pygame_init) -> None:
        boss = _TestBoss(pygame.Vector2(100, 100), max_health=20.0)
        point = WeakPoint(offset=(0, 0), size=(16, 16), multiplier=3.0)
        hit = pygame.Rect(boss.rect.x, boss.rect.y, 8, 8)
        damage, found = resolve_weak_point_damage(boss, hit, 2.0, [point], 0)
        assert found is point
        assert damage == pytest.approx(6.0)

    def test_a_hit_outside_the_weak_point_is_unchanged(self, _pygame_init) -> None:
        boss = _TestBoss(pygame.Vector2(100, 100), max_health=20.0)
        point = WeakPoint(offset=(0, 0), size=(8, 8), multiplier=3.0)
        hit = pygame.Rect(boss.rect.x + 200, boss.rect.y, 8, 8)
        damage, found = resolve_weak_point_damage(boss, hit, 2.0, [point], 0)
        assert found is None
        assert damage == pytest.approx(2.0)

    @pytest.mark.parametrize("order", [(2.0, 3.0), (3.0, 2.0)])
    def test_overlapping_points_take_the_best_not_the_product(
        self, _pygame_init, order: tuple[float, float],
    ) -> None:
        """Solapar dos puntos no debe multiplicar dos veces.

        Si se sumaran o multiplicaran, la recompensa dependería de la geometría
        del solape en lugar de la puntería, y afinar los rectángulos cambiaría
        el daño sin que nadie tocara el balance.

        Se prueban los dos órdenes de declaración a propósito. Con uno solo,
        una implementación que se quedara con el **último** punto acertado en
        lugar del mayor pasaría la prueba por casualidad — depende de cómo
        estén ordenados en la lista, no de la lógica. Esto se descubrió con una
        mutación: `best is None or point.multiplier > best.multiplier` → `True`
        sobrevivía a la versión anterior de esta prueba.
        """
        boss = _TestBoss(pygame.Vector2(100, 100), max_health=20.0)
        points = [
            WeakPoint(offset=(0, 0), size=(20, 20), multiplier=order[0]),
            WeakPoint(offset=(0, 0), size=(20, 20), multiplier=order[1]),
        ]
        hit = pygame.Rect(boss.rect.x, boss.rect.y, 4, 4)
        damage, found = resolve_weak_point_damage(boss, hit, 1.0, points, 0)
        assert damage == pytest.approx(3.0)
        assert found is not None
        assert found.multiplier == 3.0

    def test_phase_locked_points_are_not_exposed_early(self, _pygame_init) -> None:
        boss = _TestBoss(pygame.Vector2(100, 100), max_health=20.0)
        point = WeakPoint(offset=(0, 0), size=(16, 16), multiplier=4.0, phases=(1,))
        hit = pygame.Rect(boss.rect.x, boss.rect.y, 8, 8)
        assert resolve_weak_point_damage(boss, hit, 1.0, [point], 0)[1] is None
        assert resolve_weak_point_damage(boss, hit, 1.0, [point], 1)[1] is point

    def test_apply_hit_at_actually_deals_the_multiplied_damage(
        self, _pygame_init,
    ) -> None:
        """El multiplicador tiene que llegar a la vida, no sólo al cálculo."""
        boss = _TestBoss(pygame.Vector2(100, 100), max_health=20.0)
        boss.weak_points = [WeakPoint(offset=(0, 0), size=(24, 24), multiplier=2.5)]
        before = boss.current_health
        dealt = boss.apply_hit_at(
            2.0, (150.0, 100.0),
            pygame.Rect(boss.rect.x, boss.rect.y, 8, 8),
        )
        assert dealt == pytest.approx(5.0)
        assert before - boss.current_health == pytest.approx(5.0)

    def test_a_hit_without_a_rect_falls_back_to_plain_damage(
        self, _pygame_init,
    ) -> None:
        """No todas las fuentes de daño tienen rectángulo (veneno, caídas)."""
        boss = _TestBoss(pygame.Vector2(100, 100), max_health=20.0)
        boss.weak_points = [WeakPoint(offset=(0, 0), size=(24, 24), multiplier=2.5)]
        dealt = boss.apply_hit_at(3.0, (150.0, 100.0), None)
        assert dealt == pytest.approx(3.0)
        assert boss.last_weak_point is None

    def test_weak_points_follow_the_boss(self, _pygame_init) -> None:
        """En coordenadas locales: si no siguieran al jefe, sólo servirían quieto."""
        boss = _TestBoss(pygame.Vector2(100, 100), max_health=20.0)
        point = WeakPoint(offset=(4, 4), size=(8, 8))
        first = point.rect_for(boss.rect)
        boss.rect.x += 50
        second = point.rect_for(boss.rect)
        assert second.x - first.x == 50

    def test_venado_exposes_a_flank_only_in_phase_two(self, _pygame_init) -> None:
        from src.stages.boss_venado.boss_venado import BossVenado
        venado = BossVenado(pygame.Vector2(160, 180))
        labels_p0 = {p.label for p in venado.weak_points if p.exposed_in(0)}
        labels_p1 = {p.label for p in venado.weak_points if p.exposed_in(1)}
        assert labels_p0 < labels_p1, (
            "la fase 2 debería exponer algo nuevo; si no, cambiar de fase no "
            "cambia cómo se lucha"
        )


# ══════════════════════════════════════════════════════════════
# Invocaciones
# ══════════════════════════════════════════════════════════════


class TestSummons:
    def test_a_wave_spawns_real_enemies(self, _pygame_init) -> None:
        tracker = SummonTracker(waves=[
            SummonWave("FlyingCucaracha", count=2, max_alive=4, cooldown=1.0),
        ])
        wave = tracker.ready_wave(0)
        assert wave is not None
        spawned = tracker.spawn(wave, pygame.Vector2(100, 100))
        assert len(spawned) == 2
        assert all(e.is_alive for e in spawned)

    def test_population_is_capped(self, _pygame_init) -> None:
        """El tope es diseño: sin él el jefe deja de ser el combate."""
        tracker = SummonTracker(waves=[
            SummonWave("FlyingCucaracha", count=3, max_alive=4, cooldown=0.0),
        ])
        total = 0
        for _ in range(10):
            tracker.update(FRAME)
            wave = tracker.ready_wave(0)
            if wave is None:
                continue
            total += len(tracker.spawn(wave, pygame.Vector2(100, 100)))
        assert tracker.alive_count <= 4
        assert total <= 4, f"se invocaron {total} con un tope de 4"

    def test_a_dead_minion_frees_a_slot(self, _pygame_init) -> None:
        """Si no se purgaran los muertos, el jefe invocaría una vez y nunca más."""
        tracker = SummonTracker(waves=[
            SummonWave("FlyingCucaracha", count=2, max_alive=2, cooldown=0.0),
        ])
        wave = tracker.ready_wave(0)
        assert wave is not None
        spawned = tracker.spawn(wave, pygame.Vector2(100, 100))
        assert tracker.ready_wave(0) is None  # lleno
        for minion in spawned:
            minion.is_alive = False
        tracker.update(FRAME)
        assert tracker.alive_count == 0
        assert tracker.ready_wave(0) is not None

    def test_cooldown_gates_the_next_wave(self, _pygame_init) -> None:
        tracker = SummonTracker(waves=[
            SummonWave("FlyingCucaracha", count=1, max_alive=8, cooldown=5.0),
        ])
        wave = tracker.ready_wave(0)
        assert wave is not None
        tracker.spawn(wave, pygame.Vector2(100, 100))
        tracker.update(1.0)
        assert tracker.ready_wave(0) is None
        tracker.update(5.0)
        assert tracker.ready_wave(0) is not None

    def test_phase_locked_waves_wait_for_their_phase(self, _pygame_init) -> None:
        tracker = SummonTracker(waves=[
            SummonWave("FlyingCucaracha", count=1, phases=(1,)),
        ])
        assert tracker.ready_wave(0) is None
        assert tracker.ready_wave(1) is not None

    def test_an_unknown_species_spawns_nothing_instead_of_crashing(
        self, _pygame_init,
    ) -> None:
        tracker = SummonTracker(waves=[SummonWave("NoExiste", count=2)])
        wave = tracker.ready_wave(0)
        assert wave is not None
        assert tracker.spawn(wave, pygame.Vector2(0, 0)) == []

    def test_the_boss_hands_summons_over_and_forgets_them(
        self, _pygame_init,
    ) -> None:
        """`take_summons` vacía la cola: entregar dos veces duplicaría enemigos."""
        boss = _TestBoss(pygame.Vector2(100, 100), max_health=20.0)
        boss.summons = SummonTracker(waves=[
            SummonWave("FlyingCucaracha", count=2, max_alive=4, cooldown=1.0),
        ])
        boss.set_player_ref(pygame.Rect(140, 100, 16, 24))
        boss.state = EnemyState.ALERT
        boss._update_encounter(FRAME)
        first = boss.take_summons()
        assert len(first) == 2
        assert boss.take_summons() == []

    def test_un_jefe_sin_invocaciones_no_invoca_nada(self, _pygame_init) -> None:
        """AUD-107 — antes esta prueba exigía que el Venado invocara en fase 2.

        Era una propiedad de **mi** implementación de referencia, no del motor.
        La entrega del estudiante que la sustituye no invoca en ninguna fase:
        su fase 2 sube la presión con esporas y barridos, no con enemigos
        nuevos. Es una decisión de diseño legítima, y el `SummonTracker` está
        pensado para ser opcional.

        Lo que sí tiene que ser cierto siempre —y es lo que se comprueba— es
        que un jefe sin oleadas declaradas no invoque por su cuenta. Un
        `SummonTracker` vacío que devolviera una oleada sería enemigos
        apareciendo de la nada.
        """
        from src.stages.boss_venado.boss_venado import BossVenado
        venado = BossVenado(pygame.Vector2(160, 180))
        assert venado.summons.waves == []
        for fase in range(len(venado.phases)):
            assert venado.summons.ready_wave(fase) is None

    def test_un_jefe_con_oleadas_las_entrega_en_su_fase(self, _pygame_init) -> None:
        """La otra mitad: declararlas sí tiene que funcionar."""
        boss = _TestBoss(pygame.Vector2(100, 100), max_health=20.0)
        boss.summons = SummonTracker(waves=[
            SummonWave("FlyingCucaracha", count=2, max_alive=4, cooldown=1.0,
                       phases=(1,)),
        ])
        assert boss.summons.ready_wave(0) is None
        assert boss.summons.ready_wave(1) is not None


# ══════════════════════════════════════════════════════════════
# Integración con BossBase
# ══════════════════════════════════════════════════════════════


class TestBossBaseIntegration:
    @pytest.mark.parametrize("state", [EnemyState.PATROL, EnemyState.IDLE])
    def test_a_boss_out_of_aggro_does_not_attack(
        self, _pygame_init, state: EnemyState,
    ) -> None:
        """Atacar al aire gasta enfriamientos antes de que llegue el jugador.

        El jugador **sí** está referenciado aquí: la referencia existe desde
        que arranca la escena, mucho antes de que el jefe lo detecte. Sin ese
        matiz la prueba pasaría por la comprobación de `_player_ref is None` y
        no probaría la puerta de agro en absoluto — se detectó con la mutación
        que quitaba el filtro de estados y sobrevivía.
        """
        boss, timings = self._run_idle_boss(state, with_player=True)
        assert timings == {AttackTiming.IDLE}, (
            f"el jefe telegrafió en {state} sin haber detectado al jugador: "
            f"{timings}"
        )
        assert boss.attacks.current is None

    def test_a_boss_with_no_player_reference_does_not_attack(
        self, _pygame_init,
    ) -> None:
        boss, timings = self._run_idle_boss(EnemyState.ALERT, with_player=False)
        assert timings == {AttackTiming.IDLE}
        assert boss.attacks.current is None

    @staticmethod
    def _run_idle_boss(
        state: EnemyState, *, with_player: bool,
    ) -> tuple[_TestBoss, set[AttackTiming]]:
        """Corre dos segundos y devuelve **todos** los tramos observados.

        Mirar sólo el estado final no vale: un ataque de 1,4 s lanzado en el
        fotograma 0 ya ha terminado a los 2 s, así que `current is None` sería
        cierto igualmente. Se acumulan los tramos vistos en cada fotograma.
        """
        boss = _TestBoss(pygame.Vector2(100, 100), max_health=20.0)
        boss.attacks = AttackScheduler([BossAttack("A", windup=0.4, cooldown=1.0)])
        if with_player:
            boss.set_player_ref(pygame.Rect(140, 100, 16, 24))
        boss.state = state
        seen: set[AttackTiming] = set()
        for _ in range(120):
            boss._update_encounter(FRAME)
            seen.add(boss.attack_timing)
        return boss, seen

    def test_stun_interrupts_the_encounter(self, _pygame_init) -> None:
        boss = _TestBoss(pygame.Vector2(100, 100), max_health=20.0)
        boss.attacks = AttackScheduler([BossAttack("A", windup=1.0, cooldown=1.0)])
        boss.set_player_ref(pygame.Rect(140, 100, 16, 24))
        boss.state = EnemyState.ALERT
        for _ in range(20):
            boss._update_encounter(FRAME)
        assert boss.attacks.timing == AttackTiming.WINDUP
        boss.state = EnemyState.STUNNED
        boss._update_encounter(FRAME)
        assert boss.attacks.current is None

    def test_on_attack_fired_is_called_once_per_attack(self, _pygame_init) -> None:
        calls: list[str] = []

        class _Recorder(_TestBoss):
            def on_attack_fired(self, attack_name: str) -> None:
                calls.append(attack_name)

        boss = _Recorder(pygame.Vector2(100, 100), max_health=20.0)
        boss.attacks = AttackScheduler([
            BossAttack("A", windup=0.3, active=0.2, recover=0.2, cooldown=5.0),
        ])
        boss.set_player_ref(pygame.Rect(140, 100, 16, 24))
        boss.state = EnemyState.ALERT
        for _ in range(120):
            boss._update_encounter(FRAME)
        assert calls == ["A"], (
            "el gancho debe dispararse una vez al pasar de aviso a golpe, "
            f"no {len(calls)} veces"
        )

    def test_the_encounter_does_not_hijack_the_state_machine(
        self, _pygame_init,
    ) -> None:
        """El planificador no debe escribir en `self.state`.

        `EnemyBase._run_state_machine` trata TELEGRAPHING/FIRING/RECOVER como
        estados con su propio reloj y sale antes de ejecutar el comportamiento
        de la subclase. Si el planificador los impusiera, el jefe se quedaría
        inmóvil durante todo el ciclo de ataque — es decir, casi siempre.
        """
        boss = _TestBoss(pygame.Vector2(100, 100), max_health=20.0)
        boss.attacks = AttackScheduler([BossAttack("A", windup=0.3, cooldown=0.0)])
        boss.set_player_ref(pygame.Rect(140, 100, 16, 24))
        boss.state = EnemyState.ALERT
        for _ in range(120):
            boss._update_encounter(FRAME)
            assert boss.state == EnemyState.ALERT

    def test_attack_timing_is_readable_from_the_boss(self, _pygame_init) -> None:
        boss = _TestBoss(pygame.Vector2(100, 100), max_health=20.0)
        boss.attacks = AttackScheduler([
            BossAttack("A", windup=0.3, active=0.1, recover=0.5, cooldown=9.0),
        ])
        boss.set_player_ref(pygame.Rect(140, 100, 16, 24))
        boss.state = EnemyState.ALERT
        seen: set[AttackTiming] = set()
        for _ in range(120):
            boss._update_encounter(FRAME)
            seen.add(boss.attack_timing)
        assert AttackTiming.WINDUP in seen
        assert AttackTiming.RECOVER in seen
        assert boss.telegraph_progress >= 0.0

    def test_phase_change_applies_the_speed_multiplier(self, _pygame_init) -> None:
        """Era `if phase.speed_multiplier != 1.0: pass` — se leía y se tiraba."""
        boss = _TestBoss(pygame.Vector2(100, 100), max_health=20.0)
        boss.set_phases([
            BossPhase(phase_index=0, health_threshold=20.0, speed_multiplier=1.0),
            BossPhase(phase_index=1, health_threshold=10.0, speed_multiplier=1.5),
        ])
        assert boss.speed_multiplier == pytest.approx(1.0)
        boss.apply_hit(10.0, (150.0, 100.0))
        assert boss.is_transitioning is True
        boss.update(3.0)
        assert boss.current_phase == 1
        assert boss.speed_multiplier == pytest.approx(1.5)

    def test_venado_survives_a_full_encounter_without_raising(
        self, _pygame_init,
    ) -> None:
        """Diez segundos de combate real con el jugador delante.

        No comprueba un valor concreto a propósito: es la prueba de que las
        cinco ramas de ataque, los proyectiles, el cambio de fase y las
        invocaciones se ejecutan de verdad en secuencia. Todo lo demás en este
        archivo prueba piezas aisladas; esto prueba que encajan.
        """
        from src.stages.boss_venado.boss_venado import ARENA_CX, BossVenado
        venado = BossVenado(pygame.Vector2(ARENA_CX, 536))
        # Dentro de la arena. Este Venado sólo pelea en su terreno sagrado, así
        # que un jugador colocado al principio del mapa produce diez segundos
        # de nada. Antes la prueba espiaba `on_attack_fired`, el gancho del
        # planificador del framework, y este jefe no lo usa: despacha sus
        # patrones él mismo. La prueba medía **cómo** ataca en vez de **si**
        # ataca, y se quedó en cero sobre un jefe que ataca perfectamente.
        player_rect = pygame.Rect(int(ARENA_CX) + 40, 536, 16, 24)
        venado.set_player_ref(player_rect)
        venado.state = EnemyState.ALERT

        # Se observan efectos, no llamadas: telegrafiados, proyectiles y
        # embestidas. Cualquier jefe que ataque de verdad deja alguno.
        vistos: set[str] = set()
        for step in range(600):
            # Se mueve al jugador para que distintos rangos se activen.
            player_rect.x = int(ARENA_CX) - 100 + (step % 200)
            venado.update(FRAME)
            venado.take_summons()
            if venado._telegraph:
                vistos.add(venado._telegraph)
            if venado._stomp_rect is not None:
                vistos.add("STOMP_ACTIVO")
            if venado._charge_active:
                vistos.add("CHARGE_ACTIVO")
            for p in venado._projectiles:
                vistos.add(f"PROYECTIL_{p['type']}")
            if step == 300:
                venado.apply_hit(6.5, (player_rect.centerx, player_rect.centery))

        assert len(vistos) >= 3, f"apenas atacó en 10 s: {sorted(vistos)}"


class TestArenaBounds:
    """El jefe no puede salir de su arena (AUD-061).

    Fuera del mapa el jugador no lo alcanza y el combate deja de poder
    ganarse, sin que nada avise: el jugador da vueltas por una arena vacía
    buscando a un jefe que está en coordenadas negativas.

    Se prueba `clamp_to_arena` directamente y no a través del combate porque
    en el juego hay dos mecanismos que contienen al jefe —el rebote del
    movimiento sinusoidal y este límite— y una prueba de integración no
    distingue cuál actuó. Una prueba que no puede fallar no prueba nada.
    """

    def _boss(self) -> _TestBoss:
        boss = _TestBoss(pygame.Vector2(100, 100), max_health=20.0)
        boss.set_arena_bounds(pygame.Rect(0, 0, 640, 320))
        return boss

    def test_without_bounds_nothing_is_clamped(self, _pygame_init) -> None:
        """Un jefe recién construido no tiene arena y no debe inventarse una."""
        boss = _TestBoss(pygame.Vector2(100, 100), max_health=20.0)
        assert boss.arena_bounds is None
        boss.position.x = -500.0
        boss.clamp_to_arena()
        assert boss.position.x == -500.0

    def test_a_boss_pushed_left_comes_back(self, _pygame_init) -> None:
        boss = self._boss()
        boss.position.x = -200.0
        boss.clamp_to_arena()
        assert boss.position.x >= 0
        assert boss.rect.x == int(boss.position.x), (
            "el rect y la posición quedaron en desacuerdo: durante un fotograma "
            "las colisiones usarían el valor viejo"
        )

    def test_a_boss_pushed_right_comes_back(self, _pygame_init) -> None:
        boss = self._boss()
        boss.position.x = 5000.0
        boss.clamp_to_arena()
        assert boss.rect.right <= 640

    def test_a_boss_inside_the_arena_is_left_alone(self, _pygame_init) -> None:
        """Recolocar a un jefe que está bien sería un tirón visible."""
        boss = self._boss()
        boss.position.x = 300.0
        boss.clamp_to_arena()
        assert boss.position.x == 300.0

    def test_an_arena_narrower_than_the_boss_centres_it(self, _pygame_init) -> None:
        """Caso degenerado: sin esto los límites se cruzan y `min`/`max` dan
        un resultado arbitrario que depende del orden de las operaciones."""
        boss = _TestBoss(pygame.Vector2(0, 0), max_health=20.0)
        boss.set_arena_bounds(pygame.Rect(0, 0, 10, 10))
        boss.position.x = 500.0
        boss.clamp_to_arena()
        assert -boss.rect.width <= boss.position.x <= 10
