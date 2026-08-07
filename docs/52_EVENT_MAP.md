---
document_id: "LOI-EVENTMAP-052"
title: "EventBus Event Map — Observer Pattern Audit"
aliases: ["EventMap", "Event Audit"]
tags: ["event-bus", "observer", "audit", "architecture"]
description: "Complete mapping of all EventBus events: emitters, subscribers, payloads, and dispatch order."
source: "src/engine/core/events.py, src/engine/core/event_bus.py"
date_processed: "2026-07-16"
---

# EventBus Event Map

**Document ID:** LOI-EVENTMAP-052  
**Version:** 1.0.0  
**Status:** ⚠️ Medido contra el árbol del **2026-07-16**. Ver §0.

---

## 0. Qué de este documento ha caducado (AUD-254, medido 2026-08-04)

Este mapa se levantó el 16 de julio y no se ha vuelto a medir. Su §3 —«18
eventos huérfanos, ni emitidos ni suscritos»— **ya no es cierta**, y una lista
de huérfanos equivocada es peor que ninguna: manda a alguien a borrar cableado
que sí existe. Recuento de hoy, `grep` sobre `src/`:

**Dejaron de ser huérfanos** (tienen emisor desde que se escribió §3):
`MUSIC_STINGER` (`boss_base.py:336`), `SFX_PLAYER_PARRY` (`enemy_base.py`),
`SFX_UI_GAME_OVER` (`stage_scene.py`), `SFX_ENVIRONMENT_SCREEN_SHAKE` y
`SFX_BOSSES_PABURU_EYE_BEAM` (`boss_paburu.py`), `SFX_BOSS_HIT`
(`enemy_base.py`), `SFX_BOSS_PHASE_CHANGE` (`boss_base.py`).

**Se conectaron en AUD-255:** `SFX_PLAYER_HEAL`, `SFX_PLAYER_CROUCH`,
`SFX_ENVIRONMENT_ONE_WAY_PLATFORM`, `SFX_ENEMIES_PROJECTILE_HIT_WALL`. Los
cuatro tenían fichero, tabla y subtítulo, y les faltaba sólo el `emit`.

**Se conectaron en AUD-251 y AUD-256:** `ITEM_COLLECTED` y `FLAG_SET` (un
diálogo que regalaba un objeto no se lo daba a nadie) y `ACHIEVEMENT_UNLOCKED`
(el logro se veía y no se oía).

**Siguen sin emisor, y es una decisión, no un defecto (5):**
`SFX_BOSSES_GAVILAN_DIVE`, `SFX_BOSSES_GAVILAN_MASK_BEAM`,
`SFX_BOSSES_PABURU_WAVE`, `SFX_BOSSES_RELIC_APPEAR`, `SFX_BOSSES_REY_SPIT`,
`SFX_BOSSES_REY_SPLIT` — pertenecen a ataques de jefes de estudiantes.
`ACHIEVEMENT_PROGRESS` sigue reservado, como dice el propio código.

La recomendación de §6 que **sí sigue viva**: los SFX se suscriben sólo dentro
de `StageScene`, así que un sonido emitido desde un menú no suena.

---

## 1. EventBus Architecture

The `EventBus` class (`src/engine/core/event_bus.py`) implements a queue-based pub/sub pattern:

1. **`emit(event_name, **data)`** — queues the event (deferred dispatch)
2. **`dispatch()`** — called once per frame by `App` before scene update; drains the queue and invokes all subscribers
3. **`subscribe(event_name, callback)`** — registers a callback for an event
4. **`unsubscribe(event_name, callback)`** — removes a callback

Total events defined: **36** (in `src/engine/core/events.py`)
Total emit sites: **83**
Total subscribe sites: **23**

---

## 2. Event Map (alphabetical by event name)

