---
document_id: "LOI-ROADMAP-025"
title: "Legacy of InFest — Implementation Roadmap"
aliases: ["Implementation Roadmap"]
tags: ["implementation", "roadmap", "build"]
description: "16-phase build order with Definition of Done"
source: "docs/25_IMPLEMENTATION_ROADMAP.md"
date_processed: "2026-07-14"
---

# Legacy of InFest — Implementation Roadmap

**Document ID:** LOI-ROADMAP-025  
**Version:** 1.1.0  
**Status:** Official  
**Compatibility:** Requires all prior LOI documents (00–21)  
**Audience:** Professor, AI coding assistants (Claude Code, Cline, OpenCode, Codex)

---

## 1. Purpose

This document tells an AI coding assistant **exactly what to build, in what order, and how to know when each piece is done.** The other 24 documents describe *what the system should be*. This document describes *the sequence of work that gets there* without breaking dependencies, without producing dead code, and without requiring rework.

**Rule for AI assistants:** Do not start any phase before the previous phase's Definition of Done is fully satisfied. Do not implement a module out of order even if it looks simple — later modules assume earlier ones exist and behave exactly as specified.

---

## 2. Build Order Overview

```
PHASE 0   Repository scaffold, settings, dependency install
PHASE 1   Engine Core        (app, clock, event_bus, settings)
PHASE 2   Engine Input/Audio/Utils
PHASE 3   Engine Scene system + Scene stack
PHASE 4   Engine UI (HUD, MessageBox, ScreenBanner)
PHASE 5   Framework Entities (BaseEntity, Player)
PHASE 6   Framework Entities (Enemy templates)
PHASE 7   Framework Stage (Camera, Checkpoint, StageLoader)
PHASE 8   Framework Processing — ColorTools, CurveTools
PHASE 9   Stage 0 (full implementation, all 7 zones)
PHASE 10  Framework Processing — FilterTools (Unit VII)
PHASE 11  Framework Processing — VisionTools (Unit VIII)
PHASE 12  Framework Processing — PatternRecognitionTools (Unit IX)
PHASE 13  Academic Demo Scenes (Filter/Vision/Pattern)
PHASE 14  Interactive Theory Labs (Vector/Collision/Color/Curve) ← NEW
PHASE 15  Framework Entities — BossBase + one reference boss (El Venado Sagrado)
PHASE 16  student_templates/ scaffolding
PHASE 17  Full regression pass + tooling (validate_assets.py, build_dataset.py)
```

Each phase is gated: its Definition of Done (DoD) must be met before the next phase begins. Phases 10–12 may be parallelized across separate AI sessions **only if** Phase 9 is already complete, since all three depend on Stage 0 existing as an integration smoke-test target.

---

## 3. Phase 0 — Repository Scaffold

**Goal:** A repository that matches `00_SYLLABUS_ALIGNMENT_AUDIT.md` §7 exactly, with all directories present (even if empty) and dependencies installable.

**Tasks:**
1. Create the full directory tree from `00_SYLLABUS_ALIGNMENT_AUDIT.md` §7 (the `src/`-relocated structure).
2. Create `requirements.txt` per `10_LIBRARIES_AND_DEPENDENCIES.md` §13, with version pins (see `23_DATA_SCHEMAS.md` §9 for the pinned version table).
3. Create `src/engine/__init__.py`, `src/framework/__init__.py`, and all subpackage `__init__.py` files (empty, just to make packages importable).
4. Create `main.py` with a placeholder that imports nothing yet but exits cleanly (`print("Legacy of InFest — scaffold only"); sys.exit(0)`).
5. Verify `pip install -r requirements.txt` succeeds in a clean virtual environment.

**Definition of Done:**
- [ ] Directory tree matches the corrected structure exactly (diff against `00_SYLLABUS_ALIGNMENT_AUDIT.md` §7).
- [ ] `pip install -r requirements.txt` exits 0.
- [ ] `python main.py` exits 0 with no import errors.
- [ ] No module outside `src/` contains executable game logic.

---

## 4. Phase 1 — Engine Core

**Builds:** `src/engine/core/settings.py`, `clock.py`, `event_bus.py`, `app.py`

**Reference documents:** `03_ARCHITECTURE.md` §2.1, §6; `22_API_CONTRACTS.md` §2

**Order within phase:**
1. `settings.py` first — every other module imports constants from here. No logic, only declarations.
2. `event_bus.py` second — zero dependencies on other engine modules.
3. `clock.py` third — depends only on `pygame.time.Clock`.
4. `app.py` last — depends on all three above plus stub imports for `SceneManager`, `InputManager`, `AudioManager` (which do not exist yet — use placeholder classes with `pass` bodies so `app.py` is syntactically complete but not yet functional).

**Definition of Done:**
- [ ] `settings.py` contains every constant listed in `03_ARCHITECTURE.md` §2.1's table, with no additional undocumented constants.
- [ ] `EventBus.subscribe/unsubscribe/emit` match `22_API_CONTRACTS.md` §2.3 exactly.
- [ ] `DeltaClock.tick()` returns a `float` and never raises on the first call (no division by zero on first-frame delta).
- [ ] `App.__init__` creates the internal 320×224 surface and a scaled window surface per `settings.DISPLAY_SCALE`.
- [ ] Unit tests: `tests/test_event_bus.py`, `tests/test_clock.py` — both passing (see `24_TEST_PLAN.md` §3).
- [ ] `python main.py` still exits 0 (App is constructed but `run()` is not yet called from `main.py`).

---

## 5. Phase 2 — Engine Input / Audio / Utils

**Builds:** `src/engine/input/`, `src/engine/audio/`, `src/engine/utils/`

**Reference documents:** `03_ARCHITECTURE.md` §2.3, §2.4, §2.6; `22_API_CONTRACTS.md` §3, §4, §5

**Order within phase:**
1. `engine/utils/math_utils.py` — zero dependencies, needed by almost everything downstream.
2. `engine/utils/asset_loader.py` — depends only on `pygame` and `settings.ASSETS_DIR`.
3. `engine/utils/spritesheet.py` — depends on `asset_loader`.
4. `engine/input/action_map.py` — declares the default binding table from `03_ARCHITECTURE.md` §2.3.
5. `engine/input/input_manager.py` — depends on `action_map`.
6. `engine/audio/sound_bank.py` — depends on `asset_loader`.
7. `engine/audio/audio_manager.py` — depends on `sound_bank`.

**Definition of Done:**
- [ ] All math_utils functions in `22_API_CONTRACTS.md` §5 implemented with matching signatures.
- [ ] `AssetLoader` caches by absolute path string; loading the same path twice returns the same object (`is` identity check passes in tests).
- [ ] `InputManager.is_action_pressed/held/released` all implemented and distinguish pressed-this-frame from held.
- [ ] `AudioManager.play_music`/`play_sfx` do not raise when `assets/music/` or `assets/sfx/` files referenced do not yet exist (graceful fallback: log warning, do not crash) — **this fallback exists only during early development and must be removed/tightened once Phase 9 assets are in place** (tracked as a Phase 16 cleanup item).
- [ ] Unit tests: `tests/test_math_utils.py`, `tests/test_asset_loader.py`, `tests/test_input_manager.py` — all passing.

---

## 6. Phase 3 — Engine Scene System

**Builds:** `src/engine/scene/base_scene.py`, `scene_manager.py`, `transitions.py`

**Reference documents:** `03_ARCHITECTURE.md` §2.2, §6, §7; `22_API_CONTRACTS.md` §6

**Definition of Done:**
- [ ] `BaseScene` is an `abc.ABC` (or equivalent) with abstract `on_enter`, `on_exit`, `update`, `draw`.
- [ ] `SceneManager.push/pop/replace` correctly call `on_pause`/`on_resume`/`on_enter`/`on_exit` in the right order (see `22_API_CONTRACTS.md` §6.2 sequence diagram).
- [ ] `App.run()` is now wired to call `SceneManager.current.update(dt)` and `.draw(surface)` every frame.
- [ ] A minimal `SplashScene` stub (solid color fill, no assets) can be pushed and the main loop runs without crashing for 5 seconds in a manual smoke test.
- [ ] Unit tests: `tests/test_scene_manager.py` — passing.

---

## 7. Phase 4 — Engine UI

**Builds:** `src/engine/ui/hud.py`, `message_box.py`, `screen_banner.py`

**Reference documents:** `09_HUD_SPEC.md` (full document); `22_API_CONTRACTS.md` §7

**Definition of Done:**
- [ ] `HUD` subscribes to `PLAYER_DAMAGED`, `PLAYER_HEALED`, `PLAYER_DIED` per `09_HUD_SPEC.md` §10 and updates internal state without errors even with no `Player` instance present yet (defensive coding — HUD must not crash if events never fire).
- [ ] Heart rendering algorithm in `09_HUD_SPEC.md` §4.3 implemented exactly (5-slot fractional logic).
- [ ] `MessageBox` typewriter reveal rate matches `09_HUD_SPEC.md` §7.3 (30 chars/sec).
- [ ] `ScreenBanner` slide-in/hold/slide-out timing matches `09_HUD_SPEC.md` §6.3.
- [ ] Unit tests: `tests/test_hud.py` (heart fraction logic at minimum — visual rendering is exempted from automated testing, see `24_TEST_PLAN.md` §2.4).

