---
document_id: "LOI-ENEMIES-018"
title: "Legacy of InFest — Enemy Roster"
aliases: ["Enemy Roster"]
tags: ["enemy", "roster", "entities"]
description: "Every standard enemy, by zone"
source: "docs/18_ENEMY_ROSTER.md"
date_processed: "2026-07-14"
---

# Legacy of InFest — Enemy Roster

**Document ID:** LOI-ROSTER-018  
**Version:** 1.0.0  
**Status:** Official  
**Compatibility:** Requires LOI-ENEMY-005, LOI-WORLD-016  
**Audience:** Professor, Students, Artists, AI coding assistants

---

## 1. Overview

This document defines every standard enemy (non-boss) that appears in Legacy of InFest. Each enemy is a subclass of one of the three base templates: `EnemyWalker`, `EnemyFlying`, or `EnemyShooter` (see `05_ENEMY_SPEC.md`).

Enemies are organized by zone. Each zone has its own thematic enemy set that reflects the environment and the spirit that governs it. Students building traversal stages within a zone use the enemies defined for that zone — they do not create new base enemy types, but they may subclass and configure zone enemies with custom TMX properties.

---

## 2. Zone 1 — Universidad Invenio Enemies

Zone 1 enemies reflect the jungle campus: insects, small animals, and creatures displaced from the forest by the awakening of El Venado Sagrado.

### 2.1 `WalkerInsect` — Ground Insect

| Property | Value |
|---|---|
| Base Class | `EnemyWalker` |
| Appears In | Stage 1-1, 1-2 |
| Health | 1.0 heart |
| Contact Damage | 0.25 hearts |
| Patrol Speed | 35 px/s |
| Alert Speed | 55 px/s |
| Detection Range X | 120 px |
| Patrol Length (default) | 64 px |

**Visual:** A large jungle beetle — dark brown carapace, six legs animated. Sprite: `enemy_insecto_walk.png` (6 frames, 10 FPS). Size: 16×12 px.

**Behavior Note:** Slow, predictable. The first enemy the player encounters. Designed to teach the basic attack response without significant danger.

**Academic Note (Unit II):** Ledge detection uses `vec2_distance` probe check. Documented in source.

---

### 2.2 `FlyingBird` — Jungle Bird

| Property | Value |
|---|---|
| Base Class | `EnemyFlying` |
| Appears In | Stage 1-1, 1-3 |
| Health | 1.0 heart |
| Contact Damage | 0.25 hearts |
| Flight Mode | Sine |
| Sine Amplitude | 24 px |
| Sine Frequency | 1.4 Hz |
| Flight Speed | 55 px/s |
| Detection Range X | 160 px |

**Visual:** A small tropical bird (motmot-inspired coloring — teal and orange). Sprite: `enemy_pajaro_fly.png` (4 frames, 12 FPS). Size: 14×10 px.

**Behavior Note:** Swoops down across the path. The sine wave makes it difficult to jump over. Players learn to time ducks under it.

---

### 2.3 `ShooterFrog` — Poison Dart Frog

| Property | Value |
|---|---|
| Base Class | `EnemyShooter` |
| Appears In | Stage 1-1, 1-3 |
| Health | 2.0 hearts |
| Contact Damage | 0.25 hearts |
| Projectile Damage | 0.25 hearts |
| Fire Rate | 0.4 shots/s |
| Projectile Speed | 90 px/s |
| Detection Range X | 180 px |
| Patrol Length | 0 (stationary) |

**Visual:** A red-and-blue poison dart frog (Oophaga pumilio — the strawberry poison-dart frog, native to Costa Rica). Sprite: `enemy_rana_idle.png` (4 frames, 6 FPS). Size: 12×12 px. **Projectile:** small toxic droplet, `enemy_rana_proyectil.png` (2 frames, 8 FPS, 4×4 px).

**Behavior Note:** Stationary — sits on rocks and elevated surfaces. Long-range threat that forces the player to close the gap.

