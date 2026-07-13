# Legacy of InFest — Syllabus Mapping

**Document ID:** LOI-SYLLABUS-008  
**Version:** 1.0.0  
**Status:** Official  
**Audience:** Professor, Teaching Assistants, Students

---

## 1. Overview

This document maps every topic in the course syllabus to its corresponding framework component, student deliverable, Stage 0 demonstration, and evaluation criteria. It is the authoritative reference for grading and for students deciding how to implement their academic features in their stages.

Each course unit corresponds to a block of academic content. The framework provides the infrastructure for applying each topic. Students must implement at least one academic feature per unit assigned to their stage, document it in their stage README, and demonstrate it during the final presentation.

---

## 2. Unit I — Introduction to Computer Graphics

### 2.1 Topics

- History and context of computer graphics
- Raster vs. vector graphics
- Display technology and pixel grids
- The game loop as a real-time graphics system
- Frame rate, delta time, and temporal coherence

### 2.2 Framework Component

| Component | File | Description |
|---|---|---|
| Application loop | `engine/core/app.py` | Implements the game loop with delta time |
| Clock | `engine/core/clock.py` | `DeltaClock` manages temporal coherence |
| Internal surface | `engine/core/app.py` | 320×224 raster buffer scaled to display |
| Display scaling | `engine/core/app.py` | Integer-scale blit to OS window |

### 2.3 Student Deliverable

Students do not implement Unit I concepts in a stage directly. Unit I is demonstrated implicitly by the framework itself. Students are expected to document in their Stage README:

- The internal resolution used (320×224)
- The target frame rate (60 FPS)
- An explanation of how `dt` (delta time) is used in at least one entity in their stage

### 2.4 Stage 0 Demonstration

Stage 0 serves as the Unit I demonstration. Its existence as a running 60 FPS game at 320×224 scaled to a modern display is the demonstration. The debug overlay (F1) shows the current FPS counter.

### 2.5 Evaluation Criteria

| Criterion | Weight | Standard |
|---|---|---|
| Stage runs at stable 60 FPS | Pass/Fail | No frame drops below 50 FPS during normal gameplay |
| Delta time applied to all movement | Pass/Fail | All `velocity * dt` patterns present |
| README explains game loop | 10% | Correct description of update/draw cycle |

---

## 3. Unit II — Coordinate Systems, Vectors, Matrices, Transformations

### 3.1 Topics

- 2D Cartesian coordinate system
- Screen-space vs. world-space coordinates
- Vector arithmetic (addition, subtraction, scaling, dot product, normalization)
- Translation and rotation matrices
- Homogeneous coordinates
- Transformation of bounding boxes

### 3.2 Framework Component

| Component | File | Description |
|---|---|---|
| World/screen transform | `framework/stage/camera.py` | `world_to_screen()` applies camera offset |
| Vector utilities | `engine/utils/math_utils.py` | `vec2_normalize`, `vec2_dot`, `vec2_distance` |
| Hitbox transformation | `framework/entities/base_entity.py` | Local → world rect transform |
| Projectile angle (atan2) | `framework/entities/enemy_shooter.py` | Vector from shooter to player |
| Player knockback vector | `framework/entities/player.py` | Direction vector from damage source |

### 3.3 Student Deliverable

**Required:** At least one custom entity whose movement or behavior uses explicit vector arithmetic.

Examples:
- An enemy that normalizes the vector to the player to move at constant speed regardless of direction
- A projectile that uses a computed direction vector rather than hardcoded horizontal/vertical movement
- A trigger zone that computes the player's distance using `vec2_distance` and scales an effect by proximity

**Required README documentation:**
- The vector operation used, stated mathematically
- Which framework utility function was used
- A screenshot or GIF showing the behavior

### 3.4 Stage 0 Demonstration

- Zone E: Shooter `atan2` angle calculation is explicitly shown in the tutorial message and in the debug overlay (draws a line from shooter to player).
- Zone B: Player knockback vector computed from damage source position.
- Debug mode: All rects shown are local-space rects transformed to world space.

### 3.5 Evaluation Criteria

