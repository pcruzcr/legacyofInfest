---
document_id: "LOI-DELIVERABLE-014"
title: "Legacy of InFest — Professor Deliverable Matrix"
aliases: ["Professor Deliverable Matrix"]
tags: ["deliverable", "academic", "matrix"]
description: "Full syllabus-to-framework-to-assessment traceability"
source: "docs/14_PROFESSOR_DELIVERABLE_MATRIX.md"
date_processed: "2026-07-14"
---

# Legacy of InFest — Professor Deliverable Matrix

**Document ID:** LOI-MATRIX-014  
**Version:** 1.0.0  
**Status:** Official  
**Compatibility:** All LOI documents  
**Audience:** Professor, Teaching Assistants, University Academic Committee

---

<!-- cita-historica -->
> **Corrección AUD-150 — nombres que este documento daba por existentes.**
> Comprobados uno por uno contra el código. Ninguno rompe nada al jugar; todos
> engañan a quien lea el documento para programar.
>
> * `SpriteSheet` y `AnimationController` **no existen como clases.** La carga de hojas la hace `AssetLoader`, y la animación vive dentro de cada entidad (`_advance_animation`, `_sprite_frames`). La rúbrica sigue siendo válida —lo que se evalúa es que el estudiante anime su entidad—; lo que hay que leer distinto es dónde mirar el código.
> * `OneWay_` no es un prefijo de nada. Las plataformas atravesables se declaran con el tipo «Platform» en la capa `Collision`.
<!-- /cita-historica -->


## 1. Overview

This document provides complete traceability between the course syllabus and the Legacy of InFest framework. For every topic in every course unit, it defines what the professor delivers, what the student produces, which framework component is used, which libraries participate, where the concept appears in Stage 0, what a student stage must demonstrate, and how it is assessed.

This matrix is the authoritative reference for:
- Designing evaluation instruments
- Reviewing student stage submissions
- Auditing framework completeness
- Aligning course content with software deliverables

---

## 2. Reading Guide

Each unit section contains a **deliverable table** covering every topic, followed by a **learning evidence summary** for the unit as a whole.

| Column | Meaning |
|---|---|
| **Topic** | Exact syllabus topic name |
| **Professor Delivers** | What exists before the student starts |
| **Student Delivers** | What the student must produce |
| **Framework Component** | Module in `engine/` or `framework/` that carries this |
| **Libraries** | Third-party libraries involved (hidden from students) |
| **Stage 0 Example** | Where this is demonstrated in the professor's stage |
| **Student Stage** | Which stage is expected to demonstrate this |
| **Assessment** | Which graded instrument covers this |
| **Doc Reference** | Which specification document covers this in detail |

---

## 3. Unit I — Introduction to Computer Graphics

### 3.1 Deliverable Table

| Topic | Professor Delivers | Student Delivers | Framework Component | Libraries | Stage 0 Example | Student Stage | Assessment | Doc Reference |
|---|---|---|---|---|---|---|---|---|
| History of CG / raster vs. vector | Lecture slides + framework as a running raster system | README section explaining internal resolution choice | `engine/core/app.py` (internal surface) | `pygame-ce` | Entire Stage 0 running at 320×224 | All stages | Exam I (theory) | LOI-ARCH-003 |
| Display technology and pixel grids | `settings.py` constants (`INTERNAL_WIDTH`, `INTERNAL_HEIGHT`, `TILE_SIZE`) | README documents tile grid used in TMX | `engine/core/settings.py` | `pygame-ce` | Debug overlay shows pixel grid (F1) | All stages | Exam I | LOI-ARCH-003 §2.1 |
| The game loop as a real-time graphics system | `App.run()` main loop with delta time | README explains the update/draw cycle in their stage | `engine/core/app.py`, `engine/core/clock.py` | `pygame-ce` | Running stage — 60 FPS observable | All stages | Exam I + Stage README | LOI-ARCH-003 §5 |
| Frame rate, delta time, temporal coherence | `DeltaClock.tick()` returning `dt` | All entity movement uses `velocity * dt`; documented | `engine/core/clock.py` | `pygame-ce` | All entities in Stage 0 move correctly at any FPS | All stages | Code review | LOI-ARCH-003 §2.1 |
| Coordinate systems (screen space intro) | `Camera.world_to_screen()` and `Camera.screen_to_world()` | Stage uses camera offset correctly in all entity draws | `framework/stage/camera.py` | `pygame-ce` | All entities in Stage 0 draw at correct screen positions | All stages | Code review | LOI-ARCH-003 §2.8 |

