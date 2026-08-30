---
document_id: "LOI-EVAL_PRACTICA-EVAL_PRACTICA"
title: "Evaluación Práctica"
aliases: ["Eval Practica", "eval_practica"]
tags: ["evaluacion", "practica", "academico"]
description: "Documento de Eval Practica: eval_practica"
source: "docs/eval_practica/eval_practica.md"
date_processed: "2026-08-13"
---

# Evaluación Práctica

**Curso:** Legacy of InFest
**Referencia:** `27_ACADEMIC_RUBRICS.md` §4–§6, `14_PROFESSOR_DELIVERABLE_MATRIX.md` §14

> **AUD-XXX — reconciliación de rúbricas (26/08 Teams vs este documento).**
> Existe una contradicción real entre este documento (Eval II: 55 pts por histograma/kernels
> de Unidade VII — 15+20+20 con animación) y el mensaje de Teams del 26/08
> (Eval II: curvas/color/texturas de Unidades III/V/VI). Ambas son válidas:
> la primera es la rúbrica autoritativa de `27_ACADEMIC_RUBRICS.md` §5 y `14` §14.2,
> la segunda es la expectativa comunicada en clase para quienes vienen de Eval I
> sin haber cerrado color/curvas. Hasta decisión docente, **se evalúa con README dual**:
> la entrega demuestra **histograma+kernel+Sobel/Canny (VII)** y mantiene **curva+color+easing (III/V/VI)**
> sin retroceso — quien cumple ambas saca el 100% en cualquiera de las dos lecturas.
> Ver también `27_ACADEMIC_RUBRICS.md` §5 y el patrón de grupo en `docs/entregables/NOTAS_EVALUACION_PRACTICA_I.md`.

Tres evaluaciones prácticas acumulativas, cada una con un valor de **15% de la nota final**.

---

## Evaluación Práctica I — Prototipo Funcional (Clase 5, 15%)

**Unidades:** II (Vectores), III (Curvas), IV (Escena/Objeto), V (Color/Transparencia)

### Rúbrica de calificación (100 pts)

| Criterio | Puntos | Requisito |
|-----------|--------|-------------|
| Sistemas de coordenadas y vectores | 20 | La entidad propia usa matemática vectorial explícita (`vec2_normalize`/`vec2_dot`/`vec2_distance`) |
| Curvas | 15 | La entidad sigue una ruta calculada con `CurveTools`; puntos de control documentados |
| Representación de escena | 20 | El escenario TMX tiene las 8 capas obligatorias; O la geometría de la arena del jefe está completa |
| Color/transparencia | 15 | Operación de `ColorTools` (conversión o mezcla alfa) observable visualmente |
| Completitud funcional | 20 | El escenario carga; el jugador lo recorre sin fallos |
| Documentación del README | 10 | Front-matter válido según `23_DATA_SCHEMAS.md`; la sección de cada unidad explica la fórmula |
| **Total** | **100** | Aprobación: ≥60/100 |

### Entregables
- `<entrega>.tmx` con las capas obligatorias
- `<entrega>.py` — subclase correcta de `BaseScene` o `BossBase`
- Entidad propia que use matemática vectorial
- Entidad que siga una ruta de curva
- Operación de espacio de color sobre una superficie
- `README.md` con los conceptos académicos

---

## Evaluación Práctica II — Vertical Slice (Clase 8, 15%)

**Unidades:** +VI (Animación), +VII (Filtros)

### Rúbrica de calificación (100 pts)

| Criterio | Puntos | Requisito |
|-----------|--------|-------------|
| Se mantienen todos los criterios de Eval I | 25 | Sin retroceso |
| Animación e interacción (Unidad VI) | 20 | Animación dirigida por easing; interacción propia de `EventBus` |
| Histograma/brillo/contraste (Unidad VII) | 15 | `FilterTools.compute_histogram()` dirige la lógica |
| Convolución/desenfoque/detección de bordes (Unidad VII) | 20 | `apply_kernel`/`gaussian_blur`/`sobel_edge`/`canny_edge` |
| Completitud funcional | 10 | Eval I sigue funcionando; las características nuevas se integran limpiamente |
| Documentación del README | 10 | Secciones de las Unidades VI–VII con capturas de antes/después |
| **Total** | **100** | Aprobación: ≥60/100 |

### Entregables
- Se mantienen todos los entregables de Eval I
- Función de easing usada en animación
- `compute_histogram()` dirige la lógica del juego
- `adjust_brightness()` o `adjust_contrast()` aplicado
- `apply_kernel()` o `gaussian_blur()` aplicado
- Resultado de detección de bordes (Sobel o Canny)
- README: matriz de kernel, capturas de antes/después

---

## Evaluación Práctica III — Integración Final (Clase 11, 15%)

**Unidades:** +VIII (Segmentación), +IX (Reconocimiento de patrones)

### Rúbrica de calificación (100 pts)

| Criterio | Puntos | Requisito |
|-----------|--------|-------------|
| Se mantienen todos los criterios previos | 20 | Eval I + II intactas |
| Segmentación (Unidad VIII) | 20 | Umbral + morfología + componentes conectados |
| Extracción de características y clasificación (Unidad IX) | 25 | Las características alimentan un clasificador entrenado; la salida cambia el comportamiento de ≥2 formas |
| Calidad del modelo | 15 | ≥10 muestras/clase, ≥2 clases, precisión ≥0.70 |
| Integración y pulido completos | 10 | Completo, jugable, sin errores de consola |
| Documentación del README | 10 | Tubería de entrenamiento completa: dataset, hiperparámetros, precisión, matriz de confusión |
| **Total** | **100** | **15% de la nota final** |

### Entregables
- Se mantienen todos los requisitos de Eval I + II
- `threshold_binary()` o `threshold_otsu()` aplicado
- Operación morfológica aplicada
- `connected_components()` o `analyze_regions()` usado
- `extract_features()` produce características de entrenamiento
- Dataset etiquetado en `assets/datasets/`
- Modelo entrenado (`.pkl`)
- `EvaluationResult` con precisión ≥70% en el README
- El clasificador corre en tiempo de ejecución; el resultado cambia el comportamiento del juego de ≥2 formas
- README: documentación completa de la tubería de entrenamiento
