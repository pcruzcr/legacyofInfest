---
document_id: "LOI-WORLD-016"
title: "Legacy of InFest — World Design Document"
aliases: ["World Design"]
tags: ["world", "design", "narrative"]
description: "4 zones, 14 stages, narrative-to-gameplay mapping"
source: "docs/16_WORLD_DESIGN.md"
date_processed: "2026-07-14"
---

# Legacy of InFest — World Design Document

**Document ID:** LOI-WORLD-016  
**Version:** 1.0.0  
**Status:** Official  
**Compatibility:** Requires LOI-CHARTER-001, LOI-ARCH-003, LOI-STAGE0-007  
**Audience:** Professor, Students, Artists, AI coding assistants

---

## 1. Overview

Legacy of InFest takes place across four distinct geographic zones, each rooted in a real or culturally inspired Costa Rican setting. The world is structured as a linear progression of zones and stages, culminating in a confrontation with the Grand Shaman Paburu at the sacred cemetery.

Every zone is subdivided into **four stages**. Stages 1–3 are traversal and combat stages. Stage 4 is always either a boss confrontation or the culminating challenge of that zone. The exception is the Final Zone, which has only two stages — both of which are boss encounters.

The world narrative centers on two protagonists — **John** and **Jin** — who carry ancient relics (the Gold Nugget and the Pearl) that awaken the spirits of the land. Each awakened spirit acts as a guardian or antagonist, drawn from Costa Rican indigenous mythology and natural imagery.

---

## 2. World Structure

```
ZONE 1 — Universidad Invenio (Jungle Campus)
    Stage 1-1  La Entrada          (jungle mountain approach)
    Stage 1-2  La Soda             (university cafeteria, disorder)
    Stage 1-3  Las Aulas           (university classrooms)
    Stage 1-4  La Residencia       [BOSS: El Venado Sagrado]

ZONE 2 — El Datacenter
    Stage 2-1  La Planicie         (flatlands between campus and datacenter)
    Stage 2-2  Entrada y Antenas   (datacenter exterior, antenna arrays)
    Stage 2-3  Las Oficinas        (interior offices)
    Stage 2-4  El Datacenter       [BOSS: El Rey Terciopelo]

ZONE 3 — Sede Heredia
    Stage 3-1  La Entrada de Piedra (stone path to lobby)
    Stage 3-2  El Hall              (enormous university hall)
    Stage 3-3  El Patio             (outdoor courtyard)
    Stage 3-4  El Bungaló           [BOSS: El Gavilán Camionero Mascarero]

ZONA FINAL — El Cementerio Sagrado
    Stage 4-1  La Entrada al Cementerio
    Stage 4-2  [FINAL BOSS: El Gran Shaman Paburu — 4 phases]
```

---

## 3. Zone 1 — Universidad Invenio

### 3.1 Zone Identity

| Property | Value |
|---|---|
| Setting | University campus surrounded by mountain jungle, Costa Rica |
| Atmosphere | Lush, overgrown, humid. Ancient forest meets modern academia. |
| Visual palette | Deep greens, earth browns, warm amber (late afternoon light) |
| BGM mood | Ambient jungle sounds layered over tense, rhythmic percussion |
| Enemy theme | Insects, small animals, disoriented students — things disturbed from their natural order |

The zone tells the story of a campus that has been slowly reclaimed by the jungle since the spirits began to stir. Vines creep through hallways. Animals wander the cafeteria. The forest has not forgotten that it was here first.

---

### 3.2 Stage 1-1 — La Entrada

**Type:** Traversal  
**Length:** ~100 meters (625 tiles at 16px each — approximately 3.5 screens of scrolling)  
**Description:** A long, solitary path winding through a mountainous jungle. The protagonist arrives on foot. Dense canopy above. The path narrows progressively. No buildings visible — only trees, roots, and rock.

**Academic Relevance:**
- Unit III: Enemy patrol paths along Bézier curves (winding through the jungle path geometry)
- Unit VI: Parallax layers (3–4 background depth planes: sky, mountain ridge, canopy, undergrowth)

**Layout Notes:**
- Gentle elevation changes using tiered platform geometry (stone steps embedded in earth)
- No pits in this stage — punishment is enemy contact only
- Checkpoint at the midpoint (after the narrowest section of path)
- One-way drops from higher paths to lower — cannot return

**Enemy Complement:**

