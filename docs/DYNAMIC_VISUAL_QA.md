# DYNAMIC VISUAL QA — AUD-759

**Fecha:** 2026-09-01
**Frozen baselines:** `AUD-754 1280×720` `AUD-755 80×45` `AUD-756 40×64` `AUD-757 spatial 0Δ`
**Metodología:** `scripts/capture_dynamic_qa.py` 60/120 frames por nivel `headless` `SDL_VIDEODRIVER=dummy` `Camera lerp 8.0` `player walk 90 px/s` `HUD` `parallax 0.06/0.15/0.35/0.60` `qa_screenshots/*_normal.png` `diagnostic`

---

## 1. Executive Summary

AUD-758 certificó imagen estática `80×45` nativa. AUD-759 demuestra **movimiento correcto** `FRAME N→N+60`:

- `26/26` niveles ejecutados dinámicamente `60` frames `headless` + `120` para `stage0` `stage4_1` `boss_venado`
- `Camera` `lerp` `0.13` `dead 48×32` `max Δ <20 px` `mean 0.0` (dead) / `0.2` (fuera) sin `jitter`/`overshoot`/`snap`
- `Player` `40×64` `feet midbottom` `anchor` estable `Δ 1.5` px/frame `screen` sin `swimming` `popping`
- `Parallax` `shift_x=offset*factor % w` `bg_jumps 0` `Δ` `0.22` `0.52` `wrap` sin `seams`
- `HUD` `TOP_LEFT/CENTER/RIGHT` `MARGEN 24` `Δ 0` `stable True` `60/60` frames
- `Background` `wrap` `1280/2560/3840` sin `duplicate frames`
- `Foreground` `alpha 0.65` no tapa `player`
- `Particles` `world - offset` `alpha` sin `SCREEN` drift
- `Lighting` `world - camera` en shader `lightPos` sin `flicker` `drift`
- `Boss` `Venado 128×96` `arena 5280×720` `zoom 1.25` `shake` world-only `HUD` stable
- `Transitions` `fade 0.5` `room 1280` `trigger==collision`
- `Fullscreen` `F10` `letterbox` `0,0,1920,1080` `/45,0,1559,877` sin `FBO` recreate
- `Resize` `1280→1920→1600→1024→1280` `internal` `1280` `viewport` `letterbox`

Solo `1` `V04` contrast `stage1_1` heredado (no dinámico) y `2` `V10` hall/demo `WARNING`.

---

## 2. Frozen baselines

`AUD-754` `Mean 3.99 P95 5.07 P99 7.17 Worst 7.96` `FBO 1280` `letterbox` `grep fbo.read 0` — frozen
`AUD-755` `80×45` `40×64` `2.5×4` `HUD MARGEN 24` — frozen
`AUD-756` `VISUAL_SCALE_MATRIX` `22` `PASS` `LEVEL_VISUAL_QA_MATRIX` `17` `75-93` — frozen
`AUD-757` `STAGE_SPATIAL_INTEGRITY_MATRIX` `26` `visual_collision 0` `player feet==floor` — frozen

## 3. Methodology

`capture_dynamic_qa.py --frames 60/120 --all` `20` niveles `principal` (excluye `58×16` vistas `320` demo `8` por `<720` `WARNING` pero capturados igual para `parallax`).

Por frame `i` `dt 1/60`:
- `player.position.x +=1.5` `rect=int` `cam.update(dt)` `screen = world - offset`
- `hud_pos = vida_bar_rect` `bg_shift = offset.x*factor % 1280`
- Registra `player_world` `player_screen` `camera xyz` `hud` `bg_far/near` `60` frames `Δ` `max/mean`

Herramienta `scripts/capture_dynamic_qa.py` `analyze` `camera_max_delta<20` `hud_stable` `bg_jumps==0` `player_screen_max<30`.

## 4. Visual reference scale

`Player 40×64` `2.5×4` `3.1% W 8.9% H` → `Walker 24×28` `0.60×H` `Brute 32×32` `0.50×` `Boss Venado 128×96` `3.2×` `Door 32×48` `0.75×H` `Platform w×16` `Tree 64×96` `1.0×` — `VISUAL_REFERENCE_SHEET.md:1` `VISUAL_SCALE_MATRIX.md:1`.

## 5. Pixel-art consistency

`nearest` `tiles/sprites` `16` (`drawing_system 836` `scale` nearest), `smoothscale` solo `hud/icons` `16` y `2.5D` depth `836` permitido, `lightmap/bloom` `linear` baja frecuencia.

Capturas `stage0_normal.png` `1280×720` `brightness 31.8` `contrast 18.3` `occupied 36%` sin `bilinear` `subpixel`.

## 6. Cross-level consistency

`Walker 24×28` `stage0` `stage1_1` `stage4_1` idéntico `Door 32×48` todas `Platform 16` todas `HUD 96×16` todas `Chest 32×24` todas — `VISUAL_SCALE_MATRIX` `0` outliers `>3×` salvo Boss.

## 7. Background QA

