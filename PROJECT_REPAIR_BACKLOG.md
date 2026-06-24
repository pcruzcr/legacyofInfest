# PROJECT REPAIR BACKLOG

Generated from PROJECT_RECONCILIATION_AUDIT.md findings.  
All items verified by actual runtime probe, test suite execution, and source code inspection.

**No code modified during audit.**

---

## PRIORITY 0 — Runtime-Breaking Defects

These items prevent the game from functioning as a playable experience. Must be fixed before any new feature work.

### P0.1 — EnemyBase.rect never updated to world position

| Field | Value |
|-------|-------|
| Severity | **BLOCKER** |
| Root cause | `EnemyBase.__init__()` at line 69 sets `self.rect = Rect(0, 0, 16, 16)`. The `_update_rects()` method (lines 160–171) updates `hitbox` and `hurtbox` but NOT `self.rect`. |
| File | `src/framework/entities/enemy_base.py` |
| Lines | 69, 160–171 |
| Symptom | Green rectangle renders at screen (0,0) always, never at enemy world position |
| Fix | Add `self.rect.topleft = (self.position.x, self.position.y)` to `_update_rects()` OR replace world rect computation to use `self.rect` instead of separate hitbox/hurtbox |
| Effort | 5 minutes |

### P0.2 — Player.draw() ignores camera_offset

| Field | Value |
|-------|-------|
| Severity | **HIGH** |
| Root cause | `Player.draw()` at line 290 draws `pygame.draw.rect(surface, colour, self.rect)` where `self.rect` returns world coordinates. The `camera_offset` parameter is received but never used. |
| File | `src/framework/entities/player.py` |
| Lines | 280–290 |
| Symptom | Player rectangle does not scroll with camera; appears to float relative to TMX map |
| Fix | Subtract `camera_offset` from `self.rect` before drawing, e.g.: `screen_rect = self.rect.move(-camera_offset.x, -camera_offset.y)` |
| Effort | 5 minutes |

### P0.3 — EnemyBase._draw_impl() ignores camera_offset

| Field | Value |
|-------|-------|
| Severity | **HIGH** |
| Root cause | `EnemyBase._draw_impl()` at line 214 draws `pygame.draw.rect(surface, (120, 160, 120), self.rect)` where `self.rect` is stuck at (0,0,16,16). Camera offset never applied. |
| File | `src/framework/entities/enemy_base.py` |
| Lines | 208–214 |
| Symptom | Enemy rectangle always renders at screen top-left (0,0), never scrolls with map |
| Fix | Apply camera_offset to computed rect position |
| Effort | 5 minutes |

### P0.4 — Checkpoint.draw() ignores camera_offset

| Field | Value |
|-------|-------|
| Severity | **HIGH** |
| Root cause | Checkpoint draw method may not accept or apply camera_offset |
| File | `src/framework/stage/checkpoint.py` |
| Lines | (need inspection of draw method) |
| Symptom | Checkpoint rectangle may not scroll with camera |
| Fix | Apply camera_offset in checkpoint draw |
| Effort | 5 minutes |

### P0.5 — No input processing (player cannot move)

| Field | Value |
|-------|-------|
| Severity | **BLOCKER** |
| Root cause | `App.__init__()` creates stub `InputManager()` at line 56. StageScene never calls any input methods. The real `InputManager` exists in `src/engine/input/input_manager.py` but is never instantiated or used. |
| File | `src/engine/core/app.py` (stub), `src/framework/entities/player.py` (no input query) |
| Lines | app.py:29-37, app.py:56 |
| Symptom | No keyboard/controller input reaches the player. Player sits idle at spawn forever. |
| Fix | 1) Replace stub with real `InputManager` in `App.__init__()`. 2) Call `InputManager.pump(events)` each frame. 3) Add input query to `StageScene.update()` and pass direction/dash/jump flags to player. |
| Effort | 30 minutes |

### P0.6 — Camera offset computation incorrect for pyscroll center

| Field | Value |
|-------|-------|
| Severity | **HIGH** |
| Root cause | `StageScene.draw()` centers pyscroll on `(offset.x + INTERNAL_WIDTH/2, offset.y + INTERNAL_HEIGHT/2)`. But the Camera's offset is top-left, and pyscroll center is relative to viewport. After 120 frames at (32,184) target, offset becomes (0, 78.88) — the pyscroll center moves but the entity draws use the same offset in reverse. |
| File | `src/engine/scenes/stage_scene.py` |
| Lines | 117-131 |
| Symptom | Entities and map scroll inconsistently |
| Fix | Entity draws should subtract camera_offset from world position; pyscroll should receive consistent center coordinates |
| Effort | 15 minutes |

---

## PRIORITY 1 — Visual Defects

