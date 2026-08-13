---
document_id: "LOI-RUBRIC-027"
title: "Legacy of InFest — Rúbricas académicas"
aliases: ["Rúbricas académicas", "Academic Rubrics"]
tags: ["rubrica", "calificacion", "academico"]
description: "Criterios de puntuación de cada instrumento calificado"
source: "docs/27_ACADEMIC_RUBRICS.md"
date_processed: "2026-08-13"
---

# Legacy of InFest — Rúbricas académicas

**ID del documento:** LOI-RUBRIC-027
**Versión:** 1.1.0
**Estado:** Oficial
**Compatibilidad:** Requiere `08_SYLLABUS_MAPPING.md`, `14_PROFESSOR_DELIVERABLE_MATRIX.md`, `21_COURSE_SCHEDULE.md`
**Audiencia:** Profesor, ayudantes de cátedra

> **AUD-455.** Traduce el documento (el Apéndice al final ya estaba en
> español y no se toca). Quita cuatro referencias a documentos que no
> existen en este repositorio: `77_SYLLABUS_ALIGNMENT_AUDIT.md`,
> `02_CODEX_CONTEXT.md`, `28_DECISION_LOG.md`, y
> `29_GIT_WORKFLOW_AND_STANDARDS.md` — las tres últimas remitían a un
> checklist de calidad de código y de revisión que en este repositorio vive
> en `CONTRIBUTING.md`.

---

## 1. Propósito

`08_SYLLABUS_MAPPING.md` y `14_PROFESSOR_DELIVERABLE_MATRIX.md` definen **qué** se evalúa y **cuánto vale** (los seis instrumentos oficiales y sus porcentajes). Ninguno de los dos documentos define **los criterios a nivel de punto que aplica quien califica** para convertir una entrega de estudiante en un número. Este documento es ese instrumento de calificación que faltaba — cada rúbrica aquí es aditiva (los criterios suman el 100% del peso de ese instrumento) y reproducible entre distintos calificadores.

**Regla:** ninguna rúbrica de este documento introduce un instrumento de evaluación nuevo ni cambia un porcentaje de `21_COURSE_SCHEDULE.md` §5. Las rúbricas sólo subdividen los seis instrumentos existentes en criterios calificables.

---

## 2. Rúbrica de Quices (15% de la nota final)

Según `21_COURSE_SCHEDULE.md` §4, se distribuyen cuatro quices en las Clases 2, 4, 6, 9. Cada quiz vale una fracción igual salvo que el profesorado documente lo contrario.

### 2.1 Rúbrica genérica de quiz (aplica a los 4 quices; el contenido varía según `21_COURSE_SCHEDULE.md` §4)

| Criterio | Puntos | Descripción |
|---|---|---|
| Precisión conceptual | 40 | Las definiciones y afirmaciones teóricas son correctas |
| Razonamiento aplicado | 30 | El estudiante conecta el concepto con un ejemplo concreto de gráficas/imágenes (no sólo la definición de memoria) |
| Corrección matemática | 20 | Cualquier fórmula, cómputo, o derivación pedida es correcta |
| Claridad de expresión | 10 | La respuesta es legible, organizada, y usa la terminología correcta |
| **Total** | **100** | Escalado a (15% / 4) = 3.75% de la nota final por quiz |

### 2.2 Ponderación de tema por quiz (dentro de la escala de 100 puntos de arriba)

| Quiz | Clase | Temas | Distribución de preguntas sugerida |
|---|---|---|---|
| Quiz 1 | 2 | Unidad I + Unidad II (vectores, sistemas de coordenadas) | 30% historia raster/vectorial, 70% álgebra vectorial |
| Quiz 2 | 4 | Unidad III (curvas, polinomios de Bernstein) | 50% teoría de Bézier, 30% concepto de B-Spline/NURBS, 20% aplicación de trayectorias |
| Quiz 3 | 6 | Unidad V (teoría del color, conversión de espacio de color) | 60% matemática de conversión RGB/HSV/HSL/CMYK, 40% mezcla alfa y conceptos de iluminación |
| Quiz 4 | 9 | Unidad VIII (segmentación, teoría de morfología) | 40% umbralización/Otsu, 30% operaciones morfológicas, 30% concepto de componentes conectados/watershed |

---

## 3. Rúbrica de Prácticas de laboratorio (20% de la nota final)

Según `21_COURSE_SCHEDULE.md` §4, se distribuyen tres laboratorios en las Clases 3, 6, 9.

### 3.1 Rúbrica genérica de laboratorio (aplica a los 3 laboratorios)

