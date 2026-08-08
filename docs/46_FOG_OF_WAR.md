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
- **Mask:** A radial-gradient disc (`_construir_mascara`) blitted at every
  revealed position. Built in the constructor and **rebuilt only when the
  breathing profile changes** (AUD-338) — the same phase draws the same mask
- **Composite:** `mask` is subtracted from `overlay` via `BLEND_RGBA_SUB`, creating soft-edged transparent holes

The mask peaks at the veil's **current** alpha (220 at rest), not 255, on
purpose: `BLEND_RGBA_SUB` saturates at zero, so any alpha above the veil's
own would reveal exactly like it and the first stretch of the gradient would
be lost to the clamp. Matching them puts the whole falloff inside the visible
range. When the veil breathes, the mask is rebuilt with the new peak so the
profile stays exact.

### 2.2 Parameters
- `radius` — default 80px reveal radius
- `hardness` — default 0.6. Fraction of the radius that stays **fully**
  revealed; the remaining `1 - hardness` is the band where the veil returns,
  following a smoothstep (`3t² - 2t³`) that reaches zero with zero slope at
  both seams. `hardness = 1.0` reproduces the old hard-edged disc;
  `hardness = 0.0` fades from the very centre. Values are clamped to [0, 1].
- `animado` — default `True` (AUD-338). With `False`, the veil is the static
  overlay of v1.0.0. At phase zero (`t = 0`, no `update()` call yet) the
  animated veil draws **exactly** the static one, so tests and code that
  never call `update()` see no change
- `velocidad` — default 0.15. Breathing cycles per second: one full inhale
  and exhale every ~6.7 s. Clamped to `>= 0` (0 freezes the veil)
- `pulso` — default 3.0. How many pixels the hole radius swells and shrinks
  around `radius`, in sine. Clamped so the hole can never shrink to zero (a
  hole that disappears for an instant is a flicker, not a breath)
- `pulso_del_velo` — default 6.0. How many alpha units the veil darkens and
  lightens, **in antiphase** with the radius: the veil darkens while the
  holes shrink (inhale) and lightens while they grow (exhale). The result is
  clamped to [0, 255]

Measured mask alpha along a radius (`radius = 80`), sampled at fractions of
the radius — reproducible with `_hole_mask` and `pygame.surfarray.pixels_alpha`:

| hardness | 0.0 | 0.25 | 0.50 | 0.60 | 0.75 | 0.90 | 0.99 |
|---|---|---|---|---|---|---|---|
| 0.0 | 220 | 185 | 110 | 77 | 34 | 6 | 0 |
| 0.6 (default) | 220 | 220 | 220 | 220 | 150 | 34 | 0 |
| 1.0 | 220 | 220 | 220 | 220 | 220 | 220 | 220 |

---

## 3. API

| Method | Description |
|--------|-------------|
| `clear()` | Reset all revealed areas |
| `reveal(x, y)` | Add a reveal point at world coordinates |
| `reveal_all(points)` | Batch-add reveal points |
| `update(dt)` | Advance the breathing clock (AUD-338). Without it the veil stays at phase zero — the static behaviour |
| `draw(surface, offset)` | Render fog overlay, transforming world points to screen; rebuilds the mask only when the breathing profile changed |

---

## 4. Implementation Status

**File:** `src/framework/vfx/fog_of_war.py` (133 lines)
**Status:** ✅ Complete — screen-space overlay with soft-edged alpha holes (AUD-198)
**Missing:** No perma-reveal (explored areas stay black when off-screen). `draw()`
iterates over every revealed point and that set is unbounded: measured at
320x180 with `radius = 80`, the cost is linear at roughly 2.7 µs per point —
0.55 ms at 100 points, 6.65 ms at 2000, 10.73 ms at 4000. A moving player adds
about one point per frame, so the overlay eats a third of a 60 fps budget after
half a minute of walking. Tracked separately; not addressed by AUD-198.
**Note:** no TMX declares the `fog_of_war` map property yet, so no shipped
stage currently turns the overlay on.


--- Traducción al Español ---

## Niebla de Guerra

### Descripción
Superposición de niebla que oculta áreas no exploradas del mapa.

### Características
- Niebla negra con agujeros revelados de borde suave
- El agujero cae en degradado radial; `hardness` (0,6 por omisión) marca qué
  fracción del radio queda revelada del todo antes de que empiece la caída
- Revelado progresivo por movimiento del jugador
- Persistencia entre visitas
- Efecto visual de descubrimiento

Para la especificación completa de la implementación, consultar el documento original en inglés.


---
## 🔗 Documentos Relacionados

- [[47_WATER_EFFECT.md|Water Effect]]
- [[48_SCREEN_TRANSITIONS.md|Screen Transitions]]
