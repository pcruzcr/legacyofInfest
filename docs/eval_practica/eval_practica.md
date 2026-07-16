---
document_id: "LOI-EVAL_PRACTICA-EVAL_PRACTICA"
title: "Evaluación Práctica — Practical Evaluations"
aliases: ["Eval Practica", "eval_practica"]
tags: ["evaluation", "practical", "academic"]
description: "Eval Practica document: eval_practica"
source: "docs/docs\eval_practica/eval_practica.md"
date_processed: "2026-07-14"
---

# Evaluación Práctica — Practical Evaluations

**Course:** Legacy of InFest
**Reference:** `docs/27_ACADEMIC_RUBRICS.md` SS4–SS6, `docs/14_PROFESSOR_DELIVERABLE_MATRIX.md` SS14

Three cumulative practical evaluations, each worth **15% of the final grade**.

---

## Evaluación Práctica I — Functional Prototype (Class 5, 15%)

**Units:** II (Vectors), III (Curves), IV (Scene/Object), V (Color/Transparency)

### Grading Rubric (100 pts)

| Criterion | Points | Requirement |
|-----------|--------|-------------|
| Coordinate systems & vectors | 20 | Custom entity uses explicit vector math (`vec2_normalize`/`vec2_dot`/`vec2_distance`) |
| Curves | 15 | Entity follows `CurveTools`-computed path; control points documented |
| Scene representation | 20 | TMX stage has all 8 required layers; OR boss arena geometry complete |
| Color/transparency | 15 | `ColorTools` operation (conversion or alpha blend) visually observable |
| Functional completeness | 20 | Stage loads; player traverses without crashing |
| README documentation | 10 | Valid front-matter per `23_DATA_SCHEMAS.md`; each unit's section explains formula |
| **Total** | **100** | Pass: ≥60/100 |

### Deliverables
- `<assignment>.tmx` with required layers
- `<assignment>.py` — correct `BaseScene` or `BossBase` subclass
- Custom entity using vector math
- Entity following a curve path
- Color space operation on a surface
- `README.md` with academic concepts

---

## Evaluación Práctica II — Vertical Slice (Class 8, 15%)

**Units:** +VI (Animation), +VII (Filters)

### Grading Rubric (100 pts)

| Criterion | Points | Requirement |
|-----------|--------|-------------|
| All Eval I criteria maintained | 25 | No regression |
| Animation & interaction (Unit VI) | 20 | Easing-driven animation; custom `EventBus` interaction |
| Histogram/brightness/contrast (Unit VII) | 15 | `FilterTools.compute_histogram()` drives logic |
| Convolution/blur/edge detection (Unit VII) | 20 | `apply_kernel`/`gaussian_blur`/`sobel_edge`/`canny_edge` |
| Functional completeness | 10 | Eval I still works; new features integrate cleanly |
| README documentation | 10 | Units VI–VII sections with before/after screenshots |
| **Total** | **100** | Pass: ≥60/100 |

### Deliverables
- All Eval I deliverables maintained
- Easing function used in animation
- `compute_histogram()` drives game logic
- `adjust_brightness()` or `adjust_contrast()` applied
- `apply_kernel()` or `gaussian_blur()` applied
- Edge detection result (Sobel or Canny)
- README: kernel matrix, before/after screenshots

---

## Evaluación Práctica III — Final Integration (Class 11, 15%)

**Units:** +VIII (Segmentation), +IX (Pattern Recognition)

### Grading Rubric (100 pts)

| Criterion | Points | Requirement |
|-----------|--------|-------------|
| All prior criteria maintained | 20 | Eval I + II intact |
| Segmentation (Unit VIII) | 20 | Threshold + morphology + connected components |
| Feature extraction & classification (Unit IX) | 25 | Features feed trained classifier; output changes behavior in ≥2 ways |
| Model quality | 15 | ≥10 samples/class, ≥2 classes, accuracy ≥0.70 |
| Full integration & polish | 10 | Complete, playable, no console errors |
| README documentation | 10 | Full training pipeline: dataset, hyperparams, accuracy, confusion matrix |
| **Total** | **100** | **15% of final grade** |

### Deliverables
- All Eval I + II requirements maintained
- `threshold_binary()` or `threshold_otsu()` applied
- Morphological operation applied
- `connected_components()` or `analyze_regions()` used
- `extract_features()` produces training features
- Labeled dataset in `assets/datasets/`
- Trained model (`.pkl`)
- `EvaluationResult` with accuracy ≥70% in README
- Classifier runs at runtime; result changes game behavior in ≥2 ways
- README: full training pipeline documentation
