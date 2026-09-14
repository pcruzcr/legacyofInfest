# GAME STATE INVENTORY — AUD-760 Fase 1

**Fecha:** 2026-09-01 · **Inventario extraído del código real** `src/engine/scenes/*.py` `src/framework/scenes/stage_scene.py` `src/engine/scene/scene_manager.py`

> No se inventan estados; cada fila existe como `class ...Scene(BaseScene)` o `StageScene` mixin.

| State | Entry `on_enter` | Exit `on_exit` | Parent `SceneManager` | Overlay `bool` | Input `Action` | Render `draw` | Persistence `SaveManager` |
|---|---|---|---|---|---|---|---|
| `SPLASH` | `SplashScene` `asset warmup` `2s` | `auto → TITLE` | `App` | No | `—` | `logo 1280×720` `BG 14,15,28` | `None` |
| `TITLE` | `TitleScene` `3 options` `Continue/New/Options` | `START → WORLD_MAP` `OPTIONS → OPTIONS` | `App` | No | `UP/DOWN/CONFIRM` `Keyboard/Controller` | `title 1280×720` `bg_title.png 1280` | `UserSettings` `SaveManager` |
| `OPTIONS` | `OptionsScene` `5 tabs` `Resolution/Audio/Controls/Graphics/Language` | `BACK → TITLE` `APPLY → persist` | `TITLE` `PAUSE` | No | `UP/DOWN/LEFT/RIGHT` | `1280×720` `theme` | `UserSettings.json` |
| `WORLD_MAP` | `WorldMapScene` `nodes 26` `stage0-4_1` `boss` `locked/completed` | `SELECT → STAGE` `BACK → TITLE` | `App` | No | `LEFT/RIGHT/CONFIRM` | `map 1280×720` `nodes 32×32` `camera 0-0` | `SaveManager` `Bestiary` `Achievements` |
| `STAGE` | `StageScene` `TMX load` `player spawn` `camera 1280×720` `HUD` | `PAUSE → PAUSE` `DEATH → RESPAWN` `COMPLETE → WORLD_MAP` `BACK → WORLD_MAP` | `App` | No | `MOVE/JUMP/ATTACK/PAUSE` | `world 1280×720` `pyscroll` `entities` `HUD` `light` | `SaveManager` `checkpoint` `Experience` `Inventory` |
| `PAUSE` | `PausaDeEscenario` `4 tabs` `Equipo/Habilidades/Mapa/Menu` `overlay` | `RESUME → STAGE` `OPTIONS → OPTIONS` `TITLE → TITLE` | `STAGE` (overlay) | **Sí** `SRCALPHA 180` `1280×720` | `LEFT/RIGHT/CONFIRM/BACK` | `pause 1280×720` `tabs 1280×20` `BG 14,15,28` | `None` (session) |
| `INVENTORY` | `InventoryScene` `grid 3×3` `480×360` `CENTER` | `BACK → STAGE/PAUSE` | `PAUSE` `STAGE` | Sí (embebida `PAUSE` `Equipo`) | `UP/DOWN/CONFIRM` | `inventory 1280×720` `theme` `icons 32×32` | `Inventory.json` `get_inventory()` |
| `SKILL_TREE` | `SkillTreeScene` `nodes` `lines` `points` | `BACK → STAGE/PAUSE` `PURCHASE → persist` | `PAUSE` | Sí (embebida `Habilidades`) | `UP/DOWN/CONFIRM` | `skill 1280×720` `nodes 48×48` | `Experience` `UserSettings` |
| `SHOP` | `ShopScene` `categories` `prices` `4×3 grid` | `BACK → STAGE/PAUSE` `PURCHASE → Inventory-` | `PAUSE` | No (pushed) | `UP/DOWN/CONFIRM` | `shop 1280×720` `icons` | `Inventory` |
| `RECORDS` | `LeaderboardScene` `stage times` `boss` | `BACK → TITLE/WORLD_MAP` | `TITLE` | No | `UP/DOWN` | `records 1280×720` | `SaveManager` `records.json` |
| `ACHIEVEMENTS` | `AchievementScene` `4+` `locked/unlocked` `progress` | `BACK → TITLE` | `TITLE` | No | `UP/DOWN` | `achievements 1280×720` | `AchievementSystem.json` |
| `BESTIARY` | `BestiaryScene` `enemies 8+` | `BACK` | `STAGE` `TITLE` | No | `UP/DOWN` | `bestiary 1280×720` | `Bestiary.json` |
| `BOSS` | `BossBase` `arena` `health 400×24` `phase` | `DEFEAT → STAGE_COMPLETE` `DEATH → RESPAWN` | `STAGE` | No | `MOVE/ATTACK` | `world 1280×720` `boss 96-128` `arena 1632-5280` | `None` (session) |
| `CHECKPOINT` | `Checkpoint` `rect 32×48` `trigger` | `REACH → save` `RESPAWN → checkpoint` | `STAGE` | No | `—` | `glow` `32×48` | `SaveManager` `pending_load` |
| `DEATH` | `GameOverScene` `fade 0.5` | `RESPAWN → STAGE` `TITLE → TITLE` | `STAGE` | No | `CONFIRM` | `gameover 1280×720` `BG 15,15,40` | `None` |
| `STAGE_COMPLETE` | `EndCreditsScene` / `WorldMap` `unlock next` | `CONTINUE → WORLD_MAP` | `STAGE` | No | `CONFIRM` | `complete 1280×720` `banner` | `SaveManager` `unlock` |
| `LOADING` | `LoadingScene` `progress` `warmup` `2s` | `auto → STAGE/WORLD_MAP` | `App` | No | `—` | `loading 1280×720` `BG 15,15,40` `Cargando... 28` | `None` |
| `BOSS_RUSH` | `BossRushEntry` `select boss` `HUD flipped?` | `START → BOSS` `COMPLETE → WORLD_MAP` | `TITLE` | No | `UP/DOWN/CONFIRM` | `boss_rush 1280×720` `HUD 400×24` | `ScoreSystem` |
| `SAVE/LOAD` | `LoadGameScene` `slots 3` | `LOAD → WORLD_MAP` `BACK → TITLE` | `TITLE` | No | `UP/DOWN/CONFIRM` | `load 1280×720` `slots 3×3` | `SaveManager` `saves/` |
| `TUTORIAL` | `TutorialOverlay` `T` `learning` | `CLOSE → STAGE` | `STAGE` (overlay) | Sí | `T` `HELP` | `overlay 1280×720` `alpha 180` | `Session` |

**Total States:** 21 (incluye `SPLASH` `TITLE` `OPTIONS` `WORLD_MAP` `STAGE` `PAUSE` `INVENTORY` `SKILL` `SHOP` `RECORDS` `ACHIEVEMENTS` `BESTIARY` `BOSS` `CHECKPOINT` `DEATH` `COMPLETE` `LOADING` `BOSS_RUSH` `SAVE/LOAD` `TUTORIAL` `DEBUG`)

**Overlays:** `PAUSE` `TUTORIAL` `INVENTORY` (embebida) `SKILL` (embebida) — `SRCALPHA` `1280×720` `draw` sobre `STAGE` sin `camera`.

**Input:** `InputManager` `Action` `UP/DOWN/CONFIRM/BACK/PAUSE` `Keyboard` `Controller` (no `Mouse` salvo `world_map` `click` opcional).

**Render:** `App.internal_surface 1280×720` `DRAW` `LIGHT` `HUD` `overlay` `letterbox` `display.calculate_viewport` — `FROZEN`.

**Persistence:** `UserSettings` `SaveManager` `Inventory` `Experience` `Bestiary` `Achievements` `pending_load` `zone_flags`.
