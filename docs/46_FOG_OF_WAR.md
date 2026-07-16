---
document_id: "LOI-FOG-046"
title: "Legacy of InFest — Fog of War Specification"
aliases: ["Fog of War"]
tags: ["fog", "war", "vfx", "visibility"]
description: "Fog of war overlay"
source: "docs/46_FOG_OF_WAR.md"
date_processed: "2026-07-14"
---

# Legacy of InFest — Fog of War Specification

**Document ID:** LOI-FOG-046
**Version:** 1.0.0
**Status:** Official
**Audience:** Professor, Teaching Assistants, Students, AI coding assistants

---

## 1. Overview

The Fog of War (`src/framework/vfx/fog_of_war.py`) is a full-screen black overlay with alpha holes revealed around player and enemy positions. It hides unexplored areas and gradually reveals the map as the player moves. The overlay is drawn in screen space and moves with the camera.

---

## 2. Architecture

### 2.1 FogOfWar
- **Overlay:** Full-screen `Surface` at (0, 0, 0, 220) alpha
- **Mask:** A transparent `Surface` with circles drawn at revealed positions (full alpha)
- **Composite:** `mask` is subtracted from `overlay` via `BLEND_RGBA_SUB`, creating transparent holes

### 2.2 Parameters
- `radius` — default 80px reveal radius
- `hardness` — edge softness factor (reserved for future Gaussian falloff)

---

## 3. API

| Method | Description |
|--------|-------------|
| `clear()` | Reset all revealed areas |
| `reveal(x, y)` | Add a reveal point at world coordinates |
| `reveal_all(points)` | Batch-add reveal points |
| `update(dt)` | No-op placeholder for future animated fading |
| `draw(surface, offset)` | Render fog overlay, transforming world points to screen |

---

## 4. Implementation Status

**File:** `src/framework/vfx/fog_of_war.py` (49 lines)
**Status:** ✅ Complete — screen-space overlay with alpha holes
**Missing:** No perma-reveal (explored areas stay black when off-screen); no smooth edge falloff


--- Traducción al Español ---

## Niebla de Guerra

### Descripción
Superposición de niebla que oculta áreas no exploradas del mapa.

### Características
- Niebla negra con agujeros revelados
- Revelado progresivo por movimiento del jugador
- Persistencia entre visitas
- Efecto visual de descubrimiento

Para la especificación completa de la implementación, consultar el documento original en inglés.


---
## 🔗 Documentos Relacionados

- [[47_WATER_EFFECT.md|Water Effect]]
- [[48_SCREEN_TRANSITIONS.md|Screen Transitions]]
