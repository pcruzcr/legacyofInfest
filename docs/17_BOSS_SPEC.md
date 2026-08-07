---
document_id: "LOI-BOSS-017"
title: "Legacy of InFest — Boss Specification"
aliases: ["Boss Specification", "Boss Spec"]
tags: ["boss", "specification", "entity"]
description: "Los 4 jefes de diseño; 3 implementados. Ver §0 para el estado real"
source: "docs/17_BOSS_SPEC.md"
date_processed: "2026-07-14"
---

# Legacy of InFest — Boss Specification

**Document ID:** LOI-BOSS-017  
**Version:** 1.0.0  
**Status:** Official  
**Compatibility:** Requires LOI-ENEMY-005, LOI-WORLD-016, LOI-ARCH-003, LOI-FILTER-011, LOI-VISION-012, LOI-PATTERN-013  
**Audience:** Professor, Teaching Assistants, AI coding assistants

---

## 0. Qué de esto existe hoy (AUD-150)

> **Leer esto antes que nada.** Este documento describe **cuatro jefes** y
> unos cuarenta patrones de ataque. En el código hay **cuatro clases de jefe** y
> **17 patrones**. Lo demás es diseño: legítimo, útil y **no implementado**.
>
> *(Medido el 6 de agosto de 2026 — AUD-311. La versión anterior decía «tres
> clases y nueve patrones», y era cierta al escribirse: desde entonces apareció
> `BossGavilan` y `BossPaburu` pasó de una forma a cuatro.)*
>
> El registro de pendientes (`63`) lo llamaba «22 patrones que ningún jefe
> implementa» y sugería reescribir la especificación contra los jefes reales.
> No se reescribe: se **etiqueta**. Un diseño de jefe que aún no existe es lo
> que una especificación debe contener; lo que no puede es que nadie sepa cuál
> de las dos cosas está leyendo.

<!-- cita-historica -->

| Jefe | Clase en el código | Fases reales | Patrones que EXISTEN | Patrones sólo diseñados |
|---|---|---|---|---|
| El Venado Sagrado (§3) | `BossVenado` | 2 | `STOMP`, `CHARGE`, `VINE_TOSS`, `VINE_SWEEP`, `MUSHROOM_SPORE` | — |
| El Rey Terciopelo (§4) | `BossRey` | **1** | `VENOM_SPIT` | `SERPENT_CARPET`, `VENOM_BURST`, `SERPENT_WAVE`, y las formas `ReyMetad` de las fases 2-3 |
| El Gavilán Mascarero (§5) | `BossGavilan` | **1** | **ninguno** (`attack_patterns=[]`) | todo §5. Es **asignación de estudiante**: 45 % de la rúbrica de `grade_boss` |
| El Gran Shaman Paburu (§6) | `BossPaburu` | **4 formas** | Piedra: `STONE_SPIT`, `EYE_BEAM`, `EL_SELLO` · Máscara: `SPIRIT_WAVE`, `DUELO_DE_ECOS`, `MASK_PULSE` · Espíritu: `RELIC_SURGE`, `SPIRIT_FORM`, `ANCIENT_CALL`, `CONVERGENCE`, `EL_OFRECIMIENTO` | La Reliquia (forma 3) tiene `attack_patterns=[]`: se llenan al elegir 3A/3B, y esa elección no está escrita |

<!-- /cita-historica -->

**Cómo se comprobó.** Leyendo `attack_patterns` de cada `BossPhase` en las tres
clases y los métodos `_attack_*` / `_do_*` que las ejecutan. La lista de
patrones inventados del registro salía de citar nombres en este documento que
no aparecen en ningún fichero `.py`.

> **Actualización (AUD-265, 2026-08-04): el Gavilán ya tiene clase.** La fila
> de arriba dice «ninguna» y era cierta el día que se escribió; la entrega
> llegó después. Hoy existe `class BossGavilan(BossBase)` en
> `src/stages/stage3_4_boss_gavilan/boss_gavilan.py`, con su escena y su mapa.
>
> **Es parcial y lo dice ella misma**: implementa sólo la fase 1, «El Vuelo
> Circular» de §5.3, sin ataques y sin las fases 2 y 3. Los jefes son **cuatro**,
> uno de ellos a medias.
>
> Y no se completa desde aquí: `src/stages/` es **código de estudiantes**
> (invariante 1 de `CLAUDE.md`). Terminar el Gavilán es trabajo de quien lo
> tiene asignado, con esta especificación como contrato; lo que sí es trabajo
> del motor es que el documento diga la verdad sobre lo que hay.

### Aviso de asignación — el Gavilán está SIN ASIGNAR

**Estado a 4 de agosto de 2026.** Las etapas tempranas del Gavilán —lo que hay
en `boss_gavilan.py`— están **sin asignar**: nadie las mantiene hoy.

**El desarrollo completo del jefe Gavilán queda a cargo de los estudiantes.**
Es una asignación abierta, no deuda del motor. Quien la tome recibe:

<!-- cita-historica -->
| Lo que ya está hecho | Lo que falta por hacer |
|---|---|
| La clase `BossGavilan(BossBase)` con la fase 1, «El Vuelo Circular» (§5.3): órbita paramétrica con vectores explícitos (Unidad II) | Las **fases 2 y 3** completas |
| Su escena `Stage3_4BossGavilanScene` y su mapa (58,7 KB), ya en el registro y jugables | Los **patrones de ataque** de §5: `DIVE_BOMB`, `FEATHER_STORM`, `MASK_BEAM`, `ORBIT_SHRINK`, `RAPID_DIVE`, `FULL_FEATHER_STORM`, `MASK_FRAGMENT_STORM`, `FEATHER_TOSS` — hoy `attack_patterns=[]` |
| Nueve sprites en `assets/sprites/bosses/` (`dive`, `feather`, `glide`, `hover`, `masked`, `mask_frag`, `storm`, `hurt`, `death`) | Los **puntos débiles** (`WeakPoint`) y la **telegrafía** de cada ataque |
| Todo `BossBase` heredado gratis: fases, parry (AUD-243), escala de fase y teletransporte (AUD-257), arena, invocaciones | Los sonidos `SFX_BOSSES_GAVILAN_DIVE` y `_MASK_BEAM`, que **existen con fichero** y esperan su emisor |
<!-- /cita-historica -->