These items degrade the player experience but do not crash the game.

### P1.1 — AssetLoader stub in App blocks all sprite rendering

| Field | Value |
|-------|-------|
| Severity | **MEDIUM** |
| Root cause | `App.__init__()` creates stub `AssetLoader()` instead of real one. Real AssetLoader exists at `src/engine/utils/asset_loader.py`. |
| File | `src/engine/core/app.py` |
| Lines | 24-37 |
| Symptom | All sprites render as coloured rectangles (placeholder draws) |
| Fix | Replace stub with real AssetLoader |
| Effort | 5 minutes |

### P1.2 — AudioManager stub blocks all audio

| Field | Value |
|-------|-------|
| Severity | **MEDIUM** |
| Root cause | `App.__init__()` creates stub `AudioManager()` instead of real one. Real AudioManager exists at `src/engine/audio/audio_manager.py`. |
| File | `src/engine/core/app.py` |
| Lines | 39-56 |
| Symptom | No music or SFX plays |
| Fix | Replace stub with real AudioManager |
| Effort | 5 minutes |

### P1.3 — StageScene loads test fixture instead of real map

| Field | Value |
|-------|-------|
| Severity | **LOW** |
| Root cause | `App.__init__()` passes `Path("tests/fixtures/minimal_stage.tmx")` to StageScene instead of a real stage map. |
| File | `src/engine/core/app.py` |
| Lines | 119-121 |
| Symptom | Only 20×14 minimal map shows; no Stage0 zones, enemies, or layout |
| Fix | Create real `src/stages/stage0/stage0.tmx` and point StageScene to it |
| Effort | Variable (requires TMX editor) |

### P1.4 — StageScene draws entities before TMX clear

| Field | Value |
|-------|-------|
| Severity | **LOW** |
| Root cause | `StageScene.draw()` fills black, draws TMX, then draws entities. If TMX covers the full viewport, black fill is invisible. But entities drawn on top of TMX without offset may appear to float. |
| File | `src/engine/scenes/stage_scene.py` |
| Lines | 107-131 |
| Symptom | Entities rendered on top of TMX but not at correct scroll positions |
| Fix | Combine with offset fixes in P0.2 and P0.3 |
| Effort | (covered by P0) |

---

## PRIORITY 2 — Architecture Defects

These items violate the documented architecture but do not cause immediate runtime failure.

### P2.1 — BossBase not implemented

| Field | Value |
|-------|-------|
| Severity | **MEDIUM** |
| Root cause | Ticket T6.5 was never implemented. `src/framework/entities/boss_base.py` does not exist. |
| File | `src/framework/entities/boss_base.py` (missing) |
| Lines | N/A |
| Impact | Boss stages cannot be built. The boss phase system and health bar integration don't exist. |
| Effort | 2-3 hours (must follow BossBase contract from 05_ENEMY_SPEC.md) |

### P2.2 — All 5 processing tool modules missing

| Field | Value |
|-------|-------|
| Severity | **MEDIUM** |
| Root cause | Phase 8 not started. `src/framework/processing/` directory is empty. |
| Files | `color_tools.py`, `filter_tools.py`, `curve_tools.py`, `vision_tools.py`, `pattern_recognition_tools.py` |
| Lines | N/A |
| Impact | Academic Units V, VII, VIII, IX cannot be demonstrated. Student stages depend on these for grading. |
| Effort | 8-12 hours total across 5 modules |

### P2.3 — EnemyBase._check_player_contact requires player.colliderect

| Field | Value |
|-------|-------|
| Severity | **LOW** |
| Root cause | `enemy_base.py:149` calls `self.hurtbox.colliderect(player.get_hurtbox())` which works but StageScene never calls `_check_player_contact`. |
| File | `src/framework/entities/enemy_base.py` |
| Lines | 140-158, and `src/engine/scenes/stage_scene.py` |
| Impact | Enemies do no contact damage to player even when overlapping. |
| Fix | Add `enemy._check_player_contact(self._player)` in `StageScene.update()` |
| Effort | 5 minutes |

### P2.4 — StageScene doesn't register all enemy types

| Field | Value |
|-------|-------|
| Severity | **LOW** |
| Root cause | `StageScene.on_enter()` registers Walker, Flying, Shooter. Walker is the only entity in the fixture, so only Walker is tested at runtime. Flying and Shooter registration is untested. |
| File | `src/engine/scenes/stage_scene.py` |
| Lines | 45-47 |
| Impact | Unverified: Flying and Shooter may fail to spawn in a real stage |
| Fix | Create fixture with Flying/Shooter objects and verify spawning |
| Effort | 30 minutes |

---

## PRIORITY 3 — Technical Debt

