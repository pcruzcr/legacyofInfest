# Legacy of InFest — Course Schedule

**Document ID:** LOI-SCHEDULE-021  
**Version:** 1.0.0  
**Status:** Official  
**Compatibility:** Requires LOI-AUDIT-000, LOI-SYLLABUS-008, LOI-MATRIX-014  
**Audience:** Professor, Students

---

## 1. Overview

Computación Gráfica y Procesamiento de Imágenes I (TIIT3002.1) is a trimestral course delivered in **11 effective classes of 4 hours each**, structured as **2 hours of theory followed by 2 hours of practice/examples/exercises**. A 12th session is reserved for **Invenio Fest**, the interdisciplinary group project festival that is graded separately from this course but receives a 20% weight within it (see Section 5).

Each student selects **one** Legacy of InFest Stage or Boss in Class 1 and develops it across the trimester through three cumulative practical evaluations (Evaluación Práctica I, II, III), culminating in a fully functional individual deliverable by Class 10–11.

---

## 2. Schedule at a Glance

| Class | Theory Focus (2h) | Practice Focus (2h) | Evaluation Event |
|---|---|---|---|
| 1 | Unit I — Intro to Computer Graphics | Framework orientation, Stage/Boss selection, environment setup | — |
| 2 | Unit II — Coordinate Systems & Transformations | Vector math labs + TransformLabScene (Unit II/III) | Quiz 1 |
| 3 | Unit II (cont.) — Matrices, Homogeneous Coords | Hitbox/hurtbox transform exercises | Lab 1 |
| 4 | Unit III — Curves & Geometric Modeling | Bézier/B-Spline path exercises + InterpolationLabScene | Quiz 2 |
| 5 | Unit IV — Objects, Scenes, Layers | TMX layer construction, sprite/scene labs | **Evaluación Práctica I — Prototipo Funcional** |
| 6 | Unit V — Color, Transparency, Lighting | Color space conversion labs, alpha blending | Quiz 3 + Lab 2 |
| 7 | Unit VI — Texturing, Animation, Interaction | Sprite sheets, easing, collision labs | — |
| 8 | Unit VII — Digital Image Processing | Histogram, brightness/contrast, convolution, Sobel/Canny labs + NoiseLabScene | **Evaluación Práctica II — Vertical Slice** |
| 9 | Unit VIII — Segmentation & Image Analysis | Threshold, Otsu, morphology, region analysis labs | Quiz 4 + Lab 3 |
| 10 | Unit IX — Integrative Applications | Pattern recognition pipeline, classifier training labs | — |
| 11 | Course Integration & Review | Final stage/boss polishing, integration testing | **Evaluación Práctica III — Integración Final** |
| 12 | — | **Invenio Fest** (interdisciplinary group presentation) | **Proyecto Integrador Invenio Fest** |

---

## 3. Class-by-Class Detail

### Class 1 — Foundations and Project Kickoff

**Theory (2h) — Unit I: Introduction to Computer Graphics**
- Historical evolution of computer graphics
- Application domains
- Graphics systems, hardware and software
- Raster vs. vector images
- Resolution and color depth
- Introduction to the graphics pipeline

**Practice (2h) — Framework Orientation**
- Repository walkthrough: `docs/`, `assets/`, `src/`, `student_templates/`, `main.py`, `requirements.txt`
- Environment setup: virtual environment, `requirements.txt` install
- Running Stage 0 for the first time
- **Stage/Boss Selection:** Each student individually selects one Stage or Boss from the available roster (see `16_WORLD_DESIGN.md` and `17_BOSS_SPEC.md`). Selection is recorded by the professor.
- Introduction to `student_templates/` scaffold

**Deliverable:** None graded. Stage/Boss assignment confirmed.

---

### Class 2 — Coordinate Systems and Vectors

**Theory (2h) — Unit II (Part 1)**
- 2D and 3D coordinate systems
- Applied vector algebra
- Vectors and matrices

**Practice (2h)**
- **VectorLabScene** (Unit II theory lab): interactive vector arithmetic, normalization, dot product, pursuit movement
- Lab exercises using `engine/utils/math_utils.py`: `vec2_normalize`, `vec2_dot`, `vec2_distance`
- Applying vector math to a custom entity's movement within the student's assigned Stage/Boss scaffold