| Enemy | Count | Behavior |
|---|---|---|
| `WalkerInsect` | 6 | Patrolling the path, reversing at edges |
| `FlyingBird` | 3 | Sine-wave swoops across the path |
| `ShooterFrog` | 2 | Stationary on rocks, launching projectiles |

**Terrain Features:**
- Stone and earth tile set (`tileset_jungle_stone.png`)
- Thick canopy foreground overlay (renders over player — `FG_Overlay` layer)
- Three background layers: sky gradient, mountain silhouette, tree line

**Stage Entry Banner:** `"1-1  LA ENTRADA"`  
**Time Limit:** 180 seconds  
**Completion Trigger:** Portal arch at the right edge leads into Stage 1-2

---

### 3.3 Stage 1-2 — La Soda

**Type:** Traversal + Combat  
**Description:** The university cafeteria — a wide, chaotic interior space. Tables overturned. Trays scattered. Food items have been disturbed and some have become hazardous. The space is mid-height (two floors visible), with a counter area, seating rows, and a back kitchen accessible through a half-door.

**Academic Relevance:**
- Unit V: Color-based lighting (warm kitchen light vs. cool dining area — HSL tint applied to each zone)
- Unit VII: `FilterTools.adjust_brightness()` used by the student to simulate the dim post-chaos interior
- Unit IV: Multiple vertical layers — floor tiles, counter geometry, ceiling beams

**Layout Notes:**
- Wider horizontal space than Stage 1-1 (~480px)
- Two-floor geometry: ground level (tables, counters) and elevated level (kitchen service shelf)
- One-way platform separates ground from elevated section
- A tray projectile hazard zone at the counter (HazardZone, damage=0.25)
- Checkpoint after surviving the main dining hall

**Enemy Complement:**

| Enemy | Count | Behavior | Notes |
|---|---|---|---|
| `WalkerRaton` | 4 | Ground patrol, faster than jungle walker | Rats displaced from kitchen |
| `FlyingCucaracha` | 5 | Erratic sine-wave flight | Fill the mid-air space |
| `ShooterCocinero` | 1 | Stationary behind counter | Throws food items as projectiles |

**Terrain Features:**
- Interior tile set (`tileset_cafeteria.png`)
- Checkered floor tiles (red and white — SNES palette compliant)
- Hanging ceiling lights (decorative, `Terrain_Detail` layer)
- Kitchen counter as one-way platform top edge

**Stage Entry Banner:** `"1-2  LA SODA"`  
**Time Limit:** 150 seconds

---

### 3.4 Stage 1-3 — Las Aulas

**Type:** Traversal + Combat  
**Description:** The university classrooms. A corridor connecting multiple rooms, each visible through doorways. The rooms have been overrun: desks are stacked, the blackboard is cracked, forest roots have broken through the floor. The corridor runs left to right; side rooms are accessible through open doorways and contain items and hazards.

**Academic Relevance:**
- Unit VIII: Student applies `VisionTools.threshold_binary()` to distinguish "chalk dust" (bright) zones from "root shadow" (dark) zones — drives a light-on/light-off mechanic
- Unit VI: Easing-function door animation (doors swing open with `ease_out_bounce`)

**Layout Notes:**
- Three classroom alcoves (accessible, non-scrolling rooms branching off the main corridor)
- Main corridor is ~560px wide
- Roots in floor (visual only, `Terrain_Detail`) with collision spike zones embedded
- Blackboard in classroom 2 has a tutorial message written on it (Easter egg — reads course content)

**Enemy Complement:**

| Enemy | Count | Placement |
|---|---|---|
| `WalkerEstudiante` | 5 | Patrol corridor and rooms |
| `FlyingNotebook` | 3 | Flying papers with sine-wave movement |
| `ShooterTiza` | 2 | Stationary at blackboard ends, shoot chalk projectiles |

**Special Object — Checkpoint Blackboard:**
A checkpoint disguised as a blackboard. When activated, a chalk animation draws a checkmark on the board. This is the only checkpoint in Stage 1-3.

**Stage Entry Banner:** `"1-3  LAS AULAS"`  
**Time Limit:** 150 seconds

---

### 3.5 Stage 1-4 — La Residencia

**Type:** Boss Stage  
**Description:** A forested residential clearing. Ancient stone walls, moss-covered. A central open area surrounded by old-growth trees. At the far end: the dwelling of the Sacred Deer — a stone-framed arch draped in vines. This is where the first boss waits.

**Academic Relevance:**
- Unit III: Boss movement during Phase 2 follows a Bézier arc across the arena
- Unit VII: Boss Phase 1 uses `FilterTools.sobel_edge()` as a visual "aura" overlay

