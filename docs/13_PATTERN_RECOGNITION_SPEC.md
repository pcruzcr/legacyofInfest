# Legacy of InFest — Pattern Recognition Specification

**Document ID:** LOI-PATTERN-013  
**Version:** 1.0.0  
**Status:** Official  
**Compatibility:** Requires LOI-VISION-012, LOI-FILTER-011, LOI-ARCH-003, LOI-LIBS-010  
**Audience:** Professor, Teaching Assistants, AI coding assistants (Claude Code, Cline, OpenCode, Codex)

---

## 1. Overview

`PatternRecognitionTools` is the machine learning subsystem of the Legacy of InFest academic framework. It encapsulates all classification and pattern recognition operations taught in **Unit IX** of the course syllabus: feature-based classification, model training, model serialization, runtime inference, and the integration of machine learning into an interactive application.

This module is the final layer of the academic pipeline:

```
FilterTools (Unit VII) → VisionTools (Unit VIII) → PatternRecognitionTools (Unit IX)
```

`PatternRecognitionTools` receives feature vectors produced by `VisionTools.extract_features()` and returns class labels that drive observable game behavior. All classifier complexity — k-NN, decision trees, random forests, SVM — is hidden behind a unified API.

The module is located at:

```
framework/processing/pattern_recognition_tools.py
```

---

## 2. Academic Purpose

`PatternRecognitionTools` makes Unit IX concepts **executable within a real-time interactive application**. Students train classifiers offline, load them into their stage, and observe the classification result changing game behavior as the visual state of the stage evolves.

This answers the key question of the capstone unit: *Can a computer recognize patterns in visual data and respond intelligently?*

### 2.1 Learning Objectives Supported

| Objective | PatternRecognitionTools Mechanism |
|---|---|
| Understand feature spaces | `extract_features()` (from VisionTools) produces the feature space |
| Apply k-NN classification | `PatternRecognitionTools.classify(features, model='knn')` |
| Apply decision tree classification | `classify(features, model='tree')` |
| Apply random forest classification | `classify(features, model='forest')` |
| Apply SVM classification | `classify(features, model='svm')` |
| Train a classifier from a dataset | `PatternRecognitionTools.train(X, y, model_type)` |
| Evaluate classifier performance | `PatternRecognitionTools.evaluate(model, X_test, y_test)` |
| Serialize a model for runtime use | `PatternRecognitionTools.save_model(model, path)` |
| Load a model at runtime | `PatternRecognitionTools.load_model(path)` |
| Run inference in a game loop | `PatternRecognitionTools.predict(model, surface)` |

---

## 3. Framework Location

```
framework/
└── processing/
    ├── filter_tools.py
    ├── vision_tools.py
    └── pattern_recognition_tools.py    ← This module
```

### 3.1 Position in the Dependency Hierarchy

```
Stages (student code)
    ↓
framework/processing/pattern_recognition_tools.py   ← Students call this
    ↓
framework/processing/vision_tools.py                ← For feature extraction
    ↓
scikit-learn, scikit-image, numpy, joblib, opencv-python
```

---

## 4. Architecture Integration

### 4.1 Connections to the Framework

| Integration Point | Description |
|---|---|
| `VisionTools.extract_features()` | Primary source of feature vectors |
| `VisionTools.extract_hog()`, `extract_lbp()`, `extract_color_histogram()` | Alternative direct feature sources |
| Stage scenes (student code) | Students load models in `on_enter()`, run inference in `update()` |
| `student_assets/models/` | Directory for serialized model files |
| Unit test suite (`tests/test_pattern_recognition_tools.py`) | Tests training, inference, and serialization round-trips |

### 4.2 What PatternRecognitionTools Does NOT Do

| Forbidden Action | Reason |
|---|---|
| Does not call `EventBus` | Pure computation module |
| Does not modify entity state | Results are returned; students decide what to do |
| Does not perform training at runtime | Training is always offline |
| Does not read game state | All input is via explicit parameters |
| Does not hold singleton state | Stateless class methods (except the Model Registry) |