### ACHIEVEMENT_PROGRESS
| Field | Value |
|-------|-------|
| **Emitter** | `Achievements._unlock()` (`src/engine/core/achievements.py:150`) |
| **Payload** | `achievement_id: str`, `progress: int`, `target: int` |
| **Subscribers** | *(none — reserved for future UI)* |
| **Trigger** | When achievement progress value changes |

### ACHIEVEMENT_UNLOCKED
| Field | Value |
|-------|-------|
| **Emitter** | `Achievements._unlock()` (`src/engine/core/achievements.py:169`) |
| **Payload** | `achievement_id: str`, `name: str` |
| **Subscribers** | *(none — reserved for future UI)* |
| **Trigger** | When an achievement is first unlocked |

### BOSS_ATTACK
| Field | Value |
|-------|-------|
| **Emitter** | `BossVenado._do_stomp()` (`boss_venado.py:225,230,237,294`), `EnemyCaster` (`enemy_caster.py:147`), `EnemyBrute._do_attack()` (`enemy_brute.py:66`), `EnemyAssassin` (`enemy_assassin.py:100`) |
| **Payload** | `pattern: str`, `rect: pygame.Rect` |
| **Subscribers** | StageScene — `_play_sfx_named` handler (mapped to `sfx_bosses_venado_*` via `sfx_map` (en `stage_parts/sonido.py` desde AUD-290)) |
| **Trigger** | When a boss/miniboss performs a telegraphed attack |

### BOSS_PHASE_CHANGED
| Field | Value |
|-------|-------|
| **Emitter** | `BossBase._finish_phase_transition()` (`boss_base.py:164-179`) |
| **Payload** | `boss_name: str`, `phase: int`, `phase_name: str` |
| **Subscribers** | `HUD._on_boss_phase_changed` (`hud.py:186`) |
| **Trigger** | When a boss transitions to a new phase |

### CHECKPOINT_REACHED
| Field | Value |
|-------|-------|
| **Emitter** | `Checkpoint.activate()` (`checkpoint.py:68-70`) |
| **Payload** | `checkpoint_id: int` |
| **Subscribers** | `HUD._on_checkpoint_reached` (`hud.py:187`) |
| **Trigger** | When the player touches a checkpoint for the first time |

### ENEMY_DIED
| Field | Value |
|-------|-------|
| **Emitter** | `EnemyBase._die()` (`enemy_base.py:412`) |
| **Payload** | `entity_id: int`, `position: tuple[float, float]` |
| **Subscribers** | StageScene `_on_enemy_died` (particle burst), Achievements `_on_enemy_died` (`achievements.py:125`) |
| **Trigger** | When any enemy's health reaches 0 |

### FLAG_SET
| Field | Value |
|-------|-------|
| **Emitter** | `DialogueSystem` action handler (`dialogue_system.py:98`) |
| **Payload** | `flag: str` |
| **Subscribers** | *(none — reserved for future state tracking)* |
| **Trigger** | When a dialogue node executes a `set_flag` action |
| **Note** | Event constant was missing from `Events` class until 2026-07-16. No subscribers exist. |

### HIDE_MESSAGE
| Field | Value |
|-------|-------|
| **Emitter** | `MessageBox.hide()` (`message_box.py:96`) |
| **Payload** | *(none)* |
| **Subscribers** | `MessageBox._on_hide_message` (`message_box.py:57`) |
| **Trigger** | When the message box overlay should be hidden |

### ITEM_COLLECTED
| Field | Value |
|-------|-------|
| **Emitter** | `DialogueSystem` action handler (`dialogue_system.py:96`) |
| **Payload** | `item_id: str` |
| **Subscribers** | *(none — reserved for future inventory system)* |
| **Trigger** | When a dialogue node executes a `give_item:` action |
| **Note** | Event constant was missing from `Events` class until 2026-07-16. No subscribers exist. |

### MUSIC_STINGER
| Field | Value |
|-------|-------|
| **Emitter** | *(none found — reserved)* |
| **Payload** | `name: str`, `volume: float` |
| **Subscribers** | StageScene `_on_music_stinger` (audio stinger playback, `stage_scene.py:364`) |
| **Trigger** | *(event is not currently emitted by any code — handler is registered but never called)* |