**Layout:**
- No horizontal scrolling — fixed arena (320×224)
- Solid stone floor with 3 elevated platforms (jump pads for dodging)
- Boss entrance from the right: the deer emerges from behind the vine arch

**Boss:** El Venado Sagrado — see `17_BOSS_SPEC.md`

**Stage Entry Banner:** `"1-4  LA RESIDENCIA"`  
**Time Limit:** None (boss stages have no timer)

---

## 4. Zone 2 — El Datacenter

### 4.1 Zone Identity

| Property | Value |
|---|---|
| Setting | Industrial datacenter complex adjacent to the university campus |
| Atmosphere | Oppressive heat, dim server-blue glow, mechanical hum |
| Visual palette | Steel grays, deep blues, hot orange (heat vents), red warning lights |
| BGM mood | Electronic drone, industrial rhythm, metallic percussion |
| Enemy theme | Serpents — all enemies in this zone are serpent-based or serpent-adjacent |
| Narrative context | The datacenter's warmth makes it the perfect refuge for the fer-de-lance (terciopelo) serpents that answer to El Rey Terciopelo |

The datacenter was already a warm, enclosed space — the servers generated constant heat. When the spirits stirred, the terciopelo serpents migrated here and merged under the influence of El Rey, forming a collective consciousness that now controls the space.

---

### 4.2 Stage 2-1 — La Planicie

**Type:** Traversal  
**Description:** An open flatlands transition zone between the university campus and the datacenter. Agricultural land — some pasture, some cleared earth, a barbed-wire fence line. The path is exposed and wide.

**Academic Relevance:**
- Unit II: Enemy detection range demonstrated with distance-based `vec2_distance` (wide open space makes range calculations visible)
- Unit V: Alpha-blended heat shimmer effect on the ground (animated surface tint)

**Layout Notes:**
- Flat terrain, ~480px wide
- Low obstacles: barbed wire (solid at knee height — crouching required to pass)
- One fence gap that can be jumped or crouched through
- Heat shimmer visual: a subtle brightness oscillation applied to the ground tiles via `FilterTools.adjust_brightness()` with a sine-wave factor

**Enemy Complement:**

| Enemy | Count | Behavior |
|---|---|---|
| `WalkerSerpientePequena` | 6 | Ground patrol, fast |
| `ShooterSerpienteArbol` | 3 | Stationary in fence posts, spit venom |
| `FlyingBoa` | 2 | Aerial — sine wave |

**Stage Entry Banner:** `"2-1  LA PLANICIE"`  
**Time Limit:** 160 seconds

---

### 4.3 Stage 2-2 — Entrada y Antenas

**Type:** Traversal + Combat  
**Description:** The exterior approach to the datacenter. A parking lot, a security booth, and a field of communication antennas on the rooftop. The protagonist must pass through the ground level and climb to the rooftop antenna array.

**Academic Relevance:**
- Unit III: Enemy patrol along B-Spline paths wrapping around antenna poles
- Unit IV: Vertical scrolling section (bottom to top) — camera lock changes axis

**Layout Notes:**
- Stage is wider and taller than typical (320×320 internal — uses camera lock zone to restrict horizontal scroll during vertical section)
- Ground section (~200px wide): parking lot approach, security kiosk
- Vertical climb section: ladder-style platform chain up the side of the building
- Rooftop section: antenna array — narrow platforms between poles

**Vertical Climb Camera Lock:**
A `CameraLock` object with `lock_x=true, lock_y=false` activates when the player reaches the ladder. The camera then tracks vertical movement only.

**Enemy Complement:**

| Enemy | Count | Placement |
|---|---|---|
| `WalkerGuardia` | 2 | Ground level, security kiosk |
| `FlyingAntena` | 4 | Aerial patrol around antennas |
| `ShooterSerpiente` | 3 | Stationary on antenna platforms |

**Stage Entry Banner:** `"2-2  ENTRADA Y ANTENAS"`  
**Time Limit:** 170 seconds

---

### 4.4 Stage 2-3 — Las Oficinas

**Type:** Traversal + Combat  
**Description:** The interior of the datacenter — the office floor. Cubicles, servers visible through glass partitions, cable management overhead. The floor is covered in serpents. The air is heavy and warm. Server indicator lights blink red.

**Academic Relevance:**
- Unit VII: `FilterTools.canny_edge()` applied to the background produces a wireframe-style visual effect (the protagonist "sees" the serpent infestation as an edge map)
- Unit VIII: `VisionTools.connected_components()` used to count active server units (bright LED indicators) — drives a score or density indicator