---

## 5. Dependencies

| Library | Import | Used For |
|---|---|---|
| `numpy` | `import numpy as np` | Feature array handling |
| `scikit-learn` | `from sklearn.neighbors import KNeighborsClassifier` etc. | All classifiers |
| `joblib` | `import joblib` | Model serialization and loading |
| `framework.processing.vision_tools` | `from framework.processing.vision_tools import VisionTools` | Internal feature extraction (for `predict()`) |

**Students never import scikit-learn or joblib directly.**

---

## 6. Class Diagram

```
PatternRecognitionTools
│
├── [Feature Extractors]
│   ├── extract_hog(surface) → np.ndarray            [delegates to VisionTools]
│   ├── extract_lbp(surface) → np.ndarray            [delegates to VisionTools]
│   ├── extract_color_histogram(surface, bins) → np.ndarray  [delegates to VisionTools]
│   └── extract_combined(surface) → np.ndarray       [delegates to VisionTools]
│
├── [Training Pipeline]
│   ├── train(X, y, model_type, **kwargs) → TrainedModel
│   └── evaluate(model, X_test, y_test) → EvaluationResult
│
├── [Model Serialization]
│   ├── save_model(model, path) → None
│   └── load_model(path) → TrainedModel
│
├── [Model Registry]
│   ├── register_model(name, model) → None
│   ├── get_model(name) → TrainedModel
│   └── list_models() → list[str]
│
├── [Inference Pipeline]
│   ├── classify(features, model) → str
│   ├── classify_proba(features, model) → dict[str, float]
│   └── predict(model, surface, method) → str
│
└── [Internal Utilities — private]
    ├── _build_model(model_type, **kwargs) → sklearn estimator
    ├── _validate_features(features) → None
    ├── _validate_model(model) → None
    └── _validate_dataset(X, y) → None
```

### 6.1 Return Type Definitions

#### `TrainedModel` (dataclass)

| Field | Type | Description |
|---|---|---|
| `model_type` | `str` | `'knn'`, `'tree'`, `'forest'`, `'svm'` |
| `estimator` | sklearn estimator | The fitted scikit-learn model object |
| `classes` | `list[str]` | Ordered list of class label strings |
| `feature_method` | `str` | Feature extraction method used for training |
| `feature_length` | `int` | Expected input vector length |
| `training_accuracy` | `float` | Accuracy on the training set |
| `metadata` | `dict` | Arbitrary metadata (hyperparameters, notes) |

#### `EvaluationResult` (dataclass)

| Field | Type | Description |
|---|---|---|
| `accuracy` | `float` | Overall accuracy on the test set |
| `per_class_accuracy` | `dict[str, float]` | Per-class accuracy |
| `confusion_matrix` | `np.ndarray` | Confusion matrix of shape `(n_classes, n_classes)` |
| `report` | `str` | scikit-learn `classification_report` string |

---

## 7. Feature Extractors

`PatternRecognitionTools` exposes feature extractors as pass-through methods that delegate to `VisionTools`. This design means students only need to import `PatternRecognitionTools` to access the full Unit VIII + IX pipeline.

### 7.1 `PatternRecognitionTools.extract_hog(surface)`

Delegates to `VisionTools.extract_hog(surface)`. See `12_VISION_TOOLS_SPEC.md` §13.2 for full specification.

**Returns:** `np.ndarray` of shape `(512,)` for 32×32 canonical input.

---

### 7.2 `PatternRecognitionTools.extract_lbp(surface)`

Delegates to `VisionTools.extract_lbp(surface)`. See `12_VISION_TOOLS_SPEC.md` §13.3.

**Returns:** `np.ndarray` of shape `(256,)`.

---

### 7.3 `PatternRecognitionTools.extract_color_histogram(surface, bins=256)`

Delegates to `VisionTools.extract_color_histogram(surface, bins)`. See `12_VISION_TOOLS_SPEC.md` §13.4.