---

## 8. Phase 5 — Framework Entities: BaseEntity and Player

**Builds:** `src/framework/entities/base_entity.py`, `player.py`

**Reference documents:** `04_PLAYER_SPEC.md` (full document); `22_API_CONTRACTS.md` §8, §9

**Order within phase:**
1. `base_entity.py` first — defines the lifecycle contract every entity (including Player, every Enemy, and every Boss) inherits.
2. `player.py` second — full state machine per `04_PLAYER_SPEC.md` §8.

**Definition of Done:**
- [ ] `BaseEntity.update`/`draw` are abstract; calling them on `BaseEntity` directly raises `NotImplementedError`.
- [ ] Player state machine implements all 9 states in `04_PLAYER_SPEC.md` §8.1 with exact transition rules.
- [ ] Movement matches `04_PLAYER_SPEC.md` §4 exactly: walk speed 90 px/s, gravity 800 px/s², jump force −380 px/s, coyote time 6 frames, jump cut at 0.5× multiplier.
- [ ] Damage system matches §6: three damage tiers (0.25/0.50/1.00), 1.5s invincibility, knockback per §6.3.
- [ ] Attack hitboxes match §10 exactly (frame-by-frame offsets for Long Attack).
- [ ] Hurtbox matches §11 (standard and crouching variants).
- [ ] Unit tests: `tests/test_player_physics.py`, `tests/test_player_state_machine.py`, `tests/test_player_damage.py` — all passing (see `24_TEST_PLAN.md` §4).
- [ ] Manual smoke test: Player can be spawned in a blank scene with a flat floor, walk, jump, crouch, and attack without exceptions.

---

## 9. Phase 6 — Framework Entities: Enemy Templates

**Builds:** `src/framework/entities/enemy_base.py`, `enemy_walker.py`, `enemy_flying.py`, `enemy_shooter.py`

**Reference documents:** `05_ENEMY_SPEC.md` (full document); `22_API_CONTRACTS.md` §10

**Order within phase:**
1. `enemy_base.py` — FSM skeleton (`PATROL`/`ALERT`/`HURT`/`DYING`), detection rule, contact damage.
2. `enemy_walker.py` — patrol + ledge detection.
3. `enemy_flying.py` — sine/Bézier/patrol flight modes (depends on `framework/processing/curve_tools.py` — see Phase 8; if Phase 8 is not yet done, implement sine mode only and stub the Bézier/patrol modes with `NotImplementedError`, then complete after Phase 8).
4. `enemy_shooter.py` — projectile system, `atan2` angle calculation.

**Definition of Done:**
- [ ] `EnemyBase.apply_hit`, `_die`, `_check_player_contact` implemented exactly per `05_ENEMY_SPEC.md` §2.3.
- [ ] Detection zone math matches §2.5 and §10.1 exactly.
- [ ] `EnemyWalker` ledge detection probe matches §3.5's pseudocode.
- [ ] `EnemyFlying` sine mode matches §4.3's formula; Bézier/patrol modes only required once `curve_tools.py` exists.
- [ ] `EnemyShooter` projectile lifecycle matches §5.4 (spawn → update → expire).
- [ ] Unit tests: `tests/test_enemy_walker.py`, `tests/test_enemy_flying.py`, `tests/test_enemy_shooter.py` — passing for all implemented modes.

---

## 10. Phase 7 — Framework Stage System

**Builds:** `src/framework/stage/camera.py`, `checkpoint.py`, `stage_loader.py`

**Reference documents:** `03_ARCHITECTURE.md` §2.8, §8.3; `06_TMX_SPEC.md` (full document); `22_API_CONTRACTS.md` §11

**Order within phase:**
1. `camera.py` — no dependency on TMX; can be built and tested with a hardcoded target.
2. `checkpoint.py` — small, self-contained, depends on `EventBus`.
3. `stage_loader.py` — depends on `pytmx`, `pyscroll`, and the entity factory registration pattern from `03_ARCHITECTURE.md` §8.3.

**Definition of Done:**
- [ ] `Camera.follow`/`update`/`world_to_screen`/`screen_to_world` implemented; parallax factors match `06_TMX_SPEC.md` §3.2 exactly.
- [ ] `Checkpoint` activates once, emits `CHECKPOINT_REACHED` with correct `checkpoint_id`, never re-triggers.
- [ ] `StageLoader.load()` parses all 8 required layers in `06_TMX_SPEC.md` §3.1, raises `FrameworkUsageError` with descriptive message if any required layer or `PlayerSpawn` is missing (§6.1).
- [ ] Entity factory registration (`StageLoader.register_entity`) implemented and used to spawn `Walker`/`Flying`/`Shooter`/`Checkpoint` from TMX objects.
- [ ] A minimal hand-built `.tmx` test fixture (in `tests/fixtures/`) loads without error and produces a `StageData` object with non-empty `collision_rects` and a valid `spawn_point`.
- [ ] Unit tests: `tests/test_stage_loader.py`, `tests/test_camera.py`, `tests/test_checkpoint.py` — passing.

---

## 11. Phase 8 — Framework Processing: ColorTools and CurveTools

**Builds:** `src/framework/processing/color_tools.py`, `curve_tools.py`

**Reference documents:** `03_ARCHITECTURE.md` §2.9; `22_API_CONTRACTS.md` §12

**Definition of Done:**
- [ ] All `ColorTools` conversions (RGB↔HSV↔HSL↔CMYK) round-trip within ±1 unit of error for 1000 random sampled colors (automated property test — see `24_TEST_PLAN.md` §5.1).
- [ ] `ColorTools.alpha_blend` matches the standard formula `out = src*α + dst*(1-α)` exactly.
- [ ] `CurveTools.bezier` produces correct output for known control-point cases (straight line degenerate case, symmetric quadratic case — see `24_TEST_PLAN.md` §5.2 for exact test vectors).
- [ ] `CurveTools.b_spline`, `nurbs`, `catmull_rom` implemented and pass smoke tests (output is a list of `(x,y)` tuples of the requested length, monotonically progressing along the curve).
- [ ] `CurveTools.sample_path` correctly interpolates between pre-sampled points for any `t ∈ [0,1]`.
- [ ] Return to Phase 6: complete `EnemyFlying` Bézier and patrol modes now that `curve_tools.py` exists.
- [ ] Unit tests: `tests/test_color_tools.py`, `tests/test_curve_tools.py` — passing.

---

## 12. Phase 9 — Stage 0 (Full Implementation)

**Builds:** `src/stages/stage0/stage0.py`, `stage0.tmx`, all Stage 0 assets per `20_ASSET_BIBLE.md`

**Reference documents:** `07_STAGE0_DESIGN.md` (full document); `20_ASSET_BIBLE.md` (full document); `09_HUD_SPEC.md`

**This is the first full integration milestone.** Every engine and framework module built in Phases 1–8 is exercised here simultaneously.

**Order within phase:**
1. Build `stage0.tmx` in Tiled following `06_TMX_SPEC.md`, covering Zones A–G exactly as laid out in `07_STAGE0_DESIGN.md` §3.
2. Author or placeholder-source all assets listed for Stage 0 in `20_ASSET_BIBLE.md` §4–§12 (player, neutral enemies, tileset, backgrounds, UI, fonts, music, SFX). **Placeholder assets are acceptable at this phase** (solid-color rectangles sized correctly) — visual polish is not required for DoD; only correct dimensions, frame counts, and file paths matter for the engine to run.
3. Implement `Stage0Scene(BaseScene)` wiring `StageLoader`, `Camera`, `HUD`, `MessageBox`, `ScreenBanner`, and all 27 tutorial messages from `07_STAGE0_DESIGN.md` §4.
4. Wire the full scene flow up to Stage 0: `SplashScene → TitleScene → StoryScene1-3 → Stage0Scene` (Title and Story scenes may be minimal placeholders at this phase — full polish is a Phase 16 item).

**Definition of Done:**
- [ ] All 7 zones (A–G) are present and traversable start to finish without exceptions.
- [ ] All 27 tutorial messages trigger at the correct X positions and display correctly.
- [ ] All 5 checkpoints function (activate once, restore on death).
- [ ] Master systems checklist in `07_STAGE0_DESIGN.md` §10 — every row confirmed working in a manual playthrough.
- [ ] `NextTrigger` correctly fires `STAGE_COMPLETE`.
- [ ] Debug overlay (F1) renders hitboxes/hurtboxes/detection zones without crashing.
- [ ] No console errors or warnings during a full playthrough.
- [ ] This phase is the **reference smoke test** for everything that follows — Phases 10–14 must re-run this playthrough after their changes to confirm no regression.

---

## 13. Phase 10 — FilterTools (Unit VII)

**Builds:** `src/framework/processing/filter_tools.py`

