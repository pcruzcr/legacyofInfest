---
document_id: "LOI-RUBRIC-027"
title: "Legacy of InFest — Academic Rubrics"
aliases: ["Academic Rubrics"]
tags: ["rubric", "grading", "academic"]
description: "Scoring criteria for every graded instrument"
source: "docs/27_ACADEMIC_RUBRICS.md"
date_processed: "2026-07-14"
---

# Legacy of InFest — Academic Rubrics

**Document ID:** LOI-RUBRIC-027  
**Version:** 1.0.0  
**Status:** Official  
**Compatibility:** Requires `77_SYLLABUS_ALIGNMENT_AUDIT.md`, `08_SYLLABUS_MAPPING.md`, `14_PROFESSOR_DELIVERABLE_MATRIX.md`, `21_COURSE_SCHEDULE.md`  
**Audience:** Professor, Teaching Assistants

---

## 1. Purpose

`08_SYLLABUS_MAPPING.md` and `14_PROFESSOR_DELIVERABLE_MATRIX.md` define **what** is evaluated and **how much it's worth** (the six official instruments and their percentages). Neither document defines **the point-level criteria a grader applies** to turn a student submission into a number. This document is that missing grading instrument — every rubric here is additive (criteria sum to 100% of that instrument's weight) and reproducible across graders.

**Rule:** No rubric in this document introduces a new evaluation instrument or changes a percentage from `21_COURSE_SCHEDULE.md` §5. Rubrics only subdivide the existing six instruments into gradable criteria.

---

## 2. Quices Rubric (15% of final grade)

Per `21_COURSE_SCHEDULE.md` §4, four quizzes are distributed across Classes 2, 4, 6, 9. Each quiz is worth an equal share unless the professor documents otherwise in `28_DECISION_LOG.md`.

### 2.1 Generic Quiz Rubric (applies to all 4 quizzes, content varies per `21_COURSE_SCHEDULE.md` §4)

| Criterion | Points | Description |
|---|---|---|
| Conceptual accuracy | 40 | Definitions and theoretical statements are correct |
| Applied reasoning | 30 | Student connects the concept to a concrete graphics/imaging example (not just rote definition) |
| Mathematical correctness | 20 | Any formula, computation, or derivation requested is correct |
| Clarity of expression | 10 | Answer is legible, organized, and uses correct terminology |
| **Total** | **100** | Scaled to (15% / 4) = 3.75% of final grade per quiz |

### 2.2 Per-Quiz Topic Weighting (within the 100-point scale above)

| Quiz | Class | Topics | Suggested Question Distribution |
|---|---|---|---|
| Quiz 1 | 2 | Unit I + Unit II (vectors, coordinate systems) | 30% raster/vector history, 70% vector algebra |
| Quiz 2 | 4 | Unit III (curves, Bernstein polynomials) | 50% Bézier theory, 30% B-Spline/NURBS concept, 20% trajectory application |
| Quiz 3 | 6 | Unit V (color theory, color space conversion) | 60% RGB/HSV/HSL/CMYK conversion math, 40% alpha blending and lighting concepts |
| Quiz 4 | 9 | Unit VIII (segmentation, morphology theory) | 40% thresholding/Otsu, 30% morphological operations, 30% connected components/watershed concept |

---

## 3. Prácticas de Laboratorio Rubric (20% of final grade)

Per `21_COURSE_SCHEDULE.md` §4, three labs are distributed across Classes 3, 6, 9.

### 3.1 Generic Lab Rubric (applies to all 3 labs)

| Criterion | Points | Description |
|---|---|---|
| Functional correctness | 35 | Code runs without errors and produces the expected output for the lab's stated task |
| Correct use of framework API | 25 | Student calls `FilterTools`/`VisionTools`/`ColorTools`/etc. (as applicable) through the documented public API — never bypasses with direct library calls (`cv2`, `scipy`, `sklearn`) per `02_CODEX_CONTEXT.md` §11 |
| Code quality | 20 | Follows `02_CODEX_CONTEXT.md` §5 naming/typing/docstring standards |
| In-lab demonstration | 20 | Student can explain their code and its output verbally to the instructor during the 2-hour practice block |
| **Total** | **100** | Scaled to (20% / 3) ≈ 6.67% of final grade per lab |

### 3.2 Per-Lab Topic Weighting

