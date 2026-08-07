---
document_id: "LOI-DEMO-015"
title: "Legacy of InFest — Academic Demo Scenes"
aliases: ["Academic Demo Scenes", "Demo Labs"]
tags: ["demo", "lab", "academic", "interactive"]
description: "10 interactive demo/lab scenes"
source: "docs/15_ACADEMIC_DEMO_SCENES.md"
date_processed: "2026-07-14"
---

# Legacy of InFest — Academic Demo Scenes

**Document ID:** LOI-DEMO-015  
**Version:** 1.3.0  
**Status:** Official  
**Compatibility:** Requires LOI-ARCH-003, LOI-FILTER-011, LOI-VISION-012, LOI-PATTERN-013, LOI-HUD-009, LOI-STAGE0-007  
**Audience:** Professor, Teaching Assistants, AI coding assistants (Claude Code, Cline, OpenCode, Codex)

---

## 1. Overview

The Academic Demo Scenes are ten professor-built interactive scenes — 7 theory labs (Units II–VI/VIII) plus 3 advanced demos (Units VII–IX) — that function as **living laboratories** within the Legacy of InFest framework. They are accessible from the Title Scene's main menu under a dedicated **"Academic Demos"** submenu.

Unlike Stage 0, which demonstrates gameplay systems, the Academic Demo Scenes demonstrate **image processing and machine learning operations** directly on game surfaces. Each scene is fully interactive: students adjust parameters using keyboard controls and observe results in real time. Output values are displayed on screen to reinforce the mathematical connection between parameter and effect.

These scenes are **professor-owned and professor-maintained**. Students do not modify them. They use them as:

1. A reference for understanding what each framework function produces.
2. A calibration tool for choosing parameters before applying them in their own stages.
3. An assessment environment where Practical Exams II and III are partially conducted.

---

## 2. Scene Architecture

### 2.1 Integration with the Framework

Demo Scenes are standard `BaseScene` subclasses. They follow all scene lifecycle rules defined in `03_ARCHITECTURE.md`.

```
TitleScene
    ↓ (menu: Academic Demos)
DemoMenuScene              ← Selector for the ten demo/lab scenes (Units II–IX)
    ↓      ↓         ↓           ↓            ↓
Vector   Transform  Curve       Interpolate  Color
(II)     (II/III)   (III)       (III/IV)     (V)
    ↓      ↓         ↓           ↓            ↓
Noise    Collision  Filter      Vision       Pattern
(V/VIII) (VI)       (VII)       (VIII)       (IX)
    ↓ (ESC)
DemoMenuScene
```

### 2.2 File Locations

```
engine/
└── scenes/
    ├── demo_menu_scene.py              ← Selector for all 10 scenes
    ├── vector_lab_scene.py             ← Unit II  (Vectors)
    ├── transform_lab_scene.py          ← Unit II/III (2D Transformations)
    ├── curve_editor_scene.py           ← Unit III (Bézier, Splines)
    ├── interpolation_lab_scene.py      ← Unit III/IV (Interpolation & Easing)
    ├── color_theory_scene.py           ← Unit V (Color Spaces)
    ├── noise_lab_scene.py              ← Unit V/VIII (Noise & Procedural)
    ├── collision_lab_scene.py          ← Unit VI (AABB Collision)
    ├── filter_demo_scene.py            ← Unit VII
    ├── vision_demo_scene.py            ← Unit VIII
    └── pattern_demo_scene.py           ← Unit IX
```

Utility modules (shared by all scenes):
```
engine/scenes/
    ├── demo_layout.py                  ← Layout constants & draw helpers
    ├── demo_utils.py                   ← SourceSurfaceManager, FrameThrottle, ErrorDisplay, save_png
    ├── demo_common.py                  ← Legacy re-exports from demo_layout + demo_utils
    ├── scene_registry.py               ← DI Container: register → build pattern
    ├── param_panel.py                  ← Reusable ParamPanel widget
    └── debug_overlay.py                ← F11 debug console (app-wide, not scene-specific)
```

All demo/lab scene files are in `engine/scenes/`. They are professor-owned. Students do not modify them.

### 2.3 Shared Demo Scene Layout

The three academic demo scenes (Filter, Vision, Pattern) share a common layout structure.
The seven theory lab scenes (Units II–VI/VIII) use simpler layouts tailored to each topic.
A shared layout reference is available for the three academic demos:

```
┌──────────────────────────────────────────────────────────────────┐ Y=0
│  [SCENE TITLE]                              [UNIT: VII/VIII/IX]  │ Y=2
│  [Current Mode Name]                        [ESC: Back to Menu]  │ Y=12
├──────────────────────────────────────────────────────────────────┤ Y=22
│                                                                  │
│   [LEFT PANEL — 160×180]        [RIGHT PANEL — 160×180]         │ Y=22
│   Source / Input Surface        Result / Output Surface          │
│                                                                  │
├──────────────────────────────────────────────────────────────────┤ Y=202
│  [PARAMETER DISPLAY — 320×12]                                    │
│  Param: name = value  |  Param: name = value  |  [TAB: switch]  │
└──────────────────────────────────────────────────────────────────┘ Y=224
```

| Region | Dimensions | Content |
|---|---|---|
| Top bar | 320×22 px | Scene title, unit label, navigation hint |
| Left panel | 160×180 px | Input surface (source, before-state) |
| Right panel | 160×180 px | Output surface (result, after-state) |
| Divider line | 1 px vertical at X=160 | Visual separation |
| Bottom bar | 320×22 px | Current parameter name, value, controls |

### 2.4 Shared Controls

| Key | Action |
|---|---|
| `TAB` | Cycle to next operation mode within the scene |
| `LEFT` / `RIGHT` | Decrease / increase primary parameter |
| `UP` / `DOWN` | Decrease / increase secondary parameter (if applicable) |
| `SPACE` | Toggle between source surface options |
| `F` | Freeze/unfreeze the source surface (capture current frame) |
| `S` | Save the current output surface to `tests/output/demo/` as a PNG |
| `R` | Reset all parameters to defaults |
| `ESC` | Return to DemoMenuScene |

### 2.5 Source Surface Options

The three academic demo scenes (Filter, Vision, Pattern) share the same source surface pool. `SPACE` cycles through these options:

| Index | Source | Description |
|---|---|---|
| 0 | `assets/sprites/player/player_idle.png` (frame 0) | Player sprite — small, known content |
| 1 | `assets/backgrounds/bg_stage0_far.png` | Stage 0 far background — large, low contrast |
| 2 | `assets/tilesets/tileset_stage0.png` | Tileset — high frequency, many edges |
| 3 | Live capture — stage0 running in background | Real-time game surface (320×224) |
| 4 | `assets/sprites/enemies/enemy_walker_walk.png` (frame 0) | Enemy sprite |

Live capture (index 3) streams the internal surface of Stage 0 running in the background. Stage 0 must have been loaded at least once in the session for this option to be available. If unavailable, index 3 is skipped.

---

## 3. Unit VII Demo Scene — `FilterDemoScene`

### 3.1 Scene Purpose

`FilterDemoScene` demonstrates all operations provided by `FilterTools`. It is the primary interactive reference for Unit VII concepts: histogram, brightness, contrast, convolution, Gaussian blur, Sobel, and Canny edge detection.

Students use this scene to:
- Understand the visual effect of each parameter before applying it in their stage.
- Calibrate their kernel choices, sigma values, and threshold pairs.
- Capture before/after screenshots for their stage README.
- Complete Practical Exam II histogram and edge detection tasks.

