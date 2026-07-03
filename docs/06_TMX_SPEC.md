# Legacy of InFest — TMX Specification

**Document ID:** LOI-TMX-006  
**Version:** 1.0.0  
**Status:** Official  
**Audience:** Professor, Teaching Assistants, Students, AI coding assistants

---

## 1. Overview

Stage maps are designed in **Tiled Map Editor** and exported as `.tmx` files (XML format). The `StageLoader` module parses these files using `pytmx` and `pyscroll` to assemble the complete stage environment: tile layers, entity spawn points, collision zones, checkpoints, portals, and triggers.

This specification defines the exact conventions that all TMX files in Legacy of InFest must follow. Non-conforming TMX files will cause `StageLoader` to raise a `FrameworkUsageError` with a descriptive message identifying the violation.

---

## 2. File Properties

Every TMX file must have the following global map properties configured in Tiled:

| Property | Value | Notes |
|---|---|---|
| Orientation | Orthogonal | No isometric or hexagonal |
| Tile width | 16 | pixels |
| Tile height | 16 | pixels |
| Infinite | No | Maps have fixed dimensions |
| Render order | Right-down | Standard rendering order |
| Minimum map width | 20 tiles (320 px) | Must fill at least one screen |
| Minimum map height | 14 tiles (224 px) | Must fill at least one screen |
| Maximum map width | 512 tiles (8192 px) | Performance constraint |

### 2.1 Custom Map Properties

Each TMX file must declare the following custom properties at the map level:

| Property Name | Type | Required | Description |
|---|---|---|---|
| `stage_id` | string | Yes | Unique stage identifier (`stage0`, `stage1`, etc.) |
| `stage_name` | string | Yes | Display name for the HUD banner (e.g., `"The Awakening"`) |
| `time_limit` | int | Yes | Stage time limit in seconds |
| `bgm_track` | string | Yes | Name of the BGM file (without extension) |
| `background_zone` | string | No | Zone key for loading parallax backgrounds (`assets/backgrounds/{background_zone}/`). If set, `StageLoader` loads `bg_{zone}_{far,mid,near}.png`. If absent or empty, no background layers are loaded. |
| `background_color` | color | No | Sky/background fill color (default: `#000000`) |
| `gravity_multiplier` | float | No | Stage-level gravity scale (default: `1.0`) |
| `debug_mode` | bool | No | Enable debug overlay rendering (default: `false`) |

---

## 3. Layer Standards

Every TMX file must contain layers in the following order, from bottom to top (render order). Layers must be named exactly as specified.

### 3.1 Required Layers

| Layer Order | Layer Name | Layer Type | Description |
|---|---|---|---|
| 1 | `BG_Far` | Tile Layer | Distant background (sky, mountains) — slowest parallax |
| 2 | `BG_Mid` | Tile Layer | Mid-distance background (trees, architecture) — medium parallax |
| 3 | `BG_Near` | Tile Layer | Near background (decorative foreground elements) — fast parallax |
| 4 | `Terrain` | Tile Layer | Primary solid terrain tiles |
| 5 | `Terrain_Detail` | Tile Layer | Non-solid decorative terrain overlays |
| 6 | `Objects` | Object Layer | Entity spawns, triggers, checkpoints, portals |
| 7 | `Collision` | Object Layer | Collision rects (invisible at runtime) |
| 8 | `FG_Overlay` | Tile Layer | Foreground tiles that render above entities (optional) |

### 3.2 Parallax Factors

Each background layer scrolls at a different speed relative to camera movement. These factors are applied automatically by the `Camera` based on the layer name:

| Layer Name | Parallax Factor X | Parallax Factor Y |
|---|---|---|
| `BG_Far` | 0.15 | 0.05 |
| `BG_Mid` | 0.40 | 0.15 |
| `BG_Near` | 0.70 | 0.30 |
| `Terrain` | 1.00 | 1.00 |

### 3.3 Layer Visibility at Runtime

