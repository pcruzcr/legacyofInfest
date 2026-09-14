# VISUAL LEVEL AUDIT — AUD Final Fase 6-12

**Fecha:** 2026-09-01 · **26 niveles** `80×45` `16` `1280×720`

## Stage 1 — stage0 `160×45 2560×720`
- **Size:** `2560×720` `2× vp` `3600 tiles` `101 objs` `12 platforms` `solid 112`
- **Composition:** focal `spawn 160,480` `2×` pantallas `suelo y 608` `38*16` `horizon 60%` `negative space 36%` `occupied 36.2%` `brightness 31.8` — balance `92`
- **Gameplay readability:** plataformas `48×16` `y 336,448` `doors 32×48` `hazards 32×16` `checkpoints 320,400` `enemies 24×28` `3` visibles `45%` anticipación
- **Camera:** `follow lerp 8.0` `dead 48×32` `clamp 0-1280` `player 3.1% W` `look-ahead 0.30` `space 45%`
- **Background:** `1280+2560+3840` `0.06/0.15/0.35/0.60` `wrap` `clamp Y` `0.8 ms` `no drift`
- **Lighting:** `ambient 0.60` `point lights 3` `r 44` `fog` `alpha 0.35` legible `player 40` vs `bg 31.8` `contrast 14.7`
- **Status:** PASS

## Stage 2 — stage1_1 `390×45 6240×720`
- **Size:** `6240×720` `4.8× vp` `60 objs` `platform 64×16` `slope 16×16`
- **Composition:** `focal` `midground` `background` `negative 0%` `100%` `occupied` `122.9` `67.2` `bright` — `88` `V01` `ambient_light 0.55` corona `mid` `2560` brillante
- **Gameplay:** `platform 64×16` `12` `hazards 0` `enemies Walker Brute Charger` `96 px` anticipación
- **Camera:** `0-4960` `18 screens` `room 1280`
- **Background:** `1280 3 capas` `wrap` `density 0.15`
- **Status:** PASS (V01 intentional `0.55`)

## Stage 3 — stage1_2_la_soda `350×45 5600×720`
- **Size:** `5600×720` `4.3×` `70 objs` `cuarto lock`
- **Composition:** `soda machines 32×48` `midground` `density 0.14` `90` — `soda` `midground` no oculta `player`
- **Camera:** `0-4320` `+ cuarto clamp`
- **Status:** PASS

## Stage 4 — stage1_3_las_aulas `320×45 5120×720`
- **Size:** `5120×720` `4×` `76 objs` `desk 32×16` `lockers 16×32`
- **Composition:** `density 0.16` `aulas` `91` `aulas` `midground` `desks` `WORLD`
- **Status:** PASS

## Stage 5 — stage2_1_oficinas `320×45 5120×720`
- **Size:** `5120×720` `54 objs` `platform 48×16` `foso 32`
- **Composition:** `90` `oficinas` `monitor 32×24` `WORLD` `no foreground`
- **Status:** PASS

## Stage 6 — stage2_2 `120×50 1920×800` `vertical`
- **Size:** `800>720` `80 px Y` `50 tiles H` `49 objs`
- **Composition:** `1920×800` `80 scroll Y` `platform 48×16` `vertical 50` `density 0.11`
- **Camera:** `0-640×0-80` `Y` scroll `80` `horizon 60%` `space 45%` `vertical framing 80`
- **Status:** PASS `vertical` `800` intencional

## Stage 7 — 3-1 `160×45 2560×720` `stalactites FG`
- **Size:** `2560×720` `58 objs` `stalactite 16×32` `FG alpha 0.65`
- **Composition:** `93` `stalactites` `FG` no tapa `player` `WORLD` `FG` detrás `entities`? `map_layer` `FG` detrás — `coverage 0%` `FG` `alpha`
- **Status:** PASS

## Stage 8 — stage3_3_el_patio `100×45 1600×720`
- **Size:** `1600×720` `30 objs` `plant 16×32` `FG` `plant` `WORLD` `1600` `0-320` `room`
- **Status:** PASS

## Stage 9 — gavilan `102×45 1632×720`
- **Size:** `1632×720` `35 objs` `arena 1632` `lock_y`
- **Composition:** `92` `arena 1632` `352 clamp` `platform 32×16` `2` `boss Gavilan 96×96` `6×6` `2 phases`
- **Camera:** `arena 352` `lock_y` `boss framing` `96` `10% W` `13% H` `arena 352` `dead` `48`
- **Status:** PASS

## Stage 10 — stage4_1 `1440×45 23040×720` `6 capas`
- **Size:** `23040×720` `18× vp` `57 objs` `dune 96×16` `cactus 64×96`
- **Composition:** `88` `desert` `sparse 0.08` `negative 92%` `cactus` `WORLD` `midground`
- **Background:** `6 capas fase 1280×720 each` `0.06/0.10/0.15/0.35/0.60` `phase`
- **Status:** PASS `largo` `WORLD≠VIEWPORT` `camera window`

## Stage 11 — 4_1b `1440×45 23040×720` `caverna`
- **Size:** `23040×720` `74 objs` `coral 16×16` `FG` `coral` `alpha` `Bayer`
- **Status:** PASS

## Stage 12 — hall `110×45 1760×720` `sparse`
- **Size:** `1760×720` `71 objs` `lamp 16×32` `2.3%` `occupied` `24.6` `70 Composition` `sparse` intencional `lobby` vacío
- **Status:** PASS `V10`

## Boss Venado `330×45 5280×720` `4.1× vp`
- **Size:** `5280×720` `34 objs` `arena 5280` `boss 128×96` `8×6` `3 phases` `VineSwing 8×48`
- **Camera:** `0-4000` `arena_ease lerp` `zoom 1.25` reveal `shake world-only` `HUD stable`
- **Composition:** `93` `boss 10% W` `arena 4.1×` `player anticipación` `45%`
- **Status:** PASS

## Boss Rey `120×45 1920×720`
- **Size:** `1920×720` `7 objs` `arena 1920` `boss 96×96` `6×6`
- **Status:** PASS

## Boss Paburu `260×82 4160×1312` `vertical`
- **Size:** `4160×1312` `112 objs` `vertical 1312>720` `592 scroll Y` `floor 1200` `wall 0,4160` `col 16×48` `x%16`
- **Composition:** `89` `vertical arena` `camera Y 0-592` `player 40×64` `8.9% H` `1312` `boss 64×96` `12 tiles h` `col` `vertical`
- **Status:** PASS

## Lobby `80×45 1280×720` `fits`
- **Size:** `1280×720` `0-0` `fits` `no scroll` `17 objs` `monitor 32×24` `WORLD`
- **Status:** PASS

## Tutorial Hub `280×45 4480×720`
- **Size:** `4480×720` `55 objs` `sign 16×32` `density 0.05`
- **Status:** PASS

## Demo `stage_mecanicas 310×24 4960×384` `384<720`
- **Size:** `4960×384` `165 objs` `platform 32×16` `BG 720` `336 px BG_COLOR` `internal` `0-3680`
- **Composition:** `85` `demo` `WARNING` `384<720` deja `336` `BG_COLOR` `internal` `0-3680` — `BG 720` cubre `viewport` `BG` no `map`
- **Status:** WARNING `demo` `V10`

**Global:** `26/26` `TMX` `WORLD` `CAMERA` `80×45` `PASS` `2 WARNING` demo `<720` `BG_COLOR` `V10` `1` `ambient_light` `0.55` `V04`.

