# Legacy of InFest — Implementation Roadmap

**Document ID:** LOI-ROADMAP-025  
**Version:** 1.0.0  
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
PHASE 14  Framework Entities — BossBase + one reference boss (El Venado Sagrado)
PHASE 15  student_templates/ scaffolding
PHASE 16  Full regression pass + tooling (validate_assets.py, build_dataset.py)
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
- [ ] `DemoMenuScene` navigates to all three demos and back to `TitleScene`.
- [ ] `FilterDemoScene`: all 9 modes from §3.3 functional, including live histogram bars and kernel matrix text display.
- [ ] `VisionDemoScene`: all 10 modes from §4.3 functional, including HOG cell visualization and watershed pre-computation (not per-frame).
- [ ] `PatternDemoScene`: all 5 modes from §5.3 functional, including the `L`-key model loader text input and probability bars.
- [ ] Frame throttling pattern from §8.1 implemented for all expensive operations (no mode drops below 30 FPS on the reference development machine).
- [ ] `S` key save-to-PNG works in all three demo scenes, writing to `tests/output/demo/`.
- [ ] Manual smoke test: each demo scene run for 60 seconds with all modes cycled — no crashes.

---

## 17. Phase 14 — BossBase and Reference Boss

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

## 18. Phase 15 — student_templates/ Scaffolding

**Builds:** `student_templates/stage_template/`, `student_templates/boss_template/`

**Reference documents:** `26_STUDENT_TEMPLATE_SPEC.md` (full document — new)

**Definition of Done:** See `26_STUDENT_TEMPLATE_SPEC.md` §8 for the complete checklist. Summary:
- [ ] `stage_template.py` compiles, imports correctly, and produces a loadable (if empty) stage when run standalone.
- [ ] `stage_template.tmx` opens in Tiled without errors and contains all 8 required layers with placeholder content.
- [ ] `boss_template.py` compiles and produces a `BossBase` subclass with one placeholder phase.
- [ ] Both `README_template.md` files contain every section a student must fill in, with inline instructions.
- [ ] A test student (the professor, or a TA) can copy a template, rename it, and have a running (if empty) Stage or Boss within 15 minutes — this is the Class 1 onboarding target from `21_COURSE_SCHEDULE.md`.

---

## 19. Phase 16 — Regression Pass and Tooling

**Builds:** `tools/validate_assets.py`; final cleanup of all "early development fallback" code paths flagged in earlier phases

**Definition of Done:**
- [ ] `tools/validate_assets.py` implemented per `10_LIBRARIES_AND_DEPENDENCIES.md` §8.5 (Pillow-based palette validation).
- [ ] All "graceful fallback" code paths flagged during Phase 2 (missing audio files) are reviewed: either real assets now exist (preferred) or the fallback is intentionally retained and documented as such in code comments.
- [ ] Full test suite (`tests/`) passes with zero failures and zero skips that aren't explicitly justified in `24_TEST_PLAN.md`.
- [ ] Stage 0 full playthrough repeated one final time end-to-end with all final (non-placeholder) assets.
- [ ] `main.py` launches the complete scene flow: Splash → Title → Story 1-3 → Stage 0 → (Boss Venado, if reached via debug skip) without manual intervention.
- [ ] Documentation cross-check: every `TODO` or `NotImplementedError` left in the codebase is either resolved or explicitly listed in a `KNOWN_GAPS.md` file at repo root with a justification (e.g., "El Rey Terciopelo split-body boss is a student/professor assignment, not professor pre-built — intentionally absent").

---

## 20. Dependency Graph Summary

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
         Phase 13 (Demo Scenes)
    ↓
Phase 14 (BossBase + El Venado Sagrado) ◄── requires FilterTools (Phase 10) for Sobel aura
    ↓
Phase 15 (student_templates/)
    ↓
Phase 16 (Regression + Tooling)
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
| 13 | `15_ACADEMIC_DEMO_SCENES.md` | `22_API_CONTRACTS.md` §16 |
| 14 | `17_BOSS_SPEC.md` §2-3 | `22_API_CONTRACTS.md` §17 |
| 15 | `26_STUDENT_TEMPLATE_SPEC.md` | n/a |
| 16 | All documents | n/a — regression phase |