### 3.2 Scene Layout (Detail)

```
┌─────────────────────────────────────────────────────────────────┐
│  FILTER DEMO                                        UNIT VII    │
│  [Mode: HISTOGRAM]                          [ESC: Back]         │
├────────────────────────┬────────────────────────────────────────┤
│                        │                                        │
│   SOURCE SURFACE       │   RESULT SURFACE                       │
│   160×180 px           │   160×180 px                           │
│                        │                                        │
│   (current source)     │   (filtered output)                    │
│                        │                                        │
│   ▼  HISTOGRAM         │   ▼  HISTOGRAM                         │
│   [R channel bar]      │   [R channel bar]                      │
│   [G channel bar]      │   [G channel bar]                      │
│   [B channel bar]      │   [B channel bar]                      │
│   [Lum bar]            │   [Lum bar]                            │
│                        │                                        │
├────────────────────────┴────────────────────────────────────────┤
│  Threshold: 128  | Sigma: 1.0  | Kernel: identity  [TAB:mode]  │
└─────────────────────────────────────────────────────────────────┘
```

When in HISTOGRAM mode, the bottom 60px of each panel is replaced by a compact histogram bar chart (R, G, B, and luminance channels, each displayed as a 40px-tall bar chart scaled to the panel width).

### 3.3 Operation Modes

`TAB` cycles through the following modes in order:

| Mode Index | Mode Name | Description | Active Parameters |
|---|---|---|---|
| 0 | `HISTOGRAM` | Shows per-channel histogram of source and result | Threshold for binary comparison |
| 1 | `BRIGHTNESS` | Applies `adjust_brightness(factor)` | `factor` (LEFT/RIGHT, step 0.05, range 0.0–4.0) |
| 2 | `CONTRAST` | Applies `adjust_contrast(factor)` | `factor` (LEFT/RIGHT, step 0.05, range 0.0–4.0) |
| 3 | `STRETCH` | Applies `stretch_contrast()` | No parameters (toggle only) |
| 4 | `KERNEL` | Applies `apply_kernel(kernel)` | Kernel name (UP/DOWN cycles through standard kernels) |
| 5 | `GAUSSIAN` | Applies `gaussian_blur(sigma)` | `sigma` (LEFT/RIGHT, step 0.1, range 0.1–5.0) |
| 6 | `SOBEL` | Applies `sobel_edge()` | No parameters |
| 7 | `CANNY` | Applies `canny_edge(low, high)` | `low` (LEFT/RIGHT), `high` (UP/DOWN) |
| 8 | `EQUALIZE` | Applies `histogram_equalize()` | No parameters |

### 3.4 Controls (Mode-Specific)

#### Mode 1 — BRIGHTNESS
| Key | Effect |
|---|---|
| `RIGHT` | Increase `factor` by 0.05 |
| `LEFT` | Decrease `factor` by 0.05 |

Bottom bar displays: `factor = 1.35 | Range: [0.0, 4.0] | Formula: out = in × factor`

#### Mode 4 — KERNEL
| Key | Effect |
|---|---|
| `UP` | Next kernel in list |
| `DOWN` | Previous kernel in list |

Bottom bar displays: `Kernel: sharpen | Size: 3×3 | [matrix shown as text]`

The kernel matrix is rendered in the bottom bar as a compact text representation:
```
[[ 0 -1  0][-1  5 -1][ 0 -1  0]]
```

#### Mode 7 — CANNY
| Key | Effect |
|---|---|
| `RIGHT` | Increase `low_threshold` by 5 |
| `LEFT` | Decrease `low_threshold` by 5 |
| `UP` | Increase `high_threshold` by 5 |
| `DOWN` | Decrease `high_threshold` by 5 |

Bottom bar displays: `low=50 | high=150 | ratio=3.0 | [Pipeline: blur→Sobel→NMS→threshold→hysteresis]`

### 3.5 Expected Inputs

| Input Type | Description |
|---|---|
| Source surface | Any of the 5 source options (SPACE to cycle) |
| Parameter controls | LEFT/RIGHT/UP/DOWN keys as documented per mode |
| Mode selection | TAB to advance through 9 modes |

### 3.6 Expected Outputs

| Output | Location |
|---|---|
| Filtered surface | Right panel, updated every frame (throttled for expensive ops) |
| Histogram bars | Bottom 60px of each panel in HISTOGRAM mode |
| Parameter readout | Bottom bar: current values, formula, valid range |
| Saved PNG | `tests/output/demo/filter_{mode}_{timestamp}.png` when `S` pressed |

### 3.7 Update Frequency by Mode

| Mode | Update Frequency | Reason |
|---|---|---|
| HISTOGRAM | Every frame | Histogram is fast |
| BRIGHTNESS | Every frame | Very fast |
| CONTRAST | Every frame | Very fast |
| STRETCH | Every frame | Fast |
| KERNEL 3×3 | Every frame | Fast |
| KERNEL 7×7+ | Every 3 frames | Moderate cost |
| GAUSSIAN σ<2.0 | Every frame | Fast |
| GAUSSIAN σ≥2.0 | Every 3 frames | Moderate cost |
| SOBEL | Every 3 frames | Moderate |
| CANNY | Every 5 frames | Higher cost |
| EQUALIZE | Every frame | Fast |

### 3.8 Visualization Rules

1. **Histogram bars:** Drawn as vertical bars using `pygame.draw.rect()`. Each bar's height is proportional to the frequency count, normalized to the maximum count. Colors: R=red, G=green, B=blue, Lum=white.
2. **Kernel text:** Rendered using the HUD bitmap font at 5×7 px per character.
3. **Mode label:** Displayed in the top bar using the banner font at 6×9 px. Highlighted in gold when mode changes, returns to white after 0.5 seconds.
4. **Parameter value:** Displayed as a numeric readout in the bottom bar. Values that have changed in the last 0.3 seconds are displayed in yellow; otherwise white.

### 3.9 Assessment Usage

`FilterDemoScene` is used during **Practical Exam II** as follows:

| Task | Scene Mode | Assessment Goal |
|---|---|---|
| Apply Gaussian blur with sigma matching a target blur | GAUSSIAN | Correct sigma selection |
| Apply Canny with thresholds to detect only strong edges | CANNY | Threshold understanding |
| Apply a kernel and identify whether it sharpens or blurs | KERNEL | Kernel comprehension |
| Compute the histogram of a given surface and report the dominant channel | HISTOGRAM | Histogram reading |

The professor saves a target output PNG, and the student must match it using the demo scene controls. The student screenshots their matching output and submits as exam evidence.

### 3.10 Integration with Stage 0

Stage 0 Zone F includes a brief demonstration of `adjust_brightness` and `gaussian_blur` on the game surface. `FilterDemoScene` extends this by providing full interactive control over all 9 operations and all 5 source surfaces.

### 3.11 Professor Deliverables

| Deliverable | Description |
|---|---|
| `engine/scenes/filter_demo_scene.py` | Complete implementation |
| 9 operation modes | All modes listed in §3.3 implemented |
| Live histogram visualization | Per-channel bar charts updating every frame |
| Kernel matrix text renderer | Compact kernel display in bottom bar |
| Save-to-PNG function | `S` key saves output surface |

### 3.12 Student Reuse

Students use `FilterDemoScene` to:
- Preview filter results before coding them into their stage.
- Calibrate parameter values (sigma, thresholds, factor).
- Capture before/after screenshots for their README.
- Practice for Practical Exam II.

