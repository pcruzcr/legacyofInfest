---
document_id: "LOI-LABS-LAB02"
title: "Laboratorio 2: interpolación y animación (Unidad V)"
aliases: ["Lab02", "lab02"]
tags: ["laboratorio", "academico", "ejercicio"]
description: "Documento de laboratorios: lab02"
source: "docs/labs/lab02.md"
date_processed: "2026-08-13"
---

# Laboratorio 2: interpolación y animación (Unidad V)

**Objetivo:** dominar las funciones de easing y la animación por fotogramas clave usando InterpolationLabScene.

## Tareas

### Tarea 1 — Funciones de easing (20 min)
1. Abrir **InterpolationLabScene** (Unidad III/IV desde el menú de demos)
2. Recorrer cada una de las 10 funciones de easing con ARRIBA/ABAJO
3. Para cada función, anotar:
   - ¿Dónde acelera (al inicio, al final, en ambos)?
   - ¿Se pasa del objetivo?
   - ¿Rebota?

### Tarea 2 — Animación por fotogramas clave (30 min)
1. Cambiar al modo KEYFRAME_ANIM
2. Fijar 3 fotogramas clave con posiciones distintas
3. Alternar la auto-animación con ESPACIO
4. Cambiar la función de easing entre fotogramas clave y observar el resultado

### Tarea 3 — Easing propio (40 min)
1. Revisar las implementaciones de `math_utils.py` en `src/engine/utils/math_utils.py`
2. Implementar una función `ease_in_out_back` que se pase ligeramente en ambos extremos
3. Probarla en InterpolationLabScene usando la ranura personalizada

## Entregables
- Capturas de 3 funciones de easing distintas en acción
- El código de la función de easing propia
- Una comparación de ease_in_quad frente a ease_out_elastic (¿cuándo es apropiada cada una?)
