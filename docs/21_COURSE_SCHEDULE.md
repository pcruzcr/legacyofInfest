---
document_id: "LOI-SCHEDULE-021"
title: "Legacy of InFest — Calendario del curso"
aliases: ["Calendario del curso", "Course Schedule"]
tags: ["curso", "calendario", "academico"]
description: "11 clases + calendario de Invenio Fest"
source: "docs/21_COURSE_SCHEDULE.md"
date_processed: "2026-08-13"
---

# Legacy of InFest — Calendario del curso

**ID del documento:** LOI-SCHEDULE-021
**Versión:** 1.1.0
**Estado:** Oficial
**Compatibilidad:** Requiere `08_SYLLABUS_MAPPING.md`, `14_PROFESSOR_DELIVERABLE_MATRIX.md`
**Audiencia:** Profesor, estudiantes

> **AUD-455.** Traduce el documento. Quita dos referencias a
> `77_SYLLABUS_ALIGNMENT_AUDIT.md`, un documento que no existe en este
> repositorio (§7 y el Apéndice A); corrige la afirmación de que las
> funciones de easing de `math_utils.py` están "respaldadas por
> `pytweening`" — `pytweening` se retiró del proyecto (AUD-007,
> ver `10_LIBRARIES_AND_DEPENDENCIES.md`) y `math_utils.py` implementa sus
> propias funciones de easing.

---

## 1. Visión general

Computación Gráfica y Procesamiento de Imágenes I (TIIT3002.1) es un curso trimestral que se imparte en **11 clases efectivas de 4 horas cada una**, estructuradas como **2 horas de teoría seguidas de 2 horas de práctica/ejemplos/ejercicios**. Una duodécima sesión queda reservada para **Invenio Fest**, el festival de proyectos grupales interdisciplinarios que se califica por separado de este curso pero recibe un peso del 20% dentro de él (ver Sección 5).

Cada estudiante elige **un** Escenario o Jefe de Legacy of InFest en la Clase 1 y lo desarrolla a lo largo del trimestre a través de tres evaluaciones prácticas acumulativas (Evaluación Práctica I, II, III), culminando en una entrega individual completamente funcional para la Clase 10–11.

---

## 2. Calendario de un vistazo

| Clase | Enfoque teórico (2h) | Enfoque práctico (2h) | Evento de evaluación |
|---|---|---|---|
| 1 | Unidad I — Introducción a gráficas por computadora | Orientación al framework, selección de Escenario/Jefe, configuración del entorno | — |
| 2 | Unidad II — Sistemas de coordenadas y transformaciones | Laboratorios de matemática vectorial + TransformLabScene (Unidad II/III) | Quiz 1 |
| 3 | Unidad II (cont.) — Matrices, coordenadas homogéneas | Ejercicios de transformación de hitbox/hurtbox | Laboratorio 1 |
| 4 | Unidad III — Curvas y modelado geométrico | Ejercicios de rutas Bézier/B-Spline + InterpolationLabScene | Quiz 2 |
| 5 | Unidad IV — Objetos, escenas, capas | Construcción de capas TMX, laboratorios de sprite/escena | **Evaluación Práctica I — Prototipo Funcional** |
| 6 | Unidad V — Color, transparencia, iluminación | Laboratorios de conversión de espacio de color, mezcla alfa | Quiz 3 + Laboratorio 2 |
| 7 | Unidad VI — Texturizado, animación, interacción | Hojas de sprites, easing, laboratorios de colisión | — |
| 8 | Unidad VII — Procesamiento digital de imágenes | Laboratorios de histograma, brillo/contraste, convolución, Sobel/Canny + NoiseLabScene | **Evaluación Práctica II — Vertical Slice** |
| 9 | Unidad VIII — Segmentación y análisis de imágenes | Laboratorios de umbral, Otsu, morfología, análisis de regiones | Quiz 4 + Laboratorio 3 |
| 10 | Unidad IX — Aplicaciones integradoras | Tubería de reconocimiento de patrones, laboratorios de entrenamiento de clasificadores | — |
| 11 | Integración y repaso del curso | Pulido final de escenario/jefe, pruebas de integración | **Evaluación Práctica III — Integración Final** |
| 12 | — | **Invenio Fest** (presentación grupal interdisciplinaria) | **Proyecto Integrador Invenio Fest** |

