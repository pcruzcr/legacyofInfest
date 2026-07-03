# Legacy of InFest — Stage 0 Design Document

**Document ID:** LOI-STAGE0-007  
**Version:** 1.0.0  
**Status:** Official  
**Audience:** Professor, Teaching Assistants, AI coding assistants

---

## 1. Educational Purpose

Stage 0 is not a tutorial in the entertainment sense. It is the **executable documentation** of the Legacy of InFest framework. Every system that a student will use to build their stages is demonstrated in Stage 0 — correctly, completely, and with inline tutorial messages that explain what is happening and why.

A student who has played through Stage 0 and studied its source code should be able to:

1. Understand the complete framework API without reading the engine source.
2. Know exactly how each system behaves in a running stage.
3. Use Stage 0 as a reference implementation when building their own stage.

Stage 0 also serves as the grader's calibration baseline. All three student stages are evaluated against the behavior demonstrated in Stage 0.

### 1.1 Design Philosophy

- **No hidden systems.** Every system activated in Stage 0 announces itself via a tutorial message.
- **Progressive complexity.** Systems are introduced from simplest to most complex, following the same order as the course syllabus.
- **Restartable zones.** Stage 0 has checkpoints before each demonstration zone. A student can die and retry any zone independently.
- **Debug mode.** Pressing `F1` enables the debug overlay, which renders hitboxes, hurtboxes, detection zones, collision rects, and camera bounds. This is educational, not a cheat.

---

## 2. Stage Layout

Stage 0 is a single-screen-wide horizontal stage divided into seven demonstration zones. The stage scrolls from left to right. Total map width: **3840 pixels (240 tiles)**. Map height: **224 pixels (14 tiles)**.

```
[SPAWN]──[Zone A]──[Zone B]──[Zone C]──[Zone D]──[Zone E]──[Zone F]──[Zone G]──[EXIT]
  0px     160px     640px    1120px    1600px    2080px    2560px    3200px    3760px
```

### 2.1 Visual Theme

Stage 0 takes place in a neutral, stone-corridor environment. The visual style is clean and readable — no atmospheric clutter that would obscure the demonstration systems. The tileset is `tileset_stage0.png`, a desaturated stone set with clear tile boundaries visible in debug mode.

### 2.2 Vertical Layout

The stage is a flat, single-elevation corridor with the following vertical elements:

- Floor: tiles at Y=192–224 (rows 12–14)
- Ceiling: open sky (no ceiling tiles)
- Platforms: elevated platforms appear in Zone C, Zone D, and Zone E
- Pits: one death pit in Zone E
- Vertical clearance for flight: 96 pixels of open air above the floor

---

## 3. Zone Breakdown

### Zone A — Movement and Jump (X: 160–640)

**Systems Demonstrated:** Walk, Jump, Crouch, Coyote Time, Jump Cut

**Layout:**
- Flat floor, no enemies
- Two elevated platforms at Y=160 (32 px above floor)
- Platform 1: X=272–368 (96 px wide)
- Platform 2: X=416–512 (96 px wide)
- Gap between platforms: 48 px (jumpable with normal jump)

**Messages:**

| Trigger Position | Message |
|---|---|
| X=160 (zone entry) | `"Use arrow keys or left stick to walk.\nPress Space or A to jump."` |
| X=260 (before platform 1) | `"Jump to reach elevated platforms.\nYou have 6 frames of coyote time at ledge edges."` |
| X=400 (between platforms) | `"Hold jump longer for a higher jump.\nRelease early for a short hop."` |
| X=520 (after platform 2) | `"Press Down to crouch.\nCrouching reduces your hurtbox size."` |

**Entities:** None  
**Checkpoints:** None (Zone A is before the first checkpoint)

---

### Zone B — Short Attack and Long Attack (X: 640–1120)

**Systems Demonstrated:** Short Attack, Long Attack, Hitstop, Attack hitbox, Enemy death

**Layout:**
- Flat floor
- Three Walker enemies spaced 80 px apart
- Walker A: X=760, patrol_length=0 (stationary, facing right)
- Walker B: X=900, patrol_length=0 (stationary, facing right)
- Walker C: X=1040, patrol_length=0 (stationary, facing right)