**Returns:** `np.ndarray` of shape `(bins * 3,)`.

---

### 7.4 `PatternRecognitionTools.extract_combined(surface)`

Delegates to `VisionTools.extract_features(surface, method='combined')`. Concatenates HOG + LBP + color histogram into a single descriptor.

**Returns:** `np.ndarray` of shape `(512 + 256 + 768,) = (1536,)`.

**When to use:** When maximum discriminative power is needed. Note the larger vector increases training time and may require more training samples.

---

## 8. Dataset Standards

### 8.1 Dataset Format

All training datasets used in Legacy of InFest must conform to the following standards:

| Property | Standard |
|---|---|
| Feature matrix `X` | `np.ndarray`, shape `(n_samples, n_features)`, dtype `float32` |
| Label vector `y` | `np.ndarray`, shape `(n_samples,)`, dtype `str` or `int` |
| Minimum samples per class | 10 |
| Balanced classes | Recommended. Imbalanced datasets must be documented in README. |
| Feature scaling | Applied automatically inside `train()` using `StandardScaler` |

### 8.2 Dataset Sources

Students collect their training dataset from **game assets and screenshots**. Acceptable sources:

| Source | Method |
|---|---|
| Stage backgrounds | Save screenshots at different stage states; label manually |
| Sprite sheets | Extract frames; label by animation state |
| Synthetically generated | Generate surfaces programmatically with known properties |
| Provided by professor | Professor may provide pre-labeled datasets for Unit IX |

### 8.3 Dataset File Format

Datasets are serialized as `.npz` files (NumPy compressed archive):

```python
# Saving a dataset (student training script):
np.savez('student_assets/datasets/my_dataset.npz', X=X, y=y)

# Loading a dataset:
data = np.load('student_assets/datasets/my_dataset.npz')
X, y = data['X'], data['y']
```

---

## 9. Training Pipeline

### 9.1 `PatternRecognitionTools.train(X, y, model_type, **kwargs)`

**Purpose:** Fit a classifier to the provided feature matrix and label vector. Returns a `TrainedModel` object ready for serialization or immediate use. This method is called from a **training script**, not from the game itself.

**Inputs:**

| Parameter | Type | Constraints | Description |
|---|---|---|---|
| `X` | `np.ndarray` | Shape `(n_samples, n_features)`, float32 | Feature matrix |
| `y` | `np.ndarray` | Shape `(n_samples,)` | Label vector |
| `model_type` | `str` | `'knn'`, `'tree'`, `'forest'`, `'svm'` | Classifier type |
| `**kwargs` | — | Model-specific | Hyperparameters (see §12) |

**Outputs:** `TrainedModel` object.

**Internal Pipeline:**

```
Inputs: X (n_samples, n_features), y (n_samples,)
    ↓
_validate_dataset(X, y)
    ↓
StandardScaler().fit_transform(X) → X_scaled
    ↓
_build_model(model_type, **kwargs) → sklearn_estimator
    ↓
sklearn_estimator.fit(X_scaled, y)
    ↓
training_accuracy = sklearn_estimator.score(X_scaled, y)
    ↓
return TrainedModel(
    model_type=model_type,
    estimator=Pipeline([('scaler', scaler), ('classifier', estimator)]),
    classes=list(unique_labels),
    feature_method='external',  # Set by caller if known
    feature_length=X.shape[1],
    training_accuracy=training_accuracy,
    metadata={'kwargs': kwargs}
)
```

**Important:** The `StandardScaler` is embedded inside the model's `Pipeline` object. This means the scaler is applied automatically on both training and inference — students do not need to scale features manually before calling `classify()`.

**Restrictions:**

- Minimum 2 distinct classes in `y`.
- Minimum 10 samples total.
- `model_type` must be one of the registered values.
- Raises `ValueError` on validation failure.

**Dependencies:** `scikit-learn`, `numpy`

**Usage Example (training script — not game code):**

