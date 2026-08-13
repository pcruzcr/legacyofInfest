---
document_id: "LOI-LABS-LAB03"
title: "Laboratorio 3: visión y reconocimiento de patrones (Unidad VIII)"
aliases: ["Lab03", "lab03"]
tags: ["laboratorio", "academico", "ejercicio"]
description: "Documento de laboratorios: lab03"
source: "docs/labs/lab03.md"
date_processed: "2026-08-13"
---

# Laboratorio 3: visión y reconocimiento de patrones (Unidad VIII)

**Objetivo:** aplicar técnicas de procesamiento de imágenes y reconocimiento de patrones usando VisionDemoScene y PatternDemoScene.

## Tareas

### Tarea 1 — Umbralización y morfología (30 min)
1. Abrir **VisionDemoScene** (Unidad VIII desde el menú de demos)
2. Cambiar al modo THRESHOLD y ajustar el valor de umbral
3. Observar cómo cambian las máscaras binarias
4. Cambiar a los modos ERODE y DILATE — ¿cuál es el efecto del tamaño de kernel?
5. Registrar el umbral óptimo para aislar el sprite del jugador del fondo

### Tarea 2 — Componentes conectados (30 min)
1. En **VisionDemoScene**, cambiar al modo COMPONENTS
2. Contar el número de regiones conectadas detectadas
3. Cambiar al modo REGIONS y analizar las propiedades de la región más grande (área, centroide, excentricidad)
4. Explicar: ¿por qué el etiquetado de componentes conectados asigna colores distintos a regiones distintas?

### Tarea 3 — Tubería de clasificación (30 min)
1. Abrir **PatternDemoScene** (Unidad IX desde el menú de demos)
2. Observar el modo INFERENCE — ¿qué clase se predice?
3. Cambiar al modo FEATURE_COMPARE y mover el rectángulo de análisis
4. ¿Cómo cambia la muestra de entrenamiento más cercana al moverse sobre distintas partes de la imagen fuente?
5. Cambiar al modo PIPELINE y rastrear la tubería de clasificación completa

## Entregables
- Capturas mostrando máscaras umbralizadas, componentes conectados, y resultados de inferencia
- El valor de umbral óptimo encontrado en la Tarea 1
- Una explicación breve de la tubería de clasificación (fuente → preprocesamiento → extracción de características → clasificación)
