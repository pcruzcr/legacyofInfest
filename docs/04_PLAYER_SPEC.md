---
document_id: "LOI-PLAYER-004"
title: "Legacy of InFest — Player Specification"
aliases: ["Player Specification", "Player Spec"]
tags: ["player", "specification", "entity"]
description: "Player physics, states, combat — complete behavioral spec"
source: "docs/04_PLAYER_SPEC.md"
date_processed: "2026-07-14"
---

# Legacy of InFest — Player Specification

**Document ID:** LOI-PLAYER-004  
**Version:** 1.0.0  
**Status:** Official  
**Audience:** Professor, Teaching Assistants, AI coding assistants

---

<!-- cita-historica -->
> **Corrección AUD-150 — nombres que este documento daba por existentes.**
> Comprobados uno por uno contra el código. Ninguno rompe nada al jugar; todos
> engañan a quien lea el documento para programar.
>
> * `damage_amount` **no existe.** El daño se pasa como argumento a `apply_damage(cantidad, origen)`; el jugador no guarda un campo con la cantidad del último golpe.
<!-- /cita-historica -->


## 1. Concept

The player character is a hooded figure of indeterminate identity. The hood is not a costume choice — it is a narrative device. The character intentionally does not reveal whether it is John or Jin, the two protagonists of the Legacy of InFest universe. This ambiguity serves the tutorial context of Stage 0: the character is an avatar of the player and of the student, not a story character in the full sense.

The visual design must communicate:

- Agility (lean silhouette, fluid animation)
- Mystery (deep hood, face never visible)
- SNES-era authenticity (limited palette, clear readable silhouette at 16×16 to 32×32 sprite size)

The player character is not customizable. Students do not modify the player. The player is a shared framework resource.

---

## 2. Purpose

Within the framework's academic context, the player entity serves three purposes:

**2.1 Interaction Anchor**  
The player is the primary agent through which students and players interact with every stage system. Checkpoints are reached by the player. Enemies react to the player. The HUD reflects the player's state. All stage demonstration systems in Stage 0 are triggered by player proximity or player action.

**2.2 State Machine Reference**  
The player's finite state machine is the most complete example of entity state management in the framework. Students study the player's state machine to understand how to structure their own custom entities.

**2.3 Academic Concept Carrier**  
The player's movement, physics, and animation systems embody course concepts from Units II through VI: vector arithmetic, transformation matrices, frame interpolation, collision detection, sprite animation, and alpha blending.

---

## 3. Controls

All player controls are routed through the `InputManager`. The player entity never queries Pygame directly.

| Action | Keyboard Default | Controller Default |
|---|---|---|
| Walk Left | Left Arrow / A | D-Pad Left / Left Stick Left |
| Walk Right | Right Arrow / D | D-Pad Right / Left Stick Right |
| Jump | Space / W / Up Arrow | A (Xbox) / Cross (PS) |
| Crouch | Down Arrow / S | D-Pad Down / Left Stick Down |
| Short Attack | Z / J | X (Xbox) / Square (PS) |
| Long Attack | X / K | Y (Xbox) / Triangle (PS) |

**Control Rules:**
- Jump is only available when the player is grounded (`GROUNDED` state).
- Short Attack and Long Attack can be performed while walking, standing, or crouching.
- Long Attack while crouching performs a low sweep.
- The player cannot change horizontal direction during an attack animation.
- Jump cancels are not permitted (no double jump, no jump buffering beyond 4 frames).

---

## 4. Movement

### 4.1 Horizontal Movement

The player moves horizontally at a constant walk speed. There is no acceleration or deceleration ramp. This keeps the movement model simple and SNES-authentic (Super Castlevania IV reference).

| Property | Value | Unit |
|---|---|---|
| Walk speed | 90.0 | pixels/second |
| Direction | -1 (left) or +1 (right) | — |
| Facing | Stored as `facing_direction: int` | — |

**Velocity Calculation (per frame):**
```
velocity.x = direction * PLAYER_WALK_SPEED * dt
```