```python
import numpy as np
from framework.processing.pattern_recognition_tools import PatternRecognitionTools

# Load dataset
data = np.load('student_assets/datasets/stage3_regions.npz')
X, y = data['X'].astype(np.float32), data['y']

# Train random forest
model = PatternRecognitionTools.train(X, y, model_type='forest', n_estimators=50)
print(f"Training accuracy: {model.training_accuracy:.3f}")

# Save for runtime
PatternRecognitionTools.save_model(model, 'student_assets/models/stage3_classifier.pkl')
```

---

### 9.2 `PatternRecognitionTools.evaluate(model, X_test, y_test)`

**Purpose:** Evaluate a trained model on a held-out test set. Returns an `EvaluationResult` with accuracy, per-class accuracy, confusion matrix, and a classification report. This is called from the training script — not at runtime.

**Inputs:**

| Parameter | Type | Description |
|---|---|---|
| `model` | `TrainedModel` | A fitted model from `train()` |
| `X_test` | `np.ndarray` | Test feature matrix, shape `(n_test, n_features)` |
| `y_test` | `np.ndarray` | Test labels, shape `(n_test,)` |

**Outputs:** `EvaluationResult` (see Section 6.1).

**Restrictions:**

- `X_test.shape[1]` must equal `model.feature_length`.
- At least 1 sample per class in the test set.

**Dependencies:** `scikit-learn` (`classification_report`, `confusion_matrix`)

**Usage Example:**

```python
from sklearn.model_selection import train_test_split

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

model = PatternRecognitionTools.train(X_train, y_train, model_type='knn', n_neighbors=5)
result = PatternRecognitionTools.evaluate(model, X_test, y_test)

print(f"Test accuracy: {result.accuracy:.3f}")
print(result.report)
# → Include this output in stage README as required documentation
```

---

## 10. Validation Pipeline

The validation pipeline documents how students must test and document their classifiers before integrating them into their stage.

### 10.1 Required Validation Steps

| Step | Action | Documentation Required |
|---|---|---|
| 1. Split dataset | Use `train_test_split` with `test_size=0.2`, `random_state=42` | State split ratio in README |
| 2. Train model | Call `PatternRecognitionTools.train()` | State model type and hyperparameters |
| 3. Evaluate | Call `PatternRecognitionTools.evaluate()` | Include full `EvaluationResult.report` in README |
| 4. Verify feature length | Confirm `model.feature_length` matches runtime extraction | State in README |
| 5. Sanity check | Run `classify()` on 3 known examples manually | Show predictions vs. expected in README |

### 10.2 Minimum Acceptable Performance

| Metric | Threshold | Action If Below |
|---|---|---|
| Test accuracy | ≥ 0.70 (70%) | Collect more samples, adjust hyperparameters, or change model type |
| Per-class accuracy | ≥ 0.60 for every class | Check class balance, collect more samples for weak class |

A classifier below these thresholds may be submitted but must include a documented analysis of why the performance is limited and what would be needed to improve it.

---

## 11. Model Serialization

### 11.1 `PatternRecognitionTools.save_model(model, path)`

**Purpose:** Serialize a `TrainedModel` to disk using `joblib`. The entire `TrainedModel` dataclass — including the fitted scikit-learn Pipeline (with scaler), class labels, feature length, and metadata — is serialized into a single `.pkl` file.

**Inputs:**

| Parameter | Type | Description |
|---|---|---|
| `model` | `TrainedModel` | A fitted model from `train()` |
| `path` | `str` or `pathlib.Path` | Output file path (must end in `.pkl`) |

**Outputs:** None. File is written to `path`.

**File Location Convention:** All student model files must be saved to `student_assets/models/`.

**Restrictions:**

- `path` must have `.pkl` extension. Raises `ValueError` otherwise.
- Parent directory is created if it does not exist.

**Dependencies:** `joblib`

---

### 11.2 `PatternRecognitionTools.load_model(path)`

**Purpose:** Deserialize a `TrainedModel` from disk. Verifies that the loaded object is a valid `TrainedModel` before returning it.

