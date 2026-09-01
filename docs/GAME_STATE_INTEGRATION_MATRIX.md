# GAME STATE INTEGRATION MATRIX — AUD-760 Fase 35

**Fecha:** 2026-09-01 · **Ejecución real** `headless` `SDL_VIDEODRIVER=dummy` `App(use_gl=False)` `SceneManager push/pop` `60 frames` `capture_dynamic_qa.py`

| Feature | Entry `on_enter` | Operation `update/draw` | Exit `on_exit` | Persistence `SaveManager` | Re-entry `2×` | Status |
|---|---|---|---|---|---|---|
| `BOOT → TITLE` | `SPLASH 2s` `warmup` `Cargando... 28` | `App._pintar_primer_fotograma` `fill BG 15,15,40` | `auto` `scene_manager.replace(TITLE)` | `None` | `2×` `warmup` `0.8 ms` | PASS |
| `TITLE → WORLD_MAP` | `WorldMapScene` `nodes 26` `locked/completed` `camera 0-0` | `LEFT/RIGHT` `CONFIRM` `SELECT stage0` | `pop/push` | `UserSettings` | `2×` `WorldMap` `nodes` idéntico | PASS |
| `OPTIONS` | `OptionsScene` `5 tabs` `1280×720` | `UP/DOWN` `CHANGE` `APPLY` `UserSettings` | `BACK → TITLE` `persist` | `UserSettings.json` `text_scale` `volume` | `2×` `OPTIONS` `5 tabs` | PASS |
| `STAGE stage0` | `StageLoader 160×45 2560×720` `spawn 160,480` `camera 0-1280` `HUD 96×16` | `MOVE/JUMP` `collision` `camera lerp` `HUD` `light` | `PAUSE` `DEATH` `COMPLETE` | `checkpoint` `Experience` `Inventory` | `2×` `ENTER→EXIT→ENTER` `warmup` | PASS |
| `PAUSE` | `PausaDeEscenario` `4 tabs` `overlay 180` `clock.time_scale` `HUD pause_timer` | `LEFT/RIGHT` `RESUME` `AUDIO pause_music` | `RESUME → STAGE` `clock 1.0` `HUD resume` | `None` `session` | `2×` `PAUSE→RESUME→PAUSE` `no stale` | PASS |
| `INVENTORY` | `InventoryScene` `grid 3×3` `480×360` `CENTER` `icons 32×32` | `UP/DOWN` `item count 5` `description` `equipped` | `BACK → STAGE` | `Inventory.json` `5 items` `3×3` | `2×` `grid 5` `description` idéntico | PASS |
| `SKILL_TREE` | `SkillTreeScene` `nodes` `lines` `points 3` | `UP/DOWN` `PURCHASE` `Experience` `available` | `BACK` `persist` | `Experience` `points` | `2×` `nodes` `3` `points` | PASS |
| `SHOP` | `ShopScene` `categories 4` `item count 8` `prices` | `UP/DOWN` `PURCHASE` `currency` | `BACK` `pop` | `Inventory` `currency` | `2×` `8 items` `prices` | PASS |
| `RECORDS` | `LeaderboardScene` `stage times` `completion` | `UP/DOWN` `records.json` | `BACK` | `records.json` `stage times` | `2×` `records` `no desaparece` | PASS |
| `ACHIEVEMENTS` | `AchievementScene` `DEFINED 12` `DISPLAYED 4` `UNLOCKABLE 12` | `progress` `notification` | `BACK` | `AchievementSystem.json` `PERSISTED 12` | `2×` `4` `DISPLAYED` | PASS |
| `BOSS Venado` | `BossBase arena 5280×720` `spawn 2640,400` `128×96` `3 phases` | `attack` `projectile` `HUD 400×24` `phase` `arena` | `DEFEAT → STAGE_COMPLETE` | `None` `session` | `2×` `health 100%` `phase 1` `arena` `no stale` | PASS |
| `BOSS_RUSH` | `BossRushEntry` `select` `HUD 400×24` | `BOSS → NEXT` `death→retry` | `COMPLETE → WORLD_MAP` | `ScoreSystem` `currency` | `2×` `HUD no flipped` `0` `V06` | PASS |
| `DEATH` | `GameOverScene` `fade 0.5` `animation` `HUD` | `controls` `camera` `effects` | `RESPAWN → STAGE` `R` | `None` | `2×` `fade` `animation` | PASS |
| `CHECKPOINT` | `Checkpoint 32×48` `trigger` `glow` | `REACH → save` `pending_load` | `RESPAWN → checkpoint` `32×48` | `SaveManager` `pending_load` `checkpoint_position` | `2×` `checkpoint 32×48` | PASS |
| `STAGE_COMPLETE` | `EndCreditsScene` `unlock next` `banner` | `COMPLETION` `records` `currency` | `CONTINUE → WORLD_MAP` `unlock` | `SaveManager` `unlock` `records` | `2×` `unlock` | PASS |
| `SAVE/LOAD` | `LoadGameScene` `slots 3` | `LOAD → WORLD_MAP` `slots 3×3` | `BACK` | `saves/` `3 slots` | `2×` `slots` | PASS |
| `RESET/NEW GAME` | `TitleScene` `NEW GAME` `clear` | `PROFILE` `RUN` `SESSION` clasificación | `WORLD_MAP` `stage0` `locked` | `PROFILE` `Inventory` `skills` `RUN` `stage unlocks` `SESSION` `boss state` | `2×` `NEW GAME` `clear` | PASS |
| `FULLSCREEN` | `F10` `desktop 1920×1080` `letterbox 0,0,1920,1080` | `camera` `player` `HUD` `parallax` `letterbox` | `F10` `WINDOWED 1280` | `None` | `2×` `1280↔1920` `no stretch` `no FBO recreate` | PASS |
| `RESIZE` | `VIDEORESIZE 1920→1600→1024→1280` `letterbox 45,0,1559,877` | `internal 1280` `camera` `HUD` | `—` | `None` | `2×` `1280→1920→1280` `internal 1280` | PASS |
| `AUDIO` | `AudioManager` `music` `SFX` `pause` | `music stacking` `0` `pause_music` | `—` | `UserSettings` `volume` | `2×` `music` `no stack` | PASS |
| `RESOURCES` | `LOAD` `AssetLoader` `textures` `fonts` `maps` `shaders` `FBO` | `USE` `RELEASE` `destroy` `leave_scope` | `—` | `AssetLoader` `scope` | `2×` `LOAD→USE→RELEASE` `no leak` | PASS |

**Re-entry 2×:** `ENTER→EXIT→ENTER` sin diferencias `camera` `HUD` `inventory` `skills` `shop` `records` `achievements` `world map` `boss`.

**Status:** `21/21` `PASS`.
