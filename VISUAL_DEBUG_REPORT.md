# VISUAL_DEBUG_REPORT

Generated: read-only runtime visual diagnostic

## 1. Exact Coordinates at Startup

| Object | World Position | Screen Position (camera offset=0,0) | Rect |
|--------|---------------|--------------------------------------|------|
| Player | (32, 184) | (32, 184) | (32, 160, 16, 24) |
| Enemy Walker | (126, 192) | (0, 0) ← **BUG** | (0, 0, 16, 16) ← **BUG** |
| Checkpoint | (200, 160) | (200, 160) | (200, 160, 24, 32) |
| Floor collision | varies | varies | (0, 208, 320, 16) |
| Platform collision | varies | varies | (100, 176, 64, 8) |

## 2. World Size

- Map tiles: 20 × 14 (16×16 px tiles)
- Pixel size: **320 × 224** (identical to viewport)
- No scrolling occurs with this fixture

## 3. Camera

| Property | Value |
|----------|-------|
| Initial offset | (0, 0) |
| Offset after 120 frames | (0, 78.88) |
| Target player position | (32, 184) |
| Viewport center (pyscroll) | (160, 112) |
| view_rect | (0, 0, 320, 224) |

## 4. Defects Found

### Defect A: `EnemyBase.rect` is never updated to world coordinates

`EnemyBase.__init__()` sets `self.rect = Rect(0, 0, 16, 16)` at line 69.

`EnemyBase.update()` calls `_update_rects()` which only sets `hitbox` and `hurtbox` — **not `rect`**.

`EnemyBase._draw_impl()` renders at `self.rect` — always (0, 0, 16, 16).

**Result**: The green rectangle always renders at screen origin (0, 0), not at the enemy's world position. After camera offset moves to (0, 78.88), the green rect is still at screen (0,0) because the offset is not applied.

### Defect B: No entity draw method applies camera offset to rect

Both `Player.draw()` and `EnemyBase._draw_impl()` render `self.rect` directly without subtracting `camera_offset`.

**Player.draw()** (line 280-290):
```python
pygame.draw.rect(surface, colour, self.rect)
```
`self.rect` returns world coordinates like `(32, 160, 16, 24)`. When camera offset is (0, 78.88), the player would draw at world Y=160 instead of screen Y=160-78.88.

**EnemyBase._draw_impl()** (line 214):
```python
pygame.draw.rect(surface, (120, 160, 120), self.rect)
```
`self.rect` is stuck at (0, 0, 16, 16) — always top-left of screen.

### Defect C: Checkpoint draw ignores camera offset

Checkpoint also likely draws without offset (needs verification).

## 5. What Is Visible on Screen

At startup (frame 0):
- **Enemy** (green rectangle): at screen (0,0) — top-left corner, size 16×16
- **Player** (red rectangle): at screen (32, 160) — visible on left side
- **Checkpoint**: at screen (200, 160) — visible right side
- **TMX tiles**: rendered via pyscroll at (0,0) — covers entire viewport
- **Floor collision**: at screen Y=208..224 — bottom of screen

After camera moves to (0, 78.88):
- **TMX tiles**: scrolled up 78.88 px via pyscroll BufferedRenderer
- **Player**: still drawn at world (32, 160) — would appear to shift relative to map
- **Enemy**: still at screen (0, 0) — misaligned from map

## 6. Root Cause Summary

| Bug | Symptom | File |
|-----|---------|------|
| Enemy rect not set to world pos | Green rect always at (0,0) | `enemy_base.py` line 69, 160-171 |
| Entity draw ignores camera offset | All entities rendered in world coords | `player.py` line 290, `enemy_base.py` line 214 |
| Checkpoint draw may also ignore offset | Checkpoint shifts relative to map | `checkpoint.py` draw method |

## 7. Recommended Fixes (no code changed yet)

1. **`EnemyBase._update_rects()`**: Add `self.rect.topleft = (self.position.x, self.position.y)` to move the base rect to world position.

2. **`Player.draw()`**: Subtract camera offset from the drawn rect position.

3. **`EnemyBase._draw_impl()`**: Subtract camera offset from the drawn rect position.

4. **`Checkpoint.draw()`**: Verify camera offset application.