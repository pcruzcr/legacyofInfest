"""Tests for the rewritten VENADO SAGRADO boss (Evaluación Práctica I)."""
import math

import pygame

from src.engine.core.event_bus import EventBus
from src.engine.core.events import Events
from src.framework.entities.boss_kit import WeakPoint, resolve_weak_point_damage
from src.framework.entities.enemy_base import EnemyState
from src.stages.boss_venado import boss_venado as bv
from src.stages.boss_venado.boss_venado import BossVenado

DT = 1.0 / 60.0


def make_boss(with_bus: bool = False):
    boss = BossVenado(pygame.Vector2(3168, 240))
    bus = None
    if with_bus:
        bus = EventBus()
        boss.set_event_bus(bus)
    return boss, bus


def test_phases_official_config():
    boss, _ = make_boss()
    assert boss.max_health == 12.0
    assert [p.health_threshold for p in boss.phases] == [12.0, 6.0]
    assert boss.phases[0].attack_patterns == ["STOMP", "CHARGE", "VINE_TOSS"]
    assert boss.phases[1].attack_patterns == ["VINE_SWEEP", "MUSHROOM_SPORE", "CHARGE"]
    assert boss.phases[0].movement_type == "sine"
    assert boss.phases[1].movement_type == "bezier"
    assert boss.phases[1].speed_multiplier == 1.5
    assert boss.boss_name == "VENADO SAGRADO"


def test_constructor_contract_loader():
    """The TMX loader calls BossVenado(Vector2(x, y)) with no kwargs — must work as-is."""
    boss = BossVenado(pygame.Vector2(0, 0))
    assert boss.is_alive


def test_hitbox_hurtbox_spec():
    boss, _ = make_boss()
    assert boss._build_hitbox() == pygame.Rect(6, 4, 36, 44)     # 17_BOSS_SPEC §3.2
    # LOCAL space (enemy_base.py: _build_hitbox/_build_hurtbox docstrings +
    # _update_rects offsets by self.position) — 30x40 centered in the 48x48 sprite.
    assert boss._build_hurtbox() == pygame.Rect(9, 4, 30, 40)


def test_detection_is_arena_gated():
    """Design fix: the deer must NOT snipe VINE_TOSS at a player still
    walking the corridor -- it only aggros once they near the arena mouth
    (AGGRO_X = ARENA_X0 - 96), not the instant player_ref exists (which
    the loader/CollisionSystem set from frame 1, long before the arena)."""
    boss, _ = make_boss()
    assert boss._check_detection_range() is False       # no player_ref yet
    boss.set_player_ref(pygame.Rect(500, 528, 20, 32))   # corridor, far from arena
    assert boss._check_detection_range() is False
    boss.set_player_ref(pygame.Rect(2300, 528, 20, 32))  # corridor, still short of AGGRO_X=2384
    assert boss._check_detection_range() is False
    boss.set_player_ref(pygame.Rect(2400, 528, 20, 32))  # past AGGRO_X=2384: arena mouth
    assert boss._check_detection_range() is True
    boss.set_player_ref(pygame.Rect(2600, 528, 20, 32))  # inside the arena
    assert boss._check_detection_range() is True
    boss.set_player_ref(pygame.Rect(3200, 528, 20, 32))  # deep inside the arena
    assert boss._check_detection_range() is True


def test_no_attacks_fire_outside_arena():
    """Design fix companion: with detection arena-gated, a boss that never
    goes ALERT must never reach _try_attack at all -- no projectile, no
    telegraph, no charge, regardless of how open every cooldown is.
    Checked EVERY frame (not just the final one): CHARGE's own telegraph/
    dash/wall-pause cycle can transiently clear _telegraph back to "" on
    its own timing, which would make a final-frame-only check pass by
    coincidence without ever proving VINE_TOSS (the reported bug -- no
    range limit, ~2500px Bezier arc) never fired at the corridor."""
    boss, _ = make_boss()
    boss.set_player_ref(pygame.Rect(500, 528, 20, 32))   # corridor, far from arena
    for k in boss._attack_timers:
        boss._attack_timers[k] = 0.0
    for _ in range(180):                                  # 3s: plenty for any cooldown to retry
        boss.update(DT)
        assert boss._projectiles == [], "a projectile fired while the player was outside the arena"
        assert boss._telegraph == "", "an attack telegraph started while the player was outside the arena"
        assert not boss._charge_active, "CHARGE fired while the player was outside the arena"


def test_no_engine_v2_auto_retreat_at_low_health():
    """ENGINE V2 regression: EnemyBase._should_retreat (enemy_base.py) forces
    state=RETREAT once current_health <= 25% of max_health (with max_health=
    12.0, that's <=3.0 -- squarely inside phase 2), and the generic
    _retreat_behavior walks away from the player with no ARENA_X0/X1 clamp, so
    it can push the Venado clean out of the arena. The official design (17_
    BOSS_SPEC §3) has no retreat state; boss_venado.BossVenado._should_retreat
    overrides the hook to keep phase 2's figure-8 pattern authoritative."""
    boss, _ = make_boss()
    boss.current_health = 2.0                             # deep in phase 2's low-health band
    boss.set_player_ref(pygame.Rect(2600, 528, 20, 32))    # inside the arena, in detection range
    assert boss._should_retreat() is False
    for _ in range(120):                                   # 2s: plenty for the state machine to settle
        boss.update(DT)
        assert boss.state != EnemyState.RETREAT
    assert boss._should_retreat() is False