Students do **not** modify `FilterDemoScene`.

### 3.13 Learning Evidence

A student has engaged with `FilterDemoScene` effectively when their stage README:
- Contains screenshots taken from or inspired by the demo scene.
- Documents exact parameter values (sigma, thresholds, factor) chosen and why.
- Includes the kernel matrix they used.
- Notes the update frequency strategy they adopted for their stage.

---

## 4. Unit VIII Demo Scene — `VisionDemoScene`

### 4.1 Scene Purpose

`VisionDemoScene` demonstrates all operations provided by `VisionTools`. It is the primary interactive reference for Unit VIII: thresholding, Otsu's method, morphological operations, connected components, region analysis, watershed segmentation, and feature extraction.

Students use this scene to:
- Visualize binary masks, labeled regions, and segmentation overlays.
- Observe how morphological operations transform a mask.
- View `RegionInfo` data for real surfaces from the game.
- Prepare their feature extraction strategy for Unit IX.
- Complete Practical Exam II segmentation tasks.

### 4.2 Scene Layout (Detail)

```
┌─────────────────────────────────────────────────────────────────┐
│  VISION DEMO                                       UNIT VIII    │
│  [Mode: THRESHOLD]                          [ESC: Back]         │
├────────────────────────┬────────────────────────────────────────┤
│   SOURCE SURFACE       │   RESULT SURFACE                       │
│   160×180 px           │   160×180 px                           │
│                        │                                        │
│   (current source)     │   (mask / labeled / feature)           │
│                        │                                        │
│                        │   ══ REGION INFO (if applicable) ══    │
│                        │   Regions: N                           │
│                        │   Largest: A=1234 C=(80,90)            │
│                        │   Threshold: 128 [Otsu: auto]          │
│                        │                                        │
├────────────────────────┴────────────────────────────────────────┤
│  Threshold: 128  |  Kernel: 3×3  |  Method: hog  [TAB:mode]    │
└─────────────────────────────────────────────────────────────────┘
```

When in REGIONS or CONNECTED_COMPONENTS mode, the right panel bottom 60px shows a text readout of the top 3 region stats: area, centroid (x, y), and bounding rect dimensions.

### 4.3 Operation Modes

| Mode Index | Mode Name | Description | Active Parameters |
|---|---|---|---|
| 0 | `THRESHOLD` | Binary threshold mask | `threshold` (LEFT/RIGHT, step 5, range 0–255) |
| 1 | `OTSU` | Otsu auto-threshold | No parameters; computed value displayed |
| 2 | `ERODE` | Erosion of binary mask | `kernel_size` (LEFT/RIGHT, step 2, range 1–15) |
| 3 | `DILATE` | Dilation of binary mask | `kernel_size` (LEFT/RIGHT, step 2, range 1–15) |
| 4 | `OPEN` | Morphological opening | `kernel_size` (LEFT/RIGHT) |
| 5 | `CLOSE` | Morphological closing | `kernel_size` (LEFT/RIGHT) |
| 6 | `COMPONENTS` | Connected components (labeled) | `threshold` (LEFT/RIGHT) + component count display |
| 7 | `REGIONS` | Region analysis overlay | `threshold` (LEFT/RIGHT) + top-3 RegionInfo display |
| 8 | `WATERSHED` | Watershed segmentation | No parameters; color overlay shown |
| 9 | `FEATURES` | Feature extraction visualization | `method` (UP/DOWN: hog, lbp, color_hist) |

### 4.4 Controls (Mode-Specific)

#### Mode 0 — THRESHOLD
| Key | Effect |
|---|---|
| `RIGHT` | Increase threshold by 5 |
| `LEFT` | Decrease threshold by 5 |

Bottom bar: `Threshold: 128 | White pixels: 14,302 | Black pixels: 57,418`

#### Mode 1 — OTSU
No parameter controls. Bottom bar displays:
`Otsu threshold: 112 | Inter-class variance maximized at this value`

The Otsu threshold value is displayed in gold to draw attention. This value changes with each source surface switch (`SPACE`).

#### Modes 2–5 — Morphology
| Key | Effect |
|---|---|
| `RIGHT` | Increase kernel_size by 2 |
| `LEFT` | Decrease kernel_size by 2 |

In these modes, the pipeline is **always**: `threshold (default 128) → morphological operation`. The threshold is fixed at 128 in morphology modes to focus student attention on the morphological effect. A note in the bottom bar: `Pre-applied threshold: 128 | Kernel: {k}×{k}`

#### Mode 6 — COMPONENTS
| Key | Effect |
|---|---|
| `RIGHT` | Increase threshold by 5 |
| `LEFT` | Decrease threshold by 5 |

Right panel renders the `ComponentResult.label_surface` (color-coded regions). Bottom bar: `Components: 7 | Threshold: 128 | [Color key: each color = distinct region]`

#### Mode 7 — REGIONS
Same controls as COMPONENTS. Right panel renders the label_surface with bounding rect overlays (thin white border per region). Bottom 60px of right panel shows:
```
Regions found: 7
#1  A=2,840  C=(82, 91)  Rect=64×44
#2  A=1,102  C=(140,112)  Rect=33×33
#3  A=   98  C=(21, 160)  Rect=12×8
```

#### Mode 8 — WATERSHED
No parameters. Bottom bar: `Watershed: {N} segments | Updating every 15 frames | Press S to save overlay`

The watershed result is pre-computed on mode entry and on source surface change. It is not recomputed every frame. A `[computing...]` overlay is shown during computation.

#### Mode 9 — FEATURES
| Key | Effect |
|---|---|
| `UP` | Cycle to next feature method |
| `DOWN` | Cycle to previous method |

Methods cycle: `hog → lbp → color_hist → combined → hog`

Right panel renders a **feature vector visualization**:

- **HOG:** The HOG cell grid is drawn over the source (left panel), with small oriented line segments showing the dominant gradient in each cell. The right panel shows the full feature vector as a bar chart (512 bars for 32×32 canonical input).
- **LBP:** Right panel shows the LBP code image (grayscale, each pixel = its LBP code). Bottom shows the 256-bin histogram of LBP codes.
- **Color histogram:** Right panel shows three overlapping bar charts (R, G, B), one per channel.
- **Combined:** Right panel shows a concatenated bar chart of all features, color-coded by segment (HOG=blue, LBP=green, color=red).

Bottom bar: `Method: hog | Vector length: 512 | Canonical input size: 32×32`

### 4.5 Expected Inputs

| Input Type | Description |
|---|---|
| Source surface | SPACE cycles through 5 options |
| Mode | TAB cycles through 10 modes |
| Primary parameter | LEFT/RIGHT |
| Secondary parameter | UP/DOWN (modes 9 only) |

### 4.6 Expected Outputs

| Output | Description |
|---|---|
| Right panel surface | Binary mask, label overlay, watershed overlay, or feature visualization |
| Region info text | Top 3 `RegionInfo` objects displayed in right panel bottom |
| Otsu threshold | Gold-highlighted auto-computed value |
| Feature vector bars | Full vector length displayed as bar chart |
| Saved PNG | `tests/output/demo/vision_{mode}_{timestamp}.png` on `S` key |

### 4.7 Visualization Rules

