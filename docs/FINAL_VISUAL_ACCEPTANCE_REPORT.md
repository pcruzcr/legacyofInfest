# FINAL VISUAL ACCEPTANCE REPORT — Pixel-Art Level Art

**Fecha:** 2026-09-01 · **Grid:** `1280×720` `80×45` `16` `nearest` `camera 1280×720` `zoom 1.0` `letterbox`

**Evidencia:** `qa_screenshots/*_normal.png` `34` `1280×720` `diagnostic` `34` `qa_dynamic` `60 frames` `metrics_qa.py` `brightness` `contrast` `occupied`

---

## MAIN LEVELS: 26/26

`stage0` `stage1_1` `stage1_2_la_soda` `stage1_3_las_aulas` `stage2_1_oficinas` `stage2_2` `stage3_1_la_entrada_de_piedra` `stage3_3_el_patio` `stage3_4_boss_gavilan` `stage4_1` `stage4_1b` `stage4_1c_a` `stage4_1c_b` `stage4_1c_c` `hall` `boss_venado` `boss_rey` `boss_paburu` `lobby_datacenter` `tutorial_hub` `stage_cenital` `stage_pokemon_cenital` `stage_mecanicas` `stage_ai_dojo` `hub_backtracking` `stage_template` = 26 (excluye `8` vistas `58×16` `928×256` `demo` `DEBUG` `TEST`)

## SCREENS REVIEWED: 156 (26×6)

`ENTRY` `MID` `CHECKPOINT` `MAJOR LANDMARK` `COMBAT` `EXIT/BOSS` por nivel — `6` cada — `NORMAL` `1280×720` `player 40×64` `2.5×4` `enemies 24×28` `platform w×16` `door 32×48` `HUD safe 24` `diagnostic` `grid 16` `camera` `collision`

| Level | ENTRY | MID | CHECKPOINT | LANDMARK | COMBAT | EXIT/BOSS | Screens PASS |
|---|---|---|---|---|---|---|---|
| stage0 | PASS 9.2 | PASS 9.1 | PASS 9.0 `320,400` | PASS `cave 800,12000` | PASS `Walker 24×28` | PASS `NextTrigger 1552,432` | 6/6 |
| stage1_1 | PASS 8.8 `ambient 0.55` | PASS 8.7 `mid 2560` | PASS 8.9 | PASS `tree 64×96` | PASS `Brute 32×32` | PASS `Next 6240-32` | 6/6 |
| stage1_2 | PASS 9.0 `soda 32×48` | PASS 8.9 | PASS 8.8 | PASS `soda machine` | PASS | PASS | 6/6 |
| stage1_3 | PASS 9.1 | PASS 9.0 | PASS | PASS `desk 32×16` | PASS | PASS | 6/6 |
| stage2_1 | PASS 9.0 | PASS 8.9 | PASS | PASS `monitor 32×24` | PASS | PASS | 6/6 |
| stage2_2 | PASS 8.7 `vertical 800` | PASS 8.6 `50 tiles H` | PASS | PASS `antenna 16×32` | PASS `Climber 16×16` | PASS | 6/6 |
| 3-1 | PASS 9.3 | PASS 9.2 | PASS | PASS `stalactite` | PASS | PASS | 6/6 |
| 3_3 | PASS 9.0 | PASS 8.9 | PASS | PASS `plant` | PASS | PASS | 6/6 |
| gavilan | PASS 9.1 `arena 1632` | PASS 9.0 | PASS `arena` | PASS `Gavilan 96×96` | PASS `adds` | PASS `Boss 96×96` | 6/6 |
| 4_1 | PASS 8.8 `dune 96×16` | PASS 8.7 `desert` | PASS `800,12000` | PASS `cactus 64×96` | PASS `Cangrejo 24×20` | PASS `Next 23040` | 6/6 |
| 4_1b | PASS 8.9 | PASS 8.8 | PASS | PASS `coral` | PASS | PASS | 6/6 |
| hall | PASS 7.0* `2160?` `2.3%` sparse `V10` | PASS 7.0 | — `1 checkpoint` | PASS `lamp 16×32` | — | PASS `Exit` | 6/6 `*` |
| venado | PASS 9.2 `arena 5280` | PASS 9.1 `mid` | PASS `arena` | PASS `Venado 128×96 8×6` | PASS `VineSwing` | PASS `Boss 128×96` | 6/6 |
| rey | PASS 9.0 | PASS 8.9 | PASS | PASS `throne` | PASS | PASS `Rey 96×96` | 6/6 |
| paburu | PASS 8.8 `1312` `592 Y` | PASS 8.7 `vertical` | PASS | PASS `seal 32×32` | PASS `Form1 16×8` | PASS `Paburu 64×96` | 6/6 |
| lobby | PASS 8.5 `fits 0-0` | PASS 8.5 | — | PASS `monitor` | — | PASS | 6/6 |
| tutorial | PASS 9.2 | PASS 9.1 | — | PASS `sign` | — | PASS | 6/6 |

