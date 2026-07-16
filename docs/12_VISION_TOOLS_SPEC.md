---
document_id: "LOI-VISION-012"
title: "Legacy of InFest — Vision Tools Specification"
aliases: ["Vision Tools Spec"]
tags: ["vision", "segmentation", "processing"]
description: "Unit VIII segmentation subsystem"
source: "docs/12_VISION_TOOLS_SPEC.md"
date_processed: "2026-07-14"
---

# Legacy of InFest — Vision Tools Specification

**Document ID:** LOI-VISION-012  
**Version:** 1.0.0  
**Status:** Official  
**Compatibility:** Requires LOI-ARCH-003, LOI-FILTER-011, LOI-LIBS-010  
**Audience:** Professor, Teaching Assistants, AI coding assistants (Claude Code, Cline, OpenCode, Codex)

---

## 1. Overview

`VisionTools` is the segmentation and image analysis subsystem of the Legacy of InFest academic framework. It encapsulates all operations taught in **Unit VIII** of the course syllabus: thresholding, Otsu's method, morphological operations, connected component analysis, region analysis, watershed segmentation, and feature extraction.

This module is the bridge between the raw filter operations of Unit VII (covered by `FilterTools`) and the classification operations of Unit IX (covered by `PatternRecognitionTools`). It transforms filtered surfaces into structured data — regions, labels, contours, masks, and feature vectors — that can be interpreted and acted upon by game logic.

The module is located at:

```
framework/processing/vision_tools.py
```

---

## 2. Academic Purpose

`VisionTools` makes Unit VIII concepts **spatially visible** within the game. Students do not process abstract scientific images — they process regions of their own game stage, identify meaningful zones within them, and let those zones drive game behavior. This transforms segmentation from a theoretical exercise into a design decision.

### 2.1 Learning Objectives Supported

| Objective | VisionTools Mechanism |
|---|---|
| Apply binary thresholding as a decision boundary | `threshold_binary()` separates pixels into two classes |
| Apply Otsu's method as automatic threshold selection | `threshold_otsu()` computes the optimal threshold adaptively |
| Apply erosion and dilation to binary images | `morphological_erode()`, `morphological_dilate()` |
| Identify connected regions in binary images | `connected_components()` returns labeled regions |
| Extract region properties (area, centroid, bounding box) | `analyze_regions()` returns per-region statistics |
| Apply watershed to over-segmented images | `watershed_segment()` returns a labeled surface |
| Extract a feature vector from a surface region | `extract_features()` returns a numeric descriptor |

### 2.2 Position in the Academic Pipeline

```
Raw Surface (game background, sprite, screen region)
    ↓ FilterTools (Unit VII)
Preprocessed Surface (blurred, edge-detected, brightness-adjusted)
    ↓ VisionTools (Unit VIII)
Structured Data (masks, regions, labels, feature vectors)
    ↓ PatternRecognitionTools (Unit IX)
Classification result → Game behavior
```

---

## 3. Framework Location

```
framework/
└── processing/
    ├── filter_tools.py
    └── vision_tools.py          ← This module
```

### 3.1 Position in the Dependency Hierarchy

```
Stages (student code)
    ↓
framework/processing/vision_tools.py   ← Students call this
    ↓
framework/processing/filter_tools.py   ← VisionTools may call FilterTools internally
    ↓
numpy, scipy, opencv-python, scikit-image
```

---

## 4. Architecture Integration

### 4.1 Connections to the Framework

| Integration Point | Description |
|---|---|
| `FilterTools` | VisionTools may internally call `FilterTools.gaussian_blur()` for preprocessing within watershed; students may also chain them explicitly |
| `PatternRecognitionTools` | VisionTools' `extract_features()` produces the feature vector that PatternRecognitionTools' classifiers consume |
| Stage scenes (student code) | Students call `VisionTools` from stage `update()` to drive behavior from visual data |
| Unit test suite (`tests/test_vision_tools.py`) | Each method saves labeled-image and mask PNG outputs to `tests/output/vision/` |

### 4.2 What VisionTools Does NOT Do

| Forbidden Action | Reason |
|---|---|
| Does not call `EventBus` | Pure computation module |
| Does not modify entity state directly | Students use the return values to modify state |
| Does not call `InputManager` or `AudioManager` | No interaction logic |
| Does not read or write files | All I/O through return values |
| Does not modify input surfaces in place | All operations return new data |