1. **Binary masks:** White pixels on black background. White = foreground.
2. **Label surface:** 8 distinct hue-separated colors. Background (label 0) always black.
3. **Bounding rects:** Thin 1px white outlines drawn on the label surface.
4. **Centroid markers:** A 3×3 pixel cross drawn at each centroid position.
5. **Watershed overlay:** Semi-transparent (alpha=160) color overlay blended over the source surface in the right panel.
6. **HOG visualization:** Cell grid drawn at 8×8 px per cell. Dominant gradient direction per cell shown as a 5px line segment centered at the cell.
7. **Feature bar chart:** Each bar is 1px wide. Bar height is proportional to the value, normalized to the maximum. Zero values are invisible. Positive values draw upward.

### 4.8 Assessment Usage

`VisionDemoScene` is used during **Practical Exam II**:

| Task | Scene Mode | Assessment Goal |
|---|---|---|
| Apply threshold to separate foreground from background | THRESHOLD | Threshold selection |
| Explain the Otsu value for a given surface | OTSU | Otsu criterion comprehension |
| Apply erosion to remove small noise blobs | ERODE | Morphological reasoning |
| Count the connected components in a mask | COMPONENTS | Component analysis |
| Report the area and centroid of the largest region | REGIONS | RegionInfo reading |
| Extract HOG features and report vector length | FEATURES | Feature descriptor understanding |

### 4.9 Integration with Stage 0

`VisionDemoScene` complements Stage 0 by providing the Unit VIII toolset not demonstrated in gameplay. Stage 0 demonstrates gameplay systems; `VisionDemoScene` demonstrates the image analysis systems that student stages in Stage 2 and 3 will build on.

### 4.10 Professor Deliverables

| Deliverable | Description |
|---|---|
| `engine/scenes/vision_demo_scene.py` | Complete implementation |
| 10 operation modes | All modes in §4.3 implemented |
| HOG cell visualization | Oriented gradient lines drawn per cell |
| LBP code image visualization | Grayscale LBP code render |
| Region info text overlay | Top-3 `RegionInfo` in right panel |
| Watershed pre-computation | Computed on mode entry, not per frame |

### 4.11 Student Reuse

Students use `VisionDemoScene` to:
- Choose their threshold value before hardcoding or using Otsu.
- Decide which morphological operation to apply and at what kernel size.
- Extract a feature vector from a surface they will use for training.
- Capture HOG and LBP visualizations for their README.

### 4.12 Learning Evidence

A student has engaged with `VisionDemoScene` effectively when their README:
- Shows a binary mask screenshot from their stage (matches threshold mode output).
- Documents the Otsu threshold value for at least one of their stage surfaces.
- Shows a region analysis table (area, centroid, bounding rect) for a segmented surface.
- Shows a HOG or LBP visualization from their stage region.

---

## 5. Unit IX Demo Scene — `PatternDemoScene`

### 5.1 Scene Purpose

`PatternDemoScene` demonstrates the full machine learning pipeline in an interactive, real-time context. It is the primary reference for Unit IX: feature extraction, training, evaluation, and runtime inference.

This scene is unique in that it includes two phases:

**Phase A — Offline (pre-loaded):** A pre-trained model built on the professor's sample dataset is loaded at scene initialization. Students can immediately see inference running on live game surfaces.

**Phase B — Interactive:** Students can select their own saved model (from `student_assets/models/`) and load it into the scene, replacing the professor's model. Their own classifier then runs in the scene.

Students use this scene to:
- See real-time classification on game surfaces.
- Validate that their trained model loads and infers correctly.
- Compare their model's output against the professor's sample model.
- Complete Practical Exam III classification tasks.

### 5.2 Scene Layout (Detail)

```
┌─────────────────────────────────────────────────────────────────┐
│  PATTERN DEMO                                        UNIT IX    │
│  [Model: professor_sample | Method: hog | Inference: 3 frames]  │
├────────────────────────┬────────────────────────────────────────┤
│   SOURCE SURFACE       │   CLASSIFICATION RESULT                │
│   160×180 px           │   160×180 px                           │
│                        │                                        │
│   [current source]     │   ▶  CLASS: dark_zone                  │
│   [analysis rect       │   Confidence: 0.72                     │
│    highlighted in      │                                        │
│    yellow border]      │   ── TOP 3 PREDICTIONS ──              │
│                        │   dark_zone    ████████████ 72%        │
│                        │   neutral      ████         18%        │
│                        │   light_zone   ██           10%        │
│                        │                                        │
│                        │   ── FEATURE VECTOR ──                 │
│                        │   [bar chart — HOG 512 bars]           │
│                        │                                        │
├────────────────────────┴────────────────────────────────────────┤
│  [L] Load student model  |  [M] Cycle method  |  [TAB] mode    │
└─────────────────────────────────────────────────────────────────┘
```

### 5.3 Operation Modes

| Mode Index | Mode Name | Description |
|---|---|---|
| 0 | `INFERENCE` | Real-time classification of selected source region |
| 1 | `FEATURE_COMPARE` | Side-by-side feature vector of source vs. nearest training sample |
| 2 | `CLASS_GRID` | 4×4 grid of random training samples colored by class |
| 3 | `CONFUSION` | Display the loaded model's confusion matrix |
| 4 | `PIPELINE` | Step-by-step pipeline display (filter → vision → features → classify) |

### 5.4 Mode 0 — INFERENCE (Primary Mode)

**Description:** The analysis rect (yellow-bordered sub-rectangle of the source surface) is classified every N frames using the loaded model. The result, confidence, and top-3 predictions are displayed in the right panel.

**Analysis Rect:** A 32×32 pixel rectangle initially centered on the source surface. Controlled by:
| Key | Effect |
|---|---|
| `W/A/S/D` | Move the analysis rect by 8 pixels |
| `+/-` | Increase/decrease rect size by 8 pixels (min 16×16, max 80×80) |

The analysis rect is always shown as a 1px yellow border on the left panel.

**Classification display (right panel):**
```
▶  CLASS: dark_zone
Confidence: 0.72

── TOP 3 PREDICTIONS ──
dark_zone    ████████████ 72%
neutral      ████         18%
light_zone   ██           10%

── FEATURE VECTOR ──
[512-bar chart for HOG]

Inference: every 3 frames
Model: professor_sample (knn, k=5)
Feature: hog | Vector: 512
```

**Inference frequency:** Fixed at every 3 frames. Displayed in bottom bar.

**Class color coding:** Each class is assigned a unique color at model load time. The top prediction class name is displayed in that color. The probability bars use the same colors.

### 5.5 Mode 1 — FEATURE_COMPARE

**Description:** Extracts the feature vector from the current analysis rect and finds the nearest training sample in feature space. Displays both feature vectors side by side.

Left panel bottom: Feature vector of current analysis rect (bar chart).  
Right panel: Feature vector of nearest training sample (bar chart) + the sample's surface (if available in dataset).

Bottom bar: `Distance: 0.342 | Nearest class: dark_zone | k=1 nearest`

This mode illustrates what k-NN is doing: finding the closest point in the feature space.

### 5.6 Mode 2 — CLASS_GRID

**Description:** Displays a 4×4 grid (16 cells) of random training samples from the loaded dataset, each cell colored by class at the border. Cell size: 32×32 pixels.

If the dataset has more than 16 samples, 16 are selected randomly (seeded for reproducibility).

Right panel shows: 16 cells in a 4-column grid. Each cell has a 2px colored border (class color) and the class label printed in 5×7 px font at the cell bottom.

Bottom bar: `Dataset: {name} | Classes: {list} | Total samples: {N}`

### 5.7 Mode 3 — CONFUSION

**Description:** Renders the loaded model's confusion matrix as a colored grid. Each cell `(i, j)` shows the number of test samples from class `i` predicted as class `j`. Diagonal cells (correct predictions) are green; off-diagonal cells (errors) are red (intensity proportional to error count).

