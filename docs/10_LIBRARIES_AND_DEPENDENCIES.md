---
document_id: "LOI-DEPS-010"
title: "Legacy of InFest — Libraries and Dependencies"
aliases: ["Libraries and Dependencies"]
tags: ["dependencies", "libraries", "setup"]
description: "Every third-party library, purpose, integration rules"
source: "docs/10_LIBRARIES_AND_DEPENDENCIES.md"
date_processed: "2026-07-14"
---

# Legacy of InFest — Libraries and Dependencies

**Document ID:** LOI-LIBS-010  
**Version:** 1.0.0  
**Status:** Official  
**Audience:** Professor, Teaching Assistants, Students, AI coding assistants

---

## 1. Overview

This document provides the complete specification of every library used in Legacy of InFest: what it is, why it exists in this project, how it is used, what restrictions apply, and concrete examples of its integration within the framework.

All libraries listed here are included in `requirements.txt`. Students must not import any library not present in this document without explicit professor approval. Adding an unapproved library dependency is a code review rejection condition.

---

## 2. pygame-ce

### 2.1 Identity

| Property | Value |
|---|---|
| Package name | `pygame-ce` |
| Import name | `pygame` |
| Version | Latest stable (CE branch) |
| Type | Game framework |
| License | LGPL 2.1 |

### 2.2 Purpose

Pygame CE (Community Edition) is the primary game development framework for Legacy of InFest. It provides the display surface, the event loop, hardware-accelerated surface blitting, sprite management, audio playback, input handling (keyboard and gamepad), and font rendering.

Pygame CE is the fork of the original Pygame maintained by the community. It offers improved performance, better controller support, and active maintenance — advantages over the legacy Pygame package.

### 2.3 Why It Exists

The entire visual output, input processing, audio system, and real-time loop of the game runs on Pygame CE. Without it, the framework does not execute.

### 2.4 Usage Rules

| Rule | Description |
|---|---|
| Import via engine only | Students never import `pygame` directly in stage code. All Pygame functionality is accessed through the engine API. |
| No direct display calls | `pygame.display.set_mode()` is called only in `engine/core/app.py`. |
| No direct input polling | `pygame.key.get_pressed()` is not called in entities or stages. Use `InputManager`. |
| No direct sound calls | `pygame.mixer.Sound.play()` is not called in stages. Use `AudioManager`. |
| No direct image loading | `pygame.image.load()` is not called in stages. Use `AssetLoader`. |
| Surface creation permitted | Students may create `pygame.Surface` objects in stage code for off-screen rendering. |

### 2.5 Integration Rules

Pygame CE is initialized exclusively in `engine/core/app.py`:

```python
pygame.init()
pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
pygame.display.set_mode(window_size, pygame.SCALED | pygame.RESIZABLE)
```

The `pygame.SCALED` flag enables hardware-accelerated integer scaling from 320×224 to the window size.

### 2.6 Examples

#### Surface creation for off-screen filter processing (student stage):
```python
from framework.processing.filter_tools import FilterTools

# Create an off-screen copy of the background for filtering
bg_copy = self.background_surface.copy()
filtered_bg = FilterTools.gaussian_blur(bg_copy, sigma=1.5)
# Blit filtered version at the appropriate parallax offset
```

#### Controller detection:
```python
# Engine handles this in InputManager — students do not write this:
joystick_count = pygame.joystick.get_count()
if joystick_count > 0:
    self.joystick = pygame.joystick.Joystick(0)
    self.joystick.init()
```

---

## 3. numpy

### 3.1 Identity

| Property | Value |
|---|---|
| Package name | `numpy` |
| Import name | `numpy` (aliased as `np`) |
| Version | Latest stable |
| Type | Numerical computation library |
| License | BSD 3-Clause |

### 3.2 Purpose

NumPy provides the N-dimensional array type (`ndarray`) used throughout the image processing pipeline. Pygame surfaces are converted to NumPy arrays for efficient per-pixel operations. All convolution, color space conversion, and segmentation operations work on NumPy arrays rather than on Pygame surfaces directly.

### 3.3 Why It Exists

Per-pixel operations on Pygame surfaces using pure Python loops are prohibitively slow at 60 FPS. NumPy enables vectorized operations — applying a transformation to all pixels simultaneously — making image processing practical in real time.