---

## 5. Dependencies

| Library | Import | Used For |
|---|---|---|
| `numpy` | `import numpy as np` | Array representation, label arrays, feature vectors |
| `cv2` (opencv-python) | `import cv2` | Threshold, morphology, connected components, watershed, contours |
| `scipy.ndimage` | `from scipy.ndimage import label` | Connected component labeling (alternative to cv2) |
| `skimage.feature` | `from skimage.feature import hog, local_binary_pattern` | HOG and LBP feature extraction |
| `skimage.measure` | `from skimage.measure import regionprops` | Region properties (area, centroid, eccentricity) |
| `pygame` | `import pygame` | Surface input/output |

**Students never import any of the above.**

---

## 6. Class Diagram

```
VisionTools
│
├── [Threshold]
│   ├── threshold_binary(surface, threshold) → Surface (mask)
│   └── threshold_otsu(surface) → tuple[Surface, int]
│
├── [Morphology]
│   ├── morphological_erode(surface, kernel_size) → Surface
│   ├── morphological_dilate(surface, kernel_size) → Surface
│   ├── morphological_open(surface, kernel_size) → Surface
│   └── morphological_close(surface, kernel_size) → Surface
│
├── [Connected Components]
│   ├── connected_components(mask_surface) → ComponentResult
│   └── filter_components_by_area(result, min_area, max_area) → ComponentResult
│
├── [Region Analysis]
│   ├── analyze_regions(mask_surface) → list[RegionInfo]
│   └── largest_region(mask_surface) → RegionInfo | None
│
├── [Watershed]
│   └── watershed_segment(surface) → Surface (labeled color overlay)
│
├── [Feature Extraction]
│   ├── extract_features(surface, method) → np.ndarray
│   ├── extract_hog(surface) → np.ndarray
│   ├── extract_lbp(surface) → np.ndarray
│   └── extract_color_histogram(surface, bins) → np.ndarray
│
├── [Bounding Boxes and Contours]
│   ├── find_contours(mask_surface) → list[np.ndarray]
│   └── bounding_boxes_from_mask(mask_surface) → list[pygame.Rect]
│
└── [Internal Utilities — private]
    ├── _to_gray_array(surface) → np.ndarray
    ├── _to_binary_array(mask_surface) → np.ndarray
    ├── _label_array_to_color_surface(label_array) → Surface
    ├── _validate_mask(surface) → None
    └── _validate_surface(surface) → None
```

### 6.1 Return Type Definitions

#### `ComponentResult` (named tuple or dataclass)

| Field | Type | Description |
|---|---|---|
| `label_array` | `np.ndarray` (`int32`, shape `(H, W)`) | Each pixel labeled with its component ID (0 = background) |
| `num_components` | `int` | Total number of distinct connected components |
| `component_sizes` | `dict[int, int]` | Mapping of label ID → pixel count |
| `label_surface` | `pygame.Surface` | Color-coded surface for visual debugging |

#### `RegionInfo` (named tuple or dataclass)

| Field | Type | Description |
|---|---|---|
| `label` | `int` | Component label ID |
| `area` | `int` | Area in pixels |
| `centroid` | `tuple[float, float]` | `(x, y)` centroid in pixel coordinates |
| `bounding_rect` | `pygame.Rect` | Axis-aligned bounding box |
| `eccentricity` | `float` | Shape eccentricity: 0 = circle, 1 = line |
| `solidity` | `float` | Ratio of area to convex hull area |
| `perimeter` | `float` | Perimeter in pixels |

---

## 7. VisionTools Class

### 7.1 Responsibilities

1. Accept `pygame.Surface` objects and return structured data.
2. Convert surfaces to grayscale/binary arrays as needed by each operation.
3. Apply the mathematical operation using the appropriate library.
4. Return results as `pygame.Surface`, NumPy arrays, or documented data structures.
5. Validate all inputs and raise descriptive exceptions.

---

## 8. Threshold Operations

### 8.1 `VisionTools.threshold_binary(surface, threshold)`

**Purpose:** Apply a fixed binary threshold to a grayscale representation of the surface. Every pixel with luminance ≥ `threshold` becomes white (255, 255, 255). Every pixel below becomes black (0, 0, 0). This separates the image into two classes and is the foundational operation of all binary image analysis.

