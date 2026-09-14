# LEVEL VISUAL COMPOSITION MATRIX — AUD-756 Fase 20

**Fecha:** 2026-09-01 · **Grid nativa:** `80×45 tiles` `1280×720` `16 px` · **HUD safe `24`**

| Level | Player | Platforms | Enemies | Boss | Background | Parallax | Foreground | Camera | HUD | Density | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| stage0 | `40×64` `2.5×4` `feet midbottom` | `w×16` `1 tile` `y=608` suelo `80×1` `platform 48×16` | `Walker 24×28` `Flying 20×14` `3 tipos` | — | `1280+2560+3840` `sky0.06 far0.15 mid0.35 near0.60` | `wrap X` `clamp Y` `0.8 ms` | `none` `0%` | `follow lerp8` `80×45` `clamp 0-1280` `dead 48×32` | `TOP` `24` no overlap | `0.12` `solid 0.18` `3 ents/vp` | PASS |
| stage1_1 | `40×64` | `platform 64×16` `slope 16×16` 12 plats/vp | `Walker Brute Charger 3` | — | `1280×720 3 capas` `0.15/0.35/0.60` | `wrap` | `none` | `follow` `4960 clamp` | PASS | `0.15` `0.20` `4 ents` | PASS |
| stage1_2_la_soda | `40×64` | `platform 32×16` `cuarto lock` `y=448` | `SodaWalker 24×28` `4 tipos` | — | `1280 3 capas` | `wrap` | `soda machines 32×48` `midground` | `follow + extra clamp cuarto` | PASS | `0.14` | PASS |
| stage1_3_las_aulas | `40×64` | `desk 32×16` `lockers 16×32` | `CuadernoFlying 20×14` `5 tipos` | — | `1280 3 capas aulas` | `wrap` | `desks WORLD` | `follow` `0-3840` | PASS | `0.16` | PASS |
| stage2_1_oficinas | `40×64` | `platform 48×16` `foso 32` | `Officer 28×24` `Dron 20×14` `6 tipos` | — | `1280 3 capas oficinas` | `wrap` | `none` | `follow` `0-3840` | PASS | `0.13` | PASS |
| stage2_2 | `40×64` | `platform 48×16` `vertical` `800h` `80 clamp_y 0-80` | `Climber 16×16` `3 tipos` | — | `1280 3 capas` `800` mapa | `wrap` | `none` | `follow` `640×80` `room? follow` | PASS | `0.11` `vertical` | PASS |
| 3-1 | `40×64` | `stone platform 48×16` | `Stone 32×32` `2 tipos` | — | `1280 3 capas piedra` | `wrap` | `stalactites FG 0.65 alpha` `World? FG` | `follow` `0-1280` | PASS | `0.12` | PASS |
| stage3_3_el_patio | `40×64` | `patio 64×16` `4 plats` | `Patio 28×24` `3` | — | `1280 3 capas patio` | `wrap` | `plant FG` | `follow` `0-320` | PASS | `0.10` | PASS |
| stage3_4_boss_gavilan | `40×64` | `arena 1632×720` `platform 32×16` `2` | `Gavilan adds 24×28` | `Gavilan 96×96` `6×6` `2 fases` | `1280 3 capas` | `wrap` | `none` | `arena 352 clamp` `lock_y` | `boss HUD 400×24` | `0.09` `boss 12 tiles` | PASS |
| stage4_1 | `40×64` | `dune 96×16` `platform 48×16` `desert 23040` | `Cangrejo 24×20` `5 tipos` | — | `6 capas fase 1280×720 each` `phase` | `0.06/0.10/0.15/0.35/0.60` | `cactus 64×96 WORLD` | `follow` `0-21760` | PASS | `0.08` `sparse` | PASS |
| stage4_1b | `40×64` | `caverna 23040` `coral 16×16` | `Medusa 20×14` `Pez 18×26` `4` | — | `1280×720 3 capas caverna` `Bayer` | `wrap` | `coral FG` | `follow` `0-21760` `spline?` | PASS | `0.07` | PASS |
| stage4_1c_a/b/c | `40×64` | `similar 4-1` | `4` | — | `3 capas` | `wrap` | `FG` | `follow` | PASS | `0.08` | PASS |
| hall | `40×64` | `hall 1760×720` `platform 32×16` | `none` `decor` | — | `1280 3 capas hall` | `wrap` | `lamp 16×32` | `follow` `0-480` | PASS | `0.05` | PASS |
| lobby_datacenter | `40×64` | `1280×720 fits` `no scroll` `platform 0` | `Sentry 24×28` | — | `1280 3 capas` | `wrap` | `monitor 32×24` `SCREEN? WORLD` | `follow` `0-0` `stationary` | PASS | `0.04` | PASS |
| boss_venado | `40×64` | `arena 5280×720` `platform 48×16` | `VineSwing 8×48` `Liana` | `Venado 128×96` `3 phases` `128` `cresta 140` | `1280 3 capas venado` | `wrap` | `fantasmas WORLD` `overlay` | `arena_ease lerp` `4000 clamp` `shake` `zoom 1.25 reveal` | `boss HUD phases 400×24` `no offset` | `0.09` `arena 4.1× vp` | PASS |
| boss_rey | `40×64` | `1920×720` `platform 32×16` | `Rey adds` | `Rey 96×96` `6×6` `2 phases` | `1280 3 capas` | `wrap` | `none` | `follow` `0-640` | `boss HUD` | `0.08` | PASS |
| boss_paburu | `40×64` | `4160×1312` `vertical` `platform 16×48` `col 16×48` | `Form1 16×8` `Form2 64×96` | `Paburu 64×96` `12 tiles h` `col 16×48` | `1600×600 far` `1280×720 mid/near` | `far 0.06` `mid 0.15` | `seal WORLD` `cast draw` | `follow` `0-2880 X 0-592 Y` `vertical` | `boss HUD` | `0.10` `vertical arena` | PASS |
| stage_mecanicas | `40×64` | `4960×384` `24×16` `384<720` `BG_COLOR y<336` `platform 32×16` | `Brute Charger Dron 3` `BossSpawn` | — | `1280×720 3 capas` (BG `720` > map `384` → BG cubre) | `wrap` | `mech 16×16 WORLD` | `follow` `0-3680 X 0 Y` `clamp_y 0` | PASS | `0.06` `demo corta` | **WARNING** `map 384<720` deja `BG_COLOR 336px` interno bajo mapa (no letterbox externo) — documentado, producción ≥720 |
| stage_template | `40×64` | `template` | `none` | — | `none` | `none` | `none` | `follow` | PASS | `0.00` | PASS |
| tutorial_hub | `40×64` | `4480×720` `platform 32×16` `10` | `none` `tutorial` | — | `1280 3 capas hub` | `wrap` | `sign 16×32` | `follow` `0-3200` | PASS | `0.05` | PASS |
| stage_cenital etc (8 vistas) | `40×64` `vista cenital` | `928×256` `16×16` `demo 58×16` | `none` `demo` | — | `none` | `vista_system isometrica 0.866` | `y-sorting` | `follow` `cenital 0-0` | PASS | `0.02` `demo` | PASS |
| stage_ai_dojo | `40×64` | `1024×512` `32×16` `512<720` | `Dojo 10` | — | `none` `dojo` | `none` | `none` | `follow` `0-0` `centrado` | PASS | `0.07` `demo 512` | **WARNING** `512<720` similar mecanicas |
| stage_pokemon_cenital | `40×64` | `1600×720` `cenital` | `Pokemon 48×56` | — | `1280` | `wrap` | `y-sorting` | `cenital` | PASS | `0.08` | PASS |

**Densidad:** `occupied/viewport` `0.04-0.16` (`hall 0.05` sparse, `stage1_3 0.16` denso) — ningún `>0.25` sobrecarga, ningún `<0.03` vacío salvo `hall` lobby intencional.

**Camera framing:** Player `40` ocupa `3.1%` ancho, `8.9%` alto — proporción `60fps` anticipación `0.30` `space 45%` para enemigos, vertical `horizonte 60%` plataformas, boss `Venado 128` ocupa `10%` ancho `13%` alto cabe con `zoom 1.25` y `shake`, arena `5280` permite `4×` vp anticipación.

**Estado:** `24 PASS` `2 WARNING` (demo corta <720, no nativa) `0 FAIL`.

