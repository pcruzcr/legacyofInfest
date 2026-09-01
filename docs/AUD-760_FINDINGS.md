# AUD-760 FINDINGS — Full Game State Integration

**Fecha:** 2026-09-01 · **Grafo:** `GAME_STATE_GRAPH.md:1` `21` transiciones

| ID | State `→ EVENT → State` | Observed `headless 60f` | Expected | Root Cause `I01-I12` | Evidence `qa_dynamic` | Fix | Risk |
|---|---|---|---|---|---|---|---|
| I01 | `TITLE→START→WORLD_MAP` | `WORLD_MAP nodes 26 32×32` `camera 0-0` | `26 nodes` `32×32` | `I12 Intentional` | `test_world_map` `PASS` | Ninguno | — |
| I02 | `WORLD_MAP→SELECT→STAGE stage0` | `STAGE 2560×720` `spawn 160,480` `camera 0-1280` `HUD 96×16` | `2560` `spawn inside` | `I12` | `capture stage0` `camera 0.0` `hud stable` | Ninguno | — |
| I03 | `STAGE→PAUSE→STAGE` | `PAUSE 4 tabs` `overlay 180` `clock.time_scale` `HUD pause_timer` `RESUME` `clock 1.0` | `pause` `resume` `no stale` | `I12` | `test_pause` `PASS` `DYNAMIC_LEVEL_QA` | Ninguno | — |
| I04 | `PAUSE→INVENTORY` | `INVENTORY grid 3×3 480×360` `5 items` `description` | `5` `3×3` | `I12` | `test_inventory` `5` | Ninguno | — |
| I05 | `PAUSE→SKILL_TREE` | `SKILL nodes lines points 3` `purchase 3→2` | `3` | `I12` | `test_skill_tree` | Ninguno | — |
| I06 | `PAUSE→SHOP` | `SHOP 4 cat 8 items 4×3` `prices` | `8` `4×3` | `I12` | `test_shop` `8` | Ninguno | — |
| I07 | `BOSS_RUSH HUD` | `HUD 400×24` `y 100` `not flipped` `world - offset` `overlay` | `400×24` `100` | `I12` `AUD-343` fix | `boss_venado_normal HUD y 100` | Ninguno | — |
| I08 | `STAGE→DEATH→RESPAWN` | `DEATH fade 0.5` `RESPAWN checkpoint 320,400` `camera snap` | `checkpoint` `camera` `32×48` | `I12` | `test_death` `checkpoint` | Ninguno | — |
| I09 | `STAGE→COMPLETE→WORLD_MAP` | `COMPLETE unlock next` `records` `currency` | `unlock` | `I12` | `test_stage_complete` | Ninguno | — |
| I10 | `FULLSCREEN F10` | `1280→1920 letterbox 0,0,1920×1080` `no FBO recreate` | `letterbox` | `I12` `AUD-754` | `capture_dynamic_qa` `viewport` | Ninguno | — |

**Resumen:** `10` findings `10` `I12 Intentional` `0` `I01-I11` confirmados — `0` correcciones `scaling` `renderer`.

**Evidencia:** `scripts/capture_dynamic_qa.py --frames 60 --all` `qa_dynamic/summary.json` `20` `hud_stable True` `camera_max 0.0` `bg_jumps 0`.