### 3.4 Usage Rules

| Rule | Description |
|---|---|
| Always alias as `np` | `import numpy as np` throughout the codebase |
| Use `np.uint8` dtype for pixel data | Pixel arrays must be in `uint8` (0–255) range |
| Convert back to surface after processing | Use `array_to_surface()` from `color_tools.py` |
| Do not store large arrays in entity state | Arrays are transient — created, used, and discarded per operation |

### 3.5 Integration Rules

The bridge between Pygame surfaces and NumPy arrays is standardized in `color_tools.py`:

```python
# Surface → ndarray (shape: height × width × 3 for RGB, or × 4 for RGBA)
array = pygame.surfarray.array3d(surface)           # RGB only
array_alpha = pygame.surfarray.array_alpha(surface) # Alpha only

# ndarray → Surface
surface = pygame.surfarray.make_surface(array)
```

**Important:** `pygame.surfarray.array3d()` returns an array with shape `(width, height, 3)` — note the axis order is transposed relative to standard image conventions (which use `height × width`). All filter operations must account for this.

### 3.6 Examples

#### Brightness adjustment:
```python
import numpy as np
import pygame

def adjust_brightness(surface: pygame.Surface, factor: float) -> pygame.Surface:
    """
    Multiply all pixel values by factor.
    Academic Unit VII: Brightness adjustment.
    """
    arr = pygame.surfarray.array3d(surface).astype(np.float32)
    arr = np.clip(arr * factor, 0, 255).astype(np.uint8)
    return pygame.surfarray.make_surface(arr)
```

#### Histogram computation:
```python
def compute_histogram(surface: pygame.Surface) -> dict:
    arr = pygame.surfarray.array3d(surface)
    return {
        'r': np.histogram(arr[:, :, 0], bins=256, range=(0, 255))[0],
        'g': np.histogram(arr[:, :, 1], bins=256, range=(0, 255))[0],
        'b': np.histogram(arr[:, :, 2], bins=256, range=(0, 255))[0],
    }
```

---

## 4. scipy

### 4.1 Identity

| Property | Value |
|---|---|
| Package name | `scipy` |
| Import name | `scipy` |
| Version | Latest stable |
| Type | Scientific computation library |
| License | BSD 3-Clause |

### 4.2 Purpose

SciPy provides the `ndimage` submodule used for spatial convolution operations. It is more convenient and efficient than implementing convolution from scratch with NumPy alone for arbitrary kernel shapes.

### 4.3 Why It Exists

`scipy.ndimage.convolve` and `scipy.ndimage.gaussian_filter` provide academically correct implementations of the convolution and Gaussian blur operations taught in Unit VII. Using SciPy ensures that the mathematical implementation is correct and trusted, allowing students to focus on applying the concepts rather than debugging low-level kernel arithmetic.

### 4.4 Usage Rules

| Rule | Description |
|---|---|
| Use only `scipy.ndimage` | No other SciPy submodule is used in this project |
| Always applied to `np.float32` arrays | Convert to float before filtering, back to uint8 after |
| Do not apply to full-screen surfaces every frame | Computationally expensive — apply to sub-surfaces or at reduced frequency |

### 4.5 Integration Rules

SciPy is used exclusively inside `framework/processing/filter_tools.py`. Stage code never imports SciPy directly.

### 4.6 Examples

#### Convolution with custom kernel (Unit VII):
```python
from scipy.ndimage import convolve
import numpy as np
import pygame

def apply_kernel(surface: pygame.Surface, kernel: np.ndarray) -> pygame.Surface:
    """
    Apply an arbitrary convolution kernel to the surface.
    Academic Unit VII: Convolution as a mathematical operation.
    """
    arr = pygame.surfarray.array3d(surface).astype(np.float32)
    # Apply kernel to each channel independently
    result = np.stack([
        convolve(arr[:, :, c], kernel, mode='reflect')
        for c in range(3)
    ], axis=-1)
    result = np.clip(result, 0, 255).astype(np.uint8)
    return pygame.surfarray.make_surface(result)
```

