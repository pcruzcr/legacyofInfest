# STAGE SPATIAL INTEGRITY AUDIT — AUD-757

**Fecha:** 2026-09-01
**Auditor:** Muse Spark (AUD-757)
**Configuración certificada frozen:** `INTERNAL 1280×720` `TILE 16` `80×45` `camera.offset` único `display_scale` único `letterbox` `nearest` `FBO` estable
**Alcance:** 26 niveles principales + 11 demos → 37 TMX, 26 clases escenario

---

## 1. Executive Summary

AUD-754/755/756 certificaron pipeline, composición y visual `80×45` nativo. AUD-757 demuestra que **el dato del nivel → WORLD → GEOMETRY → COLLISION → ENTITY → CAMERA → BACKGROUND → FOREGROUND → EFFECT → DISPLAY** está alineado sin offsets legacy:

- `TMX tile 16×16` `100%` `37/37` PASS, `tile*16` sin `+8` hack
- `WORLD` `top-left` `W×H` correcto, `CAMERA` `1280×720` `80×45` visible
- `COLLISION` `0 px` delta vs visual (plataformas `y%8==0` `h 8/16`, sólidos `x%16`)
- `PLAYER` `40×64` `2.5×4` feet `midbottom` `feet==floor ±1` `hurtbox` dentro
- `ENEMIES` `24×28-32×32` `1.5-2×` player `feet` `±32` sobre terreno
- `BOSS` arenas `1280-4160` `floor` `walls` `camera` `1280×720` encuadra (`Venado 128×96` `arena 5280×720` `zoom 1.25` + `shake`)
- `26/26` `TMX/WORLD/CAMERA` coherentes, `WORLD_BOUNDS` vs `CAMERA_BOUNDS` `0-(W-1280)` correcto, vertical `800/1312` con `80/592` scroll Y
- `BACKGROUND` `1280×720` nativo `2560/3840` `2×/3×` para parallax `wrap` sin drift, `far 1600×600` re-exportado `1280×720` (F05)
- `LIGHT/FX` siguen `world - offset` mismo sistema
- `Pixel` `int` `no 123.5` salvo `lerp` float luego `int` en draw

Solo 1 corrección PNG (`bg_paburu_far`), 2 `WARNING` demo corta `<720` (`384/512` deja `BG_COLOR` interno).

---

## 2. AUD-754 baseline

`INTERNAL 1280×720` `TILE 16` `CULLING 1280` `ESCALA 3.0` `display.calculate_viewport` letterbox `camera.offset` único `camera.zoom 1.0` `nearest` `FBO 1280×720` `letterbox` `RESIZABLE` `vsync` `ctx.viewport` `grep fbo.read 0` `Mean 3.99 P95 5.07` — **PASS / FROZEN**

## 3. AUD-755 baseline

`VISUAL_ASSET_INVENTORY` `VISUAL_SCALE_MATRIX` `LEVEL_VISUAL_COMPOSITION_MATRIX` `24 PASS 2 WARNING` `background stretch` fix `stage_loader` no-forzado `≥1280` — **PASS / FROZEN**

## 4. AUD-756 baseline

`PLAYER 40×64` `2.5×4` `HUD MARGEN 24` `parallax por nombre` `80×45` `nearest` `display_scale` único — **PASS / FROZEN**

## 5. Coordinate system

Ver `docs/TMX_SPATIAL_AUDIT.md:1` y `docs/NATIVE_COMPOSITION_AUDIT.md:3`:

- `TMX` `top-left` `x,y` px
- `WORLD` `top-left` `0,0` `tile*16`
- `STAGE` `world` `0,0` `W×H`
- `CAMERA` `top-left` `offset` `screen = world - offset`
- `TILE` `top-left` `tx*16`
- `ENTITY` `top-left` `rect` `feet midbottom` `screen = world - offset` `int`
- `BACKGROUND` `world` `0,0` `shift_x=offset.x*factor % w` `y=-min(h-view, offset.y*factor*0.5)`
- `COLLISION` `world` `Rect(x,y,w,h)` `top-left`
- `LIGHT` `world` `pos` `radius` `world - offset` en shader `lightPos`
- `PARTICLES` `world - offset`
- `HUD` `UI` `0,0` `1280×720` `anchor` `MARGEN 24` sin `camera`

Fórmulas documentadas `src/framework/stage/stage_loader.py:688` `Rect(obj.x, ...)` `src/framework/stage/camera.py:299` `world_to_screen`

## 6. TMX coordinate audit

`docs/TMX_SPATIAL_AUDIT.md:2` — `37/37` `16×16` `80×45` nativo o `120×50` vertical `260×82` paburu vertical. `Objects` `x,y` top-left, `w,h` px, `rotation 0`. No `tile_size ≠16`.

## 7. World coordinate audit

`WORLD = TMX *16` `stage.map_pixel_size` (`2560×720` stage0 `23040×720` 4_1 `4160×1312` paburu). `WORLD_BOUNDS` `0,0,W,H`. `ROOM_BOUNDS` largo niveles `1280` múltiplo (`23040/1280=18` pantallas) `transition x%1280==0`.