Confusion matrix is pre-computed from the model's `EvaluationResult` stored in `TrainedModel.metadata`. If not available, a placeholder message is shown: `"Confusion matrix not available — run evaluate() during training and save to model.metadata"`

Bottom bar: `Accuracy: 84.3% | Classes: 3 | Test samples: 60`

### 5.8 Mode 4 — PIPELINE

**Description:** A step-by-step visualization of the full processing pipeline for the current analysis rect. Displays 5 sequential panels (top-to-bottom in the right panel area):

```
Step 1: Source Region (32×32, raw)
   ↓ FilterTools.gaussian_blur(sigma=1.0)
Step 2: Preprocessed
   ↓ VisionTools.extract_hog()
Step 3: HOG visualization (cell grid)
   ↓ PatternRecognitionTools.classify()
Step 4: Feature vector bar chart
   ↓ Result
Step 5: CLASS LABEL + confidence
```

Each step is rendered as a small surface (approx 32×32 or bar chart) with a label and arrow. This mode uses the right panel's full 160×180 space as a vertical pipeline diagram.

Bottom bar: `Pipeline: filter→vision→features→classify | Method: hog`

### 5.9 Controls

| Key | Action |
|---|---|
| `TAB` | Cycle through 5 modes |
| `SPACE` | Cycle source surface |
| `W/A/S/D` | Move analysis rect (Mode 0 and 1) |
| `+/-` | Resize analysis rect (Mode 0 and 1) |
| `M` | Cycle feature extraction method (hog / lbp / color_hist / combined) |
| `L` | Open model loader — enter filename in bottom bar |
| `R` | Reload professor sample model |
| `F` | Freeze source surface |
| `S` | Save right panel PNG to `tests/output/demo/pattern_{mode}_{timestamp}.png` |
| `ESC` | Return to DemoMenuScene |

### 5.10 Model Loading (`L` Key)

When `L` is pressed, the bottom bar becomes a text input field:

```
Load model: student_assets/models/[  ]
```

The student types the filename (without path prefix — the `student_assets/models/` prefix is fixed). Only `.pkl` files are accepted. On `ENTER`:

1. `PatternRecognitionTools.load_model(STUDENT_ASSETS_DIR / "models" / filename)` is called.
2. On success: the new model replaces the current model. Model info displayed in top bar.
3. On failure: error message displayed for 2 seconds in bottom bar. Professor model restored.

This mechanism allows students to validate their trained models without modifying any game code.

### 5.11 Expected Inputs

| Input Type | Description |
|---|---|
| Source surface | SPACE cycles through 5 options |
| Analysis rect | W/A/S/D to position, +/- to resize |
| Mode | TAB cycles through 5 modes |
| Feature method | M to cycle |
| Student model | L key + filename + ENTER |

### 5.12 Expected Outputs

| Output | Location |
|---|---|
| Predicted class label | Right panel, large font |
| Confidence percentage | Right panel |
| Top-3 probability bars | Right panel |
| Feature vector bar chart | Right panel bottom |
| Nearest training sample | Mode 1: right panel |
| Confusion matrix | Mode 3: right panel |
| Pipeline diagram | Mode 4: right panel |
| Saved PNG | `tests/output/demo/` on `S` key |

### 5.13 Visualization Rules

1. **Probability bars:** Horizontal bars, each 6px tall with 2px gap. Length proportional to probability (max bar = 120px = 100%). Label left of bar, percentage right.
2. **Class colors:** Assigned deterministically by hashing class name: `color = PALETTE[hash(class_name) % len(PALETTE)]`. Palette: 8 distinct colors from the SNES palette.
3. **Confidence threshold indicator:** A thin vertical line at 70% on the probability bars. If the top prediction's bar reaches this line, the confidence indicator glows green. Below 70%, it glows yellow.
4. **Analysis rect:** 1px yellow border. When rect moves, it briefly flashes white (2 frames) to indicate movement.
5. **Confusion matrix cell:** Cell size 20×20px. Value printed in 5×7 font. Color: green for diagonal (intensity = value / max_diagonal), red for off-diagonal (intensity = value / max_off_diagonal).
6. **Pipeline arrows:** 4px-wide downward arrow (▼) drawn between each step in Mode 4.

### 5.14 Assessment Usage

`PatternDemoScene` is used during **Practical Exam III**:

| Task | Scene Mode | Assessment Goal |
|---|---|---|
| Load a model and run inference on a specified surface | INFERENCE | Model loading + inference |
| Report the top prediction and confidence for a given input | INFERENCE | Classification reading |
| Find the nearest training sample to a test input | FEATURE_COMPARE | k-NN comprehension |
| Report the model's test accuracy from the confusion matrix | CONFUSION | Evaluation reading |
| Trace a surface through the full pipeline | PIPELINE | Pipeline understanding |

### 5.15 Integration with Framework

`PatternDemoScene` is integrated with the framework as follows:

| Framework Component | Role in PatternDemoScene |
|---|---|
| `PatternRecognitionTools.predict()` | Core inference call in INFERENCE mode |
| `PatternRecognitionTools.load_model()` | Model loading via `L` key |
| `PatternRecognitionTools.classify_proba()` | Probability bars in right panel |
| `VisionTools.extract_features()` | Feature extraction for visualization |
| `FilterTools.gaussian_blur()` | Optional preprocessing step in PIPELINE mode |
| `BaseScene` | Scene lifecycle management |
| `InputManager` | W/A/S/D, M, L, TAB, SPACE input |
| `AudioManager` | No audio in demo scenes (muted) |
| `AssetLoader` | Loading source surfaces |

### 5.16 Professor Deliverables

| Deliverable | Description |
|---|---|
| `engine/scenes/pattern_demo_scene.py` | Complete implementation |
| `student_assets/datasets/sample_dataset.npz` | 90-sample, 3-class dataset (dark_zone, neutral, light_zone) |
| `student_assets/models/professor_sample.pkl` | Pre-trained k-NN (k=5) on sample dataset |
| 5 operation modes | All modes in §5.3 implemented |
| Model loading dialog | `L` key text input for student model |
| Probability bar visualization | Top-3 bars with class colors |
| Confusion matrix renderer | Color-coded grid from `EvaluationResult` |
| Pipeline diagram | Step-by-step visualization in Mode 4 |

### 5.17 Student Reuse

Students use `PatternDemoScene` to:
- Verify their trained model loads and produces non-trivial output.
- Confirm their model's feature method matches what they trained on.
- Capture inference screenshots for their stage README.
- Prepare for Practical Exam III tasks.

### 5.18 Learning Evidence

A student has engaged with `PatternDemoScene` effectively when:
- Their model loads successfully via the `L` key.
- Inference produces at least 2 distinct class outputs across different analysis rect positions or source surfaces.
- Their README includes a screenshot from INFERENCE mode showing their model's prediction.
- Their README includes the confusion matrix from CONFUSION mode.

---

## 6. Unit II Lab Scene — `VectorLabScene`

### 6.1 Scene Purpose

`VectorLabScene` is an interactive laboratory for vector arithmetic, normalization, dot product, and pursuit movement. It is the primary interactive reference for Unit II vector concepts.

Students use this scene to:
- Visualize vector components, magnitude, and direction.
- Observe normalized vectors and their relationship to movement.
- Calculate and read dot product and angle between two vectors in real time.
- Complete Practical Exam II vector tasks.

### 6.2 Layout