**Crouch Lock:** When `CROUCHING`, horizontal velocity is forced to 0. The player cannot walk while crouched.

### 4.2 Vertical Movement (Physics)

Gravity is applied continuously. The player is grounded when their bottom edge rests on a collision rect.

| Property | Value | Unit |
|---|---|---|
| Gravity | 800.0 | pixels/second² |
| Jump initial velocity | -380.0 | pixels/second |
| Max fall speed | 500.0 | pixels/second |
| Coyote time | 6 | frames |

**Gravity Application (per frame):**
```
velocity.y += GRAVITY * dt
velocity.y = clamp(velocity.y, -INF, MAX_FALL_SPEED)
position.y += velocity.y * dt
```

**Coyote Time:** The player may jump up to 6 frames after walking off a platform edge. This is a standard SNES-era movement quality-of-life feature.

**Jump Cut:** If the player releases the jump button while ascending (velocity.y < 0), the vertical velocity is multiplied by 0.5 on that frame, producing a shorter hop. This allows variable jump height.

### 4.3 Collision Resolution

Collision is axis-separated: horizontal movement is resolved first, then vertical.

**Horizontal Resolution:**
1. Move `position.x` by `velocity.x * dt`
2. Check for overlap with any collision rect
3. If overlapping: push back to the edge of the rect, set `velocity.x = 0`

**Vertical Resolution:**
1. Move `position.y` by `velocity.y * dt`
2. Check for overlap with any collision rect
3. If overlapping and moving down (velocity.y > 0): land on top, set `velocity.y = 0`, set `is_grounded = True`
4. If overlapping and moving up (velocity.y < 0): push down to bottom of rect, set `velocity.y = 0`

### 4.4 One-Way Platforms

Collision rects tagged as `one_way` in the TMX map are passable from below and from the sides. They only resolve collision when the player is moving downward and their previous bottom-edge position was above the platform's top edge.

---

## 5. Health System

### 5.1 Heart Representation

The player's health is measured in hearts, displayed as a row of heart icons in the HUD.

| Property | Value |
|---|---|
| Maximum health | 5.0 hearts |
| Starting health | 5.0 hearts |
| Minimum health | 0.0 hearts |
| Health type | float (supports fractional values) |

### 5.2 Heart Display States

Each heart icon in the HUD renders one of four states based on remaining health:

| State | Threshold | Visual |
|---|---|---|
| Full | ≥ 1.0 remaining for this heart | Solid heart sprite |
| Three-quarter | ≥ 0.75 remaining | Three-quarter heart sprite |
| Half | ≥ 0.50 remaining | Half heart sprite |
| Quarter | ≥ 0.25 remaining | Quarter heart sprite |
| Empty | 0.0 remaining | Empty heart outline sprite |

Health is rendered left to right. The rightmost heart is the first to be depleted.

### 5.3 Invincibility Frames

After receiving damage, the player enters a brief invincibility period during which no further damage is applied.

| Property | Value |
|---|---|
| Invincibility duration | 1.5 seconds |
| Visual feedback | Player sprite flashes (alternates visible/invisible every 6 frames) |

---

## 6. Damage System

### 6.1 Damage Levels

Three tiers of damage exist to allow staged difficulty within a stage:

| Level | Hearts Lost | Typical Source |
|---|---|---|
| Light | 0.25 | Grazing projectile, weak enemy contact |
| Medium | 0.50 | Standard enemy contact, normal projectile |
| Heavy | 1.00 | Strong enemy contact, hazard zone, boss hit |

### 6.2 Damage Application

Damage is applied when the player's **hurtbox** (see Section 8.2) overlaps with an **enemy hitbox** or **hazard rect**.