| Criterio | Puntos | Descripción |
|---|---|---|
| Corrección funcional | 35 | El código corre sin errores y produce la salida esperada para la tarea del laboratorio |
| Uso correcto de la API del framework | 25 | El estudiante llama a `FilterTools`/`VisionTools`/`ColorTools`/etc. (según aplique) a través de la API pública documentada — nunca la evita con llamadas directas a la biblioteca subyacente (`cv2`, `scipy`, `sklearn`) |
| Calidad de código | 20 | Sigue los estándares de nombres/tipado/docstrings de `CONTRIBUTING.md` |
| Demostración en el laboratorio | 20 | El estudiante puede explicar su código y su salida verbalmente al instructor durante el bloque práctico de 2 horas |
| **Total** | **100** | Escalado a (20% / 3) ≈ 6.67% de la nota final por laboratorio |

### 3.2 Ponderación de tema por laboratorio

| Laboratorio | Clase | Temas | API directa ejercitada |
|---|---|---|---|
| Laboratorio 1 | 3 | Unidad II (transformaciones, coordenadas homogéneas) | funciones vectoriales de `math_utils.py`, transformación de hitbox local→mundo |
| Laboratorio 2 | 6 | Unidad V (color e iluminación aplicados) | conversiones de `ColorTools`, `alpha_blend` |
| Laboratorio 3 | 9 | Unidad VIII (segmentación y análisis visual aplicados) | umbral/morfología/análisis de regiones de `VisionTools` |

---

## 4. Rúbrica de Evaluación Práctica I — Prototipo Funcional (15% de la nota final)

**Clase 5.** Según `14_PROFESSOR_DELIVERABLE_MATRIX.md`, demuestra las Unidades II, III, IV, V sobre el único Escenario o Jefe asignado al estudiante.

| Criterio | Puntos | Descripción |
|---|---|---|
| Sistemas de coordenadas y vectores (Unidad II) | 20 | Al menos una entidad propia usa matemática vectorial explícita (`vec2_normalize`/`vec2_dot`/`vec2_distance`) para movimiento o detección, correctamente |
| Curvas (Unidad III) | 15 | Al menos una entidad o proyectil sigue una ruta calculada con `CurveTools`; puntos de control y tipo de curva documentados en el README |
| Representación de escena/objeto (Unidad IV) | 20 | El TMX del escenario tiene las 8 capas obligatorias pobladas con sentido (no sólo marcadores de posición); O, para entregas de Jefe, la geometría de la arena y el ordenamiento de entidades está completo |
| Color/transparencia (Unidad V) | 15 | Se aplica una operación de `ColorTools` (conversión o mezcla alfa) y es observable visualmente |
| Completitud funcional | 20 | El Escenario/Jefe carga, el jugador puede recorrerlo/combatirlo sin fallos, funciona la interacción básica (contacto con enemigo, checkpoint, o golpe al jefe) |
| Calidad de la documentación del README | 10 | El front-matter está presente y es válido según `23_DATA_SCHEMAS.md` §7; la sección de cada unidad explica la fórmula/algoritmo usado, no sólo nombra la característica |
| **Total** | **100** | Escalado al 15% de la nota final |

**Umbral de aprobación:** una nota por debajo de 60/100 en este instrumento exige una conversación de remediación obligatoria con el profesorado antes de la Evaluación Práctica II, ya que cada hito posterior se construye acumulativamente sobre éste (según `08_SYLLABUS_MAPPING.md` §12).

---

## 5. Rúbrica de Evaluación Práctica II — Vertical Slice (15% de la nota final)

**Clase 8.** Añade las Unidades VI, VII sobre la base de la Evaluación Práctica I.

| Criterio | Puntos | Descripción |
|---|---|---|
| Se mantienen todos los criterios de la Evaluación Práctica I | 25 | Recalificado a granularidad aprobado/parcial/reprobado — el trabajo no debe haber retrocedido |
| Animación e interacción (Unidad VI) | 20 | Al menos una animación dirigida por función de easing (`ease_*` de `math_utils.py`, no `lerp` plano); una interacción propia mediada por `EventBus` más allá de la colisión estándar |
| Histograma/brillo/contraste (Unidad VII, parte 1) | 15 | Se usa `FilterTools.compute_histogram()` para dirigir una decisión de lógica de juego (no puramente cosmética); se aplica y documenta un ajuste de brillo o contraste |
| Convolución/desenfoque/detección de bordes (Unidad VII, parte 2) | 20 | Se aplica al menos uno de `apply_kernel`/`gaussian_blur`/`sobel_edge`/`canny_edge` con una matriz de kernel documentada o justificación de parámetros |
| Completitud funcional | 10 | Toda la funcionalidad de la Evaluación Práctica I sigue funcionando; las características nuevas se integran sin romper las existentes |
| Calidad de la documentación del README | 10 | Se añaden las secciones de Unidad VI y VII con capturas de antes/después para las operaciones de filtro |
| **Total** | **100** | Escalado al 15% de la nota final |