### PLAYER_DAMAGED
| Field | Value |
|-------|-------|
| **Emitter** | `Player.apply_damage()` (`player.py:334`) |
| **Payload** | `amount: float`, `source: tuple[float, float]` |
| **Subscribers** | StageScene `_on_player_damaged` (blood particles, camera shake, flash, vignette, `stage_scene.py:357`), HUD `_on_player_damaged` (`hud.py:183`) |
| **Trigger** | When the player takes damage from any source |
| **Dispatch order** | StageScene handler first (VFX), then HUD (health bar update) |

### PLAYER_DIED
| Field | Value |
|-------|-------|
| **Emitter** | `Player.apply_damage()` (`player.py:343`), `HUD` (`hud.py:312`), `StageScene._kill_player()` (`stage_scene.py:788`), `HazardSystem` (`hazard_system.py:26`) |
| **Payload** | `pos: tuple[float, float]` (from StageScene), or empty (from HUD) |
| **Subscribers** | StageScene `_on_player_died` (death particles, `stage_scene.py:358`), SceneManager `_on_player_died` (death timer, `scene_manager.py:43`), HUD `_on_player_died` (`hud.py:185`) |
| **Trigger** | When the player's health reaches 0 or falls into a death pit |

### PLAYER_HEALED
| Field | Value |
|-------|-------|
| **Emitter** | `ProgressionSystem.process_checkpoints()` (`progression_system.py:39`), `Player.heal()` — indirect |
| **Payload** | `amount: int` |
| **Subscribers** | HUD `_on_player_healed` (`hud.py:184`) |
| **Trigger** | When the player receives healing (from checkpoint or item) |

### SAVE_REQUESTED
| Field | Value |
|-------|-------|
| **Emitter** | `ProgressionSystem.process_checkpoints()` (`progression_system.py:42`) |
| **Payload** | `stage_id: str`, `stage_index: int`, `checkpoint_x: float`, `checkpoint_y: float`, `health: float`, `max_health: float` |
| **Subscribers** | StageScene `_on_save_requested` (auto-save, `stage_scene.py:454`) |
| **Trigger** | When the player reaches a new checkpoint |

### SFX_BOSS_HIT
| Field | Value |
|-------|-------|
| **Emitter** | `collision_system.py:106` (via `Events.SFX_ENEMY_HIT`) — *see SFX_ENEMY_HIT* |
| **Payload** | *(same as SFX_ENEMY_HIT)* |
| **Subscribers** | Mapped via StageScene `sfx_map` (en `stage_parts/sonido.py` desde AUD-290) to `"sfx_boss_hit"` |
| **Notes** | This event constant is **defined but never emitted** — it exists for future boss-specific hit sounds. |

### SFX_BOSS_PHASE_CHANGE
*(Defined in Events class, not currently emitted or subscribed)*

### SFX_BOSSES_* (7 events: GAVILAN_DIVE, GAVILAN_MASK_BEAM, PABURU_EYE_BEAM, PABURU_WAVE, RELIC_APPEAR, REY_SPIT, REY_SPLIT)
*(Defined in Events class, not currently emitted or subscribed — reserved for future bosses)*

### SFX_BOSSES_VENADO_CHARGE / STOMP / VINE
| Field | Value |
|-------|-------|
| **Emitter** | `BossVenado` emits `Events.BOSS_ATTACK`, mapped via `sfx_map` (en `stage_parts/sonido.py` desde AUD-290) |
| **Payload** | *(derived from BOSS_ATTACK payload)* |
| **Subscribers** | StageScene SFX handler (`stage_scene.py:424-439`) |
| **Trigger** | When Boss Venado performs charge / stomp / vine attacks |

