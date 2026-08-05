---
document_id: "LOI-EDU-034B"
title: "Legacy of InFest — Educational Roadmap"
aliases: ["Educational Roadmap"]
tags: ["educational", "roadmap", "pedagogy"]
description: "Educational roadmap"
source: "docs/84_EDUCATIONAL_ROADMAP.md"
date_processed: "2026-07-14"
---

# Legacy of InFest — Educational Roadmap

**Document ID:** LOI-EDUROADMAP-034  
**Version:** 1.0.0  
**Status:** Official  
**Audience:** Students, Teaching Assistants, Professor

---

## 1. Purpose

This document maps the Legacy of InFest engine and framework to the course curriculum.
Each academic unit corresponds to interactive lab scenes, framework processing modules, and
stage implementation tasks that students complete during the semester.

---

## 2. Unit-by-Unit Learning Path

### Unit II — Vectors (Theory + Engine)

| Component | What you interact with | What you learn |
|---|---|---|
| `VectorLabScene` | Drag two points; see vector arrow, components, length, dot product | Vector arithmetic, normalization, pursuit movement |
| `EnemyWalker` (patrol + alerted state) | Enemy moves toward player using normalized direction | Normalized direction vectors in game AI |
| `Player.physics` (movement code) | Walk, jump, knockback velocity | Velocity as a 2D vector, frame-rate independence |

**Lab:** VectorLabScene — FREE MOVE + CHASE modes  
**Stage task:** Implement enemy patrol with correct direction vector

---

### Unit II/III — 2D Transformations

| Component | What you interact with | What you learn |
|---|---|---|
| `TransformLabScene` | Apply translate/rotate/scale/shear; see live 3×3 matrix | Affine transformation matrices, non-commutativity |
| `Camera` (world-to-screen) | Camera follows player with parallax | Coordinate system transforms |
| `BossVenado` (phase transitions) | Boss changes size/behavior per phase | Scaling + rotation applied to game entities |

**Lab:** TransformLabScene — all 5 modes  
**Stage task:** Apply at least one 2D transformation to an entity or camera effect

---

### Unit III — Curves & Interpolation

| Component | What you interact with | What you learn |
|---|---|---|
| `CurveEditorScene` | Drag control points; view Bézier/spline curves | Bézier, Catmull-Rom, B-Spline, de Casteljau algorithm |
| `InterpolationLabScene` | Adjust t; view lerp + 10 easing functions | Linear interpolation, easing, keyframe animation |
| `CurveTools.bezier()` | Tool function used by CurveEditorScene | Implementation of curve evaluation |

**Lab:** CurveEditorScene + InterpolationLabScene  
**Stage task:** Use an easing function for animation or camera movement

---

### Unit V — Color Spaces & Alpha Blending

| Component | What you interact with | What you learn |
|---|---|---|
| `ColorTheoryScene` | RGB/HSV/HSL/CMYK sliders; step-by-step conversion | Color space math, perceptual vs. linear spaces |
| `ColorTools` (all functions) | Tool functions for conversion + alpha blend | Formula-level implementation |
| `FilterTools.adjust_brightness/contrast` | Brightness/contrast slider in FilterDemoScene | Per-channel color operations |

**Lab:** ColorTheoryScene — all 6 modes (especially Challenge mode)  
**Stage task:** Apply color adjustment to a game surface

---

### Unit V/VIII — Noise & Procedural Generation

| Component | What you interact with | What you learn |
|---|---|---|
| `NoiseLabScene` | Adjust octaves/persistence/lacunarity/scale/seed | Value noise, Perlin noise, fractal noise |
| Procedural generation in student stages | Generate terrain, textures, or enemy patterns | Noise as a building block |

**Lab:** NoiseLabScene — all 3 noise types  
**Stage task:** Generate a procedural element using noise

---

### Unit VI — AABB Collision

| Component | What you interact with | What you learn |
|---|---|---|
| `CollisionLabScene` | Y-FIRST (bug) vs X-FIRST (correct) modes | Axis-separated collision resolution |
| `Player._resolve_collision()` | Player collision with solid tiles | prev_bottom, grounded detection, one-way platforms |
| `EnemyWalker._post_update()` | Y-snapping to floor | Collision rect iteration |

**Lab:** CollisionLabScene — all 3 modes, auto-demo B key  
**Stage task:** Implement collision in student stage

---

### Unit VII — Digital Image Processing

| Component | What you interact with | What you learn |
|---|---|---|
| `FilterDemoScene` | 9 modes: histogram, brightness, contrast, kernels, Gaussian, Sobel, Canny, equalize | Full Unit VII toolset |
| `FilterTools` (all functions) | Tool functions called by FilterDemoScene | Kernel convolution, edge detection |
| `BossVenado` (Sobel aura) | Sobel edge detection as visual effect | Real-time image processing on game surfaces |