**Evaluation:** Quiz 1 — fundamental concepts of Unit I and Unit II (vectors, coordinate systems)

---

### Class 3 — Transformations and Homogeneous Coordinates

**Theory (2h) — Unit II (Part 2)**
- Translation, rotation, scaling, reflection
- Homogeneous coordinates
- Composition of transformations

**Practice (2h)**
- Hitbox/hurtbox local-to-world transformation exercises (see `04_PLAYER_SPEC.md` §13.4)
- Implementing translation matrices for custom entity bounding boxes

**Evaluation:** Lab 1 (laboratory practice grade) — geometric transformations applied via Python

---

### Class 4 — Curves and Geometric Modeling

**Theory (2h) — Unit III**
- Parametric curves
- Bernstein polynomials
- Bézier curves
- B-Spline curves
- Introduction to NURBS
- Trajectory representation

**Practice (2h)**
- **CurveEditorScene** (Unit III theory lab): interactive Bézier, Catmull-Rom, B-Spline with draggable control points
- `CurveTools.bezier()`, `CurveTools.b_spline()`, `CurveTools.sample_path()` exercises
- Designing a patrol path or projectile trajectory for the student's assigned Stage/Boss using curve mathematics

**Evaluation:** Quiz 2 — curve theory and Bernstein basis

---

### Class 5 — Scene Representation and First Practical Evaluation

**Theory (2h) — Unit IV**
- Computational representation of graphic objects
- Scenes and visual structures
- Sprites and graphic elements
- Layers and visual organization
- Buffers and frame buffers
- Basic graphics resource management and optimization

**Practice (2h)**
- TMX layer construction for the student's assigned Stage (or arena construction for assigned Boss)
- Scene lifecycle implementation (`BaseScene` subclass)
- Integration checkpoint: coordinates, transformations, basic scenario, initial interaction

**Evaluation: Evaluación Práctica I — Prototipo Funcional (15%)**

Demuestra:
- Representación gráfica
- Sistemas de coordenadas
- Transformaciones geométricas
- Curvas básicas

Producto esperado: Primer avance funcional del nivel o jefe asignado dentro del proyecto Legacy of InFest.

---

### Class 6 — Color, Transparency, and Lighting

**Theory (2h) — Unit V**
- Visual perception
- RGB, CMYK, HSV, and HSL models
- Conversion between color spaces
- Transparency and image composition
- Alpha blending
- Fundamentals of computational lighting
- Basic shading models

**Practice (2h)**
- **ColorTheoryScene** (Unit V theory lab): interactive RGB/HSV/HSL/CMYK explorers, step-by-step algorithm view, alpha blending demo, color matching challenge
- `ColorTools` conversion exercises (RGB↔HSV↔HSL↔CMYK)
- Alpha blending exercises applied to the student's assigned Stage/Boss visuals

**Evaluation:** Quiz 3 — color theory and color space conversion + Lab 2 (laboratory practice grade) — color and lighting applied via Python

---

### Class 7 — Texturing, Animation, and Interaction

**Theory (2h) — Unit VI**
- Digital texturing
- Texture mapping
- Sprites and sprite sheets
- Computational animation
- Interpolation
- Transformation-based animation
- Basic collisions
- Interaction between graphic objects

**Practice (2h)**
- **CollisionLabScene** (Unit VI theory lab): interactive AABB collision with Y-first bug vs X-first correct, one-way platforms
- Sprite sheet animation implementation for the student's custom entity
- Easing function exercises (`pytweening`-backed `math_utils` functions)
- AABB collision and EventBus interaction exercises

**Evaluation:** None formally scheduled — exercises feed into Evaluación Práctica II in Class 8.

---

### Class 8 — Digital Image Processing and Second Practical Evaluation

**Theory (2h) — Unit VII**
- Image acquisition
- Histograms
- Image enhancement
- Brightness and contrast adjustment
- Spatial filtering
- Convolution
- Noise reduction
- Edge detection
- Sobel and Canny operators

