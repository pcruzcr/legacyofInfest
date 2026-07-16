---
document_id: "LOI-FILTER-011"
title: "Legacy of InFest — Filter Tools Specification"
aliases: ["Filter Tools Spec"]
tags: ["filter", "processing", "image"]
description: "Unit VII image processing subsystem"
source: "docs/11_FILTER_TOOLS_SPEC.md"
date_processed: "2026-07-14"
---

# Legacy of InFest — Filter Tools Specification

**Document ID:** LOI-FILTER-011  
**Version:** 1.0.0  
**Status:** Official  
**Compatibility:** Requires documents LOI-ARCH-003, LOI-LIBS-010  
**Audience:** Professor, Teaching Assistants, AI coding assistants (Claude Code, Cline, OpenCode, Codex)

---

## 1. Overview

`FilterTools` is the image processing subsystem of the Legacy of InFest academic framework. It encapsulates all digital image processing operations taught in **Unit VII** of the course syllabus: histogram analysis, brightness and contrast adjustment, convolution, Gaussian blur, Sobel edge detection, and Canny edge detection.

This subsystem is entirely professor-owned and professor-maintained. Students interact with it exclusively through its public API. Students never import `scipy`, `opencv-python`, or `scikit-image` directly. All third-party library complexity is hidden behind the `FilterTools` interface.

The module is located at:

```
framework/processing/filter_tools.py
```

---

## 2. Academic Purpose

`FilterTools` exists to make Unit VII concepts **executable and observable** within the running game environment. Instead of processing abstract images in a notebook, students apply these operations to live game surfaces — backgrounds, sprites, screen regions — and observe the results in real time.

### 2.1 Learning Objectives Supported

| Objective | FilterTools Mechanism |
|---|---|
| Understand histograms as frequency distributions of pixel intensities | `compute_histogram()` returns per-channel frequency arrays |
| Apply brightness manipulation as a scalar transformation | `adjust_brightness()` scales pixel values uniformly |
| Apply contrast stretching via histogram manipulation | `adjust_contrast()` expands/compresses intensity range |
| Implement convolution as a kernel-surface operation | `apply_kernel()` applies an arbitrary kernel matrix |
| Understand Gaussian blur as a separable convolution | `gaussian_blur()` uses a parameterized sigma value |
| Detect edges using gradient magnitude | `sobel_edge()` returns a gradient magnitude surface |
| Apply multi-stage edge detection | `canny_edge()` applies the full Canny pipeline |

### 2.2 Design Principle

All functions in `FilterTools` are **pure functions**: they receive a `pygame.Surface` and parameters, and return a new `pygame.Surface`. They do not hold state, do not modify the input surface, and do not emit events or call any engine system. This makes them safe to use in any context and easy to test in isolation.

---

## 3. Framework Location

```
framework/
└── processing/
    └── filter_tools.py          ← This module
```

### 3.1 Position in the Dependency Hierarchy

```
Stages (student code)
    ↓
framework/processing/filter_tools.py   ← Students call this
    ↓
numpy, scipy, opencv-python            ← FilterTools calls these
    ↓
(Hardware / OS)
```

Students are positioned **above** `filter_tools.py`. They call it. They never reach past it.

---

## 4. Architecture Integration

### 4.1 How FilterTools Connects to the Framework

`FilterTools` is a stateless utility module. It integrates with the framework through the following touchpoints:

| Integration Point | Description |
|---|---|
| `framework/processing/color_tools.py` | `ColorTools.surface_to_array()` and `array_to_surface()` are used internally to bridge Pygame surfaces and NumPy arrays |
| Stage scenes (student code) | Students call `FilterTools` methods from their stage `update()` or `draw()` loops |
| `engine/utils/asset_loader.py` | Loaded surfaces may be passed to `FilterTools` for pre-processing during stage initialization |
| Unit test suite (`tests/test_filter_tools.py`) | Each method has an isolated unit test that saves visual output as PNG for academic verification |

### 4.2 What FilterTools Does NOT Do

| Forbidden Action | Reason |
|---|---|
| Does not call `EventBus` | It is a pure computation module |
| Does not call `InputManager` | No interaction logic |
| Does not call `AudioManager` | No audio coupling |
| Does not access the scene manager | No scene knowledge |
| Does not read TMX data | No map coupling |
| Does not modify input surfaces in place | All operations return new surfaces |