**Inputs:**

| Parameter | Type | Description |
|---|---|---|
| `path` | `str` or `pathlib.Path` | Path to a `.pkl` file created by `save_model()` |

**Outputs:** `TrainedModel` — ready for use with `classify()` and `predict()`.

**Restrictions:**

- File must exist. Raises `FileNotFoundError` if not found.
- Loaded object must be a `TrainedModel`. Raises `TypeError` if not.
- Do not load models from untrusted sources (`joblib.load` can execute arbitrary code — professor-provided datasets only in academic context).

**Dependencies:** `joblib`

**Usage Example (in stage `on_enter()`):**

```python
from framework.processing.pattern_recognition_tools import PatternRecognitionTools
from engine.core.settings import STUDENT_ASSETS_DIR

class Stage3Scene(BaseScene):
    def on_enter(self):
        model_path = STUDENT_ASSETS_DIR / "models" / "stage3_classifier.pkl"
        self.classifier = PatternRecognitionTools.load_model(model_path)
```

---

## 12. Model Registry

The Model Registry provides an in-memory named store for loaded models. It allows a stage to load multiple models at startup and retrieve them by name without passing model objects through multiple method calls.

### 12.1 `PatternRecognitionTools.register_model(name, model)`

**Purpose:** Store a loaded `TrainedModel` in the registry under a string name.

**Inputs:**

| Parameter | Type | Description |
|---|---|---|
| `name` | `str` | Unique registry key for this model |
| `model` | `TrainedModel` | Fitted model to register |

**Outputs:** None.

**Restrictions:** If `name` already exists, the old model is replaced and a warning is logged.

---

### 12.2 `PatternRecognitionTools.get_model(name)`

**Purpose:** Retrieve a registered model by name.

**Inputs:**

| Parameter | Type | Description |
|---|---|---|
| `name` | `str` | Registry key |

**Outputs:** `TrainedModel`.

**Restrictions:** Raises `KeyError` if `name` not found. Message includes `list_models()` output.

---

### 12.3 `PatternRecognitionTools.list_models()`

**Purpose:** Return the list of all currently registered model names.

**Outputs:** `list[str]`.

---

## 13. Inference Pipeline

### 13.1 `PatternRecognitionTools.classify(features, model)`

**Purpose:** Classify a pre-computed feature vector using a `TrainedModel`. This is the core inference method. It applies the model's internal `StandardScaler` automatically (via the Pipeline) and returns the predicted class label as a string.

**This is the primary runtime method.** It is designed for use inside `update()` loops.

**Inputs:**

| Parameter | Type | Constraints | Description |
|---|---|---|---|
| `features` | `np.ndarray` | Shape `(n_features,)`, float32 | Feature vector from `VisionTools.extract_features()` |
| `model` | `TrainedModel` | Must be a fitted model | The classifier to use |

**Outputs:** `str` — the predicted class label.

**Restrictions:**

- `features.shape[0]` must equal `model.feature_length`. Raises `ValueError` if not.
- Must complete in < 2ms for safe use in a 60 FPS game loop.
- Does not modify the model state.

