# Legacy of InFest — Enemy Specification

**Document ID:** LOI-ENEMY-005  
**Version:** 1.0.0  
**Status:** Official  
**Audience:** Professor, Teaching Assistants, Students, AI coding assistants

---

## 1. Enemy Philosophy

### 1.1 Enemies as Academic Vehicles

Enemies in Legacy of InFest are not designed for maximum gameplay difficulty. They are designed for maximum educational clarity. Each enemy template demonstrates a distinct combination of course concepts — pathfinding using curve mathematics, behavioral state machines, collision and interaction, and visual processing feedback.

Every enemy class is intentionally simple enough to be read and understood by a student in a single session. Every student who builds a custom enemy for their stage must be able to explain, in a written README, exactly which course concepts their enemy implements and how.

### 1.2 Enemy Design Constraints

| Constraint | Reason |
|---|---|
| Maximum of 3 enemy types per student stage | Keeps scope manageable; forces depth over breadth |
| All enemies inherit from `EnemyBase` | Ensures lifecycle compatibility with the stage system |
| Enemies communicate with the player via EventBus only | Prevents tight coupling |
| Enemies do not call `InputManager` | Enemies are autonomous agents; input is a player-only system |
| Enemy sprite palettes must stay within 16 colors | SNES constraint |

### 1.3 Enemy Taxonomy

The framework provides three enemy archetypes. Students may subclass any of these to create variations for their stages.

| Class | Movement | Attack | Academic Focus |
|---|---|---|---|
| `EnemyWalker` | Horizontal patrol | Contact damage | State machines, collision |
| `EnemyFlying` | Curved/waypoint flight | Contact damage | Curve mathematics, interpolation |
| `EnemyShooter` | Stationary or slow patrol | Projectile emission | Range detection, trigonometry |

---

## 2. Enemy Base Class — `EnemyBase`

`EnemyBase` is the abstract root class for all enemies. It inherits from `BaseEntity` and adds the health system, damage reception, death handling, hitbox/hurtbox infrastructure, and animation state management.

### 2.1 Properties

| Property | Type | Default | Description |
|---|---|---|---|
| `max_health` | float | Defined per subclass | Maximum hit points |
| `current_health` | float | `max_health` | Current hit points |
| `is_alive` | bool | `True` | False when health reaches 0 |
| `facing_direction` | int | `1` (right) | -1 for left, +1 for right |
| `state` | str | `"PATROL"` | Current FSM state name |
| `hitbox` | pygame.Rect | Defined per subclass | Damage-dealing zone |
| `hurtbox` | pygame.Rect | Defined per subclass | Damage-receiving zone |
| `damage_on_contact` | float | 0.50 | Hearts of damage dealt on hurtbox collision |
| `contact_knockback` | float | 120.0 | Horizontal knockback speed applied to player |
| `death_sfx` | str | `"sfx_enemy_die"` | Sound played on death |
| `hit_sfx` | str | `"sfx_enemy_hit"` | Sound played on receiving a hit |

### 2.2 Required Overrides

Subclasses must implement:

| Method | Signature | Description |
|---|---|---|
| `_patrol_behavior(dt)` | `(float) → None` | Default movement/AI when no player detected |
| `_alert_behavior(dt)` | `(float) → None` | AI when player is within detection range |
| `_get_animation_state()` | `() → str` | Return animation key for current state |
| `_build_hitbox()` | `() → pygame.Rect` | Define the local-space hitbox rect |
| `_build_hurtbox()` | `() → pygame.Rect` | Define the local-space hurtbox rect |

### 2.3 Provided Methods (Do Not Override)

| Method | Description |
|---|---|
| `apply_hit(damage, source_position)` | Apply damage, trigger hurt state, emit events |
| `_die()` | Handle death: play animation, emit `ENEMY_DIED`, schedule removal |
| `_update_invincibility(dt)` | Tick down invincibility timer, toggle flash |
| `_check_player_contact(player)` | If hurtboxes overlap, deal contact damage to player |
| `_update_rects()` | Recompute hitbox and hurtbox world positions from local offsets |
| `update(dt)` | Master update: tick state machine, call behavior, update rects, animation |
| `draw(surface, camera_offset)` | Blit current animation frame, optionally draw debug rects |

### 2.4 Life Cycle