**Reference documents:** `11_FILTER_TOOLS_SPEC.md` (full document); `22_API_CONTRACTS.md` §13

**Definition of Done:**
- [ ] All 9 public methods in `11_FILTER_TOOLS_SPEC.md` §8 implemented with exact signatures from `22_API_CONTRACTS.md` §13.
- [ ] All 9 standard kernels in §9.2 hardcoded exactly as specified (values, not approximations).
- [ ] Input validation per §11 raises the exact exception types and message patterns specified.
- [ ] Performance: each operation meets the timing budget in §13.1 for a 320×224 surface (benchmark test, not a hard CI gate, but logged).
- [ ] Unit tests: `tests/test_filter_tools.py` with saved PNG output to `tests/output/filter/` for each of the 9 operations (see `24_TEST_PLAN.md` §6).
- [ ] Re-run Stage 0 smoke test (Phase 9 DoD) — no regression.

---

## 14. Phase 11 — VisionTools (Unit VIII)

**Builds:** `src/framework/processing/vision_tools.py`

**Reference documents:** `12_VISION_TOOLS_SPEC.md` (full document); `22_API_CONTRACTS.md` §14

**Definition of Done:**
- [ ] All public methods in `12_VISION_TOOLS_SPEC.md` §6 class diagram implemented with exact signatures.
- [ ] `ComponentResult` and `RegionInfo` data structures match `23_DATA_SCHEMAS.md` §4 field-for-field.
- [ ] `threshold_otsu` returns both the mask surface and the computed integer threshold (tuple, not just the surface).
- [ ] `analyze_regions` returns a list sorted by area descending, exactly as specified.
- [ ] `extract_hog`/`extract_lbp`/`extract_color_histogram` produce vectors of the exact documented lengths (512 / 256 / `bins*3`).
- [ ] Unit tests: `tests/test_vision_tools.py` with saved PNG output to `tests/output/vision/`.
- [ ] Re-run Stage 0 smoke test — no regression.

---

## 15. Phase 12 — PatternRecognitionTools (Unit IX)

**Builds:** `src/framework/processing/pattern_recognition_tools.py`, `tools/build_dataset.py`

**Reference documents:** `13_PATTERN_RECOGNITION_SPEC.md` (full document); `22_API_CONTRACTS.md` §15; `23_DATA_SCHEMAS.md` §5

**Definition of Done:**
- [ ] `train()` implemented for all 4 classifier types (`knn`, `tree`, `forest`, `svm`) with the embedded `StandardScaler` Pipeline pattern from §9.1.
- [ ] `evaluate()` returns a complete `EvaluationResult` (accuracy, per-class accuracy, confusion matrix, report string).
- [ ] `save_model()`/`load_model()` round-trip correctly: a model saved and reloaded produces identical predictions on the same input.
- [ ] `classify()`/`classify_proba()`/`predict()` implemented; `predict()` correctly delegates to `VisionTools.extract_features()`.
- [ ] Model Registry (`register_model`/`get_model`/`list_models`) implemented as in-memory dict, not persisted.
- [ ] `tools/build_dataset.py` produces a valid `.npz` per `23_DATA_SCHEMAS.md` §5.1 from a directory of labeled images.
- [ ] `assets/datasets/sample_dataset.npz` generated: 90 samples, 3 classes (`dark_zone`, `neutral`, `light_zone`), per `15_ACADEMIC_DEMO_SCENES.md` §5.16.
- [ ] `assets/models/professor_sample.pkl` trained and saved (k-NN, k=5) on the sample dataset.
- [ ] Unit tests: `tests/test_pattern_recognition_tools.py` covering train/evaluate/save/load/classify round trip for all 4 classifiers.
- [ ] Re-run Stage 0 smoke test — no regression.

---

## 16. Phase 13 — Academic Demo Scenes

**Builds:** `src/engine/scenes/demo_menu_scene.py`, `filter_demo_scene.py`, `vision_demo_scene.py`, `pattern_demo_scene.py`

**Reference documents:** `15_ACADEMIC_DEMO_SCENES.md` (full document); `22_API_CONTRACTS.md` §16

**Prerequisite:** Phases 10, 11, and 12 must all be complete (Demo Scenes exercise all three processing modules).

**Definition of Done:**
- [x] `DemoMenuScene` navigates to all three demos and back to `TitleScene`.
- [x] `FilterDemoScene`: all 9 modes from §3.3 functional, including live histogram bars and kernel matrix text display.
- [x] `VisionDemoScene`: all 10 modes from §4.3 functional, including HOG cell visualization and watershed pre-computation (not per-frame).
- [x] `PatternDemoScene`: all 5 modes from §5.3 functional, including the `L`-key model loader text input and probability bars.
- [x] Frame throttling pattern from §8.1 implemented for all expensive operations (no mode drops below 30 FPS on the reference development machine).
- [x] `S` key save-to-PNG works in all three demo scenes, writing to `tests/output/demo/`.
- [x] Manual smoke test: each demo scene run for 60 seconds with all modes cycled — no crashes.

---

## 17. Phase 14 — Interactive Theory Lab Scenes (Units II–VIII)

**Builds:** `src/engine/scenes/vector_lab_scene.py`, `transform_lab_scene.py`, `collision_lab_scene.py`, `color_theory_scene.py`, `curve_editor_scene.py`, `interpolation_lab_scene.py`, `noise_lab_scene.py`

**Reference documents:** `15_ACADEMIC_DEMO_SCENES.md` (full document — v1.2)

**Prerequisite:** Phases 8 (CurveTools, ColorTools) and 5 (Player physics/collision). Demos use engine infrastructure from Phases 1–3.

### Phase 14.1 — VectorLabScene (Unit II — Vectors)
Interactive laboratory for vector arithmetic, normalization, dot product, pursuit movement. Modes: FREE MOVE, CHASE (normalized), ORBIT (dot product), DISTANCE CHECK. Students see normalized vectors, dot products, and angles in real time.

**Definition of Done:**
- [x] Two draggable/controllable points (Player + Enemy) rendered as circles.
- [x] Vector AB arrow drawn from Enemy to Player with arrow head.
- [x] Mode 0 (FREE MOVE): both points move via keyboard independent of vector math.
- [x] Mode 1 (CHASE): Enemy moves toward Player using `vec2_normalize()`.
- [x] Mode 2 (ORBIT): manual control with dot product readout.
- [x] Math info panel shows: vector components, length, normalized form, dot product, angle.
- [x] `N` key toggles normalized vector display.
- [x] `TAB` cycles modes, `R` resets positions, `ESC` returns to menu.
- [x] No crash on draw with any mode combination.

### Phase 14.2 — CollisionLabScene (Unit VI — AABB Collision)
Interactive laboratory demonstrating axis-separated collision resolution. Three modes: NO COLLISION, Y-FIRST (the wall-climb bug from GAP-005), X-FIRST (correct). Teaches why `prev_bottom <= tile.top + 1` matters.

**Definition of Done:**
- [x] Three resolution modes cycled via `TAB`.
- [x] Simple test level with platforms, a wall gap, and one-way platform.
- [x] Y-first mode shows the wall-climb bug when walking into a wall.
- [x] X-first (axis-separated) mode resolves correctly.
- [x] `B` key auto-demonstrates the wall-climb bug in Y-first mode.
- [x] Collision info overlay shows prev_bottom, velocity, grounded state.
- [x] One-way platform collision works in X-first mode.
- [x] Gravity, jumping, and grounded detection implemented.
- [x] `R` resets player position, `ESC` returns to menu.

### Phase 14.3 — ColorTheoryScene (Unit V — Color Spaces)
Interactive laboratory for RGB, HSV, HSL, CMYK color spaces and alpha blending. Shows step-by-step conversion algorithms, not just final values. Includes a "Achieve the target color" challenge exercise.

**Definition of Done:**
- [x] Mode 0 (RGB Explorer): R/G/B sliders with live color swatch and hex readout.
- [x] Mode 1 (HSV Explorer): H/S/V sliders. `SHIFT` toggles step-by-step conversion algorithm display (RGB→HSV).
- [x] Mode 2 (HSL Explorer): H/S/L sliders. `SHIFT` toggles step-by-step conversion display (RGB→HSL).
- [x] Mode 3 (CMYK Explorer): C/M/Y/K sliders with live RGB preview.
- [x] Mode 4 (Alpha Blend): Two-layer blending with alpha slider. Formula `out = src*a + dst*(1-a)` displayed with live values.
- [x] Mode 5 (Challenge): Random target color displayed. Student adjusts RGB sliders to match. `SPACE` submits; diff score shown.
- [x] All space readouts (HSV, HSL, CMYK) shown simultaneously in each mode.
- [x] `TAB` cycles modes, `R` resets / new challenge, `ESC` returns to menu.

### Phase 14.4 — CurveEditorScene (Unit III — Bézier Curves & Splines)
Interactive curve editor with draggable control points. Supports quadratic/cubic/high-degree Bézier, Catmull-Rom spline, B-Spline. Step-by-step de Casteljau animation mode.

