---
document_id: "LOI-SWIMMING-045"
title: "Legacy of InFest — Swimming Mechanics Specification"
aliases: ["Swimming Spec"]
tags: ["swimming", "mechanics", "player"]
description: "Swimming mechanics"
source: "docs/45_SWIMMING_SPEC.md"
date_processed: "2026-07-14"
---

# Legacy of InFest — Swimming Mechanics Specification

**Document ID:** LOI-SWIMMING-045
**Version:** 1.0.0
**Status:** Official
**Audience:** Professor, Teaching Assistants, Students, AI coding assistants

---

## 1. Overview

Swimming is a player state (`SwimmingState` in `src/framework/entities/states/swim.py`) that activates when the player enters water zones. It provides buoyancy, reduced gravity, slower horizontal movement, and swim-jump mechanics. Bubbles are emitted during swimming for visual feedback.

---

## 2. Physics

| Property | Value |
|----------|-------|
| Gravity modifier | 0.3× normal |
| Max vertical speed | −60 px/s (rise), +120 px/s (sink) |
| Horizontal acceleration | 60 px/s² |
| Max horizontal speed | ±120 px/s |
| Horizontal deceleration | 0.9× multiplier/frame |
| Swim jump velocity | −120 px/s |
| Max swim jumps | 1 |
| Swim-dive (crouch) | +200 px/s² |
| Surface eject velocity | −200 px/s |
| Bubble emission period | 0.3 s |

---

## 3. State Transitions

- **Enter:** Player overlaps a water zone → state changes to `SWIMMING`. Vertical velocity is zeroed on entry; horizontal velocity is halved.
- **Exit:** Player leaves water zone → transitions to appropriate ground/air state.
- **Surface Y:** Recorded at entry (`player.y − 16`), used for surface visual effects.
- **Surface eject:** If the player rises above `surface_y − 8` px, they are ejected upward at −200 px/s into `JUMPING`.
- **Grounding:** Touching ground transitions to `IDLE`.

---

## 4. Bubble Particles

Bubble timer spawns visual bubble particles at regular intervals while swimming. Implemented inline in `SwimmingState.update()`: every 0.3 s the state emits `Events.VFX_BUBBLE` at the player position; `StageScene` subscribes and spawns `HitEffects.BUBBLE` from the `"bubble"` emitter.

---

## 5. Implementation Status

**File:** `src/framework/entities/states/swim.py`
**Class:** `SwimmingState(PlayerStateBase)` with `PlayerState.SWIMMING`
**Status:** ✅ Complete — swimming physics, buoyancy, bubble timer, surface eject
**Missing:** No dedicated water zone detection; depends on stage collision system to trigger state change


--- Traducción al Español ---

## Especificación de Natación

### Descripción
Mecánica de natación para el jugador en zonas de agua.

### Características
- Movimiento vertical y horizontal en agua
- Flotabilidad y gravedad reducida
- Transición entrada/salida del agua
- Animaciones de natación

Para la especificación completa con atributos físicos y estados, consultar el documento original en inglés.


---
## 🔗 Documentos Relacionados

- [[04_PLAYER_SPEC.md|Player Specification]]
- [[47_WATER_EFFECT.md|Water Effect]]