def test_alert_behavior_keeps_running_under_chase_state(monkeypatch):
    """V2 recert triage (2026-07-29): investigated hypothesis that ENGINE
    V2's rewritten EnemyBase._run_state_machine (SEARCH/CHASE/RECOVER/
    RETREAT/STUNNED) routes an in-range boss to CHASE instead of ALERT
    and, in CHASE, skips `_alert_behavior` entirely -- leaving the boss to
    persecute genericamente and hit only via `damage_on_contact` instead
    of running its designed attack patterns (motivated by
    v2_recert_dodger2: 15 damage_on_contact=0.75 hits, all correlated
    with CHARGE).

    REFUTED by reading `_run_state_machine` directly (enemy_base.py,
    ~lines 763-782): `self._alert_behavior(dt)` is called
    UNCONDITIONALLY whenever `player_in_range` is True, regardless of
    whether `self.state` ends up ALERT or CHASE -- the state label only
    changes for animation/SFX purposes (its own docstring: "ALERT es el
    primer fotograma de detección; a partir de ahí es CHASE"). The real
    cause of the dodger hits was a DIFFERENT, bot-side bug
    (playtest/bots.py's `_on_attack` arming a 45f generic reactive dodge
    on CHARGE too, hijacking `_decide_charge_dodge`'s dedicated timed
    jump -- fixed there, not here).

    This test locks the refutation with a direct call-count (not an
    indirect physics invariant like the sine formula -- a first attempt
    at that broke on the very first run: CHARGE/STOMP legitimately
    override `position.y` while active, which isn't a regression, so
    asserting the pure sine curve produces false positives whenever an
    attack happens to fire during the sampled window)."""
    calls: dict[str, int] = {}
    orig_alert_behavior = BossVenado._alert_behavior

    def counting_alert_behavior(self, dt):
        key = self.state.name
        calls[key] = calls.get(key, 0) + 1
        return orig_alert_behavior(self, dt)

    monkeypatch.setattr(BossVenado, "_alert_behavior", counting_alert_behavior)

    boss, _ = make_boss()
    boss.set_player_ref(pygame.Rect(2600, 528, 20, 32))   # inside arena, in detection range
    boss.update(DT)
    assert boss.state == EnemyState.ALERT, "primer frame en rango: debe ser ALERT (sanity)"
    for _ in range(30):
        boss.update(DT)
        assert boss.state == EnemyState.CHASE, \
            "el boss debe permanecer en CHASE con el player fijo dentro del rango"
    assert calls.get("ALERT", 0) >= 1, "sanity: _alert_behavior no corrió durante ALERT"
    assert calls.get("CHASE", 0) >= 25, (
        f"REGRESIÓN: _alert_behavior dejó de ejecutarse bajo CHASE (conteo real={calls})")


def test_spawn_rect_and_feet_anchor():
    """TMX spawn Y is the FEET line; engine pattern converts it to top-left."""
    boss = BossVenado(pygame.Vector2(3168, 240))
    assert boss.rect.size == (48, 48)
    assert boss.position.y == 240 - 48
    assert boss.rect.topleft == (3168, 192)


def test_sine_drift_formula():
    boss, _ = make_boss()
    for _ in range(30):
        boss._update_movement(DT)
    expected_y = bv.BASE_Y + bv.SINE_AMPLITUDE * math.sin(
        2 * math.pi * bv.SINE_FREQ * boss._elapsed)
    assert abs(boss.position.y - expected_y) < 1e-6
    assert boss._elapsed > 0


def test_sine_stays_reachable_and_in_arena():
    boss, _ = make_boss()
    min_x, max_x, max_bottom = 1e9, -1e9, -1e9
    for _ in range(int(6.0 / DT)):        # more than 2 full periods
        boss._update_movement(DT)
        min_x = min(min_x, boss.position.x)
        max_x = max(max_x, boss.position.x)
        max_bottom = max(max_bottom, boss.position.y + 48)
    assert min_x >= bv.ARENA_X0 + 32 - 1e-6
    assert max_x <= bv.ARENA_X1 - 80 + 1e-6
    assert 520.0 <= max_bottom <= bv.FLOOR_Y - 8   # melee-reachable window (fix H-04/H-08)


def test_stomp_trigger_telegraph_window():
    boss, _ = make_boss()
    pr = pygame.Rect(int(boss.rect.centerx) - 60, 528, 20, 32)   # within 96 px
    boss.set_player_ref(pr)
    boss._try_attack("STOMP")
    assert boss._telegraph == "STOMP" and boss._telegraph_timer == bv.STOMP_TELEGRAPH
    assert boss._attack_timers["STOMP"] == boss._attack_cooldowns["STOMP"]
    for _ in range(int(bv.STOMP_TELEGRAPH / DT) + 1):
        boss._update_attack_state(DT)
    assert boss._stomp_rect is not None
    assert boss._stomp_rect.width == 96 and boss._stomp_rect.y == int(bv.FLOOR_Y) - 8
    for _ in range(int(bv.STOMP_WINDOW / DT) + 1):
        boss._update_attack_state(DT)
    assert boss._stomp_rect is None                     # window closed (fixes base bug)


def test_stomp_not_triggered_far():
    boss, _ = make_boss()
    boss.set_player_ref(pygame.Rect(int(boss.rect.centerx) - 300, 528, 20, 32))
    boss._try_attack("STOMP")
    assert boss._telegraph == ""
    assert boss._attack_timers["STOMP"] == 0.0


def test_charge_trigger_opposite_half_and_direction():
    boss, _ = make_boss()                                   # spawn 3168 (right half)
    boss.set_player_ref(pygame.Rect(2500, 528, 20, 32))     # left half
    boss._try_attack("CHARGE")
    assert boss._telegraph == "CHARGE"
    for _ in range(int(bv.CHARGE_TELEGRAPH / DT) + 1):
        boss._update_attack_state(DT)
    assert boss._charge_active and boss._charge_direction == -1


def test_charge_same_half_no_trigger():
    boss, _ = make_boss()
    boss.set_player_ref(pygame.Rect(3000, 528, 20, 32))     # same right half
    boss._try_attack("CHARGE")
    assert boss._telegraph == "" and not boss._charge_active