```
EnemyBase instantiated
    ↓
on_spawn() called (optional override)
    ↓
Every frame: update(dt)
    ├── _update_invincibility(dt)
    ├── _run_state_machine(dt)
    │     ├── state == "PATROL" → _patrol_behavior(dt)
    │     ├── state == "ALERT" → _alert_behavior(dt)
    │     ├── state == "HURT" → hurt timer tick
    │     └── state == "DYING" → death animation tick → _die()
    ├── _update_rects()
    └── _check_player_contact(player)
    ↓
apply_hit() called by player attack collision system
    ├── current_health -= damage
    ├── if current_health <= 0: state = "DYING"
    └── else: state = "HURT", start hurt_timer
    ↓
Death animation completes
    ├── EventBus.emit("ENEMY_DIED", entity_id, position)
    └── is_active = False (removed from entity list next frame)
```

### 2.5 Detection System

All enemies share a detection range check. The player's position is compared against the enemy's `detection_rect`, a wider invisible rectangle centered on the enemy.

| Property | Default | Description |
|---|---|---|
| `detection_range_x` | 160 pixels | Horizontal half-width of detection zone |
| `detection_range_y` | 64 pixels | Vertical half-height of detection zone |

When the player enters the detection zone, the enemy transitions from `PATROL` to `ALERT`. When the player leaves the detection zone extended by a `deaggro_margin` (default 32 pixels), the enemy returns to `PATROL`.

---

## 3. Walker Enemy — `EnemyWalker`

### 3.1 Description

The Walker is a ground-bound enemy that patrols horizontally along a defined segment. It reverses direction at patrol limits or at ledge edges. When the player enters its detection range, it accelerates toward the player.

The Walker is the simplest enemy and the primary demonstration vehicle for:
- Horizontal state machine behavior
- Platform edge detection
- Contact damage and knockback
- Basic collision resolution

### 3.2 Attributes

| Attribute | Value |
|---|---|
| Max health | 2.0 hearts |
| Patrol speed | 45.0 px/s |
| Alert speed | 75.0 px/s |
| Damage on contact | 0.50 hearts |
| Detection range X | 160 px |
| Detection range Y | 48 px |
| Patrol segment length | Defined in TMX properties (default 96 px) |

### 3.3 States

| State | Behavior |
|---|---|
| `PATROL` | Move at patrol speed in facing direction. Reverse at patrol limit or ledge edge. |
| `ALERT` | Move toward player at alert speed. Continue until player leaves deaggro zone. |
| `HURT` | Halt movement for 0.25 seconds. Flash sprite. |
| `DYING` | Play death animation. No movement. |

### 3.4 Patrol Limit Detection

The Walker tracks a `patrol_origin` (spawn position) and a `patrol_length` property. It reverses when:

```
abs(position.x - patrol_origin.x) >= patrol_length / 2
```

### 3.5 Ledge Detection

Before each horizontal move, the Walker probes one tile ahead and one tile below using a point-cast against the collision rect list. If no floor tile is found below the next step, the Walker reverses. This is computed as:

```
probe_x = position.x + (facing_direction * (rect.width / 2 + 2))
probe_y = position.y + rect.height + 4
ledge_check = any(probe_x in r.x_range and probe_y in r.y_range for r in collision_rects)
```

### 3.6 Animations

| State | File | Frames | FPS | Loop |
|---|---|---|---|---|
| Walk | `enemy_walker_walk.png` | 6 | 10 | Yes |
| Alert walk | `enemy_walker_walk.png` | 6 | 14 | Yes |
| Hurt | `enemy_walker_hurt.png` | 3 | 12 | No |
| Die | `enemy_walker_die.png` | 6 | 10 | No |

### 3.7 Hitbox and Hurtbox

The Walker has no active attack hitbox — its damage is contact-based (hurtbox-to-hurtbox overlap with the player).

| Box | Offset X | Offset Y | Width | Height |
|---|---|---|---|---|
| Hurtbox | 4 px from sprite left | 2 px from sprite top | 24 px | 28 px |

---

## 4. Flying Enemy — `EnemyFlying`

### 4.1 Description

The Flying enemy travels through the air along a computed path. In its default implementation, the path is a sine-wave oscillation or a Bézier curve defined by waypoints in the TMX map. This enemy is the primary academic demonstration of:

- Bézier curves and parametric path sampling (Unit III)
- Sine-wave motion and trajectory mathematics (Unit III)
- Interpolation between waypoints (Unit VI)

### 4.2 Attributes

| Attribute | Value |
|---|---|
| Max health | 1.5 hearts |
| Flight speed | 60.0 px/s (along path) |
| Sine amplitude | 28.0 px (default) |
| Sine frequency | 1.5 Hz (default) |
| Damage on contact | 0.50 hearts |
| Detection range X | 180 px |
| Detection range Y | 96 px |