| Criterion | Weight | Standard |
|---|---|---|
| Correct vector normalization | 25% | Entity moves at constant speed toward target |
| Transformation from local to world space | 25% | Hitbox/hurtbox positioned correctly in world |
| Mathematical documentation in README | 30% | Formula written out, not just described |
| Working demo in stage | 20% | Feature observable and functional |

---

## 4. Unit III — Bézier Curves, Bernstein Polynomials, B-Splines, NURBS, Trajectories

### 4.1 Topics

- Parametric curves
- Bernstein basis polynomials
- De Casteljau algorithm
- Bézier curves (degree 2 and 3)
- B-Spline basis functions and knot vectors
- NURBS (Non-Uniform Rational B-Splines)
- Path parametrization and arc-length re-parametrization

### 4.2 Framework Component

| Component | File | Description |
|---|---|---|
| Bézier computation | `framework/processing/curve_tools.py` | `bezier(control_points, n_samples)` |
| B-Spline computation | `framework/processing/curve_tools.py` | `b_spline(points, degree, n)` |
| NURBS computation | `framework/processing/curve_tools.py` | `nurbs(points, weights, knots, degree, n)` |
| Path sampling | `framework/processing/curve_tools.py` | `sample_path(points, t)` |
| Catmull-Rom | `framework/processing/curve_tools.py` | `catmull_rom(points, n)` |
| Flying enemy Bézier path | `framework/entities/enemy_flying.py` | Uses `bezier()` for patrol path |

### 4.3 Student Deliverable

**Required:** At least one entity or environmental effect that uses a curve from `curve_tools.py`.

Examples:
- A flying enemy whose path is a B-Spline through 5+ waypoints defined in TMX
- A projectile that follows a Catmull-Rom spline instead of a straight line
- An environmental object (swinging pendulum, oscillating platform) whose position is computed from a Bézier segment
- A visual effect trace (light trail) that draws the sampled points of a NURBS curve

**Required:** The stage README must include:
- A plot or diagram of the curve (hand-drawn or generated)
- The control points used
- The type of curve (Bézier, B-Spline, NURBS, Catmull-Rom) and degree
- An explanation of what `t` represents in the context of the entity

### 4.4 Stage 0 Demonstration

- Zone D: Flying_02 uses a degree-3 Bézier path through 4 waypoints.
- Debug mode (F1): Renders the sampled path as a series of dots, and the control polygon as thin lines.
- Zone D tutorial message: Explains the relationship between control points and the curve.

### 4.5 Evaluation Criteria

| Criterion | Weight | Standard |
|---|---|---|
| Curve correctly implemented | 30% | Entity follows mathematical curve (verified vs. expected output) |
| Correct curve type for degree | 20% | Degree matches control point count or knot vector |
| Visual behavior matches documentation | 20% | Demo matches README description |
| Written mathematical explanation | 30% | Bernstein basis or knot vector correctly described |

---

## 5. Unit IV — Objects, Scenes, Layers, Sprites, Buffers

### 5.1 Topics

- Scene graph concepts
- Layered rendering architecture
- Sprite as a textured quad
- Sprite animation (frame cycling)
- Double buffering
- Z-ordering and draw calls

### 5.2 Framework Component

| Component | File | Description |
|---|---|---|
| Scene management | `engine/scene/scene_manager.py` | Scene stack, push/pop/replace |
| Layer stack | TMX `BG_Far`, `BG_Mid`, etc. | Ordered rendering layers |
| Sprite animation | `engine/utils/spritesheet.py` | Frame cycling from sprite sheet |
| Double buffer | `engine/core/app.py` | Internal surface blit to window |
| Draw order | `BaseEntity.layer` | Z-order property on entities |

### 5.3 Student Deliverable

**Required:** The student stage must correctly use a minimum of three TMX tile layers (excluding collision and objects). At least one entity must have a multi-frame animated sprite created by the student or adapted from the asset library.

**Required README documentation:**
- A diagram or table of the layer stack used in the stage
- An explanation of how the double-buffer render cycle works
- The frame count and FPS of at least one custom animation