---

## 3. Detalle clase por clase

### Clase 1 — Fundamentos e inicio del proyecto

**Teoría (2h) — Unidad I: Introducción a gráficas por computadora**
- Evolución histórica de las gráficas por computadora
- Dominios de aplicación
- Sistemas gráficos, hardware y software
- Imágenes raster frente a vectoriales
- Resolución y profundidad de color
- Introducción a la tubería gráfica

**Práctica (2h) — Orientación al framework**
- Recorrido del repositorio: `docs/`, `assets/`, `src/`, `student_templates/`, `main.py`, `requirements.txt`
- Configuración del entorno: entorno virtual, instalación de `requirements.txt`
- Primera ejecución de Stage 0
- **Selección de Escenario/Jefe:** cada estudiante elige individualmente un Escenario o Jefe del catálogo disponible (ver `16_WORLD_DESIGN.md` y `17_BOSS_SPEC.md`). El profesorado registra la selección.
- Introducción al andamiaje de `student_templates/`

**Entregable:** ninguno calificado. Se confirma la asignación de Escenario/Jefe.

---

### Clase 2 — Sistemas de coordenadas y vectores

**Teoría (2h) — Unidad II (parte 1)**
- Sistemas de coordenadas 2D y 3D
- Álgebra vectorial aplicada
- Vectores y matrices

**Práctica (2h)**
- **VectorLabScene** (laboratorio de teoría de la Unidad II): aritmética vectorial interactiva, normalización, producto punto, movimiento de persecución
- Ejercicios de laboratorio usando `src/engine/utils/math_utils.py`: `vec2_normalize`, `vec2_dot`, `vec2_distance`
- Aplicación de matemática vectorial al movimiento de una entidad propia dentro del andamiaje de Escenario/Jefe asignado al estudiante

**Evaluación:** Quiz 1 — conceptos fundamentales de la Unidad I y la Unidad II (vectores, sistemas de coordenadas)

---

### Clase 3 — Transformaciones y coordenadas homogéneas

**Teoría (2h) — Unidad II (parte 2)**
- Traslación, rotación, escalado, reflexión
- Coordenadas homogéneas
- Composición de transformaciones

**Práctica (2h)**
- Ejercicios de transformación de hitbox/hurtbox de local a mundo (ver `04_PLAYER_SPEC.md` §13.4)
- Implementación de matrices de traslación para cajas envolventes de entidades propias

**Evaluación:** Laboratorio 1 (nota de práctica de laboratorio) — transformaciones geométricas aplicadas vía Python

---

### Clase 4 — Curvas y modelado geométrico

**Teoría (2h) — Unidad III**
- Curvas paramétricas
- Polinomios de Bernstein
- Curvas de Bézier
- Curvas B-Spline
- Introducción a NURBS
- Representación de trayectorias

**Práctica (2h)**
- **CurveEditorScene** (laboratorio de teoría de la Unidad III): Bézier, Catmull-Rom, B-Spline interactivos con puntos de control arrastrables
- Ejercicios con `CurveTools.bezier()`, `CurveTools.b_spline()`, `CurveTools.sample_path()`
- Diseño de una ruta de patrulla o trayectoria de proyectil para el Escenario/Jefe asignado al estudiante usando matemática de curvas

**Evaluación:** Quiz 2 — teoría de curvas y base de Bernstein

---

### Clase 5 — Representación de escenas y primera evaluación práctica

**Teoría (2h) — Unidad IV**
- Representación computacional de objetos gráficos
- Escenas y estructuras visuales
- Sprites y elementos gráficos
- Capas y organización visual
- Búferes y framebuffers
- Gestión y optimización básica de recursos gráficos

**Práctica (2h)**
- Construcción de capas TMX para el Escenario asignado al estudiante (o construcción de arena para el Jefe asignado)
- Implementación del ciclo de vida de escena (subclase de `BaseScene`)
- Punto de control de integración: coordenadas, transformaciones, escenario básico, interacción inicial

**Evaluación: Evaluación Práctica I — Prototipo Funcional (15%)**