### 3.2 Learning Evidence — Unit I

A student demonstrates Unit I mastery when their stage:
- Runs stably at 60 FPS on the course development machine.
- Applies `dt` to all velocity-based movements (zero hardcoded pixel-per-frame values).
- Documents the game loop, frame rate, and coordinate system in their stage README.

---

## 4. Unit II — Coordinate Systems, Vectors, Matrices, Transformations

### 4.1 Deliverable Table

| Topic | Professor Delivers | Student Delivers | Framework Component | Libraries | Stage 0 Example | Student Stage | Assessment | Doc Reference |
|---|---|---|---|---|---|---|---|---|
| 2D Cartesian coordinate system | World vs. screen coordinate explanation in ARCH doc; `Camera.world_to_screen()` | Stage README explains world-space vs. screen-space | `framework/stage/camera.py` | `pygame-ce` | Debug mode shows coordinates | Stage 1 | Exam I + README | LOI-ARCH-003 §2.8 |
| Vector arithmetic | `math_utils.py`: `vec2_normalize`, `vec2_dot`, `vec2_distance`, `vec2_length` | At least one custom entity uses explicit vector math for movement | `engine/utils/math_utils.py` | `pygame-ce`, `numpy` | Zone E Shooter atan2 calculation | Stage 1 | Practical I | LOI-ARCH-003 §2.6 |
| Translation and rotation matrices | Player hitbox transform (local → world space documented in PLAYER spec) | README documents the local→world transform for their custom hitbox | `framework/entities/base_entity.py` | `pygame-ce` | Debug mode: hitboxes at correct world positions | Stage 1 | Code review + README | LOI-PLAYER-004 §12 |
| Homogeneous coordinates | Documented in PLAYER spec §13.4 as matrix illustration | Student documents the matrix form of their entity's translation | `framework/entities/base_entity.py` | `numpy` | Stage 0 source comments | Stage 1 | Exam I (theory) | LOI-PLAYER-004 §13.4 |
| Vector normalization for movement | `vec2_normalize()` in math_utils | Custom entity moves toward target at constant speed using normalization | `engine/utils/math_utils.py` | `numpy` | Player knockback direction vector | Stage 1 | Practical I | LOI-ARCH-003 §2.6 |
| Dot product and distance | `vec2_dot()`, `vec2_distance()` | Custom detection range uses distance calculation | `engine/utils/math_utils.py` | `numpy` | Enemy detection zone | Stage 1 | Practical I | LOI-ENEMY-005 §10.1 |
| Transformation of bounding boxes | `_update_rects()` in BaseEntity | Student's custom entity correctly updates hitbox/hurtbox in world space | `framework/entities/base_entity.py` | `pygame-ce` | All Stage 0 entities | Stage 1 | Code review | LOI-PLAYER-004 §10, §11 |

### 4.2 Learning Evidence — Unit II

A student demonstrates Unit II mastery when they can:
- Write the translation matrix for their entity's hitbox offset in their README.
- Show a custom entity using `vec2_normalize()` for constant-speed pursuit.
- Explain the difference between world-space and screen-space coordinates verbally in the final presentation.

---

## 5. Unit III — Bézier Curves, B-Splines, NURBS, Trajectories

### 5.1 Deliverable Table

| Topic | Professor Delivers | Student Delivers | Framework Component | Libraries | Stage 0 Example | Student Stage | Assessment | Doc Reference |
|---|---|---|---|---|---|---|---|---|
| Parametric curves | `CurveTools` module with all curve functions | At least one entity or effect follows a computed parametric path | `framework/processing/curve_tools.py` | `numpy` | Zone D Flying_02 (Bézier path) | Stage 1 | Practical I + Stage README | LOI-ARCH-003 §2.9 |
| Bernstein basis polynomials | `CurveTools.bezier()` implements Bernstein basis | README includes the Bernstein formula and the student's control points | `framework/processing/curve_tools.py` | `numpy` | Zone D debug mode shows control polygon | Stage 1 | Exam I (theory) + README | LOI-ARCH-003 §2.9 |
| De Casteljau algorithm | Implemented inside `bezier()` | Not required to implement — required to explain in README | `framework/processing/curve_tools.py` | `numpy` | Stage 0 source comments | Stage 1 | README | LOI-ARCH-003 §2.9 |
| B-Spline curves | `CurveTools.b_spline()` | Student demonstrates a B-Spline path (≥ 5 control points) | `framework/processing/curve_tools.py` | `numpy` | Not in Stage 0 — student first use | Stage 1 or 2 | Stage deliverable | LOI-ARCH-003 §2.9 |
| NURBS | `CurveTools.nurbs()` | Optional advanced: student demonstrates NURBS with custom weights | `framework/processing/curve_tools.py` | `numpy` | Not in Stage 0 | Stage 2 (optional) | Bonus | LOI-ARCH-003 §2.9 |
| Catmull-Rom splines | `CurveTools.catmull_rom()` | Student may use for smooth interpolation through waypoints | `framework/processing/curve_tools.py` | `numpy` | Not in Stage 0 | Stage 1 | Stage deliverable | LOI-ARCH-003 §2.9 |
| Path parametrization | `CurveTools.sample_path(path, t)` | Entity advances along path using `t` driven by speed | `framework/processing/curve_tools.py` | `numpy` | Zone D: Flying_02 path traversal | Stage 1 | Code review | LOI-ARCH-003 §2.9 |