---

## 5. Dependencies

| Library | Import | Used For |
|---|---|---|
| `numpy` | `import numpy as np` | Array representation of pixel data, vectorized operations |
| `scipy.ndimage` | `from scipy.ndimage import convolve, gaussian_filter` | Convolution and Gaussian blur |
| `cv2` (opencv-python) | `import cv2` | Sobel, Canny, color space operations |
| `pygame` | `import pygame` | Surface input/output, `surfarray` bridge |

**Students never import any of the above.** All imports live inside `filter_tools.py`.

---

## 6. Class Diagram

```
FilterTools
│
├── [Histogram]
│   ├── compute_histogram(surface) → dict
│   └── histogram_equalize(surface) → Surface
│
├── [Brightness]
│   └── adjust_brightness(surface, factor) → Surface
│
├── [Contrast]
│   ├── adjust_contrast(surface, factor) → Surface
│   └── stretch_contrast(surface) → Surface
│
├── [Convolution]
│   ├── apply_kernel(surface, kernel) → Surface
│   └── get_standard_kernel(name) → np.ndarray
│
├── [Gaussian Blur]
│   └── gaussian_blur(surface, sigma) → Surface
│
├── [Edge Detection]
│   ├── sobel_edge(surface) → Surface
│   └── canny_edge(surface, low_threshold, high_threshold) → Surface
│
└── [Internal Utilities — private]
    ├── _surface_to_float_array(surface) → np.ndarray
    ├── _float_array_to_surface(array) → Surface
    ├── _to_opencv(surface) → np.ndarray
    ├── _from_opencv(array) → Surface
    └── _validate_surface(surface) → None
```

All public methods are **class methods** (decorated with `@classmethod`). `FilterTools` is never instantiated. It is a namespace of operations.

---

## 7. FilterTools Class

### 7.1 Responsibilities

`FilterTools` is responsible for:

1. Accepting `pygame.Surface` objects as input.
2. Converting surfaces to the appropriate NumPy array format for the operation.
3. Applying the mathematical operation using the appropriate library.
4. Converting the result back to a `pygame.Surface`.
5. Returning the new surface to the caller.
6. Validating all inputs and raising descriptive exceptions on misuse.

`FilterTools` is **not** responsible for:

