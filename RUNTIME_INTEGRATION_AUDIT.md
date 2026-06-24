# RUNTIME_INTEGRATION_AUDIT

Generated: Phase 7 runtime audit (read-only, no code modified)

## 1. Startup Execution Path

```
main.py
  -> App()
       -> pygame.init()
       -> DeltaClock()
       -> SceneManager()
       -> scene_manager.push(SplashScene())
            -> SplashScene.on_enter()
  -> App.run()
       -> while running:
            -> pygame.event.get()
            -> dt = clock.tick()
            -> EventBus.dispatch()
            -> input_manager.pump(events)
            -> current_scene = scene_manager.current     # SplashScene
            -> current_scene.update(dt)                  # no-op
            -> current_scene.draw(internal_surface)      # fill(32,32,64)
            -> scale + blit to window
```

## 2. Active Startup Scene

**SplashScene** (`src/engine/scenes/splash_scene.py`)
- Pushed onto the SceneManager stack during `App.__init__()`
- Renders a solid `(32, 32, 64)` fill — no assets, no TMX, no entities

## 3. Runtime Object Graph

```
App
 ├── pygame.display (window)
 ├── internal_surface (320x224)
 ├── DeltaClock
 ├── EventBus (static)
 ├── AssetLoader (placeholder stub)
 ├── InputManager (placeholder stub)
 ├── AudioManager (placeholder stub)
 └── SceneManager
      └── SplashScene
```

**No Player, Camera, StageLoader, or Enemy instances exist at runtime.**

## 4. TMX Integration Status

| Question | Finding |
|----------|---------|
| Is a `.tmx` file loaded at startup? | **No** |
| Is `StageLoader` referenced outside tests/stage_loader.py? | **No** |
| Is any `StageData` created? | **No** |
| Is any `pyscroll` map layer rendered? | **No** |

`StageLoader` exists as a framework utility but is never called from `App`, `SceneManager`, `SplashScene`, or any runtime scene. The startup is entirely TMX-free.

## 5. Player Integration Status

| Question | Finding |
|----------|---------|
| Is a `Player` instantiated at runtime? | **No** |
| Is `Player.update()` called? | **No** |
| Is `Player.draw()` called? | **No** |

`Player` class is fully defined (`src/framework/entities/player.py`) but is never constructed in the application lifecycle. It is not referenced in `main.py`, `app.py`, `scene_manager.py`, `splash_scene.py`, or any runtime scene.

## 6. Enemy Integration Status

| Question | Finding |
|----------|---------|
| Is any Enemy spawned at runtime? | **No** |
| Is `entity_list` from `StageData` consumed? | **Would be yes if a stage scene existed** |

`EnemyWalker`, `EnemyFlying`, `EnemyShooter` are registered as entity factory targets in `StageLoader` docstrings but are never instantiated outside tests. The runtime scene graph contains zero enemies.

## 7. Camera Integration Status

| Question | Finding |
|----------|---------|
| Is `Camera` created at runtime? | **No** |
| Is `camera.follow(player)` called? | **No** |

`Camera` (`src/framework/stage/camera.py`) only appears in docstring examples and tests. No scene holds or updates a Camera instance.

## 8. What Should Currently Be Visible On Screen

- A 320x224 internal surface, scaled up by `DISPLAY_SCALE`
- Filled with solid RGB `(32, 32, 64)` (dark blue-grey)
- Window caption: `"Legacy of InFest"`
- Nothing else — no sprites, no tilemap, no HUD, no entities

## 9. Missing Integration Points (Blocking Runtime Use of Phase 7)

1. **No stage scene** — there is no `src/engine/scenes/stage_scene.py` (or equivalent) that consumes `StageData`
2. **StageLoader not invoked** — `App` and `SceneManager` never call `StageLoader.load()`
3. **Player not spawned** — no scene creates a `Player` at the `StageData.spawn_point`
4. **Camera not attached** — no scene creates a `Camera` and calls `follow(player)`
5. **Collision rects not provided** — `Player.update(collision_rects=...)` is never called with the `StageData.collision_rects` list
6. **Enemies not spawned** — no scene iterates `StageData.entity_list` to instantiate registered entities
7. **Checkpoints not activated** — no scene calls `Checkpoint.try_activate(player.rect)` each frame
8. **NextTrigger not monitored** — no scene checks `StageData.next_trigger` for player overlap to transition stages
9. **Parallax layers not rendered** — `StageData.background_layers` is populated by `pyscroll` but never drawn

## 10. Conclusion

Phase 7 delivered the **framework primitives** (Camera, Checkpoint, StageLoader, StageData) and their **unit tests**, but the **runtime integration** into the actual game loop is absent. The current application is a minimal splash-screen stub that exercises none of the Phase 7 systems. All Stage 7 functionality is verified in isolation via tests; wiring it into a live scene is deferred to a future phase.