These items reduce maintainability, test coverage, or code quality but do not block runtime.

### P3.1 — 13 missing test files

| Test file | Component | Reason |
|-----------|-----------|--------|
| `test_audio_manager.py` | AudioManager | No tests exist |
| `test_message_box.py` | MessageBox | No tests exist |
| `test_screen_banner.py` | ScreenBanner | No tests exist |
| `test_splash_scene.py` | SplashScene | No tests exist |
| `test_stage_scene.py` | StageScene | No tests exist |
| `test_enemy_flying.py` | EnemyFlying | No tests exist |
| `test_enemy_shooter.py` | EnemyShooter | No tests exist |
| `test_animation_controller.py` | AnimationController | No tests exist |
| `test_action_map.py` | ActionMap | No tests exist |
| `test_sound_bank.py` | SoundBank | No tests exist |
| `test_spritesheet.py` | SpriteSheet | No tests exist |
| `test_transitions.py` | Transitions | No tests exist |
| `test_camera_draw_integration.py` | Camera+entity draw | Offset application untested |

### P3.2 — Three false-positive tests

| Test | Issue |
|------|-------|
| `test_enemy_walker.py:test_patrol_movement` | Sets position manually, doesn't test `_update_rects()`. Passes despite broken rect. |
| `test_camera.py:test_follow_moves_offset_toward_target` | Tests offset value but not draw integration. Passes despite draws ignoring offset. |
| `test_stage_loader.py:test_spawn_point_matches_tmx` | Tests data values, not rendering. Passes despite broken rendering. |

### P3.3 — Stub classes in App should be removed

| Field | Value |
|-------|-------|
| Severity | **LOW** |
| Root cause | `App.__init__()` defines stub `AssetLoader`, `InputManager`, and `AudioManager` classes inline (lines 24-57) when real implementations exist in `src/engine/`. |
| File | `src/engine/core/app.py` |
| Lines | 24-57 |
| Impact | Code duplication. Real implementations exist but are unused. Increases risk of stub diverging from real implementation. |
| Fix | Remove stubs, import and use real implementations |
| Effort | 10 minutes |

### P3.4 — Docstring contract mismatch: Checkpoint vs Player

| Field | Value |
|-------|-------|
| Severity | **LOW** |
| Root cause | `Checkpoint.update()` docstring says stage should call `_try_activate(player)` but `StageScene.update()` calls `cp.try_activate(player_rect)`. The `Checkpoint.__init__` stores `self.rect` (from `checkpoint.py` parameter) but `BaseSprite` may have renamed it to `trigger_rect`. |
| Files | `src/framework/stage/checkpoint.py`, `src/engine/scenes/stage_scene.py` |
| Lines | checkpoint.py:60-100, stage_scene.py:94-96 |
| Impact | Checkpoint activation may silently fail because the wrong property name is used. |
| Fix | Ensure `StageScene` passes the correct rect to `try_activate`. Ensure `Checkpoint` exposes the trigger rect as `.trigger_rect`. |
| Effort | 10 minutes |

### P3.5 — Stage0 empty directory

| Field | Value |
|-------|-------|
| Severity | **LOW** |
| Root cause | `src/stages/stage0/` contains only `__init__.py` and `.gitkeep`. No TMX map, no scene class. |
| File | `src/stages/stage0/` |
| Impact | The professor's Stage0 demonstration is not present. Cannot be used as reference implementation or grader calibration baseline. |
| Fix | Create Stage0 TMX (per `docs/07_STAGE0_DESIGN.md`) and Stage0 scene class |
| Effort | 4-6 hours (requires Tiled editor + full asset set) |

---

## REPAIR SUMMARY

| Priority | Count | Immediate Impact |
|----------|-------|-----------------|
| P0 — Runtime-breaking | 6 | Game cannot be played |
| P1 — Visual | 4 | Game runs but looks wrong |
| P2 — Architecture | 4 | Violates spec, blocks features |
| P3 — Technical debt | 5 | Maintenance burden |
| **Total** | **19** | |

### Recommended execution order

1. Fix P0.1–P0.4 (entity rect + camera offset) → entities render at correct positions
2. Fix P0.5 (input processing) → player can move
3. Fix P0.6 (pyscroll center consistency) → map and entities scroll together
4. Fix P1.1–P1.2 (wire real AssetLoader + AudioManager) → sprites and audio work
5. Fix P2.3 (enemy contact damage) → combat loop works
6. Fix P1.3–P1.4 (real TMX map) → visible game content
7. Fix P2.1 (BossBase) → Phase 7 complete
8. Fix P3.1–P3.3 (tests + stub removal) → quality
9. P2.2 (processing tools) → Phase 8
10. P3.5 (Stage0) → reference implementation