#### Gaussian blur:
```python
from scipy.ndimage import gaussian_filter

def gaussian_blur(surface: pygame.Surface, sigma: float) -> pygame.Surface:
    arr = pygame.surfarray.array3d(surface).astype(np.float32)
    blurred = gaussian_filter(arr, sigma=[sigma, sigma, 0])
    return pygame.surfarray.make_surface(blurred.astype(np.uint8))
```

---

## 5. opencv-python

### 5.1 Identity

| Property | Value |
|---|---|
| Package name | `opencv-python` |
| Import name | `cv2` |
| Version | Latest stable |
| Type | Computer vision library |
| License | Apache 2.0 |

### 5.2 Purpose

OpenCV provides advanced computer vision functions: Canny edge detection, Otsu thresholding, watershed segmentation, morphological operations, and feature extraction utilities. These are the primary tools for Units VII, VIII, and IX.

### 5.3 Why It Exists

The academic topics in Units VII, VIII, and IX require implementations of established computer vision algorithms that would be impractical to implement from scratch in the context of a student project. OpenCV provides industry-standard, academically recognized implementations of these algorithms. Using OpenCV allows students to apply the concepts and interpret the results rather than reimplementing well-understood algorithms.

### 5.4 Usage Rules

| Rule | Description |
|---|---|
| Import as `cv2` | Standard convention |
| Note BGR vs RGB | OpenCV uses BGR channel order; Pygame uses RGB. Always convert. |
| Use only via `vision_tools.py` | Students access OpenCV through the framework's vision tools, not directly |
| Do not process full-screen every frame | OpenCV operations are expensive; use sub-surfaces or throttled updates |

### 5.5 BGR/RGB Conversion Rule

This is a critical integration detail. OpenCV represents images as NumPy arrays in BGR (Blue-Green-Red) channel order. Pygame uses RGB. All conversions must be explicit:

```python
# Pygame/NumPy array (RGB) → OpenCV (BGR):
bgr_array = cv2_array[:, :, ::-1]  # Reverse channel axis

# OpenCV result (BGR) → Pygame (RGB):
rgb_array = cv2_result[:, :, ::-1]
```

All BGR/RGB conversions are handled inside `vision_tools.py`. Students never deal with this directly.

### 5.6 Integration Rules

OpenCV operations require the input array shape to be `(height, width, channels)`. Pygame's `surfarray.array3d()` returns `(width, height, channels)`. A transpose is required:

```python
# Pygame surfarray → OpenCV-compatible shape
arr = pygame.surfarray.array3d(surface)
arr_cv = np.transpose(arr, (1, 0, 2))  # (width, height, 3) → (height, width, 3)
arr_bgr = arr_cv[:, :, ::-1]           # RGB → BGR

# After OpenCV operation, convert back:
arr_rgb = cv2_result[:, :, ::-1]       # BGR → RGB
arr_pygame = np.transpose(arr_rgb, (1, 0, 2))  # (height, width, 3) → (width, height, 3)
surface = pygame.surfarray.make_surface(arr_pygame)
```

### 5.7 Examples

#### Canny edge detection (Unit VII):
```python
import cv2
import numpy as np
import pygame

def canny_edge(surface: pygame.Surface, low: int, high: int) -> pygame.Surface:
    """
    Apply Canny edge detection. Returns a grayscale surface.
    Academic Unit VII: Multi-stage edge detection.
    """
    arr = pygame.surfarray.array3d(surface)
    arr_cv = np.transpose(arr, (1, 0, 2))[:, :, ::-1]  # → BGR
    gray = cv2.cvtColor(arr_cv.astype(np.uint8), cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, low, high)
    edges_rgb = cv2.cvtColor(edges, cv2.COLOR_GRAY2RGB)
    result = np.transpose(edges_rgb, (1, 0, 2))
    return pygame.surfarray.make_surface(result)
```

#### Watershed segmentation (Unit VIII):
```python
def watershed_segment(surface: pygame.Surface) -> pygame.Surface:
    """
    Apply watershed segmentation. Returns a labeled color overlay.
    Academic Unit VIII: Region segmentation.
    """
    arr = pygame.surfarray.array3d(surface)
    arr_cv = np.transpose(arr, (1, 0, 2))[:, :, ::-1].astype(np.uint8)
    gray = cv2.cvtColor(arr_cv, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    # Distance transform + watershed (implementation in vision_tools.py)
    # ... (full implementation is in the module)
```