```
┌──────────────────────────────────────────────────────────────────┐
│  VECTOR LAB                                           UNIT II    │
│  [Mode: FREE MOVE]                         [ESC: Back]           │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│      [Experimental Area — 320×180 px]                           │
│      Two draggable/controllable points (Player, Enemy)           │
│      Vector arrow from Enemy to Player with arrow head           │
│                                                                  │
│      Math Info Panel (bottom right corner of area):              │
│      v = (dx, dy)  |v| = N   ^v = (nx, ny)                     │
│      Dot = D   Angle = θ°                                       │
│                                                                  │
├──────────────────────────────────────────────────────────────────┤
│  v=(24, -36)  |v|=43.3  ^v=(0.55,-0.83)  Dot= -0.27  θ=106°    │
│  [TAB: mode]  [N: norm toggle]  [R: reset]  [arrows: move]      │
└──────────────────────────────────────────────────────────────────┘
```

### 6.3 Operation Modes

| Mode | Name | Description |
|---|---|---|
| 0 | FREE MOVE | Both points move independently. Vector AB updates live. |
| 1 | CHASE | Enemy moves toward Player using `vec2_normalize()` every frame. |
| 2 | ORBIT | Player orbits around center; Enemy faces Player. Dot product readout. |
| 3 | DISTANCE CHECK | Distance between points displayed with threshold indicator. |

### 6.4 Controls

| Key | Action |
|---|---|
| `ARROWS` | Move Player point (modes 0, 1) / orbit (mode 2) |
| `W/A/S/D` | Move Enemy point (mode 0 only) |
| `TAB` | Cycle modes |
| `N` | Toggle normalized vector display |
| `R` | Reset positions to defaults |
| `S` | Save screenshot |
| `ESC` | Return to DemoMenuScene |

### 6.5 Pedagogical Purpose

Students learn to connect the abstract vector formulas (`|v|`, `v̂`, `a·b`, `θ`) with visible spatial outcomes. The CHASE mode demonstrates why normalized vectors are essential for consistent-speed pursuit. The math info panel reinforces the mapping between formula and visual.

---

## 7. Unit II/III Lab Scene — `TransformLabScene`

### 7.1 Scene Purpose

`TransformLabScene` demonstrates 2D affine transformations: translation, rotation, scaling, shearing, and composite transforms. It is the primary interactive reference for Unit II/III transformation concepts.

Students use this scene to:
- See the effect of each transformation matrix on a shape.
- Understand the difference between translation and rotation matrices.
- Observe that matrix composition is not commutative (translate→rotate ≠ rotate→translate).
- Read and interpret a live 3×3 transformation matrix.

### 7.2 Layout

```
┌──────────────────────────────────────────────────────────────────┐
│  TRANSFORM LAB                                  UNIT II/III      │
│  [Mode: TRANSLATE]                           [ESC: Back]         │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│      [Experimental Area — 320×160 px]                           │
│      Original shape (ghost outline) + transformed shape (filled) │
│      Coordinate grid background                                 │
│                                                                  │
│      ┌──────────────────────┐                                    │
│      │  TRANSFORMATION      │  3×3 matrix display               │
│      │  [1.00 0.00 32.00]  │  (toggle with N)                   │
│      │  [0.00 1.00 16.00]  │                                    │
│      │  [0.00 0.00  1.00]  │                                    │
│      └──────────────────────┘                                    │
│                                                                  │
├──────────────────────────────────────────────────────────────────┤
│  dx=32  dy=16  |  [TAB:mode]  [arrows:translate]  [N:matrix]    │
└──────────────────────────────────────────────────────────────────┘
```

### 7.3 Operation Modes

| Mode | Name | Description |
|---|---|---|
| 0 | TRANSLATE | Move shape with arrow keys. Matrix shows translation components. |
| 1 | ROTATE | Rotate shape around its center. Matrix shows sin/cos values. |
| 2 | SCALE | Scale shape (arrow keys change scale factor). |
| 3 | SHEAR | Shear shape horizontally/vertically. |
| 4 | COMPOSITE | Apply translate then rotate vs rotate then translate (toggle). |

### 7.4 Controls

| Key | Action |
|---|---|
| `LEFT/RIGHT` | Primary parameter (translate X, rotate angle, scale X, shear X) |
| `UP/DOWN` | Secondary parameter (translate Y, scale Y, shear Y) |
| `TAB` | Cycle modes |
| `N` | Toggle 3×3 matrix panel |
| `R` | Reset shape to origin |
| `S` | Save screenshot |
| `ESC` | Return to DemoMenuScene |

### 7.5 Pedagogical Purpose

The ghost outline of the original shape makes the transformation visually obvious. The live 3×3 matrix display connects visual effects to linear algebra. COMPOSITE mode demonstrates non-commutativity — students see visibly different results from translate→rotate vs rotate→translate.

---

## 8. Unit III Lab Scene — `CurveEditorScene`

### 8.1 Scene Purpose

`CurveEditorScene` is an interactive Bézier and spline editor. Students place control points and watch the curve update in real time. Supports quadratic Bézier, cubic Bézier, high-degree Bézier, Catmull-Rom spline, B-Spline, and a de Casteljau step-by-step animation mode.

Students use this scene to:
- Understand how control points define curve shape.
- Visualize the de Casteljau algorithm one iteration at a time.
- Compare Bézier vs Catmull-Rom vs B-Spline interpolation behavior.
- Prepare for Unit III curve exam tasks.

### 8.2 Layout

```
┌──────────────────────────────────────────────────────────────────┐
│  CURVE EDITOR                                      UNIT III      │
│  [Mode: BEZIER_CUBIC (degree 3)]              [ESC: Back]        │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│      [Canvas — 320×180 px]                                      │
│      Control points (draggable circles)                          │
│      Control polygon (lines between points)                      │
│      Curve (thick line through interpolation)                    │
│      De Casteljau lines (if toggled)                            │
│                                                                  │
│      Grid background with 16px spacing                          │
│                                                                  │
├──────────────────────────────────────────────────────────────────┤
│  Points: 4  |  Deg: 3  |  [TAB:mode]  [D:de Casteljau]  [+/-]  │
└──────────────────────────────────────────────────────────────────┘
```

### 8.3 Operation Modes

| Mode | Name | Description |
|---|---|---|
| 0 | BEZIER_QUAD | 3 control points, quadratic Bézier |
| 1 | BEZIER_CUBIC | 4 control points, cubic Bézier |
| 2 | BEZIER_HIGH | N control points, high-degree Bézier |
| 3 | CATMULL_ROM | Catmull-Rom spline (passes through all points) |
| 4 | BSPLINE | B-Spline (control points influence but do not pass through) |
| 5 | DE_CASTELJAU | Step-by-step de Casteljau animation |

### 8.4 Controls

| Key | Action |
|---|---|
| `MOUSE CLICK+DRAG` | Move control point |
| `TAB` | Cycle modes |
| `D` | Toggle de Casteljau visualization (modes 0–2) |
| `+` / `-` | Add / remove control point (modes 2, 4) |
| `1`–`5` | Jump directly to mode |
| `R` | Reset control points to default positions |
| `S` | Save screenshot |
| `ESC` | Return to DemoMenuScene |

### 8.5 Pedagogical Purpose

Dragging control points provides immediate visual feedback of how each point influences the curve. The de Casteljau animation mode reveals the recursive linear interpolation behind Bézier curves. Comparing Bézier, Catmull-Rom, and B-Spline on the same control points clarifies the mathematical difference between approximation (Bézier) and interpolation (Catmull-Rom).