### 5.4 Stage 0 Demonstration

- All zones: Three background layers (BG_Far, BG_Mid, BG_Near) scroll at different parallax rates.
- Zone G: Torch sprite animation demonstrates a 4-frame looping object animation.
- Debug mode shows layer boundaries as colored outlines.

### 5.5 Evaluation Criteria

| Criterion | Weight | Standard |
|---|---|---|
| Minimum 3 tile layers present | Pass/Fail | TMX has BG_Far, BG_Mid, Terrain at minimum |
| Parallax scrolls at correct rates | 25% | Visual confirmation of depth |
| Custom animated sprite functional | 35% | Frames cycle at correct FPS |
| Layer architecture documented | 40% | README diagram matches TMX |

---

## 6. Unit V — RGB, HSV, HSL, CMYK, Transparency, Alpha Blending, Lighting

### 6.1 Topics

- RGB color model and byte representation
- HSV (Hue, Saturation, Value) color model
- HSL (Hue, Saturation, Lightness) color model
- CMYK color model
- Alpha channel and transparency
- Alpha blending equations
- Additive and multiplicative blending
- Simulated 2D lighting

### 6.2 Framework Component

| Component | File | Description |
|---|---|---|
| Color conversions | `framework/processing/color_tools.py` | `rgb_to_hsv`, `hsv_to_rgb`, `rgb_to_hsl`, etc. |
| Alpha blending | `framework/processing/color_tools.py` | `alpha_blend(src, dst, alpha)` |
| Tint application | `framework/processing/color_tools.py` | `apply_tint(surface, color)` |
| Surface to array | `framework/processing/color_tools.py` | `surface_to_array()`, `array_to_surface()` |
| Pygame alpha | `pygame.Surface.set_alpha()` | Direct surface transparency |

### 6.3 Student Deliverable

**Required:** At least one visual effect in the student stage that demonstrates a color space transformation or alpha blending operation applied to a surface or entity.

Examples:
- A health-based tint: as the player's health decreases, the screen tint shifts from neutral to red using HSV manipulation
- A day/night cycle overlay using alpha blending (a dark surface blended over the scene)
- An enemy that changes color phase (rotating hue in HSV space) as a "phase transition" visual
- A collectible that cycles through luminance values in HSL space to create a "glow" pulse

**Required README documentation:**
- The color space(s) used and why that space was chosen
- The mathematical formula for the transform applied
- Before/after screenshots

### 6.4 Stage 0 Demonstration

- Stage 0 does not implement a color effect directly, but the debug mode renders hitbox and hurtbox overlays using alpha-blended translucent colors (demonstrating `alpha_blend`).
- Zone F: The invincibility flash demonstrates `set_alpha()` toggling.

### 6.5 Evaluation Criteria

| Criterion | Weight | Standard |
|---|---|---|
| Correct color space used | 25% | HSV used for hue rotation, HSL for lightness, etc. |
| Mathematically valid formula | 25% | No formula errors (clamping, range normalization) |
| Visual effect clearly observable | 30% | Effect is visible and behaves as documented |
| README formula and rationale | 20% | Explains why that color space, not just what |

---

## 7. Unit VI — Textures, Animation, Interpolation, Collisions, Interaction

### 7.1 Topics

- Texture mapping fundamentals
- Animation as time-parametric texture selection
- Linear interpolation (lerp)
- Ease functions (quadratic, cubic, sine)
- AABB collision detection
- Interaction event patterns

### 7.2 Framework Component

| Component | File | Description |
|---|---|---|
| Sprite animation | `engine/utils/spritesheet.py` | Frame-based animation |
| Interpolation | `engine/utils/math_utils.py` | `lerp`, `ease_in_quad`, `ease_out_quad` |
| AABB collision | `framework/entities/player.py` | Axis-separated resolution |
| Interaction events | `engine/core/event_bus.py` | Pub/sub interaction model |
| Camera lerp | `framework/stage/camera.py` | Smooth follow via lerp |

### 7.3 Student Deliverable