Demuestra:
- Representación gráfica
- Sistemas de coordenadas
- Transformaciones geométricas
- Curvas básicas

Producto esperado: primer avance funcional del nivel o jefe asignado dentro del proyecto Legacy of InFest.

---

### Clase 6 — Color, transparencia e iluminación

**Teoría (2h) — Unidad V**
- Percepción visual
- Modelos RGB, CMYK, HSV, y HSL
- Conversión entre espacios de color
- Transparencia y composición de imágenes
- Mezcla alfa
- Fundamentos de iluminación computacional
- Modelos básicos de sombreado

**Práctica (2h)**
- **ColorTheoryScene** (laboratorio de teoría de la Unidad V): exploradores interactivos de RGB/HSV/HSL/CMYK, vista de algoritmo paso a paso, demo de mezcla alfa, desafío de emparejamiento de color
- Ejercicios de conversión con `ColorTools` (RGB↔HSV↔HSL↔CMYK)
- Ejercicios de mezcla alfa aplicados a los visuales del Escenario/Jefe asignado al estudiante

**Evaluación:** Quiz 3 — teoría del color y conversión de espacio de color + Laboratorio 2 (nota de práctica de laboratorio) — color e iluminación aplicados vía Python

---

### Clase 7 — Texturizado, animación e interacción

**Teoría (2h) — Unidad VI**
- Texturizado digital
- Mapeo de texturas
- Sprites y hojas de sprites
- Animación computacional
- Interpolación
- Animación basada en transformaciones
- Colisiones básicas
- Interacción entre objetos gráficos

**Práctica (2h)**
- **CollisionLabScene** (laboratorio de teoría de la Unidad VI): colisión AABB interactiva con el bug de Y-primero frente a la resolución correcta de X-primero, plataformas de un solo sentido
- Implementación de animación de hoja de sprites para la entidad propia del estudiante
- Ejercicios de funciones de easing (funciones propias de `math_utils`, sin `pytweening`)
- Ejercicios de colisión AABB e interacción con EventBus

**Evaluación:** ninguna programada formalmente — los ejercicios alimentan la Evaluación Práctica II en la Clase 8.

---

### Clase 8 — Procesamiento digital de imágenes y segunda evaluación práctica

**Teoría (2h) — Unidad VII**
- Adquisición de imágenes
- Histogramas
- Realce de imágenes
- Ajuste de brillo y contraste
- Filtrado espacial
- Convolución
- Reducción de ruido
- Detección de bordes
- Operadores de Sobel y Canny

**Práctica (2h)**
- Ejercicios con `FilterTools`: `compute_histogram`, `adjust_brightness`, `adjust_contrast`, `apply_kernel`, `gaussian_blur`, `sobel_edge`, `canny_edge`
- Uso de `FilterDemoScene` (ver `15_ACADEMIC_DEMO_SCENES.md`) para calibrar parámetros
- Punto de control de integración: curvas, representación de escenas, color/transparencia, texturas/animación

**Evaluación: Evaluación Práctica II — Vertical Slice (15%)**

Demuestra:
- Curvas y modelado
- Representación de escenas
- Color y transparencia
- Texturas y animación
- Representación visual avanzada

Producto esperado: versión intermedia funcional del nivel o jefe asignado.

---

### Clase 9 — Segmentación y análisis de imágenes

**Teoría (2h) — Unidad VIII**
- Segmentación de imágenes
- Umbralización
- Segmentación basada en regiones
- Operaciones morfológicas
- Dilatación y erosión
- Apertura y cierre
- Watershed
- Extracción de características
- Introducción al reconocimiento de patrones

**Práctica (2h)**
- Ejercicios con `VisionTools`: `threshold_binary`, `threshold_otsu`, operaciones morfológicas, `connected_components`, `analyze_regions`, `watershed_segment`
- Uso de `VisionDemoScene` para visualizar resultados de segmentación sobre las superficies del Escenario/Jefe del estudiante

**Evaluación:** Quiz 4 — teoría de segmentación y morfología + Laboratorio 3 (nota de práctica de laboratorio) — segmentación y análisis visual aplicados vía Python

---

### Clase 10 — Aplicaciones integradoras

