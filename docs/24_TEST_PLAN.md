---
document_id: "LOI-TEST-024"
title: "Legacy of InFest — Test Plan"
aliases: ["Test Plan"]
tags: ["test", "testing", "qa"]
description: "Exact test cases per module"
source: "docs/24_TEST_PLAN.md"
date_processed: "2026-07-14"
---

# Legacy of InFest — Test Plan

**Document ID:** LOI-TESTPLAN-024  
**Version:** 1.0.0  
**Status:** Official  
**Compatibility:** Requires `22_API_CONTRACTS.md`, `23_DATA_SCHEMAS.md`, `25_IMPLEMENTATION_ROADMAP.md`  
**Audience:** AI coding assistants (Claude Code, Cline, OpenCode, Codex)

---

## 1. Purpose

`25_IMPLEMENTATION_ROADMAP.md` references specific test files (`tests/test_clock.py`, `tests/test_player_physics.py`, etc.) in each phase's Definition of Done without specifying their contents. This document specifies **exactly what each test file must verify**, so an AI assistant can write the tests without guessing what "passing" means, and so a human reviewer can confirm a phase is genuinely complete rather than superficially complete.

---

## 2. Testing Philosophy and Scope

### 2.1 What Is Tested Automatically

- Pure functions and pure-data classes (math, color, curve, filter, vision, pattern recognition modules)
- State machine transition logic (Player, Enemy, Boss — transition correctness, not visual rendering)
- Data structure shape and field correctness (TMX parsing results, `ComponentResult`, `RegionInfo`, `TrainedModel`)
- Serialization round-trips (model save/load)
- Event bus dispatch correctness

### 2.2 What Is NOT Tested Automatically

- Pixel-perfect visual rendering (sprite appearance, animation smoothness)
- Audio playback correctness (file plays, sounds correct — verified by manual listening)
- Frame-rate / performance benchmarks (logged for awareness, not a CI gate — see §7)
- Demo scene visual layouts (all 10 scenes — 7 theory labs + 3 academic demos — verified by automated import/instantiate/draw smoke tests in `test_demo_scenes.py`, plus manual visual verification per phase DoDs)
- Full boss combat balance/feel (verified by manual playthrough)

### 2.3 Test Framework

All tests use `pytest`. Test files live under `tests/`, mirroring the `src/` package structure:

```
tests/
├── test_event_bus.py
├── test_clock.py
├── test_math_utils.py
├── test_asset_loader.py
├── test_input_manager.py
├── test_scene_manager.py
├── test_hud.py
├── test_player_physics.py
├── test_player_state_machine.py
├── test_player_damage.py
├── test_enemy_walker.py
├── test_enemy_flying.py
├── test_enemy_shooter.py
├── test_stage_loader.py
├── test_camera.py
├── test_checkpoint.py
├── test_color_tools.py
├── test_curve_tools.py
├── test_filter_tools.py
├── test_vision_tools.py
├── test_pattern_recognition_tools.py
├── test_boss_base.py
├── test_demo_scenes.py     # All 10 demo/lab scenes: import, instantiate, draw
├── fixtures/
│   ├── minimal_stage.tmx
│   ├── reference_sprite_32x32.png
│   └── sample_dataset_tiny.npz
└── output/
    ├── filter/
    ├── vision/
    └── demo/
```

`tests/output/` is gitignored content (generated PNGs for visual spot-check) but the directories themselves must exist (`.gitkeep`).

---

## 3. Phase 1 Tests — Engine Core

### 3.1 `tests/test_event_bus.py`

| Test | Assertion |
|---|---|
| `test_subscribe_and_emit` | A subscribed callback receives the exact `**data` kwargs passed to `emit()` |
| `test_emit_queues_not_immediate` | Calling `emit()` does not invoke the callback until `dispatch()` is called |
| `test_unsubscribe_stops_delivery` | After `unsubscribe()`, a subsequent `emit()` + `dispatch()` does not invoke the callback |
| `test_multiple_subscribers` | Two callbacks subscribed to the same event both receive it |
| `test_unrelated_event_not_delivered` | A callback subscribed to `"FOO"` does not fire when `"BAR"` is emitted |

### 3.2 `tests/test_clock.py`

| Test | Assertion |
|---|---|
| `test_tick_returns_float` | `DeltaClock().tick()` returns a `float >= 0.0` |
| `test_time_scale_applied` | Setting `time_scale = 0.5` halves the returned delta on the next `tick()` (within floating-point tolerance) |
| `test_fps_property_nonzero_after_tick` | `.fps` is `> 0` after at least one `tick()` call |

---

## 4. Phase 2 Tests — Input / Audio / Utils

### 4.1 `tests/test_math_utils.py`

| Test | Assertion |
|---|---|
| `test_lerp_endpoints` | `lerp(0, 10, 0.0) == 0`, `lerp(0, 10, 1.0) == 10` |
| `test_lerp_midpoint` | `lerp(0, 10, 0.5) == 5` |
| `test_clamp_below_min` | `clamp(-5, 0, 10) == 0` |
| `test_clamp_above_max` | `clamp(15, 0, 10) == 10` |
| `test_clamp_within_range` | `clamp(5, 0, 10) == 5` |
| `test_ease_functions_boundary` | Every `ease_*` function returns `≈0.0` at `t=0.0` and `≈1.0` at `t=1.0` (within 1e-6, except `ease_out_bounce`/`ease_out_elastic` which may overshoot slightly past 1.0 by design — assert only the `t=0` boundary strictly for those two) |
| `test_vec2_normalize_unit_length` | `vec2_length(vec2_normalize((3, 4))) ≈ 1.0` |
| `test_vec2_normalize_zero_vector` | `vec2_normalize((0, 0))` does not raise (returns `(0, 0)`, documented edge case) |
| `test_vec2_dot_orthogonal` | `vec2_dot((1, 0), (0, 1)) == 0` |
| `test_vec2_distance_known_case` | `vec2_distance((0, 0), (3, 4)) == 5.0` |

### 4.2 `tests/test_asset_loader.py`

| Test | Assertion |
|---|---|
| `test_load_image_caches` | Calling `load_image(same_path)` twice returns the **same object** (`is` check) |
| `test_load_image_different_paths_different_objects` | Two different paths return different objects |
| `test_load_spritesheet_frame_count` | A spritesheet of known width/frame_w produces the expected `frame_count` |
| `test_load_missing_file_raises` | Loading a nonexistent path raises `FileNotFoundError` (not a silent `None`) |

### 4.3 `tests/test_input_manager.py`

| Test | Assertion |
|---|---|
| `test_pressed_only_first_frame` | Simulating a keydown event: `is_action_pressed()` is `True` on the frame of the event, `False` on the next frame while still held |
| `test_held_while_down` | `is_action_held()` is `True` for every frame the key remains down |
| `test_released_only_on_keyup_frame` | `is_action_released()` is `True` only on the frame of the keyup event |
| `test_no_action_when_unbound_key_pressed` | A keydown for a key not in `DEFAULT_KEYBOARD_BINDINGS` does not trigger any action |

---

## 5. Phase 3 Tests — Scene System

### 5.1 `tests/test_scene_manager.py`