---

## 6. scikit-image

### 6.1 Identity

| Property | Value |
|---|---|
| Package name | `scikit-image` |
| Import name | `skimage` |
| Version | Latest stable |
| Type | Image processing library |
| License | BSD 3-Clause |

### 6.2 Purpose

scikit-image provides image processing utilities that complement OpenCV, with a more Pythonic API. It is particularly useful for morphological operations, local binary patterns (LBP), and histogram of oriented gradients (HOG) feature extraction.

### 6.3 Why It Exists

Some Unit VIII and IX operations — particularly HOG and LBP feature extraction — are more cleanly expressed in scikit-image's API than in OpenCV's. scikit-image also has excellent support for structured arrays and labeled images, which are useful for region analysis.

### 6.4 Usage Rules

| Rule | Description |
|---|---|
| Use only via `vision_tools.py` | Stage code does not import `skimage` directly |
| LBP feature extraction | `skimage.feature.local_binary_pattern()` |
| HOG feature extraction | `skimage.feature.hog()` |
| Note float [0,1] range | scikit-image functions often expect float arrays in [0,1], not uint8 in [0,255] |

### 6.5 Integration Rules

```python
# scikit-image expects float [0, 1] for most operations:
arr_float = arr.astype(np.float32) / 255.0

# After operation, convert back:
result_uint8 = (result_float * 255).astype(np.uint8)
```

### 6.6 Examples

#### HOG feature extraction (Unit IX):
```python
from skimage.feature import hog
import numpy as np
import pygame

def extract_features(surface: pygame.Surface) -> np.ndarray:
    """
    Extract HOG feature vector from surface.
    Academic Unit IX: Feature extraction for classification.
    """
    arr = pygame.surfarray.array3d(surface)
    arr_t = np.transpose(arr, (1, 0, 2)).astype(np.float32) / 255.0
    # Convert to grayscale for HOG
    gray = 0.299 * arr_t[:, :, 0] + 0.587 * arr_t[:, :, 1] + 0.114 * arr_t[:, :, 2]
    features = hog(
        gray,
        orientations=8,
        pixels_per_cell=(8, 8),
        cells_per_block=(2, 2),
        feature_vector=True
    )
    return features
```

---

## 7. scikit-learn

### 7.1 Identity

| Property | Value |
|---|---|
| Package name | `scikit-learn` |
| Import name | `sklearn` |
| Version | Latest stable |
| Type | Machine learning library |
| License | BSD 3-Clause |

### 7.2 Purpose

scikit-learn provides the classification algorithms used in Unit IX. Students train classifiers offline (in a Jupyter notebook or script) and serialize them to disk. At runtime, the game loads the serialized model and runs inference against in-game visual features.

### 7.3 Why It Exists

Unit IX requires classification. scikit-learn provides well-documented, academically standard implementations of k-NN, decision trees, random forests, and SVMs. Its consistent `fit` / `predict` API means that swapping classifiers (from k-NN to random forest, for example) is a one-line change — useful for comparative experiments.

### 7.4 Usage Rules

| Rule | Description |
|---|---|
| Train offline | Models are trained outside the game (in a script or notebook), then serialized |
| Serialize with `joblib` | `joblib.dump(model, path)` / `joblib.load(path)` |
| Load model in stage `on_enter()` | Do not load the model every frame |
| Max inference time | Single inference on a feature vector must complete in < 2ms |
| Use only via `vision_tools.py` | `classify_region()` is the framework entry point |

### 7.5 Integration Rules

#### Training script (offline, not part of game runtime):
```python
from sklearn.neighbors import KNeighborsClassifier
from sklearn.model_selection import train_test_split
import joblib
import numpy as np

# Load pre-extracted features and labels
X = np.load("features.npy")
y = np.load("labels.npy")

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

model = KNeighborsClassifier(n_neighbors=5)
model.fit(X_train, y_train)

accuracy = model.score(X_test, y_test)
print(f"Test accuracy: {accuracy:.3f}")

joblib.dump(model, "student_assets/models/sprite_classifier.pkl")
```