def test_charge_speed_by_phase_and_wall_stop():
    boss, _ = make_boss()
    boss._charge_active, boss._charge_direction = True, -1
    x0 = boss.position.x
    boss._update_charge(DT)
    assert abs((x0 - boss.position.x) - bv.CHARGE_SPEED_P1 * DT) < 1e-6
    boss.current_phase = 1
    x1 = boss.position.x
    boss._update_charge(DT)
    assert abs((x1 - boss.position.x) - bv.CHARGE_SPEED_P2 * DT) < 1e-6
    boss.position.x = bv.ARENA_X0 + 17
    boss._update_charge(1.0)
    assert not boss._charge_active                          # stopped at the wall


def test_charge_emits_boss_attack_event():
    """H-08 parity with STOMP: CHARGE must announce itself too, or nothing
    observable (event-driven bots/tests included) can ever detect it fired."""
    boss, bus = make_boss(with_bus=True)
    received = []
    # ENGINE V2: EventBus.subscribe() holds only a weak reference (event_bus.py
    # _Subscription -- weakref.ref for plain callables). A lambda passed inline
    # with no other referent is collected before the next dispatch() and the
    # subscription silently drops (logged as "dropping collected subscriber").
    # Keeping it bound to a local name keeps it alive for the test's lifetime.
    on_attack = lambda **kw: received.append(kw)  # noqa: E731
    bus.subscribe(Events.BOSS_ATTACK, on_attack)
    boss.set_player_ref(pygame.Rect(2500, 528, 20, 32))     # left half
    boss._try_attack("CHARGE")
    for _ in range(int(bv.CHARGE_TELEGRAPH / DT) + 1):
        boss._update_attack_state(DT)
    assert boss._charge_active
    bus.dispatch()
    assert received and received[-1]["pattern"] == "CHARGE"


def test_stomp_plants_boss_to_ground_during_window():
    """H-04 design fix: STOMP must lower the boss all the way to the floor
    (spec §3.3 'at floor level') during the telegraph + punish window --
    that's the melee-vulnerability window the spec (and the QA bots) expect.
    Settles the sine drift first (real fights never STOMP right at spawn
    height -- enter_arena() in the playtest harness settles 120f before any
    attack can trigger) so the boss starts in its normal oscillation band,
    same as in-game, rather than testing an unreachable full 192->560 climb
    the window's time budget was never meant to cover."""
    boss, _ = make_boss()
    far_pr = pygame.Rect(int(boss.rect.centerx) + 1000, 528, 20, 32)  # far: no auto-trigger while settling
    boss.set_player_ref(far_pr)
    for _ in range(90):             # 1.5s: let the sine settle into its normal band
        boss.update(DT)
    pr = pygame.Rect(int(boss.rect.centerx) - 60, 528, 20, 32)        # now bring the player close
    boss.set_player_ref(pr)
    boss._try_attack("STOMP")
    reached_floor = False
    for _ in range(int((bv.STOMP_TELEGRAPH + bv.STOMP_WINDOW) / DT) + 2):
        boss.update(DT)
        if boss.rect.bottom >= int(bv.FLOOR_Y):
            reached_floor = True
            break
    assert reached_floor, (
        f"boss never planted to the ground during STOMP: rect.bottom={boss.rect.bottom}")
    assert boss.rect.bottom == int(bv.FLOOR_Y)


def test_charge_sweeps_into_melee_band():
    """H-08 design fix: CHARGE must lower the boss into the player's melee
    band while dashing, not just cross the arena at whatever height the sine
    left it -- the spec's contact-damage wall-stop only makes physical sense
    at that height. Starts the boss at ARENA_CX (room on both sides) so the
    dash doesn't wall-stop before the (much faster) vertical sweep finishes --
    a boss spawned right next to a wall stopping in 2-3 frames is a test-setup
    artifact, not something the real trigger geometry (CHARGE only fires
    dx>=ARENA_W//2 away) ever produces."""
    boss, _ = make_boss()
    boss.position.x = bv.ARENA_CX
    boss.position.y = bv.BASE_Y - bv.SINE_AMPLITUDE   # start at the sine's high point (far from the band)
    boss._charge_active, boss._charge_direction = True, 1
    for _ in range(int(2.0 / DT)):                    # charge itself only lasts a fraction of this
        boss._update_charge(DT)
        if not boss._charge_active:                   # wall-stop: band sweep already applied this frame
            break
    assert boss.position.y + 48 >= 540, (
        f"boss never swept into the melee band during CHARGE: rect.bottom={boss.position.y + 48}")


def test_y_recovery_after_attack_is_bounded_no_teleport():
    """H-04/H-08 recovery contract: once an attack ends, the boss eases back
    toward the sine formula at VERTICAL_ATTACK_SPEED, it never snaps/
    teleports back in a single frame.

    UPDATED for the Hallazgo C fix (grounded punish recover, FINDINGS.md):
    the shockwave window closing no longer arms _y_recovering directly --
    the boss now spends STOMP_RECOVER seconds planted and harmless first (a
    real punish window, see test_stomp_has_grounded_punish_recover below),
    THEN eases back. This test drives through that recover phase before
    checking the original bounded-step contract, which is otherwise
    unchanged."""
    boss, _ = make_boss()
    far_pr = pygame.Rect(int(boss.rect.centerx) + 1000, 528, 20, 32)
    boss.set_player_ref(far_pr)
    for _ in range(90):
        boss.update(DT)
    pr = pygame.Rect(int(boss.rect.centerx) - 60, 528, 20, 32)
    boss.set_player_ref(pr)
    boss._try_attack("STOMP")
    for _ in range(int((bv.STOMP_TELEGRAPH + bv.STOMP_WINDOW) / DT) + 2):
        boss.update(DT)
    assert boss._stomp_rect is None                    # shockwave window closed
    assert boss._stomp_recover > 0, "grounded punish recover never armed"
    assert not boss._y_recovering, "recovery should wait for the punish recover, not start immediately"

    for _ in range(int(bv.STOMP_RECOVER / DT) + 3):     # drive through the new punish recover
        if boss._stomp_recover <= 0:
            break
        boss.update(DT)
    assert boss._y_recovering, "recovery flag never armed once the punish recover ended"

    eps = 1e-6
    max_step = bv.VERTICAL_ATTACK_SPEED * DT + eps
    for _ in range(int(2.0 / DT)):
        y_before = boss.position.y
        boss.update(DT)
        assert abs(boss.position.y - y_before) <= max_step, (
            f"y jumped {abs(boss.position.y - y_before):.3f}px in one frame "
            f"(max allowed {max_step:.3f}) -- recovery teleported instead of easing")
        if not boss._y_recovering:
            break
    assert not boss._y_recovering, "recovery never finished re-locking to the sine formula"