| Lab | Class | Topics | Direct API Exercised |
|---|---|---|---|
| Lab 1 | 3 | Unit II (transformations, homogeneous coordinates) | `math_utils.py` vector functions, local→world hitbox transform |
| Lab 2 | 6 | Unit V (color and lighting applied) | `ColorTools` conversions, `alpha_blend` |
| Lab 3 | 9 | Unit VIII (segmentation and visual analysis applied) | `VisionTools` threshold/morphology/region analysis |

---

## 4. Evaluación Práctica I — Prototipo Funcional Rubric (15% of final grade)

**Class 5.** Per `14_PROFESSOR_DELIVERABLE_MATRIX.md` (corrected), demonstrates Units II, III, IV, V on the student's single assigned Stage or Boss.

| Criterion | Points | Description |
|---|---|---|
| Coordinate systems & vectors (Unit II) | 20 | At least one custom entity uses explicit vector math (`vec2_normalize`/`vec2_dot`/`vec2_distance`) for movement or detection, correctly |
| Curves (Unit III) | 15 | At least one entity or projectile follows a `CurveTools`-computed path; control points and curve type documented in README |
| Scene/object representation (Unit IV) | 20 | TMX stage has all 8 required layers populated meaningfully (not just placeholder); OR for Boss assignments, arena geometry and entity layering is complete |
| Color/transparency (Unit V) | 15 | A `ColorTools` operation (conversion or alpha blend) is applied and visually observable |
| Functional completeness | 20 | Stage/Boss loads, player can traverse/fight without crashing, basic interaction (enemy contact, checkpoint, or boss hit) works |
| README documentation quality | 10 | Front-matter present and valid per `23_DATA_SCHEMAS.md` §7; each unit's section explains the formula/algorithm used, not just names the feature |
| **Total** | **100** | Scaled to 15% of final grade |

**Pass threshold:** A score below 60/100 on this instrument requires a mandatory remediation conversation with the professor before Evaluación Práctica II, since each subsequent milestone builds cumulatively on this one (per `08_SYLLABUS_MAPPING.md` §12).

---

## 5. Evaluación Práctica II — Vertical Slice Rubric (15% of final grade)

**Class 8.** Adds Units VI, VII on top of the Evaluación Práctica I baseline.

| Criterion | Points | Description |
|---|---|---|
| All Evaluación Práctica I criteria maintained | 25 | Re-graded at a pass/partial/fail granularity — work must not have regressed |
| Animation & interaction (Unit VI) | 20 | At least one easing-function-driven animation (`ease_*` from `math_utils.py`, not plain `lerp`); a custom `EventBus`-mediated interaction beyond standard collision |
| Histogram/brightness/contrast (Unit VII, part 1) | 15 | `FilterTools.compute_histogram()` used to drive a game-logic decision (not purely cosmetic); brightness or contrast adjustment applied and documented |
| Convolution/blur/edge detection (Unit VII, part 2) | 20 | At least one of `apply_kernel`/`gaussian_blur`/`sobel_edge`/`canny_edge` applied with a documented kernel matrix or parameter rationale |
| Functional completeness | 10 | All Evaluación Práctica I functionality still works; new features integrate without breaking existing ones |
| README documentation quality | 10 | Unit VI and VII sections added with before/after screenshots for filter operations |
| **Total** | **100** | Scaled to 15% of final grade |

**Pass threshold:** Same as §4 — below 60/100 triggers mandatory remediation before Evaluación Práctica III.

---

## 6. Evaluación Práctica III — Integración Final Rubric (15% of final grade)

**Class 11.** Adds Units VIII, IX — the capstone milestone for the student's single assignment.

| Criterion | Points | Description |
|---|---|---|
| All prior criteria maintained | 20 | Evaluación Práctica I + II functionality intact, re-graded pass/partial/fail |
| Segmentation (Unit VIII) | 20 | `VisionTools.threshold_binary()`/`threshold_otsu()` + at least one morphological operation applied; `connected_components()` or `analyze_regions()` drives observable behavior |
| Feature extraction & pattern recognition (Unit IX) | 25 | `VisionTools.extract_features()` (or `PatternRecognitionTools` direct equivalent) produces a feature vector that is fed into a trained classifier; classifier output changes game behavior in at least 2 distinguishable ways |
| Model quality | 15 | Dataset has ≥10 samples/class across ≥2 classes (per `23_DATA_SCHEMAS.md` §5.4); `EvaluationResult.accuracy` ≥ 0.70, OR a documented justification if below threshold (per `13_PATTERN_RECOGNITION_SPEC.md` §10.2) |
| Full integration & polish | 10 | The single assigned Stage/Boss is complete, playable start-to-finish, no console errors during a full run |
| README documentation quality | 10 | Full training pipeline documented: dataset description, classifier type/hyperparameters, accuracy, confusion matrix |
| **Total** | **100** | Scaled to 15% of final grade |