**Inputs:**

| Parameter | Type | Constraints | Description |
|---|---|---|---|
| `surface` | `pygame.Surface` | RGB/RGBA, any size | Source surface |
| `threshold` | `int` | `[0, 255]` | Intensity cutoff value |

**Outputs:** New `pygame.Surface` of identical size. Binary: pixels are either pure white or pure black. RGB, no alpha.

**Internal Pipeline:**
```
surface → grayscale array (luminance formula: 0.299R + 0.587G + 0.114B)
       → cv2.threshold(arr, threshold, 255, cv2.THRESH_BINARY)
       → binary uint8 array
       → RGB surface (replicate grayscale across 3 channels)
```

**Restrictions:**

- `threshold` outside `[0, 255]` raises `ValueError`.
- Output is always RGB binary (not grayscale single-channel).
- Does not modify input.

**Dependencies:** `numpy`, `opencv-python`

**Usage Example:**

```python
from framework.processing.vision_tools import VisionTools

# Segment a background layer — identify bright regions:
mask = VisionTools.threshold_binary(self.background_surface, threshold=128)

# Count white pixels (bright regions):
bright_boxes = VisionTools.bounding_boxes_from_mask(mask)
if len(bright_boxes) > 3:
    EventBus.emit("SHOW_MESSAGE", text="Many bright zones detected!", duration=2.0)
```

---

### 8.2 `VisionTools.threshold_otsu(surface)`

**Purpose:** Apply Otsu's automatic thresholding method. Instead of requiring a manual threshold value, Otsu's method analyzes the histogram and finds the threshold that minimizes intra-class intensity variance (equivalently, maximizes inter-class variance). This demonstrates adaptive decision-making based on image statistics.

**Inputs:**

| Parameter | Type | Description |
|---|---|---|
| `surface` | `pygame.Surface` | RGB/RGBA, any size |

**Outputs:** A `tuple` of two values:

| Index | Type | Description |
|---|---|---|
| `[0]` | `pygame.Surface` | Binary mask surface (same as `threshold_binary` output) |
| `[1]` | `int` | The computed Otsu threshold value (for student documentation) |

**Internal Pipeline:**
```
surface → grayscale array
       → cv2.threshold(arr, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
       → (binary_array, computed_threshold_value)
       → return (surface, int(threshold_value))
```

**Restrictions:**

- Requires the surface to have meaningful tonal variation. A uniform surface will produce an arbitrary threshold; a warning is logged.
- Output surface is RGB binary.
- Does not modify input.

**Dependencies:** `numpy`, `opencv-python`

**Usage Example:**

```python
mask, otsu_t = VisionTools.threshold_otsu(self.terrain_surface)
print(f"Otsu threshold: {otsu_t}")  # For README documentation
regions = VisionTools.analyze_regions(mask)
```

---

## 9. Morphological Operations

All morphological operations require a **binary mask surface** as input (output of `threshold_binary` or `threshold_otsu`). They use a square structuring element of size `kernel_size × kernel_size`.

### 9.1 `VisionTools.morphological_erode(surface, kernel_size)`

**Purpose:** Apply morphological erosion to a binary mask. Erosion shrinks white regions by removing pixels on their boundaries. A pixel is kept white only if all pixels within the structuring element are also white. This removes small noise blobs and separates weakly connected regions.

**Inputs:**

| Parameter | Type | Constraints | Description |
|---|---|---|---|
| `surface` | `pygame.Surface` | Binary mask (RGB or grayscale) | Source binary mask |
| `kernel_size` | `int` | `≥ 1`, odd recommended | Side length of the square structuring element |

**Outputs:** New `pygame.Surface` of identical size. Binary mask after erosion.

**Dependencies:** `opencv-python` (`cv2.erode`)

**Usage Example:**

```python
mask = VisionTools.threshold_binary(bg_surface, 100)
eroded = VisionTools.morphological_erode(mask, kernel_size=3)
# Small isolated pixels removed from mask
```

---

### 9.2 `VisionTools.morphological_dilate(surface, kernel_size)`

**Purpose:** Apply morphological dilation to a binary mask. Dilation grows white regions by adding pixels to their boundaries. A pixel becomes white if any pixel within the structuring element is white. This fills small holes and connects nearby regions.