### 4.3 Y-Tracking (Alert Mode)

When the player enters detection range, the flying enemy accelerates path speed by 1.5× and actively tracks the player's Y position. This uses a **leaky-integrator offset** (`_y_track_offset`) that persists across strategy frames:

```
# Each alert frame:
# 1. Strategy executes (fully resets position.y for sine/bezier modes)
# 2. Compute Y error: player_center_y - (position.y + _y_track_offset + rect.height/2)
# 3. Push offset toward player at 0.4 × flight_speed
# 4. Damp offset: _y_track_offset *= 0.98
# 5. Apply: position.y += _y_track_offset
```

The 0.98 damping prevents windup while keeping the enemy near the player's vertical position. The offset resets to 0.0 when returning to PATROL state.

### 4.4 Flight Modes

The flight mode is specified in the TMX object properties:

| Mode | Property Key | Description |
|---|---|---|
| `sine` | `flight_mode=sine` | Horizontal movement with sinusoidal vertical oscillation |
| `bezier` | `flight_mode=bezier` | Follow a Bézier path defined by waypoint objects in TMX |
| `patrol` | `flight_mode=patrol` | Linear ping-pong between two waypoints |

**Sine Mode:**
```
position.x += speed * facing_direction * dt
position.y = origin.y + amplitude * sin(2π * frequency * elapsed_time)
```

**Bézier Mode:**
The TMX object layer defines control points as `Waypoint` objects tagged to this enemy's `id`. The `CurveTools.bezier(control_points, n_samples=64)` function pre-computes the path on spawn. The enemy then uses `CurveTools.sample_path(path_points, t)` to find its current position, where `t` advances at `speed / path_length` per second.

### 4.4 States

| State | Behavior |
|---|---|
| `PATROL` | Follow defined flight path continuously |
| `ALERT` | Accelerate path speed by 1.5×, track player's Y axis via leaky-integrator offset (`_y_track_offset`, damping 0.98) that survives strategy position resets |
| `HURT` | Halt for 0.2 seconds. Flash. |
| `DYING` | Slow fall animation with horizontal drift. No path following. |

### 4.5 Animations

| State | File | Frames | FPS | Loop |
|---|---|---|---|---|
| Fly | `enemy_flying_fly.png` | 4 | 12 | Yes |
| Alert | `enemy_flying_fly.png` | 4 | 16 | Yes |
| Hurt | `enemy_flying_hurt.png` | 3 | 12 | No |
| Die | `enemy_flying_die.png` | 8 | 10 | No |

### 4.6 Hitbox and Hurtbox

| Box | Offset X | Offset Y | Width | Height |
|---|---|---|---|---|
| Hurtbox | 6 px from sprite left | 4 px from sprite top | 20 px | 14 px |

---

## 5. Shooter Enemy — `EnemyShooter`

### 5.1 Description

The Shooter enemy fires projectiles at the player when detection conditions are met. It may be stationary or perform a slow patrol. This enemy demonstrates:

- Range detection using distance calculation (Unit II — vectors)
- Angle calculation using `atan2` (Unit II — vectors)
- Projectile as a sub-entity with its own velocity and lifetime (Unit IV — sprites)

### 5.2 Attributes

| Attribute | Value |
|---|---|
| Max health | 3.0 hearts |
| Patrol speed | 20.0 px/s (if mobile) |
| Projectile speed | 120.0 px/s |
| Projectile damage | 0.50 hearts |
| Fire rate | 1 shot per 2.0 seconds |
| Max active projectiles | 3 |
| Detection range X | 200 px |
| Detection range Y | 64 px |
| Contact damage | 0.25 hearts |

### 5.3 States

| State | Behavior |
|---|---|
| `PATROL` | Slow horizontal movement or idle |
| `ALERT` | Face player, enter firing stance |
| `FIRING` | Emit projectile at computed angle, respect fire rate |
| `HURT` | Interrupt firing for 0.4 seconds. Flash. |
| `DYING` | Play death animation. Expire all projectiles. |

### 5.4 Projectile System

#### Projectile Entity

Each fired projectile is a lightweight `Projectile` entity with the following properties:

| Property | Value |
|---|---|
| Velocity | Computed from shooter → player angle at fire time |
| Lifetime | 3.0 seconds |
| Damage | Inherited from parent shooter's `projectile_damage` |
| Sprite | `enemy_shooter_projectile.png` (4×4 px glowing orb) |
| Hurtbox | 4×4 px, centered on position |
| Collision | Expires on contact with collision tiles OR player hurtbox |