---

### 2.4 `WalkerRaton` — Cafeteria Rat

| Property | Value |
|---|---|
| Base Class | `EnemyWalker` |
| Appears In | Stage 1-2 |
| Health | 1.0 heart |
| Contact Damage | 0.25 hearts |
| Patrol Speed | 55 px/s |
| Alert Speed | 90 px/s |
| Detection Range X | 96 px |
| Patrol Length | 48 px |

**Visual:** A large rat — gray, red eyes. Running animation. Sprite: `enemy_raton_walk.png` (6 frames, 14 FPS). Size: 14×10 px.

**Behavior Note:** Faster than WalkerInsect. Alert state is notably quick — players who are not attentive get caught off guard. Teaches the importance of attention to detection ranges.

---

### 2.5 `FlyingCucaracha` — Flying Cockroach

| Property | Value |
|---|---|
| Base Class | `EnemyFlying` |
| Appears In | Stage 1-2 |
| Health | 1.0 heart |
| Contact Damage | 0.25 hearts |
| Flight Mode | Sine |
| Sine Amplitude | 16 px |
| Sine Frequency | 2.0 Hz |
| Flight Speed | 45 px/s |

**Visual:** A cockroach with wings spread — brown, glossy carapace. Sprite: `enemy_cucaracha_fly.png` (4 frames, 16 FPS). Size: 12×8 px. High-frequency wing beat animation.

**Behavior Note:** High sine frequency makes movement erratic at close range. Fills the vertical mid-space of the cafeteria.

---

### 2.6 `ShooterCocinero` — Rogue Cook

| Property | Value |
|---|---|
| Base Class | `EnemyShooter` |
| Appears In | Stage 1-2 (unique — 1 per stage) |
| Health | 3.0 hearts |
| Contact Damage | 0.25 hearts |
| Projectile Damage | 0.50 hearts |
| Fire Rate | 0.5 shots/s |
| Projectile Speed | 110 px/s |

**Visual:** A cafeteria cook in stained uniform, throwing food items. Sprite: `enemy_cocinero_idle.png` and `enemy_cocinero_throw.png`. Size: 16×24 px. **Projectile:** food tray, `enemy_cocinero_tray.png` (2 frames, 8 FPS, 12×6 px, tumbling rotation).

**Behavior Note:** Stationed behind the cafeteria counter (uses counter as cover — hurtbox is partially obscured by counter geometry). Player must jump over the counter to close range.

---

### 2.7 `WalkerEstudiante` — Disoriented Student

| Property | Value |
|---|---|
| Base Class | `EnemyWalker` |
| Appears In | Stage 1-3 |
| Health | 1.5 hearts |
| Contact Damage | 0.50 hearts |
| Patrol Speed | 40 px/s |
| Alert Speed | 70 px/s |
| Detection Range X | 144 px |
| Patrol Length | 80 px |

**Visual:** A university student — backpack, smartphone in hand (acting as a weapon). Sprite: `enemy_estudiante_walk.png` (8 frames, 10 FPS). Size: 16×24 px. The smartphone projectile (if using ShooterEstudiante variant) is a small screen glow.

**Behavior Note:** Slightly more health than Zone 1 walkers — represents the escalation heading into the classroom zone. Alert movement is believably human-speed.

---

### 2.8 `FlyingNotebook` — Animated Notebook Pages

| Property | Value |
|---|---|
| Base Class | `EnemyFlying` |
| Appears In | Stage 1-3 |
| Health | 0.5 hearts |
| Contact Damage | 0.25 hearts |
| Flight Mode | Sine |
| Sine Amplitude | 32 px |
| Sine Frequency | 1.0 Hz |
| Flight Speed | 50 px/s |

**Visual:** Animated loose notebook pages flying through the air — spinning slowly. Sprite: `enemy_hoja_fly.png` (4 frames, 8 FPS). Size: 10×14 px.

