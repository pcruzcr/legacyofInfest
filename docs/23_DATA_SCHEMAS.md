# Legacy of InFest — Data Schemas

**Document ID:** LOI-SCHEMA-023  
**Version:** 1.0.0  
**Status:** Official  
**Compatibility:** Requires `22_API_CONTRACTS.md`  
**Audience:** AI coding assistants (Claude Code, Cline, OpenCode, Codex)

---

## 1. Purpose

`22_API_CONTRACTS.md` defines function and class **signatures**. This document defines the exact **shape of the data** that flows through those signatures and across files on disk — TMX object properties, event payloads, dataset files, serialized models, and configuration files. Where `22_API_CONTRACTS.md` says `dict[str, Any]` or `**kwargs`, this document says exactly which keys are valid and what they mean.

---

## 2. EventBus Payload Schemas

Every event in the system, with its exact `**data` keys, types, and emission/consumption rules. This expands `22_API_CONTRACTS.md` §2.3 into a complete reference.

| Event | Payload Schema | Emitted By | Consumed By |
|---|---|---|---|
| `PLAYER_DAMAGED` | `{amount: float, source: tuple[float, float]}` | `Player.apply_damage()` | `HUD`, `AudioManager` |
| `PLAYER_HEALED` | `{amount: float}` | `Checkpoint` (on respawn restore) | `Player`, `HUD` |
| `PLAYER_DIED` | `{}` | `Player.apply_damage()` (health reaches 0) | `SceneManager` (pushes GameOverScene) |
| `CHECKPOINT_REACHED` | `{checkpoint_id: int}` | `Checkpoint.update()` | `StageLoader` (updates respawn anchor) |
| `ENEMY_DIED` | `{entity_id: str, position: tuple[float, float]}` | `EnemyBase._die()` | Stage (loot/score logic), `AudioManager` |
| `STAGE_COMPLETE` | `{}` | `NextTrigger` collision check (stage code) or boss defeat sequence | `SceneManager` (advances scene) |
| `BOSS_PHASE_CHANGED` | `{phase: int}` | `BossBase._begin_phase_transition()` | Boss HUD element, stage code |
| `SHOW_MESSAGE` | `{text: str, duration: float}` | Stage code (Message trigger zone) | `MessageBox` |
| `HIDE_MESSAGE` | `{}` | Stage code | `MessageBox` |

**Rule:** `entity_id` in `ENEMY_DIED` is a string, not an object reference — typically `f"{type(self).__name__}_{id(self)}"` or a TMX object name if available. Never pass a live entity object through the EventBus; payloads must be plain data (str, float, int, tuple) to avoid lifecycle coupling.

---

## 3. TMX Object Property Schemas

This expands `06_TMX_SPEC.md` §6 into exact property dictionaries as `StageLoader` will receive them from `pytmx`. All property values arrive from `pytmx` already type-coerced according to the `type` attribute set in Tiled (`int`, `float`, `bool`, `string`).

### 3.1 `PlayerSpawn`

```python
{
    # No custom properties required.
}
```

### 3.2 `Walker`

```python
{
    "patrol_length": int,      # default 96 if absent
    "facing": str,              # "left" | "right", default "right"
    "patrol_speed": float,      # default 45.0
    "alert_speed": float,       # default 75.0
    "damage_on_contact": float, # default 0.5
}
```

### 3.3 `Flying`

```python
{
    "flight_mode": str,         # "sine" | "bezier" | "patrol", default "sine"
    "flight_speed": float,      # default 60.0
    "sine_amplitude": float,    # default 28.0, only used if flight_mode == "sine"
    "sine_frequency": float,    # default 1.5, only used if flight_mode == "sine"
    # "owner_id" appears on linked Waypoint objects, NOT on the Flying object itself.
}
```

### 3.4 `Shooter`

```python
{
    "fire_rate": float,            # default 0.5
    "projectile_speed": float,     # default 120.0
    "projectile_damage": float,    # default 0.5
    "patrol_length": int,          # default 0 (stationary)
}
```

### 3.5 `Checkpoint`