**Angle Calculation:**
```python
dx = player.rect.centerx - shooter.rect.centerx
dy = player.rect.centery - shooter.rect.centery
angle = math.atan2(dy, dx)  # Radians
velocity_x = math.cos(angle) * PROJECTILE_SPEED
velocity_y = math.sin(angle) * PROJECTILE_SPEED
```

This calculation is documented inline in the source code as an illustration of Unit II vector mathematics.

#### Projectile Lifecycle

```
Shooter fires:
  ├── Create Projectile at shooter's muzzle position
  ├── Set velocity from angle calculation
  ├── Add to stage entity list
  └── Reset fire_cooldown_timer

Each frame:
  ├── Update projectile position (velocity * dt)
  ├── Check collision with solid tiles → expire
  ├── Check hurtbox overlap with player → deal damage, expire
  └── Check lifetime elapsed → expire

Expiration:
  └── is_active = False (removed next frame)
```

### 5.5 Animations

| State | File | Frames | FPS | Loop |
|---|---|---|---|---|
| Idle/Patrol | `enemy_shooter_idle.png` | 4 | 6 | Yes |
| Alert/Aim | `enemy_shooter_aim.png` | 3 | 8 | No (hold last) |
| Fire | `enemy_shooter_fire.png` | 5 | 16 | No |
| Hurt | `enemy_shooter_hurt.png` | 3 | 12 | No |
| Die | `enemy_shooter_die.png` | 7 | 10 | No |

### 5.6 Hitbox and Hurtbox

| Box | Offset X | Offset Y | Width | Height |
|---|---|---|---|---|
| Hurtbox | 4 px from sprite left | 2 px from sprite top | 24 px | 30 px |

---

## 6. Attributes Summary Table

| Attribute | EnemyWalker | EnemyFlying | EnemyShooter |
|---|---|---|---|
| Max health | 2.0 | 1.5 | 3.0 |
| Contact damage | 0.50 | 0.50 | 0.25 |
| Invincibility after hit | 0.5 s | 0.3 s | 0.4 s |
| Death SFX | `sfx_walker_die` | `sfx_flying_die` | `sfx_shooter_die` |
| Has projectiles | No | No | Yes |
| Gravity affected | Yes | No | Yes (if mobile) |
| Patrol limit (default) | 96 px | Path-based | 48 px |

---

## 7. States Reference

All enemies share the base state names listed below. Subclasses may add additional states.

| State Name | Applicable To | Description |
|---|---|---|
| `PATROL` | All | Default movement behavior |
| `ALERT` | All | Player detected, reactive behavior |
| `FIRING` | Shooter only | Emitting a projectile |
| `HURT` | All | Damage received, brief stun |
| `DYING` | All | Death animation playing |

---

## 8. Animation Rules

### 8.1 General Rules

- All enemy sprite sheets are horizontal, equal-width frames.
- All sheets face right. Horizontal flip is applied when `facing_direction == -1`.
- Non-looping animations hold on the last frame until the state exits.
- Looping animations restart from frame 0 when the animation completes.

### 8.2 Death Animation Special Rule

The death animation is non-interruptible. Once `DYING` is entered, no incoming `apply_hit()` calls have any effect. The entity is immune to further state changes until `is_active = False`.

### 8.3 Flashing During Hurt / Invincibility

When an enemy receives a hit and is within its invincibility window:
- Alpha toggles between 255 and 0 every 4 frames.
- The flash count equals `ceil(invincibility_duration * 60 / 4)`.

### 8.4 Student Animation Extension Rule

Students creating custom enemy subclasses must:
1. Add a new sprite sheet to `student_assets/sprites/enemies/`.
2. Define all animation entries in the subclass `__init__`, using `AssetLoader`.
3. Override `_get_animation_state()` to return the correct key for the subclass's states.
4. Not modify any existing animation files in `assets/sprites/enemies/`.

---

## 9. Collision Rules

### 9.1 Enemy vs. Solid Tiles

Walkers and Shooters participate in gravity and platform collision identically to the player (axis-separated resolution). Flying enemies do not apply gravity and do not resolve tile collision — they pass over and through terrain (their path is defined above the terrain).

### 9.2 Enemy vs. Player Hurtbox (Contact Damage)