def test_stomp_has_grounded_punish_recover():
    """Hallazgo C fix (FINDINGS.md): the boss reescrito had no safe remnant
    after the shockwave -- the melee reach lived entirely inside the
    shockwave's own radius the whole time _stomp_window was alive, so
    "wait until it's safe, then hit it" was not a strategy that existed for
    this attack. Now the window closing arms a grounded, harmless
    STOMP_RECOVER punish phase: boss stays planted at the floor, the
    shockwave stays gone, and no new attack can start."""
    boss, _ = make_boss()
    far_pr = pygame.Rect(int(boss.rect.centerx) + 1000, 528, 20, 32)
    boss.set_player_ref(far_pr)
    for _ in range(90):
        boss.update(DT)
    pr = pygame.Rect(int(boss.rect.centerx) - 60, 528, 20, 32)
    boss.set_player_ref(pr)
    boss._try_attack("STOMP")
    for _ in range(int((bv.STOMP_TELEGRAPH + bv.STOMP_WINDOW) / DT) + 2):
        boss.update(DT)

    assert boss._stomp_rect is None, "shockwave should already be gone"
    assert boss._stomp_recover > 0, "grounded punish recover never armed"
    assert boss.rect.bottom == int(bv.FLOOR_Y), "boss should stay planted during the punish recover"
    assert not boss._y_recovering, "recovery should wait for the punish recover to end"

    # No new attack should be able to start while grounded and recovering --
    # move the player to the opposite half (a valid CHARGE trigger) and
    # force every cooldown open, then drive alert behavior directly.
    boss.set_player_ref(pygame.Rect(int(bv.ARENA_X0) + 10, 528, 20, 32))
    for k in boss._attack_timers:
        boss._attack_timers[k] = 0.0
    boss._alert_behavior(DT)
    assert boss._telegraph == "" and not boss._charge_active, (
        "a new attack started during the grounded punish recover")

    recover_frames = int(bv.STOMP_RECOVER / DT) + 3
    for _ in range(recover_frames):
        if boss._stomp_recover <= 0:
            break
        assert boss.rect.bottom == int(bv.FLOOR_Y), "boss left the floor before recover expired"
        assert boss._stomp_rect is None, "shockwave should stay gone during recover"
        boss.update(DT)
    assert boss._stomp_recover <= 0
    assert boss._y_recovering, "y_recovering never armed once the punish recover expired"


def test_charge_wall_pause_is_stationary_punish_window():
    """Hallazgo C fix, CHARGE side: the dash used to hand off straight to
    _y_recovering the instant it hit the wall, with no observable pause at
    all -- now it holds still at the wall (band height) for
    CHARGE_WALL_PAUSE seconds, a second stationary punish window mirroring
    STOMP's grounded recover."""
    boss, _ = make_boss()
    boss.position.x = bv.ARENA_X0 + 17
    boss._charge_active, boss._charge_direction = True, -1
    boss._update_charge(1.0)                       # large dt: guarantees the wall-stop this frame
    assert not boss._charge_active
    assert boss._charge_recover > 0, "wall pause never armed"
    assert not boss._y_recovering, "recovery should wait for the wall pause, not start immediately"

    x_at_wall = boss.position.x
    y_at_wall = boss.position.y
    recover_frames = int(bv.CHARGE_WALL_PAUSE / DT) + 3
    saw_pause = False
    for _ in range(recover_frames):
        boss.update(DT)
        # Checked AFTER update (not before): the frame where _charge_recover
        # decays past 0 legitimately resumes movement within that same
        # update() call (recover is ticked in _update_attack_state, which
        # runs before _update_movement reads it) -- same boundary as
        # test_no_horizontal_drift_during_stomp_cycle below.
        still_paused = boss._charge_recover > 0
        if still_paused:
            saw_pause = True
            assert boss.position.x == x_at_wall, "boss drifted horizontally during the CHARGE wall pause"
            assert boss.position.y == y_at_wall, "boss should stay at band height during the wall pause"
            assert not boss._charge_active, "a new CHARGE should not restart during its own wall pause"
        else:
            break
    assert saw_pause, "wall pause never observed active during the loop"
    assert boss._charge_recover <= 0
    assert boss._y_recovering, "y_recovering never armed once the CHARGE wall pause expired"


def test_no_horizontal_drift_during_stomp_cycle():
    """Hallazgo C fix: the old sine drift kept adding to position.x
    throughout the whole STOMP telegraph+window(+recover), undermining the
    bots' assumption of a quasi-static punish target -- the old boss froze
    X during STOMP, this one didn't (FINDINGS.md Hallazgo C, point 1)."""
    boss, _ = make_boss()
    far_pr = pygame.Rect(int(boss.rect.centerx) + 1000, 528, 20, 32)
    boss.set_player_ref(far_pr)
    for _ in range(90):
        boss.update(DT)
    pr = pygame.Rect(int(boss.rect.centerx) - 60, 528, 20, 32)
    boss.set_player_ref(pr)
    boss._try_attack("STOMP")
    x0 = boss.position.x
    total_frames = int((bv.STOMP_TELEGRAPH + bv.STOMP_WINDOW + bv.STOMP_RECOVER) / DT) + 4
    saw_recover = False
    for _ in range(total_frames):
        boss.update(DT)
        still_in_cycle = (boss._telegraph == "STOMP" or boss._stomp_window > 0
                           or boss._stomp_recover > 0)
        if boss._stomp_recover > 0:
            saw_recover = True
        if still_in_cycle:
            assert boss.position.x == x0, "boss drifted horizontally during the STOMP punish cycle"
        else:
            break
    assert saw_recover, "recover window never armed -- test didn't exercise the full cycle"