#### Runtime classification (in stage):
```python
import joblib
from framework.processing.vision_tools import VisionTools

class Stage3Scene(BaseScene):
    def on_enter(self):
        # Load model once at stage start
        self.classifier = joblib.load(STUDENT_ASSETS_DIR / "models" / "sprite_classifier.pkl")

    def _classify_screen_region(self, region_surface):
        features = VisionTools.extract_features(region_surface)
        label = VisionTools.classify_region(features, self.classifier)
        return label
```

### 7.6 Examples

#### classify_region in vision_tools.py:
```python
def classify_region(features: np.ndarray, model) -> str:
    """
    Classify a feature vector using a pre-trained scikit-learn model.
    Academic Unit IX: Pattern recognition and classification.
    
    Args:
        features: Feature vector (e.g., from extract_features())
        model: A fitted scikit-learn classifier with a .predict() method
    
    Returns:
        Predicted class label as a string.
    """
    prediction = model.predict(features.reshape(1, -1))
    return str(prediction[0])
```

---

## 8. Pillow

### 8.1 Identity

| Property | Value |
|---|---|
| Package name | `Pillow` |
| Import name | `PIL` |
| Version | Latest stable |
| Type | Image I/O and manipulation library |
| License | HPND (open source) |

### 8.2 Purpose

Pillow handles image loading and format conversion for the asset pipeline. While Pygame CE can load PNG and JPEG files natively, Pillow provides more robust support for edge cases: palette-mode PNGs, indexed color images, and images that require pre-processing before being loaded as Pygame surfaces.

Pillow is also used by the asset validation script (`tools/validate_assets.py`) to check that student assets conform to palette and dimension constraints.

### 8.3 Why It Exists

Some SNES-era sprite assets are created as indexed-color PNGs (palette mode `P`) in Aseprite. Pygame's `image.load()` handles these, but validation of the palette (checking that no more than 16 colors are used per sprite sheet) requires Pillow.

### 8.4 Usage Rules

| Rule | Description |
|---|---|
| Not used at runtime | Pillow is a development and validation tool; it is not imported in any engine or framework module |
| Asset validation only | `tools/validate_assets.py` uses Pillow to check palette compliance |
| Not in student stage code | Students do not import Pillow |

### 8.5 Integration Rules

Pillow is only used in offline tooling:

```python
from PIL import Image

def validate_sprite_palette(path: str, max_colors: int = 16) -> bool:
    """Check that a PNG sprite does not exceed max_colors in its palette."""
    img = Image.open(path)
    if img.mode == 'P':
        palette = img.getpalette()
        used_colors = len(set(img.getdata()))
        return used_colors <= max_colors
    elif img.mode == 'RGBA':
        colors = img.getcolors(maxcolors=65536)
        return len(colors) <= max_colors
    return True
```

---

## 9. pytmx

### 9.1 Identity

| Property | Value |
|---|---|
| Package name | `pytmx` |
| Import name | `pytmx` |
| Version | Latest stable |
| Type | Tiled map file parser |
| License | LGPL |

### 9.2 Purpose

`pytmx` parses `.tmx` files created by the Tiled map editor. It reads tile layers, object layers, tileset references, and custom properties, and exposes them as Python objects.

### 9.3 Why It Exists

Manual XML parsing of TMX files would be verbose and error-prone. `pytmx` provides a clean, well-tested API that integrates directly with Pygame CE, returning tile data as surface references.

### 9.4 Usage Rules

| Rule | Description |
|---|---|
| Used only in `StageLoader` | `framework/stage/stage_loader.py` is the only module that imports `pytmx` |
| Students never import pytmx | TMX parsing is an engine responsibility |
| All map access via `StageData` | `StageLoader` returns a `StageData` object; students use that |

### 9.5 Integration Rules

```python
import pytmx
import pygame

tmx_data = pytmx.util_pygame.load_pygame(str(tmx_path))

# Accessing tile layers:
for layer in tmx_data.visible_layers:
    if isinstance(layer, pytmx.TiledTileLayer):
        for x, y, gid in layer:
            tile_surface = tmx_data.get_tile_image_by_gid(gid)
            if tile_surface:
                # blit to appropriate layer surface

# Accessing object layers:
for obj in tmx_data.objects:
    if obj.type == "Walker":
        patrol_length = obj.properties.get("patrol_length", 96)
        spawn_pos = pygame.Vector2(obj.x, obj.y)
```