**Messages:**

| Trigger Position | Message |
|---|---|
| X=640 (zone entry) | `"Press Z to perform a Short Attack (fists).\nPress X for a Long Attack (stick)."` |
| X=700 (before Walker A) | `"Short Attack: 0.5 heart damage, fast recovery.\nLong Attack: 1.0 heart damage, wider reach."` |
| X=840 (after Walker A dies) | `"Notice the hitstop effect on hit.\nTime briefly slows to emphasize impact."` |
| X=1000 (before Walker C) | `"Try crouching (Down) then attacking.\nThe hitbox shifts to hit low targets."` |

**Checkpoint:** `Checkpoint_01` at X=1080, `checkpoint_id=0`

---

### Zone C — Walker Enemy and Contact Damage (X: 1120–1600)

**Systems Demonstrated:** Walker patrol, ledge detection, alert state, contact damage, invincibility frames

**Layout:**
- Flat floor
- Two elevated platforms creating an elevated walkway section
  - Platform 1: X=1200–1376 (176 px wide, Y=160)
  - Gap: X=1376–1440 (64 px — Walker will turn here due to ledge detection)
  - Platform 2: X=1440–1616 (176 px wide, Y=160)
- Walker A: on Platform 1, patrol_length=160, facing=right
- Walker B: at floor level, patrol_length=128, facing=left

**Messages:**

| Trigger Position | Message |
|---|---|
| X=1120 | `"Walker enemies patrol back and forth.\nThey detect ledge edges automatically."` |
| X=1200 | `"When you enter their detection range,\nWalkers accelerate toward you."` |
| X=1360 | `"If a Walker touches you, you lose 0.5 hearts.\nYou briefly become invincible after taking damage."` |
| X=1520 | `"Watch the sprite flash during invincibility.\nThis is feedback for the damage-received state."` |

**Checkpoint:** `Checkpoint_02` at X=1560, `checkpoint_id=1`

---

### Zone D — Flying Enemy and Curve Paths (X: 1600–2080)

**Systems Demonstrated:** Flying enemy, sine-wave flight, Bézier path flight, parametric sampling

**Layout:**
- Flat floor
- Wide open vertical space (no ceiling obstacles)
- Flying_A: sine mode, amplitude=28, frequency=1.2, X=1700, patrol horizontal range 200 px
- Flying_B: bezier mode, control points forming an S-curve across the zone
  - Waypoint 0: X=1900, Y=80
  - Waypoint 1: X=1800, Y=40
  - Waypoint 2: X=1700, Y=80
  - Waypoint 3: X=1800, Y=120

**Messages:**

| Trigger Position | Message |
|---|---|
| X=1600 | `"Flying enemies move along computed paths.\nThe first uses a sine wave trajectory."` |
| X=1780 | `"Sine wave: position.y = origin + A * sin(2πft)\nAmplitude (A) and frequency (f) are TMX properties."` |
| X=1880 | `"The second Flying enemy uses a Bézier curve path.\nFour control points define the S-shaped trajectory."` |
| X=2000 | `"Press F1 to toggle debug view.\nYou can see the Bézier control points and sampled path."` |

**Checkpoint:** `Checkpoint_03` at X=2040, `checkpoint_id=2`

---

### Zone E — Shooter Enemy and Projectiles (X: 2080–2560)

**Systems Demonstrated:** Shooter, projectile velocity, angle calculation, range detection, death pit

**Layout:**
- Floor with a death pit at X=2240–2304 (64 px wide)
- One-way platform spanning the pit: X=2240–2320, Y=176
- Shooter_A: stationary, X=2400, facing=left, fire_rate=0.6
- Shooter_B: slow patrol, spawn at X=2500, fire_rate=0.4

**Messages:**