```python
{
    "checkpoint_id": int,   # REQUIRED, no default — StageLoader raises FrameworkUsageError if absent
}
```

### 3.6 `Message`

```python
{
    "text": str,            # REQUIRED. May contain literal "\n" for line breaks.
    "duration": float,      # REQUIRED. 0.0 means manual dismiss (wait for CONFIRM).
    "trigger_once": bool,   # default True
}
```

### 3.7 `Waypoint`

```python
{
    "owner_id": str,            # REQUIRED. Must match the `name` of a Flying object in the same map.
    "waypoint_index": int,      # REQUIRED. 0-based; waypoints sorted ascending by this value.
}
```

### 3.8 `HazardZone`

```python
{
    "damage": float,         # REQUIRED
    "damage_type": str,      # free-text label, e.g. "spike", "floor_spikes" — cosmetic/SFX hint only
}
```

### 3.9 `CameraLock`

```python
{
    "lock_x": bool,   # default False
    "lock_y": bool,   # default False
}
```

### 3.10 `BossSpawn`

```python
{
    "boss_id": str,   # REQUIRED. Must match a key in the boss factory registry (see §3.11).
}
```

### 3.11 Entity Factory Registration Table

This is the canonical mapping `StageLoader.register_entity()` calls must establish before any TMX is loaded. AI assistants implementing `app.py` or a stage's `on_enter()` must register exactly these names:

```python
StageLoader.register_entity("Walker", EnemyWalker)
StageLoader.register_entity("Flying", EnemyFlying)
StageLoader.register_entity("Shooter", EnemyShooter)
StageLoader.register_entity("Checkpoint", Checkpoint)
# Boss entries registered per-assignment, e.g.:
StageLoader.register_entity("BossVenado", BossVenado)
```

Student-authored custom entities register additional names following the same pattern — see `26_STUDENT_TEMPLATE_SPEC.md` §5.

---

## 4. Processing Module Data Structures

### 4.1 `ComponentResult` (VisionTools)

Already typed in `22_API_CONTRACTS.md` §14.1. Field semantics:

| Field | Shape/Type | Notes |
|---|---|---|
| `label_array` | `np.ndarray`, `int32`, `(H, W)` | `0` = background; `1..N` = component labels |
| `num_components` | `int` | Count of distinct non-zero labels |
| `component_sizes` | `dict[int, int]` | `{label_id: pixel_count}`, all labels 1..N present as keys |
| `label_surface` | `pygame.Surface` | RGB, same `(W, H)` as input; each label gets a distinct hue from an 8-color palette, cycling if `num_components > 8` |

### 4.2 `RegionInfo` (VisionTools)

| Field | Type | Range/Notes |
|---|---|---|
| `label` | `int` | Matches a key in the originating `ComponentResult.component_sizes` |
| `area` | `int` | Pixel count, > 0 |
| `centroid` | `tuple[float, float]` | `(x, y)` in pixel coordinates, image space (not world space — caller must offset) |
| `bounding_rect` | `pygame.Rect` | Axis-aligned, in the same coordinate space as the input surface |
| `eccentricity` | `float` | `[0.0, 1.0]`; 0 = circle, approaching 1 = line |
| `solidity` | `float` | `(0.0, 1.0]`; area / convex_hull_area |
| `perimeter` | `float` | Pixel units, > 0 |

### 4.3 `TrainedModel` (PatternRecognitionTools)

| Field | Type | Notes |
|---|---|---|
| `model_type` | `str` | One of `"knn"`, `"tree"`, `"forest"`, `"svm"` — no other values valid |
| `estimator` | `sklearn.pipeline.Pipeline` | Always `Pipeline([("scaler", StandardScaler()), ("classifier", <estimator>)])` — never a bare estimator |
| `classes` | `list[str]` | Sorted unique values from training `y`, cast to `str` |
| `feature_method` | `str` | One of `"hog"`, `"lbp"`, `"color_hist"`, `"combined"`, `"external"` |
| `feature_length` | `int` | Must match the second dimension of any `X` passed to `classify()` |
| `training_accuracy` | `float` | `[0.0, 1.0]` |
| `metadata` | `dict[str, Any]` | Free-form; **must** include `"kwargs"` (the hyperparameters dict passed to `train()`); **should** include `"evaluation"` holding the serialized `EvaluationResult` if `evaluate()` was run before saving (see §4.4 for the exact sub-schema, required for `PatternDemoScene` Mode 3 — Confusion) |