| Layer | Visible at Runtime |
|---|---|
| `BG_Far`, `BG_Mid`, `BG_Near` | Yes |
| `Terrain`, `Terrain_Detail` | Yes |
| `FG_Overlay` | Yes |
| `Objects` | No (spawns entities, then invisible) |
| `Collision` | No (processed into `pygame.Rect` list, then invisible) |

### 3.4 Additional Layers (Optional)

Students may add additional tile layers for visual effect, following this naming rule:

- Additional background layers: prefix with `BG_` followed by a unique descriptor (e.g., `BG_Clouds`)
- Additional foreground layers: prefix with `FG_` followed by a unique descriptor
- No additional object or collision layers are permitted; all data must remain in `Objects` and `Collision`

---

## 4. Object Standards

The `Objects` layer contains all non-tile game data. Each object is a Tiled rectangle or point with a `type` property and optional custom properties.

### 4.1 Object Coordinate System

All object positions in Tiled use pixel coordinates with the origin at the top-left of the map. The `StageLoader` reads these coordinates directly and converts them to world-space `pygame.Vector2` positions.

### 4.2 Object Type Registry

| Object Type | Shape | Required Properties | Description |
|---|---|---|---|
| `PlayerSpawn` | Point | — | Player start position |
| `Walker` | Point | `patrol_length`, `facing` | Spawn a Walker enemy |
| `Flying` | Point | `flight_mode`, `flight_speed` | Spawn a Flying enemy |
| `Shooter` | Point | `fire_rate`, `projectile_speed` | Spawn a Shooter enemy |
| `Checkpoint` | Rectangle | `checkpoint_id` | Checkpoint trigger zone |
| `NextTrigger` | Rectangle | — | Stage completion trigger |
| `Message` | Rectangle | `text`, `duration`, `trigger_once` | Show tutorial message |
| `Waypoint` | Point | `owner_id`, `waypoint_index` | Bézier/patrol waypoint for an entity |
| `HazardZone` | Rectangle | `damage`, `damage_type` | Persistent damage zone |
| `OneWayPlatform` | Rectangle | — | Passable from below |
| `CameraLock` | Rectangle | `lock_x`, `lock_y` | Override camera scroll in zone |
| `BossSpawn` | Point | `boss_id` | Spawn point for boss entity |

---

## 5. Naming Rules

### 5.1 Object Naming

All objects in the `Objects` layer must have a unique name. The name format is:

```
<type>_<id>
```

Examples:
- `PlayerSpawn_01`
- `Walker_01`, `Walker_02`
- `Checkpoint_01`, `Checkpoint_02`
- `Message_01`, `Message_02`
- `Waypoint_01` (with `owner_id` pointing to `Flying_01`)

### 5.2 Tileset Naming

Tilesets referenced by a TMX file must be named and stored according to the standard in `02_CODEX_CONTEXT.md`:

```
tileset_<environment>.png
```

The tileset file must reside in `assets/tilesets/` (for professor-provided tilesets) or `student_assets/tilesets/` (for student-created tilesets).

### 5.3 Property Naming

All custom object properties use `snake_case`. No spaces, no hyphens. Property names must exactly match those defined in this specification or in the entity class that consumes them.

---

## 6. Spawn Rules

### 6.1 Player Spawn

- Exactly one `PlayerSpawn` object must exist per TMX map.
- It is a point object placed on a solid tile surface (player spawns on the ground).
- Its Y position represents the player's feet, not center.
- If no `PlayerSpawn` is found, `StageLoader` raises `FrameworkUsageError("No PlayerSpawn found in TMX")`.

### 6.2 Enemy Spawn

- Enemy objects are point objects placed at the spawn position.
- The spawn position represents the entity's bottom-center (feet), consistent with the player.
- Properties defined on the TMX object override the entity class defaults.
- If a required property is missing, the entity class default is used and a warning is logged.

#### Walker TMX Properties