### 5.2 Learning Evidence — Unit III

A student demonstrates Unit III mastery when they can:
- Present a diagram of their control points and the resulting curve.
- Explain what `t` represents in their path traversal implementation.
- Describe in writing the difference between Bézier, B-Spline, and Catmull-Rom for their specific use case.

---

## 6. Unit IV — Objects, Scenes, Layers, Sprites, Buffers

### 6.1 Deliverable Table

| Topic | Professor Delivers | Student Delivers | Framework Component | Libraries | Stage 0 Example | Student Stage | Assessment | Doc Reference |
|---|---|---|---|---|---|---|---|---|
| Scene graph concepts | `SceneManager` with push/pop/replace | Student stage implements `BaseScene` correctly with `on_enter`, `update`, `draw` | `engine/scene/scene_manager.py`, `engine/scene/base_scene.py` | `pygame-ce` | All scenes in the game flow | All stages | Code review | LOI-ARCH-003 §2.2 |
| Layered rendering | TMX layer system (BG_Far through FG_Overlay) | TMX map has all required layers; parallax visually observable | `framework/stage/stage_loader.py`, `pyscroll` | `pygame-ce`, `pyscroll`, `pytmx` | All zones: parallax scrolling | All stages | TMX review + demo | LOI-TMX-006 §3 |
| Sprite as textured quad | `AssetLoader` (AUD-150: no hay ninguna clase de hoja de sprites) | At least one custom animated sprite created by student | `engine/utils/asset_loader.py` | `pygame-ce` | Player and enemy sprites | All stages | Code review | LOI-ARCH-003 §2.6 |
| Sprite animation | la animación vive en cada entidad, no en un controlador aparte | Custom entity has multi-frame animation with correct FPS | `framework/entities/base_entity.py` + player/enemy | `pygame-ce` | All animated entities in Stage 0 | All stages | Code review | LOI-PLAYER-004 §9 |
| Double buffering | `App.internal_surface` (320×224) blitted to window | README explains double buffering (internal → window) | `engine/core/app.py` | `pygame-ce` | Entire Stage 0 | All stages (README) | README | LOI-ARCH-003 §4.1 |
| Z-ordering / draw calls | `BaseEntity.layer` property; pyscroll group | Entity layer values produce correct visual depth order | `framework/entities/base_entity.py`, `pyscroll` | `pygame-ce` | Stage 0 entities at correct depths | All stages | Visual review | LOI-ARCH-003 §2.7 |
| Object lifecycle | `BaseEntity.is_active`, `is_visible` | Custom entities correctly set `is_active = False` on death | `framework/entities/base_entity.py` | `pygame-ce` | Enemy death in Stage 0 | All stages | Code review | LOI-ARCH-003 §2.7 |

### 6.2 Learning Evidence — Unit IV

A student demonstrates Unit IV mastery when their stage:
- Has a correct TMX layer stack with visible parallax.
- Has at least one custom animated sprite with documented frame count and FPS.
- Includes a README diagram of the layer rendering order.

---

## 7. Unit V — RGB, HSV, HSL, CMYK, Transparency, Alpha Blending, Lighting

### 7.1 Deliverable Table