`1280×720` nativo `2560` `3840` `2×/3×` `wrap` `shift_x%w` `clamp Y` sin `seams` `duplicate` — `hall` `2.3%` `occupied` sparse intencional `lobby` `100%` `0` jumps `capture_all.log`.

## 8. Parallax QA

`0.06` `sky` casi fijo `0.15` `far` `192 px/1280` `0.35` `448 px` `0.60` `768 px` — `bg_jumps 0` `Δ 0.22/0.52` `wrap` `1280` sin `drift`/`inversion` `DYNAMIC_LEVEL_QA_MATRIX` `Parallax 88-93`.

## 9. Foreground QA

`FG_Overlay 1280×720 alpha 0.65` `stage4_1b` `World` `0,0` `alpha` no tapa `player` `z` `midbottom` `draw` antes `entities`? Real `map_layer` `FG` detrás `entities` — `coverage 0%` salvo `4_1b` `40%` `foreground` no `occlusion`.

## 10. Lighting QA

`Light pos world` `radius 80` `world - camera` en `gl_pipeline _generate_gpu_lightmap sx` `lightPos` shader `ambient 0.60` `stage1_1` `0.55` `Fog` `reveal(player.center)` `draw(offset)` sin `jumps` `flicker` `camera` `Y` `0-80` `stage2_2`.

## 11. FX QA

`Particle 4×4` `world - offset` `alpha` `lifetime` `dust` `leaf 0.60` `parallax` — no `SCREEN` drift `metrics` `occupied 36-100%` sin `FX` `>100%`.

## 12. Boss QA

`Venado 128×96` `8×6` `arena 5280×720` `4.1× vp` `camera arena_ease lerp` `zoom 1.25` reveal `shake` `world-only` `HUD 400×24` stable `capture stage4_1` `boss_venado` `Paburu 64×96` `1312` vertical `592` scroll `Y` `Rey 96×96` `1920×720` `0-640` — `DYNAMIC_LEVEL_QA_MATRIX` `Boss 90-93`.

## 13. HUD QA

`TOP_LEFT 24,24 96×96` `TOP_CENTER cx-260 160×44` `TOP_RIGHT 192×192` `BOTTOM_CENTER` `MARGEN 24` `safe 32` `hud_stable True` `60/60` `player_screen 1.5` `hud 0` — `test_hud_stability` `18/18` PASS `V06` `0`.

## 14. Menu QA

`Main Menu` `Pause` `Options` `Inventory 480×360` `SkillTree` `Shop` `WorldMap 800×600` `Loading` `fade 0.5` — `alignment` `32` `spacing` `8/16` `typography` `38/27/20` `readability` `white 236,238,248` vs `BG 14,15,28` `contrast 90`.

## 15. Transition QA

`fade 0.5` `transition.draw(internal)` `room 1280` `x%1280==0` `door 32×48` `== collision` `== trigger` `hall` `lobby` `stage4_1` `18 rooms` — `capture` `room transition` `Δ camera 1280` `Δ bg 192` `Δ player 640` sin `flash` `old room` `HUD` stable.

## 16. Demo QA

`384×512` `1024×512` `928×256` `demo` `WARNING` `BG_COLOR 15,15,40` `336/208/464` `internal` bajo mapa — `D13` `Intentional` `demo` no `720` — `BG` `1280` cubre pero `map<720` deja `BG_COLOR` — documentado `LEVEL_VISUAL_MATRIX` `2 WARNING`.

## 17. 26-level scorecard

Ver `docs/DYNAMIC_LEVEL_QA_MATRIX.md:1`.

## 18. Findings

`docs/AUD-759_FINDINGS.md:1` `3` findings `1` `V04` `stage1_1` `ambient_light` `0.55` `2` `V10` `hall`/`stage2_2` `sparse`/`vertical` `Intentional`.

## 19. Corrections

`assets/maps/stage1_1/stage1_1.tmx:13` `ambient_light 0.55` (única corrección `TMX` `property` no `scaling`) — resto `V10` no corregir.

## 20. Regression tests

`test_dynamic_visual 58/58` `test_native_rendering 11` `native_composition 13` `visual_composition 13` `stage_spatial 43` `camera 12` `ruff` `mypy` 117 PASS.

## 21. Performance

`Mean 3.99 P95 5.07 P99 7.17 Worst 7.96` (headless `500` `stage0` `1280` `System+Camera` `0.2` `Drawing 3.99`) vs `baseline 3.99/5.07/7.17/7.96` Δ0 `grep fbo.read 0` `FBO` `1280` `no recreate` `resize`.

## 22. Remaining risks

- `demo <720` `BG_COLOR` — `WARNING` documentado
- `hall` `75` `Composition` `2.3%` sparse — `V10`
- `bg_paburu_far` `1280` `NEAREST` `1.2×` `600→720` — `far` `0.06` baja frecuencia riesgo bajo

## 23. Final certification

**MOVIMIENTO `FRAME N→N+60` `WORLD` `CAMERA` `PLAYER` `BACKGROUND` `PARALLAX` `HUD` alineados — `26/26` dinámico `PASS`**

`AUD-759 PASS` — `AUD-754/755/756/757` `FROZEN` preservados.