**Inputs/Outputs:** Same structure as `morphological_erode`.

**Dependencies:** `opencv-python` (`cv2.dilate`)

---

### 9.3 `VisionTools.morphological_open(surface, kernel_size)`

**Purpose:** Apply morphological opening (erosion followed by dilation). Opening removes small objects while preserving the shape and size of larger objects. Useful for noise removal in binary masks.

**Mathematical definition:** `open(A, B) = dilate(erode(A, B), B)`

**Inputs/Outputs:** Same structure as `morphological_erode`.

**Dependencies:** `opencv-python` (`cv2.MORPH_OPEN`)

---

### 9.4 `VisionTools.morphological_close(surface, kernel_size)`

**Purpose:** Apply morphological closing (dilation followed by erosion). Closing fills small holes within regions and connects nearby regions while preserving the overall size of objects.

**Mathematical definition:** `close(A, B) = erode(dilate(A, B), B)`

**Inputs/Outputs:** Same structure as `morphological_erode`.

**Dependencies:** `opencv-python` (`cv2.MORPH_CLOSE`)

---

### 9.5 Morphological Operations — Performance Table

| Operation | Kernel 3×3 | Kernel 7×7 | Kernel 15×15 |
|---|---|---|---|
| Erode | < 0.5ms | < 1ms | ~2ms |
| Dilate | < 0.5ms | < 1ms | ~2ms |
| Open | < 1ms | ~2ms | ~4ms |
| Close | < 1ms | ~2ms | ~4ms |

All timings for a 320×224 surface.

---

## 10. Connected Components

### 10.1 `VisionTools.connected_components(mask_surface)`

**Purpose:** Label all connected regions in a binary mask. Each distinct connected group of white pixels receives a unique integer label. The background (black pixels) is always label 0. This is the foundational operation for identifying distinct objects in a segmented image.

**Connectivity:** 8-connected (diagonal neighbors are connected).

**Inputs:**

| Parameter | Type | Description |
|---|---|---|
| `mask_surface` | `pygame.Surface` | Binary mask (output of threshold or morphology operation) |

**Outputs:** `ComponentResult` (see Section 6.1):
- `label_array`: `np.ndarray int32` shape `(H, W)` — each pixel holds its component label
- `num_components`: total distinct foreground components
- `component_sizes`: `{label_id: pixel_count}` for all labels
- `label_surface`: color-coded surface for visual debugging (each component a different color)

**Internal Pipeline:**
```
mask_surface → binary uint8 grayscale array
             → cv2.connectedComponentsWithStats(arr, connectivity=8)
             → (num_labels, label_array, stats, centroids)
             → build ComponentResult
             → generate color-coded label_surface
```

**Restrictions:**

- Input must be a binary surface (white/black). A warning is issued if non-binary values are detected.
- Maximum supported components: 32,767 (OpenCV limit).
- Does not modify input.

**Dependencies:** `numpy`, `opencv-python`

**Usage Example:**

```python
mask = VisionTools.threshold_binary(self.ground_surface, 140)
result = VisionTools.connected_components(mask)

print(f"Found {result.num_components} regions")
# Visual debug:
surface.blit(result.label_surface, (0, 0))
```

---

### 10.2 `VisionTools.filter_components_by_area(result, min_area, max_area)`

**Purpose:** Filter a `ComponentResult` to retain only components whose pixel area falls within `[min_area, max_area]`. Returns a new `ComponentResult` with only the qualifying components, and a new `label_surface` reflecting the filter.

**Inputs:**

| Parameter | Type | Constraints | Description |
|---|---|---|---|
| `result` | `ComponentResult` | From `connected_components()` | Input result to filter |
| `min_area` | `int` | `≥ 0` | Minimum component area in pixels |
| `max_area` | `int` | `> min_area` | Maximum component area in pixels |

**Outputs:** New `ComponentResult` with only qualifying components. Labels are **not renumbered** — the original label IDs are preserved to allow cross-referencing with the original `label_array`.

**Usage Example:**

```python
result = VisionTools.connected_components(mask)
# Keep only medium-sized regions (not noise, not background):
filtered = VisionTools.filter_components_by_area(result, min_area=50, max_area=2000)
```

---

## 11. Region Analysis