---

## 9. Unit III/IV Lab Scene — `InterpolationLabScene`

### 9.1 Scene Purpose

`InterpolationLabScene` demonstrates linear interpolation, easing functions, and keyframe animation curves. Students adjust `t` and watch the interpolated value move between endpoints.

Students use this scene to:
- Understand the lerp formula `P = A + t(B - A)`.
- Compare 10 easing functions (Linear, Quad In/Out/InOut, Cubic In/Out, Bounce Out, Elastic Out, Sine In/Out).
- Build a multi-keyframe animation and watch eased interpolation between frames.
- Prepare for animation-related tasks in their stages.

### 9.2 Operation Modes

| Mode | Name | Description |
|---|---|---|
| 0 | LERP | Two endpoints A and B. `t` slider moves a point between them. Formula displayed. |
| 1 | EASING CURVES | Graph of current easing function. 10 functions cycled via UP/DOWN. |
| 2 | KEYFRAME ANIM | 3 keyframes with eased animation loop. SPACE to toggle auto-play. |

### 9.3 Controls

| Key | Action |
|---|---|
| `LEFT/RIGHT` | Adjust `t` value (mode 0) |
| `UP/DOWN` | Cycle easing function (modes 1, 2) |
| `SPACE` | Toggle auto-animation (mode 2) |
| `TAB` | Cycle modes |
| `R` | Reset |
| `S` | Save screenshot |
| `ESC` | Return to DemoMenuScene |

### 9.4 Pedagogical Purpose

The LERP mode demystifies the formula by showing every intermediate position. The easing curves graph provides an intuitive visual of "slow in, fast out" vs linear. Keyframe animation mode connects interpolation theory to game animation practice.

---

## 10. Unit V Lab Scene — `ColorTheoryScene`

### 10.1 Scene Purpose

`ColorTheoryScene` is an interactive color space explorer for RGB, HSV, HSL, CMYK, and alpha blending. It shows step-by-step conversion algorithms, not just final values.

Students use this scene to:
- Explore how R/G/B sliders affect the resulting color.
- Understand HSV and HSL as perceptual color spaces.
- Follow the step-by-step RGB→HSV and RGB→HSL conversion math.
- Practice alpha blending with the formula `out = src·α + dst·(1-α)`.

### 10.2 Operation Modes

| Mode | Name | Description |
|---|---|---|
| 0 | RGB EXPLORER | R/G/B sliders with live color swatch and hex readout |
| 1 | HSV EXPLORER | H/S/V sliders. `SHIFT` toggles step-by-step conversion display |
| 2 | HSL EXPLORER | H/S/L sliders. `SHIFT` toggles step-by-step conversion display |
| 3 | CMYK EXPLORER | C/M/Y/K sliders with live RGB preview |
| 4 | ALPHA BLEND | Two-layer blending with α slider. Formula displayed with live values |
| 5 | CHALLENGE | Match a random target color using RGB sliders. `SPACE` submits, diff shown |

### 10.3 Controls

| Key | Action |
|---|---|
| `LEFT/RIGHT` | Decrease/increase selected channel |
| `UP/DOWN` | Cycle to next/previous channel |
| `TAB` | Cycle modes |
| `SHIFT` | Toggle step-by-step algorithm display (modes 1, 2) |
| `SPACE` | Submit challenge attempt (mode 5) |
| `R` | Reset / new challenge |
| `S` | Save screenshot |
| `ESC` | Return to DemoMenuScene |

### 10.4 Pedagogical Purpose

The color explorer modes let students build intuition for each color space by direct manipulation. The step-by-step conversion display reveals the math behind RGB→HSV/HSL, making the algorithm concrete rather than opaque. The Challenge mode gamifies color matching and reinforces perceptual color distance.

---

## 11. Unit V/VIII Lab Scene — `NoiseLabScene`

### 11.1 Scene Purpose

`NoiseLabScene` demonstrates value noise, Perlin noise, and fractal noise generation. Students adjust parameters and see the noise map update in real time.

Students use this scene to:
- Understand how octaves, persistence, and lacunarity affect fractal noise.
- Compare value noise (blocky) vs Perlin noise (smooth) visually.
- Observe how scale changes the frequency of the noise pattern.
- Prepare for procedural generation tasks in their stages.

### 11.2 Operation Modes

| Mode | Name | Description |
|---|---|---|
| 0 | VALUE NOISE | Grayscale value noise texture |
| 1 | PERLIN NOISE | Smoother Perlin noise texture |
| 2 | FRACTAL NOISE | Multi-octave fractal noise (value or Perlin base) |

### 11.3 Parameters

| Parameter | Range | Step | Description |
|---|---|---|---|
| Octaves | 1–8 | 1 | Number of noise layers summed |
| Persistence | 0–1 | 0.05 | Amplitude decay per octave |
| Lacunarity | 1–8 | 0.1 | Frequency multiplier per octave |
| Scale | 0.005–0.5 | 0.005 | Base frequency of the noise |
| Seed | 0–9999 | 1 | Random seed for noise pattern |

### 11.4 Controls

| Key | Action |
|---|---|
| `UP/DOWN` | Cycle selected parameter |
| `LEFT/RIGHT` | Adjust selected parameter value |
| `SPACE` | Randomize seed |
| `TAB` | Cycle noise type |
| `R` | Reset all parameters to defaults |
| `S` | Save screenshot |
| `ESC` | Return to DemoMenuScene |

### 11.5 Pedagogical Purpose

The real-time noise map provides immediate visual feedback for each parameter. Students can see how increasing octaves adds detail, how persistence controls roughness, and how lacunarity changes feature frequency. Comparing value noise directly against Perlin noise clarifies why Perlin's smoother output is preferred for natural terrains.

---

## 12. Unit VI Lab Scene — `CollisionLabScene`

### 12.1 Scene Purpose

`CollisionLabScene` demonstrates axis-separated AABB collision resolution. Students observe why the order of axis resolution matters: resolving Y before X causes the wall-climb bug (entity walks up walls), while X before Y resolves correctly.

Students use this scene to:
- Understand axis-separated collision resolution.
- See the wall-climb bug in action and understand its root cause.
- Observe one-way platform collision behavior.
- Prepare for collision implementation in their own stages.

### 12.2 Layout

```
┌──────────────────────────────────────────────────────────────────┐
│  COLLISION LAB                                       UNIT VI     │
│  [Mode: Y-FIRST (wall-climb bug)]             [ESC: Back]        │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│      [Test Level — 320×180 px]                                  │
│      Floor, wall gap, platforms, one-way platform               │
│      Player rect (20×32 px, colored)                            │
│                                                                  │
│      Collision info overlay (top-right):                        │
│      prev_bottom=184  velocity=(64,-120)  grounded=YES          │
│                                                                  │
├──────────────────────────────────────────────────────────────────┤
│  Mode: Y-FIRST  |  prev_bottom: 184  |  [B: demo bug]  [R]     │
└──────────────────────────────────────────────────────────────────┘
```

### 12.3 Operation Modes

| Mode | Name | Description |
|---|---|---|
| 0 | NO COLLISION | Player passes through everything |
| 1 | Y-FIRST | Resolve Y axis first — shows wall-climb bug when walking into wall |
| 2 | X-FIRST | Resolve X axis first — correct resolution |

### 12.4 Controls

