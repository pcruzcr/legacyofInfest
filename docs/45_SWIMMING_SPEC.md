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

Swimming is a player state (`SwimmingState` in `src/framework/entities/player_states.py`) that activates when the player enters water zones. It provides buoyancy, reduced gravity, slower horizontal movement, and swim-jump mechanics. Bubbles are emitted during swimming for visual feedback.

---

## 2. Physics

| Property | Value |
|----------|-------|
| Gravity modifier | 0.3× normal |
| Max vertical speed | ±80 px/s |
| Horizontal acceleration | 60 px/s² |
| Max horizontal speed | ±120 px/s |
| Horizontal deceleration | 0.9× multiplier/frame |
| Swim jump velocity | −120 px/s |
| Max swim jumps | 1 |

---

## 3. State Transitions

- **Enter:** Player overlaps a water zone → state changes to `SWIMMING`. Velocity is halved on entry.
- **Exit:** Player leaves water zone → transitions to appropriate ground/air state.
- **Surface Y:** Recorded at entry (`player.y − 16`), used for surface visual effects.

---

## 4. Bubble Particles

Bubble timer spawns visual bubble particles at regular intervals while swimming. Implemented inline in `SwimmingState.update()`.

---

## 5. Implementation Status

**File:** `src/framework/entities/player_states.py:1540-1607`
**Class:** `SwimmingState(PlayerStateBase)` with `PlayerState.SWIMMING`
**Status:** ✅ Complete — swimming physics, buoyancy, bubble timer
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