**Lab:** FilterDemoScene — all 9 modes  
**Practical Exam II:** Reproduce target outputs using specific parameters

---

### Unit VIII — Segmentation & Analysis

| Component | What you interact with | What you learn |
|---|---|---|
| `VisionDemoScene` | 10 modes: threshold, Otsu, morphology, components, regions, watershed, features | Full Unit VIII toolset |
| `VisionTools` (all functions) | Tool functions called by VisionDemoScene | Binary masks, region analysis, HOG/LBP features |
| `NoiseLabScene` (Perlin/value noise) | Noise as grayscale texture | Thresholding a noise field |

**Lab:** VisionDemoScene — all 10 modes  
**Practical Exam II:** Segmentation and region analysis tasks

---

### Unit IX — Pattern Recognition

| Component | What you interact with | What you learn |
|---|---|---|
| `PatternDemoScene` | 5 modes: inference, feature compare, class grid, confusion, pipeline | Full ML pipeline |
| `PatternRecognitionTools` | train/evaluate/save/load/classify | k-NN, decision tree, random forest, SVM |
| Model loading (L key) | Load your own .pkl model into the scene | Model serialization and deployment |

**Lab:** PatternDemoScene — all 5 modes  
**Practical Exam III:** Train a classifier and demonstrate inference

---

## 3. Stage Progression

| Stage | When | What you build |
|---|---|---|
| Stage 0 | Given (professor-built) | Reference implementation — all 7 zones, 27 tutorial messages, 5 checkpoints |
| Stage 1 | Mid-semester | Your first playable stage with enemies, platforms, and at least one processing effect |
| Stage 2 | Late semester | Add segmentation (threshold/morphology) and feature extraction |
| Stage 3 | Final project | Full pipeline: filter → segment → classify, with a trained model |

Each stage reuses the same engine infrastructure. The progression is cumulative:
Stage 1 adds gameplay, Stage 2 adds vision, Stage 3 adds pattern recognition.

---

## 4. Framework vs. Engine: What Students Modify

| Layer | What it is | Can students modify? |
|---|---|---|
| `src/engine/` | Core game loop, input, audio, scene management, UI | **No** — professor-owned |
| `src/framework/` | Entities, processing tools (Color/Curve/Filter/Vision/Pattern) | **No** — professor-owned reference implementations |
| `src/stages/stage0/` | Stage 0 (reference stage) | **No** — professor-owned |
| `src/engine/scenes/*_lab_*` | Theory lab scenes (Vector, Transform, etc.) | **No** — professor-owned |
| `src/engine/scenes/*_demo_*` | Demo scenes (Filter, Vision, Pattern) | **No** — professor-owned |
| `student_templates/` | Stage/boss templates | **Yes** — students copy and modify |
| Student's own stage directory | `src/stages/stageN/` (student-created) | **Yes** — student-owned |
| `student_assets/` | Student sprites, models, datasets | **Yes** — student-owned |

The processing tools (`FilterTools`, `VisionTools`, `PatternRecognitionTools`) are called by student code but are not modified by students. Students **use** the tools; the professor **maintains** the tools.

---

## 5. Assessment Map

| Assessment | Units | Scene Used | What You Do |
|---|---|---|---|
| Practical Exam I | II, III, V, VI | Lab scenes | Theory questions + short demo tasks |
| Practical Exam II | VII, VIII | FilterDemoScene, VisionDemoScene | Reproduce target outputs |
| Practical Exam III | IX | PatternDemoScene | Train + load + demonstrate model |
| Final presentation | All | Your stage + demo scenes | Live demo + README + Q&A |

---

## 6. Recommended Exploration Order

1. Stage 0 (full playthrough) — see what a complete stage looks like
2. VectorLabScene — understand vectors before touching enemy AI
3. CollisionLabScene — understand collision before building platforms
4. ColorTheoryScene — understand color before applying filters
5. TransformLabScene — understand transforms before camera effects
6. CurveEditorScene + InterpolationLabScene — curves and easing for animation
7. NoiseLabScene — procedural generation
8. FilterDemoScene — image processing for Stage 2
9. VisionDemoScene — segmentation for Stage 2/3
10. PatternDemoScene — pattern recognition for Stage 3


---
## 🔗 Documentos Relacionados

- [[34_CLASS_MATERIALS.md|Class Materials]]
- [[08_SYLLABUS_MAPPING.md|Syllabus Mapping]]