**Definition of Done:**
- [x] Six curve modes: BEZIER_QUAD, BEZIER_CUBIC, BEZIER_HIGH, CATMULL_ROM, BSPLINE, DE_CASTELJAU.
- [x] Control points draggable with mouse click+drag.
- [x] Curve rendered using `CurveTools.bezier()`, `catmull_rom()`, `b_spline()`.
- [x] Control polygon lines shown behind curve.
- [x] `D` key toggles de Casteljau visualization (modes 0–2): all interpolation levels + final point.
- [x] `+/-` add/remove control points (modes 2, 4).
- [x] `1-5` keys jump directly to modes.
- [x] Grid background for spatial reference.
- [x] Info panel shows degree, point count, mode name.
- [x] `TAB` cycles modes, `R` resets points, `ESC` returns to menu.

### Phase 14.5 — TransformLabScene (Unit II/III — 2D Transformations)
Interactive laboratory for 2D affine transformations: translation, rotation, scaling, shearing, and composite (translate+rotate). Live matrix display toggled with `N`.

**Definition of Done:**
- [x] Five transform modes: TRANSLATE, ROTATE, SCALE, SHEAR, COMPOSITE (translate then rotate).
- [x] Keyboard controls per mode (arrows translate, LEFT/RIGHT rotate/scale/shear).
- [x] Original shape drawn as ghost outline; transformed shape filled.
- [x] Matrix display shows the current 3×3 transformation matrix with live values.
- [x] `N` toggles matrix panel, `R` resets, `TAB` cycles modes.
- [x] Composite mode demonstrates non-commutativity (translate then rotate vs rotate then translate).

### Phase 14.6 — InterpolationLabScene (Unit III/IV — Interpolation & Easing)
Interactive laboratory for linear interpolation, easing functions, and keyframe animation curves.

**Definition of Done:**
- [x] Three modes: LERP (LINEAR), EASING CURVES, KEYFRAME ANIM.
- [x] LERP mode: point A, point B, lerped point with formula and live x/t readout.
- [x] EASING CURVES mode: graph of current easing function (10 functions: Linear, In/Out/InOut Quad, In/Out Cubic, Out Bounce, Out Elastic, In/Out Sine).
- [x] KEYFRAME ANIM mode: animated point traverses 3 keyframes with eased interpolation.
- [x] `UP/DOWN` cycle easing function, `LEFT/RIGHT` adjust t, `SPACE` toggles auto-animation.
- [x] `R` resets, `TAB` cycles display modes.

### Phase 14.7 — NoiseLabScene (Unit V/VIII — Noise & Procedural Generation)
Interactive laboratory for value noise, Perlin noise, and fractal noise with parameter controls.

**Definition of Done:**
- [x] Three noise types: VALUE NOISE, PERLIN NOISE, FRACTAL NOISE.
- [x] Five adjustable parameters: Octaves (1-8), Persistence (0-1), Lacunarity (1-8), Scale (0.005-0.5), Seed (0-9999).
- [x] UP/DOWN cycle selected parameter, LEFT/RIGHT adjust value.
- [x] SPACE randomizes seed for new noise pattern.
- [x] R resets all parameters to defaults.
- [x] Noise map rendered live as grayscale texture.

### Phase 14.8 — Demo Menu Integration
Extend the existing `DemoMenuScene` to include all 10 lab/demo scenes.

**Definition of Done:**
- [x] `DemoMenuScene._options` lists exactly 10 entries: Vector (II), Transform (II/III), Curve (III), Interpolate (III/IV), Color (V), Noise (V/VIII), Collision (VI), Filter (VII), Vision (VIII), Pattern (IX).
- [x] UP/DOWN navigation wraps correctly through 10 options.
- [x] ENTER/CONFIRM navigates to selected scene.
- [x] ESC returns to TitleScene.
- [x] All 10 scenes pass smoke test (import → instantiate → draw → no crash).

### Phase 14.9 — Engine/Infrastructure Improvements

**Builds:** `src/engine/scenes/scene_registry.py`, `param_panel.py`, `demo_layout.py`, `demo_utils.py`, `debug_overlay.py`, `scripts/validate_assets.py`, `scripts/generate_exam.py`; `src/engine/scene/base_scene.py` (params field)

**Definition of Done:**
- [x] `SceneRegistry` (DI Container) replaces the `_try_scene()` elif chain. `register_demo_scenes()` called once in `App.__init__`.
- [x] `ParamPanel` widget with `add_int()`/`add_float()`/`handle_input()`/`draw()` for reuse across lab scenes.
- [x] `demo_common.py` split into `demo_layout.py` (layout/draw helpers) + `demo_utils.py` (sources, throttle, save). Legacy re-exports preserved.
- [x] `BaseScene.params: dict[str, Any]` for cross-scene data passing.
- [x] `DebugOverlay` (F3) with FPS, event queue snapshot, and module tree browser (F4/F5/F6).
- [x] `scripts/validate_assets.py` validates fonts, models, maps; exits 0 on success.
- [x] `scripts/generate_exam.py` generates practice exams from 16-question bank (Units II-IX) with `--unit` and `--num-questions` flags.

**Overall Phase 14 DoD:**
- [x] All 7 theory lab scenes implement all documented modes.
- [x] All 10 scenes pass import/instantiate/draw tests in `tests/test_demo_scenes.py`.
- [x] Existing 364 tests all pass.
- [x] Manual smoke test: each scene cycled through all modes for 30 seconds — no crashes.

---

## 18. Phase 15 — BossBase and Reference Boss

**Builds:** `src/framework/entities/boss_base.py`, `src/stages/boss_venado/boss_venado.py` (+ TMX arena)

**Reference documents:** `17_BOSS_SPEC.md` §2, §3; `22_API_CONTRACTS.md` §17