**Layout Notes:**
- Interior tileset (`tileset_datacenter.png`): metal floor, glass partitions, server racks
- Glass partitions: visual-only walls (no collision) — player passes through them
- Cable overhead: decorative `FG_Overlay`
- Floor hazard: `HazardZone` strips where serpents cluster (damage=0.25)
- Two checkpoint locations: midway through cubicle field, at the server room entrance door

**Enemy Complement:**

| Enemy | Count | Behavior |
|---|---|---|
| `WalkerTerciopelo` | 7 | Aggressive patrol between cubicles |
| `ShooterVenomoLargo` | 3 | Long-range venom spit from behind partitions |
| `FlyingTerciovolador` | 2 | Small flying variants above partition height |

**Stage Entry Banner:** `"2-3  LAS OFICINAS"`  
**Time Limit:** 150 seconds

---

### 4.5 Stage 2-4 — El Datacenter

**Type:** Boss Stage  
**Description:** The server room. A cathedral of machines. Rows of server racks reaching to the ceiling. Blinking lights everywhere. Hot air rising from floor vents. The floor is a writhing mass of serpents. In the center, suspended between two server pillars: El Rey Terciopelo — the amalgamated spirit.

**Academic Relevance:**
- Unit IX: Boss Phase 2 classification — the collective shifts between three attack modes (aggressive, defensive, dispersed). Student recognizes the mode using `PatternRecognitionTools.predict()` on the visual state of the boss surface and responds accordingly.

**Layout:**
- Fixed arena (320×224), no scrolling
- Server racks as side walls (visual and collision)
- Three floor vents as HazardZone (damage=0.25, periodic — active for 2 seconds every 5 seconds)
- Central arena floor: flat with one low platform for jumping over serpent sweeps

**Boss:** El Rey Terciopelo — see `17_BOSS_SPEC.md`

**Stage Entry Banner:** `"2-4  EL DATACENTER"`

---

## 5. Zone 3 — Sede Heredia

### 5.1 Zone Identity

| Property | Value |
|---|---|
| Setting | Universidad Invenio's Heredia campus building |
| Atmosphere | Academic grandeur — large open spaces, stone and glass architecture |
| Visual palette | Warm stone beige, cool interior shadow, gold afternoon light through skylights |
| BGM mood | Tense orchestral — something hunting, patient, aerial |
| Enemy theme | Birds and aerial creatures — the domain of El Gavilán |

The Heredia campus has become the hunting ground of El Gavilán Camionero Mascarero. Its high ceilings and open courtyards make it perfect for aerial predators. The Tilawa mask has given the hawk both intelligence and supernatural reach.

---

### 5.2 Stage 3-1 — La Entrada de Piedra

**Type:** Traversal  
**Description:** A long stone-paved path leading to the main entrance of the Heredia building. Stone walls on both sides. Archways overhead. The path is wide and exposed — no cover from aerial attacks.

**Academic Relevance:**
- Unit VI: Stone paving animation (each stone tile activates sequentially using timed lerp — a "awakening" effect when the player walks over them)
- Unit V: HSL-based stone color shift between sun-lit (warm) and shadow (cool) zones as clouds pass

**Layout Notes:**
- ~560px long, flat path
- Archways as visual only (FG_Overlay)
- Intermittent aerial dive-bomb attacks from pre-placed FlyingHawk enemies
- Two raised stone planters as cover (one-way platform tops)

**Enemy Complement:**

| Enemy | Count | Behavior |
|---|---|---|
| `WalkerGarza` | 4 | Patrol the stone path on foot |
| `FlyingHalcon` | 4 | Fast sine-wave, dive toward player |
| `ShooterQuetzal` | 2 | Stationary on archway tops, fire feather projectiles |

**Stage Entry Banner:** `"3-1  LA ENTRADA DE PIEDRA"`  
**Time Limit:** 160 seconds

---

### 5.3 Stage 3-2 — El Hall

**Type:** Traversal + Combat  
**Description:** An enormous hall — high ceilings, wide floor, balconies on both sides. Natural light from skylights above. The space is vast and open, making the player feel exposed. Birds circle overhead. The hall connects the entrance to the interior corridors.

**Academic Relevance:**
- Unit VIII: `VisionTools.watershed_segment()` used to identify distinct "zones" of the hall (entrance zone, center zone, balcony zone) — student uses zone classification to trigger different enemy spawns per zone
- Unit IV: The most complex layer stack in the game: floor, balcony platforms, ceiling beams, skylight overlay — 5 visible layers