| Property | Type | Default | Description |
|---|---|---|---|
| `patrol_length` | int | 96 | Total patrol distance in pixels |
| `facing` | string | `"right"` | Initial facing: `"left"` or `"right"` |
| `patrol_speed` | float | 45.0 | Override patrol speed |
| `alert_speed` | float | 75.0 | Override alert speed |
| `damage_on_contact` | float | 0.5 | Override contact damage |

#### Flying TMX Properties

| Property | Type | Default | Description |
|---|---|---|---|
| `flight_mode` | string | `"sine"` | `"sine"`, `"bezier"`, or `"patrol"` |
| `flight_speed` | float | 60.0 | Path traversal speed |
| `sine_amplitude` | float | 28.0 | Vertical oscillation amplitude (sine mode only) |
| `sine_frequency` | float | 1.5 | Oscillation frequency Hz (sine mode only) |
| `owner_id` | string | — | Used on Waypoint objects to link to this entity's name |

#### Shooter TMX Properties

| Property | Type | Default | Description |
|---|---|---|---|
| `fire_rate` | float | 0.5 | Shots per second |
| `projectile_speed` | float | 120.0 | Projectile velocity in px/s |
| `projectile_damage` | float | 0.5 | Damage per projectile hit |
| `patrol_length` | int | 0 | 0 = stationary, >0 = slow patrol |

### 6.3 Waypoint Linking

When a `Flying` enemy uses `flight_mode=bezier` or `flight_mode=patrol`, it reads waypoints from the `Objects` layer. Waypoints are linked by matching the `owner_id` property of the waypoint to the `name` of the Flying object.

Waypoints are sorted by their `waypoint_index` property (integer, 0-based) to form the control point sequence. The resulting array is passed to `CurveTools.bezier()`.

**Example Tiled configuration:**
```
Object: Flying_01 (type: Flying, name: Flying_01)
  Properties: flight_mode=bezier, flight_speed=55.0

Object: Waypoint_01 (type: Waypoint, name: Waypoint_01)
  Properties: owner_id=Flying_01, waypoint_index=0

Object: Waypoint_02 (type: Waypoint, name: Waypoint_02)
  Properties: owner_id=Flying_01, waypoint_index=1

Object: Waypoint_03 (type: Waypoint, name: Waypoint_03)
  Properties: owner_id=Flying_01, waypoint_index=2
```

---

## 7. Checkpoint Rules

### 7.1 Definition

A checkpoint is a rectangle object in the `Objects` layer, type `Checkpoint`. When the player's rect overlaps the checkpoint's rect, the checkpoint activates.

### 7.2 Required Properties

| Property | Type | Description |
|---|---|---|
| `checkpoint_id` | int | Unique integer within the stage (0-based, ascending order) |

### 7.3 Behavior

- Checkpoints activate only once. After activation, they are marked as consumed and will not re-trigger.
- Upon activation, the checkpoint broadcasts `CHECKPOINT_REACHED` via the EventBus with its `checkpoint_id`.
- The `StageLoader` updates the stage's current respawn position to the checkpoint's pixel center X, bottom Y.
- If the player dies after a checkpoint is activated, they respawn at that checkpoint's position with full health.
- Checkpoints are ordered by their `checkpoint_id`. The player must activate them in order — activating checkpoint 2 before checkpoint 1 is valid but checkpoint 1 will not re-activate if reached later.

### 7.4 Visual Feedback

Checkpoints are rendered as a glowing post or flag sprite (non-animated when inactive, animated when active). The visual is part of `assets/sprites/shared/checkpoint.png`. Students may not replace this sprite.

### 7.5 Placement Rules

- At least one checkpoint must be present in every student stage.
- No two checkpoint rects may overlap.
- Checkpoints must be placed on solid ground (their bottom edge must align with a terrain tile top edge).
- Checkpoint rects must be at minimum 16×32 pixels.

---

## 8. Portal Rules

The `NextTrigger` object marks the end of a stage.

### 8.1 Definition

A `NextTrigger` is a rectangle object in the `Objects` layer. When the player's rect overlaps it, the stage emits `STAGE_COMPLETE` via the EventBus.

### 8.2 Placement Rules