**Teoría (2h) — Unidad IX**
- Visualización de información
- Interfaces gráficas de usuario
- Sistemas interactivos
- Visión por computadora
- Reconocimiento de patrones
- Aplicaciones empresariales e industriales
- Integración de técnicas de gráficas por computadora y procesamiento de imágenes

**Práctica (2h)**
- Ejercicios con `PatternRecognitionTools`: construcción de dataset, `train()`, `evaluate()`, `save_model()`, `predict()`
- Uso de `PatternDemoScene` para validar modelos entrenados
- Construcción de la tubería de integración final para el Escenario/Jefe asignado al estudiante

**Evaluación:** ninguna programada formalmente — los ejercicios alimentan la Evaluación Práctica III en la Clase 11.

---

### Clase 11 — Integración final y tercera evaluación práctica

**Teoría (2h) — Integración y repaso del curso**
- Repaso transversal: cómo se combinan las Unidades I–IX en una única aplicación funcional
- Revisión de calidad de software, documentación y buenas prácticas de ingeniería (según el programa §11, "Desarrollo de Soluciones Tecnológicas")
- Guía de preparación para la presentación de Invenio Fest

**Práctica (2h)**
- Pulido final y pruebas de integración del Escenario/Jefe asignado al estudiante
- Finalización del README y la documentación técnica
- Revisión entre pares / ensayos de presentación (formativo, sin calificar)

**Evaluación: Evaluación Práctica III — Integración Final (15%)**

Demuestra:
- Procesamiento digital de imágenes
- Segmentación
- Reconocimiento básico de patrones
- Integración de todos los contenidos del curso

Producto esperado: versión final funcional del nivel o jefe asignado dentro de Legacy of InFest.

---

### Clase 12 — Invenio Fest

**Formato:** festival de proyectos grupales interdisciplinarios. No es una sesión de clase regular de este curso; los estudiantes presentan un proyecto grupal ("proyecto semilla macro") que integra contenido de todos los cursos del trimestre.

**Computación Gráfica y Procesamiento de Imágenes I evalúa, desde la perspectiva de este curso:**
- Aplicación efectiva de técnicas visuales
- Calidad de la interfaz gráfica
- Uso apropiado de imágenes y recursos visuales
- Integración de componentes gráficos dentro de la solución
- Contribución individual al proyecto grupal
- Presentación y demostración final

**Evaluación: Proyecto Integrador Invenio Fest (20%)**

**Distinción importante (según el programa, intención literal preservada):**

| | Legacy of InFest | Invenio Fest |
|---|---|---|
| Alcance | Individual | Grupal, interdisciplinario |
| Pertenece a | Sólo este curso | Integra todos los cursos del trimestre |
| Evalúa | Computación Gráfica y Procesamiento de Imágenes | Integración transdisciplinaria |

El conocimiento y el código producidos en Legacy of InFest pueden transferirse al proyecto grupal de Invenio Fest del estudiante, de forma consistente con el modelo de aprendizaje dual de la Universidad Invenio.

---

## 4. Resumen del calendario de quices y laboratorios

| Instrumento | Clase | Cobertura de tema |
|---|---|---|
| Quiz 1 | 2 | Unidad I + Unidad II (vectores, sistemas de coordenadas) |
| Laboratorio 1 | 3 | Unidad II (transformaciones, coordenadas homogéneas) |
| Quiz 2 | 4 | Unidad III (curvas, polinomios de Bernstein) |
| Quiz 3 | 6 | Unidad V (teoría del color, conversión de espacio de color) |
| Laboratorio 2 | 6 | Unidad V (color e iluminación aplicados) |
| Quiz 4 | 9 | Unidad VIII (teoría de segmentación y morfología) |
| Laboratorio 3 | 9 | Unidad VIII (segmentación y análisis visual aplicados) |

**Nota:** el conteo exacto y la distribución de quices y laboratorios dentro de las bolsas del 15%/20% queda a discreción del profesorado según el programa §8 ("La persona docente podrá incorporar..."); la tabla anterior refleja una distribución válida consistente con la estructura de 11 clases. Se pueden añadir quices o laboratorios cortos adicionales en las Clases 1, 5, 7, 8, 10, u 11 sin contradecir el programa, siempre que el peso **total** de Quices se mantenga en 15% y el peso total de Prácticas de laboratorio se mantenga en 20%.