**Why El Venado Sagrado specifically:** It is the simplest boss (2 phases, no split-body mechanic, no random branch), making it the correct reference implementation for `BossBase` before any student or the professor attempts the more complex bosses (Rey Terciopelo's split, Gavilán's circular orbit, Paburu's 4-form random branch).

**Definition of Done:**
- [ ] `BossBase` phase transition protocol matches `17_BOSS_SPEC.md` §2.3 exactly (invincibility during transition, `BOSS_PHASE_CHANGED` event, health bar re-fill).
- [ ] Boss HUD element (separate from player HUD) renders per §2.4.
- [ ] El Venado Sagrado Phase 1 and Phase 2 attack patterns implemented exactly per §3.3 (cooldowns, damage values, hitbox dimensions).
- [ ] `STOMP`/`CHARGE`/`VINE_TOSS` (Phase 1) and `VINE_SWEEP`/`MUSHROOM_SPORE` (Phase 2) all functional.
- [ ] Sobel aura visual effect (Unit VII) applied per §3.3 using the now-complete `FilterTools`.
- [ ] Defeat sequence per §3.6 (dissolve, skull, Relic Fragment 1, `STAGE_COMPLETE`).
- [ ] This boss can be reached and fully fought through to defeat from a fresh game launch.
- [ ] Unit tests: `tests/test_boss_base.py` (phase transition logic only — full boss combat is exempted from automated testing per `24_TEST_PLAN.md` §2.4).

---

## 19. Phase 16 — student_templates/ Scaffolding

**Builds:** `student_templates/stage_template/`, `student_templates/boss_template/`

**Reference documents:** `26_STUDENT_TEMPLATE_SPEC.md` (full document — new)

**Definition of Done:** See `26_STUDENT_TEMPLATE_SPEC.md` §8 for the complete checklist. Summary:
- [ ] `stage_template.py` compiles, imports correctly, and produces a loadable (if empty) stage when run standalone.
- [ ] `stage_template.tmx` opens in Tiled without errors and contains all 8 required layers with placeholder content.
- [ ] `boss_template.py` compiles and produces a `BossBase` subclass with one placeholder phase.
- [ ] Both `README_template.md` files contain every section a student must fill in, with inline instructions.
- [ ] A test student (the professor, or a TA) can copy a template, rename it, and have a running (if empty) Stage or Boss within 15 minutes — this is the Class 1 onboarding target from `21_COURSE_SCHEDULE.md`.

---

## 20. Phase 17 — Regression Pass and Tooling

**Builds:** `scripts/validate_assets.py`; final cleanup of all "early development fallback" code paths flagged in earlier phases

**Definition of Done:**
- [ ] `scripts/validate_assets.py` implemented per `10_LIBRARIES_AND_DEPENDENCIES.md` §8.5 (Pillow-based palette validation).
  - **Status update:** initial version created at `scripts/validate_assets.py` (exits 0 on success; validates font loading and model loading).
- [ ] All "graceful fallback" code paths flagged during Phase 2 (missing audio files) are reviewed: either real assets now exist (preferred) or the fallback is intentionally retained and documented as such in code comments.
- [ ] Full test suite (`tests/`) passes with zero failures and zero skips that aren't explicitly justified in `24_TEST_PLAN.md`.
- [ ] Stage 0 full playthrough repeated one final time end-to-end with all final (non-placeholder) assets.
- [ ] `main.py` launches the complete scene flow: Splash → Title → Story 1-3 → Stage 0 → (Boss Venado, if reached via debug skip) without manual intervention.
- [ ] Documentation cross-check: every `TODO` or `NotImplementedError` left in the codebase is either resolved or explicitly listed in a `KNOWN_GAPS.md` file at repo root with a justification (e.g., "El Rey Terciopelo split-body boss is a student/professor assignment, not professor pre-built — intentionally absent").

---

## 21. Phase 18 — Bug Fix and Audit Remediation Session

**Date:** July 2026  
**Applies to:** All prior phases (1–17)  
**Reference documents:** `PHASE_FIX_REPORT.md`, `KNOWN_GAPS.md`, `REMEDIATION_PLAN.md`

**Scope:** Systematic audit and correction of defects found during documentation-driven testing, code audit, and student playthroughs.

### 21.1 fix_plataformas (Gameplay)

| File | Before (regression) | After (fix) |
|---|---|---|
| `player.py` (one-way collision) | Straddle-based detection — entity could be trapped from below | `_prev_foot_y` comparison — only traps if feet came from above |
| `generate_stage0_tmx.py` (collision rect classifier) | Tile type 3 mapped uniformly to `Platform` | Pit cover (2240,176,80,16) → Platform; Zones A/C platforms → Solid |
| `stage0.tmx` | 4 one-way platforms in Zones A/C | All Solid — blocks walking through |
| `test_stage0_platform_solidity.py` | Did not exist | 5 regression tests (369 total, up from 364) |

### 21.2 Crash Bug Fixes (3 commits: 8bd5c1d, e9a37f9, 58311db)

- 14 crash bugs corrected across engine core, entity framework, and stage loading
- ZeroDivisionError guards (division by zero in timing/cooldown calculations)
- None-type guards in sprite loading and collision detection paths

### 21.3 Blurry Text Fix (commit 70df788)

| Asset | Previous Size | New Size |
|---|---|---|
| Font `5x7` (HUD/hearts) | 5×7 px | 5×7 px (unchanged) |
| Font `6x9` (banners) | 6×9 px | 6×15 px |
| Font `7x11` (dialogs) | 7×11 px | 7×18 px |

- Antialiasing enabled on all font rendering
- `SDL_HINT_RENDER_SCALE_QUALITY=0` set at process start

### 21.4 Auditoría Remediation (8 issues)

| # | Issue | Fix |
|---|---|---|
| 1 | Walker `_alert_behavior` lacks ledge detection (floats over pits) | Added same probe/reverse logic as `_patrol_behavior` |
| 2 | No fault isolation in `App.run()` — single `except Exception` wraps entire loop | Individual try/except around scene `update()` and `draw()` per stage |
| 3 | Dual EventBus — no test isolation | Fixture `_reset_eventbus` (autouse) in `conftest.py` |
| 4 | `fire_rate=0` → ALERT→FIRING loop | Both `_alert_behavior` (guards transition) and `_firing_behavior` (min cooldown) |
| 5 | `hasattr(entity, "_boss_name")` duck-typing → `isinstance(entity, BossBase)` | Import `BossBase`, explicit type check; `_completion_fired` initialized in `BossBase.__init__` |
| 6 | `_run_state_machine` docstring omits FIRING priority | `DYING > HURT > FIRING > ALERT > PATROL` |
| 7 | Player invincibility flash uses `1.0/60.0` hardcoded | `self._flash_timer += dt` with configurable period |
| 8 | Missing zone0 zone1 aim/fire sprites | False positive — sprites exist at `assets/sprites/enemies/zone1/` |

### 21.5 Test Count Evolution

| Milestone | Tests |
|---|---|
| End of Phase 17 | 364 |
| After fix_plataformas (5 new regression tests) | 369 |
| After auditoría remediation (no test count change) | 369 (still) |

**Definition of Done:**
- [x] `fix_plataformas` applied to all 4 files; TMX regenerated with 33 collision rects
- [x] 14 crash bugs resolved (3 commits)
- [x] Blurry text fix applied (font sizes, antialiasing, SDL_HINT)
- [x] 8 auditoría remediation items verified against current code
- [x] Full test suite: 369 passed, 0 failures
- [x] Documentation updated across `03_ARCHITECTURE.md` (v1.1.0), `22_API_CONTRACTS.md` (v1.2.0), `15_ACADEMIC_DEMO_SCENES.md` (v1.3.0), `25_IMPLEMENTATION_ROADMAP.md` (v1.1.0), `README.md`

---

## 22. Dependency Graph Summary

```
Phase 0 (scaffold)
    ↓
Phase 1 (core) ──────────────────┐
    ↓                            │
Phase 2 (input/audio/utils)      │
    ↓                            │
Phase 3 (scene system)           │
    ↓                            │
Phase 4 (UI) ◄────────────────────┘ (HUD needs EventBus from Phase 1)
    ↓
Phase 5 (BaseEntity, Player)
    ↓
Phase 6 (Enemies) ──── partial dependency ───► Phase 8 (CurveTools, for Flying Bézier mode)
    ↓                                              ↓
Phase 7 (Stage system) ◄──────────────────────────┘
    ↓
Phase 8 (ColorTools, CurveTools) [if not already done for Phase 6]
    ↓
Phase 9 (STAGE 0 — FIRST FULL INTEGRATION) ◄── requires Phases 1-8 complete
    ↓
    ├──► Phase 10 (FilterTools)
    ├──► Phase 11 (VisionTools)
    └──► Phase 12 (PatternRecognitionTools)
              ↓ (all three required)
          Phase 13 (Academic Demo Scenes VII–IX)
     ↓
Phase 14 (Interactive Theory Labs II–VI)
     ↓   ◄── requires CurveTools/ColorTools (Phase 8) + entity collision (Phase 5)
     ↓
Phase 15 (BossBase + El Venado Sagrado) ◄── requires FilterTools (Phase 10) for Sobel aura
     ↓
Phase 16 (student_templates/)
     ↓
Phase 17 (Regression + Tooling)
     ↓
Phase 18 (Bug fix + Audit remediation)
```

---

## 21. Session Handoff Protocol

Because this roadmap is designed to be executed across multiple AI coding sessions (possibly different tools — Claude Code, Cline, OpenCode, Codex — per the original project brief), each session must:

1. **State which phase it is starting**, referencing this document by phase number.
2. **Confirm the previous phase's DoD checklist** is satisfied before writing new code (re-run tests if uncertain; do not assume).
3. **Not skip ahead** — if a later phase's code would be easier to write first, flag it as a note in `KNOWN_GAPS.md` rather than reordering silently.
4. **Update this document's checkboxes** (or maintain a separate `PROGRESS.md` mirroring this structure) so the next session/tool knows exactly where work left off.

---

## 22. Cross-Reference Index

| Phase | Primary Spec Doc(s) | Contract Doc Section |
|---|---|---|
| 1 | `03_ARCHITECTURE.md` §2.1, §6 | `22_API_CONTRACTS.md` §2 |
| 2 | `03_ARCHITECTURE.md` §2.3-2.4, §2.6 | `22_API_CONTRACTS.md` §3-5 |
| 3 | `03_ARCHITECTURE.md` §2.2 | `22_API_CONTRACTS.md` §6 |
| 4 | `09_HUD_SPEC.md` | `22_API_CONTRACTS.md` §7 |
| 5 | `04_PLAYER_SPEC.md` | `22_API_CONTRACTS.md` §8-9 |
| 6 | `05_ENEMY_SPEC.md` | `22_API_CONTRACTS.md` §10 |
| 7 | `06_TMX_SPEC.md`, `03_ARCHITECTURE.md` §2.8 | `22_API_CONTRACTS.md` §11 |
| 8 | `03_ARCHITECTURE.md` §2.9 | `22_API_CONTRACTS.md` §12 |
| 9 | `07_STAGE0_DESIGN.md`, `20_ASSET_BIBLE.md` | n/a — integration phase |
| 10 | `11_FILTER_TOOLS_SPEC.md` | `22_API_CONTRACTS.md` §13 |
| 11 | `12_VISION_TOOLS_SPEC.md` | `22_API_CONTRACTS.md` §14 |
| 12 | `13_PATTERN_RECOGNITION_SPEC.md` | `22_API_CONTRACTS.md` §15 |
| 13 | `15_ACADEMIC_DEMO_SCENES.md` (original 3 demos VII–IX) | `22_API_CONTRACTS.md` §16 |
| 14 | `15_ACADEMIC_DEMO_SCENES.md` v1.1 (theory labs II–VI) | n/a — teaching extension |
| 15 | `17_BOSS_SPEC.md` §2-3 | `22_API_CONTRACTS.md` §17 |
| 16 | `26_STUDENT_TEMPLATE_SPEC.md` | n/a |
| 17 | All documents | n/a — regression phase |
| 18 | `PHASE_FIX_REPORT.md`, `KNOWN_GAPS.md`, `REMEDIATION_PLAN.md` | n/a — audit with fixes against all prior phases |


---
## 🔗 Documentos Relacionados

- [[30_TICKET_BACKLOG.md|Ticket Backlog]]
- [[24_TEST_PLAN.md|Test Plan]]

---
--- Traducción al Español ---

*This document is also available in English above.*

# Legacy of InFest — Hoja de Ruta de Implementación

**ID del Documento:** LOI-ROADMAP-025
**Versión:** 1.1.0
**Estado:** Oficial
**Compatibilidad:** Requiere todos los documentos LOI anteriores (00 a 21)
**Audiencia:** Profesor, asistentes de codificación IA (Claude Code, Cline, OpenCode, Codex)

---

## 1. Propósito

Este documento le dice a un asistente de codificación IA **exactamente qué construir, en qué orden, y cómo saber cuándo cada pieza está terminada.** Los otros 24 documentos describen *cómo debería ser el sistema*. Este documento describe *la secuencia de trabajo que llega allí* sin romper dependencias, sin producir código muerto, y sin requerir retrabajo.

**Regla para asistentes IA:** No comience ninguna fase antes de que la Definición de Terminado de la fase anterior esté completamente satisfecha. No implemente un módulo fuera de orden incluso si parece simple — los módulos posteriores asumen que los anteriores existen y se comportan exactamente como se especifica.

---

## 2. Resumen del Orden de Construcción

FASE 0   Andamio del repositorio, configuración, instalación de dependencias
FASE 1   Núcleo del Motor (app, clock, event_bus, settings)
FASE 2   Entrada/Audio/Utilidades del Motor
FASE 3   Sistema de Escenas del Motor + Pila de escenas
FASE 4   UI del Motor (HUD, MessageBox, ScreenBanner)
FASE 5   Entidades del Marco (BaseEntity, Player)
FASE 6   Entidades del Marco (Plantillas de enemigos)
FASE 7   Marco del Nivel (Camera, Checkpoint, StageLoader)
FASE 8   Procesamiento del Marco — ColorTools, CurveTools
FASE 9   Nivel 0 (implementación completa, las 7 zonas)
FASE 10  Procesamiento del Marco — FilterTools (Unidad VII)
FASE 11  Procesamiento del Marco — VisionTools (Unidad VIII)
FASE 12  Procesamiento del Marco — PatternRecognitionTools (Unidad IX)
FASE 13  Escenas de Demostración Académica (Filter/Vision/Pattern)
FASE 14  Laboratorios Teóricos Interactivos (Vector/Collision/Color/Curve)
FASE 15  Entidades del Marco — BossBase + un jefe de referencia (El Venado Sagrado)
FASE 16  Andamio de student_templates/
FASE 17  Pase de regresión completo + herramientas (validate_assets.py, build_dataset.py)

Cada fase tiene una puerta: su Definición de Terminado (DoD) debe cumplirse antes de que comience la siguiente fase. Las Fases 10-12 pueden paralelizarse en sesiones IA separadas **solo si** la Fase 9 ya está completa, ya que las tres dependen de que el Nivel 0 exista como objetivo de prueba de humo de integración.

---

## 3. Fase 0 — Andamio del Repositorio

**Objetivo:** Un repositorio que coincida exactamente con 00_SYLLABUS_ALIGNMENT_AUDIT.md sección 7, con todos los directorios presentes (incluso si están vacíos) y dependencias instalables.

**Tareas:**
1. Crear el árbol de directorios completo de 00_SYLLABUS_ALIGNMENT_AUDIT.md sección 7 (la estructura reubicada en src/).
2. Crear requirements.txt según 10_LIBRARIES_AND_DEPENDENCIES.md sección 13, con pines de versión (ver 23_DATA_SCHEMAS.md sección 9 para la tabla de versiones fijadas).
3. Crear src/engine/__init__.py, src/framework/__init__.py, y todos los archivos __init__.py de subpaquetes (vacíos, solo para hacer los paquetes importables).
4. Crear main.py con un placeholder que no importa nada aún pero sale limpiamente (print("Legacy of InFest — scaffold only"); sys.exit(0)).
5. Verificar que pip install -r requirements.txt tenga éxito en un entorno virtual limpio.

**Definición de Terminado:**
- [ ] El árbol de directorios coincide exactamente con la estructura corregida (diff contra 00_SYLLABUS_ALIGNMENT_AUDIT.md sección 7).
- [ ] pip install -r requirements.txt sale con código 0.
- [ ] python main.py sale con código 0 sin errores de importación.
- [ ] Ningún módulo fuera de src/ contiene lógica de juego ejecutable.

---

## 4. Fase 1 — Núcleo del Motor

**Construye:** src/engine/core/settings.py, clock.py, event_bus.py, app.py

**Documentos de referencia:** 03_ARCHITECTURE.md secciones 2.1, 6; 22_API_CONTRACTS.md seccion 2

**Orden dentro de la fase:**
1. settings.py primero — cada otro módulo importa constantes de aquí. Sin lógica, solo declaraciones.
2. event_bus.py segundo — cero dependencias de otros módulos del motor.
3. clock.py tercero — depende solo de pygame.time.Clock.
4. app.py último — depende de los tres anteriores más importaciones stub para SceneManager, InputManager, AudioManager (que aún no existen — use clases placeholder con cuerpos pass para que app.py esté sintácticamente completo pero aún no funcional).

**Definición de Terminado:**
- [ ] settings.py contiene cada constante listada en la tabla de 03_ARCHITECTURE.md seccion 2.1, sin constantes no documentadas adicionales.
- [ ] EventBus.subscribe/unsubscribe/emit coinciden exactamente con 22_API_CONTRACTS.md seccion 2.3.
- [ ] DeltaClock.tick() devuelve un float y nunca lanza en la primera llamada (sin división por cero en delta del primer fotograma).
- [ ] App.__init__ crea la superficie interna de 320x224 y una superficie de ventana escalada según settings.DISPLAY_SCALE.
- [ ] Pruebas unitarias: tests/test_event_bus.py, tests/test_clock.py — ambas pasando (ver 24_TEST_PLAN.md seccion 3).
- [ ] python main.py todavía sale con código 0 (App se construye pero run() aún no se llama desde main.py).

---

## 5. Fase 2 — Entrada / Audio / Utilidades del Motor

**Construye:** src/engine/input/, src/engine/audio/, src/engine/utils/

**Documentos de referencia:** 03_ARCHITECTURE.md secciones 2.3, 2.4, 2.6; 22_API_CONTRACTS.md secciones 3, 4, 5

**Orden dentro de la fase:**
1. engine/utils/math_utils.py — cero dependencias, necesario para casi todo aguas abajo.
2. engine/utils/asset_loader.py — depende solo de pygame y settings.ASSETS_DIR.
3. engine/utils/spritesheet.py — depende de asset_loader.
4. engine/input/action_map.py — declara la tabla de enlace predeterminada de 03_ARCHITECTURE.md seccion 2.3.
5. engine/input/input_manager.py — depende de action_map.
6. engine/audio/sound_bank.py — depende de asset_loader.
7. engine/audio/audio_manager.py — depende de sound_bank.

**Definición de Terminado:**
- [ ] Todas las funciones de math_utils en 22_API_CONTRACTS.md seccion 5 implementadas con firmas coincidentes.
- [ ] AssetLoader almacena en caché por ruta absoluta; cargar la misma ruta dos veces devuelve el mismo objeto.
- [ ] InputManager.is_action_pressed/held/released todos implementados y distinguen presionado-este-fotograma de mantenido.
- [ ] AudioManager.play_music/play_sfx no lanzan cuando los archivos referenciados de assets/music/ o assets/sfx/ aún no existen.
- [ ] Pruebas unitarias: tests/test_math_utils.py, tests/test_asset_loader.py, tests/test_input_manager.py — todas pasando.

---

## 6. Fase 3 — Sistema de Escenas del Motor

**Construye:** src/engine/scene/base_scene.py, scene_manager.py, transitions.py

**Documentos de referencia:** 03_ARCHITECTURE.md secciones 2.2, 6, 7; 22_API_CONTRACTS.md seccion 6

**Definición de Terminado:**
- [ ] BaseScene es un abc.ABC con on_enter, on_exit, update, draw abstractos.
- [ ] SceneManager.push/pop/replace llaman correctamente a on_pause/on_resume/on_enter/on_exit en el orden correcto.
- [ ] App.run() ahora está conectado para llamar a SceneManager.current.update(dt) y .draw(surface) cada fotograma.
- [ ] Un SplashScene stub mínimo se puede empujar y el bucle principal se ejecuta sin fallar por 5 segundos en una prueba de humo manual.
- [ ] Pruebas unitarias: tests/test_scene_manager.py — pasando.

---

## 7. Fase 4 — UI del Motor

**Construye:** src/engine/ui/hud.py, message_box.py, screen_banner.py

**Documentos de referencia:** 09_HUD_SPEC.md (documento completo); 22_API_CONTRACTS.md seccion 7

**Definición de Terminado:**
- [ ] HUD se suscribe a PLAYER_DAMAGED, PLAYER_HEALED, PLAYER_DIED según 09_HUD_SPEC.md seccion 10 y actualiza el estado interno sin errores incluso sin una instancia de Player presente aún.
- [ ] Algoritmo de renderizado de corazones en 09_HUD_SPEC.md seccion 4.3 implementado exactamente.
- [ ] MessageBox tiene una tasa de revelación de máquina de escribir que coincide con 09_HUD_SPEC.md seccion 7.3 (30 caracteres/segundo).
- [ ] El tiempo de deslizamiento-entrada/mantener/deslizamiento-salida de ScreenBanner coincide con 09_HUD_SPEC.md seccion 6.3.
- [ ] Pruebas unitarias: tests/test_hud.py (lógica de fracción de corazón como mínimo).

---

## 8. Fase 5 — Entidades del Marco: BaseEntity y Player

**Construye:** src/framework/entities/base_entity.py, player.py

**Documentos de referencia:** 04_PLAYER_SPEC.md (documento completo); 22_API_CONTRACTS.md secciones 8, 9

**Orden dentro de la fase:**
1. base_entity.py primero — define el contrato de ciclo de vida que cada entidad hereda.
2. player.py segundo — máquina de estados completa según 04_PLAYER_SPEC.md seccion 8.

**Definición de Terminado:**
- [ ] BaseEntity.update/draw son abstractos; llamarlos en BaseEntity directamente lanza NotImplementedError.
- [ ] La máquina de estados del jugador implementa los 9 estados en 04_PLAYER_SPEC.md seccion 8.1 con reglas de transición exactas.
- [ ] El movimiento coincide exactamente con 04_PLAYER_SPEC.md seccion 4: velocidad de caminar 90 px/s, gravedad 800 px/s², fuerza de salto -380 px/s, tiempo coyote 6 fotogramas, corte de salto en multiplicador 0.5x.
- [ ] El sistema de daño coincide con la seccion 6: tres niveles de daño (0.25/0.50/1.00), invencibilidad de 1.5s, retroceso según seccion 6.3.
- [ ] Las hitboxes de ataque coinciden con la seccion 10 exactamente.
- [ ] La hurtbox coincide con la seccion 11.
- [ ] Pruebas unitarias: tests/test_player_physics.py, tests/test_player_state_machine.py, tests/test_player_damage.py — todas pasando.
- [ ] Prueba de humo manual: el jugador puede generarse en una escena en blanco con un suelo plano, caminar, saltar, agacharse y atacar sin excepciones.

---

## 9. Fase 6 — Entidades del Marco: Plantillas de Enemigos

**Construye:** src/framework/entities/enemy_base.py, enemy_walker.py, enemy_flying.py, enemy_shooter.py

**Documentos de referencia:** 05_ENEMY_SPEC.md (documento completo); 22_API_CONTRACTS.md seccion 10

**Orden dentro de la fase:**
1. enemy_base.py — esqueleto FSM (PATROL/ALERT/HURT/DYING), regla de detección, daño de contacto.
2. enemy_walker.py — patrulla + detección de borde.
3. enemy_flying.py — modos de vuelo senoidal/Bézier/patrulla.
4. enemy_shooter.py — sistema de proyectiles, cálculo de ángulo atan2.

**Definición de Terminado:**
- [ ] EnemyBase.apply_hit, _die, _check_player_contact implementados exactamente según 05_ENEMY_SPEC.md seccion 2.3.
- [ ] La zona de detección coincide exactamente con las secciones 2.5 y 10.1.
- [ ] La sonda de detección de borde de EnemyWalker coincide con el pseudocódigo de la seccion 3.5.
- [ ] El modo senoidal de EnemyFlying coincide con la fórmula de la seccion 4.3.
- [ ] El ciclo de vida del proyectil de EnemyShooter coincide con la seccion 5.4 (generar a actualizar a expirar).
- [ ] Pruebas unitarias: tests/test_enemy_walker.py, tests/test_enemy_flying.py, tests/test_enemy_shooter.py — pasando para todos los modos implementados.

---

## 10. Fase 7 — Sistema de Nivel del Marco

**Construye:** src/framework/stage/camera.py, checkpoint.py, stage_loader.py

**Documentos de referencia:** 03_ARCHITECTURE.md secciones 2.8, 8.3; 06_TMX_SPEC.md (documento completo); 22_API_CONTRACTS.md seccion 11

**Orden dentro de la fase:**
1. camera.py — sin dependencia de TMX; puede construirse y probarse con un objetivo codificado.
2. checkpoint.py — pequeño, autocontenido, depende de EventBus.
3. stage_loader.py — depende de pytmx, pyscroll, y el patrón de registro de fábrica de entidades.

**Definición de Terminado:**
- [ ] Camera.follow/update/world_to_screen/screen_to_world implementados; los factores de paralaje coinciden exactamente con 06_TMX_SPEC.md seccion 3.2.
- [ ] Checkpoint se activa una vez, emite CHECKPOINT_REACHED con checkpoint_id correcto, nunca se vuelve a disparar.
- [ ] StageLoader.load() analiza las 8 capas requeridas en 06_TMX_SPEC.md seccion 3.1, lanza FrameworkUsageError si falta alguna capa requerida o PlayerSpawn.
- [ ] El registro de fábrica de entidades implementado y usado para generar Walker/Flying/Shooter/Checkpoint desde objetos TMX.
- [ ] Pruebas unitarias: tests/test_stage_loader.py, tests/test_camera.py, tests/test_checkpoint.py — pasando.

---

## 11. Fase 8 — Procesamiento del Marco: ColorTools y CurveTools

**Construye:** src/framework/processing/color_tools.py, curve_tools.py

**Documentos de referencia:** 03_ARCHITECTURE.md seccion 2.9; 22_API_CONTRACTS.md seccion 12

**Definición de Terminado:**
- [ ] Todas las conversiones de ColorTools (RGB a HSV a HSL a CMYK) viajan de ida y vuelta dentro de +/-1 unidad de error para 1000 colores muestreados aleatoriamente.
- [ ] ColorTools.alpha_blend coincide exactamente con la fórmula estándar out = src*a + dst*(1-a).
- [ ] CurveTools.bezier produce salida correcta para casos conocidos de puntos de control.
- [ ] CurveTools.b_spline, nurbs, catmull_rom implementados y pasan pruebas de humo.
- [ ] CurveTools.sample_path interpola correctamente entre puntos pre-muestreados para cualquier t en [0,1].
- [ ] Volver a la Fase 6: completar los modos Bézier y patrulla de EnemyFlying ahora que curve_tools.py existe.
- [ ] Pruebas unitarias: tests/test_color_tools.py, tests/test_curve_tools.py — pasando.

---

## 12. Fase 9 — Nivel 0 (Implementación Completa)

**Construye:** src/stages/stage0/stage0.py, stage0.tmx, todos los recursos del Nivel 0 según 20_ASSET_BIBLE.md

**Documentos de referencia:** 07_STAGE0_DESIGN.md (documento completo); 20_ASSET_BIBLE.md (documento completo); 09_HUD_SPEC.md

**Este es el primer hito de integración completo.** Cada módulo del motor y marco construido en las Fases 1-8 se ejercita aquí simultáneamente.

**Definición de Terminado:**
- [ ] Las 7 zonas (A a G) están presentes y transitables de principio a fin sin excepciones.
- [ ] Los 27 mensajes de tutorial se disparan en las posiciones X correctas y se muestran correctamente.
- [ ] Los 5 puntos de control funcionan (se activan una vez, restauran al morir).
- [ ] NextTrigger dispara correctamente STAGE_COMPLETE.
- [ ] Sin errores ni advertencias de consola durante un juego completo.
- [ ] Esta fase es la **prueba de humo de referencia** para todo lo que sigue.

---

## 13. Fase 10 — FilterTools (Unidad VII)

**Construye:** src/framework/processing/filter_tools.py

**Documentos de referencia:** 11_FILTER_TOOLS_SPEC.md (documento completo); 22_API_CONTRACTS.md seccion 13

**Definición de Terminado:**
- [ ] Los 9 métodos públicos en 11_FILTER_TOOLS_SPEC.md seccion 8 implementados con firmas exactas.
- [ ] Los 9 kernels estándar en la seccion 9.2 codificados exactamente como se especifica.
- [ ] Validación de entrada según la seccion 11 lanza los tipos de excepción exactos.
- [ ] Pruebas unitarias: tests/test_filter_tools.py con salida PNG guardada a tests/output/filter/.
- [ ] Re-ejecutar prueba de humo del Nivel 0 — sin regresión.

---

## 14. Fase 11 — VisionTools (Unidad VIII)

**Construye:** src/framework/processing/vision_tools.py

**Documentos de referencia:** 12_VISION_TOOLS_SPEC.md (documento completo); 22_API_CONTRACTS.md seccion 14

**Definición de Terminado:**
- [ ] Todos los métodos públicos implementados con firmas exactas.
- [ ] Pruebas unitarias: tests/test_vision_tools.py con salida PNG guardada a tests/output/vision/.
- [ ] Re-ejecutar prueba de humo del Nivel 0 — sin regresión.

---

## 15. Fase 12 — PatternRecognitionTools (Unidad IX)

**Construye:** src/framework/processing/pattern_recognition_tools.py, tools/build_dataset.py

**Documentos de referencia:** 13_PATTERN_RECOGNITION_SPEC.md (documento completo); 22_API_CONTRACTS.md seccion 15; 23_DATA_SCHEMAS.md seccion 5

**Definición de Terminado:**
- [ ] train() implementado para los 4 tipos de clasificador (knn, tree, forest, svm).
- [ ] evaluate() devuelve un EvaluationResult completo.
- [ ] save_model()/load_model() viajan de ida y vuelta correctamente.
- [ ] classify()/classify_proba()/predict() implementados.
- [ ] Pruebas unitarias: tests/test_pattern_recognition_tools.py.
- [ ] Re-ejecutar prueba de humo del Nivel 0 — sin regresión.

---

## 16. Fase 13 — Escenas de Demostración Académica

**Construye:** src/engine/scenes/demo_menu_scene.py, filter_demo_scene.py, vision_demo_scene.py, pattern_demo_scene.py

**Documentos de referencia:** 15_ACADEMIC_DEMO_SCENES.md (documento completo); 22_API_CONTRACTS.md seccion 16

**Prerrequisito:** Las Fases 10, 11 y 12 deben estar completas.

**Definición de Terminado:**
- [x] DemoMenuScene navega a las tres demostraciones y de vuelta a TitleScene.
- [x] FilterDemoScene: los 9 modos funcionales, incluyendo barras de histograma en vivo y visualización de matriz de kernel.
- [x] VisionDemoScene: los 10 modos funcionales.
- [x] PatternDemoScene: los 5 modos funcionales.
- [x] Tecla S guarda a PNG en las tres escenas demo.
- [x] Prueba de humo manual: cada escena demo ejecutada por 60 segundos con todos los modos — sin fallos.

---

## 17. Fase 14 — Escenas de Laboratorio Teórico Interactivo

**Construye:** 7 escenas de laboratorio

**Prerrequisito:** Fases 8 y 5.

**Definición de Terminado general:**
- [x] Las 7 escenas de laboratorio teórico implementan todos los modos documentados.
- [x] Las 10 escenas pasan pruebas de importar/instanciar/dibujar en tests/test_demo_scenes.py.
- [x] Las 364 pruebas existentes pasan todas.
- [x] Prueba de humo manual: cada escena recorrida a través de todos los modos por 30 segundos — sin fallos.

---

## 18. Fase 15 — BossBase y Jefe de Referencia

**Construye:** src/framework/entities/boss_base.py, src/stages/boss_venado/boss_venado.py (+ arena TMX)

**Documentos de referencia:** 17_BOSS_SPEC.md secciones 2, 3; 22_API_CONTRACTS.md seccion 17

**Definición de Terminado:**
- [ ] El protocolo de transición de fase de BossBase coincide exactamente con 17_BOSS_SPEC.md seccion 2.3.
- [ ] Los patrones de ataque de la Fase 1 y Fase 2 de El Venado Sagrado implementados exactamente según la seccion 3.3.
- [ ] Pruebas unitarias: tests/test_boss_base.py.

---

## 19. Fase 16 — Andamio de student_templates/

**Construye:** student_templates/stage_template/, student_templates/boss_template/

**Documentos de referencia:** 26_STUDENT_TEMPLATE_SPEC.md (documento completo)

---

## 20. Fase 17 — Pase de Regresión y Herramientas

**Construye:** scripts/validate_assets.py; limpieza final de todos los caminos de código de "respaldo de desarrollo temprano" marcados en fases anteriores.

---

## 21. Fase 18 — Sesión de Corrección de Errores y Remediación de Auditoría

**Fecha:** Julio 2026
**Alcance:** Auditoría sistemática y corrección de defectos encontrados durante pruebas, auditoría de código y juegos de estudiantes.

### 21.1 fix_plataformas (Jugabilidad)

| Archivo | Antes (regresión) | Después (corrección) |
|---|---|---|
| player.py (colisión unidireccional) | Detección basada en straddle | Comparación _prev_foot_y |
| generate_stage0_tmx.py | Tile tipo 3 mapeado uniformemente a Platform | Correcciones específicas |
| stage0.tmx | 4 plataformas unidireccionales en Zonas A/C | Todas Sólidas |
| test_stage0_platform_solidity.py | No existía | 5 pruebas de regresión |

### 21.2 Correcciones de Fallos (3 commits)

- 14 fallos corregidos en núcleo del motor, marco de entidades y carga de niveles
- Guardas de ZeroDivisionError
- Guardas de tipo None en carga de sprites y detección de colisión

### 21.3 Corrección de Texto Borroso

| Recurso | Tamaño Anterior | Nuevo Tamaño |
|---|---|---|
| Fuente 5x7 (HUD/corazones) | 5x7 px | 5x7 px (sin cambios) |
| Fuente 6x9 (banners) | 6x9 px | 6x15 px |
| Fuente 7x11 (diálogos) | 7x11 px | 7x18 px |

### 21.4 Remediación de Auditoría (8 problemas)

Problemas 1-8 corregidos.

### 21.5 Evolución del Conteo de Pruebas

| Hito | Pruebas |
|---|---|
| Fin de Fase 17 | 364 |
| Después de fix_plataformas | 369 |
| Después de remediación de auditoría | 369 |

---

## 22. Resumen del Grafo de Dependencias

Fase 0 (andamio) → Fase 1 (núcleo) → Fase 2 (entrada/audio/utils) → Fase 3 (sistema de escenas) → Fase 4 (UI) → Fase 5 (BaseEntity, Player) → Fase 6 (Enemigos) → Fase 7 (Sistema de nivel) → Fase 8 (ColorTools, CurveTools) → Fase 9 (NIVEL 0) → Fase 10 (FilterTools), Fase 11 (VisionTools), Fase 12 (PatternRecognitionTools) → Fase 13 (Escenas Demo) → Fase 14 (Laboratorios Teóricos) → Fase 15 (BossBase + El Venado Sagrado) → Fase 16 (student_templates/) → Fase 17 (Regresión) → Fase 18 (Corrección de errores)

---

## 21. Protocolo de Transferencia de Sesión

Cada sesión debe:
1. **Indicar qué fase está comenzando**, referenciando este documento por número de fase.
2. **Confirmar que la lista de verificación DoD de la fase anterior** está satisfecha antes de escribir nuevo código.
3. **No saltar adelante**.
4. **Actualizar las casillas de verificación de este documento** para que la próxima sesión sepa exactamente dónde se dejó el trabajo.

---

## 22. Índice de Referencia Cruzada

| Fase | Documento(s) de Especificación | Sección del Documento de Contrato |
|---|---|---|
| 1 | 03_ARCHITECTURE.md secciones 2.1, 6 | 22_API_CONTRACTS.md seccion 2 |
| 2 | 03_ARCHITECTURE.md secciones 2.3-2.4, 2.6 | 22_API_CONTRACTS.md secciones 3-5 |
| 3 | 03_ARCHITECTURE.md seccion 2.2 | 22_API_CONTRACTS.md seccion 6 |
| 4 | 09_HUD_SPEC.md | 22_API_CONTRACTS.md seccion 7 |
| 5 | 04_PLAYER_SPEC.md | 22_API_CONTRACTS.md secciones 8-9 |
| 6 | 05_ENEMY_SPEC.md | 22_API_CONTRACTS.md seccion 10 |
| 7 | 06_TMX_SPEC.md, 03_ARCHITECTURE.md seccion 2.8 | 22_API_CONTRACTS.md seccion 11 |
| 8 | 03_ARCHITECTURE.md seccion 2.9 | 22_API_CONTRACTS.md seccion 12 |
| 9 | 07_STAGE0_DESIGN.md, 20_ASSET_BIBLE.md | N/A — fase de integración |
| 10 | 11_FILTER_TOOLS_SPEC.md | 22_API_CONTRACTS.md seccion 13 |
| 11 | 12_VISION_TOOLS_SPEC.md | 22_API_CONTRACTS.md seccion 14 |
| 12 | 13_PATTERN_RECOGNITION_SPEC.md | 22_API_CONTRACTS.md seccion 15 |
| 13 | 15_ACADEMIC_DEMO_SCENES.md | 22_API_CONTRACTS.md seccion 16 |
| 14 | 15_ACADEMIC_DEMO_SCENES.md v1.1 | N/A — extensión educativa |
| 15 | 17_BOSS_SPEC.md secciones 2-3 | 22_API_CONTRACTS.md seccion 17 |
| 16 | 26_STUDENT_TEMPLATE_SPEC.md | N/A |
| 17 | Todos los documentos | N/A — fase de regresión |
| 18 | PHASE_FIX_REPORT.md, KNOWN_GAPS.md, REMEDIATION_PLAN.md | N/A — auditoría con correcciones |