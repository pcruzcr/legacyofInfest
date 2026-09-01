# VISUAL FINDINGS — NATIVE AUDIT FINAL

**Fecha:** 2026-09-01 · **26 niveles** `qa_screenshots` `metrics_qa` `STAGE_SPATIAL_INTEGRITY_MATRIX`

| ID | Level | Screen `1280×720` | Object | Observed | Expected | Delta `px` | Root Cause `V01-V10` `A-N` | Evidence | Fix | Risk |
|---|---|---|---|---|---|---|---|---|---|
| VF01 | stage1_1 | `mid 640,200` | `bg_mid 2560×720` `brightness 122.9` `100%` | `122.9` `67.2` `100%` domina `player 40` `14.7` vs `bg` | `31.8` `18.3` `stage0` | `91` `86%` | `V04 Contrast` `A-N` `H background` | `metrics stage1_1 122.9` `stage0 31.8` `qa_screenshots/stage1_1_normal` | `TMX ambient_light 0.60→0.55` `stage1_1.tmx:13` (no scaling) | Bajo `TMX property` |
| VF02 | hall | `0-1280` | `hall 1760×720` `2.3%` `71 objs` `16×32` | `2.3%` `24.6` sparse `Composition 70` | `36.2%` `stage0` | `34%` | `V10 Intentional` `A-N` `O` `hall` lobby vacío | `metrics hall 2.3%` `STAGE_SPATIAL` `71` `2.3%` | Ninguno `hall` `lobby` vacío | Nulo |
| VF03 | stage2_2 | `1920×800` | `Camera 0-640×0-80` `80 Y` `player 40×64` `8.9% H` | `80` `Y` `800>720` `vertical` `Navigation 88` | `80` | `0` | `V10` `vertical 800` intencional `50 tiles H` | `TMX 120×50 1920×800` `metrics 163 53 100%` | Ninguno | Nulo |
| VF04 | stage_mecanicas | `4960×384` | `World 384<720` `BG 720` `336 BG_COLOR` | `384` `336` `BG_COLOR` `internal` | `720` | `336 /21 tiles` | `V10` `demo corta` `E level data` `B` `384<720` | `STAGE_SPATIAL` `384` `BG 720` `qa_screenshots/stage_mecanicas` | Ninguno `WARNING` documentado | Bajo |
| VF05 | all | `1280×720` | `Player 40×64` `feet midbottom` `hurtbox 20×28` `+4` | `feet 608==floor 608` `0` | `0` | `0` | `V10` `hurtbox smaller` `O` | `test_player_feet 0` | Ninguno | — |
| VF06 | all | `1280×720` | `Tile 16×16` `nearest` `platform w×16` `h 8/16` | `16` `nearest` `0` `smoothscale` `tile` `0` | `16` | `0` | `V10` `nearest` `pipeline` | `RENDER_PIPELINE_AUDIT` `0` `FORBIDDEN` | Ninguno | — |

**Clasificación:** `VF01 V04` `1` `V04` `contrast` `TMX` `ambient_light` `VF02-V06` `V10` `5` `Intentional`.

**Total:** `6` findings `1` `V04` `5` `V10` — `0` `V01-V09` estructural `scaling` `zoom`.

**Verificación:** `capture_dynamic_qa 60 frames` `hud_stable True` `camera_max 0.0` `bg_jumps 0` `player_screen 1.5`.
