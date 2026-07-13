# Legacy of InFest — Screen Transitions Specification

**Document ID:** LOI-TRANSITIONS-048
**Version:** 1.0.0
**Status:** Official
**Audience:** Professor, Teaching Assistants, Students, AI coding assistants

---

## 1. Overview

The Screen Transitions system provides visual effects between scene changes. It has two layers:
1. **Low-level:** `src/engine/scene/transitions.py` — individual transition effect classes
2. **High-level:** `src/engine/scenes/transition_manager.py` — orchestration controller

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
- `src/engine/scene/transitions.py` (199 lines) — 4 transition effect classes
- `src/engine/scenes/transition_manager.py` (164 lines) — orchestration controller
**Status:** ✅ Complete — fade, wipe, slide, circle transitions


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