| Topic | Professor Delivers | Student Delivers | Framework Component | Libraries | Stage 0 Example | Student Stage | Assessment | Doc Reference |
|---|---|---|---|---|---|---|---|---|
| RGB color model | `ColorTools.surface_to_array()` returns RGB ndarray | Student documents an RGB value from their stage and explains each channel | `framework/processing/color_tools.py` | `numpy`, `pygame-ce` | Debug mode: pixel inspector | Stage 1 | Exam I (theory) + README | LOI-ARCH-003 §2.9 |
| HSV color model | `ColorTools.rgb_to_hsv()`, `hsv_to_rgb()` | Student applies HSV manipulation (e.g., hue rotation, saturation change) | `framework/processing/color_tools.py` | `numpy` | Not in Stage 0 — student first use | Stage 1 | Practical I | LOI-ARCH-003 §2.9 |
| HSL color model | `ColorTools.rgb_to_hsl()`, `hsl_to_rgb()` | Student applies lightness adjustment via HSL | `framework/processing/color_tools.py` | `numpy` | Not in Stage 0 | Stage 1 | Stage deliverable | LOI-ARCH-003 §2.9 |
| CMYK color model | `ColorTools.rgb_to_cmyk()`, `cmyk_to_rgb()` | Student converts a sprite palette to CMYK and documents the values | `framework/processing/color_tools.py` | `numpy` | Not in Stage 0 | Stage 1 (theory exercise) | README | LOI-ARCH-003 §2.9 |
| Alpha channel and transparency | `pygame.Surface.set_alpha()`, `ColorTools.alpha_blend()` | At least one visual effect uses alpha transparency | `framework/processing/color_tools.py` | `pygame-ce`, `numpy` | Debug overlays (semi-transparent) | Stage 1 | Code review | LOI-ARCH-003 §2.9 |
| Alpha blending equation | `ColorTools.alpha_blend()` | Student documents the blending formula in README: `out = src * α + dst * (1-α)` | `framework/processing/color_tools.py` | `numpy` | Invincibility flash | Stage 1 | README | LOI-ARCH-003 §2.9 |
| Simulated 2D lighting | `ColorTools.apply_tint()` + `adjust_brightness()` | Student creates a directional or ambient light effect using color tinting | `framework/processing/color_tools.py`, `framework/processing/filter_tools.py` | `numpy`, `pygame-ce` | Not in Stage 0 | Stage 1 or 2 | Stage deliverable | LOI-FILTER-011 §8.2 |

### 7.2 Learning Evidence — Unit V

A student demonstrates Unit V mastery when they can:
- Convert a sampled pixel from their stage between RGB, HSV, and HSL by hand (shown in README).
- Show a visual effect driven by a color space operation.
- Explain the alpha blending formula and how it is applied in their stage.

---

## 8. Unit VI — Textures, Animation, Interpolation, Collisions, Interaction

### 8.1 Deliverable Table

| Topic | Professor Delivers | Student Delivers | Framework Component | Libraries | Stage 0 Example | Student Stage | Assessment | Doc Reference |
|---|---|---|---|---|---|---|---|---|
| Texture mapping | `AssetLoader.load_image()` | Student's entities use correctly sized textures (16-color constraint) | `engine/utils/asset_loader.py` | `pygame-ce` | All sprite entities | All stages | Asset review | LOI-ARCH-003 §2.6 |
| Frame-based animation | `_advance_animation` y `_sprite_frames` en cada entidad | Custom entity animation with documented frame count, FPS, loop mode | `framework/entities/base_entity.py` | `pygame-ce` | Player and enemy animations | All stages | Code review | LOI-PLAYER-004 §9 |
| Linear interpolation | `math_utils.lerp()` | At least one lerp-driven value (camera follow, platform movement, fade) | `engine/utils/math_utils.py` | — | Camera follow uses lerp | Stage 1 or 2 | Code review | LOI-ARCH-003 §2.6 |
| Easing functions | `math_utils.ease_*` functions + `pytweening` | At least one entity or UI uses an ease function (not plain lerp) | `engine/utils/math_utils.py` | `pytweening` | Screen banner slide (ease_out_quad) | Stage 1 or 2 | Practical I | LOI-ARCH-003 §2.6 |
| AABB collision detection | Player and enemy collision resolution in engine | Student's custom entity resolves AABB collision correctly | `framework/entities/player.py`, `framework/entities/enemy_base.py` | `pygame-ce` | All Zone A–F interactions | All stages | Code review | LOI-PLAYER-004 §4.3 |
| Interaction events | `EventBus` pub/sub system | Custom trigger zone emits an event; another entity subscribes | `engine/core/event_bus.py` | — | Checkpoint → HUD; Shooter → projectile | Stage 1 or 2 | Code review | LOI-ARCH-003 §2.1 |
| One-way platforms | objetos de tipo «Platform» en la capa `Collision` (AUD-150: no hay ningún prefijo especial en los nombres) | Student designs a stage zone with one-way platforms | TMX `Collision` layer, `framework/stage/stage_loader.py` | `pygame-ce`, `pytmx` | Zone E one-way platform | Stage 1 or 2 | TMX review | LOI-TMX-006 §9.2 |