**Dependencies:** `scikit-learn` (via model's internal Pipeline)

**Usage Example:**

```python
# In Stage3Scene.update(dt):
region_surface = self.stage_surface.subsurface(self.analysis_rect)
features = PatternRecognitionTools.extract_hog(region_surface)
label = PatternRecognitionTools.classify(features, self.classifier)

if label == 'dark_zone':
    self.spawn_dark_enemy()
elif label == 'light_zone':
    self.spawn_light_enemy()
```

---

### 13.2 `PatternRecognitionTools.classify_proba(features, model)`

**Purpose:** Return the class probability distribution for a feature vector. Instead of a single label, this returns the model's confidence for each class. Available only for models that support probability estimation (`knn`, `forest`, `svm` with `probability=True`).

**Inputs:** Same as `classify()`.

**Outputs:** `dict[str, float]` — class label mapped to probability. Probabilities sum to 1.0.

**Restrictions:**

- Decision tree (`'tree'`) does not support probability estimation — raises `NotImplementedError`.
- Probability calibration is not applied (raw `predict_proba()` output).

**Usage Example:**

```python
proba = PatternRecognitionTools.classify_proba(features, self.classifier)
# {'dark_zone': 0.72, 'light_zone': 0.18, 'neutral': 0.10}

if proba.get('dark_zone', 0) > 0.6:
    self.activate_dark_mode()
```

---

### 13.3 `PatternRecognitionTools.predict(model, surface, method='hog')`

**Purpose:** Convenience method. Combines feature extraction and classification in one call. Internally calls `VisionTools.extract_features(surface, method)` then `classify(features, model)`.

**Inputs:**

| Parameter | Type | Description |
|---|---|---|
| `model` | `TrainedModel` | Fitted model |
| `surface` | `pygame.Surface` | Surface to classify |
| `method` | `str` | Feature extraction method (`'hog'`, `'lbp'`, `'color_hist'`, `'combined'`) |

**Outputs:** `str` — predicted class label.

**Restrictions:**

- `method` must match the method used during training. Raises `ValueError` if `model.feature_method` is set and does not match.
- Inference time = feature extraction + classification; must remain < 2ms total.

**Usage Example:**

```python
# One-line classification:
label = PatternRecognitionTools.predict(self.classifier, region_surface, method='hog')
```

---

## 14. Classification API — Classifier Specifications

### 14.1 K-Nearest Neighbors (`'knn'`)

| Parameter | Default | Description |
|---|---|---|
| `n_neighbors` | 5 | Number of neighbors to consider |
| `weights` | `'uniform'` | `'uniform'` or `'distance'` |
| `metric` | `'euclidean'` | Distance metric |

**Characteristics:**
- Simple, interpretable — students can explain "the 5 most similar training examples"
- No training phase (lazy learner) — `train()` is fast
- Inference time grows with dataset size — keep training set small (< 500 samples) for < 2ms inference

**Usage Example:**

```python
model = PatternRecognitionTools.train(X, y, 'knn', n_neighbors=3, weights='distance')
```

---

### 14.2 Decision Tree (`'tree'`)

| Parameter | Default | Description |
|---|---|---|
| `max_depth` | `None` (unlimited) | Maximum tree depth |
| `min_samples_split` | 2 | Minimum samples to split a node |
| `criterion` | `'gini'` | Split criterion: `'gini'` or `'entropy'` |
| `random_state` | 42 | Reproducibility seed |

**Characteristics:**
- Highly interpretable — students can inspect the decision tree structure
- Prone to overfitting without `max_depth` — students should set this
- Fast inference: O(log n_nodes)
- Probability output not supported

**Usage Example:**

```python
model = PatternRecognitionTools.train(X, y, 'tree', max_depth=5, criterion='entropy')
```

---

### 14.3 Random Forest (`'forest'`)

| Parameter | Default | Description |
|---|---|---|
| `n_estimators` | 50 | Number of trees in the forest |
| `max_depth` | `None` | Maximum tree depth |
| `max_features` | `'sqrt'` | Features per tree split |
| `random_state` | 42 | Reproducibility seed |

**Characteristics:**
- Robust to overfitting — good default choice for students
- Slower training than single tree, but still fast for small datasets
- Feature importance accessible via `model.estimator.named_steps['classifier'].feature_importances_`

**Usage Example:**

```python
model = PatternRecognitionTools.train(X, y, 'forest', n_estimators=100, max_depth=8)
```

---

### 14.4 Support Vector Machine (`'svm'`)

| Parameter | Default | Description |
|---|---|---|
| `kernel` | `'rbf'` | Kernel type: `'linear'`, `'rbf'`, `'poly'` |
| `C` | 1.0 | Regularization parameter |
| `gamma` | `'scale'` | Kernel coefficient |
| `probability` | `True` | Enable probability estimation (required for `classify_proba`) |
| `random_state` | 42 | Reproducibility seed |

**Characteristics:**
- Strong performance on small datasets with high-dimensional features
- Longer training time than tree methods for large datasets
- Probability estimation with `probability=True` requires additional Platt scaling (slower training)

**Usage Example:**

```python
model = PatternRecognitionTools.train(X, y, 'svm', kernel='rbf', C=2.0)
```

---

## 15. Model Registry Usage Pattern

The recommended pattern for a student stage using multiple classifiers:

```python
# In Stage3Scene.on_enter():
PatternRecognitionTools.register_model(
    'region_classifier',
    PatternRecognitionTools.load_model(STUDENT_ASSETS_DIR / 'models' / 'regions.pkl')
)
PatternRecognitionTools.register_model(
    'sprite_classifier',
    PatternRecognitionTools.load_model(STUDENT_ASSETS_DIR / 'models' / 'sprites.pkl')
)

# In Stage3Scene.update(dt):
region_label = PatternRecognitionTools.predict(
    PatternRecognitionTools.get_model('region_classifier'),
    self.background_region,
    method='hog'
)
sprite_label = PatternRecognitionTools.predict(
    PatternRecognitionTools.get_model('sprite_classifier'),
    self.sprite_region,
    method='lbp'
)
```

---

## 16. Prediction Workflow

### 16.1 Complete Runtime Inference Flow

```
[Stage update() — every N frames]
    ↓
1. Capture surface region
   region = screen_surface.subsurface(analysis_rect)
    ↓
2. Preprocess (optional — if training used filtered input)
   preprocessed = FilterTools.gaussian_blur(region, sigma=1.0)
    ↓
3. Extract features
   features = PatternRecognitionTools.extract_hog(preprocessed)
    ↓
4. Classify
   label = PatternRecognitionTools.classify(features, self.classifier)
    ↓
5. Act on result
   if label == 'class_A': → game behavior A
   if label == 'class_B': → game behavior B
```

### 16.2 Frame Throttling for Inference

Classification is not performed every frame. Students use a frame counter:

| Classifier Type | Recommended Inference Frequency |
|---|---|
| k-NN (dataset < 100) | Every 3 frames |
| k-NN (dataset 100–500) | Every 5 frames |
| Decision Tree | Every 2 frames |
| Random Forest (50 trees) | Every 3 frames |
| SVM (RBF kernel) | Every 3 frames |

---

## 17. Performance Constraints

### 17.1 Inference Time Budget

Total inference budget per call: **< 2ms** (to remain within the 16.67ms frame budget alongside feature extraction).

| Classifier | Dataset Size | Typical Inference Time |
|---|---|---|
| k-NN (k=5) | 100 samples | < 0.5ms |
| k-NN (k=5) | 500 samples | ~1ms |
| k-NN (k=5) | 1000+ samples | > 2ms ⚠ |
| Decision Tree (depth 5) | Any | < 0.1ms |
| Random Forest (50 trees) | Any | ~0.5ms |
| SVM (RBF) | Any | < 1ms |

### 17.2 Training Time (Offline Only)

| Classifier | Dataset 100 | Dataset 500 | Dataset 1000 |
|---|---|---|---|
| k-NN | ~0ms (lazy) | ~0ms (lazy) | ~0ms (lazy) |
| Decision Tree | < 100ms | < 500ms | ~1s |
| Random Forest (50) | ~500ms | ~2s | ~5s |
| SVM (RBF) | ~100ms | ~2s | ~10s |

---

## 18. Unit IX Mapping

| Unit IX Topic | PatternRecognitionTools Component | Observable In-Game |
|---|---|---|
| Descriptors (HOG, LBP) | `extract_hog()`, `extract_lbp()` | Feature vector printed in README |
| Color-based features | `extract_color_histogram()` | Color distribution drives class |
| Combined descriptors | `extract_combined()` | Multi-modal feature vector |
| KNN Classification | `train(..., 'knn')` + `classify()` | Game changes behavior by class |
| Decision Tree | `train(..., 'tree')` | Student inspects tree structure |
| Random Forest | `train(..., 'forest')` | Robust classifier for capstone |
| SVM | `train(..., 'svm')` | Advanced optional classifier |
| Model training pipeline | `train()` + `evaluate()` | Accuracy documented in README |
| Model serialization | `save_model()` / `load_model()` | `.pkl` file in student_assets/ |
| Inference loop | `predict()` in `update()` | Real-time classification result |
| Computer vision integration | Full pipeline (Filter→Vision→Pattern) | End-to-end demo in Stage 3 |

---

## 19. Assessment Mapping

| Assessment | Unit | Required Deliverable | Evidence |
|---|---|---|---|
| Practical Exam III | IX | Full pipeline: dataset → train → evaluate → integrate | Live demo + EvaluationResult in README |
| Stage 3 Final | IX | Classifier running at runtime, changing game behavior | Code review + oral explanation |
| Final Presentation | IX | Explain one classifier mathematically (decision boundary, feature space) | Oral + notebook |

---

## 20. Professor Deliverables

1. **`framework/processing/pattern_recognition_tools.py`** — Complete, documented, tested implementation.
2. **`tests/test_pattern_recognition_tools.py`** — Tests for training, serialization, inference, and the complete pipeline.
3. **`tools/build_dataset.py`** — A helper script students use to extract features from labeled image directories and build a `.npz` dataset file.
4. **`student_assets/datasets/sample_dataset.npz`** — A small sample dataset (50 samples, 3 classes) for students to verify their pipeline before building their own.
5. **Demo Scene (see Document 15)** — Interactive Unit IX demo where a trained classifier is shown classifying screen regions in real time.
6. **Training notebook template** — `notebooks/train_stage3_classifier.ipynb` — a Jupyter notebook template with all required steps pre-scaffolded.

---

## 21. Student Reuse

Students reuse `PatternRecognitionTools` by:

1. Running `tools/build_dataset.py` to build their dataset from labeled surface screenshots.
2. Using the training notebook template to train and evaluate their classifier.
3. Calling `save_model()` to save the trained model.
4. Loading the model in `Stage3Scene.on_enter()`.
5. Calling `predict()` in `Stage3Scene.update()` every N frames.
6. Using the predicted label to change game behavior.

Students write **no machine learning code**. They write **game behavior conditioned on classification results**.

---

## 22. Learning Evidence

A student has demonstrated Unit IX learning when they can:

1. **Show** their dataset: number of samples, classes, feature method, and class balance.
2. **Present** their `EvaluationResult`: accuracy, confusion matrix, and per-class report.
3. **Explain** why they chose their classifier type (interpretability, accuracy, speed).
4. **Demonstrate live** the classifier changing game behavior in at least two distinct classes.
5. **Explain** mathematically what the decision boundary of their classifier looks like (linear for SVM linear, tree splits for decision tree, etc.).
6. **Compare** two classifier types on their dataset and explain the tradeoff.

---

## 23. Restrictions

| Restriction | Scope |
|---|---|
| Students never import `sklearn` directly | All student stage files |
| Students never import `joblib` directly | All student stage files |
| Model training never happens at runtime | Training is always offline |
| Model files stored in `student_assets/models/` only | File system constraint |
| `PatternRecognitionTools` never calls `EventBus` | Processing isolation |
| Feature extraction method must match between training and inference | Enforced by `model.feature_method` check |

---

## 24. Future Extensions

| Extension | Description | Target |
|---|---|---|
| `cross_validate(X, y, model_type, folds)` | K-fold cross-validation | Unit IX advanced |
| `hyperparameter_search(X, y, model_type, param_grid)` | Grid search | Unit IX advanced |
| `explain_prediction(features, model)` | LIME/SHAP local explanation | Beyond scope |
| `online_learning(model, new_X, new_y)` | Incremental model update at runtime | Beyond scope |
| `neural_net(X, y, layers)` | Simple MLP via scikit-learn | Unit IX extension |