**Practice (2h)**
- `FilterTools` exercises: `compute_histogram`, `adjust_brightness`, `adjust_contrast`, `apply_kernel`, `gaussian_blur`, `sobel_edge`, `canny_edge`
- Using `FilterDemoScene` (see `15_ACADEMIC_DEMO_SCENES.md`) to calibrate parameters
- Integration checkpoint: curves, scene representation, color/transparency, textures/animation

**Evaluation: Evaluación Práctica II — Vertical Slice (15%)**

Demuestra:
- Curvas y modelado
- Representación de escenas
- Color y transparencia
- Texturas y animación
- Representación visual avanzada

Producto esperado: Versión intermedia funcional del nivel o jefe asignado.

---

### Class 9 — Segmentation and Image Analysis

**Theory (2h) — Unit VIII**
- Image segmentation
- Thresholding
- Region-based segmentation
- Morphological operations
- Dilation and erosion
- Opening and closing
- Watershed
- Feature extraction
- Introduction to pattern recognition

**Practice (2h)**
- `VisionTools` exercises: `threshold_binary`, `threshold_otsu`, morphological operations, `connected_components`, `analyze_regions`, `watershed_segment`
- Using `VisionDemoScene` to visualize segmentation results on the student's Stage/Boss surfaces

**Evaluation:** Quiz 4 — segmentation and morphology theory + Lab 3 (laboratory practice grade) — segmentation and visual analysis applied via Python

---

### Class 10 — Integrative Applications

**Theory (2h) — Unit IX**
- Information visualization
- Graphical user interfaces
- Interactive systems
- Computer vision
- Pattern recognition
- Business and industrial applications
- Integration of computer graphics and image processing techniques

**Practice (2h)**
- `PatternRecognitionTools` exercises: dataset construction, `train()`, `evaluate()`, `save_model()`, `predict()`
- Using `PatternDemoScene` to validate trained models
- Building the final integration pipeline for the student's assigned Stage/Boss

**Evaluation:** None formally scheduled — exercises feed into Evaluación Práctica III in Class 11.

---

### Class 11 — Final Integration and Third Practical Evaluation

**Theory (2h) — Course Integration and Review**
- Cross-unit review: how Units I–IX combine into a single functional application
- Software quality, documentation, and engineering best-practice review (per syllabus §11, "Desarrollo de Soluciones Tecnológicas")
- Preparation guidance for Invenio Fest presentation

**Practice (2h)**
- Final polishing and integration testing of the student's assigned Stage/Boss
- README and technical documentation finalization
- Peer review / dry-run presentations (formative, ungraded)

**Evaluation: Evaluación Práctica III — Integración Final (15%)**

Demuestra:
- Procesamiento digital de imágenes
- Segmentación
- Reconocimiento básico de patrones
- Integración de todos los contenidos del curso

Producto esperado: Versión final funcional del nivel o jefe asignado dentro de Legacy of InFest.

---

### Class 12 — Invenio Fest

**Format:** Interdisciplinary group project festival. Not a regular class session of this course; students present a group project ("proyecto semilla macro") that integrates content from all courses of the trimester.

**Computación Gráfica y Procesamiento de Imágenes I evaluates, from this course's perspective:**
- Aplicación efectiva de técnicas visuales
- Calidad de la interfaz gráfica
- Uso apropiado de imágenes y recursos visuales
- Integración de componentes gráficos dentro de la solución
- Contribución individual al proyecto grupal
- Presentación y demostración final

**Evaluation: Proyecto Integrador Invenio Fest (20%)**

**Important distinction (per syllabus, verbatim intent preserved):**

| | Legacy of InFest | Invenio Fest |
|---|---|---|
| Scope | Individual | Grupal, interdisciplinario |
| Belongs to | This course only | Integrates all courses of the trimester |
| Evaluates | Computación Gráfica y Procesamiento de Imágenes | Cross-disciplinary integration |

Knowledge and code produced in Legacy of InFest may be transferred into the student's Invenio Fest group project, consistent with Universidad Invenio's dual-learning model.

---

## 4. Quiz and Lab Schedule Summary