**Layout Notes:**
- ~640px wide — the widest stage in the game
- Floor level: wide, few obstacles
- Balcony level: accessible via two staircases (solid platforms)
- Ceiling: indestructible — projectiles bounce off (if shooter is positioned below)
- Skylight shafts: semi-transparent bright columns at fixed X positions (visual only)

**Enemy Complement:**

| Enemy | Count | Placement |
|---|---|---|
| `WalkerPalom` | 5 | Floor level — slow, large hitbox |
| `FlyingHalcon` | 6 | Aerial patrol — dive-bombing from ceiling height |
| `ShooterBuitre` | 2 | Stationary on balconies |

**Stage Entry Banner:** `"3-2  EL HALL"`  
**Time Limit:** 170 seconds

---

### 5.4 Stage 3-3 — El Patio

**Type:** Traversal + Combat  
**Description:** An outdoor courtyard inside the building. Open sky above. Vegetation in planters. A fountain in the center. The ground is cobblestone. The patio is surrounded by building walls on three sides — a partially enclosed space that feels like an ambush zone.

**Academic Relevance:**
- Unit VII: `FilterTools.gaussian_blur()` on the sky layer simulates an overcast effect — sky brightness drives enemy aggression (bright sky = more flying enemies active)
- Unit III: The fountain arc water animation uses a Catmull-Rom spline for the water particle trajectory

**Layout Notes:**
- ~400px wide
- Central fountain: visual + solid collision top (one-way platform)
- Planter boxes: low solid obstacles (32px tall) — good for crouching behind
- Sky visible in top half — parallax cloud layer at BG_Far

**Enemy Complement:**

| Enemy | Count | Behavior |
|---|---|---|
| `WalkerPalom` | 3 | Ground patrol |
| `FlyingHalcon` | 5 | Very aggressive — detect at full patio width |
| `ShooterQuetzal` | 3 | From building window ledges (upper edges of screen) |

**Fountain Special:** Touching the fountain restores 0.25 hearts (light heal). One use per activation. Reactivates at each checkpoint respawn.

**Stage Entry Banner:** `"3-3  EL PATIO"`  
**Time Limit:** 145 seconds

---

### 5.5 Stage 3-4 — El Bungaló

**Type:** Boss Stage  
**Description:** The top floor of the building — a high open bungaló space with a panoramic view and a skylight roof. Stone and wood architecture. The hawk roosts here. This is its lair.

**Academic Relevance:**
- Unit IX: Boss phase detection — `PatternRecognitionTools.predict()` classifies the hawk's current flight pattern (dive, circle, roost) from the visual distribution of its position over recent frames. The player uses the predicted pattern to anticipate the next attack.

**Layout:**
- Fixed arena (320×224)
- Wooden beams as platforms at three heights (low: Y=192, mid: Y=152, high: Y=112)
- Skylight opening at top center: boss enters and exits through it in certain phases
- No HazardZones — pure platform and aerial combat

**Boss:** El Gavilán Camionero Mascarero — see `17_BOSS_SPEC.md`

**Stage Entry Banner:** `"3-4  EL BUNGALÓ"`

---

## 6. Zone Final — El Cementerio Sagrado

### 6.1 Zone Identity

| Property | Value |
|---|---|
| Setting | A sacred indigenous cemetery in the Costa Rican highlands |
| Atmosphere | Still, ancient, otherworldly. The air feels thick. |
| Visual palette | Deep purple-black sky, pale stone, spectral green light, gold highlights |
| BGM mood | Ritual percussion, deep drone, silence punctuated by drums |
| Narrative function | The convergence point. All spirits that John and Jin have defeated have led to this place. Paburu waits. |

This zone has only two stages. There is no traversal — the cemetery itself IS the confrontation. Stage 4-1 is the approach through the cemetery grounds. Stage 4-2 is the final boss encounter.

---

### 6.2 Stage 4-1 — La Entrada al Cementerio

**Type:** Traversal + Pre-Boss Atmospheric Stage  
**Description:** A winding path through the sacred cemetery. Ancient stone markers on both sides. Ceremonial fire bowls that cast moving light. The protagonist walks in near-silence. Spirits of defeated bosses appear as visual echoes in the background — translucent, non-hostile, watching.