| Trigger Position | Message |
|---|---|
| X=2080 | `"Shooter enemies fire projectiles when you enter range.\nProjectile angle is computed with atan2."` |
| X=2160 | `"angle = atan2(dy, dx) from shooter to player.\nThis is Unit II vector mathematics."` |
| X=2240 | `"The gap ahead has a one-way platform.\nJump up through it; fall back down through it."` |
| X=2360 | `"Crouch to avoid projectiles that fly high.\nTime your movement between shots."` |

**Checkpoint:** `Checkpoint_04` at X=2520, `checkpoint_id=3`

---

### Zone F — HUD and Timer Demonstration (X: 2560–3200)

**Systems Demonstrated:** HUD hearts, timer countdown, checkpoint restore with full health, Game Over flow

**Layout:**
- Flat floor, slightly more complex enemy arrangement
- Walker_A: X=2680, patrol_length=128, damage_on_contact=1.0 (heavy damage enemy — marked with a visual indicator)
- Walker_B: X=2820, patrol_length=96
- Walker_C: X=2960, patrol_length=64
- HazardZone_A: X=3040–3088 (48 px wide), damage=0.25, damage_type=floor_spikes (visible spike tiles in Terrain_Detail)

**Messages:**

| Trigger Position | Message |
|---|---|
| X=2560 | `"The HUD shows your health (hearts) and the stage timer.\nThe portrait in the corner is the player avatar."` |
| X=2640 | `"The red Walker deals 1.0 heart of damage.\nHeavy damage enemies are marked differently."` |
| X=2760 | `"If you run out of health, Game Over appears.\nYou can continue from the last checkpoint."` |
| X=3040 | `"The spike floor deals 0.25 heart damage per tick.\nThis is the Light damage tier."` |

**Checkpoint:** `Checkpoint_05` at X=3160, `checkpoint_id=4`

---

### Zone G — Stage Banner, Next Trigger, and Completion (X: 3200–3760)

**Systems Demonstrated:** Stage completion trigger, next stage transition, screen banner

**Layout:**
- Flat corridor, no enemies
- Decorative arch tilework in `FG_Overlay` at X=3600
- `NextTrigger` rect: X=3720–3760 (40 px wide), Y=160–224 (64 px tall)
- A torch animation plays at X=3640 (sprite: `shared/torch_anim.png`, 4 frames, 8 fps)

**Messages:**

| Trigger Position | Message |
|---|---|
| X=3200 | `"You have demonstrated all framework systems.\nWalk right to complete Stage 0."` |
| X=3500 | `"Your stages (Stage 1, 2, 3) will build on everything shown here.\nStudy the source code for each zone."` |
| X=3680 | `"Step through the arch to proceed.\nGood luck."` |

---

## 4. Messages — Complete List

All tutorial messages in Stage 0 are `trigger_once=true`. They appear once and do not reappear on replay unless the stage is fully restarted.

| ID | Zone | Trigger X | Text Summary |
|---|---|---|---|
| MSG_01 | A | 160 | Walk and jump controls |
| MSG_02 | A | 260 | Platforms and coyote time |
| MSG_03 | A | 400 | Jump cut (variable height) |
| MSG_04 | A | 520 | Crouch mechanics |
| MSG_05 | B | 640 | Short and long attack buttons |
| MSG_06 | B | 700 | Damage tiers |
| MSG_07 | B | 840 | Hitstop explanation |
| MSG_08 | B | 1000 | Crouch-attack lowered hitbox |
| MSG_09 | C | 1120 | Walker patrol and ledge detection |
| MSG_10 | C | 1200 | Walker alert state |
| MSG_11 | C | 1360 | Contact damage and invincibility |
| MSG_12 | C | 1520 | Invincibility flash feedback |
| MSG_13 | D | 1600 | Flying enemy introduction |
| MSG_14 | D | 1780 | Sine wave math explanation |
| MSG_15 | D | 1880 | Bézier curve path introduction |
| MSG_16 | D | 2000 | Debug mode F1 hint |
| MSG_17 | E | 2080 | Shooter introduction and atan2 |
| MSG_18 | E | 2160 | Vector mathematics reference |
| MSG_19 | E | 2240 | One-way platform explanation |
| MSG_20 | E | 2360 | Crouch to dodge projectiles |
| MSG_21 | F | 2560 | HUD overview |
| MSG_22 | F | 2640 | Heavy damage enemy indicator |
| MSG_23 | F | 2760 | Game Over flow |
| MSG_24 | F | 3040 | Light damage spike floor |
| MSG_25 | G | 3200 | Stage completion introduction |
| MSG_26 | G | 3500 | Study the source code |
| MSG_27 | G | 3680 | Proceed instruction |