def test_projectile_attacks_emit_boss_attack():
    """Hallazgo D fix (FINDINGS.md): VINE_TOSS/MUSHROOM_SPORE must announce
    themselves too, same as STOMP/CHARGE, or the dodger bot is structurally
    blind to them (measured: 0 frames of warning, 4/5 hits in f2_dodger_recal
    were unannounced VINE_TOSS)."""
    boss, bus = make_boss(with_bus=True)
    received = []
    # ENGINE V2: keep the handler alive -- see test_charge_emits_boss_attack_event.
    on_attack = lambda **kw: received.append(kw)  # noqa: E731
    bus.subscribe(Events.BOSS_ATTACK, on_attack)
    pr = pygame.Rect(2600, 528, 20, 32)

    boss._do_vine_toss(pr)
    bus.dispatch()
    assert received and received[-1]["pattern"] == "VINE_TOSS"
    assert received[-1]["rect"].size == (10, 10)

    boss._do_mushroom_spore(pr)
    bus.dispatch()
    assert received[-1]["pattern"] == "MUSHROOM_SPORE"
    assert received[-1]["rect"] == boss.rect


def test_stomp_emits_sfx_event():
    """Feature A (SFX): STOMP must emit SFX_BOSSES_VENADO_STOMP at the same
    resolution point where it already emits BOSS_ATTACK (_do_stomp)."""
    boss, bus = make_boss(with_bus=True)
    received = []
    on_sfx = lambda **kw: received.append(kw)  # noqa: E731
    bus.subscribe(Events.SFX_BOSSES_VENADO_STOMP, on_sfx)
    pr = pygame.Rect(int(boss.rect.centerx) - 60, 528, 20, 32)   # within 96 px
    boss.set_player_ref(pr)
    boss._try_attack("STOMP")
    for _ in range(int(bv.STOMP_TELEGRAPH / DT) + 1):
        boss._update_attack_state(DT)
    bus.dispatch()
    assert received, "STOMP never emitted SFX_BOSSES_VENADO_STOMP"


def test_charge_emits_sfx_event():
    """Feature A (SFX): CHARGE must emit SFX_BOSSES_VENADO_CHARGE at the same
    resolution point where it already emits BOSS_ATTACK (_do_charge)."""
    boss, bus = make_boss(with_bus=True)
    received = []
    on_sfx = lambda **kw: received.append(kw)  # noqa: E731
    bus.subscribe(Events.SFX_BOSSES_VENADO_CHARGE, on_sfx)
    boss.set_player_ref(pygame.Rect(2500, 528, 20, 32))     # left half
    boss._try_attack("CHARGE")
    for _ in range(int(bv.CHARGE_TELEGRAPH / DT) + 1):
        boss._update_attack_state(DT)
    bus.dispatch()
    assert received, "CHARGE never emitted SFX_BOSSES_VENADO_CHARGE"


def test_vine_toss_emits_sfx_event():
    """Feature A (SFX): VINE_TOSS must emit SFX_BOSSES_VENADO_VINE at launch
    (_do_vine_toss), the same instant it already emits BOSS_ATTACK."""
    boss, bus = make_boss(with_bus=True)
    received = []
    on_sfx = lambda **kw: received.append(kw)  # noqa: E731
    bus.subscribe(Events.SFX_BOSSES_VENADO_VINE, on_sfx)
    boss._do_vine_toss(pygame.Rect(2600, 528, 20, 32))
    bus.dispatch()
    assert received, "VINE_TOSS never emitted SFX_BOSSES_VENADO_VINE"


def test_vine_sweep_emits_sfx_event():
    """Feature A (SFX): VINE_SWEEP must emit SFX_BOSSES_VENADO_VINE (reused --
    only 3 Venado wavs exist) when its punish window opens, even though this
    attack deliberately does NOT emit BOSS_ATTACK there (Hallazgo D candado)."""
    boss, bus = make_boss(with_bus=True)
    received = []
    on_sfx = lambda **kw: received.append(kw)  # noqa: E731
    bus.subscribe(Events.SFX_BOSSES_VENADO_VINE, on_sfx)
    boss.set_player_ref(pygame.Rect(2600, 528, 20, 32))  # _try_attack no-ops without a player_ref
    boss._try_attack("VINE_SWEEP")
    for _ in range(int(bv.SWEEP_TELEGRAPH / DT) + 1):
        boss._update_attack_state(DT)
    bus.dispatch()
    assert received, "VINE_SWEEP never emitted SFX_BOSSES_VENADO_VINE"


def test_mushroom_spore_emits_sfx_event():
    """Feature A (SFX): MUSHROOM_SPORE reuses SFX_BOSSES_VENADO_VINE (deliberate
    deviation from the reference boss, which leaves this attack silent --
    only 3 Venado wavs exist, no dedicated spore sound)."""
    boss, bus = make_boss(with_bus=True)
    received = []
    on_sfx = lambda **kw: received.append(kw)  # noqa: E731
    bus.subscribe(Events.SFX_BOSSES_VENADO_VINE, on_sfx)
    boss._do_mushroom_spore(pygame.Rect(2600, 528, 20, 32))
    bus.dispatch()
    assert received, "MUSHROOM_SPORE never emitted SFX_BOSSES_VENADO_VINE"


def test_sfx_not_emitted_during_telegraph():
    """The SFX must fire at resolution (windup end, same instant as BOSS_ATTACK),
    not the instant the telegraph starts -- an early emit would desync the
    sound cue from the visible hit."""
    boss, bus = make_boss(with_bus=True)
    received = []
    on_sfx = lambda **kw: received.append(kw)  # noqa: E731
    bus.subscribe(Events.SFX_BOSSES_VENADO_STOMP, on_sfx)
    pr = pygame.Rect(int(boss.rect.centerx) - 60, 528, 20, 32)
    boss.set_player_ref(pr)
    boss._try_attack("STOMP")
    bus.dispatch()
    assert boss._telegraph == "STOMP"
    assert not received, "SFX fired at telegraph start instead of resolution"


