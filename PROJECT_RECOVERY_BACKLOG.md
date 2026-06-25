# PROJECT_RECOVERY_BACKLOG.md

## LEGACY OF INFEST — Project Recovery Backlog

### R = Runtime blocker | I = Integration issue | C = Contract violation | A = Asset dependency | Q = Quality issue

---

### [R-001] Tile layer renders no visible output (black screen suspected)

| Field | Value |
|---|---|
| Severity | CRITICAL |
| Root cause | The `minimal_stage.tmx` Terrain layer uses tile IDs 0 and 1; `tileset_stage0.tsx` has been fixed to `tilecount=4, columns=2`. Need verification that pyscroll actually renders tiles. If still black, the draw call may not produce visible pixels. |
| File | `assets/tileset_stage0.tsx`, `src/framework/stage/stage_loader.py`, `src/engine/scenes/stage_scene.py` |
| Function | `StageLoader.load()`, `StageScene.draw()` |
| Runtime impact | All tiles invisible; player/enemies/HUD only visible on black background |
| Dependencies | None |
| Estimated fix complexity | S |
| Current status | Investigating |

---

### [R-002] NextTrigger does not emit STAGE_COMPLETE

| Field | Value |
|---|---|
| Severity | HIGH |
| Root cause | `StageScene.update()` executes `pass` when player overlaps `next_trigger` instead of emitting an event |
| File | `src/engine/scenes/stage_scene.py` |
| Function | `StageScene.update()` |
| Runtime impact | Stage transitions do not occur |
| Dependencies | None |
| Estimated fix complexity | XS |
| Current status | Pending |

---

### [I-001] Stage startup flow verification

| Field | Value |
|---|---|
| Severity | HIGH |
| Root cause | `App.__init__()` pushes `SplashScene()` per `03_ARCHITECTURE.md §5`, but need to verify SplashScene transitions to StageScene after timeout or key press |
| File | `src/engine/core/app.py`, `src/engine/scenes/splash_scene.py` |
| Function | `App.__init__()`, `SplashScene.update()` |
| Runtime impact | Developer shortcut may bypass splash scene; unclear transition path |
| Dependencies | None |
| Estimated fix complexity | S |
| Current status | Investigating |

---

### [C-001] EnemyShooter.update() overrides EnemyBase.update() — violates 05_ENEMY_SPEC.md §2.3

| Field | Value |
|---|---|
| Severity | MEDIUM |
| Root cause | `EnemyShooter.update()` overrides master update method |
| File | `src/framework/entities/enemy_shooter.py` |
| Function | `EnemyShooter.update()` |
| Runtime impact | Potential subtle enemy AI bugs; Phase 8 may propagate pattern |
| Dependencies | None |
| Estimated fix complexity | M |
| Current status | Pending (not a runtime blocker) |

---

### [C-002] ENEMY_DIED event payload uses `int` for `entity_id` instead of `str`

| Field | Value |
|---|---|
| Severity | LOW |
| Root cause | `entity_id=id(self)` uses Python memory address int |
| File | `src/framework/entities/enemy_base.py` |
| Function | `EnemyBase.apply_hit()` |
| Runtime impact | None currently; violates 23_DATA_SCHEMAS.md §2 |
| Dependencies | None |
| Estimated fix complexity | XS |
| Current status | Pending (not a runtime blocker) |

---

### [Q-001] flake8 style warnings (5)

| Field | Value |
|---|---|
| Severity | LOW |
| Root cause | W503 line-break-before-operator and E501 line-too-long |
| File | `src/framework/entities/enemy_base.py`, `src/framework/entities/player.py`, `src/framework/stage/stage_loader.py` |
| Function | N/A |
| Runtime impact | None |
| Dependencies | None |
| Estimated fix complexity | XS |
| Current status | Pending (not a runtime blocker) |

---

### Recovery Priority Order (UPDATED)

1. **I-001** — SplashScene transition path (BLOCKER: app starts in SplashScene and never transitions to StageScene; tile rendering cannot be validated until this is fixed)
2. **R-001** — tile rendering black screen (secondary; verify after stage is actually visible)
3. **R-002** — NextTrigger event
4. C/C/Q items after runtime is fully operational