### 4.4 `EvaluationResult` Embedding Convention

When a `TrainedModel.metadata["evaluation"]` key is present, it must follow this exact sub-schema so `PatternDemoScene` (see `15_ACADEMIC_DEMO_SCENES.md` §5.7) can render it without special-casing:

```python
metadata["evaluation"] = {
    "accuracy": float,                      # mirrors EvaluationResult.accuracy
    "per_class_accuracy": dict[str, float],
    "confusion_matrix": list[list[int]],    # JSON/pickle-safe nested list, NOT np.ndarray
    "report": str,
    "test_set_size": int,                   # len(y_test) at evaluation time
}
```

**Note:** `confusion_matrix` is stored as a nested `list[list[int]]` inside `metadata` (pickle-safe and human-inspectable) even though `EvaluationResult.confusion_matrix` itself is a live `np.ndarray` at runtime. Convert with `.tolist()` before storing, `np.array(...)` after loading if matrix operations are needed.

---

## 5. Dataset File Format (`.npz`)

### 5.1 Structure

Per `13_PATTERN_RECOGNITION_SPEC.md` §8.3, all datasets are NumPy compressed archives with exactly two arrays:

```python
np.savez(path, X=X, y=y)

# X.shape == (n_samples, n_features), dtype == np.float32
# y.shape == (n_samples,), dtype == '<U...' (numpy unicode string) or object
```

### 5.2 Loading Convention

```python
data = np.load(path)
X: np.ndarray = data["X"].astype(np.float32)   # always re-cast defensively
y: np.ndarray = data["y"]
```

### 5.3 Sample Dataset Specification (Professor-Provided)

`assets/datasets/sample_dataset.npz` — required by Phase 12 of `25_IMPLEMENTATION_ROADMAP.md` and by `PatternDemoScene`'s default-loaded model:

| Property | Value |
|---|---|
| `n_samples` | 90 |
| `n_features` | 512 (HOG on 32×32 canonical resize) |
| Classes | `"dark_zone"`, `"neutral"`, `"light_zone"` — exactly 30 samples each |
| Source | Synthetically generated or screenshot-derived 32×32 surface crops, brightness-stratified into the three classes by mean luminance threshold |

### 5.4 Student Dataset Minimum Requirements

Per `13_PATTERN_RECOGNITION_SPEC.md` §8.1, restated as a hard schema check an AI assistant's `tools/build_dataset.py` must enforce:

```python
assert X.shape[0] == y.shape[0]
assert X.shape[0] >= 10
assert X.dtype == np.float32
assert len(set(y.tolist())) >= 2
for class_label in set(y.tolist()):
    assert (y == class_label).sum() >= 10  # min samples per class
```

---

## 6. Model File Format (`.pkl`)

### 6.1 Serialization

```python
import joblib
joblib.dump(trained_model_dataclass_instance, path)  # path: *.pkl
```

The entire `TrainedModel` dataclass instance is serialized — not just the sklearn estimator. This is why `load_model()` returns a `TrainedModel`, not a bare estimator (see `22_API_CONTRACTS.md` §15.1).

### 6.2 File Location Convention

| Context | Path |
|---|---|
| Professor sample model | `assets/models/professor_sample.pkl` |
| Student assignment model | `src/stages/<student_assignment>/models/<name>.pkl` |

**Note:** This corrects the path convention from earlier drafts of `13_PATTERN_RECOGNITION_SPEC.md` (which referenced `student_assets/models/`) to match the `src/`-relocated repository structure defined in `00_SYLLABUS_ALIGNMENT_AUDIT.md` §7. A student's model lives inside their own assignment folder, not a separate top-level directory.

---

## 7. Stage README Front-Matter Schema