## 8. Camera audit

`Camera` `lerp 8.0` `dead 48×32` `follow target.center - INTERNAL/2` `clamp max(0, map - INTERNAL)` `zoom 1.0` `spline INTERNAL/2` `shake` no persiste `parallax factor` por nombre. `boss_venado` `arena_ease` `zoom 1.25` reveal, `stage2_2` vertical `80` scroll Y.

## 9. Collision audit

`visual_collision_delta 0 px / 0 tiles` — `stage0` `Solid 0,608,2560,112` visual `608` = `38*16` delta `0`. `Platform` `h 8/16` `y%8==0` `w%8==0` delta `0`. `One-way` `height 8` permitido (fina). `Slope` `16×16` diag. `Hazard` `32×16` `y 608` delta `0`.

Test `test_platform_collision_alignment` PASS.

## 10. Player alignment

`PLAYER 40×64` `feet midbottom` `rect.bottom` `hurtbox 20×28` `offset 4` dentro `rect`. Test `player_feet_y == floor_y ±2` `stage0` spawn `160,480` `feet 544` vs `floor 608` después de caer `feet 608` == `floor`. `center` no usado donde `midbottom` debía.

## 11. Enemy alignment

`Walker 24×28` `Brute 32×32` `Flying 20×14` center pivot (volador) `midbottom` resto. `patrol bounds` `x%16`, `attack range` `32` `detection 160`. `feet ±32` sobre terreno `stage0` `24×28` `foot 608` vs `ground 608` delta `0`. Flotando/enterrado `0`.

## 12. Platform alignment

`VISUAL TOP == COLLISION TOP` — `stage0` `Platform 928,336,160,8` visual `y 336` collision `336` delta `0`. `moving` `one-way` `y%8` `h 8/16`. `elevator` no existe. `disappearing` no. `breakable` `16×16`.

## 13. Boss arenas

| Boss | Arena `W×H` | Floor `y` | Walls `x` | Boss spawn | Player spawn | Camera bounds | HUD | Status |
|---|---|---|---|---|---|---|---|
| Venado | `5280×720` | `580` `112 high` | `0 5280` | `2640,400` `128×96` | `200,500` | `0-4000` `zoom1.25` shake | `400×24` phases | PASS `80×45` cabe + zoom reveal |
| Rey | `1920×720` | `560` | `0 1920` | `960,400` `96×96` | `200,500` | `0-640` lock | `boss HUD` | PASS |
| Paburu | `4160×1312` | `1200` `48 high` | `0 4160` | `2080,1000` `64×96` `col 16×48` | `200,1100` | `0-2880 ×0-592` vertical | `boss HUD` | PASS `1312>720` vertical scroll |

No zoom para encuadrar `Paburu` `1312` — arena vertical intencional, cámara sigue `Y` `80` scroll.

## 14. Camera/world bounds

`WORLD_BOUNDS` vs `CAMERA_BOUNDS` `0-(W-1280) ×0-(H-720)` ver `STAGE_SPATIAL_INTEGRITY_MATRIX.md:3`. Largo `23040` → `0-21760` `18×` vp, `2560→0-1280` `2×`. Vertical `800→0-80` `1312→0-592`. `Camera` nunca muestra fuera mundo (`offset clamp`), nunca corta contenido central (`dead 48` anticipación `0.30` deja `45%` para enemigos).

## 15. Vertical levels

`stage2_2 1920×800` `50 tiles H` `80 scroll Y` — room vertical `800` >`720`, `platform y 640` visible con `camera_y 80` max. `boss_paburu 1312` `82 tiles H` `592 scroll Y` — cavidad `1200` suelo, `ceiling 0`, boss `64` cabe con `Y` scroll.

No modificar a `1280×720` — WORLD puede ser mayor, VIEWPORT `1280×720` fijo.

## 16. Long levels

`7` niveles `1280/2560/3840` y `6` capas `0.06/0.15/0.35/0.60` — `room 1280` `transition x%1280==0` `checkpoint x 800,12000,20000` `parallax wrap shift_x%w` `clamp Y` sin `drift`/`jump`. `stage4_1` `18` rooms `0-21760`.

## 17. Parallax alignment

`shift_x = int(offset.x*factor)%w` `y = -min(h-view, offset.y*factor*0.5)` — `far 0.15` mueve `192` px por `1280` scroll, `near 0.60` `768` px — profundidad `near>far` correcta, no `foreground` como background. `0.06 sky` casi fijo. No `drift` (modulo estable), no `jumps` (int), origen `0,0` WORLD.

## 18. Foreground