**Damage Application Sequence:**
1. Check: Is `invincibility_timer > 0`? If yes, skip.
2. Resta del `current_health` la cantidad **que llega como argumento** a `apply_damage(cantidad, origen)`. El jugador no guarda un campo con el daño del último golpe (AUD-150).
3. Clamp `current_health` to `[0.0, MAX_HEALTH]`.
4. Set `invincibility_timer = INVINCIBILITY_DURATION`.
5. Emit `PLAYER_DAMAGED` event with `amount` and `source`.
6. Trigger `HURT` animation state.
7. Apply knockback velocity (see below).
8. If `current_health == 0.0`: emit `PLAYER_DIED`.

### 6.3 Knockback

When the player takes damage, a brief knockback impulse is applied:

| Property | Value |
|---|---|
| Knockback horizontal speed | 150.0 pixels/second (away from source) |
| Knockback vertical speed | -200.0 pixels/second (upward) |
| Knockback duration | 0.3 seconds |

During knockback duration, player input is ignored. The player resumes normal control after the knockback timer expires.

### 6.4 Death

When `current_health` reaches 0.0:

1. The `PLAYER_DIED` event is emitted.
2. The player enters the `DYING` state and plays the death animation.
3. After the death animation completes, `SceneManager` receives the event and pushes `GameOverScene`.

---

## 7. Attack System

### 7.1 Short Attack (Fists)

The short attack is a rapid close-range punch.

| Property | Value |
|---|---|
| Reach | 20 pixels in front of player |
| Width | 12 pixels |
| Height | 16 pixels |
| Damage | 0.50 hearts |
| Active frames | 3 |
| Total animation frames | 6 |
| Cooldown after animation | 0 frames (can chain) |
| Hitstop | 2 frames |

**Behavior:**
- The hitbox is only active during frames 2–4 of the animation.
- The hitbox is positioned relative to the player's facing direction.
- Short attacks can be performed while crouching; the hitbox drops to match the crouched posture.

### 7.2 Long Attack (Stick)

The long attack swings a stick in a wider arc.

| Property | Value |
|---|---|
| Reach | 36 pixels in front of player |
| Width | 36 pixels |
| Height | 20 pixels |
| Damage | 1.00 heart |
| Active frames | 4 |
| Total animation frames | 10 |
| Cooldown after animation | 4 frames |
| Hitstop | 4 frames |

**Behavior:**
- The hitbox is active during frames 4–7.
- The arc sweeps slightly upward on frame 4, horizontal on frames 5–6, slightly downward on frame 7. This is represented by offsetting the hitbox rect's vertical position per active frame.
- Long attack while crouching: the arc is entirely low, covering the floor zone. Hitbox height is 12 pixels, positioned at floor level.

### 7.3 Hitstop

When a player attack connects with an enemy:
1. The game loop's `DeltaClock.time_scale` is set to `0.15` for the hitstop duration, slowing all game-time updates (physics, animations, AI) to 15% speed.
2. Hitstop duration is `frames / 60.0` seconds: **2 frames** for Short Attack (0.5 damage), **4 frames** for Long Attack (1.0 damage).
3. After the hitstop duration expires, `time_scale` is restored to `1.0`.
4. The enemy's `apply_hit()` method is called with the damage amount.
5. The player's hitbox is consumed on any connect — only one enemy per swing takes damage.
6. Only the first enemy hitbox collision triggers hitstop — later enemies hitting the same frame are damaged without re-triggering slowdown (break after first hit).

Implementation: `stage_scene.py` lines 199-211. The timer decrements each frame regardless of `time_scale` so the real-world slowdown persists for the intended number of display frames.

---

## 8. States

The player is governed by a finite state machine. Only one state is active at a time. The `PlayerState` enum in `src/framework/entities/player.py` defines **19 states**.

### 8.1 State Table