### SFX_CHECKPOINT
| Field | Value |
|-------|-------|
| **Emitter** | `ProgressionSystem.process_checkpoints()` (`progression_system.py:35`) |
| **Payload** | *(none)* |
| **Subscribers** | Mapped via StageScene `sfx_map` (en `stage_parts/sonido.py` desde AUD-290) to `"sfx_checkpoint"` |
| **Trigger** | When the player touches a checkpoint |

### SFX_ENEMIES_PROJECTILE_HIT_WALL
*(Defined but not emitted or subscribed)*

### SFX_ENEMY_DIE_LARGE / SFX_ENEMY_DIE_SMALL
| Field | Value |
|-------|-------|
| **Emitter** | `EnemyBase._die()` (`enemy_base.py:418`) |
| **Payload** | *(none)* |
| **Subscribers** | Mapped via StageScene `sfx_map` (en `stage_parts/sonido.py` desde AUD-290) |
| **Trigger** | When an enemy dies (LARGE for bosses/brutes, SMALL for walkers/flying) |

### SFX_ENEMY_HIT
| Field | Value |
|-------|-------|
| **Emitter** | `CollisionSystem.check_attack_hits()` (`collision_system.py:106`) |
| **Payload** | `pos: list[float]`, `damage: float` |
| **Subscribers** | StageScene `_on_enemy_hit` (blood particles, camera shake, `stage_scene.py:340`) |
| **Trigger** | When the player's attack connects with an enemy |

### SFX_ENVIRONMENT_ONE_WAY_PLATFORM
*(Defined but not emitted or subscribed)*

### SFX_ENVIRONMENT_SCREEN_SHAKE
*(Defined but not emitted or subscribed)*

### SFX_HAZARD_ZONE
| Field | Value |
|-------|-------|
| **Emitter** | `HazardSystem.update()` (`hazard_system.py:48`) |
| **Payload** | *(none)* |
| **Subscribers** | Mapped via StageScene `sfx_map` (en `stage_parts/sonido.py` desde AUD-290) |
| **Trigger** | When the player takes damage from a hazard zone |

### SFX_HIT_CONNECT
| Field | Value |
|-------|-------|
| **Emitter** | `CollisionSystem.check_attack_hits()` (`collision_system.py:121`) |
| **Payload** | `pos: list[float]`, `damage: float` |
| **Subscribers** | StageScene `_on_hit_connect` (hit particles, damage numbers, `stage_scene.py:339`) |
| **Trigger** | When any player attack hitbox connects (after processing per-enemy hits) |

### SFX_MENU_HOVER
| Field | Value |
|-------|-------|
| **Emitter** | `DemoMenuScene` (`demo_menu_scene.py:115`), `OptionsScene` (`options_scene.py:116`), `TitleScene` (`title_scene.py:121`), `WorldMapScene` (`world_map_scene.py:89`) |
| **Payload** | *(none)* |
| **Subscribers** | Mapped via StageScene `sfx_map` (en `stage_parts/sonido.py` desde AUD-290) |
| **Trigger** | When the user navigates over a menu item |

### SFX_MENU_CONFIRM
| Field | Value |
|-------|-------|
| **Emitter** | `DemoMenuScene` (`demo_menu_scene.py:118`), `OptionsScene` (`options_scene.py:130`), `TitleScene` (`title_scene.py:128`), `WorldMapScene` (`world_map_scene.py:93`) |
| **Payload** | *(none)* |
| **Subscribers** | Mapped via StageScene `sfx_map` (en `stage_parts/sonido.py` desde AUD-290) |
| **Trigger** | When the user confirms a menu selection |

### SFX_MENU_CANCEL
| Field | Value |
|-------|-------|
| **Emitter** | `DemoMenuScene` (`demo_menu_scene.py:134`), `OptionsScene` (`options_scene.py:118`), `TitleScene` (`title_scene.py:132`) |
| **Payload** | *(none)* |
| **Subscribers** | Mapped via StageScene `sfx_map` (en `stage_parts/sonido.py` desde AUD-290) |
| **Trigger** | When the user cancels/dismisses a menu |