---

## 10. pyscroll

### 10.1 Identity

| Property | Value |
|---|---|
| Package name | `pyscroll` |
| Import name | `pyscroll` |
| Version | Latest stable |
| Type | Scrolling map renderer for pytmx |
| License | LGPL |

### 10.2 Purpose

`pyscroll` provides an efficient scrolling tile map renderer that integrates with `pytmx`. It renders only the visible portion of the map each frame, manages the camera viewport, and handles parallax layer scrolling.

### 10.3 Why It Exists

Rendering an entire 3840-pixel-wide map to a 320×224 surface on every frame is unnecessary and slow. `pyscroll` renders only the tiles that are currently in the viewport, using a buffered approach that pre-renders surrounding tiles for smooth scrolling.

### 10.4 Usage Rules

| Rule | Description |
|---|---|
| Used only in `StageLoader` and `Camera` | Students do not interact with pyscroll directly |
| Camera drives the pyscroll center | `Camera.update()` sets the pyscroll group center |

### 10.5 Integration Rules

```python
import pyscroll

map_data = pyscroll.data.TiledMapData(tmx_data)
map_layer = pyscroll.BufferedRenderer(
    map_data,
    size=(320, 224),
    clamp_camera=True
)
group = pyscroll.PyscrollGroup(map_layer=map_layer, default_layer=4)

# In stage draw():
group.center(player.rect.center)
group.draw(surface)
```

---

## 11. pytweening

### 11.1 Identity

| Property | Value |
|---|---|
| Package name | `pytweening` |
| Import name | `pytweening` |
| Version | Latest stable |
| Type | Easing functions library |
| License | BSD |

### 11.2 Purpose

`pytweening` provides a complete set of easing functions for smooth animation interpolation. These functions map a linear parameter `t ∈ [0, 1]` to a non-linear output, creating natural-feeling motion with acceleration and deceleration.

### 11.3 Why It Exists

The `engine/utils/math_utils.py` module wraps `pytweening` functions for use throughout the engine and framework. Implementing easing functions from scratch is error-prone and unnecessary. `pytweening` provides the full Robert Penner easing function set, which is the academic standard for animation interpolation.

The use of `pytweening` directly illustrates Unit VI course content: interpolation and ease functions are not abstractions — they are mathematical functions (polynomial, sinusoidal, exponential) applied to a normalized parameter.

### 11.4 Usage Rules

| Rule | Description |
|---|---|
| Always through `math_utils.py` | Stages use `ease_out_quad(t)` from `math_utils.py`, not `pytweening.easeOutQuad(t)` directly |
| `t` must be in [0, 1] | Easing functions are undefined outside this range |
| Do not mutate `t` inside the function | The easing function is stateless; the caller manages `t` progression |

### 11.5 Available Easing Functions (via math_utils.py)

| Function | math_utils name | Description |
|---|---|---|
| `pytweening.easeInQuad` | `ease_in_quad(t)` | Quadratic, slow start |
| `pytweening.easeOutQuad` | `ease_out_quad(t)` | Quadratic, slow end |
| `pytweening.easeInOutQuad` | `ease_in_out_quad(t)` | Quadratic, slow start and end |
| `pytweening.easeInCubic` | `ease_in_cubic(t)` | Cubic, slow start |
| `pytweening.easeOutCubic` | `ease_out_cubic(t)` | Cubic, slow end |
| `pytweening.easeOutBounce` | `ease_out_bounce(t)` | Bounce at end |
| `pytweening.easeOutElastic` | `ease_out_elastic(t)` | Elastic overshoot at end |
| `pytweening.easeInSine` | `ease_in_sine(t)` | Sinusoidal, slow start |
| `pytweening.easeOutSine` | `ease_out_sine(t)` | Sinusoidal, slow end |
| `pytweening.linear` | (use plain `lerp`) | Linear — not wrapped |

### 11.6 Examples

