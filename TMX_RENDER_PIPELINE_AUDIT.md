# TMX_RENDER_PIPELINE_AUDIT

## Defect

`AttributeError: 'TiledMapData' object has no attribute 'get_center_offset'`

## Actual Object Graph (current broken state)

```
StageLoader.load()
  ├── tmx: pytmx.TiledMap
  ├── map_data = data.TiledMapData(tmx)      # pyscroll.data.TiledMapData
  └── map_layer = PyscrollGroup(map_data, ...)
       └── self._map_layer = TiledMapData    # WRONG TYPE
```

When `StageScene.draw()` calls:
```python
self._data.map_layer.draw(surface)
```

`PyscrollGroup.draw()` internally calls:
```python
ox, oy = self._map_layer.get_center_offset()
```

But `TiledMapData` has no `get_center_offset()` method — it's defined on `BufferedRenderer`.

## Expected Object Graph (correct state)

```
StageLoader.load()
  ├── tmx: pytmx.TiledMap
  ├── map_data = data.TiledMapData(tmx)
  ├── renderer = BufferedRenderer(map_data, size)   # MISSING STEP
  └── map_layer = PyscrollGroup(renderer, ...)
       └── self._map_layer = BufferedRenderer       # CORRECT
```

## Root Cause

`src/framework/stage/stage_loader.py` line 155–156:

```python
map_data = data.TiledMapData(tmx)
map_layer = PyscrollGroup(map_data, default_layer=4)
```

`PyscrollGroup.__init__` expects `map_layer: BufferedRenderer`, but receives `TiledMapData`. No `BufferedRenderer` is ever constructed.

The `BufferedRenderer` wraps the `TiledMapData` and manages the camera view, scroll offset, and tile culling. `PyscrollGroup` delegates `center()` and `get_center_offset()` to the renderer.

## Required Fix

In `src/framework/stage/stage_loader.py`, replace:

```python
map_data = data.TiledMapData(tmx)
map_layer = PyscrollGroup(map_data, default_layer=4)
```

With:

```python
from pyscroll import BufferedRenderer

map_data = data.TiledMapData(tmx)
renderer = BufferedRenderer(
    map_data,
    size=(INTERNAL_WIDTH, INTERNAL_HEIGHT),
    clamp_camera=True,
)
map_layer = PyscrollGroup(renderer, default_layer=4)
```

Where `INTERNAL_WIDTH` and `INTERNAL_HEIGHT` are the engine's internal resolution (320×224). `clamp_camera=True` prevents the camera from scrolling past the map edges.

## Files That Must Change

| File | Change |
|------|--------|
| `src/framework/stage/stage_loader.py` | Construct `BufferedRenderer` from `TiledMapData`, pass to `PyscrollGroup` |
| `src/engine/scenes/stage_scene.py` | No change needed (draw call is already correct) |

## Impact on StageScene

`StageScene.draw()` currently does:
```python
if self._camera is not None:
    cx = offset.x + INTERNAL_WIDTH / 2
    cy = offset.y + INTERNAL_HEIGHT / 2
    self._data.map_layer.center = (cx, cy)
self._data.map_layer.draw(surface)
```

This is correct for a `PyscrollGroup` wrapping a `BufferedRenderer`. The `center` property on `PyscrollGroup` delegates to `self._map_layer.center(value)`, which is `BufferedRenderer.center()`. No changes needed in `stage_scene.py`.