- Exactly one `NextTrigger` must exist per TMX map.
- It is typically placed at the rightmost extent of the stage, spanning the full vertical space of a doorway or exit.
- The player must be grounded (not jumping) to trigger it. This prevents accidental activation by jumping over it at a wrong angle.
- A minimum rect size of 16×32 pixels is required.

### 8.3 Behavior on Trigger

1. `STAGE_COMPLETE` event emitted.
2. `SceneManager` receives the event and initiates transition to the next scene.
3. Audio fades out over 500ms.
4. Screen fades to black over 800ms.
5. Next scene (next stage or end scene) is pushed onto the stack.

---

## 9. Collision Rules

### 9.1 Collision Layer

All solid collision geometry is defined in the `Collision` object layer as rectangle objects. These rectangles are invisible at runtime — they are converted to a `list[pygame.Rect]` by `StageLoader` and used for physics resolution.

### 9.2 Collision Object Types

Each object in the `Collision` layer has a `type` attribute. `StageLoader` uses the `type` attribute to classify the object:

| `type` Attribute | Behavior |
|---|---|
| `Solid` | Full AABB resolution for player and Walker/Shooter |
| `Platform` | One-way platform — passable from below, solid from above |

Any object type other than `Platform` is treated as `Solid`. Objects with `type="Solid"`, or objects left with no type, all resolve as solid ground.

For hazards, death pits, camera locks, and similar non-collision zones, place those objects in the `Objects` layer (not the `Collision` layer) with the appropriate `type` value (`HazardZone`, `DeathPit`, `CameraLock`, etc.).

**Note:** Collision objects should align to the 16-pixel tile grid. Sub-tile-precision collision is permitted but must be justified (e.g., a sloped surface approximated with thin rectangles).

### 9.3 Collision Resolution Priority

When multiple collision rects overlap simultaneously, resolution priority is:

1. `Death_` — applied first (overrides everything)
2. `Solid_` — standard physics resolution
3. `OneWay_` — applied only if downward movement
4. `Hazard_` — damage applied, no movement resolution

### 9.4 Terrain vs. Collision Layer

The `Terrain` tile layer is **not** used for collision. Collision is derived exclusively from the `Collision` object layer. This separation is intentional: it allows visual terrain to be shaped freely without being constrained by collision geometry, and it allows collision zones (like invisible walls or death pits) to exist without visual tiles.

### 9.5 Tileset Collision Override

If a student wishes to define per-tile collision in Tiled (rather than placing individual collision objects), they must:

1. Configure tile collision shapes in the Tiled tileset editor.
2. Set the TMX map property `use_tile_collision` to `true`.
3. `StageLoader` will then extract collision rects from tile properties instead of the `Collision` object layer.

This approach is permitted but not recommended for beginners, as it is harder to debug.

---

## 10. Message Trigger Rules

### 10.1 Definition

A `Message` object is a rectangle trigger in the `Objects` layer. When the player enters the rectangle, the HUD's `MessageBox` displays the configured text.

### 10.2 Required Properties

| Property | Type | Description |
|---|---|---|
| `text` | string | The message to display |
| `duration` | float | Seconds before auto-dismiss (0 = manual dismiss) |
| `trigger_once` | bool | If `true`, the message only triggers the first time the player enters |

### 10.3 Message Text Rules

- Maximum 80 characters per line.
- Maximum 3 lines per message (the MessageBox renders up to 3 lines).
- Use `\n` within the `text` property string to create line breaks.
- No special formatting codes. Plain text only.

---

## 11. Examples

### 11.1 Minimal Valid TMX Structure (Pseudocode)

