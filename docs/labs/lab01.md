---
document_id: "LOI-LABS-LAB01"
title: "Laboratorio 1: vectores y curvas (Unidad II)"
aliases: ["Lab01", "lab01"]
tags: ["laboratorio", "academico", "ejercicio"]
description: "Documento de laboratorios: lab01"
source: "docs/labs/lab01.md"
date_processed: "2026-08-13"
---

# Laboratorio 1: vectores y curvas (Unidad II)

**Objetivo:** implementar operaciones vectoriales y curvas de Bézier en VectorLabScene y CurveEditorScene.

## Tareas

### Tarea 1 — Aritmética vectorial (30 min)
1. Abrir **VectorLabScene** (Unidad II desde el menú de demos)
2. Cambiar al modo CHASE con la tecla TAB
3. Observar cómo se calcula el vector de persecución desde la posición del jugador hasta el objetivo
4. Modificar el comportamiento de persecución para usar un vector de dirección normalizado multiplicado por una velocidad fija

### Tarea 2 — Curvas de Bézier (30 min)
1. Abrir **CurveEditorScene** (Unidad III desde el menú de demos)
2. Crear una curva de Bézier cuadrática con 3 puntos de control
3. Alternar la visualización de de Casteljau con la tecla D
4. Observar cómo la interpolación lineal recursiva produce la curva

### Tarea 3 — Ruta Catmull-Rom (30 min)
1. En **CurveEditorScene**, cambiar al modo CATMULL_ROM
2. Colocar 5+ puntos de control para crear una ruta que pase por todos ellos
3. Notar cómo la interpolación Catmull-Rom pasa por todos los puntos de control (a diferencia de Bézier)

## Entregables
- Capturas mostrando el comportamiento de persecución vectorial y la curva de Bézier
- Una explicación breve (2-3 oraciones) de cómo funciona el algoritmo de de Casteljau