**Required:** At least one entity movement or UI animation in the stage that uses an ease function from `math_utils.py` (not linear interpolation alone).

Examples:
- A platform that moves between two positions using `ease_in_out_quad` for smooth deceleration
- An enemy that approaches the player using `ease_in_cubic` (slow start, fast approach)
- A collectible bounce animation using `ease_out_bounce`
- A door opening animation timed with easing

**Required:** At least one custom collision interaction beyond standard wall/floor (e.g., a trigger zone, a bouncing hazard, a movable block).

### 7.4 Stage 0 Demonstration

- Camera follow uses `lerp` for smooth viewport movement.
- The screen banner slides in/out using `ease_out_quad` and `ease_in_quad`.
- Checkpoint activation uses alpha lerp for the activation glow effect.

### 7.5 Evaluation Criteria

| Criterion | Weight | Standard |
|---|---|---|
| Ease function applied | 30% | Not plain `lerp`; uses a curve |
| Visually distinguishable from linear | 20% | Observer can see acceleration/deceleration |
| Custom interaction event implemented | 30% | Beyond standard floor/wall collision |
| README explains easing math | 20% | Correct mathematical description |

---

## 8. Unit VII — Histogram, Brightness, Contrast, Convolution, Gaussian Blur, Sobel, Canny

### 8.1 Topics

- Image histograms and their interpretation
- Brightness and contrast adjustment
- Convolution as a mathematical operation
- Gaussian blur kernel
- Sobel edge detection operator
- Canny multi-stage edge detection

### 8.2 Framework Component

| Component | File | Description |
|---|---|---|
| Histogram | `framework/processing/filter_tools.py` | `compute_histogram(surface)` |
| Brightness | `framework/processing/filter_tools.py` | `adjust_brightness(surface, factor)` |
| Contrast | `framework/processing/filter_tools.py` | `adjust_contrast(surface, factor)` |
| Convolution | `framework/processing/filter_tools.py` | `apply_kernel(surface, kernel)` |
| Gaussian blur | `framework/processing/filter_tools.py` | `gaussian_blur(surface, sigma)` |
| Sobel | `framework/processing/filter_tools.py` | `sobel_edge(surface)` |
| Canny | `framework/processing/filter_tools.py` | `canny_edge(surface, low, high)` |

### 8.3 Student Deliverable

**Required:** At least one real-time or semi-real-time application of a filter from `filter_tools.py` to a surface or background layer.

Performance note: Full-surface convolution every frame at 60 FPS is computationally expensive. Students are expected to apply filters intelligently (e.g., update every 5 frames, apply to a small sub-surface, pre-compute for static elements).

Examples:
- Apply Sobel edge detection to a background tile layer and render the edge map as a secondary visual overlay (e.g., for a "digital world" stage aesthetic)
- Apply Gaussian blur to the background layers behind a semi-transparent fog element
- Compute the brightness histogram of the current screen and use it to trigger a "darkness event" (play an alarm SFX) when average brightness drops below a threshold
- Apply a Canny edge map to an enemy sprite and use the edge data for a stylized outline rendering effect

**Required README documentation:**
- Which filter was applied
- The kernel matrix used (if convolution)
- The frame-update strategy (how often applied)
- Before/after screenshot of the filtered surface

### 8.4 Stage 0 Demonstration

Stage 0 does not apply real-time filters (it demonstrates core gameplay systems). However, the `filter_tools.py` module is provided with runnable unit tests in `tests/test_filter_tools.py` that produce visual output files demonstrating each filter. Students are expected to run these tests and examine the output as part of their Unit VII study.

### 8.5 Evaluation Criteria

| Criterion | Weight | Standard |
|---|---|---|
| Filter applied to correct surface type | 25% | Applied to `pygame.Surface`, converted via `surface_to_array` |
| Mathematically correct filter | 30% | Kernel values correct; output matches expected behavior |
| Performance-conscious application | 20% | Not applied every frame to the full screen without justification |
| README kernel + strategy explanation | 25% | Kernel shown as matrix; update frequency explained |

---

## 9. Unit VIII — Segmentation, Threshold, Regions, Morphology, Watershed, Feature Extraction

