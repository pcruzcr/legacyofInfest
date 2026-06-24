# ASSET_AUDIT_REPORT

Generated: Runtime asset audit (read-only)

## 1. Existing Asset Inventory

### 1.1 Root-level assets

| File | Status |
|------|--------|
| `assets/tileset_stage0.tsx` | Present |
| `assets/tileset_stage0.png` | Present |

### 1.2 Subdirectory assets

| Directory | Present files | Status |
|-----------|---------------|--------|
| `assets/audio/` | (empty — only `.gitkeep`) | **Missing** |
| `assets/backgrounds/` | (empty — only `.gitkeep`) | **Missing** |
| `assets/bosses/` | (empty — only `.gitkeep`) | **Missing** |
| `assets/enemies/` | (empty — only `.gitkeep`) | **Missing** |
| `assets/player/` | (empty — only `.gitkeep`) | **Missing** |
| `assets/stages/` | **Directory does not exist** | **Missing** |
| `assets/maps/` | **Directory does not exist** | **Missing** |
| `assets/tilesets/` | (empty — only `.gitkeep`) | **Missing** (root copy used instead) |
| `assets/ui/` | (empty — only `.gitkeep`) | **Missing** |

## 2. Missing Files Required by Stage 0

### 2.1 Tilesets (per docs/20_ASSET_BIBLE.md §7)

Required:
- `assets/tilesets/tileset_stage0.png` — **MISSING** (stub exists at `assets/tileset_stage0.png`, not in `tilesets/`)
- `assets/tilesets/tileset_stage0.tsx` — **MISSING** (stub exists at `assets/tileset_stage0.tsx`, not in `tilesets/`)

### 2.2 Background Layers (per docs/20_ASSET_BIBLE.md §8.1)

Required:
- `assets/backgrounds/stage0/bg_stage0_far.png` — **MISSING**
- `assets/backgrounds/stage0/bg_stage0_mid.png` — **MISSING**
- `assets/backgrounds/stage0/bg_stage0_near.png` — **MISSING**

### 2.3 Player Sprites (per docs/20_ASSET_BIBLE.md §4)

Required in `assets/player/`:
- `player_idle.png` — **MISSING**
- `player_walk.png` — **MISSING**
- `player_jump.png` — **MISSING**
- `player_fall.png` — **MISSING**
- `player_crouch.png` — **MISSING**
- `player_short_attack.png` — **MISSING**
- `player_long_attack.png` — **MISSING**
- `player_hurt.png` — **MISSING**
- `player_die.png` — **MISSING**

### 2.4 Enemy Sprites (per docs/20_ASSET_BIBLE.md §5.1)

Required in `assets/enemies/` (or `assets/sprites/enemies/`):
- `enemy_insecto_walk.png` — **MISSING**
- `enemy_insecto_hurt.png` — **MISSING**
- `enemy_insecto_die.png` — **MISSING**

### 2.5 Shared Sprites (per docs/20_ASSET_BIBLE.md §13)

Required in `assets/sprites/shared/`:
- `checkpoint.png` — **MISSING**
- `torch_anim.png` — **MISSING**

## 3. Files Referenced by TMX but Not Present

### 3.1 Current test fixture (`tests/fixtures/minimal_stage.tmx`)

References:
- `../assets/tileset_stage0.tsx` → resolves to `tests/assets/tileset_stage0.tsx` — **PRESENT** (copied from root)
- `../assets/tileset_stage0.png` → resolves to `tests/assets/tileset_stage0.png` — **PRESENT** (copied from root)

Result: **Fixture loads successfully.**

### 3.2 Expected full Stage0 TMX (`src/stages/stage0/stage0.tmx`)

Would reference:
- `../assets/tilesets/tileset_stage0.tsx` — **MISSING**
- Background layer images — **MISSING**

Result: **Cannot load full Stage0 map yet.**

## 4. Runtime Impact Assessment

### 4.1 What currently works

- `python main.py` opens a window
- `StageScene` loads `tests/fixtures/minimal_stage.tmx`
- Tile layers render (flat colour tiles from tileset image)
- Player, Camera, Enemy, Checkpoint objects exist and update
- No exceptions raised

### 4.2 What is broken or degraded

- No player sprite visible (AssetLoader stub returns 16×16 surface)
- No enemy sprite visible (AssetLoader stub returns 16×16 surface)
- No checkpoint sprite visible (AssetLoader stub returns 16×16 surface)
- No background parallax (background layer images absent)
- No HUD hearts/timer (font sprites absent)
- No audio (music/sfx files absent)

### 4.3 Visual state of current runtime

The running application displays:
- A 320×224 scaled window
- TMX tilemap rendered as flat colour blocks (from stub tileset)
- Player rendered as 16×16 coloured rectangle
- Enemy rendered as 16×16 coloured rectangle
- Checkpoint rendered as 16×16 coloured rectangle
- No sprites, no backgrounds, no HUD

## 5. Asset Gap Summary

| Category | Required | Present | Gap |
|----------|----------|---------|-----|
| Tileset images | 2 (tsx + png) | 2 (stubs) | Functional but no tile graphics |
| Background layers | 3 | 0 | **Complete gap** |
| Player sprites | 9 sheets | 0 | **Complete gap** |
| Enemy sprites | 3 sheets | 0 | **Complete gap** |
| Shared sprites | 2+ | 0 | **Complete gap** |
| Fonts | 6 | 0 | **Complete gap** |
| Music | 11 | 0 | **Complete gap** |
| SFX | 20+ | 0 | **Complete gap** |
| Boss sprites | 30+ | 0 | **Complete gap** |

## 6. Conclusion

The runtime is functional at the **system primitives level** but produces a **minimal placeholder visual**. All sprite, background, font, and audio assets are absent. The current stub tileset is sufficient for TMX parsing and flat-colour tile rendering, but no meaningful visual feedback exists.

To achieve the Stage 0 demonstration described in `docs/07_STAGE0_DESIGN.md`, the following asset sets must be created:

1. **tileset_stage0** (128×128 PNG + matching TSX)
2. **Stage0 backgrounds** (far/mid/near, 320×224 / 640×224 / 960×224)
3. **Player sprite sheets** (9 animations, 32×32 frames)
4. **Enemy sprite sheets** (Walker, Flying, Shooter — walk/hurt/die + projectile)
5. **Shared sprites** (checkpoint, torch)
6. **HUD assets** (hearts, portraits, banners)
7. **Fonts** (digits, message, banner, game over, menu)
8. **Audio** (BGM + SFX per Asset Bible)

None of these assets block the runtime from running; they only affect visual and audio fidelity.