| Test | Assertion |
|---|---|
| `test_push_calls_on_enter` | Pushing a scene calls its `on_enter()` exactly once |
| `test_push_calls_previous_on_pause` | Pushing scene B while A is current calls `A.on_pause()` |
| `test_pop_calls_on_exit_and_resume` | Popping B (with A below) calls `B.on_exit()` then `A.on_resume()` |
| `test_replace_does_not_call_pause_resume` | `replace()` calls `on_exit()`/`on_enter()` only — never `on_pause()`/`on_resume()` |
| `test_current_property_reflects_top` | `.current` always returns the most recently pushed (and not popped) scene |
| `test_pop_empty_stack_does_not_crash` | Calling `pop()` with no scenes on the stack either no-ops safely or raises a documented exception (assistant's choice, but must not crash silently into an inconsistent state — pick one behavior and assert it) |

---

## 6. Phase 4 Tests — Engine UI

### 6.1 `tests/test_hud.py`

| Test | Assertion |
|---|---|
| `test_heart_full_state` | `current_health = 5.0` → all 5 heart slots render as `"full"` |
| `test_heart_fraction_states` | `current_health = 2.6` → slot 0 and 1 are `"full"`, slot 2 is `"three_quarter"` (per `09_HUD_SPEC.md` §4.3 thresholds: 0.6 ≥ 0.50 → three-quarter), slots 3-4 are `"empty"` |
| `test_heart_zero_health` | `current_health = 0.0` → all 5 slots are `"empty"` |
| `test_hud_does_not_crash_without_player` | `HUD()` constructed and `.update(dt)`/`.draw(surface)` called with no `PLAYER_DAMAGED` ever emitted — no exception |
| `test_player_damaged_updates_health_display` | Emitting `PLAYER_DAMAGED` followed by `EventBus.dispatch()` changes the HUD's internal health-tracking value |

**Note:** This test file exercises the *heart-fraction algorithm* described in `09_HUD_SPEC.md` §4.3, which should be implemented as a small pure function (e.g., `_heart_slot_state(current_health: float, slot_index: int) -> str`) specifically so it is unit-testable without rendering a real `pygame.Surface`.

---

## 7. Phase 5 Tests — Player

### 7.1 `tests/test_player_physics.py`

| Test | Assertion |
|---|---|
| `test_gravity_applied_when_airborne` | After one `update(dt)` call with no ground beneath, `velocity.y` increases by `GRAVITY * dt` |
| `test_max_fall_speed_clamped` | After many update calls while falling, `velocity.y` never exceeds `PLAYER_MAX_FALL_SPEED` |
| `test_jump_sets_negative_velocity` | Triggering jump while grounded sets `velocity.y == PLAYER_JUMP_FORCE` |
| `test_coyote_time_allows_late_jump` | Jump input within `PLAYER_COYOTE_FRAMES` frames after leaving a platform edge still succeeds |
| `test_coyote_time_expires` | Jump input after `PLAYER_COYOTE_FRAMES` have elapsed since leaving the platform does NOT succeed |
| `test_jump_cut_halves_velocity` | Releasing jump while `velocity.y < 0` multiplies `velocity.y` by 0.5 on that frame |
| `test_horizontal_collision_stops_movement` | Moving into a solid rect zeroes `velocity.x` and positions the player at the rect's edge |
| `test_vertical_landing_sets_grounded` | Falling onto a solid rect from above sets `is_grounded = True` and `velocity.y = 0` |
| `test_one_way_platform_passable_from_below` | Moving upward through a `one_way` rect does not collide |
| `test_one_way_platform_solid_from_above` | Falling onto a `one_way` rect from above collides normally |

### 7.2 `tests/test_player_state_machine.py`

| Test | Assertion |
|---|---|
| `test_idle_to_walking_on_move_input` | Player in `IDLE` with horizontal input transitions to `WALKING` on next update |
| `test_walking_to_idle_on_input_release` | Player in `WALKING` with no input transitions to `IDLE` |
| `test_grounded_jump_input_to_jumping` | `IDLE`/`WALKING` + jump input → `JUMPING` |
| `test_jumping_to_falling_at_peak` | `JUMPING` transitions to `FALLING` once `velocity.y >= 0` |
| `test_falling_to_idle_on_land` | `FALLING` transitions to `IDLE` (or `WALKING` if horizontal input present) on landing |
| `test_crouch_locks_horizontal_velocity` | In `CROUCHING`, `velocity.x` is forced to `0` even with movement input held |
| `test_attack_state_locks_input` | While in `SHORT_ATTACK` or `LONG_ATTACK`, movement input is ignored until the animation completes |
| `test_damage_forces_hurt_state_from_any_non_dying_state` | Calling `apply_damage()` while in any state except `DYING` transitions to `HURT` |
| `test_health_zero_forces_dying_state` | `apply_damage()` that brings health to exactly `0.0` transitions to `DYING` regardless of current state |
| `test_dying_state_is_terminal` | No input or damage call changes state once `DYING` is entered |

### 7.3 `tests/test_player_damage.py`

| Test | Assertion |
|---|---|
| `test_damage_reduces_health` | `apply_damage(0.5, ...)` reduces `current_health` by exactly `0.5` |
| `test_damage_clamped_at_zero` | Repeated damage past `0.0` never makes `current_health` negative |
| `test_invincibility_blocks_repeat_damage` | A second `apply_damage()` call within the 1.5s invincibility window has no effect on `current_health` |
| `test_invincibility_expires` | After simulating 1.5s of elapsed time, a subsequent `apply_damage()` call succeeds |
| `test_player_died_emitted_at_zero_health` | `apply_damage()` that brings health to `0.0` causes `PLAYER_DIED` to be queued in the `EventBus` |
| `test_player_damaged_always_emitted_on_successful_hit` | Every non-blocked `apply_damage()` call queues `PLAYER_DAMAGED` with the correct `amount` and `source` |
| `test_knockback_velocity_applied` | After `apply_damage()`, `velocity` reflects the documented knockback values (150 px/s horizontal away from source, −200 px/s vertical) for the duration of the knockback window |

---

## 8. Phase 6 Tests — Enemies

### 8.1 `tests/test_enemy_walker.py`

| Test | Assertion |
|---|---|
| `test_patrol_reverses_at_patrol_limit` | Walker moving away from `patrol_origin` reverses direction once `abs(position.x - origin.x) >= patrol_length/2` |
| `test_ledge_detection_reverses_direction` | Walker approaching a platform edge (no floor tile ahead) reverses before stepping off |
| `test_alert_triggered_within_detection_range` | Player within `detection_range_x/y` causes `state` to become `ALERT` |
| `test_deaggro_on_player_leaving_extended_range` | Player leaving detection range + `deaggro_margin` causes `state` to revert to `PATROL` |
| `test_contact_damage_applied_once_per_cooldown` | Sustained hurtbox overlap with the player applies damage only once per the 0.3s cooldown window, not every frame |

### 8.2 `tests/test_enemy_flying.py`

| Test | Assertion |
|---|---|
| `test_sine_mode_y_oscillates` | Over several update calls in `"sine"` mode, `position.y` follows `origin.y + amplitude * sin(2π·frequency·t)` within floating tolerance |
| `test_bezier_mode_follows_precomputed_path` | In `"bezier"` mode, `position` after advancing `t` matches `CurveTools.sample_path()` applied to the precomputed path |
| `test_no_gravity_applied` | `EnemyFlying` never has `GRAVITY` applied to its vertical velocity, unlike `EnemyWalker` |

### 8.3 `tests/test_enemy_shooter.py`

| Test | Assertion |
|---|---|
| `test_fires_within_range_respecting_fire_rate` | A `Shooter` with player in range emits exactly one projectile per `1/fire_rate` seconds, not more |
| `test_no_fire_outside_detection_range` | No projectile spawned while player is outside `detection_range_x/y` |
| `test_projectile_angle_points_at_player` | The spawned `Projectile`'s velocity direction matches `atan2(player.y - shooter.y, player.x - shooter.x)` within tolerance |
| `test_projectile_expires_after_lifetime` | A `Projectile` with no collision becomes `is_active = False` after its `lifetime` seconds elapse |
| `test_projectile_expires_on_wall_collision` | A `Projectile` colliding with a solid tile rect immediately deactivates |

---

## 9. Phase 7 Tests — Stage System

### 9.1 `tests/test_stage_loader.py`

Uses `tests/fixtures/minimal_stage.tmx` — a hand-built TMX with exactly: all 8 required layers (minimal content), one `PlayerSpawn`, one `Walker`, one `Checkpoint`, one `NextTrigger`, a small `Collision` rect set.

| Test | Assertion |
|---|---|
| `test_load_returns_stage_data` | `StageLoader.load(fixture_path)` returns a `StageData` instance |
| `test_spawn_point_matches_tmx` | `StageData.spawn_point` matches the fixture's `PlayerSpawn` coordinates exactly |
| `test_collision_rects_nonempty` | `StageData.collision_rects` has at least one entry, matching the fixture's `Collision` layer objects |
| `test_walker_entity_spawned` | `StageData.entity_list` contains exactly one `EnemyWalker` instance at the fixture's coordinates |
| `test_checkpoint_registered` | `StageData.checkpoints` contains one `Checkpoint` with the fixture's `checkpoint_id` |
| `test_missing_player_spawn_raises` | Loading a TMX fixture with no `PlayerSpawn` object raises `FrameworkUsageError` |
| `test_missing_required_layer_raises` | Loading a TMX fixture missing e.g. the `Terrain` layer raises `FrameworkUsageError` |
| `test_duplicate_player_spawn_raises` | Loading a TMX fixture with two `PlayerSpawn` objects raises `FrameworkUsageError` |

### 9.2 `tests/test_camera.py`

| Test | Assertion |
|---|---|
| `test_follow_moves_offset_toward_target` | After several `update(dt)` calls, `camera.offset` approaches the followed entity's position (lerp convergence, not instant snap) |
| `test_world_to_screen_screen_to_world_inverse` | `screen_to_world(world_to_screen(p)) ≈ p` for an arbitrary point `p` |

### 9.3 `tests/test_checkpoint.py`

| Test | Assertion |
|---|---|
| `test_activates_once_on_player_overlap` | First overlap emits `CHECKPOINT_REACHED`; `is_active` becomes `True` |
| `test_does_not_reactivate_on_repeat_overlap` | A second overlap after activation does not emit a second `CHECKPOINT_REACHED` |

---

## 10. Phase 8 Tests — ColorTools and CurveTools

### 10.1 `tests/test_color_tools.py`

| Test | Assertion |
|---|---|
| `test_rgb_hsv_round_trip` | For 1000 random `(r,g,b)` triples, `hsv_to_rgb(*rgb_to_hsv(r,g,b))` is within ±1 per channel of the original |
| `test_rgb_hsl_round_trip` | Same property test for HSL |
| `test_rgb_cmyk_round_trip` | Same property test for CMYK |
| `test_known_color_red` | `rgb_to_hsv(255, 0, 0) ≈ (0.0, 1.0, 1.0)` |
| `test_known_color_white` | `rgb_to_hsv(255, 255, 255) ≈ (0.0, 0.0, 1.0)` (hue undefined/0 at zero saturation) |
| `test_alpha_blend_full_opacity` | `alpha_blend(src, dst, 1.0)` equals `src` pixel-for-pixel |
| `test_alpha_blend_zero_opacity` | `alpha_blend(src, dst, 0.0)` equals `dst` pixel-for-pixel |
| `test_surface_array_round_trip` | `array_to_surface(surface_to_array(s))` produces a surface with identical pixel data to `s` |

### 10.2 `tests/test_curve_tools.py`

| Test | Assertion |
|---|---|
| `test_bezier_linear_degenerate_case` | A 2-control-point Bézier (degree 1) produces a straight line; sampled midpoint equals the arithmetic midpoint of the two control points |
| `test_bezier_endpoint_interpolation` | A Bézier curve always passes exactly through its first and last control points (`t=0` and `t=1`) |
| `test_bezier_symmetric_quadratic` | A 3-point symmetric Bézier (control points at `(0,0)`, `(50,100)`, `(100,0)`) has its midpoint sample at `x=50`, `y=50` (known geometric property of the quadratic Bézier with this configuration) |
| `test_bezier_sample_count` | `bezier(points, n_samples=50)` returns a list of exactly 50 tuples |
| `test_sample_path_interpolates` | `sample_path(points, 0.5)` returns a value between the two points straddling the 50% arc-length mark |
| `test_catmull_rom_passes_through_control_points` | The Catmull-Rom curve passes through each interior control point at the corresponding `t` |

---

## 11. Phase 9 Tests — Stage 0 (Integration)

No new isolated unit test file — Stage 0's Definition of Done in `25_IMPLEMENTATION_ROADMAP.md` §12 is itself the test, executed as a **manual playthrough checklist**. However, the following **automatable smoke test** must exist:

### 11.1 `tests/test_stage0_smoke.py`

| Test | Assertion |
|---|---|
| `test_stage0_loads_without_exception` | `StageLoader.load(STAGES_DIR / "stage0" / "stage0.tmx")` completes without raising |
| `test_stage0_has_five_checkpoints` | `len(StageData.checkpoints) == 5`, matching `07_STAGE0_DESIGN.md` §7 |
| `test_stage0_has_next_trigger` | `StageData.next_trigger is not None` |
| `test_stage0_enemy_count_matches_design` | `len(StageData.entity_list)` matches the total enemy count in `07_STAGE0_DESIGN.md` §6 (12 enemies) |

---

## 12. Phase 10 Tests — FilterTools

### 12.1 `tests/test_filter_tools.py`

Uses `tests/fixtures/reference_sprite_32x32.png` as a known input. Saves visual output to `tests/output/filter/` for each test (filename pattern: `{test_name}.png`) for human spot-check, in addition to the programmatic assertion.

| Test | Assertion |
|---|---|
| `test_compute_histogram_total_pixels` | `total_pixels == width * height` of the input surface |
| `test_compute_histogram_sums_correctly` | `sum(hist['r']) == total_pixels` (every pixel counted exactly once per channel) |
| `test_adjust_brightness_factor_one_is_identity` | `adjust_brightness(s, 1.0)` produces pixel values equal to the original (±1 rounding tolerance) |
| `test_adjust_brightness_factor_zero_is_black` | `adjust_brightness(s, 0.0)` produces an all-black surface |
| `test_adjust_brightness_out_of_range_raises` | `factor=4.1` or `factor=-0.1` raises `ValueError` |
| `test_adjust_contrast_factor_one_is_identity` | Same identity property as brightness |
| `test_apply_kernel_identity_kernel_is_noop` | `apply_kernel(s, get_standard_kernel('identity'))` equals the input (±1 rounding tolerance) |
| `test_apply_kernel_invalid_shape_raises` | A non-square or even-sized kernel raises `ValueError` |
| `test_get_standard_kernel_unknown_name_raises` | `get_standard_kernel('not_a_kernel')` raises `KeyError` |
| `test_gaussian_blur_reduces_variance` | The pixel-value variance of a noisy input surface decreases after `gaussian_blur` (blur smooths) |
| `test_gaussian_blur_invalid_sigma_raises` | `sigma=0.0` or `sigma=10.1` raises `ValueError` |
| `test_sobel_edge_flat_surface_near_zero` | A uniform-color input produces a near-black (no-edge) Sobel output |
| `test_sobel_edge_high_contrast_edge_detected` | A surface with a sharp half-black/half-white vertical split produces a bright vertical line in the Sobel output at the boundary |
| `test_canny_edge_invalid_thresholds_raises` | `low >= high` raises `ValueError` |
| `test_canny_edge_output_is_binary` | Every pixel in the Canny output is either `(0,0,0)` or `(255,255,255)` |

---

## 13. Phase 11 Tests — VisionTools

### 13.1 `tests/test_vision_tools.py`

| Test | Assertion |
|---|---|
| `test_threshold_binary_known_split` | A surface that is exactly half below and half above the threshold produces the expected black/white split |
| `test_threshold_otsu_returns_tuple` | Return value unpacks as `(pygame.Surface, int)` |
| `test_threshold_otsu_threshold_in_range` | The returned threshold is in `[0, 255]` |
| `test_erode_shrinks_white_region` | After erosion, the white pixel count in the mask is `<=` the pre-erosion count |
| `test_dilate_grows_white_region` | After dilation, the white pixel count is `>=` the pre-dilation count |
| `test_open_removes_small_noise` | A mask with a single isolated 1-pixel white speck has zero white pixels after `morphological_open` with `kernel_size=3` |
| `test_close_fills_small_hole` | A mask with a single isolated 1-pixel black hole inside a white region has the hole filled after `morphological_close` |
| `test_connected_components_count` | A mask with 3 visually separated white blobs produces `num_components == 3` |
| `test_connected_components_background_is_zero` | `label_array` background pixels are always `0` |
| `test_filter_components_by_area_excludes_outliers` | A component smaller than `min_area` is absent from the filtered result |
| `test_analyze_regions_sorted_descending` | Returned `list[RegionInfo]` has non-increasing `.area` values |
| `test_largest_region_matches_first_of_analyze_regions` | `largest_region(mask) == analyze_regions(mask)[0]` (or `None` for both on an empty mask) |
| `test_watershed_returns_tuple` | Return value unpacks as `(pygame.Surface, np.ndarray)` |
| `test_extract_hog_output_length` | `extract_hog(surface).shape == (512,)` regardless of input surface size (canonical resize) |
| `test_extract_lbp_output_length` | `extract_lbp(surface).shape == (256,)` |
| `test_extract_color_histogram_output_length` | `extract_color_histogram(surface, bins=64).shape == (192,)` (64×3) |
| `test_extract_features_method_dispatch` | `extract_features(s, method='hog')` produces output identical to calling `extract_hog(s)` directly |
| `test_bounding_boxes_count_matches_components` | `len(bounding_boxes_from_mask(mask)) == connected_components(mask).num_components` |

---

## 14. Phase 12 Tests — PatternRecognitionTools

### 14.1 `tests/test_pattern_recognition_tools.py`

Uses `tests/fixtures/sample_dataset_tiny.npz` — a small synthetic dataset (e.g., 30 samples, 2 classes, 16-dimensional features) kept separate from the full `assets/datasets/sample_dataset.npz` so tests run fast.

| Test | Assertion (run once per `model_type` in `{"knn", "tree", "forest", "svm"}` via `pytest.mark.parametrize`) |
|---|---|
| `test_train_returns_trained_model` | `train(X, y, model_type)` returns a `TrainedModel` with `.model_type` matching the input |
| `test_train_feature_length_matches_input` | `.feature_length == X.shape[1]` |
| `test_train_classes_match_unique_labels` | `set(.classes) == set(y.tolist())` (as strings) |
| `test_evaluate_returns_evaluation_result` | `.accuracy` is in `[0.0, 1.0]` |
| `test_evaluate_confusion_matrix_shape` | `confusion_matrix.shape == (n_classes, n_classes)` |
| `test_save_load_round_trip_identical_predictions` | A model saved then loaded produces identical `classify()` output on the same input vector as the pre-save model |
| `test_classify_returns_known_class` | `classify(features, model)` returns a string present in `model.classes` |
| `test_classify_wrong_feature_length_raises` | Passing a feature vector of the wrong length raises `ValueError` |
| `test_classify_proba_sums_to_one` | `sum(classify_proba(features, model).values()) ≈ 1.0` (skipped/xfail for `model_type == "tree"` per documented `NotImplementedError`) |
| `test_predict_matches_manual_extract_then_classify` | `predict(model, surface, method)` equals `classify(extract_features(surface, method), model)` |

| Additional non-parametrized tests | Assertion |
|---|---|
| `test_register_and_get_model` | `get_model(name)` returns the exact object passed to `register_model(name, ...)` |
| `test_get_unregistered_model_raises` | `get_model("nonexistent")` raises `KeyError` |
| `test_list_models_reflects_registry` | `list_models()` contains every name passed to `register_model()` |
| `test_train_minimum_samples_enforced` | Training with fewer than 10 total samples raises `ValueError` |
| `test_train_minimum_classes_enforced` | Training with only 1 distinct class raises `ValueError` |

---

## 15. Phase 14 Tests — BossBase

### 15.1 `tests/test_boss_base.py`

| Test | Assertion |
|---|---|
| `test_starts_at_phase_zero` | A freshly constructed boss has `current_phase == 0` |
| `test_phase_transition_at_health_threshold` | Reducing health below `phases[0].health_threshold` advances `current_phase` to `1` |
| `test_invincible_during_transition` | While `is_transitioning == True`, `apply_hit()` does not reduce health further |
| `test_boss_phase_changed_event_emitted` | A phase transition queues `BOSS_PHASE_CHANGED` with the correct new `phase` value |
| `test_transition_timer_counts_down` | `transition_timer` decreases each `update(dt)` call during a transition and `is_transitioning` becomes `False` once it reaches `0` |
| `test_final_phase_has_no_further_transition` | Reducing health to `0` in the last phase triggers death handling (`EnemyBase._die()` behavior), not another phase transition |

---

## 16. Test Execution Summary Table

Cross-reference back to `25_IMPLEMENTATION_ROADMAP.md` phase gates:

| Phase | Test File(s) | Must Pass Before |
|---|---|---|
| 1 | `test_event_bus.py`, `test_clock.py` | Phase 2 begins |
| 2 | `test_math_utils.py`, `test_asset_loader.py`, `test_input_manager.py` | Phase 3 begins |
| 3 | `test_scene_manager.py` | Phase 4 begins |
| 4 | `test_hud.py` | Phase 5 begins |
| 5 | `test_player_physics.py`, `test_player_state_machine.py`, `test_player_damage.py` | Phase 6 begins |
| 6 | `test_enemy_walker.py`, `test_enemy_flying.py` (sine mode only until Phase 8), `test_enemy_shooter.py` | Phase 7 begins |
| 7 | `test_stage_loader.py`, `test_camera.py`, `test_checkpoint.py` | Phase 8 begins |
| 8 | `test_color_tools.py`, `test_curve_tools.py` + completion of `test_enemy_flying.py` Bézier/patrol cases | Phase 9 begins |
| 9 | `test_stage0_smoke.py` + manual playthrough checklist | Phases 10-14 begin |
| 10 | `test_filter_tools.py` | Phase 13 begins (needs 10+11+12) |
| 11 | `test_vision_tools.py` | Phase 13 begins |
| 12 | `test_pattern_recognition_tools.py` | Phase 13 begins |
| 13 | Manual smoke test only (see §2.2) | Phase 14 begins |
| 14 | `test_boss_base.py` | Phase 15 begins |
| 15 | Manual 15-minute onboarding test (see `26_STUDENT_TEMPLATE_SPEC.md` §8) | Phase 16 begins |
| 16 | Full suite, zero failures | Project considered implementation-complete |

---

## 17. Running the Suite

```bash
# Full suite
pytest tests/ -v

# Single phase gate, e.g. before starting Phase 6:
pytest tests/test_enemy_walker.py tests/test_enemy_flying.py tests/test_enemy_shooter.py -v

# With coverage (optional, not a hard gate, but useful for the professor to spot-check):
pytest tests/ --cov=src --cov-report=term-missing
```

No test in this plan requires a display/windowing system — all tests must run headless (`SDL_VIDEODRIVER=dummy` if needed for any `pygame.display` calls triggered indirectly via `App` construction in integration-style tests).


---
## 🔗 Documentos Relacionados

- [[22_API_CONTRACTS.md|API Contracts]]
- [[23_DATA_SCHEMAS.md|Data Schemas]]

---
--- Traducción al Español ---

*This document is also available in English above.*

# Legacy of InFest — Plan de Pruebas

**ID del Documento:** LOI-TESTPLAN-024
**Versión:** 1.0.0
**Estado:** Oficial
**Compatibilidad:** Requiere 22_API_CONTRACTS.md, 23_DATA_SCHEMAS.md, 25_IMPLEMENTATION_ROADMAP.md
**Audiencia:** Asistentes de codificación IA (Claude Code, Cline, OpenCode, Codex)

---

## 1. Propósito

25_IMPLEMENTATION_ROADMAP.md referencia archivos de prueba específicos (tests/test_clock.py, tests/test_player_physics.py, etc.) en la Definición de Terminado de cada fase sin especificar su contenido. Este documento especifica **exactamente qué debe verificar cada archivo de prueba**, para que un asistente IA pueda escribir las pruebas sin adivinar qué significa "pasar", y para que un revisor humano pueda confirmar que una fase está genuinamente completa en lugar de superficialmente completa.

---

## 2. Filosofía y Alcance de las Pruebas

### 2.1 Qué Se Prueba Automáticamente

- Funciones puras y clases de datos puros (módulos de matemáticas, color, curva, filtro, visión, reconocimiento de patrones)
- Lógica de transición de máquina de estados (Player, Enemy, Boss — corrección de transición, no renderizado visual)
- Corrección de forma y campos de estructura de datos (resultados de análisis TMX, ComponentResult, RegionInfo, TrainedModel)
- Viajes de ida y vuelta de serialización (guardar/cargar modelo)
- Corrección de despacho del bus de eventos

### 2.2 Qué NO Se Prueba Automáticamente

- Renderizado visual píxel perfecto (apariencia de sprite, suavidad de animación)
- Corrección de reproducción de audio (el archivo se reproduce, suena correcto — verificado por escucha manual)
- Benchmarks de rendimiento/tasa de fotogramas (registrado para conciencia, no una puerta CI — ver sección 7)
- Diseños visuales de escenas de demostración (las 10 escenas — 7 laboratorios teóricos + 3 demostraciones académicas — verificadas por pruebas de humo automatizadas de importar/instanciar/dibujar en test_demo_scenes.py, más verificación visual manual por DoDs de fase)
- Equilibrio/sensación de combate completo de jefes (verificado por juego manual)

### 2.3 Marco de Pruebas

Todas las pruebas usan pytest. Los archivos de prueba viven bajo tests/, reflejando la estructura del paquete src/:

tests/
  test_event_bus.py
  test_clock.py
  test_math_utils.py
  test_asset_loader.py
  test_input_manager.py
  test_scene_manager.py
  test_hud.py
  test_player_physics.py
  test_player_state_machine.py
  test_player_damage.py
  test_enemy_walker.py
  test_enemy_flying.py
  test_enemy_shooter.py
  test_stage_loader.py
  test_camera.py
  test_checkpoint.py
  test_color_tools.py
  test_curve_tools.py
  test_filter_tools.py
  test_vision_tools.py
  test_pattern_recognition_tools.py
  test_boss_base.py
  test_demo_scenes.py     # Las 10 escenas demo/lab: importar, instanciar, dibujar
  fixtures/
    minimal_stage.tmx
    reference_sprite_32x32.png
    sample_dataset_tiny.npz
  output/
    filter/
    vision/
    demo/

tests/output/ está en gitignore (PNGs generados para verificación visual puntual) pero los directorios mismos deben existir (.gitkeep).

---

## 3. Pruebas de la Fase 1 — Núcleo del Motor

### 3.1 tests/test_event_bus.py

| Prueba | Afirmación |
|---|---|
| test_subscribe_and_emit | Un callback suscrito recibe los kwargs **data exactos pasados a emit() |
| test_emit_queues_not_immediate | Llamar a emit() no invoca el callback hasta que se llama a dispatch() |
| test_unsubscribe_stops_delivery | Después de unsubscribe(), un emit() + dispatch() posterior no invoca el callback |
| test_multiple_subscribers | Dos callbacks suscritos al mismo evento ambos lo reciben |
| test_unrelated_event_not_delivered | Un callback suscrito a FOO no se dispara cuando se emite BAR |

### 3.2 tests/test_clock.py

| Prueba | Afirmación |
|---|---|
| test_tick_returns_float | DeltaClock().tick() devuelve un float >= 0.0 |
| test_time_scale_applied | Establecer time_scale = 0.5 reduce a la mitad el delta devuelto en el próximo tick() (dentro de tolerancia de punto flotante) |
| test_fps_property_nonzero_after_tick | .fps es > 0 después de al menos una llamada a tick() |

---

## 4. Pruebas de la Fase 2 — Entrada / Audio / Utilidades

### 4.1 tests/test_math_utils.py

| Prueba | Afirmación |
|---|---|
| test_lerp_endpoints | lerp(0, 10, 0.0) == 0, lerp(0, 10, 1.0) == 10 |
| test_lerp_midpoint | lerp(0, 10, 0.5) == 5 |
| test_clamp_below_min | clamp(-5, 0, 10) == 0 |
| test_clamp_above_max | clamp(15, 0, 10) == 10 |
| test_clamp_within_range | clamp(5, 0, 10) == 5 |
| test_ease_functions_boundary | Cada función ease_* devuelve aproximadamente 0.0 en t=0.0 y aproximadamente 1.0 en t=1.0 |
| test_vec2_normalize_unit_length | vec2_length(vec2_normalize((3, 4))) aproximadamente 1.0 |
| test_vec2_normalize_zero_vector | vec2_normalize((0, 0)) no lanza excepción (devuelve (0, 0), caso extremo documentado) |
| test_vec2_dot_orthogonal | vec2_dot((1, 0), (0, 1)) == 0 |
| test_vec2_distance_known_case | vec2_distance((0, 0), (3, 4)) == 5.0 |

### 4.2 tests/test_asset_loader.py

| Prueba | Afirmación |
|---|---|
| test_load_image_caches | Llamar a load_image(misma_ruta) dos veces devuelve el mismo objeto (verificación is) |
| test_load_image_different_paths_different_objects | Dos rutas diferentes devuelven objetos diferentes |
| test_load_spritesheet_frame_count | Una hoja de sprites de ancho/frame_w conocido produce el frame_count esperado |
| test_load_missing_file_raises | Cargar una ruta inexistente lanza FileNotFoundError (no un None silencioso) |

### 4.3 tests/test_input_manager.py

| Prueba | Afirmación |
|---|---|
| test_pressed_only_first_frame | Simular un evento keydown: is_action_pressed() es True en el fotograma del evento, False en el próximo fotograma mientras aún está presionado |
| test_held_while_down | is_action_held() es True para cada fotograma que la tecla permanece presionada |
| test_released_only_on_keyup_frame | is_action_released() es True solo en el fotograma del evento keyup |
| test_no_action_when_unbound_key_pressed | Un keydown para una tecla no en DEFAULT_KEYBOARD_BINDINGS no dispara ninguna acción |

---

## 5. Pruebas de la Fase 3 — Sistema de Escenas

### 5.1 tests/test_scene_manager.py

| Prueba | Afirmación |
|---|---|
| test_push_calls_on_enter | Empujar una escena llama a su on_enter() exactamente una vez |
| test_push_calls_previous_on_pause | Empujar la escena B mientras A es actual llama a A.on_pause() |
| test_pop_calls_on_exit_and_resume | Extraer B (con A debajo) llama a B.on_exit() luego A.on_resume() |
| test_replace_does_not_call_pause_resume | replace() llama a on_exit()/on_enter() solamente — nunca on_pause()/on_resume() |
| test_current_property_reflects_top | .current siempre devuelve la escena más recientemente empujada (y no extraída) |
| test_pop_empty_stack_does_not_crash | Llamar a pop() sin escenas en la pila o no hace nada de forma segura o lanza una excepción documentada |

---

## 6. Pruebas de la Fase 4 — UI del Motor

### 6.1 tests/test_hud.py

| Prueba | Afirmación |
|---|---|
| test_heart_full_state | current_health = 5.0 → los 5 espacios de corazón se renderizan como llenos |
| test_heart_fraction_states | current_health = 2.6 → los espacios 0 y 1 están llenos, el espacio 2 está en tres_cuartos, los espacios 3-4 están vacíos |
| test_heart_zero_health | current_health = 0.0 → los 5 espacios están vacíos |
| test_hud_does_not_crash_without_player | HUD() construido y .update(dt)/.draw(surface) llamados sin que PLAYER_DAMAGED se haya emitido nunca — sin excepción |
| test_player_damaged_updates_health_display | Emitir PLAYER_DAMAGED seguido de EventBus.dispatch() cambia el valor interno de seguimiento de salud del HUD |

**Nota:** Este archivo de prueba ejercita el *algoritmo de fracción de corazón* descrito en 09_HUD_SPEC.md sección 4.3.

---

## 7. Pruebas de la Fase 5 — Jugador

### 7.1 tests/test_player_physics.py

| Prueba | Afirmación |
|---|---|
| test_gravity_applied_when_airborne | Después de una llamada a update(dt) sin suelo debajo, velocity.y aumenta en GRAVITY * dt |
| test_max_fall_speed_clamped | Después de muchas llamadas de update mientras cae, velocity.y nunca excede PLAYER_MAX_FALL_SPEED |
| test_jump_sets_negative_velocity | Disparar salto mientras está en el suelo establece velocity.y == PLAYER_JUMP_FORCE |
| test_coyote_time_allows_late_jump | Entrada de salto dentro de PLAYER_COYOTE_FRAMES fotogramas después de dejar un borde de plataforma todavía tiene éxito |
| test_coyote_time_expires | Entrada de salto después de que hayan transcurrido PLAYER_COYOTE_FRAMES desde dejar la plataforma NO tiene éxito |
| test_jump_cut_halves_velocity | Soltar salto mientras velocity.y < 0 multiplica velocity.y por 0.5 en ese fotograma |
| test_horizontal_collision_stops_movement | Moverse hacia un rect sólido pone a cero velocity.x y posiciona al jugador en el borde del rect |
| test_vertical_landing_sets_grounded | Caer sobre un rect sólido desde arriba establece is_grounded = True y velocity.y = 0 |
| test_one_way_platform_passable_from_below | Moverse hacia arriba a través de un rect one_way no colisiona |
| test_one_way_platform_solid_from_above | Caer sobre un rect one_way desde arriba colisiona normalmente |

### 7.2 tests/test_player_state_machine.py

| Prueba | Afirmación |
|---|---|
| test_idle_to_walking_on_move_input | Jugador en IDLE con entrada horizontal transiciona a WALKING en la próxima actualización |
| test_walking_to_idle_on_input_release | Jugador en WALKING sin entrada transiciona a IDLE |
| test_grounded_jump_input_to_jumping | IDLE/WALKING + entrada de salto a JUMPING |
| test_jumping_to_falling_at_peak | JUMPING transiciona a FALLING una vez que velocity.y >= 0 |
| test_falling_to_idle_on_land | FALLING transiciona a IDLE (o WALKING si hay entrada horizontal presente) al aterrizar |
| test_crouch_locks_horizontal_velocity | En CROUCHING, velocity.x se fuerza a 0 incluso con entrada de movimiento mantenida |
| test_attack_state_locks_input | Mientras está en SHORT_ATTACK o LONG_ATTACK, la entrada de movimiento se ignora hasta que la animación se completa |
| test_damage_forces_hurt_state_from_any_non_dying_state | Llamar a apply_damage() mientras está en cualquier estado excepto DYING transiciona a HURT |
| test_health_zero_forces_dying_state | apply_damage() que lleva la salud exactamente a 0.0 transiciona a DYING independientemente del estado actual |
| test_dying_state_is_terminal | Ninguna entrada o llamada de daño cambia el estado una vez que se entra a DYING |

### 7.3 tests/test_player_damage.py

| Prueba | Afirmación |
|---|---|
| test_damage_reduces_health | apply_damage(0.5, ...) reduce current_health exactamente en 0.5 |
| test_damage_clamped_at_zero | Daño repetido más allá de 0.0 nunca hace que current_health sea negativo |
| test_invincibility_blocks_repeat_damage | Una segunda llamada a apply_damage() dentro de la ventana de invencibilidad de 1.5s no tiene efecto en current_health |
| test_invincibility_expires | Después de simular 1.5s de tiempo transcurrido, una llamada subsiguiente a apply_damage() tiene éxito |
| test_player_died_emitted_at_zero_health | apply_damage() que lleva la salud a 0.0 hace que PLAYER_DIED se ponga en cola en el EventBus |
| test_player_damaged_always_emitted_on_successful_hit | Cada llamada no bloqueada a apply_damage() pone en cola PLAYER_DAMAGED con la cantidad y fuente correctas |
| test_knockback_velocity_applied | Después de apply_damage(), velocity refleja los valores de retroceso documentados |

---

## 8. Pruebas de la Fase 6 — Enemigos

### 8.1 tests/test_enemy_walker.py

| Prueba | Afirmación |
|---|---|
| test_patrol_reverses_at_patrol_limit | Walker moviéndose lejos de patrol_origin invierte la dirección una vez que abs(position.x - origin.x) >= patrol_length/2 |
| test_ledge_detection_reverses_direction | Walker acercándose a un borde de plataforma (sin tile de suelo adelante) invierte antes de salir |
| test_alert_triggered_within_detection_range | Jugador dentro de detection_range_x/y causa que el estado se convierta en ALERT |
| test_deaggro_on_player_leaving_extended_range | Jugador saliendo del rango de detección + deaggro_margin causa que el estado vuelva a PATROL |
| test_contact_damage_applied_once_per_cooldown | Superposición sostenida de hurtbox con el jugador aplica daño solo una vez por la ventana de enfriamiento de 0.3s, no cada fotograma |

### 8.2 tests/test_enemy_flying.py

| Prueba | Afirmación |
|---|---|
| test_sine_mode_y_oscillates | En varias llamadas de update en modo sine, position.y sigue origin.y + amplitude * sin(2*pi*frequency*t) dentro de tolerancia de punto flotante |
| test_bezier_mode_follows_precomputed_path | En modo bezier, position después de avanzar t coincide con CurveTools.sample_path() aplicada a la ruta precomputada |
| test_no_gravity_applied | EnemyFlying nunca tiene GRAVITY aplicada a su velocidad vertical, a diferencia de EnemyWalker |

### 8.3 tests/test_enemy_shooter.py

| Prueba | Afirmación |
|---|---|
| test_fires_within_range_respecting_fire_rate | Un Shooter con jugador en rango emite exactamente un proyectil por cada 1/fire_rate segundos, no más |
| test_no_fire_outside_detection_range | No se genera ningún proyectil mientras el jugador está fuera de detection_range_x/y |
| test_projectile_angle_points_at_player | La dirección de velocidad del Projectile generado coincide con atan2(player.y - shooter.y, player.x - shooter.x) dentro de tolerancia |
| test_projectile_expires_after_lifetime | Un Projectile sin colisión se vuelve is_active = False después de que transcurren sus segundos de lifetime |
| test_projectile_expires_on_wall_collision | Un Projectile que colisiona con un rect de tile sólido se desactiva inmediatamente |

---

## 9. Pruebas de la Fase 7 — Sistema de Nivel

### 9.1 tests/test_stage_loader.py

Usa tests/fixtures/minimal_stage.tmx — un TMX construido manualmente con exactamente: las 8 capas requeridas (contenido mínimo), un PlayerSpawn, un Walker, un Checkpoint, un NextTrigger, un pequeño conjunto de rects Collision.

| Prueba | Afirmación |
|---|---|
| test_load_returns_stage_data | StageLoader.load(fixture_path) devuelve una instancia de StageData |
| test_spawn_point_matches_tmx | StageData.spawn_point coincide exactamente con las coordenadas de PlayerSpawn del fixture |
| test_collision_rects_nonempty | StageData.collision_rects tiene al menos una entrada, coincidiendo con los objetos de la capa Collision del fixture |
| test_walker_entity_spawned | StageData.entity_list contiene exactamente una instancia de EnemyWalker en las coordenadas del fixture |
| test_checkpoint_registered | StageData.checkpoints contiene un Checkpoint con el checkpoint_id del fixture |
| test_missing_player_spawn_raises | Cargar un fixture TMX sin objeto PlayerSpawn lanza FrameworkUsageError |
| test_missing_required_layer_raises | Cargar un fixture TMX que falta, ej. la capa Terrain, lanza FrameworkUsageError |
| test_duplicate_player_spawn_raises | Cargar un fixture TMX con dos objetos PlayerSpawn lanza FrameworkUsageError |

### 9.2 tests/test_camera.py

| Prueba | Afirmación |
|---|---|
| test_follow_moves_offset_toward_target | Después de varias llamadas a update(dt), camera.offset se acerca a la posición de la entidad seguida (convergencia lerp, no instantánea) |
| test_world_to_screen_screen_to_world_inverse | screen_to_world(world_to_screen(p)) aproximadamente p para un punto p arbitrario |

### 9.3 tests/test_checkpoint.py

| Prueba | Afirmación |
|---|---|
| test_activates_once_on_player_overlap | La primera superposición emite CHECKPOINT_REACHED; is_active se vuelve True |
| test_does_not_reactivate_on_repeat_overlap | Una segunda superposición después de la activación no emite un segundo CHECKPOINT_REACHED |

---

## 10. Pruebas de la Fase 8 — ColorTools y CurveTools

### 10.1 tests/test_color_tools.py

| Prueba | Afirmación |
|---|---|
| test_rgb_hsv_round_trip | Para 1000 triples (r,g,b) aleatorios, hsv_to_rgb(*rgb_to_hsv(r,g,b)) está dentro de +/-1 por canal del original |
| test_rgb_hsl_round_trip | Misma prueba de propiedad para HSL |
| test_rgb_cmyk_round_trip | Misma prueba de propiedad para CMYK |
| test_known_color_red | rgb_to_hsv(255, 0, 0) aproximadamente (0.0, 1.0, 1.0) |
| test_known_color_white | rgb_to_hsv(255, 255, 255) aproximadamente (0.0, 0.0, 1.0) |
| test_alpha_blend_full_opacity | alpha_blend(src, dst, 1.0) es igual a src píxel por píxel |
| test_alpha_blend_zero_opacity | alpha_blend(src, dst, 0.0) es igual a dst píxel por píxel |
| test_surface_array_round_trip | array_to_surface(surface_to_array(s)) produce una superficie con datos de píxel idénticos a s |

### 10.2 tests/test_curve_tools.py

| Prueba | Afirmación |
|---|---|
| test_bezier_linear_degenerate_case | Una Bézier de 2 puntos de control (grado 1) produce una línea recta; el punto medio muestreado es igual al punto medio aritmético de los dos puntos de control |
| test_bezier_endpoint_interpolation | Una curva Bézier siempre pasa exactamente a través de su primer y último punto de control (t=0 y t=1) |
| test_bezier_symmetric_quadratic | Una Bézier cuadrática simétrica de 3 puntos tiene su punto medio muestreado en x=50, y=50 |
| test_bezier_sample_count | bezier(points, n_samples=50) devuelve una lista de exactamente 50 tuplas |
| test_sample_path_interpolates | sample_path(points, 0.5) devuelve un valor entre los dos puntos que rodean la marca del 50% de longitud de arco |
| test_catmull_rom_passes_through_control_points | La curva Catmull-Rom pasa a través de cada punto de control interior en el t correspondiente |

---

## 11. Pruebas de la Fase 9 — Nivel 0 (Integración)

Ningún archivo de prueba unitaria aislada nuevo — la Definición de Terminado del Nivel 0 en 25_IMPLEMENTATION_ROADMAP.md sección 12 es en sí misma la prueba, ejecutada como una **lista de verificación de juego manual**. Sin embargo, la siguiente **prueba de humo automatizable** debe existir:

### 11.1 tests/test_stage0_smoke.py

| Prueba | Afirmación |
|---|---|
| test_stage0_loads_without_exception | StageLoader.load(STAGES_DIR / "stage0" / "stage0.tmx") se completa sin lanzar |
| test_stage0_has_five_checkpoints | len(StageData.checkpoints) == 5, coincidiendo con 07_STAGE0_DESIGN.md sección 7 |
| test_stage0_has_next_trigger | StageData.next_trigger is not None |
| test_stage0_enemy_count_matches_design | len(StageData.entity_list) coincide con el conteo total de enemigos en 07_STAGE0_DESIGN.md sección 6 (12 enemigos) |

---

## 12. Pruebas de la Fase 10 — FilterTools

### 12.1 tests/test_filter_tools.py

Usa tests/fixtures/reference_sprite_32x32.png como entrada conocida. Guarda la salida visual en tests/output/filter/ para cada prueba (patrón de nombre de archivo: {test_name}.png) para verificación humana, además de la afirmación programática.

| Prueba | Afirmación |
|---|---|
| test_compute_histogram_total_pixels | total_pixels == ancho * alto de la superficie de entrada |
| test_compute_histogram_sums_correctly | sum(hist[r]) == total_pixels (cada píxel contado exactamente una vez por canal) |
| test_adjust_brightness_factor_one_is_identity | adjust_brightness(s, 1.0) produce valores de píxel iguales al original (+/-1 tolerancia de redondeo) |
| test_adjust_brightness_factor_zero_is_black | adjust_brightness(s, 0.0) produce una superficie completamente negra |
| test_adjust_brightness_out_of_range_raises | factor=4.1 o factor=-0.1 lanza ValueError |
| test_adjust_contrast_factor_one_is_identity | Misma propiedad de identidad que el brillo |
| test_apply_kernel_identity_kernel_is_noop | apply_kernel(s, get_standard_kernel('identity')) es igual a la entrada (+/-1 tolerancia de redondeo) |
| test_apply_kernel_invalid_shape_raises | Un kernel no cuadrado o de tamaño par lanza ValueError |
| test_get_standard_kernel_unknown_name_raises | get_standard_kernel('not_a_kernel') lanza KeyError |
| test_gaussian_blur_reduces_variance | La varianza del valor de píxel de una superficie de entrada ruidosa disminuye después de gaussian_blur |
| test_gaussian_blur_invalid_sigma_raises | sigma=0.0 o sigma=10.1 lanza ValueError |
| test_sobel_edge_flat_surface_near_zero | Una entrada de color uniforme produce una salida Sobel casi negra (sin bordes) |
| test_sobel_edge_high_contrast_edge_detected | Una superficie con una división vertical nítida mitad negra/mitad blanca produce una línea vertical brillante en la salida Sobel en el límite |
| test_canny_edge_invalid_thresholds_raises | low >= high lanza ValueError |
| test_canny_edge_output_is_binary | Cada píxel en la salida Canny es (0,0,0) o (255,255,255) |

---

## 13. Pruebas de la Fase 11 — VisionTools

### 13.1 tests/test_vision_tools.py

| Prueba | Afirmación |
|---|---|
| test_threshold_binary_known_split | Una superficie que está exactamente mitad debajo y mitad encima del umbral produce la división blanco/negro esperada |
| test_threshold_otsu_returns_tuple | El valor de retorno se desempaqueta como (pygame.Surface, int) |
| test_threshold_otsu_threshold_in_range | El umbral devuelto está en [0, 255] |
| test_erode_shrinks_white_region | Después de la erosión, el conteo de píxeles blancos en la máscara es <= al conteo antes de la erosión |
| test_dilate_grows_white_region | Después de la dilatación, el conteo de píxeles blancos es >= al conteo antes de la dilatación |
| test_open_removes_small_noise | Una máscara con una mota blanca aislada de 1 píxel tiene cero píxeles blancos después de morphological_open con kernel_size=3 |
| test_close_fills_small_hole | Una máscara con un agujero negro aislado de 1 píxel dentro de una región blanca tiene el agujero llenado después de morphological_close |
| test_connected_components_count | Una máscara con 3 manchas blancas visualmente separadas produce num_components == 3 |
| test_connected_components_background_is_zero | Los píxeles de fondo de label_array son siempre 0 |
| test_filter_components_by_area_excludes_outliers | Un componente más pequeño que min_area está ausente del resultado filtrado |
| test_analyze_regions_sorted_descending | La lista devuelta de RegionInfo tiene valores de .area no crecientes |
| test_largest_region_matches_first_of_analyze_regions | largest_region(mask) == analyze_regions(mask)[0] (o None para ambos en una máscara vacía) |
| test_watershed_returns_tuple | El valor de retorno se desempaqueta como (pygame.Surface, np.ndarray) |
| test_extract_hog_output_length | extract_hog(surface).shape == (512,) independientemente del tamaño de la superficie de entrada |
| test_extract_lbp_output_length | extract_lbp(surface).shape == (256,) |
| test_extract_color_histogram_output_length | extract_color_histogram(surface, bins=64).shape == (192,) (64x3) |
| test_extract_features_method_dispatch | extract_features(s, method='hog') produce una salida idéntica a llamar a extract_hog(s) directamente |
| test_bounding_boxes_count_matches_components | len(bounding_boxes_from_mask(mask)) == connected_components(mask).num_components |

---

## 14. Pruebas de la Fase 12 — PatternRecognitionTools

### 14.1 tests/test_pattern_recognition_tools.py

Usa tests/fixtures/sample_dataset_tiny.npz — un conjunto de datos sintético pequeño (ej. 30 muestras, 2 clases, características de 16 dimensiones) mantenido separado del sample_dataset.npz completo para que las pruebas se ejecuten rápido.

| Prueba | Afirmación (se ejecuta una vez por model_type en {knn, tree, forest, svm} via pytest.mark.parametrize) |
|---|---|
| test_train_returns_trained_model | train(X, y, model_type) devuelve un TrainedModel con .model_type coincidiendo con la entrada |
| test_train_feature_length_matches_input | .feature_length == X.shape[1] |
| test_train_classes_match_unique_labels | set(.classes) == set(y.tolist()) (como cadenas) |
| test_evaluate_returns_evaluation_result | .accuracy está en [0.0, 1.0] |
| test_evaluate_confusion_matrix_shape | confusion_matrix.shape == (n_classes, n_classes) |
| test_save_load_round_trip_identical_predictions | Un modelo guardado y luego cargado produce una salida classify() idéntica en el mismo vector de entrada que el modelo antes de guardar |
| test_classify_returns_known_class | classify(features, model) devuelve una cadena presente en model.classes |
| test_classify_wrong_feature_length_raises | Pasar un vector de características de longitud incorrecta lanza ValueError |
| test_classify_proba_sums_to_one | sum(classify_proba(features, model).values()) aproximadamente 1.0 |
| test_predict_matches_manual_extract_then_classify | predict(model, surface, method) es igual a classify(extract_features(surface, method), model) |

| Pruebas adicionales no parametrizadas | Afirmación |
|---|---|
| test_register_and_get_model | get_model(name) devuelve el objeto exacto pasado a register_model(name, ...) |
| test_get_unregistered_model_raises | get_model("nonexistent") lanza KeyError |
| test_list_models_reflects_registry | list_models() contiene cada nombre pasado a register_model() |
| test_train_minimum_samples_enforced | Entrenar con menos de 10 muestras totales lanza ValueError |
| test_train_minimum_classes_enforced | Entrenar con solo 1 clase distinta lanza ValueError |

---

## 15. Pruebas de la Fase 14 — BossBase

### 15.1 tests/test_boss_base.py

| Prueba | Afirmación |
|---|---|
| test_starts_at_phase_zero | Un jefe recién construido tiene current_phase == 0 |
| test_phase_transition_at_health_threshold | Reducir la salud por debajo de phases[0].health_threshold avanza current_phase a 1 |
| test_invincible_during_transition | Mientras is_transitioning == True, apply_hit() no reduce más la salud |
| test_boss_phase_changed_event_emitted | Una transición de fase pone en cola BOSS_PHASE_CHANGED con el nuevo valor de phase correcto |
| test_transition_timer_counts_down | transition_timer disminuye cada llamada a update(dt) durante una transición y is_transitioning se vuelve False una vez que llega a 0 |
| test_final_phase_has_no_further_transition | Reducir la salud a 0 en la última fase dispara el manejo de muerte, no otra transición de fase |

---

## 16. Tabla Resumen de Ejecución de Pruebas

Referencia cruzada a las puertas de fase de 25_IMPLEMENTATION_ROADMAP.md:

| Fase | Archivo(s) de Prueba | Debe Pasar Antes de |
|---|---|---|
| 1 | test_event_bus.py, test_clock.py | Que comience la Fase 2 |
| 2 | test_math_utils.py, test_asset_loader.py, test_input_manager.py | Que comience la Fase 3 |
| 3 | test_scene_manager.py | Que comience la Fase 4 |
| 4 | test_hud.py | Que comience la Fase 5 |
| 5 | test_player_physics.py, test_player_state_machine.py, test_player_damage.py | Que comience la Fase 6 |
| 6 | test_enemy_walker.py, test_enemy_flying.py, test_enemy_shooter.py | Que comience la Fase 7 |
| 7 | test_stage_loader.py, test_camera.py, test_checkpoint.py | Que comience la Fase 8 |
| 8 | test_color_tools.py, test_curve_tools.py | Que comience la Fase 9 |
| 9 | test_stage0_smoke.py + lista de verificación de juego manual | Que comiencen las Fases 10-14 |
| 10 | test_filter_tools.py | Que comience la Fase 13 |
| 11 | test_vision_tools.py | Que comience la Fase 13 |
| 12 | test_pattern_recognition_tools.py | Que comience la Fase 13 |
| 13 | Solo prueba de humo manual | Que comience la Fase 14 |
| 14 | test_boss_base.py | Que comience la Fase 15 |
| 15 | Prueba de incorporación manual de 15 minutos | Que comience la Fase 16 |
| 16 | Suite completa, cero fallos | Proyecto considerado implementación completa |

---

## 17. Ejecución de la Suite

`
# Suite completa
pytest tests/ -v

# Puerta de fase única, ej. antes de comenzar la Fase 6:
pytest tests/test_enemy_walker.py tests/test_enemy_flying.py tests/test_enemy_shooter.py -v

# Con cobertura (opcional, no una puerta estricta, pero útil para que el profesor verifique):
pytest tests/ --cov=src --cov-report=term-missing
`

Ninguna prueba en este plan requiere un sistema de visualización/ventanas — todas las pruebas deben ejecutarse sin cabeza (SDL_VIDEODRIVER=dummy si es necesario para cualquier llamada a pygame.display activada indirectamente por la construcción de App en pruebas de estilo integración).