### 11.1 `VisionTools.analyze_regions(mask_surface)`

**Purpose:** Extract quantitative properties from each connected region in a binary mask. Returns a list of `RegionInfo` objects, one per foreground component, sorted by area (largest first). This is the bridge between a visual mask and numerical data that can drive game logic.

**Inputs:**

| Parameter | Type | Description |
|---|---|---|
| `mask_surface` | `pygame.Surface` | Binary mask surface |

**Outputs:** `list[RegionInfo]`, sorted by area descending. Empty list if no foreground regions found.

**`RegionInfo` fields** (see Section 6.1 for full definition):
- `label`, `area`, `centroid`, `bounding_rect`, `eccentricity`, `solidity`, `perimeter`

**Internal Pipeline:**
```
mask_surface → binary array → cv2.connectedComponentsWithStats
            → skimage.measure.regionprops (for eccentricity, solidity, perimeter)
            → build list[RegionInfo]
            → sort by area descending
```

**Dependencies:** `numpy`, `opencv-python`, `scikit-image` (`skimage.measure.regionprops`)

**Usage Example:**

```python
regions = VisionTools.analyze_regions(mask)

for region in regions:
    print(f"Area: {region.area}, Centroid: {region.centroid}")

    # Spawn an entity at each large region centroid:
    if region.area > 500:
        cx, cy = int(region.centroid[0]), int(region.centroid[1])
        spawn_position = pygame.Vector2(cx, cy)
        new_entity = MyCustomEntity(spawn_position)
        self.entities.append(new_entity)
```

---

### 11.2 `VisionTools.largest_region(mask_surface)`

**Purpose:** Convenience method. Returns the `RegionInfo` for the single largest connected region in the mask, or `None` if no foreground regions exist.

**Inputs/Outputs:** Same as `analyze_regions` but returns a single `RegionInfo` or `None`.

**Usage Example:**

```python
largest = VisionTools.largest_region(mask)
if largest:
    rect = largest.bounding_rect
    pygame.draw.rect(surface, (255, 0, 0), rect, 2)
```

---

## 12. Watershed Segmentation

### 12.1 `VisionTools.watershed_segment(surface)`

**Purpose:** Apply watershed segmentation to identify distinct regions separated by ridge lines. The watershed algorithm treats the image as a topographic surface (intensity = elevation) and floods it from marked minima. The ridgelines between flooding fronts form the segment boundaries.

This operation produces a richer segmentation than binary thresholding — it can separate touching or overlapping regions that thresholding would merge.

**Inputs:**

| Parameter | Type | Description |
|---|---|---|
| `surface` | `pygame.Surface` | Source surface (RGB/RGBA, any size) |

**Outputs:** New `pygame.Surface` of identical size. A color-coded label overlay where each segment is filled with a unique color. This is intended for **visual display** — not for further binary processing.

Additionally, returns a tuple: `(label_surface, label_array)` where `label_array` is the `np.ndarray int32` of component labels.

**Internal Pipeline:**
```
surface → grayscale → blur (Gaussian, sigma=1.0 internal)
        → distance transform (cv2.distanceTransform)
        → sure foreground mask (threshold at 70% of max distance)
        → unknown region (dilate - sure_fg)
        → connected components on sure_fg → markers
        → cv2.watershed(original_bgr, markers)
        → color-code each label → return label_surface
```

**Restrictions:**

- Watershed is computationally expensive. Use on sub-surfaces or at reduced frequency (every 10+ frames).
- Output `label_surface` uses 8 distinct hue-separated colors for label visualization. If more than 8 segments exist, colors repeat.
- Does not modify input.

**Dependencies:** `numpy`, `opencv-python`

**Performance:** ~8–15ms for a 320×224 surface. Must be frame-throttled or pre-computed.

**Usage Example:**

```python
# Pre-compute at stage load:
label_surface, label_array = VisionTools.watershed_segment(self.background_surface)
self.segment_overlay = label_surface
self.segment_overlay.set_alpha(120)

# Draw every frame (no per-frame recompute):
surface.blit(self.segment_overlay, (0, 0))
```

---

## 13. Feature Extraction

Feature extraction converts a surface region into a compact numerical vector (the "feature vector") that can be used as input to a classifier in Unit IX.

### 13.1 `VisionTools.extract_features(surface, method='hog')`