**Por dónde empezar, medido:** `src/stages/boss_venado/boss_venado.py` es el
jefe de referencia y hace las mismas cosas que §5 pide — telegrafía, puntos
débiles, proyectiles con curva, dos fases con escala y teletransporte, voz—.
Copiar de ahí es lo esperado, no hacer trampa.

**Cómo se califica:** `python scripts/grade_boss.py src/stages/stage3_4_boss_gavilan/boss_gavilan.py --json`
(100 puntos). Medido el 2026-08-04: el venado saca **100 %**, el Gavilán **45 %**. Esos 55 puntos son, literalmente, la tarea.

**`BossSpawn`** —el tipo de objeto de Tiled que §8 describe— **ya funciona
(AUD-259)**. Hasta entonces el motor no lo conocía y un estudiante que siguiera
esta especificación al pie de la letra recibía un aviso de tipo desconocido.

Declara **dónde entra** el jefe que nombra su propiedad `boss`:

```
type = "BossSpawn"      boss = "BossVenado"
```

y produce exactamente la misma entidad que escribir `BossVenado` como tipo,
porque se resuelve por el mismo registro. Sin `boss`, o con un nombre no
registrado, el cargador **avisa** en vez de callarse.

Los jefes existentes siguen colocándose con su tipo propio y no se tocó
ninguno: `BossSpawn` es aditivo y ningún mapa entregado lo declara.

---

## 1. Overview

Legacy of InFest features four boss encounters — one per zone. **Corrected per `77_SYLLABUS_ALIGNMENT_AUDIT.md` §2.A.1 and §5:** the course syllabus explicitly allows a student to individually select a **Boss** (not only a Stage) as their trimester assignment — *"Cada estudiante selecciona un Stage o Boss durante la primera clase."* This document's boss designs therefore serve two purposes: (1) Stage 0 and any boss **not** claimed by a student remain professor-owned, implemented as reference/executable documentation; (2) any boss **claimed by a student** is built by that student, using this specification as the required design contract, in the same way `07_STAGE0_DESIGN.md` and `16_WORLD_DESIGN.md` define the contract for Stage assignments. `BossBase` and the academic pipeline integration points described below apply identically regardless of who implements a given boss.

**Boss origin classification and implementation status (required by `77_SYLLABUS_ALIGNMENT_AUDIT.md` §5):**

| Boss | Origin | Implementation Status |
|---|---|---|
| El Venado Sagrado (Zone 1) | **Syllabus-official.** Defined verbatim in the course syllabus. | **Implemented** — `BossVenado` in `src/stages/boss_venado/boss_venado.py` |
| El Rey Terciopelo (Zone 2) | **Syllabus-official.** Defined verbatim in the course syllabus. | **Planned** — design specified below, implementation by assigned student |
| El Gavilán Camionero Mascarero (Zone 3) | **Confirmed official (project-defined, now professor-confirmed final).** The syllabus originally stated the Zone 3 boss was *"Pendiente de definición final dentro de la narrativa general."* This design was authored by the documentation project to fill that open item and has since been **reviewed and confirmed as final by the professor** (see `28_DECISION_LOG.md` ADR-008). It is the permanent Zone 3 boss — no longer subject to reassignment risk. | **Planned** — design specified below, implementation by assigned student |
| Gran Shaman Paburu (Final Boss) | **Syllabus-official** (core identity and role) **+ project-defined elaboration** (the specific 4-form structure). The syllabus confirms Paburu as *"el guardián ancestral que busca restaurar el equilibrio natural y recuperar las reliquias que provocaron su despertar"* but gives no phase-by-phase detail; the 4-form design below elaborates on that one-paragraph description and is preserved as a legitimate extension. | **Planned** — design specified below, implementation reserved for professor |

Each boss is a multi-phase entity that demonstrates the full academic pipeline of the course:
- Phase transitions use **Unit III** curve mathematics for movement
- Visual effects use **Unit V, VII** color and filter operations
- Phase detection uses **Unit IX** classification (for the relevant bosses)

All bosses inherit from `BossBase`, a subclass of `EnemyBase`. The `BossBase` class adds phase management, phase-based health bars, a dedicated boss HUD element, and the `BOSS_PHASE_CHANGED` event.

---

## 2. BossBase

### 2.1 Class Definition

`BossBase` extends `EnemyBase` (see `05_ENEMY_SPEC.md`) with the following additions:

| Property | Type | Description |
|---|---|---|
| `phases` | `list[BossPhase]` | Ordered list of phase definitions |
| `current_phase` | `int` | Index of the active phase (0-based) |
| `phase_health_thresholds` | `list[float]` | Health values at which phase transitions occur |
| `is_transitioning` | `bool` | True during phase transition animation |
| `transition_timer` | `float` | Countdown for transition duration |

### 2.2 BossPhase Definition

Each phase is a `BossPhase` dataclass:

| Field | Type | Description |
|---|---|---|
| `phase_index` | `int` | 0-based phase number |
| `health_threshold` | `float` | Boss transitions to NEXT phase when health drops below this |
| `attack_patterns` | `list[str]` | Named attack pattern identifiers for this phase |
| `movement_type` | `str` | Movement strategy: `'stationary'`, `'bezier'`, `'sine'`, `'random_walk'` |
| `speed_multiplier` | `float` | Speed relative to Phase 0 baseline |
| `sprite_override` | `str | None` | If set, replace sprite sheet for this phase |
| `filter_effect` | `str | None` | FilterTools effect applied to boss surface each frame: `'sobel'`, `'canny'`, `'tint_green'`, etc. |