def bernstein2(p0, p1, p2, t):
    u = 1.0 - t
    return (u * u * p0[0] + 2 * u * t * p1[0] + t * t * p2[0],
            u * u * p0[1] + 2 * u * t * p1[1] + t * t * p2[1])


def test_vine_toss_path_is_quadratic_bezier():
    boss, _ = make_boss()
    boss._last_player_velocity = pygame.Vector2(100.0, 0.0)
    pr = pygame.Rect(2600, 528, 20, 32)
    boss._do_vine_toss(pr)
    assert len(boss._projectiles) == 1
    proj = boss._projectiles[0]
    assert proj["type"] == "vine" and proj["damage"] == 0.5
    p0 = (boss.rect.centerx + 18.0 * boss.facing_direction, boss.rect.centery - 6.0)
    px = pygame.Vector2(pr.centerx, pr.centery) + pygame.Vector2(100.0, 0.0) * bv.VINE_PREDICT
    p2 = (px.x, min(px.y, bv.FLOOR_Y - 16.0))
    p1 = ((p0[0] + p2[0]) / 2.0, min(p0[1], p2[1]) - 80.0)
    path = proj["path"]
    assert len(path) == 32
    for k in (0, 8, 16, 31):
        ex, ey = bernstein2(p0, p1, p2, k / 31.0)
        assert abs(path[k][0] - ex) < 1e-6 and abs(path[k][1] - ey) < 1e-6


def test_vine_projectile_traverses_and_expires():
    boss, _ = make_boss()
    boss._do_vine_toss(pygame.Rect(2600, 528, 20, 32))
    proj = boss._projectiles[0]
    boss._update_projectiles(0.5)
    assert proj["alive"] and proj["t"] > 0
    assert proj["pos"] != pygame.Vector2(proj["path"][0])   # advanced along the arc
    boss._update_projectiles(2.0)                     # t >= 1.0
    assert boss._projectiles == []                    # cleaned up


def test_phase_transition_emits_event_and_builds_figure8():
    boss, bus = make_boss(with_bus=True)
    received = []
    # ENGINE V2: keep the handler alive -- see test_charge_emits_boss_attack_event.
    on_phase = lambda **kw: received.append(kw)  # noqa: E731
    bus.subscribe(Events.BOSS_PHASE_CHANGED, on_phase)
    boss.apply_hit(6.5, (0, 0))                       # 12 -> 5.5 <= 6.0
    assert boss.is_transitioning
    hp_before = boss.current_health
    boss.apply_hit(3.0, (0, 0))                       # invulnerable while transitioning
    assert boss.current_health == hp_before
    for _ in range(int(2.6 / DT)):                    # transition_timer=2.5 (engine)
        boss.update(DT)
    assert not boss.is_transitioning and boss.current_phase == 1
    bus.dispatch()                                    # EventBus is a queue
    assert received and received[-1]["phase"] == 1
    assert len(boss._bezier_path) == 64               # figure-8 precomputed


def test_figure8_path_inside_arena_and_reachable():
    boss, _ = make_boss()
    path = boss._build_figure8_path()
    xs = [p[0] for p in path]; ys = [p[1] for p in path]
    assert min(xs) >= bv.ARENA_X0 + 16 and max(xs) <= bv.ARENA_X1 - 48
    assert max(ys) + 48 <= bv.FLOOR_Y and max(ys) + 48 >= 500   # dips into melee range


def test_spores_three_fan_aimed_at_player():
    boss, _ = make_boss()
    pr = pygame.Rect(2600, 528, 20, 32)
    boss._do_mushroom_spore(pr)
    spores = [p for p in boss._projectiles if p["type"] == "spore"]
    assert len(spores) == 3 and all(p["damage"] == 0.25 for p in spores)
    to_player = pygame.Vector2(pr.centerx - boss.rect.centerx,
                               pr.centery - boss.rect.centery).normalize()
    center = spores[1]["vel"].normalize()
    assert center.dot(to_player) > 0.9999             # center spore aims at player
    for side in (spores[0], spores[2]):
        assert abs(side["vel"].normalize().dot(center) - math.cos(math.radians(15))) < 1e-4
    assert all(abs(p["vel"].length() - bv.SPORE_SPEED) < 1e-6 for p in spores)


def test_spore_expires_by_distance_not_lifetime():
    boss, _ = make_boss()
    boss._do_mushroom_spore(pygame.Rect(2600, 528, 20, 32))
    proj = boss._projectiles[0]
    proj["vel"] = proj["vel"].normalize() * 1000.0    # accelerated for the test
    boss._update_projectiles(0.5)                     # 500 px > SPORE_RANGE, age 0.5s
    assert proj not in boss._projectiles


def test_sweep_damages_grounded_player_zone():
    boss, _ = make_boss()
    boss.set_player_ref(pygame.Rect(2600, 528, 20, 32))  # _try_attack no-ops without a player_ref
    boss._try_attack("VINE_SWEEP")
    for _ in range(int(bv.SWEEP_TELEGRAPH / DT) + 1):
        boss._update_attack_state(DT)
    sweep = pygame.Rect(int(bv.ARENA_X0), int(bv.FLOOR_Y) - 24,
                        int(bv.ARENA_X1 - bv.ARENA_X0), 24)
    assert boss._sweep_window > 0
    assert boss._sweep_rect == sweep                             # persisted attribute (Task 9 carry-over)
    assert sweep.colliderect(pygame.Rect(2600, 540, 20, 32))     # grounded: hit
    assert not sweep.colliderect(pygame.Rect(2600, 460, 20, 32)) # jumping: safe


