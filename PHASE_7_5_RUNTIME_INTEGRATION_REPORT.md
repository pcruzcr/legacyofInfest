# PHASE 7.5 RUNTIME INTEGRATION REPORT

## Status: COMPLETE

## Tickets delivered

- T7.5.1 `src/engine/scenes/stage_scene.py`
- T7.5.2 `src/engine/core/app.py` startup wired to StageScene
- T7.5.3 Update loop integration verified
- T7.5.4 Render integration verified
- T7.5.5 Runtime validation passed

## Runtime object graph (after integration)

```
App
 ├── internal_surface (320x224)
 ├── window_surface
 ├── DeltaClock
 ├── EventBus (static)
 ├── AssetLoader (stub)
 ├── InputManager (stub)
 ├── AudioManager (stub)
 └── SceneManager
      └── StageScene
           ├── StageData (from minimal_stage.tmx)
           ├── Player (at spawn_point)
           ├── Camera (following Player)
           ├── EnemyWalker x1
           └── Checkpoint x1
```

## Scene graph

```
SceneManager
 └── StageScene  (active)
```

## TMX integration status

- `StageLoader.load("tests/fixtures/minimal_stage.tmx")` called at startup
- `StageData` created and held by `StageScene`
- `pyscroll.PyscrollGroup` rendered via `StageScene.draw()`
- Required layers validated by `StageLoader`

## Camera integration status

- `Camera` instantiated in `StageScene.on_enter()`
- `camera.follow(player)` attached
- `camera.update(dt)` called every frame
- Parallax offset used in `StageScene.draw()`

## Player integration status

- `Player` spawned at `StageData.spawn_point`
- `Player.update(dt, collision_rects=...)` called every frame
- `Player.draw()` rendered with camera offset

## Enemy integration status

- `EnemyWalker` spawned from `StageData.entity_list`
- `Enemy.update(dt)` called every frame
- `enemy.set_collision_rects()` called with stage collision list

## Checkpoint integration status

- Checkpoints loaded from `StageData.checkpoints`
- `Checkpoint.try_activate(player.rect)` called every frame

## Screens visible after startup

- TMX tilemap rendered with camera parallax
- Player sprite rendered
- Enemy sprite rendered
- Checkpoint outline rendered

## Verification

- pytest: 104 passed
- flake8: clean
- Runtime smoke test: App constructs, StageScene loads, Player/Camera/Enemies present

## Next required work before Phase 8

- Replace `tests/fixtures/minimal_stage.tmx` with the full Stage0 map (`src/stages/stage0/stage0.tmx`)
- Register remaining entity types (Flying, Shooter) in `StageScene.on_enter()`
- Implement stage transition logic in `NextTrigger` handler
- Add HUD overlay (hearts, timer, messages)
- Add save/restore via checkpoint persistence