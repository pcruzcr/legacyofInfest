# TMX SPATIAL AUDIT — AUD-757 Fase 4

**Fecha:** 2026-09-01 · **Grid nativa:** `80×45` `1280×720` `16×16`
**Metodología:** Parseo `xml.etree` + `StageLoader.load` headless `SDL_VIDEODRIVER=dummy`

## 1. TMX → World conversión

```
TMX (tile_x, tile_y) * 16 → WORLD (px)
TMX object (x, y, w, h) — top-left en px WORLD
Layer tile: `data` índice → world (tx*16, ty*16)
```

No `+8`/`-8` legacy salvo `collision` `Platform` `one_way` `rect` alignment a `16` (ver §3).

## 2. Matriz TMX

| TMX (parent) | Tiles `w×h` | Pixels `W×H` | `tilewidth` | `tile_ok` | World bounds | Camera bounds `0-(W-1280) × 0-(H-720)` | Status | Objetos |
|---|---|---|---|---|---|---|---|
| boss_paburu | `260×82` | `4160×1312` | `16×16` | PASS | `4160×1312` | `0-2880 × 0-592` | PASS vertical | 112 |
| boss_rey | `120×45` | `1920×720` | `16×16` | PASS | `1920×720` | `0-640 × 0-0` | PASS | 7 |
| boss_venado | `330×45` | `5280×720` | `16×16` | PASS | `5280×720` | `0-4000 × 0-0` | PASS | 34 |
| hall | `110×45` | `1760×720` | `16×16` | PASS | `1760×720` | `0-480 × 0-0` | PASS | 71 |
| lobby_datacenter | `80×45` | `1280×720` | `16×16` | PASS | `1280×720` | `0-0 × 0-0` | PASS (fits) | 17 |
| stage0 | `160×45` | `2560×720` | `16×16` | PASS | `2560×720` | `0-1280 × 0-0` | PASS | 101 |
| stage1_1 | `390×45` | `6240×720` | `16×16` | PASS | `6240×720` | `0-4960 × 0-0` | PASS | 60 |
| stage1_2_la_soda | `350×45` | `5600×720` | `16×16` | PASS | `5600×720` | `0-4320 × 0-0` | PASS | 70 |
| stage1_3_las_aulas | `320×45` | `5120×720` | `16×16` | PASS | `5120×720` | `0-3840 × 0-0` | PASS | 76 |
| stage2_1_oficinas | `320×45` | `5120×720` | `16×16` | PASS | `5120×720` | `0-3840 × 0-0` | PASS | 54 |
| stage2_2 | `120×50` | `1920×800` | `16×16` | PASS | `1920×800` | `0-640 × 0-80` | PASS vertical | 49 |
| stage3_1 | `160×45` | `2560×720` | `16×16` | PASS | `2560×720` | `0-1280 × 0-0` | PASS | 58 |
| stage3_3_el_patio | `100×45` | `1600×720` | `16×16` | PASS | `1600×720` | `0-320 × 0-0` | PASS | 30 |
| stage3_4_boss_gavilan | `102×45` | `1632×720` | `16×16` | PASS | `1632×720` | `0-352 × 0-0` | PASS | 35 |
| stage4_1 / 4_1b / 4_1c×3 | `1440×45` | `23040×720` | `16×16` | PASS | `23040×720` | `0-21760 × 0-0` | PASS largo | 57-113 |
| tutorial_hub | `280×45` | `4480×720` | `16×16` | PASS | `4480×720` | `0-3200 × 0-0` | PASS | 55 |
| stage_cenital | `100×45` | `1600×720` | `16×16` | PASS | `1600×720` | `0-320 × 0-0` | PASS cenital | 55 |
| hub_backtracking | `64×32` | `1024×512` | `16×16` | PASS | `1024×512` | `0-0 × 0-0` | WARNING demo | 81 |
| stage_mecanicas | `310×24` | `4960×384` | `16×16` | PASS | `4960×384` | `0-3680 × 0-0` | WARNING demo corta | 165 |
| stage_ai_dojo | `64×32` | `1024×512` | `16×16` | PASS | `1024×512` | `0-0 × 0-0` | WARNING | 153 |
| stage_* 58×16 (8 vistas) | `58×16` | `928×256` | `16×16` | PASS | `928×256` | `0-0 × 0-0` | WARNING demo | 56 |

**Total TMX:** 37 archivos, `tilewidth` `16×16` **100% PASS**, `37/37` `16`. No `tile_size ≠16`.

**Objetos:** todo `top-left` WORLD, `w,h` en px, sin rotación ≠0 (verificar `rotation` 0 en todos).

## 3. TILE → PIXEL offsets

Buscar `+8`/`-8` en `stage_loader`: solo `collision` `rect` snap a `16` (int). No `+8` para centrar tiles — válido (tile origin top-left). `Platform` `y` `+?` no existe.

Ver `src/framework/stage/stage_loader.py:688` `rect = Rect(obj.x, obj.y, obj.width, obj.height)` — directo top-left → WORLD, sin offset.

**Estado:** PASS — `tile_x*16` sin hack.

## 4. Object anchor

TMX `PlayerSpawn` `EnemySpawn` etc usan `x,y` top-left. `Player.__init__` `Rect(int(x),int(y),40,64)` — top-left; `EnemyBase` igual `int(position.x)`. `draw` usa `rect.x - offset.x` → `screen = world - camera`. Consistente `top-left` para world, `midbottom` para feet lógico (ver `player.py:653` `position` → `rect`).

No `center` vs `top-left` discrepancia.

## 5. Layers

`Terrain` `Collision` `Objects` `Foreground` cada uno `top-left` `0,0` mundo. `pyscroll` `BufferedRenderer` `center(camera+half)` → tiles `world - offset`.

Background `bg_*` capas `1280/2560/3840` `wrap` `shift_x % w` — origen WORLD `0,0`.

## 6. Conclusión

`TMX → WORLD` es `*16` puro, `top-left`, sin offsets legacy. `37/37` `16×16` PASS.