**Umbral de aprobación:** igual que en §4 — por debajo de 60/100 dispara remediación obligatoria antes de la Evaluación Práctica III.

---

## 6. Rúbrica de Evaluación Práctica III — Integración Final (15% de la nota final)

**Clase 11.** Añade las Unidades VIII, IX — el hito de cierre para la única entrega del estudiante.

| Criterio | Puntos | Descripción |
|---|---|---|
| Se mantienen todos los criterios previos | 20 | La funcionalidad de la Evaluación Práctica I + II está intacta, recalificada aprobado/parcial/reprobado |
| Segmentación (Unidad VIII) | 20 | Se aplica `VisionTools.threshold_binary()`/`threshold_otsu()` + al menos una operación morfológica; `connected_components()` o `analyze_regions()` dirige un comportamiento observable |
| Extracción de características y reconocimiento de patrones (Unidad IX) | 25 | `VisionTools.extract_features()` produce un vector de características que se alimenta a un clasificador entrenado (`PatternRecognitionTools`); la salida del clasificador cambia el comportamiento del juego de al menos 2 formas distinguibles |
| Calidad del modelo | 15 | El dataset tiene ≥10 muestras/clase en ≥2 clases (según `23_DATA_SCHEMAS.md` §5.4); `EvaluationResult.accuracy` ≥ 0.70, O una justificación documentada si está por debajo del umbral (según `13_PATTERN_RECOGNITION_SPEC.md` §10.2) |
| Integración y pulido completos | 10 | El único Escenario/Jefe asignado está completo, jugable de principio a fin, sin errores de consola durante una corrida completa |
| Calidad de la documentación del README | 10 | Tubería de entrenamiento completa documentada: descripción del dataset, tipo de clasificador/hiperparámetros, precisión, matriz de confusión |
| **Total** | **100** | Escalado al 15% de la nota final |

**Éste es el hito final del curso individual.** No aplica ninguna puerta de remediación después de este punto — la nota queda fija, y alimenta el promedio final del curso junto con Quices, Laboratorios, e Invenio Fest.

---

## 7. Rúbrica del Proyecto Integrador Invenio Fest (20% de la nota final)

**Clase 12.** Según `21_COURSE_SCHEDULE.md` §3 Clase 12 y §7, este curso califica **sólo la contribución gráfica/visual** al proyecto grupal interdisciplinario — no el proyecto grupal como un todo (los demás cursos califican sus propias dimensiones por separado).

| Criterio | Puntos | Descripción |
|---|---|---|
| Aplicación efectiva de técnicas visuales | 25 | La contribución individual del estudiante al proyecto grupal aplica visiblemente técnicas del curso (cualquiera de las Unidades I–IX) de forma apropiada al dominio de aplicación elegido por el grupo |
| Calidad de GUI/interfaz | 20 | Si la contribución del estudiante incluye una interfaz gráfica o salida visual, es funcional, legible, y sin problemas de usabilidad evidentes |
| Uso apropiado de recursos visuales | 15 | Las imágenes, sprites, o recursos visuales generados se usan con propósito, no decorativa o irrelevantemente |
| Integración de componentes gráficos en la solución | 20 | El código de gráficas/imágenes que escribió el estudiante no es una demo independiente — está conectado a la lógica real de la aplicación del grupo |
| Claridad de la contribución individual | 10 | El profesorado puede identificar claramente qué parte de la entrega grupal es el trabajo de este estudiante en particular (vía historial de commits, un rol declarado, o un segmento presentado individualmente) |
| Presentación y demostración final | 10 | El estudiante puede explicar y demostrar en vivo su contribución gráfica durante Invenio Fest |
| **Total** | **100** | Escalado al 20% de la nota final |

**Nota entre cursos:** esta rúbrica es independiente de la rúbrica que apliquen los demás cursos del trimestre del estudiante al mismo proyecto de Invenio Fest — según la tabla de `21_COURSE_SCHEDULE.md` §3 Clase 12, cada curso evalúa su propia dimensión.

---

## 8. Cómputo de la nota final

```
Nota final = (promedio_Quices × 0.15)
           + (promedio_Laboratorios × 0.20)
           + (Eval_Practica_I × 0.15)
           + (Eval_Practica_II × 0.15)
           + (Eval_Practica_III × 0.15)
           + (Invenio_Fest × 0.20)
```

Donde cada término de la derecha es la nota porcentual (0.0–1.0) sobre la rúbrica de 100 puntos de ese instrumento, y los pesos suman 1.00 (100%), coincidiendo exactamente con `21_COURSE_SCHEDULE.md` §5.

---

## 9. Notas de consistencia de calificación para varios calificadores

Si un ayudante de cátedra califica alguna parte de estas rúbricas:

1. **Se requiere una sesión de calibración** antes de la Clase 5 (primera evaluación práctica): el profesorado y el ayudante califican juntos 2-3 entregas de muestra y reconcilian diferencias de puntuación antes de calificar a toda la cohorte.
2. **Los criterios de calidad de código** deben revisarse con un checklist compartido, no con impresión subjetiva — usar el checklist de revisión de código de `CONTRIBUTING.md` como el instrumento de calificación literal para cualquier renglón de "calidad de código" de arriba.
3. **Los desacuerdos de más de 15 puntos** entre dos calificadores sobre la misma entrega deben resolverlos directamente el profesorado, no promediarse en silencio.

---

## 10. Índice de referencia cruzada de rúbricas

| Sección de rúbrica | Instrumento de evaluación | Peso oficial | Documento fuente para el alcance del contenido |
|---|---|---|---|
| §2 | Quices | 15% | `21_COURSE_SCHEDULE.md` §4, §6 |
| §3 | Prácticas de laboratorio | 20% | `21_COURSE_SCHEDULE.md` §4 |
| §4 | Evaluación Práctica I | 15% | `08_SYLLABUS_MAPPING.md` §12, `14_PROFESSOR_DELIVERABLE_MATRIX.md` |
| §5 | Evaluación Práctica II | 15% | `08_SYLLABUS_MAPPING.md` §12, `14_PROFESSOR_DELIVERABLE_MATRIX.md` |
| §6 | Evaluación Práctica III | 15% | `08_SYLLABUS_MAPPING.md` §12, `14_PROFESSOR_DELIVERABLE_MATRIX.md` |
| §7 | Invenio Fest | 20% | `21_COURSE_SCHEDULE.md` §3 Clase 12 |

---
## 🔗 Documentos relacionados

- [[30_ASSIGNMENT_01_STAGE_DESIGN.md|Entrega 1: diseño de escenario]]
- [[31_ASSIGNMENT_02_BOSS_DESIGN.md|Entrega 2: diseño de jefe]]
- [[32_ASSIGNMENT_03_LAB_EXERCISES.md|Entrega 3: ejercicios de laboratorio]]
- [[33_ASSIGNMENT_04_FINAL_PROJECT.md|Entrega 4: proyecto final]]

---

## Apéndice — Diseño de nivel en `grade_stage.py` (F2.4)

### El hueco que cierra

Hasta ahora la rúbrica automática medía que los objetos **estuvieran**, no que
el nivel se pudiera jugar. Un estudiante que colocara las ocho capas
obligatorias, un spawn, cuatro checkpoints y algunos enemigos en un rectángulo
vacío sacaba más del 90 %.

`framework/stage/level_metrics.py` ya sabía responder a las preguntas que
importan, y llevaba desde su creación sin conectarse a nada que calificara.

### Las tres categorías nuevas — 30 de 130 puntos

| Categoría | Puntos | Qué mide | Cómo se pierde |
|---|---|---|---|
| `design_completable` | 12 | ¿Hay ruta de plataformas del spawn a la salida? | Todo o nada. |
| `design_geometry` | 10 | Repechos imposibles y plataformas aisladas | −3 por cada uno. |
| `design_pacing` | 8 | Distancia entre checkpoints, y si hay algún salto exigente | −6 si hay más de 500 px sin checkpoint; −3 si no hay ningún salto que ponga a prueba. |

El informe incluye además las métricas crudas bajo la clave `design` de la
salida `--json`, para que puedas ver el dato y no sólo la nota.

### Referencias medidas

| Mapa | Nota | Qué le pasa |
|---|---|---|
| `stage0` | 86,2 % | 2 plataformas sin ruta desde el spawn; ningún salto exigente. |
| `stage_template` | 63,8 % | Estructuralmente pobre, pero geométricamente trivial: un rectángulo plano no tiene saltos imposibles. |
| `boss_venado` | 44,6 % | **Aquí la rúbrica no aplica.** |

### Aviso importante sobre las arenas

`design_completable` recorre plataformas. En una arena de jefe la salida se
abre al derrotarlo, no al llegar andando, así que la arena de referencia del
propio juego puntúa 0 en esa categoría. **No es un fallo de la arena: es que se
le está aplicando la rúbrica equivocada.** El calificador lo avisa en el
informe; usa `scripts/grade_boss.py` para esas entregas.

### Qué decirle a un estudiante

- «2 plataformas sin ruta desde el spawn» → o sobran, o falta un camino. Las
  dos cosas son información: una plataforma decorativa está bien si es
  deliberada.
- «ningún salto pone a prueba al jugador» → el nivel se recorre solo. No es un
  error, es un nivel sin tensión.
- «588 px sin checkpoint» → morir ahí cuesta demasiado camino rehecho.
