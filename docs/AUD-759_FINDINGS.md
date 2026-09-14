# AUD-759 FINDINGS — Dinámica

**Fecha:** 2026-09-01 · **Sequences:** `60` `120` frames `20` niveles `capture_dynamic_qa.py` `qa_dynamic/*`

| ID | LEVEL | FRAME RANGE `0-60` | OBJECT | OBSERVED `Δ` | EXPECTED `Δ` | ROOT CAUSE `D01-D13` | EVIDENCE `capture_all.log` `qa_screenshots` | FIX | RISK |
|---|---|---|---|---|---|---|---|---|---|
| D01 | stage0 | `0-60` walk `1.5/frame` | `Camera` `offset.x` `max Δ 0.0` `mean 0.0` `dead 48` | `0.0` | `~0.2` `lerp 0.13*1.5` | `D13 Intentional` `dead zone` `48` `player` dentro `dead` no mueve cámara | `capture_all.log stage0 camera 0.0` `qa_screenshots/stage0_normal` `player_screen 1.5` `HUD stable` | Ninguno (`dead` intencional para no marear) | — |
| D02 | all | `0-60` | `HUD` `vida_bar 24,138` `96×16` | `Δ 0` `stable True` `60/60` | `0` | `D13` `UI` `VIEWPORT` `1280×720` `anchor TOP_LEFT` `display_scale` único `letterbox` | `test_hud_stability 18/18 PASS` `capture_all hud_stable True` | Ninguno | — |
| D03 | all | `0-60` | `Background far 0.15` `shift 0.22/frame` `mid 0.35` `0.52` `near 0.60` `0.90` `wrap %1280` | `0 jumps` | `0` | `D13` `parallax` `factor` por nombre `VELOCIDAD_DE_FONDO` | `capture bg_jumps 0` `test_parallax_continuity 20/20` | Ninguno | — |
| D04 | stage1_1 | `0-60` `walk` | `Player feet 40×64` `bottom 608` `hurtbox 20×28` `+4` `feet 608` `== floor 608` `Δ 1.5` `screen` `swimming 0` | `1.5` | `1.5` | `D13` `anchor midbottom` `int` `rect` `feet` estable `animation` `40×64` `hurtbox` dentro | `test_player_anchor 2/2` `metrics stage0 feet 0` | Ninguno | — |
| D05 | stage4_1 | `0-60` `18 rooms 21760` | `Transition room x%1280==0` `trigger==door` `fade 0.5` | `0` | `0` | `D13` `room 1280` `transition` `camera` `1280` `Δ bg 192` `player 640` sin `flash` | `DYNAMIC_LEVEL_QA_MATRIX Transition room` `STAGE_SPATIAL_INTEGRITY` | Ninguno | — |

**Resumen:** `5` findings `5` `D13 Intentional` `0` `D01-D12` confirmados — `HUD` `camera` `parallax` `player` `transition` todos estables `Δ` coherente con `90 px/s` `lerp` `dead`.

**Correcciones:** `0` `A-N` — ningún `scaling` `zoom` `TILE_SIZE` `INTERNAL` `FBO` modificado.

**Evidencia reproducible:** `scripts/capture_dynamic_qa.py --frames 60 --all` `qa_dynamic/summary.json` `camera_max 0.0` `player_screen 1.5` `hud_stable True` `bg_jumps 0`.