**Academic Relevance:**
- Unit V: `ColorTools.apply_tint()` — the green spectral glow applied to every background surface
- Unit VII: `FilterTools.adjust_brightness()` tied to proximity to fire bowls — closer to fire = brighter
- Unit VIII: `VisionTools.threshold_binary()` used to create a "spectral vision" toggle — pressing a button reveals a threshold-filtered version of the screen showing hidden grave markings

**Layout Notes:**
- ~400px wide — medium length
- No enemies (intentional — the atmosphere IS the challenge)
- HazardZone: cracked earth fissures that pulse with energy (damage=0.25, periodic)
- Fire bowl platforms: raised 32px stone pedestals with fire sprite above
- Spectral vision toggle: activated by `LONG_ATTACK` button — replaces screen with threshold-filtered version for 3 seconds

**Spirits in Background (visual only — BG_Mid layer):**
- Silhouette of El Venado Sagrado (deer antlers)
- Coiled mass silhouette of El Rey Terciopelo
- Wing silhouette of El Gavilán

These are static sprites at BG_Mid parallax depth — visual storytelling, not entities.

**Stage Entry Banner:** `"4-1  LA ENTRADA AL CEMENTERIO"`  
**Time Limit:** None (atmospheric pacing — no time pressure)

---

### 6.3 Stage 4-2 — El Gran Shaman Paburu

**Type:** Final Boss Stage (4 phases)  
**Description:** The heart of the cemetery. A circular stone clearing with a massive stone head at the center. Ritual carvings on the floor. Spectral green flames at the perimeter. The stone head opens its eyes.

**Layout:**
- Fixed arena (320×224)
- Stone floor with carved ritual circles (visual)
- Four perimeter flame pillars (visual + HazardZone at their base: damage=0.25)
- No platforms — flat arena for maximum phase flexibility
- Boss occupies the upper-center region in most phases

**Boss:** El Gran Shaman Paburu — see `17_BOSS_SPEC.md`  
**Stage Entry Banner:** `"4-2  EL GRAN SHAMAN PABURU"`

---

## 7. Zone Summary Table

| Zone | Stages | Boss | Setting | Primary Academic Units |
|---|---|---|---|---|
| 1 — Universidad Invenio | 1-1 through 1-4 | El Venado Sagrado | Mountain jungle campus | II, III, V, VII |
| 2 — El Datacenter | 2-1 through 2-4 | El Rey Terciopelo | Industrial server complex | III, V, VII, IX |
| 3 — Sede Heredia | 3-1 through 3-4 | El Gavilán Camionero Mascarero | Urban university building | VI, VII, VIII, IX |
| Final — Cementerio | 4-1, 4-2 | El Gran Shaman Paburu | Sacred highland cemetery | V, VII, VIII |

---

## 8. Student Stage Assignment

Each student stage (Stage 1, 2, 3 in the framework's terminology) maps to a zone within the world:

| Framework Stage | World Zone | Rationale |
|---|---|---|
| Student Stage 1 | Zone 1 (one of 1-1 through 1-3) | Introduces Units II, III, IV, V |
| Student Stage 2 | Zone 2 (one of 2-1 through 2-3) | Introduces Units VI, VII |
| Student Stage 3 | Zone 3 (one of 3-1 through 3-3) | Introduces Units VIII, IX |

Boss stages (X-4) and the Final Zone are professor-owned. Students build the traversal stages within each zone.

---

## 9. Narrative Summary

| Act | Event |
|---|---|
| Prologue | John and Jin arrive at the university campus. They carry the Gold Nugget (John) and the Pearl (Jin). |
| Zone 1 | The forest awakens around them. El Venado Sagrado — a spirit deer, ancient bones wrapped in the jungle — rises to reclaim the relics. Defeated, its spirit joins them as a guide. |
| Zone 2 | The heat of the datacenter draws them in. El Rey Terciopelo — thousands of serpents animating a decayed body — commands the space. Defeated, its venom-knowledge joins them. |
| Zone 3 | A masked hawk hunts them through the university's Heredia campus. El Gavilán Camionero Mascarero — empowered by a Tilawa mask — guards the path to Paburu. Defeated, its aerial sight joins them. |
| Zone Final | The cemetery. Paburu does not hide. He waits. Four phases. Four forms. The Gold Nugget and the Pearl are the key — and the danger. |


---
## 🔗 Documentos Relacionados

- [[18_ENEMY_ROSTER.md|Enemy Roster]]
- [[19_NARRATIVE_AND_LORE.md|Narrative and Lore]]
- [[07_STAGE0_DESIGN.md|Stage 0 Design]]