**Purpose:** Compute a feature vector from a surface using the specified method. This is the primary integration point between VisionTools (Unit VIII) and PatternRecognitionTools (Unit IX).

**Inputs:**

| Parameter | Type | Constraints | Description |
|---|---|---|---|
| `surface` | `pygame.Surface` | RGB/RGBA, any size | Source surface |
| `method` | `str` | `'hog'`, `'lbp'`, `'color_hist'`, `'combined'` | Feature extraction method |

**Outputs:** `np.ndarray` of shape `(n,)` — a 1D feature vector. Length `n` depends on method.

| Method | Output Length | Description |
|---|---|---|
| `'hog'` | Variable (depends on surface size and HOG parameters) | Histogram of Oriented Gradients |
| `'lbp'` | 256 | Local Binary Pattern histogram |
| `'color_hist'` | `bins * 3` (default: 256 × 3 = 768) | Per-channel color histogram |
| `'combined'` | HOG + LBP + color_hist concatenated | All features combined |

**Restrictions:**

- Surface should be at minimum 8×8 pixels for HOG to produce meaningful features.
- Surface is internally resized to a canonical size (32×32) before feature extraction to ensure consistent vector length regardless of input size. This resizing is internal and does not affect the input surface.
- Does not modify input.

**Dependencies:** `numpy`, `scikit-image` (`hog`, `local_binary_pattern`), `opencv-python` (resizing)

**Usage Example:**

```python
# Extract HOG features from a 32×32 region around the player:
player_region = screen_surface.subsurface(pygame.Rect(
    player.rect.centerx - 16,
    player.rect.centery - 16,
    32, 32
))
features = VisionTools.extract_features(player_region, method='hog')
# features is now ready for PatternRecognitionTools.classify()
```

---

### 13.2 `VisionTools.extract_hog(surface)`

**Purpose:** Extract Histogram of Oriented Gradients (HOG) features. HOG captures the distribution of local gradient orientations — a shape descriptor that is robust to changes in illumination and small geometric distortions.

**HOG Parameters (fixed for consistency across all stages):**

| Parameter | Value |
|---|---|
| Orientations | 8 |
| Pixels per cell | 8×8 |
| Cells per block | 2×2 |
| Block normalization | L2-Hys |
| Input size (canonical) | 32×32 |

**Inputs:**

| Parameter | Type | Description |
|---|---|---|
| `surface` | `pygame.Surface` | Source surface (internally resized to 32×32) |

**Outputs:** `np.ndarray` of shape `(n,)`. For 32×32 canonical size: `n = 4 * 4 * 2 * 2 * 8 = 512` dimensions.

**Dependencies:** `scikit-image` (`skimage.feature.hog`), `opencv-python` (resize)

---

### 13.3 `VisionTools.extract_lbp(surface)`

**Purpose:** Extract Local Binary Pattern (LBP) histogram. LBP describes texture by comparing each pixel to its 8 neighbors and encoding the pattern as a binary number. The histogram of all LBP codes describes the texture character of the region.

**LBP Parameters:**

| Parameter | Value |
|---|---|
| Radius | 1 |
| Number of neighbors | 8 |
| Method | `'uniform'` (26 uniform patterns + 1 non-uniform = 27 bins) |
| Output | 256-bin histogram (standard bins for `uniform` with radius 1, n_points 8) |

**Inputs:**

| Parameter | Type | Description |
|---|---|---|
| `surface` | `pygame.Surface` | Source surface (internally resized to 32×32) |

**Outputs:** `np.ndarray` of shape `(256,)` — normalized histogram (sum = 1.0).

**Dependencies:** `scikit-image` (`skimage.feature.local_binary_pattern`), `numpy`

---

### 13.4 `VisionTools.extract_color_histogram(surface, bins=256)`

**Purpose:** Extract a concatenated per-channel color histogram. Computes the frequency distribution of intensity values for each R, G, B channel separately and concatenates them into a single vector. This descriptor captures the overall color distribution of the region.

**Inputs:**

| Parameter | Type | Constraints | Description |
|---|---|---|---|
| `surface` | `pygame.Surface` | RGB/RGBA | Source surface |
| `bins` | `int` | `[4, 256]` | Number of histogram bins per channel |

**Outputs:** `np.ndarray` of shape `(bins * 3,)` — normalized (sum per channel = 1.0).