**Behavior Note:** Very low health — one short attack kills it. But they come in pairs or threes. Teaches the distinction between individual and group threat.

---

### 2.9 `ShooterTiza` — Chalk Thrower

| Property | Value |
|---|---|
| Base Class | `EnemyShooter` |
| Appears In | Stage 1-3 |
| Health | 2.5 hearts |
| Projectile Damage | 0.25 hearts |
| Fire Rate | 1.0 shots/s |
| Projectile Speed | 130 px/s |
| Patrol Length | 0 (stationary) |

**Visual:** Animated blackboard eraser character (anthropomorphic — the classroom's spirit). Sprite: `enemy_tiza_idle.png`. Size: 14×14 px. **Projectile:** chalk stick, `enemy_tiza_proyectil.png` (1 frame, 4×4 px, fast tumble).

**Behavior Note:** High fire rate. Stationary at blackboard ends. Long range. Creates a fire-zone that the player must breach through timed dashes between chalk shots.

---

## 3. Zone 2 — El Datacenter Enemies

Zone 2 enemies are serpent-based. All walkers are serpents. All flyers are airborne serpent variants. The shooter represents the long-range spit capability of the terciopelo.

### 3.1 `WalkerSerpientePequena` — Small Fer-de-Lance

| Property | Value |
|---|---|
| Base Class | `EnemyWalker` |
| Appears In | Stage 2-1, 2-2, 2-3, 2-4 (as boss summon) |
| Health | 1.0 heart |
| Contact Damage | 0.50 hearts |
| Patrol Speed | 55 px/s |
| Alert Speed | 100 px/s |
| Detection Range X | 96 px |

**Visual:** A small terciopelo — brown and tan pattern. Slithering animation. Sprite: `enemy_terciopelo_small_walk.png` (6 frames, 12 FPS). Size: 20×8 px (wide, low).

**Behavior Note:** Low hitbox — crouching attacks are required. High contact damage for their health level — they are dangerous despite their size.

---

### 3.2 `FlyingBoa` — Aerial Boa

| Property | Value |
|---|---|
| Base Class | `EnemyFlying` |
| Appears In | Stage 2-1, 2-2 |
| Health | 2.0 hearts |
| Contact Damage | 0.50 hearts |
| Flight Mode | Sine |
| Sine Amplitude | 30 px |
| Sine Frequency | 0.8 Hz |
| Flight Speed | 45 px/s |

**Visual:** A large boa constrictor — airborne, undulating through the air. Sprite: `enemy_boa_fly.png` (6 frames, 10 FPS). Size: 32×12 px. Large hitbox — harder to dodge.

---

### 3.3 `ShooterSerpienteArbol` — Tree Viper Shooter

| Property | Value |
|---|---|
| Base Class | `EnemyShooter` |
| Appears In | Stage 2-1, 2-2, 2-3 |
| Health | 2.0 hearts |
| Projectile Damage | 0.50 hearts (venom) |
| Fire Rate | 0.6 shots/s |
| Projectile Speed | 100 px/s |
| Patrol Length | 0 (stationary) |

**Visual:** A green tree viper — coiled around an elevated object (fence post, antenna bracket, office partition top). Sprite: `enemy_serpiente_arbol_idle.png`. Size: 14×16 px. **Projectile:** venom glob, green, `enemy_venom_proyectil.png` (2 frames, 8 FPS, 5×5 px).

---

### 3.4 `WalkerTerciopelo` — Large Fer-de-Lance

| Property | Value |
|---|---|
| Base Class | `EnemyWalker` |
| Appears In | Stage 2-3 |
| Health | 2.5 hearts |
| Contact Damage | 0.75 hearts |
| Patrol Speed | 40 px/s |
| Alert Speed | 80 px/s |
| Detection Range X | 160 px |

**Visual:** A large, full-grown terciopelo. Thicker body, slower but heavier. Sprite: `enemy_terciopelo_large_walk.png` (6 frames, 8 FPS). Size: 28×12 px.

---

### 3.5 `ShooterVenomoLargo` — Long-Range Venom Shooter

| Property | Value |
|---|---|
| Base Class | `EnemyShooter` |
| Appears In | Stage 2-3 |
| Health | 3.0 hearts |
| Projectile Damage | 0.50 hearts |
| Fire Rate | 0.4 shots/s |
| Projectile Speed | 150 px/s |
| Detection Range X | 220 px |

**Visual:** A spitting cobra variant — elevated, swaying. Sprite: `enemy_cobra_idle.png`. Size: 16×20 px. **Projectile:** long-range venom stream, `enemy_venom_stream.png` (4 frames, 12 FPS, 8×4 px).

---

### 3.6 `FlyingTerciovolador` — Winged Serpent

| Property | Value |
|---|---|
| Base Class | `EnemyFlying` |
| Appears In | Stage 2-3 |
| Health | 1.5 hearts |
| Contact Damage | 0.50 hearts |
| Flight Mode | Bezier (short 3-point paths) |
| Flight Speed | 70 px/s |
| Detection Range X | 180 px |

**Visual:** A small winged serpent — mythological design, two small wings. Sprite: `enemy_terciovolador_fly.png` (6 frames, 12 FPS). Size: 18×14 px.

---

### 3.7 `WalkerGuardia` — Datacenter Security Guard

| Property | Value |
|---|---|
| Base Class | `EnemyWalker` |
| Appears In | Stage 2-2 (parking lot) |
| Health | 3.0 hearts |
| Contact Damage | 0.50 hearts |
| Patrol Speed | 45 px/s |
| Alert Speed | 65 px/s |

**Visual:** A security guard — uniform, flashlight. Under serpent influence (eyes glowing faintly green). Sprite: `enemy_guardia_walk.png` (8 frames, 10 FPS). Size: 16×24 px.

---

## 4. Zone 3 — Sede Heredia Enemies

Zone 3 enemies are bird-based — the domain of El Gavilán. All walkers are ground-dwelling birds. Flyers are raptors. Shooters are perching birds that fire feather or beak projectiles.

### 4.1 `WalkerGarza` — Heron

| Property | Value |
|---|---|
| Base Class | `EnemyWalker` |
| Appears In | Stage 3-1 |
| Health | 2.0 hearts |
| Contact Damage | 0.50 hearts |
| Patrol Speed | 35 px/s |
| Alert Speed | 60 px/s |

**Visual:** A large heron (Ardea herodias — Great Blue Heron variant). Slow, deliberate steps. Sprite: `enemy_garza_walk.png` (6 frames, 7 FPS). Size: 18×28 px (tall).

**Behavior Note:** Tall hitbox — long-attack low sweep is effective. Short attack may miss if player is not crouching.

---

### 4.2 `FlyingHalcon` — Roadside Hawk (standard)

| Property | Value |
|---|---|
| Base Class | `EnemyFlying` |
| Appears In | Stage 3-1, 3-2, 3-3 |
| Health | 2.0 hearts |
| Contact Damage | 0.75 hearts |
| Flight Mode | Sine + alert dive |
| Sine Amplitude | 20 px |
| Sine Frequency | 0.6 Hz |
| Alert Behavior | Dives straight down to player X, then reascends |
| Flight Speed | 65 px/s / 200 px/s (dive) |

**Visual:** Roadside hawk in flight — brown and white underside. Sprite: `enemy_halcon_fly.png` (6 frames, 12 FPS) and `enemy_halcon_dive.png` (4 frames, 18 FPS). Size: 20×14 px.

**Custom Behavior — Alert Dive:**  
When the player enters detection range, the hawk transitions to a dive: moves horizontally to player's X position (50px/s), then dives at 200px/s. After reaching Y=200 or hitting a platform, reascends to patrol altitude. This overrides the standard alert behavior from `EnemyFlying`.

---

### 4.3 `ShooterQuetzal` — Quetzal Sniper

| Property | Value |
|---|---|
| Base Class | `EnemyShooter` |
| Appears In | Stage 3-1, 3-2, 3-3 |
| Health | 2.5 hearts |
| Projectile Damage | 0.25 hearts (feather) |
| Fire Rate | 0.8 shots/s |
| Projectile Speed | 120 px/s |
| Patrol Length | 0 (stationary) |

**Visual:** A resplendent quetzal (Pharomachrus mocinno — sacred bird of Costa Rica). Perched on ledges and archway tops. Sprite: `enemy_quetzal_idle.png` (4 frames, 6 FPS). Size: 12×20 px (upright). **Projectile:** long tail feather, `enemy_quetzal_feather.png` (2 frames, spin, 3×10 px).

**Cultural Note:** The quetzal is one of the most revered birds in Central American culture. Its depiction here is respectful — it is under the maleku mask's influence, not naturally aggressive.

---

### 4.4 `WalkerPalom` — Domestic Pigeon (corrupted)

| Property | Value |
|---|---|
| Base Class | `EnemyWalker` |
| Appears In | Stage 3-2, 3-3 |
| Health | 2.5 hearts |
| Contact Damage | 0.50 hearts |
| Patrol Speed | 30 px/s |
| Alert Speed | 55 px/s |
| Detection Range X | 128 px |

**Visual:** A large, aggressive pigeon — eyes red from the hawk's influence. Puffed up. Sprite: `enemy_palom_walk.png` (6 frames, 8 FPS). Size: 16×16 px.

**Behavior Note:** Slow but sturdy. Fills the ground-level threat in the wide Hall stage. Their large health pool means they persist as a hazard even while the player deals with aerial threats.

---

### 4.5 `ShooterBuitre` — Black Vulture (Perching)

| Property | Value |
|---|---|
| Base Class | `EnemyShooter` |
| Appears In | Stage 3-2 |
| Health | 3.5 hearts |
| Projectile Damage | 0.50 hearts |
| Fire Rate | 0.35 shots/s |
| Projectile Speed | 100 px/s |
| Detection Range X | 240 px |

**Visual:** A large black vulture (Coragyps atratus — common in urban Costa Rica). Perched on balcony railings, hunched. Sprite: `enemy_buitre_idle.png` (4 frames, 5 FPS). Size: 18×22 px. **Projectile:** bone fragment, `enemy_buitre_proyectil.png` (2 frames, tumbling, 8×6 px).

**Behavior Note:** Very long detection range — 240px means it can engage the player from off-screen at the start of the Hall. Paired with the hawk dives, it creates crossfire situations.

---

## 5. Zone Final — Cemetery Enemies

The cemetery has no standard enemies during Stage 4-1 (intentionally empty — see World Design). The only enemy encounters are with the final boss in Stage 4-2.

However, **Spirit Echoes** — spectral versions of defeated zone enemies — may appear during El Gran Shaman Paburu's `ANCIENT_CALL` attack:

| Echo | Source | Health | Damage |
|---|---|---|---|
| `EchoVenado` | El Venado Sagrado Phase 1 | N/A (single attack, then dissipate) | 50% of original |
| `EchoRey` | El Rey Terciopelo Phase 1 | N/A (single attack) | 50% |
| `EchoGavilán` | El Gavilán Phase 1 | N/A (single attack) | 50% |

Spirit Echoes are implemented as temporary entity instances using the boss sprites with `set_alpha(120)`. They do not have health bars. One attack, then auto-destroy.

---

## 6. Enemy Roster Summary Table

| ID | Name | Zone | Stages | Base | Health | Contact | Projectile |
|---|---|---|---|---|---|---|---|
| E-101 | WalkerInsect | 1 | 1-1, 1-2 | Walker | 1.0 | 0.25 | — |
| E-102 | FlyingBird | 1 | 1-1, 1-3 | Flying | 1.0 | 0.25 | — |
| E-103 | ShooterFrog | 1 | 1-1, 1-3 | Shooter | 2.0 | 0.25 | 0.25 |
| E-104 | WalkerRaton | 1 | 1-2 | Walker | 1.0 | 0.25 | — |
| E-105 | FlyingCucaracha | 1 | 1-2 | Flying | 1.0 | 0.25 | — |
| E-106 | ShooterCocinero | 1 | 1-2 | Shooter | 3.0 | 0.25 | 0.50 |
| E-107 | WalkerEstudiante | 1 | 1-3 | Walker | 1.5 | 0.50 | — |
| E-108 | FlyingNotebook | 1 | 1-3 | Flying | 0.5 | 0.25 | — |
| E-109 | ShooterTiza | 1 | 1-3 | Shooter | 2.5 | — | 0.25 |
| E-201 | WalkerSerpientePequena | 2 | 2-1 to 2-4 | Walker | 1.0 | 0.50 | — |
| E-202 | FlyingBoa | 2 | 2-1, 2-2 | Flying | 2.0 | 0.50 | — |
| E-203 | ShooterSerpienteArbol | 2 | 2-1 to 2-3 | Shooter | 2.0 | — | 0.50 |
| E-204 | WalkerTerciopelo | 2 | 2-3 | Walker | 2.5 | 0.75 | — |
| E-205 | ShooterVenomoLargo | 2 | 2-3 | Shooter | 3.0 | — | 0.50 |
| E-206 | FlyingTerciovolador | 2 | 2-3 | Flying | 1.5 | 0.50 | — |
| E-207 | WalkerGuardia | 2 | 2-2 | Walker | 3.0 | 0.50 | — |
| E-301 | WalkerGarza | 3 | 3-1 | Walker | 2.0 | 0.50 | — |
| E-302 | FlyingHalcon | 3 | 3-1 to 3-3 | Flying | 2.0 | 0.75 | — |
| E-303 | ShooterQuetzal | 3 | 3-1 to 3-3 | Shooter | 2.5 | — | 0.25 |
| E-304 | WalkerPalom | 3 | 3-2, 3-3 | Walker | 2.5 | 0.50 | — |
| E-305 | ShooterBuitre | 3 | 3-2 | Shooter | 3.5 | — | 0.50 |

---

## 7. Enemy Design Constraints for Students

Students building traversal stages (1-1 through 1-3, 2-1 through 2-3, 3-1 through 3-3) must follow these rules when placing enemies:

| Rule | Description |
|---|---|
| Use only zone-appropriate enemies | Zone 1 enemies in Zone 1 stages only, etc. |
| Maximum 3 distinct enemy types per stage | Depth over breadth |
| No mixing zone enemy rosters | No Zone 2 serpents in Zone 1 jungle stages |
| Enemy properties may be overridden via TMX | `patrol_length`, `damage_on_contact`, speeds can be adjusted |
| New enemy subclasses require professor approval | Custom enemies must extend a base template |
| Enemy counts must be manageable | No more than 12 simultaneous active enemies in a single stage |

---

## 8. Enemy Progression

Difficulty escalates deliberately across zones and within each zone:

| Zone | Health Range | Damage Range | Speed Profile |
|---|---|---|---|
| 1 — Campus | 0.5–3.0 hearts | 0.25–0.50 hearts | Slow to moderate |
| 2 — Datacenter | 1.0–3.5 hearts | 0.50–0.75 hearts | Moderate to fast |
| 3 — Heredia | 2.0–3.5 hearts | 0.50–0.75 hearts | Moderate + aerial |
| Final — Cemetery | Boss echoes only | 50% of boss values | Variable |

This progression ensures that Stage 0 (which uses Zone-neutral enemies) feels accessible, while student stages carry appropriate threat escalation.