#### Moving platform with ease-in-out:
```python
from engine.utils.math_utils import ease_in_out_quad, lerp

class MovingPlatform(BaseEntity):
    def __init__(self, start_pos, end_pos, duration):
        super().__init__()
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.duration = duration
        self.t = 0.0
        self.direction = 1

    def update(self, dt: float):
        self.t += (dt / self.duration) * self.direction
        if self.t >= 1.0:
            self.t = 1.0
            self.direction = -1
        elif self.t <= 0.0:
            self.t = 0.0
            self.direction = 1

        # Apply easing to t before lerping position
        eased_t = ease_in_out_quad(self.t)
        self.position.x = lerp(self.start_pos.x, self.end_pos.x, eased_t)
        self.position.y = lerp(self.start_pos.y, self.end_pos.y, eased_t)
        self.rect.topleft = (int(self.position.x), int(self.position.y))
```

---

## 12. Dependency Summary Table

| Library | Runtime | Dev/Validation | Stage Code | Framework Code | Engine Code |
|---|---|---|---|---|---|
| `pygame-ce` | ✅ | — | ❌ (indirect only) | ✅ | ✅ |
| `numpy` | ✅ | — | ❌ (indirect only) | ✅ | — |
| `scipy` | ✅ | — | ❌ | ✅ | — |
| `opencv-python` | ✅ | — | ❌ | ✅ | — |
| `scikit-image` | ✅ | — | ❌ | ✅ | — |
| `scikit-learn` | ✅ | — | ✅ (model load) | ✅ | — |
| `Pillow` | — | ✅ | ❌ | — | — |
| `pytmx` | ✅ | — | ❌ | ✅ (stage only) | — |
| `pyscroll` | ✅ | — | ❌ | ✅ (stage only) | — |
| `pytweening` | ✅ | — | ❌ (via math_utils) | — | ✅ |

**Legend:**
- ✅ Used
- ❌ Prohibited
- — Not applicable

---

## 13. requirements.txt

The complete `requirements.txt` for Legacy of InFest:

```
pygame-ce
numpy
scipy
opencv-python
scikit-image
scikit-learn
Pillow
pytmx
pyscroll
pytweening
joblib
```

`joblib` is included as an explicit dependency (it is a scikit-learn dependency but is listed explicitly for clarity, as it is used directly for model serialization/deserialization).

---

## 14. Installation and Environment

### 14.1 Virtual Environment Setup

```bash
# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Activate (macOS / Linux)
source .venv/bin/activate

# Install all dependencies
pip install -r requirements.txt

# Verify installation
python -c "import pygame; print(pygame.version.ver)"
python -c "import cv2; print(cv2.__version__)"
python -c "import numpy; print(numpy.__version__)"
```

### 14.2 Troubleshooting

| Issue | Solution |
|---|---|
| `ModuleNotFoundError: No module named 'cv2'` | Run `pip install opencv-python` |
| `pygame-ce` conflicts with `pygame` | Uninstall `pygame` first: `pip uninstall pygame && pip install pygame-ce` |
| `pytmx` map loading fails | Ensure Tiled exported with `.tsx` tileset files relative to the `.tmx` |
| Controller not detected | Update `pygame-ce` to the latest version; CE has improved controller support |
| NumPy version conflict with scikit-learn | Ensure all packages installed in the same virtual environment |


--- Traducción al Español ---

## Librerías y Dependencias

Este documento especifica cada librería utilizada en Legacy of InFest.

| Librería | Propósito |
|----------|-----------|
| pygame-ce | Framework de juego principal |
| numpy | Arreglos N-dimensionales para procesamiento de imágenes |
| scipy | Convolución espacial y filtros |
| opencv-python | Visión por computadora avanzada |
| scikit-image | Procesamiento de imágenes (HOG, LBP) |
| scikit-learn | Algoritmos de clasificación (k-NN, árboles, SVM) |
| Pillow | Validación de assets (solo herramientas) |
| pytmx | Carga de archivos de mapa Tiled |
| pyscroll | Renderizado eficiente de mapas |
| pytweening | Funciones de easing para animación |
| joblib | Serialización de modelos ML |

Para reglas de uso, ejemplos de integración y configuración de entorno, consultar el documento original en inglés.


---
## 🔗 Documentos Relacionados

- [[32_ENVIRONMENT_SETUP_GUIDE.md|Environment Setup Guide]]