---

## 5. Ponderación oficial de evaluación (literal del programa)

| Instrumento | Porcentaje | Clase(s) |
|---|---|---|
| Quices | 15% | Distribuidos en las Clases 2, 4, 6, 9 (ver §4) |
| Prácticas de laboratorio | 20% | Distribuidas en las Clases 3, 6, 9 (ver §4) |
| Evaluación Práctica I – Prototipo Funcional | 15% | Clase 5 |
| Evaluación Práctica II – Vertical Slice | 15% | Clase 8 |
| Evaluación Práctica III – Integración Final | 15% | Clase 11 |
| Proyecto Integrador Invenio Fest | 20% | Clase 12 |
| **Total** | **100%** | |

---

## 6. Mapeo de unidad del programa a clase

| Unidad del programa | Título | Clase principal |
|---|---|---|
| I | Introducción a la Computación Gráfica | Clase 1 |
| II | Sistemas de Coordenadas y Transformaciones Geométricas | Clases 2–3 |
| III | Curvas y Modelado Geométrico | Clase 4 |
| IV | Representación de Objetos y Escenas | Clase 5 |
| V | Color, Transparencia e Iluminación | Clase 6 |
| VI | Texturizado, Animación e Interacción | Clase 7 |
| VII | Procesamiento Digital de Imágenes | Clase 8 |
| VIII | Segmentación y Análisis de Imágenes | Clase 9 |
| IX | Aplicaciones Integradoras | Clase 10 |
| — | Integración y repaso | Clase 11 |
| — | Invenio Fest | Clase 12 |

Este mapeo es consistente con `08_SYLLABUS_MAPPING.md`, que define el contenido académico de cada unidad en detalle completo. Este calendario sólo añade la secuenciación temporal a través de las 11+1 sesiones del trimestre.

---

## 7. Relación con la documentación existente de hitos de Escenario/Jefe

Los tres puntos de control de Evaluación Práctica de este calendario (Clase 5, 8, 11) corresponden a los mismos tres hitos acumulativos ya definidos conceptualmente en `08_SYLLABUS_MAPPING.md` y `14_PROFESSOR_DELIVERABLE_MATRIX.md` — ahora anclados a sesiones de clase específicas:

| Hito | Clase | Nombre oficial | Referencia interna previa |
|---|---|---|---|
| Hito 1 | Clase 5 | Evaluación Práctica I – Prototipo Funcional | Antes referido informalmente como "Entrega de Stage 1" |
| Hito 2 | Clase 8 | Evaluación Práctica II – Vertical Slice | Antes referido informalmente como "Entrega de Stage 2" |
| Hito 3 | Clase 11 | Evaluación Práctica III – Integración Final | Antes referido informalmente como "Entrega de Stage 3" |

**Aclaración:** los tres hitos aplican al **mismo Escenario o Jefe único** que el estudiante eligió en la Clase 1. "Stage 1 / Stage 2 / Stage 3" en documentación interna anterior nunca significó tres escenarios distintos — significaba tres estados secuenciales de completitud (prototipo → vertical slice → integración final) de una sola entrega. Este calendario usa de aquí en adelante el nombramiento oficial Evaluación Práctica I/II/III para eliminar la ambigüedad.

---

## Apéndice A — Referencia de la estructura del repositorio

La estructura real del repositorio (`docs/`, `assets/`, `src/`, `student_templates/`, `main.py`, `requirements.txt`) se documenta en `03_ARCHITECTURE.md`.

---
## 🔗 Documentos relacionados

- [[30_ASSIGNMENT_01_STAGE_DESIGN.md|Entrega 1: diseño de escenario]]
- [[31_ASSIGNMENT_02_BOSS_DESIGN.md|Entrega 2: diseño de jefe]]
- [[32_ASSIGNMENT_03_LAB_EXERCISES.md|Entrega 3: ejercicios de laboratorio]]
- [[33_ASSIGNMENT_04_FINAL_PROJECT.md|Entrega 4: proyecto final]]
