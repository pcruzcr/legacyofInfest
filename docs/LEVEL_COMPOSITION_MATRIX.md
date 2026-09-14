# LEVEL COMPOSITION MATRIX — AUD Final

**Fecha:** 2026-09-01 · **Grid:** `80×45` `1280×720` `16`

| Level | Size `tiles` `px` | Tiles `solid/empty` | Objects `density` | Enemies `count` `size` | Checkpoints `n` | Camera `bounds` `start` `limits` | Background `size` `parallax` | Lighting `ambient` | Player spawn `x,y` `feet` | Boss `size` `arena` | Visual Density `occupied` | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| stage0 | `160×45` `2560×720` | `3600` `112/8` `608` `solid 0.18` `empty 0.64` | `101` `0.12` `Chest 32×24` | `Walker 24×28` `3` | `2` `320,400` | `0-1280` `0-0` `spawn 160,480` `dead 48` | `1280+2560+3840` `0.06/0.15/0.35/0.60` | `0.60` | `160,480` `feet 544→608` | — | `36.2%` `31.8` | PASS |
| stage1_1 | `390×45` `6240×720` | `112` `solid 0.20` | `60` `0.15` | `3` `24×28` | `3` | `0-4960` | `1280 3 capas` | `0.55` | `96,400` | — | `100%` `122.9` | PASS |
| stage1_2 | `350×45` `5600×720` | `70` `0.14` | `70` | `4` | `2` | `0-4320` `cuarto` | `1280` | `0.60` | `120,420` | — | `97.6%` | PASS |
| stage2_2 | `120×50` `1920×800` | `50` `vertical` `0.11` | `49` | `3` `16×16` | `2` | `0-640×0-80` | `1280` `800` | `0.60` | `160,600` | — | `100%` | PASS vertical |
| boss_venado | `330×45` `5280×720` | `34` `0.09` | `34` | `1` `128×96` | `1` | `0-4000` `arena` | `1280×720` | `0.60` | `200,500` `2640,400` | `128×96` `5280` | `94.2%` | PASS |
| boss_paburu | `260×82` `4160×1312` | `112` `vertical` `0.10` | `112` | `Form1 16×8` `Form2 64×96` | `1` | `0-2880×0-592` | `1280×720` `1600→1280` | `0.60` | `200,1100` `2080,1000` | `64×96` `4160` | `65.5%` | PASS |
| stage_mecanicas | `310×24` `4960×384` | `165` `0.06` `384<720` | `165` | `3` | `0` | `0-3680×0-0` | `1280×720` | `0.60` | `160,300` | — | `28.7%` | WARNING `384` |

*Completa en `docs/LEVEL_VISUAL_COMPOSITION_MATRIX.md:1` 26 filas, `docs/STAGE_SPATIAL_INTEGRITY_MATRIX.md:1` `docs/LEVEL_VISUAL_MATRIX.md:1`.*