### SFX_PLAYER_CROUCH
*(Defined but not emitted or subscribed)*

### SFX_PLAYER_DIE
| Field | Value |
|-------|-------|
| **Emitter** | `Player.apply_damage()` (`player.py:344`) |
| **Payload** | *(none)* |
| **Subscribers** | Mapped via StageScene `sfx_map` (en `stage_parts/sonido.py` desde AUD-290) |
| **Trigger** | When the player dies |

### SFX_PLAYER_FOOTSTEP
| Field | Value |
|-------|-------|
| **Emitter** | `WalkingState` (`states/grounded.py:83`) |
| **Payload** | *(none)* |
| **Subscribers** | Mapped via StageScene `sfx_map` (en `stage_parts/sonido.py` desde AUD-290) |
| **Trigger** | On each footstep during player walk animation |

### SFX_PLAYER_HEAL
*(Defined but not emitted or subscribed)*

### SFX_PLAYER_HURT
| Field | Value |
|-------|-------|
| **Emitter** | `Player.apply_damage()` (`player.py:348`) |
| **Payload** | *(none)* |
| **Subscribers** | Mapped via StageScene `sfx_map` (en `stage_parts/sonido.py` desde AUD-290) |
| **Trigger** | When the player takes damage (but doesn't die) |

### SFX_PLAYER_JUMP
| Field | Value |
|-------|-------|
| **Emitter** | `JumpingState` (`states/airborne.py:79`), `WallSlideState` (`states/wall.py:13`) |
| **Payload** | *(none)* |
| **Subscribers** | Mapped via StageScene `sfx_map` (en `stage_parts/sonido.py` desde AUD-290) |
| **Trigger** | When the player jumps |

### SFX_PLAYER_LAND
| Field | Value |
|-------|-------|
| **Emitter** | `Player` physics update (`player.py:654`) |
| **Payload** | *(none)* |
| **Subscribers** | Mapped via StageScene `sfx_map` (en `stage_parts/sonido.py` desde AUD-290) |
| **Trigger** | When the player lands on the ground after being airborne |

### SFX_PLAYER_LONG_ATTACK
| Field | Value |
|-------|-------|
| **Emitter** | los estados de ataque de `states/attack.py` |
| **Payload** | *(none)* |
| **Subscribers** | Mapped via StageScene `sfx_map` (en `stage_parts/sonido.py` desde AUD-290) |
| **Trigger** | When the player performs a long/heavy attack |

### SFX_PLAYER_PARRY
*(Defined but not emitted or subscribed)*

### SFX_PLAYER_SHORT_ATTACK
| Field | Value |
|-------|-------|
| **Emitter** | los estados de ataque de `states/attack.py` |
| **Payload** | *(none)* |
| **Subscribers** | Mapped via StageScene `sfx_map` (en `stage_parts/sonido.py` desde AUD-290) |
| **Trigger** | When the player performs a quick/short attack |

### SFX_PROJECTILE_FIRE
| Field | Value |
|-------|-------|
| **Emitter** | `EnemyCaster` (`enemy_caster.py:180`), `EnemyArcher` (`enemy_archer.py:119`), `EnemyShooter` (`enemy_shooter.py:315`) |
| **Payload** | *(none)* |
| **Subscribers** | Mapped via StageScene `sfx_map` (en `stage_parts/sonido.py` desde AUD-290) |
| **Trigger** | When an enemy fires a projectile |

### SFX_STAGE_BANNER
| Field | Value |
|-------|-------|
| **Emitter** | `StageScene` (`stage_scene.py:194`) |
| **Payload** | *(none)* |
| **Subscribers** | Mapped via StageScene `sfx_map` (en `stage_parts/sonido.py` desde AUD-290) |
| **Trigger** | When the stage name banner is displayed |

### SFX_STAGE_COMPLETE
| Field | Value |
|-------|-------|
| **Emitter** | `StageScene.check_stage_complete()` (`stage_scene.py:622,625`) |
| **Payload** | *(none)* |
| **Subscribers** | Mapped via StageScene `sfx_map` (en `stage_parts/sonido.py` desde AUD-290) |
| **Trigger** | When the player completes a stage |

### SFX_UI_GAME_OVER
*(Defined but not emitted or subscribed)*

### SHOW_MESSAGE
| Field | Value |
|-------|-------|
| **Emitter** | `HazardSystem.update()` — message triggers (`hazard_system.py:38`) |
| **Payload** | `text: str`, `duration: float` |
| **Subscribers** | `MessageBox._on_show_message` (`message_box.py:56`) |
| **Trigger** | When the player overlaps a message trigger zone |

### STAGE_COMPLETE
| Field | Value |
|-------|-------|
| **Emitter** | `StageScene.check_stage_complete()` (`stage_scene.py:635`), `BossVenado.on_defeated()` — indirect |
| **Payload** | `stage_id: str` |
| **Subscribers** | `SceneManager._on_stage_complete` (advance to next stage, `scene_manager.py:42`), `HUD._on_stage_complete` (`hud.py:188`) |
| **Trigger** | When the stage exit is reached or final boss is defeated |

### VFX_CHARGE
| Field | Value |
|-------|-------|
| **Emitter** | `ChargingState` (`states/ability.py:279`), `WallSlideState` (`states/wall.py:13`) |
| **Payload** | `pos: tuple[float, float]`, `level: int` |
| **Subscribers** | StageScene `_on_vfx_charge` (charge particles, `stage_scene.py:360`) |
| **Trigger** | When the player charges an attack |

### VFX_PARRY
| Field | Value |
|-------|-------|
| **Emitter** | `ParryState` (`states/ability.py:93`), `EnemyBase._on_parried()` (`enemy_base.py:526`), `EnemyCaster` (`enemy_caster.py:208`), `EnemyArcher` (`enemy_archer.py:147`), `EnemyShooter` (`enemy_shooter.py:204`) |
| **Payload** | `pos: tuple[float, float]` |
| **Subscribers** | StageScene `_on_vfx_parry` (parry particles, camera shake, flash, bloom, `stage_scene.py:359`), Achievements `_on_parry` (`achievements.py:126`) |
| **Trigger** | When a player parry connects with an enemy attack |

### VFX_SLAM
| Field | Value |
|-------|-------|
| **Emitter** | `PlayerStates.SlamState` (`player_states.py:1268`) |
| **Payload** | `pos: tuple[float, float]` |
| **Subscribers** | StageScene `_on_vfx_slam` (slam particles, camera shake, `stage_scene.py:361`) |
| **Trigger** | When the player performs a ground slam |

### VFX_ULTIMATE
| Field | Value |
|-------|-------|
| **Emitter** | `PlayerStates.UltimateState` (`player_states.py:798`) |
| **Payload** | `pos: tuple[float, float]` |
| **Subscribers** | StageScene `_on_vfx_ultimate` (ultimate particles, bloom, flash, shake, `stage_scene.py:362`) |
| **Trigger** | When the player uses the ultimate/special attack |

---

## 3. Orphan Events (defined but never emitted nor subscribed)

These events exist in the `Events` class but have **zero emit sites and zero subscribers**:

| Event | Notes |
|-------|-------|
| `PLAYER_HEALED` | Subscribed by HUD, but only emitted indirectly via checkpoint healing in ProgressionSystem (not from Player.heal() directly). One-directional. |
| `MUSIC_STINGER` | Subscribed by StageScene, never emitted by any code |
| `SFX_BOSS_HIT` | Reserved |
| `SFX_BOSS_PHASE_CHANGE` | Reserved |
| `SFX_BOSSES_GAVILAN_DIVE` | Future boss |
| `SFX_BOSSES_GAVILAN_MASK_BEAM` | Future boss |
| `SFX_BOSSES_PABURU_EYE_BEAM` | Future boss |
| `SFX_BOSSES_PABURU_WAVE` | Future boss |
| `SFX_BOSSES_RELIC_APPEAR` | Future boss mechanic |
| `SFX_BOSSES_REY_SPIT` | Future boss |
| `SFX_BOSSES_REY_SPLIT` | Future boss |
| `SFX_ENEMIES_PROJECTILE_HIT_WALL` | Unused |
| `SFX_ENVIRONMENT_ONE_WAY_PLATFORM` | Unused |
| `SFX_ENVIRONMENT_SCREEN_SHAKE` | Unused |
| `SFX_PLAYER_CROUCH` | Unused |
| `SFX_PLAYER_HEAL` | Unused |
| `SFX_PLAYER_PARRY` | Unused |
| `SFX_UI_GAME_OVER` | Unused |

---

## 4. Undefined Events (emitted but not in Events class)

These are **string literals** or attribute references that exist in emit/subscribe calls but are NOT defined in `Events`:

| Event Literal | File | Line | Action Taken |
|---------------|------|------|-------------|
| `Events.ITEM_COLLECTED` | `dialogue_system.py` | 96 | ✅ Added to `Events` class (2026-07-16) |
| `Events.FLAG_SET` | `dialogue_system.py` | 98 | ✅ Added to `Events` class (2026-07-16) |

---

## 5. Subscriber Dispatch Order Map

This section documents the **order** in which multiple subscribers receive the same event.

### PLAYER_DAMAGED
1. **StageScene._on_player_damaged** — spawns blood particles, camera shake, flash, vignette
2. **HUD._on_player_damaged** — updates health bar display

### PLAYER_DIED
1. **StageScene._on_player_died** — death particles, camera shake, flash
2. **HUD._on_player_died** — hides HUD
3. **SceneManager._on_player_died** — starts death-timer → game over scene
*(Note: depends on subscribe order in `StageScene.on_enter()` vs `SceneManager.__init__` vs `HUD.__init__`)*

### ENEMY_DIED
1. **StageScene._on_enemy_died** — spawns death particles
2. **Achievements._on_enemy_died** — tracks enemy kill count

### STAGE_COMPLETE
1. **HUD._on_stage_complete** — plays stage complete animation
2. **SceneManager._on_stage_complete** — advances to next stage or menu

### VFX_PARRY
1. **StageScene._on_vfx_parry** — parry particles, shake, flash, bloom
2. **Achievements._on_parry** — tracks parry count

---

## 6. Findings & Recommendations

### 6.1 Findings

1. **No subscriber for SFX events in non-StageScene contexts** — All SFX events are wired only inside `StageScene`. Menu SFX events (`SFX_MENU_HOVER`, `SFX_MENU_CONFIRM`, `SFX_MENU_CANCEL`) work because they use the same EventBus instance, but they depend on StageScene being the active scene.

2. **ITEMS_COLLECTED and FLAG_SET had no event constants** — DialogueSystem emitted these via `Events.ITEM_COLLECTED` and `Events.FLAG_SET` but they were missing from the `Events` class. Fixed in this audit.

3. **14 orphan events** — defined but never emitted. Some are reserved for future bosses.

4. **`MUSIC_STINGER` has a subscriber but no emitter** — StageScene registers a handler but nothing ever fires this event.

5. **`PLAYER_HEALED` is emitted via raw event name** — `ProgressionSystem.process_checkpoints()` uses `Events.PLAYER_HEALED` but `Player.heal()` does NOT emit this event. Only checkpoint healing triggers it.

### 6.2 Recommendations

1. 🔴 **Remove orphan events** or add a lint check to warn about events with no emit sites
2. 🟡 **Wire `MUSIC_STINGER`** into boss phase transitions (`BossBase._finish_phase_transition`)
3. 🟢 **Add subscriber‑side integration tests** for all events that have both emitter and subscriber
4. 🟢 **Consider an `unsubscribe_all_events(callback)`** helper on EventBus for cleaner cleanup