### 8.2 Learning Evidence — Unit VI

A student demonstrates Unit VI mastery when:
- Their custom entity uses `ease_out_quad` (or equivalent) and the visual deceleration is observable.
- Their stage has a working EventBus interaction between two entities.
- Their AABB collision is resolved without tunneling at 60 FPS.

---

## 9. Unit VII — Histogram, Brightness, Contrast, Convolution, Gaussian Blur, Sobel, Canny

### 9.1 Deliverable Table

| Topic | Professor Delivers | Student Delivers | Framework Component | Libraries | Stage 0 Example | Student Stage | Assessment | Doc Reference |
|---|---|---|---|---|---|---|---|---|
| Histogram | `FilterTools.compute_histogram()` | Student uses histogram output to trigger a game event; documents histogram shape | `framework/processing/filter_tools.py` | `numpy`, `pygame-ce` | Unit test + Zone F (demo) | Stage 2 | Practical II | LOI-FILTER-011 §8.1 |
| Histogram equalization | `FilterTools.histogram_equalize()` | Student applies equalization to a surface and shows before/after in README | `framework/processing/filter_tools.py` | `opencv-python`, `numpy` | Demo Scene | Stage 2 | Stage deliverable | LOI-FILTER-011 §8.1 |
| Brightness adjustment | `FilterTools.adjust_brightness()` | Student creates a health-based or time-based brightness effect | `framework/processing/filter_tools.py` | `numpy` | Zone F (demonstrated) | Stage 2 | Code review | LOI-FILTER-011 §8.2 |
| Contrast adjustment | `FilterTools.adjust_contrast()` | Student creates a contrast-based visual mode toggle | `framework/processing/filter_tools.py` | `numpy` | Demo Scene | Stage 2 | Stage deliverable | LOI-FILTER-011 §8.3 |
| Convolution | `FilterTools.apply_kernel()`, `get_standard_kernel()` | Student applies a custom or standard kernel and documents the kernel matrix | `framework/processing/filter_tools.py` | `scipy.ndimage`, `numpy` | Unit test | Stage 2 | Practical II | LOI-FILTER-011 §8.4 |
| Gaussian blur | `FilterTools.gaussian_blur()` | Student applies blur to a background or sprite region with documented sigma | `framework/processing/filter_tools.py` | `scipy.ndimage`, `numpy` | Demo Scene (interactive sigma) | Stage 2 | Code review | LOI-FILTER-011 §8.5 |
| Sobel edge detection | `FilterTools.sobel_edge()` | Student applies Sobel and uses the edge map as a visual overlay | `framework/processing/filter_tools.py` | `opencv-python`, `numpy` | Demo Scene | Stage 2 | Practical II | LOI-FILTER-011 §8.6 |
| Canny edge detection | `FilterTools.canny_edge()` | Student applies Canny with documented thresholds; shows result in README | `framework/processing/filter_tools.py` | `opencv-python`, `numpy` | Demo Scene | Stage 2 | Stage deliverable | LOI-FILTER-011 §8.6 |

### 9.2 Learning Evidence — Unit VII

A student demonstrates Unit VII mastery when they can:
- Write the mathematical definition of convolution and match it to their applied kernel.
- Show a histogram of a surface from their stage and explain what it reveals.
- Demonstrate a Sobel edge map and explain why certain edges appear stronger.
- Justify their Canny thresholds and explain hysteresis in their own words.

---

## 10. Unit VIII — Threshold, Otsu, Morphology, Connected Components, Watershed, Region Analysis, Feature Extraction

### 10.1 Deliverable Table