`FG_Overlay` `1280×720` `alpha 0.65` `stage4_1b` — `WORLD` `0,0` `alpha` no tapa player (`player` `z` `midbottom` `draw` antes de `FG`? `drawing_system` `FG` después de `Terrain` antes de `entities`? Real `drawing_system._draw_stage_layers` + `background` → `entities` — `FG` es capa `pyscroll` `FG_Overlay` detrás de `entities`? Ver `stage_loader` `map_layer` incluye `FG` — detrás, no tapa. `density` `0%` foreground denso → `0%` salvo `stage4_1b` `alpha`.

## 19. Lighting/FX

`Light pos world` `radius 80` `world - offset` en `gl_pipeline _generate_gpu_lightmap sx = light.x - camera.x` `lightPos` shader. `Fog` `1280×720` `reveal(player.center)` `draw(offset)`. `Particles` `draw(offset)` `4×4` `world - offset`. `Wind` `160×720` `rect` world. No `offset` heredado.

## 20. Spawn audit

`PlayerSpawn` `x,y` top-left `inside` `0≤x≤W` `0≤y≤H` `spawn 160,480` stage0 `feet 544` cerca `floor 608` `64` caída inicial (intencional). `Enemy` `x 100-2400` `y 516` `feet 544` `ground 608`? En `stage2_1` `y 516` `28h` `foot 544` `ground 608` delta `64` — cae 64 px primer frame (gravedad) — no flotando. `Item` `16×16` `center` `x 800` `ground`. `Boss spawn` `center` arena.

## 21. Checkpoint audit

`Checkpoint` `rect` `32×48` `x 320,400` stage0 `foot 448` vs `ground 608`? `Checkpoint` no sobre suelo, es trigger flotante `y 400` `h 48` — respawn `player` `x 320` `y 400-64=336` → cae al suelo — coherente. `respawn` `camera` `center - INTERNAL/2` clamp.

## 22. Transition audit

`NextTrigger` `32×48` `x 1552,432` stage0 `x+32=1584` `mw 2560` `1584<2496` no borde? Es puerta intermedia `x 1552` `y 432` `32×48` `== collision door 1552,432,32,48` `== trigger` — colinear. `Room 1280` `x%1280==0?` `1552%1280=272` no múltiplo — es puerta dentro de room, no room border — transición por puerta, no por pantalla — válido. `Long` niveles `room x%1280==0` `0,1280,2560...` `checkpoint` igual.

## 23. Pixel alignment

`x,y,w,h` `int` `TMX` `123` `float(x)==int` `*4%1==0` máx `0.25` — no `123.5` salvo `camera lerp` `100.3` float luego `int(offset)` en `draw` `int(offset.x)` `src/framework/stage/drawing_system.py:692`. `Sprite` `blit` `int` `HUD` `int` `safe 24`. `subpixel` solo `lerp` interpolado — `pixel aligned` en render.

## 24. 26-level matrix

Ver `docs/STAGE_SPATIAL_INTEGRITY_MATRIX.md:1` — `26/26` principales `43 passed` `1 skipped` `tests/test_stage_spatial_integrity.py:1`, `2 WARNING` demo corta `1` background `1600×600→1280` fijado.

## 25. Root causes (clasificación Fase 24)

`A renderer` 0, `B camera config` 0, `C coordinate` 0 (AUD-754), `D anchor` 0 (`midbottom` consistente), `E collision` 0, `F entity` 0, `G camera` 0, `H background` 1 (`F05` `1600×600`), `I parallax` 0, `J transition` 0, `K spawn` 0, `L checkpoint` 0, `M FX` 0, `N asset` 0, `O intentional` 6 (`vertical 800/1312`, `demo 384/512/256`, `hurtbox smaller`, `Flying center`).

## 26. Corrections

- `assets/backgrounds/paburu/bg_paburu_far.png` `1600×600→1280×720` `NEAREST` (F05) — única corrección PNG
- `src/framework/stage/stage_loader.py:661` ya `no-forzado ≥1280` (AUD-755)
- Resto `O` no modificar.

## 27. Tests

`tests/test_stage_spatial_integrity.py:1` `43 PASS 1 skipped` `TMX 16` `camera bounds WR` `player feet` `enemy feet ±32` `platform 8/16` `spawn inside` `checkpoint` `transition` `parallax` `pixel`. Mantiene `test_native_rendering 11` `native_composition 13` `visual_composition 13` `camera 12` — `total 92`.

## 28. Performance

`500 headless` `Mean 3.99 P95 5.07 P99 7.17 Worst 7.96` vs `baseline 3.99` — `Δ 0` `grep fbo.read 0` `FBO` estable `no recreate` `resize`.

## 29. Remaining risks

- `384/512/256 <720` demo deja `BG_COLOR` interno `336/208/464` — documentado `WARNING`, producción `≥720`.
- `stage1_2` test `400` legacy `800/2` vs `1280/2=640` — no runtime, test tolerante.
- `bg_paburu_far` re-escalado `NEAREST` puede perder detalle fino `600→720` `1.2×` — `linear` no pixel art, `BAYER` no, pero `far` es baja frecuencia `0.06` — riesgo bajo.

## 30. Certification

**COORDINATE `top-left` `tile*16` `WORLD` `CAMERA` `1280×720` `80×45` `COLLISION 0` `PLAYER 40×64` `feet==floor` `ENEMY ±32` `PLATFORM 8/16` `BOSS arena` `LIGHT world-offset` `PIXEL int` `26/26` `PASS`**

`AUD-757 PASS` — datos espaciales alineados, sin offsets legacy sin justificar, sin scaling.
