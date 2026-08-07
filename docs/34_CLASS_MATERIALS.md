---
document_id: "LOI-CLASS-034"
title: "Class Materials — Lecture Slides & Live Coding Scripts"
aliases: ["Class Materials"]
tags: ["class", "materials", "academic"]
description: "Class materials and resources"
source: "docs/34_CLASS_MATERIALS.md"
date_processed: "2026-07-14"
---

# Class Materials — Lecture Slides & Live Coding Scripts

This document indexes all professor-facing presentation and live coding materials.
Files marked with ✅ exist in the repository. Files marked with ❌ are planned but not yet created.

## Unit I: Introduction (Week 1)
- ❌ `slides/u01_intro.md` — Course overview, engine architecture, game loop
- ❌ `live_code/u01_create_window.py` — Minimal pygame window setup
- ❌ `exercise/u01_setup_environment.md` — Dev environment setup guide

## Unit II: Vectors & Transforms (Weeks 2-3)
- ❌ `slides/u02_vectors.md` — Vector math, normalization, dot product, transforms
- ✅ `live_code/u02_vector_class.py` — Implement Vector2 from scratch (`docs/34_LIVE_CODE_u02_vector_class.py`)
- ❌ `exercise/u02_vector_chase.md` — Implement NPC chase behavior
- ❌ `slides/u02_transforms.md` — Translation, rotation, scale, shear matrices

## Unit III: Curves & Interpolation (Weeks 4-5)
- ❌ `slides/u03_curves.md` — Bezier, Catmull-Rom, B-spline, NURBS
- ❌ `live_code/u03_de_casteljau.py` — Implement de Casteljau algorithm
- ❌ `exercise/u03_curve_path.md` — Build a smooth patrol path
- ❌ `slides/u03_interpolation.md` — Lerp, easing functions, keyframes

## Unit IV: OOP & State Machines (Weeks 6-7)
- ❌ `slides/u04_inheritance.md` — BossBase subclass, override patterns
- ❌ `live_code/u04_boss_template.py` — Create a boss from scratch
- ❌ `slides/u04_state_machines.md` — Player states: idle, walk, jump, attack
- ❌ `exercise/u04_state_machine.md` — Add a new player state

## Unit V: Color Spaces (Week 8)
- ❌ `slides/u05_color.md` — RGB, HSV, HSL, CMYK, alpha blending
- ❌ `live_code/u05_rgb_to_hsv.py` — Implement color conversion
- ❌ `exercise/u05_color_match.md` — Color match challenge

## Unit VI: Collision Detection (Week 9)
- ❌ `slides/u06_collision.md` — AABB, circle, SAT, spatial hashing
- ❌ `live_code/u06_aabb_collision.py` — AABB overlap test
- ❌ `exercise/u06_collision_resolve.md` — Resolve collision penetration

## Unit VII: Image Processing (Weeks 10-11)
- ❌ `slides/u07_filters.md` — Convolution kernels, blur, sharpen, edge detection
- ✅ `live_code/u07_convolution.py` — Manual convolution implementation (`docs/34_LIVE_CODE_u07_convolution.py`)
- ❌ `exercise/u07_filter_chain.md` — Build a processing pipeline
- ❌ `slides/u07_histogram.md` — Histogram equalization, stretching

## Unit VIII: Computer Vision (Weeks 12-14)
- ❌ `slides/u08_vision.md` — Thresholding, morphology, components, watershed
- ❌ `live_code/u08_otsu.py` — Implement Otsu thresholding
- ❌ `exercise/u08_object_detection.md` — Detect and label objects
- ❌ `live_code/u08_feature_extraction.py` — HOG, LBP, color histograms

## Final Project (Weeks 15-16)
- ❌ `slides/u09_final_project.md` — Integration, submission requirements
- ❌ `exercise/u09_zone_design.md` — Complete zone deliverable checklist

## Delivery Format

Each `slides/uXX_*.md` file follows this structure:
1. Learning objectives (3-5 items)
2. Key concepts with diagrams (ASCII)
3. Code snippets showing framework usage
4. Common pitfalls
5. In-class activity

Each `live_code/` script is a minimal standalone Python file the professor
can run during lecture to demonstrate a concept interactively.

Each `exercise/` doc is a 1-page handout for in-class group work.

> **Note:** Only 2 of the 23 referenced files currently exist
> (`docs/34_LIVE_CODE_u02_vector_class.py` and `docs/34_LIVE_CODE_u07_convolution.py`).
> The remaining 21 files are placeholder entries to be created before the
> corresponding class session.


--- Traducción al Español ---

## Materiales de Clase

Este documento contiene referencias a los materiales didácticos utilizados en cada clase del curso.

### Estructura
- 11 clases efectivas de 4 horas (2h teoría + 2h práctica)
- 12ava sesión: Invenio Fest
- 6 instrumentos de evaluación oficiales

Para el cronograma detallado clase por clase, consultar el documento original en inglés.


---
## 🔗 Documentos Relacionados

- [[21_COURSE_SCHEDULE.md|Course Schedule]]