| State | Entry Condition | Exit Condition | Input Accepted |
|---|---|---|---|
| `IDLE` | Grounded + no input | Move input OR attack input | All |
| `WALKING` | Grounded + horizontal input | No horizontal input OR jump OR attack | All |
| `JUMPING` | Jump pressed while grounded or within coyote frames | Vertical velocity ≤ 0 (peak) | Move, Attack |
| `FALLING` | Vertical velocity > 0 and not grounded | Land on ground | Move, Attack |
| `CROUCHING` | Down input while grounded | Down released | Short Attack, Long Attack |
| `SHORT_ATTACK` | Short attack input | Animation complete | None (locked) |
| `LONG_ATTACK` | Long attack input | Animation complete + cooldown | None (locked) |
| `HURT` | Damage received | Knockback timer expires | None (locked) |
| `DYING` | Health == 0 | Death animation complete | None (locked) |
| `DASHING` | Dash input while grounded or within air dash limit | Dash timer expires (0.15s) | None (locked) |
| `PARRY` | Attack + crouch simultaneously | Timer expires (0.2s) | None |
| `CHARGE_ATTACK` | Hold long attack | Release long attack | Parry |
| `DASH_ATTACK` | Attack while dashing | Animation complete | None (locked) |
| `WALL_SLIDE` | Touch wall while falling + holding toward wall | Move away from wall or land | Jump, Attack |
| `LEDGE_GRAB` | Reach ledge edge while wall sliding | Jump up or drop down | Jump |
| `GRAB` | Long attack + crouch (no short attack) | Hit connects | Attack (throw) |
| `THROW` | Attack while grabbing | Animation complete | None |
| `SLIDE` | Crouch + momentum while running | Timer expires or crouch released | None (locked) |
| `SWIMMING` | Enter water zone | Leave water (surface/ground) | Move, Jump |

### 8.2 State Transition Diagram (Simplified — Subset of Core States)

The full state machine spans 19 states in the `PlayerState` enum. The diagram below shows the most common transitions. Additional states (PARRY, CHARGE_ATTACK, DASH_ATTACK, WALL_SLIDE, LEDGE_GRAB, GRAB, THROW, SLIDE, SWIMMING) follow similar patterns — see `src/framework/entities/player_states.py` for complete implementation.

```
              ┌─────────────────────────────────────────────┐
              │                                             │
           [IDLE] ←──────── move released ──────────── [WALKING]
              │                                             │
         move input                                    move input
              │                                             │
              └──────────────────────────────────────► [WALKING]
              │
         jump input ──────────────────────────────────► [JUMPING]
              │                                             │
         crouch input ──────────────────────────────► [CROUCHING]   ─► [SHORT_ATTACK]
              │                                                        ─► [LONG_ATTACK]
         attack inputs ─────────────────────────────► [SHORT_ATTACK]
                                                      ► [LONG_ATTACK]

[JUMPING] ──── peak velocity ────────────────────────► [FALLING]
[FALLING] ──── land ─────────────────────────────────► [IDLE]

[IDLE] [WALKING] [CROUCHING]
       [JUMPING] [FALLING] ──── dash input ────────► [DASHING]

[DASHING] ──── timer expires + grounded ────────────► [IDLE]
[DASHING] ──── timer expires + airborne ────────────► [FALLING]

any state (except DYING) ──── damage ───────────────► [HURT]
[HURT] ──── knockback end ───────────────────────────► [IDLE]

any state ──── health == 0 ──────────────────────────► [DYING]
[DYING] ──── animation complete ─────────────────────► (PLAYER_DIED event)
```

---

## 9. Animations

All player animations are horizontal sprite sheets stored in `assets/sprites/player/`.

### 9.1 Animation Specifications

| Animation Name | File | Frame Count | FPS | Loop |
|---|---|---|---|---|
| Idle | `player_idle.png` | 4 | 8 | Yes |
| Walk | `player_walk.png` | 8 | 12 | Yes |
| Jump (ascending) | `player_jump.png` | 3 | 12 | No (hold last frame) |
| Fall (descending) | `player_fall.png` | 2 | 8 | Yes |
| Crouch | `player_crouch.png` | 2 | 8 | No (hold last frame) |
| Short Attack | `player_short_attack.png` | 6 | 18 | No |
| Long Attack | `player_long_attack.png` | 10 | 16 | No |
| Hurt | `player_hurt.png` | 4 | 12 | No |
| Dash | `player_walk.png` | 4 | 12 | No (hold last frame) |
| Die | `player_die.png` | 8 | 10 | No |