| Instrument | Class | Topic Coverage |
|---|---|---|
| Quiz 1 | 2 | Unit I + Unit II (vectors, coordinate systems) |
| Lab 1 | 3 | Unit II (transformations, homogeneous coordinates) |
| Quiz 2 | 4 | Unit III (curves, Bernstein polynomials) |
| Quiz 3 | 6 | Unit V (color theory, color space conversion) |
| Lab 2 | 6 | Unit V (color and lighting applied) |
| Quiz 4 | 9 | Unit VIII (segmentation, morphology theory) |
| Lab 3 | 9 | Unit VIII (segmentation and visual analysis applied) |

**Note:** The exact count and distribution of quizzes and labs within the 15%/20% pools is at the professor's discretion per syllabus §8 ("La persona docente podrá incorporar..."); the table above reflects one valid distribution consistent with the 11-class structure. Additional short quizzes or labs may be added in Classes 1, 5, 7, 8, 10, or 11 without contradicting the syllabus, provided the **total** Quices weight remains 15% and the total Prácticas de laboratorio weight remains 20%.

---

## 5. Official Evaluation Weighting (Verbatim from Syllabus)

| Instrumento | Porcentaje | Class(es) |
|---|---|---|
| Quices | 15% | Distributed across Classes 2, 4, 6, 9 (see §4) |
| Prácticas de laboratorio | 20% | Distributed across Classes 3, 6, 9 (see §4) |
| Evaluación Práctica I – Prototipo Funcional | 15% | Class 5 |
| Evaluación Práctica II – Vertical Slice | 15% | Class 8 |
| Evaluación Práctica III – Integración Final | 15% | Class 11 |
| Proyecto Integrador Invenio Fest | 20% | Class 12 |
| **Total** | **100%** | |

---

## 6. Syllabus Unit-to-Class Mapping

| Syllabus Unit | Title | Primary Class |
|---|---|---|
| I | Introducción a la Computación Gráfica | Class 1 |
| II | Sistemas de Coordenadas y Transformaciones Geométricas | Classes 2–3 |
| III | Curvas y Modelado Geométrico | Class 4 |
| IV | Representación de Objetos y Escenas | Class 5 |
| V | Color, Transparencia e Iluminación | Class 6 |
| VI | Texturizado, Animación e Interacción | Class 7 |
| VII | Procesamiento Digital de Imágenes | Class 8 |
| VIII | Segmentación y Análisis de Imágenes | Class 9 |
| IX | Aplicaciones Integradoras | Class 10 |
| — | Integration & Review | Class 11 |
| — | Invenio Fest | Class 12 |

This mapping is consistent with `08_SYLLABUS_MAPPING.md` (Documents 01–10 package), which defines the academic content of each unit in full detail. This schedule adds only the temporal sequencing across the trimester's 11+1 sessions.

---

## 7. Relationship to Existing Stage/Boss Milestone Documentation

The three Evaluación Práctica checkpoints in this schedule (Class 5, 8, 11) correspond to the same three cumulative milestones already defined conceptually in `08_SYLLABUS_MAPPING.md` and `14_PROFESSOR_DELIVERABLE_MATRIX.md` — they are now anchored to specific class sessions:

| Milestone | Class | Official Name | Prior Internal Reference |
|---|---|---|---|
| Milestone 1 | Class 5 | Evaluación Práctica I – Prototipo Funcional | Previously referred to informally as "Stage 1 Deliverable" |
| Milestone 2 | Class 8 | Evaluación Práctica II – Vertical Slice | Previously referred to informally as "Stage 2 Deliverable" |
| Milestone 3 | Class 11 | Evaluación Práctica III – Integración Final | Previously referred to informally as "Stage 3 Deliverable" |

**Clarification (see `00_SYLLABUS_ALIGNMENT_AUDIT.md` §2 A.1):** All three milestones apply to the **same single Stage or Boss** that the student selected in Class 1. "Stage 1 / Stage 2 / Stage 3" in earlier internal documentation never meant three different stages — it meant three sequential states of completeness (prototype → vertical slice → final integration) of one assignment. This schedule uses the official Evaluación Práctica I/II/III naming going forward to eliminate ambiguity.

---

## Appendix A — Corrected Repository Structure Reference

See `00_SYLLABUS_ALIGNMENT_AUDIT.md` §7 for the full corrected repository tree reflecting the real GitHub structure (`docs/`, `assets/`, `src/`, `student_templates/`, `main.py`, `requirements.txt`).