---

## 5. Triggers — Complete List

| Name | Type | X | Y | Width | Height | Properties |
|---|---|---|---|---|---|---|
| `PlayerSpawn_01` | PlayerSpawn | 48 | 160 | — | — | — |
| `Checkpoint_01` | Checkpoint | 1080 | 160 | 24 | 32 | `checkpoint_id=0` |
| `Checkpoint_02` | Checkpoint | 1560 | 160 | 24 | 32 | `checkpoint_id=1` |
| `Checkpoint_03` | Checkpoint | 2040 | 160 | 24 | 32 | `checkpoint_id=2` |
| `Checkpoint_04` | Checkpoint | 2520 | 160 | 24 | 32 | `checkpoint_id=3` |
| `Checkpoint_05` | Checkpoint | 3160 | 160 | 24 | 32 | `checkpoint_id=4` |
| `NextTrigger_01` | NextTrigger | 3720 | 160 | 40 | 64 | — |
| `HazardZone_A` | HazardZone | 3040 | 176 | 48 | 16 | `damage=0.25, damage_type=floor_spikes` |
| `CameraLock_BossArena` | CameraLock | — | — | — | — | (reserved, not active in Stage 0) |

---

## 6. Enemy Placement — Complete List

| Name | Type | X | Y | Key Properties |
|---|---|---|---|---|
| `Walker_01` | Walker | 760 | 192 | patrol_length=0, stationary |
| `Walker_02` | Walker | 900 | 192 | patrol_length=0, stationary |
| `Walker_03` | Walker | 1040 | 192 | patrol_length=0, stationary |
| `Walker_04` | Walker | 1260 | 160 | patrol_length=160, facing=right, on Platform 1 |
| `Walker_05` | Walker | 1480 | 192 | patrol_length=128, facing=left, floor level |
| `Flying_01` | Flying | 1700 | 112 | flight_mode=sine, amplitude=28, frequency=1.2 |
| `Flying_02` | Flying | 1900 | 80 | flight_mode=bezier, linked waypoints Waypoint_01–04 |
| `Shooter_01` | Shooter | 2400 | 192 | stationary, fire_rate=0.6, facing=left |
| `Shooter_02` | Shooter | 2500 | 192 | patrol_length=40, fire_rate=0.4 |
| `Walker_06` | Walker | 2680 | 192 | patrol_length=128, damage_on_contact=1.0 |
| `Walker_07` | Walker | 2820 | 192 | patrol_length=96 |
| `Walker_08` | Walker | 2960 | 192 | patrol_length=64 |

---

## 7. Checkpoint Placement

| ID | X | Trigger Context |
|---|---|---|
| 0 | 1080 | After completing Zone B (attack demonstration) |
| 1 | 1560 | After Zone C (Walker enemy section) |
| 2 | 2040 | After Zone D (Flying enemy section) |
| 3 | 2520 | After Zone E (Shooter section) |
| 4 | 3160 | After Zone F (HUD and damage demonstration) |

---

## 8. Completion Conditions

### 8.1 Normal Completion

The player reaches and overlaps the `NextTrigger_01` rect at X=3720 while grounded.

**On completion:**
1. `STAGE_COMPLETE` event emitted.
2. Audio fades out (500ms).
3. Screen fades to black (800ms).
4. `SceneManager.replace(Stage1Scene())` called.

### 8.2 Timer Expiration

Stage 0 does not have a time limit. The timer is displayed as a demonstration of the HUD timer system but it counts up (not down) and does not trigger a game over. This is noted in the HUD tutorial message.

---

## 9. Failure Conditions

