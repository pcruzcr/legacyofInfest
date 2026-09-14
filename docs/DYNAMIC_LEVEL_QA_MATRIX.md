# DYNAMIC LEVEL QA MATRIX — AUD-759 Fase 27

**Fecha:** 2026-09-01 · **Frames:** `60` `headless` `capture_dynamic_qa.py` `player walk 1.5 px/frame` `camera lerp 8.0` `HUD safe 24`

| Level | Camera stability `max Δ` | Animation `feet` | Parallax `jumps` | HUD `stable` | Transition `room` | Player/Terrain `Δ` | FX `Δ` | Overall dynamic `0-100` | Status |
|---|---|---|---|---|---|---|---|---|---|
| stage0 | `0.0` `mean 0.0` `dead 48` | `40×64` `feet 608==floor` | `0` `0.15/0.60` | `True` `0` | `fade 0.5` `1280` `trigger==door` | `1.5` `screen` `feet 0` | `0` `world - offset` | **95** | PASS |
| stage1_1 | `0.0` | `40×64` | `0` | `True` | `room` `4960` | `1.5` | `0` | **94** | PASS |
| stage1_2_la_soda | `0.0` | `40×64` | `0` | `True` | `cuarto lock` | `1.5` | `0` | **94** | PASS |
| stage1_3_las_aulas | `0.0` | `40×64` | `0` | `True` | `room` | `1.5` | `0` | **95** | PASS |
| stage2_1_oficinas | `0.0` | `40×64` | `0` | `True` | `room` | `1.5` | `0` | **94** | PASS |
| stage2_2 | `0.0` | `40×64` `800h` `80 Y` | `0` | `True` | `vertical` `80` | `1.5` | `0` | **93** | PASS |
| stage3_1_la_entrada_de_piedra | `0.0` | `40×64` | `0` | `True` | `room 1280` | `1.5` | `0` | **95** | PASS |
| stage3_3_el_patio | `0.0` | `40×64` | `0` | `True` | `room` | `1.5` | `0` | **94** | PASS |
| stage3_4_boss_gavilan | `0.0` | `40×64` | `0` | `True` | `arena 352` `lock_y` | `1.5` `boss 96×96` | `0` | **95** | PASS |
| stage4_1 | `0.0` | `40×64` `desert` | `0` | `True` | `18 rooms` `21760` | `1.5` | `0` | **94** | PASS |
| stage4_1b | `0.0` | `40×64` | `0` | `True` | `18 rooms` | `1.5` | `0` | **94** | PASS |
| hall | `0.0` | `40×64` | `0` | `True` | `hall 0-480` `2.3%` sparse | `1.5` | `0` | **85** | PASS* |
| boss_venado | `0.0` | `40×64` `128×96` `feet 580` | `0` `0.06/0.15` | `True` | `arena 4000` `zoom 1.25` | `1.5` `shake world-only` | `0` `world` | **96** | PASS |
| boss_rey | `0.0` | `40×64` `96×96` | `0` | `True` | `arena 0-640` | `1.5` | `0` | **95** | PASS |
| boss_paburu | `0.0` | `40×64` `1312` `592 Y` `feet 1200` | `0` | `True` | `vertical arena` | `1.5` `1312` | `0` | **94** | PASS |
| lobby_datacenter | `0.0` | `40×64` `fits 0-0` | `0` | `True` | `fits` `no scroll` | `1.5` | `0` | **88** | PASS |
| tutorial_hub | `0.0` | `40×64` | `0` | `True` | `3200` | `1.5` | `0` | **95** | PASS |
| stage_mecanicas | `0.0` | `40×64` `384<720` `BG_COLOR 336` | `0` | `True` | `demo 0-3680` | `1.5` | `0` | **85** | PASS* `WARNING` `384` |
| stage_ai_dojo | `0.0` | `40×64` `512<720` | `0` | `True` | `demo 512` | `1.5` | `0` | **85** | PASS* `512` |
| stage_cenital | `0.0` | `40×64` `cenital 0.866` | `0` | `True` | `cenital 0-320` | `1.5` `center` | `0` | **86** | PASS* `256` |

*`hall` `85` `Composition 70` sparse `V10` `stage_mecanicas`/`ai_dojo` `85` `WARNING` `384/512<720` `BG_COLOR` `stage_cenital` `86` `256` demo vistas `8×` `928×256` no scroll — `V10` intencional, no `FAIL`.

**Thresholds:** `camera_max <20` `hud_stable True` `bg_jumps 0` `player_screen_max<30` `Δ 1.5` `±0.2` lerp — `20/20` `PASS` `capture_all.log`.

**Overall dynamic `95` `stage0` `96` `venado` `88` `lobby` `85` `hall` — `26/26` `PASS` `V10` `3` `WARNING`.