| Topic | Professor Delivers | Student Delivers | Framework Component | Libraries | Stage 0 Example | Student Stage | Assessment | Doc Reference |
|---|---|---|---|---|---|---|---|---|
| Binary thresholding | `VisionTools.threshold_binary()` | Student applies threshold to a stage surface; threshold value documented | `framework/processing/vision_tools.py` | `opencv-python`, `numpy` | Demo Scene | Stage 2 or 3 | Practical II | LOI-VISION-012 §8.1 |
| Otsu's method | `VisionTools.threshold_otsu()` | Student applies Otsu and documents the computed threshold | `framework/processing/vision_tools.py` | `opencv-python`, `numpy` | Demo Scene | Stage 2 or 3 | Practical II | LOI-VISION-012 §8.2 |
| Morphological erosion | `VisionTools.morphological_erode()` | Student applies erosion after threshold; shows noise removal | `framework/processing/vision_tools.py` | `opencv-python`, `numpy` | Demo Scene | Stage 2 or 3 | Code review | LOI-VISION-012 §9.1 |
| Morphological dilation | `VisionTools.morphological_dilate()` | Student applies dilation; shows gap filling | `framework/processing/vision_tools.py` | `opencv-python`, `numpy` | Demo Scene | Stage 2 or 3 | Code review | LOI-VISION-012 §9.2 |
| Opening and closing | `VisionTools.morphological_open()`, `morphological_close()` | Student documents the sequence (erosion→dilation or vice versa) | `framework/processing/vision_tools.py` | `opencv-python` | Demo Scene | Stage 3 | Stage deliverable | LOI-VISION-012 §9.3, §9.4 |
| Connected components | `VisionTools.connected_components()` | Student counts distinct regions; uses region count to drive game logic | `framework/processing/vision_tools.py` | `opencv-python`, `numpy` | Demo Scene | Stage 3 | Practical II | LOI-VISION-012 §10.1 |
| Region analysis | `VisionTools.analyze_regions()` | Student documents a `RegionInfo` object (area, centroid, bounding rect) | `framework/processing/vision_tools.py` | `scikit-image`, `opencv-python` | Demo Scene | Stage 3 | README + Practical II | LOI-VISION-012 §11.1 |
| Watershed segmentation | `VisionTools.watershed_segment()` | Student applies watershed and shows color-coded segment overlay in stage | `framework/processing/vision_tools.py` | `opencv-python`, `numpy` | Demo Scene | Stage 3 | Stage deliverable | LOI-VISION-012 §12.1 |
| Feature extraction (HOG, LBP) | `VisionTools.extract_hog()`, `extract_lbp()`, `extract_color_histogram()` | Student extracts features and documents vector dimensionality | `framework/processing/vision_tools.py` | `scikit-image`, `numpy` | Demo Scene | Stage 3 | Practical II + III | LOI-VISION-012 §13 |

### 10.2 Learning Evidence — Unit VIII

A student demonstrates Unit VIII mastery when:
- Their README contains a real `RegionInfo` printout from their stage.
- They show a before/after comparison of morphological operations.
- They explain Otsu's criterion (maximize inter-class variance) in their presentation.
- They demonstrate segmentation output changing game behavior in at least two cases.

---

## 11. Unit IX — Pattern Recognition, Classification, Computer Vision, Interactive Applications, Machine Learning

### 11.1 Deliverable Table