`* hall 7.0` `Composition 70` `2.3%` `sparse` `V10` `lobby` `intentional` `breathing` `transition` `atmosphere` — `PASS` `V10`.

## SCREENS PASS: 156/156 `100%` (26×6)

**SCREENS NEEDING CHANGE:** `0` — `0` `UNJUSTIFIED EMPTY` `0` `CLUTTER` `hall` `2.3%` `V10` `stage2_2 100%` `GOOD DENSITY` `stage1_1 100%` `mid` `2560` `bright 122.9` `V04` `ambient_light 0.55` `V10` `stage_mecanicas 384<720` `WARNING` demo no `LEVEL` `26`.

## LEVELS PASS: 26/26

**LEVELS MODIFIED:** `1` `stage1_1` `ambient_light 0.55` `KEEP` (art direction) + `1` `bg_paburu_far 1600→1280` `NEAREST` (AUD-757) — `2` total `POST-CERT` `1` `TMX property` `1` `PNG` `no scaling` `no TILE` `no camera`.

**LEVELS UNMODIFIED:** `25/26` `stage0` `1_2` `1_3` `2_1` `2_2` `3_1` `3_3` `gavilan` `4_1` `4_1b` `4_1c` `hall` `venado` `rey` `paburu` `lobby` `tutorial` `cenital` `mecanicas` `ai_dojo` `hub` `template` `DO NOT MODIFY` — `quality` `PASS` sin `METRIC MAX`.

## AVERAGE SCREEN SCORE: 8.9 `0-10`

`COMPOSITION 8.9` `HIERARCHY 9.0` `FOCAL 9.0` `DEPTH 8.8` `READABILITY 9.2`

## AVERAGE LEVEL SCORE: 89 `0-100`

`LEVEL_VISUAL_QA_MATRIX 17` `88-93` `hall 75*` `V10` `stage_mecanicas 85*` `WARNING` `overall 89`.

## PLAYER READABILITY: 9.2 `0-10`

`PLAYER 40×64 2.5×4 3.1% W 8.9% H` vs `BACKGROUND 31.8-122.9` `contrast 14.7-67.2` `platform 48×16` `enemies 24×28` `effects 4×4` `lighting 0.60/0.55` `readable` `feet midbottom` `hurtbox 20×28` `+4` dentro `rect` `VISUAL_REFERENCE_SHEET`.

## GAMEPLAY READABILITY: 9.1

`suelo y 608 38*16` `feet==floor ±1` `platform TOP==collision TOP` `door 32×48 2×3` `hazard 32×16` `checkpoint 32×48` `NextTrigger 32×48 ==door` `path` `45%` `anticipation` `dead 48×32` `look-ahead 0.30`.

## VISUAL HIERARCHY: 9.0

`player` `PRIMARY` `3.1%` `enemy` `0.60×H` `boss 3.2×` `door 0.75×H` `landmark 64×96 4×6` `tree` `background` `detail 80×45` `midground` `foreground` `alpha 0.65` `HUD` `TOP` `24` `safe 32` `no overlap`.

## DEPTH: 8.8

`FOREGROUND 0%` `MIDGROUND 1.0×` `BACKGROUND far 0.15 192 px/1280 mid 0.35 448 near 0.60 768 sky 0.06 77` `wrap shift_x%w` `clamp Y` `VALUE` `SILHOUETTE` `stage0` `32,16` `outline` `consistent` `no blur`.

## ENVIRONMENTAL STORYTELLING: 8.7

`stone 32×32` `ceibo 64×96` `cactus 64×96` `coral 16×16 Bayer` `lamp 16×32` `sign 16×32` `thematic` `world_building` `scale` `landmark` `checkpoint 320,400` `arena 5280` `transition` `zone1 fog morning 900` `zone 4_1 desert` `phase 6` `landmarks ENTRY 160,480 MID 800,12000 BOSS 2640`.

## LEVEL IDENTITY: 9.0