- Deciding when to apply filters (that is the stage's responsibility)
- Caching processed surfaces (that is the `AssetLoader`'s responsibility)
- Scheduling filter updates at reduced frame rates (that is the stage's responsibility)

---

## 8. Public API

### 8.1 Histogram Operations

#### `FilterTools.compute_histogram(surface)`

**Purpose:** Compute the per-channel frequency histogram of a surface's pixel intensities. Returns the distribution of R, G, B (and optionally A) values across all pixels. Used to analyze the tonal character of an image — a fundamental Unit VII diagnostic tool.

**Inputs:**

| Parameter | Type | Description |
|---|---|---|
| `surface` | `pygame.Surface` | The source surface. Any size. RGB or RGBA. |

**Outputs:**

| Key | Type | Shape | Description |
|---|---|---|---|
| `'r'` | `np.ndarray` | `(256,)` | Frequency count per intensity level for Red channel |
| `'g'` | `np.ndarray` | `(256,)` | Frequency count per intensity level for Green channel |
| `'b'` | `np.ndarray` | `(256,)` | Frequency count per intensity level for Blue channel |
| `'luminance'` | `np.ndarray` | `(256,)` | Frequency count per intensity for grayscale luminance |
| `'total_pixels'` | `int` | scalar | Total pixel count (width × height) |

Returns a `dict` with the above keys.

**Restrictions:**

- Input surface must be at least 1×1 pixel.
- Surface must be convertible to RGB or RGBA format.
- This function does not modify the input surface.

**Dependencies:** `numpy`, `pygame.surfarray`

**Usage Example:**

```python
# In a student stage — compute histogram of a background layer:
from framework.processing.filter_tools import FilterTools

hist = FilterTools.compute_histogram(self.background_surface)

# Check average luminance:
avg_luminance = sum(i * hist['luminance'][i] for i in range(256)) / hist['total_pixels']

if avg_luminance < 80:
    EventBus.emit("SHOW_MESSAGE", text="The scene is very dark.", duration=2.0)
```

---

#### `FilterTools.histogram_equalize(surface)`

**Purpose:** Apply histogram equalization to improve contrast by redistributing pixel intensities to span the full 0–255 range uniformly. Demonstrates the relationship between histogram shape and perceived image quality.

**Inputs:**

| Parameter | Type | Description |
|---|---|---|
| `surface` | `pygame.Surface` | Source surface. RGB or RGBA. |

**Outputs:** A new `pygame.Surface` of the same size with equalized luminance. Color channels are equalized independently to preserve hue relationships (per-channel equalization).

**Restrictions:**

- Applied to grayscale or color surfaces.
- Does not modify input surface.
- Computationally expensive on large surfaces — use on sub-surfaces or at reduced frequency.

**Dependencies:** `numpy`, `opencv-python` (`cv2.equalizeHist`)

**Usage Example:**

```python
# Pre-process a dark background tile during stage initialization:
equalized_bg = FilterTools.histogram_equalize(raw_background_surface)
self.background_surface = equalized_bg
```

---

### 8.2 Brightness Operations

#### `FilterTools.adjust_brightness(surface, factor)`

**Purpose:** Multiply all pixel channel values by `factor`. A value of `1.0` is identity. Values above `1.0` brighten. Values below `1.0` darken. Values at `0.0` produce black. This operation models the scalar multiplication of pixel vectors — a Unit VII concept.

**Inputs:**

| Parameter | Type | Constraints | Description |
|---|---|---|---|
| `surface` | `pygame.Surface` | Any size, RGB/RGBA | Source surface |
| `factor` | `float` | `[0.0, 4.0]` | Brightness multiplier |

**Outputs:** New `pygame.Surface` of identical size. Pixel values clamped to `[0, 255]`.

**Restrictions:**

- `factor` outside `[0.0, 4.0]` raises `ValueError`.
- Alpha channel is preserved unmodified if surface has alpha.
- Does not modify input surface.

**Dependencies:** `numpy`, `pygame.surfarray`

**Internal Implementation Note (for AI assistants):**

```
arr = surfarray.array3d(surface).astype(float32)
arr = clip(arr * factor, 0, 255).astype(uint8)
result = surfarray.make_surface(arr)
if surface has alpha:
    result.set_alpha(surface.get_alpha())
return result
```

**Usage Example:**

```python
# Health-based screen darkening in a student stage:
health_ratio = player.current_health / 5.0
dimmed = FilterTools.adjust_brightness(self.internal_surface_copy, factor=health_ratio)
surface.blit(dimmed, (0, 0))
```

---

### 8.3 Contrast Operations

#### `FilterTools.adjust_contrast(surface, factor)`

**Purpose:** Apply linear contrast scaling around the midpoint (128). A `factor` of `1.0` is identity. Values above `1.0` increase contrast (push darks darker, lights lighter). Values below `1.0` reduce contrast (flatten toward gray). Models the affine pixel transformation: `out = (in - 128) * factor + 128`.

**Inputs:**

| Parameter | Type | Constraints | Description |
|---|---|---|---|
| `surface` | `pygame.Surface` | Any size, RGB/RGBA | Source surface |
| `factor` | `float` | `[0.0, 4.0]` | Contrast multiplier |

**Outputs:** New `pygame.Surface` of identical size. Values clamped to `[0, 255]`.

**Restrictions:**

- `factor` outside `[0.0, 4.0]` raises `ValueError`.
- Alpha preserved if present.
- Does not modify input.

**Dependencies:** `numpy`, `pygame.surfarray`

**Usage Example:**

```python
# High-contrast visual mode triggered by a stage event:
high_contrast_bg = FilterTools.adjust_contrast(self.background_surface, factor=2.5)
surface.blit(high_contrast_bg, camera_offset)
```

---

#### `FilterTools.stretch_contrast(surface)`

**Purpose:** Perform min-max contrast stretching. Finds the actual minimum and maximum pixel values in the surface and linearly remaps them to 0 and 255. Unlike `adjust_contrast()`, this is adaptive — it analyzes the surface before transforming it.

**Inputs:**

| Parameter | Type | Description |
|---|---|---|
| `surface` | `pygame.Surface` | Any size, RGB/RGBA |

**Outputs:** New `pygame.Surface` with full-range contrast. Each channel is stretched independently.

**Restrictions:**

- If min == max (uniform surface), returns the input surface unchanged and logs a warning.
- Does not modify input.

**Dependencies:** `numpy`, `pygame.surfarray`

**Usage Example:**

```python
# Stretch a low-contrast sprite sheet for visual clarity in debug mode:
stretched = FilterTools.stretch_contrast(sprite_surface)
```

---

### 8.4 Convolution Operations

#### `FilterTools.apply_kernel(surface, kernel)`

**Purpose:** Apply an arbitrary convolution kernel to the surface. This is the generalized form of all linear spatial filters. The kernel is a 2D NumPy array (square, odd-sized). The operation is the discrete 2D convolution:

```
output(x, y) = Σ Σ kernel(i, j) * input(x+i, y+j)
```

Applied independently to each RGB channel.

**Inputs:**

| Parameter | Type | Constraints | Description |
|---|---|---|---|
| `surface` | `pygame.Surface` | Any size, RGB/RGBA | Source surface |
| `kernel` | `np.ndarray` | Shape `(n, n)`, `n` odd, `n ≥ 3` | Convolution kernel |

**Outputs:** New `pygame.Surface` of identical size. Values clamped to `[0, 255]`.

**Restrictions:**

- Kernel must be square: `kernel.shape[0] == kernel.shape[1]`.
- Kernel dimensions must be odd: `kernel.shape[0] % 2 == 1`.
- Minimum kernel size: 3×3. Maximum kernel size: 15×15 (performance constraint).
- Kernel values are not required to sum to 1 (unnormalized kernels are valid for edge detection).
- Border handling: `mode='reflect'` (reflects pixels at edges).
- Raises `ValueError` if kernel shape is invalid.

**Dependencies:** `numpy`, `scipy.ndimage.convolve`

**Usage Example:**

```python
import numpy as np
from framework.processing.filter_tools import FilterTools

# Sharpen kernel (Unit VII — custom convolution):
sharpen_kernel = np.array([
    [ 0, -1,  0],
    [-1,  5, -1],
    [ 0, -1,  0]
], dtype=np.float32)

sharpened = FilterTools.apply_kernel(self.background_surface, sharpen_kernel)
```

---

#### `FilterTools.get_standard_kernel(name)`

**Purpose:** Return a pre-defined, academically standard convolution kernel by name. Provides students with correct kernel definitions without requiring them to construct them manually. Covers all kernels discussed in Unit VII.

**Inputs:**

| Parameter | Type | Description |
|---|---|---|
| `name` | `str` | Kernel identifier (see table below) |

**Available Kernels:**

| Name | Size | Description | Academic Topic |
|---|---|---|---|
| `'identity'` | 3×3 | No-op kernel | Baseline for comparison |
| `'sharpen'` | 3×3 | Laplacian-based sharpening | Convolution |
| `'box_blur'` | 3×3 | Uniform average blur | Convolution |
| `'box_blur_5'` | 5×5 | Larger uniform blur | Convolution |
| `'edge_laplacian'` | 3×3 | Laplacian edge detection | Edge detection |
| `'emboss'` | 3×3 | Emboss effect | Convolution |
| `'ridge'` | 3×3 | Ridge/valley detection | Edge detection |
| `'sobel_x'` | 3×3 | Sobel horizontal gradient | Sobel |
| `'sobel_y'` | 3×3 | Sobel vertical gradient | Sobel |

**Outputs:** `np.ndarray` of the appropriate shape and dtype `float32`.

**Restrictions:**

- Raises `KeyError` with a list of valid names if `name` is unrecognized.

**Dependencies:** `numpy`

**Usage Example:**

```python
kernel = FilterTools.get_standard_kernel('sharpen')
sharpened = FilterTools.apply_kernel(background, kernel)
```

---

### 8.5 Gaussian Blur

#### `FilterTools.gaussian_blur(surface, sigma)`

**Purpose:** Apply Gaussian blur to a surface. The blur is implemented as a separable convolution with a Gaussian kernel parameterized by `sigma` (standard deviation). Higher `sigma` values produce stronger blur. This demonstrates the Gaussian function as a spatial weighting kernel and its separability property.

**Mathematical definition:**

```
G(x, y) = (1 / 2πσ²) * exp(-(x² + y²) / 2σ²)
```

**Inputs:**

| Parameter | Type | Constraints | Description |
|---|---|---|---|
| `surface` | `pygame.Surface` | Any size, RGB/RGBA | Source surface |
| `sigma` | `float` | `(0.0, 10.0]` | Standard deviation of the Gaussian |

**Outputs:** New `pygame.Surface` of identical size, blurred according to the Gaussian kernel.

**Restrictions:**

- `sigma ≤ 0.0` raises `ValueError`.
- `sigma > 10.0` raises `ValueError` (performance guard — for strong blur, apply iteratively).
- Border handling: `mode='reflect'`.
- Alpha channel preserved if present.
- Applied to each RGB channel independently.

**Dependencies:** `numpy`, `scipy.ndimage.gaussian_filter`

**Performance Note:** For `sigma > 3.0`, the effective kernel radius is large. On surfaces larger than 320×224 pixels, this can exceed the 2ms frame budget for real-time use. Apply to sub-surfaces or at reduced frequency.

**Usage Example:**

```python
# Apply blur to a background layer to simulate depth of field:
blurred_far_bg = FilterTools.gaussian_blur(self.far_background, sigma=1.8)
surface.blit(blurred_far_bg, far_bg_offset)
```

---

### 8.6 Edge Detection

#### `FilterTools.sobel_edge(surface)`

**Purpose:** Apply the Sobel operator to detect edges by computing the gradient magnitude at each pixel. The gradient in X and Y directions are computed separately using the Sobel kernels, then combined as the Euclidean magnitude. Returns a **grayscale** surface where bright pixels represent strong edges.

**Mathematical definition:**

```
Gx = sobel_x_kernel ⊗ I
Gy = sobel_y_kernel ⊗ I
|G| = sqrt(Gx² + Gy²)
```

**Inputs:**

| Parameter | Type | Description |
|---|---|---|
| `surface` | `pygame.Surface` | Source surface. RGB or RGBA. |

**Outputs:** New `pygame.Surface` of identical size. **Grayscale** (all three channels equal). White = strong edge. Black = no edge. Alpha is not preserved (output is always RGB).

**Restrictions:**

- Input is converted to grayscale internally before applying Sobel. Color information is discarded for the computation.
- Output is always an RGB surface (no alpha), suitable for blending over the scene.
- Does not modify input.

**Dependencies:** `numpy`, `opencv-python` (`cv2.Sobel`, `cv2.convertScaleAbs`)

**Usage Example:**

```python
# Render an edge-detection overlay on the terrain layer:
edge_map = FilterTools.sobel_edge(self.terrain_surface)
edge_map.set_alpha(140)  # Semi-transparent overlay
surface.blit(edge_map, camera_offset)
```

---

#### `FilterTools.canny_edge(surface, low_threshold, high_threshold)`

**Purpose:** Apply the Canny multi-stage edge detection algorithm. Canny uses Gaussian smoothing, Sobel gradients, non-maximum suppression, and double thresholding with hysteresis to produce clean, thin edges. Returns a binary (black and white) surface.

**The Canny pipeline (internal):**

```
1. Convert to grayscale
2. Apply Gaussian blur (sigma ≈ 1.4 — internal, fixed)
3. Compute Sobel gradients (Gx, Gy)
4. Non-maximum suppression along gradient direction
5. Double threshold: pixels above high_threshold → strong edge
                     pixels between low and high → weak edge (kept if connected to strong)
                     pixels below low_threshold → rejected
6. Edge tracking by hysteresis
```

**Inputs:**

| Parameter | Type | Constraints | Description |
|---|---|---|---|
| `surface` | `pygame.Surface` | RGB/RGBA, any size | Source surface |
| `low_threshold` | `int` | `[1, 254]`, `< high_threshold` | Lower hysteresis threshold |
| `high_threshold` | `int` | `[2, 255]`, `> low_threshold` | Upper hysteresis threshold |

**Recommended threshold pairs:**

| Effect | Low | High |
|---|---|---|
| Very sensitive (many edges) | 20 | 60 |
| Balanced (default) | 50 | 150 |
| Strict (strong edges only) | 100 | 200 |

**Outputs:** New `pygame.Surface` of identical size. **Binary grayscale**: pixels are either white (edge) or black (no edge). Alpha not preserved.

**Restrictions:**

- `low_threshold >= high_threshold` raises `ValueError`.
- Both thresholds must be in range `[1, 255]`.
- Input is converted to grayscale internally.
- Output is RGB (not RGBA).

**Dependencies:** `numpy`, `opencv-python` (`cv2.Canny`)

**Usage Example:**

```python
# Canny edge detection applied to an enemy sprite region:
enemy_region = self.stage_surface.subsurface(enemy.rect)
edges = FilterTools.canny_edge(enemy_region, low_threshold=50, high_threshold=150)
edges.set_alpha(180)
surface.blit(edges, enemy.rect.topleft)
```

---

## 9. Kernel Standards

All kernels in Legacy of InFest follow these standards:

### 9.1 Format

| Property | Standard |
|---|---|
| Data type | `np.float32` |
| Shape | Square: `(n, n)` |
| Dimension | Odd: `n ∈ {3, 5, 7, 9, 11, 13, 15}` |
| Normalization | Optional. Normalized kernels (sum = 1.0) for blur. Unnormalized for detection. |
| Orientation | Row-major NumPy convention |

### 9.2 Standard Kernel Definitions

**Identity (3×3):**
```
[[0, 0, 0],
 [0, 1, 0],
 [0, 0, 0]]
```

**Box Blur (3×3):**
```
[[1/9, 1/9, 1/9],
 [1/9, 1/9, 1/9],
 [1/9, 1/9, 1/9]]
```

**Sharpen (3×3):**
```
[[ 0, -1,  0],
 [-1,  5, -1],
 [ 0, -1,  0]]
```

**Sobel X (3×3):**
```
[[-1,  0,  1],
 [-2,  0,  2],
 [-1,  0,  1]]
```

**Sobel Y (3×3):**
```
[[-1, -2, -1],
 [ 0,  0,  0],
 [ 1,  2,  1]]
```

**Laplacian Edge (3×3):**
```
[[ 0,  1,  0],
 [ 1, -4,  1],
 [ 0,  1,  0]]
```

---

## 10. Image Format Standards

### 10.1 Input Surface Requirements

| Property | Required Value |
|---|---|
| Format | `pygame.Surface` |
| Pixel mode | RGB (24-bit) or RGBA (32-bit) |
| Minimum size | 1×1 pixel |
| Maximum size | 1920×1080 (performance ceiling) |
| Color depth | 8 bits per channel |

### 10.2 Internal Array Format

| Stage | Format | Shape |
|---|---|---|
| Pygame surface | `pygame.Surface` | — |
| surfarray extraction | `np.ndarray`, `uint8` | `(W, H, 3)` |
| Transposed for OpenCV | `np.ndarray`, `uint8` | `(H, W, 3)` |
| Float computation | `np.ndarray`, `float32` | `(H, W, 3)` or `(H, W)` |
| Result clip and cast | `np.ndarray`, `uint8` | `(W, H, 3)` |
| surfarray reconstruct | `pygame.Surface` | — |

**The axis transposition between Pygame and OpenCV is mandatory and always applied inside `FilterTools`.** Students never encounter this complexity.

### 10.3 Output Surface Guarantee

All `FilterTools` methods guarantee:

- Output surface has the **same dimensions** as the input surface.
- Output surface is a **new object** — it does not share memory with the input.
- Output pixel depth is **24-bit RGB** unless otherwise documented (e.g., edge detection always returns RGB).

---

## 11. Input Validation

All public methods call `_validate_surface(surface)` before processing:

### `_validate_surface(surface)` — Internal

| Check | Exception Raised |
|---|---|
| `surface` is `None` | `TypeError("Surface cannot be None")` |
| `surface` is not `pygame.Surface` | `TypeError(f"Expected pygame.Surface, got {type(surface)}")` |
| Surface size is `(0, 0)` | `ValueError("Surface has zero dimensions")` |
| Surface not locked (during surfarray ops) | Managed internally — surface is never left locked |

Parameter-specific validation:

| Method | Parameter | Validation |
|---|---|---|
| `adjust_brightness` | `factor` | `0.0 ≤ factor ≤ 4.0` |
| `adjust_contrast` | `factor` | `0.0 ≤ factor ≤ 4.0` |
| `apply_kernel` | `kernel` | Square, odd, 3–15 |
| `gaussian_blur` | `sigma` | `0.0 < sigma ≤ 10.0` |
| `canny_edge` | thresholds | `1 ≤ low < high ≤ 255` |

---

## 12. Error Handling

`FilterTools` raises descriptive exceptions. It never returns `None` silently. It never logs and continues on bad input.

| Exception | When Raised | Message Pattern |
|---|---|---|
| `TypeError` | Wrong argument type | `"FilterTools.{method}: expected {type}, got {actual_type}"` |
| `ValueError` | Out-of-range parameter | `"FilterTools.{method}: {param} must be in [{min}, {max}], got {value}"` |
| `KeyError` | Unknown kernel name in `get_standard_kernel` | `"Unknown kernel '{name}'. Valid names: {list}"` |
| `RuntimeError` | Internal processing failure (e.g., OpenCV error) | `"FilterTools.{method}: processing failed — {cv2_error_message}"` |

Students who receive a `FilterTools` exception can immediately identify what they passed incorrectly. The exception message always includes the method name and the invalid value.

---

## 13. Performance Constraints

### 13.1 Time Budget

The full game loop frame budget at 60 FPS is **16.67ms**. Filter operations consume a portion of this budget.

| Operation | Typical Time (320×224 surface) | Recommendation |
|---|---|---|
| `compute_histogram` | < 0.5ms | Safe every frame |
| `adjust_brightness` | < 0.5ms | Safe every frame |
| `adjust_contrast` | < 0.5ms | Safe every frame |
| `stretch_contrast` | < 1.0ms | Safe every frame |
| `apply_kernel` (3×3) | < 1.5ms | Safe every frame |
| `apply_kernel` (7×7) | ~3ms | Every 3 frames |
| `apply_kernel` (15×15) | ~8ms | Every 10 frames or pre-compute |
| `gaussian_blur` (σ=1.0) | < 1ms | Safe every frame |
| `gaussian_blur` (σ=3.0) | ~2.5ms | Every 3 frames |
| `gaussian_blur` (σ=5.0) | ~5ms | Every 8 frames or pre-compute |
| `sobel_edge` | ~2ms | Every 3 frames |
| `canny_edge` | ~3ms | Every 5 frames |

### 13.2 Sub-Surface Strategy

Students are expected to apply expensive filters to **sub-surfaces** rather than the full screen. A sub-surface is created with `pygame.Surface.subsurface(rect)`.

```
# Instead of:
filtered = FilterTools.canny_edge(full_320x224_surface, 50, 150)  # ~3ms

# Prefer:
region = full_surface.subsurface(pygame.Rect(0, 0, 160, 112))     # Quarter surface
filtered_region = FilterTools.canny_edge(region, 50, 150)         # ~0.8ms
```

### 13.3 Frame-Throttled Updates

For expensive operations that don't need per-frame precision, students use a frame counter:

```
# Concept — update filter result every 5 frames:
if self.frame_count % 5 == 0:
    self.cached_edge_map = FilterTools.sobel_edge(self.background_surface)
self.frame_count += 1
surface.blit(self.cached_edge_map, (0, 0))
```

---

## 14. Unit VII Mapping

| Unit VII Topic | FilterTools Method | Observable In-Game |
|---|---|---|
| Histogram | `compute_histogram()` | Numeric output drives game logic |
| Histogram Equalization | `histogram_equalize()` | Visual quality improvement on dark surfaces |
| Brightness | `adjust_brightness()` | Screen dims/brightens based on health or time |
| Contrast | `adjust_contrast()` | High/low contrast visual mode |
| Contrast Stretching | `stretch_contrast()` | Low-contrast sprite made visually clear |
| Convolution | `apply_kernel()` | Custom kernel applied to background |
| Gaussian Blur | `gaussian_blur()` | Background blur simulating depth or fog |
| Sobel | `sobel_edge()` | Edge overlay rendered on terrain or enemies |
| Canny | `canny_edge()` | Binary edge map driving a visual effect |

---

## 15. Assessment Mapping

| Assessment | Unit | Required FilterTools Usage | Evidence |
|---|---|---|---|
| Practical Exam I | VII | Student applies at least 2 distinct filter operations in their stage | Running stage demo + README |
| Stage 1 Deliverable | VII | At least one filter changes game behavior (not just visual) | README + code review |
| Stage 2 Deliverable | VII | Filter pipeline with at least one kernel-based operation | Demo + explanation |
| Final Presentation | VII | Student explains the mathematical basis of one filter live | Oral explanation |

---

## 16. Professor Deliverables

The professor delivers the following as part of `FilterTools`:

1. **`framework/processing/filter_tools.py`** — Complete, documented, tested implementation.
2. **`tests/test_filter_tools.py`** — Unit test suite. Each test saves a PNG output file to `tests/output/filter/` for visual verification.
3. **Stage 0 Zone F** — Demonstrates `adjust_brightness`, `gaussian_blur`, and `sobel_edge` in a running stage context.
4. **Demo Scene (see Document 15)** — An interactive scene where students can adjust filter parameters in real time using keyboard controls.
5. **Kernel reference card** — A one-page PDF showing all standard kernels with their visual effect on a reference image.

---

## 17. Student Reuse

Students inherit the complete `FilterTools` API. They reuse it by:

1. Importing `FilterTools` from `framework.processing.filter_tools`.
2. Passing `pygame.Surface` objects (their backgrounds, sprites, or screen regions) to `FilterTools` methods.
3. Using the returned surface as a visual overlay, replacement, or input to further processing.
4. Using `compute_histogram()` output to make game logic decisions.

Students write **zero image processing code**. They write game logic that uses image processing results.

---

## 18. Learning Evidence

A student has demonstrated Unit VII learning when they can:

1. **Explain** the convolution operation in their own words, using their stage's kernel as an example.
2. **Predict** what their filter will do to a given surface before running it.
3. **Justify** the kernel values they chose for their effect.
4. **Show** in their running stage where the filter result changes observable game behavior.
5. **Describe** why they applied the filter at the frequency they chose (every frame, every N frames, pre-computed).

---

## 19. Restrictions

| Restriction | Scope |
|---|---|
| Students never import `scipy`, `cv2`, `skimage`, or `numpy` | All student stage files |
| Students never call `pygame.surfarray` directly | All student stage files |
| Students never call `cv2.Canny()`, `cv2.Sobel()`, or `scipy.ndimage.convolve()` directly | All student stage files |
| `FilterTools` methods are never called from `engine/` | Engine does not depend on framework |
| `FilterTools` never calls `EventBus`, `InputManager`, or `AudioManager` | Processing isolation |
| No FilterTools method has side effects | All outputs via return value |

---

## 20. Future Extensions

The following extensions are identified for potential future semesters. They are **not implemented in the current version** and are documented here only as placeholders for the professor's roadmap.

| Extension | Description | Target Unit |
|---|---|---|
| `motion_blur(surface, direction, amount)` | Directional motion blur for fast-moving sprites | Unit VII |
| `chromatic_aberration(surface, offset)` | RGB channel offset for visual glitch effect | Unit VII |
| `barrel_distortion(surface, coefficient)` | Lens distortion effect | Unit VII |
| `apply_kernel_to_sprite(entity, kernel)` | Apply filter to a specific entity's surface | Unit VII |
| `compute_optical_flow(surface_a, surface_b)` | Dense optical flow between two frames | Unit IX |


--- Traducción al Español ---

## Especificación de FilterTools

FilterTools proporciona funciones de convolución y detección de bordes aplicadas a superficies de Pygame mediante NumPy y SciPy.

### Funciones
- `apply_kernel(surface, kernel)` — Aplicar kernel de convolución personalizado
- `gaussian_blur(surface, sigma)` — Desenfoque gaussiano
- `sobel_edge(surface)` — Detección de bordes Sobel
- `canny_edge(surface, low, high)` — Detección de bordes Canny
- `adjust_brightness(surface, factor)` — Ajuste de brillo
- `adjust_contrast(surface, factor)` — Ajuste de contraste
- `compute_histogram(surface)` — Histograma RGB

Todas las funciones son de la Unidad VII del sílabo. Para ejemplos detallados de uso y kernels estándar, consultar el documento original en inglés.


---
## 🔗 Documentos Relacionados

- [[12_VISION_TOOLS_SPEC.md|Vision Tools Spec]]
- [[13_PATTERN_RECOGNITION_SPEC.md|Pattern Recognition Spec]]
