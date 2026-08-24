---
document_id: "LOI-ASGN03-032B"
title: "Entrega 3: finalización de ejercicios de laboratorio"
aliases: ["Entrega 3: ejercicios de laboratorio", "Assignment 3: Lab Exercises"]
tags: ["entrega", "laboratorio", "ejercicios", "academico"]
description: "Entrega de ejercicios de laboratorio"
source: "docs/32_ASSIGNMENT_03_LAB_EXERCISES.md"
date_processed: "2026-08-13"
---

# Entrega 3: finalización de ejercicios de laboratorio

**Entrega:** continua, a lo largo del trimestre | **Instrumento:** Prácticas de laboratorio (ver `21_COURSE_SCHEDULE.md` §4, `27_ACADEMIC_RUBRICS.md` §3) | **Unidades:** II–VIII

> **AUD-455.** Traduce el documento. El resumen en español que traía al
> final no correspondía a este tema — era el contenido (mal pegado) de la
> entrega de reconocimiento de patrones. Se sustituye por un resumen
> fiel al contenido real del documento (ejercicios de laboratorio de las
> Unidades II–VIII).

## Objetivo

Completar los ejercicios de laboratorio interactivos incrustados en el juego. Cada laboratorio pone a prueba un concepto central de las unidades del curso — ver `15_ACADEMIC_DEMO_SCENES.md` para la especificación completa de cada escena de laboratorio.

## Calendario de laboratorios

| Laboratorio | Unidad |
|---|---|
| VectorLabScene | II — Vectores |
| TransformLabScene | II — Transformaciones |
| CurveEditorScene | III — Curvas |
| InterpolationLabScene | III/IV — Interpolación |
| ColorTheoryScene | V — Espacios de color |
| NoiseLabScene | V/VIII — Ruido |
| CollisionLabScene | VI — Colisión |
| FilterDemoScene | VII — Filtros |
| VisionDemoScene | VIII — Visión |

La distribución exacta entre las Clases 2–9 está en `21_COURSE_SCHEDULE.md` §4.

## Requisitos

Para cada laboratorio, el estudiante debe:

1. **Abrir el laboratorio** desde el Menú de Demos del juego
2. **Explorar todos los modos** — ciclar con TAB
3. **Responder las preguntas del quiz** — el sistema de quiz (`QuizManager`, `src/engine/scenes/quiz_system.py`) registra las respuestas
4. **Demostrar comprensión** — cada laboratorio registra su completitud cuando se responden todas las preguntas

### Criterios de completitud

Un laboratorio se marca completo cuando:
- El estudiante ha recorrido todos los modos al menos una vez
- Las preguntas del quiz están respondidas (50%+ correctas)
- Se guardó una captura (tecla S en cualquier modo)

## Calificación

- Cada laboratorio se califica de forma independiente
- Laboratorios completados = puntos obtenidos (sin crédito parcial por laboratorios incompletos)
- Laboratorios tardíos: -20% por semana de retraso

## Ejemplos de preguntas de quiz por laboratorio

### Laboratorio de vectores
1. ¿Qué devuelve `Vector2.normalize()`?
2. ¿Cuál es el producto punto de vectores perpendiculares?
3. ¿Qué curva de interpolación usa 4 puntos de control?
4. ¿Qué devuelve `distance()`?

### Teoría del color
1. ¿Cuáles son los 3 canales de HSV?
2. ¿Qué combina la mezcla alfa?
3. ¿Cuál es la fórmula de conversión a escala de grises?

### Laboratorio de filtros
1. ¿Qué kernel de convolución detecta bordes?
2. ¿Qué hace un kernel de desenfoque de caja?
3. ¿Qué calcula el operador de Sobel?

### Editor de curvas
1. ¿Qué curva interpola a través de todos los puntos de control?
2. ¿Qué algoritmo evalúa las curvas de Bézier?
3. ¿Qué es un peso de NURBS?

## Verificar el progreso

```bash
# Comprobar el progreso dentro del juego:
# Abrir el Panel de Progreso desde el Menú de Demos

# O desde la línea de comandos:
python -c "from src.engine.scenes.progress_scene import ProgressScene; print('Progreso comprobado')"
```

---
## 🔗 Documentos relacionados

- [[15_ACADEMIC_DEMO_SCENES.md|Escenas de demostración académica]]
- [[27_ACADEMIC_RUBRICS.md|Rúbricas académicas]]