**This is the final individual-course milestone.** No remediation gate applies after this point — the grade stands, feeding into the final course average alongside Quices, Labs, and Invenio Fest.

---

## 7. Proyecto Integrador Invenio Fest Rubric (20% of final grade)

**Class 12.** Per `21_COURSE_SCHEDULE.md` §3 Class 12 and §7, this course grades **only the graphics/visual contribution** to the interdisciplinary group project — not the group project as a whole (other courses grade their own dimensions separately).

| Criterion | Points | Description |
|---|---|---|
| Effective application of visual techniques | 25 | The student's individual contribution to the group project visibly applies course techniques (any of Units I–IX) appropriately to the group's chosen application domain |
| GUI/interface quality | 20 | If the student's contribution includes a graphical interface or visual output, it is functional, readable, and free of glaring usability issues |
| Appropriate use of visual resources | 15 | Images, sprites, or generated visual assets are used purposefully, not decoratively or irrelevantly |
| Integration of graphics components into the solution | 20 | The graphics/imaging code the student wrote is not a standalone demo — it is wired into the group's actual application logic |
| Individual contribution clarity | 10 | The professor can clearly identify which part of the group deliverable is this specific student's work (via commit history, a stated role, or a individually-presented segment) |
| Presentation and final demonstration | 10 | The student can explain and demonstrate their graphics contribution live during Invenio Fest |
| **Total** | **100** | Scaled to 20% of final grade |

**Cross-course note:** This rubric is independent of whatever rubric the student's other trimester courses apply to the same Invenio Fest project — per `21_COURSE_SCHEDULE.md` §3 Class 12 table, each course evaluates its own dimension.

---

## 8. Final Grade Computation

```
Final Grade = (Quices_avg × 0.15)
            + (Labs_avg × 0.20)
            + (Eval_Practica_I × 0.15)
            + (Eval_Practica_II × 0.15)
            + (Eval_Practica_III × 0.15)
            + (Invenio_Fest × 0.20)
```

Where each term on the right is the percentage score (0.0–1.0) on that instrument's 100-point rubric above, and the weights sum to 1.00 (100%), matching `21_COURSE_SCHEDULE.md` §5 exactly.

---

## 9. Grading Consistency Notes for Multiple Graders

If a Teaching Assistant grades any portion of these rubrics:

1. **Calibration session required** before Class 5 (first practical evaluation): professor and TA jointly grade 2–3 sample submissions and reconcile scoring differences before grading the full cohort.
2. **Code-quality criteria** (`02_CODEX_CONTEXT.md` §5–6 compliance) should be checked with a shared checklist, not subjective impression — use `29_GIT_WORKFLOW_AND_STANDARDS.md` §4's code review checklist as the literal grading instrument for any "code quality" line item above.
3. **Disagreements >15 points** between two graders on the same submission must be resolved by the professor directly, not averaged silently.

---

## 10. Rubric Cross-Reference Index

| Rubric Section | Evaluation Instrument | Official Weight | Source Document for Content Scope |
|---|---|---|---|
| §2 | Quices | 15% | `21_COURSE_SCHEDULE.md` §4, §6 |
| §3 | Prácticas de laboratorio | 20% | `21_COURSE_SCHEDULE.md` §4 |
| §4 | Evaluación Práctica I | 15% | `08_SYLLABUS_MAPPING.md` §12, `14_PROFESSOR_DELIVERABLE_MATRIX.md` §14.1 |
| §5 | Evaluación Práctica II | 15% | `08_SYLLABUS_MAPPING.md` §12, `14_PROFESSOR_DELIVERABLE_MATRIX.md` §14.2 |
| §6 | Evaluación Práctica III | 15% | `08_SYLLABUS_MAPPING.md` §12, `14_PROFESSOR_DELIVERABLE_MATRIX.md` §14.3 |
| §7 | Invenio Fest | 20% | `21_COURSE_SCHEDULE.md` §3 Class 12 |


---
## 🔗 Documentos Relacionados

- [[30_ASSIGNMENT_01_STAGE_DESIGN.md|Assignment 1: Stage Design]]
- [[31_ASSIGNMENT_02_BOSS_DESIGN.md|Assignment 2: Boss Design]]
- [[32_ASSIGNMENT_03_LAB_EXERCISES.md|Assignment 3: Lab Exercises]]
- [[33_ASSIGNMENT_04_FINAL_PROJECT.md|Assignment 4: Final Project]]

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