Every frame, each active enemy calls `_check_player_contact(player)`. If the enemy's `hurtbox` rect overlaps the player's `hurtbox` rect, and the player is not invincible:

1. `player.apply_damage(self.damage_on_contact, self.rect.center, self.contact_knockback)` is called (the knockback force defaults to 120.0 and can be overridden per enemy).
2. A 0.3-second cooldown prevents repeated damage application from sustained overlap.

### 9.3 Player Attack vs. Enemy Hurtbox

The player's attack hitbox collision is checked by the stage's collision system (not by the enemy). In the stage update loop:

```python
for enemy in active_enemies:
    if player.active_hitbox and player.active_hitbox.colliderect(enemy.hurtbox):
        enemy.apply_hit(
            damage=player.current_attack_damage,
            source_position=player.rect.center
        )
        player.consume_hitbox()  # Prevent multi-hit on same frame
```

### 9.4 Projectile vs. Player Hurtbox

Projectile collision is checked in the projectile's own `update()` method:

```python
if self.hurtbox.colliderect(player.hurtbox):
    player.apply_damage(self.damage, source_position=self.rect.center)
    self.is_active = False
```

### 9.5 Enemy vs. Enemy

Enemies do not collide with each other. They pass through each other's rects. This simplification is intentional — enemy-to-enemy collision is not an academic objective and adds unnecessary complexity.

---

## 10. AI Rules

### 10.1 Detection Rule

Detection is not line-of-sight. It is pure range check. This is intentional: it keeps AI simple enough to study and understand in the context of a course exercise.

```python
@property
def _player_in_range(self) -> bool:
    dx = abs(player.rect.centerx - self.rect.centerx)
    dy = abs(player.rect.centery - self.rect.centery)
    return dx <= self.detection_range_x and dy <= self.detection_range_y
```

### 10.2 Facing Rule

All enemies always face the direction of their current movement. When stationary in `ALERT` state, enemies face the player.

```python
if target_x < self.rect.centerx:
    self.facing_direction = -1
elif target_x > self.rect.centerx:
    self.facing_direction = 1
```

### 10.3 State Transition Timing

State transitions may not occur more than once per frame. If multiple conditions are simultaneously true (e.g., player in range AND health dropped to zero in the same frame), the priority order is:

```
DYING > HURT > ALERT > PATROL
```

### 10.4 Student AI Extension Rules

Students may extend enemy AI within their stage by subclassing the provided enemy templates. Custom AI must:

1. Call `super().update(dt)` to preserve base lifecycle behavior.
2. Implement custom behavior only within overrides of `_patrol_behavior()` or `_alert_behavior()`.
3. Not bypass the FSM by setting `self.state` directly from outside the class.
4. Document the academic concept driving the custom AI in a comment block.

---

## 11. Examples

### 11.1 Spawning a Walker via TMX

In the TMX object layer, create an object of type `Walker` with the following properties:

```
Type: Walker
Properties:
  patrol_length: 128
  damage_on_contact: 0.5
  patrol_speed: 40.0
```

`StageLoader` reads these properties and passes them to the `EnemyWalker` constructor.

### 11.2 Custom Enemy Subclass (Student Example)

```python
# stages/stage1/entities/patrol_guard.py

from framework.entities.enemy_walker import EnemyWalker
from framework.processing.curve_tools import CurveTools

class PatrolGuard(EnemyWalker):
    """
    A Walker subclass that patrols along a Bézier curve path.
    Academic Unit III: Bézier curves and parametric path sampling.
    """

    def __init__(self, spawn_position, control_points, **kwargs):
        super().__init__(spawn_position, **kwargs)
        # Pre-compute Bézier path (Unit III concept)
        self.path = CurveTools.bezier(control_points, n_samples=80)
        self.path_t = 0.0
        self.path_speed = 0.4  # t-units per second

    def _patrol_behavior(self, dt: float) -> None:
        # Advance along the Bézier path
        self.path_t = (self.path_t + self.path_speed * dt) % 1.0
        target = CurveTools.sample_path(self.path, self.path_t)
        dx = target[0] - self.position.x
        self.facing_direction = 1 if dx > 0 else -1
        self.position.x = target[0]
        self.position.y = target[1]
```

### 11.3 Shooter Firing Range Visualization (Stage 0 Debug Mode)

In Stage 0, debug mode renders the Shooter's detection rect as a semi-transparent yellow overlay, and draws a line from the Shooter's muzzle to the player's center when in ALERT state. This visualization is toggled with the `F1` key and serves as a live demonstration of vector distance calculation from Unit II.