### 9.1 Topics

- Binary thresholding
- Otsu's automatic threshold
- Connected region analysis
- Morphological operations (erosion, dilation, opening, closing)
- Watershed segmentation algorithm
- HOG (Histogram of Oriented Gradients)
- LBP (Local Binary Patterns)

### 9.2 Framework Component

| Component | File | Description |
|---|---|---|
| Binary threshold | `framework/processing/vision_tools.py` | `threshold_binary(surface, thresh)` |
| Otsu threshold | `framework/processing/vision_tools.py` | `threshold_otsu(surface)` |
| Morphological erosion | `framework/processing/vision_tools.py` | `morphological_erode(surface, k)` |
| Morphological dilation | `framework/processing/vision_tools.py` | `morphological_dilate(surface, k)` |
| Watershed | `framework/processing/vision_tools.py` | `watershed_segment(surface)` |
| Feature extraction | `framework/processing/vision_tools.py` | `extract_features(surface)` |

### 9.3 Student Deliverable

**Required:** At least one application of a segmentation or morphology operation to a surface, used to drive game behavior (not purely visual).

Examples:
- Apply Otsu threshold to the current screen; count the number of dark pixels; if above a threshold, trigger an event (lights-off mechanic)
- Apply erosion to a sprite's alpha channel to create a "dissolving" death effect
- Use watershed segmentation on a background surface to identify and highlight distinct "zones" — render zone borders as a visual overlay
- Extract HOG features from a tileset region and use the feature vector as input to a runtime classifier

### 9.4 Stage 0 Demonstration

Unit tests in `tests/test_vision_tools.py` demonstrate each function with saved output images. Students must run and study these tests.

### 9.5 Evaluation Criteria

| Criterion | Weight | Standard |
|---|---|---|
| Correct function from vision_tools | 25% | Right tool for the right task |
| Output drives game behavior | 35% | Segmentation result changes state, not just displayed |
| Edge case handling | 20% | What happens on black/white/uniform surfaces |
| README explanation | 20% | Algorithm explained, not just named |

---

## 10. Unit IX — Pattern Recognition, Classification, Visualization, Interactive Systems, Computer Vision

### 10.1 Topics

- Feature spaces and classification
- k-Nearest Neighbors (k-NN)
- Decision Trees and Random Forests
- scikit-learn model training and inference
- Real-time computer vision loops
- Interactive systems driven by visual state

### 10.2 Framework Component

| Component | File | Description |
|---|---|---|
| Feature extraction | `framework/processing/vision_tools.py` | `extract_features(surface)` |
| Classification | `framework/processing/vision_tools.py` | `classify_region(features, model)` |
| scikit-learn integration | `requirements.txt` | `scikit-learn` available |
| OpenCV integration | `requirements.txt` | `opencv-python` available |

### 10.3 Student Deliverable

**Required:** At least one system in Stage 3 (the final student stage) that applies a trained classifier to visual game data and uses the classification result to drive game behavior.

This is the capstone academic feature of the course. It must integrate concepts from all prior units.

Examples:
- Train a k-NN classifier offline on sprite feature vectors (HOG or LBP). At runtime, classify new sprites and spawn different enemy types based on the classification.
- Train a decision tree on screen histogram features. At runtime, classify the current screen's "mood" (bright/dark/red-heavy) and change BGM and lighting accordingly.
- Use OpenCV to process a small screen region (e.g., around the player) and detect a visual pattern that triggers a game event.
- Implement a real-time gesture recognizer using input history as a feature vector, classifying movement patterns into named player actions beyond the standard control set.

**Required README documentation:**
- Dataset description (what was used to train the classifier)
- Feature vector definition and dimensionality
- Classifier type and hyperparameters
- Training accuracy and test accuracy
- How the classification output changes game behavior

### 10.4 Stage 0 Demonstration

Not demonstrated directly in Stage 0. Unit IX is demonstrated in the unit test `tests/test_vision_tools.py` which includes a small k-NN example on generated sprite data.

### 10.5 Evaluation Criteria