| Key | Action |
|---|---|
| `LEFT/RIGHT` | Move player horizontally |
| `SPACE`/`UP` | Jump |
| `TAB` | Cycle collision mode |
| `B` | Auto-demonstrate wall-climb bug in Y-FIRST mode |
| `R` | Reset player position |
| `S` | Save screenshot |
| `ESC` | Return to DemoMenuScene |

### 12.5 Pedagogical Purpose

The three modes (no collision → buggy → correct) scaffold understanding of axis-separated collision. Students first see the problem (wall-climb in Y-FIRST), then the correct behavior (X-FIRST). The collision info overlay (`prev_bottom`, velocity, grounded) provides the data needed to understand why the bug occurs.

---

## 13. Demo Menu Scene — `DemoMenuScene`

### 13.1 Purpose

`DemoMenuScene` is the entry point for the Academic Demos. It presents ten options (7 theory labs + 3 academic demos) and navigates to the selected scene.

### 6.2 Layout

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│              ACADEMIC DEMONSTRATIONS                            │
│                                                                 │
│         ▶  Unit II            — Vectors & Transformations       │
│            Unit II/III        — 2D Transformations              │
│            Unit III           — Bézier Curves & Splines         │
│            Unit III/IV        — Interpolation & Easing          │
│            Unit V             — Color Spaces & Alpha Blending   │
│            Unit V/VIII        — Noise & Procedural Generation   │
│            Unit VI            — AABB Collision Resolution       │
│            Unit VII           — Digital Image Processing        │
│            Unit VIII          — Segmentation & Analysis          │
│            Unit IX            — Pattern Recognition             │
│                                                                 │
│                        [ESC: Back to Title]                     │
└─────────────────────────────────────────────────────────────────┘
```

### 6.3 Controls

| Key | Action |
|---|---|
| `UP` / `DOWN` | Navigate between options |
| `CONFIRM` (Enter/Z/A) | Enter selected demo |
| `ESC` | Return to TitleScene |

---

## 14. Integration with Evaluation Instruments

### 14.1 Practical Exam II — Units VII and VIII

The exam is conducted in the laboratory. Students receive:
1. A target output PNG (saved from the demo scene by the professor).
2. A source surface PNG.
3. 90 minutes to reproduce the target output using the demo scene.

They must document the parameters used (kernel, sigma, threshold, kernel size) on their exam sheet.

### 14.2 Practical Exam III — Unit IX

The exam is conducted in the laboratory. Students receive:
1. A dataset file (`.npz`).
2. Instructions to train a specific classifier with specific hyperparameters.
3. 90 minutes to train, evaluate, and demonstrate inference using the demo scene.

They submit: the `.pkl` model, a screenshot of the confusion matrix, and a screenshot of the inference in Mode 0.

### 14.3 Final Presentation Integration

During the final presentation, students use the demo scenes as a live reference to:
- Show how they calibrated their parameters before implementing them in their stage.
- Demonstrate the processing pipeline from raw surface to classification result.
- Compare their model's confusion matrix with the professor's sample model.

---

## 15. Technical Implementation Notes

These notes are directed at the AI coding assistant implementing the demo scenes.

### 15.1 Frame Throttling Pattern

All expensive operations in the demo scenes use a shared throttle pattern:

```
DemoScene.update_counter: int  # Incremented every frame
DemoScene.cached_result: pygame.Surface | None  # Cached output

on update():
    update_counter += 1
    if should_update(current_mode, update_counter):
        cached_result = apply_operation(source, params)
    draw cached_result to right panel
```

`should_update(mode, counter)` returns True based on the mode's update frequency table (see §3.7 for FilterDemoScene, equivalent tables apply to VisionDemoScene and PatternDemoScene).

### 15.2 Source Surface Management

The source surface is always rendered at 160×180 pixels in the left panel. If the original source is larger (e.g., 320×224 live capture), it is scaled to 160×180 using `pygame.transform.scale()` for display only. The actual operation is applied to the original size unless it exceeds the performance ceiling.

For the WATERSHED and CANNY operations on large surfaces, the source is scaled to a maximum of 160×112 before processing (maintaining aspect ratio).

### 15.3 Text Input for Model Loading

The model loading text input in `PatternDemoScene` is implemented as a simple character buffer:

```
text_buffer: str = ""
cursor_visible: bool = True  # Blinks every 0.5 seconds

On KEYDOWN:
    if key is BACKSPACE: text_buffer = text_buffer[:-1]
    elif key is RETURN: attempt_load(text_buffer); text_buffer = ""
    elif key is printable: text_buffer += event.unicode

Render:
    draw "Load model: student_assets/models/" + text_buffer + ("|" if cursor_visible)
```

Only `.pkl` extension input is accepted. If the student enters a name without `.pkl`, it is appended automatically.

### 15.4 Save Functionality

The `S` key saves the right panel surface to disk:

```
path = Path("tests/output/demo") / f"{scene_prefix}_{mode_name}_{timestamp}.png"
pygame.image.save(right_panel_surface, str(path))
# Show "Saved: {filename}" in bottom bar for 2 seconds
```

The `tests/output/demo/` directory is created if it does not exist.

### 15.5 Font Sizing

| Context | Previous Size | Current Size |
|---|---|---|
| HUD bitmap font (small text, hearts, numbers) | 5×7 px | 5×7 px (unchanged) |
| Banner font (stage/boss names) | 6×9 px | 6×15 px |
| Dialog/UI font (message boxes, menus) | 7×11 px | 7×18 px |

Larger font sizes improve readability on modern displays. SDL_HINT_RENDER_SCALE_QUALITY=0 ensures nearest-neighbor scaling for pixel-art crispness. Antialiasing is enabled on all font rendering.

### 15.6 Error Display

All exceptions caught during demo operations (invalid parameter, failed load, processing error) are displayed in the bottom bar for 2 seconds:

```
error_message: str = ""
error_timer: float = 0.0

On exception:
    error_message = f"Error: {str(e)[:60]}"
    error_timer = 2.0

On update:
    if error_timer > 0:
        error_timer -= dt
    if error_timer <= 0:
        error_message = ""

On draw:
    if error_message:
        draw error_message in red in bottom bar
    else:
        draw normal bottom bar
```

---

## 16. Restrictions

| Restriction | Scope |
|---|---|
| Demo scenes are professor-owned; students do not modify them | All demo scene files |
| Demo scenes do not call `EventBus` | No event emission from demos |
| Demo scenes do not affect game state | No entity spawning, no stage progression |
| Model loading accepts only `.pkl` files from `student_assets/models/` | Security constraint |
| No audio playback in demo scenes | AudioManager.stop_music() called on demo entry |
| Demo scenes are not accessible mid-stage | Accessible only from DemoMenuScene via TitleScene |

---

## 17. Future Extensions

| Extension | Description | Target |
|---|---|---|
| Video export mode | Record demo session as GIF | Professor tooling |
| Parameter preset save/load | Save named parameter sets for exam use | Practical exams |
| Side-by-side classifier comparison | Two models shown simultaneously | Unit IX advanced |
| Batch inference mode | Classify all 5 source surfaces automatically | Unit IX exam |
| Custom dataset builder | Draw labeled regions on source surface | Unit IX advanced |


---
## 🔗 Documentos Relacionados

- [[11_FILTER_TOOLS_SPEC.md|Filter Tools Spec]]
- [[12_VISION_TOOLS_SPEC.md|Vision Tools Spec]]
- [[13_PATTERN_RECOGNITION_SPEC.md|Pattern Recognition Spec]]
- [[37_DEMO_QUICK_GUIDE.md|Demo Quick Guide]]