def test_defeat_sequence_stages_then_progression_ready():
    boss, bus = make_boss(with_bus=True)
    boss.apply_hit(12.0, (0, 0))
    assert boss.state == EnemyState.DYING and boss.is_alive
    for _ in range(int(1.6 / DT)):
        boss.update(DT)
    assert boss._defeat_stage == 1                    # glowing skull (§3.6)
    for _ in range(int(2.1 / DT)):
        boss.update(DT)
    assert boss._defeat_stage == 2 and not boss.is_alive
    assert boss.death_timer <= 0 and not boss.completion_fired
    # -> ProgressionSystem.check_boss_defeat() will fire the banner (engine side)


def test_defeat_sequence_is_one_shot_even_if_hit_again():
    boss, _ = make_boss()
    boss.apply_hit(12.0, (0, 0))
    boss.update(DT)                                   # sequence underway
    timer_before = boss.death_timer
    boss.apply_hit(5.0, (0, 0))                       # mashing attacks on the dying boss
    assert boss._defeat_stage == 0 and boss.death_timer == timer_before


def test_spore_glow_uses_colortools_cache():
    boss, _ = make_boss()
    assert isinstance(boss._spore_glow, pygame.Surface)
    assert boss._spore_glow.get_size() == (16, 16)


def test_defeat_clears_combat_state():
    boss, _ = make_boss()
    boss._do_mushroom_spore(pygame.Rect(2600, 528, 20, 32))
    boss._charge_active = True
    boss._telegraph = "STOMP"
    boss._stomp_recover = 0.3          # Hallazgo C fix: must not strand the boss mid-recover
    boss._charge_recover = 0.3
    boss.apply_hit(12.0, (0, 0))
    assert boss._projectiles == [] and not boss._charge_active and boss._telegraph == ""
    assert boss._stomp_recover == 0.0 and boss._charge_recover == 0.0


class FakePlayer:
    """Duck-typed player: just what _check_player_contact touches."""
    def __init__(self, rect):
        self.rect = rect
        self.hurtbox = rect
        self.velocity = pygame.Vector2(50.0, 0.0)
        self.damage_calls = []
    def apply_damage(self, amount, source_position, knockback_force=150.0):
        self.damage_calls.append(amount)


def test_check_player_contact_applies_projectile_and_sweep_damage():
    boss, _ = make_boss()
    fake = FakePlayer(pygame.Rect(2600, 528, 20, 32))
    boss._do_mushroom_spore(fake.rect)
    boss._projectiles[1]["pos"] = pygame.Vector2(fake.rect.center)  # center spore on player
    boss._sweep_rect = pygame.Rect(int(bv.ARENA_X0), int(bv.FLOOR_Y) - 24,
                                   int(bv.ARENA_X1 - bv.ARENA_X0), 24)
    boss._sweep_window = bv.SWEEP_WINDOW
    boss._check_player_contact(fake)
    assert 0.25 in fake.damage_calls and 0.5 in fake.damage_calls
    assert boss._last_player_velocity == pygame.Vector2(50.0, 0.0)


def test_get_animation_key_flags():
    """Pure function of instance flags — cheap coverage, no update() ticks needed."""
    boss, _ = make_boss()
    assert boss._get_animation_key() == "drift"
    boss._charge_active = True
    assert boss._get_animation_key() == "charge"
    boss._charge_active = False
    boss._telegraph = "CHARGE"
    assert boss._get_animation_key() == "charge"
    boss._telegraph = "STOMP"
    assert boss._get_animation_key() == "stomp"
    boss._telegraph = ""
    boss._stomp_window = 0.1
    assert boss._get_animation_key() == "stomp"
    boss._stomp_window = 0.0
    boss._telegraph = "VINE_SWEEP"
    assert boss._get_animation_key() == "vine"
    boss._telegraph = ""
    boss._sweep_window = 0.1
    assert boss._get_animation_key() == "vine"
    boss._sweep_window = 0.0
    # Hallazgo C fix: grounded/wall punish recovers keep the matching pose.
    boss._stomp_recover = 0.1
    assert boss._get_animation_key() == "stomp"
    boss._stomp_recover = 0.0
    boss._charge_recover = 0.1
    assert boss._get_animation_key() == "charge"
    boss._charge_recover = 0.0
    boss.current_phase = 1
    assert boss._get_animation_key() == "frenzy_drift"


# ──────────────────────────────────────────────
# Weak points (Feature C, adopted from boss_kit.WeakPoint -- spec
# 2026-07-29-adopcion-v2-sfx-luces-weakpoints-design.md §3)
# ──────────────────────────────────────────────

def _cuernos_player_ref(boss, facing: int = 1) -> pygame.Rect:
    """A player rect placed squarely inside the (facing-aware) cuernos rect."""
    ox = bv.CUERNOS_OFFSET[0]
    if facing < 0:
        ox = boss.rect.width - bv.CUERNOS_OFFSET[0] - bv.CUERNOS_SIZE[0]
    return pygame.Rect(boss.rect.x + ox, boss.rect.y + bv.CUERNOS_OFFSET[1], 20, 32)


def _flanco_player_ref(boss, facing: int = 1) -> pygame.Rect:
    """A player rect placed squarely inside the (facing-aware) flanco rect."""
    ox = bv.FLANCO_OFFSET[0]
    if facing < 0:
        ox = boss.rect.width - bv.FLANCO_OFFSET[0] - bv.FLANCO_SIZE[0]
    return pygame.Rect(boss.rect.x + ox, boss.rect.y + bv.FLANCO_OFFSET[1], 20, 32)


def test_weak_point_cuernos_multiplies_damage():
    """Cuernos are exposed in every phase (17_BOSS_SPEC has no rubric
    requirement here -- this is the reference boss's enrichment, see
    README)."""
    boss, _ = make_boss()
    boss.set_player_ref(_cuernos_player_ref(boss))
    boss.apply_hit(1.0, (0, 0))
    assert boss.current_health == 12.0 - 1.0 * bv.CUERNOS_MULTIPLIER


