# STAGE_RUNTIME_AUDIT

Generated: Stage runtime integration audit (read-only)

## 1. Startup Execution Flow

```
main.py: main()
  -> App()
       -> pygame.init()
       -> internal_surface = Surface((320, 224))
       -> window_surface = set_mode(320*DISPLAY_SCALE, 224*DISPLAY_SCALE)
       -> clock = DeltaClock()
       -> scene_manager = SceneManager()
       -> scene_manager.push(SplashScene())
            -> SplashScene.on_enter()
  -> App.run()
       -> loop:
            -> events = pygame.event.get()
            -> dt = clock.tick()
            -> EventBus.dispatch()
            -> input_manager.pump(events)
            -> current_scene = scene_manager.current
            -> current_scene.update(dt)       # SplashScene: no-op
            -> current_scene.draw(internal_surface)  # fill(32,32,64)
            -> scale + blit -> window
```

## 2. Scene Graph

```
SceneManager
 └── SplashScene  (top of stack)
```

No other scenes exist under `src/engine/scenes/`.

## 3. Runtime Object Graph

```
App
 ├── internal_surface: pygame.Surface  (320x224)
 ├── window_surface: pygame.Surface
 ├── clock: DeltaClock
 ├── event_bus: EventBus (static)
 ├── asset_loader: AssetLoader (placeholder stub)
 ├── input_manager: InputManager (placeholder stub)
 ├── audio_manager: AudioManager (placeholder stub)
 └── scene_manager: SceneManager
      └── SplashScene
```

**None of the following are present at runtime:**
- `StageLoader`
- `StageData`
- `Camera`
- `Player`
- `EnemyWalker` / `EnemyFlying` / `EnemyShooter`
- `Checkpoint`
- `pyscroll.PyscrollGroup`

## 4. Stage Integration Status

| Check | Result |
|-------|--------|
| Is `StageLoader` used by any runtime scene? | **No** |
| Is a `.tmx` file loaded during startup? | **No** |
| Is a `StageScene` implemented? | **No** (`src/engine/scenes/stage_scene.py` does not exist) |
| Is `StageLoader.load()` called in `App`? | **No** |
| Is any `StageData` created at runtime? | **No** |
| Is any `pyscroll` map layer rendered? | **No** |

## 5. Camera Integration Status

| Check | Result |
|-------|--------|
| Is `Camera` instantiated at runtime? | **No** |
| Is `camera.follow(player)` called? | **No** |
| Is parallax rendered? | **No** |

Camera exists only as a framework class (`src/framework/stage/camera.py`) with unit tests.

## 6. Enemy Integration Status

| Check | Result |
|-------|--------|
| Is any enemy spawned at runtime? | **No** |
| Is `StageData.entity_list` consumed? | **No** (no StageData exists) |
| Is `EnemyWalker.update()` called? | **No** |

Enemies are registered as entity-factory targets in `StageLoader` docstrings only.

## 7. Player Integration Status

| Check | Result |
|-------|--------|
| Is `Player` instantiated at runtime? | **No** |
| Is `Player.update(collision_rects=...)` called? | **No** |
| Is `Player.draw()` called? | **No** |

Player class is fully defined (`src/framework/entities/player.py`) but never constructed.

## 8. What Should Be Visible When Running `python main.py`

Currently visible:
- A 320x224 scaled window
- Solid fill colour `(32, 32, 64)` (dark blue-grey)
- Window title: `"Legacy of InFest"`
- No sprites, no tilemap, no HUD, no entities

## 9. Missing Connections

1. No `StageScene` (or equivalent) that consumes `StageData`
2. `App` never invokes `StageLoader.load()`
3. No scene creates a `Player` at `StageData.spawn_point`
4. No `Camera` created or attached to Player
5. `Player.update()` never receives `StageData.collision_rects`
6. No scene iterates `StageData.entity_list` to spawn enemies
7. No scene calls `Checkpoint.try_activate(player.rect)`
8. No scene checks `StageData.next_trigger` for stage transitions
9. `StageData.background_layers` (pyscroll) never drawn

## 10. Exact Next Implementation Required to Display Stage0

To show Stage0 on screen, the following must be implemented (in order):

1. **Create `src/engine/scenes/stage_scene.py`**
   - Subclass `BaseScene`
   - On enter: call `StageLoader.load(Path("src/stages/stage0/stage0.tmx"))`
   - Spawn `Player` at `stage_data.spawn_point`
   - Create `Camera` and call `camera.follow(player)`
   - Iterate `stage_data.entity_list` and call `entity.on_enter()` / store in scene entity list
   - Store `stage_data.collision_rects`

2. **Wire stage_scene into App startup**
   - Replace `SplashScene` push with `StageScene` (or add a transition)

3. **Update stage_scene.update(dt)**
   - Call `player.update(dt, collision_rects=stage_data.collision_rects)`
   - Update `camera.update(dt)`
   - Update all enemies
   - Call `checkpoint.try_activate(player.rect)` for each checkpoint
   - Check `next_trigger` overlap for stage transition

4. **Update stage_scene.draw(surface)**
   - Draw `stage_data.background_layers` with parallax offsets from camera
   - Draw terrain / entities / player / HUD

No code has been modified. This audit is read-only.