### 9.2 Animation Rules

- When entering a non-looping animation, the frame counter always resets to 0.
- When a non-looping animation reaches its last frame, the frame holds until the state exits.
- All animations flip horizontally based on `facing_direction`. The sprite sheets are drawn facing right.
- During the invincibility flashing period, the sprite's alpha alternates between 255 and 0 every 6 frames.
- Sprite frame size: 32×32 pixels. The bounding rect is smaller (see hitbox/hurtbox below).

### 9.3 Animation Controller Logic

```
AnimationController:
  current_animation: str
  current_frame: int
  frame_timer: float

  update(dt: float):
    frame_timer += dt
    if frame_timer >= (1.0 / current_fps):
      frame_timer = 0
      if not at_last_frame OR is_looping:
        current_frame = (current_frame + 1) % frame_count

  get_surface() → pygame.Surface:
    raw = spritesheet.get_frame(current_frame)
    if facing_left: raw = pygame.transform.flip(raw, True, False)
    if flashing and flash_visible: raw.set_alpha(0)
    return raw
```

---

## 10. Hitboxes

Hitboxes are the regions in which the player's attacks can deal damage to enemies. Hitboxes are only active during the defined active frames of an attack animation.

### 10.1 Short Attack Hitbox

Positioned relative to the player's center, offset in the `facing_direction`.

| Property | Value |
|---|---|
| Offset X | 8 pixels toward facing direction from player center |
| Offset Y | -4 pixels (slightly upward from center) |
| Width | 20 pixels |
| Height | 16 pixels |
| Active frames | 2, 3, 4 (of 6 total) |

**Crouching modifier:** Offset Y = +8 pixels (drops to lower zone).

### 10.2 Long Attack Hitbox

The long attack hitbox shifts position across its active frames to simulate a swing arc.

| Active Frame | Offset X | Offset Y | Width | Height |
|---|---|---|---|---|
| 4 | 12 px facing | -10 px | 36 px | 20 px |
| 5 | 18 px facing | -4 px | 36 px | 20 px |
| 6 | 18 px facing | 0 px | 36 px | 20 px |
| 7 | 12 px facing | +6 px | 36 px | 20 px |

**Crouching modifier:** All Y offsets raised by +12 px. Width remains 36 px, height reduced to 12 px.

---

## 11. Hurtboxes

The hurtbox is the region in which the player can receive damage from enemies and hazards. Unlike hitboxes, the hurtbox is always active (except during invincibility frames and the `DYING` state).

### 11.1 Standard Hurtbox

| Property | Value |
|---|---|
| Offset X | 6 pixels from sprite left edge |
| Offset Y | 4 pixels from sprite top edge |
| Width | 20 pixels |
| Height | 28 pixels |

The hurtbox is centered within the 32×32 sprite frame, smaller than the sprite to allow visual near-misses consistent with SNES-era feel.

### 11.2 Crouching Hurtbox

When in the `CROUCHING` state, the hurtbox shrinks vertically:

| Property | Value |
|---|---|
| Offset X | 6 pixels from sprite left |
| Offset Y | 14 pixels from sprite top |
| Width | 20 pixels |
| Height | 18 pixels |

Crouching allows the player to duck under projectiles that pass above the crouching hurtbox.

### 11.3 Hurtbox During Attack States

During `SHORT_ATTACK` and `LONG_ATTACK`, the hurtbox uses the standard dimensions. There is no extended vulnerability during attacks (unlike some action games).

---

## 12. Restrictions

The following constraints apply to the player entity and must not be violated by framework modifications or stage code:

| Restriction | Reason |
|---|---|
| Player class is not subclassed by students | The player is a shared framework resource |
| Player's `_health` attribute is not accessed directly | Always use `player.apply_damage()` and `player.current_health` property |
| Player's state machine is not bypassed | Do not set `player._state` directly from stage code |
| Player sprite files are not replaced | Visual consistency across all stages |
| Player's `InputManager` binding is not modified from stage code | Input is a global system |
| Player's `rect` is not repositioned directly | Use `player.set_spawn(position)` |

---

## 13. Examples

### 13.1 Spawning the Player in a Stage

```python
from framework.entities.player import Player

# In Stage.on_enter():
player = Player(
    spawn_position=stage_data.spawn_point,
)
self.entities.append(player)
self.camera.follow(player)
self.hud.bind_player(player)
```

### 13.2 Checking Player Health from Stage Code

```python
# Correct: use the property
if player.current_health <= 1.0:
    self.event_bus.emit("SHOW_MESSAGE", text="Warning: Low health!", duration=3.0)
```

### 13.3 Subscribing to Player Events in a Custom Stage Entity

```python
from engine.core.event_bus import EventBus

class MyTrigger(BaseEntity):
    def __init__(self):
        super().__init__()
        EventBus.subscribe("PLAYER_DAMAGED", self._on_player_damaged)

    def _on_player_damaged(self, amount, source):
        # React to player taking damage
        if amount >= 1.0:
            self.activate_heavy_damage_effect()

    def on_destroy(self):
        EventBus.unsubscribe("PLAYER_DAMAGED", self._on_player_damaged)
```

### 13.4 Academic Concept — Bounding Box Transformation (Unit II)

The player's hurtbox and hitboxes are defined in local space (relative to the sprite origin) and transformed into world space each frame using a translation matrix. This directly illustrates Unit II's transformation concepts:

```
world_hurtbox_origin = player.position + local_hurtbox_offset
```

In matrix form (homogeneous 2D coordinates):
```
[1  0  tx] [local_x]   [world_x]
[0  1  ty] [local_y] = [world_y]
[0  0   1] [  1    ]   [  1    ]
```

Where `tx, ty = player.position`. Students are expected to recognize this pattern and document it in their stage README when implementing custom entity hitboxes.


--- Traducción al Español ---

## Especificación del Jugador

### Concepto
El personaje jugable es una figura encapuchada de identidad indeterminada. El diseño visual debe comunicar agilidad, misterio y autenticidad SNES.

### Propósitos
1. **Ancla de interacción** — El jugador es el agente principal que interactúa con todos los sistemas del escenario.
2. **Referencia de máquina de estados** — La máquina de estados finitos del jugador es el ejemplo más completo de gestión de estados en el framework.
3. **Portador de conceptos académicos** — El movimiento, la física y la animación incorporan conceptos de las Unidades II a VI.

### Controles
| Acción | Teclado | Control |
|--------|---------|---------|
| Caminar Izquierda | Flecha Izquierda / A | D-Pad Izquierdo / Stick Izquierdo |
| Caminar Derecha | Flecha Derecha / D | D-Pad Derecho / Stick Derecho |
| Saltar | Espacio / W / Flecha Arriba | A (Xbox) |
| Agacharse | Flecha Abajo / S | D-Pad Abajo |
| Ataque Corto | Z / J | X (Xbox) |
| Ataque Largo | X / K | Y (Xbox) |

### Estados del Jugador
El jugador tiene 19 estados: IDLE, WALKING, JUMPING, FALLING, CROUCHING, SHORT_ATTACK, LONG_ATTACK, HURT, DYING, DASHING, PARRY, CHARGE_ATTACK, DASH_ATTACK, WALL_SLIDE, LEDGE_GRAB, GRAB, THROW, SLIDE, SWIMMING.

Para la especificación completa con tablas de física, sistema de daño, hitboxes y ejemplos de código, consultar el documento original en inglés.


---
## 🔗 Documentos Relacionados

- [[45_SWIMMING_SPEC.md|Swimming Spec]]
- [[09_HUD_SPEC.md|HUD Specification]]
- [[03_ARCHITECTURE.md|Architecture]]
