# RUNTIME_DEFECT_REPORT

## Defect

`TypeError: PyscrollGroup.draw() takes 2 positional arguments but 3 were given`

## Root Cause

`src/engine/scenes/stage_scene.py` called:
```python
self._data.map_layer.draw(surface, offset)
```

`pyscroll.PyscrollGroup.draw()` signature is `draw(surface)`, taking only the target surface. The camera position is controlled via the `center` attribute, not via a draw argument.

## Fix Applied

Modified `src/engine/scenes/stage_scene.py`:

```python
offset = self._camera.offset if self._camera else pygame.Vector2(0, 0)
if self._camera is not None:
    cx = offset.x + INTERNAL_WIDTH / 2
    cy = offset.y + INTERNAL_HEIGHT / 2
    self._data.map_layer.center = (cx, cy)
self._data.map_layer.draw(surface)
```

The camera offset is now applied to `map_layer.center` (which pyscroll uses internally), and `draw()` is called with only the surface argument. Entity draw calls continue to receive the offset vector for manual world-to-screen translation.

## Runtime Validation

- `python main.py`: window opens without exceptions
- TMX tilemap renders via pyscroll
- Player visible (rectangle placeholder)
- Enemy visible (walker rectangle)
- Camera follows player (lerp applied to `map_layer.center`)
- Checkpoint draws without error
- Clean shutdown

## Screens Now Visible

- 320×224 scaled window
- Black background cleared each frame
- Tile layer rendered through pyscroll with camera tracking
- Player entity rendered at world position offset by camera
- Enemy walker rendered and updating (patrol state)
- Checkpoint rendered as rectangle marker

## Remaining Runtime Risks

- No player sprite (AssetLoader stub returns 16×16 surface)
- No enemy sprite (same stub limitation)
- No background parallax images (BG layers empty in fixture)
- No HUD overlay
- No input processing (InputManager stub)
- Collision rects limited to floor only in current fixture

## Verification Commands

```
python -m pytest tests/ -q   # 104 passed
python -m flake8 src/engine/scenes/stage_scene.py --max-line-length=79   # clean
python main.py              # opens window, no exceptions
```

## Commit

Pending: `[RUNTIME] fix: correct pyscroll draw integration`