### 2.3 Phase Transition Protocol

When boss health drops below `phase_health_thresholds[current_phase]`:

1. `is_transitioning = True`
2. Boss becomes invincible (`invincibility_timer = INF`)
3. Transition animation plays (typically 2–3 seconds)
4. `BOSS_PHASE_CHANGED` event emitted with `phase = current_phase + 1`
5. HUD boss health bar re-fills to new phase maximum
6. `current_phase += 1`
7. `is_transitioning = False`
8. Invincibility expires; combat resumes

### 2.4 Boss HUD Element

A dedicated boss health bar is rendered at the bottom of the screen during boss stages, separate from the player health display:

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │ Y=208
│  [BOSS NAME          ] [████████████████████████████████] [P1]  │ Y=212
│                                                                 │ Y=220
└─────────────────────────────────────────────────────────────────┘
```

| Element | Description |
|---|---|
| Boss name | Displayed left-aligned in gold `banner_medium` font |
| Health bar | Fills left to right. Color: red for full health, shifts to orange then yellow as depleted |
| Phase indicator | `[P1]`, `[P2]`, etc. — updates on phase change |

---

## 3. Boss 1 — El Venado Sagrado

### 3.1 Concept

**Name:** El Venado Sagrado (The Sacred Deer)  
**Location:** Stage 1-4 — La Residencia  
**Health:** 12 hearts (3 per phase × 4 phases equivalent — distributed as 12 total across 2 phases)

El Venado Sagrado is the spirit of an ancient white-tailed deer — a creature of the forest that has been dead for decades, now fully reclaimed by nature. Its skeleton is entwined with vines, draped in moss and ferns, crawling with beetles and worms. Mushrooms grow from its ribs. It does not walk — it **drifts**, as if the forest itself carries it.

**Design References:**
- White-tailed deer (Odocoileus virginianus) — the animal
- Forest spirit aesthetic: Studio Ghibli's Forest Spirit, Demon's Crest gothic bone design
- SNES palette: 16 colors — bone white, deep moss green, earth brown, fungus cream, shadow black

### 3.2 Sprite Specifications

| Sheet | File | Frames | FPS | Loop |
|---|---|---|---|---|
| Phase 1 — Drift | `boss_venado_drift.png` | 6 | 8 | Yes |
| Phase 1 — Attack Stomp | `boss_venado_stomp.png` | 8 | 12 | No |
| Phase 1 — Attack Charge | `boss_venado_charge.png` | 6 | 14 | No |
| Phase 2 — Frenzy Drift | `boss_venado_frenzy_drift.png` | 6 | 14 | Yes |
| Phase 2 — Attack Vine Sweep | `boss_venado_vine.png` | 10 | 12 | No |
| Hurt | `boss_venado_hurt.png` | 4 | 12 | No |
| Death | `boss_venado_death.png` | 12 | 8 | No |

**Sprite size:** 48×48 pixels  
**Hitbox:** 36×44 px (offset 6px from sprite left, 4px from sprite top)  
**Hurtbox:** 30×40 px (centered within sprite)

### 3.3 Phases

#### Phase 1 — "El Bosque Duerme" (Health: 12 → 6 hearts)

**Entry Condition:** Stage 1-4 loaded, banner complete  
**Movement Type:** Sinusoidal drift across the arena (horizontal, amplitude=40px, frequency=0.4 Hz)  
**Speed:** 60 px/s horizontal base

**Attack Patterns:**

| Pattern Name | Trigger | Description |
|---|---|---|
| `STOMP` | Player within 96px horizontally | Boss rears up and slams front hooves. Creates a 96px-wide shockwave rect at floor level. Damage: 1.0 heart. |
| `CHARGE` | Player in opposite half of arena | Boss charges horizontally at 220px/s. Damage on contact: 0.75 hearts. Stops at arena wall. |
| `VINE_TOSS` | Every 8 seconds | Releases a vine projectile that travels in a Bézier arc to a predicted player position. Damage: 0.5 hearts. |

**Attack Cooldowns:**
- `STOMP` cooldown: 3.0 seconds
- `CHARGE` cooldown: 6.0 seconds  
- `VINE_TOSS` cooldown: 8.0 seconds

**Visual Effect (Unit VII):**  
Phase 1: `FilterTools.sobel_edge()` is applied to the boss surface every 5 frames and blended at alpha=80 over the boss sprite. This creates a subtle edge-glow aura — as if the forest outlines the deer.

**Academic Illustration (Unit III):**  
The `VINE_TOSS` projectile follows a degree-2 Bézier arc:
- Control point 0: Boss muzzle position
- Control point 1: Midpoint elevated by 80px
- Control point 2: Predicted player position (current position + velocity × 0.5s)

#### Phase 2 — "El Bosque Despierta" (Health: 6 → 0 hearts)

**Transition:**
1. Boss stops moving (0.5s)
2. Vines on the skeleton pulse and writhe (animation override)
3. Two new antler-vine extensions grow (sprite changes)
4. `BOSS_PHASE_CHANGED` emitted
5. Speed increases, new attacks unlock

**Movement Type:** Bézier path — pre-computed figure-8 path through the arena  
**Speed multiplier:** 1.5×

**New Attack Patterns:**

| Pattern Name | Trigger | Description |
|---|---|---|
| `VINE_SWEEP` | Every 5 seconds | Boss sweeps both vine-antlers in a wide arc. Full-width floor-level hitbox (320×24px). Damage: 0.5 hearts. Jump to avoid. |
| `MUSHROOM_SPORE` | Every 10 seconds | Releases 3 spore projectiles in a spread (left, center, right) from boss position. Each travels straight. Damage: 0.25 hearts each. |
| `CHARGE` | Still available — faster | Now at 280 px/s. |

**Visual Effect (Unit VII — Phase 2):**  
Phase 2: `FilterTools.apply_kernel(sobel_x_kernel)` applied every 3 frames creates a directional glow that intensifies as health decreases. At <3 hearts remaining, the boss visually flickers between normal and edge-map overlay each frame.

### 3.4 Arena Elements

| Element | Position | Type | Description |
|---|---|---|---|
| Stone platform L | X=48, Y=160 | OneWay | Elevated platform left |
| Stone platform C | X=136, Y=144 | OneWay | Central high platform |
| Stone platform R | X=224, Y=160 | OneWay | Elevated platform right |
| Vine arch | X=272–320 | Visual only | Boss entrance point |

### 3.5 Academic Mapping

| Phase | Academic Unit | Implementation |
|---|---|---|
| Phase 1 Drift | Unit III — Sine trajectory | `position.y = base_y + A * sin(2πft)` |
| Phase 1 Vine Toss | Unit III — Bézier projectile | `CurveTools.bezier(control_points, 32)` |
| Phase 1 Aura | Unit VII — Sobel edge | `FilterTools.sobel_edge(boss_surface)` |
| Phase 2 Path | Unit III — Bézier arena path | Pre-computed figure-8 with 6 control points |
| Phase 2 Flicker | Unit VII — Kernel convolution | `FilterTools.apply_kernel(sobel_x)` |

### 3.6 Defeat Sequence

1. Death animation plays (12 frames, 8 FPS)
2. Boss dissolves into floating leaf/vine particles (sprite-based particle system, 8 sprites)
3. A glowing deer skull remains for 2 seconds
4. Skull fades — a new HUD icon appears: **Relic Fragment 1** (antler icon)
5. `STAGE_COMPLETE` emitted
6. Transition to Stage 2-1

---

## 4. Boss 2 — El Rey Terciopelo

<!-- cita-historica -->
> **Estado (AUD-150): fase 1 implementada, fases 2 y 3 no.** `BossRey` existe
> con una sola `BossPhase` y un único patrón, `VENOM_SPIT`. Todo lo que este
> apartado dice de serpientes, ráfagas y mitades `ReyMetad` es diseño.
<!-- /cita-historica -->

### 4.1 Concept

**Name:** El Rey Terciopelo (The Fer-de-Lance King)  
**Location:** Stage 2-4 — El Datacenter  
**Health:** 15 hearts total across 3 phases (5 per phase)

El Rey Terciopelo is not a single creature — it is thousands of terciopelo (fer-de-lance) vipers that have merged into a collective intelligence, animating a decomposed humanoid body as their vessel. The body is their **puppet** — they flow in and out of it through its joints and mouth, communicating through venom signals. The body moves jerkily, unnaturally — controlled from within.

**Design References:**
- Terciopelo (Bothrops asper) — the most dangerous snake in Costa Rica
- Puppet/marionette movement aesthetics
- Decay and infestation — worm-style animation cycles within the body's silhouette

### 4.2 Sprite Specifications

| Sheet | File | Frames | FPS | Loop |
|---|---|---|---|---|
| Phase 1 — Walk | `boss_rey_walk.png` | 8 | 10 | Yes |
| Phase 1 — Spit | `boss_rey_spit.png` | 6 | 12 | No |
| Phase 2 — Split | `boss_rey_split.png` | 8 | 10 | Yes (two entities) |
| Phase 3 — Merge | `boss_rey_merge.png` | 6 | 8 | No |
| Phase 3 — Rampage | `boss_rey_rampage.png` | 8 | 16 | Yes |
| Hurt | `boss_rey_hurt.png` | 4 | 12 | No |
| Death | `boss_rey_death.png` | 14 | 8 | No |

**Sprite size:** Phase 1: 40×56 px. Phase 2 split entities: 24×28 px each.  
**Phase 1 Hurtbox:** 28×48 px

### 4.3 Phases
<!-- diseno-pendiente -->

#### Phase 1 — "La Marioneta" (Health: 15 → 10 hearts)

**Movement Type:** Erratic random walk — jittered position updated every 0.3s using `CurveTools.catmull_rom()` through 4 random arena positions  
**Speed:** 50 px/s

**Attack Patterns:**

| Pattern | Trigger | Description |
|---|---|---|
| `VENOM_SPIT` | Player within 200px | Spits a slow venom glob that travels straight. Damage: 0.5 hearts. |
| `SERPENT_CARPET` | Every 10 seconds | Releases 6 small `WalkerSerpientePequena` enemies from its body. Damage if touched: 0.25 hearts each. |
| `BODY_SLAM` | Player within 64px | Lurches forward 80px instantly. Contact damage: 1.0 heart. |

**Visual Effect (Unit V):**  
Phase 1: `ColorTools.apply_tint(boss_surface, (30, 80, 0))` — a sickly green tint applied to the entire boss surface each frame, giving the decomposed body a venomous glow.

#### Phase 2 — "La División" (Health: 10 → 4 hearts)

**Transition:**
1. Body shudders and collapses
2. Two streams of serpents exit and form two **independent sub-bosses**: `ReyMetad` (Left Half) and `ReyMetad` (Right Half)
3. Each half has 3 hearts of its own health
4. When both halves are reduced to 0, Phase 3 begins

**Sub-Boss Behavior:**
- Each `ReyMetad` behaves like an enlarged `EnemyWalker` with Phase 1's `VENOM_SPIT`
- They coordinate: one attacks while the other repositions
- Contact damage: 0.5 hearts

**How Phase 3 Triggers:**  
When both `ReyMetad` entities reach 0 health, they are not killed — they simultaneously trigger `BOSS_PHASE_CHANGED`. The stage catches this event and initiates Phase 3.

#### Phase 3 — "El Frenesí" (Health: 4 → 0 hearts)

**Transition:**
1. Both half-bodies collapse and serpents stream back together
2. Body re-assembles — now faster, larger (sprites upscaled by 1.25× using pygame transform)
3. Body pulses with green venom

**Movement Type:** Aggressive straight-line pursuit of player at 130 px/s  
**Speed multiplier:** 2.6× vs Phase 1

**New Attack Patterns:**

| Pattern | Trigger | Description |
|---|---|---|
| `VENOM_BURST` | Every 6 seconds | Spits 5 venom globs in a fan spread (angles: -30°, -15°, 0°, +15°, +30°). Each: 0.25 hearts. |
| `SERPENT_WAVE` | Every 12 seconds | Releases 12 serpents simultaneously across the full arena floor. 3-second duration. |
| `LUNGE` | Player in any position | Charges 160px in player direction at 350px/s. 1.25 hearts damage. 8-second cooldown. |

**Visual Effect (Unit IX — Academic Highlight):**  
Phase 3 introduces a pattern recognition mechanic. The boss alternates between three sub-states every 8–15 seconds: `AGGRESSIVE` (charges frequently), `DISPERSED` (releases serpents), and `DEFENSIVE` (venom burst from distance). The transition between states is not announced explicitly.

The professor's implementation includes inline comments documenting that a student with Unit IX knowledge could implement a classifier to detect the current sub-state by analyzing the boss sprite's position history or the density of active serpent entities on screen — and use that to inform player strategy. This is documented in Stage 2-4's README as an extension exercise.

<!-- /diseno-pendiente -->
### 4.4 Defeat Sequence

1. Death animation: body collapses, serpents scatter and writhe
2. All `WalkerSerpientePequena` enemies are immediately deactivated
3. A large terciopelo head remains, dissolves in green light
4. **Relic Fragment 2** (serpent coil icon) appears
5. `STAGE_COMPLETE` emitted → Zone 3

---

## 5. Boss 3 — El Gavilán Camionero Mascarero

<!-- cita-historica -->
> **Estado (AUD-150): NO EXISTE.** No hay clase, ni sprites, ni escena. El
> registro de escenarios reserva el hueco `stage3_4_boss_gavilan` y los
> créditos ya lo citan, pero el jefe está entero por hacer. Todo este apartado
> es diseño; ninguno de sus patrones —`DIVE_BOMB`, `FEATHER_STORM`,
> `MASK_BEAM` y los demás— aparece en el código.
<!-- /cita-historica -->

### 5.1 Concept

**Name:** El Gavilán Camionero Mascarero (The Masked Trucker Hawk)  
**Location:** Stage 3-4 — El Bungaló  
**Health:** 14 hearts across 3 phases

El Gavilán is a common roadside hawk (Buteo magnirostris — the Roadside Hawk, colloquially called "gavilán camionero" in Costa Rica because they perch on highway signs). A Tilawa ceremonial mask has fused with the hawk's face, granting it supernatural intelligence and power. The mask pulses with golden Tilawa energy. The hawk is enormous — wingspan equal to the arena width.

**Design References:**
- Buteo magnirostris — real Costa Rican hawk
- Tilawa ceremonial masks — fictional cultural artifact (handled with deep respect)
- Super Castlevania IV Medusa aesthetic — large, slow, aerial predator

**Cultural Note:** The Tilawa mask is depicted with respect and reverence. It is presented as a sacred object that was appropriated by Paburu's influence — the mask itself is not evil; it has been corrupted. The defeat sequence honors this.

### 5.2 Sprite Specifications

| Sheet | File | Frames | FPS | Loop |
|---|---|---|---|---|
| Phase 1 — Glide | `boss_gavilán_glide.png` | 8 | 10 | Yes |
| Phase 1 — Dive | `boss_gavilán_dive.png` | 6 | 16 | No |
| Phase 2 — Hover | `boss_gavilán_hover.png` | 4 | 8 | Yes |
| Phase 2 — Feather Storm | `boss_gavilán_storm.png` | 8 | 12 | No |
| Phase 3 — Mask Glow | `boss_gavilán_masked.png` | 6 | 14 | Yes |
| Hurt | `boss_gavilán_hurt.png` | 4 | 12 | No |
| Death | `boss_gavilán_death.png` | 16 | 8 | No |
| Mask Fragment | `boss_gavilán_mask_frag.png` | 4 | 12 | No (projectile) |

**Sprite size:** 56×40 px (wider than tall — wingspan emphasis)  
**Hurtbox:** 40×28 px (body center, excluding wing tips)

### 5.3 Phases
<!-- diseno-pendiente -->

#### Phase 1 — "El Vuelo Circular" (Health: 14 → 9 hearts)

**Movement Type:** Circular orbit around the arena center  
- Orbit radius: 80px from center
- Orbit speed: 0.6 radians/second (full circle ~10 seconds)
- Computed as: `position = center + (cos(angle) * radius, sin(angle) * radius)`
- This is documented in source comments as an illustration of circular parametric movement (Unit II — vector, Unit III — parametric)

**Attack Patterns:**

| Pattern | Trigger | Description |
|---|---|---|
| `DIVE_BOMB` | Every 6 seconds | Leaves orbit, dives straight down to player's current X, then returns to orbit. Speed: 300px/s. Damage: 0.75 hearts. |
| `FEATHER_TOSS` | Every 8 seconds | Releases 4 feather projectiles at cardinal directions (left, right, down-left, down-right). Each: 0.25 hearts. |
| `ORBIT_SHRINK` | At 11 hearts | Orbit radius reduces to 48px — hawk is closer and harder to dodge |

**Visual Effect (Unit V):**  
Phase 1: `ColorTools.rgb_to_hsv()` is applied to the boss surface each frame, hue is rotated by +5° per second, and `ColorTools.hsv_to_rgb()` converts back. This creates a slow iridescent shimmer on the feathers.

#### Phase 2 — "El Ojo de la Máscara" (Health: 9 → 4 hearts)

**Transition:**
1. Hawk halts in center of arena (1 second hold)
2. Tilawa mask begins to glow — pulse animation on mask sprite region
3. Hawk lifts to top-center of arena and hovers there for the entire phase
4. `BOSS_PHASE_CHANGED`

**Movement Type:** Stationary hover at (160, 48)  
**Phase 2 introduces aerial dominance — the hawk never lands, never moves from its hover point. All attacks are downward.**

**New Attack Patterns:**

| Pattern | Trigger | Description |
|---|---|---|
| `FEATHER_STORM` | Every 7 seconds | Releases 8 feathers in a full downward spread. Variable speeds. Duration: 3 seconds of falling feathers. 0.25 hearts each. |
| `MASK_BEAM` | Every 10 seconds | Fires a vertical beam from mask eye downward. 24px-wide rect, instantaneous, full arena height. Damage: 1.0 heart. 0.5s warning flash before activation. |
| `WIND_BLAST` | Every 12 seconds | Horizontal wind pushes player 96px in the direction the hawk is facing. No damage — positional disruption. |

**Visual Effect (Unit VII):**  
Phase 2: `FilterTools.gaussian_blur(boss_surface, sigma=0.8)` applied every 3 frames creates a soft glow around the mask. The blur radius increases as health decreases.

#### Phase 3 — "La Máscara Sin Control" (Health: 4 → 0)

**Transition:**
1. The Tilawa mask cracks — fracture lines animate across it
2. Golden energy bursts from the cracks (particle sprites)
3. Hawk descends from hover, now unpredictable

**Movement Type:** Erratic — combines diving and hovering randomly. Uses `CurveTools.catmull_rom()` through 6 random-but-bounded points in the arena.

**New Attack Patterns:**

| Pattern | Trigger | Description |
|---|---|---|
| `MASK_FRAGMENT_STORM` | Every 8 seconds | Broken mask pieces fly outward in 6 directions. Each fragment has 0.5 hearts damage and bounces off arena walls once. |
| `RAPID_DIVE` | Every 4 seconds | Two consecutive dive-bombs in quick succession (0.5s gap). |
| `FULL_FEATHER_STORM` | Every 15 seconds | Extended storm — 16 feathers over 5 seconds. |

**Visual Effect (Unit VII — Phase 3):**  
`FilterTools.canny_edge(boss_surface, 40, 120)` blended at alpha=100 over the boss sprite. The fractured mask creates strong edges that the Canny filter highlights — the hawk's form is surrounded by harsh, erratic edge lines matching the broken mask aesthetic.

**Academic Highlight (Unit IX):**  
Phase 3's movement pattern — a combination of diving and erratic hovering — can theoretically be classified using a trained classifier on positional history. The professor documents this in Stage 3-4's README as an advanced exercise: given the hawk's Y-position over the last 10 frames, classify whether the next action will be `DIVE` or `HOVER` and position the player accordingly.

<!-- /diseno-pendiente -->
### 5.4 Defeat Sequence

1. Death animation: hawk drops to the arena floor
2. Tilawa mask slowly lifts from the hawk's face — floats upward, pulsing gently
3. Mask glows warm gold and dissipates (it is freed, not destroyed)
4. Hawk reverts to its natural size — a normal roadside hawk — and flies out through the skylight
5. **Relic Fragment 3** (mask outline icon) appears
6. `STAGE_COMPLETE` emitted → Zone Final

---

## 6. Final Boss — El Gran Shaman Paburu

<!-- cita-historica -->
> **Estado (AUD-150): Forma 1 implementada.** `BossPaburu` tiene sus tres
> patrones —`STONE_SPIT`, `EYE_BEAM`, `EL_SELLO`— y su arena. Las formas 2, 3
> y 4 están por hacer, y el propio código lo dice en un comentario que remite
> a EP3.
<!-- /cita-historica -->

### 6.1 Concept

**Name:** El Gran Shaman Paburu  
**Location:** Stage 4-2 — El Cementerio Sagrado  
**Health:** 20 hearts total across 4 phases (5 per phase)

Paburu is the Grand Shaman — a Tilawa spiritual figure of immense power who has been corrupted by an ancient grief. He does not fight to destroy — he fights to **test**. The Gold Nugget (La Pepita) and the Pearl (La Perla) carried by John and Jin are the final keys to his ritual. He needs to see if they are worthy.

His four forms are not separate entities — they are layers of his power, each revealing more of who he truly is.

### 6.2 Sprite Specifications

| Sheet | File | Frames | FPS | Loop |
|---|---|---|---|---|
| Form 1 — Stone Head | `boss_paburu_stone.png` | 4 | 6 | Yes |
| Form 1 — Stone Slam | `boss_paburu_stone_slam.png` | 8 | 12 | No |
| Form 2 — Spectral Mask | `boss_paburu_mask.png` | 6 | 10 | Yes |
| Form 2 — Spectral Wave | `boss_paburu_mask_wave.png` | 8 | 12 | No |
| Form 3A — Gold Sphere | `boss_paburu_gold.png` | 6 | 14 | Yes |
| Form 3B — Black Sphere | `boss_paburu_black.png` | 6 | 14 | Yes |
| Form 3 — Relic Attack | `boss_paburu_relic_atk.png` | 10 | 14 | No |
| Form 4 — Spirit | `boss_paburu_spirit.png` | 8 | 10 | Yes |
| Form 4 — Spirit Surge | `boss_paburu_spirit_surge.png` | 12 | 14 | No |
| Hurt | `boss_paburu_hurt.png` | 4 | 12 | No |
| Death | `boss_paburu_transcend.png` | 20 | 8 | No |

**Sprite sizes:**  
- Form 1: 64×64 px  
- Form 2: 56×72 px  
- Form 3: 32×32 px (spheres)  
- Form 4: 64×80 px

---

### 6.3 Form 1 — "La Cabeza de Piedra" (Health: 20 → 15)

**Visual:** An enormous stone head — carved green stone, pre-Columbian style. Eyes closed. It rests on the cemetery ground, slightly embedded. When the battle begins, the eyes open: glowing green.

**Movement:** Stationary. The stone head does not move horizontally. It can tilt slightly left and right (visual, ±8px animation).

**Attack Patterns:**

| Pattern | Trigger | Description |
|---|---|---|
| `STONE_SPIT` | Every 4 seconds | Spits stone projectiles in an arc (3 projectiles, spread 15° apart). Damage: 0.5 hearts each. |
| `EYE_BEAM` | Every 8 seconds | Fires a horizontal beam from both eyes simultaneously. Beam is 8px tall, travels at 200px/s. Damage: 1.0 heart. |
<!-- diseno-pendiente -->
| `GROUND_SLAM` | Every 10 seconds | Causes screen shake (camera offset oscillates ±4px for 0.5s). Fissure HazardZones appear at 3 random X positions (24px wide, full height). Damage: 0.5 hearts. Duration: 2 seconds. |
<!-- /diseno-pendiente -->

**Visual Effect (Unit V):**  
`ColorTools.apply_tint(stone_surface, (0, 120, 40))` — the stone head has a permanent green spectral tint, reinforcing the cemetery supernatural atmosphere.

**Phase Transition Narrative:**  
When reduced to 15 hearts: the stone head cracks. The three spirit silhouettes from Stage 4-1 (deer, serpent, hawk) emerge from the cracks and flow into Paburu's form. The stone shell falls away. Form 2 emerges.

---

### 6.4 Form 2 — "La Máscara Espectral" (Health: 15 → 10)

**Visual:** A towering spectral figure — the outline of a shaman, made entirely of green energy. Where the face would be: a massive floating Tilawa mask, green and translucent. The mask is the damage point — the body outline is invulnerable.

**Movement Type:** Slow floating drift — vertical sine wave (amplitude: 20px, frequency: 0.3 Hz) while moving horizontally at 40px/s.

**Damage Point:** Only the mask (a 40×40px hurtbox centered on the mask sprite) takes damage. The body outline does not register hits.

**Attack Patterns:**

| Pattern | Trigger | Description |
|---|---|---|
| `SPIRIT_WAVE` | Every 5 seconds | Sends a wave of spectral energy along the floor (crouching avoids it) OR along the ceiling (jumping avoids it). Alternates. Damage: 0.5 hearts. |
<!-- diseno-pendiente -->
| `SUMMON_ECHOES` | Every 12 seconds | Summons spectral copies of the three defeated bosses (venado echo, serpiente echo, gavilán echo) — they each perform one attack then dissipate. Echo damage: 50% of original. |
<!-- /diseno-pendiente -->
| `MASK_PULSE` | Every 7 seconds | The mask releases a circular shockwave. Damage within 80px: 0.75 hearts. |

**Visual Effect (Unit VII):**  
`FilterTools.adjust_brightness(mask_surface, factor = 0.8 + 0.4 * sin(elapsed_time * 3))` applied every frame — the mask pulses with a breathing glow effect.

**Spirit Echoes:**  
The three echoes are lightweight entity instances using the same sprites as the defeated bosses but with:
- `set_alpha(120)` — semi-transparent
- 50% of original attack damage
- Single attack then auto-destroy

---

### 6.5 Form 3 — "La Reliquia" (Health: 10 → 5) — Random Phase
<!-- diseno-pendiente -->

**Visual Transition:**
1. Spectral mask form dissolves
2. The Gold Nugget (La Pepita) and The Pearl (La Perla) fly into the arena — previously held by John and Jin
3. Paburu's hand catches them
4. He puts on the mask
5. **At this point, the game randomly selects Form 3A or Form 3B**

The random selection is seeded per-session (not per-attempt). The player learns which form to expect through experience.

---

#### Form 3A — "La Pepita" (Gold Sphere) — Offensive

**Visual:** The mask transforms into a glowing golden sphere (32×32 px). Fast, erratic.

**Movement Type:** Aggressive pursuit. Uses `vec2_normalize()` toward player at 120px/s, with a jitter applied every 0.5 seconds (random direction offset ±30°).

**Characteristics:**
- Purely offensive — no stationary attacks
- Moves constantly and fast
- Contact damage: 1.0 heart

**Attack Patterns:**

| Pattern | Description |
|---|---|
| `GOLD_RUSH` | Accelerates to 240px/s for 0.8 seconds every 5 seconds |
| `GOLD_BURST` | At health multiples of 1.0: releases 8 gold orb projectiles in all directions (radial spread). Each: 0.25 hearts |
| `RICOCHET` | Gold orb bounces off arena walls (reflects velocity vector on wall contact). Remains fast. |

**Academic Note (Unit II):** The bounce off walls is a direct application of vector reflection: `velocity = velocity - 2 * dot(velocity, normal) * normal`. This is documented in the source code as a Unit II illustration.

---

#### Form 3B — "La Perla" (Black Sphere) — Defensive

**Visual:** The mask transforms into a deep black sphere (32×32 px), slow, methodical.

**Movement Type:** Slowly orbits the arena center at radius 64px. Speed: 0.3 radians/second.

**Characteristics:**
- Purely defensive — rarely approaches the player
- Generates traps and area denial
- Contact damage: 0.5 hearts

**Attack Patterns:**

| Pattern | Description |
|---|---|
| `DARK_FIELD` | Places a 48×48 slow zone on the ground (player speed halved while inside). Lasts 8 seconds. Places up to 3 simultaneously. |
| `PEARL_VOLLEY` | Fires 3 slow-moving black orbs in a spread toward the player. Each: 0.5 hearts. Orbs persist for 6 seconds (long range). |
| `PULL` | Every 10 seconds: draws the player toward the sphere 120px using a gravitational force (velocity += normalize(sphere_pos - player_pos) * 80 * dt for 1 second). |

**Academic Note (Unit II — Gravity-Pull Implementation):**  
The PULL attack directly implements a simplified gravitational attraction: `attraction_vector = normalize(paburu_pos - player_pos) * G_CONSTANT`. This is documented inline as Unit II vector mathematics.

---

<!-- /diseno-pendiente -->
### 6.6 Form 4 — "El Espíritu del Shaman" (Health: 5 → 0)

**Transition Narrative:**
1. The sphere (gold or black) slowly dissolves
2. A tall, ancient figure materializes — Paburu's true spirit form
3. He looks at John and Jin for a long moment
4. Then he raises his hand — and the final battle begins

**Visual:** A tall, thin spectral figure. Robes made of flowing light. Ancient face — peaceful but immense. Eyes glow white. Hands glow with alternating gold and pearl light.

**Movement Type:** Slow vertical float — rises and descends in a sine pattern (amplitude: 32px, frequency: 0.2 Hz). Moves horizontally very slowly (20px/s), drifting.

**Health:** 5 hearts. Every hit staggers him slightly (brief float pause animation).

**Attack Patterns:**

| Pattern | Trigger | Description |
|---|---|---|
| `RELIC_SURGE` | Every 6 seconds | Both relics (pepita and perla) orbit Paburu and release simultaneous outward bursts — gold orbs (fast, few) and black orbs (slow, many). Gold: 0.5 hearts, Black: 0.25 hearts. |
| `SPIRIT_FORM` | Every 10 seconds | Paburu becomes momentarily intangible — hurtbox deactivates for 1.5 seconds. Continues releasing attacks during intangibility. |
| `ANCIENT_CALL` | Every 15 seconds | All three spirit echoes (venado, serpiente, gavilán) appear simultaneously for 3 seconds and each perform one attack. Then dissipate. |
| `CONVERGENCE` | At 2 hearts remaining | One-time attack: both relics converge on the player. Player has 2 seconds warning (relics telegraph by orbiting toward player). If hit: 2.0 hearts (heavy). Can be avoided by moving to extreme left or right edge. |

**Visual Effect (Unit VII + Unit VIII — Combined Academic Application):**
- `FilterTools.sobel_edge(boss_surface)` blended at alpha=60 — spirit outline reinforcement
- `VisionTools.threshold_binary(screen_region_around_boss, 180)` used in Stage 4-2 as a student exercise (in Stage README): identifying the "active zone" around Paburu to predict attack patterns

---

### 6.7 Paburu Defeat Sequence

1. At 0 health: Paburu's spirit form does not fall — it rises upward
2. The relics (pepita and perla) fly toward John and Jin respectively
3. Paburu spreads his arms — a long hold (4 seconds of animation)
4. The three spirit guardians (venado, serpiente, gavilán) appear one final time — and bow to Paburu
5. Paburu bows back — and dissolves into golden light
6. The cemetery goes quiet. The screen fades to white.
7. End sequence / credits begin

---

## 7. Boss Academic Summary

| Boss | Key Units | Primary Framework APIs | Player Takeaway |
|---|---|---|---|
| El Venado Sagrado | III, VII | `CurveTools.bezier`, `FilterTools.sobel_edge` | Curve projectiles, Sobel aura |
| El Rey Terciopelo | III, V, IX | `CurveTools.catmull_rom`, `ColorTools.apply_tint` | Multi-body phase, tint effect |
| El Gavilán Camionero | II, III, V, VII, IX | Circular parametric, `FilterTools.gaussian_blur`, `FilterTools.canny_edge` | Circular orbit, blur glow, Canny fracture |
| El Gran Shaman Paburu | II, V, VII, VIII | `ColorTools.apply_tint`, `FilterTools.adjust_brightness`, `VisionTools.threshold_binary` | Vector reflection, breathing glow, binary vision |

---

## 8. Boss Framework Integration

### 8.1 Required Files

**Corrected per `77_SYLLABUS_ALIGNMENT_AUDIT.md` §2.A.6.** Paths use the `src/` prefix; boss implementation files live in the individually-assigned student folder under `src/stages/`, or under `src/stages/stage0/` siblings if professor-owned (unclaimed).

| File | Description | Typical Owner |
|---|---|---|
| `src/framework/entities/boss_base.py` | `BossBase` class — phase manager, health bar event | Professor (always) |
| `src/stages/boss_venado/boss_venado.py` | El Venado Sagrado implementation | Assigned student, or professor if unclaimed |
| `src/stages/boss_rey/boss_rey.py` | El Rey Terciopelo implementation | Assigned student, or professor if unclaimed |
| `src/stages/stage3_4_boss_gavilan/boss_gavilan.py` | El Gavilán Camionero Mascarero | Assigned student, or professor if unclaimed |
| `src/stages/boss_paburu/boss_paburu.py` | El Gran Shaman Paburu (4 forms) | Professor (Final Boss is not assigned to a single student) |

### 8.2 Required TMX Objects

Each boss stage TMX must contain:
- `BossSpawn` object at the boss entry point
- `CameraLock` covering the entire boss arena (lock_x=true, lock_y=true)
- No `NextTrigger` — boss stages complete via `STAGE_COMPLETE` event emitted by the boss death sequence

### 8.3 HUD Integration

On boss stage entry:
- Standard timer is hidden
- Boss health bar appears (bottom of screen)
- Boss name displayed in the bar
- `BOSS_PHASE_CHANGED` event updates the phase indicator and re-fills the bar segment


---
## 🔗 Documentos Relacionados

- [[44_BOSS_RUSH_MODE.md|Boss Rush Mode]]
- [[05_ENEMY_SPEC.md|Enemy Specification]]
