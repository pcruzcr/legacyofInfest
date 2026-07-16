---
document_id: "LOI-LABS-LAB02"
title: "Lab 2: Interpolation & Animation (Unit V)"
aliases: ["Lab02", "lab02"]
tags: ["lab", "academic", "exercise"]
description: "Labs document: lab02"
source: "docs/docs\labs/lab02.md"
date_processed: "2026-07-14"
---

# Lab 2: Interpolation & Animation (Unit V)

**Objective:** Master easing functions and keyframe animation using the InterpolationLabScene.

## Tasks

### Task 1 — Easing Functions (20 min)
1. Open **InterpolationLabScene** (Unit III/IV from the demo menu)
2. Cycle through each of the 10 easing functions using UP/DOWN
3. For each function, note:
   - Where does it accelerate (beginning, end, both)?
   - Does it overshoot the target?
   - Does it bounce?

### Task 2 — Keyframe Animation (30 min)
1. Switch to KEYFRAME_ANIM mode
2. Set 3 keyframes with different positions
3. Toggle auto-animation with SPACE
4. Change the easing function between keyframes and observe the result

### Task 3 — Custom Easing (40 min)
1. Review the math_utils.py implementations in `src/engine/utils/math_utils.py`
2. Implement an `ease_in_out_back` function that overshoots slightly at both ends
3. Test it in the InterpolationLabScene using the custom slot

## Deliverables
- Screenshots of 3 different easing functions in action
- Your custom easing function code
- A comparison of ease_in_quad vs ease_out_elastic (when is each appropriate?)


--- Traducción al Español ---

## Laboratorio 2: Interpolación y Animación (Unidad V)

**Objetivo:** Dominar funciones de easing y animación por fotogramas clave.

### Tareas
1. **Funciones de Easing** — Explorar las 10 funciones de easing
2. **Animación por Fotogramas Clave** — Configurar 3 fotogramas clave con diferentes easing
3. **Easing Personalizado** — Implementar función ease_in_out_back

### Entregables
- Capturas de 3 funciones de easing diferentes
- Código de función de easing personalizada
- Comparación de ease_in_quad vs ease_out_elastic