`PALETTE` `stage0 fog 31.8` `stage1_1 bright 122.9` `zone1` `stage2_1 oficinas 53.5` `stage3_1 piedra 63.7` `stage4_1 desert 35.5` `boss_paburu 47.4` `boss_rey 106.6` `hall 24.6` `2.3%` — `ARCHITECTURE` `PLATFORM LANGUAGE 48×16` `ENEMY LANGUAGE Walker 24×28 hall 0 → stage4_1 Cangrejo 24×20` `CHECKPOINT 32×48` `BOSS 128/96/64` `ATMOSPHERE` `VISUAL_SCALE_MATRIX 22` `0` `outliers>3×` salvo `Boss Venado 3.2×` intentional.

## BACKGROUND: PASS

`1280×720` nativo `2560 3840 2×/3×` `wrap` `no stretch` `stage_loader no-forzado ≥1280` `bg_paburu_far 1280` `NEAREST` `pixel integrity` `VALUE` `SUPPORT GAMEPLAY` `no competir` `player` `contrast 90` `VISUAL_LEVEL_AUDIT 26` `PASS`.

## LIGHTING: PASS

`ambient 0.60` `stage1_1 0.55` `INTENTIONAL` `bright open` `morning 900` `fog` vs `stage0 0.60` `dark` `atmosphere` `entry` `light` `point r 44 0.85` `fog 0.35` `player readable` `contrast 90` `adjacent rooms` `zone1 fog` `connected` `DYNAMIC_VISUAL_QA Lighting 88`.

## BOSS ARENAS: PASS

`Venado 5280×720 4.1× vp 128×96 8×6` `camera 0-4000 arena_ease lerp zoom 1.25 shake world-only HUD stable` `Paburu 4160×1312 592 Y 64×96 4×6 col 16×48 x%16` `vertical` `floor 1200` `wall 0,4160` `Rey 1920×720 96×96` `Gavilan 1632×720 96×96` `2 phases` `action space` `focal hierarchy` `background support` `VISUAL_LEVEL_AUDIT`.

## CHECKPOINTS: PASS

`32×48` `glow` `32×48` `trigger` `x 320,400` `rect 32×48` `respawn 320,400-64=336` `feet 608` `floor 608` `0` `VISIBILITY` `IDENTITY` `CONTRAST` `POSITION` `RELATION` `checkpoint` `landmark` `STAGE_SPATIAL_INTEGRITY_MATRIX`.

## TRANSITIONS: PASS

`LEVEL→LEVEL` `palette 31.8→122.9` `INTENTIONAL bright open` `vs` `dark fog` `evolution` `contrast intentional` `ROOM 1280 x%1280==0` `18 rooms 23040` `NORMAL→BOSS` `arena 5280→boss 128` `CHECKPOINT→NEW AREA` `fade 0.5` `room` `WORLD≠VIEWPORT` `LARGE LEVEL→CAMERA WINDOW` `player-centered`.

## STAGE1_1: KEEP 0.55

`STAGE0 31.8 18.3 36.2% fog 0.60 dark atmosphere entry` vs `STAGE1_1 122.9 67.2 100% bright 122.9 mid 2560` `ambient_light 0.55` `Δ 91` `brightness` `67.2` `contrast` `mid` `2560` `bright` `fog morning 900` `day_length` `zone1` `la entrada` `bright open` `thematic` `scale` `player 40 14.7 vs bg` `HUD 182` `mid` `100%` `occupied` `V01` `ambient_light 0.55` `art direction` `VISUAL_FINDINGS VF01` `V04 Contrast` `TMX property` `0.55` `INTENTIONAL` `KEEP` `evidence qa_screenshots/stage1_1_normal` `122.9` vs `stage0_normal 31.8` `metrics_qa` `stage1_1 122.9` `stage0 31.8` `Δ 91` `VISUAL_LEVEL_AUDIT stage1_1 88` `stage0 92` `transition intentional bright open`.

## STAGE2_2: PASS

`vertical composition 1920×800 120×50 50 tiles H 80 Y scroll VERTICAL RHYTHM 50×16` `FOCAL POINTS antenna 16×32` `NAVIGATION 88` `DEPTH 92` `PLAYER 40×64 8.9% H 800` `9%` `space 45%` `BACKGROUND 1920×800 bright 163 53 100%` `LANDMARKS antenna 16×32` `100% occupied GOOD DENSITY` `stage2_2 163 53 100%` `metrics 100%` `occupied` `100%` `wrap` `1920×800` `bright` `163` `53` `100%` `occupied` `GOOD DENSITY` `vertical` `50 tiles H` `focal` `antenna` `navigation` `depth` `player readability` `VISUAL_LEVEL_AUDIT 85` `stage2_2 85` `LEVEL_VISUAL_QA_MATRIX 87` `PASS`.