```xml
<map version="1.10" orientation="orthogonal" renderorder="right-down"
     width="80" height="14" tilewidth="16" tileheight="16">

  <properties>
    <property name="stage_id" value="stage1"/>
    <property name="stage_name" value="The Descent"/>
    <property name="time_limit" type="int" value="180"/>
    <property name="bgm_track" value="bgm_stage1_tense"/>
  </properties>

  <tileset firstgid="1" source="../assets/tilesets/tileset_dungeon.tsx"/>

  <layer name="BG_Far" .../>     <!-- sky tiles -->
  <layer name="BG_Mid" .../>     <!-- rock wall tiles -->
  <layer name="BG_Near" .../>    <!-- pillars -->
  <layer name="Terrain" .../>    <!-- solid floor and platforms -->
  <layer name="Terrain_Detail" .../>

  <objectgroup name="Objects">
    <object id="1" type="PlayerSpawn" name="PlayerSpawn_01" x="48" y="192"/>
    <object id="2" type="Walker" name="Walker_01" x="256" y="192">
      <properties>
        <property name="patrol_length" type="int" value="128"/>
        <property name="facing" value="left"/>
      </properties>
    </object>
    <object id="3" type="Checkpoint" name="Checkpoint_01" x="640" y="160" width="24" height="32">
      <properties>
        <property name="checkpoint_id" type="int" value="0"/>
      </properties>
    </object>
    <object id="4" type="Message" name="Message_01" x="144" y="160" width="48" height="32">
      <properties>
        <property name="text" value="Walk right to continue.\nUse Z to attack enemies."/>
        <property name="duration" type="float" value="5.0"/>
        <property name="trigger_once" type="bool" value="true"/>
      </properties>
    </object>
    <object id="5" type="NextTrigger" name="NextTrigger_01" x="1248" y="160" width="16" height="64"/>
  </objectgroup>

  <objectgroup name="Collision">
    <object id="10" name="Solid_Floor" x="0" y="192" width="1280" height="32"/>
    <object id="11" name="Solid_Platform01" x="256" y="160" width="80" height="16"/>
    <object id="12" name="Death_Pit01" x="512" y="224" width="64" height="16"/>
  </objectgroup>

  <layer name="FG_Overlay" .../>

</map>
```

### 11.2 Bézier-Path Flying Enemy Configuration

```xml
<!-- In Objects layer -->
<object id="20" type="Flying" name="Flying_01" x="400" y="96">
  <properties>
    <property name="flight_mode" value="bezier"/>
    <property name="flight_speed" type="float" value="55.0"/>
  </properties>
</object>

<object id="21" type="Waypoint" name="Waypoint_01" x="400" y="96">
  <properties>
    <property name="owner_id" value="Flying_01"/>
    <property name="waypoint_index" type="int" value="0"/>
  </properties>
</object>

<object id="22" type="Waypoint" name="Waypoint_02" x="560" y="60">
  <properties>
    <property name="owner_id" value="Flying_01"/>
    <property name="waypoint_index" type="int" value="1"/>
  </properties>
</object>

<object id="23" type="Waypoint" name="Waypoint_03" x="720" y="112">
  <properties>
    <property name="owner_id" value="Flying_01"/>
    <property name="waypoint_index" type="int" value="2"/>
  </properties>
</object>
```

### 11.3 Hazard Zone Configuration

```xml
<!-- In Objects layer -->
<object id="30" type="HazardZone" name="Hazard_Spikes01" x="512" y="176" width="48" height="16">
  <properties>
    <property name="damage" type="float" value="1.0"/>
    <property name="damage_type" value="spike"/>
  </properties>
</object>

<!-- In Collision layer — hazard geometry is separate from collision geometry -->
<!-- Hazard objects in Objects layer handle damage; no Solid_ rect needed below spikes -->
<!-- Death zone beneath spikes: -->
<object id="31" name="Death_Pit_Spikes" x="512" y="192" width="48" height="16"/>
```

### 11.4 Camera Lock Zone

```xml
<!-- Lock horizontal scroll inside a room, allow vertical scroll -->
<object id="40" type="CameraLock" name="CameraLock_Room01" x="800" y="0" width="320" height="224">
  <properties>
    <property name="lock_x" type="bool" value="true"/>
    <property name="lock_y" type="bool" value="false"/>
  </properties>
</object>
```

When the player is inside this zone, the camera's X offset is clamped to keep the room viewport fixed (useful for vertical-scroll room segments or boss arenas).
