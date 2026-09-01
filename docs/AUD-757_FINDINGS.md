# AUD-757 FINDINGS — Hallazgos espaciales

**Fecha:** 2026-09-01 · **26 niveles auditados** · **Metodología:** `audit757_spatial.py` + `StageLoader` headless + `TMX` parse + `player 40×64` referencia

| ID | Level | File:Line | Object | Observed | Expected | Delta `px / tiles` | Root cause | Proposed fix | Risk |
|---|---|---|---|---|---|---|---|---|---|
| F01 | stage0 | `assets/maps/stage0/stage0.tmx:42` `Terrain` `608,112` | `Solid` `0,608,2560,112` visual `608` vs collision `608` | `0` `0` | — | — | — | — |
| F02 | stage_mecanicas | `310×24` `4960×384` | `World 384` `Viewport 720` `336 px BG_COLOR` bajo mapa `y 384-720` `=336` | `720` | `336 / 21` | `E level data` `B world < viewport` | Documentar como demo corta <720 (no escalar mapa) o agrandar TMX a `45` filas `720` si se quiere nativo | Bajo (demo) |
| F03 | stage_ai_dojo | `64×32` `1024×512` | `World 512` `Viewport 720` `208 px BG` | `720` | `208 /13` | `E` `512<720` | Documentar `WARNING` (ya) | Bajo |
| F04 | stage_* 58×16 | `928×256` | `256` `720` `464 BG` | `720` | `464 /29` | `E` `demo vistas` | Documentar `WARNING` | Bajo |
| F05 | boss_paburu | `bg_paburu_far.png 1600×600` `assets/backgrounds/bg_paburu_far.png:1` | `1600×600` `aspect 2.66` vs `viewport 1.77` `600<720` `120 px BG` bajo far | `1280×720` | `120 /7.5` `aspect 0.89` | `H background` `far` no nativo 1280×720 | Re-exportar `bg_paburu_far` a `1280×720` (o `2560×720` parallax 2×) y ajustar `0.06` a `0.15` si se quiere 1600 ancho heredado | Medio (visual far desalineado) |
| F06 | boss_paburu | `4160×1312` `Platform` `y 1200` `col y 1200` | `feet y 1200+64=1264` vs `floor y 1200` `delta 0` | `0` | `0/0` | `O intentional` `vertical` | Ninguno | — |
| F07 | stage2_2 | `120×50` `1920×800` | `800>720` `80 px scroll Y` `floor y 704` vs `visual 704` | `704` | `0` | `O` `vertical` | Ninguno | — |
| F08 | all | `src/framework/entities/player.py:421` `40×64` `hurtbox 20×28` | `hurtbox x = rect.x +10` `y+4` `20×28` vs `rect 40×64` `delta 10,4` | `10,4` | `0.625,0.25` | `O` `smaller hurtbox` intencional para jugabilidad | Ninguno | — |
| F09 | all | `src/framework/entities/enemy_*.py` `rect` | `walker 24×28` vs `visual 24×28` `delta 0` | `0` | `0` | `O` | Ninguno | — |
| F10 | all | `src/framework/stage/camera.py:330` `clamp` | `camera 0-1280` vs `world 2560` `show 0-1280` `delta 0` | `0` | `0` | `O` | Ninguno | — |
| F11 | all | `TMX object` `x,y` `float` `123.5?` | `grep 0.5` 0 en TMX `int` | `int` | `0` | `O` | Ninguno | — |
| F12 | stage1_2 | `stage1_2` `SodaMachine 32×48` `x 100.5?` | `SodaMachine` `x 100` `int` | `int` | `0` | `O` | Ninguno | — |

**Resumen:** Solo `F02-F05` con delta >0, todos `WARNING` demo corta o `H background` legacy `1600×600`. `F01,F06-F12` `0` PASS. No `A` renderer, no `C` coordinate conversion (AUD-754), no `D` anchor (pies `midbottom` consistente).

**Propuesta:** Corregir `F05` `bg_paburu_far` a `1280×720` nativo (1 archivo PNG) — resto documentar.