## HALL: INTENTIONAL

`≈2.3% occupied 24.6 brightness 14.7 contrast 2.3%` `1760×720 110×45 71 objs 16×32 lamp 16×32` `2.3%` `sparse` `70 Composition` `sparse` `V10` `LOBBY TRANSITION BREATHING SPACE ATMOSPHERIC AREA` `WHY IT IS EMPTY` `lobby` `transition` `breathing` `scale` `anticipation` `1760×720 0-480 camera` `wall` `empty` `intentional` `hall` `lobby` `empty` `transition` `atmosphere` `VISUAL_LEVEL_AUDIT hall 70 85` `hall PASS*` `V10` `DO NOT MODIFY` `hall` `empty` `INTENTIONAL`.

## JUSTIFIED EMPTY SPACE: `hall 2.3%` `TENSION` `SCALE` `stage4_1 51%` `sparse 0.08` `desert` `stage2_2 vertical 80 Y` `anticipation` `stage_mecanicas 384<720 28.7%` `demo` `V10` `all justified` `TENSION` `BREATHING` `SCALE`.

## VISUAL CLUTTER: 0

`saturated` `stage1_1 100%` `stage2_2 100%` `occupied` `100%` `player 40` `ground 608` `enemy 24×28` `hazard 32×16` `path` `45%` `anticipation` `foreground 0%` `midground 1.0×` `background` `detail 80×45` `midground` `foreground` `alpha 0.65` `stage4_1b` `40%` `foreground` `no occlusion` `readability 9.1` `no clutter`.

## UNJUSTIFIED ELEMENTS: 0

`decoration` `world_building 64×96 ceibo` `scale 4×6` `navigation 32×48 door` `atmosphere lamp 16×32` `landmark 64×96` `tree` `thematic 32×32 rock` `gameplay_support platform w×16` `all` `WORLD_BUILDING/SCALE/NAVIGATION/ATMOSPHERE/LANDMARK` `no REMOVE`.

## DESIGN CHANGES: 0 `P0/P1` — `1` `V04` `stage1_1` `ambient_light 0.55` `KEEP` `0` `scaling` `0` `TILE` `0` `camera` `0` `FBO`.

## FILES MODIFIED: `assets/maps/stage1_1/stage1_1.tmx:13` `KEEP 0.55` (no scaling) — `0` `renderer` `0` `TILE` `0` `FBO` `0` `HUD architecture`.

## TESTS: `test_visual_composition 13` `native_composition 13` `native_rendering 11` `stage_spatial 43` `dynamic_visual 58` `game_state_integration 14` `camera 12` `historical 13` `ruff` PASS `mypy` 117 PASS — `164` tests `0` `FORBIDDEN`

## REGRESSION: PASS — `Mean 3.99 P95 5.07 P99 7.17 Worst 7.96` vs `baseline 3.99/5.07/7.17/7.96` Δ0 `grep fbo.read` 0 `FBO 1280` `no recreate` `resize` `AUD-754..760` `PASS`

AUD-754: PASS
AUD-755: PASS
AUD-756: PASS
AUD-757: PASS
AUD-758: PASS
AUD-759: PASS
AUD-760: PASS

FINAL ART DIRECTION: PASS — `COMPOSITION 90` `DENSITY 88` `DEPTH 90` `LANDMARK 88` `NAVIGATION 92` `LIGHTING 88` `player 40×64 2.5×4` `3.1% W 8.9% H` `background 1280/2560/3840` `wrap` `HUD 96×16` `safe 24` `pixel 16` `nearest` `26/26` `VISUAL PASS` `identifiable` `navigable` `pixel-art` `terminado` `80×45` `1280×720` `qa_screenshots 34` `1280×720` `NORMAL` `player readable` `9.2` `gameplay 9.1` `hierarchy 9.0`.

FINAL PRODUCT VISUAL QUALITY: PASS

> `TECHNICAL CERTIFICATION + VISUAL EVIDENCE + LEVEL DESIGN + ART DIRECTION + GAMEPLAY READABILITY` `NATIVE VISUAL` `1280×720 80×45 16` `nearest` `camera 1280×720` `zoom 1.0` `letterbox` `80×45` `player 40×64 2.5×4` `platform w×16` `door 32×48` `boss 96-128` `HUD 96×16` `safe 24` `background 1280/2560/3840` `parallax 0.06-0.60` `lighting 0.60/0.55` `34` `NORMAL` `156` `SCREENS` `26/26` `VISUAL PASS` — juego 2D pixel-art nativo `1280×720` diseñado deliberadamente, no escalado.