### 9.1 Player Death

When `current_health <= 0`:

1. `PLAYER_DIED` emitted.
2. Player death animation plays.
3. `GameOverScene` pushed.
4. Player selects **Continue** → `GameOverScene` popped, player respawns at last active checkpoint with full health.
5. Player selects **Quit** → return to `TitleScene`.

### 9.2 Death Pit

The death pit in Zone E (X=2240–2304, Y=224) has a `Death_` collision rect immediately below. If the player falls into it, `current_health` is set to 0 directly (bypasses damage tiers) and `PLAYER_DIED` is emitted immediately. The effect is instant — no damage animation, no invincibility frames.

---

## 10. Systems Demonstrated — Master Checklist

The following table confirms that every framework system documented in this specification package is demonstrated somewhere in Stage 0.

| System | Zone | Reference Document |
|---|---|---|
| Walk | A | `04_PLAYER_SPEC.md` §4.1 |
| Jump | A | `04_PLAYER_SPEC.md` §4.2 |
| Coyote Time | A | `04_PLAYER_SPEC.md` §4.2 |
| Jump Cut | A | `04_PLAYER_SPEC.md` §4.2 |
| Crouch | A | `04_PLAYER_SPEC.md` §4.1 |
| Short Attack | B | `04_PLAYER_SPEC.md` §7.1 |
| Long Attack | B | `04_PLAYER_SPEC.md` §7.2 |
| Hitstop | B | `04_PLAYER_SPEC.md` §7.3 |
| Attack hitbox | B | `04_PLAYER_SPEC.md` §10 |
| Hurtbox | C | `04_PLAYER_SPEC.md` §11 |
| Walker enemy | B, C | `05_ENEMY_SPEC.md` §3 |
| Ledge detection | C | `05_ENEMY_SPEC.md` §3.5 |
| Alert state | C | `05_ENEMY_SPEC.md` §3.3 |
| Contact damage | C | `05_ENEMY_SPEC.md` §9.2 |
| Invincibility frames | C | `04_PLAYER_SPEC.md` §5.3 |
| Flying enemy (sine) | D | `05_ENEMY_SPEC.md` §4 |
| Flying enemy (Bézier) | D | `05_ENEMY_SPEC.md` §4.3 |
| Shooter enemy | E | `05_ENEMY_SPEC.md` §5 |
| Projectile system | E | `05_ENEMY_SPEC.md` §5.4 |
| atan2 angle calculation | E | `05_ENEMY_SPEC.md` §5.4 |
| One-way platform | E | `06_TMX_SPEC.md` §9.2 |
| Death pit | E | `06_TMX_SPEC.md` §9.3 |
| Checkpoint | B, C, D, E, F | `06_TMX_SPEC.md` §7 |
| HUD hearts | F | `09_HUD_SPEC.md` §3 |
| HUD timer | F | `09_HUD_SPEC.md` §4 |
| Light damage (0.25) | F | `04_PLAYER_SPEC.md` §6.1 |
| Heavy damage (1.0) | F | `04_PLAYER_SPEC.md` §6.1 |
| HazardZone | F | `06_TMX_SPEC.md` §9.2 |
| Game Over flow | F | `03_ARCHITECTURE.md` §7 |
| Stage Banner | G (entry) | `09_HUD_SPEC.md` §6 |
| NextTrigger / Completion | G | `06_TMX_SPEC.md` §8 |
| Tutorial Messages | A–G | `09_HUD_SPEC.md` §5 |
| Debug overlay (F1) | D | `03_ARCHITECTURE.md` §2 |
| Camera scrolling | All | `03_ARCHITECTURE.md` §2.8 |
| Parallax backgrounds | All | `06_TMX_SPEC.md` §3.2 |
| TMX layer system | All | `06_TMX_SPEC.md` §3 |
| Entity spawn from TMX | All | `06_TMX_SPEC.md` §6 |
| EventBus communication | All | `03_ARCHITECTURE.md` §8.5 |
| Audio (BGM + SFX) | All | `03_ARCHITECTURE.md` §2.4 |
