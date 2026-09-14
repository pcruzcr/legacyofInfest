# VISUAL REGRESSION BASELINE — Golden Frames

**Fecha:** 2026-09-01 · **Resolución:** `1280×720` `80×45` `16` `nearest` · **Capturas:** `qa_screenshots/*_normal.png` `17` + `diagnostic` `17` `gen_qa_screenshots.py:1` `metrics_qa.py`

## Golden Frames

| Frame | Tamaño `px` | Origen | Hash `md5` `headless` | Status |
|---|---|---|---|---|
| TITLE | `1280×720` | `title_scene` `bg_title 1280` | `title_1280.png` `bg 15,15,40` | REFERENCE |
| WORLD_MAP | `1280×720` | `world_map_scene` `nodes 26 32×32` | `world_map_1280.png` | REFERENCE |
| STAGE0 SPAWN | `1280×720` | `stage0` `160,480` `camera 0-1280` `HUD 96×16` | `stage0_normal.png` `31.8 18.3 36.2%` | REFERENCE `golden` |
| STAGE1_1 MID | `1280×720` | `stage1_1` `mid` `camera 640` `parallax 0.35` | `stage1_1_normal 122.9 67.2 100%` | REFERENCE |
| STAGE2_2 VERTICAL | `1280×720` `viewport 1920×800` `Y 80` | `stage2_2` `800h` | `stage2_2_normal 163 53 100%` | REFERENCE |
| BOSS_VENADO ARENA | `1280×720` | `boss_venado` `arena 5280` `boss 128×96` `HUD 400×24` | `boss_venado_normal 81 44 94%` | REFERENCE |
| BOSS_PABURU VERTICAL | `1280×720` `1312h` `Y 592` | `boss_paburu` `4160×1312` `floor 1200` | `boss_paburu_normal 47 28 65%` | REFERENCE |
| PAUSE | `1280×720` | `PausaDeEscenario` `4 tabs` `overlay 180` `clock pause` | `pause_1280.png` | REFERENCE |
| INVENTORY | `1280×720` | `InventoryScene` `grid 3×3 480×360` `5 items` | `inventory_1280.png` | REFERENCE |
| SKILL | `1280×720` | `SkillTreeScene` `nodes 48×48` `points 3` | `skill_1280.png` | REFERENCE |
| SHOP | `1280×720` | `ShopScene` `4 cat 8 items` | `shop_1280.png` | REFERENCE |
| DEATH | `1280×720` | `GameOverScene` `fade 0.5` | `death_1280.png` | REFERENCE |
| COMPLETE | `1280×720` | `EndCreditsScene` `banner` | `complete_1280.png` | REFERENCE |

**Comparación:** `metrics_qa.py` `brightness` `contrast` `occupied` `hud_brightness` — `stage0` `31.8` vs `stage1_1` `122.9` `Δ 91` `V01` `ambient_light 0.55`.

**Thresholds:** `HUD stability Δ 0` `camera_max Δ<20` `bg_jumps 0` `occupied 2-100%` `2.3% hall` `WARNING` `player_screen Δ 1.5` `±0.2`.

**Estado:** `13` `GOLDEN` `PASS` — `qa_screenshots` `34` `1280×720` `headless` `SDL_VIDEODRIVER=dummy`.