def test_weak_point_flanco_only_in_phase_2():
    """Two fresh bosses, not one hit twice: EnemyBase.apply_hit sets a 0.5s
    invincibility_timer on any non-lethal hit (enemy_base.py), which would
    silently no-op a second immediate apply_hit and confuse this test's
    intent -- isolating phase 0 vs phase 1 in separate instances avoids that
    entirely instead of threading update() calls through just to burn it
    down."""
    boss0, _ = make_boss()
    boss0.set_player_ref(_flanco_player_ref(boss0))
    boss0.apply_hit(1.0, (0, 0))                   # phase 0: flanco not exposed
    assert boss0.current_health == 12.0 - 1.0      # base damage, no multiplier

    boss1, _ = make_boss()
    boss1.current_phase = 1
    boss1.set_player_ref(_flanco_player_ref(boss1))
    boss1.apply_hit(1.0, (0, 0))                   # phase 1 (index): flanco exposed now
    assert boss1.current_health == 12.0 - 1.0 * bv.FLANCO_MULTIPLIER


def test_weak_point_miss_applies_base_damage():
    boss, _ = make_boss()
    boss.set_player_ref(pygame.Rect(boss.rect.x, boss.rect.y + 300, 20, 32))  # nowhere near either rect
    boss.apply_hit(1.0, (0, 0))
    assert boss.current_health == 12.0 - 1.0


def test_weak_point_overlap_uses_higher_multiplier():
    """Documents boss_kit.resolve_weak_point_damage's own contract (best
    multiplier wins, not the sum) in this boss's context -- our two real
    weak points never overlap by construction, so this uses synthetic ones."""
    boss, _ = make_boss()
    low = WeakPoint(offset=(0, 0), size=(20, 20), multiplier=1.5, label="low")
    high = WeakPoint(offset=(5, 5), size=(20, 20), multiplier=3.0, label="high")
    hit_rect = pygame.Rect(boss.rect.x + 10, boss.rect.y + 10, 4, 4)  # inside both
    damage, point = resolve_weak_point_damage(boss, hit_rect, 1.0, [low, high], 0)
    assert point is high and damage == 3.0


def test_last_weak_point_recorded():
    boss, _ = make_boss()
    boss.set_player_ref(_cuernos_player_ref(boss))
    boss.apply_hit(1.0, (0, 0))
    assert boss.last_weak_point is not None
    assert boss.last_weak_point.label == "cuernos"
    assert boss.last_weak_point.multiplier == bv.CUERNOS_MULTIPLIER


def test_weak_point_offsets_mirror_with_facing():
    """Sprite flips horizontally when facing_direction < 0 (boss_base.py
    pygame.transform.flip, within the 48px-wide canvas). Weak points are
    authored in canonical (facing-right) space, so hitting the mirrored
    cuernos position must still crit -- and the UN-mirrored (canonical)
    offset must NOT crit anymore, proving the mirror actually ran instead
    of the check being facing-agnostic by accident."""
    boss, _ = make_boss()
    boss.facing_direction = -1
    boss.set_player_ref(_cuernos_player_ref(boss, facing=-1))
    boss.apply_hit(1.0, (0, 0))
    assert boss.current_health == 12.0 - 1.0 * bv.CUERNOS_MULTIPLIER

    boss2, _ = make_boss()
    boss2.facing_direction = -1
    canonical_rect = pygame.Rect(boss2.rect.x + bv.CUERNOS_OFFSET[0],
                                  boss2.rect.y + bv.CUERNOS_OFFSET[1], 20, 32)
    boss2.set_player_ref(canonical_rect)
    boss2.apply_hit(1.0, (0, 0))
    assert boss2.current_health == 12.0 - 1.0     # canonical offset misses once flipped


def test_weak_point_multiplier_respects_transition_invulnerability():
    """The multiplier is computed and handed to super().apply_hit() -- it
    must not bypass the engine's existing invulnerable-while-transitioning
    guard (same chain the rest of the boss's apply_hit already relies on,
    see test_phase_transition_emits_event_and_builds_figure8)."""
    boss, _ = make_boss()
    boss.set_player_ref(_cuernos_player_ref(boss))
    boss.apply_hit(3.0, (0, 0))                   # 3*2.5=7.5 -> 12-7.5=4.5 <= 6.0 threshold
    assert boss.is_transitioning
    hp_before = boss.current_health
    boss.apply_hit(1.0, (0, 0))                   # still on cuernos, but mid-transition
    assert boss.current_health == hp_before


def test_apply_hit_still_triggers_phase_transition_and_defeat():
    """Regression: weak point resolution must not interfere with the phase
    threshold or the death sequence -- both already exercised without a
    weak-point hit by test_phase_transition_emits_event_and_builds_figure8
    / test_defeat_sequence_stages_then_progression_ready; this repeats the
    shape of both WITH self._player_ref parked on cuernos."""
    boss, _ = make_boss()
    boss.set_player_ref(_cuernos_player_ref(boss))
    boss.apply_hit(3.0, (0, 0))                   # -> transition (see test above)
    for _ in range(int(2.6 / DT)):
        boss.update(DT)
    assert not boss.is_transitioning and boss.current_phase == 1
    boss.set_player_ref(_cuernos_player_ref(boss))
    boss.apply_hit(10.0, (0, 0))                  # 10*2.5=25, far past 0
    assert boss.state == EnemyState.DYING and boss.is_alive


def test_weak_point_flash_activates_on_crit_not_on_normal_hit():
    boss, _ = make_boss()
    boss.set_player_ref(_cuernos_player_ref(boss))
    boss.apply_hit(1.0, (0, 0))
    assert boss._weak_point_flash_timer > 0.0
    assert boss._weak_point_flash_point is not None

    boss2, _ = make_boss()
    boss2.set_player_ref(pygame.Rect(boss2.rect.x, boss2.rect.y + 300, 20, 32))
    boss2.apply_hit(1.0, (0, 0))
    assert boss2._weak_point_flash_timer == 0.0
    assert boss2._weak_point_flash_point is None
