---
document_id: "LOI-TICKET-030"
title: "Legacy of InFest — Ticket Backlog"
aliases: ["Ticket Backlog"]
tags: ["ticket", "backlog", "tasks"]
description: "Every roadmap phase decomposed into atomic tickets"
source: "docs/30_TICKET_BACKLOG.md"
date_processed: "2026-07-14"
---

# Legacy of InFest — Ticket Backlog

**Document ID:** LOI-BACKLOG-030  
**Version:** 1.0.0  
**Status:** Official  
**Compatibility:** Requires `25_IMPLEMENTATION_ROADMAP.md`, `22_API_CONTRACTS.md`, `24_TEST_PLAN.md`  
**Audience:** AI coding assistants (Claude Code, Cline, OpenCode, Codex)

---

## 1. Purpose

`25_IMPLEMENTATION_ROADMAP.md` defines 16 **phases**. A phase is too large a unit of work for a single AI coding turn or a single GitHub issue — Phase 5 alone ("Player") involves a full state machine, physics, damage system, and attack hitboxes. This document decomposes every phase into **atomic tickets**: the granularity at which an AI assistant should actually pick up one unit of work, complete it, test it, and commit it (per `29_GIT_WORKFLOW_AND_STANDARDS.md` §3's "one logical change per commit" rule).

Each ticket includes a title, the files it touches, its acceptance criteria, and its estimated relative size. Tickets within a phase are ordered; tickets across phases follow the phase order from `25_IMPLEMENTATION_ROADMAP.md` §2.

**Sizing scale (relative, not time-based — AI coding speed varies too much for hour estimates to be meaningful):**

| Size | Meaning |
|---|---|
| **XS** | Single function or small data declaration, < 50 lines |
| **S** | Single class or module, 50–150 lines |
| **M** | Multiple related classes/functions, 150–400 lines |
| **L** | Full module with significant internal complexity, 400+ lines |

---

## 2. Phase 0 — Repository Scaffold

| Ticket | Files | Acceptance Criteria | Size |
|---|---|---|---|
| **T0.1** Create directory tree | All directories per `00_SYLLABUS_ALIGNMENT_AUDIT.md` §7 | `find . -type d` output matches the documented tree | XS |
| **T0.2** Write `requirements.txt` | `requirements.txt` | Matches `23_DATA_SCHEMAS.md` §9 pin table; `pip install -r requirements.txt` exits 0 | XS |
| **T0.3** Create `__init__.py` stubs | `src/engine/__init__.py` + all subpackages, `src/framework/__init__.py` + all subpackages | All packages importable (`python -c "import src.engine"` succeeds) | XS |
| **T0.4** Write placeholder `main.py` | `main.py` | Exits 0, prints scaffold message | XS |
| **T0.5** Configure `.gitignore` | `.gitignore` | Matches `29_GIT_WORKFLOW_AND_STANDARDS.md` §6, including the `*.pkl` scoping exception | XS |
| **T0.6** Initialize `KNOWN_GAPS.md` | `KNOWN_GAPS.md` (repo root) | Empty file with the header format from `23_DATA_SCHEMAS.md` §8 ready for entries | XS |

---

## 3. Phase 1 — Engine Core

| Ticket | Files | Acceptance Criteria | Size |
|---|---|---|---|
| **T1.1** Implement `settings.py` | `src/engine/core/settings.py` | All constants from `22_API_CONTRACTS.md` §2.1 present, no extras | XS |
| **T1.2** Implement `EventBus` | `src/engine/core/event_bus.py` | Matches `22_API_CONTRACTS.md` §2.3; `tests/test_event_bus.py` passes | S |
| **T1.3** Implement `DeltaClock` | `src/engine/core/clock.py` | Matches `22_API_CONTRACTS.md` §2.2; `tests/test_clock.py` passes | XS |
| **T1.4** Implement `App` skeleton | `src/engine/core/app.py` | Constructs without error using placeholder Scene/Input/Audio classes; `python main.py` still exits 0 | M |
| **T1.5** Write Phase 1 tests | `tests/test_event_bus.py`, `tests/test_clock.py` | All assertions from `24_TEST_PLAN.md` §3 present and passing | S |

---

## 4. Phase 2 — Engine Input / Audio / Utils

| Ticket | Files | Acceptance Criteria | Size |
|---|---|---|---|
| **T2.1** Implement `math_utils.py` | `src/engine/utils/math_utils.py` | All functions from `22_API_CONTRACTS.md` §5.1 implemented | S |
| **T2.2** Implement `AssetLoader` | `src/engine/utils/asset_loader.py` | Matches `22_API_CONTRACTS.md` §5.2; caching verified | S |
| **T2.3** ~~Implement `SpriteSheet`~~ — anulado (AUD-098) | el recorte lo hace `AssetLoader.load_sprite_sheet`; el módulo aparte se retiró por ser código muerto | — | XS |
| **T2.4** Implement `action_map.py` | `src/engine/input/action_map.py` | `Action` enum and default binding tables match `22_API_CONTRACTS.md` §3.1 and `03_ARCHITECTURE.md` §2.3 table | XS |
| **T2.5** Implement `InputManager` | `src/engine/input/input_manager.py` | Matches `22_API_CONTRACTS.md` §3.2; pressed/held/released distinction correct | S |
| **T2.6** Implement `SoundBank` | `src/engine/audio/sound_bank.py` | Matches `22_API_CONTRACTS.md` §4.1 | XS |
| **T2.7** Implement `AudioManager` | `src/engine/audio/audio_manager.py` | Matches `22_API_CONTRACTS.md` §4.2; graceful fallback for missing files (flagged for Phase 16 cleanup) | S |
| **T2.8** Write Phase 2 tests | `tests/test_math_utils.py`, `tests/test_asset_loader.py`, `tests/test_input_manager.py` | All assertions from `24_TEST_PLAN.md` §4 present and passing | M |

---

## 5. Phase 3 — Engine Scene System

| Ticket | Files | Acceptance Criteria | Size |
|---|---|---|---|
| **T3.1** Implement `BaseScene` | `src/engine/scene/base_scene.py` | Abstract class matches `22_API_CONTRACTS.md` §6.1 | XS |
| **T3.2** Implement `SceneManager` | `src/engine/scene/scene_manager.py` | Push/pop/replace call-order matches `22_API_CONTRACTS.md` §6.2 sequence diagram | S |
| **T3.3** ~~Implement `transitions.py`~~ — anulado (AUD-111) | las cuatro transiciones son modos de `src/engine/scenes/transition_manager.py` | — | S |
| **T3.4** Wire `App.run()` to `SceneManager` | `src/engine/core/app.py` | Main loop calls `scene_manager.current.update/draw` every frame | S |
| **T3.5** Build minimal `SplashScene` stub | `src/engine/scenes/splash_scene.py` (temporary, replaced in later phases) | Solid color fill, runs for 5s without crash in manual smoke test | XS |
| **T3.6** Write Phase 3 tests | `tests/test_scene_manager.py` | All assertions from `24_TEST_PLAN.md` §5 present and passing | S |

---

## 6. Phase 4 — Engine UI

| Ticket | Files | Acceptance Criteria | Size |
|---|---|---|---|
| **T4.1** Implement `HUD` heart-fraction logic as pure function | `src/engine/ui/hud.py` | `_heart_slot_state()` matches `09_HUD_SPEC.md` §4.3 thresholds exactly | S |
| **T4.2** Implement `HUD` rendering and event subscriptions | `src/engine/ui/hud.py` | Portrait states, timer, full `09_HUD_SPEC.md` §10 event table wired | M |
| **T4.3** Implement `MessageBox` | `src/engine/ui/message_box.py` | Typewriter reveal at 30 chars/sec per `09_HUD_SPEC.md` §7.3 | S |
| **T4.4** Implement `ScreenBanner` | `src/engine/ui/screen_banner.py` | Slide-in/hold/slide-out timing per `09_HUD_SPEC.md` §6.3 | S |
| **T4.5** Write Phase 4 tests | `tests/test_hud.py` | All assertions from `24_TEST_PLAN.md` §6 present and passing | S |

---

## 7. Phase 5 — Player

| Ticket | Files | Acceptance Criteria | Size |
|---|---|---|---|
| **T5.1** Implement `BaseEntity` | `src/framework/entities/base_entity.py` | Abstract class matches `22_API_CONTRACTS.md` §8.1 | XS |
| **T5.2** Implement `Player` movement and physics | `src/framework/entities/player.py` | Walk/jump/gravity/coyote-time/jump-cut match `04_PLAYER_SPEC.md` §4 exactly | M |
| **T5.3** Implement `Player` state machine | `src/framework/entities/player.py` | All 9 `PlayerState` transitions match `04_PLAYER_SPEC.md` §8.1 | M |
| **T5.4** Implement `Player` damage system | `src/framework/entities/player.py` | Damage tiers, invincibility, knockback match `04_PLAYER_SPEC.md` §6 | M |
| **T5.5** Implement `Player` attack hitboxes | `src/framework/entities/player.py` | Short/Long attack frame-by-frame offsets match `04_PLAYER_SPEC.md` §10 | M |
| **T5.6** Implement `Player` hurtbox + animation controller | `src/framework/entities/player.py` | Standard/crouching hurtbox per §11; animation table per §9 | M |
| **T5.7** Write Phase 5 tests | `tests/test_player_physics.py`, `tests/test_player_state_machine.py`, `tests/test_player_damage.py` | All assertions from `24_TEST_PLAN.md` §7 present and passing | L |
| **T5.8** Manual smoke test | (no new files — verification only) | Player spawns, walks, jumps, crouches, attacks in a blank scene without exceptions | XS |

---

## 8. Phase 6 — Enemy Templates

| Ticket | Files | Acceptance Criteria | Size |
|---|---|---|---|
| **T6.1** Implement `EnemyBase` FSM skeleton | `src/framework/entities/enemy_base.py` | `EnemyState` transitions, detection rule match `05_ENEMY_SPEC.md` §2.3, §2.5 | M |
| **T6.2** Implement `EnemyBase.apply_hit`/`_die`/contact damage | `src/framework/entities/enemy_base.py` | Matches `05_ENEMY_SPEC.md` §2.3, §9.2 | S |
| **T6.3** Implement `EnemyWalker` patrol + ledge detection | `src/framework/entities/enemy_walker.py` | Matches `05_ENEMY_SPEC.md` §3 | S |
| **T6.4** Implement `EnemyFlying` sine mode only | `src/framework/entities/enemy_flying.py` | Sine formula matches `05_ENEMY_SPEC.md` §4.3; Bézier/patrol modes stubbed `NotImplementedError` | S |
| **T6.5** Implement `EnemyShooter` + `Projectile` | `src/framework/entities/enemy_shooter.py` | Fire rate, `atan2` angle calc, projectile lifecycle match `05_ENEMY_SPEC.md` §5.4 | M |
| **T6.6** Write Phase 6 tests (sine mode subset) | `tests/test_enemy_walker.py`, `tests/test_enemy_flying.py` (partial), `tests/test_enemy_shooter.py` | All assertions from `24_TEST_PLAN.md` §8 present and passing, except Bézier-mode test (deferred to T8.6) | M |

---

## 9. Phase 7 — Stage System

| Ticket | Files | Acceptance Criteria | Size |
|---|---|---|---|
| **T7.1** Implement `Camera` | `src/framework/stage/camera.py` | Follow/lerp/parallax/world-screen conversion match `22_API_CONTRACTS.md` §11.1 | S |
| **T7.2** Implement `Checkpoint` | `src/framework/stage/checkpoint.py` | Single-activation, `CHECKPOINT_REACHED` event match `06_TMX_SPEC.md` §7.3 | XS |
| **T7.3** Implement `StageData` dataclass | `src/framework/stage/stage_loader.py` | Matches `22_API_CONTRACTS.md` §11.3 field-for-field | XS |
| **T7.4** Implement `StageLoader.load()` — layer parsing | `src/framework/stage/stage_loader.py` | All 8 required layers parsed per `06_TMX_SPEC.md` §3.1; `FrameworkUsageError` on missing layer | M |
| **T7.5** Implement `StageLoader` — entity factory registration + spawn | `src/framework/stage/stage_loader.py` | `register_entity()`/spawn-from-TMX-object pattern matches `23_DATA_SCHEMAS.md` §3.11 | M |
| **T7.6** Build `tests/fixtures/minimal_stage.tmx` | `tests/fixtures/minimal_stage.tmx` | Valid TMX per §9.1 of `24_TEST_PLAN.md`, opens cleanly in Tiled | S |
| **T7.7** Write Phase 7 tests | `tests/test_stage_loader.py`, `tests/test_camera.py`, `tests/test_checkpoint.py` | All assertions from `24_TEST_PLAN.md` §9 present and passing | M |

---

## 10. Phase 8 — ColorTools and CurveTools

| Ticket | Files | Acceptance Criteria | Size |
|---|---|---|---|
| **T8.1** Implement `ColorTools` conversions (RGB↔HSV↔HSL↔CMYK) | `src/framework/processing/color_tools.py` | Round-trip property test passes per `24_TEST_PLAN.md` §10.1 | M |
| **T8.2** Implement `ColorTools.alpha_blend`/`apply_tint`/array bridge | `src/framework/processing/color_tools.py` | Matches `22_API_CONTRACTS.md` §12.1 | S |
| **T8.3** Implement `CurveTools.bezier` | `src/framework/processing/curve_tools.py` | Passes `test_bezier_linear_degenerate_case`, `test_bezier_endpoint_interpolation`, `test_bezier_symmetric_quadratic` | S |
| **T8.4** Implement `CurveTools.b_spline`/`nurbs` | `src/framework/processing/curve_tools.py` | Smoke tests pass per `24_TEST_PLAN.md` §10.2 | M |
| **T8.5** Implement `CurveTools.catmull_rom`/`sample_path` | `src/framework/processing/curve_tools.py` | Passes through control points; `sample_path` interpolates correctly | S |
| **T8.6** Complete `EnemyFlying` Bézier and patrol modes | `src/framework/entities/enemy_flying.py` | Deferred from T6.4; now functional, full `tests/test_enemy_flying.py` passes | S |
| **T8.7** Write Phase 8 tests | `tests/test_color_tools.py`, `tests/test_curve_tools.py` | All assertions from `24_TEST_PLAN.md` §10 present and passing | M |

---

## 11. Phase 9 — Stage 0 (Full Implementation)

This phase is large enough that tickets are grouped by Stage 0 zone (per `07_STAGE0_DESIGN.md` §3).

| Ticket | Files | Acceptance Criteria | Size |
|---|---|---|---|
| **T9.1** Author `stage0.tmx` — all zones, layers, layout | `assets/maps/stage0/stage0.tmx` | All 7 zones (A–G) present per `07_STAGE0_DESIGN.md` §3; opens cleanly in Tiled | L |
| **T9.2** Source/placeholder Stage 0 assets | `assets/sprites/`, `assets/tilesets/`, `assets/backgrounds/` (Stage 0 subset) | All files listed for Stage 0 in `20_ASSET_BIBLE.md` §4–12 present (placeholders acceptable) | L |
| **T9.3** Implement `Stage0Scene` class | `src/stages/stage0/stage0.py` | Wires `StageLoader`, `Camera`, `HUD`, `MessageBox`, `ScreenBanner` | M |
| **T9.4** Wire all 27 tutorial messages | `assets/maps/stage0/stage0.tmx` (Message objects), `stage0.py` | All messages from `07_STAGE0_DESIGN.md` §4 trigger at correct X positions | M |
| **T9.5** Wire all 5 checkpoints | `stage0.tmx`, `stage0.py` | Checkpoints activate once, restore correctly on death | S |
| **T9.6** Implement minimal `TitleScene`/`StoryScene1-3` placeholders | `src/engine/scenes/title_scene.py`, `story_scene.py` | Scene flow Splash→Title→Story1-3→Stage0 navigable end to end | M |
| **T9.7** Implement debug overlay (F1) | `src/engine/core/app.py` or a dedicated debug module | Renders hitboxes/hurtboxes/detection zones without crashing | S |
| **T9.8** Full manual playthrough verification | (no new files) | Master systems checklist `07_STAGE0_DESIGN.md` §10 — every row confirmed | XS |

---

## 12. Phase 10 — FilterTools

| Ticket | Files | Acceptance Criteria | Size |
|---|---|---|---|
| **T10.1** Implement histogram operations | `src/framework/processing/filter_tools.py` | `compute_histogram`, `histogram_equalize` per `11_FILTER_TOOLS_SPEC.md` §8.1 | S |
| **T10.2** Implement brightness/contrast operations | `src/framework/processing/filter_tools.py` | `adjust_brightness`, `adjust_contrast`, `stretch_contrast` per §8.2–8.3 | S |
| **T10.3** Implement convolution + standard kernels | `src/framework/processing/filter_tools.py` | `apply_kernel`, `get_standard_kernel` with all 9 kernels per §9.2 | M |
| **T10.4** Implement Gaussian blur | `src/framework/processing/filter_tools.py` | `gaussian_blur` per §8.5 | S |
| **T10.5** Implement Sobel and Canny edge detection | `src/framework/processing/filter_tools.py` | `sobel_edge`, `canny_edge` per §8.6 | M |
| **T10.6** Write Phase 10 tests | `tests/test_filter_tools.py` | All assertions from `24_TEST_PLAN.md` §12 present and passing; PNG output saved to `tests/output/filter/` | M |
| **T10.7** Re-run Stage 0 regression | (no new files) | Stage 0 playthrough — no regression | XS |

---

## 13. Phase 11 — VisionTools

| Ticket | Files | Acceptance Criteria | Size |
|---|---|---|---|
| **T11.1** Implement threshold operations | `src/framework/processing/vision_tools.py` | `threshold_binary`, `threshold_otsu` per `12_VISION_TOOLS_SPEC.md` §8 | S |
| **T11.2** Implement morphological operations | `src/framework/processing/vision_tools.py` | Erode/dilate/open/close per §9 | S |
| **T11.3** Implement connected components + region analysis | `src/framework/processing/vision_tools.py` | `ComponentResult`/`RegionInfo` dataclasses match `23_DATA_SCHEMAS.md` §4.1–4.2 | M |
| **T11.4** Implement watershed segmentation | `src/framework/processing/vision_tools.py` | `watershed_segment` per §12 | M |
| **T11.5** Implement feature extraction (HOG/LBP/color histogram) | `src/framework/processing/vision_tools.py` | Output vector lengths exactly 512/256/`bins*3` | M |
| **T11.6** Implement contours and bounding boxes | `src/framework/processing/vision_tools.py` | `find_contours`, `bounding_boxes_from_mask` per §14 | S |
| **T11.7** Write Phase 11 tests | `tests/test_vision_tools.py` | All assertions from `24_TEST_PLAN.md` §13 present and passing | M |
| **T11.8** Re-run Stage 0 regression | (no new files) | No regression | XS |

---

## 14. Phase 12 — PatternRecognitionTools

| Ticket | Files | Acceptance Criteria | Size |
|---|---|---|---|
| **T12.1** Implement feature extractor delegation methods | `src/framework/processing/pattern_recognition_tools.py` | `extract_hog`/`extract_lbp`/`extract_color_histogram`/`extract_combined` delegate correctly to `VisionTools` | S |
| **T12.2** Implement `train()` for all 4 classifier types | `src/framework/processing/pattern_recognition_tools.py` | `TrainedModel` with embedded `StandardScaler` Pipeline, per `13_PATTERN_RECOGNITION_SPEC.md` §9.1 | M |
| **T12.3** Implement `evaluate()` | `src/framework/processing/pattern_recognition_tools.py` | `EvaluationResult` complete per §9.2 | S |
| **T12.4** Implement `save_model()`/`load_model()` | `src/framework/processing/pattern_recognition_tools.py` | Round-trip identical predictions per `24_TEST_PLAN.md` §14.1 | S |
| **T12.5** Implement Model Registry | `src/framework/processing/pattern_recognition_tools.py` | `register_model`/`get_model`/`list_models` per `22_API_CONTRACTS.md` §15.1 | XS |
| **T12.6** Implement `classify()`/`classify_proba()`/`predict()` | `src/framework/processing/pattern_recognition_tools.py` | Inference methods per §13 | M |
| **T12.7** Build `tools/build_dataset.py` | `tools/build_dataset.py` | Produces valid `.npz` per `23_DATA_SCHEMAS.md` §5.1 | M |
| **T12.8** Generate `assets/datasets/sample_dataset.npz` | `assets/datasets/sample_dataset.npz` | 90 samples, 3 classes, 30 each, per `23_DATA_SCHEMAS.md` §5.3 | S |
| **T12.9** Train and save `assets/models/professor_sample.pkl` | `assets/models/professor_sample.pkl` | k-NN k=5 trained on the sample dataset | S |
| **T12.10** Write Phase 12 tests | `tests/test_pattern_recognition_tools.py` | All assertions from `24_TEST_PLAN.md` §14 present and passing for all 4 classifier types | L |
| **T12.11** Re-run Stage 0 regression | (no new files) | No regression | XS |

---

## 15. Phase 13 — Academic Demo Scenes

| Ticket | Files | Acceptance Criteria | Size |
|---|---|---|---|
| **T13.1** Implement `DemoMenuScene` | `src/engine/scenes/demo_menu_scene.py` | Navigates to all 3 demos and back per `15_ACADEMIC_DEMO_SCENES.md` §6 | S |
| **T13.2** Implement `FilterDemoScene` — modes 0-4 | `src/engine/scenes/filter_demo_scene.py` | Histogram, Brightness, Contrast, Stretch, Kernel modes functional | M |
| **T13.3** Implement `FilterDemoScene` — modes 5-8 | `src/engine/scenes/filter_demo_scene.py` | Gaussian, Sobel, Canny, Equalize modes functional | M |
| **T13.4** Implement `VisionDemoScene` — modes 0-4 | `src/engine/scenes/vision_demo_scene.py` | Threshold, Otsu, Erode, Dilate, Open modes functional | M |
| **T13.5** Implement `VisionDemoScene` — modes 5-9 | `src/engine/scenes/vision_demo_scene.py` | Close, Components, Regions, Watershed, Features modes functional | L |
| **T13.6** Implement `PatternDemoScene` — modes 0-2 | `src/engine/scenes/pattern_demo_scene.py` | Inference, Feature Compare, Class Grid functional | M |
| **T13.7** Implement `PatternDemoScene` — modes 3-4 + model loader | `src/engine/scenes/pattern_demo_scene.py` | Confusion, Pipeline modes + `L`-key text input functional | M |
| **T13.8** Implement frame throttling pattern across all 3 demos | All 3 demo scene files | No mode drops below 30 FPS, per `15_ACADEMIC_DEMO_SCENES.md` §8.1 | S |
| **T13.9** Manual smoke test all demo scenes | (no new files) | 60-second run per scene, all modes cycled, no crashes | XS |

---

## 16. Phase 14 — Interactive Theory Lab Scenes (Units II–VIII)

| Ticket | Files | Acceptance Criteria | Size |
|---|---|---|---|
| **T14.1** Implement `VectorLabScene` | `src/engine/scenes/vector_lab_scene.py` | 4 modes (FREE MOVE, CHASE, ORBIT, DISTANCE), vector math info panel, normalized toggle | M |
| **T14.2** Implement `TransformLabScene` | `src/engine/scenes/transform_lab_scene.py` | 5 modes (TRANSLATE, ROTATE, SCALE, SHEAR, COMPOSITE), live matrix display | M |
| **T14.3** Implement `CurveEditorScene` | `src/engine/scenes/curve_editor_scene.py` | 6 curve modes, draggable control points, de Casteljau animation | M |
| **T14.4** Implement `InterpolationLabScene` | `src/engine/scenes/interpolation_lab_scene.py` | 3 modes (LERP, EASING CURVES, KEYFRAME ANIM), 10 easing functions | M |
| **T14.5** Implement `ColorTheoryScene` | `src/engine/scenes/color_theory_scene.py` | 6 modes (RGB/HSV/HSL/CMYK/Alpha Blend/Challenge) | M |
| **T14.6** Implement `NoiseLabScene` | `src/engine/scenes/noise_lab_scene.py` | 3 noise types, 5 adjustable parameters, live noise map texture | M |
| **T14.7** Implement `CollisionLabScene` | `src/engine/scenes/collision_lab_scene.py` | 3 resolution modes, wall-climb bug demo, one-way platforms | M |
| **T14.8** DemoMenuScene integration | `src/engine/scenes/demo_menu_scene.py` | 10 options, uses SceneRegistry for DI | S |
| **T14.9** Engine infrastructure improvements | Multiple files | SceneRegistry, ParamPanel, demo_layout, demo_utils, debug_overlay, validate_assets.py, generate_exam.py | L |
| **T14.10** Write Phase 14 tests | `tests/test_demo_scenes.py` | All 10 scenes: import/instantiate/draw smoke tests pass | M |

---

## 17. Phase 15 — student_templates/

| Ticket | Files | Acceptance Criteria | Size |
|---|---|---|---|
| **T15.1** Write `stage_template.py` | `student_templates/stage_template/stage_template.py` | Exact content per `26_STUDENT_TEMPLATE_SPEC.md` §3 | S |
| **T15.2** Generate `stage_template.tmx` | `student_templates/stage_template/stage_template.tmx` | Per `26_STUDENT_TEMPLATE_SPEC.md` §4 | M |
| **T15.3** Write `boss_template.py` | `student_templates/boss_template/boss_template.py` | Exact content per `26_STUDENT_TEMPLATE_SPEC.md` §5 | S |
| **T15.4** Write both `README_template.md` files | `student_templates/stage_template/README_template.md`, `student_templates/boss_template/README_template.md` | Per §6–7, including valid YAML front-matter | S |
| **T15.5** Write `tests/test_student_template.py` | `tests/test_student_template.py` | All assertions from `26_STUDENT_TEMPLATE_SPEC.md` §8.1 present and passing | S |
| **T15.6** 15-minute onboarding manual test | (no new files) | Copy→rename→run cycle completes within 15 minutes per §8 | XS |

---

## 18. Phase 16 — Regression and Tooling

| Ticket | Files | Acceptance Criteria | Size |
|---|---|---|---|
| **T16.1** Implement `scripts/validate_assets.py` | `scripts/validate_assets.py` | Validates font + model loading; exits 0 on success | S |
| **T16.2** Review and resolve/document all early-development fallbacks | Various (flagged in T2.7) | Each fallback either removed (real asset now exists) or documented in `KNOWN_GAPS.md` | M |
| **T16.3** Full test suite pass | All `tests/` | Zero failures, zero unjustified skips | XS |
| **T16.4** Final Stage 0 playthrough with final assets | (no new files) | End-to-end, no placeholder assets remaining | XS |
| **T16.5** Verify full scene flow launch | `main.py` | Splash→Title→Story1-3→Stage0(→Boss via debug skip) with no manual intervention | S |
| **T16.6** Final `KNOWN_GAPS.md` audit | `KNOWN_GAPS.md` | Every remaining `TODO`/`NotImplementedError` has a corresponding entry | S |

---

## 19. Ticket Dependency Notes

- Tickets within a phase generally follow the listed order, but **T-prefixed tickets within the same phase with no shared file** (e.g., T2.1 `math_utils.py` and T2.4 `action_map.py`) may be done in either order or in parallel across sessions.
- Cross-phase dependencies follow `25_IMPLEMENTATION_ROADMAP.md` §20's dependency graph exactly — do not start a Phase N+1 ticket before all Phase N tickets are complete, except where the roadmap explicitly allows partial parallelism (e.g., T6.4's sine-only stub, completed later in T8.6).

---

## 20. Using This Backlog with an Issue Tracker

If the professor wants to mirror this backlog into actual GitHub Issues for the private repository, each ticket row maps 1:1 to one Issue:

- **Issue title:** `[<Phase Number>.<Ticket Number>] <Ticket Title>` (e.g., `[5.2] Implement Player movement and physics`)
- **Issue body:** Files + Acceptance Criteria columns, verbatim
- **Issue label:** Size (`size:XS`/`size:S`/`size:M`/`size:L`) and Phase (`phase:5`)
- **Issue milestone:** The roadmap phase number

This is optional tooling — the backlog is fully usable as a plain Markdown checklist without GitHub Issues if preferred.


---
## 🔗 Documentos Relacionados

- [[25_IMPLEMENTATION_ROADMAP.md|Implementation Roadmap]]