| Topic | Professor Delivers | Student Delivers | Framework Component | Libraries | Stage 0 Example | Student Stage | Assessment | Doc Reference |
|---|---|---|---|---|---|---|---|---|
| HOG descriptor | `PatternRecognitionTools.extract_hog()` (via VisionTools) | Student's README documents HOG parameters and vector length | `framework/processing/pattern_recognition_tools.py` | `scikit-image`, `numpy` | Demo Scene | Stage 3 | README + Practical III | LOI-PATTERN-013 §7.1 |
| LBP descriptor | `PatternRecognitionTools.extract_lbp()` | Student uses LBP and documents texture pattern interpretation | `framework/processing/pattern_recognition_tools.py` | `scikit-image`, `numpy` | Demo Scene | Stage 3 | README | LOI-PATTERN-013 §7.2 |
| Color histogram descriptor | `PatternRecognitionTools.extract_color_histogram()` | Student shows how color distribution distinguishes their classes | `framework/processing/pattern_recognition_tools.py` | `numpy` | Demo Scene | Stage 3 | README | LOI-PATTERN-013 §7.3 |
| Dataset construction | `tools/build_dataset.py` script (professor-provided) | Student builds a labeled `.npz` dataset (≥ 3 classes, ≥ 30 samples/class) | Build script + `student_assets/datasets/` | `numpy`, `scikit-image` | Sample dataset provided | Stage 3 | Dataset deliverable | LOI-PATTERN-013 §8 |
| K-NN classification | `PatternRecognitionTools.train(..., 'knn')` | Student trains, evaluates, and documents a k-NN model | `framework/processing/pattern_recognition_tools.py` | `scikit-learn` | Demo Scene | Stage 3 | Practical III | LOI-PATTERN-013 §14.1 |
| Decision tree | `PatternRecognitionTools.train(..., 'tree')` | Student trains a tree; documents depth and split criterion | `framework/processing/pattern_recognition_tools.py` | `scikit-learn` | Demo Scene | Stage 3 | Practical III | LOI-PATTERN-013 §14.2 |
| Random forest | `PatternRecognitionTools.train(..., 'forest')` | Student compares forest vs. single tree on their dataset | `framework/processing/pattern_recognition_tools.py` | `scikit-learn` | Demo Scene | Stage 3 | Stage deliverable | LOI-PATTERN-013 §14.3 |
| SVM | `PatternRecognitionTools.train(..., 'svm')` | Optional: student applies SVM and compares to other classifiers | `framework/processing/pattern_recognition_tools.py` | `scikit-learn` | Demo Scene | Stage 3 (optional) | Bonus | LOI-PATTERN-013 §14.4 |
| Model training pipeline | `train()` + `evaluate()` workflow | Student documents training accuracy, test accuracy, confusion matrix | `framework/processing/pattern_recognition_tools.py` | `scikit-learn`, `numpy` | Notebook template | Stage 3 | Practical III | LOI-PATTERN-013 §9, §10 |
| Model serialization | `save_model()` / `load_model()` | `.pkl` file in `student_assets/models/`; loaded in `on_enter()` | `framework/processing/pattern_recognition_tools.py` | `joblib` | — | Stage 3 | Code review | LOI-PATTERN-013 §11 |
| Runtime inference | `predict()` in game loop | Classification result changes observable game behavior | `framework/processing/pattern_recognition_tools.py` | `scikit-learn`, `numpy` | Demo Scene | Stage 3 | Live demo | LOI-PATTERN-013 §13.3 |
| Interactive application | Full pipeline: Filter → Vision → Pattern → Behavior | Stage 3 is a complete interactive ML application | All processing modules | All libraries | Demo Scene | Stage 3 | Final presentation | LOI-PATTERN-013 |

### 11.2 Learning Evidence — Unit IX

A student demonstrates Unit IX mastery when they can:
- Present a complete `EvaluationResult` with accuracy ≥ 70%.
- Show live in their Stage 3 that two different visual inputs produce different classification outputs and different game behavior.
- Explain mathematically how k-NN finds the nearest neighbors (distance formula, k selection).
- Compare two classifier types on their dataset and explain the tradeoff.

---

## 12. Assessment Instrument Summary

**Corrected per `00_SYLLABUS_ALIGNMENT_AUDIT.md` §2.A.2.** The table below replaces the prior invented instrument set with the six **official** instruments and their **official weighting**, as defined by the course syllabus. Full class-by-class scheduling is in `21_COURSE_SCHEDULE.md`.

| Instrumento | Porcentaje | Units Covered | Class | Format |
|---|---|---|---|---|
| **Quices** | 15% | Distributed: I–II, III, V, VIII | Classes 2, 4, 6, 9 | Short written/conceptual checks |
| **Prácticas de laboratorio** | 20% | Distributed: II, V, VIII | Classes 3, 6, 9 | Individual hands-on Python lab exercises |
| **Evaluación Práctica I – Prototipo Funcional** | 15% | II, III, IV, V | Class 5 | Stage/Boss submission — coordinates, transformations, basic scenario, initial interaction |
| **Evaluación Práctica II – Vertical Slice** | 15% | III, IV, V, VI | Class 8 | Stage/Boss submission — curves, scenes, color/transparency, textures/animation |
| **Evaluación Práctica III – Integración Final** | 15% | VII, VIII, IX | Class 11 | Stage/Boss submission — image processing, segmentation, pattern recognition, full integration |
| **Proyecto Integrador Invenio Fest** | 20% | I–IX (applied) | Class 12 | Group interdisciplinary presentation; this course grades the graphics/visual contribution only |
| **Total** | **100%** | | | |

Each Evaluación Práctica is a submission of the **same single Stage or Boss** the student selected individually in Class 1 — not a different stage per checkpoint. See `08_SYLLABUS_MAPPING.md` §12 for the full milestone-to-unit mapping.

---

## 13. Professor Pre-Semester Checklist

The following items must be delivered before the course begins:

**Corrected per `00_SYLLABUS_ALIGNMENT_AUDIT.md` §2.A.3 and §2.A.6** — timeline uses Class numbers (11-class trimester, see `21_COURSE_SCHEDULE.md`) instead of Week numbers, and paths reflect the `src/` relocation.

| Deliverable | Status Target | Document |
|---|---|---|
| `src/engine/` fully implemented and tested | Before Class 1 | LOI-ARCH-003 |
| `src/framework/entities/` fully implemented and tested | Before Class 1 | LOI-PLAYER-004, LOI-ENEMY-005 |
| `src/framework/processing/filter_tools.py` fully implemented | Before Class 8 | LOI-FILTER-011 |
| `src/framework/processing/vision_tools.py` fully implemented | Before Class 9 | LOI-VISION-012 |
| `src/framework/processing/pattern_recognition_tools.py` fully implemented | Before Class 10 | LOI-PATTERN-013 |
| `src/stages/stage0/` fully implemented | Before Class 1 | LOI-STAGE0-007 |
| Demo Scenes (Units VII, VIII, IX) implemented | Before Classes 8, 9, 10 respectively | LOI-DEMO-015 |
| All unit tests passing | Continuous | All spec docs |
| `tools/build_dataset.py` available | Before Class 10 | LOI-PATTERN-013 §20 |
| Training notebook template available | Before Class 10 | LOI-PATTERN-013 §20 |
| `assets/datasets/sample_dataset.npz` available | Before Class 10 | LOI-PATTERN-013 §8 |
| `student_templates/stage_template/` and `student_templates/boss_template/` available | Before Class 1 | This document, §1 |

---

## 14. Student Deliverable Checklist (Per Evaluación Práctica)

**Corrected per `00_SYLLABUS_ALIGNMENT_AUDIT.md` §2.A.1 and §9.** The checklists below apply to the **single Stage or Boss individually assigned** to each student in Class 1 — they are **not** three different stages. "14.1 / 14.2 / 14.3" are the three cumulative completeness checkpoints of that one assignment, renamed to match the official Evaluación Práctica I/II/III instruments.

### 14.1 Evaluación Práctica I — Prototipo Funcional Checklist (Class 5)

| Item | Units | Required |
|---|---|---|
| `<assignment>.tmx` — valid TMX with all required layers (Stages only) | I, IV | Mandatory |
| `<assignment>.py` — correct `BaseScene` (Stage) or `BossBase` (Boss) subclass | I, IV | Mandatory |
| At least one custom entity using vector math | II | Mandatory |
| At least one entity following a curve path | III | Mandatory |
| Color space operation applied to a surface | V | Mandatory |
| `README.md` — all academic concepts documented | I–V | Mandatory |

### 14.2 Evaluación Práctica II — Vertical Slice Checklist (Class 8)

| Item | Units | Required |
|---|---|---|
| All Evaluación Práctica I requirements maintained | I–V | Mandatory |
| Easing function used in movement or animation | VI | Mandatory |
| `FilterTools.compute_histogram()` used to drive logic | VII | Mandatory |
| `FilterTools.adjust_brightness()` or `adjust_contrast()` applied | VII | Mandatory |
| `FilterTools.apply_kernel()` or `gaussian_blur()` applied | VII | Mandatory |
| At least one edge detection result (Sobel or Canny) | VII | Mandatory |
| README: kernel matrix, filter applied, before/after screenshots | VI, VII | Mandatory |

### 14.3 Evaluación Práctica III — Integración Final Checklist (Class 11)

| Item | Units | Required |
|---|---|---|
| All Evaluación Práctica I and II requirements maintained | I–VII | Mandatory |
| `VisionTools.threshold_binary()` or `threshold_otsu()` applied | VIII | Mandatory |
| At least one morphological operation applied | VIII | Mandatory |
| `VisionTools.connected_components()` or `analyze_regions()` used | VIII | Mandatory |
| `VisionTools.extract_features()` produces training features | VIII, IX | Mandatory |
| Labeled dataset in `assets/datasets/` or student assignment folder | IX | Mandatory |
| Trained model in student assignment folder (`.pkl`) | IX | Mandatory |
| `EvaluationResult` with accuracy ≥ 70% in README | IX | Mandatory |
| Classifier runs at runtime; result changes game behavior | IX | Mandatory |
| README: full training pipeline documentation | IX | Mandatory |


---
## 🔗 Documentos Relacionados

- [[08_SYLLABUS_MAPPING.md|Syllabus Mapping]]
- [[27_ACADEMIC_RUBRICS.md|Academic Rubrics]]