**Dependencies:** `numpy`

---

## 14. Bounding Boxes and Contours

### 14.1 `VisionTools.find_contours(mask_surface)`

**Purpose:** Find the boundaries of all foreground regions in a binary mask. Returns the contours as a list of NumPy arrays, where each array contains the (x, y) pixel coordinates of the contour points of one region.

**Inputs:**

| Parameter | Type | Description |
|---|---|---|
| `mask_surface` | `pygame.Surface` | Binary mask surface |

**Outputs:** `list[np.ndarray]` — each element is an array of shape `(N, 1, 2)` in OpenCV contour format, representing the (x, y) coordinates of contour points.

**Dependencies:** `opencv-python` (`cv2.findContours`)

**Usage Example:**

```python
mask = VisionTools.threshold_binary(self.terrain_surface, 120)
contours = VisionTools.find_contours(mask)

# Draw all contours on the surface:
for contour in contours:
    for point in contour:
        x, y = point[0]
        pygame.draw.circle(surface, (255, 255, 0), (x, y), 1)
```

---

### 14.2 `VisionTools.bounding_boxes_from_mask(mask_surface)`

**Purpose:** Extract a list of `pygame.Rect` bounding boxes, one per connected foreground region in the mask. This converts the geometric output of segmentation directly into Pygame-compatible collision/render rectangles.

**Inputs:**

| Parameter | Type | Description |
|---|---|---|
| `mask_surface` | `pygame.Surface` | Binary mask surface |

**Outputs:** `list[pygame.Rect]`, one per foreground region. Rects are in pixel coordinates matching the mask_surface dimensions.

**Dependencies:** `numpy`, `opencv-python`

**Usage Example:**

```python
mask = VisionTools.threshold_binary(screen_copy, 150)
boxes = VisionTools.bounding_boxes_from_mask(mask)

# Draw debug boxes:
for rect in boxes:
    pygame.draw.rect(surface, (0, 255, 0), rect, 1)

# Use as trigger zones:
for box in boxes:
    if box.colliderect(player.rect):
        EventBus.emit("SHOW_MESSAGE", text="Region contact!", duration=1.0)
```

---

## 15. Image Validation

### `_validate_surface(surface)` — Internal

| Check | Exception |
|---|---|
| `None` input | `TypeError("VisionTools: surface cannot be None")` |
| Not `pygame.Surface` | `TypeError(f"VisionTools: expected pygame.Surface, got {type(surface)}")` |
| Zero dimensions | `ValueError("VisionTools: surface has zero dimensions")` |

### `_validate_mask(surface)` — Internal

Additional check for methods requiring a binary mask:

| Check | Action |
|---|---|
| Pixel values not in {0, 255} | Warning logged; operation continues (non-binary input is processed but results may be unexpected) |

---

## 16. Performance Constraints

| Operation | 320×224 Surface | Recommendation |
|---|---|---|
| `threshold_binary` | < 0.5ms | Safe every frame |
| `threshold_otsu` | < 1ms | Safe every frame |
| `morphological_erode/dilate` (k=3) | < 0.5ms | Safe every frame |
| `morphological_open/close` (k=3) | < 1ms | Safe every frame |
| `connected_components` | ~1.5ms | Every 3 frames |
| `analyze_regions` | ~2ms | Every 5 frames |
| `watershed_segment` | ~12ms | Every 15 frames or pre-compute |
| `extract_hog` (32×32 canonical) | < 1ms | Safe every frame |
| `extract_lbp` (32×32 canonical) | < 0.5ms | Safe every frame |
| `find_contours` | < 1ms | Every 3 frames |
| `bounding_boxes_from_mask` | < 0.5ms | Safe every frame |

---

## 17. Unit VIII Mapping

| Unit VIII Topic | VisionTools Method | Observable In-Game |
|---|---|---|
| Binary Threshold | `threshold_binary()` | Binary mask drives entity spawn or trigger zones |
| Otsu's Method | `threshold_otsu()` | Adaptive threshold — student logs computed value |
| Morphological Erosion | `morphological_erode()` | Noise removal from mask |
| Morphological Dilation | `morphological_dilate()` | Gap filling in mask |
| Opening | `morphological_open()` | Artifact removal |
| Closing | `morphological_close()` | Hole filling |
| Connected Components | `connected_components()` | Label and count distinct regions |
| Region Analysis | `analyze_regions()` | Centroid, area, shape metrics per region |
| Watershed | `watershed_segment()` | Multi-region color-coded overlay |
| Feature Extraction | `extract_features()` | Feature vector ready for classification |