Every stage/boss `README.md` (whether `stage0/README.md` or a student assignment's `README.md`) must begin with this exact YAML front-matter block, so tooling (and the professor's grading scripts, if any are built later) can parse metadata without NLP:

```yaml
---
assignment_type: stage | boss
assignment_name: "La Soda"          # human-readable name
assignment_id: "stage1_2_la_soda"   # must match the src/stages/<folder> name
zone: 1 | 2 | 3 | final
student_name: "Jane Doe"             # omit or set to "professor" for Stage 0 / unclaimed bosses
units_demonstrated: [II, III, IV, V]  # syllabus units, updated as milestones progress
evaluation_milestone: "Evaluación Práctica I" | "Evaluación Práctica II" | "Evaluación Práctica III"
---
```

Followed by free-form Markdown documenting the academic concepts per `02_CODEX_CONTEXT.md` §9 (student responsibility #6).

---

## 8. `KNOWN_GAPS.md` Entry Schema

Per `25_IMPLEMENTATION_ROADMAP.md` §19, any unresolved `TODO`/`NotImplementedError` must be logged at repo root in `KNOWN_GAPS.md` using this exact entry format so entries are scriptable/greppable:

```markdown
## [GAP-001] <short title>

- **File:** `src/path/to/file.py`
- **Phase:** <roadmap phase number where this was deferred>
- **Reason:** <why this is intentionally incomplete>
- **Resolution plan:** <when/how this gets resolved, or "N/A — out of scope">
```

---

## 9. Dependency Version Pin Table

`requirements.txt` must pin exact or compatible-release versions to guarantee reproducibility across the professor's machine, student machines, and any AI coding assistant's sandboxed execution environment. Exact pins are determined at first successful `pip install` and then locked — the table below specifies the **constraint operator convention**, not literal version numbers (which an AI assistant should fill in from the environment's actual resolved versions at Phase 0):

```
pygame-ce~=2.5          # compatible release: 2.5.x
numpy~=1.26
scipy~=1.13
opencv-python~=4.10
scikit-image~=0.24
scikit-learn~=1.5
Pillow~=10.4
pytmx~=3.32
pyscroll~=2.31
pytweening~=1.2
joblib~=1.4
matplotlib~=3.9
```

**Note on Matplotlib:** Flagged in `00_SYLLABUS_ALIGNMENT_AUDIT.md` §3 B.3 as a syllabus-mandated library with no defined integration point at the time of that audit. It is pinned here for installation completeness. Its concrete usage (training-report plots, confusion-matrix visualization in `tools/build_dataset.py` output, etc.) remains an open item — log it in `KNOWN_GAPS.md` if Phase 12 of the roadmap is completed without a Matplotlib call site being implemented.

---

## 10. Coordinate Space Conventions

A recurring source of bugs in 2D game code is inconsistent coordinate space assumptions. This table is the single disambiguation reference:

| Space | Origin | Used By | Conversion |
|---|---|---|---|
| **World space** | Top-left of the TMX map (0,0) | `BaseEntity.position`, `StageData.collision_rects`, `Camera.follow` target | — |
| **Screen space** | Top-left of the 320×224 internal surface | `HUD`, `MessageBox`, `ScreenBanner`, anything drawn without `camera_offset` | `screen = world - camera.offset` |
| **Local entity space** | Top-left of the entity's own sprite frame | `EnemyBase._build_hitbox()`, `_build_hurtbox()` return values | `world = entity.position + local_offset` |
| **TMX pixel space** | Top-left of the Tiled map, in pixels (matches World space 1:1) | Raw `pytmx` object `.x`/`.y` values | Identical to World space — no conversion needed |
| **Surface-local array space** | Top-left of a `pygame.Surface`/`np.ndarray` being processed | All `FilterTools`/`VisionTools` inputs/outputs | Caller's responsibility to blit at the correct world/screen offset after processing |

**Rule for `RegionInfo.centroid` and `.bounding_rect`:** These are always in the coordinate space of the surface that was passed into `VisionTools.analyze_regions()` — if the caller passed a `subsurface()` cropped from world space, the caller must add the subsurface's offset back before treating the result as a world-space position.