| Criterion | Weight | Standard |
|---|---|---|
| Classifier trained and serialized | 20% | Model loadable at runtime |
| Features correctly extracted | 20% | Correct dimensionality, no data leakage |
| Classification drives behavior | 30% | Distinct game response for each class |
| Accuracy documented | 15% | Training and test accuracy reported |
| README capstone explanation | 15% | End-to-end system described clearly |

---

## 11. Consolidated Mapping Table

| Unit | Topic Summary | Framework Module | Student Stage | Stage 0 Zone |
|---|---|---|---|---|
| I | Game loop, raster, delta time | `app.py`, `clock.py` | All stages (implicit) | Entire Stage 0 |
| II | Vectors, matrices, transforms | `math_utils.py`, `camera.py`, `base_entity.py` | Stage 1 or 2 | Zone E (atan2), debug overlay |
| III | Bézier, B-Spline, NURBS, paths | `curve_tools.py`, `enemy_flying.py` | Stage 1 or 2 | Zone D (Flying_02) |
| IV | Scenes, layers, sprites, buffers | `scene_manager.py`, `spritesheet.py` | All stages | All zones |
| V | Color spaces, alpha, lighting | `color_tools.py` | Stage 1 or 2 | Debug overlays |
| VI | Animation, interpolation, collision | `math_utils.py`, `player.py`, `camera.py` | Stage 1 or 2 | Camera, banner, checkpoint |
| VII | Filters, convolution, edges | `filter_tools.py` | Stage 2 or 3 | Unit tests |
| VIII | Segmentation, morphology, features | `vision_tools.py` | Stage 2 or 3 | Unit tests |
| IX | Classification, computer vision | `vision_tools.py`, scikit-learn | Stage 3 | Unit tests |

---

## 12. Milestone-to-Unit Assignment

**Corrected per `00_SYLLABUS_ALIGNMENT_AUDIT.md` §2.A.1 and §9.** The labels "Stage 1," "Stage 2," and "Stage 3" used throughout this and other framework documents do **not** refer to three different stages assigned to one student. Per the official syllabus, Legacy of InFest is an **individual project**: each student selects exactly **one** Stage or Boss in Class 1 (see `21_COURSE_SCHEDULE.md`) and develops that single assignment through three cumulative completeness milestones, each corresponding to one official Evaluación Práctica:

| Internal Label (legacy) | Official Name | Class | Cumulative Units Demonstrated |
|---|---|---|---|
| "Stage 1" | Evaluación Práctica I – Prototipo Funcional | Class 5 | II, III, IV, V |
| "Stage 2" | Evaluación Práctica II – Vertical Slice | Class 8 | + VI, VII |
| "Stage 3" | Evaluación Práctica III – Integración Final | Class 11 | + VIII, IX |

A student's single assigned Stage or Boss must demonstrate Units II–V by Evaluación Práctica I, add Units VI–VII by Evaluación Práctica II, and add Units VIII–IX by Evaluación Práctica III — all within the **same** piece of work, progressively elaborated. Unit I is foundational and demonstrated implicitly from the start (see Section 2 of this document).


--- Traducción al Español ---

## Mapeo del Sílabo

Este documento mapea cada tema del sílabo del curso a su componente correspondiente en el framework, el entregable del estudiante, la demostración en el Escenario 0 y los criterios de evaluación.

### Unidades Cubiertas
I. Introducción a Gráficas por Computadora
II. Sistemas de Coordenadas, Vectores, Matrices, Transformaciones
III. Curvas de Bézier, Bernstein, B-Splines, NURBS
IV. Objetos, Escenas, Capas, Sprites, Buffers
V. RGB, HSV, HSL, CMYK, Transparencia, Iluminación
VI. Texturas, Animación, Interpolación, Colisiones
VII. Histograma, Brillo, Convolución, Gaussian Blur, Sobel, Canny
VIII. Segmentación, Threshold, Morfología, Watershed
IX. Reconocimiento de Patrones, Clasificación

Para la tabla completa de mapeo con criterios de evaluación detallados, consultar el documento original en inglés.