---

## 18. Assessment Mapping

| Assessment | Unit | Required VisionTools Usage | Evidence |
|---|---|---|---|
| Practical Exam II | VIII | Student applies threshold + morphology + region analysis | Running demo + README |
| Stage 2 Deliverable | VIII | At least one segmentation result drives game behavior | Code review + oral |
| Stage 3 Deliverable | VIII+IX | Feature extraction feeds classifier | Pipeline demonstrated live |
| Final Presentation | VIII | Student explains Otsu's method mathematically | Oral + demo |

---

## 19. Professor Deliverables

1. **`framework/processing/vision_tools.py`** — Complete, documented, tested implementation.
2. **`tests/test_vision_tools.py`** — Unit tests with visual PNG output to `tests/output/vision/`.
3. **Demo Scene (see Document 15)** — Interactive Unit VIII demo where students adjust threshold sliders and observe segmentation output in real time.
4. **Pipeline walkthrough** — A commented Stage 0 sub-scene where the full pipeline (filter → threshold → morphology → region analysis) is demonstrated step by step.

---

## 20. Student Reuse

Students call `VisionTools` methods to:

1. Segment regions of their stage's visual content.
2. Count or locate regions to determine where entities should spawn or where events should trigger.
3. Extract feature vectors for classification in Unit IX pipelines.
4. Display segmentation overlays for debug or academic visualization.

Students produce **no segmentation algorithms**. They produce **game logic driven by segmentation results**.

---

## 21. Learning Evidence

A student has demonstrated Unit VIII learning when they can:

1. **Explain** why they chose a specific threshold value (or why Otsu's method was appropriate).
2. **Predict** what morphological operation will do to their mask before running it.
3. **Show** a `RegionInfo` object in their README with the area, centroid, and bounding rect of a region in their stage.
4. **Demonstrate** game behavior that is different in two different stage states because the segmentation result changed.
5. **Document** the feature vector dimensionality and what each group of values represents.

---

## 22. Restrictions

| Restriction | Scope |
|---|---|
| Students never import `cv2`, `scipy`, `skimage` | All student files |
| Students never call `cv2.threshold()`, `cv2.connectedComponents()`, `skimage.feature.hog()` directly | All student files |
| `VisionTools` never calls `EventBus`, `InputManager`, `AudioManager` | Processing isolation |
| `VisionTools` never modifies entity state | Return-value-based interface |
| Watershed is not used every frame without throttling | Performance constraint |

---

## 23. Future Extensions

| Extension | Description | Target Unit |
|---|---|---|
| `optical_flow(surface_a, surface_b)` | Dense optical flow between frames | Unit IX |
| `skeleton(mask_surface)` | Morphological skeletonization | Unit VIII |
| `convex_hull(mask_surface)` | Convex hull of foreground regions | Unit VIII |
| `texture_segmentation(surface, method)` | LBP-based texture-driven segmentation | Unit VIII |
| `depth_from_stereo(left, right)` | Stereo disparity map | Beyond course scope |


--- Traducción al Español ---

## Especificación de VisionTools

VisionTools proporciona utilidades de segmentación de imágenes y reconocimiento de patrones para las Unidades VIII y IX.

### Funciones
- `threshold_binary(surface, thresh)` — Umbral binario
- `threshold_otsu(surface)` — Umbral automático de Otsu
- `morphological_erode(surface, kernel_size)` — Erosión morfológica
- `morphological_dilate(surface, kernel_size)` — Dilatación morfológica
- `watershed_segment(surface)` — Segmentación Watershed
- `extract_features(surface)` — Extracción de características HOG o LBP
- `classify_region(features, model)` — Clasificación con modelo scikit-learn

Para ejemplos detallados y parámetros, consultar el documento original en inglés.


---
## 🔗 Documentos Relacionados

- [[11_FILTER_TOOLS_SPEC.md|Filter Tools Spec]]
- [[13_PATTERN_RECOGNITION_SPEC.md|Pattern Recognition Spec]]
