---
document_id: "LOI-TRANSITION-048"
title: "Legacy of InFest — Screen Transitions Specification"
aliases: ["Screen Transitions"]
tags: ["transition", "screen", "vfx"]
description: "Fade/wipe/slide/circle transitions"
source: "docs/48_SCREEN_TRANSITIONS.md"
date_processed: "2026-07-14"
---

# Legacy of InFest — Screen Transitions Specification

**Document ID:** LOI-TRANSITIONS-048
**Version:** 1.0.0
**Status:** Official
**Audience:** Professor, Teaching Assistants, Students, AI coding assistants

---

## 1. Overview

The Screen Transitions system provides visual effects between scene changes.

> **AUD-168.** Este documento describía dos capas, y la de abajo —un módulo
> `src/engine/scene/transitions.py` con cuatro clases de efecto— **fue retirada
> en AUD-111** por ser código muerto: cinco clases, cero usos en todo el
> repositorio, ni siquiera en pruebas, compitiendo por el nombre con el
> controlador que `SceneManager` sí instancia. El documento se quedó
> describiendo la arquitectura anterior, con recuento de líneas incluido.

Hoy hay **una sola capa**: `src/engine/scenes/transition_manager.py`, un
controlador con cuatro modos (fade, wipe, slide, circle) que se eligen por el
método que se llama — `start_fade_in`, `start_wipe`, `start_slide`,
`start_circle`. Las secciones 2.x de abajo describen esos modos, no clases
separadas.

---

## 2. Transition Types

### 2.1 FadeTransition
Fades to/from a solid color (default black) over duration. Parameter: `fade_in` boolean, `color` tint.

### 2.2 WipeTransition
Horizontal wipe revealing the new scene. Direction: `left_to_right` / `right_to_left`. Requires a snapshot of the old surface.

### 2.3 SlideTransition
Slides the old scene out in a direction (`left`, `right`, `up`, `down`) to reveal the new scene beneath.

### 2.4 CircleTransition
Expanding or contracting circle wipe centered on screen.

---

## 3. TransitionManager

Single controller that wraps all transition types with a unified API.

| Method | Duration | Details |
|--------|----------|---------|
| `start_fade_out(dur)` | 0.35s | Fade to black |
| `start_fade_in(dur)` | 0.35s | Fade from black |
| `start_wipe(dir, dur)` | 0.4s | Wipe reveal |
| `start_slide(dir, dur)` | 0.4s | Slide out |
| `start_circle(expanding, dur)` | 0.4s | Circle wipe |

The `update(dt)` method drives the animation; `draw(surface)` renders the overlay. Properties `active` and `finished` report state.

---

## 4. Usage

Called by `SceneManager` before/after scene swaps:
```python
tm.start_fade_out()
# ... swap scene ...
tm.start_fade_in()
```

---

## 5. Implementation Status

**Files:**
- `src/engine/scenes/transition_manager.py` (164 lines) — el controlador, con
  los cuatro modos dentro

**Status:** ✅ Complete — fade, wipe, slide, circle transitions

> **AUD-168.** Esta lista incluía un segundo fichero «(199 lines) — 4
> transition effect classes» que llevaba retirado desde AUD-111. Un recuento de
> líneas es exactamente la clase de dato que hace creer que alguien lo miró.


--- Traducción al Español ---

## Transiciones de Pantalla

### Descripción
Sistema de transiciones entre escenas: fundido, barrido, deslizamiento y círculo.

### Tipos de Transición
- Fundido (Fade) — entrada/salida en negro
- Barrido (Wipe) — barrido horizontal o vertical
- Deslizamiento (Slide) — diapositiva desde un borde
- Círculo (Circle) — revelado circular

Para la especificación completa de duraciones y easing, consultar el documento original en inglés.


---
## 🔗 Documentos Relacionados

- [[42_CUTSCENE_SYSTEM.md|Cutscene System]]
- [[46_FOG_OF_WAR.md|Fog of War]]
